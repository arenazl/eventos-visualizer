"""
🎫 EVENTBRITE SCRAPER - Global Event Discovery
Scraper global para Eventbrite con inyección de dependencias y detección inteligente
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

class EventbriteScraper(BaseGlobalScraper):
    """
    🎫 EVENTBRITE SCRAPER GLOBAL
    
    CARACTERÍSTICAS:
    - Funciona en cualquier ubicación mundial
    - Detección inteligente de provincia para fallbacks
    - Parsing optimizado para estructura HTML de Eventbrite
    - Manejo de eventos pagos y gratuitos
    - Sistema de fallbacks inteligentes
    """
    
    # 🎯 HABILITADO POR DEFECTO - SCRAPER PRINCIPAL
    enabled_by_default: bool = True
    priority: int = 2  # Fast web scraping ~1200ms
    nearby_cities: bool = True  # Soporta búsqueda de ciudades cercanas por IA
    
    def __init__(self, url_discovery_service: IUrlDiscoveryService, config: ScraperConfig = None):
        """
        Constructor con DEPENDENCY INJECTION
        
        Args:
            url_discovery_service: Servicio inyectado para descubrir URLs de Eventbrite
            config: Configuración específica del scraper
        """
        super().__init__(url_discovery_service, config)
        
        # Headers HTTP optimizados para Eventbrite
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
        🎯 SCRAPING PRINCIPAL DE EVENTBRITE CON CACHÉ INTELIGENTE
        
        Proceso:
        1. Descubrir URL con caché JSON (súper rápido) o IA (primera vez)
        2. Scrapear eventos principales
        3. Fallback inteligente con detección de provincia
        4. Parsing y estandarización
        """
        
        logger.info(f"🎫 Eventbrite Scraper: Iniciando para '{location}' con caché inteligente")
        
        try:
            # 1. 🎯 GENERAR URL CON PATTERN SERVICE (SIN AI)
            from services.pattern_service import pattern_service
            
            detected_country = self.context.get('detected_country', '')
            detected_province = self.context.get('detected_province', '')
            
            url = pattern_service.generate_url(
                platform="eventbrite",
                localidad=location,
                provincia=detected_province,
                pais=detected_country
            )
            if not url:
                logger.warning("⚠️ No se pudo generar URL para Eventbrite")
                return []
            
            # 2. Scrapear URL principal
            events = await self._scrape_eventbrite_page(url, limit, location)
            
            # 3. Si no hay eventos, intentar fallback con provincia
            if not events:
                logger.info("🔄 No se encontraron eventos en {}, intentando fallback inteligente con IA...".format(location.split(',')[0]))
                events = await self._intelligent_fallback(location, category, limit)
            
            logger.info(f"✅ Eventbrite: {len(events)} eventos parseados")
            return events[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error en Eventbrite Scraper: {str(e)}")
            return []
    
    async def _scrape_eventbrite_page(self, url: str, limit: int, location: str) -> List[Dict[str, Any]]:
        """
        🌐 SCRAPING DE PÁGINA ESPECÍFICA DE EVENTBRITE
        
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
                    logger.info(f"⏱️ EVENTBRITE HTTP REQUEST: {http_duration:.2f}s")
                    
                    # ⏱️ TIMING: Inicio del parsing
                    parse_start = time.time()
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Selector principal para eventos de Eventbrite
                    event_links = soup.select('a.event-card-link')
                    
                    if not event_links:
                        logger.warning("⚠️ No se encontraron enlaces de eventos en Eventbrite")
                        return []
                    
                    logger.info(f"🎯 Encontrados {len(event_links)} eventos con 'a.event-card-link'")
                    
                    events = []
                    for link in event_links[:limit]:
                        event_data = self._parse_eventbrite_event(link, location)
                        if event_data:
                            events.append(self._standardize_event(event_data))
                    
                    # ⏱️ TIMING: Parsing completado
                    parse_end = time.time()
                    parse_duration = parse_end - parse_start
                    total_duration = parse_end - http_start
                    
                    logger.info(f"⏱️ EVENTBRITE PARSING: {parse_duration:.2f}s")
                    logger.info(f"⏱️ EVENTBRITE TOTAL: {total_duration:.2f}s (HTTP: {http_duration:.2f}s + Parse: {parse_duration:.2f}s)")
                    
                    return events
                    
        except Exception as e:
            logger.error(f"❌ Error scrapeando {url}: {str(e)}")
            return []
    
    async def _intelligent_fallback(self, location: str, category: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """
        🧠 FALLBACK INTELIGENTE CON DETECCIÓN DE PROVINCIA
        
        Si no encuentra eventos en la ciudad específica, detecta la provincia
        usando IA y busca eventos a nivel provincial
        """
        
        try:
            # Usar el servicio de IA para detectar provincia
            ai_service = self.url_discovery_service.ai_service
            location_info = await ai_service.detect_location_info(location)
            
            province = location_info.get('province')
            if not province:
                logger.warning("⚠️ No se pudo detectar provincia para fallback")
                return []
            
            logger.info(f"🧠 IA detectó provincia: '{location}' → '{province}'")
            logger.info(f"🧠 IA detectó provincia para fallback: {province}")
            
            # Generar nueva URL con provincia
            request = UrlDiscoveryRequest(
                platform="eventbrite", 
                location=province,
                category=category,
                detected_country=self.context.get('detected_country')
            )
            
            province_url = await self.url_discovery_service.discover_url(request)
            if not province_url:
                logger.warning("⚠️ No se pudo generar URL de fallback con provincia")
                return []
            
            logger.info(f"🌐 URL fallback con provincia: {province_url}")
            
            # Intentar scrapear con la provincia
            events = await self._scrape_eventbrite_page(province_url, limit, province)
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error en fallback inteligente: {str(e)}")
            return []
    
    def _extract_title_intelligent(self, event_element) -> str:
        """
        🎯 EXTRACCIÓN INTELIGENTE DE TÍTULO
        
        Busca el título con múltiples estrategias hasta encontrarlo
        """
        # Lista de selectores en orden de prioridad
        title_selectors = [
            '.event-card-title',           # Selector clásico
            'h3',                          # Header común
            '.card-text--truncated__one',  # Selector específico
            '.Stack-child',                # Stack child
            '[data-testid*="title"]',      # Data testid con title
            '[aria-label*="title"]',       # Aria label
            'a[href*="/e/"] span',         # Span dentro de link de evento
            'a[href*="/e/"]',              # El link mismo
            '.eds-event-card-content__title', # Nuevo selector EDS
            '.eds-text-weight--heavy',     # Texto en negrita
            '.eds-l-mar-bot-2',           # Margin bottom 2
            'div[data-automation="eventcard-title"]', # Data automation
            'span',                        # Cualquier span
            'div',                         # Cualquier div con texto
        ]
        
        # Intentar cada selector
        for selector in title_selectors:
            try:
                title_elem = event_element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and title.lower() not in ['', 'sin título', 'event', 'more']:
                        logger.debug(f"🎯 Título encontrado con selector '{selector}': {title[:50]}...")
                        return title
            except Exception:
                continue
        
        # Fallback: extraer texto de toda la estructura
        try:
            all_text = event_element.get_text(strip=True)
            if all_text:
                # Tomar las primeras palabras (título probable)
                words = all_text.split()[:10]  # Primeras 10 palabras
                title_candidate = ' '.join(words)
                if len(title_candidate) > 5:  # Al menos 5 caracteres
                    logger.debug(f"🎯 Título extraído de texto completo: {title_candidate[:50]}...")
                    return title_candidate
        except Exception:
            pass
        
        # Último recurso: extraer del href si es descriptivo
        try:
            href = event_element.get('href', '')
            if '/e/' in href:
                # Extraer nombre del evento de la URL
                url_parts = href.split('/e/')[-1].split('-')[:-1]  # Quitar ID final
                if url_parts:
                    title_from_url = ' '.join(url_parts).replace('-', ' ').title()
                    if len(title_from_url) > 5:
                        logger.debug(f"🎯 Título extraído de URL: {title_from_url[:50]}...")
                        return title_from_url
        except Exception:
            pass
        
        return 'Sin título'

    def _parse_eventbrite_event(self, event_element, location: str) -> Optional[Dict[str, Any]]:
        """
        📋 PARSING DE EVENTO INDIVIDUAL DE EVENTBRITE
        
        Extrae información estructurada de un elemento de evento
        """
        
        try:
            # URL del evento
            event_url = event_element.get('href', '')
            if event_url and not event_url.startswith('http'):
                event_url = 'https://www.eventbrite.com' + event_url
            
            # Buscar título con múltiples estrategias
            title = self._extract_title_intelligent(event_element)
            
            # Imagen
            img_elem = event_element.select_one('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Venue/ubicación
            venue_elem = event_element.select_one('.event-card-venue, .card-text--truncated__two')
            if venue_elem:
                venue_name = venue_elem.get_text(strip=True)
            else:
                # Usar la ciudad como ubicación por defecto
                venue_name = f"{location}"
            
            # Precio (si está disponible)
            price_elem = event_element.select_one('.event-card-price, .eds-text-bs, .eds-text-weight--heavy')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            
            is_free = False
            if price_text and ('gratis' in price_text.lower() or 'free' in price_text.lower()):
                is_free = True
            
            return {
                'title': title,
                'description': 'Evento encontrado en Eventbrite',
                'event_url': event_url,
                'image_url': image_url,
                'venue_name': venue_name,
                'venue_address': None,
                'start_datetime': None,
                'price': None,
                'is_free': is_free,
                'category': 'Eventos',
                'external_id': None
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parseando evento de Eventbrite: {str(e)}")
            return None