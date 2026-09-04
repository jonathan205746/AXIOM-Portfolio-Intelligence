"""
Shared portfolio weight-change and rebalancing classifications.

All weights and thresholds in this module use decimal form:

    0.25 = 25%
    0.01 = 1 percentage point
"""

import math
from collections.abc import Callable, Iterable, Mapping
from typing import Any, Final

from src.data.market_data import market_currency


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


def calculate_current_allocation(
    holdings: Iterable[Mapping[str, Any]],
    latest_prices: Mapping[str, float],
    base_currency: str,
    fx_rate_provider: Callable[[str, str], float],
) -> dict[str, Any]:
    """
    Calculate current market values and weights in one base currency.

    Holdings without a valid price or FX rate are excluded and returned
    in the excluded_tickers mapping.
    """
    normalized_base = base_currency.upper()
    market_values: dict[str, float] = {}
    excluded_tickers: dict[str, str] = {}

    for holding in holdings:
        ticker = str(holding.get("ticker") or "").strip()

        if not ticker:
            continue

        try:
            quantity = float(holding.get("quantity", 0.0))
            price = float(latest_prices[ticker])

            if (
                not math.isfinite(quantity)
                or quantity <= 0
            ):
                raise ValueError("invalid quantity")

            if (
                not math.isfinite(price)
                or price <= 0
            ):
                raise ValueError("invalid current price")

            quote_currency = market_currency(
                ticker,
                str(holding.get("exchange") or ""),
            )

            fx_rate = float(
                fx_rate_provider(
                    quote_currency,
                    normalized_base,
                )
            )

            if (
                not math.isfinite(fx_rate)
                or fx_rate <= 0
            ):
                raise ValueError("invalid FX rate")

            market_value = quantity * price * fx_rate

            market_values[ticker] = (
                market_values.get(ticker, 0.0)
                + market_value
            )

        except Exception as exc:
            excluded_tickers[ticker] = (
                f"{type(exc).__name__}: {exc}"
            )

    total_market_value = sum(market_values.values())

    if total_market_value <= 0:
        raise ValueError(
            "No valid current market values are available"
        )

    current_weights = {
        ticker: value / total_market_value
        for ticker, value in market_values.items()
    }

    return {
        "base_currency": normalized_base,
        "market_values": market_values,
        "current_weights": current_weights,
        "total_market_value": total_market_value,
        "excluded_tickers": excluded_tickers,
        "is_complete": not excluded_tickers,
    }


def build_rebalance_plan(
    current_weights: Mapping[str, float],
    target_weights: Mapping[str, float],
    *,
    allocation_complete: bool,
    threshold: float = REBALANCE_THRESHOLD,
) -> dict[str, dict[str, Any]]:
    """
    Build the canonical current-versus-target rebalance plan.

    If any current holding is missing valid price or FX data, actions are
    unavailable because the remaining weights would be incorrectly
    normalized.
    """
    plan: dict[str, dict[str, Any]] = {}

    for ticker, target_value in target_weights.items():
        target_weight = float(target_value)
        current_value = current_weights.get(ticker)

        if (
            not allocation_complete
            or current_value is None
        ):
            plan[ticker] = {
                "current_weight": None,
                "target_weight": target_weight,
                "gap": None,
                "action": "UNAVAILABLE",
                "reason": (
                    "Current allocation is incomplete because price "
                    "or FX data is unavailable"
                ),
            }
            continue

        current_weight = float(current_value)
        gap = target_weight - current_weight
        action = classify_rebalance_action(
            current_weight,
            target_weight,
            threshold=threshold,
        )

        reason_by_action = {
            "BUY": "Current allocation is below final target",
            "SELL": "Current allocation is above final target",
            "HOLD": (
                "Current allocation is within the "
                "1 percentage-point threshold"
            ),
        }

        plan[ticker] = {
            "current_weight": current_weight,
            "target_weight": target_weight,
            "gap": gap,
            "action": action,
            "reason": reason_by_action[action],
        }

    return plan