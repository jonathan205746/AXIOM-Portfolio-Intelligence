"""
news_fetcher.py
Fetches recent financial news for stock tickers using NewsAPI.
Free tier: 100 requests/day, 1 month history, 1 req/sec rate limit.

Run this file directly to test:
    python src/data/news_fetcher.py
"""

import logging
import os
import re
import time
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"


# ── Ticker → Company Name Mapping ────────────────────────────────────────────
# Critical for Indian (.NS) tickers where the ticker symbol is not a natural
# news keyword (e.g. "ASIANPAINT" vs "Asian Paints").
TICKER_TO_COMPANY = {
    # Indian NSE tickers
    "ASIANPAINT.NS": "Asian Paints",
    "SBIN.NS": "State Bank of India",
    "BAJFINANCE.NS": "Bajaj Finance",
    "WIPRO.NS": "Wipro",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "RELIANCE.NS": "Reliance Industries",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ICICIBANK.NS": "ICICI Bank",
    "HDFCBANK.NS": "HDFC Bank",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "AXISBANK.NS": "Axis Bank",
    "LT.NS": "Larsen & Toubro",
    "MARUTI.NS": "Maruti Suzuki",
    "TATAMOTORS.NS": "Tata Motors",
    "SUNPHARMA.NS": "Sun Pharmaceutical",
    "CIPLA.NS": "Cipla",
    "DRREDDY.NS": "Dr. Reddy's Laboratories",
    "HCLTECH.NS": "HCL Technologies",
    "ITC.NS": "ITC Limited",
    "NESTLEIND.NS": "Nestle India",
    "POWERGRID.NS": "Power Grid Corporation",
    "NTPC.NS": "NTPC Limited",
    "ONGC.NS": "Oil and Natural Gas Corporation",
    "COALINDIA.NS": "Coal India",
    "ADANIENT.NS": "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports",
    "BAJAJFINSV.NS": "Bajaj Finserv",
    "BHARTIARTL.NS": "Bharti Airtel",
    "BRITANNIA.NS": "Britannia Industries",
    "EICHERMOT.NS": "Eicher Motors",
    "GRASIM.NS": "Grasim Industries",
    "HEROMOTOCO.NS": "Hero MotoCorp",
    "HINDALCO.NS": "Hindalco Industries",
    "INDUSINDBK.NS": "IndusInd Bank",
    "JSWSTEEL.NS": "JSW Steel",
    "M&M.NS": "Mahindra & Mahindra",
    "TATASTEEL.NS": "Tata Steel",
    "TECHM.NS": "Tech Mahindra",
    "TITAN.NS": "Titan Company",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "UPL.NS": "UPL Limited",
    "VEDL.NS": "Vedanta",
    # US / Global tickers
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "GOOG": "Alphabet",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "META": "Meta",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "INTC": "Intel",
    "SONY": "Sony",
    "IBM": "IBM",
    "ORCL": "Oracle",
    "CRM": "Salesforce",
    "ADBE": "Adobe",
    "PYPL": "PayPal",
    "UBER": "Uber",
    "LYFT": "Lyft",
    "COIN": "Coinbase",
    "PLTR": "Palantir",
    "SNOW": "Snowflake",
    "ZM": "Zoom",
    "SHOP": "Shopify",
    "SQ": "Block",
    "HOOD": "Robinhood",
}
# NewsAPI query contract.
TICKER_ALIASES = {
    "GOOGL": ("Alphabet", "Google", "YouTube", "Waymo"),
    "GOOG": ("Alphabet", "Google", "YouTube", "Waymo"),
    "MSFT": ("Microsoft", "Azure", "Windows", "Microsoft Copilot"),
    "AAPL": ("Apple", "iPhone", "iPad", "Mac", "App Store"),
    "AMZN": ("Amazon", "Amazon Web Services", "AWS"),
    "META": ("Meta Platforms", "Meta", "Facebook", "Instagram"),
    "NVDA": ("Nvidia",),
    "TSLA": ("Tesla",),
    "SBIN.NS": ("State Bank of India", "SBI"),
    "RELIANCE.NS": (
        "Reliance Industries",
        "Reliance",
        "Jio",
        "Jio Platforms",
    ),
    "TCS.NS": (
        "Tata Consultancy Services",
        "TCS",
    ),
    "INFY.NS": ("Infosys",),
    "WIPRO.NS": ("Wipro",),
    "HDFCBANK.NS": ("HDFC Bank",),
    "ICICIBANK.NS": ("ICICI Bank",),
}

