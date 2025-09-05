"""
🔌 DISCOVERY ENGINE INTERFACE - Dependency Injection Pattern
Interface para abstraer el servicio de descubrimiento de scrapers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class DiscoveryEngineInterface(ABC):
    """
    Interface para discovery engines que siguen el patrón Strategy
    
    Permite intercambiar diferentes implementaciones de descubrimiento:
    - AutoDiscoveryEngine (actual)  
    - StaticDiscoveryEngine (configuración fija)
    - RemoteDiscoveryEngine (desde API externa)
    - TestDiscoveryEngine (para testing)
    """
    
    @abstractmethod
    def discover_all_scrapers(self) -> Dict[str, Dict[str, Any]]:
        """
        Descubre todos los scrapers disponibles
        
        Returns:
            Dict con estructura:
            {
                'global': {'scraper_name': scraper_instance, ...},
                'regional': {'country': {'scraper_name': scraper_instance, ...}},
                'local': {'scraper_name': scraper_instance, ...}
            }
        """
        pass
    
    @abstractmethod
    def discover_scrapers_by_type(self, scraper_type: str) -> Dict[str, Any]:
        """
        Descubre scrapers de un tipo específico
        
        Args:
            scraper_type: 'global', 'regional', 'local'
            
        Returns:
            Dict con scrapers del tipo solicitado
        """
        pass
    
    @abstractmethod
    def is_scraper_enabled(self, scraper_name: str) -> bool:
        """
        Verifica si un scraper está habilitado
        
        Args:
            scraper_name: Nombre del scraper a verificar
            
        Returns:
            True si está habilitado, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_scraper_config(self, scraper_name: str) -> Dict[str, Any]:
        """
        Obtiene la configuración de un scraper específico
        
        Args:
            scraper_name: Nombre del scraper
            
        Returns:
            Dict con configuración del scraper (timeout, priority, etc.)
        """
        pass