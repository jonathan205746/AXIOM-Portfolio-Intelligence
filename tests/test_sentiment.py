import pytest

from src.utils.sentiment import (
    SentimentLabel,
    classify_sentiment,
)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (-0.037, SentimentLabel.NEUTRAL),
        (-0.190, SentimentLabel.NEGATIVE),
        (+0.036, SentimentLabel.NEUTRAL),
        (-0.101, SentimentLabel.NEGATIVE),
        (+0.141, SentimentLabel.POSITIVE),
        (+0.088, SentimentLabel.NEUTRAL),
        (None, SentimentLabel.INSUFFICIENT_EVIDENCE),
    ],
)
def test_report_sentiment_classification(score, expected):
    assert classify_sentiment(score) == expected


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (-0.10, SentimentLabel.NEUTRAL),
        (+0.10, SentimentLabel.NEUTRAL),
    ],
)
def test_threshold_boundaries_are_neutral(score, expected):
    assert classify_sentiment(score) == expected


@pytest.mark.parametrize("score", [-1.01, 1.01])
def test_invalid_sentiment_score_is_rejected(score):
    with pytest.raises(ValueError):
        classify_sentiment(score)


@pytest.mark.parametrize("score", ["positive", [], {}])
def test_non_numeric_sentiment_score_is_rejected(score):
    with pytest.raises(TypeError):
        classify_sentiment(score)