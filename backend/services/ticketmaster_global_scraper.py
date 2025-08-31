"""
Ticketmaster Discovery API - Global Events
API oficial para eventos globales de calidad
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os
from .city_scraper_factory import BaseGlobalScraper

logger = logging.getLogger(__name__)

class TicketmasterGlobalScraper(BaseGlobalScraper):
    """
    Scraper usando Ticketmaster Discovery API v2
    Coverage: US, Canada, Mexico, Australia, UK, Europe
    """
    
    def __init__(self):
        self.base_url = "https://app.ticketmaster.com/discovery/v2"
        self.api_key = os.getenv("TICKETMASTER_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️ TICKETMASTER_API_KEY not set - using demo mode")
            self.api_key = "DEMO_KEY"  # Para testing
        
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'EventosApp/1.0'
        }
        
        # Country codes supported by Ticketmaster
        self.supported_countries = {
            "España": "ES",
            "Barcelona": "ES", 
            "Madrid": "ES",
            "Francia": "FR",
            "Paris": "FR",
            "México": "MX",
            "Mexico City": "MX",
            "Estados Unidos": "US",
            "Canadá": "CA",
            "Australia": "AU",
            "Reino Unido": "GB",
            "Londres": "GB"
        }
        
        # Classification mapping for better categorization
        self.classifications = {
            "music": "music",
            "sports": "sports", 
            "arts": "arts",
            "film": "film",
            "miscellaneous": "miscellaneous"
        }

    async def fetch_events(self, location: str, country: str = None) -> Dict[str, Any]:
        """
        Método principal requerido por BaseGlobalScraper
        """
        try:
            events = await self.search_events_by_city(location, limit=50)
            
            return {
                "source": "Ticketmaster Global",
                "location": location,
                "events": events,
                "total": len(events),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Ticketmaster fetch_events error for {location}: {e}")
            return {
                "source": "Ticketmaster Global",
                "location": location,
                "events": [],
                "total": 0,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def search_events_by_city(self, city: str, limit: int = 20) -> List[Dict]:
        """
        Busca eventos por ciudad usando Ticketmaster API
        """
        if not self.api_key or self.api_key == "DEMO_KEY":
            logger.info("🎫 Ticketmaster: Demo mode - returning sample events")
            return self._get_demo_events(city)
        
        country_code = self._get_country_code(city)
        
        params = {
            'apikey': self.api_key,
            'city': city,
            'size': min(limit, 200),  # Max 200 per request
            'sort': 'date,asc'
        }
        
        if country_code:
            params['countryCode'] = country_code
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/events.json"
                async with session.get(url, params=params, headers=self.headers) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        events = self._parse_ticketmaster_events(data, city)
                        logger.info(f"✅ Ticketmaster {city}: {len(events)} eventos oficiales")
                        return events
                    elif response.status == 401:
                        logger.error("❌ Ticketmaster: Invalid API key")
                        return []
                    else:
                        logger.error(f"❌ Ticketmaster API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ Ticketmaster error: {e}")
            return []

    async def search_events_by_category(self, city: str, category: str, limit: int = 15) -> List[Dict]:
        """
        Busca eventos por ciudad y categoría
        """
        if not self.api_key or self.api_key == "DEMO_KEY":
            return self._get_demo_events(city, category)
        
        country_code = self._get_country_code(city)
        classification = self.classifications.get(category.lower(), category)
        
        params = {
            'apikey': self.api_key,
            'city': city,
            'classificationName': classification,
            'size': min(limit, 200),
            'sort': 'date,asc'
        }
        
        if country_code:
            params['countryCode'] = country_code
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/events.json"
                async with session.get(url, params=params, headers=self.headers) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        events = self._parse_ticketmaster_events(data, city)
                        logger.info(f"✅ Ticketmaster {city} ({category}): {len(events)} eventos")
                        return events
                    else:
                        logger.error(f"❌ Ticketmaster category search error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ Ticketmaster category error: {e}")
            return []

    def _parse_ticketmaster_events(self, data: Dict, city: str) -> List[Dict]:
        """
        Parsea la respuesta de Ticketmaster a formato estándar
        """
        events = []
        
        if '_embedded' not in data or 'events' not in data['_embedded']:
            return events
        
        for tm_event in data['_embedded']['events']:
            try:
                # Parse básico
                title = tm_event.get('name', 'Evento Ticketmaster')
                description = tm_event.get('info', f"Evento oficial en {city}")
                
                # Fechas
                start_date = None
                if 'dates' in tm_event and 'start' in tm_event['dates']:
                    date_info = tm_event['dates']['start']
                    if 'dateTime' in date_info:
                        start_date = date_info['dateTime']
                    elif 'localDate' in date_info:
                        start_date = f"{date_info['localDate']}T20:00:00"
                
                # Venue
                venue_name = city
                venue_address = f"{city}"
                latitude = None
                longitude = None
                
                if '_embedded' in tm_event and 'venues' in tm_event['_embedded']:
                    venue = tm_event['_embedded']['venues'][0]
                    venue_name = venue.get('name', city)
                    
                    if 'address' in venue:
                        venue_address = f"{venue['address'].get('line1', '')}, {city}"
                    
                    if 'location' in venue:
                        latitude = float(venue['location'].get('latitude', 0))
                        longitude = float(venue['location'].get('longitude', 0))
                
                # Categoría
                category = 'general'
                if 'classifications' in tm_event and tm_event['classifications']:
                    classification = tm_event['classifications'][0]
                    if 'segment' in classification:
                        category = classification['segment']['name'].lower()
                
                # Precios
                price = 0
                currency = 'EUR' if city in ['Barcelona', 'Madrid', 'Paris'] else 'USD'
                is_free = False
                
                if 'priceRanges' in tm_event and tm_event['priceRanges']:
                    price_range = tm_event['priceRanges'][0]
                    price = price_range.get('min', 0)
                    currency = price_range.get('currency', currency)
                
                # Imagen
                image_url = 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4'
                if 'images' in tm_event and tm_event['images']:
                    image_url = tm_event['images'][0].get('url', image_url)
                
                event = {
                    'title': title[:150],
                    'description': description[:300],
                    'venue_name': venue_name,
                    'venue_address': venue_address,
                    'start_datetime': start_date or datetime.now().isoformat(),
                    'category': category,
                    'price': price,
                    'currency': currency,
                    'is_free': is_free,
                    'source': 'ticketmaster_official',
                    'source_api': 'ticketmaster',
                    'latitude': latitude,
                    'longitude': longitude,
                    'image_url': image_url,
                    'status': 'live',
                    'city': city,
                    'external_url': tm_event.get('url', ''),
                    'external_id': tm_event.get('id', '')
                }
                
                events.append(event)
                
            except Exception as e:
                logger.debug(f"Error parsing Ticketmaster event: {e}")
                continue
        
        return events

    def _get_country_code(self, city: str) -> Optional[str]:
        """
        Obtiene el código de país para una ciudad
        """
        return self.supported_countries.get(city)

    def _get_demo_events(self, city: str, category: str = None) -> List[Dict]:
        """
        Eventos demo cuando no hay API key
        """
        base_events = {
            'Barcelona': [
                {
                    'title': 'FC Barcelona vs Real Madrid - El Clásico',
                    'venue_name': 'Camp Nou',
                    'category': 'sports',
                    'price': 85,
                    'currency': 'EUR'
                },
                {
                    'title': 'Concierto Rosalía - World Tour',
                    'venue_name': 'Palau de la Música Catalana',
                    'category': 'music',
                    'price': 65,
                    'currency': 'EUR'
                },
                {
                    'title': 'Primavera Sound Festival',
                    'venue_name': 'Parc del Fòrum',
                    'category': 'music',
                    'price': 250,
                    'currency': 'EUR'
                }
            ],
            'Paris': [
                {
                    'title': 'Paris Saint-Germain vs Manchester City',
                    'venue_name': 'Parc des Princes',
                    'category': 'sports',
                    'price': 95,
                    'currency': 'EUR'
                },
                {
                    'title': 'Daft Punk Tribute Show',
                    'venue_name': 'Olympia',
                    'category': 'music',
                    'price': 75,
                    'currency': 'EUR'
                }
            ],
            'Madrid': [
                {
                    'title': 'Real Madrid vs Barcelona',
                    'venue_name': 'Santiago Bernabéu',
                    'category': 'sports',
                    'price': 120,
                    'currency': 'EUR'
                },
                {
                    'title': 'Alejandro Sanz - Tour 2025',
                    'venue_name': 'WiZink Center',
                    'category': 'music',
                    'price': 55,
                    'currency': 'EUR'
                }
            ]
        }
        
        city_events = base_events.get(city, [])
        demo_events = []
        
        for i, event_template in enumerate(city_events):
            if category and event_template['category'] != category.lower():
                continue
                
            event = {
                'title': event_template['title'],
                'description': f"Evento oficial Ticketmaster en {city}",
                'venue_name': event_template['venue_name'],
                'venue_address': f"{event_template['venue_name']}, {city}",
                'start_datetime': (datetime.now()).isoformat(),
                'category': event_template['category'],
                'price': event_template['price'],
                'currency': event_template['currency'],
                'is_free': False,
                'source': 'ticketmaster_demo',
                'source_api': 'ticketmaster',
                'latitude': 41.3851 if city == 'Barcelona' else 48.8566,
                'longitude': 2.1734 if city == 'Barcelona' else 2.3522,
                'image_url': 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4',
                'status': 'live',
                'city': city
            }
            demo_events.append(event)
        
        logger.info(f"🎫 Ticketmaster DEMO {city}: {len(demo_events)} eventos")
        return demo_events


# Testing
async def test_ticketmaster_global():
    """
    Prueba el scraper global de Ticketmaster
    """
    scraper = TicketmasterGlobalScraper()
    
    print("🎫 Probando Ticketmaster Global API...")
    
    # Test diferentes ciudades
    test_cities = ['Barcelona', 'Paris', 'Madrid']
    
    for city in test_cities:
        print(f"\n🌍 Testing {city}...")
        events = await scraper.search_events_by_city(city, limit=5)
        
        print(f"   ✅ {len(events)} eventos encontrados")
        
        for event in events[:3]:
            print(f"   📌 {event['title']}")
            print(f"      📍 {event['venue_name']}")
            print(f"      💰 {event['price']} {event['currency']}")
            print(f"      🏷️ {event['category']}")

if __name__ == "__main__":
    asyncio.run(test_ticketmaster_global())