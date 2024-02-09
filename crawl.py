import json
import os
import sqlite3

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from news_scraper.spiders.cnn import CNNSpider
from news_scraper.spiders.foxnews import FoxNewsSpider
from news_scraper.spiders.nbcnews import NBCNewsSpider

data_path = os.path.join(".", "data")

if not os.path.exists(data_path):
    os.mkdir(data_path)

process = CrawlerProcess(settings=get_project_settings())
process.crawl(FoxNewsSpider)
process.crawl(NBCNewsSpider)
process.crawl(CNNSpider)
process.start()

items = []

cnn_path = os.path.join(".", "data", "cnn_items.jsonl")
foxnews_path = os.path.join(".", "data", "foxnews_items.jsonl")
nbcnews_path = os.path.join(".", "data", "nbcnews_items.jsonl")

paths = [cnn_path, foxnews_path, nbcnews_path]


def read_from_jsonl(path, items_):
    with open(path, "r") as f:
        for line in f:
            items_.append(json.loads(line.strip()))


def insert(conn_, items_):
    query = "INSERT OR IGNORE INTO raw_news (title, text, url, source, scraped_at) VALUES (?, ?, ?, ?, ?)"
    for item in items_:
        conn.execute(
            query,
            (
                item["title"],
                item["text"],
                item["url"],
                item["source"],
                item["scraped_at"],
            ),
        )
    conn_.commit()


# Read from JSONL files and delete them
for path in paths:
    read_from_jsonl(path, items)
    os.remove(path)

# Create a connection to the database and insert the items
conn = sqlite3.connect(os.path.join(".", "data", "news_scraper.db"), timeout=20)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute(
    "CREATE TABLE IF NOT EXISTS raw_news "
    "(id INTEGER PRIMARY KEY, title TEXT UNIQUE, text TEXT, url TEXT, source TEXT, scraped_at TEXT)"
)

insert(conn, items)

conn.close()
