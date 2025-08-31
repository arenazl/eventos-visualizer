"""
🏟️ SeatGeek Global API Scraper
Global events and tickets using SeatGeek API
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from .city_scraper_factory import BaseGlobalScraper

logger = logging.getLogger(__name__)

class SeatGeekGlobalScraper(BaseGlobalScraper):
    """
    Global scraper para SeatGeek API
    Cobertura: Estados Unidos, Canadá, Reino Unido
    Especializado en: Sports, Concerts, Theater
    """
    
    def __init__(self):
        self.api_key = os.getenv("SEATGEEK_API_KEY")
        self.client_id = os.getenv("SEATGEEK_CLIENT_ID") 
        self.base_url = "https://api.seatgeek.com/2"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "EventosApp/1.0"
        }
        
        # Mapping de taxonomías SeatGeek a nuestras categorías
        self.taxonomy_mapping = {
            # Sports
            "sports": "sports",
            "baseball": "sports",
            "basketball": "sports", 
            "football": "sports",
            "soccer": "sports",
            "hockey": "sports",
            "tennis": "sports",
            "golf": "sports",
            "racing": "sports",
            "wrestling": "sports",
            "boxing": "sports",
            "mma": "sports",
            
            # Music & Concerts
            "concert": "music",
            "music": "music",
            "pop": "music",
            "rock": "music",
            "hip_hop": "music",
            "country": "music",
            "jazz": "music",
            "classical": "music",
            "electronic": "music",
            "reggae": "music",
            "latin": "music",
            "blues": "music",
            "folk": "music",
            
            # Theater & Arts
            "theater": "cultural",
            "broadway_tickets_national": "cultural",
            "comedy": "cultural",
            "opera": "cultural",
            "dance_performance_tour": "cultural",
            "circus": "cultural",
            
            # Family & Other
            "family": "family",
            "festival": "cultural",
            "conference": "tech",
            "convention": "tech"
        }

    async def fetch_events(self, location: str, country: str = None) -> Dict[str, Any]:
        """
        Fetch events from SeatGeek API
        """
        if not self.client_id and not self.api_key:
            logger.warning("⚠️ SeatGeek API credentials not found in .env")
            return {"source": "SeatGeek", "events": [], "total": 0, "status": "no_credentials"}
        
        try:
            # Preparar parámetros de búsqueda
            params = self._build_search_params(location)
            
            # Hacer request a la API
            events = await self._fetch_from_api(params)
            
            logger.info(f"✅ SeatGeek: {len(events)} eventos para {location}")
            
            return {
                "source": "SeatGeek Global API",
                "location": location,
                "events": events,
                "total": len(events),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ SeatGeek error for {location}: {e}")
            return {"source": "SeatGeek", "events": [], "total": 0, "status": "error", "error": str(e)}

    def _build_search_params(self, location: str) -> Dict:
        """
        Construir parámetros de búsqueda para SeatGeek API
        """
        params = {
            "per_page": 50,  # Máximo eventos por request
            "sort": "datetime_utc.asc",  # Ordenar por fecha
            "geoip": location,  # Búsqueda geográfica
            "datetime_utc.gte": datetime.now().strftime("%Y-%m-%d"),  # Eventos futuros
            "datetime_utc.lte": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")  # Próximos 3 meses
        }
        
        # Autenticación - SeatGeek puede usar client_id público
        if self.client_id:
            params["client_id"] = self.client_id
        elif self.api_key:
            params["access_token"] = self.api_key
        
        return params

    async def _fetch_from_api(self, params: Dict) -> List[Dict[str, Any]]:
        """
        Hacer request a SeatGeek API
        """
        events = []
        
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout, headers=self.headers) as session:
                url = f"{self.base_url}/events"
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "events" in data:
                            api_events = data["events"]
                            
                            for event in api_events:
                                processed_event = self._process_event(event)
                                if processed_event:
                                    events.append(processed_event)
                    
                    elif response.status == 401:
                        logger.error("❌ SeatGeek API: Invalid credentials")
                    elif response.status == 429:
                        logger.warning("⚠️ SeatGeek API: Rate limit exceeded")
                    elif response.status == 404:
                        logger.warning(f"⚠️ SeatGeek API: Location not found")
                    else:
                        logger.warning(f"⚠️ SeatGeek API HTTP {response.status}")
        
        except Exception as e:
            logger.error(f"❌ SeatGeek API request failed: {e}")
        
        return events

    def _process_event(self, api_event: Dict) -> Optional[Dict[str, Any]]:
        """
        Procesar evento de SeatGeek API al formato estándar
        """
        try:
            # Datos básicos
            title = api_event.get("title", "")
            short_title = api_event.get("short_title", title)
            
            if not title:
                return None
            
            # Usar short_title si es más descriptivo
            if short_title and len(short_title) > 5 and len(short_title) < len(title):
                title = short_title
            
            # Fecha y hora
            start_datetime = None
            datetime_utc = api_event.get("datetime_utc")
            datetime_local = api_event.get("datetime_local")
            
            # Preferir datetime_local, fallback a UTC
            datetime_str = datetime_local or datetime_utc
            if datetime_str:
                try:
                    start_datetime = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
                except:
                    try:
                        start_datetime = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
                    except:
                        start_datetime = datetime.now() + timedelta(days=7)
            
            # Venue información
            venue_data = api_event.get("venue", {})
            venue_name = venue_data.get("name", "Venue TBD")
            venue_address = ""
            latitude = None
            longitude = None
            
            if venue_data.get("address"):
                venue_address = venue_data["address"]
            if venue_data.get("extended_address"):
                venue_address += f", {venue_data['extended_address']}"
            if venue_data.get("display_location"):
                if venue_address:
                    venue_address += f", {venue_data['display_location']}"
                else:
                    venue_address = venue_data["display_location"]
            
            # Coordenadas del venue
            if venue_data.get("location"):
                try:
                    latitude = float(venue_data["location"]["lat"])
                    longitude = float(venue_data["location"]["lon"])
                except:
                    pass
            
            # Categoría basada en taxonomías
            category = "general"
            taxonomies = api_event.get("taxonomies", [])
            
            for taxonomy in taxonomies:
                taxonomy_name = taxonomy.get("name", "").lower()
                if taxonomy_name in self.taxonomy_mapping:
                    category = self.taxonomy_mapping[taxonomy_name]
                    break
            
            # Performers info para descripción
            performers = api_event.get("performers", [])
            description = ""
            
            if performers:
                performer_names = [p.get("name", "") for p in performers if p.get("name")]
                if performer_names:
                    description = f"Featuring: {', '.join(performer_names[:3])}"
                    if len(performer_names) > 3:
                        description += f" and {len(performer_names) - 3} more"
            
            if not description:
                description = f"Event at {venue_name}"
            
            # Información de precios
            price = None
            currency = "USD"  # SeatGeek principalmente USA/Canadá
            is_free = False
            
            stats = api_event.get("stats", {})
            if stats.get("lowest_price"):
                price = stats["lowest_price"]
            elif stats.get("average_price"):
                price = stats["average_price"]
            
            # SeatGeek raramente tiene eventos gratis, pero puede ocurrir
            if price == 0:
                is_free = True
            
            # Imagen del evento
            image_url = ""
            performers_images = []
            
            # Intentar obtener imagen de performers
            for performer in performers:
                if performer.get("image"):
                    performers_images.append(performer["image"])
            
            if performers_images:
                image_url = performers_images[0]  # Primera imagen de performer
            
            # URL del evento en SeatGeek
            event_url = api_event.get("url", "")
            
            return {
                "title": title.strip()[:200],
                "description": description.strip()[:300],
                "start_datetime": start_datetime.isoformat() if start_datetime else datetime.now().isoformat(),
                "venue_name": venue_name,
                "venue_address": venue_address,
                "category": category,
                "price": price,
                "currency": currency,
                "is_free": is_free,
                "image_url": image_url,
                "event_url": event_url,
                "latitude": latitude,
                "longitude": longitude,
                "external_id": str(api_event.get("id", "")),
                "source": "seatgeek",
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error processing SeatGeek event: {e}")
            return None

# Función de testing
async def test_seatgeek_scraper():
    """
    Test function para SeatGeek scraper
    """
    scraper = SeatGeekGlobalScraper()
    
    test_locations = ["New York", "Los Angeles", "Chicago", "Miami", "Boston"]
    
    for location in test_locations:
        print(f"\n🏟️ Testing SeatGeek for: {location}")
        result = await scraper.fetch_events(location)
        
        print(f"   Status: {result['status']}")
        print(f"   Events: {result['total']}")
        
        if result['events']:
            for event in result['events'][:3]:  # Mostrar primeros 3
                print(f"   🎉 {event['title']} - {event['venue_name']} ({event['category']})")
                if event.get('price'):
                    print(f"       💰 From ${event['price']}")

if __name__ == "__main__":
    asyncio.run(test_seatgeek_scraper())