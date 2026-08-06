"""
stock_fetcher.py
Fetches historical stock price data, company info, and returns.
Uses yfinance — no API key required.

Run this file directly to test:
    python src/data/stock_fetcher.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import logging
import os
import warnings
from pathlib import Path
from requests_cache import CachedSession

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Cached session to avoid YFinance rate limits ──────────────────────────────
# Cache responses for 1 hour. On Railway /tmp is writable.
_cache_dir = os.getenv("YFINANCE_CACHE_DIR", "/tmp/yfinance_cache")
os.makedirs(_cache_dir, exist_ok=True)

_session = CachedSession(
    cache_name=os.path.join(_cache_dir, "yfinance"),
    expire_after=3600,  # 1 hour
    backend="sqlite",
)
_session.headers["User-agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ── Main Functions ─────────────────────────────────────────────────────────────

def fetch_stock_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """
    Fetch historical closing prices for given tickers.

    Args:
        tickers : List of stock symbols e.g. ["AAPL", "MSFT", "GOOGL"]
        period  : Time period — "1mo", "3mo", "6mo", "1y", "2y"

    Returns:
        DataFrame — dates as index, tickers as columns, closing prices as values

    Raises:
        ValueError : If no data returned (invalid ticker or no internet)

    Example:
        prices = fetch_stock_data(["AAPL", "MSFT"], period="6mo")
        print(prices.tail())
    """
    logger.info(f"Fetching price data for {tickers} | period={period}")

    try:
        # Download data — auto_adjust=True adjusts for splits and dividends
        data = yf.download(
            tickers=tickers,
            period=period,
            auto_adjust=True,
            progress=False,
            threads=False,
            session=_session,  # ← uses cache
        )

        if data is None or data.empty:
            raise ValueError(f"No price data returned. Check ticker symbols: {tickers}")

        # Normalize yfinance's output into a clean DataFrame with ticker columns.
        if isinstance(data.columns, pd.MultiIndex):
            # yfinance returns columns like ('Close', 'SPY') for single-ticker requests.
            if len(tickers) == 1:
                close_data = data.xs("Close", axis=1, level=0, drop_level=False)
                if isinstance(close_data, pd.DataFrame) and not close_data.empty:
                    prices = close_data.copy()
                    if prices.columns.nlevels > 1:
                        prices = prices.droplevel(0, axis=1)
                else:
                    raise ValueError(f"No closing price data returned for {tickers[0]}")
            else:
                if "Close" in data.columns.get_level_values(0):
                    prices = data["Close"]
                else:
                    raise ValueError(f"No closing price data returned. Check ticker symbols: {tickers}")
        else:
            # Flat columns such as ['Close', 'High', ...] for single ticker, or a simple DataFrame for one ticker
            if len(tickers) == 1:
                if "Close" in data.columns:
                    prices = data[["Close"]].rename(columns={"Close": tickers[0]})
                elif tickers[0] in data.columns:
                    prices = data[[tickers[0]]]
                else:
                    raise ValueError(f"No closing price data returned for {tickers[0]}")
            else:
                if "Close" in data:
                    prices = data["Close"]
                else:
                    raise ValueError(f"No closing price data returned. Check ticker symbols: {tickers}")

        # Ensure we always return a DataFrame (yfinance may return a Series for a single column)
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()

        if prices.empty:
            raise ValueError(f"No price data returned. Check ticker symbols: {tickers}")

        # Normalize column labels so tuple-shaped yfinance columns are treated as ticker names.
        normalized_columns = []
        for col in prices.columns:
            if isinstance(col, tuple):
                values = [v for v in col if isinstance(v, str)]
                if len(values) >= 2:
                    match = next((v for v in values if v in set(tickers)), None)
                    normalized = match or values[-1]
                elif values:
                    normalized = values[0]
                else:
                    normalized = str(col)
            else:
                normalized = str(col)
            normalized_columns.append(normalized)

        prices = prices.copy()
        prices.columns = normalized_columns

        # Validate data
        valid_tickers = [col for col in prices.columns if prices[col].notna().any()]
        invalid_tickers = [t for t in tickers if t not in valid_tickers]

        if invalid_tickers:
            logger.warning(f"No data found for: {invalid_tickers}. Removing from results.")

        prices = prices[valid_tickers].dropna(how="all")

        logger.info(f"Successfully fetched {len(prices)} rows for {valid_tickers}")
        return prices

    except Exception as e:
        logger.error(f"Error fetching stock data: {e}")
        raise


def fetch_stock_info(ticker: str) -> Dict:
    """
    Fetch company metadata for a single stock.

    Args:
        ticker : Stock symbol e.g. "AAPL"

    Returns:
        Dict with: name, sector, industry, market_cap, description, currency,
                   country, website, employees, pe_ratio, dividend_yield

    Example:
        info = fetch_stock_info("AAPL")
        print(info["name"])  # "Apple Inc."
    """
    logger.info(f"Fetching company info for {ticker}")

    try:
        stock = yf.Ticker(ticker, session=_session)
        info = stock.info

        return {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "country": info.get("country", "Unknown"),
            "market_cap": info.get("marketCap", 0),
            "currency": info.get("currency", "USD"),
            "website": info.get("website", ""),
            "employees": info.get("fullTimeEmployees", 0),
            "pe_ratio": info.get("trailingPE", None),
            "dividend_yield": info.get("dividendYield", 0),
            "description": info.get("longBusinessSummary", "")[:500],  # First 500 chars
        }

    except Exception as e:
        logger.warning(f"Could not fetch info for {ticker}: {e}")
        return {
            "ticker": ticker,
            "name": ticker,
            "sector": "Unknown",
            "industry": "Unknown",
            "country": "Unknown",
            "market_cap": 0,
            "currency": "USD",
        }


def fetch_stock_info_batch(tickers: List[str]) -> Dict[str, Dict]:
    """
    Fetch company info for multiple tickers.

    Returns:
        Dict mapping ticker → info dict
    """
    return {ticker: fetch_stock_info(ticker) for ticker in tickers}


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily percentage returns from price data.

    Args:
        prices : DataFrame of closing prices

    Returns:
        DataFrame of daily returns (NaN first row removed)

    Example:
        returns = calculate_returns(prices)
        print(returns.mean())  # Average daily return per stock
    """
    returns = prices.pct_change().dropna()
    logger.info(f"Calculated returns: {len(returns)} rows, {len(returns.columns)} tickers")
    return returns


