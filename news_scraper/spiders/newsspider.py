from datetime import datetime, timezone
from typing import Any, Generator, Optional
import hashlib
import re
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import scrapy
from random_user_agent.user_agent import UserAgent
from newspaper import Article, Config
from news_scraper.items import NewsItem


ua = UserAgent()

# Tracking parameters to strip from URLs for canonical url_hash
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_source_platform", "utm_creative_format", "utm_marketing_tactic",
    "gclid", "gclsrc", "dclid", "fbclid", "msclkid", "twclid", "igshid",
    "mc_cid", "mc_eid", "ref", "referer", "referrer", "source",
    "_ga", "_gl", "_hsenc", "_hsmi", "trk", "trkInfo",
}


def canonicalize_url_clean(url: str) -> str:
    """
    Canonicalize URL and remove tracking parameters for stable hashing.
    
    This removes common tracking params like utm_*, gclid, fbclid, etc.
    to ensure the same article from the same URL doesn't produce duplicates
    across runs with different referral sources.
    """
    
    try:
        parsed = urlparse(url)
        
        # Parse query params and filter out tracking params
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        filtered_params = {
            k: v for k, v in query_params.items() 
            if k.lower() not in TRACKING_PARAMS
        }
        
        # Rebuild URL with filtered params, sorted for consistency
        clean_query = urlencode(filtered_params, doseq=True) if filtered_params else ""
        
        # Normalize: lowercase scheme/host, remove trailing slash from path
        clean_path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        
        cleaned = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            clean_path,
            parsed.params,
            clean_query,
            ""  # Remove fragment
        ))
        return cleaned
    except Exception:
        return url


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """
    Collapse all whitespace (spaces, tabs, newlines) into single spaces.
    Returns None if input is None or empty after stripping.
    """
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized if normalized else None


def parse_iso8601_date(date_input) -> Optional[str]:
    """
    Parse various date formats and return ISO-8601 UTC string.
    
    Rules:
    - Never invent dates
    - If only date (no time), set time to 00:00:00Z (documented behavior)
    - Returns None if parsing fails
    
    Returns: ISO-8601 string in UTC (e.g., "2026-01-29T12:00:00Z") or None
    """
    if date_input is None:
        return None
    
    # If already a datetime object
    if isinstance(date_input, datetime):
        dt = date_input
        # Ensure UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # If string, try to parse
    if isinstance(date_input, str):
        date_str = date_input.strip()
        if not date_str:
            return None
        
        # Common ISO formats to try
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",      # 2026-01-29T12:00:00+00:00
            "%Y-%m-%dT%H:%M:%SZ",        # 2026-01-29T12:00:00Z
            "%Y-%m-%dT%H:%M:%S",         # 2026-01-29T12:00:00
            "%Y-%m-%d %H:%M:%S%z",       # 2026-01-29 12:00:00+00:00
            "%Y-%m-%d %H:%M:%S",         # 2026-01-29 12:00:00
            "%Y-%m-%d",                   # 2026-01-29 (date only -> 00:00:00Z)
            "%B %d, %Y",                  # January 29, 2026
            "%b %d, %Y",                  # Jan 29, 2026
            "%d %B %Y",                   # 29 January 2026
            "%d %b %Y",                   # 29 Jan 2026
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # If no timezone, assume UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
        
        # Try Python's fromisoformat (more flexible)
        try:
            # Handle 'Z' suffix
            clean_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            pass
    
    return None


