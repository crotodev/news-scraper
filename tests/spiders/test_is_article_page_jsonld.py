"""Tests for JSON-LD Article/NewsArticle detection in is_article_page()."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.spiders.apnews import APNewsSpider
from news_scraper.spiders.bbc import BBCSpider
from news_scraper.spiders.cbsnews import CBSNewsSpider
from news_scraper.spiders.newsspider import NewsSpider


@pytest.fixture
def ap_html():
    """Load AP News HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "ap.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def bbc_html():
    """Load BBC HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "bbc.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def cbs_html():
    """Load CBS News HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "cbs.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


def test_jsonld_article_detection_ap(ap_html):
    """Test JSON-LD Article detection with AP News fixture."""
    response = HtmlResponse(
        url="https://apnews.com/article/test-article",
        body=ap_html,
        encoding="utf-8",
    )

    spider = APNewsSpider()
    # Should detect as article page due to JSON-LD NewsArticle
    assert spider.is_article_page(response) is True


def test_jsonld_article_detection_bbc(bbc_html):
    """Test JSON-LD Article detection with BBC fixture."""
    response = HtmlResponse(
        url="https://www.bbc.com/sport/articles/test",
        body=bbc_html,
        encoding="utf-8",
    )

    spider = BBCSpider()
    # Should detect as article page
    assert spider.is_article_page(response) is True


def test_jsonld_article_detection_cbs(cbs_html):
    """Test JSON-LD Article detection with CBS News fixture."""
    response = HtmlResponse(
        url="https://www.cbsnews.com/news/test-article/",
        body=cbs_html,
        encoding="utf-8",
    )

    spider = CBSNewsSpider()
    # Should detect as article page
    assert spider.is_article_page(response) is True


def test_no_article_indicators():
    """Test page with no JSON-LD, no og:type, no article tag returns False."""
    minimal_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Not an Article</title>
        <meta name="description" content="Just a regular page">
    </head>
    <body>
        <div class="content">
            <h1>Section Page</h1>
            <p>This is not an article page.</p>
        </div>
    </body>
    </html>
    """

    response = HtmlResponse(
        url="https://example.com/section/page",
        body=minimal_html,
        encoding="utf-8",
    )

    spider = NewsSpider()
    spider.allowed_domains = ["example.com"]

    # This should return False because:
    # - No JSON-LD Article/NewsArticle
    # - No og:type=article
    # - No <article> tag
    # - URL doesn't strongly suggest article
    # Note: is_article_url will likely return False for this URL anyway
    result = spider.is_article_page(response)
    assert result is False
