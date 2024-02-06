from datetime import datetime
import json
import os

import scrapy
from random_user_agent.user_agent import UserAgent
from newspaper import Article

ua = UserAgent()


class NewsSpider(scrapy.Spider):
    name = "newsspider"
    allowed_domains = []

    custom_settings = {
        'USER_AGENT': ua.get_random_user_agent(),
        'ROBOTSTXT_OBEY': True,
        "DEPTH_LIMIT": 2,
    }

    articles = []

    articles_processed = 0
    max_articles = 5

    def parse(self, response):

        if self.is_article_page(response):



            if self.articles_processed < self.max_articles:
                self.articles.append(self.process_article(response, self.allowed_domains[0]))
                self.articles_processed += 1
            else:
                self.logger.info("Reached max number of articles. Stopping spider.")
                return  # Stop the spider or avoid scheduling more requests

        for href in response.xpath("//a/@href").getall():
            full_url = response.urljoin(href)  # Ensure the URL is absolute
            if self.is_valid_url(full_url):  # Implement this method to validate URLs
                yield response.follow(full_url, self.parse)

    def is_valid_url(self, url):
        # Implement logic to check if the URL is valid
        # For example, check if the URL has a scheme
        if url.startswith('http://') or url.startswith('https://'):
            return True
        else:
            self.logger.error(f"Invalid URL found: {url}")
            return False

    def closed(self, reason):
        self.log("Saving articles to file")



        self.log(os.getcwd())

        file = "data/articles.json"
        stored_articles = []
        try:
            with open(file, 'r', encoding='utf-8') as f:
                try:
                    stored_articles = json.load(f)
                except json.decoder.JSONDecodeError:
                    # If the file is empty or content is not valid JSON, log a warning and proceed with an empty list
                    self.logger.warning(
                        f"File {file} is empty or contains invalid JSON. Starting with an empty list.")
        except FileNotFoundError:
            stored_articles = []

        filtered = self.filter_articles(stored_articles, self.articles)

        stored_articles.extend(filtered)

        with open(file, "w") as f:
            json.dump(stored_articles, f)

    @staticmethod
    def is_article_page(response):
        return True

    @staticmethod
    def filter_articles(stored, new):
        filtered = []

        titles = {x['title'] for x in stored}

        for x in new:
            if x['title'] not in titles:
                titles.add(x['title'])
                filtered.append(x)

        return filtered

    @staticmethod
    def process_article(response, source):
        a = Article(response.url)
        a.download()
        a.parse()

        article = {
            "title": a.title,
            "text": a.text,
            "url": response.url,
            "source": source,
            "scraped_at": datetime.now().isoformat(),

        }
        return article
