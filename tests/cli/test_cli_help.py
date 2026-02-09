"""Verify that ``--help`` exits cleanly."""

from typer.testing import CliRunner

from news_scraper.cli import app

runner = CliRunner()


class TestCliHelp:
    def test_app_help_exits_zero(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_crawl_help_exits_zero(self):
        result = runner.invoke(app, ["crawl", "--help"])
        assert result.exit_code == 0

    def test_crawl_help_shows_spider_argument(self):
        result = runner.invoke(app, ["crawl", "--help"])
        assert "SPIDER" in result.output or "spider" in result.output.lower()

    def test_crawl_help_shows_rich_option(self):
        result = runner.invoke(app, ["crawl", "--help"])
        assert "--rich" in result.output or "--no-rich" in result.output
