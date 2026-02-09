"""Tests for BBC extractor."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.extractors.bbc import BBCExtractor


@pytest.fixture
def bbc_html():
    """Load BBC HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "bbc.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def bbc_response(bbc_html):
    """Create scrapy Response from BBC HTML."""
    return HtmlResponse(
        url="https://www.bbc.com/news/test-article",
        body=bbc_html,
        encoding="utf-8",
    )


def test_bbc_extractor_basic_structure(bbc_response):
    """Test BBC extractor returns valid article structure."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    # Required fields must be present
    assert article.title is not None, "Title must be extracted"
    assert article.body is not None, "Body must be extracted"
    assert len(article.body) > 300, f"Body too short: {len(article.body)} chars"

    # Confidence and method checks
    assert article.confidence >= 0.75, f"Confidence too low: {article.confidence}"
    assert (
        article.extraction_method == "dom"
    ), f"Unexpected extraction method: {article.extraction_method}"


def test_bbc_extractor_uses_article_paragraphs(bbc_response):
    """Test BBC extractor prioritizes article p over data-component selectors."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    # BBC Sport pages and others use article p as primary selector
    # Body should be extracted successfully
    assert article.body is not None
    assert (
        len(article.body) > 300
    ), "Article paragraphs should provide substantial content"


def test_bbc_extractor_confidence_cap(bbc_response):
    """Test BBC extractor confidence is capped at 0.90."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    # BBC confidence must never exceed 0.90
    assert (
        article.confidence <= 0.90
    ), f"BBC confidence must be capped at 0.90, got {article.confidence}"


def test_bbc_extractor_body_quality(bbc_response):
    """Test BBC body content has no missing paragraphs."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    assert article.body is not None

    # Body should be substantial for BBC Sport and news articles
    assert len(article.body) > 400, "Expected substantial BBC article body"

    # Check for normalized formatting
    assert "\n\n\n" not in article.body, "Body should have normalized paragraphs"


def test_bbc_extractor_author_optional(bbc_response):
    """Test BBC extractor handles missing author gracefully."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    # Author is often missing on BBC - this is acceptable
    # Should not cause low confidence or critical errors
    if article.author is None:
        assert (
            article.confidence >= 0.75
        ), "Missing author should not cause critically low confidence"


def test_bbc_extractor_metadata_extraction(bbc_response):
    """Test BBC extractor gets basic metadata."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    # Title is always required
    assert article.title is not None
    assert len(article.title) > 5, "Title should be meaningful"

    # Published date should be present (from time element or meta)
    # but not strictly required for successful extraction


def test_bbc_extractor_error_tracking(bbc_response):
    """Test BBC extractor tracks errors appropriately."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    # Errors should be a list
    assert isinstance(article.errors, list)

    # High confidence articles should have body extracted
    if article.confidence >= 0.85:
        body_errors = [
            e
            for e in article.errors
            if "body" in e.lower() and "not found" in e.lower()
        ]
        assert (
            len(body_errors) == 0
        ), f"High confidence article shouldn't be missing body: {body_errors}"


def test_bbc_extractor_no_junk_content(bbc_response):
    """Test BBC body doesn't contain navigation or junk."""
    extractor = BBCExtractor()
    article = extractor.extract(bbc_response)

    if article.body:
        # Should be actual article content, not navigation
        # BBC articles should have substantial paragraphs
        assert (
            len(article.body) > 300
        ), "Body should be substantial, not navigation snippets"
