import re

from random_user_agent.user_agent import UserAgent

from news_scraper.extractors.nyt import NYTimesExtractor
from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class NYTimesSpider(NewsSpider):
    name = "nytimes"
    domain = "nytimes.com"
    allowed_domains = ["nytimes.com", "www.nytimes.com"]
    extractor = NYTimesExtractor()

    # Section pages for discovery
    start_urls = [
        "https://www.nytimes.com",
        "https://www.nytimes.com/section/world",
        "https://www.nytimes.com/section/technology",
        "https://www.nytimes.com/section/business",
        "https://www.nytimes.com/section/politics",
    ]

    def is_article_url(self, url: str) -> bool:
        """NYT article URLs contain date patterns like /2026/01/27/section/slug.html."""
        # Reject section pages
        if re.match(r"https?://[^/]+/section/", url, re.I):
            return False
        # Reject video/interactive
        if re.search(r"/(video|interactive|slideshow)/", url, re.I):
            return False
        # Accept URLs with date pattern
        if re.search(r"/\d{4}/\d{2}/\d{2}/", url):
            return True
        return False

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        # NYT articles have date pattern in URL
        if re.search(r"/\d{4}/\d{2}/\d{2}/", response.url):
            return True
        return super().is_article_page(response)
