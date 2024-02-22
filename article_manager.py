import sqlite3


class ArticleManager:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cursor = conn.cursor()

    def create_table(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS articles "
            "(id INTEGER PRIMARY KEY, title TEXT UNIQUE, "
            "author TEXT, text TEXT, summary TEXT, url TEXT, "
            "source TEXT, published_at TEXT, scraped_at TEXT)"
        )

    def insert(self, items) -> None:
        query = (
            "INSERT OR IGNORE INTO articles "
            "(title, author, text, summary, url, source, published_at, scraped_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )
        for item in items:
            self.conn.execute(
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
        self.commit()

    def select_all(self) -> list:
        return self.cursor.execute(
            """
            SELECT * FROM articles
            """
        ).fetchall()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
