#!/usr/bin/env python3
"""
🗺️ NEARBY CITIES SERVICE
Servicio para detectar 3 ciudades aledañas a cualquier ubicación
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CityInfo:
    name: str
    distance_km: int
    country: str
    province: Optional[str] = None

class NearbyCitiesService:
    """
    🏙️ SERVICIO DE CIUDADES ALEDAÑAS
    
    Detecta 3 ciudades cercanas para usar en el WebSocket recommend
    """
    
    def __init__(self):
        self.nearby_cities_cache = {}
        self.city_database = self._build_city_database()
        logger.info("🗺️ Nearby Cities Service inicializado")
    
    def _build_city_database(self) -> Dict[str, List[CityInfo]]:
        """
        🏗️ BASE DE DATOS DE CIUDADES ALEDAÑAS
        
        Returns:
            Diccionario con ciudades y sus aledañas
        """
        
        # DISABLED - No hardcoded city relationships
        return {}
    
    async def get_nearby_cities(self, location: str) -> List[str]:
        """
        🔍 OBTENER 3 CIUDADES ALEDAÑAS
        
        Args:
            location: Ciudad principal
            
        Returns:
            Lista de 3 ciudades aledañas como strings
        """
        
        try:
            # Normalizar ubicación
            normalized_location = self._normalize_location(location)
            
            if normalized_location in self.city_database:
                nearby_cities_info = self.city_database[normalized_location]
                
                # Convertir a lista de strings para compatibilidad
                nearby_cities = [city.name for city in nearby_cities_info]
                
                logger.info(f"🗺️ Ciudades aledañas para {location}: {nearby_cities}")
                
                # Almacenar en cache para el recommend WebSocket
                self.nearby_cities_cache[normalized_location] = nearby_cities
                
                return nearby_cities
            else:
                # Fallback: ciudades por defecto si no encontramos la ubicación
                logger.warning(f"⚠️ No se encontraron ciudades aledañas para: {location}")
                fallback_cities = await self._get_fallback_cities(location)
                
                self.nearby_cities_cache[normalized_location] = fallback_cities
                return fallback_cities
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo ciudades aledañas: {e}")
            return await self._get_fallback_cities(location)
    
    def _normalize_location(self, location: str) -> str:
        """
        🔧 NORMALIZAR NOMBRE DE UBICACIÓN
        
        Args:
            location: Ubicación original
            
        Returns:
            Ubicación normalizada
        """
        
        # Mapeo de variaciones comunes
        location_mapping = {
            "cordoba": "Córdoba",
            "buenos aires": "Buenos Aires",
            "caba": "Buenos Aires",
            "cdmx": "Mexico City",
            "ciudad de méxico": "Mexico City",
            "df": "Mexico City",
            "bcn": "Barcelona",
            "barna": "Barcelona",
            "parís": "Paris",
            "sao paulo": "São Paulo"
        }
        
        normalized = location_mapping.get(location.lower(), location)
        return normalized
    
    async def _get_fallback_cities(self, location: str) -> List[str]:
        """
        🔄 CIUDADES FALLBACK SI NO ENCONTRAMOS LA UBICACIÓN
        
        Args:
            location: Ubicación original
            
        Returns:
            Lista de ciudades fallback
        """
        
        # Detectar país y dar fallback inteligente
        location_lower = location.lower()
        
        if any(keyword in location_lower for keyword in ['argentina', 'buenos aires', 'cordoba', 'mendoza']):
            return ["Buenos Aires", "Córdoba", "Rosario"]
        elif any(keyword in location_lower for keyword in ['españa', 'spain', 'madrid', 'barcelona']):
            return ["Madrid", "Barcelona", "Valencia"]
        elif any(keyword in location_lower for keyword in ['francia', 'france', 'paris']):
            return ["Paris", "Lyon", "Marseille"]
        elif any(keyword in location_lower for keyword in ['mexico', 'méxico']):
            return ["Mexico City", "Guadalajara", "Monterrey"]
        elif any(keyword in location_lower for keyword in ['usa', 'united states', 'new york', 'los angeles']):
            return ["New York", "Los Angeles", "Miami"]
        else:
            # Fallback global más popular
            return ["Barcelona", "Paris", "New York"]
    
    def get_cached_nearby_cities(self, location: str) -> Optional[List[str]]:
        """
        📦 OBTENER CIUDADES ALEDAÑAS DESDE CACHE
        
        Args:
            location: Ciudad principal
            
        Returns:
            Lista de ciudades aledañas o None si no está en cache
        """
        
        normalized_location = self._normalize_location(location)
        return self.nearby_cities_cache.get(normalized_location)
    
    def clear_cache(self):
        """🗑️ LIMPIAR CACHE DE CIUDADES ALEDAÑAS"""
        self.nearby_cities_cache.clear()
        logger.info("🗑️ Cache de ciudades aledañas limpiado")

# Instancia global del servicio
nearby_cities_service = NearbyCitiesService()