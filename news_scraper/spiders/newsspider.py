from datetime import datetime
from typing import Any, Generator, Optional
import hashlib
import re
from urllib.parse import urlparse
from w3lib.url import canonicalize_url

import scrapy
from random_user_agent.user_agent import UserAgent
from newspaper import Article, Config
from news_scraper.items import NewsItem


ua = UserAgent()


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
        Returns None if the article doesn't meet quality thresholds.
        """
        article = Article(response.url, config=config)
        
        # Download and parse
        try:
            article.download(input_html=response.text)
        except TypeError:
            # API compatibility
            if hasattr(article, "set_html"):
                article.set_html(response.text)
            elif hasattr(article, "set_article_html"):
                article.set_article_html(response.text)
        
        article.parse()
        
        # Validate article has substance BEFORE expensive NLP
        if not self._validate_article_content(article, response.url):
            return None
        
        # Run NLP for summary/keywords
        article.nlp()

        # Generate hashes
        url = canonicalize_url(response.url)
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        fingerprint = hashlib.sha256(
            (article.text or "").strip().encode("utf-8")
        ).hexdigest()

        # Build summary with fallback
        summary = self._get_summary_with_fallback(article)

        item = NewsItem()
        item["title"] = article.title or ""
        item["author"] = article.authors[0] if article.authors else ""
        item["text"] = article.text or ""
        item["summary"] = summary
        item["url"] = response.url
        item["source"] = source
        item["published_at"] = (
            article.publish_date.isoformat() if article.publish_date else ""
        )
        item["scraped_at"] = datetime.now().isoformat()
        item["url_hash"] = url_hash
        item["fingerprint"] = fingerprint

        return item

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

    def _get_summary_with_fallback(self, article: Article, max_length: int = 500) -> str:
        """
        Get article summary with fallback to first few sentences if NLP summary is empty.
        """
        summary = (article.summary or "").strip()
        
        if summary and len(summary) >= 50:
            # Truncate if too long
            if len(summary) > max_length:
                return summary[:max_length].rsplit(" ", 1)[0] + "..."
            return summary
        
        # Fallback: extract first 3-5 sentences from text
        text = (article.text or "").strip()
        if not text:
            return ""
        
        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)
        fallback_sentences = sentences[:5]
        fallback_summary = " ".join(fallback_sentences)
        
        # Truncate if needed
        if len(fallback_summary) > max_length:
            return fallback_summary[:max_length].rsplit(" ", 1)[0] + "..."
        
        return fallback_summary
