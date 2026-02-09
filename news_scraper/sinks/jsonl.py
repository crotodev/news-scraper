import json
import os

from itemadapter import ItemAdapter

from .base import Sink


class JsonlSink(Sink):
    def __init__(self, path_template: str = None) -> None:
        # path_template should be a format string accepting `spider` variable
        self.path_template = path_template or "./data/{spider.name}_items.jsonl"
        self._file = None

    def open(self, spider) -> None:
        path = self.path_template.format(spider=spider)
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        self._file = open(path, "w", encoding="utf-8")

    def send(self, item) -> None:
        if not self._file:
            return
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False) + "\n"
        self._file.write(line)

    def close(self):
        if self._file:
            self._file.close()
            self._file = None
