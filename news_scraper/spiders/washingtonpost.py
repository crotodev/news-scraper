from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class WashingtonPostSpider(NewsSpider):
    name = "washingtonpost"
    domain = "washingtonpost.com"
    allowed_domains = ["washingtonpost.com", "www.washingtonpost.com"]
    start_urls = [
        "https://www.washingtonpost.com",
        "https://www.washingtonpost.com/politics/",
        "https://www.washingtonpost.com/technology/",
    ]

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return bool(response.xpath("//article")) or "/202" in response.url
