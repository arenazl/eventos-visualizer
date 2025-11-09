"""
🎫 ALLEVENTS PLAYWRIGHT SCRAPER
Scraper avanzado para extraer eventos de AllEvents.in usando Playwright
6M+ usuarios globalmente, plataforma gratuita de eventos
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

class AllEventsPlaywrightScraper:
    """
    🎫 SCRAPER DE ALLEVENTS CON PLAYWRIGHT
    
    CARACTERÍSTICAS:
    - Plataforma global con 6M+ usuarios
    - Eventos gratuitos y de pago
    - Múltiples categorías: música, deportes, cultural, tech
    - Soporte para búsqueda por ciudad globalmente
    """
    
    def __init__(self):
        """Inicializar el scraper"""
        self.base_url = 'https://allevents.in'
        logger.info("🎫 AllEvents Playwright Scraper inicializado")
    
    async def search_events(self, location: str, category: str = None, max_events: int = 20) -> List[Dict[str, Any]]:
        """
        🔍 BUSCAR EVENTOS EN ALLEVENTS
        
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
            # Construir URL de búsqueda para AllEvents
            location_clean = location.lower().replace(' ', '-').replace(',', '')
            
            # URLs posibles para AllEvents
            search_urls = [
                f"{self.base_url}/{location_clean}",
                f"{self.base_url}/{location_clean}/all",
                f"{self.base_url}/events/{location_clean}",
                f"{self.base_url}/city/{location_clean}"
            ]
            
            logger.info(f"🎫 Buscando eventos en AllEvents: '{location}'")
            
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
                
                events = []
                
                # Probar diferentes URLs hasta encontrar eventos
                for search_url in search_urls:
                    try:
                        logger.info(f"🌐 Probando URL: {search_url}")
                        
                        # Navegar a la página
                        response = await page.goto(search_url, wait_until='networkidle', timeout=15000)
                        
                        if response and response.status == 200:
                            # Esperar que carguen los eventos
                            await page.wait_for_timeout(3000)
                            
                            # Extraer eventos de esta URL
                            page_events = await self._extract_events_from_page(page, max_events)
                            
                            if page_events:
                                events.extend(page_events)
                                logger.info(f"✅ AllEvents: {len(page_events)} eventos desde {search_url}")
                                break
                                
                    except Exception as e:
                        logger.warning(f"⚠️ Error probando {search_url}: {e}")
                        continue
                
                await browser.close()
                
                # Eliminar duplicados por título
                unique_events = []
                seen_titles = set()
                for event in events[:max_events]:
                    title = event.get('title', '').lower()
                    if title and title not in seen_titles:
                        unique_events.append(event)
                        seen_titles.add(title)
                
                logger.info(f"✅ AllEvents: {len(unique_events)} eventos únicos extraídos")
                return unique_events
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de AllEvents: {e}")
            return []
    
    async def _extract_events_from_page(self, page, max_events: int) -> List[Dict[str, Any]]:
        """
        📊 EXTRAER EVENTOS DE LA PÁGINA DE ALLEVENTS
        
        Args:
            page: Página de Playwright
            max_events: Máximo número de eventos
            
        Returns:
            Lista de eventos extraídos
        """
        
        try:
            # Esperar a que aparezcan los eventos
            await page.wait_for_selector('.event-style-top .item, .item-event, .event-card, article, .event-item', timeout=10000)
            
            # Selectores posibles para eventos en AllEvents
            event_selectors = [
                '.event-style-top .item',  # Selector principal según CSS
                '.item-event',
                '.event-card',
                'article',
                '.event-item',
                '.featured-section .item',
                '[data-event]',
                '.event-list-item'
            ]
            
            events = []
            
            for selector in event_selectors:
                event_elements = await page.query_selector_all(selector)
                if event_elements:
                    logger.info(f"🎯 AllEvents: Encontrados {len(event_elements)} elementos con selector: {selector}")
                    
                    for i, element in enumerate(event_elements[:max_events]):
                        try:
                            event_data = await self._extract_single_event(element)
                            if event_data:
                                events.append(event_data)
                                if len(events) >= max_events:
                                    break
                        except Exception as e:
                            logger.warning(f"⚠️ Error extrayendo evento AllEvents {i}: {e}")
                    
                    break  # Usar el primer selector que funcione
            
            if not events:
                logger.warning("⚠️ No se encontraron eventos con los selectores conocidos")
                # Intentar extracción genérica
                events = await self._generic_event_extraction(page, max_events)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos de AllEvents: {e}")
            return []
    
    async def _extract_single_event(self, element) -> Optional[Dict[str, Any]]:
        """
        🎫 EXTRAER DATOS DE UN EVENTO INDIVIDUAL DE ALLEVENTS
        
        Args:
            element: Elemento HTML del evento
            
        Returns:
            Datos del evento o None si falla
        """
        
        try:
            # Extraer título (según CSS: .title_new)
            title_selectors = [
                '.title_new',  # Selector específico de AllEvents
                '.event-title',
                'h1, h2, h3, h4, h5', 
                '.title', 
                '.event-name',
                'a[title]',
                'a'
            ]
            title = await self._get_text_from_selectors(element, title_selectors)
            
            # También intentar obtener título desde atributo title de enlaces
            if not title:
                link_elem = await element.query_selector('a[title]')
                if link_elem:
                    title = await link_elem.get_attribute('title')
            
            # Extraer fecha
            date_selectors = [
                '.date', 
                '.event-date',
                '.datetime', 
                'time',
                '[data-date]',
                '.when',
                '.event-time'
            ]
            date = await self._get_text_from_selectors(element, date_selectors)
            
            # Extraer venue/lugar
            venue_selectors = [
                '.venue', 
                '.location', 
                '.place',
                '.where',
                '.event-venue',
                '.address',
                '.event-location'
            ]
            venue = await self._get_text_from_selectors(element, venue_selectors)
            
            # Extraer precio
            price_selectors = [
                '.price', 
                '.cost', 
                '.ticket-price',
                '[data-price]',
                '.amount',
                '.fee'
            ]
            price = await self._get_text_from_selectors(element, price_selectors)
            
            # Extraer URL del evento
            link_element = await element.query_selector('a')
            event_url = ''
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        event_url = f"https://allevents.in{href}"
                    elif href.startswith('http'):
                        event_url = href
            
            # Extraer imagen (según CSS: .banner-image)
            img_selectors = [
                '.banner-image img',  # Selector específico AllEvents
                '.event-image img',
                'img'
            ]
            image_url = ''
            for img_sel in img_selectors:
                img_element = await element.query_selector(img_sel)
                if img_element:
                    src = await img_element.get_attribute('src') or await img_element.get_attribute('data-src')
                    if src:
                        if src.startswith('/'):
                            image_url = f"https://allevents.in{src}"
                        elif src.startswith('http'):
                            image_url = src
                        break
            
            # Verificar si es evento válido
            if title and title.strip() and len(title.strip()) > 3:
                # Limpiar título
                title_clean = title.strip()
                if len(title_clean) > 200:  # Truncar títulos muy largos
                    title_clean = title_clean[:200] + "..."
                
                event = {
                    'title': title_clean,
                    'date': date.strip() if date else '',
                    'venue': venue.strip() if venue else '',
                    'price': price.strip() if price else '',
                    'url': event_url,
                    'image_url': image_url,
                    'source': 'allevents',
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                logger.debug(f"🎫 Evento AllEvents extraído: {event['title'][:50]}...")
                return event
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo evento individual de AllEvents: {e}")
        
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
        🔍 EXTRACCIÓN GENÉRICA COMO FALLBACK PARA ALLEVENTS
        
        Args:
            page: Página de Playwright
            max_events: Máximo eventos a extraer
            
        Returns:
            Lista de eventos extraídos genéricamente
        """
        
        try:
            logger.info("🔍 AllEvents: Intentando extracción genérica...")
            
            # Buscar enlaces que parezcan eventos
            links = await page.query_selector_all('a[href*="/events/"], a[href*="/event/"], a[title]')
            
            events = []
            for link in links[:max_events * 2]:  # Buscar más para filtrar
                try:
                    title = await link.text_content() or await link.get_attribute('title')
                    url = await link.get_attribute('href')
                    
                    if title and title.strip() and len(title.strip()) > 10:
                        if url and url.startswith('/'):
                            url = f"https://allevents.in{url}"
                        
                        # Filtrar títulos que parezcan eventos reales
                        title_clean = title.strip()
                        if (len(title_clean) > 10 and 
                            not title_clean.lower() in ['home', 'about', 'contact', 'login', 'register']):
                            
                            event = {
                                'title': title_clean[:200],
                                'date': '',
                                'venue': '',
                                'price': '',
                                'url': url if url else '',
                                'image_url': '',
                                'source': 'allevents_generic',
                                'scraped_at': datetime.utcnow().isoformat()
                            }
                            events.append(event)
                            
                            if len(events) >= max_events:
                                break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en extracción genérica AllEvents: {e}")
            
            logger.info(f"🔍 AllEvents: Eventos extraídos genéricamente: {len(events)}")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error en extracción genérica de AllEvents: {e}")
            return []

# Función de prueba
async def test_allevents_scraper():
    """
    🧪 FUNCIÓN DE PRUEBA DEL SCRAPER DE ALLEVENTS
    """
    
    print("🎫 PROBANDO ALLEVENTS PLAYWRIGHT SCRAPER")
    print("=" * 50)
    
    scraper = AllEventsPlaywrightScraper()
    
    # Probar búsqueda
    events = await scraper.search_events("Barcelona", max_events=5)
    
    print(f"\n✅ Eventos encontrados en AllEvents: {len(events)}")
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Fecha: {event['date']}")
        print(f"   Venue: {event['venue']}")
        print(f"   Precio: {event['price']}")
        print(f"   URL: {event['url'][:70]}..." if event['url'] else "   URL: N/A")

if __name__ == "__main__":
    # Ejecutar prueba
    asyncio.run(test_allevents_scraper())