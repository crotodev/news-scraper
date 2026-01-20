from itemadapter import ItemAdapter
from .base import Sink


class MongoSink(Sink):
    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        db: str = "news_db",
        collection: str = "raw_news",
    ) -> None:
        self.uri = uri
        self.db_name = db
        self.collection = collection
        self.client = None
        self.db = None

    def open(self, spider) -> None:
        try:
            from pymongo import MongoClient

            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            # ensure index on url to prevent duplicates
            self.db[self.collection].create_index("url", unique=True)
        except Exception as e:
            spider.logger.error(f"MongoSink: connection/import failed: {e}")

    def send(self, item) -> None:
        if not self.db:
            return
        record = ItemAdapter(item).asdict()
        try:
            self.db[self.collection].update_one(
                {"url": record.get("url")}, {"$setOnInsert": record}, upsert=True
            )
        except Exception:
            # keep sink best-effort; logging is done in open
            pass

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
