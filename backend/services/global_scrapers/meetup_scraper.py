"""
🤝 MEETUP SCRAPER - Community Events with New Interface
Scraper global para Meetup usando URL Discovery Service y parsing específico
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

class MeetupScraper(BaseGlobalScraper):
    """
    🤝 MEETUP SCRAPER GLOBAL
    
    CARACTERÍSTICAS:
    - Funciona en cualquier ubicación mundial
    - Especializado en eventos comunitarios y networking
    - Parsing optimizado para estructura HTML de Meetup
    - Manejo de eventos gratuitos típicos de la plataforma
    """
    
    def __init__(self, url_discovery_service: IUrlDiscoveryService, config: ScraperConfig = None):
        """
        Constructor con DEPENDENCY INJECTION
        
        Args:
            url_discovery_service: Servicio inyectado para descubrir URLs de Meetup
            config: Configuración específica del scraper
        """
        super().__init__(url_discovery_service, config)
        
        # Headers HTTP optimizados para Meetup
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
        🎯 SCRAPING PRINCIPAL DE MEETUP
        
        Proceso:
        1. Usar URL hardcodeada que funciona
        2. Scrapear eventos principales
        3. Fallback inteligente si no hay eventos
        4. Parsing y estandarización
        """
        
        logger.info(f"🤝 Meetup Scraper: Iniciando para '{location}'")
        
        try:
            # 1. 🎯 GENERAR URL CON PATTERN SERVICE (DINÁMICO)
            from services.pattern_service import pattern_service
            
            detected_country = self.context.get('detected_country', '')
            detected_province = self.context.get('detected_province', '')
            
            url = pattern_service.generate_url(
                platform="meetup",
                localidad=location,
                provincia=detected_province,
                pais=detected_country
            )
            
            if not url:
                # Fallback usando patrón similar pero con datos dinámicos
                url = f"https://www.meetup.com/find/?location={location}&source=EVENTS"
                logger.info(f"🔗 Meetup: Fallback dinámico para {location}")
            else:
                logger.info(f"🎯 Meetup: URL generada con PatternService: {url}")
            
            # 2. Scrapear URL principal
            events = await self._scrape_meetup_page(url, limit, location)
            
            # 3. Si no hay eventos, intentar fallback inteligente
            if not events:
                logger.info(f"🔄 No se encontraron eventos Meetup en {location}, intentando fallback con IA...")
                events = await self._intelligent_fallback(location, category, limit)
            
            logger.info(f"✅ Meetup: {len(events)} eventos parseados")
            return events[:limit]
            
        except Exception as e:
            logger.error(f"❌ Meetup Scraper error: {str(e)}")
            return []
    
    async def _scrape_meetup_page(self, url: str, limit: int, location: str) -> List[Dict[str, Any]]:
        """
        🌐 SCRAPING DE PÁGINA ESPECÍFICA DE MEETUP
        
        Args:
            url: URL a scrapear
            limit: Límite de eventos
            
        Returns:
            Lista de eventos parseados
        """
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.error(f"❌ HTTP {response.status} al acceder a {url}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Debug: Imprimir parte del HTML para ver qué hay
                    logger.info(f"🔍 Meetup HTML contenido (primeros 500 chars): {html[:500]}")
                    
                    # Selectores específicos para Meetup SPA (React/Next.js)
                    event_elements = (
                        soup.select('[data-testid*="event"]') or
                        soup.select('[data-element-name*="event"]') or
                        soup.select('[data-event-id]') or
                        soup.select('.event') or
                        soup.select('div[id*="event"]') or
                        soup.select('a[href*="/events/"]') or
                        soup.select('div:contains("evento")') or
                        soup.select('*[class*="event"]')
                    )
                    
                    logger.info(f"🔍 Elementos encontrados con selectores: {len(event_elements) if event_elements else 0}")
                    
                    if not event_elements:
                        logger.warning("⚠️ No se encontraron elementos de eventos en Meetup")
                        return []
                    
                    events = []
                    for element in event_elements[:limit]:
                        event_data = self._parse_meetup_event(element, location)
                        if event_data:
                            events.append(self._standardize_event(event_data))
                    
                    return events
                    
        except Exception as e:
            logger.error(f"❌ Error scrapeando {url}: {str(e)}")
            return []
    
    async def _intelligent_fallback(self, location: str, category: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """
        🧠 FALLBACK INTELIGENTE PARA MEETUP
        
        Si no encuentra eventos en la ubicación específica, intenta con ubicaciones más generales
        """
        
        try:
            # Usar el servicio de IA para obtener información de ubicación
            ai_service = self.url_discovery_service.ai_service
            location_info = await ai_service.detect_location_info(location)
            
            # Intentar con la ciudad principal o país
            fallback_location = location_info.get('city', location)
            
            # Generar nueva URL para fallback
            request = UrlDiscoveryRequest(
                platform="meetup", 
                location=fallback_location,
                category=category
            )
            
            fallback_url = await self.url_discovery_service.discover_url(request)
            if not fallback_url:
                return []
            
            # Intentar scraping con ubicación de fallback
            events = await self._scrape_meetup_page(fallback_url, limit)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error en fallback inteligente de Meetup: {str(e)}")
            return []
    
    def _parse_meetup_event(self, event_element, location: str) -> Optional[Dict[str, Any]]:
        """
        📋 PARSING DE EVENTO INDIVIDUAL DE MEETUP
        
        Extrae información estructurada de un elemento de evento
        """
        
        try:
            # Título - Selectores modernos de Meetup
            title_elem = (
                event_element.select_one('[data-testid*="title"]') or
                event_element.select_one('h1, h2, h3, h4') or
                event_element.select_one('.event-title') or
                event_element.select_one('.title') or
                event_element.select_one('a')
            )
            title = title_elem.get_text(strip=True) if title_elem else 'Sin título'
            
            # URL del evento - Más específico
            link_elem = (
                event_element.select_one('a[href*="/events/"]') or
                event_element.select_one('a[href*="meetup.com"]') or
                event_element.select_one('a')
            )
            event_url = ''
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    event_url = f'https://www.meetup.com{href}'
                elif href.startswith('http'):
                    event_url = href
            
            # Imagen - Más opciones
            img_elem = (
                event_element.select_one('img[data-testid]') or
                event_element.select_one('img') 
            )
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Ubicación
            venue_elem = event_element.select_one('.venue, .location, [data-testid*="venue"]')
            if venue_elem:
                venue_name = venue_elem.get_text(strip=True)
            else:
                # Usar la ciudad como ubicación por defecto
                venue_name = f"{location}"
            
            # Fecha
            date_elem = event_element.select_one('.date, .time, [data-testid*="date"]')
            start_datetime = date_elem.get_text(strip=True) if date_elem else None
            
            return {
                'title': title,
                'description': 'Evento encontrado en Meetup',
                'event_url': event_url,
                'image_url': image_url,
                'venue_name': venue_name,
                'venue_address': None,
                'start_datetime': start_datetime,
                'price': None,
                'is_free': True,  # Meetup events son típicamente gratuitos
                'category': 'Eventos Comunitarios',
                'external_id': None
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parseando evento de Meetup: {str(e)}")
            return None