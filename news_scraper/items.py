# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    author = scrapy.Field()
    text = scrapy.Field()
    summary = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    published_at = scrapy.Field()
    scraped_at = scrapy.Field()
    # stable fields for sinks
    url_hash = scrapy.Field()
    fingerprint = scrapy.Field()
