# Test Fixtures

This directory contains HTML snapshots for extractor testing.

## Required Files

Place the following HTML snapshot files in this directory:

- `ap.html` - AP News article
- `bbc.html` - BBC article
- `cbs.html` - CBS News article
- `cnn.html` - CNN article
- `foxnews.html` - Fox News article
- `guardian.html` - The Guardian article
- `nbc.html` - NBC News article
- `nyt.html` - New York Times article

## Capturing HTML Snapshots

To capture HTML for testing:

```bash
# Example: Save full HTML from a URL
curl -L "https://apnews.com/article/..." > tests/fixtures/ap.html
```

Or use your browser:
1. Navigate to an article page
2. Right-click → "Save Page As..." → "Webpage, Complete"
3. Save the HTML file to this directory with the appropriate name

## Running Tests

Once fixtures are in place, run:

```bash
# Run all extractor tests
pytest tests/extractors/

# Run specific extractor tests
pytest tests/extractors/test_ap.py
pytest tests/extractors/test_bbc.py

# With verbose output
pytest tests/extractors/ -v
```

## Test Structure

Each test file follows this pattern:

1. **Fixture loading**: Load HTML from file, skip if not present
2. **Response creation**: Create Scrapy HtmlResponse object
3. **Extraction tests**: Call extractor.extract() and assert expectations
4. **Assertions focus on**:
   - Structural guarantees (title, body present)
   - Body length thresholds (>300 chars minimum)
   - Confidence ranges
   - Extraction methods
   - Content quality (no junk, proper filtering)
   - Error tracking

Tests are designed to be resilient to minor content changes while catching structural breakage.
