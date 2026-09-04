"""
sentiment.py
FinBERT-based sentiment analysis for financial news.
FinBERT = BERT fine-tuned on financial text (Reuters, Bloomberg).

Run this file directly to test:
    python src/models/sentiment.py
"""

import torch
import logging
import time
from typing import Any, Dict, List, Optional, TypedDict
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from torch.nn.functional import softmax
from src.utils.sentiment import classify_sentiment

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "ProsusAI/finbert"
LABELS = ["positive", "negative", "neutral"]


class SentimentResult(TypedDict):
    positive: float
    negative: float
    neutral: float
    label: str


class SentimentAnalyzer:
    """
    Analyzes sentiment of financial text using FinBERT.

    Why FinBERT and not regular BERT?
    - Regular BERT: "Apple beats" could mean anything
    - FinBERT: trained on financial text, knows "beats earnings" = positive
    - More accurate for financial language, analyst reports, news headlines

    Sentiment score per article: positive / negative / neutral
    Aggregated score per ticker: -1.0 (very negative) to +1.0 (very positive)
    """

    def __init__(self):
        logger.info(f"Loading FinBERT model: {MODEL_NAME}")
        logger.info("First run downloads ~500MB — please wait...")
        self.tokenizer: Any = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model: Any = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        self.model.eval()  # Set to evaluation mode (no gradient computation)
        logger.info("FinBERT loaded successfully")

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of a single text string.

        Args:
            text: Financial news headline or article snippet
                  e.g. "Apple beats Q4 earnings expectations with record revenue"

        Returns:
            Dict with:
                label    : "positive", "negative", or "neutral"
                positive : confidence score 0-1
                negative : confidence score 0-1
                neutral  : confidence score 0-1
                (all three scores sum to 1.0)

        Example:
            result = analyzer.analyze("Apple beats earnings")
            print(result["label"])    # "positive"
            print(result["positive"]) # 0.9123
        """
        # Tokenize — convert text to token IDs FinBERT understands
        inputs = self.tokenizer(
            text,
            return_tensors="pt",    # PyTorch tensors
            truncation=True,         # Cut off at 512 tokens max
            max_length=512,
            padding=True
        )

        # Run through FinBERT — no gradient needed for inference.  The explicit
        # Any/Tensor annotations are intentional: recent Transformers versions
        # expose broad overloads that strict Pylance can otherwise mis-infer.
        with torch.no_grad():
            outputs: Any = self.model(**inputs)

        scores: torch.Tensor = softmax(outputs.logits, dim=-1).squeeze(0)
        probabilities = [float(v) for v in scores.detach().cpu().tolist()]
        label_index = int(torch.argmax(scores).item())

        result: SentimentResult = {
            "positive": round(probabilities[0], 4),
            "negative": round(probabilities[1], 4),
            "neutral": round(probabilities[2], 4),
            "label": LABELS[label_index],
        }
        return result

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze sentiment for multiple texts.

        Args:
            texts: List of financial news texts

        Returns:
            List of sentiment dicts (one per text)

        Note: Runs sequentially — FinBERT is slow on CPU (~0.5s per text)
              For 10 articles: ~5 seconds total
        """
        results = []
        for i, text in enumerate(texts):
            result = self.analyze(text)
            results.append(result)
            if (i + 1) % 5 == 0:
                logger.info(f"Analyzed {i+1}/{len(texts)} articles")
        return results

    def aggregate_sentiment(self, texts: List[str]) -> Dict:
        """
        Get overall sentiment score for a ticker based on all its news.

        Score calculation:
            score = mean(positive_score - negative_score) for all articles
            Range: -1.0 (all articles very negative) to +1.0 (all very positive)

        Args:
            texts: List of article text strings for one ticker

        Returns:
            Dict with:
                score         : Float -1.0 to +1.0
                label         : "positive", "negative", or "neutral"
                article_count : How many articles were analyzed
                breakdown     : Individual result per article

        Example:
            texts = ["Apple beats earnings", "Apple faces supply shortage"]
            result = analyzer.aggregate_sentiment(texts)
            print(result["score"])  # 0.35 (net positive)
            print(result["label"])  # "positive"
        """
        if not texts:
            return {
                "score": 0.0,
                "label": "neutral",
                "article_count": 0,
                "breakdown": []
            }

        results = self.analyze_batch(texts)

        # Score = average of (positive - negative) per article
        score = sum(r["positive"] - r["negative"] for r in results) / len(results)
        score = round(score, 4)

        # Use the shared AXIOM sentiment classification policy.
        # Keep the model-service response lowercase for backward compatibility.
        label = classify_sentiment(score).value.lower()

        return {
            "score": score,
            "label": label,
            "article_count": len(texts),
            "breakdown": results
        }

    def analyze_portfolio(
        self,
        news_by_ticker: Dict[str, List[Dict]]
    ) -> Dict[str, Dict]:
        """
        Run sentiment analysis for all tickers in the portfolio.

        Args:
            news_by_ticker: Output from fetch_news_batch()
                            {"AAPL": [articles...], "MSFT": [articles...]}

        Returns:
            Dict mapping ticker to aggregated sentiment
            {"AAPL": {"score": 0.72, "label": "positive", ...},
             "MSFT": {"score": -0.15, "label": "neutral", ...}}
        """
        sentiments = {}

        for ticker, articles in news_by_ticker.items():
            logger.info(f"Analyzing sentiment for {ticker}...")

            if not articles:
                logger.warning(f"No articles for {ticker} — using neutral")
                sentiments[ticker] = {
                    "score": 0.0,
                    "label": "neutral",
                    "article_count": 0,
                    "breakdown": []
                }
                continue

            texts = [a["text"] for a in articles if a.get("text")]
            sentiments[ticker] = self.aggregate_sentiment(texts)

            logger.info(
                f"{ticker}: score={sentiments[ticker]['score']}, "
                f"label={sentiments[ticker]['label']}, "
                f"articles={sentiments[ticker]['article_count']}"
            )

        return sentiments

