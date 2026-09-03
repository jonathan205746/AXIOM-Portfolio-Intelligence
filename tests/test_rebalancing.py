import pytest

from src.optimization.rebalancing import (
    classify_model_adjustment,
    classify_rebalance_action,
)


@pytest.mark.parametrize(
    ("optimized", "final", "expected"),
    [
        (0.25, 0.2469, "UNCHANGED"),
        (0.25, 0.2428, "UNCHANGED"),
        (0.02, 0.0379, "INCREASE"),
        (0.25, 0.23, "DECREASE"),
        (0.10, 0.11, "INCREASE"),
        (0.11, 0.10, "DECREASE"),
    ],
)
def test_model_adjustment_uses_one_percent_threshold(
    optimized,
    final,
    expected,
):
    assert (
        classify_model_adjustment(optimized, final)
        == expected
    )


def test_model_adjustment_excludes_zero_target():
    assert (
        classify_model_adjustment(0.10, 0.0005)
        == "EXCLUDE"
    )


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        (0.28, 0.243, "SELL"),
        (0.20, 0.205, "HOLD"),
        (0.02, 0.038, "BUY"),
    ],
)
def test_actual_rebalance_uses_current_weight(
    current,
    target,
    expected,
):
    assert (
        classify_rebalance_action(current, target)
        == expected
    )


@pytest.mark.parametrize(
    "function",
    [
        classify_model_adjustment,
        classify_rebalance_action,
    ],
)
def test_negative_threshold_is_rejected(function):
    with pytest.raises(ValueError):
        function(0.20, 0.25, threshold=-0.01)