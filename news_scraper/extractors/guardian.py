"""
The Guardian article extractor.

Extraction strategy:
- Primary: JSON-LD (reliable for Guardian)
- Body: div[itemprop="articleBody"] p
- Author: link with rel="author"
- Date: time[datetime]
- Confidence: ~0.90
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


class GuardianExtractor(ArticleExtractor):
    """Extractor for The Guardian articles (theguardian.com)."""

    name = "guardian"

    def extract(self, response: Response) -> ExtractedArticle:
        """Extract article from Guardian page."""
        errors = []
        title = None
        author = None
        published_at = None
        modified_at = None
        section = None
        tags = []
        body = None
        extraction_method = "json-ld"
        confidence = 0.0

        # Extract from JSON-LD (reliable for Guardian)
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

        # Extract body from itemprop="articleBody"
        paragraphs = response.css('div[itemprop="articleBody"] p::text').getall()
        if paragraphs:
            body = normalize_paragraphs(paragraphs)
        else:
            # Fallback to article paragraphs
            paragraphs = response.css("article p::text").getall()
            if paragraphs:
                body = normalize_paragraphs(paragraphs)
            else:
                errors.append("No article body paragraphs found")

        # DOM fallbacks
        if not title:
            title = clean_text(response.css("h1::text").get())

        if not author:
            # Try rel="author" link
            author_link = response.css('a[rel="author"]::text').get()
            if author_link:
                author = clean_text(author_link)
            else:
                # Try meta tag
                author_meta = response.xpath('//meta[@name="author"]/@content').get()
                if author_meta:
                    author = clean_text(author_meta)

        if not published_at:
            # Try time element
            time_elem = response.css("time::attr(datetime)").get()
            if time_elem:
                published_at = parse_datetime_from_meta(time_elem)

        # Calculate confidence (~0.90 per requirements)
        if body and len(body) > 500 and title and author:
            confidence = 0.90
        elif body and len(body) > 500 and title:
            confidence = 0.88
        elif body and title:
            confidence = 0.80
        else:
            confidence = 0.65
            errors.append("Low confidence: missing critical content")

        # Note if JSON-LD not found
        if not json_ld_data:
            extraction_method = "dom"
            errors.append("JSON-LD not found (unusual for Guardian)")

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
