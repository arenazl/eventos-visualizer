"""
🏗️ BASE SCRAPER - Clase base para scrapers regionales
Clase base abstracta que define la interfaz común para todos los scrapers regionales
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """
    🏗️ CLASE BASE PARA SCRAPERS REGIONALES
    
    CARACTERÍSTICAS:
    - Interface común para todos los scrapers regionales
    - Manejo estándar de ubicación y categorías
    - Logging y métricas integradas
    - Compatibilidad con EventOrchestrator
    """
    
    def __init__(self, region: str, city: str):
        """
        Constructor base para scrapers regionales
        
        Args:
            region: País/región (ej: 'argentina', 'brasil')
            city: Ciudad específica (ej: 'cordoba', 'sao_paulo')
        """
        self.region = region
        self.city = city
        self.scraper_name = f"{region}_{city}_scraper"
        
        logger.info(f"🏗️ {self.scraper_name} inicializado")
    
    @abstractmethod
    async def scrape_events(
        self, 
        location: str, 
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🎯 MÉTODO PRINCIPAL DE SCRAPING (ABSTRACTO)
        
        Args:
            location: Ubicación de búsqueda
            category: Categoría opcional
            limit: Límite de eventos
            
        Returns:
            Lista de eventos encontrados
        """
        pass
    
    def _standardize_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        📋 ESTANDARIZAR FORMATO DE EVENTO
        
        Args:
            event_data: Datos crudos del evento
            
        Returns:
            Evento en formato estándar
        """
        
        standardized = {
            'title': event_data.get('title', 'Sin título'),
            'description': event_data.get('description', f'Evento encontrado en {self.scraper_name}'),
            'event_url': event_data.get('event_url', ''),
            'image_url': event_data.get('image_url', ''),
            'venue_name': event_data.get('venue_name', f'{self.city.title()}'),
            'venue_address': event_data.get('venue_address'),
            'start_datetime': event_data.get('start_datetime'),
            'end_datetime': event_data.get('end_datetime'),
            'price': event_data.get('price'),
            'is_free': event_data.get('is_free', False),
            'source': self.scraper_name,
            'category': event_data.get('category', 'Eventos Regionales'),
            'external_id': event_data.get('external_id'),
            'region_info': {
                'region': self.region,
                'city': self.city,
                'scraper_type': 'regional'
            }
        }
        
        return standardized
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """
        📊 INFORMACIÓN DEL SCRAPER
        
        Returns:
            Información detallada del scraper
        """
        return {
            'name': self.scraper_name,
            'region': self.region,
            'city': self.city,
            'type': 'regional',
            'status': 'active',
            'supports_categories': True,
            'supports_limits': True
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        🏥 HEALTH CHECK DEL SCRAPER
        
        Returns:
            Estado de salud del scraper
        """
        try:
            # Test básico de funcionalidad
            test_events = await self.scrape_events(
                location=f"{self.city}, {self.region}", 
                limit=1
            )
            
            return {
                'scraper': self.scraper_name,
                'status': 'healthy',
                'region': self.region,
                'city': self.city,
                'test_events_found': len(test_events),
                'last_check': 'now'
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed for {self.scraper_name}: {str(e)}")
            return {
                'scraper': self.scraper_name,
                'status': 'unhealthy',
                'region': self.region,
                'city': self.city,
                'error': str(e),
                'last_check': 'now'
            }