from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class WSJSpider(NewsSpider):
    name = "wsj"
    domain = "wsj.com"
    allowed_domains = ["wsj.com", "www.wsj.com"]
    start_urls = [
        "https://www.wsj.com",
        "https://www.wsj.com/news/world",
        "https://www.wsj.com/news/technology",
    ]

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return "/articles/" in response.url or bool(response.xpath("//article"))
