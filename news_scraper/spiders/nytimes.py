from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class NYTimesSpider(NewsSpider):
    name = "nytimes"
    domain = "nytimes.com"
    allowed_domains = ["nytimes.com", "www.nytimes.com"]
    start_urls = [
        "https://www.nytimes.com",
        "https://www.nytimes.com/section/world",
        "https://www.nytimes.com/section/technology",
    ]

    def is_article_page(self, response) -> bool:
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return "/" in response.url and "article" in response.url
