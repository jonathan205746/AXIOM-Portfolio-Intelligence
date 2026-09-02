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