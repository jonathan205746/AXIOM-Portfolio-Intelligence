from pathlib import Path


def test_adaptive_search_does_not_scale_health_or_sharpe():
    source = Path(
        "frontend/pages/3_Analysis.py"
    ).read_text(encoding="utf-8")

    assert 'round(float(value) * 100, 1)' not in source
    assert 'round(float(value) * 100, 3)' not in source

    assert 'round(float(value), 1)' in source
    assert 'round(float(value), 3)' in source

def test_performance_chart_uses_return_percentages():
    source = Path(
        "frontend/pages/3_Analysis.py"
    ).read_text(encoding="utf-8")

    assert ".sub(1.0)" in source
    assert ".mul(100.0)" in source
    assert "Cumulative Return (%)" in source
    assert "It does not apply portfolio weights" in source


def test_performance_tab_uses_independent_figure():
    source = Path(
        "frontend/pages/3_Analysis.py"
    ).read_text(encoding="utf-8")

    performance_source = source.split(
        "with tab6:",
        1,
    )[1].split(
        "# ── Health Score Expander",
        1,
    )[0]

    assert "ticker_return_fig = go.Figure()" in (
        performance_source
    )
    assert (
        'key="ticker_cumulative_returns"'
        in performance_source
    )
    assert "Cumulative Return (%)" in performance_source


def test_risk_gauge_uses_centered_annotation():
    source = Path(
        "frontend/pages/3_Analysis.py"
    ).read_text(encoding="utf-8")

    assert 'mode="gauge"' in source
    assert "figure.add_annotation(" in source
    assert 'mode="gauge+number"' not in source


def test_drawdown_does_not_use_concentration_label():
    source = Path(
        "frontend/pages/3_Analysis.py"
    ).read_text(encoding="utf-8")

    assert 'delta=conc["label"]' not in source
    assert '"Peak-to-trough loss"' in source