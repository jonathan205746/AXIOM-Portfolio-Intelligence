"""Shared price-currency and USD/INR conversion utilities."""

import math
from datetime import date, datetime, timedelta

import pandas as pd
import yfinance as yf


def market_currency(
    ticker: str,
    exchange: str,
) -> str:
    """Return the native quote currency for a holding."""
    normalized_ticker = ticker.upper()
    normalized_exchange = exchange.upper()

    if (
        normalized_exchange == "IN"
        or normalized_ticker.endswith((".NS", ".BO"))
    ):
        return "INR"

    return "USD"


def parse_date(value) -> date:
    """Convert a stored date-like value into a date."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    ).date()


def get_fx_rate(
    source_currency: str,
    target_currency: str,
    rate_date=None,
) -> float:
    """Return a USD/INR conversion rate."""
    source = source_currency.upper()
    target = target_currency.upper()

    if source == target:
        return 1.0

    if {source, target} != {"USD", "INR"}:
        raise ValueError(
            f"Unsupported conversion: {source}/{target}"
        )

    pair = yf.Ticker("USDINR=X")

    if rate_date is None:
        history = pair.history(period="5d")
    else:
        requested = parse_date(rate_date)
        history = pair.history(
            start=requested - timedelta(days=5),
            end=requested + timedelta(days=6),
        )

    if history.empty or "Close" not in history.columns:
        raise RuntimeError(
            f"FX rate unavailable for {source}/{target}"
        )

    closes: pd.Series = history["Close"].dropna()

    if closes.empty:
        raise RuntimeError(
            f"FX rate unavailable for {source}/{target}"
        )

    if rate_date is None:
        usd_to_inr = float(closes.iloc[-1])
    else:
        requested = parse_date(rate_date)

        eligible_values = [
            float(value)
            for index, value in closes.items()
            if parse_date(index) >= requested
        ]

        usd_to_inr = (
            eligible_values[0]
            if eligible_values
            else float(closes.iloc[-1])
        )

    if (
        not math.isfinite(usd_to_inr)
        or usd_to_inr <= 0
    ):
        raise RuntimeError(
            "USD/INR provider returned an invalid rate"
        )

    if source == "USD":
        return usd_to_inr

    return 1.0 / usd_to_inr


def convert_money(
    amount: float,
    source_currency: str,
    target_currency: str,
    rate_date=None,
) -> float:
    """Convert an amount using the requested FX rate."""
    return float(amount) * get_fx_rate(
        source_currency,
        target_currency,
        rate_date,
    )