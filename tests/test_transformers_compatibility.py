from types import SimpleNamespace

import pytest
import torch

from src.models.rag_pipeline import RAGPipeline, _response_text
from src.models.sentiment import SentimentAnalyzer


class FakeTokenizer:
    def __call__(self, text, **kwargs):
        return {"input_ids": torch.tensor([[1, 2, 3]])}


class FakeFinBert:
    def eval(self):
        return self

    def __call__(self, **kwargs):
        return SimpleNamespace(
            logits=torch.tensor([[4.0, 1.0, 0.5]], dtype=torch.float32)
        )


class SuccessfulChain:
    def invoke(self, payload):
        return SimpleNamespace(
            content="Evidence quality: Sufficient\n"
            "Model observation: Positive evidence without changing the target."
        )


class FailingChain:
    def invoke(self, payload):
        raise RuntimeError("simulated provider failure")


def test_finbert_inference_contract_remains_stable():
    analyzer = object.__new__(SentimentAnalyzer)
    analyzer.tokenizer = FakeTokenizer()
    analyzer.model = FakeFinBert()

    result = analyzer.analyze("Company reports stronger quarterly earnings.")

    assert result["label"] == "positive"
    assert result["positive"] > result["negative"]
    assert result["positive"] > result["neutral"]

    total_probability = result["positive"] + result["negative"] + result["neutral"]
    assert total_probability == pytest.approx(1.0, abs=0.001)


def test_rag_response_text_handles_langchain_message_contract():
    response = SimpleNamespace(content="  grounded response  ")

    assert _response_text(response) == "grounded response"


def test_rag_recommendation_preserves_quantitative_target():
    pipeline = object.__new__(RAGPipeline)
    pipeline.chain = SuccessfulChain()

    result = pipeline.generate_recommendation(
        ticker="AAPL",
        sentiment_score=0.25,
        portfolio_weight=0.35,
        retrieved_articles=["Apple reports quarterly earnings growth."],
    )

    assert result["ticker"] == "AAPL"
    assert result["sentiment_score"] == 0.25
    assert result["portfolio_weight_pct"] == "35.0"
    assert result["sentiment_label"] == "POSITIVE"
    assert "Sufficient" in result["recommendation"]


def test_rag_failure_does_not_remove_optimizer_result():
    pipeline = object.__new__(RAGPipeline)
    pipeline.chain = FailingChain()

    result = pipeline.generate_recommendation(
        ticker="MSFT",
        sentiment_score=-0.20,
        portfolio_weight=0.30,
        retrieved_articles=[],
    )

    assert result["ticker"] == "MSFT"
    assert result["portfolio_weight_pct"] == "30.0"
    assert result["sentiment_label"] == "NEGATIVE"
    assert "temporarily unavailable" in result["recommendation"]
    assert "optimizer target: 30.0%" in result["recommendation"]
