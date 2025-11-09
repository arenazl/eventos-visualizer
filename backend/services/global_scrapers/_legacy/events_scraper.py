"""
🎪 EVENTS.COM SCRAPER - Global Event Discovery  
Scraper global para Events.com con inyección de dependencias
"""

import asyncio
import aiohttp
import logging
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

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

class EventsScraper(BaseGlobalScraper):
    """
    🎪 EVENTS.COM SCRAPER GLOBAL
    
    CARACTERÍSTICAS:
    - Funciona en cualquier ubicación mundial
    - Especializado en eventos generales y conferencias
    - Parsing optimizado para estructura HTML de Events.com
    - Manejo de eventos corporativos y educativos
    """
    
    def __init__(self, url_discovery_service: IUrlDiscoveryService, config: ScraperConfig = None):
        """
        Constructor con DEPENDENCY INJECTION
        
        Args:
            url_discovery_service: Servicio inyectado para descubrir URLs de Events.com
            config: Configuración específica del scraper
        """
        super().__init__(url_discovery_service, config)
        
        # Headers HTTP optimizados para Events.com
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🎯 SCRAPING PRINCIPAL DE EVENTS.COM
        
        Proceso:
        1. Descubrir URL con IA
        2. Scrapear eventos principales
        3. Parsing y estandarización
        """
        
        logger.info(f"🎪 Events.com Scraper: Iniciando para '{location}'")
        
        try:
            # 1. Descubrir URL con IA
            request = UrlDiscoveryRequest(
                platform="events",
                location=location,
                category=category
            )
            
            url = await self.url_discovery_service.discover_url(request)
            if not url:
                logger.warning("⚠️ No se pudo generar URL para Events.com")
                return []
            
            # 2. Scrapear URL principal
            events = await self._scrape_events_page(url, limit, location)
            
            logger.info(f"✅ Events.com: {len(events)} eventos parseados")
            return events[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error en Events.com Scraper: {str(e)}")
            return []
    
    async def _scrape_events_page(self, url: str, limit: int, location: str) -> List[Dict[str, Any]]:
        """
        🌐 SCRAPING DE PÁGINA ESPECÍFICA DE EVENTS.COM
        
        Args:
            url: URL a scrapear
            limit: Límite de eventos
            
        Returns:
            Lista de eventos parseados
        """
        
        try:
            # ⏱️ TIMING: Inicio del HTTP request
            http_start = time.time()
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.error(f"❌ HTTP {response.status} al acceder a {url}")
                        return []
                    
                    html = await response.text()
                    
                    # ⏱️ TIMING: HTTP request completado
                    http_end = time.time()
                    http_duration = http_end - http_start
                    logger.info(f"⏱️ EVENTS.COM HTTP REQUEST: {http_duration:.2f}s")
                    
                    # ⏱️ TIMING: Inicio del parsing
                    parse_start = time.time()
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Selector principal para eventos de Events.com (que usa Eventbrite)
                    event_cards = soup.select('.event-card')
                    
                    if not event_cards:
                        logger.warning("⚠️ No se encontraron elementos de eventos en Events.com")
                        return []
                    
                    logger.info(f"🎯 Events.com: Encontrados {len(event_cards)} eventos con '.event-card'")
                    
                    events = []
                    valid_events = 0
                    
                    for card in event_cards:
                        if valid_events >= limit:
                            break
                            
                        event_data = self._parse_events_event(card, location)
                        if event_data:
                            events.append(self._standardize_event(event_data))
                            valid_events += 1
                    
                    # ⏱️ TIMING: Parsing completado
                    parse_end = time.time()
                    parse_duration = parse_end - parse_start
                    total_duration = parse_end - http_start
                    
                    logger.info(f"⏱️ EVENTS.COM PARSING: {parse_duration:.2f}s")
                    logger.info(f"⏱️ EVENTS.COM TOTAL: {total_duration:.2f}s (HTTP: {http_duration:.2f}s + Parse: {parse_duration:.2f}s)")
                    logger.info(f"📝 Events.com: {valid_events} eventos válidos extraídos usando '.event-card'")
                    
                    return events
                    
        except Exception as e:
            logger.error(f"❌ Error scrapeando {url}: {str(e)}")
            return []
    
    def _parse_events_event(self, event_element, location: str) -> Optional[Dict[str, Any]]:
        """
        📋 PARSING DE EVENTO INDIVIDUAL DE EVENTS.COM
        
        Extrae información estructurada de un elemento de evento
        """
        
        try:
            # URL del evento (buscar en enlaces internos)
            link_elem = event_element.select_one('a[href*="eventbrite"]')
            event_url = link_elem.get('href', '') if link_elem else ''
            
            # Título
            title_elem = event_element.select_one('.event-card-title, h3, .card-text--truncated__one')
            title = title_elem.get_text(strip=True) if title_elem else 'Sin título'
            
            # Imagen
            img_elem = event_element.select_one('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Venue/ubicación - buscar en varios posibles selectores
            venue_elem = (
                event_element.select_one('.event-card-venue') or
                event_element.select_one('.card-text--truncated__two') or
                event_element.select_one('.venue-name')
            )
            if venue_elem:
                venue_name = venue_elem.get_text(strip=True)
            else:
                # Usar la ciudad como ubicación por defecto
                venue_name = f"{location}"
            
            # Fecha/hora
            datetime_elem = event_element.select_one('.event-card-date, .event-date')
            start_datetime = datetime_elem.get_text(strip=True) if datetime_elem else None
            
            # Precio
            price_elem = event_element.select_one('.event-card-price, .price')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            
            is_free = False
            if price_text and ('gratis' in price_text.lower() or 'free' in price_text.lower()):
                is_free = True
            
            # Solo retornar eventos que tengan al menos título
            if not title or title == 'Sin título':
                return None
            
            return {
                'title': title,
                'description': 'Evento encontrado en Events.com',
                'event_url': event_url,
                'image_url': image_url,
                'venue_name': venue_name,
                'venue_address': None,
                'start_datetime': start_datetime,
                'price': None,
                'is_free': is_free,
                'category': 'Eventos Generales',
                'external_id': None
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parseando evento de Events.com: {str(e)}")
            return None