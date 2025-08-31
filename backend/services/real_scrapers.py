"""
🏭 Real Scrapers - Wrappers que usan scrapers existentes
Estos scrapers implementan BaseScraper pero usan multi_source y provincial_scrapers
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from .country_scraper_factory import BaseScraper

logger = logging.getLogger(__name__)

class RealArgentinaScraper(BaseScraper):
    """
    🇦🇷 Argentina Scraper - Usa provincial_scrapers + multi_source
    """
    
    def __init__(self, country: str, city: str):
        super().__init__(country, city)
        self.scraper_name = f"Argentina_{city}_Real"
    
    async def _do_scraping(self) -> List[Dict[str, Any]]:
        """
        Implementación del método abstracto - usa multi_source
        """
        try:
            # Importar multi_source aquí para evitar circular imports
            # Import usando import directo para evitar problemas
            import sys
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from api.multi_source import fetch_all_progressive
            
            # Ejecutar multi_source para la ciudad argentina
            events_response = await fetch_all_progressive(location=self.city, fast=True)
            
            if events_response and "events" in events_response:
                events = events_response["events"]
                logger.info(f"✅ {self.scraper_name}: {len(events)} eventos obtenidos")
                return events
            else:
                logger.info(f"⚠️ {self.scraper_name}: 0 eventos obtenidos")
                return []
                
        except Exception as e:
            logger.error(f"❌ {self.scraper_name}: Error - {e}")
            return []

class RealSpainScraper(BaseScraper):
    """
    🇪🇸 Spain Scraper - Usa multi_source
    """
    
    def __init__(self, country: str, city: str):
        super().__init__(country, city)
        self.scraper_name = f"Spain_{city}_Real"
    
    async def _do_scraping(self) -> List[Dict[str, Any]]:
        """
        Implementación del método abstracto - usa multi_source para España
        """
        try:
            # Importar multi_source aquí para evitar circular imports
            # Import usando import directo para evitar problemas
            import sys
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from api.multi_source import fetch_all_progressive
            
            # Ejecutar multi_source para la ciudad española
            events_response = await fetch_all_progressive(location=self.city, fast=True)
            
            if events_response and "events" in events_response:
                events = events_response["events"]
                logger.info(f"✅ {self.scraper_name}: {len(events)} eventos obtenidos")
                return events
            else:
                logger.info(f"⚠️ {self.scraper_name}: 0 eventos obtenidos")
                return []
                
        except Exception as e:
            logger.error(f"❌ {self.scraper_name}: Error - {e}")
            return []

class RealUSAScraper(BaseScraper):
    """
    🇺🇸 USA Scraper - Usa multi_source
    """
    
    def __init__(self, country: str, city: str):
        super().__init__(country, city)
        self.scraper_name = f"USA_{city}_Real"
    
    async def _do_scraping(self) -> List[Dict[str, Any]]:
        """
        Implementación del método abstracto - usa multi_source para USA
        """
        try:
            # Importar multi_source aquí para evitar circular imports
            # Import usando import directo para evitar problemas
            import sys
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from api.multi_source import fetch_all_progressive 
            
            # Ejecutar multi_source para la ciudad USA
            events_response = await fetch_all_progressive(location=self.city, fast=True)
            
            if events_response and "events" in events_response:
                events = events_response["events"]
                logger.info(f"✅ {self.scraper_name}: {len(events)} eventos obtenidos")
                return events
            else:
                logger.info(f"⚠️ {self.scraper_name}: 0 eventos obtenidos")
                return []
                
        except Exception as e:
            logger.error(f"❌ {self.scraper_name}: Error - {e}")
            return []

class GenericScraper(BaseScraper):
    """
    🌍 Generic Scraper - Fallback para países no específicos
    """
    
    def __init__(self, country: str, city: str):
        super().__init__(country, city)
        self.scraper_name = f"Generic_{country}_{city}"
    
    async def _do_scraping(self) -> List[Dict[str, Any]]:
        """
        Implementación del método abstracto - usa multi_source genérico
        """
        try:
            # Importar multi_source aquí para evitar circular imports
            # Import usando import directo para evitar problemas
            import sys
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from api.multi_source import fetch_all_progressive
            
            # Ejecutar multi_source para cualquier ubicación
            location_query = f"{self.city}, {self.country}"
            events_response = await fetch_all_progressive(location=location_query, fast=True)
            
            if events_response and "events" in events_response:
                events = events_response["events"]
                logger.info(f"✅ {self.scraper_name}: {len(events)} eventos obtenidos")
                return events
            else:
                logger.info(f"⚠️ {self.scraper_name}: 0 eventos obtenidos")
                return []
                
        except Exception as e:
            logger.error(f"❌ {self.scraper_name}: Error - {e}")
            return []