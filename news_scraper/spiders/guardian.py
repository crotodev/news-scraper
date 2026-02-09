import re

from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class GuardianSpider(NewsSpider):
    name = "guardian"
    domain = "theguardian.com"
    allowed_domains = ["theguardian.com", "www.theguardian.com"]
    # Section pages for discovery
    start_urls = [
        "https://www.theguardian.com/international",
        "https://www.theguardian.com/world",
        "https://www.theguardian.com/technology",
        "https://www.theguardian.com/business",
        "https://www.theguardian.com/politics",
        "https://www.theguardian.com/us-news",
    ]

    def is_article_url(self, url: str) -> bool:
        """Guardian article URLs have date pattern like /2026/jan/27/slug."""
        # Reject section roots
        if re.match(
            r"https?://[^/]+/(world|uk|us|technology|business|politics)/?$", url, re.I
        ):
            return False
        # Reject video/gallery/live
        if re.search(r"/(video|gallery|live)/", url, re.I):
            return False
        # Accept URLs with date pattern (Guardian uses /2026/jan/27/ format)
        if re.search(r"/\d{4}/[a-z]{3}/\d{2}/", url, re.I):
            return True
        return False

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        if response.xpath("//article"):
            return True
        return super().is_article_page(response)
