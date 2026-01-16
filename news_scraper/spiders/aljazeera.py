from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class AlJazeeraSpider(NewsSpider):
    name = "aljazeera"
    domain = "aljazeera.com"
    allowed_domains = ["aljazeera.com", "www.aljazeera.com"]
    start_urls = [
        "https://www.aljazeera.com",
        "https://www.aljazeera.com/news/",
        "https://www.aljazeera.com/topics/",
    ]

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return bool(response.xpath("//article")) or "/news/" in response.url
