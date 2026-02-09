"""
Fox News article extractor.

Extraction strategy:
- Primary: DOM (JSON-LD often incomplete)
- Body: .article-body p
- Filter: Promo text, "WATCH:" lines, promotional content
- Confidence: capped at 0.75
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


class FoxNewsExtractor(ArticleExtractor):
    """Extractor for Fox News articles (foxnews.com)."""

    name = "foxnews"

    def extract(self, response: Response) -> ExtractedArticle:
        """Extract article from Fox News page."""
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

        # Extract title from h1
        title = clean_text(response.css("h1::text").get())
        if not title:
            errors.append("Title not found")

        # Extract body from .article-body paragraphs
        paragraphs = response.css(".article-body p::text").getall()

        # Filter out promotional content
        filtered_paragraphs = []
        for para in paragraphs:
            para_text = para.strip()
            # Skip empty paragraphs
            if not para_text:
                continue
            # Skip WATCH: promotional lines
            if para_text.upper().startswith("WATCH:"):
                continue
            # Skip very short lines (likely navigation/promo)
            if len(para_text) < 20:
                continue
            # Skip all-caps promotional text
            if para_text.isupper() and len(para_text) < 100:
                continue
            filtered_paragraphs.append(para_text)

        if filtered_paragraphs:
            body = normalize_paragraphs(filtered_paragraphs)
        else:
            # Fallback to article paragraphs without class filter
            paragraphs = response.css("article p::text").getall()
            if paragraphs:
                body = normalize_paragraphs(paragraphs)
            else:
                errors.append("No article body paragraphs found")

        # Try JSON-LD for metadata (often incomplete)
        json_ld_data = extract_json_ld(response)
        for item in json_ld_data:
            if item.get("@type") in ["NewsArticle", "Article"]:
                if not author:
                    author_data = item.get("author")
                    if isinstance(author_data, dict):
                        author = clean_text(author_data.get("name"))
                    elif isinstance(author_data, str):
                        author = clean_text(author_data)

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

        # DOM fallbacks for metadata
        if not author:
            # Try meta tag
            author_meta = response.xpath('//meta[@name="author"]/@content').get()
            if author_meta:
                author = clean_text(author_meta)
            else:
                # Try byline class
                author_text = response.css('[class*="author"]::text').get()
                if author_text:
                    author = clean_text(author_text)

        if not published_at:
            # Try meta tag
            pub_meta = response.xpath(
                '//meta[@property="article:published_time"]/@content'
            ).get()
            if pub_meta:
                published_at = parse_datetime_from_meta(pub_meta)
            else:
                # Try time element
                time_elem = response.css("time::attr(datetime)").get()
                if time_elem:
                    published_at = parse_datetime_from_meta(time_elem)

        # Calculate confidence (capped at 0.75 per requirements)
        if body and len(body) > 500 and title:
            confidence = 0.75
        elif body and len(body) > 300 and title:
            confidence = 0.70
        elif body and title:
            confidence = 0.65
        else:
            confidence = 0.50
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
            confidence=min(confidence, 0.75),  # Hard cap at 0.75
            errors=errors,
        )
