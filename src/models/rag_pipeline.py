"""
rag_pipeline.py
---------------
Compatible with LangChain 1.3.0+ (no LLMChain — it was removed)
Uses: prompt | llm pattern (modern LangChain syntax)

LLM: llama-3.3-70b-versatile via Groq (free, no daily quota)
"""

import os
import time
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ── Prompt Template ───────────────────────────────────────────────────────────

RECOMMENDATION_PROMPT = ChatPromptTemplate.from_template("""
You are a rigorous, skeptical financial analyst AI. Do NOT simply agree with the data — challenge it.

Stock: {ticker}
FinBERT Sentiment: {sentiment_score} (range: -1.0 to +1.0)
Sentiment Label: {sentiment_label}
Optimizer Recommended Weight: {portfolio_weight}%

Recent News Articles:
{articles}

Instructions:
1. One-line verdict: STRONG BUY / BUY / HOLD / REDUCE / SELL with confidence (High/Medium/Low).
2. 2-3 bullet points of critical analysis. If the weight seems too concentrated, say so. If news contradicts the sentiment score, highlight it.
3. One specific risk factor to monitor.
4. If you disagree with the optimizer weight, suggest a revised weight and explain why. Do not blindly agree.

Keep under 150 words. Use plain English, no jargon.
""")

# ── Helper Functions ──────────────────────────────────────────────────────────

def score_to_label(score: float) -> str:
    if score >= 0.3:
        return "Positive"
    elif score <= -0.3:
        return "Negative"
    return "Neutral"


def format_articles(articles: list) -> str:
    if not articles:
        return "No recent news articles available."
    return "\n".join(
        f"{i+1}. {a.strip()}" for i, a in enumerate(articles[:5])
    )


def weight_to_percent(weight: float) -> str:
    return f"{round(weight * 100, 1)}"


# ── RAG Pipeline Class ────────────────────────────────────────────────────────

