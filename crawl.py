import json
import os
import sqlite3

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import nltk

from news_scraper.spiders.cnn import CNNSpider
from news_scraper.spiders.foxnews import FoxNewsSpider
from news_scraper.spiders.nbcnews import NBCNewsSpider
from news_scraper.spiders.reuters import ReutersSpider
from news_scraper.spiders.bbc import BBCSpider
from news_scraper.spiders.apnews import APNewsSpider
from news_scraper.spiders.guardian import GuardianSpider
from news_scraper.spiders.nytimes import NYTimesSpider
from news_scraper.spiders.washingtonpost import WashingtonPostSpider
from news_scraper.spiders.wsj import WSJSpider
from news_scraper.spiders.aljazeera import AlJazeeraSpider

nltk.download("punkt")

data_path = os.path.join(".", "data")

if not os.path.exists(data_path):
    os.mkdir(data_path)

spiders = [
    CNNSpider,
    FoxNewsSpider,
    NBCNewsSpider,
    ReutersSpider,
    BBCSpider,
    APNewsSpider,
    GuardianSpider,
    NYTimesSpider,
    WashingtonPostSpider,
    WSJSpider,
    AlJazeeraSpider,
]

process = CrawlerProcess(settings=get_project_settings())

[process.crawl(spider) for spider in spiders]

process.start()

items = []

# dynamically build JSONL paths from spider names so new spiders are included
paths = [os.path.join(".", "data", f"{spider.name}_items.jsonl") for spider in spiders]


def read_from_jsonl(path, items_):
    with open(path, "r") as f:
        for line in f:
            items_.append(json.loads(line.strip()))


def insert(conn_, items_):
    query = (
        "INSERT OR IGNORE INTO raw_news "
        "(title, author, text, summary, url, source, published_at, scraped_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for item in items_:
        conn.execute(
            query,
            (
                item["title"],
                item["author"],
                item["text"],
                item["summary"],
                item["url"],
                item["source"],
                item["published_at"],
                item["scraped_at"],
            ),
        )
    conn_.commit()


# Read from JSONL files and delete them
for path in paths:
    read_from_jsonl(path, items)
    os.remove(path)

# Create a connection to the database and insert the items
conn = sqlite3.connect(os.path.join(".", "data", "news.db"), timeout=20)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute(
    "CREATE TABLE IF NOT EXISTS raw_news "
    "(id INTEGER PRIMARY KEY, title TEXT UNIQUE, "
    "author TEXT, text TEXT, summary TEXT, url TEXT, "
    "source TEXT, published_at TEXT, scraped_at TEXT)"
)

insert(conn, items)

conn.close()

# %%
