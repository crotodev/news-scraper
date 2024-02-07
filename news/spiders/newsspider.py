from datetime import datetime

import scrapy
from random_user_agent.user_agent import UserAgent
from newspaper import Article
from news.items import NewsItem


ua = UserAgent()


class NewsSpider(scrapy.Spider):
    name = "news"
    domain = ""
    allowed_domains = []

    custom_settings = {
        "USER_AGENT": ua.get_random_user_agent(),
        "ROBOTSTXT_OBEY": True,
        "DEPTH_LIMIT": 1,
    }

    def parse(self, response):
        if self.is_article_page(response):
            item = self.process_article(response, self.domain)
            yield item

        for href in response.xpath("//a/@href").getall():
            full_url = response.urljoin(href)  # Ensure the URL is absolute
            if self.is_valid_url(full_url):  # Implement this method to validate URLs
                yield response.follow(full_url, self.parse)

    def is_valid_url(self, url):
        # Implement logic to check if the URL is valid
        # For example, check if the URL has a scheme
        if url.startswith("http://") or url.startswith("https://"):
            return True
        else:
            self.logger.error(f"Invalid URL found: {url}")
            return False

    @staticmethod
    def is_article_page(response):
        return True

    @staticmethod
    def process_article(response, source):
        a = Article(response.url)
        a.download()
        a.parse()

        item = NewsItem()
        item["title"] = a.title
        item["text"] = a.text
        item["url"] = response.url
        item["source"] = source
        item["scraped_at"] = datetime.now().isoformat()
        return item
