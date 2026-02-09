"""
CNN article extractor.

Extraction strategy:
- Hybrid: Combine JSON-LD metadata with DOM content
- Body: article p
- Author: JSON-LD or [data-testid="byline"]
- Date: meta[property="article:published_time"]
- Confidence: ~0.85
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


class CNNExtractor(ArticleExtractor):
    """Extractor for CNN articles (cnn.com)."""

    name = "cnn"

    def extract(self, response: Response) -> ExtractedArticle:
        """Extract article from CNN page."""
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

        # Extract from JSON-LD first
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

                # Extract keywords
                keywords = item.get("keywords")
                if keywords and not tags:
                    if isinstance(keywords, str):
                        tags = [k.strip() for k in keywords.split(",") if k.strip()]
                    elif isinstance(keywords, list):
                        tags = [str(k).strip() for k in keywords if k]

        # DOM fallbacks
        if not title:
            title = clean_text(response.css("h1::text").get())

        if not author:
            # Try data-testid="byline"
            byline = response.css('[data-testid="byline"]::text').get()
            if byline:
                author = clean_text(byline)
            else:
                # Try meta tag
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

        # Extract body from article paragraphs
        paragraphs = response.css("article p::text").getall()
        if paragraphs:
            body = normalize_paragraphs(paragraphs)
        else:
            # Fallback to generic paragraphs
            paragraphs = response.css("p::text").getall()
            if paragraphs:
                body = normalize_paragraphs(paragraphs)
            else:
                errors.append("No article body paragraphs found")

        # Calculate confidence (~0.85 per requirements)
        if body and len(body) > 500 and title and author:
            confidence = 0.85
        elif body and len(body) > 500 and title:
            confidence = 0.83
        elif body and title:
            confidence = 0.75
        else:
            confidence = 0.60
            errors.append("Low confidence: missing critical content")

        # Add note if JSON-LD not found
        if not json_ld_data:
            extraction_method = "dom"
            errors.append("JSON-LD not found, using DOM extraction only")

        return ExtractedArticle(
            title=title,
            body=body,
            author=author,
            published_at=published_at,
            modified_at=modified_at,
            section=section,
            tags=tags,
            extraction_method=extraction_method,
            confidence=confidence,
            errors=errors,
        )
