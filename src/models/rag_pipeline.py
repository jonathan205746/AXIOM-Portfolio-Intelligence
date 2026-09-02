"""
rag_pipeline.py
---------------
Compatible with LangChain 1.3.0+ (no LLMChain — it was removed)
Uses: prompt | llm pattern (modern LangChain syntax)
LLM: Groq-hosted model configured through GROQ_MODEL.
"""

import os
import time
from dotenv import load_dotenv
from typing import Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from src.utils.sentiment import classify_sentiment


load_dotenv()

# ── Prompt Template ───────────────────────────────────────────────────────────

RECOMMENDATION_PROMPT = ChatPromptTemplate.from_template("""
You are the research-explanation layer of AXIOM Portfolio Intelligence.

The quantitative optimizer is the only component allowed to calculate
or modify portfolio target weights. You explain its output; you do not
replace it.

Asset: {ticker}
FinBERT aggregate score: {sentiment_score}
Canonical sentiment label: {sentiment_label}
Quantitative optimizer target: {portfolio_weight}%

Retrieved news evidence:
{articles}

Rules:
1. Do not produce BUY, SELL, STRONG BUY, or STRONG SELL advice.
2. Do not invent or recommend a revised portfolio weight.
3. Do not override the quantitative optimizer target.
4. Do not claim that an article is relevant unless its supplied text
   directly concerns the asset or company.
5. Do not invent prices, financial results, catalysts, risks, sources,
   dates, or company facts.
6. If the supplied articles are missing, irrelevant, or insufficient,
   explicitly state: "Insufficient ticker-specific news evidence."
7. Treat sentiment as supporting evidence, not as proof of future returns.
8. Clearly distinguish supplied evidence from a general risk hypothesis.

Return no more than 130 words using this structure:

Evidence quality: Sufficient / Limited / Insufficient
Model observation: one concise sentence
- Two evidence-based bullet points
Risk scenario to test: one sentence
Quantitative next step: suggest a constraint or stress test, without
providing a new target weight
""")

# ── Helper Functions ──────────────────────────────────────────────────────────

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
    RAG pipeline using a Groq-hosted LLM and LangChain 1.3.0.
    Uses prompt | llm chain syntax (replaces deprecated LLMChain)
    """

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.3
    ):
        api_key = os.getenv("GROQ_API_KEY", "").strip()

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

        chatgroq_options: dict[str, Any] = {
            "model_name": self.model_name,
            "temperature": temperature,
            "groq_api_key": api_key,  # pyright: ignore[reportCallIssue]
            "max_retries": 2,
        }

        # Modern LangChain 1.x syntax: prompt | llm (no LLMChain needed)
        self.llm = ChatGroq(**chatgroq_options)
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
        Generate evidence-grounded research commentary.

        Args:
            ticker:             e.g. "AAPL"
            sentiment_score:    FinBERT score, -1.0 to +1.0
            portfolio_weight:   Sharpe weight, 0.0 to 1.0
            retrieved_articles: News strings from FAISS vector store

        Returns:
            Dictionary containing the ticker, sentiment score,
            canonical label, optimizer weight, and evidence-grounded
            research commentary under the compatibility key
            ``recommendation``.
        """
        sentiment_label = classify_sentiment(sentiment_score).value
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
                "AI research commentary is temporarily unavailable.\n"
                f"- Sentiment: {sentiment_label} "
                f"({round(sentiment_score, 3)})\n"
                f"- Quantitative optimizer target: {weight_pct}%\n"
                "- The optimizer result remains available without AI commentary."
      )

        return {
            "ticker": ticker,
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_label": sentiment_label,
            "portfolio_weight_pct": weight_pct,
            "recommendation": recommendation_text,
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
            "You are the research-explanation layer of AXIOM. "
            "Here is the quantitative portfolio summary:\n\n"
            + "\n".join(lines)
            + "\n\nIn 3-4 sentences, explain the portfolio's "
            "diversification and sentiment distribution. Identify one "
            "scenario for quantitative stress testing. Do not provide "
            "investment advice, invent facts, or modify any portfolio "
            "weight. Use plain English."
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
            print(f"\n📊 {result['ticker']} RESEARCH COMMENTARY:")
            print(result["recommendation"])
        time.sleep(1)

    print(f"\n{'=' * 60}")
    print("PORTFOLIO SUMMARY:")
    print("=" * 60)
    print(pipeline.generate_portfolio_summary(all_recommendations))
    print("\n✅ RAG Pipeline test complete.")