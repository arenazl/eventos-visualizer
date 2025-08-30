"""
Gestor de APIs de Eventos
Configura y gestiona todas las APIs disponibles
"""

import os
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class APIManager:
    """
    Gestor centralizado de todas las APIs de eventos
    """
    
    def __init__(self):
        # APIs configuradas
        self.apis = {
            'eventbrite': {
                'enabled': bool(os.getenv('EVENTBRITE_API_KEY')),
                'key': os.getenv('EVENTBRITE_API_KEY'),
                'base_url': 'https://www.eventbriteapi.com/v3',
                'rate_limit': 1000,  # por hora
                'coverage': ['Argentina', 'México', 'Brasil', 'Chile', 'Colombia']
            },
            'ticketmaster': {
                'enabled': bool(os.getenv('TICKETMASTER_API_KEY')),
                'key': os.getenv('TICKETMASTER_API_KEY'),
                'base_url': 'https://app.ticketmaster.com/discovery/v2',
                'rate_limit': 5000,  # por día
                'coverage': ['México', 'Argentina', 'Chile', 'Colombia']
            },
            'bandsintown': {
                'enabled': bool(os.getenv('BANDSINTOWN_APP_ID')),
                'app_id': os.getenv('BANDSINTOWN_APP_ID', 'eventos-visualizer'),
                'base_url': 'https://rest.bandsintown.com',
                'rate_limit': None,  # Sin límite para apps no comerciales
                'coverage': ['Global']
            },
            'seatgeek': {
                'enabled': bool(os.getenv('SEATGEEK_CLIENT_ID')),
                'client_id': os.getenv('SEATGEEK_CLIENT_ID'),
                'client_secret': os.getenv('SEATGEEK_CLIENT_SECRET'),
                'base_url': 'https://api.seatgeek.com/2',
                'rate_limit': 1000,  # por mes
                'coverage': ['Global']
            },
            'meetup': {
                'enabled': bool(os.getenv('MEETUP_API_KEY')),
                'key': os.getenv('MEETUP_API_KEY'),
                'base_url': 'https://api.meetup.com/gql',
                'rate_limit': None,  # Variable
                'coverage': ['Global']
            }
        }
        
        # Cache de respuestas
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de todas las APIs
        """
        status = {
            'total_apis': len(self.apis),
            'enabled_apis': sum(1 for api in self.apis.values() if api['enabled']),
            'apis': {}
        }
        
        for name, api in self.apis.items():
            status['apis'][name] = {
                'enabled': api['enabled'],
                'has_credentials': bool(api.get('key') or api.get('app_id') or api.get('client_id')),
                'rate_limit': api['rate_limit'],
                'coverage': api['coverage']
            }
        
        return status
    
    async def fetch_ticketmaster_events(self, location: str, limit: int = 50) -> List[Dict]:
        """
        Obtiene eventos de Ticketmaster
        """
        if not self.apis['ticketmaster']['enabled']:
            logger.warning("Ticketmaster API no configurada")
            return []
        
        events = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.apis['ticketmaster']['base_url']}/events.json"
                params = {
                    'apikey': self.apis['ticketmaster']['key'],
                    'city': location,
                    'countryCode': self._get_country_code(location),
                    'size': limit,
                    'sort': 'date,asc'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if '_embedded' in data and 'events' in data['_embedded']:
                            for event in data['_embedded']['events']:
                                normalized = self._normalize_ticketmaster_event(event)
                                events.append(normalized)
                        
                        logger.info(f"✅ Ticketmaster: {len(events)} eventos en {location}")
                    else:
                        logger.error(f"Error Ticketmaster API: {response.status}")
        
        except Exception as e:
            logger.error(f"Error fetching Ticketmaster events: {e}")
        
        return events
    
    async def fetch_bandsintown_events(self, artist: Optional[str] = None, location: str = "Buenos Aires") -> List[Dict]:
        """
        Obtiene eventos de Bandsintown
        """
        if not self.apis['bandsintown']['enabled']:
            return []
        
        events = []
        
        try:
            async with aiohttp.ClientSession() as session:
                if artist:
                    # Buscar eventos de un artista específico
                    url = f"{self.apis['bandsintown']['base_url']}/artists/{artist}/events"
                else:
                    # Buscar eventos por ubicación
                    url = f"{self.apis['bandsintown']['base_url']}/events/search"
                
                params = {
                    'app_id': self.apis['bandsintown']['app_id'],
                    'location': location
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for event in data:
                            normalized = self._normalize_bandsintown_event(event)
                            events.append(normalized)
                        
                        logger.info(f"✅ Bandsintown: {len(events)} eventos")
                    else:
                        logger.error(f"Error Bandsintown API: {response.status}")
        
        except Exception as e:
            logger.error(f"Error fetching Bandsintown events: {e}")
        
        return events
    
    async def fetch_seatgeek_events(self, location: str, limit: int = 50) -> List[Dict]:
        """
        Obtiene eventos de SeatGeek
        """
        if not self.apis['seatgeek']['enabled']:
            return []
        
        events = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.apis['seatgeek']['base_url']}/events"
                params = {
                    'client_id': self.apis['seatgeek']['client_id'],
                    'client_secret': self.apis['seatgeek']['client_secret'],
                    'q': location,
                    'per_page': limit,
                    'type': 'concert,sports,theater'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for event in data.get('events', []):
                            normalized = self._normalize_seatgeek_event(event)
                            events.append(normalized)
                        
                        logger.info(f"✅ SeatGeek: {len(events)} eventos en {location}")
                    else:
                        logger.error(f"Error SeatGeek API: {response.status}")
        
        except Exception as e:
            logger.error(f"Error fetching SeatGeek events: {e}")
        
        return events
    
    def _normalize_ticketmaster_event(self, event: Dict) -> Dict:
        """
        Normaliza evento de Ticketmaster al formato universal
        """
        try:
            # Extraer venue
            venues = event.get('_embedded', {}).get('venues', [])
            venue = venues[0] if venues else {}
            
            # Extraer precio
            price_ranges = event.get('priceRanges', [])
            min_price = price_ranges[0].get('min', 0) if price_ranges else 0
            
            return {
                'title': event.get('name', 'Sin título'),
                'description': event.get('info', ''),
                'start_datetime': event.get('dates', {}).get('start', {}).get('dateTime'),
                'end_datetime': None,
                'venue_name': venue.get('name', ''),
                'venue_address': venue.get('address', {}).get('line1', ''),
                'neighborhood': venue.get('city', {}).get('name', ''),
                'latitude': float(venue.get('location', {}).get('latitude', 0)),
                'longitude': float(venue.get('location', {}).get('longitude', 0)),
                'category': self._map_ticketmaster_category(event.get('classifications', [])),
                'price': min_price,
                'currency': price_ranges[0].get('currency', 'USD') if price_ranges else 'USD',
                'is_free': min_price == 0,
                'source': 'ticketmaster',
                'source_id': event.get('id'),
                'event_url': event.get('url'),
                'image_url': self._get_best_image(event.get('images', [])),
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizando evento Ticketmaster: {e}")
            return {}
    
    def _normalize_bandsintown_event(self, event: Dict) -> Dict:
        """
        Normaliza evento de Bandsintown
        """
        try:
            venue = event.get('venue', {})
            
            return {
                'title': event.get('title') or f"{event.get('lineup', ['Artista'])[0]} en vivo",
                'description': event.get('description', ''),
                'start_datetime': event.get('datetime'),
                'venue_name': venue.get('name', ''),
                'venue_address': f"{venue.get('street_address', '')} {venue.get('city', '')}",
                'neighborhood': venue.get('city', ''),
                'latitude': float(venue.get('latitude', 0)),
                'longitude': float(venue.get('longitude', 0)),
                'category': 'music',
                'price': 0,
                'is_free': event.get('offers', [{}])[0].get('type') == 'Free' if event.get('offers') else False,
                'source': 'bandsintown',
                'source_id': event.get('id'),
                'event_url': event.get('url'),
                'image_url': event.get('artist', {}).get('image_url'),
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizando evento Bandsintown: {e}")
            return {}
    
    def _normalize_seatgeek_event(self, event: Dict) -> Dict:
        """
        Normaliza evento de SeatGeek
        """
        try:
            venue = event.get('venue', {})
            
            return {
                'title': event.get('title', 'Sin título'),
                'description': event.get('description', ''),
                'start_datetime': event.get('datetime_utc'),
                'venue_name': venue.get('name', ''),
                'venue_address': venue.get('address', ''),
                'neighborhood': venue.get('city', ''),
                'latitude': float(venue.get('location', {}).get('lat', 0)),
                'longitude': float(venue.get('location', {}).get('lon', 0)),
                'category': event.get('type', 'general'),
                'price': event.get('stats', {}).get('lowest_price', 0),
                'currency': 'USD',
                'is_free': False,
                'source': 'seatgeek',
                'source_id': str(event.get('id')),
                'event_url': event.get('url'),
                'image_url': event.get('performers', [{}])[0].get('image') if event.get('performers') else None,
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizando evento SeatGeek: {e}")
            return {}
    
    def _get_country_code(self, location: str) -> str:
        """
        Obtiene el código de país para la ubicación
        """
        country_codes = {
            'argentina': 'AR',
            'buenos aires': 'AR',
            'méxico': 'MX',
            'ciudad de méxico': 'MX',
            'brasil': 'BR',
            'são paulo': 'BR',
            'chile': 'CL',
            'santiago': 'CL',
            'colombia': 'CO',
            'bogotá': 'CO',
            'perú': 'PE',
            'lima': 'PE',
            'uruguay': 'UY',
            'montevideo': 'UY'
        }
        
        location_lower = location.lower()
        for key, code in country_codes.items():
            if key in location_lower:
                return code
        
        return 'AR'  # Default Argentina
    
    def _map_ticketmaster_category(self, classifications: List[Dict]) -> str:
        """
        Mapea categorías de Ticketmaster
        """
        if not classifications:
            return 'general'
        
        segment = classifications[0].get('segment', {}).get('name', '').lower()
        
        category_map = {
            'music': 'music',
            'sports': 'sports',
            'arts': 'art',
            'theatre': 'theater',
            'film': 'film',
            'family': 'family'
        }
        
        for key, value in category_map.items():
            if key in segment:
                return value
        
        return 'general'
    
    def _get_best_image(self, images: List[Dict]) -> Optional[str]:
        """
        Obtiene la mejor imagen disponible
        """
        if not images:
            return None
        
        # Preferir imágenes de alta resolución
        for img in images:
            if img.get('width', 0) >= 1024:
                return img.get('url')
        
        # Si no hay alta resolución, tomar la primera
        return images[0].get('url') if images else None


# Función de prueba
async def test_apis():
    """
    Prueba todas las APIs configuradas
    """
    manager = APIManager()
    
    print("📡 Estado de las APIs:")
    status = manager.get_status()
    print(f"  Total: {status['total_apis']}")
    print(f"  Habilitadas: {status['enabled_apis']}")
    
    for name, api_status in status['apis'].items():
        emoji = '✅' if api_status['enabled'] else '❌'
        print(f"  {emoji} {name}: {'Configurada' if api_status['enabled'] else 'No configurada'}")
    
    # Probar APIs habilitadas
    print("\n🔍 Probando APIs habilitadas...")
    
    # Ticketmaster
    if manager.apis['ticketmaster']['enabled']:
        events = await manager.fetch_ticketmaster_events("Buenos Aires", limit=5)
        print(f"\nTicketmaster: {len(events)} eventos encontrados")
        for event in events[:2]:
            print(f"  - {event['title']}")
            print(f"    📍 {event['venue_name']}")
    
    # Bandsintown
    if manager.apis['bandsintown']['enabled']:
        events = await manager.fetch_bandsintown_events(location="Buenos Aires")
        print(f"\nBandsintown: {len(events)} eventos encontrados")
        for event in events[:2]:
            print(f"  - {event['title']}")
    
    # SeatGeek
    if manager.apis['seatgeek']['enabled']:
        events = await manager.fetch_seatgeek_events("Buenos Aires", limit=5)
        print(f"\nSeatGeek: {len(events)} eventos encontrados")
        for event in events[:2]:
            print(f"  - {event['title']}")


if __name__ == "__main__":
    asyncio.run(test_apis())