class RAGPipeline:
    """
    RAG Pipeline using Groq (Llama 3.3 70B) + LangChain 1.3.0
    Uses prompt | llm chain syntax (replaces deprecated LLMChain)
    """

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.3
    ):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in .env\n"
                "Add: GROQ_API_KEY=your_key_here\n"
                "Get free key: console.groq.com"
            )

        model_name = model_name or os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

        self.model_name = model_name

        self.llm = ChatGroq(
            model=self.model_name,
            temperature=temperature,
            api_key=SecretStr(api_key),
            max_retries=2
        )

        # Modern LangChain 1.x syntax: prompt | llm (no LLMChain needed)
        self.chain = RECOMMENDATION_PROMPT | self.llm

        print(f"[RAGPipeline] Initialized — model: {self.model_name} via Groq")

    def generate_recommendation(
        self,
        ticker: str,
        sentiment_score: float,
        portfolio_weight: float,
        retrieved_articles: list
    ) -> dict:
        """
        Generate a plain English investment recommendation.

        Args:
            ticker:             e.g. "AAPL"
            sentiment_score:    FinBERT score, -1.0 to +1.0
            portfolio_weight:   Sharpe weight, 0.0 to 1.0
            retrieved_articles: News strings from FAISS vector store

        Returns:
            dict: ticker, sentiment_score, sentiment_label,
                  portfolio_weight_pct, recommendation
        """
        sentiment_label = score_to_label(sentiment_score)
        formatted_articles = format_articles(retrieved_articles)
        weight_pct = weight_to_percent(portfolio_weight)

        print(f"\n[RAGPipeline] Generating for {ticker}...")
        print(f"  Sentiment : {sentiment_score:.3f} ({sentiment_label})")
        print(f"  Weight    : {weight_pct}%")
        print(f"  Articles  : {len(retrieved_articles)}")

        try:
            response = self.chain.invoke({
                "ticker": ticker,
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": sentiment_label,
                "portfolio_weight": weight_pct,
                "articles": formatted_articles
            })

            if hasattr(response, "content"):
                content = response.content
            elif isinstance(response, list) and response:
                first_item = response[0]
                content = first_item.content if hasattr(first_item, "content") else first_item
            else:
                content = str(response)

            if isinstance(content, list):
                content = content[0] if content else ""

            recommendation_text = str(content).strip()

        except Exception as e:
            print(f"[RAGPipeline] LLM call failed for {ticker}: {e}")
            recommendation_text = (
                f"HOLD — Medium confidence (LLM unavailable).\n"
                f"- Sentiment: {sentiment_label} ({round(sentiment_score, 3)})\n"
                f"- Weight: {weight_pct}%\n"
                f"- Note: Check GROQ_API_KEY in .env\n"
            )

        return {
            "ticker": ticker,
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_label": sentiment_label,
            "portfolio_weight_pct": weight_pct,
            "recommendation": recommendation_text
        }

    def generate_portfolio_summary(self, recommendations: list) -> str:
        """Overall portfolio summary from all ticker recommendations."""
        if not recommendations:
            return "No recommendations to summarize."

        lines = [
            f"- {r['ticker']}: {r['sentiment_label']} sentiment "
            f"({r['sentiment_score']}), weight {r['portfolio_weight_pct']}%"
            for r in recommendations
        ]

        prompt = (
            "You are a portfolio manager AI. Here is the portfolio summary:\n\n"
            + "\n".join(lines)
            + "\n\nIn 3-4 sentences give an overall health assessment. "
            "Cover: diversification, sentiment bias, and one key risk. Plain English only."
        )

        try:
            response = self.llm.invoke(prompt)
            if hasattr(response, "content"):
                content = response.content
            elif isinstance(response, list) and response:
                first_item = response[0]
                content = first_item.content if hasattr(first_item, "content") else first_item
            else:
                content = str(response)

            if isinstance(content, list):
                content = content[0] if content else ""
            return str(content).strip()
        except Exception as e:
            print(f"[RAGPipeline] Summary failed: {e}")
            return "Portfolio summary unavailable — check GROQ_API_KEY."


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("RAG PIPELINE TEST — Groq + LangChain 1.3.0")
    print("=" * 60)

    test_tickers = [
        {
            "ticker": "AAPL",
            "sentiment_score": 0.72,
            "portfolio_weight": 0.35,
            "articles": [
                "Apple reports record iPhone sales in Q4 2024.",
                "Apple Vision Pro receives mixed reviews from developers.",
                "Apple increases dividend payout for third consecutive year."
            ]
        },
        {
            "ticker": "MSFT",
            "sentiment_score": 0.55,
            "portfolio_weight": 0.30,
            "articles": [
                "Microsoft Azure cloud revenue grows 28% year-over-year.",
                "Microsoft Copilot integration drives Office 365 adoption.",
            ]
        },
        {
            "ticker": "GOOGL",
            "sentiment_score": -0.15,
            "portfolio_weight": 0.20,
            "articles": [
                "Google faces antitrust scrutiny in EU over search dominance.",
                "Google Cloud gains market share in AI infrastructure deals.",
            ]
        }
    ]

    pipeline = RAGPipeline()
    all_recommendations = []

    for data in test_tickers:
        print(f"\n{'─' * 50}")
        result = pipeline.generate_recommendation(
            ticker=data["ticker"],
            sentiment_score=data["sentiment_score"],
            portfolio_weight=data["portfolio_weight"],
            retrieved_articles=data["articles"]
        )
        if result:
            all_recommendations.append(result)
            print(f"\n📊 {result['ticker']} RECOMMENDATION:")
            print(result["recommendation"])
        time.sleep(1)

    print(f"\n{'=' * 60}")
    print("PORTFOLIO SUMMARY:")
    print("=" * 60)
    print(pipeline.generate_portfolio_summary(all_recommendations))
    print("\n✅ RAG Pipeline test complete.")