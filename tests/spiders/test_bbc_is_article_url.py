"""Tests for BBC spider is_article_url() including Sport articles."""

from news_scraper.spiders.bbc import BBCSpider


def test_bbc_sport_article_url():
    """Test BBC Sport article URL with alphanumeric ID is accepted."""
    spider = BBCSpider()

    # Accept BBC Sport articles
    assert (
        spider.is_article_url("https://www.bbc.com/sport/articles/c4g5lj59rr9o") is True
    )
    assert (
        spider.is_article_url("https://www.bbc.com/sport/articles/abc123def456") is True
    )

    # Accept existing /news/ article patterns
    assert spider.is_article_url("https://www.bbc.com/news/world-12345678") is True
    assert spider.is_article_url("https://www.bbc.com/news/technology-87654321") is True

    # Accept /articles/ pattern
    assert spider.is_article_url("https://www.bbc.com/articles/cxyz123abc") is True


def test_bbc_rejects_non_article_urls():
    """Test BBC spider rejects non-article URLs."""
    spider = BBCSpider()

    # Reject sport section root
    assert spider.is_article_url("https://www.bbc.com/sport") is False
    assert spider.is_article_url("https://www.bbc.com/sport/") is False

    # Reject video/av pages
    assert spider.is_article_url("https://www.bbc.com/news/av/world-12345678") is False

    # Reject live pages
    assert (
        spider.is_article_url("https://www.bbc.com/news/live/world-12345678") is False
    )

    # Reject programmes
    assert spider.is_article_url("https://www.bbc.com/programmes/b0abcdef") is False

    # Reject newsround
    assert spider.is_article_url("https://www.bbc.com/newsround") is False
