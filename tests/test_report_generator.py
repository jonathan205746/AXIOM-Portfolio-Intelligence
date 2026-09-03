from pathlib import Path

from frontend.pages.report_generator import (
    get_report_sentiment,
    render_ai_commentary,
)


TEST_COLORS = {
    "green": "#00ff00",
    "red": "#ff0000",
    "amber": "#ffaa00",
    "text_secondary": "#888888",
}


def test_report_uses_canonical_negative_label():
    label, _, score_text, _ = get_report_sentiment(
        -0.190,
        TEST_COLORS,
    )

    assert label == "NEGATIVE"
    assert score_text == "-0.190"


def test_report_uses_canonical_positive_label():
    label, _, score_text, _ = get_report_sentiment(
        0.141,
        TEST_COLORS,
    )

    assert label == "POSITIVE"
    assert score_text == "+0.141"


def test_report_uses_canonical_neutral_label():
    label, _, score_text, _ = get_report_sentiment(
        0.036,
        TEST_COLORS,
    )

    assert label == "NEUTRAL"
    assert score_text == "+0.036"


def test_missing_sentiment_is_not_neutral():
    label, _, score_text, bar_width = get_report_sentiment(
        None,
        TEST_COLORS,
    )

    assert label == "INSUFFICIENT_EVIDENCE"
    assert score_text == "N/A"
    assert bar_width == 50


def test_ai_markdown_is_rendered():
    rendered = render_ai_commentary(
        "**Evidence quality:** Limited"
    )

    assert "<strong>Evidence quality:</strong>" in rendered
    assert "**Evidence quality:**" not in rendered


def test_ai_script_is_removed():
    rendered = render_ai_commentary(
        "<script>alert('unsafe')</script>Safe text"
    )

    assert "<script>" not in rendered
    assert "Safe text" in rendered


def test_report_source_contains_complete_news_pipeline():
    source = Path(
        "frontend/pages/report_generator.py"
    ).read_text(encoding="utf-8")

    assert "news_parts = []" in source
    assert "for ticker in available:" in source
    assert 'articles = all_news.get(ticker, [])' in source
    assert 'news_html = "\\n".join(news_parts)' in source
    assert "{optimizer_weight_pct}%%" not in source

def test_report_frontier_displays_sharpe_labels():
    source = Path(
        "frontend/pages/report_generator.py"
    ).read_text(encoding="utf-8")

    assert "final_sharpe" in source
    assert "baseline_sharpe" in source
    assert "Sharpe {final_sharpe:.3f}" in source
    assert "Sharpe {baseline_sharpe:.3f}" in source


def test_report_identifies_var_amounts_as_usd():
    source = Path(
        "frontend/pages/report_generator.py"
    ).read_text(encoding="utf-8")

    assert 'risk_currency_symbol = "$"' in source
    assert "95% VaR · 1 DAY · USD" in source
    assert "99% VaR · 1 DAY · USD" in source


def test_live_and_report_consume_canonical_rebalance_plan():
    analysis_source = Path(
        "frontend/pages/3_Analysis.py"
    ).read_text(encoding="utf-8")

    report_source = Path(
        "frontend/pages/report_generator.py"
    ).read_text(encoding="utf-8")

    expected_lookup = (
        'plan_entry = rebalance_plan.get(ticker, {})'
    )

    assert expected_lookup in analysis_source
    assert expected_lookup in report_source

    assert (
        'rebalance_plan = results.get("rebalance_plan", {})'
        in analysis_source
    )
    assert (
        'rebalance_plan = results.get("rebalance_plan", {})'
        in report_source
    )

    assert "Rebalance Action" in analysis_source
    assert "rebalance_action" in report_source