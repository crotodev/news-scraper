from random_user_agent.user_agent import UserAgent

from news.spiders.newsspider import NewsSpider

ua = UserAgent()


class CNNSpider(NewsSpider):
    name = "cnn"
    domain = "cnn.com"
    allowed_domains = ["cnn.com"]
    start_urls = [
        "https://www.cnn.com",
        "https://www.cnn.com/politics",
        "https://www.cnn.com/business",
    ]

    def is_article_page(self, response):
        # This method checks if the "class" attribute of the <body> tag contains "article"
        # Using XPath to select the body tag and extract the class attribute
        data_page_type = response.xpath("//body/@data-page-type").extract_first()
        # Checking if "article" is in the class attribute
        return "article" in data_page_type if data_page_type else False
