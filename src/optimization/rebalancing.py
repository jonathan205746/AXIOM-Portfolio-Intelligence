"""
Shared portfolio weight-change and rebalancing classifications.

All weights and thresholds in this module use decimal form:

    0.25 = 25%
    0.01 = 1 percentage point
"""

from typing import Final


REBALANCE_THRESHOLD: Final[float] = 0.01
EXCLUSION_THRESHOLD: Final[float] = 0.001
FLOAT_TOLERANCE: Final[float] = 1e-12


def classify_model_adjustment(
    optimized_weight: float,
    final_weight: float,
    *,
    threshold: float = REBALANCE_THRESHOLD,
    exclusion_threshold: float = EXCLUSION_THRESHOLD,
) -> str:
    """
    Classify the change from the quantitative optimizer weight to the
    sentiment-adjusted final target.

    This is a model adjustment, not an instruction based on the user's
    actual holdings.
    """
    optimized = float(optimized_weight)
    final = float(final_weight)

    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    if exclusion_threshold < 0:
        raise ValueError(
            "exclusion_threshold must be non-negative"
        )

    if final < exclusion_threshold:
        return "EXCLUDE"

    change = final - optimized

    if change >= threshold - FLOAT_TOLERANCE:
        return "INCREASE"

    if change <= -threshold + FLOAT_TOLERANCE:
        return "DECREASE"

    return "UNCHANGED"


def classify_rebalance_action(
    current_weight: float,
    target_weight: float,
    *,
    threshold: float = REBALANCE_THRESHOLD,
) -> str:
    """
    Classify the trade needed to move an actual holding toward its target.
    """
    current = float(current_weight)
    target = float(target_weight)

    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    gap = target - current

    if gap >= threshold - FLOAT_TOLERANCE:
        return "BUY"

    if gap <= -threshold + FLOAT_TOLERANCE:
        return "SELL"

    return "HOLD"