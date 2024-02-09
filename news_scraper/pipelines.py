# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3
import os
import json

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

#
# class NewsPipeline:
#     conn = None
#
#     def process_item(self, item, spider):
#         insert_query = "INSERT OR IGNORE INTO raw_news (title, text, url, source, scraped_at) VALUES (?, ?, ?, ?, ?)"
#
#         adapter = ItemAdapter(item)
#         self.conn.execute(
#             insert_query,
#             (
#                 adapter["title"],
#                 adapter["text"],
#                 adapter["url"],
#                 adapter["source"],
#                 adapter["scraped_at"],
#             ),
#         )
#         return item
#
#     def open_spider(self, spider):
#         if not os.path.exists("./data"):
#             os.makedirs("./data")
#
#         path = os.path.join("./data", "news_scraper.db")
#         self.conn = sqlite3.connect(path, timeout=20)
#         self.conn.execute("PRAGMA journal_mode=WAL;")
#
#         self.conn.execute(
#             "CREATE TABLE IF NOT EXISTS raw_news "
#             "(id INTEGER PRIMARY KEY, title TEXT UNIQUE, text TEXT, url TEXT, source TEXT, scraped_at TEXT)"
#         )
#
#     def close_spider(self, spider):
#         self.conn.commit()
#         self.conn.close()


class FilePipeline:
    def __init__(self):
        self.file = None

    def open_spider(self, spider):
        path = os.path.join(".", "data", f"{spider.name}_items.jsonl")
        self.file = open(path, "w")

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(ItemAdapter(item).asdict()) + "\n"
        self.file.write(line)
        return item
