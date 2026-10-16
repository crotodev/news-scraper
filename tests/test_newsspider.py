"""Item serialization contract for the raw_news topic."""

import json

from scrapy.http import HtmlResponse

from news_scraper.spiders.newsspider import NewsSpider

HTML = b"""<html><head><title>Big Headline</title></head><body>
<h1>Big Headline</h1>
<p>The city council approved a new budget on Tuesday after a long debate.
Officials said the plan funds schools, roads and public transit for the year.</p>
<p>Residents expressed mixed feelings about the tax changes included in the plan.</p>
</body></html>"""


def _item():
    response = HtmlResponse(
        url="https://example.com/news/budget", body=HTML, encoding="utf-8"
    )
    return NewsSpider.process_article(response, "example.com", NewsSpider.config)


def test_item_is_json_serializable_with_all_fields() -> None:
    payload = json.loads(json.dumps(dict(_item())))

    assert set(payload) == {
        "title",
        "author",
        "text",
        "summary",
        "url",
        "source",
        "published_at",
        "scraped_at",
        "url_hash",
        "fingerprint",
    }
    assert len(payload["url_hash"]) == 64


def test_missing_publish_date_is_null_not_empty_string() -> None:
    assert _item()["published_at"] is None


def test_scraped_at_is_utc_iso() -> None:
    assert _item()["scraped_at"].endswith("+00:00")
