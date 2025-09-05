"""
🤝 MEETUP SCRAPER - Using Playwright to bypass Cloudflare
Scraper global para Meetup usando Playwright para obtener eventos reales
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Imports de interfaces y servicios
from services.scraper_interface import (
    BaseGlobalScraper, 
    ScraperRequest, 
    ScraperResult,
    ScraperConfig
)
from services.url_discovery_service import (
    IUrlDiscoveryService,
    UrlDiscoveryRequest
)

logger = logging.getLogger(__name__)

class MeetupScraper(BaseGlobalScraper):
    """
    🤝 MEETUP SCRAPER GLOBAL WITH PLAYWRIGHT
    
    CARACTERÍSTICAS:
    - Usa Playwright para bypass Cloudflare
    - Extrae eventos del Apollo State en __NEXT_DATA__
    - Funciona en cualquier ubicación mundial
    - Obtiene eventos reales, no mockups
    """
    
    # 🎯 HABILITADO POR DEFECTO - SCRAPER PRINCIPAL
    enabled_by_default: bool = True
    nearby_cities: bool = True  # Soporta búsqueda de ciudades cercanas por IA
    priority: int = 3  # Slower - Playwright required ~4500ms
    
    def __init__(self, url_discovery_service: IUrlDiscoveryService, config: ScraperConfig = None):
        """
        Constructor con DEPENDENCY INJECTION
        
        Args:
            url_discovery_service: Servicio inyectado para descubrir URLs de Meetup
            config: Configuración específica del scraper
        """
        super().__init__(url_discovery_service, config)
        self.browser = None
        self.playwright = None
        
    async def initialize_playwright(self):
        """Initialize Playwright browser if not already initialized"""
        if not self.browser:
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
        return True
        
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🎯 SCRAPING PRINCIPAL DE MEETUP CON PLAYWRIGHT
        
        Proceso:
        1. Inicializar Playwright si es necesario
        2. Navegar a la URL de Meetup
        3. Extraer JSON de __NEXT_DATA__
        4. Parsear eventos del Apollo State
        """
        
        logger.info(f"🤝 Meetup Scraper (Playwright): Iniciando para '{location}'")
        
        # Initialize Playwright if needed
        if not await self.initialize_playwright():
            logger.error("❌ Could not initialize Playwright for Meetup")
            return []
        
        try:
            # Create context and page
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # Build URL
            url = f"https://www.meetup.com/find/?location={location}&source=EVENTS"
            logger.info(f"🎭 Navigating to Meetup: {url}")
            
            # Navigate with OPTIMIZED timeout for speed (5s max navigation)
            await page.goto(url, wait_until='domcontentloaded', timeout=5000)
            
            # Wait for __NEXT_DATA__ to be present (3s max)
            try:
                await page.wait_for_selector('#__NEXT_DATA__', timeout=3000)
            except:
                logger.warning("⚠️ __NEXT_DATA__ selector not found, trying to proceed anyway")
            
            # Minimal delay to ensure content loads (500ms only)
            await page.wait_for_timeout(500)
            
            # Extract __NEXT_DATA__ JSON
            json_data = await page.evaluate('''
                () => {
                    const scriptTag = document.getElementById('__NEXT_DATA__');
                    if (scriptTag) {
                        try {
                            return JSON.parse(scriptTag.textContent);
                        } catch (e) {
                            return null;
                        }
                    }
                    return null;
                }
            ''')
            
            # Close page and context
            await page.close()
            await context.close()
            
            if not json_data:
                logger.warning("⚠️ No __NEXT_DATA__ found on Meetup page")
                return []
            
            # Extract events from Apollo State
            events = self._extract_events_from_apollo(json_data, location, limit)
            logger.info(f"✅ Meetup (Playwright): {len(events)} eventos extraídos")
            
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
            
            logger.info(f"🎯 Apollo State found with {len(apollo_state)} objects")
            
            events = []
            
            # Extract events from Apollo State
            for key, value in apollo_state.items():
                if key.startswith('Event:') and isinstance(value, dict):
                    if 'title' in value:  # Valid event
                        event = self._parse_apollo_event(value, location)
                        if event:
                            # Apply standardization
                            standardized = self._standardize_event(event)
                            events.append(standardized)
                            if len(events) >= limit:
                                break
            
            logger.info(f"✅ {len(events)} events extracted from Apollo State")
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
            logger.info(f"📝 DEBUG event: title='{title}' url='{event_url}'")
            
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
                logger.info(f"🏢 DEBUG venue: name='{venue.get('name')}' → venue_name='{venue_name}' (location='{location}')")
            else:
                venue_name = location
                venue_address = ''
                logger.info(f"🏢 DEBUG venue: No venue dict → venue_name='{venue_name}' (location='{location}')")
            
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
            
            # Build event URL
            if event_url and not event_url.startswith('http'):
                event_url = f"https://www.meetup.com{event_url}"
            
            return {
                'title': title,
                'description': description[:500] if description else f"Meetup event in {location}",
                'start_datetime': formatted_date,
                'venue_name': venue_name,
                'venue_address': venue_address,
                'event_url': event_url,
                'image_url': image_url,
                'category': 'Community Events',
                'is_free': is_free,
                'price': price,
                'external_id': event_data.get('id')
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing Apollo event: {e}")
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