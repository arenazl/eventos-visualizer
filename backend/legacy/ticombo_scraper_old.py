"""
🎪 TICOMBO SCRAPER - Discovery Platform for Events
Scraper global para Ticombo.com con inyección de dependencias
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

class TicomboScraper(BaseGlobalScraper):
    """
    🎪 TICOMBO.COM SCRAPER GLOBAL
    
    CARACTERÍSTICAS:
    - Plataforma de descubrimiento de eventos internacional
    - Especializado en eventos culturales, conciertos, actividades
    - Parsing optimizado para estructura HTML de Ticombo
    - Manejo de eventos de diferentes categorías
    """
    
    def __init__(self, url_discovery_service: IUrlDiscoveryService, config: ScraperConfig = None):
        """
        Constructor con DEPENDENCY INJECTION
        
        Args:
            url_discovery_service: Servicio inyectado para descubrir URLs de Ticombo
            config: Configuración específica del scraper
        """
        super().__init__(url_discovery_service, config)
        
        # Headers HTTP optimizados para Ticombo
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
        🎯 SCRAPING PRINCIPAL DE TICOMBO.COM
        
        Proceso:
        1. Descubrir URL con IA
        2. Scrapear eventos principales
        3. Parsing y estandarización
        """
        
        logger.info(f"🎪 Ticombo Scraper: Iniciando para '{location}'")
        
        try:
            # 1. Descubrir URL con IA
            request = UrlDiscoveryRequest(
                platform="ticombo",
                location=location,
                category=category
            )
            
            url = await self.url_discovery_service.discover_url(request)
            if not url:
                logger.warning("⚠️ No se pudo generar URL para Ticombo")
                return []
            
            # 2. Scrapear URL principal
            events = await self._scrape_ticombo_page(url, limit)
            
            logger.info(f"✅ Ticombo: {len(events)} eventos parseados")
            return events[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error en Ticombo Scraper: {str(e)}")
            return []
    
    async def _scrape_ticombo_page(self, url: str, limit: int) -> List[Dict[str, Any]]:
        """
        🌐 SCRAPING DE PÁGINA ESPECÍFICA DE TICOMBO.COM
        
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
                    
                    # Selectores principales para eventos de Ticombo
                    event_cards = (
                        soup.select('.event-card') or
                        soup.select('.search-result') or
                        soup.select('.event-item') or
                        soup.select('[data-event]') or
                        soup.select('.card')
                    )
                    
                    if not event_cards:
                        logger.warning("⚠️ No se encontraron elementos de eventos en Ticombo")
                        return []
                    
                    logger.info(f"🎯 Ticombo: Encontrados {len(event_cards)} eventos potenciales")
                    
                    events = []
                    valid_events = 0
                    
                    for card in event_cards:
                        if valid_events >= limit:
                            break
                            
                        event_data = self._parse_ticombo_event(card)
                        if event_data:
                            events.append(self._standardize_event(event_data))
                            valid_events += 1
                    
                    logger.info(f"📝 Ticombo: {valid_events} eventos válidos extraídos")
                    return events
                    
        except Exception as e:
            logger.error(f"❌ Error scrapeando {url}: {str(e)}")
            return []
    
    def _parse_ticombo_event(self, event_element) -> Optional[Dict[str, Any]]:
        """
        📋 PARSING DE EVENTO INDIVIDUAL DE TICOMBO
        
        Extrae información estructurada de un elemento de evento
        """
        
        try:
            # URL del evento
            link_elem = (
                event_element.select_one('a[href*="/event/"]') or
                event_element.select_one('a[href*="/discover/"]') or
                event_element.select_one('a') 
            )
            event_url = ''
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    event_url = f"https://www.ticombo.com{href}"
                elif href.startswith('http'):
                    event_url = href
            
            # Título
            title_elem = (
                event_element.select_one('.event-title') or
                event_element.select_one('.title') or
                event_element.select_one('h1, h2, h3, h4') or
                event_element.select_one('[data-title]')
            )
            title = title_elem.get_text(strip=True) if title_elem else 'Sin título'
            
            # Imagen
            img_elem = event_element.select_one('img')
            image_url = ''
            if img_elem:
                src = img_elem.get('src', '') or img_elem.get('data-src', '')
                if src and not src.startswith('http'):
                    image_url = f"https://www.ticombo.com{src}"
                else:
                    image_url = src
            
            # Venue/ubicación
            venue_elem = (
                event_element.select_one('.venue') or
                event_element.select_one('.location') or
                event_element.select_one('.place')
            )
            venue_name = venue_elem.get_text(strip=True) if venue_elem else 'Ubicación no especificada'
            
            # Fecha/hora
            date_elem = (
                event_element.select_one('.date') or
                event_element.select_one('.datetime') or
                event_element.select_one('[data-date]')
            )
            start_datetime = date_elem.get_text(strip=True) if date_elem else None
            
            # Precio
            price_elem = (
                event_element.select_one('.price') or
                event_element.select_one('.cost') or
                event_element.select_one('[data-price]')
            )
            price_text = price_elem.get_text(strip=True) if price_elem else None
            
            is_free = False
            if price_text and ('free' in price_text.lower() or 'gratis' in price_text.lower()):
                is_free = True
            
            # Solo retornar eventos que tengan al menos título
            if not title or title == 'Sin título' or len(title) < 3:
                return None
            
            return {
                'title': title,
                'description': 'Evento encontrado en Ticombo',
                'event_url': event_url,
                'image_url': image_url,
                'venue_name': venue_name,
                'venue_address': None,
                'start_datetime': start_datetime,
                'price': None,
                'is_free': is_free,
                'category': 'Eventos Culturales',
                'external_id': None
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parseando evento de Ticombo: {str(e)}")
            return None