"""
New York Times article extractor.

Extraction strategy:
- Primary: JSON-LD for metadata
- Body: section[name="articleBody"] p with multiple fallbacks
- Expect partial failures (NYT has complex layouts)
- Confidence: capped at 0.70
"""

from scrapy.http import Response

from news_scraper.extractors.base import (
    ArticleExtractor,
    ExtractedArticle,
    clean_text,
    extract_json_ld,
    normalize_paragraphs,
    parse_datetime_from_meta,
)


class NYTimesExtractor(ArticleExtractor):
    """Extractor for New York Times articles (nytimes.com)."""

    name = "nyt"

    def extract(self, response: Response) -> ExtractedArticle:
        """Extract article from NYT page."""
        errors = []
        title = None
        author = None
        published_at = None
        modified_at = None
        section = None
        tags = []
        body = None
        extraction_method = "hybrid"
        confidence = 0.0

        # Extract from JSON-LD
        json_ld_data = extract_json_ld(response)
        for item in json_ld_data:
            if item.get("@type") in ["NewsArticle", "Article"]:
                if not title:
                    title = clean_text(item.get("headline"))
                if not author:
                    author_data = item.get("author")
                    if isinstance(author_data, dict):
                        author = clean_text(author_data.get("name"))
                    elif isinstance(author_data, str):
                        author = clean_text(author_data)
                    elif isinstance(author_data, list) and author_data:
                        names = []
                        for a in author_data:
                            if isinstance(a, dict) and a.get("name"):
                                names.append(a["name"])
                            elif isinstance(a, str):
                                names.append(a)
                        if names:
                            author = clean_text(", ".join(names))

                if not published_at:
                    date_str = item.get("datePublished")
                    if date_str:
                        published_at = parse_datetime_from_meta(date_str)

                if not modified_at:
                    date_str = item.get("dateModified")
                    if date_str:
                        modified_at = parse_datetime_from_meta(date_str)

                if not section:
                    section = clean_text(item.get("articleSection"))

        # Multiple fallbacks for body extraction
        # Try 1: section[name="articleBody"]
        paragraphs = response.css('section[name="articleBody"] p::text').getall()

        # Try 2: article section p
        if not paragraphs:
            paragraphs = response.css("article section p::text").getall()

        # Try 3: div.article-body or similar
        if not paragraphs:
            paragraphs = response.css(
                'div[class*="article"] p::text, div[class*="story"] p::text'
            ).getall()

        # Try 4: Generic article paragraphs
        if not paragraphs:
            paragraphs = response.css("article p::text").getall()

        if paragraphs:
            body = normalize_paragraphs(paragraphs)
        else:
            errors.append("No article body paragraphs found (all fallbacks failed)")

        # DOM fallbacks for metadata
        if not title:
            title = clean_text(response.css("h1::text").get())
            if not title:
                # Try meta tag
                title_meta = response.xpath(
                    '//meta[@property="og:title"]/@content'
                ).get()
                if title_meta:
                    title = clean_text(title_meta)

        if not author:
            # Try meta[name="byl"] (NYT-specific)
            byl_meta = response.xpath('//meta[@name="byl"]/@content').get()
            if byl_meta:
                author_text = byl_meta.strip()
                # Often formatted as "By Author Name"
                if author_text.lower().startswith("by "):
                    author_text = author_text[3:]
                author = clean_text(author_text)
            else:
                # Try generic author meta
                author_meta = response.xpath('//meta[@name="author"]/@content').get()
                if author_meta:
                    author = clean_text(author_meta)

        if not published_at:
            # Try meta tag
            pub_meta = response.xpath(
                '//meta[@property="article:published_time"]/@content'
            ).get()
            if pub_meta:
                published_at = parse_datetime_from_meta(pub_meta)

        # Calculate confidence (capped at 0.70 per requirements due to complexity)
        if body and len(body) > 500 and title and author:
            confidence = 0.70
        elif body and len(body) > 500 and title:
            confidence = 0.68
        elif body and title:
            confidence = 0.60
        else:
            confidence = 0.50
            errors.append("Low confidence: missing critical content")

        # Expect partial failures
        if not author:
            errors.append("Author extraction failed (common for NYT)")
        if not body or len(body) < 300:
            errors.append("Body extraction may be incomplete (NYT complex layout)")

        return ExtractedArticle(
            title=title,
            body=body,
            author=author,
            published_at=published_at,
            modified_at=modified_at,
            section=section,
            tags=tags,
            extraction_method=extraction_method,
            confidence=min(confidence, 0.70),  # Hard cap at 0.70
            errors=errors,
        )
