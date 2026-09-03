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
    parser.add_argument(
        "--tickers", nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    )
    parser.add_argument("--benchmark", default="^GSPC")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--lookback", type=int, default=252)
    parser.add_argument("--risk-free-rate", type=float, default=0.05)
    parser.add_argument(
        "--transaction-cost",
        type=float,
        default=0.0015,
        help="Cost per traded notional; 0.0015 = 15 bps",
    )
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
    download_start = requested_start - timedelta(
        days=max(550, int(config.lookback * 2.2))
    )
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
    benchmark = _close_frame(raw_benchmark, [config.benchmark])[
        config.benchmark
    ].dropna()
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
) -> tuple[pd.DataFrame, float, float, list[dict[str, Any]]]:
    returns = prices.pct_change(fill_method=None)
    requested_start = pd.Timestamp(config.start)
    requested_end = pd.Timestamp(config.end)
    dates = prices.index[
        (prices.index >= requested_start) & (prices.index <= requested_end)
    ]
    if len(dates) < 2:
        raise RuntimeError(
            "Not enough observations in the requested evaluation window."
        )
    rebalances = rebalance_dates(pd.DatetimeIndex(dates), requested_start)
    n = len(config.tickers)
    weights: np.ndarray | None = None
    gross_nav = config.initial_capital
    net_nav = config.initial_capital
    nav_rows: list[tuple[pd.Timestamp, float, float]] = []
    total_turnover = 0.0
    total_cost = 0.0
    weight_log: list[dict[str, Any]] = []

    for date in dates:
        location = prices.index.get_loc(date)
        if isinstance(location, slice):
            location = location.start
        if date in rebalances:
            history = prices.iloc[
                max(0, int(location) - config.lookback) : int(location)
            ]
            if len(history) < config.lookback:
                continue
            if mode == "quantitative_only":
                result = PortfolioOptimizer(history).optimize(
                    risk_free_rate=config.risk_free_rate,
                    min_weight=config.min_weight,
                    max_weight=config.max_weight,
                )
                target = np.array(
                    [result["weights"][ticker] for ticker in config.tickers],
                    dtype=float,
                )
            elif mode == "equal_weight":
                target = np.repeat(1.0 / n, n)
            else:
                raise ValueError(f"Unsupported mode: {mode}")
            target = target / target.sum()
            initial_establishment = weights is None
            if initial_establishment:
                # Initial deployment is the common starting condition, not a
                # rebalance. It is excluded from turnover and modeled costs.
                traded_notional = 0.0
                reported_turnover = 0.0
                cost = 0.0
            else:
                # Complete bought-and-sold notional; one-way turnover is half.
                traded_notional = float(np.abs(target - weights).sum())
                reported_turnover = 0.5 * traded_notional
                cost = net_nav * traded_notional * config.transaction_cost
                net_nav -= cost
                total_turnover += reported_turnover
                total_cost += cost

            weights = target
            weight_log.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "strategy": mode,
                    "initial_establishment": initial_establishment,
                    "reported_turnover": reported_turnover,
                    "traded_notional": traded_notional,
                    "transaction_cost": cost,
                    **{
                        ticker: float(weight)
                        for ticker, weight in zip(
                            config.tickers,
                            weights if weights is not None else [],
                        )
                    },
                }
            )

            if initial_establishment:
                # The first eligible close is the common NAV baseline. Returns
                # begin on the following observation.
                nav_rows.append((date, gross_nav, net_nav))
                continue

        if weights is None:
            continue

        daily = returns.loc[date, config.tickers]
        if daily.isna().any():
            continue
        growth_factor = 1.0 + float(np.dot(weights, daily.to_numpy(dtype=float)))
        gross_nav *= growth_factor
        net_nav *= growth_factor
        if growth_factor > 0:
            weights = weights * (1.0 + daily.to_numpy(dtype=float)) / growth_factor
            weights = weights / weights.sum()
        nav_rows.append((date, gross_nav, net_nav))

    frame = (
        pd.DataFrame(
            nav_rows,
            columns=["date", "gross", "net"],
        )
        .set_index("date")
        .sort_index()
    )
    if frame.empty:
        raise RuntimeError(f"No NAV observations produced for {mode}.")
    return frame, total_turnover, total_cost, weight_log


def benchmark_nav(benchmark: pd.Series, config: Config, index: pd.Index) -> pd.Series:
    date_index = pd.DatetimeIndex(index)
    aligned = benchmark.reindex(date_index).dropna()
    if aligned.empty:
        raise RuntimeError("Benchmark could not be aligned to the strategy dates.")
    return (aligned / aligned.iloc[0] * config.initial_capital).rename("benchmark")


