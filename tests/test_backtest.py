import numpy as np
import pandas as pd
import pytest

from scripts import backtest


def make_config(**overrides):
    values = {
        "tickers": ["A", "B"],
        "benchmark": "SPY",
        "start": "2026-02-02",
        "end": "2026-03-02",
        "lookback": 2,
        "risk_free_rate": 0.0,
        "transaction_cost": 0.01,
        "min_weight": 0.0,
        "max_weight": 1.0,
        "initial_capital": 100_000.0,
    }
    values.update(overrides)
    return backtest.Config(**values)


def sample_prices():
    index = pd.to_datetime(
        ["2026-01-28", "2026-01-29", "2026-02-02", "2026-02-03", "2026-03-02"]
    )
    return pd.DataFrame(
        {
            "A": [100.0, 100.0, 100.0, 110.0, 110.0],
            "B": [100.0, 100.0, 100.0, 100.0, 100.0],
        },
        index=index,
    )


def test_initial_establishment_is_common_cost_free_baseline():
    nav, turnover, cost, log = backtest.run_strategy(
        sample_prices(), make_config(), "equal_weight"
    )

    assert nav.iloc[0].to_dict() == {
        "gross": 100_000.0,
        "net": 100_000.0,
    }
    assert log[0]["initial_establishment"] is True
    assert log[0]["reported_turnover"] == 0.0
    assert log[0]["transaction_cost"] == 0.0
    assert turnover > 0.0
    assert cost > 0.0


def test_turnover_uses_drifted_pretrade_weights_and_costs_both_sides():
    nav, turnover, cost, log = backtest.run_strategy(
        sample_prices(), make_config(), "equal_weight"
    )

    drifted = np.array([110.0 / 210.0, 100.0 / 210.0])
    target = np.array([0.5, 0.5])
    traded_notional = float(np.abs(target - drifted).sum())
    expected_turnover = 0.5 * traded_notional
    expected_cost = 105_000.0 * traded_notional * 0.01

    assert turnover == pytest.approx(expected_turnover)
    assert cost == pytest.approx(expected_cost)
    assert log[-1]["traded_notional"] == pytest.approx(traded_notional)
    assert nav.iloc[-1]["gross"] == pytest.approx(105_000.0)
    assert nav.iloc[-1]["net"] == pytest.approx(105_000.0 - expected_cost)


def test_optimizer_history_excludes_rebalance_date(monkeypatch):
    history_end_dates = []

    class StubOptimizer:
        def __init__(self, history):
            history_end_dates.append(history.index[-1])

        def optimize(self, **_kwargs):
            return {"weights": {"A": 0.5, "B": 0.5}}

    monkeypatch.setattr(backtest, "PortfolioOptimizer", StubOptimizer)
    _, _, _, log = backtest.run_strategy(
        sample_prices(), make_config(), "quantitative_only"
    )

    rebalance_dates = [pd.Timestamp(row["date"]) for row in log]
    assert len(history_end_dates) == len(rebalance_dates)
    assert all(
        history_end < rebalance_date
        for history_end, rebalance_date in zip(history_end_dates, rebalance_dates)
    )


def test_benchmark_alignment_does_not_forward_fill_missing_dates():
    index = pd.to_datetime(["2026-02-02", "2026-02-03", "2026-02-04"])
    benchmark = pd.Series(
        [100.0, 102.0],
        index=pd.to_datetime(["2026-02-02", "2026-02-04"]),
    )

    result = backtest.benchmark_nav(benchmark, make_config(), index)

    assert list(result.index) == [index[0], index[2]]
    assert result.iloc[0] == pytest.approx(100_000.0)
    assert result.iloc[-1] == pytest.approx(102_000.0)


def test_zero_cost_makes_gross_and_net_identical():
    nav, _, cost, _ = backtest.run_strategy(
        sample_prices(),
        make_config(transaction_cost=0.0),
        "equal_weight",
    )

    pd.testing.assert_series_equal(nav["gross"], nav["net"], check_names=False)
    assert cost == 0.0
