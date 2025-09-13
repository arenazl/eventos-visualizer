"""
🎫 EVENTBRITE SCRAPER V2
Scraper para Eventbrite usando su API v3
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from ..base import IScraper, Event, EventCategory

class EventbriteScraper(IScraper):
    """
    Scraper para Eventbrite API v3
    Documentación: https://www.eventbrite.com/platform/api
    """
    
    name = "eventbrite"
    timeout = 5
    priority = 1  # Alta prioridad - API rápida y confiable
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("EVENTBRITE_API_KEY"))
        self.base_url = "https://www.eventbriteapi.com/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        } if self.api_key else {}
    
    async def scrape(self, location: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Busca eventos en Eventbrite para una ubicación
        
        Formato típico de respuesta de Eventbrite v3:
        {
            "pagination": {...},
            "events": [
                {
                    "id": "123456",
                    "name": {
                        "text": "Event Name",
                        "html": "<p>Event Name</p>"
                    },
                    "description": {
                        "text": "Event description",
                        "html": "<p>Event description</p>"
                    },
                    "start": {
                        "timezone": "America/Buenos_Aires",
                        "local": "2024-12-25T19:00:00",
                        "utc": "2024-12-25T22:00:00Z"
                    },
                    "end": {
                        "timezone": "America/Buenos_Aires",
                        "local": "2024-12-25T23:00:00",
                        "utc": "2024-12-26T02:00:00Z"
                    },
                    "url": "https://www.eventbrite.com/e/event-name-tickets-123456",
                    "venue_id": "789",
                    "organizer_id": "456",
                    "logo": {
                        "url": "https://img.evbuc.com/..."
                    },
                    "is_free": false,
                    "ticket_availability": {
                        "has_available_tickets": true,
                        "minimum_ticket_price": {
                            "currency": "USD",
                            "value": 2500,
                            "display": "$25.00"
                        }
                    }
                }
            ]
        }
        """
        
        if not self.api_key:
            # Si no hay API key, hacer web scraping
            return await self._scrape_web(location, limit)
        
        # Usar API si tenemos key
        async with aiohttp.ClientSession() as session:
            params = {
                "q": location,
                "expand": "venue,organizer,ticket_availability",
                "page_size": limit
            }
            
            try:
                async with session.get(
                    f"{self.base_url}/events/search/",
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        # Fallback a web scraping si falla la API
                        return await self._scrape_web(location, limit)
                        
            except asyncio.TimeoutError:
                raise
            except Exception as e:
                # Fallback a web scraping
                return await self._scrape_web(location, limit)
    
    async def _scrape_web(self, location: str, limit: int) -> Dict[str, Any]:
        """
        Fallback: Web scraping cuando no hay API key
        """
        from bs4 import BeautifulSoup
        
        async with aiohttp.ClientSession() as session:
            url = f"https://www.eventbrite.com/d/{location.replace(' ', '-').lower()}--events/"
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                events = []
                # Buscar tarjetas de eventos
                event_cards = soup.find_all('article', class_='event-card', limit=limit)
                
                for card in event_cards:
                    event = {
                        "name": {"text": card.find('h3').text.strip() if card.find('h3') else ""},
                        "url": card.find('a')['href'] if card.find('a') else "",
                        "start": {"local": card.find('time')['datetime'] if card.find('time') else ""},
                        "venue": {"name": card.find('.venue-name').text if card.find('.venue-name') else ""},
                        "is_free": "Free" in card.text,
                        "logo": {"url": card.find('img')['src'] if card.find('img') else ""}
                    }
                    events.append(event)
                
                return {"events": events}
    
    def normalize_output(self, raw_data: Dict[str, Any]) -> List[Event]:
        """
        Normaliza la respuesta de Eventbrite al formato Event estándar
        """
        events = []
        
        for item in raw_data.get("events", []):
            # Extraer datos básicos
            title = item.get("name", {}).get("text", "Sin título")
            description = item.get("description", {}).get("text", "")
            
            # Fechas
            start_date = self.parse_date(item.get("start", {}).get("local"))
            end_date = self.parse_date(item.get("end", {}).get("local"))
            
            # Ubicación (si se expandió el venue)
            venue = item.get("venue", {})
            venue_name = venue.get("name", "")
            venue_address = venue.get("address", {}).get("localized_address_display", "")
            city = venue.get("address", {}).get("city", "")
            country = venue.get("address", {}).get("country", "")
            latitude = venue.get("latitude")
            longitude = venue.get("longitude")
            
            # Precio
            is_free = item.get("is_free", False)
            ticket_info = item.get("ticket_availability", {})
            min_price = ticket_info.get("minimum_ticket_price", {})
            price = min_price.get("value", 0) / 100 if min_price else 0  # Viene en centavos
            price_display = min_price.get("display", "Gratis" if is_free else "")
            currency = min_price.get("currency", "USD")
            
            # Multimedia
            logo = item.get("logo", {})
            image_url = logo.get("url") if logo else None
            
            # Organizador
            organizer = item.get("organizer", {})
            organizer_name = organizer.get("name", "")
            
            # Crear evento normalizado
            event = Event(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                venue_name=venue_name,
                venue_address=venue_address,
                city=city,
                country=country,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                price=price if not is_free else 0,
                price_display=price_display,
                currency=currency,
                is_free=is_free,
                image_url=image_url,
                source="eventbrite",
                source_url=item.get("url"),
                source_id=item.get("id"),
                category=self.detect_category(f"{title} {description}"),
                organizer_name=organizer_name,
                capacity=item.get("capacity")
            )
            
            events.append(event)
        
        return events