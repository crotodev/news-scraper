"""
BBC article extractor.

Extraction strategy:
- Primary: DOM selectors (BBC has clean, consistent HTML structure)
- Body: div[data-component="text-block"] p
- Title: h1
- Date: time[datetime]
- Author: often missing (acceptable)
- Confidence: capped at 0.90
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


class BBCExtractor(ArticleExtractor):
    """Extractor for BBC articles (bbc.com)."""

    name = "bbc"

    def extract(self, response: Response) -> ExtractedArticle:
        """Extract article from BBC page."""
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

        # Extract title from h1, fallback to og:title meta tag
        title = clean_text(response.css("h1::text").get())
        if not title:
            # BBC often has title only in meta tags
            title = clean_text(
                response.xpath('//meta[@property="og:title"]/@content').get()
            )
        if not title:
            errors.append("Title not found")

        # Extract body from article paragraphs (primary for BBC Sport and other pages)
        paragraphs = response.css("article p::text").getall()
        if paragraphs:
            body = normalize_paragraphs(paragraphs)
        else:
            # Fallback to text block component
            paragraphs = response.css(
                'div[data-component="text-block"] p::text'
            ).getall()
            if paragraphs:
                body = normalize_paragraphs(paragraphs)
            else:
                errors.append("No article body paragraphs found")

        # Extract date from time element
        time_elem = response.css("time::attr(datetime)").get()
        if time_elem:
            published_at = parse_datetime_from_meta(time_elem)
        else:
            # Try meta tag
            pub_meta = response.xpath(
                '//meta[@property="article:published_time"]/@content'
            ).get()
            if pub_meta:
                published_at = parse_datetime_from_meta(pub_meta)

        # Try to extract author (often missing on BBC)
        author_meta = response.xpath('//meta[@name="author"]/@content').get()
        if author_meta:
            author = clean_text(author_meta)
        else:
            # Try byline class
            author_text = response.css('[class*="byline"]::text').get()
            if author_text:
                author = clean_text(author_text)

        # Try JSON-LD for additional metadata
        json_ld_data = extract_json_ld(response)
        for item in json_ld_data:
            if item.get("@type") in ["NewsArticle", "Article"]:
                if not author and item.get("author"):
                    author_data = item["author"]
                    if isinstance(author_data, dict):
                        author = clean_text(author_data.get("name"))
                    elif isinstance(author_data, str):
                        author = clean_text(author_data)

                if not section and item.get("articleSection"):
                    section = clean_text(item["articleSection"])

                # Extract keywords
                keywords = item.get("keywords")
                if keywords and not tags:
                    if isinstance(keywords, str):
                        tags = [k.strip() for k in keywords.split(",") if k.strip()]
                    elif isinstance(keywords, list):
                        tags = [str(k).strip() for k in keywords if k]

        # Calculate confidence (capped at 0.90 per requirements)
        if body and len(body) > 500 and title:
            confidence = 0.90
        elif body and len(body) > 300 and title:
            confidence = 0.85
        elif body and title:
            confidence = 0.75
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
            confidence=min(confidence, 0.90),  # Hard cap at 0.90
            errors=errors,
        )
