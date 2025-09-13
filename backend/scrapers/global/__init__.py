"""
🌍 GLOBAL SCRAPERS
Scrapers que funcionan internacionalmente
"""

from .eventbrite import EventbriteScraper
from .meetup import MeetupScraper
from .facebook import FacebookScraper
from .allevents import AllEventsScraper

__all__ = [
    'EventbriteScraper',
    'MeetupScraper', 
    'FacebookScraper',
    'AllEventsScraper'
]