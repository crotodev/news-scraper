# News Scraper - Scrapy crawlers with pluggable sinks
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NLTK_DATA=/usr/share/nltk_data

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt \
    && python -m nltk.downloader -d /usr/share/nltk_data punkt
COPY scrapy.cfg crawl.py ./
COPY news_scraper/ news_scraper/

# ---------------------------------------------------------------------------
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY tests/ tests/
CMD ["python", "-m", "pytest", "-q", "tests"]

# ---------------------------------------------------------------------------
FROM base AS production
CMD ["python", "crawl.py"]
