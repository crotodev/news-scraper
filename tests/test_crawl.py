"""
Integration tests for the crawl script.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crawl import get_spiders, build_jsonl_paths, main


class TestGetSpiders:
    """Test cases for get_spiders function."""

    def test_get_spiders_returns_list(self):
        """Test that get_spiders returns a list."""
        spiders = get_spiders()
        assert isinstance(spiders, list)

    def test_get_spiders_not_empty(self):
        """Test that get_spiders returns non-empty list."""
        spiders = get_spiders()
        assert len(spiders) > 0

    def test_all_spiders_have_name_attribute(self):
        """Test that all returned spiders have a name attribute."""
        spiders = get_spiders()
        for spider in spiders:
            assert hasattr(spider, "name")
            assert spider.name is not None


class TestBuildJsonlPaths:
    """Test cases for build_jsonl_paths function."""

    def test_build_jsonl_paths_returns_list(self):
        """Test that build_jsonl_paths returns a list."""
        spiders = get_spiders()
        paths = build_jsonl_paths(spiders)
        assert isinstance(paths, list)

    def test_build_jsonl_paths_length_matches_spiders(self):
        """Test that number of paths matches number of spiders."""
        spiders = get_spiders()
        paths = build_jsonl_paths(spiders)
        assert len(paths) == len(spiders)

    def test_build_jsonl_paths_format(self):
        """Test that paths have correct format."""
        spiders = get_spiders()
        paths = build_jsonl_paths(spiders)

        for path in paths:
            assert path.endswith("_items.jsonl")
            assert "data" in path

    def test_build_jsonl_paths_custom_dir(self):
        """Test build_jsonl_paths with custom directory."""
        spiders = get_spiders()
        custom_dir = "/tmp/test"
        paths = build_jsonl_paths(spiders, data_dir=custom_dir)

        for path in paths:
            assert path.startswith(custom_dir)


class TestMainFunction:
    """Test cases for main function."""

    @patch("crawl.CrawlerProcess")
    @patch("crawl.get_project_settings")
    def test_main_with_no_crawl_flag(self, mock_settings, mock_crawler):
        """Test main function with --no-crawl flag."""
        mock_settings.return_value = MagicMock()

        with patch("sys.argv", ["crawl.py", "--no-crawl"]):
            main(run_crawl=True)

        # CrawlerProcess should not be instantiated when --no-crawl is used
        mock_crawler.assert_not_called()

    @patch("crawl.CrawlerProcess")
    @patch("crawl.get_project_settings")
    def test_main_with_run_crawl_false(self, mock_settings, mock_crawler):
        """Test main function with run_crawl=False."""
        mock_settings.return_value = MagicMock()

        with patch("sys.argv", ["crawl.py"]):
            main(run_crawl=False)

        mock_crawler.assert_not_called()

    @patch("crawl.CrawlerProcess")
    @patch("crawl.get_project_settings")
    def test_main_schedules_all_spiders(self, mock_settings, mock_crawler):
        """Test that main schedules all spiders."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.get.return_value = "news_scraper.sinks.jsonl.JsonlSink"
        mock_settings.return_value = mock_settings_instance

        mock_process = MagicMock()
        mock_crawler.return_value = mock_process

        with patch("sys.argv", ["crawl.py"]):
            main(run_crawl=True)

        # Verify CrawlerProcess was created
        mock_crawler.assert_called_once()

        # Verify start was called
        mock_process.start.assert_called_once()

        # Verify crawl was called for each spider
        spiders = get_spiders()
        assert mock_process.crawl.call_count == len(spiders)

    @patch("crawl.CrawlerProcess")
    @patch("crawl.get_project_settings")
    def test_main_with_custom_sink_class(self, mock_settings, mock_crawler):
        """Test main function with custom sink class."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        mock_process = MagicMock()
        mock_crawler.return_value = mock_process

        custom_sink = "news_scraper.sinks.mongo.MongoSink"
        with patch("sys.argv", ["crawl.py", "--sink-class", custom_sink]):
            main(run_crawl=True)

        # Verify sink class was set
        mock_settings_instance.set.assert_any_call(
            "SINK_CLASS", custom_sink, priority="cmdline"
        )

    @patch("crawl.CrawlerProcess")
    @patch("crawl.get_project_settings")
    def test_main_with_log_level(self, mock_settings, mock_crawler):
        """Test main function with custom log level."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        mock_process = MagicMock()
        mock_crawler.return_value = mock_process

        with patch("sys.argv", ["crawl.py", "--log-level", "DEBUG"]):
            main(run_crawl=True)

        # Verify log level was set
        mock_settings_instance.set.assert_any_call(
            "LOG_LEVEL", "DEBUG", priority="cmdline"
        )

    @patch("crawl.CrawlerProcess")
    @patch("crawl.get_project_settings")
    def test_main_with_sink_settings_json(self, mock_settings, mock_crawler):
        """Test main function with sink settings as JSON."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        mock_process = MagicMock()
        mock_crawler.return_value = mock_process

        sink_settings = '{"path": "./custom/path.jsonl"}'
        with patch("sys.argv", ["crawl.py", "--sink-settings", sink_settings]):
            main(run_crawl=True)

        # Verify sink settings were parsed and set
        assert mock_settings_instance.set.called

    @patch("crawl.CrawlerProcess")
    @patch("crawl.get_project_settings")
    def test_main_with_sink_settings_keyval(self, mock_settings, mock_crawler):
        """Test main function with sink settings as key=value pairs."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        mock_process = MagicMock()
        mock_crawler.return_value = mock_process

        sink_settings = "path=./custom/path.jsonl,format=json"
        with patch("sys.argv", ["crawl.py", "--sink-settings", sink_settings]):
            main(run_crawl=True)

        # Verify settings were set
        assert mock_settings_instance.set.called
