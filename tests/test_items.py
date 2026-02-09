"""
Unit tests for news scraper items.
"""

import pytest

from news_scraper.items import NewsItem


class TestNewsItem:
    """Test cases for NewsItem."""

    def test_news_item_has_required_fields(self):
        """Test that NewsItem has all required fields."""
        item = NewsItem()

        # Test that all fields can be set
        item["title"] = "Test Title"
        item["author"] = "Test Author"
        item["text"] = "Test article text"
        item["summary"] = "Test summary"
        item["url"] = "https://example.com/article"
        item["source"] = "example.com"
        item["published_at"] = "2024-01-15T12:00:00"
        item["scraped_at"] = "2024-01-15T13:00:00"
        item["url_hash"] = "abc123hash"
        item["fingerprint"] = "def456fingerprint"

        # Verify all fields are set
        assert item["title"] == "Test Title"
        assert item["author"] == "Test Author"
        assert item["text"] == "Test article text"
        assert item["summary"] == "Test summary"
        assert item["url"] == "https://example.com/article"
        assert item["source"] == "example.com"
        assert item["published_at"] == "2024-01-15T12:00:00"
        assert item["scraped_at"] == "2024-01-15T13:00:00"
        assert item["url_hash"] == "abc123hash"
        assert item["fingerprint"] == "def456fingerprint"

    def test_news_item_field_names(self):
        """Test that NewsItem has correct field names."""
        item = NewsItem()
        expected_fields = {
            "title",
            "author",
            "text",
            "summary",
            "url",
            "source",
            "published_at",
            "scraped_at",
            "url_hash",
            "fingerprint",
        }

        # Get actual field names from the item
        actual_fields = set(item.fields.keys())

        assert expected_fields == actual_fields
