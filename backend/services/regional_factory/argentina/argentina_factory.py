"""
🇦🇷 ARGENTINA REGIONAL FACTORY
Factory principal para scrapers regionales argentinos con eventos de prueba
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ArgentinaFactory:
    """
    🏛️ Factory Regional de Argentina
    
    Maneja scrapers específicos para diferentes ciudades argentinas:
    - Buenos Aires
    - Córdoba  
    - Rosario
    - Santa Fe
    - Salta
    - Mendoza
    """
    
    def __init__(self):
        self.country = "Argentina"
        self.supported_cities = [
            "Buenos Aires", "Córdoba", "Rosario", 
            "Santa Fe", "Salta", "Mendoza"
        ]
        
        # 🎭 Eventos de prueba por ciudad
        self.sample_events = {
            "Buenos Aires": [
                {
                    "title": "Tango en San Telmo - Espectáculo Nocturno",
                    "description": "Auténtico show de tango en el corazón de San Telmo con los mejores bailarines de Buenos Aires",
                    "venue_name": "El Querandí",
                    "venue_address": "Perú 302, San Telmo, Buenos Aires",
                    "start_datetime": (datetime.now() + timedelta(days=3)).isoformat(),
                    "category": "cultural",
                    "price": "3500",
                    "is_free": False,
                    "event_url": "https://www.elquerandi.com.ar/tango-show"
                },
                {
                    "title": "Feria de Mataderos - Folclore Argentino",
                    "description": "Tradicional feria dominical con música folclórica, danzas y artesanías típicas",
                    "venue_name": "Plaza de los Trabajadores",
                    "venue_address": "Av. Lisandro de la Torre y Av. de los Corrales, Mataderos",
                    "start_datetime": (datetime.now() + timedelta(days=5)).isoformat(),
                    "category": "cultural",
                    "price": None,
                    "is_free": True,
                    "event_url": "https://turismo.buenosaires.gob.ar/es/atractivo/feria-de-mataderos"
                },
                {
                    "title": "River Plate vs Boca Juniors - Superclásico",
                    "description": "El partido más importante del fútbol argentino en el Estadio Monumental",
                    "venue_name": "Estadio Monumental Antonio Vespucio Liberti",
                    "venue_address": "Av. Pres. Figueroa Alcorta 7597, Belgrano, Buenos Aires",
                    "start_datetime": (datetime.now() + timedelta(days=10)).isoformat(),
                    "category": "sports",
                    "price": "8000",
                    "is_free": False,
                    "event_url": "https://www.cariverplate.com.ar/"
                }
            ],
            "Córdoba": [
                {
                    "title": "Festival Nacional de Folclore de Cosquín",
                    "description": "El festival de folclore más importante de Argentina en el corazón de las sierras",
                    "venue_name": "Plaza Próspero Molina",
                    "venue_address": "Plaza Próspero Molina, Cosquín, Córdoba",
                    "start_datetime": (datetime.now() + timedelta(days=15)).isoformat(),
                    "category": "music",
                    "price": "2000",
                    "is_free": False,
                    "event_url": "https://www.cosquinfestival.com/"
                },
                {
                    "title": "Oktoberfest Villa General Belgrano",
                    "description": "Celebración de la cerveza artesanal en el pueblo alemán de Argentina",
                    "venue_name": "Centro de Villa General Belgrano",
                    "venue_address": "Av. San Martín, Villa General Belgrano, Córdoba",
                    "start_datetime": (datetime.now() + timedelta(days=12)).isoformat(),
                    "category": "food",
                    "price": "1500",
                    "is_free": False,
                    "event_url": "https://www.vgb.gov.ar/oktoberfest"
                }
            ],
            "Rosario": [
                {
                    "title": "Noche de los Museos Rosario",
                    "description": "Apertura nocturna gratuita de todos los museos de la ciudad con actividades especiales",
                    "venue_name": "Múltiples Museos",
                    "venue_address": "Centro Histórico, Rosario, Santa Fe",
                    "start_datetime": (datetime.now() + timedelta(days=7)).isoformat(),
                    "category": "cultural",
                    "price": None,
                    "is_free": True,
                    "event_url": "https://www.rosario.gob.ar/noche-museos"
                }
            ],
            "Santa Fe": [
                {
                    "title": "Festival Gastronómico Santa Fe",
                    "description": "Muestra de la mejor gastronomía santafesina con chefs locales e internacionales",
                    "venue_name": "Centro de Convenciones",
                    "venue_address": "Bv. Pellegrini 3100, Santa Fe",
                    "start_datetime": (datetime.now() + timedelta(days=8)).isoformat(),
                    "category": "food",
                    "price": "2500",
                    "is_free": False,
                    "event_url": "https://www.santafe.gob.ar/festival-gastronomico"
                }
            ],
            "Salta": [
                {
                    "title": "Carnaval de Salta - Corso de la Alegría",
                    "description": "Celebración tradicional del carnaval norteño con comparsas y música folclórica",
                    "venue_name": "Av. Belgrano",
                    "venue_address": "Av. Belgrano, Salta Capital",
                    "start_datetime": (datetime.now() + timedelta(days=20)).isoformat(),
                    "category": "cultural",
                    "price": None,
                    "is_free": True,
                    "event_url": "https://www.salta.gob.ar/carnaval"
                }
            ],
            "Mendoza": [
                {
                    "title": "Fiesta Nacional de la Vendimia",
                    "description": "La celebración más importante de Mendoza honrando la tradición vitivinícola",
                    "venue_name": "Teatro Griego Frank Romero Day",
                    "venue_address": "Parque General San Martín, Mendoza",
                    "start_datetime": (datetime.now() + timedelta(days=25)).isoformat(),
                    "category": "cultural",
                    "price": "4000",
                    "is_free": False,
                    "event_url": "https://www.vendimia.mendoza.gov.ar/"
                },
                {
                    "title": "Ruta del Vino Mendoza - Tour Gastronómico",
                    "description": "Experiencia enológica por las mejores bodegas de Maipú y Luján de Cuyo",
                    "venue_name": "Múltiples Bodegas",
                    "venue_address": "Maipú y Luján de Cuyo, Mendoza",
                    "start_datetime": (datetime.now() + timedelta(days=6)).isoformat(),
                    "category": "food",
                    "price": "12000",
                    "is_free": False,
                    "event_url": "https://www.rutadelvino.mendoza.gov.ar/"
                }
            ]
        }

    def get_supported_cities(self) -> List[str]:
        """
        📋 Retorna ciudades soportadas por el factory argentino
        
        Returns:
            List[str]: Lista de ciudades soportadas
        """
        return self.supported_cities.copy()

    def is_city_supported(self, city: str) -> bool:
        """
        🔍 Verifica si una ciudad está soportada
        
        Args:
            city: Nombre de la ciudad
            
        Returns:
            bool: True si está soportada
        """
        city_normalized = city.strip().title()
        return any(supported.lower() in city_normalized.lower() 
                  for supported in self.supported_cities)

    async def get_events(self, location: str, category: Optional[str] = None, limit: int = 30) -> Dict[str, Any]:
        """
        🎯 Obtiene eventos para una ubicación argentina específica
        
        Args:
            location: Ciudad argentina
            category: Categoría opcional de eventos
            limit: Límite de eventos
            
        Returns:
            Dict con eventos encontrados
        """
        start_time = time.time()
        logger.info(f"🇦🇷 Argentina Factory: Buscando eventos en {location}")
        
        try:
            # Normalizar nombre de ciudad
            city = self._normalize_city_name(location)
            
            if not self.is_city_supported(city):
                logger.warning(f"⚠️ Ciudad no soportada: {city}")
                return {
                    "events": [],
                    "count": 0,
                    "source": "argentina_factory",
                    "city": city,
                    "supported": False,
                    "message": f"Ciudad {city} no disponible en Argentina Factory"
                }
            
            # Obtener eventos de la ciudad
            city_events = self.sample_events.get(city, [])
            
            # Filtrar por categoría si se especifica
            if category:
                category_lower = category.lower()
                filtered_events = [
                    event for event in city_events 
                    if event.get("category", "").lower() == category_lower
                ]
                city_events = filtered_events
            
            # Aplicar límite
            if limit:
                city_events = city_events[:limit]
            
            # Agregar metadatos a cada evento
            processed_events = []
            for event in city_events:
                processed_event = event.copy()
                processed_event.update({
                    "source": "argentina_regional",
                    "country": "Argentina",
                    "city": city,
                    "scraped_at": datetime.now().isoformat(),
                    "external_id": f"ar_{city.lower()}_{len(processed_events) + 1}"
                })
                processed_events.append(processed_event)
            
            execution_time = time.time() - start_time
            
            logger.info(f"🇦🇷 Argentina Factory: {len(processed_events)} eventos encontrados en {city} ({execution_time:.2f}s)")
            
            return {
                "events": processed_events,
                "count": len(processed_events),
                "source": "argentina_factory",
                "city": city,
                "supported": True,
                "execution_time": f"{execution_time:.2f}s",
                "scrapers_execution": {
                    "summary": f"Argentina Factory: {len(processed_events)} eventos en {city}",
                    "total_scrapers": 1,
                    "scrapers_info": [{
                        "name": f"Argentina-{city}",
                        "status": "success",
                        "events_count": len(processed_events),
                        "response_time": f"{execution_time:.2f}s",
                        "message": f"✅ Eventos regionales de {city}"
                    }]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error en Argentina Factory: {e}")
            return {
                "events": [],
                "count": 0,
                "source": "argentina_factory",
                "error": str(e),
                "execution_time": f"{time.time() - start_time:.2f}s"
            }

    def _normalize_city_name(self, location: str) -> str:
        """
        🔧 Normaliza el nombre de la ciudad
        
        Args:
            location: Ubicación original
            
        Returns:
            str: Nombre normalizado
        """
        # Limpiar y normalizar
        location = location.strip().replace(',', '').replace('Argentina', '').strip()
        
        # Mapeo de nombres comunes
        city_mapping = {
            "buenos aires": "Buenos Aires",
            "ba": "Buenos Aires",
            "caba": "Buenos Aires",
            "capital federal": "Buenos Aires",
            "cordoba": "Córdoba",
            "córdoba": "Córdoba",
            "rosario": "Rosario",
            "santa fe": "Santa Fe",
            "salta": "Salta",
            "mendoza": "Mendoza"
        }
        
        location_lower = location.lower()
        for key, value in city_mapping.items():
            if key in location_lower:
                return value
                
        return location.title()

# Instancia global del factory
argentina_factory = ArgentinaFactory()