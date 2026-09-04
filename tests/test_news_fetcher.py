from src.data.news_fetcher import (
    filter_relevant_articles,
    get_ticker_aliases,
    is_ticker_relevant,
    normalize_news_text,
)


def make_article(
    title: str,
    description: str = "",
    url: str = "https://example.com/article",
) -> dict:
    return {
        "ticker": "",
        "title": title,
        "description": description,
        "url": url,
        "published_at": "2026-09-02T10:00:00Z",
        "source": "Test Source",
        "text": f"{title}. {description}",
    }


def test_normalize_news_text():
    assert normalize_news_text(
        "  Google—launches   Gemini! "
    ) == "google launches gemini"


def test_google_headline_is_relevant():
    assert is_ticker_relevant(
        ticker="GOOGL",
        title="Google launches a new Gemini model",
    )


def test_alphabet_headline_is_relevant_to_google():
    assert is_ticker_relevant(
        ticker="GOOGL",
        title="Alphabet announces quarterly results",
    )


def test_nvidia_headline_is_not_google_news():
    assert not is_ticker_relevant(
        ticker="GOOGL",
        title="Nvidia prepares to report earnings",
    )


def test_meta_headline_is_not_google_news():
    assert not is_ticker_relevant(
        ticker="GOOGL",
        title="Meta settles youth safety case",
    )


def test_microsoft_headline_is_relevant():
    assert is_ticker_relevant(
        ticker="MSFT",
        title="Microsoft expands Azure infrastructure",
    )


def test_hdfc_article_is_not_sbi_news():
    assert not is_ticker_relevant(
        ticker="SBIN.NS",
        title="HDFC Bank faces a shareholder lawsuit",
    )


def test_state_bank_article_is_sbi_news():
    assert is_ticker_relevant(
        ticker="SBIN.NS",
        title="State Bank of India reports quarterly earnings",
    )


def test_jio_article_is_reliance_news():
    assert is_ticker_relevant(
        ticker="RELIANCE.NS",
        title="Jio Platforms receives IPO approval",
    )


def test_tcs_word_boundary_avoids_partial_match():
    assert not is_ticker_relevant(
        ticker="TCS.NS",
        title="Markets and products report general updates",
        description="Statistics remain unchanged.",
    )


def test_tcs_headline_is_relevant():
    assert is_ticker_relevant(
        ticker="TCS.NS",
        title="TCS changes variable pay for senior employees",
    )


def test_duplicate_titles_are_removed():
    articles = [
        make_article(
            "Google launches Gemini update",
            "Alphabet expands its AI offering.",
        ),
        make_article(
            "Google launches Gemini update",
            "The same story from another provider.",
        ),
    ]

    filtered = filter_relevant_articles(
        ticker="GOOGL",
        articles=articles,
    )

    assert len(filtered) == 1


def test_irrelevant_articles_are_removed():
    articles = [
        make_article(
            "Google launches Gemini update",
        ),
        make_article(
            "Nvidia reports record chip revenue",
        ),
        make_article(
            "Warren Buffett celebrates his birthday",
        ),
    ]

    filtered = filter_relevant_articles(
        ticker="GOOGL",
        articles=articles,
    )

    assert len(filtered) == 1
    assert filtered[0]["title"] == (
        "Google launches Gemini update"
    )


def test_article_schema_is_preserved():
    article = make_article(
        "Microsoft expands Azure",
        "Cloud infrastructure investment continues.",
    )

    filtered = filter_relevant_articles(
        ticker="MSFT",
        articles=[article],
    )

    assert filtered[0]["title"] == article["title"]
    assert filtered[0]["description"] == article["description"]
    assert filtered[0]["url"] == article["url"]
    assert filtered[0]["published_at"] == article["published_at"]
    assert filtered[0]["source"] == article["source"]
    assert filtered[0]["text"] == article["text"]
    assert filtered[0]["relevance_status"] == "DIRECT_MATCH"
    assert filtered[0]["relevance_match"]


def test_max_articles_is_enforced():
    articles = [
        make_article(f"Microsoft Azure update {number}")
        for number in range(5)
    ]

    filtered = filter_relevant_articles(
        ticker="MSFT",
        articles=articles,
        max_articles=2,
    )

    assert len(filtered) == 2


def test_known_ticker_has_company_aliases():
    aliases = get_ticker_aliases("GOOGL")

    assert "alphabet" in aliases
    assert "google" in aliases