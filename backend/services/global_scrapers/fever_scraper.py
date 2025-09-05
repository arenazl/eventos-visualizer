"""
🔥 FEVER SCRAPER - Latin America & Global Experiences Platform
Scraper for Fever (feverup.com) - Popular in LATAM, Spain, USA
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.scraper_interface import BaseGlobalScraper, ScraperConfig
from services.url_discovery_service import IUrlDiscoveryService

logger = logging.getLogger(__name__)

class FeverScraper(BaseGlobalScraper):
    """
    🔥 FEVER SCRAPER - Experiences Platform
    
    CARACTERÍSTICAS:
    - Popular en América Latina (México, Brasil, Argentina, Colombia, Chile, Perú)
    - También en España, USA, Europa
    - Eventos únicos: Candlelight, experiencias inmersivas, gastronomía
    - Necesita Playwright para bypass de protección
    """
    
    # 🎯 DESHABILITADO POR DEFECTO - Solo para Latin America específico
    enabled_by_default: bool = False  # Too slow for general queries
    nearby_cities: bool = True
    priority: int = 4  # Slowest - Playwright required ~5000ms
    
    # City slugs for Latin America
    LATAM_CITIES = {
        # Mexico
        'mexico city': 'mexico-city',
        'ciudad de mexico': 'mexico-city',
        'cdmx': 'mexico-city',
        'guadalajara': 'guadalajara',
        'monterrey': 'monterrey',
        # Brazil
        'sao paulo': 'sao-paulo',
        'são paulo': 'sao-paulo',
        'rio de janeiro': 'rio-de-janeiro',
        'rio': 'rio-de-janeiro',
        # Argentina
        'buenos aires': 'buenos-aires',
        # Colombia
        'bogota': 'bogota',
        'bogotá': 'bogota',
        # Chile
        'santiago': 'santiago-chile',
        # Peru
        'lima': 'lima',
        # Spain (bonus)
        'madrid': 'madrid',
        'barcelona': 'barcelona',
        # USA
        'miami': 'miami',
        'new york': 'new-york',
        'los angeles': 'los-angeles',
    }
    
    def __init__(self, url_discovery_service: IUrlDiscoveryService, config: ScraperConfig = None):
        """Initialize Fever scraper"""
        super().__init__(url_discovery_service, config)
        self.browser = None
        self.playwright = None
    
    async def initialize_playwright(self):
        """Initialize Playwright browser"""
        if not self.browser:
            try:
                from playwright.async_api import async_playwright
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                logger.info("🎭 Playwright browser initialized for Fever")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to initialize Playwright for Fever: {e}")
                return False
        return True
    
    def _get_city_slug(self, location: str) -> str:
        """Convert city name to Fever URL slug"""
        location_lower = location.lower().strip()
        
        # Check if it's a known LATAM city
        if location_lower in self.LATAM_CITIES:
            return self.LATAM_CITIES[location_lower]
        
        # Default slug conversion
        return location_lower.replace(' ', '-').replace(',', '')
    
    async def scrape_events(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🔥 SCRAPE FEVER EVENTS
        
        Process:
        1. Initialize Playwright
        2. Navigate to Fever city page
        3. Extract events from React/Next.js structure
        4. Parse and standardize events
        """
        
        logger.info(f"🔥 Fever Scraper: Starting for '{location}'")
        
        # Initialize Playwright
        if not await self.initialize_playwright():
            logger.error("❌ Could not initialize Playwright for Fever")
            return []
        
        try:
            # Create browser context
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                locale='es-ES' if location in ['Buenos Aires', 'Mexico City', 'Bogota'] else 'en-US'
            )
            page = await context.new_page()
            
            # Build Fever URL
            city_slug = self._get_city_slug(location)
            url = f"https://feverup.com/{city_slug}"
            logger.info(f"🔥 Navigating to Fever: {url}")
            
            # Navigate to page
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            except:
                # Try alternative URL format
                url = f"https://feverup.com/en/{city_slug}/experiences"
                logger.info(f"🔄 Trying alternative URL: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Try to find event elements
            await page.wait_for_selector('[data-testid*="event"], .experience-card, [class*="Card"], a[href*="/experience/"]', 
                                        state='visible', 
                                        timeout=5000).catch(lambda: None)
            
            # Extract events using JavaScript
            events_data = await page.evaluate('''
                () => {
                    const events = [];
                    
                    // Try multiple selectors for Fever's event cards
                    const selectors = [
                        '[data-testid*="event"]',
                        '.experience-card',
                        '[class*="ExperienceCard"]',
                        'a[href*="/experience/"]',
                        '[class*="Card"][class*="experience"]',
                        'article[class*="experience"]'
                    ];
                    
                    let eventElements = [];
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            eventElements = elements;
                            break;
                        }
                    }
                    
                    eventElements.forEach((element, index) => {
                        if (index >= 30) return; // Limit
                        
                        try {
                            // Extract title
                            const titleEl = element.querySelector('h2, h3, [class*="title"], [class*="Title"]');
                            const title = titleEl ? titleEl.innerText : '';
                            
                            // Extract price
                            const priceEl = element.querySelector('[class*="price"], [class*="Price"]');
                            const priceText = priceEl ? priceEl.innerText : '';
                            
                            // Extract image
                            const imgEl = element.querySelector('img');
                            const imageUrl = imgEl ? imgEl.src : '';
                            
                            // Extract link
                            const linkEl = element.closest('a') || element.querySelector('a');
                            const eventUrl = linkEl ? linkEl.href : '';
                            
                            // Extract location/venue
                            const venueEl = element.querySelector('[class*="location"], [class*="venue"], [class*="Location"]');
                            const venue = venueEl ? venueEl.innerText : '';
                            
                            if (title) {
                                events.push({
                                    title: title,
                                    priceText: priceText,
                                    imageUrl: imageUrl,
                                    eventUrl: eventUrl,
                                    venue: venue
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing event:', e);
                        }
                    });
                    
                    return events;
                }
            ''')
            
            # Close page and context
            await page.close()
            await context.close()
            
            # Parse and standardize events
            events = []
            for event_data in events_data[:limit]:
                parsed = self._parse_fever_event(event_data, location)
                if parsed:
                    standardized = self._standardize_event(parsed)
                    events.append(standardized)
            
            logger.info(f"✅ Fever: {len(events)} events extracted for {location}")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error scraping Fever: {e}")
            return []
    
    def _parse_fever_event(self, event_data: Dict, location: str) -> Optional[Dict[str, Any]]:
        """Parse individual Fever event"""
        try:
            title = event_data.get('title', '').strip()
            if not title:
                return None
            
            # Parse price
            price_text = event_data.get('priceText', '')
            is_free = 'free' in price_text.lower() or 'gratis' in price_text.lower()
            
            # Extract price number if present
            price = None
            if not is_free and price_text:
                import re
                price_match = re.search(r'[\d,]+', price_text.replace('.', ''))
                if price_match:
                    try:
                        price = float(price_match.group().replace(',', '.'))
                    except:
                        pass
            
            # Build event URL
            event_url = event_data.get('eventUrl', '')
            if event_url and not event_url.startswith('http'):
                event_url = f"https://feverup.com{event_url}"
            
            # Venue
            venue = event_data.get('venue', '') or location
            
            return {
                'title': title,
                'description': f"Experience on Fever: {title}",
                'venue_name': venue,
                'venue_address': '',
                'event_url': event_url,
                'image_url': event_data.get('imageUrl', ''),
                'category': 'Experiences',
                'is_free': is_free,
                'price': price,
                'external_id': None,
                'start_datetime': None  # Fever doesn't show dates on listing
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing Fever event: {e}")
            return None
    
    async def __del__(self):
        """Cleanup browser when scraper is destroyed"""
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass


# Test function
async def test_fever():
    """Test Fever scraper with Latin American cities"""
    from services.url_discovery_service import UrlDiscoveryService
    from services.ai_service import ai_service_singleton
    
    url_service = UrlDiscoveryService(ai_service_singleton)
    scraper = FeverScraper(url_service)
    
    cities = ['Buenos Aires', 'Mexico City', 'Sao Paulo']
    
    for city in cities:
        print(f"\n🔥 Testing Fever in {city}...")
        events = await scraper.scrape_events(city, limit=5)
        
        if events:
            print(f"✅ Found {len(events)} events:")
            for event in events[:3]:
                print(f"  - {event['title']}")
                print(f"    💰 {'Free' if event['is_free'] else f'${event.get('price', 'N/A')}'}")
        else:
            print(f"❌ No events found in {city}")
    
    await scraper.__del__()


if __name__ == "__main__":
    asyncio.run(test_fever())