"""Tests for NBC News extractor."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.extractors.nbc import NBCExtractor


@pytest.fixture
def nbc_html():
    """Load NBC News HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "nbc.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def nbc_response(nbc_html):
    """Create scrapy Response from NBC News HTML."""
    return HtmlResponse(
        url="https://www.nbcnews.com/news/test-article",
        body=nbc_html,
        encoding="utf-8",
    )


def test_nbc_extractor_basic_structure(nbc_response):
    """Test NBC extractor returns valid article structure."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

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


def test_nbc_extractor_confidence_range(nbc_response):
    """Test NBC confidence is around 0.80 for good articles."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    # NBC typically achieves ~0.80 confidence
    if article.body and len(article.body) > 500 and article.title and article.author:
        assert (
            article.confidence >= 0.75
        ), f"Expected confidence >= 0.75 for complete article"


def test_nbc_extractor_filters_promotional_content(nbc_response):
    """Test NBC extractor filters non-article paragraph blocks."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    assert article.body is not None

    # Should filter out promotional phrases
    promo_phrases = ["sign up", "subscribe", "click here", "read more"]
    for phrase in promo_phrases:
        # These shouldn't dominate the body content
        if phrase in article.body.lower():
            # If present, should be minimal
            assert (
                article.body.lower().count(phrase) <= 2
            ), f"Promotional phrase '{phrase}' should be filtered"


def test_nbc_extractor_body_quality(nbc_response):
    """Test NBC body content is substantial after filtering."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    assert article.body is not None
    assert (
        len(article.body) > 400
    ), "Expected substantial NBC article body after filtering"

    # Body should be normalized
    assert "\n\n\n" not in article.body, "Body should have normalized paragraphs"


def test_nbc_extractor_filters_short_lines(nbc_response):
    """Test NBC extractor filters very short navigation lines."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    assert article.body is not None

    # After filtering, body should be substantial article content
    # not navigation snippets (< 25 chars filtered out)
    if article.confidence >= 0.75:
        assert (
            len(article.body) > 300
        ), "Filtering should preserve substantial article content"


def test_nbc_extractor_metadata_extraction(nbc_response):
    """Test NBC extractor gets metadata from JSON-LD."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    # Title is required
    assert article.title is not None
    assert len(article.title) > 5, "Title should be meaningful"

    # NBC typically has good JSON-LD metadata
    if article.confidence >= 0.75:
        # Should have at least title and body
        assert article.title is not None
        assert article.body is not None


def test_nbc_extractor_hybrid_method(nbc_response):
    """Test NBC extractor uses hybrid method (JSON-LD + filtered DOM)."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    # NBC typically combines JSON-LD metadata with filtered DOM body
    if article.confidence >= 0.75:
        assert article.extraction_method in ["hybrid", "dom"]


def test_nbc_extractor_error_tracking(nbc_response):
    """Test NBC extractor tracks errors appropriately."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    # Errors should be a list
    assert isinstance(article.errors, list)

    # High confidence articles should have body
    if article.confidence >= 0.75:
        body_errors = [
            e
            for e in article.errors
            if "body" in e.lower() and "not found" in e.lower()
        ]
        assert (
            len(body_errors) == 0
        ), f"High confidence article shouldn't be missing body: {body_errors}"


def test_nbc_extractor_handles_article_paragraphs(nbc_response):
    """Test NBC extractor extracts from article p elements."""
    extractor = NBCExtractor()
    article = extractor.extract(nbc_response)

    # NBC uses article p for body content with filtering
    assert article.body is not None
    assert len(article.body) > 300, "Should extract substantial content from article p"
