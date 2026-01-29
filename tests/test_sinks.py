"""
Unit tests for sink implementations.
"""

import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch

from news_scraper.items import NewsItem
from news_scraper.sinks.jsonl import JsonlSink
from news_scraper.sinks.base import Sink


@pytest.fixture
def temp_dir():
    """Fixture for temporary directory."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def test_spider():
    """Fixture for test spider mock."""
    spider = Mock()
    spider.name = "test_spider"
    return spider


class TestBaseSink:
    """Test cases for base Sink class."""

    def test_base_sink_is_abstract(self):
        """Test that base Sink class has abstract methods."""
        sink = Sink()

        # Base methods should exist but do nothing
        assert sink.open(Mock()) is None
        assert sink.send(Mock()) is None
        assert sink.close() is None


class TestJsonlSink:
    """Test cases for JsonlSink."""

    def test_jsonl_sink_initialization(self):
        """Test JsonlSink initialization."""
        sink = JsonlSink()
        assert sink.path_template is not None
        assert sink._file is None

    def test_jsonl_sink_custom_path_template(self):
        """Test JsonlSink with custom path template."""
        custom_template = "./custom/{spider.name}_output.jsonl"
        sink = JsonlSink(path_template=custom_template)
        assert sink.path_template == custom_template

    def test_jsonl_sink_open_creates_directory(self, temp_dir, test_spider):
        """Test that open() creates necessary directories."""
        path_template = os.path.join(temp_dir, "data/{spider.name}_items.jsonl")
        sink = JsonlSink(path_template=path_template)

        sink.open(test_spider)

        expected_path = os.path.join(temp_dir, "data", "test_spider_items.jsonl")
        assert os.path.exists(os.path.dirname(expected_path))
        assert sink._file is not None

        sink.close()

    def test_jsonl_sink_send_writes_item(self, temp_dir, test_spider):
        """Test that send() writes items to file."""
        path_template = os.path.join(temp_dir, "{spider.name}_items.jsonl")
        sink = JsonlSink(path_template=path_template)

        # Create test item
        item = NewsItem()
        item["title"] = "Test Article"
        item["author"] = "Test Author"
        item["text"] = "Test content"
        item["url"] = "https://example.com/test"
        item["source"] = "test"

        sink.open(test_spider)
        sink.send(item)
        sink.close()

        # Verify file contents
        output_file = os.path.join(temp_dir, "test_spider_items.jsonl")
        assert os.path.exists(output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["title"] == "Test Article"
            assert data["author"] == "Test Author"

    def test_jsonl_sink_send_multiple_items(self, temp_dir, test_spider):
        """Test that send() correctly handles multiple items."""
        path_template = os.path.join(temp_dir, "{spider.name}_items.jsonl")
        sink = JsonlSink(path_template=path_template)

        sink.open(test_spider)

        # Send multiple items
        for i in range(3):
            item = NewsItem()
            item["title"] = f"Article {i}"
            item["text"] = f"Content {i}"
            item["url"] = f"https://example.com/article{i}"
            sink.send(item)

        sink.close()

        # Verify all items written
        output_file = os.path.join(temp_dir, "test_spider_items.jsonl")
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 3

            for i, line in enumerate(lines):
                data = json.loads(line)
                assert data["title"] == f"Article {i}"

    def test_jsonl_sink_send_without_open(self):
        """Test that send() handles being called before open()."""
        sink = JsonlSink()
        item = NewsItem()
        item["title"] = "Test"

        # Should not raise an error
        sink.send(item)

    def test_jsonl_sink_close_multiple_times(self, temp_dir, test_spider):
        """Test that close() can be called multiple times safely."""
        path_template = os.path.join(temp_dir, "{spider.name}_items.jsonl")
        sink = JsonlSink(path_template=path_template)

        sink.open(test_spider)
        sink.close()
        sink.close()  # Should not raise error

    def test_jsonl_sink_unicode_content(self, temp_dir, test_spider):
        """Test that JsonlSink correctly handles unicode content."""
        path_template = os.path.join(temp_dir, "{spider.name}_items.jsonl")
        sink = JsonlSink(path_template=path_template)

        item = NewsItem()
        item["title"] = "Test Article with émojis 🚀 and ünïcödé"
        item["text"] = "Content with 中文字符"
        item["url"] = "https://example.com/test"

        sink.open(test_spider)
        sink.send(item)
        sink.close()

        # Verify unicode is preserved
        output_file = os.path.join(temp_dir, "test_spider_items.jsonl")
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.loads(f.readline())
            assert "émojis 🚀" in data["title"]
            assert "中文字符" in data["text"]
