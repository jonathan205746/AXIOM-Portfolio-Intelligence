"""
test_data.py
Tests for data fetching modules.
Run: pytest tests/
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


class TestStockFetcher:

    def test_fetch_stock_data_returns_dataframe(self):
        """Stock fetcher should return a DataFrame with ticker columns."""
        from src.data.stock_fetcher import fetch_stock_data
        df = fetch_stock_data(["AAPL", "MSFT"], period="1mo")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_fetch_stock_data_has_correct_columns(self):
        """Returned DataFrame should have requested tickers as columns."""
        from src.data.stock_fetcher import fetch_stock_data
        tickers = ["AAPL", "MSFT"]
        df = fetch_stock_data(tickers, period="1mo")
        for ticker in tickers:
            assert ticker in df.columns

    def test_calculate_returns_no_nan(self):
        """Returns DataFrame should not have NaN after dropna."""
        from src.data.stock_fetcher import fetch_stock_data, calculate_returns
        prices = fetch_stock_data(["AAPL", "MSFT"], period="1mo")
        returns = calculate_returns(prices)
        assert not returns.isnull().any().any()

    def test_calculate_returns_range(self):
        """Daily returns should be between -50% and +50% for normal stocks."""
        from src.data.stock_fetcher import fetch_stock_data, calculate_returns
        prices = fetch_stock_data(["AAPL"], period="6mo")
        returns = calculate_returns(prices)
        assert (returns > -0.5).all().all()
        assert (returns < 0.5).all().all()


class TestPortfolioOptimization:

    def test_weights_sum_to_one(self):
        """Optimized weights must sum to 1.0."""
        from src.data.stock_fetcher import fetch_stock_data, calculate_returns
        from src.optimization.portfolio import optimize_portfolio
        prices = fetch_stock_data(["AAPL", "MSFT", "GOOGL"], period="6mo")
        returns = calculate_returns(prices)
        result = optimize_portfolio(returns)
        total_weight = sum(result["weights"].values())
        assert abs(total_weight - 1.0) < 0.001

    def test_weights_non_negative(self):
        """No short selling — all weights must be >= 0."""
        from src.data.stock_fetcher import fetch_stock_data, calculate_returns
        from src.optimization.portfolio import optimize_portfolio
        prices = fetch_stock_data(["AAPL", "MSFT", "GOOGL"], period="6mo")
        returns = calculate_returns(prices)
        result = optimize_portfolio(returns)
        for weight in result["weights"].values():
            assert weight >= 0

    def test_sharpe_ratio_positive(self):
        """Optimized Sharpe ratio should be positive for reasonable stocks."""
        from src.data.stock_fetcher import fetch_stock_data, calculate_returns
        from src.optimization.portfolio import optimize_portfolio
        prices = fetch_stock_data(["AAPL", "MSFT"], period="1y")
        returns = calculate_returns(prices)
        result = optimize_portfolio(returns)
        assert result["sharpe_ratio"] > 0