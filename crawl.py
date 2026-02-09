import argparse
import json
import logging
import os
from typing import List, Type

import nltk
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from news_scraper.spiders import *


def ensure_nltk_data() -> None:
    """Download NLTK tokenizers only if not already present."""
    required = ["tokenizers/punkt", "tokenizers/punkt_tab"]
    for resource in required:
        try:
            nltk.data.find(resource)
        except LookupError:
            # Resource not found, download it
            name = resource.split("/")[-1]
            nltk.download(name, quiet=True)


# Ensure NLTK tokenizers for article NLP are available when running the crawl
ensure_nltk_data()


def get_spiders() -> List[Type]:
    """Return the list of spider classes used by the project."""
    return [
        CNNSpider,
        FoxNewsSpider,
        NBCNewsSpider,
        BBCSpider,
        APNewsSpider,
        GuardianSpider,
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
        "--spider",
        dest="spider",
        help="Run only this spider (by name). If not specified, runs all spiders.",
    )
    parser.add_argument(
        "--sink",
        dest="sink",
        choices=["jsonl", "kafka", "mongo"],
        help="Shorthand for sink class: jsonl, kafka, or mongo",
    )
    parser.add_argument(
        "--jsonl-path",
        dest="jsonl_path",
        help="Output path for JSONL sink (requires --sink jsonl)",
    )
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
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    spiders = get_spiders()

    # Filter to specific spider if requested
    if args.spider:
        spider_names = {s.name: s for s in spiders}
        if args.spider not in spider_names:
            logger.error(f"Unknown spider: {args.spider}")
            logger.info(f"Available spiders: {list(spider_names.keys())}")
            return
        spiders = [spider_names[args.spider]]

    logger.info(f"Loaded {len(spiders)} spiders: {[s.name for s in spiders]}")

    # Allow configuring sink via CLI args or environment variables.
    settings = get_project_settings()

    # Handle --sink shorthand
    if args.sink:
        sink_map = {
            "jsonl": "news_scraper.sinks.jsonl.JSONLSink",
            "kafka": "news_scraper.sinks.kafka.KafkaSink",
            "mongo": "news_scraper.sinks.mongo.MongoSink",
        }
        sink_class = sink_map[args.sink]
        settings.set("SINK_CLASS", sink_class, priority="cmdline")
        logger.info(f"Using sink: {args.sink} ({sink_class})")

        # Handle JSONL path
        if args.sink == "jsonl" and args.jsonl_path:
            settings.set("SINK_SETTINGS", {"path": args.jsonl_path}, priority="cmdline")
            logger.info(f"JSONL output path: {args.jsonl_path}")

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
