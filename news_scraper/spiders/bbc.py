import re

from random_user_agent.user_agent import UserAgent

from news_scraper.extractors.bbc import BBCExtractor
from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class BBCSpider(NewsSpider):
    name = "bbc"
    domain = "bbc.com"
    allowed_domains = ["bbc.com", "www.bbc.com"]
    extractor = BBCExtractor()

    # Section pages for discovery
    start_urls = [
        "https://www.bbc.com/news",
        "https://www.bbc.com/news/world",
        "https://www.bbc.com/news/technology",
        "https://www.bbc.com/news/business",
        "https://www.bbc.com/news/science_and_environment",
    ]

    def is_article_url(self, url: str) -> bool:
        """BBC article URLs contain /news/ followed by a slug or ID."""
        # Reject video/live pages
        if re.search(r"/(av|live|programmes|newsround)/", url, re.I):
            return False
        # Accept /news/ URLs with article IDs (e.g., /news/world-12345678)
        if re.search(r"/news/[a-z]+-\d{6,}", url, re.I):
            return True
        # Accept article paths with slugs
        if re.search(r"/articles/[a-z0-9]+", url, re.I):
            return True
        # Accept BBC Sport article URLs (e.g., /sport/articles/c4g5lj59rr9o)
        if re.search(r"/sport/articles/[a-z0-9]+", url, re.I):
            return True
        return False

    def is_article_page(self, response) -> bool:
        # BBC uses og:type metadata
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        if response.xpath("//article"):
            return True
        return super().is_article_page(response)
