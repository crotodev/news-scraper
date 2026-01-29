"""
Unit tests for specific spider implementations (CNN, BBC, etc.).
"""

import pytest
from unittest.mock import Mock
from typing import List

from scrapy.http import HtmlResponse, Request
from news_scraper.spiders.cnn import CNNSpider
from news_scraper.spiders.bbc import BBCSpider
from news_scraper.spiders.foxnews import FoxNewsSpider
from news_scraper.spiders.nytimes import NYTimesSpider
from news_scraper.spiders.guardian import GuardianSpider
from news_scraper.spiders.nbcnews import NBCNewsSpider
from news_scraper.spiders.apnews import APNewsSpider
from news_scraper.spiders.cbsnews import CBSNewsSpider
from news_scraper.spiders.newsspider import NewsSpider


@pytest.fixture
def cnn_spider() -> CNNSpider:
    """Fixture for CNNSpider."""
    return CNNSpider()


class TestCNNSpider:
    """Test cases for CNNSpider."""

    def test_spider_attributes(self, cnn_spider) -> None:
        """Test spider has correct attributes."""
        assert cnn_spider.name == "cnn"
        assert cnn_spider.domain == "cnn.com"
        assert "cnn.com" in cnn_spider.allowed_domains
        assert len(cnn_spider.start_urls) > 0

    def test_is_article_page_with_article(self, cnn_spider) -> None:
        """Test is_article_page returns True for article pages."""
        request = Request(url="https://www.cnn.com/test-article")
        response = HtmlResponse(
            url="https://www.cnn.com/test-article",
            request=request,
            body=b'<html><body data-page-type="article"></body></html>',
            encoding="utf-8",
        )
        assert cnn_spider.is_article_page(response) is True

    def test_is_article_page_without_article(self, cnn_spider):
        """Test is_article_page returns False for non-article pages."""
        request = Request(url="https://www.cnn.com")
        response = HtmlResponse(
            url="https://www.cnn.com",
            request=request,
            body=b'<html><body data-page-type="homepage"></body></html>',
            encoding="utf-8",
        )
        assert cnn_spider.is_article_page(response) is False


@pytest.fixture
def bbc_spider() -> BBCSpider:
    """Fixture for BBCSpider."""
    return BBCSpider()


class TestBBCSpider:
    """Test cases for BBCSpider."""

    def test_spider_attributes(self, bbc_spider) -> None:
        """Test spider has correct attributes."""
        assert bbc_spider.name == "bbc"
        assert bbc_spider.domain == "bbc.com"
        assert "bbc.com" in bbc_spider.allowed_domains
        assert len(bbc_spider.start_urls) > 0

    def test_is_article_page_with_og_type(self, bbc_spider) -> None:
        """Test is_article_page returns True when og:type is article."""
        request = Request(url="https://www.bbc.com/news/test-article")
        response = HtmlResponse(
            url="https://www.bbc.com/news/test-article",
            request=request,
            body=b'<html><head><meta property="og:type" content="article"/></head><body></body></html>',
            encoding="utf-8",
        )
        assert bbc_spider.is_article_page(response) is True

    def test_is_article_page_with_article_tag(self, bbc_spider) -> None:
        """Test is_article_page returns True when article tag exists."""
        request = Request(url="https://www.bbc.com/news/test-article")
        response = HtmlResponse(
            url="https://www.bbc.com/news/test-article",
            request=request,
            body=b"<html><body><article>Content</article></body></html>",
            encoding="utf-8",
        )
        assert bbc_spider.is_article_page(response) is True

    def test_is_article_page_without_article(self, bbc_spider) -> None:
        """Test is_article_page returns False for non-article pages."""
        request = Request(url="https://www.bbc.com/news")
        response = HtmlResponse(
            url="https://www.bbc.com/news",
            request=request,
            body=b"<html><body><div>News list</div></body></html>",
            encoding="utf-8",
        )
        assert bbc_spider.is_article_page(response) is False


@pytest.fixture
def foxnews_spider() -> FoxNewsSpider:
    """Fixture for FoxNewsSpider."""
    return FoxNewsSpider()


class TestFoxNewsSpider:
    """Test cases for FoxNewsSpider."""

    def test_spider_attributes(self, foxnews_spider) -> None:
        """Test spider has correct attributes."""
        assert foxnews_spider.name == "foxnews"
        assert foxnews_spider.domain == "foxnews.com"
        assert "foxnews.com" in foxnews_spider.allowed_domains


