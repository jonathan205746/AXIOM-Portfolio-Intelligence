"""Leakage-aware price-only walk-forward backtest for AXIOM.

Produces real results for:
1. quantitative-only PortfolioOptimizer
2. monthly rebalanced equal weight
3. buy-and-hold market benchmark

AXIOM combined is intentionally not calculated because the current project
does not include a point-in-time historical news/sentiment dataset.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.optimization.portfolio import PortfolioOptimizer

TRADING_DAYS = 252


@dataclass(frozen=True)
class Config:
    tickers: list[str]
    benchmark: str
    start: str
    end: str
    lookback: int
    risk_free_rate: float
    transaction_cost: float
    min_weight: float
    max_weight: float
    initial_capital: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "META"])
    parser.add_argument("--benchmark", default="^GSPC")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--lookback", type=int, default=252)
    parser.add_argument("--risk-free-rate", type=float, default=0.05)
    parser.add_argument("--transaction-cost", type=float, default=0.0015, help="Cost per traded notional; 0.0015 = 15 bps")
    parser.add_argument("--min-weight", type=float, default=0.02)
    parser.add_argument("--max-weight", type=float, default=0.35)
    parser.add_argument("--initial-capital", type=float, default=100000.0)
    parser.add_argument("--output-dir", default="results")
    return parser.parse_args()


def _close_frame(raw: pd.DataFrame | None, symbols: list[str]) -> pd.DataFrame:
    if raw is None or raw.empty:
        raise RuntimeError("The market-data download returned no rows.")
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"]
        elif "Close" in raw.columns.get_level_values(1):
            close = raw.xs("Close", axis=1, level=1)
        else:
            raise RuntimeError("Could not locate Close prices in yfinance response.")
        if isinstance(close, pd.Series):
            close = close.to_frame()
    else:
        if "Close" not in raw.columns:
            raise RuntimeError("Could not locate Close prices in yfinance response.")
        close = raw[["Close"]].rename(columns={"Close": symbols[0]})
    close = close.rename_axis(index="date").sort_index()
    available = [symbol for symbol in symbols if symbol in close.columns]
    missing = sorted(set(symbols) - set(available))
    if missing:
        raise RuntimeError(f"Missing Close data for: {missing}")
    return close[available].astype(float)


def download_prices(config: Config) -> tuple[pd.DataFrame, pd.Series]:
    requested_start = pd.Timestamp(config.start)
    download_start = requested_start - timedelta(days=max(550, int(config.lookback * 2.2)))
    download_end = pd.Timestamp(config.end) + timedelta(days=1)
    raw_assets = yf.download(
        config.tickers,
        start=download_start.strftime("%Y-%m-%d"),
        end=download_end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    assets = _close_frame(raw_assets, config.tickers).dropna(how="any")
    raw_benchmark = yf.download(
        [config.benchmark],
        start=download_start.strftime("%Y-%m-%d"),
        end=download_end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    benchmark = _close_frame(raw_benchmark, [config.benchmark])[config.benchmark].dropna()
    return assets, benchmark


def rebalance_dates(index: pd.DatetimeIndex, start: pd.Timestamp) -> set[pd.Timestamp]:
    eligible = index[index >= start]
    if eligible.empty:
        return set()
    frame = pd.DataFrame(index=eligible)
    first_days = frame.groupby([eligible.year, eligible.month]).head(1).index
    return set(pd.Timestamp(x) for x in first_days)


def run_strategy(
    prices: pd.DataFrame,
    config: Config,
    mode: str,
) -> tuple[pd.Series, float, float, list[dict[str, Any]]]:
    returns = prices.pct_change(fill_method=None)
    requested_start = pd.Timestamp(config.start)
    requested_end = pd.Timestamp(config.end)
    dates = prices.index[(prices.index >= requested_start) & (prices.index <= requested_end)]
    if len(dates) < 2:
        raise RuntimeError("Not enough observations in the requested evaluation window.")
    rebalances = rebalance_dates(pd.DatetimeIndex(dates), requested_start)
    n = len(config.tickers)
    weights = np.repeat(1.0 / n, n)
    nav = config.initial_capital
    nav_rows: list[tuple[pd.Timestamp, float]] = []
    total_turnover = 0.0
    total_cost = 0.0
    weight_log: list[dict[str, Any]] = []

    for date in dates:
        location = prices.index.get_loc(date)
        if isinstance(location, slice):
            location = location.start
        if date in rebalances:
            history = prices.iloc[max(0, int(location) - config.lookback):int(location)]
            if len(history) < config.lookback:
                continue
            if mode == "quantitative_only":
                result = PortfolioOptimizer(history).optimize(
                    risk_free_rate=config.risk_free_rate,
                    min_weight=config.min_weight,
                    max_weight=config.max_weight,
                )
                target = np.array([result["weights"][ticker] for ticker in config.tickers], dtype=float)
            elif mode == "equal_weight":
                target = np.repeat(1.0 / n, n)
            else:
                raise ValueError(f"Unsupported mode: {mode}")
            target = target / target.sum()
            turnover = float(np.abs(target - weights).sum())
            cost = nav * turnover * config.transaction_cost
            nav -= cost
            total_turnover += turnover
            total_cost += cost
            weights = target
            weight_log.append({
                "date": date.strftime("%Y-%m-%d"),
                "strategy": mode,
                "turnover": turnover,
                **{ticker: float(weight) for ticker, weight in zip(config.tickers, weights)},
            })
        daily = returns.loc[date, config.tickers]
        if daily.isna().any():
            continue
        gross = 1.0 + float(np.dot(weights, daily.to_numpy(dtype=float)))
        nav *= gross
        if gross > 0:
            weights = weights * (1.0 + daily.to_numpy(dtype=float)) / gross
            weights = weights / weights.sum()
        nav_rows.append((date, nav))

    series = pd.Series(dict(nav_rows), name=mode, dtype=float).sort_index()
    if series.empty:
        raise RuntimeError(f"No NAV observations produced for {mode}.")
    return series, total_turnover, total_cost, weight_log


def benchmark_nav(benchmark: pd.Series, config: Config, index: pd.Index) -> pd.Series:
    date_index = pd.DatetimeIndex(index)
    aligned = benchmark.reindex(date_index).ffill().dropna()
    if aligned.empty:
        raise RuntimeError("Benchmark could not be aligned to the strategy dates.")
    return (aligned / aligned.iloc[0] * config.initial_capital).rename("benchmark")


def metrics(nav: pd.Series, risk_free_rate: float, turnover: float = 0.0, total_cost: float = 0.0) -> dict[str, float | int]:
    nav = nav.dropna()
    daily = nav.pct_change(fill_method=None).dropna()
    elapsed_years = max((nav.index[-1] - nav.index[0]).days / 365.25, len(daily) / TRADING_DAYS)
    cagr = float((nav.iloc[-1] / nav.iloc[0]) ** (1.0 / elapsed_years) - 1.0) if elapsed_years > 0 else 0.0
    volatility = float(daily.std(ddof=1) * math.sqrt(TRADING_DAYS)) if len(daily) > 1 else 0.0
    annual_return = float(daily.mean() * TRADING_DAYS) if len(daily) else 0.0
    sharpe = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0.0
    downside = daily[daily < 0]
    downside_vol = float(downside.std(ddof=1) * math.sqrt(TRADING_DAYS)) if len(downside) > 1 else 0.0
    sortino = (annual_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0.0
    drawdown = nav / nav.cummax() - 1.0
    max_drawdown = float(drawdown.min())
    return {
        "start_nav": float(nav.iloc[0]),
        "end_nav": float(nav.iloc[-1]),
        "observations": int(len(nav)),
        "elapsed_years": float(elapsed_years),
        "cagr": cagr,
        "annualized_volatility": volatility,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "maximum_drawdown": max_drawdown,
        "annual_turnover": float(turnover / elapsed_years) if elapsed_years > 0 else 0.0,
        "transaction_cost_drag": float(total_cost / nav.iloc[0]),
        "total_transaction_cost": float(total_cost),
    }


def main() -> None:
    args = parse_args()
    config = Config(
        tickers=[ticker.upper() for ticker in args.tickers],
        benchmark=args.benchmark,
        start=args.start,
        end=args.end,
        lookback=args.lookback,
        risk_free_rate=args.risk_free_rate,
        transaction_cost=args.transaction_cost,
        min_weight=args.min_weight,
        max_weight=args.max_weight,
        initial_capital=args.initial_capital,
    )
    if config.start >= config.end:
        raise ValueError("--start must be earlier than --end")
    if config.lookback < 60:
        raise ValueError("--lookback must be at least 60 trading days")
    if len(config.tickers) < 2:
        raise ValueError("Provide at least two tickers")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prices, benchmark_prices = download_prices(config)
    quant_nav, quant_turnover, quant_cost, quant_weights = run_strategy(prices, config, "quantitative_only")
    equal_nav, equal_turnover, equal_cost, equal_weights = run_strategy(prices, config, "equal_weight")
    shared_index = quant_nav.index.intersection(equal_nav.index)
    quant_nav = quant_nav.reindex(shared_index)
    equal_nav = equal_nav.reindex(shared_index)
    bench_nav = benchmark_nav(benchmark_prices, config, shared_index)
    common = shared_index.intersection(bench_nav.index)
    nav_frame = pd.concat([quant_nav.reindex(common), equal_nav.reindex(common), bench_nav.reindex(common)], axis=1).dropna()
    # Normalize all strategies to the same initial capital after final alignment.
    nav_frame = nav_frame.div(nav_frame.iloc[0]).mul(config.initial_capital)
    summary = {
        "status": "completed_price_only",
        "axiom_combined_status": "not_measured_point_in_time_historical_news_unavailable",
        "config": asdict(config),
        "data": {
            "first_date": nav_frame.index[0].strftime("%Y-%m-%d"),
            "last_date": nav_frame.index[-1].strftime("%Y-%m-%d"),
            "observations": int(len(nav_frame)),
        },
        "strategies": {
            "quantitative_only": metrics(nav_frame["quantitative_only"], config.risk_free_rate, quant_turnover, quant_cost),
            "equal_weight": metrics(nav_frame["equal_weight"], config.risk_free_rate, equal_turnover, equal_cost),
            "benchmark": metrics(nav_frame["benchmark"], config.risk_free_rate),
        },
    }
    nav_frame.index.name = "date"
    nav_frame.to_csv(output / "daily_nav.csv")
    nav_frame.resample("ME").last().dropna(how="all").to_csv(output / "monthly_nav.csv")
    pd.DataFrame(quant_weights + equal_weights).to_csv(output / "portfolio_weights.csv", index=False)
    (output / "backtest_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved results to: {output.resolve()}")


if __name__ == "__main__":
    main()
