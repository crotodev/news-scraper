# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import importlib
import logging
from typing import Any, Self

# useful for handling different item types with a single interface


class SinkPipeline:
    """Generic pipeline that adapts a pluggable Sink implementation.

    Configure via settings:
    - SINK_CLASS: full import path to sink class (e.g. "news_scraper.sinks.jsonl.JsonlSink")
    - SINK_SETTINGS: dict of keyword args to pass to the sink constructor
    """

    def __init__(self, sink_class_path: str, sink_settings: dict | None = None):
        self.sink_class_path = sink_class_path
        self.sink_settings = sink_settings or {}
        self.sink = None

    @classmethod
    def from_crawler(cls, crawler) -> Self:
        path = crawler.settings.get("SINK_CLASS", "news_scraper.sinks.jsonl.JsonlSink")
        settings = crawler.settings.get("SINK_SETTINGS", {})
        return cls(path, settings)

    def _load_sink_class(self) -> Any:
        try:
            module_name, class_name = self.sink_class_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except Exception as e:
            logging.error(f"Failed to import sink class {self.sink_class_path}: {e}")
            raise

    def open_spider(self, spider) -> None:
        SinkClass = self._load_sink_class()
        try:
            # prefer kwargs constructor
            self.sink = SinkClass(**self.sink_settings)
        except TypeError:
            try:
                self.sink = SinkClass(self.sink_settings)
            except Exception:
                self.sink = SinkClass()

        try:
            if hasattr(self.sink, "open"):
                self.sink.open(spider)
        except Exception as e:
            spider.logger.error(f"Sink open failed: {e}")

    def close_spider(self, spider) -> None:
        try:
            if self.sink and hasattr(self.sink, "close"):
                self.sink.close()
        except Exception as e:
            spider.logger.error(f"Sink close failed: {e}")

    def process_item(self, item, spider) -> Any:
        try:
            if self.sink and hasattr(self.sink, "send"):
                # best-effort; sink handles its own errors
                self.sink.send(item)
        except Exception as e:
            spider.logger.error(f"Sink send failed: {e}")
        return item


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


# class FilePipeline:
#     def __init__(self) -> None:
#         self.file = None

#     def open_spider(self, spider):
#         path = os.path.join(".", "data", f"{spider.name}_items.jsonl")
#         self.file = open(path, "w")

#     def close_spider(self, spider):
#         self.file.close()

#     def process_item(self, item, spider):
#         line = json.dumps(ItemAdapter(item).asdict()) + "\n"
#         self.file.write(line)
#         return item


# class MongoDBPipeline:
#     """Pipeline to write items to MongoDB.

#     Requires `pymongo`. Configure via settings:
#     - MONGO_URI (default: mongodb://localhost:27017)
#     - MONGO_DATABASE (default: news_db)
#     - MONGO_COLLECTION (default: raw_news)
#     """

#     def __init__(self, mongo_uri, mongo_db, mongo_collection):
#         self.mongo_uri = mongo_uri
#         self.mongo_db = mongo_db
#         self.mongo_collection = mongo_collection
#         self.client = None
#         self.db = None

#     @classmethod
#     def from_crawler(cls, crawler):
#         uri = crawler.settings.get("MONGO_URI", "mongodb://localhost:27017")
#         db = crawler.settings.get("MONGO_DATABASE", "news_db")
#         coll = crawler.settings.get("MONGO_COLLECTION", "raw_news")
#         return cls(uri, db, coll)

#     def open_spider(self, spider):
#         try:
#             from pymongo import MongoClient

#             self.client = MongoClient(self.mongo_uri)
#             self.db = self.client[self.mongo_db]
#             # Ensure an index on title to avoid duplicates
#             self.db[self.mongo_collection].create_index("title", unique=True)
#         except Exception as e:
#             spider.logger.error(f"MongoDB connection failed: {e}")

#     def close_spider(self, spider):
#         if self.client:
#             self.client.close()

#     def process_item(self, item, spider):
#         if not self.db:
#             return item

#         record = ItemAdapter(item).asdict()
#         try:
#             # use upsert to avoid duplicate title entries
#             self.db[self.mongo_collection].update_one(
#                 {"title": record.get("title")}, {"$setOnInsert": record}, upsert=True
#             )
#         except Exception as e:
#             spider.logger.error(f"Failed to write item to MongoDB: {e}")

#         return item
