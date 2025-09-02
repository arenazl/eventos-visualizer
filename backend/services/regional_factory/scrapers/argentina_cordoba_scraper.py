"""
🏛️ ARGENTINA CÓRDOBA SCRAPER - Eventos específicos de Córdoba
Scraper especializado para eventos en la ciudad de Córdoba, Argentina
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from ..base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ArgentinaCordobaScraper(BaseScraper):
    """
    🏛️ SCRAPER ESPECÍFICO DE CÓRDOBA, ARGENTINA
    
    CARACTERÍSTICAS:
    - Especializado en eventos locales de Córdoba
    - Conoce venues específicos de la ciudad
    - Maneja categorías típicas cordobesas
    - URLs y fuentes locales optimizadas
    """
    
    def __init__(self):
        super().__init__(region='argentina', city='cordoba')
        
        # Headers optimizados para sitios argentinos
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
        
        # URLs específicas de Córdoba
        self.local_sources = [
            'https://www.eventbrite.com.ar/d/argentina--cordoba/events/',
            'https://www.cordoba.gob.ar/agenda-cultural/',
            # Agregar más fuentes locales específicas de Córdoba
        ]
        
        # Venues conocidos de Córdoba
        self.known_venues = [
            'Teatro del Libertador San Martín',
            'Centro Cultural Córdoba',
            'Complejo Forja',
            'Estadio Mario Alberto Kempes', 
            'La Vieja Esquina',
            'Quality Espacio',
            'Sala Lavardén'
        ]
    
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🎯 SCRAPING ESPECÍFICO DE CÓRDOBA
        
        Busca eventos en fuentes locales conocidas de Córdoba
        """
        
        logger.info(f"🏛️ Córdoba Scraper: Iniciando para '{location}' (categoría: {category})")
        
        all_events = []
        
        try:
            # 1. Scraper Eventbrite Córdoba específico
            eventbrite_events = await self._scrape_eventbrite_cordoba(limit // 2)
            all_events.extend(eventbrite_events)
            
            # 2. Scraper agenda cultural oficial de Córdoba
            cultural_events = await self._scrape_cordoba_oficial(limit // 2)
            all_events.extend(cultural_events)
            
            # 3. Filtrar por categoría si se especifica
            if category and category != 'general':
                all_events = self._filter_by_category(all_events, category)
            
            # 4. Estandarizar todos los eventos
            standardized_events = []
            for event in all_events[:limit]:
                standardized = self._standardize_event(event)
                standardized_events.append(standardized)
            
            logger.info(f"✅ Córdoba: {len(standardized_events)} eventos encontrados")
            return standardized_events
            
        except Exception as e:
            logger.error(f"❌ Error en Córdoba scraper: {str(e)}")
            return []
    
    async def _scrape_eventbrite_cordoba(self, limit: int) -> List[Dict[str, Any]]:
        """
        🎫 SCRAPER EVENTBRITE ESPECÍFICO DE CÓRDOBA
        
        Args:
            limit: Límite de eventos
            
        Returns:
            Lista de eventos de Eventbrite Córdoba
        """
        
        try:
            url = 'https://www.eventbrite.com.ar/d/argentina--cordoba/events/'
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ Eventbrite Córdoba HTTP {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Selectores específicos de Eventbrite
                    event_cards = soup.select('a.event-card-link')
                    
                    events = []
                    for card in event_cards[:limit]:
                        event_data = self._parse_eventbrite_event(card)
                        if event_data:
                            events.append(event_data)
                    
                    logger.info(f"🎫 Eventbrite Córdoba: {len(events)} eventos")
                    return events
                    
        except Exception as e:
            logger.warning(f"⚠️ Error en Eventbrite Córdoba: {str(e)}")
            return []
    
    async def _scrape_cordoba_oficial(self, limit: int) -> List[Dict[str, Any]]:
        """
        🏛️ SCRAPER AGENDA CULTURAL OFICIAL DE CÓRDOBA
        
        Args:
            limit: Límite de eventos
            
        Returns:
            Lista de eventos oficiales de Córdoba
        """
        
        try:
            # Placeholder para scraper oficial de Córdoba
            # En la implementación real, scrapearia www.cordoba.gob.ar/agenda-cultural/
            
            # Por ahora, devolvemos eventos simulados específicos de Córdoba
            cordoba_events = [
                {
                    'title': 'Festival de Tango en el Cabildo',
                    'description': 'Festival de tango en el histórico Cabildo de Córdoba',
                    'venue_name': 'Cabildo Histórico de Córdoba',
                    'venue_address': 'Independencia 30, Córdoba Capital',
                    'category': 'Cultural',
                    'is_free': True,
                    'event_url': 'https://www.cordoba.gob.ar/eventos/festival-tango'
                },
                {
                    'title': 'Concierto en Teatro del Libertador',
                    'description': 'Concierto de música clásica en el teatro principal de Córdoba',
                    'venue_name': 'Teatro del Libertador San Martín',
                    'venue_address': 'Av. Vélez Sársfield 365, Córdoba',
                    'category': 'Música',
                    'is_free': False,
                    'event_url': 'https://www.teatrodellibertador.gob.ar'
                }
            ]
            
            logger.info(f"🏛️ Agenda Oficial Córdoba: {len(cordoba_events)} eventos")
            return cordoba_events[:limit]
            
        except Exception as e:
            logger.warning(f"⚠️ Error en agenda oficial Córdoba: {str(e)}")
            return []
    
    def _parse_eventbrite_event(self, event_card) -> Optional[Dict[str, Any]]:
        """
        📋 PARSER DE EVENTO EVENTBRITE CON CONTEXTO CÓRDOBA
        
        Args:
            event_card: Elemento HTML del evento
            
        Returns:
            Diccionario con datos del evento o None
        """
        
        try:
            # URL del evento
            event_url = event_card.get('href', '')
            if not event_url.startswith('http'):
                event_url = 'https://www.eventbrite.com.ar' + event_url
            
            # Título
            title_elem = event_card.select_one('.event-card-title')
            title = title_elem.get_text(strip=True) if title_elem else 'Evento en Córdoba'
            
            # Imagen
            img_elem = event_card.select_one('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Venue - intentar detectar si es un venue conocido de Córdoba
            venue_elem = event_card.select_one('.event-card-venue')
            venue_name = 'Córdoba'
            
            if venue_elem:
                venue_text = venue_elem.get_text(strip=True)
                # Verificar si coincide con venues conocidos de Córdoba
                for known_venue in self.known_venues:
                    if known_venue.lower() in venue_text.lower():
                        venue_name = known_venue
                        break
                else:
                    venue_name = venue_text if venue_text else 'Córdoba'
            
            return {
                'title': title,
                'event_url': event_url,
                'image_url': image_url,
                'venue_name': venue_name,
                'description': f'Evento encontrado en Eventbrite Córdoba',
                'category': 'Eventos'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parseando evento Eventbrite: {str(e)}")
            return None
    
    def _filter_by_category(self, events: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        """
        🏷️ FILTRAR EVENTOS POR CATEGORÍA
        
        Args:
            events: Lista de eventos
            category: Categoría a filtrar
            
        Returns:
            Eventos filtrados por categoría
        """
        
        if not category or category.lower() == 'general':
            return events
        
        category_keywords = {
            'música': ['música', 'concierto', 'show', 'banda', 'cantante'],
            'cultural': ['cultural', 'arte', 'museo', 'teatro', 'exposición'],
            'deportes': ['deporte', 'fútbol', 'rugby', 'basket', 'partido'],
            'tech': ['tech', 'tecnología', 'conferencia', 'workshop', 'hackathon']
        }
        
        keywords = category_keywords.get(category.lower(), [category.lower()])
        
        filtered_events = []
        for event in events:
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()
            
            if any(keyword in title or keyword in description for keyword in keywords):
                filtered_events.append(event)
        
        return filtered_events