class NewsSpider(scrapy.Spider):
    name = "news_scraper"
    domain = ""
    allowed_domains = []
    random_ua = ua.get_random_user_agent()

    config = Config()
    config.browser_user_agent = random_ua

    custom_settings = {
        "USER_AGENT": random_ua,
        "ROBOTSTXT_OBEY": True,
        "DEPTH_LIMIT": 50,
        "CONCURRENT_REQUESTS": 20,
    }

    # Minimum text length for a valid article (configurable per spider)
    MIN_ARTICLE_TEXT_LENGTH = 250
    
    # Maximum length for summary field (truncated if longer)
    SUMMARY_MAX_CHARS = 512
    
    # Maximum links to follow from a single page
    MAX_FOLLOW_PER_PAGE = 100
    
    # Deny-list for section/list page URL patterns
    SECTION_DENY_PATTERNS = [
        r"^/news/?$",
        r"^/world/?$",
        r"^/business/?$",
        r"^/markets/?$",
        r"^/technology/?$",
        r"^/politics/?$",
        r"^/opinion/?$",
        r"^/latest/?$",
        r"^/us/?$",
        r"^/uk/?$",
        r"^/sport/?$",
        r"^/sports/?$",
        r"^/entertainment/?$",
        r"^/lifestyle/?$",
        r"^/health/?$",
        r"^/science/?$",
        r"^/section/",
        r"^/hub/",
        r"^/topics?/",
        r"^/tag/",
        r"^/category/",
        r"^/author/",
        r"^/search",
        r"^/video/?$",
        r"^/videos/?$",
        r"^/live/?$",
        r"^/podcasts?/?$",
        r"^/?$",  # homepage
    ]
    
    # Feed/sitemap patterns to reject
    FEED_PATTERNS = ["rss", "feed", "sitemap", "atom"]

    def parse(
        self, response
    ) -> Generator[
        NewsItem | Any, Any, None
    ]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Parse strategy:
        1. If page is a real article, process and yield it
        2. Otherwise, treat as discovery page and extract article links
        """
        # Check if this is a real article page
        if self.is_article_page(response):
            item = self.process_article(response, self.domain, self.config)
            if item is not None:  # Only yield valid articles
                yield item
            return  # Don't follow links from articles
        
        # This is a section/discovery page - extract article links
        self.logger.debug(f"Discovery page: {response.url}")
        
        hrefs = response.css("a::attr(href)").getall()
        followed_count = 0
        
        for href in hrefs:
            if followed_count >= self.MAX_FOLLOW_PER_PAGE:
                break
                
            # Normalize URL
            abs_url = response.urljoin(href)
            
            # Validate and filter
            if not self.is_valid_url(abs_url):
                continue
            
            # Check if URL is from same domain
            if not self._is_same_domain(abs_url):
                continue
            
            # Check if URL looks like an article
            if self.is_article_url(abs_url):
                followed_count += 1
                yield response.follow(abs_url, callback=self.parse)
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to one of the allowed domains."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            return any(
                hostname == domain or hostname.endswith(f".{domain}")
                for domain in self.allowed_domains
            )
        except Exception:
            return False

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid HTTP(S) and not a feed/sitemap."""
        if not url.startswith(("http://", "https://")):
            return False
        
        url_lower = url.lower()
        # Reject feed/sitemap URLs
        for pattern in self.FEED_PATTERNS:
            if pattern in url_lower:
                return False
        
        return True

    def is_article_url(self, url: str) -> bool:
        """
        URL-only heuristic to determine if a URL looks like an article.
        Subclasses can override for site-specific patterns.
        
        Returns True if URL looks like an article, False otherwise.
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
        except Exception:
            return False
        
        # Reject section/list pages
        for pattern in self.SECTION_DENY_PATTERNS:
            if re.match(pattern, path, re.IGNORECASE):
                return False
        
        # Accept patterns that look like articles
        # Pattern 1: Contains /article/ or /articles/
        if "/article/" in path or "/articles/" in path:
            return True
        
        # Pattern 2: Date pattern like /2026/01/27/
        if re.search(r"/\d{4}/\d{2}/\d{2}/", path):
            return True
        
        # Pattern 3: Slug with ID style (-12345678 at end)
        if re.search(r"-\d{6,}$", path) or re.search(r"-\d{6,}\.html?$", path):
            return True
        
        # Pattern 4: Long slug (likely an article, not a section)
        # e.g., /this-is-a-long-article-headline
        slug_match = re.search(r"/([a-z0-9]+-){4,}[a-z0-9]+/?$", path)
        if slug_match:
            return True
        
        # Pattern 5: Contains /news/ with a sub-path (but not just /news/)
        if re.match(r"^/news/.+", path) and len(path) > 10:
            return True
        
        # Default: reject if path is too short (likely a section)
        if len(path.rstrip("/")) < 15:
            return False
        
        return True

    def is_article_page(self, response) -> bool:
        """
        Check if the response is an actual article page worth processing.
        Combines URL checks with page-level validation.
        
        Subclasses should override this for site-specific checks.
        """
        url = response.url
        
        # A) Check content-type (reject XML/JSON feeds)
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore").lower()
        if "xml" in content_type or "json" in content_type:
            return False
        
        # B) URL must pass basic article URL check
        if not self.is_article_url(url):
            return False
        
        # C) Check for common article page indicators
        # Look for og:type="article"
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        
        # Look for <article> tag
        if response.xpath("//article"):
            return True
        
        # Look for common article body classes
        article_indicators = [
            "//div[contains(@class, 'article-body')]",
            "//div[contains(@class, 'article-content')]",
            "//div[contains(@class, 'story-body')]",
            "//div[contains(@class, 'post-content')]",
            "//*[contains(@itemtype, 'Article')]",
        ]
        for xpath in article_indicators:
            if response.xpath(xpath):
                return True
        
        # If URL strongly suggests article, accept it
        parsed = urlparse(url)
        path = parsed.path.lower()
        if "/article/" in path or "/articles/" in path:
            return True
        if re.search(r"/\d{4}/\d{2}/\d{2}/.+", path):
            return True
        
        return False

    def process_article(self, response, source: str, config: Config) -> Optional[NewsItem]:
        """
        Process an article page and return a NewsItem.
        
        Always emits a row (for debugging/metrics), but sets parse_ok=False
        if parsing fails. This ensures the pipeline never crashes on individual
        article failures and allows measuring failure rate by source.
        """
        # Initialize item with guaranteed fields
        item = NewsItem()
        item["url"] = response.url
        item["source"] = source
        item["scraped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Initialize parse-debug fields
        item["parse_ok"] = False
        item["parse_error"] = None
        item["extraction_method"] = "newspaper3k"
        item["content_length_chars"] = 0
        
        article = Article(response.url, config=config)
        
        # Download and parse
        try:
            try:
                article.download(input_html=response.text)
            except TypeError:
                # API compatibility for different newspaper3k versions
                if hasattr(article, "set_html"):
                    article.set_html(response.text)
                elif hasattr(article, "set_article_html"):
                    article.set_article_html(response.text)
            
            article.parse()
        except Exception as e:
            item["parse_error"] = f"Parse failed: {str(e)[:200]}"
            item["title"] = None
            item["author"] = None
            item["author_source"] = "missing"
            item["text"] = None
            item["summary"] = None
            item["summary_max_chars"] = self.SUMMARY_MAX_CHARS
            item["summary_truncated"] = False
            item["published_at"] = None
            item["url_hash"] = self._compute_url_hash(response.url)
            item["fingerprint"] = self._compute_fingerprint(None, None, source, None)
            return item
        
        # Validate article has substance BEFORE expensive NLP
        if not self._validate_article_content(article, response.url):
            item["parse_error"] = "Content validation failed (too short or invalid)"
            item["title"] = normalize_whitespace(article.title)
            item["author"] = None
            item["author_source"] = "missing"
            item["text"] = None
            item["summary"] = None
            item["summary_max_chars"] = self.SUMMARY_MAX_CHARS
            item["summary_truncated"] = False
            item["published_at"] = parse_iso8601_date(article.publish_date)
            item["url_hash"] = self._compute_url_hash(response.url)
            item["fingerprint"] = self._compute_fingerprint(
                normalize_whitespace(article.title), 
                parse_iso8601_date(article.publish_date), 
                source, 
                None
            )
            return item
        
        # Run NLP for summary/keywords
        try:
            article.nlp()
        except Exception as e:
            # NLP failure is non-fatal, continue with what we have
            self.logger.debug(f"NLP processing failed for {response.url}: {e}")
        
        # === Extract and normalize text ===
        raw_text = article.text or ""
        normalized_text = normalize_whitespace(raw_text)
        
        # Low-quality text check: if text exists but < 200 chars, treat as low-quality
        # Keep summary but set text=None
        if normalized_text and len(normalized_text) < 200:
            normalized_text = None
        
        item["text"] = normalized_text
        item["content_length_chars"] = len(normalized_text) if normalized_text else 0
        
        # === Extract author with fallbacks ===
        author, author_source = self._extract_author(article, response)
        item["author"] = author
        item["author_source"] = author_source
        
        # === Extract and normalize title ===
        item["title"] = normalize_whitespace(article.title)
        
        # === Extract published_at ===
        item["published_at"] = parse_iso8601_date(article.publish_date)
        
        # === Generate summary with metadata ===
        summary, summary_truncated = self._get_summary_with_metadata(article)
        item["summary"] = summary
        item["summary_max_chars"] = self.SUMMARY_MAX_CHARS
        item["summary_truncated"] = summary_truncated
        
        # === Generate deduplication hashes ===
        item["url_hash"] = self._compute_url_hash(response.url)
        item["fingerprint"] = self._compute_fingerprint(
            item["title"], 
            item["published_at"], 
            source, 
            normalized_text
        )
        
        # Mark as successfully parsed
        item["parse_ok"] = True
        
        return item

    def _extract_author(self, article: Article, response) -> tuple[Optional[str], str]:
        """
        Extract author with ordered fallbacks.
        
        Priority order:
        1. RSS / feed author (if available in response meta)
        2. newspaper3k: article.authors (join list with ", ")
        3. meta tags: meta[name="author"], meta[property="article:author"]
        4. If still missing: author = None
        
        Returns: (author_name, author_source)
        """
        # 1. Check for feed author in response meta (set by RSS/feed parsing if applicable)
        feed_author = response.meta.get("feed_author")
        if feed_author and feed_author.strip():
            return feed_author.strip(), "feed"
        
        # 2. newspaper3k authors
        if article.authors:
            # Filter out empty strings and join
            valid_authors = [a.strip() for a in article.authors if a and a.strip()]
            if valid_authors:
                return ", ".join(valid_authors), "newspaper3k"
        
        # 3. Meta tags fallback (best-effort from HTML already available)
        try:
            # Try meta[name="author"]
            meta_author = response.xpath(
                "//meta[@name='author']/@content"
            ).get()
            if meta_author and meta_author.strip():
                return meta_author.strip(), "meta"
            
            # Try meta[property="article:author"]
            og_author = response.xpath(
                "//meta[@property='article:author']/@content"
            ).get()
            if og_author and og_author.strip():
                return og_author.strip(), "meta"
            
            # Try meta[name="byl"] (NYT style)
            byl_author = response.xpath(
                "//meta[@name='byl']/@content"
            ).get()
            if byl_author and byl_author.strip():
                # Often formatted as "By Author Name"
                author_text = byl_author.strip()
                if author_text.lower().startswith("by "):
                    author_text = author_text[3:]
                return author_text, "meta"
            
            # Try JSON-LD author
            import json
            ld_scripts = response.xpath(
                "//script[@type='application/ld+json']/text()"
            ).getall()
            for script in ld_scripts:
                try:
                    data = json.loads(script)
                    if isinstance(data, dict):
                        author_data = data.get("author")
                        if author_data:
                            if isinstance(author_data, str):
                                return author_data, "meta"
                            elif isinstance(author_data, dict):
                                name = author_data.get("name")
                                if name:
                                    return name, "meta"
                            elif isinstance(author_data, list) and author_data:
                                names = []
                                for a in author_data:
                                    if isinstance(a, str):
                                        names.append(a)
                                    elif isinstance(a, dict) and a.get("name"):
                                        names.append(a["name"])
                                if names:
                                    return ", ".join(names), "meta"
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception:
            pass
        
        # 4. No author found
        return None, "missing"

    def _compute_url_hash(self, url: str) -> str:
        """
        Compute stable URL hash after removing tracking parameters.
        
        This ensures the same story from the same URL doesn't produce
        duplicates across runs (even with different utm_* params).
        """
        canonical = canonicalize_url_clean(url)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _compute_fingerprint(
        self, 
        title: Optional[str], 
        published_at: Optional[str], 
        source: str, 
        text: Optional[str]
    ) -> str:
        """
        Compute content fingerprint for deduplication.
        
        Logic:
        - If text is missing: hash(title + published_at + source)
        - Else: hash(title + first_2k_chars_of_text)
        
        This handles cases where the same article might appear with
        slightly different URLs but identical content.
        """
        if text and len(text) > 0:
            # Use title + first 2k chars of text
            basis = f"{title or ''}|{text[:2000]}"
        else:
            # Use title + published_at + source
            basis = f"{title or ''}|{published_at or ''}|{source}"
        
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    def _validate_article_content(self, article: Article, url: str) -> bool:
        """
        Validate that an article has enough substance to be worth keeping.
        Returns False for section pages, navigation junk, etc.
        """
        # Must have a title
        if not article.title or len(article.title.strip()) == 0:
            self.logger.debug(f"Rejecting article (no title): {url}")
            return False
        
        # Must have sufficient text content
        text = (article.text or "").strip()
        if len(text) < self.MIN_ARTICLE_TEXT_LENGTH:
            self.logger.debug(
                f"Rejecting article (text too short: {len(text)} < {self.MIN_ARTICLE_TEXT_LENGTH}): {url}"
            )
            return False
        
        # Reject navigation junk (too many short lines)
        lines = text.split("\n")
        if len(lines) > 10:
            short_lines = sum(1 for line in lines if len(line.strip()) < 30)
            if short_lines / len(lines) > 0.7:
                self.logger.debug(f"Rejecting article (looks like nav junk): {url}")
                return False
        
        return True

    def _get_summary_with_metadata(self, article: Article) -> tuple[Optional[str], bool]:
        """
        Get article summary with truncation metadata.
        
        Logic:
        1. Try newspaper3k summary (article.summary)
        2. Fallback to first 3-5 sentences from text
        3. Normalize whitespace
        4. Truncate to SUMMARY_MAX_CHARS
        5. Track whether truncation occurred
        
        Returns: (summary_text, was_truncated)
        """
        max_chars = self.SUMMARY_MAX_CHARS
        
        # Try newspaper3k summary first
        raw_summary = (article.summary or "").strip()
        
        if not raw_summary or len(raw_summary) < 50:
            # Fallback: extract first 3-5 sentences from text
            text = (article.text or "").strip()
            if not text:
                return None, False
            
            # Simple sentence splitting
            sentences = re.split(r"(?<=[.!?])\s+", text)
            fallback_sentences = sentences[:5]
            raw_summary = " ".join(fallback_sentences)
        
        # Normalize whitespace
        normalized = normalize_whitespace(raw_summary)
        if not normalized:
            return None, False
        
        original_len = len(normalized)
        
        # Truncate if needed
        if original_len > max_chars:
            # Truncate at word boundary
            truncated = normalized[:max_chars].rsplit(" ", 1)[0]
            # Add ellipsis only if we actually cut content
            if len(truncated) < original_len:
                truncated = truncated.rstrip(".,!?;:") + "..."
            return truncated, True
        
        return normalized, False
