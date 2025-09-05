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
    
    # 🔴 DISABLED - Old version without Playwright
    enabled_by_default: bool = False
    nearby_cities: bool = True  # Soporta búsqueda de ciudades cercanas por IA
    
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
                    
                    # 🎯 NUEVA ESTRATEGIA: Extraer JSON embebido de __NEXT_DATA__
                    import json
                    import re
                    
                    # Buscar el script con __NEXT_DATA__
                    json_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
                    
                    # Logging para debug
                    if '__NEXT_DATA__' in html:
                        logger.info("✅ Meetup: __NEXT_DATA__ encontrado en HTML")
                    else:
                        logger.warning("⚠️ Meetup: __NEXT_DATA__ NO encontrado en HTML")
                    
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(1))
                            logger.info(f"✅ Meetup: JSON __NEXT_DATA__ encontrado y parseado")
                            
                            # Navegar por la estructura de Next.js para encontrar eventos
                            events = []
                            
                            # La estructura puede variar, intentar múltiples rutas
                            props = json_data.get('props', {})
                            page_props = props.get('pageProps', {})
                            
                            # 🎯 MEETUP USA APOLLO STATE PARA EVENTOS
                            apollo_state = page_props.get('__APOLLO_STATE__', {})
                            raw_events = []
                            
                            # Extraer eventos del Apollo State
                            if apollo_state:
                                logger.info(f"🎯 Meetup: Apollo State encontrado con {len(apollo_state)} objetos")
                                for key, value in apollo_state.items():
                                    # Los eventos están en keys como "Event:123456"
                                    if key.startswith('Event:') and isinstance(value, dict):
                                        if 'title' in value:  # Validar que sea un evento real
                                            raw_events.append(value)
                                logger.info(f"✅ Meetup: {len(raw_events)} eventos extraídos de Apollo State")
                            
                            # Si no hay eventos en Apollo, buscar recursivamente
                            if not raw_events:
                                raw_events = self._find_events_in_json(json_data)
                            
                            if raw_events:
                                logger.info(f"🎯 Meetup: {len(raw_events)} eventos encontrados en JSON")
                                
                                for event in raw_events[:limit]:
                                    parsed_event = self._parse_json_event(event, location)
                                    if parsed_event:
                                        events.append(self._standardize_event(parsed_event))
                                
                                return events
                            else:
                                logger.warning("⚠️ No se encontraron eventos en el JSON de Meetup")
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Error parseando JSON de Meetup: {e}")
                    else:
                        logger.warning("⚠️ No se encontró __NEXT_DATA__ en la página de Meetup")
                    
                    # Fallback: intentar parsing HTML tradicional si no hay JSON
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Selectores específicos para Meetup SPA (React/Next.js)
                    event_elements = (
                        soup.select('[data-testid*="event"]') or
                        soup.select('[data-element-name*="event"]') or
                        soup.select('[data-event-id]') or
                        soup.select('.event') or
                        soup.select('div[id*="event"]') or
                        soup.select('a[href*="/events/"]')
                    )
                    
                    logger.info(f"🔍 Elementos HTML encontrados: {len(event_elements) if event_elements else 0}")
                    
                    if not event_elements:
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
    
    def _find_events_in_json(self, data: Dict, depth: int = 0) -> List[Dict]:
        """
        🔍 BUSCAR EVENTOS RECURSIVAMENTE EN JSON
        
        Busca estructuras que parezcan eventos en el JSON de Meetup
        """
        if depth > 5:  # Evitar recursión infinita
            return []
        
        events = []
        
        # Si es una lista, verificar si son eventos
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # Verificar si tiene campos típicos de eventos
                    if any(key in item for key in ['title', 'name', 'eventType', 'dateTime', 'startDate']):
                        events.append(item)
                    else:
                        # Buscar recursivamente
                        events.extend(self._find_events_in_json(item, depth + 1))
        
        # Si es un diccionario, buscar en sus valores
        elif isinstance(data, dict):
            for key, value in data.items():
                # Keys que típicamente contienen eventos
                if any(event_key in key.lower() for event_key in ['event', 'result', 'edge', 'node']):
                    if isinstance(value, (list, dict)):
                        events.extend(self._find_events_in_json(value, depth + 1))
        
        return events
    
    def _parse_json_event(self, event: Dict, location: str) -> Optional[Dict[str, Any]]:
        """
        📋 PARSING DE EVENTO JSON DE MEETUP
        
        Extrae información estructurada de un evento en JSON
        """
        try:
            # Extraer campos comunes de eventos de Meetup
            title = (
                event.get('title') or 
                event.get('name') or 
                event.get('eventName') or
                'Evento de Meetup'
            )
            
            description = (
                event.get('description') or 
                event.get('shortDescription') or 
                event.get('plainTextDescription') or
                ''
            )
            
            # URL del evento
            event_url = event.get('eventUrl') or event.get('link') or ''
            if event_url and not event_url.startswith('http'):
                event_url = f'https://www.meetup.com{event_url}'
            
            # Imagen
            images = event.get('images', [])
            image_url = ''
            if images and isinstance(images, list):
                image_url = images[0].get('source') if isinstance(images[0], dict) else ''
            elif event.get('featuredPhoto'):
                image_url = event['featuredPhoto'].get('source', '')
            elif event.get('image'):
                image_url = event['image']
            
            # Ubicación
            venue = event.get('venue', {})
            venue_name = (
                venue.get('name') or 
                venue.get('address') or 
                event.get('venueName') or
                location
            )
            
            venue_address = (
                venue.get('address') or
                venue.get('fullAddress') or
                event.get('address') or
                ''
            )
            
            # Fecha y hora
            date_time = (
                event.get('dateTime') or
                event.get('startDate') or
                event.get('localDate') or
                event.get('datetime') or
                None
            )
            
            # Precio
            is_free = event.get('isFree', True)
            price = None
            if event.get('feeSettings'):
                fee = event['feeSettings'].get('amount', 0)
                if fee > 0:
                    price = fee
                    is_free = False
            
            # Categoría
            category = (
                event.get('category', {}).get('name') if isinstance(event.get('category'), dict) else
                event.get('category') or
                'Eventos Comunitarios'
            )
            
            # Grupo organizador
            group = event.get('group', {})
            group_name = group.get('name', '') if isinstance(group, dict) else ''
            
            # Número de asistentes
            attendee_count = (
                event.get('going', 0) or
                event.get('rsvpCount', 0) or
                event.get('attendeeCount', 0)
            )
            
            return {
                'title': title,
                'description': description[:500] if description else f"Evento organizado por {group_name}" if group_name else "Evento de Meetup",
                'event_url': event_url,
                'image_url': image_url,
                'venue_name': venue_name,
                'venue_address': venue_address,
                'start_datetime': date_time,
                'price': price,
                'is_free': is_free,
                'category': category,
                'external_id': event.get('id') or event.get('eventId'),
                'attendee_count': attendee_count
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parseando evento JSON de Meetup: {str(e)}")
            return None
    
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