def calculate_cumulative_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate cumulative returns — shows portfolio growth over time.
    Base = 100 (easy to read as percentage growth from start)

    Returns:
        DataFrame where 110 means +10% from start date
    """
    return (prices / prices.iloc[0]) * 100


def calculate_rolling_volatility(returns: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """
    Calculate rolling 30-day volatility for each stock.
    Useful for seeing how volatility changes over time.

    Args:
        returns : Daily returns DataFrame
        window  : Rolling window in days (default 30)

    Returns:
        DataFrame of annualized rolling volatility
    """
    return returns.rolling(window=window).std() * np.sqrt(252) * 100


def fetch_52_week_range(ticker: str) -> Dict:
    """
    Fetch 52-week high and low for a stock.

    Returns:
        Dict with high, low, current price, and % from high/low
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current = info.get("currentPrice", info.get("regularMarketPrice", 0))
        high_52w = info.get("fiftyTwoWeekHigh", 0)
        low_52w = info.get("fiftyTwoWeekLow", 0)

        return {
            "ticker": ticker,
            "current_price": current,
            "52w_high": high_52w,
            "52w_low": low_52w,
            "pct_from_high": round((current - high_52w) / high_52w * 100, 2) if high_52w else None,
            "pct_from_low": round((current - low_52w) / low_52w * 100, 2) if low_52w else None,
        }
    except Exception as e:
        logger.warning(f"Could not fetch 52w range for {ticker}: {e}")
        return {"ticker": ticker}


def get_summary_stats(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Get summary statistics for all stocks in the portfolio.

    Returns DataFrame with: mean daily return, volatility, min, max, skew
    """
    stats = pd.DataFrame({
        "mean_daily_return_%": (returns.mean() * 100).round(4),
        "annual_return_%": (returns.mean() * 252 * 100).round(2),
        "annual_volatility_%": (returns.std() * np.sqrt(252) * 100).round(2),
        "min_daily_return_%": (returns.min() * 100).round(4),
        "max_daily_return_%": (returns.max() * 100).round(4),
        "skewness": returns.skew().round(4),
    })
    return stats


# ── Main — Run this to test ────────────────────────────────────────────────────

if __name__ == "__main__":

    print("=" * 60)
    print("AI Portfolio Optimizer — Stock Data Fetcher Test")
    print("=" * 60)

    # Test tickers — mix of US tech stocks
    tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN"
]

    # ── Test 1: Fetch Price Data ──
    print("\n[1] Fetching 1-Year price history...")
    prices = fetch_stock_data(tickers, period="1y")
    print(f"Shape: {prices.shape} (rows=trading days, cols=tickers)")
    print(f"\nLatest 10 closing prices:")
    print(prices.tail().to_string())

    # ── Test 2: Calculate Returns ──
    print("\n[2] Calculating daily returns...")
    returns = calculate_returns(prices)
    print(f"Returns shape: {returns.shape}")
    print(f"\nLatest 10 daily returns (%):")
    print((returns.tail() * 100).round(3).to_string())

    # ── Test 3: Summary Stats ──
    print("\n[3] Summary statistics:")
    stats = get_summary_stats(returns)
    print(stats.to_string())

    # ── Test 4: Cumulative Returns ──
    print("\n[4] Cumulative returns (base=100):")
    cumulative = calculate_cumulative_returns(prices)
    print(f"Start: {cumulative.iloc[0].to_dict()}")
    print(f"End  : {cumulative.iloc[-1].round(2).to_dict()}")
    print(f"(Values above 100 = profit, below 100 = loss from start date)")

    # ── Test 5: Company Info ──
    print("\n[5] Company info for AAPL:")
    info = fetch_stock_info("AAPL")
    for key, value in info.items():
        if key != "description":
            print(f"  {key}: {value}")

    # ── Test 6: 52-week range ──
    print("\n[6] 52-week range for AAPL:")
    range_data = fetch_52_week_range("AAPL")
    for key, value in range_data.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)