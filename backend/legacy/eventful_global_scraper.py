"""
🎪 Eventful Global API Scraper
Global events discovery using Eventful API
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

class EventfulGlobalScraper(BaseGlobalScraper):
    """
    Global scraper para Eventful API
    Cobertura: Global (principalmente US, Canada, UK, Australia)
    """
    
    def __init__(self):
        self.api_key = os.getenv("EVENTFUL_API_KEY")
        self.base_url = "http://api.eventful.com/json/events/search"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "EventosApp/1.0 (eventos-visualizer)"
        }
        
        # Category mapping from Eventful to our standard
        self.category_mapping = {
            "music": "music",
            "concerts": "music",
            "sports": "sports",
            "comedy": "cultural",
            "theatre": "cultural",
            "performing_arts": "cultural",
            "art": "cultural",
            "festivals_parades": "cultural",
            "family_fun_kids": "family",
            "food": "food",
            "nightlife": "nightlife",
            "business": "tech",
            "technology": "tech",
            "conference": "tech"
        }

    async def fetch_events(self, location: str, country: str = None) -> Dict[str, Any]:
        """
        Fetch events from Eventful API
        """
        if not self.api_key:
            logger.warning("⚠️ Eventful API key not found in .env")
            return {"source": "Eventful", "events": [], "total": 0, "status": "no_api_key"}
        
        try:
            # Preparar parámetros de búsqueda
            params = self._build_search_params(location)
            
            # Hacer request a la API
            events = await self._fetch_from_api(params)
            
            logger.info(f"✅ Eventful: {len(events)} eventos para {location}")
            
            return {
                "source": "Eventful Global API",
                "location": location,
                "events": events,
                "total": len(events),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Eventful error for {location}: {e}")
            return {"source": "Eventful", "events": [], "total": 0, "status": "error", "error": str(e)}

    def _build_search_params(self, location: str) -> Dict:
        """
        Construir parámetros de búsqueda para Eventful API
        """
        # Fecha range - próximos 60 días
        date_start = datetime.now().strftime("%Y%m%d00")
        date_end = (datetime.now() + timedelta(days=60)).strftime("%Y%m%d00")
        
        params = {
            "app_key": self.api_key,
            "location": location,
            "date": f"{date_start}-{date_end}",
            "page_size": 50,  # Máximo por request
            "sort_order": "date",
            "sort_direction": "ascending",
            "include": "categories,links,price"  # Incluir información adicional
        }
        
        return params

    async def _fetch_from_api(self, params: Dict) -> List[Dict[str, Any]]:
        """
        Hacer request a Eventful API
        """
        events = []
        
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout, headers=self.headers) as session:
                
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "events" in data and data["events"] and "event" in data["events"]:
                            api_events = data["events"]["event"]
                            
                            # Eventful puede devolver un solo evento como dict o múltiples como lista
                            if isinstance(api_events, dict):
                                api_events = [api_events]
                            
                            for event in api_events:
                                processed_event = self._process_event(event)
                                if processed_event:
                                    events.append(processed_event)
                    
                    elif response.status == 401:
                        logger.error("❌ Eventful API: Invalid API key")
                    elif response.status == 403:
                        logger.error("❌ Eventful API: Access denied")
                    elif response.status == 429:
                        logger.warning("⚠️ Eventful API: Rate limit exceeded")
                    else:
                        logger.warning(f"⚠️ Eventful API HTTP {response.status}")
        
        except Exception as e:
            logger.error(f"❌ Eventful API request failed: {e}")
        
        return events

    def _process_event(self, api_event: Dict) -> Optional[Dict[str, Any]]:
        """
        Procesar evento de Eventful API al formato estándar
        """
        try:
            # Datos básicos
            title = api_event.get("title", "")
            if not title:
                return None
            
            # Descripción
            description = api_event.get("description", "")
            if not description:
                description = f"Evento en {api_event.get('city_name', 'la ciudad')}"
            
            # Fecha y hora
            start_datetime = None
            start_time = api_event.get("start_time")
            if start_time:
                try:
                    start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        start_datetime = datetime.strptime(start_time.split(" ")[0], "%Y-%m-%d")
                    except:
                        start_datetime = datetime.now() + timedelta(days=7)
            else:
                start_datetime = datetime.now() + timedelta(days=7)
            
            # Venue información
            venue_name = api_event.get("venue_name", "")
            venue_address = ""
            
            if api_event.get("venue_address"):
                venue_address = api_event["venue_address"]
            elif api_event.get("city_name"):
                venue_address = f"{api_event['city_name']}"
            
            # Coordenadas
            latitude = None
            longitude = None
            try:
                if api_event.get("latitude"):
                    latitude = float(api_event["latitude"])
                if api_event.get("longitude"):
                    longitude = float(api_event["longitude"])
            except:
                pass
            
            # Categoría
            category = "general"
            if "categories" in api_event and api_event["categories"]:
                if "category" in api_event["categories"]:
                    categories = api_event["categories"]["category"]
                    if isinstance(categories, list) and categories:
                        category_id = categories[0].get("id", "").lower()
                    elif isinstance(categories, dict):
                        category_id = categories.get("id", "").lower()
                    else:
                        category_id = ""
                    
                    category = self.category_mapping.get(category_id, "general")
            
            # Precio (Eventful no siempre tiene precios precisos)
            price = None
            currency = "USD"  # Default
            is_free = False
            
            # Eventful a veces incluye "Free" en el título o descripción
            if any(keyword in (title + " " + description).lower() for keyword in ["free", "gratis", "gratuito"]):
                is_free = True
                price = 0
            
            # Imagen
            image_url = ""
            if "images" in api_event and api_event["images"]:
                if "image" in api_event["images"]:
                    images = api_event["images"]["image"]
                    if isinstance(images, list) and images:
                        # Buscar imagen más grande
                        for img in images:
                            if img.get("width", 0) >= 300:  # Imagen decente
                                image_url = img.get("url", "")
                                break
                        if not image_url and images:
                            image_url = images[0].get("url", "")
                    elif isinstance(images, dict):
                        image_url = images.get("url", "")
            
            # URL del evento
            event_url = api_event.get("url", "")
            
            return {
                "title": title.strip()[:200],
                "description": description.strip()[:300],
                "start_datetime": start_datetime.isoformat() if start_datetime else datetime.now().isoformat(),
                "venue_name": venue_name or "Venue TBD",
                "venue_address": venue_address,
                "category": category,
                "price": price,
                "currency": currency,
                "is_free": is_free,
                "image_url": image_url,
                "event_url": event_url,
                "latitude": latitude,
                "longitude": longitude,
                "external_id": api_event.get("id", ""),
                "source": "eventful",
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error processing Eventful event: {e}")
            return None

# Función de testing
async def test_eventful_scraper():
    """
    Test function para Eventful scraper
    """
    scraper = EventfulGlobalScraper()
    
    test_locations = ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco"]
    
    for location in test_locations:
        print(f"\n🎪 Testing Eventful for: {location}")
        result = await scraper.fetch_events(location)
        
        print(f"   Status: {result['status']}")
        print(f"   Events: {result['total']}")
        
        if result['events']:
            for event in result['events'][:3]:  # Mostrar primeros 3
                print(f"   🎉 {event['title']} - {event['venue_name']} ({event['category']})")

if __name__ == "__main__":
    asyncio.run(test_eventful_scraper())