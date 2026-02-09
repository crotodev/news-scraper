"""Verify CLI works without Rich installed (graceful fallback)."""

import importlib
import sys
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

runner = CliRunner()


class TestCliNoRich:
    """Tests that exercise the CLI when Rich is unavailable."""

    def test_rich_available_false_when_import_fails(self):
        """RICH_AVAILABLE should be False when rich is not importable."""
        import news_scraper.cli as cli_mod

        # Block all rich.* submodules from importing
        blocked = {
            k: None for k in list(sys.modules) if k == "rich" or k.startswith("rich.")
        }
        blocked["rich"] = None
        blocked["rich.console"] = None
        blocked["rich.panel"] = None
        blocked["rich.progress"] = None
        blocked["rich.table"] = None
        blocked["rich.text"] = None

        original_rich_available = cli_mod.RICH_AVAILABLE

        try:
            with patch.dict(sys.modules, blocked):
                importlib.reload(cli_mod)
                assert cli_mod.RICH_AVAILABLE is False
        finally:
            # Restore the module to its original state
            importlib.reload(cli_mod)
            assert cli_mod.RICH_AVAILABLE == original_rich_available

    def test_should_use_rich_returns_false_when_unavailable(self):
        """_should_use_rich should return False when RICH_AVAILABLE is False."""
        import news_scraper.cli as cli_mod

        original = cli_mod.RICH_AVAILABLE
        try:
            cli_mod.RICH_AVAILABLE = False
            # Auto-detect (None) should return False
            assert cli_mod._should_use_rich(None) is False
            # Explicit True should still return False (not available)
            assert cli_mod._should_use_rich(True) is False
            # Explicit False should return False
            assert cli_mod._should_use_rich(False) is False
        finally:
            cli_mod.RICH_AVAILABLE = original

    def test_crawl_no_crawl_with_no_rich_flag(self):
        """crawl --no-crawl --no-rich should work (plain output path)."""
        from news_scraper.cli import app

        result = runner.invoke(app, ["crawl", "apnews", "--no-crawl", "--no-rich"])
        assert result.exit_code == 0

    def test_crawl_no_crawl_plain_output_shows_banner(self):
        """Plain output path should print a banner with spider info."""
        from news_scraper.cli import app

        result = runner.invoke(app, ["crawl", "apnews", "--no-crawl", "--no-rich"])
        assert "apnews" in result.output
        assert "News Scraper" in result.output