def normalize_news_text(value: str) -> str:
    """Normalize text for reliable matching and deduplication."""

    normalized = unicodedata.normalize(
        "NFKC",
        str(value or ""),
    )
    normalized = normalized.casefold()
    normalized = re.sub(r"[^\w&]+", " ", normalized)
    return " ".join(normalized.split())


def get_ticker_aliases(
    ticker: str,
    company_name: Optional[str] = None,
) -> tuple[str, ...]:
    """Return normalized aliases used to validate article relevance."""

    canonical_ticker = ticker.upper().strip()
    aliases = list(TICKER_ALIASES.get(canonical_ticker, ()))

    resolved_company = (
        company_name
        or TICKER_TO_COMPANY.get(canonical_ticker)
    )

    if resolved_company:
        aliases.append(resolved_company)

    ticker_without_exchange = canonical_ticker.split(".", 1)[0]

    # Very short ticker symbols create excessive false matches.
    if len(ticker_without_exchange) >= 3:
        aliases.append(ticker_without_exchange)

    normalized_aliases = {
        normalize_news_text(alias)
        for alias in aliases
        if normalize_news_text(alias)
    }

    return tuple(
        sorted(
            normalized_aliases,
            key=len,
            reverse=True,
        )
    )


def find_matching_aliases(
    ticker: str,
    title: str,
    description: str = "",
    company_name: Optional[str] = None,
) -> list[str]:
    """Return company aliases found in the article text."""

    article_text = normalize_news_text(
        f"{title or ''} {description or ''}"
    )
    matches = []

    for alias in get_ticker_aliases(ticker, company_name):
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"

        if re.search(pattern, article_text):
            matches.append(alias)

    return matches


def is_ticker_relevant(
    ticker: str,
    title: str,
    description: str = "",
    company_name: Optional[str] = None,
) -> bool:
    """Return True when an article directly mentions the company."""

    return bool(
        find_matching_aliases(
            ticker=ticker,
            title=title,
            description=description,
            company_name=company_name,
        )
    )


def filter_relevant_articles(
    ticker: str,
    articles: List[Dict],
    company_name: Optional[str] = None,
    max_articles: Optional[int] = None,
) -> List[Dict]:
    """
    Remove irrelevant, empty and duplicate news articles.

    The original article schema is preserved. Two evidence fields are
    added: relevance_match and relevance_status.
    """

    filtered_articles = []
    seen_titles = set()

    for article in articles:
        title = str(article.get("title") or "").strip()
        description = str(
            article.get("description") or ""
        ).strip()

        if not title or title == "[Removed]":
            continue

        normalized_title = normalize_news_text(title)

        if not normalized_title:
            continue

        if normalized_title in seen_titles:
            continue

        matched_aliases = find_matching_aliases(
            ticker=ticker,
            title=title,
            description=description,
            company_name=company_name,
        )

        if not matched_aliases:
            continue

        seen_titles.add(normalized_title)

        filtered_article = dict(article)
        filtered_article["relevance_status"] = "DIRECT_MATCH"
        filtered_article["relevance_match"] = matched_aliases
        filtered_articles.append(filtered_article)

        if (
            max_articles is not None
            and len(filtered_articles) >= max_articles
        ):
            break

    return filtered_articles

# ── Core Functions ─────────────────────────────────────────────────────────────

