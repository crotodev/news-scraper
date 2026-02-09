import re

from random_user_agent.user_agent import UserAgent

from news_scraper.extractors.cnn import CNNExtractor
from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class CNNSpider(NewsSpider):
    name = "cnn"
    domain = "cnn.com"
    allowed_domains = ["cnn.com", "www.cnn.com"]
    extractor = CNNExtractor()

    # Section pages for discovery, not article processing
    start_urls = [
        "https://www.cnn.com",
        "https://www.cnn.com/politics",
        "https://www.cnn.com/business",
        "https://www.cnn.com/world",
        "https://www.cnn.com/us",
        "https://www.cnn.com/health",
        "https://www.cnn.com/entertainment",
    ]

    def is_article_url(self, url: str) -> bool:
        """CNN article URLs contain date patterns like /2026/01/27/."""
        # Reject obvious non-article paths
        if re.search(r"/(video|gallery|live-news|cnn-underscored)/", url, re.I):
            return False
        # Accept URLs with date pattern
        if re.search(r"/\d{4}/\d{2}/\d{2}/", url):
            return True
        return False

    def is_article_page(self, response) -> bool:
        # CNN uses data-page-type attribute
        data_page_type = response.xpath("//body/@data-page-type").extract_first()
        if data_page_type and "article" in data_page_type:
            return True
        # Fallback to base check
        return super().is_article_page(response)
