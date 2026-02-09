"""
Base classes and helper functions for deterministic article extraction.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from scrapy.http import Response


@dataclass
class ExtractedArticle:
    """
    Raw extracted article content from HTML.

    This is not the Scrapy item - it represents intermediate extraction results
    before being mapped to NewsItem fields.
    """

    title: Optional[str]
    body: Optional[str]
    author: Optional[str]
    published_at: Optional[datetime]
    modified_at: Optional[datetime]
    section: Optional[str]
    tags: List[str] = field(default_factory=list)

    extraction_method: str = "unknown"
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence is in valid range."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


class ArticleExtractor(ABC):
    """
    Abstract base class for platform-specific article extractors.

    Subclasses must:
    - Set the 'name' attribute
    - Implement extract() method
    """

    name: str = "base"

    @abstractmethod
    def extract(self, response: Response) -> ExtractedArticle:
        """
        Extract article data from a Scrapy Response.

        Rules:
        - No network requests
        - No retries
        - No NLP or summarization
        - HTML → structured data only

        Args:
            response: Scrapy Response object containing HTML

        Returns:
            ExtractedArticle with extracted content and metadata
        """
        raise NotImplementedError


# === Helper Functions ===


def extract_json_ld(response: Response) -> List[dict]:
    """
    Parse all <script type="application/ld+json"> blocks from HTML.

    Safely handles:
    - Arrays of objects
    - Invalid JSON
    - Missing scripts

    Args:
        response: Scrapy Response object

    Returns:
        List of parsed JSON-LD dictionaries
    """
    json_ld_data = []
    scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()

    for script in scripts:
        try:
            data = json.loads(script)
            # Handle both single objects and arrays
            if isinstance(data, list):
                json_ld_data.extend([item for item in data if isinstance(item, dict)])
            elif isinstance(data, dict):
                json_ld_data.append(data)
        except (json.JSONDecodeError, TypeError):
            # Skip invalid JSON
            continue

    return json_ld_data


def normalize_paragraphs(paragraphs: List[str]) -> str:
    """
    Normalize a list of paragraph strings into clean body text.

    Processing:
    - Strip whitespace from each paragraph
    - Drop empty paragraphs
    - Join with double newlines

    Args:
        paragraphs: List of raw paragraph strings

    Returns:
        Normalized body text with paragraphs separated by double newlines
    """
    cleaned = []
    for para in paragraphs:
        stripped = para.strip()
        if stripped:
            cleaned.append(stripped)

    return "\n\n".join(cleaned)


def parse_datetime_from_meta(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse datetime from HTML meta tags or JSON-LD.

    Attempts multiple ISO-8601 formats and returns None on failure.
    Does not invent dates - returns None if parsing fails.

    Args:
        date_str: Date string to parse

    Returns:
        datetime object or None
    """
    if not date_str:
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Try various ISO-8601 formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",  # 2026-01-29T12:00:00+00:00
        "%Y-%m-%dT%H:%M:%SZ",  # 2026-01-29T12:00:00Z
        "%Y-%m-%dT%H:%M:%S.%f%z",  # With microseconds
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",  # No timezone
        "%Y-%m-%d",  # Date only
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try Python's fromisoformat (more flexible)
    try:
        # Handle 'Z' suffix
        clean_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except (ValueError, TypeError):
        pass

    return None


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Clean and normalize text content.

    - Collapse multiple whitespace to single space
    - Strip leading/trailing whitespace
    - Return None for empty strings
    - Handle lists by joining with ", "

    Args:
        text: Raw text string or list of strings

    Returns:
        Cleaned text or None
    """
    if not text:
        return None

    # Handle lists (e.g., from JSON-LD articleSection which can be array)
    if isinstance(text, list):
        text = ", ".join(str(item) for item in text if item)
        if not text:
            return None

    # Convert to string if needed
    if not isinstance(text, str):
        text = str(text)

    # Collapse all whitespace (including newlines) to single spaces
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else None
