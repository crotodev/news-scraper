from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class ReutersSpider(NewsSpider):
    name = "reuters"
    domain = "reuters.com"
    allowed_domains = ["reuters.com", "www.reuters.com"]
    start_urls = [
        "https://www.reuters.com",
        "https://www.reuters.com/world",
        "https://www.reuters.com/technology",
    ]

    def is_article_page(self, response) -> bool:
        # Check metadata for article type, or `/article/` in URL
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return "/article/" in response.url
