"""Tests for CBS News spider is_article_url() with loosened slug requirements."""

from news_scraper.spiders.cbsnews import CBSNewsSpider


def test_cbs_accepts_news_urls_with_single_slug():
    """Test CBS spider accepts /news/ URLs with single slug segment."""
    spider = CBSNewsSpider()

    # Accept /news/ with slug
    assert (
        spider.is_article_url(
            "https://www.cbsnews.com/news/bad-bunny-spotify-super-bowl-halftime-performance/"
        )
        is True
    )
    assert spider.is_article_url("https://www.cbsnews.com/news/short-slug/") is True
    assert (
        spider.is_article_url("https://www.cbsnews.com/news/test-article-2026/") is True
    )

    # Accept without trailing slash
    assert spider.is_article_url("https://www.cbsnews.com/news/some-article") is True


def test_cbs_rejects_news_root():
    """Test CBS spider rejects /news/ root."""
    spider = CBSNewsSpider()

    # Reject /news/ root
    assert spider.is_article_url("https://www.cbsnews.com/news/") is False
    assert spider.is_article_url("https://www.cbsnews.com/news") is False


def test_cbs_rejects_section_roots():
    """Test CBS spider rejects section root URLs."""
    spider = CBSNewsSpider()

    # Reject section roots
    assert spider.is_article_url("https://www.cbsnews.com/us/") is False
    assert spider.is_article_url("https://www.cbsnews.com/world") is False
    assert spider.is_article_url("https://www.cbsnews.com/politics/") is False
    assert spider.is_article_url("https://www.cbsnews.com/moneywatch") is False


def test_cbs_rejects_video_live_essentials():
    """Test CBS spider rejects video, live, and essentials URLs."""
    spider = CBSNewsSpider()

    # Reject video
    assert spider.is_article_url("https://www.cbsnews.com/video/some-video/") is False

    # Reject live
    assert spider.is_article_url("https://www.cbsnews.com/live/stream/") is False

    # Reject essentials
    assert (
        spider.is_article_url("https://www.cbsnews.com/essentials/best-products/")
        is False
    )
