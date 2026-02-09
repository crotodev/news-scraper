"""
NBC News article extractor.

Extraction strategy:
- Primary: JSON-LD for metadata
- Body: article p (with filtering)
- Filter non-article paragraph blocks
- Confidence: ~0.80
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


class NBCExtractor(ArticleExtractor):
    """Extractor for NBC News articles (nbcnews.com)."""

    name = "nbc"

    def extract(self, response: Response) -> ExtractedArticle:
        """Extract article from NBC News page."""
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

                # Extract keywords
                keywords = item.get("keywords")
                if keywords and not tags:
                    if isinstance(keywords, str):
                        tags = [k.strip() for k in keywords.split(",") if k.strip()]
                    elif isinstance(keywords, list):
                        tags = [str(k).strip() for k in keywords if k]

        # Extract body from article paragraphs with filtering
        paragraphs = response.css("article p::text").getall()

        # Filter out non-article content
        filtered_paragraphs = []
        for para in paragraphs:
            para_text = para.strip()
            # Skip empty paragraphs
            if not para_text:
                continue
            # Skip very short lines (likely navigation/metadata)
            if len(para_text) < 25:
                continue
            # Skip promotional text patterns
            if any(
                phrase in para_text.lower()
                for phrase in ["sign up", "subscribe", "click here", "read more"]
            ):
                continue
            filtered_paragraphs.append(para_text)

        if filtered_paragraphs:
            body = normalize_paragraphs(filtered_paragraphs)
        else:
            # Fallback without filtering
            if paragraphs:
                body = normalize_paragraphs(paragraphs)
            else:
                errors.append("No article body paragraphs found")

        # DOM fallbacks
        if not title:
            title = clean_text(response.css("h1::text").get())

        if not author:
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

        # Calculate confidence (~0.80 per requirements)
        if body and len(body) > 500 and title and author:
            confidence = 0.80
        elif body and len(body) > 500 and title:
            confidence = 0.78
        elif body and title:
            confidence = 0.70
        else:
            confidence = 0.60
            errors.append("Low confidence: missing critical content")

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
