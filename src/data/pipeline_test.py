"""
pipeline_test.py
Tests that stock_fetcher.py and news_fetcher.py work together.
This is a temporary test file — delete before final deployment.

Run: python src/data/pipeline_test.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.stock_fetcher import fetch_stock_data, calculate_returns, fetch_stock_info
from src.data.news_fetcher import fetch_news_batch, get_article_texts
import time

print("=" * 60)
print("PIPELINE TEST — Stock Data + News Data Combined")
print("=" * 60)

tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN"
]

# ── STEP 1: Stock Prices ──────────────────────────────────
print("\n[STEP 1] Fetching stock prices...")
prices = fetch_stock_data(tickers, period="1mo")
returns = calculate_returns(prices)
print(f"Price data shape: {prices.shape}")
print(f"Latest prices:\n{prices.tail(10)}\n")

# ── STEP 2: Company Names ─────────────────────────────────
print("[STEP 2] Fetching company info...")
company_names = {}
for ticker in tickers:
    info = fetch_stock_info(ticker)
    company_names[ticker] = info["name"]
    print(f"  {ticker} = {info['name']} | Sector: {info['sector']}")

# ── STEP 3: News Articles ─────────────────────────────────
print("\n[STEP 3] Fetching news...")
news_by_ticker = fetch_news_batch(tickers, company_names, days_back=7)

for ticker, articles in news_by_ticker.items():
    print(f"\n{ticker}: {len(articles)} articles")
    for a in articles[:2]:
        print(f"  [{a['source']}] {a['title'][:65]}")

# ── STEP 4: Article Texts ─────────────────────────────────
print("\n[STEP 4] Extracting text for sentiment analysis...")
for ticker in tickers:
    texts = get_article_texts(ticker, news_by_ticker.get(ticker, []))
    print(f"  {ticker}: {len(texts)} text strings ready for FinBERT")

# ── STEP 5: Combined Summary ──────────────────────────────
print("\n" + "=" * 60)
print("PIPELINE SUMMARY")
print("=" * 60)
for ticker in tickers:
    article_count = len(news_by_ticker.get(ticker, []))
    latest_price = prices[ticker].iloc[-1]
    daily_return = returns[ticker].iloc[-1] * 100
    print(
        f"{ticker}: "
        f"Price=${latest_price:.2f} | "
        f"Return={daily_return:+.2f}% | "
        f"News={article_count} articles"
    )

print("\nDATA PIPELINE WORKING")
print("=" * 60)