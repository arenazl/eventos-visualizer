"""
📘 FACEBOOK EVENTS SCRAPER V2
Scraper para Facebook Events usando RapidAPI
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from ..base import IScraper, Event, EventCategory

class FacebookScraper(IScraper):
    """
    Scraper para Facebook Events via RapidAPI
    Documentación: https://rapidapi.com/
    """
    
    name = "facebook"
    timeout = 4
    priority = 3  # Prioridad media - API puede ser lenta
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("RAPIDAPI_KEY"))
        self.base_url = "https://facebook-scraper-api.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "facebook-scraper-api.p.rapidapi.com"
        } if self.api_key else {}
    
    async def scrape(self, location: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Busca eventos en Facebook para una ubicación
        
        Formato típico de respuesta de Facebook RapidAPI:
        {
            "data": [
                {
                    "id": "123456789",
                    "name": "Event Name",
                    "description": "Event description",
                    "start_time": "2024-12-25T19:00:00-0300",
                    "end_time": "2024-12-25T23:00:00-0300",
                    "place": {
                        "name": "Venue Name",
                        "location": {
                            "city": "Buenos Aires",
                            "country": "Argentina",
                            "latitude": -34.603,
                            "longitude": -58.381,
                            "street": "Street Address 123"
                        }
                    },
                    "cover": {
                        "source": "https://scontent.xx.fbcdn.net/..."
                    },
                    "attending_count": 150,
                    "interested_count": 500,
                    "maybe_count": 200,
                    "is_online": false,
                    "ticket_uri": "https://www.facebook.com/events/123456789",
                    "owner": {
                        "name": "Event Organizer",
                        "id": "987654321"
                    }
                }
            ],
            "paging": {
                "cursors": {
                    "before": "...",
                    "after": "..."
                },
                "next": "..."
            }
        }
        """
        
        if not self.api_key:
            # Sin API key, retornar vacío
            return {"data": []}
        
        async with aiohttp.ClientSession() as session:
            # Endpoint para buscar eventos
            url = f"{self.base_url}/search/events"
            
            params = {
                "query": location,
                "limit": limit,
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now().replace(year=datetime.now().year + 1)).strftime("%Y-%m-%d")
            }
            
            try:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"data": data.get("events", [])} if isinstance(data, dict) else {"data": data}
                    else:
                        return {"data": []}
                        
            except asyncio.TimeoutError:
                raise
            except Exception as e:
                return {"data": [], "error": str(e)}
    
    def normalize_output(self, raw_data: Dict[str, Any]) -> List[Event]:
        """
        Normaliza la respuesta de Facebook al formato Event estándar
        """
        events = []
        
        for item in raw_data.get("data", []):
            # Extraer datos básicos
            title = item.get("name", "Sin título")
            description = item.get("description", "")
            
            # Fechas
            start_date = self.parse_date(item.get("start_time"))
            end_date = self.parse_date(item.get("end_time"))
            
            # Ubicación
            place = item.get("place", {})
            venue_name = place.get("name", "")
            location = place.get("location", {})
            street = location.get("street", "")
            city = location.get("city", "")
            country = location.get("country", "")
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            
            # Construir dirección completa
            venue_address = ", ".join(filter(None, [street, city, country]))
            
            # Multimedia
            cover = item.get("cover", {})
            image_url = cover.get("source") if cover else None
            
            # Asistencia
            attending = item.get("attending_count", 0)
            interested = item.get("interested_count", 0)
            maybe = item.get("maybe_count", 0)
            total_interested = attending + interested + maybe
            
            # Organizador
            owner = item.get("owner", {})
            organizer_name = owner.get("name", "")
            
            # Es online?
            is_online = item.get("is_online", False)
            if is_online:
                venue_name = "Evento Online"
                venue_address = "Online"
            
            # URL del evento
            event_id = item.get("id", "")
            source_url = f"https://www.facebook.com/events/{event_id}" if event_id else item.get("ticket_uri", "")
            
            # Crear evento normalizado
            event = Event(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                venue_name=venue_name,
                venue_address=venue_address,
                city=city if not is_online else "Online",
                country=country,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                price=0,  # Facebook no proporciona precios
                price_display="Ver en Facebook",
                currency="ARS",
                is_free=True,  # Asumimos que son gratuitos salvo indicación
                image_url=image_url,
                source="facebook",
                source_url=source_url,
                source_id=event_id,
                category=self.detect_category(f"{title} {description}"),
                organizer_name=organizer_name,
                attendee_count=total_interested,
                tags=["facebook", "social"] + (["online"] if is_online else [])
            )
            
            events.append(event)
        
        return events