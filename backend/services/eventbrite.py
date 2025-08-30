from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import json

from utils.config import settings

logger = logging.getLogger(__name__)

class EventbriteService:
    """Eventbrite API integration service"""
    
    BASE_URL = "https://www.eventbriteapi.com/v3"
    
    def __init__(self):
        self.api_key = settings.eventbrite_api_key
    
    async def search_events(
        self, 
        location: str = None,
        latitude: float = None,
        longitude: float = None,
        radius: str = "25km",
        categories: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 1
    ) -> List[Dict]:
        """Search for events using Eventbrite API"""
        
        # For demo purposes, return mock data
        logger.info("Eventbrite API - returning mock data for demo")
        return self._get_mock_events(location)
    
    def _get_mock_events(self, location: str = None) -> List[Dict]:
        """Return mock events for demo purposes"""
        mock_events = [
            {
                "external_id": "mock_1",
                "source_api": "eventbrite",
                "title": "Concierto de Rock en Buenos Aires",
                "description": "Una noche increíble de rock nacional e internacional en el corazón de Buenos Aires.",
                "start_datetime": datetime.now() + timedelta(days=7),
                "end_datetime": datetime.now() + timedelta(days=7, hours=4),
                "venue_name": "Teatro Colón",
                "venue_address": "Cerrito 628, Buenos Aires",
                "latitude": -34.6037,
                "longitude": -58.3816,
                "category": "musica",
                "price": 2500.0,
                "currency": "ARS",
                "is_free": False,
                "external_url": "https://example.com/evento1",
                "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
                "api_data": {}
            },
            {
                "external_id": "mock_2", 
                "source_api": "eventbrite",
                "title": "Festival de Tecnología Argentina 2024",
                "description": "El evento tech más importante del año con speakers internacionales y workshops.",
                "start_datetime": datetime.now() + timedelta(days=14),
                "end_datetime": datetime.now() + timedelta(days=16),
                "venue_name": "Centro de Convenciones",
                "venue_address": "Puerto Madero, Buenos Aires",
                "latitude": -34.6118,
                "longitude": -58.3684,
                "category": "tech",
                "price": 0.0,
                "currency": "ARS",
                "is_free": True,
                "external_url": "https://example.com/evento2",
                "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400",
                "api_data": {}
            },
            {
                "external_id": "mock_3",
                "source_api": "eventbrite", 
                "title": "Maratón Buenos Aires 2024",
                "description": "Maratón internacional por las calles más emblemáticas de Buenos Aires.",
                "start_datetime": datetime.now() + timedelta(days=21),
                "end_datetime": datetime.now() + timedelta(days=21, hours=6),
                "venue_name": "Obelisco",
                "venue_address": "Av. Corrientes & 9 de Julio, Buenos Aires",
                "latitude": -34.6033,
                "longitude": -58.3817,
                "category": "deportes",
                "price": 1500.0,
                "currency": "ARS",
                "is_free": False,
                "external_url": "https://example.com/evento3", 
                "image_url": "https://images.unsplash.com/photo-1513593771513-7b58b6c4af38?w=400",
                "api_data": {}
            },
            {
                "external_id": "mock_4",
                "source_api": "eventbrite",
                "title": "Exposición de Arte Contemporáneo",
                "description": "Muestra de artistas locales e internacionales con obras de vanguardia.",
                "start_datetime": datetime.now() + timedelta(days=5),
                "end_datetime": datetime.now() + timedelta(days=35),
                "venue_name": "Museo Nacional de Bellas Artes",
                "venue_address": "Av. del Libertador 1473, Buenos Aires",
                "latitude": -34.5833,
                "longitude": -58.3933,
                "category": "cultural",
                "price": 800.0,
                "currency": "ARS",
                "is_free": False,
                "external_url": "https://example.com/evento4",
                "image_url": "https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=400",
                "api_data": {}
            },
            {
                "external_id": "mock_5",
                "source_api": "eventbrite",
                "title": "Fiesta de Fin de Año en Puerto Madero",
                "description": "Celebra la llegada del nuevo año con la mejor música, fuegos artificiales y gastronomía.",
                "start_datetime": datetime.now() + timedelta(days=90),
                "end_datetime": datetime.now() + timedelta(days=90, hours=8),
                "venue_name": "Costanera Sur",
                "venue_address": "Puerto Madero, Buenos Aires",
                "latitude": -34.6118,
                "longitude": -58.3684,
                "category": "fiestas",
                "price": 3500.0,
                "currency": "ARS",
                "is_free": False,
                "external_url": "https://example.com/evento5",
                "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
                "api_data": {}
            }
        ]
        
        return mock_events
    
    async def close(self):
        """Close HTTP session (no-op for mock implementation)"""
        pass