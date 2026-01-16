from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class BBCSpider(NewsSpider):
    name = "bbc"
    domain = "bbc.com"
    allowed_domains = ["bbc.com", "www.bbc.com"]
    start_urls = [
        "https://www.bbc.com/news",
        "https://www.bbc.com/news/world",
        "https://www.bbc.com/news/technology",
    ]

    def is_article_page(self, response) -> bool:
        # Prefer explicit metadata or an <article> tag
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return bool(response.xpath("//article"))
