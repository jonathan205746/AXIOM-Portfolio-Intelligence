"""
risk.py
-------
Risk analysis module for the portfolio optimizer.

Computes:
- Annualized volatility per ticker + portfolio
- Value at Risk (VaR) — historical and parametric
- Maximum Drawdown
- Correlation matrix
- Beta vs market (SPY as proxy)
- Risk-adjusted return metrics

Usage:
    from src.optimization.risk import RiskAnalyzer
    analyzer = RiskAnalyzer(price_data, currency="INR")
    report = analyzer.full_risk_report(weights)
    print(report)
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional
from typing import cast

# ── Constants ─────────────────────────────────────────────────────────────────

TRADING_DAYS = 252
CONFIDENCE_95 = 0.05    # 5% tail → 95% VaR
CONFIDENCE_99 = 0.01    # 1% tail → 99% VaR


# ── Risk Analyzer ─────────────────────────────────────────────────────────────

class RiskAnalyzer:
    """
    Computes portfolio and individual stock risk metrics.

    Args:
        price_data: DataFrame of closing prices
                    Rows = dates, Columns = ticker symbols
        market_data: Optional DataFrame with market index (SPY) prices
                     Used for Beta calculation. If None, Beta is skipped.
        currency: Portfolio currency code (e.g. "USD", "INR").
                  Used only for display symbols in interpretation strings.
    """

    def __init__(self, price_data: pd.DataFrame, market_data: Optional[pd.DataFrame] = None, currency: str = "USD"):
        self.price_data = price_data
        self.price_data = self.price_data.loc[:, ~self.price_data.columns.duplicated()]
        self.tickers = list(self.price_data.columns)
        self.returns = price_data.pct_change(fill_method=None).dropna()
        self.market_data = market_data
        self.market_returns = (
            market_data.pct_change(fill_method=None).dropna()
            if market_data is not None else None
        )
        self.currency = currency.upper()
        self.currency_symbol = "₹" if self.currency == "INR" else "$"
        print(f"[RiskAnalyzer] Initialized with {len(self.tickers)} assets.")
        print(f"  Return periods: {len(self.returns)}")
        print(f"  Currency: {self.currency} ({self.currency_symbol})")

    # ── Volatility ────────────────────────────────────────────────────────────

    def annualized_volatility(self) -> dict:
        """
        Annualized volatility per ticker.
        Formula: std(daily_returns) * sqrt(252)
        """
        vol = self.returns.std() * np.sqrt(TRADING_DAYS)
        return {ticker: round(float(v), 6) for ticker, v in vol.items()}

    def portfolio_volatility(self, weights: dict) -> float:
        """
        Portfolio-level annualized volatility (accounts for correlation).

        Args:
            weights: dict {ticker: weight}

        Returns:
            Annualized portfolio volatility (decimal)
        """
        w = np.array([weights.get(t, 0) for t in self.tickers])
        cov = self.returns.cov() * TRADING_DAYS
        variance = np.dot(w.T, np.dot(cov.values, w))
        return round(float(np.sqrt(variance)), 6)

    # ── Value at Risk ─────────────────────────────────────────────────────────

    def historical_var(self, weights: dict, confidence: float = 0.95,
                       portfolio_value: float = 100_000) -> dict:
        """
        Historical VaR — uses actual return distribution.

        Interpretation: With X% confidence, the portfolio will NOT lose
        more than the VaR amount in a single day.

        Args:
            weights: dict {ticker: weight}
            confidence: 0.95 = 95% VaR, 0.99 = 99% VaR
            portfolio_value: portfolio size in local currency (default 100,000)

        Returns:
            dict with var_pct and var_amount
        """
        w = np.array([weights.get(t, 0) for t in self.tickers])
        portfolio_returns = self.returns.values @ w

        alpha = 1 - confidence
        var_pct = float(np.percentile(portfolio_returns, alpha * 100))
        var_amount = abs(var_pct) * portfolio_value
        sym = self.currency_symbol

        return {
            "method": "historical",
            "confidence": confidence,
            "var_pct": round(var_pct, 6),         # negative = loss
            "var_usd": round(var_amount, 2),      # key kept for backward compat
            "var_amount": round(var_amount, 2),   # currency-agnostic key
            "interpretation": (
                    f"With {int(confidence*100)}% confidence, max 1-day loss = "
                    f"{sym}{var_amount:,.0f} ({abs(var_pct)*100:.2f}%)"
            )
        }

    def parametric_var(self, weights: dict, confidence: float = 0.95,
                       portfolio_value: float = 100_000) -> dict:
        """
        Parametric VaR — assumes normal distribution of returns.
        Formula: VaR = -(mean + z_score * std) * portfolio_value

        Args:
            weights: dict {ticker: weight}
            confidence: 0.95 or 0.99
            portfolio_value: local currency

        Returns:
            dict with var_pct and var_amount
        """
        w = np.array([weights.get(t, 0) for t in self.tickers])
        portfolio_returns = self.returns.values @ w

        mean = portfolio_returns.mean()
        std = portfolio_returns.std()
        z_score = stats.norm.ppf(1 - confidence)

        var_pct = mean + z_score * std   # Will be negative (loss)
        var_amount = abs(var_pct) * portfolio_value
        sym = self.currency_symbol

        return {
            "method": "parametric",
            "confidence": confidence,
            "var_pct": round(var_pct, 6),
            "var_usd": round(var_amount, 2),
            "var_amount": round(var_amount, 2),
            "interpretation": (
                f"Parametric {int(confidence*100)}% 1-day VaR = "
                f"{sym}{var_amount:,.0f} ({abs(var_pct)*100:.2f}%)"
            )
        }

    # ── Drawdown ──────────────────────────────────────────────────────────────

    def max_drawdown(self, weights: Optional[dict] = None) -> dict:
        """
        Maximum Drawdown — largest peak-to-trough decline.

        If weights provided: computes portfolio-level drawdown.
        If None: computes per-ticker drawdown.

        Args:
            weights: dict {ticker: weight} or None for per-ticker

        Returns:
            dict with max_drawdown_pct and drawdown series
        """
        if weights:
            # Portfolio-level
            w = np.array([weights.get(t, 0) for t in self.tickers])
            port_returns = pd.Series(self.returns.values @ w, index=self.returns.index)
            cumulative = (1 + port_returns).cumprod()
            rolling_max = cumulative.cummax()
            drawdown = (cumulative - rolling_max) / rolling_max
            mdd = float(drawdown.min())

            return {
                "scope": "portfolio",
                "max_drawdown_pct": round(mdd * 100, 4),
                "max_drawdown_decimal": round(mdd, 6),
                "interpretation": f"Worst peak-to-trough drop: {mdd*100:.2f}%"
            }

        else:
            # Per-ticker
            results = {}
            for ticker in self.tickers:
                cumulative = (1 + self.returns[ticker]).cumprod()  
                rolling_max = cumulative.cummax()
                drawdown = (cumulative - rolling_max) / rolling_max
                mdd = float(drawdown.min())
                results[ticker] = round(mdd * 100, 4)
            return results

    # ── Correlation ───────────────────────────────────────────────────────────

    def correlation_matrix(self) -> pd.DataFrame:
        """
        Return correlation matrix of daily returns.
        Values close to 1.0 = highly correlated (less diversification benefit).
        """
        return self.returns.corr().round(4)

    def high_correlation_pairs(self, threshold: float = 0.8) -> list:
        """
        Find pairs of tickers with correlation above threshold.
        High correlation = concentrated risk.

        Returns:
            List of tuples: (ticker1, ticker2, correlation)
        """
        corr = self.correlation_matrix()
        pairs = []
        for i, t1 in enumerate(self.tickers):
            for j, t2 in enumerate(self.tickers):
                if i < j:
                    val = cast(float, corr.at[t1, t2])
                    if abs(val) >= threshold:
                        pairs.append((t1, t2, round((val), 4)))
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)

    # ── Beta ──────────────────────────────────────────────────────────────────

    def beta(self) -> Optional[dict]:
        """
        Compute Beta for each ticker vs market (SPY).
        Beta > 1 = more volatile than market.
        Beta < 1 = less volatile.
        Beta < 0 = inverse to market (rare for large caps).

        Returns None if market_data was not provided.
        """
        if self.market_returns is None:
            return None

        # Align dates
        market_col = self.market_returns.columns[0]
        market = self.market_returns[market_col]

        betas = {}
        for ticker in self.tickers:
            if ticker not in self.returns.columns:
                continue
            # Align
            aligned = pd.concat([self.returns[ticker], market], axis=1).dropna()
            aligned.columns = ["stock", "market"]
            
            cov = cast(float, aligned.cov().at["stock", "market"])
            var = cast(float, aligned["market"].var())
            beta_val = cov / var if var != 0.0 else 0.0
            betas[ticker] = round(float(beta_val), 4)

        return betas


    # ── Downside / Tail Risk v3 ───────────────────────────────────────────────

    def sortino_ratio(self, weights: dict, target_return: float = 0.0) -> float:
        """Annualized Sortino ratio using downside deviation only."""
        w = np.array([weights.get(t, 0.0) for t in self.tickers], dtype=float)
        port = self.returns.values @ w
        if len(port) == 0:
            return 0.0
        daily_target = target_return / TRADING_DAYS
        downside = np.minimum(port - daily_target, 0.0)
        downside_dev = float(np.sqrt(np.mean(downside ** 2)) * np.sqrt(TRADING_DAYS))
        annual_return = float(np.mean(port) * TRADING_DAYS)
        if downside_dev <= 1e-12:
            return 0.0
        return round((annual_return - target_return) / downside_dev, 6)

    def expected_shortfall(self, weights: dict, confidence: float = 0.95,
                           portfolio_value: float = 100_000) -> dict:
        """Historical Expected Shortfall / CVaR beyond the VaR threshold."""
        w = np.array([weights.get(t, 0.0) for t in self.tickers], dtype=float)
        port = self.returns.values @ w
        if len(port) == 0:
            es_pct = 0.0
        else:
            cutoff = float(np.percentile(port, (1.0 - confidence) * 100.0))
            tail = port[port <= cutoff]
            es_pct = float(np.mean(tail)) if len(tail) else cutoff
        amount = abs(es_pct) * portfolio_value
        return {
            "method": "historical_expected_shortfall",
            "confidence": confidence,
            "es_pct": round(es_pct, 6),
            "es_amount": round(amount, 2),
            "interpretation": (
                f"Average loss in the worst {(1-confidence)*100:.0f}% of days = "
                f"{self.currency_symbol}{amount:,.0f} ({abs(es_pct)*100:.2f}%)"
            ),
        }

    # ── Concentration Risk ────────────────────────────────────────────────────

    def concentration_risk(self, weights: dict) -> dict:
        """
        Herfindahl-Hirschman Index (HHI) — measures concentration.
        HHI = sum of squared weights
        - HHI = 1/n → perfectly diversified
        - HHI = 1.0 → 100% in one stock

        Args:
            weights: dict {ticker: weight}

        Returns:
            dict with HHI score and risk label
        """
        w = np.array(list(weights.values()))
        hhi = float(np.sum(w ** 2))
        min_hhi = 1.0 / len(self.tickers)  # perfectly diversified

        if hhi < 0.15:
            label = "Well Diversified"
        elif hhi < 0.25:
            label = "Moderate Concentration"
        else:
            label = "High Concentration"

        return {
            "hhi": round(hhi, 6),
            "min_possible_hhi": round(min_hhi, 6),
            "label": label,
            "interpretation": f"HHI={hhi:.3f} ({label}) | min={min_hhi:.3f}"
        }

    # ── Full Report ───────────────────────────────────────────────────────────

    def full_risk_report(self, weights: dict, portfolio_value: float = 100_000) -> dict:
        """
        Generate complete risk report for a portfolio.

        Args:
            weights: dict {ticker: weight} — must sum to 1.0
            portfolio_value: value of portfolio in local currency

        Returns:
            dict with all risk metrics
        """
        print(f"\n[RiskAnalyzer] Generating full risk report...")

        vol_per_ticker = self.annualized_volatility()
        port_vol = self.portfolio_volatility(weights)
        hist_var_95 = self.historical_var(weights, 0.95, portfolio_value)
        hist_var_99 = self.historical_var(weights, 0.99, portfolio_value)
        param_var_95 = self.parametric_var(weights, 0.95, portfolio_value)
        mdd_portfolio = self.max_drawdown(weights)
        mdd_tickers = self.max_drawdown()
        corr = self.correlation_matrix()
        high_corr = self.high_correlation_pairs(threshold=0.8)
        concentration = self.concentration_risk(weights)
        sortino = self.sortino_ratio(weights)
        es95 = self.expected_shortfall(weights, 0.95, portfolio_value)

        report = {
            "volatility": {
                "per_ticker_annualized": vol_per_ticker,
                "portfolio_annualized": port_vol
            },
            "value_at_risk": {
                "historical_95": hist_var_95,
                "historical_99": hist_var_99,
                "parametric_95": param_var_95
            },
            "drawdown": {
                "portfolio": mdd_portfolio,
                "per_ticker": mdd_tickers
            },
            "correlation": {
                "matrix": corr.to_dict(),
                "high_correlation_pairs": high_corr
            },
            "concentration": concentration,
            "downside": {"sortino_ratio": sortino},
            "tail_risk": {"expected_shortfall_95": es95}
        }

        # Print summary
        print(f"  Portfolio Volatility : {port_vol*100:.2f}%")
        print(f"  Historical 95% VaR   : {hist_var_95['interpretation']}")
        print(f"  Historical 99% VaR   : {hist_var_99['interpretation']}")
        print(f"  Max Drawdown         : {mdd_portfolio['max_drawdown_pct']:.2f}%")
        print(f"  Concentration (HHI)  : {concentration['interpretation']}")
        print(f"  Sortino Ratio        : {sortino:.4f}")
        print(f"  Expected Shortfall   : {es95['interpretation']}")
        if high_corr:
            print(f"  High Corr Pairs      : {high_corr}")
        else:
            print(f"  High Corr Pairs      : None above 0.8 threshold ✅")

        return report


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("RISK ANALYZER TEST")
    print("=" * 60)

    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

    from src.data.stock_fetcher import fetch_stock_data

    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    print(f"\nFetching real price data for: {tickers}")
    prices = fetch_stock_data(tickers)

    if isinstance(prices.columns, pd.MultiIndex):
        prices = prices["Close"]

    # Sample weights — in real pipeline these come from portfolio.py
    weights = {"AAPL": 0.35, "MSFT": 0.30, "GOOGL": 0.20, "AMZN": 0.15}
    print(f"\nWeights: {weights}")
    print(f"Weights sum: {sum(weights.values()):.1f}")

    if isinstance(prices.columns, pd.MultiIndex):
        prices = prices["Close"]

    prices = prices if isinstance(prices, pd.DataFrame) else prices.to_frame()
    analyzer = RiskAnalyzer(prices, currency="INR")
    report = analyzer.full_risk_report(weights, portfolio_value=100_000)

    print("\n" + "─" * 40)
    print("Per-ticker Volatility:")
    for t, v in report["volatility"]["per_ticker_annualized"].items():
        print(f"  {t}: {v*100:.2f}%")

    print("\nPer-ticker Max Drawdown:")
    for t, mdd in report["drawdown"]["per_ticker"].items():
        print(f"  {t}: {mdd:.2f}%")

    print(f"\nCorrelation Matrix:")
    print(pd.DataFrame(report["correlation"]["matrix"]).round(3))

    print("\n✅ Risk analysis working.")
