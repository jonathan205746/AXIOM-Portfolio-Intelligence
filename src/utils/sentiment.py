"""
Shared sentiment classification utilities.

All AXIOM components must use this module so the dashboard,
RAG pipeline, optimizer commentary, and reports display the
same sentiment label for the same score.
"""

from enum import Enum
from typing import Optional


POSITIVE_THRESHOLD = 0.10
NEGATIVE_THRESHOLD = -0.10


class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def classify_sentiment(
    score: Optional[float],
) -> SentimentLabel:
    """
    Convert an aggregate FinBERT score into a canonical label.

    The aggregate score is the mean of:

        positive_probability - negative_probability

    Threshold policy:
        score > +0.10 -> POSITIVE
        score < -0.10 -> NEGATIVE
        otherwise     -> NEUTRAL
        score is None -> INSUFFICIENT_EVIDENCE

    A missing score must not be represented as neutral.
    """

    if score is None:
        return SentimentLabel.INSUFFICIENT_EVIDENCE

    if not isinstance(score, (int, float)):
        raise TypeError(
            "Sentiment score must be a number or None."
        )

    numeric_score = float(score)

    if not -1.0 <= numeric_score <= 1.0:
        raise ValueError(
            "Sentiment score must be between -1.0 and 1.0; "
            f"received {numeric_score}."
        )

    if numeric_score > POSITIVE_THRESHOLD:
        return SentimentLabel.POSITIVE

    if numeric_score < NEGATIVE_THRESHOLD:
        return SentimentLabel.NEGATIVE

    return SentimentLabel.NEUTRAL