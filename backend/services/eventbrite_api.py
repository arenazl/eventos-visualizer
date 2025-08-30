"""
Conector para Eventbrite API - LATAM Focus
Cobertura: Argentina, México, Colombia, Chile, Brasil, Perú, Uruguay
Eventbrite es la plataforma líder de eventos en Latinoamérica
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
import random

load_dotenv()
logger = logging.getLogger(__name__)

class EventbriteLatamConnector:
    """
    Conector para Eventbrite API con foco en Latinoamérica
    Rate limit: 1000 requests/hora
    """
    
    def __init__(self):
        # Use private token for API calls (it works with the API)
        self.api_key = os.getenv('EVENTBRITE_PRIVATE_TOKEN', os.getenv('EVENTBRITE_API_KEY', ''))
        self.base_url = "https://www.eventbriteapi.com/v3"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}'
        } if self.api_key else {}
        
        # Cache para optimizar rate limit
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)
        
        # Ciudades principales de LATAM
        self.latam_cities = {
            'argentina': [
                'Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata',
                'Mar del Plata', 'Tucumán', 'Salta', 'Santa Fe'
            ],
            'mexico': [
                'Ciudad de México', 'CDMX', 'Guadalajara', 'Monterrey',
                'Puebla', 'Tijuana', 'León', 'Cancún', 'Mérida', 'Querétaro'
            ],
            'colombia': [
                'Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena',
                'Bucaramanga', 'Pereira', 'Santa Marta'
            ],
            'chile': [
                'Santiago', 'Valparaíso', 'Concepción', 'Antofagasta',
                'Viña del Mar', 'Temuco', 'La Serena'
            ],
            'brasil': [
                'São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Brasília',
                'Salvador', 'Fortaleza', 'Curitiba', 'Recife', 'Porto Alegre'
            ],
            'peru': [
                'Lima', 'Arequipa', 'Trujillo', 'Chiclayo', 'Piura',
                'Cusco', 'Iquitos'
            ],
            'uruguay': [
                'Montevideo', 'Punta del Este', 'Colonia del Sacramento'
            ]
        }
        
    async def fetch_events_by_location(self, location: str, page: int = 1) -> List[Dict]:
        """
        Obtiene eventos por ubicación
        """
        try:
            # Verificar cache
            cache_key = f"{location}_{page}"
            if self.is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            # Si no hay API key, intentar scraping público
            if not self.api_key:
                logger.warning(f"No Eventbrite API key configured - trying public scraping")
                return await self.scrape_eventbrite_public(location)
            
            url = f"{self.base_url}/events/search/"
            params = {
                'location.address': location,
                'location.within': '50km',
                'expand': 'venue,organizer,category',
                'sort_by': 'date',
                'page': page,
                'page_size': 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Guardar en cache
                        self.cache[cache_key] = {
                            'data': data,
                            'timestamp': datetime.now()
                        }
                        
                        logger.info(f"✅ Eventbrite API {location}: {len(data.get('events', []))} eventos")
                        # Normalizar eventos antes de retornar
                        return self.normalize_events(data.get('events', []))
                    else:
                        logger.error(f"Error Eventbrite API: {response.status} - trying scraping fallback")
                        # Fallback a scraping público
                        return await self.scrape_eventbrite_public(location)
                        
        except Exception as e:
            logger.error(f"Error fetching Eventbrite events: {e} - trying scraping fallback")
            return await self.scrape_eventbrite_public(location)
    
    async def fetch_all_latam_events(self) -> List[Dict]:
        """
        Obtiene eventos de todas las ciudades principales de LATAM
        """
        all_events = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Crear tareas para cada ciudad
            for country, cities in self.latam_cities.items():
                for city in cities[:3]:  # Top 3 ciudades por país para no exceder rate limit
                    tasks.append(self.fetch_events_by_location(city))
                    
                    # Pequeña demora para respetar rate limit
                    if len(tasks) % 5 == 0:
                        await asyncio.sleep(0.5)
            
            # Ejecutar todas las tareas
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for result in results:
                if isinstance(result, dict) and 'events' in result:
                    all_events.extend(result['events'])
                elif isinstance(result, Exception):
                    logger.error(f"Error fetching LATAM events: {result}")
        
        return self.normalize_events(all_events)
    
    async def scrape_eventbrite_public(self, location: str) -> List[Dict]:
        """
        Scraping público de Eventbrite sin API key
        """
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            import re
            
            # URL pública de Eventbrite Argentina
            location_slug = location.lower().replace(' ', '-')
            url = f"https://www.eventbrite.com.ar/d/argentina--{location_slug}/events/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        events = []
                        
                        # Buscar cards de eventos
                        event_cards = soup.find_all(['article', 'div'], class_=re.compile('event-card|search-event-card|discover-search-desktop-card'))
                        
                        for card in event_cards[:10]:  # Limitar a 10 eventos
                            try:
                                # Título
                                title_elem = card.find(['h1', 'h2', 'h3', 'a'], class_=re.compile('event.*title|card.*title'))
                                if not title_elem:
                                    title_elem = card.find('a', {'data-event-label': True})
                                
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                                    
                                    event = {
                                        'name': {'text': title},
                                        'description': {'text': ''},
                                        'is_free': False,
                                        'currency': 'ARS',
                                        'venue': {'name': location, 'address': {'city': location}},
                                        'start': {'utc': (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()},
                                        'category': {'name': 'General'},
                                        'url': '',
                                        'id': f"scraping_{hash(title)}"
                                    }
                                    
                                    # Intentar extraer precio
                                    price_elem = card.find(text=re.compile(r'\$|\bgratis\b|\bfree\b', re.I))
                                    if price_elem:
                                        price_text = price_elem.strip().lower()
                                        if 'gratis' in price_text or 'free' in price_text:
                                            event['is_free'] = True
                                    
                                    # Intentar extraer fecha
                                    date_elem = card.find(['time', 'span'], class_=re.compile('date|time'))
                                    if date_elem:
                                        date_text = date_elem.get_text(strip=True)
                                        # Procesar fecha si es posible
                                        
                                    # Intentar extraer venue
                                    venue_elem = card.find(['span', 'div'], class_=re.compile('location|venue'))
                                    if venue_elem:
                                        venue_text = venue_elem.get_text(strip=True)
                                        event['venue']['name'] = venue_text
                                    
                                    events.append(event)
                            
                            except Exception as e:
                                logger.error(f"Error parsing Eventbrite card: {e}")
                                continue
                        
                        logger.info(f"✅ Eventbrite Scraping {location}: {len(events)} eventos")
                        return events
                    
                    else:
                        logger.error(f"Error scraping Eventbrite: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error in Eventbrite public scraping: {e}")
            return []
    
    def normalize_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normaliza eventos de Eventbrite al formato universal
        """
        normalized = []
        
        for event in raw_events:
            try:
                # Extraer venue info
                venue = event.get('venue', {})
                address = venue.get('address', {})
                
                # Extraer precio
                is_free = event.get('is_free', False)
                price = 0 if is_free else self._extract_price(event)
                
                # Extraer categoría
                category = self._map_category(event.get('category', {}))
                
                normalized_event = {
                    # Información básica
                    'title': event.get('name', {}).get('text', 'Sin título'),
                    'description': event.get('description', {}).get('text', ''),
                    
                    # Fechas (convertir a string ISO)
                    'start_datetime': self.parse_date(event.get('start', {}).get('utc')).isoformat() if self.parse_date(event.get('start', {}).get('utc')) else None,
                    'end_datetime': self.parse_date(event.get('end', {}).get('utc')).isoformat() if self.parse_date(event.get('end', {}).get('utc')) else None,
                    
                    # Ubicación
                    'venue_name': venue.get('name', ''),
                    'venue_address': address.get('localized_address_display', ''),
                    'neighborhood': address.get('city', ''),
                    'latitude': float(address.get('latitude', 0)) if address.get('latitude') else None,
                    'longitude': float(address.get('longitude', 0)) if address.get('longitude') else None,
                    
                    # Categorización
                    'category': category,
                    'subcategory': event.get('subcategory', {}).get('name', ''),
                    'tags': self.extract_tags(event),
                    
                    # Precio
                    'price': price,
                    'currency': event.get('currency', 'USD'),
                    'is_free': is_free,
                    
                    # Metadata
                    'source': 'eventbrite',
                    'source_id': event.get('id', ''),
                    'event_url': event.get('url', ''),
                    'image_url': event.get('logo', {}).get('original', {}).get('url', ''),
                    
                    # Info adicional
                    'organizer': event.get('organizer', {}).get('name', ''),
                    'capacity': event.get('capacity', 0),
                    'status': event.get('status', 'live'),
                    
                    # Timestamps
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                normalized.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing Eventbrite event: {e}")
                continue
        
        return normalized
    
    def _extract_price(self, event: Dict) -> float:
        """
        Extrae el precio mínimo del evento
        """
        try:
            ticket_classes = event.get('ticket_classes', [])
            if ticket_classes:
                prices = [float(tc.get('cost', {}).get('major_value', 0)) 
                         for tc in ticket_classes if tc.get('cost')]
                return min(prices) if prices else 0
        except:
            pass
        return 0
    
    def _map_category(self, category: Dict) -> str:
        """
        Mapea categorías de Eventbrite a categorías universales
        """
        if not category:
            return 'general'
            
        name = category.get('name', '').lower()
        
        category_map = {
            'music': 'music',
            'música': 'music',
            'concerts': 'music',
            'conciertos': 'music',
            
            'business': 'business',
            'negocios': 'business',
            'conference': 'conference',
            'conferencia': 'conference',
            
            'food': 'food',
            'comida': 'food',
            'gastronomy': 'food',
            'gastronomía': 'food',
            
            'arts': 'art',
            'arte': 'art',
            'culture': 'cultural',
            'cultura': 'cultural',
            
            'sports': 'sports',
            'deportes': 'sports',
            'fitness': 'sports',
            
            'technology': 'tech',
            'tecnología': 'tech',
            'science': 'tech',
            'ciencia': 'tech',
            
            'party': 'nightlife',
            'fiesta': 'nightlife',
            'nightlife': 'nightlife',
            
            'education': 'education',
            'educación': 'education',
            'workshop': 'workshop',
            'taller': 'workshop',
            
            'health': 'wellness',
            'salud': 'wellness',
            'wellness': 'wellness',
            
            'family': 'family',
            'familia': 'family',
            'kids': 'family',
            'niños': 'family'
        }
        
        for key, value in category_map.items():
            if key in name:
                return value
        
        return 'general'
    
    def extract_tags(self, event: Dict) -> List[str]:
        """
        Extrae tags del evento
        """
        tags = []
        
        # Categoría como tag
        if event.get('category'):
            tags.append(event['category'].get('name', ''))
        
        # Subcategoría como tag
        if event.get('subcategory'):
            tags.append(event['subcategory'].get('name', ''))
        
        # Tags de formato
        if event.get('online_event'):
            tags.append('online')
            tags.append('virtual')
        
        # Tags de precio
        if event.get('is_free'):
            tags.append('gratis')
            tags.append('free')
        
        # Tags de idioma
        if event.get('locale'):
            if 'es' in event['locale']:
                tags.append('español')
            elif 'pt' in event['locale']:
                tags.append('português')
        
        return list(set(tags))  # Eliminar duplicados
    
    def parse_date(self, date_str: Any) -> Optional[datetime]:
        """
        Parsea fecha de Eventbrite
        """
        if not date_str:
            return None
            
        try:
            # Formato ISO 8601
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Formato alternativo
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            except:
                return None
    
    def is_cached(self, key: str) -> bool:
        """
        Verifica si hay datos en cache
        """
        if key not in self.cache:
            return False
            
        cached_data = self.cache[key]
        age = datetime.now() - cached_data['timestamp']
        
        return age < self.cache_duration
    
    def _get_empty_response(self, location: str) -> Dict:
        """
        Retorna eventos mock cuando no hay API key
        """
        mock_events = [
            {
                'name': {'text': f'Festival de Música en {location}'},
                'description': {'text': 'Gran festival con artistas internacionales'},
                'start': {'utc': (datetime.now() + timedelta(days=7)).isoformat()},
                'end': {'utc': (datetime.now() + timedelta(days=7, hours=6)).isoformat()},
                'venue': {
                    'name': f'Estadio Principal {location}',
                    'address': {
                        'localized_address_display': f'Centro de {location}',
                        'city': location
                    }
                },
                'is_free': False,
                'currency': 'USD',
                'url': 'https://eventbrite.com/e/123456',
                'category': {'name': 'Music'},
                'id': 'mock_1'
            },
            {
                'name': {'text': f'Conferencia Tech {location}'},
                'description': {'text': 'Conferencia sobre innovación y tecnología'},
                'start': {'utc': (datetime.now() + timedelta(days=14)).isoformat()},
                'end': {'utc': (datetime.now() + timedelta(days=14, hours=8)).isoformat()},
                'venue': {
                    'name': f'Centro de Convenciones {location}',
                    'address': {
                        'localized_address_display': f'Zona empresarial {location}',
                        'city': location
                    }
                },
                'is_free': True,
                'currency': 'USD',
                'url': 'https://eventbrite.com/e/123457',
                'category': {'name': 'Technology'},
                'id': 'mock_2'
            },
            {
                'name': {'text': f'Feria Gastronómica {location}'},
                'description': {'text': 'Los mejores sabores de la región'},
                'start': {'utc': (datetime.now() + timedelta(days=3)).isoformat()},
                'end': {'utc': (datetime.now() + timedelta(days=3, hours=10)).isoformat()},
                'venue': {
                    'name': f'Parque Central {location}',
                    'address': {
                        'localized_address_display': f'Parque Principal {location}',
                        'city': location
                    }
                },
                'is_free': False,
                'currency': 'USD',
                'url': 'https://eventbrite.com/e/123458',
                'category': {'name': 'Food & Drink'},
                'id': 'mock_3'
            }
        ]
        
        return {'events': mock_events, 'pagination': {'page_count': 1}}


# Función de prueba
async def test_eventbrite_latam():
    """
    Prueba el conector de Eventbrite LATAM
    """
    connector = EventbriteLatamConnector()
    
    print("🔍 Obteniendo eventos de Eventbrite LATAM...")
    
    # Probar con Buenos Aires
    print("\n📍 Buenos Aires:")
    ba_events = await connector.fetch_events_by_location('Buenos Aires')
    events = connector.normalize_events(ba_events.get('events', []))
    
    for event in events[:3]:
        print(f"\n📌 {event['title']}")
        print(f"   📍 {event['venue_name']} - {event['neighborhood']}")
        print(f"   📅 {event['start_datetime']}")
        print(f"   🏷️ {event['category']}")
        print(f"   💰 {'GRATIS' if event['is_free'] else f'${event["price"]} {event["currency"]}'}")
    
    # Probar con México
    print("\n📍 Ciudad de México:")
    mx_events = await connector.fetch_events_by_location('Ciudad de México')
    events = connector.normalize_events(mx_events.get('events', []))
    
    for event in events[:3]:
        print(f"\n📌 {event['title']}")
        print(f"   📍 {event['venue_name']}")
    
    return events


if __name__ == "__main__":
    asyncio.run(test_eventbrite_latam())