"""
🎪 TICKETMASTER PLAYWRIGHT SCRAPER
Scraper avanzado para extraer eventos de Ticketmaster usando Playwright
"""

import asyncio
import json
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

class TicketmasterPlaywrightScraper:
    """
    🎪 SCRAPER DE TICKETMASTER CON PLAYWRIGHT
    
    CARACTERÍSTICAS:
    - Búsqueda por query (ciudad, artista, evento)
    - Manejo de contenido dinámico con JavaScript
    - Extracción de datos completos de eventos
    - Soporte para diferentes dominios por país
    """
    
    def __init__(self):
        """Inicializar el scraper"""
        self.base_urls = {
            'usa': 'https://www.ticketmaster.com',
            'españa': 'https://www.ticketmaster.es',
            'france': 'https://www.ticketmaster.fr',
            'germany': 'https://www.ticketmaster.de',
            'mexico': 'https://www.ticketmaster.com.mx',
            'canada': 'https://www.ticketmaster.ca',
            'uk': 'https://www.ticketmaster.co.uk',
            'australia': 'https://www.ticketmaster.com.au'
        }
        logger.info("🎪 Ticketmaster Playwright Scraper inicializado")
    
    async def search_events(self, query: str, country: str = 'usa', max_events: int = 20) -> List[Dict[str, Any]]:
        """
        🔍 BUSCAR EVENTOS EN TICKETMASTER
        
        Args:
            query: Término de búsqueda (ciudad, artista, evento)
            country: País del dominio de Ticketmaster
            max_events: Máximo número de eventos a extraer
            
        Returns:
            Lista de eventos encontrados
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("❌ Playwright no está disponible")
            return []
        
        try:
            base_url = self.base_urls.get(country.lower(), self.base_urls['usa'])
            search_url = f"{base_url}/search"
            
            logger.info(f"🎪 Buscando eventos: '{query}' en {country}")
            logger.info(f"🔗 URL: {search_url}")
            
            async with async_playwright() as p:
                # Configurar navegador
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
                
                # Crear página
                page = await browser.new_page()
                
                # Configurar user agent para evitar detección
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                # Navegar a la página de búsqueda
                logger.info("🌐 Navegando a Ticketmaster...")
                await page.goto(search_url, wait_until='networkidle')
                
                # Esperar que cargue la página
                await page.wait_for_timeout(3000)
                
                # Buscar el campo de búsqueda con los selectores correctos encontrados
                search_input = await page.query_selector('input[name="q"]')
                if not search_input:
                    # Buscar selectores alternativos
                    search_input = await page.query_selector('input[placeholder*="Artist" i]')
                    if not search_input:
                        search_input = await page.query_selector('input[placeholder*="Event" i]')
                
                if search_input:
                    logger.info(f"✍️ Escribiendo query: '{query}'")
                    await search_input.fill(query)
                    await page.keyboard.press('Enter')
                    
                    # Esperar a que carguen los resultados
                    await page.wait_for_timeout(5000)
                else:
                    logger.warning("⚠️ No se encontró el campo de búsqueda")
                    await browser.close()
                    return []
                
                # Extraer eventos de los resultados
                events = await self._extract_events_from_page(page, max_events)
                
                await browser.close()
                
                logger.info(f"✅ Eventos extraídos: {len(events)}")
                return events
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de Ticketmaster: {e}")
            return []
    
    async def _extract_events_from_page(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        📊 EXTRAER EVENTOS DE LA PÁGINA DE RESULTADOS
        
        Args:
            page: Página de Playwright
            max_events: Máximo número de eventos
            
        Returns:
            Lista de eventos extraídos
        """
        
        try:
            # Esperar a que aparezcan los resultados
            await page.wait_for_selector('[data-testid*="event"], .event-tile, .search-result-item', timeout=10000)
            
            # Selectores posibles para eventos
            event_selectors = [
                '[data-testid*="event"]',
                '.event-tile',
                '.search-result-item',
                '.event-card',
                '[class*="event"]'
            ]
            
            events = []
            
            for selector in event_selectors:
                event_elements = await page.query_selector_all(selector)
                if event_elements:
                    logger.info(f"🎯 Encontrados {len(event_elements)} elementos con selector: {selector}")
                    
                    for i, element in enumerate(event_elements[:max_events]):
                        try:
                            event_data = await self._extract_single_event(element)
                            if event_data:
                                events.append(event_data)
                        except Exception as e:
                            logger.warning(f"⚠️ Error extrayendo evento {i}: {e}")
                    
                    break  # Usar el primer selector que funcione
            
            if not events:
                logger.warning("⚠️ No se encontraron eventos con los selectores conocidos")
                # Intentar extracción genérica
                events = await self._generic_event_extraction(page, max_events)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos: {e}")
            return []
    
    async def _extract_single_event(self, element) -> Optional[Dict[str, Any]]:
        """
        🎫 EXTRAER DATOS DE UN EVENTO INDIVIDUAL
        
        Args:
            element: Elemento HTML del evento
            
        Returns:
            Datos del evento o None si falla
        """
        
        try:
            # Extraer título
            title_selectors = ['h3', 'h2', '.event-name', '[data-testid*="name"]', 'a']
            title = await self._get_text_from_selectors(element, title_selectors)
            
            # Extraer fecha
            date_selectors = ['.date', '[data-testid*="date"]', '.event-date', 'time']
            date = await self._get_text_from_selectors(element, date_selectors)
            
            # Extraer venue/lugar
            venue_selectors = ['.venue', '[data-testid*="venue"]', '.location', '.event-venue']
            venue = await self._get_text_from_selectors(element, venue_selectors)
            
            # Extraer precio
            price_selectors = ['.price', '[data-testid*="price"]', '.event-price', '.cost']
            price = await self._get_text_from_selectors(element, price_selectors)
            
            # Extraer URL del evento
            link_element = await element.query_selector('a')
            event_url = await link_element.get_attribute('href') if link_element else None
            
            # Si encontramos al menos título, es un evento válido
            if title and title.strip():
                event = {
                    'title': title.strip(),
                    'date': date.strip() if date else '',
                    'venue': venue.strip() if venue else '',
                    'price': price.strip() if price else '',
                    'url': event_url if event_url else '',
                    'source': 'ticketmaster',
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                logger.debug(f"🎫 Evento extraído: {event['title']}")
                return event
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo evento individual: {e}")
        
        return None
    
    async def _get_text_from_selectors(self, element, selectors: List[str]) -> Optional[str]:
        """
        📝 OBTENER TEXTO USANDO MÚLTIPLES SELECTORES
        
        Args:
            element: Elemento padre
            selectors: Lista de selectores CSS a probar
            
        Returns:
            Texto encontrado o None
        """
        
        for selector in selectors:
            try:
                target_element = await element.query_selector(selector)
                if target_element:
                    text = await target_element.text_content()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        
        return None
    
    async def _generic_event_extraction(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        🔍 EXTRACCIÓN GENÉRICA COMO FALLBACK
        
        Args:
            page: Página de Playwright
            max_events: Máximo eventos a extraer
            
        Returns:
            Lista de eventos extraídos genéricamente
        """
        
        try:
            logger.info("🔍 Intentando extracción genérica...")
            
            # Buscar todos los enlaces que parezcan eventos
            links = await page.query_selector_all('a[href*="/event/"]')
            
            events = []
            for link in links[:max_events]:
                try:
                    title = await link.text_content()
                    url = await link.get_attribute('href')
                    
                    if title and title.strip():
                        event = {
                            'title': title.strip(),
                            'date': '',
                            'venue': '',
                            'price': '',
                            'url': url if url else '',
                            'source': 'ticketmaster_generic',
                            'scraped_at': datetime.utcnow().isoformat()
                        }
                        events.append(event)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en extracción genérica: {e}")
            
            logger.info(f"🔍 Eventos extraídos genéricamente: {len(events)}")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error en extracción genérica: {e}")
            return []
    
    async def search_by_location(self, city: str, country: str = 'usa') -> List[Dict[str, Any]]:
        """
        📍 BUSCAR EVENTOS POR UBICACIÓN
        
        Args:
            city: Ciudad a buscar
            country: País del dominio
            
        Returns:
            Lista de eventos en la ciudad
        """
        
        # Usar la ciudad como query de búsqueda
        return await self.search_events(city, country, max_events=50)
    
    def get_supported_countries(self) -> List[str]:
        """
        🌍 OBTENER PAÍSES SOPORTADOS
        
        Returns:
            Lista de países donde opera Ticketmaster
        """
        
        return list(self.base_urls.keys())

# Función de prueba
async def test_ticketmaster_scraper():
    """
    🧪 FUNCIÓN DE PRUEBA DEL SCRAPER
    """
    
    print("🎪 PROBANDO TICKETMASTER PLAYWRIGHT SCRAPER")
    print("=" * 50)
    
    scraper = TicketmasterPlaywrightScraper()
    
    # Probar búsqueda
    events = await scraper.search_events("concerts", "usa", max_events=5)
    
    print(f"\n✅ Eventos encontrados: {len(events)}")
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Fecha: {event['date']}")
        print(f"   Venue: {event['venue']}")
        print(f"   Precio: {event['price']}")
        print(f"   URL: {event['url'][:50]}..." if event['url'] else "   URL: N/A")

if __name__ == "__main__":
    # Ejecutar prueba
    asyncio.run(test_ticketmaster_scraper())