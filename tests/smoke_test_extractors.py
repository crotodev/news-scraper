#!/usr/bin/env python3
"""Quick smoke test for all extractors."""

from pathlib import Path

from scrapy.http import HtmlResponse

from news_scraper.extractors import (
    APNewsExtractor,
    BBCExtractor,
    CBSExtractor,
    CNNExtractor,
    FoxNewsExtractor,
    GuardianExtractor,
    NBCExtractor,
)


def test_extractor(name, extractor, fixture_path):
    """Test single extractor with fixture."""
    html = Path(fixture_path).read_text()
    response = HtmlResponse(url="https://example.com", body=html, encoding="utf-8")
    article = extractor.extract(response)

    has_content = article.title and article.body and article.confidence >= 0.6
    status = "✅" if has_content else "⚠️"
    body_len = len(article.body) if article.body else 0

    return f"{status} {name:12s} | conf={article.confidence:.2f} | body={body_len:5d} | method={article.extraction_method:12s}"


if __name__ == "__main__":
    extractors = [
        ("AP News", APNewsExtractor(), "tests/fixtures/ap.html"),
        ("BBC", BBCExtractor(), "tests/fixtures/bbc.html"),
        ("CBS", CBSExtractor(), "tests/fixtures/cbs.html"),
        ("CNN", CNNExtractor(), "tests/fixtures/cnn.html"),
        ("Fox News", FoxNewsExtractor(), "tests/fixtures/foxnews.html"),
        ("Guardian", GuardianExtractor(), "tests/fixtures/guardian.html"),
        ("NBC", NBCExtractor(), "tests/fixtures/nbc.html"),
    ]

    print("\n🧪 Extractor Smoke Test\n")
    print("=" * 70)
    for name, extractor, fixture in extractors:
        result = test_extractor(name, extractor, fixture)
        print(result)
    print("=" * 70)
