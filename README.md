# News Scraper

A lightweight Scrapy-based news scraper that extracts article metadata and text from major outlets and writes "raw" NewsItem events to configurable sinks (JSONL, MongoDB, Kafka, S3, etc.).

This project keeps scraping (spiders + parsing + normalization) separate from delivery (sinks/pipelines). Spiders emit a stable `NewsItem` shape and pipelines adapt sinks.

## Features

- **Multi-source scraping**: Collects news from 11 major news outlets
- **Structured data extraction**: Extracts `title`, `author`, `text`, `summary`, `url`, `source`, `published_at`, `scraped_at`, plus `url_hash` and `fingerprint` for downstream deduplication
- **Pluggable sinks**: Choose destination(s) via settings or CLI (JSONL, MongoDB, Kafka, etc.)
- **Respectful crawling**: Obeys robots.txt and supports concurrency/autothrottle
- **NLP integration**: Uses NLTK/newspaper3k for article parsing and summarization
- **Random user agents**: Rotates user agents to avoid detection

## Supported News Sources

The scraper supports the following news outlets:

- **Al Jazeera** (`aljazeera`)
- **AP News** (`apnews`)
- **BBC** (`bbc`)
- **CNN** (`cnn`)
- **Fox News** (`foxnews`)
- **The Guardian** (`guardian`)
- **NBC News** (`nbcnews`)
- **The New York Times** (`nytimes`)
- **Reuters** (`reuters`)
- **The Wall Street Journal** (`wsj`)
- **The Washington Post** (`washingtonpost`)

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

CLI sink configuration

`crawl.py` accepts options to configure the sink used by the pipeline:

- `--sink-class`: full import path to the sink class (e.g. `news_scraper.sinks.kafka.KafkaSink`)
- `--sink-settings`: JSON string or comma-separated `key=val` pairs passed to the sink constructor

Examples:

```bash
# JSON settings
python crawl.py --sink-class news_scraper.sinks.kafka.KafkaSink --sink-settings '{"bootstrap_servers":"localhost:9092","topic":"raw_news"}'

# simple key=val pairs
python crawl.py --sink-class news_scraper.sinks.jsonl.JsonlSink --sink-settings path_template=./data/{spider.name}_items.jsonl

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

### JSONL files

By default the project uses `news_scraper.sinks.jsonl.JsonlSink` and writes JSONL files into `./data/`.

Path template: `./data/{spider.name}_items.jsonl` (configurable via `path_template` sink setting).

Each line is a JSON object with the canonical `NewsItem` fields:

```json
{
    "title": "Article Title",
    "author": "Author Name",
    "text": "Full article text...",
    "summary": "Article summary...",
    "url": "https://example.com/article",
    "source": "cnn",
    "published_at": "2026-01-16T12:00:00",
    "scraped_at": "2026-01-16T12:30:00",
    "url_hash": "...",
    "fingerprint": "..."
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
        ├── newsspider.py       # Base spider class
        ├── aljazeera.py        # Al Jazeera spider
        ├── apnews.py           # AP News spider
        ├── bbc.py              # BBC spider
        ├── cnn.py              # CNN spider
        ├── foxnews.py          # Fox News spider
        ├── guardian.py         # Guardian spider
        ├── nbcnews.py          # NBC News spider
        ├── nytimes.py          # NY Times spider
        ├── reuters.py          # Reuters spider
        ├── washingtonpost.py   # Washington Post spider
        └── wsj.py              # Wall Street Journal spider
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
2. Inherit from `NewsSpider` and implement `is_article_page()`.
3. Add the spider to `get_spiders()` in `crawl.py` if you want it included by the default runner.

Example:

```python
from news_scraper.spiders.newsspider import NewsSpider

class NewSourceSpider(NewsSpider):
    name = "newsource"
    domain = "newsource.com"
    allowed_domains = ["newsource.com"]
    start_urls = ["https://www.newsource.com"]
    
    def is_article_page(self, response) -> bool:
        # Implement logic to identify article pages
        return "article" in response.url
```

## Notes

- The scraper downloads the NLTK punkt tokenizer on first run.
- Spiders respect `robots.txt`.
- Default JSONL files are saved to `./data/`.
- Optional sink packages must be installed by the user (see Installation).