"""
AP News article extractor.

Extraction strategy:
- Primary: JSON-LD with @type == "NewsArticle"
- Secondary: DOM fallbacks for body content
- Confidence: 0.95 with JSON-LD + body > 500 chars, 0.80 for DOM only
"""

from datetime import datetime
from typing import Optional

from scrapy.http import Response

from news_scraper.extractors.base import (
    ArticleExtractor,
    ExtractedArticle,
    clean_text,
    extract_json_ld,
    normalize_paragraphs,
    parse_datetime_from_meta,
)


class APNewsExtractor(ArticleExtractor):
    """Extractor for AP News articles (apnews.com)."""

    name = "ap"

    def extract(self, response: Response) -> ExtractedArticle:
        """Extract article from AP News page."""
        errors = []
        title = None
        author = None
        published_at = None
        modified_at = None
        section = None
        tags = []
        body = None
        extraction_method = "dom"
        confidence = 0.0

        # Try JSON-LD first
        json_ld_data = extract_json_ld(response)
        json_ld_article = self._find_news_article(json_ld_data)

        if json_ld_article:
            title = self._extract_from_json_ld(json_ld_article, "headline", clean_text)
            author = self._extract_author_from_json_ld(json_ld_article)
            published_at = self._extract_date_from_json_ld(
                json_ld_article, "datePublished"
            )
            modified_at = self._extract_date_from_json_ld(
                json_ld_article, "dateModified"
            )
            section = self._extract_from_json_ld(
                json_ld_article, "articleSection", clean_text
            )

            # Extract keywords/tags
            keywords = json_ld_article.get("keywords")
            if keywords:
                if isinstance(keywords, str):
                    tags = [k.strip() for k in keywords.split(",") if k.strip()]
                elif isinstance(keywords, list):
                    tags = [str(k).strip() for k in keywords if k]

        # Extract body from DOM
        # AP JSON-LD does not include articleBody; body always comes from DOM
        # Try multiple selectors for body paragraphs
        paragraphs = response.css(".RichTextStoryBody p::text").getall()
        if not paragraphs:
            paragraphs = response.css("article p::text").getall()

        if paragraphs:
            body = normalize_paragraphs(paragraphs)
        else:
            errors.append("No article body paragraphs found")

        # Calculate confidence and set extraction method
        # Use 'hybrid' when JSON-LD metadata is combined with DOM body
        if json_ld_article and body and len(body) > 500:
            confidence = 0.95
            extraction_method = "hybrid"
        elif json_ld_article and body:
            confidence = 0.90
            extraction_method = "hybrid"
        elif body and len(body) > 500:
            confidence = 0.80
            extraction_method = "dom"
        elif body:
            confidence = 0.75
            extraction_method = "dom"
        else:
            confidence = 0.50
            errors.append("Low confidence: missing critical content")

        # DOM fallbacks if JSON-LD failed
        if not title:
            title = clean_text(response.css("h1::text").get())
            if not title:
                errors.append("Title not found in JSON-LD or DOM")

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

    def _find_news_article(self, json_ld_data: list) -> Optional[dict]:
        """Find NewsArticle object in JSON-LD data."""
        for item in json_ld_data:
            if item.get("@type") == "NewsArticle":
                return item
        return None

    def _extract_from_json_ld(
        self, data: dict, key: str, transform=None
    ) -> Optional[str]:
        """Extract and optionally transform a value from JSON-LD."""
        value = data.get(key)
        if value and transform:
            return transform(value)
        return value

    def _extract_author_from_json_ld(self, data: dict) -> Optional[str]:
        """Extract author from JSON-LD author field."""
        author_data = data.get("author")
        if not author_data:
            return None

        # Handle string
        if isinstance(author_data, str):
            return clean_text(author_data)

        # Handle dict with name
        if isinstance(author_data, dict):
            name = author_data.get("name")
            if name:
                return clean_text(name)

        # Handle list of authors
        if isinstance(author_data, list):
            names = []
            for a in author_data:
                if isinstance(a, str):
                    names.append(a)
                elif isinstance(a, dict) and a.get("name"):
                    names.append(a["name"])
            if names:
                return clean_text(", ".join(names))

        return None

    def _extract_date_from_json_ld(self, data: dict, key: str) -> Optional[datetime]:
        """Extract and parse date from JSON-LD."""
        date_str = data.get(key)
        if date_str:
            return parse_datetime_from_meta(date_str)
        return None
