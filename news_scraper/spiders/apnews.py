from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class APNewsSpider(NewsSpider):
    name = "apnews"
    domain = "apnews.com"
    allowed_domains = ["apnews.com", "www.apnews.com"]
    start_urls = [
        "https://apnews.com",
        "https://apnews.com/hub/politics",
        "https://apnews.com/hub/technology",
    ]

    def is_article_page(self, response) -> bool:
        # Prefer explicit metadata or an <article> tag; also check common URL pattern
        og_type = response.xpath("//meta[@property='og:type']/@content").get()
        if og_type == "article":
            return True
        return bool(response.xpath("//article")) or "/article/" in response.url
