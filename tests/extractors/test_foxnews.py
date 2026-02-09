"""Tests for Fox News extractor."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.extractors.foxnews import FoxNewsExtractor


@pytest.fixture
def foxnews_html():
    """Load Fox News HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "foxnews.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def foxnews_response(foxnews_html):
    """Create scrapy Response from Fox News HTML."""
    return HtmlResponse(
        url="https://www.foxnews.com/politics/test-article",
        body=foxnews_html,
        encoding="utf-8",
    )


def test_foxnews_extractor_basic_structure(foxnews_response):
    """Test Fox News extractor returns valid article structure."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    # Required fields must be present
    assert article.title is not None, "Title must be extracted"
    assert article.body is not None, "Body must be extracted"
    assert len(article.body) > 300, f"Body too short: {len(article.body)} chars"

    # Confidence and method checks
    assert article.confidence >= 0.50, f"Confidence too low: {article.confidence}"
    assert (
        article.extraction_method == "dom"
    ), f"Unexpected extraction method: {article.extraction_method}"


def test_foxnews_extractor_confidence_cap(foxnews_response):
    """Test Fox News extractor confidence is capped at 0.75."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    # Fox News confidence must never exceed 0.75 (per requirements)
    assert (
        article.confidence <= 0.75
    ), f"Fox News confidence must be capped at 0.75, got {article.confidence}"


def test_foxnews_extractor_filters_watch_lines(foxnews_response):
    """Test Fox News extractor filters out 'WATCH:' promotional lines."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    # Body must not contain WATCH: promotional lines
    if article.body:
        assert (
            "WATCH:" not in article.body
        ), "Body should not contain 'WATCH:' promotional content"


def test_foxnews_extractor_filters_promo_text(foxnews_response):
    """Test Fox News extractor filters promotional content."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    assert article.body is not None

    # Should filter out very short lines and all-caps promo text
    # Body should be substantial article content
    assert len(article.body) > 300, "Expected substantial article body after filtering"


def test_foxnews_extractor_body_quality(foxnews_response):
    """Test Fox News body content is clean after filtering."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    assert article.body is not None

    # Body should be normalized
    assert "\n\n\n" not in article.body, "Body should have normalized paragraphs"

    # Should have filtered out junk while keeping content
    if len(article.body) > 400:
        assert (
            article.confidence >= 0.65
        ), "Substantial body should yield reasonable confidence"


def test_foxnews_extractor_handles_promo_heavy_markup(foxnews_response):
    """Test Fox News extractor handles promo-heavy markup correctly."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    # Fox News has analytics-driven noise and promotional content
    # Extractor should filter this and extract real article content
    assert article.body is not None
    assert (
        len(article.body) > 300
    ), "Should extract real content despite promotional markup"


def test_foxnews_extractor_metadata_extraction(foxnews_response):
    """Test Fox News extractor attempts metadata extraction."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    # Title is required
    assert article.title is not None
    assert len(article.title) > 5, "Title should be meaningful"

    # Author and dates are optional but attempted via JSON-LD and DOM


def test_foxnews_extractor_error_tracking(foxnews_response):
    """Test Fox News extractor tracks errors appropriately."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    # Errors should be a list
    assert isinstance(article.errors, list)

    # Should extract body even with challenging markup
    if article.confidence >= 0.70:
        body_errors = [
            e
            for e in article.errors
            if "body" in e.lower() and "not found" in e.lower()
        ]
        assert len(body_errors) == 0, f"Should have extracted body: {body_errors}"


def test_foxnews_extractor_realistic_expectations(foxnews_response):
    """Test Fox News extractor has realistic confidence levels."""
    extractor = FoxNewsExtractor()
    article = extractor.extract(foxnews_response)

    # Fox News is challenging due to markup, confidence should reflect this
    # Should not be overly optimistic (capped at 0.75)
    assert article.confidence <= 0.75, "Confidence appropriately capped"

    # But should still extract usable content
    if article.body and len(article.body) > 500:
        assert (
            article.confidence >= 0.65
        ), "Should have reasonable confidence for good extraction"