def metrics(
    nav: pd.Series,
    risk_free_rate: float,
) -> dict[str, float | int]:
    nav = nav.dropna()
    daily = nav.pct_change(fill_method=None).dropna()
    elapsed_years = (nav.index[-1] - nav.index[0]).days / 365.25
    cagr = (
        float((nav.iloc[-1] / nav.iloc[0]) ** (1.0 / elapsed_years) - 1.0)
        if elapsed_years > 0
        else 0.0
    )
    volatility = (
        float(daily.std(ddof=1) * math.sqrt(TRADING_DAYS)) if len(daily) > 1 else 0.0
    )
    daily_risk_free = (1.0 + risk_free_rate) ** (1.0 / TRADING_DAYS) - 1.0
    excess = daily - daily_risk_free
    sharpe = (
        float(excess.mean() / daily.std(ddof=1) * math.sqrt(TRADING_DAYS))
        if len(daily) > 1 and daily.std(ddof=1) > 0
        else 0.0
    )
    downside = np.minimum(excess.to_numpy(dtype=float), 0.0)
    downside_deviation = (
        float(np.sqrt(np.mean(np.square(downside))) * math.sqrt(TRADING_DAYS))
        if len(downside)
        else 0.0
    )
    annualized_excess = float(excess.mean() * TRADING_DAYS) if len(excess) else 0.0
    sortino = annualized_excess / downside_deviation if downside_deviation > 0 else 0.0
    drawdown = nav / nav.cummax() - 1.0
    max_drawdown = float(drawdown.min())
    return {
        "start_nav": float(nav.iloc[0]),
        "end_nav": float(nav.iloc[-1]),
        "observations": int(len(nav)),
        "elapsed_years": float(elapsed_years),
        "total_return": float(nav.iloc[-1] / nav.iloc[0] - 1.0),
        "cagr": cagr,
        "annualized_volatility": volatility,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "maximum_drawdown": max_drawdown,
    }


def strategy_summary(
    nav: pd.DataFrame,
    config: Config,
    turnover: float,
    total_cost: float,
) -> dict[str, Any]:
    gross = metrics(nav["gross"], config.risk_free_rate)
    net = metrics(nav["net"], config.risk_free_rate)
    elapsed_years = float(net["elapsed_years"])
    return {
        "gross": gross,
        "net": net,
        "implementation": {
            "turnover_convention": "one_way_half_absolute_weight_change",
            "initial_establishment_included": False,
            "total_turnover": float(turnover),
            "annual_turnover": (
                float(turnover / elapsed_years) if elapsed_years > 0 else 0.0
            ),
            "total_transaction_cost": float(total_cost),
            "transaction_cost_pct_initial": float(total_cost / config.initial_capital),
            "terminal_return_cost_drag": float(
                gross["total_return"] - net["total_return"]
            ),
            "cagr_cost_drag": float(gross["cagr"] - net["cagr"]),
        },
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
    quant_nav, quant_turnover, quant_cost, quant_weights = run_strategy(
        prices, config, "quantitative_only"
    )
    equal_nav, equal_turnover, equal_cost, equal_weights = run_strategy(
        prices, config, "equal_weight"
    )
    shared_index = quant_nav.index.intersection(equal_nav.index)
    bench_nav = benchmark_nav(benchmark_prices, config, shared_index)
    common = shared_index.intersection(bench_nav.index)
    nav_frame = pd.concat(
        [
            quant_nav["gross"].reindex(common).rename("quantitative_only_gross"),
            quant_nav["net"].reindex(common).rename("quantitative_only_net"),
            equal_nav["gross"].reindex(common).rename("equal_weight_gross"),
            equal_nav["net"].reindex(common).rename("equal_weight_net"),
            bench_nav.reindex(common),
        ],
        axis=1,
    ).dropna()
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
            "quantitative_only": strategy_summary(
                nav_frame[["quantitative_only_gross", "quantitative_only_net"]].rename(
                    columns={
                        "quantitative_only_gross": "gross",
                        "quantitative_only_net": "net",
                    }
                ),
                config,
                quant_turnover,
                quant_cost,
            ),
            "equal_weight": strategy_summary(
                nav_frame[["equal_weight_gross", "equal_weight_net"]].rename(
                    columns={
                        "equal_weight_gross": "gross",
                        "equal_weight_net": "net",
                    }
                ),
                config,
                equal_turnover,
                equal_cost,
            ),
            "benchmark": metrics(nav_frame["benchmark"], config.risk_free_rate),
        },
    }
    nav_frame.index.name = "date"
    nav_frame.to_csv(output / "daily_nav.csv")
    nav_frame.resample("ME").last().dropna(how="all").to_csv(output / "monthly_nav.csv")
    pd.DataFrame(quant_weights + equal_weights).to_csv(
        output / "portfolio_weights.csv", index=False
    )
    (output / "backtest_results.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print(f"\nSaved results to: {output.resolve()}")


if __name__ == "__main__":
    main()
