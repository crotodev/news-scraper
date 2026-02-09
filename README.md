# News Scraper

A lightweight Scrapy-based news scraper that extracts article metadata and text from major outlets and writes "raw" NewsItem events to configurable sinks (JSONL, MongoDB, Kafka, S3, etc.).

This project keeps scraping (spiders + parsing + normalization) separate from delivery (sinks/pipelines). Spiders emit a stable `NewsItem` shape and pipelines adapt sinks.

## Features

- **Multi-source scraping**: Collects news from 8 major news outlets
- **Structured data extraction**: Extracts `title`, `author`, `text`, `summary`, `url`, `source`, `published_at`, `scraped_at`, plus `url_hash` and `fingerprint` for downstream deduplication
- **Pluggable sinks**: Choose destination(s) via settings or CLI (JSONL, MongoDB, Kafka, etc.)
- **Respectful crawling**: Obeys robots.txt and supports concurrency/autothrottle
- **NLP integration**: Uses NLTK/newspaper3k for article parsing and summarization
- **Random user agents**: Rotates user agents to avoid detection

## Supported News Sources

The scraper supports the following news outlets:

- **AP News** (`apnews`)
- **BBC** (`bbc`)
- **CBS News** (`cbsnews`)
- **CNN** (`cnn`)
- **Fox News** (`foxnews`)
- **The Guardian** (`guardian`)
- **NBC News** (`nbcnews`)
- **The New York Times** (`nytimes`)

## Installation

### Prerequisites

- Python 3.8+

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd news-scraper
```

2. Install core dependencies (no optional sink clients):

```bash
python -m pip install -e .
```

3. Optional sink clients

If you want to enable MongoDB or Kafka sinks, install the extras:

```bash
# MongoDB support
python -m pip install -e .[mongo]

# Kafka support (kafka-python and confluent-kafka fallback)
python -m pip install -e .[kafka]

# Or install everything
python -m pip install -e .[all]
```

4. (Optional) Configure MongoDB: install and run MongoDB and adjust `MONGO_URI` in `news_scraper/settings.py` if needed.

## Usage

### Run All Spiders (default)

Run the bundled `crawl.py` which starts the set of spiders defined in `get_spiders()`:

```bash
python crawl.py
```

CLI options

`crawl.py` accepts the following options:

- `--spider`: Run a specific spider by name (e.g. `cnn`, `bbc`). If omitted, runs all spiders.
- `--sink`: Sink type to use: `jsonl` (default), `kafka`, or `mongo`
- `--jsonl-path`: Path for JSONL output (default: `./data/{spider.name}_items.jsonl`)
- `--sink-class`: Full import path to a custom sink class (e.g. `news_scraper.sinks.kafka.KafkaSink`)
- `--sink-settings`: JSON string or comma-separated `key=val` pairs passed to the sink constructor

Examples:

```bash
# Run a specific spider
python crawl.py --spider cnn

# Use MongoDB sink
python crawl.py --sink mongo

# Use Kafka sink
python crawl.py --sink kafka

# Custom JSONL path
python crawl.py --jsonl-path ./output/news.jsonl

# Advanced: Custom sink class with JSON settings
python crawl.py --sink-class news_scraper.sinks.kafka.KafkaSink --sink-settings '{"bootstrap_servers":"localhost:9092","topic":"raw_news"}'

# Or use environment variables
export SINK_CLASS=news_scraper.sinks.mongo.MongoSink
export SINK_SETTINGS='{"uri":"mongodb://localhost:27017","db":"news_db","collection":"raw_news"}'
python crawl.py
```

You can also use Scrapy's normal CLI against individual spiders (they are unchanged):

```bash
scrapy crawl cnn -s SINK_CLASS=news_scraper.sinks.kafka.KafkaSink -s SINK_SETTINGS='{"bootstrap_servers":"localhost:9092","topic":"raw_news"}'
```

## Output

### Schema Definition

Every scraped article produces a `NewsItem` with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str \| None` | Article headline (whitespace normalized, stripped) |
| `author` | `str \| None` | Author name(s), comma-separated if multiple |
| `text` | `str \| None` | Full article text (whitespace collapsed). Set to `None` if < 200 chars (low-quality) |
| `summary` | `str \| None` | Article summary, truncated to `summary_max_chars` |
| `url` | `str` | Original article URL |
| `source` | `str` | Spider/source identifier (e.g., `"cnn"`, `"bbc"`) |
| `published_at` | `str \| None` | ISO-8601 UTC timestamp (e.g., `"2026-01-29T12:00:00Z"`), or `None` if not found |
| `scraped_at` | `str` | ISO-8601 UTC timestamp (always present) |
| `url_hash` | `str` | SHA-256 of canonicalized URL (tracking params removed) |
| `fingerprint` | `str` | SHA-256 of content basis for deduplication |
| `author_source` | `str` | How author was extracted: `"feed"`, `"newspaper3k"`, `"meta"`, or `"missing"` |
| `summary_max_chars` | `int` | Maximum allowed summary length (default: 512) |
| `summary_truncated` | `bool` | `True` if summary was truncated to fit `summary_max_chars` |
| `parse_ok` | `bool` | `True` if parsing succeeded, `False` otherwise |
| `parse_error` | `str \| None` | Error message if parsing failed |
| `extraction_method` | `str` | How content was extracted: `"newspaper3k"`, `"rss_only"`, or `"html_fallback"` |
| `content_length_chars` | `int` | Length of `text` field, or 0 if no text |

