"""
🎟️ STUBHUB SCRAPER - Marketplace Global de Tickets
Scraper para extraer eventos de StubHub.com usando Playwright
Marketplace global para compra/venta de tickets de deportes, conciertos, teatro
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("⚠️ Playwright no está instalado")

class StubHubScraper:
    """
    🎟️ SCRAPER DE STUBHUB CON PLAYWRIGHT
    
    CARACTERÍSTICAS:
    - Marketplace global de tickets
    - Deportes, conciertos, teatro, Broadway
    - Compra/venta entre usuarios
    - Precios variables (mercado secundario)
    """
    
    def __init__(self):
        """Inicializar el scraper"""
        self.base_url = 'https://www.stubhub.com'
        logger.info("🎟️ StubHub Scraper inicializado")
    
    async def search_events(self, location: str, category: str = None, max_events: int = 20) -> List[Dict[str, Any]]:
        """
        🔍 BUSCAR EVENTOS EN STUBHUB
        
        Args:
            location: Ciudad a buscar
            category: Categoría (opcional)
            max_events: Máximo eventos a extraer
            
        Returns:
            Lista de eventos encontrados
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("❌ Playwright no está disponible")
            return []
        
        try:
            # Construir URL de búsqueda StubHub
            location_encoded = quote(location)
            search_url = f"{self.base_url}/find/s/?q={location_encoded}"
            
            logger.info(f"🎟️ Buscando en StubHub: '{location}'")
            logger.info(f"🔗 URL: {search_url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                page = await browser.new_page()
                
                # Configurar headers
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                # Navegar y buscar eventos
                await page.goto(search_url, wait_until='networkidle', timeout=15000)
                await page.wait_for_timeout(3000)
                
                events = await self._extract_events_from_page(page, max_events)
                
                await browser.close()
                
                logger.info(f"✅ StubHub: {len(events)} eventos extraídos")
                return events
                
        except Exception as e:
            logger.error(f"❌ Error en StubHub scraper: {e}")
            return []
    
    async def _extract_events_from_page(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        📊 EXTRAER EVENTOS DE STUBHUB
        """
        
        try:
            # Esperar elementos de eventos
            await page.wait_for_selector('.event-item, .ticket-item, [data-testid*="event"], .search-result', timeout=10000)
            
            # Selectores para StubHub
            event_selectors = [
                '.event-item',
                '.ticket-item',
                '[data-testid*="event"]',
                '.search-result',
                '.event-card',
                'article'
            ]
            
            events = []
            
            for selector in event_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"🎯 StubHub: {len(elements)} elementos con {selector}")
                    
                    for element in elements[:max_events]:
                        try:
                            event_data = await self._extract_single_event(element)
                            if event_data:
                                events.append(event_data)
                                if len(events) >= max_events:
                                    break
                        except Exception as e:
                            continue
                    break
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo de StubHub: {e}")
            return []
    
    async def _extract_single_event(self, element) -> Optional[Dict[str, Any]]:
        """
        🎟️ EXTRAER EVENTO INDIVIDUAL DE STUBHUB
        """
        
        try:
            # Título
            title_selectors = ['h1, h2, h3, h4', '.event-title', '.title', 'a']
            title = await self._get_text_from_selectors(element, title_selectors)
            
            # Fecha
            date_selectors = ['.date', '.event-date', 'time', '[data-date]']
            date = await self._get_text_from_selectors(element, date_selectors)
            
            # Venue
            venue_selectors = ['.venue', '.location', '.place']
            venue = await self._get_text_from_selectors(element, venue_selectors)
            
            # Precio
            price_selectors = ['.price', '.cost', '[data-price]']
            price = await self._get_text_from_selectors(element, price_selectors)
            
            # URL
            link = await element.query_selector('a')
            event_url = ''
            if link:
                href = await link.get_attribute('href')
                if href:
                    event_url = href if href.startswith('http') else f"https://www.stubhub.com{href}"
            
            if title and len(title.strip()) > 3:
                return {
                    'title': title.strip(),
                    'date': date.strip() if date else '',
                    'venue': venue.strip() if venue else '',
                    'price': price.strip() if price else '',
                    'url': event_url,
                    'source': 'stubhub',
                    'scraped_at': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo evento StubHub: {e}")
        
        return None
    
    async def _get_text_from_selectors(self, element, selectors: List[str]) -> Optional[str]:
        """Obtener texto usando múltiples selectores"""
        for selector in selectors:
            try:
                target = await element.query_selector(selector)
                if target:
                    text = await target.text_content()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return None

# Test function
async def test_stubhub():
    scraper = StubHubScraper()
    events = await scraper.search_events("Barcelona", max_events=3)
    
    print(f"🎟️ STUBHUB - {len(events)} eventos:")
    for i, event in enumerate(events, 1):
        print(f"{i}. {event['title']}")
        print(f"   📅 {event['date']}")
        print(f"   💰 {event['price']}")

if __name__ == "__main__":
    asyncio.run(test_stubhub())