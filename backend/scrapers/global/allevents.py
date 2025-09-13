"""
🌐 ALLEVENTS SCRAPER V2
Scraper para AllEvents.in
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from ..base import IScraper, Event, EventCategory

class AllEventsScraper(IScraper):
    """
    Scraper para AllEvents.in API
    Documentación: https://allevents.in/pages/api
    """
    
    name = "allevents"
    timeout = 4
    priority = 4  # Prioridad media-baja
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("ALLEVENTS_API_KEY"))
        self.base_url = "https://allevents.in/api/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        } if self.api_key else {}
    
    async def scrape(self, location: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Busca eventos en AllEvents para una ubicación
        
        Formato típico de respuesta de AllEvents (estimado):
        {
            "request": {
                "city": "Buenos Aires",
                "country": "Argentina"
            },
            "events": [
                {
                    "event_id": "123456",
                    "eventname": "Event Name",
                    "description": "Event description",
                    "start_time": "2024-12-25 19:00:00",
                    "end_time": "2024-12-25 23:00:00",
                    "location": "Venue Name",
                    "venue": {
                        "venue_name": "Venue Name",
                        "full_address": "123 Street, City, Country",
                        "city": "Buenos Aires",
                        "country": "Argentina",
                        "latitude": "-34.603",
                        "longitude": "-58.381"
                    },
                    "banner_url": "https://cdn.allevents.in/banners/...",
                    "thumb_url": "https://cdn.allevents.in/thumbs/...",
                    "categories": ["Music", "Concert"],
                    "tags": ["rock", "live music"],
                    "organizer": {
                        "name": "Organizer Name",
                        "id": "org123"
                    },
                    "tickets": {
                        "has_tickets": true,
                        "ticket_url": "https://allevents.in/e/123456",
                        "min_price": 500,
                        "max_price": 1500,
                        "currency": "ARS"
                    },
                    "is_free": false,
                    "going_count": 150,
                    "interested_count": 500,
                    "share_url": "https://allevents.in/e/123456"
                }
            ],
            "count": 25,
            "status": "success"
        }
        """
        
        # Por defecto hacer web scraping ya que la API requiere registro
        return await self._scrape_web(location, limit)
    
    async def _scrape_web(self, location: str, limit: int) -> Dict[str, Any]:
        """
        Web scraping de AllEvents.in
        """
        from bs4 import BeautifulSoup
        
        async with aiohttp.ClientSession() as session:
            # AllEvents usa URLs con formato: /city/events
            city_slug = location.lower().replace(' ', '-')
            url = f"https://allevents.in/{city_slug}/all"
            
            try:
                async with session.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        return {"events": []}
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    events = []
                    
                    # Buscar tarjetas de eventos
                    event_items = soup.find_all('li', class_='event-item', limit=limit)
                    if not event_items:
                        # Intentar otro selector
                        event_items = soup.find_all('article', class_='event-card', limit=limit)
                    
                    for item in event_items:
                        event_data = {}
                        
                        # Título
                        title_elem = item.find(['h3', 'h4', 'a'], class_=['event-title', 'title'])
                        if title_elem:
                            event_data['eventname'] = title_elem.text.strip()
                        
                        # Fecha/hora
                        date_elem = item.find(['time', 'span'], class_=['event-date', 'date'])
                        if date_elem:
                            event_data['start_time'] = date_elem.get('datetime', date_elem.text.strip())
                        
                        # Ubicación
                        location_elem = item.find(['span', 'div'], class_=['event-location', 'location', 'venue'])
                        if location_elem:
                            event_data['location'] = location_elem.text.strip()
                            event_data['venue'] = {
                                'venue_name': location_elem.text.strip(),
                                'city': location
                            }
                        
                        # Imagen
                        img_elem = item.find('img')
                        if img_elem:
                            event_data['thumb_url'] = img_elem.get('src', '')
                            event_data['banner_url'] = img_elem.get('data-src', event_data['thumb_url'])
                        
                        # URL del evento
                        link_elem = item.find('a', href=True)
                        if link_elem:
                            event_data['share_url'] = f"https://allevents.in{link_elem['href']}" if link_elem['href'].startswith('/') else link_elem['href']
                            # Extraer ID del URL
                            if '/e/' in event_data['share_url']:
                                event_data['event_id'] = event_data['share_url'].split('/e/')[-1].split('/')[0]
                        
                        # Precio (buscar indicadores de "Free" o precio)
                        price_elem = item.find(['span', 'div'], class_=['price', 'ticket-price'])
                        if price_elem:
                            price_text = price_elem.text.strip().lower()
                            event_data['is_free'] = 'free' in price_text or 'gratis' in price_text
                        else:
                            event_data['is_free'] = False
                        
                        # Categoría (si está disponible)
                        category_elem = item.find(['span', 'a'], class_=['category', 'tag'])
                        if category_elem:
                            event_data['categories'] = [category_elem.text.strip()]
                        
                        if event_data:
                            events.append(event_data)
                    
                    return {"events": events}
                    
            except asyncio.TimeoutError:
                raise
            except Exception as e:
                return {"events": [], "error": str(e)}
    
    def normalize_output(self, raw_data: Dict[str, Any]) -> List[Event]:
        """
        Normaliza la respuesta de AllEvents al formato Event estándar
        """
        events = []
        
        for item in raw_data.get("events", []):
            # Extraer datos básicos
            title = item.get("eventname", item.get("title", "Sin título"))
            description = item.get("description", "")
            
            # Fechas
            start_date = self.parse_date(item.get("start_time"))
            end_date = self.parse_date(item.get("end_time"))
            
            # Ubicación
            venue = item.get("venue", {})
            venue_name = venue.get("venue_name", item.get("location", ""))
            venue_address = venue.get("full_address", "")
            city = venue.get("city", "")
            country = venue.get("country", "")
            latitude = venue.get("latitude")
            longitude = venue.get("longitude")
            
            # Convertir lat/lng a float si vienen como string
            try:
                latitude = float(latitude) if latitude else None
                longitude = float(longitude) if longitude else None
            except (ValueError, TypeError):
                latitude = None
                longitude = None
            
            # Precio
            tickets = item.get("tickets", {})
            is_free = item.get("is_free", False)
            min_price = tickets.get("min_price", 0)
            currency = tickets.get("currency", "ARS")
            price_display = "Gratis" if is_free else f"{currency} {min_price}"
            ticket_url = tickets.get("ticket_url", item.get("share_url", ""))
            
            # Multimedia
            image_url = item.get("banner_url", item.get("thumb_url"))
            thumbnail_url = item.get("thumb_url")
            
            # Organizador
            organizer = item.get("organizer", {})
            organizer_name = organizer.get("name", "") if isinstance(organizer, dict) else str(organizer)
            
            # Categorías y tags
            categories = item.get("categories", [])
            tags = item.get("tags", [])
            
            # Detectar categoría principal
            category_text = " ".join(categories + tags + [title, description])
            category = self.detect_category(category_text)
            
            # Asistencia
            going = item.get("going_count", 0)
            interested = item.get("interested_count", 0)
            
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
                latitude=latitude,
                longitude=longitude,
                price=min_price if not is_free else 0,
                price_display=price_display,
                currency=currency,
                is_free=is_free,
                ticket_url=ticket_url,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                source="allevents",
                source_url=item.get("share_url", ticket_url),
                source_id=item.get("event_id"),
                category=category,
                organizer_name=organizer_name,
                attendee_count=going + interested,
                tags=tags + ["allevents"]
            )
            
            events.append(event)
        
        return events