### Timestamp Rules

- **`scraped_at`**: Always present, always UTC ISO-8601 (`"2026-01-29T15:30:00Z"`)
- **`published_at`**: ISO-8601 UTC if found, otherwise `None`
  - If only a date is available (no time), time defaults to `00:00:00Z`
  - Dates are never invented—if parsing fails, returns `None`

### Summary Truncation

Summaries are capped at **512 characters** by default (configurable via `SUMMARY_MAX_CHARS`):

1. First attempts newspaper3k's NLP summary
2. Falls back to first 3-5 sentences of article text
3. Normalizes whitespace (collapses to single spaces)
4. Truncates at word boundary with `"..."` suffix if over limit
5. Sets `summary_truncated = True` if truncation occurred

### Text Normalization

All text fields undergo normalization before output:

- Whitespace collapsed: `re.sub(r"\s+", " ", text).strip()`
- Titles are stripped of leading/trailing whitespace
- If `text` exists but is < 200 characters, it's treated as low-quality and set to `None` (summary is preserved)

### Deduplication (url_hash & fingerprint)

Two-level deduplication prevents duplicate articles:

**`url_hash`** — Stable URL identifier:
- Canonicalizes URL (lowercase scheme/host, no trailing slash)
- Removes tracking parameters: `utm_*`, `gclid`, `fbclid`, `msclkid`, `ref`, `_ga`, etc.
- Same article with different referral sources produces identical hash

**`fingerprint`** — Content-based identifier:
- If text is available: `SHA256(title + first_2k_chars_of_text)`
- If text is missing: `SHA256(title + published_at + source)`
- Catches duplicate content published at different URLs

### Parse Debugging

Every output row includes debug fields for monitoring:

- `parse_ok`: `False` means parsing failed but row is still emitted
- `parse_error`: Human-readable error message (truncated to 200 chars)
- `extraction_method`: Currently always `"newspaper3k"` (reserved for future extractors)
- `content_length_chars`: Quick metric for content quality

**Failed parses still emit rows** with available data (`url`, `source`, `scraped_at`, `parse_ok=False`). This ensures:
- Pipeline never crashes on individual article failures
- Failure rates can be measured by source
- Partial data is preserved for debugging

### JSONL files

By default the project uses `news_scraper.sinks.jsonl.JsonlSink` and writes JSONL files into `./data/`.

Path template: `./data/{spider.name}_items.jsonl` (configurable via `path_template` sink setting).

Each line is a JSON object with the canonical `NewsItem` fields:

```json
{
    "title": "Article Title",
    "author": "Author Name",
    "text": "Full article text with normalized whitespace...",
    "summary": "Article summary truncated to 512 chars if needed...",
    "url": "https://example.com/article",
    "source": "cnn",
    "published_at": "2026-01-29T12:00:00Z",
    "scraped_at": "2026-01-29T12:30:00Z",
    "url_hash": "a1b2c3d4...",
    "fingerprint": "e5f6g7h8...",
    "author_source": "newspaper3k",
    "summary_max_chars": 512,
    "summary_truncated": false,
    "parse_ok": true,
    "parse_error": null,
    "extraction_method": "newspaper3k",
    "content_length_chars": 2847,
    "sentiment_label": null,
    "sentiment_score": null,
    "category_label": null,
    "category_score": null,
    "category_model_version": null
}
```

### MongoDB

If you enable `news_scraper.sinks.mongo.MongoSink` (install `[mongo]` extra), items are upserted into the configured database and collection. Configure via `MONGO_URI`, `MONGO_DATABASE`, `MONGO_COLLECTION` or use the `SINK_CLASS`/`SINK_SETTINGS` approach.

### Kafka

If you enable `news_scraper.sinks.kafka.KafkaSink` (install `[kafka]` extra), items are published as JSON to the configured topic (default `raw_news`). Use the `SINK_SETTINGS` to pass `bootstrap_servers` and `topic`.

## Local Kafka for testing

If you don't have a local Kafka, the repository includes a recommended `docker-compose.yml` snippet (see below) you can copy and run to start Zookeeper + Kafka bound to `localhost:9092`.

Example `docker-compose.yml`:

