import re

from random_user_agent.user_agent import UserAgent

from news_scraper.extractors.nbc import NBCExtractor
from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class NBCNewsSpider(NewsSpider):
    name = "nbcnews"
    domain = "nbcnews.com"
    allowed_domains = ["nbcnews.com", "www.nbcnews.com"]
    extractor = NBCExtractor()

    # Section pages for discovery
    start_urls = [
        "https://www.nbcnews.com",
        "https://www.nbcnews.com/politics",
        "https://www.nbcnews.com/world",
        "https://www.nbcnews.com/business",
        "https://www.nbcnews.com/tech-media",
    ]

    def is_article_url(self, url: str) -> bool:
        """NBC News article URLs contain ID pattern like rcna12345."""
        # Reject section roots
        if re.match(
            r"https?://[^/]+/(politics|world|business|tech-media|health|us-news)/?$",
            url,
            re.I,
        ):
            return False
        # Reject video/shows
        if re.search(r"/(video|shows|now)/", url, re.I):
            return False
        # Accept URLs with article ID pattern (rcna12345 or n12345)
        if re.search(r"-rcna\d{4,}$", url, re.I):
            return True
        if re.search(r"-n\d{6,}$", url, re.I):
            return True
        return False

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        if response.xpath("//article"):
            return True
        return super().is_article_page(response)
