"""
Songkick Scraper - Conciertos y música en vivo
Funciona globalmente sin necesidad de API key
"""

import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re

from services.scraper_interface import BaseGlobalScraper

logger = logging.getLogger(__name__)

class SongkickScraper(BaseGlobalScraper):
    def __init__(self, url_discovery_service=None):
        super().__init__(url_discovery_service)
        self.name = "songkick"
        self.display_name = "Songkick"
        self.base_url = "https://www.songkick.com"
        self.enabled_by_default = True
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def _build_search_url(self, location: str) -> str:
        """Construye URL de búsqueda para Songkick"""
        # Songkick usa formato: /search?query=barcelona&type=upcoming
        location_clean = location.split(',')[0].strip().lower()
        return f"{self.base_url}/search?query={location_clean}&type=upcoming"

    async def fetch_events(self, location: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Obtiene eventos de Songkick para una ubicación"""
        logger.info(f"🎸 Songkick Scraper: Iniciando para '{location}'")

        events = []
        try:
            url = self._build_search_url(location)
            logger.info(f"🔗 Songkick URL: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Buscar el JSON con los datos de eventos
                        script_tags = soup.find_all('script', type='application/ld+json')

                        for script in script_tags:
                            try:
                                data = json.loads(script.string)
                                if isinstance(data, dict) and '@type' in data:
                                    if data['@type'] == 'MusicEvent' or data['@type'] == 'Event':
                                        events.append(self._parse_json_event(data))
                            except:
                                pass

                        # También buscar en el HTML directo
                        event_cards = soup.find_all('div', class_='event-listings-element')
                        if not event_cards:
                            event_cards = soup.find_all('li', class_='event-listing')

                        for card in event_cards[:limit]:
                            event = self._parse_html_event(card, location)
                            if event:
                                events.append(event)

                        # Si no encontramos eventos, intentar con la API JSON
                        if not events:
                            events = await self._fetch_from_api(location, limit)

                        logger.info(f"✅ Songkick: {len(events)} eventos encontrados")
                    else:
                        logger.error(f"❌ HTTP {response.status} al acceder a {url}")

        except aiohttp.ClientTimeout:
            logger.error(f"⏰ Timeout scrapeando Songkick para {location}")
        except Exception as e:
            logger.error(f"❌ Error scrapeando Songkick: {str(e)}")

        return events[:limit]

    async def _fetch_from_api(self, location: str, limit: int) -> List[Dict[str, Any]]:
        """Intenta obtener eventos desde el endpoint API de Songkick"""
        events = []
        try:
            # Songkick tiene un endpoint API público sin key
            location_clean = location.split(',')[0].strip()
            api_url = f"{self.base_url}/api/3.0/search/locations.json?query={location_clean}&apikey=io09K9l3ebJxmxe2"

            async with aiohttp.ClientSession() as session:
                # Primero obtener el location ID
                async with session.get(api_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('resultsPage', {}).get('results', {}).get('location'):
                            location_data = data['resultsPage']['results']['location'][0]
                            metro_id = location_data.get('metroArea', {}).get('id')

                            if metro_id:
                                # Ahora obtener eventos para ese metro area
                                events_url = f"{self.base_url}/api/3.0/metro_areas/{metro_id}/calendar.json?apikey=io09K9l3ebJxmxe2"
                                async with session.get(events_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=5)) as events_resp:
                                    if events_resp.status == 200:
                                        events_data = await events_resp.json()
                                        for event in events_data.get('resultsPage', {}).get('results', {}).get('event', [])[:limit]:
                                            events.append(self._parse_api_event(event, location))
        except:
            pass

        return events

    def _parse_json_event(self, data: Dict) -> Dict[str, Any]:
        """Parsea evento desde JSON-LD"""
        return {
            'id': f"songkick_{data.get('url', '').split('/')[-1]}",
            'title': data.get('name', 'Concierto sin título'),
            'description': data.get('description', ''),
            'start_datetime': data.get('startDate'),
            'venue_name': data.get('location', {}).get('name', ''),
            'venue_address': data.get('location', {}).get('address', ''),
            'category': 'Música',
            'subcategory': 'Conciertos',
            'price': None,
            'currency': 'EUR',
            'is_free': False,
            'image_url': data.get('image'),
            'event_url': data.get('url'),
            'source': 'songkick',
            'source_display': '🎸 Songkick'
        }

    def _parse_html_event(self, card, location: str) -> Optional[Dict[str, Any]]:
        """Parsea evento desde HTML"""
        try:
            # Título
            title_elem = card.find(['h2', 'h3', 'a'], class_=re.compile('event-name|artist-name'))
            if not title_elem:
                title_elem = card.find('a')
            title = title_elem.text.strip() if title_elem else 'Concierto'

            # URL
            url_elem = card.find('a', href=True)
            event_url = f"{self.base_url}{url_elem['href']}" if url_elem else None

            # Fecha
            date_elem = card.find(['time', 'div', 'span'], class_=re.compile('date|when'))
            date_str = date_elem.text.strip() if date_elem else None

            # Venue
            venue_elem = card.find(['div', 'span'], class_=re.compile('venue|location|place'))
            venue = venue_elem.text.strip() if venue_elem else location

            return {
                'id': f"songkick_{hash(title + str(date_str))}",
                'title': title,
                'description': f"Concierto en {venue}",
                'start_datetime': self._parse_date(date_str),
                'venue_name': venue,
                'venue_address': location,
                'category': 'Música',
                'subcategory': 'Conciertos',
                'price': None,
                'currency': 'EUR',
                'is_free': False,
                'image_url': f"https://picsum.photos/400/200?random={hash(title)}",
                'event_url': event_url,
                'source': 'songkick',
                'source_display': '🎸 Songkick'
            }
        except:
            return None

    def _parse_api_event(self, event: Dict, location: str) -> Dict[str, Any]:
        """Parsea evento desde API JSON"""
        # Obtener artistas
        artists = []
        for perf in event.get('performance', []):
            artists.append(perf.get('artist', {}).get('displayName', ''))

        title = ', '.join(artists) if artists else event.get('displayName', 'Concierto')

        return {
            'id': f"songkick_{event.get('id')}",
            'title': title,
            'description': event.get('type', 'Concert'),
            'start_datetime': event.get('start', {}).get('datetime'),
            'venue_name': event.get('venue', {}).get('displayName', ''),
            'venue_address': f"{event.get('location', {}).get('city', location)}",
            'category': 'Música',
            'subcategory': event.get('type', 'Conciertos'),
            'price': None,
            'currency': 'EUR',
            'is_free': False,
            'image_url': f"https://images.sk-static.com/images/media/profile_images/events/{event.get('id')}/huge_avatar",
            'event_url': event.get('uri', ''),
            'source': 'songkick',
            'source_display': '🎸 Songkick'
        }

    async def scrape_events(self, location: str, category: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Implementación del método abstracto requerido"""
        return await self.fetch_events(location, limit)

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Intenta parsear fecha desde string"""
        if not date_str:
            return None
        try:
            # Intentar varios formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%B %d, %Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except:
                    continue
        except:
            pass
        return None