```yaml
version: "3.8"
services:
    zookeeper:
        image: bitnami/zookeeper:latest
        environment:
            - ALLOW_ANONYMOUS_LOGIN=yes
        ports:
            - "2181:2181"

    kafka:
        image: bitnami/kafka:latest
        environment:
            - KAFKA_BROKER_ID=1
            - KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
            - ALLOW_PLAINTEXT_LISTENER=yes
            - KAFKA_CFG_LISTENERS=PLAINTEXT://0.0.0.0:9092
            - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
        ports:
            - "9092:9092"
        depends_on:
            - zookeeper
```

Start it with:

```bash
docker compose up -d
```

Then verify with `kcat` or `nc`:

```bash
# brew install kcat
kcat -L -b localhost:9092
kcat -C -b localhost:9092 -t raw_news -o beginning -c 10 | jq .
```

## Project Structure

```
news-scraper/
├── crawl.py                    # Main script to run all spiders
├── requirements.txt            # Python dependencies
├── scrapy.cfg                  # Scrapy configuration
├── README.md                   # This file
└── news_scraper/
    ├── __init__.py
    ├── items.py                # Item definitions (NewsItem)
    ├── middlewares.py          # Custom middlewares
    ├── pipelines.py            # Data pipelines (File, MongoDB)
    ├── settings.py             # Scrapy settings
    └── spiders/
        ├── __init__.py
        ├── newsspider.py       # Base spider class with article detection
        ├── apnews.py           # AP News spider
        ├── bbc.py              # BBC spider
        ├── cbsnews.py          # CBS News spider
        ├── cnn.py              # CNN spider
        ├── foxnews.py          # Fox News spider
        ├── guardian.py         # Guardian spider
        ├── nbcnews.py          # NBC News spider
        └── nytimes.py          # NY Times spider
```

## Configuration

Key settings live in `news_scraper/settings.py`. The pipeline now uses a `SinkPipeline` adapter which loads `SINK_CLASS` and `SINK_SETTINGS` to instantiate a sink.

Defaults are JSONL sink (`news_scraper.sinks.jsonl.JsonlSink`) writing to `./data/{spider.name}_items.jsonl`.

You may configure sinks via:

- `SINK_CLASS` (full import path string)
- `SINK_SETTINGS` (dict of kwargs) — can be passed via Scrapy `-s` or via `crawl.py` CLI or environment variables

Examples:

```bash
# Using scrapy CLI
scrapy crawl cnn -s SINK_CLASS=news_scraper.sinks.kafka.KafkaSink -s SINK_SETTINGS='{"bootstrap_servers":"localhost:9092","topic":"raw_news"}'

# Using crawl.py
python crawl.py --sink-class news_scraper.sinks.mongo.MongoSink --sink-settings '{"uri":"mongodb://localhost:27017","db":"news_db","collection":"raw_news"}'
```

Notes:

- The project does not force Kafka/Mongo runtime dependencies. Install the extras described above when you enable those sinks.
- If both `kafka-python` and `confluent-kafka` are present, `kafka-python` is attempted first and `confluent-kafka` is a fallback.

## Dependencies

Core dependencies are installed by default. Optional sink clients are behind extras:

- `.[mongo]` installs `pymongo`
- `.[kafka]` installs `kafka-python` and `confluent-kafka`

Install core only:

```bash
python -m pip install -e .
```

Install with extras:

```bash
python -m pip install -e .[kafka]
python -m pip install -e .[mongo]
```

## Development

### Adding a new spider

1. Create a new spider file in `news_scraper/spiders/`.
2. Inherit from `NewsSpider` and optionally override `is_article_url()` with site-specific URL patterns.
3. Add the spider to `get_spiders()` in `crawl.py` if you want it included by the default runner.

Example:

```python
import re
from news_scraper.spiders.newsspider import NewsSpider

class NewSourceSpider(NewsSpider):
    name = "newsource"
    domain = "newsource.com"
    allowed_domains = ["newsource.com"]
    start_urls = ["https://www.newsource.com"]

    def is_article_url(self, url: str) -> bool:
        # Override with site-specific URL pattern matching
        # The base class will handle article page validation
        return bool(re.search(r'/\d{4}/\d{2}/\d{2}/', url)) or '/article/' in url
```

### Article Detection & Validation

The base `NewsSpider` class includes robust article detection:

- **URL filtering**: `is_article_url()` checks for date patterns, article slugs, and rejects section/tag/author pages
- **Content validation**: `is_article_page()` validates HTML structure (og:type, `<article>` tags)
- **Quality enforcement**: Articles must have:
  - Valid title
  - Text content ≥ 250 characters (MIN_ARTICLE_TEXT_LENGTH)
  - Summary (generated via newspaper3k NLP or first 5 sentences)
- **Discovery-first crawling**: The `parse()` method prioritizes:
  1. Extract articles from current page
  2. Discover and follow article links (up to MAX_FOLLOW_PER_PAGE=100)
  3. Skip section pages, list pages, and navigation

## Notes

- The scraper downloads the NLTK punkt tokenizer on first run.
- Spiders respect `robots.txt`.
- Default JSONL files are saved to `./data/`.
- Optional sink packages must be installed by the user (see Installation).
