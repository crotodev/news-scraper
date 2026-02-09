# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsItem(scrapy.Item):
    """
    Canonical schema for scraped news articles.

    All fields are documented below with their expected types and constraints.
    See README.md for full schema documentation.
    """

    # === Core content fields ===
    title = scrapy.Field()  # str: Article headline (stripped whitespace)
    author = scrapy.Field()  # str | None: Author name(s), comma-separated if multiple
    text = scrapy.Field()  # str | None: Full article text (whitespace normalized)
    summary = (
        scrapy.Field()
    )  # str | None: Article summary (truncated to summary_max_chars)
    url = scrapy.Field()  # str: Original article URL
    source = scrapy.Field()  # str: Spider/source identifier (e.g. "cnn", "bbc")

    # === Timestamps (ISO-8601 UTC) ===
    published_at = scrapy.Field()  # str | None: ISO-8601 UTC, or None if not found
    scraped_at = scrapy.Field()  # str: ISO-8601 UTC (always present)

    # === Deduplication fields ===
    url_hash = (
        scrapy.Field()
    )  # str: SHA-256 of canonicalized URL (tracking params removed)
    fingerprint = (
        scrapy.Field()
    )  # str: SHA-256 of content basis (title + published_at + source, or title + first 2k chars of text)

    # === Author extraction metadata ===
    author_source = scrapy.Field()  # str: "feed" | "newspaper3k" | "meta" | "missing"

    # === Summary metadata ===
    summary_max_chars = scrapy.Field()  # int: Maximum allowed summary length (e.g. 512)
    summary_truncated = scrapy.Field()  # bool: True if summary was truncated

    # === Parse debug fields ===
    parse_ok = scrapy.Field()  # bool: True if parsing succeeded
    parse_error = scrapy.Field()  # str | None: Error message if parsing failed
    extraction_method = (
        scrapy.Field()
    )  # str: "newspaper3k" | "rss_only" | "html_fallback"
    content_length_chars = scrapy.Field()  # int: len(text) or 0 if no text
