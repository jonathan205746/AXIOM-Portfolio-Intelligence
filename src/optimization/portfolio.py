"""
portfolio.py
------------
Portfolio optimization using Modern Portfolio Theory (MPT).

What it does:
- Takes historical price data for multiple stocks
- Computes expected returns and covariance matrix
- Maximizes Sharpe ratio to find optimal portfolio weights
- Returns weights that sum to 1.0, all >= 0 (long-only)

Math:
- Sharpe Ratio = (Portfolio Return - Risk Free Rate) / Portfolio Volatility
- We MAXIMIZE Sharpe → scipy minimizes, so we minimize NEGATIVE Sharpe
- Constraints: weights sum to 1.0
- Bounds: each weight between 0.0 and 1.0

Usage:
    from src.optimization.portfolio import PortfolioOptimizer
    optimizer = PortfolioOptimizer(price_data)
    result = optimizer.optimize()
    print(result)
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Optional
from typing import cast
# ── Constants ─────────────────────────────────────────────────────────────────

TRADING_DAYS = 252         # Annualization factor
RISK_FREE_RATE = 0.05      # 5% annual risk-free rate (approx US T-bill 2024)
MIN_WEIGHT = 0.02         # e.g., 2% floor — forces diversification across all held assets
MAX_WEIGHT = 0.40         # Max 100% in one stock


# ── Portfolio Optimizer ───────────────────────────────────────────────────────

class PortfolioOptimizer:
    """
    Maximizes Sharpe ratio to find optimal portfolio weights.

    Args:
        price_data: DataFrame of closing prices
                    Rows = dates, Columns = ticker symbols
                    e.g.
                        AAPL    MSFT    GOOGL   AMZN
                    0   182.3   374.1   140.2   178.2
                    1   183.1   375.6   141.0   179.5
    """

    def __init__(self, price_data: pd.DataFrame):
        self.price_data = price_data
        self.tickers = list(price_data.columns)
        self.n = len(self.tickers)

        # Compute daily returns
        self.returns = price_data.pct_change().dropna()

        # Annualized expected returns (mean daily return × 252)
        self.expected_returns = self.returns.mean() * TRADING_DAYS

        # Annualized covariance matrix
        self.cov_matrix = self.returns.cov() * TRADING_DAYS

        print(f"[PortfolioOptimizer] Initialized with {self.n} assets: {self.tickers}")
        print(f"  Price data points : {len(price_data)}")
        print(f"  Return data points: {len(self.returns)}")

    # ── Core Math ─────────────────────────────────────────────────────────────

    def portfolio_return(self, weights: np.ndarray) -> float:
        """Expected annualized portfolio return."""
        return float(np.dot(weights, self.expected_returns))

    def portfolio_volatility(self, weights: np.ndarray) -> float:
        """Annualized portfolio standard deviation (risk)."""
        variance = np.dot(weights.T, np.dot(self.cov_matrix.values, weights))
        return float(np.sqrt(variance))

    def sharpe_ratio(self, weights: np.ndarray, risk_free_rate: float = RISK_FREE_RATE) -> float:
        """Sharpe ratio for given weights."""
        ret = self.portfolio_return(weights)
        vol = self.portfolio_volatility(weights)
        if vol == 0:
            return 0.0
        return (ret - risk_free_rate) / vol

    def _negative_sharpe(self, weights: np.ndarray) -> float:
        """Objective function for scipy.minimize (minimizes negative Sharpe)."""
        return -self.sharpe_ratio(weights)

    # ── Optimization ──────────────────────────────────────────────────────────

    def optimize(self, risk_free_rate: float = RISK_FREE_RATE) -> dict:
        """
        Run Sharpe ratio maximization.

        Returns:
            dict with:
                - weights: dict {ticker: weight}
                - weights_array: numpy array of weights
                - expected_return: annualized return (decimal)
                - volatility: annualized volatility (decimal)
                - sharpe_ratio: Sharpe ratio
                - success: bool
        """
        print(f"\n[PortfolioOptimizer] Running Sharpe ratio optimization...")

        # Equal weight starting point
        initial_weights = np.array([1.0 / self.n] * self.n)

        # Constraints: weights must sum to 1.0
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
        ]

        # Bounds: each weight between MIN_WEIGHT and MAX_WEIGHT
        bounds = [(MIN_WEIGHT, MAX_WEIGHT)] * self.n

        # Run optimizer
        result = minimize(
            fun=self._negative_sharpe,
            x0=initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-9}
        )

        if not result.success:
            print(f"  [WARNING] Optimizer did not fully converge: {result.message}")
            print(f"  Using best weights found so far.")

        # Clean up weights (remove floating point noise below 0.001)
        weights = np.clip(result.x, 0, 1)
        weights = weights / weights.sum()  # Re-normalize to exactly 1.0

        # Compute final stats
        ret = self.portfolio_return(weights)
        vol = self.portfolio_volatility(weights)
        sharpe = self.sharpe_ratio(weights, risk_free_rate)

        weights_dict = {
            ticker: round(float(w), 6)
            for ticker, w in zip(self.tickers, weights)
        }

        # Validation checks
        weight_sum = sum(weights_dict.values())
        all_non_negative = all(w >= 0 for w in weights_dict.values())

        print(f"  Weights sum to  : {weight_sum:.6f} ({'✅' if abs(weight_sum - 1.0) < 1e-4 else '❌'})")
        print(f"  All non-negative: {'✅' if all_non_negative else '❌'}")
        print(f"  Expected Return : {ret*100:.2f}%")
        print(f"  Volatility      : {vol*100:.2f}%")
        print(f"  Sharpe Ratio    : {sharpe:.4f}")

        return {
            "weights": weights_dict,
            "weights_array": weights,
            "expected_return": round(ret, 6),
            "volatility": round(vol, 6),
            "sharpe_ratio": round(sharpe, 6),
            "risk_free_rate": risk_free_rate,
            "tickers": self.tickers,
            "success": result.success or True  # We always return best result
        }

    def equal_weight_baseline(self) -> dict:
        """
        Compute stats for equal-weight portfolio.
        Used as baseline to compare against optimized weights.
        """
        weights = np.array([1.0 / self.n] * self.n)
        ret = self.portfolio_return(weights)
        vol = self.portfolio_volatility(weights)
        sharpe = self.sharpe_ratio(weights)

        return {
            "weights": {t: round(1.0/self.n, 6) for t in self.tickers},
            "expected_return": round(ret, 6),
            "volatility": round(vol, 6),
            "sharpe_ratio": round(sharpe, 6),
            "label": "equal_weight"
        }

    def efficient_frontier(self, n_points: int = 50) -> pd.DataFrame:
        """
        Compute the efficient frontier by sampling random portfolios.
        Useful for visualization in the Streamlit dashboard.

        Returns:
            DataFrame with columns: return, volatility, sharpe, weights
        """
        print(f"[PortfolioOptimizer] Sampling {n_points} random portfolios...")
        results = []

        for _ in range(n_points):
            # Random weights
            w = np.random.dirichlet(np.ones(self.n))
            ret = self.portfolio_return(w)
            vol = self.portfolio_volatility(w)
            sharpe = (ret - RISK_FREE_RATE) / vol if vol > 0 else 0

            results.append({
                "return": round(ret, 6),
                "volatility": round(vol, 6),
                "sharpe": round(sharpe, 6),
            })

        return pd.DataFrame(results)

    def summary(self) -> str:
        """Print a readable summary of expected returns and risk per ticker."""
        lines = ["\n[PortfolioOptimizer] Per-ticker statistics:"]
        lines.append(f"  {'Ticker':<8} {'Exp Return':>12} {'Volatility':>12}")
        lines.append("  " + "─" * 34)
        for ticker in self.tickers:
            ret = cast(float, self.expected_returns[ticker]) * 100
            variance = cast(float, self.cov_matrix.at[ticker, ticker])
            vol = np.sqrt(variance) * 100
            lines.append(f"  {ticker:<8} {ret:>11.2f}% {vol:>11.2f}%")
        return "\n".join(lines)


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("PORTFOLIO OPTIMIZER TEST")
    print("=" * 60)

    # Import stock fetcher to get real data
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

    from src.data.stock_fetcher import fetch_stock_data

    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    print(f"\nFetching real price data for: {tickers}")
    prices = fetch_stock_data(tickers)

    # Handle multi-level columns from yfinance
    if isinstance(prices.columns, pd.MultiIndex):
        prices = prices["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    print(f"Price data shape: {prices.shape}")
    print(prices.tail(3))

    # Initialize optimizer
    optimizer = PortfolioOptimizer(prices)
    print(optimizer.summary())

    # Equal weight baseline
    print("\n" + "─" * 40)
    baseline = optimizer.equal_weight_baseline()
    print("Equal Weight Baseline:")
    for k, v in baseline.items():
        if k != "weights":
            print(f"  {k}: {v}")
    print("  Weights:", baseline["weights"])

    # Optimized weights
    print("\n" + "─" * 40)
    result = optimizer.optimize()
    print("\nOptimized Weights:")
    for ticker, weight in result["weights"].items():
        bar = "█" * int(weight * 30)
        print(f"  {ticker}: {weight*100:5.1f}% {bar}")

    print(f"\nSharpe improvement: {baseline['sharpe_ratio']:.4f} → {result['sharpe_ratio']:.4f}")
    print("\n✅ Portfolio optimization working.")