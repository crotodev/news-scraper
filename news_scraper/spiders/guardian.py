from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class GuardianSpider(NewsSpider):
    name = "guardian"
    domain = "theguardian.com"
    allowed_domains = ["theguardian.com", "www.theguardian.com"]
    start_urls = [
        "https://www.theguardian.com/international",
        "https://www.theguardian.com/world",
        "https://www.theguardian.com/technology",
    ]

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return bool(response.xpath("//article"))
