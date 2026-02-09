"""
Typer-based CLI for the news-scraper project.

Usage:
    python -m news_scraper.cli crawl
    python -m news_scraper.cli crawl apnews
    python -m news_scraper.cli crawl apnews --loglevel DEBUG
    python -m news_scraper.cli crawl bbc --start-urls "https://www.bbc.com/news"
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import typer
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from news_scraper.spiders.newsspider import NewsSpider

# ---------------------------------------------------------------------------
# Optional Rich imports
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

app = typer.Typer(add_completion=False)


# ---------------------------------------------------------------------------
# Rich helpers
# ---------------------------------------------------------------------------


def _should_use_rich(rich_flag: Optional[bool]) -> bool:
    """Determine whether to use Rich output.

    * ``True``  -> use Rich if available (warn if not).
    * ``False`` -> plain output.
    * ``None``  -> auto: Rich only when available AND stdout is a TTY.
    """
    if rich_flag is True:
        if not RICH_AVAILABLE:
            print(
                "Warning: --rich requested but 'rich' is not installed; using plain output.",
                file=sys.stderr,
            )
        return RICH_AVAILABLE
    if rich_flag is False:
        return False
    return RICH_AVAILABLE and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _print_banner(
    console,
    use_rich: bool,
    spider_name: str,
    loglevel: str,
    output: Optional[Path],
    start_urls: Optional[str],
) -> None:
    """Print a startup banner showing crawl configuration."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if use_rich:
        lines = [
            f"[bold]Spider:[/bold]     {spider_name}",
            f"[bold]Log level:[/bold]  {loglevel}",
            f"[bold]Output:[/bold]     {output or 'none'}",
        ]
        if start_urls:
            lines.append(f"[bold]Start URLs:[/bold] {start_urls}")
        else:
            lines.append("[bold]Start URLs:[/bold] default")
        lines.append(f"[bold]Timestamp:[/bold]  {ts}")
        panel = Panel(
            "\n".join(lines),
            title="[bold blue]News Scraper[/bold blue]",
            border_style="blue",
        )
        console.print(panel)
    else:
        print(
            f"News Scraper - Spider: {spider_name}, Log level: {loglevel}",
            file=sys.stderr,
        )
        print(f"  Output:     {output or 'none'}", file=sys.stderr)
        print(f"  Start URLs: {start_urls or 'default'}", file=sys.stderr)
        print(f"  Timestamp:  {ts}", file=sys.stderr)


def _print_resolved_config(
    console,
    use_rich: bool,
    spider_names: list[str],
    loglevel: str,
    sink_class: Optional[str],
    sink_settings: Optional[dict],
    feeds_setting: Optional[dict],
    start_urls: Optional[list[str]],
) -> None:
    """Print resolved configuration for a dry-run style summary."""
    spider_label = ", ".join(spider_names)
    sink_settings_label = (
        json.dumps(sink_settings) if sink_settings is not None else "none"
    )
    start_urls_label = ", ".join(start_urls) if start_urls else "default"

    if use_rich:
        table = Table(title="Resolved Config")
        table.add_column("Setting", style="bold")
        table.add_column("Value")
        table.add_row("Spiders", spider_label)
        table.add_row("LOG_LEVEL", loglevel)
        table.add_row("SINK_CLASS", sink_class or "none")
        if sink_settings is not None:
            table.add_row("SINK_SETTINGS", sink_settings_label)
        if feeds_setting is not None:
            table.add_row("FEEDS", json.dumps(feeds_setting))
        table.add_row("Start URLs", start_urls_label)
        console.print(table)
    else:
        print("\nResolved Config:", file=sys.stderr)
        print(f"  Spiders:      {spider_label}", file=sys.stderr)
        print(f"  LOG_LEVEL:    {loglevel}", file=sys.stderr)
        print(f"  SINK_CLASS:   {sink_class or 'none'}", file=sys.stderr)
        if sink_settings is not None:
            print(f"  SINK_SETTINGS: {sink_settings_label}", file=sys.stderr)
        if feeds_setting is not None:
            print(f"  FEEDS:        {json.dumps(feeds_setting)}", file=sys.stderr)
        print(f"  Start URLs:   {start_urls_label}", file=sys.stderr)


