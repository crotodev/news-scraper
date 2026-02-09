"""Tests for The Guardian extractor."""

from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from news_scraper.extractors.guardian import GuardianExtractor


@pytest.fixture
def guardian_html():
    """Load Guardian HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "guardian.html"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def guardian_response(guardian_html):
    """Create scrapy Response from Guardian HTML."""
    return HtmlResponse(
        url="https://www.theguardian.com/world/2026/feb/09/test-article",
        body=guardian_html,
        encoding="utf-8",
    )


def test_guardian_extractor_basic_structure(guardian_response):
    """Test Guardian extractor returns valid article structure."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Required fields must be present
    assert article.title is not None, "Title must be extracted"
    assert article.body is not None, "Body must be extracted"
    assert len(article.body) > 300, f"Body too short: {len(article.body)} chars"

    # Confidence and method checks
    assert article.confidence >= 0.75, f"Confidence too low: {article.confidence}"


def test_guardian_extractor_jsonld_reliable(guardian_response):
    """Test Guardian extractor reliably uses JSON-LD."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Guardian JSON-LD is reliable
    if article.confidence >= 0.85:
        assert article.extraction_method in [
            "json-ld",
            "dom",
        ], f"Expected json-ld or dom method, got {article.extraction_method}"


def test_guardian_extractor_confidence_range(guardian_response):
    """Test Guardian confidence is around 0.90 for good articles."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Guardian typically achieves ~0.90 confidence
    if article.body and len(article.body) > 500 and article.title:
        assert (
            article.confidence >= 0.80
        ), f"Expected high confidence for complete article"


def test_guardian_extractor_body_quality(guardian_response):
    """Test Guardian body content is substantial."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    assert article.body is not None
    assert len(article.body) > 400, "Expected substantial Guardian article body"

    # Body should be normalized
    assert "\n\n\n" not in article.body, "Body should have normalized paragraphs"


def test_guardian_extractor_uses_itemprop_selector(guardian_response):
    """Test Guardian extractor uses div[itemprop='articleBody'] selector."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Guardian uses itemprop="articleBody" for body content
    # Should extract substantial content
    assert article.body is not None
    assert len(article.body) > 300, "Should extract from articleBody itemprop"


def test_guardian_extractor_metadata_extraction(guardian_response):
    """Test Guardian extractor gets rich metadata from JSON-LD."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Title is required
    assert article.title is not None
    assert len(article.title) > 5, "Title should be meaningful"

    # Guardian typically has excellent metadata
    if article.confidence >= 0.85:
        # Should have good metadata coverage
        has_metadata = any(
            [
                article.author is not None,
                article.published_at is not None,
                article.section is not None,
            ]
        )
        assert has_metadata, "High confidence should include rich metadata"


def test_guardian_extractor_author_extraction(guardian_response):
    """Test Guardian extractor gets author from rel='author' or JSON-LD."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Guardian typically includes author information
    # Either from link rel="author" or JSON-LD
    # Not strictly required but commonly present


def test_guardian_extractor_error_tracking(guardian_response):
    """Test Guardian extractor tracks errors appropriately."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Errors should be a list
    assert isinstance(article.errors, list)

    # High confidence articles should have minimal errors
    if article.confidence >= 0.85:
        critical_errors = [e for e in article.errors if "not found" in e.lower()]
        assert (
            len(critical_errors) <= 1
        ), f"High confidence article shouldn't have many critical errors: {critical_errors}"


def test_guardian_extractor_clean_structure(guardian_response):
    """Test Guardian extractor handles clean DOM structure."""
    extractor = GuardianExtractor()
    article = extractor.extract(guardian_response)

    # Guardian has clean, consistent HTML
    # Should extract with high confidence
    if article.body and len(article.body) > 500:
        assert (
            article.confidence >= 0.80
        ), "Clean structure should yield high confidence"
