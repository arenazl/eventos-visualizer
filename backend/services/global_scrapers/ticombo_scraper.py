"""
🎪 TICOMBO PLAYWRIGHT SCRAPER
Scraper avanzado para extraer eventos de Ticombo.com usando Playwright
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

class TicomboPlaywrightScraper:
    """
    🎪 SCRAPER DE TICOMBO CON PLAYWRIGHT
    
    CARACTERÍSTICAS:
    - Búsqueda en plataforma global de eventos culturales
    - Manejo de contenido dinámico con JavaScript
    - Extracción de datos completos de eventos
    - Soporte para múltiples ciudades globalmente
    """
    
    def __init__(self):
        """Inicializar el scraper"""
        self.base_url = 'https://www.ticombo.com'
        logger.info("🎪 Ticombo Playwright Scraper inicializado")
    
    async def search_events(self, location: str, category: str = None, max_events: int = 20) -> List[Dict[str, Any]]:
        """
        🔍 BUSCAR EVENTOS EN TICOMBO
        
        Args:
            location: Ciudad a buscar
            category: Categoría de eventos (opcional)
            max_events: Máximo número de eventos a extraer
            
        Returns:
            Lista de eventos encontrados
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("❌ Playwright no está disponible")
            return []
        
        try:
            # Construir URL de búsqueda
            search_query = quote(location)
            search_url = f"{self.base_url}/en/discover/search?q={search_query}"
            
            logger.info(f"🎪 Buscando eventos en Ticombo: '{location}'")
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
                
                # Configurar user agent
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                # Navegar a la página de búsqueda
                logger.info("🌐 Navegando a Ticombo...")
                await page.goto(search_url, wait_until='networkidle')
                
                # Esperar que carguen los resultados
                await page.wait_for_timeout(5000)
                
                # Extraer eventos de los resultados
                events = await self._extract_events_from_page(page, max_events)
                
                await browser.close()
                
                logger.info(f"✅ Eventos extraídos de Ticombo: {len(events)}")
                return events
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de Ticombo: {e}")
            return []
    
    async def _extract_events_from_page(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        📊 EXTRAER EVENTOS DE LA PÁGINA DE RESULTADOS DE TICOMBO
        
        Args:
            page: Página de Playwright
            max_events: Máximo número de eventos
            
        Returns:
            Lista de eventos extraídos
        """
        
        try:
            # Esperar a que aparezcan los resultados de eventos
            await page.wait_for_selector('article, .event-card, .search-result, [data-event]', timeout=10000)
            
            # Selectores posibles para eventos en Ticombo
            event_selectors = [
                'article',
                '.event-card', 
                '.search-result',
                '.result-item',
                '[data-event]',
                '.card',
                '.event-item'
            ]
            
            events = []
            
            for selector in event_selectors:
                event_elements = await page.query_selector_all(selector)
                if event_elements:
                    logger.info(f"🎯 Ticombo: Encontrados {len(event_elements)} elementos con selector: {selector}")
                    
                    for i, element in enumerate(event_elements[:max_events]):
                        try:
                            event_data = await self._extract_single_event(element)
                            if event_data:
                                events.append(event_data)
                                if len(events) >= max_events:
                                    break
                        except Exception as e:
                            logger.warning(f"⚠️ Error extrayendo evento {i}: {e}")
                    
                    break  # Usar el primer selector que funcione
            
            if not events:
                logger.warning("⚠️ No se encontraron eventos con los selectores conocidos")
                # Intentar extracción genérica
                events = await self._generic_event_extraction(page, max_events)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos de Ticombo: {e}")
            return []
    
    async def _extract_single_event(self, element) -> Optional[Dict[str, Any]]:
        """
        🎫 EXTRAER DATOS DE UN EVENTO INDIVIDUAL DE TICOMBO
        
        Args:
            element: Elemento HTML del evento
            
        Returns:
            Datos del evento o None si falla
        """
        
        try:
            # Extraer título
            title_selectors = [
                'h1, h2, h3, h4, h5', 
                '.title', 
                '.event-title',
                '.event-name',
                '[data-title]',
                'a'
            ]
            title = await self._get_text_from_selectors(element, title_selectors)
            
            # Extraer fecha
            date_selectors = [
                '.date', 
                '.datetime', 
                '.event-date',
                'time',
                '[data-date]',
                '.when'
            ]
            date = await self._get_text_from_selectors(element, date_selectors)
            
            # Extraer venue/lugar
            venue_selectors = [
                '.venue', 
                '.location', 
                '.place',
                '.where',
                '.event-venue',
                '.address'
            ]
            venue = await self._get_text_from_selectors(element, venue_selectors)
            
            # Extraer precio
            price_selectors = [
                '.price', 
                '.cost', 
                '.ticket-price',
                '[data-price]',
                '.amount'
            ]
            price = await self._get_text_from_selectors(element, price_selectors)
            
            # Extraer URL del evento
            link_element = await element.query_selector('a')
            event_url = ''
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        event_url = f"https://www.ticombo.com{href}"
                    elif href.startswith('http'):
                        event_url = href
            
            # Extraer imagen
            img_element = await element.query_selector('img')
            image_url = ''
            if img_element:
                src = await img_element.get_attribute('src') or await img_element.get_attribute('data-src')
                if src:
                    if src.startswith('/'):
                        image_url = f"https://www.ticombo.com{src}"
                    elif src.startswith('http'):
                        image_url = src
            
            # Si encontramos al menos título, es un evento válido
            if title and title.strip() and len(title.strip()) > 3:
                event = {
                    'title': title.strip(),
                    'date': date.strip() if date else '',
                    'venue': venue.strip() if venue else '',
                    'price': price.strip() if price else '',
                    'url': event_url,
                    'image_url': image_url,
                    'source': 'ticombo',
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                logger.debug(f"🎫 Evento Ticombo extraído: {event['title']}")
                return event
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo evento individual de Ticombo: {e}")
        
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
        🔍 EXTRACCIÓN GENÉRICA COMO FALLBACK PARA TICOMBO
        
        Args:
            page: Página de Playwright
            max_events: Máximo eventos a extraer
            
        Returns:
            Lista de eventos extraídos genéricamente
        """
        
        try:
            logger.info("🔍 Ticombo: Intentando extracción genérica...")
            
            # Buscar todos los enlaces que parezcan eventos
            links = await page.query_selector_all('a[href*="/event"], a[href*="/discover"]')
            
            events = []
            for link in links[:max_events]:
                try:
                    title = await link.text_content()
                    url = await link.get_attribute('href')
                    
                    if title and title.strip() and len(title.strip()) > 5:
                        if url and url.startswith('/'):
                            url = f"https://www.ticombo.com{url}"
                        
                        event = {
                            'title': title.strip(),
                            'date': '',
                            'venue': '',
                            'price': '',
                            'url': url if url else '',
                            'image_url': '',
                            'source': 'ticombo_generic',
                            'scraped_at': datetime.utcnow().isoformat()
                        }
                        events.append(event)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en extracción genérica de Ticombo: {e}")
            
            logger.info(f"🔍 Ticombo: Eventos extraídos genéricamente: {len(events)}")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error en extracción genérica de Ticombo: {e}")
            return []

# Función de prueba
async def test_ticombo_scraper():
    """
    🧪 FUNCIÓN DE PRUEBA DEL SCRAPER DE TICOMBO
    """
    
    print("🎪 PROBANDO TICOMBO PLAYWRIGHT SCRAPER")
    print("=" * 50)
    
    scraper = TicomboPlaywrightScraper()
    
    # Probar búsqueda
    events = await scraper.search_events("Barcelona", max_events=5)
    
    print(f"\n✅ Eventos encontrados en Ticombo: {len(events)}")
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Fecha: {event['date']}")
        print(f"   Venue: {event['venue']}")
        print(f"   Precio: {event['price']}")
        print(f"   URL: {event['url'][:70]}..." if event['url'] else "   URL: N/A")

if __name__ == "__main__":
    # Ejecutar prueba
    asyncio.run(test_ticombo_scraper())