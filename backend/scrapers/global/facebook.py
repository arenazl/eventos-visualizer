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
        self.base_url = "facebook-scraper3.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.api_key or "f3435e87bbmsh512cdcef2082564p161dacjsnb5f035481232",
            "x-rapidapi-host": "facebook-scraper3.p.rapidapi.com"
        }
    
    async def scrape(self, location: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Busca eventos en Facebook para una ubicación usando RapidAPI facebook-scraper3
        """

        # Use http.client as per the example
        import http.client
        import json

        try:
            # Create HTTPS connection
            conn = http.client.HTTPSConnection(self.base_url)

            # Make the request with location as query parameter
            endpoint = f"/search/events?query={location.replace(' ', '%20')}"

            conn.request("GET", endpoint, headers=self.headers)

            # Get response
            res = conn.getresponse()
            data = res.read()

            # Parse JSON response
            result = json.loads(data.decode("utf-8"))

            # Close connection
            conn.close()

            # Return in expected format
            # The new API returns {"results": [...], "cursor": "..."}
            if isinstance(result, dict):
                if 'results' in result:
                    # New format from facebook-scraper3
                    return {"results": result["results"], "data": result.get("results", [])}
                elif 'data' in result:
                    return result
                elif 'events' in result:
                    return {"data": result["events"]}
                else:
                    return {"data": []}
            elif isinstance(result, list):
                return {"data": result}
            else:
                return {"data": []}

        except http.client.HTTPException as e:
            print(f"❌ HTTP Error in Facebook scraper: {e}")
            return {"data": [], "error": str(e)}
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error in Facebook scraper: {e}")
            return {"data": [], "error": "Invalid JSON response"}
        except Exception as e:
            print(f"❌ Error in Facebook scraper: {e}")
            return {"data": [], "error": str(e)}
    
    def normalize_output(self, raw_data: Dict[str, Any]) -> List[Event]:
        """
        Normaliza la respuesta de Facebook al formato Event estándar
        """
        events = []

        # Handle new response format from facebook-scraper3
        results = raw_data.get("results", raw_data.get("data", []))

        for item in results:
            # Extract data from new format
            if item.get("type") == "search_event":
                # Basic data
                title = item.get("title", "Sin título").strip()
                event_id = item.get("event_id", "")
                event_url = item.get("url", "")

                # Since the new API doesn't provide all details, we'll use what we have
                # and potentially fetch more details later if needed

                # Create event with available data
                event = Event(
                    title=title,
                    description="",  # Not provided in search results
                    start_date=None,  # Would need to fetch event details
                    end_date=None,
                    venue_name="Ver en Facebook",  # Placeholder
                    venue_address="",
                    city="",  # Will be filled from search location
                    country="",
                    latitude=None,
                    longitude=None,
                    price=0,
                    price_display="Ver detalles en Facebook",
                    currency="EUR",
                    is_free=True,
                    image_url=None,  # Would need to fetch from event page
                    source="facebook",
                    source_url=event_url,
                    source_id=event_id,
                    category=self.detect_category(title),
                    organizer_name="",
                    attendee_count=0,
                    tags=["facebook", "social"]
                )

                events.append(event)
            elif not item.get("type"):
                # Handle old format if still used
                title = item.get("name", item.get("title", "Sin título"))
                description = item.get("description", "")

                # Try to extract other fields from old format
                event_id = item.get("id", item.get("event_id", ""))
                source_url = item.get("url", f"https://www.facebook.com/events/{event_id}" if event_id else "")

                event = Event(
                    title=title,
                    description=description,
                    start_date=self.parse_date(item.get("start_time")),
                    end_date=self.parse_date(item.get("end_time")),
                    venue_name=item.get("place", {}).get("name", ""),
                    venue_address="",
                    city=item.get("place", {}).get("location", {}).get("city", ""),
                    country=item.get("place", {}).get("location", {}).get("country", ""),
                    latitude=None,
                    longitude=None,
                    price=0,
                    price_display="Ver en Facebook",
                    currency="EUR",
                    is_free=True,
                    image_url=item.get("cover", {}).get("source") if item.get("cover") else None,
                    source="facebook",
                    source_url=source_url,
                    source_id=event_id,
                    category=self.detect_category(f"{title} {description}"),
                    organizer_name=item.get("owner", {}).get("name", "") if item.get("owner") else "",
                    attendee_count=0,
                    tags=["facebook", "social"]
                )

                events.append(event)
        
        return events