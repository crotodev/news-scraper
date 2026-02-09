"""
Deterministic article extraction framework.

This module provides platform-specific extractors that replace newspaper3k
with DOM-based extraction using JSON-LD and CSS selectors.
"""

from news_scraper.extractors.ap import APNewsExtractor
from news_scraper.extractors.bbc import BBCExtractor
from news_scraper.extractors.cbs import CBSExtractor
from news_scraper.extractors.cnn import CNNExtractor
from news_scraper.extractors.foxnews import FoxNewsExtractor
from news_scraper.extractors.guardian import GuardianExtractor
from news_scraper.extractors.nbc import NBCExtractor
from news_scraper.extractors.nyt import NYTimesExtractor

__all__ = [
    "APNewsExtractor",
    "BBCExtractor",
    "CBSExtractor",
    "CNNExtractor",
    "FoxNewsExtractor",
    "GuardianExtractor",
    "NBCExtractor",
    "NYTimesExtractor",
]
