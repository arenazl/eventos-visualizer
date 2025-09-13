"""
🤝 MEETUP SCRAPER V2
Scraper para Meetup usando GraphQL API
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json

from ..base import IScraper, Event, EventCategory

class MeetupScraper(IScraper):
    """
    Scraper para Meetup GraphQL API
    Documentación: https://www.meetup.com/api/schema/
    """
    
    name = "meetup"
    timeout = 3
    priority = 2  # Alta prioridad - API rápida
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("MEETUP_API_KEY"))
        self.graphql_url = "https://api.meetup.com/gql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else None
        }
    
    async def scrape(self, location: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Busca eventos en Meetup para una ubicación usando GraphQL
        
        Formato típico de respuesta de Meetup GraphQL:
        {
            "data": {
                "rankedEvents": {
                    "edges": [
                        {
                            "node": {
                                "id": "123456",
                                "title": "Event Title",
                                "description": "Event description",
                                "dateTime": "2024-12-25T19:00:00-03:00",
                                "endTime": "2024-12-25T21:00:00-03:00",
                                "venue": {
                                    "name": "Venue Name",
                                    "address": "123 Street",
                                    "city": "Buenos Aires",
                                    "country": "Argentina",
                                    "lat": -34.603,
                                    "lng": -58.381
                                },
                                "group": {
                                    "name": "Group Name",
                                    "urlname": "group-url"
                                },
                                "eventUrl": "https://www.meetup.com/group-url/events/123456",
                                "going": 25,
                                "maxTickets": 50,
                                "images": [
                                    {
                                        "source": "https://secure.meetupstatic.com/photos/..."
                                    }
                                ],
                                "feeSettings": {
                                    "amount": 10.00,
                                    "currency": "USD",
                                    "required": true
                                },
                                "eventType": "PHYSICAL",
                                "status": "PUBLISHED"
                            }
                        }
                    ],
                    "totalCount": 100
                }
            }
        }
        """
        
        # Query GraphQL para buscar eventos
        query = """
        query SearchEvents($location: String!, $first: Int!) {
            rankedEvents(
                filter: {
                    query: $location
                    startDateRange: {
                        min: "NOW"
                    }
                }
                first: $first
                sortOrder: DATETIME
            ) {
                edges {
                    node {
                        id
                        title
                        description
                        dateTime
                        endTime
                        eventUrl
                        going
                        maxTickets
                        eventType
                        status
                        venue {
                            name
                            address
                            city
                            country
                            lat
                            lng
                        }
                        group {
                            name
                            urlname
                        }
                        images {
                            source
                        }
                        feeSettings {
                            amount
                            currency
                            required
                        }
                    }
                }
                totalCount
            }
        }
        """
        
        variables = {
            "location": location,
            "first": limit
        }
        
        # Si no hay API key, intentar web scraping básico
        if not self.api_key:
            return await self._scrape_web(location, limit)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.graphql_url,
                    headers=self.headers,
                    json={"query": query, "variables": variables},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("rankedEvents", {"edges": []})
                    else:
                        return await self._scrape_web(location, limit)
                        
            except asyncio.TimeoutError:
                raise
            except Exception as e:
                return {"edges": [], "error": str(e)}
    
    async def _scrape_web(self, location: str, limit: int) -> Dict[str, Any]:
        """
        Fallback: Web scraping cuando no hay API key
        """
        from bs4 import BeautifulSoup
        
        async with aiohttp.ClientSession() as session:
            url = f"https://www.meetup.com/find/?keywords={location.replace(' ', '+')}"
            
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    events = []
                    # Buscar eventos en el HTML
                    event_cards = soup.find_all('div', class_='eventCard', limit=limit)
                    
                    for card in event_cards:
                        node = {
                            "title": card.find('h3').text.strip() if card.find('h3') else "",
                            "dateTime": card.find('time')['datetime'] if card.find('time') else "",
                            "venue": {
                                "name": card.find('.location').text if card.find('.location') else ""
                            },
                            "eventUrl": card.find('a')['href'] if card.find('a') else "",
                            "going": 0
                        }
                        events.append({"node": node})
                    
                    return {"edges": events}
                    
            except Exception:
                return {"edges": []}
    
    def normalize_output(self, raw_data: Dict[str, Any]) -> List[Event]:
        """
        Normaliza la respuesta de Meetup al formato Event estándar
        """
        events = []
        
        for edge in raw_data.get("edges", []):
            item = edge.get("node", {})
            
            # Extraer datos básicos
            title = item.get("title", "Sin título")
            description = item.get("description", "")
            
            # Fechas
            start_date = self.parse_date(item.get("dateTime"))
            end_date = self.parse_date(item.get("endTime"))
            
            # Ubicación
            venue = item.get("venue", {})
            venue_name = venue.get("name", "")
            venue_address = venue.get("address", "")
            city = venue.get("city", "")
            country = venue.get("country", "")
            latitude = venue.get("lat")
            longitude = venue.get("lng")
            
            # Tipo de evento (online o presencial)
            event_type = item.get("eventType", "PHYSICAL")
            is_online = event_type == "ONLINE"
            
            if is_online:
                venue_name = "Evento Online"
                venue_address = "Online"
                city = "Online"
            
            # Precio
            fee = item.get("feeSettings", {})
            has_fee = fee.get("required", False)
            price = fee.get("amount", 0) if has_fee else 0
            currency = fee.get("currency", "USD")
            is_free = not has_fee or price == 0
            price_display = f"{currency} {price:.2f}" if has_fee else "Gratis"
            
            # Multimedia
            images = item.get("images", [])
            image_url = images[0].get("source") if images else None
            
            # Grupo organizador
            group = item.get("group", {})
            organizer_name = group.get("name", "")
            
            # Asistencia
            going = item.get("going", 0)
            max_tickets = item.get("maxTickets", 0)
            
            # URL del evento
            event_url = item.get("eventUrl", "")
            
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
                price=price,
                price_display=price_display,
                currency=currency,
                is_free=is_free,
                ticket_url=event_url,
                image_url=image_url,
                source="meetup",
                source_url=event_url,
                source_id=item.get("id"),
                category=self.detect_category(f"{title} {description}"),
                organizer_name=organizer_name,
                attendee_count=going,
                capacity=max_tickets,
                tags=["meetup", "community"] + (["online"] if is_online else ["presencial"])
            )
            
            events.append(event)
        
        return events