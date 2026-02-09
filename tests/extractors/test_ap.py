"""Tests for AP News extractor."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.extractors.ap import APNewsExtractor


@pytest.fixture
def ap_html():
    """Load AP News HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "ap.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def ap_response(ap_html):
    """Create scrapy Response from AP News HTML."""
    return HtmlResponse(
        url="https://apnews.com/article/test-article",
        body=ap_html,
        encoding="utf-8",
    )


def test_ap_extractor_basic_structure(ap_response):
    """Test AP News extractor returns valid article structure."""
    extractor = APNewsExtractor()
    article = extractor.extract(ap_response)

    # Required fields must be present
    assert article.title is not None, "Title must be extracted"
    assert article.body is not None, "Body must be extracted"
    assert len(article.body) > 300, f"Body too short: {len(article.body)} chars"

    # Confidence and method checks
    assert article.confidence >= 0.80, f"Confidence too low: {article.confidence}"
    assert article.extraction_method in [
        "hybrid",
        "dom",
    ], f"Unexpected extraction method: {article.extraction_method}"


def test_ap_extractor_uses_hybrid_method(ap_response):
    """Test AP News extractor uses 'hybrid' method when JSON-LD + DOM."""
    extractor = APNewsExtractor()
    article = extractor.extract(ap_response)

    # AP JSON-LD does not include articleBody; body always comes from DOM
    # So when JSON-LD metadata exists, method should be 'hybrid'
    if article.confidence >= 0.90:
        assert (
            article.extraction_method == "hybrid"
        ), "High confidence articles should use hybrid extraction method"


def test_ap_extractor_body_quality(ap_response):
    """Test AP News body content is substantial and clean."""
    extractor = APNewsExtractor()
    article = extractor.extract(ap_response)

    assert article.body is not None
    assert len(article.body) > 500, "Expected substantial article body"

    # Body should be normalized (no excessive whitespace)
    assert "  " not in article.body, "Body should have normalized whitespace"
    assert "\n\n\n" not in article.body, "Body should have normalized paragraphs"


def test_ap_extractor_metadata_extraction(ap_response):
    """Test AP News extractor gets metadata from JSON-LD."""
    extractor = APNewsExtractor()
    article = extractor.extract(ap_response)

    # At least some metadata should be extracted
    # Title is required, others are optional but commonly present
    assert article.title is not None

    # If we have high confidence, we should have found JSON-LD metadata
    if article.confidence >= 0.90:
        # At least one of: author, published_at, section should be present
        has_metadata = any(
            [
                article.author is not None,
                article.published_at is not None,
                article.section is not None,
            ]
        )
        assert has_metadata, "High confidence should include JSON-LD metadata"


def test_ap_extractor_confidence_thresholds(ap_response):
    """Test AP News confidence scoring matches expected thresholds."""
    extractor = APNewsExtractor()
    article = extractor.extract(ap_response)

    # AP extractor confidence ranges
    assert 0.0 <= article.confidence <= 1.0, "Confidence must be in valid range"

    if article.body and len(article.body) > 500:
        # Should have high confidence with substantial body
        assert (
            article.confidence >= 0.80
        ), f"Expected confidence >= 0.80 for body length {len(article.body)}"


def test_ap_extractor_error_tracking(ap_response):
    """Test AP News extractor tracks errors appropriately."""
    extractor = APNewsExtractor()
    article = extractor.extract(ap_response)

    # Errors should be a list
    assert isinstance(article.errors, list)

    # High confidence articles should have no critical errors
    if article.confidence >= 0.90:
        critical_errors = [e for e in article.errors if "not found" in e.lower()]
        assert (
            len(critical_errors) == 0
        ), f"High confidence article shouldn't have critical errors: {critical_errors}"
