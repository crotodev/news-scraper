# Testing Guide

## Overview

This directory contains comprehensive unit and integration tests for the news scraper project using pytest.

## Test Files

- **test_newsspider.py** - Tests for the base NewsSpider class
- **test_spiders.py** - Tests for all specific spider implementations (CNN, BBC, etc.)
- **test_items.py** - Tests for NewsItem data structures
- **test_sinks.py** - Tests for sink implementations (JsonlSink, etc.)
- **test_crawl.py** - Integration tests for the crawl script

## Running Tests

### Install pytest

```bash
pip install pytest pytest-cov pytest-mock
# Or install dev dependencies
pip install -e ".[dev]"
```

### Basic usage

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_spiders.py
```

Run specific test class:
```bash
pytest tests/test_spiders.py::TestCNNSpider
```

Run specific test method:
```bash
pytest tests/test_spiders.py::TestCNNSpider::test_spider_attributes
```

Run with verbose output:
```bash
pytest -v
```

### Using markers

Run only unit tests:
```bash
pytest -m unit
```

Run only integration tests:
```bash
pytest -m integration
```

### Coverage reports

Run with coverage:
```bash
pytest --cov=news_scraper
```

Generate HTML coverage report:
```bash
pytest --cov=news_scraper --cov-report=html
```

View the report:
```bash
open htmlcov/index.html
```

### Other useful options

Run in parallel (requires pytest-xdist):
```bash
pip install pytest-xdist
pytest -n auto
```

Stop on first failure:
```bash
pytest -x
```

Show local variables in tracebacks:
```bash
pytest -l
```

Re-run failed tests:
```bash
pytest --lf
```

## Test Coverage

The test suite includes **57 passing tests** covering:

- ✅ Base NewsSpider functionality (test_newsspider.py)
  - URL validation with `is_article_url()`
  - Article page detection with `is_article_page()`
  - Content validation (MIN_ARTICLE_TEXT_LENGTH=250)
  - Article processing with summary fallback
  - Fingerprint generation
  - Item creation

- ✅ All 8 spider implementations (test_spiders.py)
  - Initialization and attributes
  - Article URL pattern matching
  - Consistency across spiders
  - Spiders: CNN, BBC, CBS News, Fox News, Guardian, NBC News, AP News, NY Times

- ✅ NewsItem structure
  - Field definitions
  - Data storage

- ✅ Sink implementations
  - JsonlSink file operations
  - Unicode handling
  - Error handling

- ✅ Crawl script
  - Command-line arguments
  - Spider scheduling
  - Configuration management

## Writing New Tests

When adding new features, follow these pytest patterns:

### 1. Use fixtures for setup
```python
@pytest.fixture
def my_spider():
    return MySpider()

def test_spider_feature(my_spider):
    result = my_spider.some_method()
    assert result == expected_value
```

### 2. Test with mock responses
```python
from scrapy.http import HtmlResponse, Request

def test_with_response():
    request = Request(url="https://example.com")
    response = HtmlResponse(
        url="https://example.com",
        request=request,
        body=b"<html>...</html>",
        encoding='utf-8'
    )
    result = spider.parse(response)
    assert result is not None
```

### 3. Parametrize tests for multiple inputs
```python
@pytest.mark.parametrize("url,expected", [
    ("http://example.com", True),
    ("https://example.com", True),
    ("ftp://example.com", False),
])
def test_url_validation(url, expected):
    assert spider.is_valid_url(url) == expected
```

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
- name: Install dependencies
  run: pip install -e ".[dev]"

- name: Run tests
  run: pytest --cov=news_scraper --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

**Import errors**: Run tests from project root:
```bash
cd /path/to/news-scraper
pytest
```

**Module not found**: Install in development mode:
```bash
pip install -e .
```

**Fixture not found**: Check fixture is defined in same file or conftest.py
