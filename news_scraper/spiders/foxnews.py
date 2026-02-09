import re

from random_user_agent.user_agent import UserAgent

from news_scraper.extractors.foxnews import FoxNewsExtractor
from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class FoxNewsSpider(NewsSpider):
    name = "foxnews"
    domain = "foxnews.com"
    allowed_domains = ["foxnews.com", "www.foxnews.com"]
    extractor = FoxNewsExtractor()

    # Section pages for discovery
    start_urls = [
        "https://www.foxnews.com",
        "https://www.foxnews.com/politics",
        "https://www.foxnews.com/us",
        "https://www.foxnews.com/world",
        "https://www.foxnews.com/media",
    ]

    def is_article_url(self, url: str) -> bool:
        """Fox News article URLs have section/slug pattern."""
        # Reject section roots
        if re.match(r"https?://[^/]+/(politics|us|world|media|opinion)/?$", url, re.I):
            return False
        # Reject video/category pages
        if re.search(r"/(video|category|shows|person)/", url, re.I):
            return False
        # Accept articles with slug (section/long-slug-name)
        if re.search(
            r"/(politics|us|world|media|opinion|entertainment|tech)/[a-z0-9-]{20,}",
            url,
            re.I,
        ):
            return True
        return False

    def is_article_page(self, response) -> bool:
        # Fox News uses body class
        body_class = response.xpath("//body/@class").get()
        if body_class and "fn article-single" in body_class:
            return True
        return super().is_article_page(response)
