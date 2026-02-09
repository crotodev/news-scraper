"""Verify that an invalid spider name produces a helpful error."""

from typer.testing import CliRunner

from news_scraper.cli import app

runner = CliRunner()


class TestCliInvalidSpider:
    def test_invalid_spider_exits_nonzero(self):
        result = runner.invoke(app, ["crawl", "nonexistent_spider", "--no-crawl"])
        assert result.exit_code != 0

    def test_invalid_spider_shows_error_message(self):
        result = runner.invoke(app, ["crawl", "nonexistent_spider", "--no-crawl"])
        assert (
            "Unknown spider" in result.output
            or "unknown spider" in result.output.lower()
        )

    def test_invalid_spider_lists_available(self):
        result = runner.invoke(app, ["crawl", "nonexistent_spider", "--no-crawl"])
        # Should mention at least one real spider name
        assert "apnews" in result.output or "bbc" in result.output
