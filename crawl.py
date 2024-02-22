import json
import os
import sqlite3

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import nltk

from news_scraper.spiders.cnn import CNNSpider
from news_scraper.spiders.foxnews import FoxNewsSpider
from news_scraper.spiders.nbcnews import NBCNewsSpider

from article_manager import ArticleManager


def crawl():
    nltk.download("punkt")

    data_path = os.path.join(".", "data")

    if not os.path.exists(data_path):
        os.mkdir(data_path)

    process = CrawlerProcess(settings=get_project_settings())
    process.crawl(FoxNewsSpider)
    process.crawl(NBCNewsSpider)
    process.crawl(CNNSpider)
    process.start()

    def read_from_jsonl(path, items_):
        with open(path, "r") as f:
            for line in f:
                items_.append(json.loads(line.strip()))

    items = []

    cnn_path = os.path.join(".", "data", "cnn_items.jsonl")
    foxnews_path = os.path.join(".", "data", "foxnews_items.jsonl")
    nbcnews_path = os.path.join(".", "data", "nbcnews_items.jsonl")

    paths = [cnn_path, foxnews_path, nbcnews_path]

    # Read from JSONL files and delete them
    for path in paths:
        read_from_jsonl(path, items)
        os.remove(path)

    # Create a connection to the database and insert the items
    conn = sqlite3.connect(os.path.join(".", "data", "news.db"), timeout=20)

    manager = ArticleManager(conn)

    manager.create_table()
    manager.insert(items)
    manager.close()
