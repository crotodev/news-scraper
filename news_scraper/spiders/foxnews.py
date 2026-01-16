from random_user_agent.user_agent import UserAgent

from news_scraper.spiders.newsspider import NewsSpider

ua = UserAgent()


class FoxNewsSpider(NewsSpider):
    name = "foxnews"
    domain = "foxnews.com"
    allowed_domains = ["foxnews.com"]
    start_urls = [
        "https://foxnews.com",
        "https://www.foxnews.com/politics",
        "https://www.foxnews.com/us",
    ]

    def is_article_page(self, response) -> bool:
        # This method checks if the "class" attribute of the <body> tag contains "fn article-single"
        # Using XPath to select the body tag and extract the class attribute
        body_class = response.xpath("//body/@class").get()
        # Checking if "articlePage news_scraper savory" is in the class attribute
        return "fn article-single" in body_class if body_class else False
