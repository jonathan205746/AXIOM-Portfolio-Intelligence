import pytest

from src.optimization.rebalancing import (
    build_rebalance_plan,
    calculate_current_allocation,
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


def test_current_allocation_uses_quantity_and_price():
    holdings = [
        {
            "ticker": "AAPL",
            "exchange": "US",
            "quantity": 2,
        },
        {
            "ticker": "MSFT",
            "exchange": "US",
            "quantity": 1,
        },
    ]

    result = calculate_current_allocation(
        holdings=holdings,
        latest_prices={
            "AAPL": 300.0,
            "MSFT": 400.0,
        },
        base_currency="USD",
        fx_rate_provider=lambda source, target: 1.0,
    )

    assert result["total_market_value"] == 1000.0
    assert result["current_weights"]["AAPL"] == pytest.approx(0.6)
    assert result["current_weights"]["MSFT"] == pytest.approx(0.4)
    assert sum(result["current_weights"].values()) == pytest.approx(1.0)


def test_current_allocation_converts_mixed_currency():
    holdings = [
        {
            "ticker": "GOOGL",
            "exchange": "US",
            "quantity": 3,
        },
        {
            "ticker": "TCS.NS",
            "exchange": "IN",
            "quantity": 6,
        },
    ]

    def fx_rate(source, target):
        rates = {
            ("USD", "INR"): 83.0,
            ("INR", "INR"): 1.0,
        }
        return rates[(source, target)]

    result = calculate_current_allocation(
        holdings=holdings,
        latest_prices={
            "GOOGL": 337.12,
            "TCS.NS": 2369.0,
        },
        base_currency="INR",
        fx_rate_provider=fx_rate,
    )

    google_value = 3 * 337.12 * 83.0
    tcs_value = 6 * 2369.0
    total = google_value + tcs_value

    assert result["market_values"]["GOOGL"] == pytest.approx(
        google_value
    )
    assert result["market_values"]["TCS.NS"] == pytest.approx(
        tcs_value
    )
    assert result["total_market_value"] == pytest.approx(total)
    assert result["current_weights"]["GOOGL"] == pytest.approx(
        google_value / total
    )
    assert sum(result["current_weights"].values()) == pytest.approx(1.0)


def test_current_allocation_reports_missing_price():
    holdings = [
        {
            "ticker": "AAPL",
            "exchange": "US",
            "quantity": 2,
        },
        {
            "ticker": "MSFT",
            "exchange": "US",
            "quantity": 1,
        },
    ]

    result = calculate_current_allocation(
        holdings=holdings,
        latest_prices={"AAPL": 300.0},
        base_currency="USD",
        fx_rate_provider=lambda source, target: 1.0,
    )

    assert result["current_weights"] == {"AAPL": 1.0}
    assert "MSFT" in result["excluded_tickers"]


def test_rebalance_plan_compares_current_to_target():
    plan = build_rebalance_plan(
        current_weights={
            "GOOGL": 0.28,
            "TCS.NS": 0.042,
            "RELIANCE.NS": 0.138,
        },
        target_weights={
            "GOOGL": 0.243,
            "TCS.NS": 0.038,
            "RELIANCE.NS": 0.138,
        },
        allocation_complete=True,
    )

    assert plan["GOOGL"]["gap"] == pytest.approx(-0.037)
    assert plan["GOOGL"]["action"] == "SELL"

    assert plan["TCS.NS"]["gap"] == pytest.approx(-0.004)
    assert plan["TCS.NS"]["action"] == "HOLD"

    assert plan["RELIANCE.NS"]["gap"] == pytest.approx(0.0)
    assert plan["RELIANCE.NS"]["action"] == "HOLD"


def test_incomplete_allocation_disables_all_actions():
    plan = build_rebalance_plan(
        current_weights={"AAPL": 1.0},
        target_weights={
            "AAPL": 0.60,
            "MSFT": 0.40,
        },
        allocation_complete=False,
    )

    assert plan["AAPL"]["action"] == "UNAVAILABLE"
    assert plan["MSFT"]["action"] == "UNAVAILABLE"
    assert plan["AAPL"]["gap"] is None
    assert plan["MSFT"]["current_weight"] is None