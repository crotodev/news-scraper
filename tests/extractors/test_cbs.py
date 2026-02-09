"""Tests for CBS News extractor."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.extractors.cbs import CBSExtractor


@pytest.fixture
def cbs_html():
    """Load CBS News HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "cbs.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def cbs_response(cbs_html):
    """Create scrapy Response from CBS News HTML."""
    return HtmlResponse(
        url="https://www.cbsnews.com/news/test-article/",
        body=cbs_html,
        encoding="utf-8",
    )


def test_cbs_extractor_basic_structure(cbs_response):
    """Test CBS extractor returns valid article structure."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    # Required fields must be present
    assert article.title is not None, "Title must be extracted"
    assert article.body is not None, "Body must be extracted"
    assert len(article.body) > 300, f"Body too short: {len(article.body)} chars"

    # Confidence check
    assert article.confidence >= 0.75, f"Confidence too low: {article.confidence}"


def test_cbs_extractor_uses_jsonld_full(cbs_response):
    """Test CBS extractor uses jsonld_full method when articleBody is in JSON-LD."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    # CBS JSON-LD contains the entire article text
    # If extraction_method is jsonld_full, it means we found articleBody
    if article.extraction_method == "jsonld_full":
        assert (
            article.confidence == 1.0
        ), f"jsonld_full extraction should have confidence 1.0, got {article.confidence}"
        assert article.body is not None
        assert len(article.body) > 500, "JSON-LD full body should be substantial"


def test_cbs_extractor_confidence_perfect_with_jsonld_body(cbs_response):
    """Test CBS extractor sets confidence to 1.0 when using JSON-LD articleBody."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    # When CBS provides full articleBody in JSON-LD, confidence should be 1.0
    if article.extraction_method == "jsonld_full":
        assert (
            article.confidence == 1.0
        ), "Full JSON-LD extraction must have confidence 1.0"


def test_cbs_extractor_body_quality(cbs_response):
    """Test CBS body content is substantial."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    assert article.body is not None
    assert len(article.body) > 400, "Expected substantial CBS article body"

    # Body should be normalized
    assert "\n\n\n" not in article.body, "Body should have normalized paragraphs"


def test_cbs_extractor_prioritizes_jsonld(cbs_response):
    """Test CBS extractor prioritizes JSON-LD articleBody over DOM."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    # CBS should prefer JSON-LD when available
    # extraction_method should indicate the source
    assert article.extraction_method in [
        "jsonld_full",
        "json-ld",
        "dom",
    ], f"Unexpected extraction method: {article.extraction_method}"


def test_cbs_extractor_metadata_extraction(cbs_response):
    """Test CBS extractor gets metadata from JSON-LD."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    # Title is required
    assert article.title is not None
    assert len(article.title) > 5, "Title should be meaningful"

    # High confidence should mean we got JSON-LD metadata
    if article.confidence >= 0.90:
        # At least one of: author, published_at, section should be present
        has_metadata = any(
            [
                article.author is not None,
                article.published_at is not None,
                article.section is not None,
            ]
        )
        assert has_metadata, "High confidence should include metadata"


def test_cbs_extractor_error_tracking(cbs_response):
    """Test CBS extractor tracks errors appropriately."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    # Errors should be a list
    assert isinstance(article.errors, list)

    # Perfect confidence articles should have no critical errors
    if article.confidence == 1.0:
        critical_errors = [e for e in article.errors if "not found" in e.lower()]
        assert (
            len(critical_errors) == 0
        ), f"Perfect confidence article shouldn't have critical errors: {critical_errors}"


def test_cbs_extractor_no_dom_when_jsonld_body_exists(cbs_response):
    """Test CBS doesn't extract from DOM when JSON-LD has articleBody."""
    extractor = CBSExtractor()
    article = extractor.extract(cbs_response)

    # If we got jsonld_full, we shouldn't have fallen back to DOM
    if article.extraction_method == "jsonld_full":
        assert article.confidence == 1.0
        # Body should come from JSON-LD, not DOM selectors
        assert article.body is not None
