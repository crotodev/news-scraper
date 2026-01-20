from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class CBSNewsSpider(NewsSpider):
    name = "cbsnews"
    domain = "cbsnews.com"
    allowed_domains = ["cbsnews.com"]
    start_urls = [
        "https://www.cbsnews.com",
        "https://www.cbsnews.com/politics",
        "https://www.cbsnews.com/business",
    ]

    def is_article_page(self, response) -> bool:
        # CBS News articles have specific article sections
        article_body = response.xpath("//article[@class='content__body']").extract_first()
        return bool(article_body) or bool(response.xpath("//article").extract_first())
