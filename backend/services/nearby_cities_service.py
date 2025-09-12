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
        
        return {
            # Argentina
            "Buenos Aires": [
                CityInfo("La Plata", 56, "Argentina", "Buenos Aires"),
                CityInfo("Rosario", 298, "Argentina", "Santa Fe"),
                CityInfo("Córdoba", 695, "Argentina", "Córdoba")
            ],
            "Córdoba": [
                CityInfo("Villa Carlos Paz", 36, "Argentina", "Córdoba"),
                CityInfo("Mendoza", 465, "Argentina", "Mendoza"),
                CityInfo("Buenos Aires", 695, "Argentina", "Buenos Aires")
            ],
            "Mendoza": [
                CityInfo("San Juan", 165, "Argentina", "San Juan"),
                CityInfo("Córdoba", 465, "Argentina", "Córdoba"),
                CityInfo("Santiago", 360, "Chile", "Región Metropolitana")
            ],
            "Rosario": [
                CityInfo("Santa Fe", 155, "Argentina", "Santa Fe"),
                CityInfo("Buenos Aires", 298, "Argentina", "Buenos Aires"),
                CityInfo("Córdoba", 400, "Argentina", "Córdoba")
            ],
            
            # España
            "Barcelona": [
                CityInfo("Girona", 98, "España", "Cataluña"),
                CityInfo("Valencia", 350, "España", "Comunidad Valenciana"),
                CityInfo("Madrid", 620, "España", "Comunidad de Madrid")
            ],
            "Madrid": [
                CityInfo("Toledo", 70, "España", "Castilla-La Mancha"),
                CityInfo("Segovia", 88, "España", "Castilla y León"),
                CityInfo("Valencia", 355, "España", "Comunidad Valenciana")
            ],
            "Valencia": [
                CityInfo("Alicante", 166, "España", "Comunidad Valenciana"),
                CityInfo("Barcelona", 350, "España", "Cataluña"),
                CityInfo("Madrid", 355, "España", "Comunidad de Madrid")
            ],
            
            # Francia
            "Paris": [
                CityInfo("Versailles", 20, "Francia", "Île-de-France"),
                CityInfo("Reims", 144, "Francia", "Grand Est"),
                CityInfo("Orleans", 120, "Francia", "Centre-Val de Loire")
            ],
            "Lyon": [
                CityInfo("Saint-Étienne", 58, "Francia", "Auvergne-Rhône-Alpes"),
                CityInfo("Grenoble", 106, "Francia", "Auvergne-Rhône-Alpes"),
                CityInfo("Paris", 462, "Francia", "Île-de-France")
            ],
            
            # México
            "Mexico City": [
                CityInfo("Toluca", 63, "México", "Estado de México"),
                CityInfo("Puebla", 127, "México", "Puebla"),
                CityInfo("Cuernavaca", 85, "México", "Morelos")
            ],
            "Guadalajara": [
                CityInfo("Puerto Vallarta", 224, "México", "Jalisco"),
                CityInfo("Leon", 181, "México", "Guanajuato"),
                CityInfo("Mexico City", 541, "México", "Ciudad de México")
            ],
            
            # Estados Unidos
            "New York": [
                CityInfo("Philadelphia", 152, "Estados Unidos", "Pennsylvania"),
                CityInfo("Boston", 306, "Estados Unidos", "Massachusetts"),
                CityInfo("Washington DC", 365, "Estados Unidos", "District of Columbia")
            ],
            "Los Angeles": [
                CityInfo("San Diego", 191, "Estados Unidos", "California"),
                CityInfo("Las Vegas", 433, "Estados Unidos", "Nevada"),
                CityInfo("San Francisco", 616, "Estados Unidos", "California")
            ],
            "Miami": [
                CityInfo("Fort Lauderdale", 43, "Estados Unidos", "Florida"),
                CityInfo("Orlando", 378, "Estados Unidos", "Florida"),
                CityInfo("Tampa", 453, "Estados Unidos", "Florida")
            ],
            
            # Chile
            "Santiago": [
                CityInfo("Valparaíso", 116, "Chile", "Valparaíso"),
                CityInfo("Viña del Mar", 119, "Chile", "Valparaíso"),
                CityInfo("Mendoza", 360, "Argentina", "Mendoza")
            ],
            
            # Colombia
            "Bogotá": [
                CityInfo("Medellín", 416, "Colombia", "Antioquia"),
                CityInfo("Cali", 461, "Colombia", "Valle del Cauca"),
                CityInfo("Barranquilla", 1002, "Colombia", "Atlántico")
            ],
            "Medellín": [
                CityInfo("Bogotá", 416, "Colombia", "Cundinamarca"),
                CityInfo("Cali", 424, "Colombia", "Valle del Cauca"),
                CityInfo("Cartagena", 461, "Colombia", "Bolívar")
            ],
            
            # Brasil
            "São Paulo": [
                CityInfo("Rio de Janeiro", 429, "Brasil", "Rio de Janeiro"),
                CityInfo("Campinas", 96, "Brasil", "São Paulo"),
                CityInfo("Belo Horizonte", 586, "Brasil", "Minas Gerais")
            ],
            "Rio de Janeiro": [
                CityInfo("São Paulo", 429, "Brasil", "São Paulo"),
                CityInfo("Belo Horizonte", 434, "Brasil", "Minas Gerais"),
                CityInfo("Brasília", 1148, "Brasil", "Distrito Federal")
            ],
        }
    
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