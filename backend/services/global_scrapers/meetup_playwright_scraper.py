"""
🎭 MEETUP PLAYWRIGHT SCRAPER - Using real browser to bypass Cloudflare
Scraper that uses Playwright to get Meetup events
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Meetup_PlaywrightScraper:  # Fixed class name to match auto-discovery pattern
    """
    🎭 MEETUP SCRAPER WITH PLAYWRIGHT (DISABLED - OLD VERSION)
    
    Uses real browser automation to:
    - Bypass Cloudflare protection
    - Execute JavaScript
    - Extract events from __NEXT_DATA__
    """
    
    # 🔴 DISABLED - Using meetup_scraper.py instead
    enabled_by_default = False
    
    def __init__(self):
        self.browser = None
        self.playwright = None
        
    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            logger.info("🎭 Playwright browser initialized for Meetup")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Playwright: {e}")
            return False
    
    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_meetup_events(
        self, 
        location: str = "Miami",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        🎭 SCRAPE MEETUP USING PLAYWRIGHT
        
        Args:
            location: City name (e.g., "Miami", "New York")
            limit: Maximum number of events to return
            
        Returns:
            List of parsed events
        """
        
        if not self.browser:
            if not await self.initialize():
                return []
        
        try:
            # Create a new page with realistic viewport and user agent
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # Build URL - simple format for now
            url = f"https://www.meetup.com/find/?location={location}&source=EVENTS"
            logger.info(f"🎭 Navigating to: {url}")
            
            # Navigate to Meetup - don't wait for full network idle
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for the __NEXT_DATA__ script to be present
            try:
                await page.wait_for_selector('#__NEXT_DATA__', timeout=10000)
            except:
                # Try to wait for any event element as fallback
                try:
                    await page.wait_for_selector('[data-testid*="event"]', timeout=5000)
                except:
                    pass
            
            # Small delay to ensure JS execution
            await page.wait_for_timeout(1000)
            
            # Extract __NEXT_DATA__ JSON
            json_data = await page.evaluate('''
                () => {
                    const scriptTag = document.getElementById('__NEXT_DATA__');
                    if (scriptTag) {
                        return JSON.parse(scriptTag.textContent);
                    }
                    return null;
                }
            ''')
            
            await page.close()
            
            if not json_data:
                logger.warning("⚠️ No __NEXT_DATA__ found on Meetup page")
                return []
            
            # Extract events from Apollo State
            events = self._extract_events_from_apollo(json_data, location, limit)
            logger.info(f"✅ Extracted {len(events)} events from Meetup")
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error scraping Meetup with Playwright: {e}")
            return []
    
    def _extract_events_from_apollo(
        self, 
        json_data: Dict, 
        location: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Extract events from Apollo State in __NEXT_DATA__
        """
        try:
            # Navigate to Apollo State
            props = json_data.get('props', {})
            page_props = props.get('pageProps', {})
            apollo_state = page_props.get('__APOLLO_STATE__', {})
            
            if not apollo_state:
                logger.warning("⚠️ No Apollo State found in JSON")
                return []
            
            events = []
            
            # Extract events from Apollo State
            for key, value in apollo_state.items():
                if key.startswith('Event:') and isinstance(value, dict):
                    if 'title' in value:  # Valid event
                        event = self._parse_apollo_event(value, location)
                        if event:
                            events.append(event)
                            if len(events) >= limit:
                                break
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extracting events from Apollo: {e}")
            return []
    
    def _parse_apollo_event(self, event_data: Dict, location: str) -> Optional[Dict[str, Any]]:
        """
        Parse individual event from Apollo State
        """
        try:
            # Extract basic info
            title = event_data.get('title', 'Meetup Event')
            event_url = event_data.get('eventUrl', '')
            
            # Date and time
            date_time = event_data.get('dateTime')
            if date_time:
                try:
                    # Parse ISO format
                    dt = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_date = date_time
            else:
                formatted_date = None
            
            # Venue information
            venue = event_data.get('venue', {})
            if isinstance(venue, dict):
                venue_name = venue.get('name', location)
                venue_address = venue.get('address', '')
            else:
                venue_name = location
                venue_address = ''
            
            # Group info
            group = event_data.get('group', {})
            if isinstance(group, dict):
                group_name = group.get('name', '')
            else:
                group_name = ''
            
            # Build description
            description = event_data.get('description', '')
            if not description and group_name:
                description = f"Event organized by {group_name}"
            
            # Image
            featured_photo = event_data.get('featuredEventPhoto', {})
            if isinstance(featured_photo, dict):
                image_url = featured_photo.get('highResUrl') or featured_photo.get('baseUrl', '')
            else:
                image_url = ''
            
            # Fee settings
            fee_settings = event_data.get('feeSettings', {})
            is_free = True
            price = None
            if isinstance(fee_settings, dict):
                if fee_settings.get('amount'):
                    price = fee_settings['amount']
                    is_free = False
            
            return {
                'title': title,
                'description': description[:500] if description else f"Meetup event in {location}",
                'start_datetime': formatted_date,
                'venue_name': venue_name,
                'venue_address': venue_address,
                'event_url': event_url if event_url.startswith('http') else f"https://www.meetup.com{event_url}",
                'image_url': image_url,
                'category': 'Community Events',
                'is_free': is_free,
                'price': price,
                'source': 'Meetup',
                'external_id': event_data.get('id'),
                'group_name': group_name
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing Apollo event: {e}")
            return None


# Singleton instance
meetup_playwright_scraper = MeetupPlaywrightScraper()


async def test_meetup_playwright():
    """Test function to verify Meetup Playwright scraper works"""
    scraper = MeetupPlaywrightScraper()
    
    try:
        # Test with Miami
        events = await scraper.scrape_meetup_events("Miami", limit=5)
        
        if events:
            print(f"\n✅ Found {len(events)} events in Miami:")
            for i, event in enumerate(events[:3], 1):
                print(f"\n{i}. {event['title']}")
                print(f"   📅 {event.get('start_datetime', 'TBD')}")
                print(f"   📍 {event.get('venue_name', 'Location TBD')}")
                print(f"   💰 {'Free' if event.get('is_free') else f'${event.get('price', 'N/A')}'}")
        else:
            print("❌ No events found")
            
    finally:
        await scraper.close()


if __name__ == "__main__":
    # Run test
    asyncio.run(test_meetup_playwright())