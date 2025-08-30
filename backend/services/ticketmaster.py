from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from utils.config import settings

logger = logging.getLogger(__name__)

class TicketmasterService:
    """Ticketmaster Discovery API integration"""
    
    BASE_URL = "https://app.ticketmaster.com/discovery/v2"
    
    def __init__(self):
        self.api_key = settings.ticketmaster_api_key
    
    async def search_events(
        self,
        location: str = None,
        latitude: float = None,
        longitude: float = None,
        radius: str = "25",
        categories: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 0,
        size: int = 20
    ) -> List[Dict]:
        """Search events using Ticketmaster API"""
        
        # For demo purposes, return mock data
        logger.info("Ticketmaster API - returning mock data for demo")
        return self._get_mock_events(location)
    
    def _get_mock_events(self, location: str = None) -> List[Dict]:
        """Return mock events for demo purposes"""
        mock_events = [
            {
                "external_id": "tm_mock_1",
                "source_api": "ticketmaster",
                "title": "Argentina vs Brasil - Clásico Sudamericano",
                "description": "El partido más esperado del año entre las dos potencias del fútbol sudamericano.",
                "start_datetime": datetime.now() + timedelta(days=10),
                "end_datetime": None,
                "venue_name": "Estadio Monumental",
                "venue_address": "Av. Figueroa Alcorta 7597, Buenos Aires",
                "latitude": -34.5451,
                "longitude": -58.4497,
                "category": "deportes",
                "price": 5000.0,
                "currency": "ARS",
                "is_free": False,
                "external_url": "https://example.com/partido",
                "image_url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=400",
                "api_data": {}
            },
            {
                "external_id": "tm_mock_2",
                "source_api": "ticketmaster", 
                "title": "Hamilton - Musical en Buenos Aires",
                "description": "La aclamada producción de Broadway llega por primera vez a Argentina.",
                "start_datetime": datetime.now() + timedelta(days=30),
                "end_datetime": None,
                "venue_name": "Teatro San Martín",
                "venue_address": "Av. Corrientes 1530, Buenos Aires",
                "latitude": -34.6037,
                "longitude": -58.3816,
                "category": "cultural",
                "price": 8000.0,
                "currency": "ARS",
                "is_free": False,
                "external_url": "https://example.com/hamilton",
                "image_url": "https://images.unsplash.com/photo-1507924538820-ede94a04019d?w=400",
                "api_data": {}
            },
            {
                "external_id": "tm_mock_3",
                "source_api": "ticketmaster",
                "title": "Copa América Final",
                "description": "La gran final de la Copa América 2024 en Buenos Aires.",
                "start_datetime": datetime.now() + timedelta(days=45),
                "end_datetime": None,
                "venue_name": "Estadio River Plate",
                "venue_address": "Av. Presidente Figueroa Alcorta 7597, Buenos Aires",
                "latitude": -34.5451,
                "longitude": -58.4497,
                "category": "deportes",
                "price": 12000.0,
                "currency": "ARS",
                "is_free": False,
                "external_url": "https://example.com/copa-america",
                "image_url": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=400",
                "api_data": {}
            }
        ]
        
        return mock_events
    
    async def close(self):
        """Close HTTP session (no-op for mock implementation)"""
        pass