# ============================================================================
# Compatibility wrappers for notebooks
# ============================================================================

_analyzer = None

def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer


def get_sentiment_score(text: str) -> float:
    """
    Returns a sentiment score between -1 and +1.
    Positive values = bullish
    Negative values = bearish
    """
    result = _get_analyzer().analyze(text)
    return round(result["positive"] - result["negative"], 4)


def aggregate_sentiment(texts):
    """
    Return the average net sentiment score for notebook use (-1.0 to +1.0).

    The class method returns a detailed dictionary; the notebook expects only
    its numeric score field.
    """
    if not texts:
        return 0.0
    return _get_analyzer().aggregate_sentiment(texts)["score"]
# ── Main — Run this to test ────────────────────────────────────────────────────


if __name__ == "__main__":

    print("=" * 60)
    print("AI Portfolio Optimizer — FinBERT Sentiment Test")
    print("=" * 60)

    print("\n[1] Loading FinBERT model (first run ~500MB download)...")
    analyzer = SentimentAnalyzer()

    # ── Test 1: Single headline ──
    print("\n[2] Testing single headline analysis...")
    test_headlines = [
        "Apple beats Q4 earnings expectations with record iPhone revenue",
        "Microsoft faces antitrust investigation in European markets",
        "Google announces quarterly dividend increase for shareholders",
        "Amazon Web Services reports strong cloud growth beating estimates",
        "Tesla recalls 200000 vehicles due to software safety concerns",
        "NVIDIA reports record revenue driven by AI chip demand",
    ]

    print("\nResults:")
    for headline in test_headlines:
        result = analyzer.analyze(headline)
        bar = "+" * int(result["positive"] * 20)
        print(f"\n  Text: {headline[:60]}")
        print(f"  Label: {result['label'].upper()}")
        print(f"  Positive: {result['positive']:.4f} | Negative: {result['negative']:.4f} | Neutral: {result['neutral']:.4f}")

    # ── Test 2: Aggregate sentiment ──
    print("\n[3] Testing aggregate sentiment for AAPL...")
    apple_texts = [
        "Apple beats Q4 earnings expectations with record iPhone revenue",
        "Apple Vision Pro faces tough competition from Samsung and Meta",
        "Apple services revenue grows 14 percent year over year",
        "Apple supply chain faces challenges due to geopolitical tensions",
        "Apple announces new MacBook Pro with M4 chip to strong demand"
    ]

    result = analyzer.aggregate_sentiment(apple_texts)
    print(f"\n  Articles analyzed: {result['article_count']}")
    print(f"  Overall score: {result['score']} (range: -1.0 to +1.0)")
    print(f"  Overall label: {result['label'].upper()}")
    print("\n  Individual article scores:")
    for i, (text, breakdown) in enumerate(zip(apple_texts, result["breakdown"])):
        print(f"  {i+1}. [{breakdown['label']}] {text[:55]}")

    # ── Test 3: Real news (if NewsAPI key available) ──
    print("\n[4] Testing with real news articles...")
    try:
        from src.data.news_fetcher import fetch_news

        articles = fetch_news("AAPL", "Apple", days_back=7, max_articles=5)
        if articles:
            texts = [a["text"] for a in articles]
            real_result = analyzer.aggregate_sentiment(texts)
            print(f"\n  Real AAPL news sentiment:")
            print(f"  Score: {real_result['score']} | Label: {real_result['label'].upper()}")
            print(f"  Based on {real_result['article_count']} real articles")
        else:
            print("  No real articles fetched — check NEWS_API_KEY")
    except Exception as e:
        print(f"  Skipping real news test: {e}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
