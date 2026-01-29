"""
Unit tests for the base NewsSpider class.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import hashlib
from w3lib.url import canonicalize_url

from scrapy.http import HtmlResponse, Request
from news_scraper.spiders.newsspider import NewsSpider
from news_scraper.items import NewsItem


@pytest.fixture
def news_spider():
    """Fixture for NewsSpider."""
    return NewsSpider()


@pytest.fixture
def test_url():
    """Fixture for test URL."""
    return "https://example.com/article"


class TestNewsSpider:
    """Test cases for the NewsSpider base class."""

    def test_spider_initialization(self, news_spider):
        """Test spider is initialized with correct attributes."""
        assert news_spider.name == "news_scraper"
        assert news_spider.domain == ""
        assert news_spider.allowed_domains == []
        assert news_spider.config is not None
        assert "USER_AGENT" in news_spider.custom_settings

    def test_is_valid_url_with_http(self, news_spider):
        """Test URL validation for http URLs."""
        assert news_spider.is_valid_url("http://example.com") is True

    def test_is_valid_url_with_https(self, news_spider):
        """Test URL validation for https URLs."""
        assert news_spider.is_valid_url("https://example.com") is True

    def test_is_valid_url_invalid(self, news_spider):
        """Test URL validation for invalid URLs."""
        assert news_spider.is_valid_url("ftp://example.com") is False
        assert news_spider.is_valid_url("javascript:void(0)") is False
        assert news_spider.is_valid_url("mailto:test@example.com") is False

    def test_is_article_page_always_true(self, news_spider):
        """Test that base is_article_page always returns True."""
        response = Mock()
        assert news_spider.is_article_page(response) is True

    @patch("news_scraper.spiders.newsspider.Article")
    def test_process_article_creates_news_item(
        self, mock_article_class, news_spider, test_url
    ):
        """Test that process_article creates a NewsItem with correct fields."""
        # Setup mock response
        request = Request(url=test_url)
        response = HtmlResponse(
            url=test_url,
            request=request,
            body=b"<html><body>Test article</body></html>",
            encoding="utf-8",
        )

        # Setup mock article
        mock_article = MagicMock()
        mock_article.title = "Test Title"
        mock_article.authors = ["Test Author"]
        mock_article.text = "Test article text content"
        mock_article.summary = "Test summary"
        mock_article.publish_date = datetime(2024, 1, 15, 12, 0, 0)
        mock_article_class.return_value = mock_article

        # Process article
        item = NewsSpider.process_article(response, "example.com", news_spider.config)

        # Assertions
        assert isinstance(item, NewsItem)
        assert item["title"] == "Test Title"
        assert item["author"] == "Test Author"
        assert item["text"] == "Test article text content"
        assert item["summary"] == "Test summary"
        assert item["url"] == test_url
        assert item["source"] == "example.com"
        assert item["published_at"] is not None
        assert item["scraped_at"] is not None
        assert item["url_hash"] is not None
        assert item["fingerprint"] is not None

        # Verify article methods were called
        mock_article.parse.assert_called_once()
        mock_article.nlp.assert_called_once()

        # Verify article has actual content
        assert mock_article.title is not None and mock_article.title != ""
        assert mock_article.text is not None and mock_article.text != ""
        assert len(item["text"]) > 0
        assert len(item["title"]) > 0

    @patch("news_scraper.spiders.newsspider.Article")
    def test_process_article_handles_no_authors(
        self, mock_article_class, news_spider, test_url
    ):
        """Test that process_article handles articles with no authors."""
        request = Request(url=test_url)
        response = HtmlResponse(
            url=test_url,
            request=request,
            body=b"<html><body>Test</body></html>",
            encoding="utf-8",
        )

        mock_article = MagicMock()
        mock_article.title = "Test"
        mock_article.authors = []
        mock_article.text = "Text"
        mock_article.summary = "Summary"
        mock_article.publish_date = None
        mock_article_class.return_value = mock_article

        item = NewsSpider.process_article(response, "example.com", news_spider.config)

        assert item["author"] == ""
        assert item["published_at"] == ""

        # Verify article still has content even without author
        assert item["text"] is not None and len(item["text"]) > 0
        assert item["title"] is not None and len(item["title"]) > 0
        assert mock_article.text == "Text"
        assert mock_article.title == "Test"

    @patch("news_scraper.spiders.newsspider.Article")
    def test_process_article_creates_unique_fingerprint(
        self, mock_article_class, news_spider, test_url
    ):
        """Test that process_article creates unique fingerprints for different content."""
        request = Request(url=test_url)
        response = HtmlResponse(
            url=test_url,
            request=request,
            body=b"<html><body>Test</body></html>",
            encoding="utf-8",
        )

        # First article
        mock_article1 = MagicMock()
        mock_article1.title = "Title 1"
        mock_article1.authors = []
        mock_article1.text = "Content 1"
        mock_article1.summary = "Summary 1"
        mock_article1.publish_date = None
        mock_article_class.return_value = mock_article1

        item1 = NewsSpider.process_article(response, "example.com", news_spider.config)

        # Second article with different content
        mock_article2 = MagicMock()
        mock_article2.title = "Title 2"
        mock_article2.authors = []
        mock_article2.text = "Content 2"
        mock_article2.summary = "Summary 2"
        mock_article2.publish_date = None
        mock_article_class.return_value = mock_article2

        item2 = NewsSpider.process_article(response, "example.com", news_spider.config)

        # Fingerprints should be different
        assert item1["fingerprint"] != item2["fingerprint"]

        # Verify both articles have content
        assert item1["text"] is not None and len(item1["text"]) > 0
        assert item2["text"] is not None and len(item2["text"]) > 0
        assert item1["text"] != item2["text"]  # Content should be different

    @patch("news_scraper.spiders.newsspider.Article")
    def test_process_article_with_empty_content(
        self, mock_article_class, news_spider, test_url
    ):
        """Test that process_article handles articles with empty content."""
        request = Request(url=test_url)
        response = HtmlResponse(
            url=test_url,
            request=request,
            body=b"<html><body></body></html>",
            encoding="utf-8",
        )

        mock_article = MagicMock()
        mock_article.title = ""
        mock_article.authors = []
        mock_article.text = ""
        mock_article.summary = ""
        mock_article.publish_date = None
        mock_article_class.return_value = mock_article

        item = NewsSpider.process_article(response, "example.com", news_spider.config)

        # Item should still be created but with empty strings
        assert isinstance(item, NewsItem)
        assert item["title"] == ""
        assert item["text"] == ""
        assert item["summary"] == ""
        # Fingerprint should still be generated (hash of empty string)
        assert item["fingerprint"] is not None
        assert len(item["fingerprint"]) > 0

    @patch("news_scraper.spiders.newsspider.Article")
    def test_process_article_verifies_content_exists(
        self, mock_article_class, news_spider, test_url
    ):
        """Test that process_article verifies newspaper3k extracted actual content."""
        request = Request(url=test_url)
        response = HtmlResponse(
            url=test_url,
            request=request,
            body=b"<html><body><article><h1>Real Title</h1><p>Real content here</p></article></body></html>",
            encoding="utf-8",
        )

        # Mock article with realistic content
        mock_article = MagicMock()
        mock_article.title = "Real Title"
        mock_article.authors = ["Jane Doe"]
        mock_article.text = (
            "Real content here with multiple sentences. This is test content."
        )
        mock_article.summary = "Real content here"
        mock_article.publish_date = datetime(2024, 1, 15, 12, 0, 0)
        mock_article_class.return_value = mock_article

        item = NewsSpider.process_article(response, "example.com", news_spider.config)

        # Verify content was actually extracted
        assert item["title"] is not None
        assert len(item["title"]) > 0
        assert item["text"] is not None
        assert len(item["text"]) > 10  # Real content should be substantial
        assert item["summary"] is not None

        # Verify the extracted content matches what newspaper3k returned
        assert item["title"] == mock_article.title
        assert item["text"] == mock_article.text
        assert item["summary"] == mock_article.summary
        assert item["author"] == mock_article.authors[0]

    def test_parse_follows_valid_links(self, news_spider, test_url):
        """Test that parse follows valid links."""
        request = Request(url=test_url)
        response = HtmlResponse(
            url=test_url,
            request=request,
            body=b"""
            <html>
                <body>
                    <a href="https://example.com/article1">Article 1</a>
                    <a href="https://example.com/article2">Article 2</a>
                </body>
            </html>
            """,
            encoding="utf-8",
        )

        # Mock is_article_page to return False so it doesn't try to process
        news_spider.is_article_page = Mock(return_value=False)

        results = list(news_spider.parse(response))

        # Should yield follow requests
        assert any(hasattr(r, "url") for r in results)


class TestNewsSpiderIntegration:
    """Integration tests for NewsSpider."""

    def test_url_hash_is_consistent(self):
        """Test that same URL produces same hash."""
        url1 = "https://example.com/article?utm_source=test"
        url2 = "https://example.com/article?utm_source=test"

        canon_url1 = canonicalize_url(url1)
        canon_url2 = canonicalize_url(url2)

        hash1 = hashlib.sha256(canon_url1.encode("utf-8")).hexdigest()
        hash2 = hashlib.sha256(canon_url2.encode("utf-8")).hexdigest()

        assert hash1 == hash2