@pytest.fixture
def nytimes_spider() -> NYTimesSpider:
    """Fixture for NYTimesSpider."""
    return NYTimesSpider()


class TestNYTimesSpider:
    """Test cases for NYTimesSpider."""

    def test_spider_attributes(self, nytimes_spider) -> None:
        """Test spider has correct attributes."""
        assert nytimes_spider.name == "nytimes"
        assert nytimes_spider.domain == "nytimes.com"
        assert "nytimes.com" in nytimes_spider.allowed_domains


@pytest.fixture
def guardian_spider() -> GuardianSpider:
    """Fixture for GuardianSpider."""
    return GuardianSpider()


class TestGuardianSpider:
    """Test cases for GuardianSpider."""

    def test_spider_attributes(self, guardian_spider) -> None:
        """Test spider has correct attributes."""
        assert guardian_spider.name == "guardian"
        assert guardian_spider.domain == "theguardian.com"
        assert "theguardian.com" in guardian_spider.allowed_domains


@pytest.fixture
def nbcnews_spider() -> NBCNewsSpider:
    """Fixture for NBCNewsSpider."""
    return NBCNewsSpider()


class TestNBCNewsSpider:
    """Test cases for NBCNewsSpider."""

    def test_spider_attributes(self, nbcnews_spider) -> None:
        """Test spider has correct attributes."""
        assert nbcnews_spider.name == "nbcnews"
        assert nbcnews_spider.domain == "nbcnews.com"
        assert "nbcnews.com" in nbcnews_spider.allowed_domains


@pytest.fixture
def apnews_spider() -> APNewsSpider:
    """Fixture for APNewsSpider."""
    return APNewsSpider()


class TestAPNewsSpider:
    """Test cases for APNewsSpider."""

    def test_spider_attributes(self, apnews_spider):
        """Test spider has correct attributes."""
        assert apnews_spider.name == "apnews"
        assert apnews_spider.domain == "apnews.com"
        assert "apnews.com" in apnews_spider.allowed_domains


@pytest.fixture
def cbsnews_spider() -> CBSNewsSpider:
    """Fixture for CBSNewsSpider."""
    return CBSNewsSpider()


class TestCBSNewsSpider:
    """Test cases for CBSNewsSpider."""

    def test_spider_attributes(self, cbsnews_spider) -> None:
        """Test spider has correct attributes."""
        assert cbsnews_spider.name == "cbsnews"
        assert cbsnews_spider.domain == "cbsnews.com"
        assert "cbsnews.com" in cbsnews_spider.allowed_domains


@pytest.fixture
def all_spiders() -> List[NewsSpider]:
    """Fixture that returns all spider instances."""
    return [
        CNNSpider(),
        BBCSpider(),
        FoxNewsSpider(),
        NYTimesSpider(),
        GuardianSpider(),
        NBCNewsSpider(),
        APNewsSpider(),
        CBSNewsSpider(),
    ]


class TestAllSpidersConsistency:
    """Test consistency across all spider implementations."""

    def test_all_spiders_have_unique_names(self, all_spiders):
        """Test that all spiders have unique names."""
        names = [spider.name for spider in all_spiders]
        assert len(names) == len(set(names)), "Spider names must be unique"

    def test_all_spiders_have_domains(self, all_spiders) -> None:
        """Test that all spiders have domain defined."""
        for spider in all_spiders:
            assert spider.domain is not None
            assert spider.domain != ""

    def test_all_spiders_have_allowed_domains(self, all_spiders) -> None:
        """Test that all spiders have allowed_domains defined."""
        for spider in all_spiders:
            assert isinstance(spider.allowed_domains, list)
            assert len(spider.allowed_domains) > 0

    def test_all_spiders_have_start_urls(self, all_spiders) -> None:
        """Test that all spiders have start_urls defined."""
        for spider in all_spiders:
            assert hasattr(spider, "start_urls")
            assert isinstance(spider.start_urls, list)
            assert len(spider.start_urls) > 0

    def test_all_spiders_have_custom_settings(self, all_spiders) -> None:
        """Test that all spiders inherit custom_settings."""
        for spider in all_spiders:
            assert hasattr(spider, "custom_settings")
            assert "USER_AGENT" in spider.custom_settings

    def test_all_spiders_have_is_article_page_method(self, all_spiders) -> None:
        """Test that all spiders implement is_article_page method."""
        for spider in all_spiders:
            assert hasattr(spider, "is_article_page")
            assert callable(spider.is_article_page)
