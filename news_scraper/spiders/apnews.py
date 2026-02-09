import re

from random_user_agent.user_agent import UserAgent

from news_scraper.extractors.ap import APNewsExtractor
from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class APNewsSpider(NewsSpider):
    name = "apnews"
    domain = "apnews.com"
    allowed_domains = ["apnews.com", "www.apnews.com"]
    extractor = APNewsExtractor()

    # Section pages for discovery
    start_urls = [
        "https://apnews.com",
        "https://apnews.com/politics",
        "https://apnews.com/world-news",
        "https://apnews.com/business",
        "https://apnews.com/technology",
        "https://apnews.com/us-news",
    ]

    def is_article_url(self, url: str) -> bool:
        """AP News article URLs have /article/slug format."""
        # Reject section roots and hubs
        if re.match(
            r"https?://[^/]+/(hub/|politics/?$|world-news/?$|business/?$|technology/?$|us-news/?$)",
            url,
            re.I,
        ):
            return False
        # Accept /article/ URLs
        if "/article/" in url:
            return True
        return False

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        if "/article/" in response.url:
            return True
        return super().is_article_page(response)