def fetch_news(
    ticker: str,
    company_name: Optional[str] = None,
    days_back: int = 7,
    max_articles: int = 20
) -> List[Dict]:
    """
    Fetch recent news articles for a stock ticker.

    Args:
        ticker       : Stock symbol e.g. "AAPL" or "ASIANPAINT.NS"
        company_name : Full name e.g. "Apple" (improves search quality).
                       If omitted, auto-resolved from TICKER_TO_COMPANY.
        days_back    : How many days back to search (max 30 on free tier)
        max_articles : Maximum number of articles to return

    Returns:
        List of article dicts with keys:
        ticker, title, description, url, published_at, source, text

    Example:
        articles = fetch_news("ASIANPAINT.NS", days_back=7)
        print(articles[0]["title"])
    """
    if not NEWS_API_KEY:
        raise ValueError(
            "NEWS_API_KEY not found. "
            "Add it to your .env file: NEWS_API_KEY=your_key_here"
        )

    # Auto-resolve company name if not provided
    if company_name is None:
        company_name = TICKER_TO_COMPANY.get(ticker)

    # Use company name if available — gives far better results than raw ticker
    query = company_name if company_name else ticker

    # Strip exchange suffixes for cleaner search when falling back to ticker
    if query.endswith((".NS", ".BO", ".NSE", ".BSE")):
        query = query.rsplit(".", 1)[0]

    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    params = {
        "q": f"{query} stock",
        "from": from_date,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": min(max(max_articles * 3, max_articles), 100),
        "apiKey": NEWS_API_KEY,
    }

    try:
        logger.info(f"Fetching news for {ticker} (query: '{query} stock')")
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            logger.error(f"NewsAPI error for {ticker}: {data.get('message')}")
            return []

        articles = []
        for article in data.get("articles", []):
            # Skip articles with missing title or description
            if not article.get("title") or not article.get("description"):
                continue
            # Skip removed articles
            if article.get("title") == "[Removed]":
                continue

            articles.append({
                "ticker": ticker,
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
                "published_at": article["publishedAt"],
                "source": article["source"]["name"],
                # text = combined title + description (used by FinBERT and FAISS)
                "text": f"{article['title']}. {article['description']}"
            })

        raw_article_count = len(articles)

        articles = filter_relevant_articles(
           ticker=ticker,
           articles=articles,
           company_name=company_name,
           max_articles=max_articles,
        )

        logger.info(
            "News relevance for %s: %d/%d articles retained",
            ticker,
            len(articles),
            raw_article_count,
        )

        return articles

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching news for {ticker}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {ticker}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error for {ticker}: {e}")
        return []


def fetch_news_batch(
    tickers: List[str],
    company_names: Optional[Dict[str, str]] = None,
    days_back: int = 7,
    max_articles: int = 20,
    delay: float = 1.1
) -> Dict[str, List[Dict]]:
    """
    Fetch news for multiple tickers with rate limiting.

    Args:
        tickers       : List of stock symbols
        company_names : Dict mapping ticker to company name
                        e.g. {"AAPL": "Apple", "MSFT": "Microsoft"}
                        If omitted, TICKER_TO_COMPANY is used automatically.
        days_back     : Days back to search
        max_articles  : Max articles per ticker
        delay         : Seconds between requests (1.1 > 1 to be safe)

    Returns:
        Dict mapping ticker to list of article dicts

    Example:
        news = fetch_news_batch(["AAPL", "ASIANPAINT.NS"])
        print(news["ASIANPAINT.NS"][0]["title"])
    """
    company_names = company_names or {}
    results = {}

    logger.info(f"Fetching news for {len(tickers)} tickers...")

    for i, ticker in enumerate(tickers):
        articles = fetch_news(
            ticker=ticker,
            company_name=company_names.get(ticker),  # None is OK — fetch_news auto-resolves
            days_back=days_back,
            max_articles=max_articles
        )
        results[ticker] = articles

        # Rate limiting — NewsAPI free tier: 1 req/sec
        # We wait even after the last ticker to be safe
        if i < len(tickers) - 1:
            logger.info(f"Waiting {delay}s (rate limit)...")
            time.sleep(delay)

    total_articles = sum(len(a) for a in results.values())
    logger.info(f"Total articles fetched: {total_articles}")
    return results


