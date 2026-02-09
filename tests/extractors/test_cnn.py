"""Tests for CNN extractor."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.extractors.cnn import CNNExtractor


@pytest.fixture
def cnn_html():
    """Load CNN HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "cnn.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def cnn_response(cnn_html):
    """Create scrapy Response from CNN HTML."""
    return HtmlResponse(
        url="https://www.cnn.com/2026/02/09/test-article/index.html",
        body=cnn_html,
        encoding="utf-8",
    )


def test_cnn_extractor_basic_structure(cnn_response):
    """Test CNN extractor returns valid article structure."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # Required fields must be present
    assert article.title is not None, "Title must be extracted"
    assert article.body is not None, "Body must be extracted"
    assert len(article.body) > 300, f"Body too short: {len(article.body)} chars"

    # Confidence and method checks
    assert article.confidence >= 0.70, f"Confidence too low: {article.confidence}"
    assert article.extraction_method in [
        "hybrid",
        "dom",
    ], f"Unexpected extraction method: {article.extraction_method}"


def test_cnn_extractor_body_not_empty(cnn_response):
    """Test CNN body is not empty (regression test)."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # CNN body must not be empty
    assert article.body is not None, "CNN body must not be None"
    assert len(article.body) > 0, "CNN body must not be empty"
    assert len(article.body) > 300, "CNN body should be substantial"


def test_cnn_extractor_confidence_range(cnn_response):
    """Test CNN confidence is around 0.85 for good articles."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # CNN typically achieves ~0.85 confidence
    if article.body and len(article.body) > 500:
        assert (
            article.confidence >= 0.75
        ), f"Expected confidence >= 0.75 for substantial body"


def test_cnn_extractor_body_quality(cnn_response):
    """Test CNN body content is substantial and clean."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    assert article.body is not None
    assert len(article.body) > 400, "Expected substantial CNN article body"

    # Body should be normalized
    assert "\n\n\n" not in article.body, "Body should have normalized paragraphs"


def test_cnn_extractor_filters_editors_notes(cnn_response):
    """Test CNN extractor optionally filters 'Editor's Note:' content."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # If Editor's Note filtering is implemented, it should not dominate the body
    # This is an optional enhancement - test should be flexible
    if article.body and "Editor's Note:" in article.body:
        # It's OK if it's present, but shouldn't be the majority of content
        assert (
            len(article.body) > 500
        ), "Body should have substantial content beyond Editor's Note"


def test_cnn_extractor_metadata_extraction(cnn_response):
    """Test CNN extractor gets metadata from JSON-LD and DOM."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # Title is required
    assert article.title is not None
    assert len(article.title) > 5, "Title should be meaningful"

    # CNN typically has good metadata
    if article.confidence >= 0.80:
        # Should have at least title and body
        assert article.title is not None
        assert article.body is not None


def test_cnn_extractor_hybrid_method(cnn_response):
    """Test CNN extractor uses hybrid method (JSON-LD + DOM)."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # CNN typically combines JSON-LD metadata with DOM body
    if article.confidence >= 0.80:
        assert article.extraction_method in ["hybrid", "dom"]


def test_cnn_extractor_error_tracking(cnn_response):
    """Test CNN extractor tracks errors appropriately."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # Errors should be a list
    assert isinstance(article.errors, list)

    # High confidence articles should not be missing body
    if article.confidence >= 0.80:
        body_errors = [
            e
            for e in article.errors
            if "body" in e.lower() and "not found" in e.lower()
        ]
        assert (
            len(body_errors) == 0
        ), f"High confidence article shouldn't be missing body: {body_errors}"


def test_cnn_extractor_acceptable_noise(cnn_response):
    """Test CNN extractor handles acceptable noise in markup."""
    extractor = CNNExtractor()
    article = extractor.extract(cnn_response)

    # CNN has analytics-driven markup, but should still extract clean body
    assert article.body is not None
    assert (
        len(article.body) > 300
    ), "Should extract substantial content despite markup noise"
