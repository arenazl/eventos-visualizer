"""
🌍 ALLEVENTS.IN SCRAPER - Simple HTTP scraping
"""

import aiohttp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

async def scrape_allevents(location: str = "miami", limit: int = 10):
    """
    Simple scraper for AllEvents.in - works with regular HTTP
    """
    url = f"https://allevents.in/{location.lower().replace(' ', '-')}/all"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                events = []
                # Find event cards
                event_cards = soup.find_all('li', class_='event-item', limit=limit)
                
                for card in event_cards:
                    title = card.find('h3', class_='event-title')
                    venue = card.find('span', class_='venue-name')
                    date = card.find('span', class_='event-date')
                    
                    if title:
                        events.append({
                            'title': title.text.strip(),
                            'venue_name': venue.text.strip() if venue else location,
                            'start_datetime': date.text.strip() if date else None,
                            'source': 'AllEvents.in'
                        })
                
                logger.info(f"✅ Found {len(events)} events from AllEvents.in")
                return events
                
    except Exception as e:
        logger.error(f"❌ Error scraping AllEvents: {e}")
        return []

# Test it
if __name__ == "__main__":
    import asyncio
    events = asyncio.run(scrape_allevents("miami"))
    for e in events[:3]:
        print(f"- {e['title']}")