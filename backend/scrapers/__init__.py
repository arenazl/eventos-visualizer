"""
🎯 SCRAPERS V2 - Sistema modular de scraping con SSE
"""

from .base import IScraper, Event, ScraperResult
from .discovery import ScraperDiscovery

__all__ = ['IScraper', 'Event', 'ScraperResult', 'ScraperDiscovery']