def _attach_signals(
    crawler, counters: dict, item_stats: list, max_samples: int
) -> None:
    """Connect Scrapy signal handlers to track crawl progress."""
    from scrapy import signals

    def on_request_scheduled(request, spider):
        counters["requests"] += 1

    def on_response_received(response, request, spider):
        counters["responses"] += 1

    def on_item_scraped(item, response, spider):
        counters["items"] += 1
        if len(item_stats) < max_samples:
            sample = {}
            for field in (
                "title",
                "author",
                "published_at",
                "parse_ok",
                "parse_error",
                "extraction_method",
                "content_length_chars",
                "author_source",
            ):
                sample[field] = item.get(field)
            item_stats.append(sample)

    def on_spider_error(failure, response, spider):
        counters["errors"] += 1

    crawler.signals.connect(
        on_request_scheduled, signal=signals.request_scheduled, weak=False
    )
    crawler.signals.connect(
        on_response_received, signal=signals.response_received, weak=False
    )
    crawler.signals.connect(on_item_scraped, signal=signals.item_scraped, weak=False)
    crawler.signals.connect(on_spider_error, signal=signals.spider_error, weak=False)


def _print_summary(console, use_rich: bool, crawler_stats, counters: dict) -> None:
    """Print end-of-run summary from crawler stats and signal counters."""
    finish_reason = "N/A"
    elapsed = "N/A"
    log_errors = 0
    retry_count = 0

    if crawler_stats:
        finish_reason = str(crawler_stats.get_value("finish_reason", "N/A"))
        raw_elapsed = crawler_stats.get_value("elapsed_time_seconds", None)
        if raw_elapsed is not None:
            elapsed = f"{raw_elapsed:.1f}s"
        log_errors = crawler_stats.get_value("log_count/ERROR", 0)
        retry_count = crawler_stats.get_value(
            "retry/count", 0
        ) + crawler_stats.get_value("retry/max_reached", 0)

    if use_rich:
        table = Table(title="Crawl Summary", show_lines=False)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Finish reason", finish_reason)
        table.add_row("Elapsed time", str(elapsed))
        table.add_row("Requests scheduled", str(counters["requests"]))
        table.add_row("Responses received", str(counters["responses"]))
        table.add_row("Items scraped", str(counters["items"]))
        table.add_row("Spider errors", str(counters["errors"]))
        if log_errors:
            table.add_row("Log ERROR count", str(log_errors))
        if retry_count:
            table.add_row("Retries", str(retry_count))

        console.print()
        console.print(table)
    else:
        print("\nCrawl Summary:", file=sys.stderr)
        print(f"  Finish reason:      {finish_reason}", file=sys.stderr)
        print(f"  Elapsed time:       {elapsed}", file=sys.stderr)
        print(f"  Requests scheduled: {counters['requests']}", file=sys.stderr)
        print(f"  Responses received: {counters['responses']}", file=sys.stderr)
        print(f"  Items scraped:      {counters['items']}", file=sys.stderr)
        print(f"  Spider errors:      {counters['errors']}", file=sys.stderr)
        if log_errors:
            print(f"  Log ERROR count:    {log_errors}", file=sys.stderr)
        if retry_count:
            print(f"  Retries:            {retry_count}", file=sys.stderr)


