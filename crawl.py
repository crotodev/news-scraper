"""
DEPRECATED: Use ``python -m news_scraper.cli crawl ...`` instead.

This module is kept for backward compatibility with existing scripts and tests.
It re-exports helpers from the new CLI and provides a legacy ``main()`` that
accepts the old-style flags (``--spider``, ``--log-level``, ``--no-crawl``,
``--sink-class``, ``--sink-settings``).
"""

import json
import logging
import os
import sys
import warnings

from scrapy.crawler import CrawlerProcess  # noqa: F401  (mock target)
from scrapy.utils.project import get_project_settings  # noqa: F401  (mock target)

# Re-export helpers so existing imports keep working.
from news_scraper.cli import build_jsonl_paths, get_spiders  # noqa: F401


def main(run_crawl: bool = True) -> None:
    """Legacy entrypoint — backward-compatible with old tests.

    Parameters
    ----------
    run_crawl:
        When *False* the crawl is skipped (matches the old test behaviour).
    """
    warnings.warn(
        "crawl.py is deprecated; use `python -m news_scraper.cli crawl ...` instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # ---- Parse legacy argv flags ----
    args = sys.argv[1:]
    spider_name = None
    log_level = "INFO"
    no_crawl = False
    sink_class = None
    sink_settings_raw = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--spider" and i + 1 < len(args):
            spider_name = args[i + 1]
            i += 2
            continue
        if arg == "--log-level" and i + 1 < len(args):
            log_level = args[i + 1]
            i += 2
            continue
        if arg == "--no-crawl":
            no_crawl = True
            i += 1
            continue
        if arg == "--sink-class" and i + 1 < len(args):
            sink_class = args[i + 1]
            i += 2
            continue
        if arg == "--sink-settings" and i + 1 < len(args):
            sink_settings_raw = args[i + 1]
            i += 2
            continue
        i += 1

    # ---- Set up logging ----
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # ---- Resolve spiders ----
    spiders = get_spiders()
    if spider_name:
        spider_map = {s.name: s for s in spiders}
        if spider_name not in spider_map:
            logger.error("Unknown spider: %s", spider_name)
            return
        spiders = [spider_map[spider_name]]

    # ---- Configure Scrapy settings ----
    settings = get_project_settings()
    settings.set("LOG_LEVEL", log_level.upper(), priority="cmdline")

    if sink_class:
        settings.set("SINK_CLASS", sink_class, priority="cmdline")

    if sink_settings_raw:
        parsed = None
        txt = sink_settings_raw.strip()
        if txt.startswith("{"):
            try:
                parsed = json.loads(txt)
            except Exception:
                parsed = None
        if parsed is None:
            parsed = {}
            for part in txt.split(","):
                if not part:
                    continue
                if "=" in part:
                    k, v = part.split("=", 1)
                    parsed[k.strip()] = v.strip()
        settings.set("SINK_SETTINGS", parsed, priority="cmdline")

    # ---- Crawl ----
    if no_crawl or not run_crawl:
        logger.info("Crawl skipped")
        return

    process = CrawlerProcess(settings=settings)
    for spider in spiders:
        process.crawl(spider)
    process.start()


if __name__ == "__main__":
    main()
