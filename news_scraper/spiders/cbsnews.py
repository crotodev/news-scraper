import re

from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class CBSNewsSpider(NewsSpider):
    name = "cbsnews"
    domain = "cbsnews.com"
    allowed_domains = ["cbsnews.com", "www.cbsnews.com"]
    # Section pages for discovery
    start_urls = [
        "https://www.cbsnews.com",
        "https://www.cbsnews.com/us",
        "https://www.cbsnews.com/world",
        "https://www.cbsnews.com/politics",
        "https://www.cbsnews.com/moneywatch",
    ]

    def is_article_url(self, url: str) -> bool:
        """CBS News article URLs have /news/ pattern with slug."""
        # Reject section roots
        if re.match(
            r"https?://[^/]+/(us|world|politics|moneywatch|entertainment|business)/?$",
            url,
            re.I,
        ):
            return False
        # Reject video/live pages
        if re.search(r"/(video|live|essentials)/", url, re.I):
            return False
        # Accept /news/ URLs with slugs
        if re.search(r"/news/[a-z0-9-]{20,}", url, re.I):
            return True
        return False

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        if response.xpath("//article"):
            return True
        return super().is_article_page(response)
