from datetime import datetime
from typing import Any, Generator, Literal
import hashlib
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
        "ROBOTSTXT_OBEY": False,
        "DEPTH_LIMIT": 10,
        "CONCURRENT_REQUESTS": 16,
    }

    def parse(
        self, response
    ) -> Generator[
        NewsItem | Any, Any, None
    ]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.is_article_page(response):
            item = self.process_article(response, self.domain, self.config)
            yield item

        for href in response.xpath("//a/@href").getall():
            full_url = response.urljoin(href)  # Ensure the URL is absolute
            if self.is_valid_url(full_url):  # Implement this method to validate URLs
                yield response.follow(full_url, self.parse)

    def is_valid_url(self, url) -> bool:
        # Implement logic to check if the URL is valid
        # For example, check if the URL has a scheme
        if url.startswith("http://") or url.startswith("https://"):
            return True
        else:
            self.logger.error(f"Invalid URL found: {url}")
            return False

    @staticmethod
    def is_article_page(response) -> Literal[True]:
        return True

    @staticmethod
    def process_article(response, source, config) -> NewsItem:
        article = Article(response.url, config=config)
        # Use download with input_html to ensure newspaper marks the article as downloaded
        # (works across newspaper3k versions and avoids raising "You must download() an article first!")
        try:
            article.download(input_html=response.text)
        except TypeError:
            # older/newer API differences: fallback to set_html if available
            if hasattr(article, "set_html"):
                article.set_html(response.text)
            elif hasattr(article, "set_article_html"):
                article.set_article_html(response.text)
        article.parse()
        article.nlp()

        url = canonicalize_url(response.url)
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        fingerprint = hashlib.sha256(
            (article.text or "").strip().encode("utf-8")
        ).hexdigest()

        item = NewsItem()
        item["title"] = article.title
        item["author"] = article.authors[0] if article.authors else ""
        item["text"] = article.text
        item["summary"] = article.summary
        item["url"] = response.url
        item["source"] = source
        item["published_at"] = (
            article.publish_date.isoformat() if article.publish_date else ""
        )
        item["scraped_at"] = datetime.now().isoformat()
        item["url_hash"] = url_hash
        item["fingerprint"] = fingerprint

        return item
