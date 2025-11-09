"""🎵 BANDSINTOWN SCRAPER - Music Events Discovery"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from services.scraper_interface import BaseGlobalScraper, ScraperConfig
from services.url_discovery_service import IUrlDiscoveryService, UrlDiscoveryRequest

logger = logging.getLogger(__name__)

class BandsintownScraper(BaseGlobalScraper):
    """🎵 BANDSINTOWN SCRAPER GLOBAL - Eventos musicales"""
    
    def __init__(self, url_discovery_service: IUrlDiscoveryService, config: ScraperConfig = None):
        super().__init__(url_discovery_service, config)
        
    async def scrape_events(self, location: str, category: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """🎵 Bandsintown Scraper: Iniciando"""
        logger.info(f"🎵 Bandsintown Scraper: Iniciando para '{location}'")
        
        try:
            request = UrlDiscoveryRequest(platform="bandsintown", location=location, category=category)
            url = await self.url_discovery_service.discover_url(request)
            
            if not url:
                return []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.error(f"❌ HTTP {response.status} al acceder a {url}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Buscar elementos de eventos
                    event_elements = soup.select('.event-item, .concert-item, [data-testid*="event"]')
                    
                    if not event_elements:
                        logger.warning("⚠️ No se encontraron elementos de eventos en Bandsintown")
                        return []
                    
                    events = []
                    for element in event_elements[:limit]:
                        event_data = self._parse_event(element)
                        if event_data:
                            events.append(self._standardize_event(event_data))
                    
                    return events
                    
        except Exception as e:
            logger.error(f"❌ Error en Bandsintown Scraper: {str(e)}")
            return []
    
    def _parse_event(self, element) -> Optional[Dict[str, Any]]:
        """Parse individual event"""
        try:
            title_elem = element.select_one('h3, .artist-name, .event-title')
            title = title_elem.get_text(strip=True) if title_elem else 'Sin título'
            
            return {
                'title': title,
                'description': 'Evento musical encontrado en Bandsintown',
                'event_url': '',
                'image_url': '',
                'venue_name': 'Venue no especificado',
                'category': 'Música'
            }
        except:
            return None