def _print_extractor_quality(console, use_rich: bool, item_stats: list) -> None:
    """Print extractor quality table from sampled items."""
    if not item_stats:
        return

    total = len(item_stats)
    ok_count = sum(1 for s in item_stats if s.get("parse_ok"))
    fail_count = total - ok_count
    has_title = sum(1 for s in item_stats if s.get("title"))
    has_author = sum(1 for s in item_stats if s.get("author"))
    has_text = sum(1 for s in item_stats if (s.get("content_length_chars") or 0) > 0)
    has_date = sum(1 for s in item_stats if s.get("published_at"))
    avg_len = sum(s.get("content_length_chars") or 0 for s in item_stats) / max(
        total, 1
    )

    # Group by extraction_method
    methods: dict[str, int] = {}
    for s in item_stats:
        m = s.get("extraction_method") or "unknown"
        methods[m] = methods.get(m, 0) + 1

    def _pct(n: int) -> str:
        return f"{n / total * 100:.0f}%"

    if use_rich:
        table = Table(title=f"Extractor Quality ({total} sampled)")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        table.add_column("%", justify="right")

        table.add_row("parse_ok", str(ok_count), _pct(ok_count))
        table.add_row("parse_fail", str(fail_count), _pct(fail_count))
        table.add_row("Has title", str(has_title), _pct(has_title))
        table.add_row("Has author", str(has_author), _pct(has_author))
        table.add_row("Has text", str(has_text), _pct(has_text))
        table.add_row("Has published_at", str(has_date), _pct(has_date))
        table.add_row("Avg content length", f"{avg_len:.0f} chars", "")

        for method, count in sorted(methods.items()):
            table.add_row(f"  method: {method}", str(count), _pct(count))

        console.print(table)
    else:
        print(f"\nExtractor Quality ({total} sampled):", file=sys.stderr)
        print(
            f"  parse_ok:         {ok_count}/{total} ({_pct(ok_count)})",
            file=sys.stderr,
        )
        print(
            f"  parse_fail:       {fail_count}/{total} ({_pct(fail_count)})",
            file=sys.stderr,
        )
        print(f"  Has title:        {has_title}/{total}", file=sys.stderr)
        print(f"  Has author:       {has_author}/{total}", file=sys.stderr)
        print(f"  Has text:         {has_text}/{total}", file=sys.stderr)
        print(f"  Has published_at: {has_date}/{total}", file=sys.stderr)
        print(f"  Avg content len:  {avg_len:.0f} chars", file=sys.stderr)
        for method, count in sorted(methods.items()):
            print(f"  method={method}: {count}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Helpers (migrated from crawl.py)
# ---------------------------------------------------------------------------


def _ensure_nltk_data() -> None:
    """Download NLTK tokenizers only if not already present."""
    import nltk

    required = ["tokenizers/punkt", "tokenizers/punkt_tab"]
    for resource in required:
        try:
            nltk.data.find(resource)
        except LookupError:
            name = resource.split("/")[-1]
            nltk.download(name, quiet=True)


def get_spiders() -> List[type[NewsSpider]]:
    """Return the list of spider classes used by the project."""
    from news_scraper.spiders import (
        APNewsSpider,
        BBCSpider,
        CBSNewsSpider,
        CNNSpider,
        FoxNewsSpider,
        GuardianSpider,
        NBCNewsSpider,
    )

    return [
        CNNSpider,
        FoxNewsSpider,
        NBCNewsSpider,
        BBCSpider,
        APNewsSpider,
        GuardianSpider,
        CBSNewsSpider,
    ]


def build_jsonl_paths(spiders, data_dir: str = "."):
    """Build JSONL output paths for each spider using its ``name`` attribute."""
    if not os.path.exists(os.path.join(data_dir, "data")):
        os.makedirs(os.path.join(data_dir, "data"), exist_ok=True)
    return [
        os.path.join(data_dir, "data", f"{spider.name}_items.jsonl")
        for spider in spiders
    ]


_SINK_MAP = {
    "jsonl": "news_scraper.sinks.jsonl.JSONLSink",
    "kafka": "news_scraper.sinks.kafka.KafkaSink",
    "mongo": "news_scraper.sinks.mongo.MongoSink",
}

_FEED_FORMAT_MAP = {
    ".jsonl": "jsonlines",
    ".json": "json",
    ".csv": "csv",
    ".xml": "xml",
}


def _resolve_spider(name: str, spiders):
    """Find a spider class by its ``name`` attribute or exit with an error."""
    spider_names = {s.name: s for s in spiders}
    if name not in spider_names:
        typer.echo(
            f"Error: Unknown spider '{name}'. "
            f"Available spiders: {', '.join(sorted(spider_names.keys()))}",
            err=True,
        )
        raise typer.Exit(code=1)
    return spider_names[name]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.callback()
def _app_callback() -> None:
    """News scraper CLI."""


@app.command()
def crawl(
    spider: Optional[str] = typer.Argument(
        None,
        help="Spider name to run (e.g. apnews, bbc, cnn). If omitted, run all spiders.",
    ),
    start_urls: Optional[str] = typer.Option(
        None,
        "--start-urls",
        help="Comma-separated list of start URLs (overrides spider defaults)",
    ),
    loglevel: str = typer.Option(
        "INFO",
        "--loglevel",
        help="Scrapy log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional output file (format inferred from suffix: .jsonl, .csv, .json)",
    ),
    # ---- legacy options preserved from crawl.py ----
    sink: Optional[str] = typer.Option(
        None,
        "--sink",
        help="Shorthand sink type: jsonl, kafka, or mongo",
    ),
    jsonl_path: Optional[str] = typer.Option(
        None,
        "--jsonl-path",
        help="Output path for JSONL sink (requires --sink jsonl)",
    ),
    sink_class: Optional[str] = typer.Option(
        None,
        "--sink-class",
        help="Full import path to a custom sink class",
    ),
    sink_settings: Optional[str] = typer.Option(
        None,
        "--sink-settings",
        help="Sink settings as JSON string or comma-separated key=val pairs",
    ),
    no_crawl: bool = typer.Option(
        False,
        "--no-crawl",
        help="Skip crawl execution (useful for testing)",
    ),
    # ---- Rich / presentation options ----
    rich: Optional[bool] = typer.Option(
        None,
        "--rich/--no-rich",
        help="Enable/disable Rich terminal output (default: auto-detect TTY)",
    ),
    show_items: bool = typer.Option(
        False,
        "--show-items",
        help="Show extractor quality table at end of crawl",
    ),
    max_item_samples: int = typer.Option(
        50,
        "--max-item-samples",
        help="Max items to sample for extractor quality table",
    ),
) -> None:
    """Run a Scrapy spider by name.

    \b
    Examples:
        crawl
        crawl apnews
        crawl apnews --loglevel DEBUG
        crawl bbc --start-urls "https://www.bbc.com/news"
        crawl cnn --output ./data/cnn.jsonl
    """
    _ensure_nltk_data()

    # Configure logging
    log_level_upper = loglevel.upper()
    numeric_level = getattr(logging, log_level_upper, None)
    if numeric_level is None:
        typer.echo(f"Error: Invalid log level '{loglevel}'", err=True)
        raise typer.Exit(code=1)

    logger = logging.getLogger(__name__)

    # Resolve spider
    all_spiders = get_spiders()
    if spider:
        spider_names = [spider]
        spider_classes = [_resolve_spider(spider, all_spiders)]
    else:
        spider_names = sorted([s.name for s in all_spiders])
        spider_classes = [_resolve_spider(name, all_spiders) for name in spider_names]
    logger.info(f"Selected spider(s): {', '.join(spider_names)}")

    # Load Scrapy settings
    settings = get_project_settings()
    settings.set("LOG_LEVEL", log_level_upper, priority="cmdline")
    settings.set(
        "LOG_FORMAT",
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        priority="cmdline",
    )
    settings.set("LOG_DATEFORMAT", "%Y-%m-%d %H:%M:%S", priority="cmdline")

    # --sink shorthand
    resolved_sink_class = None
    resolved_sink_settings = None
    feeds_setting = None

    if sink:
        if sink not in _SINK_MAP:
            typer.echo(
                f"Error: Unknown sink '{sink}'. Choose from: {', '.join(_SINK_MAP)}",
                err=True,
            )
            raise typer.Exit(code=1)
        settings.set("SINK_CLASS", _SINK_MAP[sink], priority="cmdline")
        resolved_sink_class = _SINK_MAP[sink]
        logger.info(f"Using sink: {sink} ({_SINK_MAP[sink]})")

        if sink == "jsonl" and jsonl_path:
            settings.set("SINK_SETTINGS", {"path": jsonl_path}, priority="cmdline")
            resolved_sink_settings = {"path": str(jsonl_path)}
            logger.info(f"JSONL output path: {jsonl_path}")

    # --sink-class / env override
    effective_sink_class = sink_class or os.environ.get("SINK_CLASS")
    if effective_sink_class:
        settings.set("SINK_CLASS", effective_sink_class, priority="cmdline")
        resolved_sink_class = effective_sink_class
        logger.info(f"Overriding sink class: {effective_sink_class}")

    # --sink-settings / env override
    sink_settings_val = sink_settings or os.environ.get("SINK_SETTINGS")
    if sink_settings_val:
        parsed = None
        txt = sink_settings_val.strip()
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
        resolved_sink_settings = parsed
        logger.info(f"Overriding sink settings: {parsed}")

    # --output: set Scrapy FEEDS
    if output:
        suffix = output.suffix.lower()
        fmt = _FEED_FORMAT_MAP.get(suffix)
        if fmt is None:
            typer.echo(
                f"Error: Unsupported output format '{suffix}'. "
                f"Supported: {', '.join(_FEED_FORMAT_MAP)}",
                err=True,
            )
            raise typer.Exit(code=1)
        settings.set(
            "FEEDS",
            {str(output): {"format": fmt, "overwrite": True}},
            priority="cmdline",
        )
        feeds_setting = {str(output): {"format": fmt, "overwrite": True}}
        logger.info(f"Output file: {output} (format={fmt})")

    # Build spider kwargs only when a real start_urls override is provided.
    spider_kwargs: dict = {}
    start_urls_list: Optional[list[str]] = None
    if start_urls is not None:
        parsed_start_urls = [u.strip() for u in start_urls.split(",") if u.strip()]
        if parsed_start_urls:
            start_urls_list = parsed_start_urls
            spider_kwargs["start_urls"] = start_urls_list
            logger.info(f"Overriding start_urls: {spider_kwargs['start_urls']}")
        else:
            logger.warning(
                "Ignoring empty --start-urls override; using spider defaults."
            )

    # ---- Rich presentation ----
    use_rich = _should_use_rich(rich)
    console = Console(stderr=True) if (use_rich and RICH_AVAILABLE) else None

    spider_label = spider if spider else f"all ({', '.join(spider_names)})"
    _print_banner(console, use_rich, spider_label, loglevel, output, start_urls)
    _print_resolved_config(
        console,
        use_rich,
        spider_names,
        log_level_upper,
        resolved_sink_class,
        resolved_sink_settings,
        feeds_setting,
        start_urls_list,
    )

    if no_crawl:
        logger.info("Crawl skipped (--no-crawl flag)")
        return

    # Set up counters and item stats for signal tracking
    counters = {"requests": 0, "responses": 0, "items": 0, "errors": 0}
    item_stats: list[dict] = []

    # Create crawler and attach signal handlers
    logger.info("Starting crawl process...")
    process = CrawlerProcess(settings=settings)
    crawlers = []
    for spider_cls in spider_classes:
        crawler = process.create_crawler(spider_cls)
        _attach_signals(crawler, counters, item_stats, max_item_samples)
        crawlers.append(crawler)

    # Hook up Rich progress updates via signals
    _progress_ctx = None
    if use_rich:
        from scrapy import signals as scrapy_signals

        _progress_ctx = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        )
        _task_id = _progress_ctx.add_task("Starting crawl...", total=None)

        def _update_progress(**kwargs):
            _progress_ctx.update(
                _task_id,
                description=(
                    f"[cyan]{counters['requests']}[/] req | "
                    f"[green]{counters['responses']}[/] resp | "
                    f"[yellow]{counters['items']}[/] items | "
                    f"[red]{counters['errors']}[/] err"
                ),
            )

        for crawler in crawlers:
            crawler.signals.connect(
                _update_progress, signal=scrapy_signals.request_scheduled, weak=False
            )
            crawler.signals.connect(
                _update_progress, signal=scrapy_signals.response_received, weak=False
            )
            crawler.signals.connect(
                _update_progress, signal=scrapy_signals.item_scraped, weak=False
            )
            crawler.signals.connect(
                _update_progress, signal=scrapy_signals.spider_error, weak=False
            )

    # When using pre-created crawlers + direct crawler.crawl(), CrawlerProcess
    # must track each Deferred so process.start() waits for active crawls.
    def _track_crawl_deferred(crawler, deferred):
        process.crawlers.add(crawler)
        process._active.add(deferred)

        def _finalize(result):
            process.crawlers.discard(crawler)
            process._active.discard(deferred)
            process.bootstrap_failed |= not getattr(crawler, "spider", None)
            return result

        deferred.addBoth(_finalize)
        return deferred

    logger.info("Start URLs override keys: %s", list(spider_kwargs.keys()))
    deferreds = []
    for crawler in crawlers:
        logger.info("Scheduling spider: %s", crawler.spidercls.name)
        if spider_kwargs:
            d = crawler.crawl(**spider_kwargs)
        else:
            d = crawler.crawl()
        deferreds.append(_track_crawl_deferred(crawler, d))

    # Run the crawl (blocks until finished)
    try:
        if _progress_ctx is not None:
            with _progress_ctx:
                process.start()
        else:
            process.start()
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user.")

    logger.info("Crawl completed.")

    # ---- Post-crawl output ----
    summary_stats = None
    if len(crawlers) == 1 and hasattr(crawlers[0], "stats"):
        summary_stats = crawlers[0].stats
    _print_summary(console, use_rich, summary_stats, counters)

    if show_items:
        _print_extractor_quality(console, use_rich, item_stats)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main():
    """CLI entrypoint (used by console_scripts and __main__)."""
    app()


if __name__ == "__main__":
    main()
