from random_user_agent.user_agent import UserAgent

from news.spiders.newsspider import NewsSpider

ua = UserAgent()


class NBCNewsSpider(NewsSpider):
    name = "nbcnews"
    allowed_domains = ["nbcnews.com"]
    start_urls = ["https://nbcnews.com"]

    custom_settings = {
        'USER_AGENT': ua.get_random_user_agent(),
        'ROBOTSTXT_OBEY': True,
        "DEPTH_LIMIT": 1,
    }

    articles = []
    titles = []

    articles_processed = 0
    max_articles = 20

    def is_article_page(self, response):
        # This method checks if the "class" attribute of the <body> tag contains "articlePage"
        # Using XPath to select the body tag and extract the class attribute
        body_class = response.xpath('//body/@class').get()
        # Checking if "articlePage news savory" is in the class attribute
        return "articlePage news savory" in body_class if body_class else False
