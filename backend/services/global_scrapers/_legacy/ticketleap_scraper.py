"""
🎪 TICKETLEAP SCRAPER - Plataforma Gratuita de Tickets
Scraper para extraer eventos de TicketLeap.com usando Playwright
Plataforma gratuita para organizadores de eventos
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

class TicketLeapScraper:
    """
    🎪 SCRAPER DE TICKETLEAP CON PLAYWRIGHT
    
    CARACTERÍSTICAS:
    - Plataforma gratuita para organizadores
    - Eventos diversos: conferencias, workshops, música
    - Sin comisiones ocultas
    - Fácil gestión de eventos
    """
    
    def __init__(self):
        """Inicializar el scraper"""
        self.base_url = 'https://www.ticketleap.com'
        logger.info("🎪 TicketLeap Scraper inicializado")
    
    async def search_events(self, location: str, category: str = None, max_events: int = 20) -> List[Dict[str, Any]]:
        """
        🔍 BUSCAR EVENTOS EN TICKETLEAP
        
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
            # URLs posibles para TicketLeap
            search_urls = [
                f"{self.base_url}/search?q={quote(location)}",
                f"{self.base_url}/events?location={quote(location)}",
                f"{self.base_url}/find-events?city={quote(location)}"
            ]
            
            logger.info(f"🎪 Buscando en TicketLeap: '{location}'")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                page = await browser.new_page()
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                events = []
                
                # Probar diferentes URLs
                for url in search_urls:
                    try:
                        logger.info(f"🔗 Probando: {url}")
                        
                        await page.goto(url, wait_until='networkidle', timeout=15000)
                        await page.wait_for_timeout(3000)
                        
                        page_events = await self._extract_events_from_page(page, max_events)
                        
                        if page_events:
                            events.extend(page_events)
                            logger.info(f"✅ TicketLeap: {len(page_events)} eventos desde {url}")
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error con {url}: {e}")
                        continue
                
                await browser.close()
                
                # Eliminar duplicados
                unique_events = []
                seen = set()
                for event in events[:max_events]:
                    title_key = event.get('title', '').lower()
                    if title_key and title_key not in seen:
                        unique_events.append(event)
                        seen.add(title_key)
                
                logger.info(f"✅ TicketLeap: {len(unique_events)} eventos únicos")
                return unique_events
                
        except Exception as e:
            logger.error(f"❌ Error en TicketLeap scraper: {e}")
            return []
    
    async def _extract_events_from_page(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        📊 EXTRAER EVENTOS DE TICKETLEAP
        """
        
        try:
            # Selectores para TicketLeap
            await page.wait_for_selector('.event, .event-item, .ticket-item, [data-event]', timeout=10000)
            
            event_selectors = [
                '.event',
                '.event-item', 
                '.ticket-item',
                '[data-event]',
                '.event-card',
                'article',
                '.search-result'
            ]
            
            events = []
            
            for selector in event_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"🎯 TicketLeap: {len(elements)} elementos con {selector}")
                    
                    for element in elements[:max_events]:
                        try:
                            event_data = await self._extract_single_event(element)
                            if event_data:
                                events.append(event_data)
                                if len(events) >= max_events:
                                    break
                        except Exception:
                            continue
                    break
            
            if not events:
                # Fallback genérico
                events = await self._generic_extraction(page, max_events)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo de TicketLeap: {e}")
            return []
    
    async def _extract_single_event(self, element) -> Optional[Dict[str, Any]]:
        """
        🎪 EXTRAER EVENTO INDIVIDUAL DE TICKETLEAP
        """
        
        try:
            # Título
            title_selectors = ['h1, h2, h3, h4', '.event-title', '.title', '.name', 'a']
            title = await self._get_text_from_selectors(element, title_selectors)
            
            # Fecha
            date_selectors = ['.date', '.event-date', '.datetime', 'time', '[data-date]']
            date = await self._get_text_from_selectors(element, date_selectors)
            
            # Venue
            venue_selectors = ['.venue', '.location', '.place', '.event-venue']
            venue = await self._get_text_from_selectors(element, venue_selectors)
            
            # Precio
            price_selectors = ['.price', '.cost', '.ticket-price', '[data-price]']
            price = await self._get_text_from_selectors(element, price_selectors)
            
            # URL
            link = await element.query_selector('a')
            event_url = ''
            if link:
                href = await link.get_attribute('href')
                if href:
                    event_url = href if href.startswith('http') else f"https://www.ticketleap.com{href}"
            
            if title and len(title.strip()) > 3:
                return {
                    'title': title.strip(),
                    'date': date.strip() if date else '',
                    'venue': venue.strip() if venue else '',
                    'price': price.strip() if price else '',
                    'url': event_url,
                    'source': 'ticketleap',
                    'scraped_at': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo evento TicketLeap: {e}")
        
        return None
    
    async def _generic_extraction(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        🔍 EXTRACCIÓN GENÉRICA PARA TICKETLEAP
        """
        
        try:
            logger.info("🔍 TicketLeap: Extracción genérica...")
            
            links = await page.query_selector_all('a[href*="/events/"], a[title]')
            
            events = []
            for link in links[:max_events * 2]:
                try:
                    title = await link.text_content() or await link.get_attribute('title')
                    url = await link.get_attribute('href')
                    
                    if title and len(title.strip()) > 10:
                        if url and url.startswith('/'):
                            url = f"https://www.ticketleap.com{url}"
                        
                        title_clean = title.strip()
                        if len(title_clean) > 10:
                            events.append({
                                'title': title_clean,
                                'date': '',
                                'venue': '',
                                'price': '',
                                'url': url or '',
                                'source': 'ticketleap_generic',
                                'scraped_at': datetime.now().isoformat()
                            })
                            
                            if len(events) >= max_events:
                                break
                                
                except Exception:
                    continue
            
            logger.info(f"🔍 TicketLeap genérico: {len(events)} eventos")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extracción genérica TicketLeap: {e}")
            return []
    
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
async def test_ticketleap():
    scraper = TicketLeapScraper()
    events = await scraper.search_events("New York", max_events=3)
    
    print(f"🎪 TICKETLEAP - {len(events)} eventos:")
    for i, event in enumerate(events, 1):
        print(f"{i}. {event['title']}")
        print(f"   📅 {event['date']}")
        print(f"   💰 {event['price']}")

if __name__ == "__main__":
    asyncio.run(test_ticketleap())