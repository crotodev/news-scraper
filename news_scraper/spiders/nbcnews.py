from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class NBCNewsSpider(NewsSpider):
    name = "nbcnews"
    domain = "nbcnews.com"
    allowed_domains = ["nbcnews.com"]
    start_urls = [
        "https://www.nbcnews.com",
        "https://www.nbcnews.com/us-news",
        "https://www.nbcnews.com/politics",
    ]

    def is_article_page(
        self, response
    ) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        # This method checks if the "class" attribute of the <body> tag contains "articlePage"
        # Using XPath to select the body tag and extract the class attribute
        body_class = response.xpath("//body/@class").get()
        # Checking if "articlePage news_scraper savory" is in the class attribute
        return "articlePage news_scraper savory" in body_class if body_class else False
