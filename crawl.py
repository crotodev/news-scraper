import os
import logging
from typing import List, Type
import argparse
import json

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import nltk

from news_scraper.spiders import *


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
        CBSNewsSpider,
    ]


def build_jsonl_paths(spiders: List[Type], data_dir: str = ".") -> List[str]:
    """Build JSONL output paths for each spider using its `name` attribute."""
    if not os.path.exists(os.path.join(data_dir, "data")):
        os.makedirs(os.path.join(data_dir, "data"), exist_ok=True)
    return [
        os.path.join(data_dir, "data", f"{spider.name}_items.jsonl")
        for spider in spiders
    ]


def main(run_crawl: bool = True) -> None:
    """Run the Scrapy crawl for the configured spiders.

    Set `run_crawl=False` to avoid starting Scrapy (useful for tests).
    """
    parser = argparse.ArgumentParser(description="Run news-scraper crawlers")
    parser.add_argument(
        "--sink-class",
        dest="sink_class",
        help="Sink class import path, e.g. news_scraper.sinks.kafka.KafkaSink",
    )
    parser.add_argument(
        "--sink-settings",
        dest="sink_settings",
        help="Sink settings as JSON string or comma-separated key=val pairs",
    )
    parser.add_argument(
        "--no-crawl",
        dest="no_crawl",
        action="store_true",
        help="Don't start the crawl (useful for testing)",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level for both script and Scrapy (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging with the specified level
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    spiders = get_spiders()
    logger.info(f"Loaded {len(spiders)} spiders: {[s.name for s in spiders]}")

    # Allow configuring sink via CLI args or environment variables.
    settings = get_project_settings()
    logger.info(f"Using sink class: {settings.get('SINK_CLASS')}")
    
    # Set Scrapy's log level
    settings.set("LOG_LEVEL", args.log_level, priority="cmdline")
    logger.info(f"Set Scrapy log level to: {args.log_level}")
    # CLI overrides env
    sink_class = args.sink_class or os.environ.get("SINK_CLASS")
    sink_settings_val = args.sink_settings or os.environ.get("SINK_SETTINGS")

    if sink_class:
        logger.info(f"Overriding sink class from CLI: {sink_class}")
        settings.set("SINK_CLASS", sink_class, priority="cmdline")

    if sink_settings_val:
        # Accept JSON blob or comma-separated key=val pairs
        parsed = None
        txt = sink_settings_val.strip()
        if txt.startswith("{"):
            try:
                parsed = json.loads(txt)
            except Exception:
                parsed = None
        if parsed is None:
            # parse key=val,key=val
            parsed = {}
            for part in txt.split(","):
                if not part:
                    continue
                if "=" in part:
                    k, v = part.split("=", 1)
                    parsed[k.strip()] = v.strip()
        logger.info(f"Overriding sink settings from CLI: {parsed}")
        settings.set("SINK_SETTINGS", parsed, priority="cmdline")

    if not args.no_crawl and run_crawl:
        logger.info("Starting crawl process...")
        process = CrawlerProcess(settings=settings)
        for spider in spiders:
            logger.info(f"Scheduling spider: {spider.name}")
            process.crawl(spider)
        logger.info("All spiders scheduled. Starting Scrapy engine...")
        process.start()
        logger.info("Crawl completed successfully.")
    else:
        logger.info("Crawl skipped (--no-crawl flag or run_crawl=False)")


if __name__ == "__main__":
    main()
