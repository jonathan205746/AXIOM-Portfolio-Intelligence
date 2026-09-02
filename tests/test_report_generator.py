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


def test_report_uses_canonical_neutral_label():
    label, _, score_text, _ = get_report_sentiment(
        0.088,
        TEST_COLORS,
    )

    assert label == "NEUTRAL"
    assert score_text == "+0.088"


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