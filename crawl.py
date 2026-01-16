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

import os
from typing import List, Type

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


# Ensure punkt tokenizer for article NLP is available when running the crawl
nltk.download("punkt")


def get_spiders() -> List[Type]:
    """Return the list of spider classes used by the project."""
    return [
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


def build_jsonl_paths(spiders: List[Type], data_dir: str = ".") -> List[str]:
    """Build JSONL output paths for each spider using its `name` attribute."""
    if not os.path.exists(os.path.join(data_dir, "data")):
        os.makedirs(os.path.join(data_dir, "data"), exist_ok=True)
    return [os.path.join(data_dir, "data", f"{spider.name}_items.jsonl") for spider in spiders]


def main(run_crawl: bool = True) -> None:
    """Run the Scrapy crawl for the configured spiders.

    Set `run_crawl=False` to avoid starting Scrapy (useful for tests).
    """
    spiders = get_spiders()

    if run_crawl:
        process = CrawlerProcess(settings=get_project_settings())
        for spider in spiders:
            process.crawl(spider)
        process.start()


if __name__ == "__main__":
    main()
    read_from_jsonl(path, items)