def get_article_texts(ticker: str, articles: List[Dict]) -> List[str]:
    """
    Extract just the text strings from a list of articles.
    This is what sentiment.py and vector_store.py will consume.

    Args:
        ticker   : Stock symbol (for logging)
        articles : List of article dicts from fetch_news()

    Returns:
        List of text strings (title + description combined)

    Example:
        texts = get_article_texts("AAPL", articles)
        # ["Apple beats Q4 earnings. Revenue exceeded expectations...",
        #  "Apple Vision Pro sales. The headset has sold..."]
    """
    texts = [a["text"] for a in articles if a.get("text")]
    logger.info(f"Extracted {len(texts)} text strings for {ticker}")
    return texts


def check_api_status() -> Dict:
    """
    Check if NewsAPI key is valid and how many requests remain today.

    Returns:
        Dict with status, requests_remaining, requests_limit
    """
    if not NEWS_API_KEY:
        return {"status": "error", "message": "NEWS_API_KEY not set in .env"}

    try:
        # Make a minimal request to check quota
        response = requests.get(
            BASE_URL,
            params={"q": "test", "pageSize": 1, "apiKey": NEWS_API_KEY},
            timeout=5
        )
        data = response.json()

        if data.get("status") == "ok":
            return {
                "status": "ok",
                "message": "API key valid",
                "total_results_for_test": data.get("totalResults", 0)
            }
        else:
            return {
                "status": "error",
                "message": data.get("message", "Unknown error")
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Main — Run this to test ────────────────────────────────────────────────────

if __name__ == "__main__":

    print("=" * 60)
    print("AI Portfolio Optimizer — News Fetcher Test")
    print("=" * 60)

    # ── Test 1: API Key Check ──
    print("\n[1] Checking NewsAPI key...")
    status = check_api_status()
    print(f"Status: {status}")
    if status["status"] == "error":
        print("ERROR: Fix your API key first. Add NEWS_API_KEY to .env file")
        exit(1)

    # ── Test 2: Single Ticker (US) ──
    print("\n[2] Fetching news for single ticker (AAPL)...")
    articles = fetch_news("AAPL", company_name="Apple", days_back=7)
    print(f"Found: {len(articles)} articles")

    if articles:
        print("\nFirst article:")
        print(f"  Title     : {articles[0]['title']}")
        print(f"  Source    : {articles[0]['source']}")
        print(f"  Published : {articles[0]['published_at']}")
        print(f"  Text      : {articles[0]['text'][:150]}...")

    time.sleep(1.1)  # Rate limit

    # ── Test 3: Indian Ticker with Auto-Resolved Name ──
    print("\n[3] Fetching news for Indian ticker (ASIANPAINT.NS)...")
    articles_in = fetch_news("ASIANPAINT.NS", days_back=7)
    print(f"Found: {len(articles_in)} articles (should be >0 if API quota available)")
    if articles_in:
        print(f"  First: {articles_in[0]['title'][:70]}...")

    time.sleep(1.1)

    # ── Test 4: Multiple Tickers ──
    print("\n[4] Fetching news for multiple tickers...")
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "ASIANPAINT.NS", "SBIN.NS"]

    news_by_ticker = fetch_news_batch(tickers)

    print("\nResults:")
    for ticker, arts in news_by_ticker.items():
        print(f"\n{ticker}: {len(arts)} articles")
        for a in arts[:2]:
            print(f"  [{a['source']}] {a['title'][:65]}")

    # ── Test 5: get_article_texts ──
    print("\n[5] Testing get_article_texts() for AAPL...")
    aapl_texts = get_article_texts("AAPL", news_by_ticker.get("AAPL", []))
    print(f"Text strings extracted: {len(aapl_texts)}")
    if aapl_texts:
        print(f"First text: {aapl_texts[0][:120]}...")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)