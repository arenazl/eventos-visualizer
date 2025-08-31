"""
🏭 City Scraper Factory - Sistema dinámico por ciudad
Cada ciudad tiene sus scrapers específicos + scrapers globales
No más hardcodeados - completamente dinámico por geolocalización
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseCityScraper(ABC):
    """
    🏗️ Base class para todos los scrapers de ciudad
    """
    
    def __init__(self, city: str, country: str):
        self.city = city
        self.country = country
        self.scraper_name = self.__class__.__name__
    
    @abstractmethod
    async def fetch_events(self) -> List[Dict[str, Any]]:
        """Método que cada scraper debe implementar"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Info del scraper para debugging"""
        return {
            "name": self.scraper_name,
            "city": self.city,
            "country": self.country,
            "type": "city_specific"
        }

class BaseGlobalScraper(ABC):
    """
    🌐 Base class para scrapers globales (APIs)
    """
    
    def __init__(self):
        self.scraper_name = self.__class__.__name__
    
    @abstractmethod
    async def fetch_events(self, location: str) -> List[Dict[str, Any]]:
        """Método que cada scraper global debe implementar"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Info del scraper para debugging"""
        return {
            "name": self.scraper_name,
            "type": "global"
        }

# 🇦🇷 ARGENTINA - Buenos Aires Scrapers
class OleSportsScraperBA(BaseCityScraper):
    """Scraper de deportes específico para Buenos Aires"""
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        try:
            from .ole_sports_scraper import OleSportsScraper
            scraper = OleSportsScraper()
            if hasattr(scraper, 'fetch_sports_events'):
                return await scraper.fetch_sports_events("Buenos Aires")
        except Exception as e:
            logger.error(f"OleSportsScraperBA error: {e}")
        return []

class TeatroArgentinaScraper(BaseCityScraper):
    """Scraper de teatro específico para Buenos Aires"""
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        try:
            from .teatro_argentina_scraper import TeatroArgentinaScraper as TeatroScraper
            scraper = TeatroScraper()
            if hasattr(scraper, 'fetch_theater_events'):
                return await scraper.fetch_theater_events()
        except Exception as e:
            logger.error(f"TeatroArgentinaScraper error: {e}")
        return []

class ArgentinaCulturalScraper(BaseCityScraper):
    """Scraper cultural específico para Argentina"""
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        try:
            from .argentina_cultural_sports_scraper import ArgentinaCulturalSportsScraper
            scraper = ArgentinaCulturalSportsScraper()
            if hasattr(scraper, 'fetch_cultural_events'):
                return await scraper.fetch_cultural_events("Buenos Aires")
        except Exception as e:
            logger.error(f"ArgentinaCulturalScraper error: {e}")
        return []

# 🇪🇸 ESPAÑA - Madrid Scrapers
class MarcaMadridScraper(BaseCityScraper):
    """Scraper específico para deportes en Madrid"""
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        try:
            from .marca_madrid_scraper import MarcaMadridScraper as MarcaScraper
            scraper = MarcaScraper()
            if hasattr(scraper, 'fetch_madrid_sports'):
                return await scraper.fetch_madrid_sports()
        except Exception as e:
            logger.error(f"MarcaMadridScraper error: {e}")
        return []

class TimeoutMadridScraper(BaseCityScraper):
    """Scraper específico para eventos en Madrid"""
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        try:
            from .timeout_madrid_scraper import TimeoutMadridScraper as TimeoutScraper
            scraper = TimeoutScraper()
            if hasattr(scraper, 'fetch_madrid_events'):
                return await scraper.fetch_madrid_events()
        except Exception as e:
            logger.error(f"TimeoutMadridScraper error: {e}")
        return []

# 🇪🇸 ESPAÑA - Barcelona Scrapers  
class BarcelonaScraper(BaseCityScraper):
    """Scraper específico para eventos en Barcelona"""
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        try:
            from .barcelona_scraper import BarcelonaScraper as BcnScraper
            scraper = BcnScraper()
            if hasattr(scraper, 'fetch_barcelona_events'):
                return await scraper.fetch_barcelona_events()
        except Exception as e:
            logger.error(f"BarcelonaScraper error: {e}")
        return []

# 🇺🇸 USA - Miami Scrapers
class MiamiScraper(BaseCityScraper):
    """Scraper específico para eventos en Miami"""
    
    async def fetch_events(self) -> List[Dict[str, Any]]:
        try:
            from .miami_scraper import MiamiScraper as MiamiEventsScraper
            scraper = MiamiEventsScraper()
            if hasattr(scraper, 'fetch_miami_events'):
                result = await scraper.fetch_miami_events()
                # MiamiScraper retorna {"events": [...]} - extraer solo los eventos
                if isinstance(result, dict) and 'events' in result:
                    return result['events']
                return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"MiamiScraper error: {e}")
        return []

# 🌐 SCRAPERS GLOBALES (APIs con keys)
class EventbriteGlobalScraper(BaseGlobalScraper):
    """Eventbrite API - funciona en todo el mundo"""
    
    async def fetch_events(self, location: str) -> List[Dict[str, Any]]:
        try:
            from .eventbrite_api import EventbriteLatamConnector
            connector = EventbriteLatamConnector()
            return await connector.fetch_events_by_location(location)
        except Exception as e:
            logger.error(f"EventbriteGlobalScraper error: {e}")
        return []

class RapidApiFacebookScraper(BaseGlobalScraper):
    """Facebook via RapidAPI - funciona globalmente con endpoint real"""
    
    async def fetch_events(self, location: str) -> List[Dict[str, Any]]:
        try:
            logger.info(f"🔵 Facebook RapidAPI: INICIANDO para {location}")
            from .facebook_rapidapi_scraper import FacebookRapidApiScraper
            logger.info(f"🔵 Facebook RapidAPI: Import exitoso")
            scraper = FacebookRapidApiScraper()
            logger.info(f"🔵 Facebook RapidAPI: Scraper creado, ejecutando fetch_events...")
            result = await scraper.fetch_events(location)
            logger.info(f"🔵 Facebook RapidAPI: fetch_events completado, procesando resultado...")
            events = result.get("events", [])
            logger.info(f"🔵 Facebook RapidAPI devolvió {len(events)} eventos para {location}")
            return events
        except Exception as e:
            logger.error(f"❌ RapidApiFacebookScraper error: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return []

class TicketmasterGlobalScraper(BaseGlobalScraper):
    """Ticketmaster Discovery API - funciona globalmente"""
    
    async def fetch_events(self, location: str) -> List[Dict[str, Any]]:
        try:
            from .ticketmaster_global_scraper import TicketmasterGlobalScraper as TMScraper
            scraper = TMScraper()
            result = await scraper.fetch_events(location)
            return result.get("events", [])
        except Exception as e:
            logger.error(f"TicketmasterGlobalScraper error: {e}")
        return []

class EventfulGlobalScraper(BaseGlobalScraper):
    """Eventful API - funciona globalmente"""
    
    async def fetch_events(self, location: str) -> List[Dict[str, Any]]:
        try:
            from .eventful_global_scraper import EventfulGlobalScraper as EventfulScraper
            scraper = EventfulScraper()
            result = await scraper.fetch_events(location)
            return result.get("events", [])
        except Exception as e:
            logger.error(f"EventfulGlobalScraper error: {e}")
        return []

class SeatGeekGlobalScraper(BaseGlobalScraper):
    """SeatGeek API - funciona globalmente"""
    
    async def fetch_events(self, location: str) -> List[Dict[str, Any]]:
        try:
            from .seatgeek_global_scraper import SeatGeekGlobalScraper as SGScraper
            scraper = SGScraper()
            result = await scraper.fetch_events(location)
            return result.get("events", [])
        except Exception as e:
            logger.error(f"SeatGeekGlobalScraper error: {e}")
        return []

class InstagramRapidApiScraper(BaseGlobalScraper):
    """Instagram RapidAPI - funciona globalmente"""
    
    async def fetch_events(self, location: str) -> List[Dict[str, Any]]:
        try:
            from .instagram_rapidapi_scraper import InstagramRapidApiScraper as IGScraper
            scraper = IGScraper()
            result = await scraper.fetch_events(location)
            return result.get("events", [])
        except Exception as e:
            logger.error(f"InstagramRapidApiScraper error: {e}")
        return []

class CityScraperFactory:
    """
    🏭 Factory que crea scrapers específicos por ciudad + globales
    """
    
    def __init__(self):
        # 🏙️ CONFIGURACIÓN POR CIUDAD - Scrapers específicos
        self.city_scrapers = {
            # 🇦🇷 Argentina
            ("Argentina", "Buenos Aires"): [
                OleSportsScraperBA,
                TeatroArgentinaScraper,
                ArgentinaCulturalScraper
            ],
            ("Argentina", "Córdoba"): [
                ArgentinaCulturalScraper  # Cultura argentina general
            ],
            ("Argentina", "Mendoza"): [
                ArgentinaCulturalScraper  # Cultura argentina general
            ],
            
            # 🇪🇸 España
            ("Spain", "Madrid"): [
                MarcaMadridScraper,
                TimeoutMadridScraper
            ],
            ("Spain", "Barcelona"): [
                BarcelonaScraper
            ],
            
            # 🇺🇸 USA
            ("USA", "Miami"): [
                MiamiScraper
            ],
            
            # 🇮🇹 Italia - Solo scrapers globales (no city scrapers)
            ("Italy", "Rome"): [
                # No city-specific scrapers - solo globales para testing
            ]
        }
        
        # 🌐 SCRAPERS GLOBALES REMOVIDOS DEL FACTORY
        # Ahora están en capa separada para evitar duplicación
    
    def create_scrapers_for_location(self, country: str, city: str) -> Dict[str, Any]:
        """
        🎯 Método principal - Crea SOLO scrapers específicos de ciudad
        """
        scrapers = []
        city_specific = []
        
        # SOLO scrapers específicos de la ciudad
        city_key = (country, city)
        if city_key in self.city_scrapers:
            for scraper_class in self.city_scrapers[city_key]:
                try:
                    instance = scraper_class(city, country)
                    scrapers.append(instance)
                    city_specific.append(instance)
                    logger.info(f"✅ City scraper: {instance.scraper_name} for {city}, {country}")
                except Exception as e:
                    logger.error(f"❌ Error creating city scraper {scraper_class.__name__}: {e}")
        
        return {
            "city_scrapers": scrapers,
            "location": f"{city}, {country}",
            "total_count": len(scrapers)
        }
    
    async def execute_city_scrapers(self, country: str, city: str) -> Dict[str, Any]:
        """
        🏙️ Ejecuta SOLO scrapers específicos de ciudad
        """
        start_time = datetime.now()
        scrapers_data = self.create_scrapers_for_location(country, city)
        
        all_events = []
        scraper_results = {}
        location = f"{city}, {country}"
        
        logger.info(f"🏙️ INICIANDO execute_city_scrapers para {location}")
        logger.info(f"📋 Scrapers de ciudad disponibles: {len(scrapers_data['city_scrapers'])}")
        
        # Ejecutar SOLO scrapers específicos de ciudad
        for i, scraper in enumerate(scrapers_data["city_scrapers"]):
            try:
                logger.info(f"🏙️ Executing city scraper {i+1}/{len(scrapers_data['city_scrapers'])}: {scraper.scraper_name}")
                events = await scraper.fetch_events()
                
                logger.info(f"📊 {scraper.scraper_name}: Recibidos {len(events)} eventos del scraper")
                
                # Log primeros eventos para debug
                if events:
                    logger.info(f"📋 Primeros eventos de {scraper.scraper_name}:")
                    for j, event in enumerate(events[:3]):  # Primeros 3
                        title = event.get('title', 'Sin título')[:50]
                        venue = event.get('venue_name', 'Sin venue')[:30]
                        logger.info(f"   📌 Evento {j+1}: '{title}...' en '{venue}...'")
                
                # Antes de extend
                before_extend = len(all_events)
                all_events.extend(events)
                after_extend = len(all_events)
                
                logger.info(f"📊 CityFactory all_events: {before_extend} → {after_extend} (+{len(events)})")
                
                scraper_results[scraper.scraper_name] = {
                    "type": "city_specific",
                    "status": "success",
                    "events": len(events)
                }
            except Exception as e:
                logger.error(f"❌ City scraper {scraper.scraper_name} failed: {e}")
                scraper_results[scraper.scraper_name] = {
                    "type": "city_specific", 
                    "status": "error",
                    "events": 0,
                    "error": str(e)
                }
        
        logger.info(f"📊 TOTAL eventos antes de deduplicación en CityFactory: {len(all_events)}")
        
        # Eliminar duplicados
        unique_events = self._remove_duplicates(all_events)
        duplicates_removed = len(all_events) - len(unique_events)
        
        logger.info(f"🔄 CityFactory deduplicación: {duplicates_removed} duplicados removidos")
        logger.info(f"✅ CityFactory eventos únicos FINALES: {len(unique_events)}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎯 FINALIZANDO execute_city_scrapers para {location}")
        logger.info(f"📊 RESULTADO FINAL: {len(unique_events)} eventos únicos")
        logger.info(f"⏱️ Tiempo total: {execution_time:.2f}s")
        
        return {
            "status": "success",
            "location": location,
            "country": country,
            "city": city,
            "events": unique_events,
            "total_events": len(unique_events),
            "duplicates_removed": len(all_events) - len(unique_events),
            "execution_time": execution_time,
            "scrapers": scraper_results,
            "city_scrapers_count": len(scrapers_data["city_scrapers"]),
            "timestamp": datetime.now().isoformat()
        }
    
    def _remove_duplicates(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina duplicados por título"""
        logger.info(f"🔄 INICIANDO _remove_duplicates con {len(events)} eventos")
        seen_titles = set()
        unique_events = []
        duplicates_found = []
        
        for i, event in enumerate(events):
            title_key = event.get('title', '').lower().strip()
            
            if not title_key:
                logger.debug(f"❌ Evento {i+1}: título vacío - DESCARTADO")
                continue
            
            if len(title_key) <= 3:
                logger.debug(f"❌ Evento {i+1}: título muy corto '{title_key}' - DESCARTADO")
                continue
                
            if title_key in seen_titles:
                duplicates_found.append(title_key[:40])
                logger.debug(f"❌ Evento {i+1}: DUPLICADO '{title_key[:40]}...'")
                continue
                
            seen_titles.add(title_key)
            unique_events.append(event)
            logger.debug(f"✅ Evento {i+1}: ÚNICO '{title_key[:40]}...'")
        
        if duplicates_found:
            logger.info(f"📋 Duplicados encontrados en CityFactory ({len(duplicates_found)}):")
            for dup in duplicates_found[:5]:  # Mostrar primeros 5
                logger.info(f"   🔄 '{dup}...'")
            if len(duplicates_found) > 5:
                logger.info(f"   ... y {len(duplicates_found) - 5} más")
        
        logger.info(f"✅ _remove_duplicates TERMINADO: {len(unique_events)} únicos de {len(events)} totales")
        return unique_events

# 🔍 LOCATION PARSER - Convierte ubicación a (país, ciudad)
class LocationParser:
    """Mapea ubicaciones del mundo real a país/ciudad"""
    
    def __init__(self):
        self.location_mapping = {
            # 🇦🇷 Argentina
            "buenos aires": ("Argentina", "Buenos Aires"),
            "ba": ("Argentina", "Buenos Aires"),
            "bsas": ("Argentina", "Buenos Aires"),
            "caba": ("Argentina", "Buenos Aires"),
            "córdoba": ("Argentina", "Córdoba"),
            "cordoba": ("Argentina", "Córdoba"),
            "mendoza": ("Argentina", "Mendoza"),
            "rosario": ("Argentina", "Rosario"),
            "la plata": ("Argentina", "La Plata"),
            
            # 🇪🇸 España
            "madrid": ("Spain", "Madrid"),
            "barcelona": ("Spain", "Barcelona"),
            "bcn": ("Spain", "Barcelona"),
            "valencia": ("Spain", "Valencia"),
            "sevilla": ("Spain", "Sevilla"),
            "seville": ("Spain", "Sevilla"),
            "bilbao": ("Spain", "Bilbao"),
            
            # 🇺🇸 USA
            "miami": ("USA", "Miami"),
            "miami beach": ("USA", "Miami"),
            "new york": ("USA", "New York"),
            "nyc": ("USA", "New York"),
            "los angeles": ("USA", "Los Angeles"),
            "la": ("USA", "Los Angeles"),
            
            # 🇫🇷 Francia
            "paris": ("France", "Paris"),
            "marseille": ("France", "Marseille"),
            "lyon": ("France", "Lyon"),
            
            # 🇮🇹 Italia
            "rome": ("Italy", "Rome"),
            "roma": ("Italy", "Rome"),
            "milan": ("Italy", "Milan"),
            "milano": ("Italy", "Milan"),
            "florence": ("Italy", "Florence"),
            "firenze": ("Italy", "Florence"),
            
            # 🇬🇧 Reino Unido
            "london": ("UK", "London"),
            "manchester": ("UK", "Manchester")
        }
    
    def parse_location(self, location_str: str) -> tuple:
        """
        Convierte string de ubicación a (país, ciudad)
        """
        if not location_str:
            return "Argentina", "Buenos Aires"  # Fallback por defecto
            
        location_lower = location_str.lower().strip()
        
        # Buscar coincidencia exacta
        for key, (country, city) in self.location_mapping.items():
            if key == location_lower:
                return country, city
        
        # Buscar coincidencia parcial
        for key, (country, city) in self.location_mapping.items():
            if key in location_lower or location_lower in key:
                return country, city
        
        # Si no encuentra nada, fallback a Buenos Aires
        logger.warning(f"Location '{location_str}' not mapped, defaulting to Buenos Aires")
        return "Argentina", "Buenos Aires"


# 🌐 SCRAPERS GLOBALES SEPARADOS
class GlobalScrapersManager:
    """
    🌐 Manager para scrapers globales (APIs)
    Se ejecuta UNA SOLA VEZ por ubicación, no por cada ciudad
    """
    
    def __init__(self):
        self.global_scrapers = [
            # RapidAPI scrapers with API keys configured:
            RapidApiFacebookScraper,       # ✅ RAPIDAPI_KEY configured
            InstagramRapidApiScraper,      # ✅ RAPIDAPI_KEY configured
            
            # Commented out - external API issues:
            # EventbriteGlobalScraper,       # API deprecated since 2019
            
            # Temporarily commented out - pending API keys:
            # TicketmasterGlobalScraper,  # Need TICKETMASTER_API_KEY 
            # EventfulGlobalScraper,      # Need EVENTFUL_API_KEY
            # SeatGeekGlobalScraper       # Need SEATGEEK_CLIENT_ID
        ]
    
    async def execute_global_scrapers(self, location: str) -> Dict[str, Any]:
        """
        🌐 Ejecuta scrapers globales una sola vez
        """
        start_time = datetime.now()
        all_events = []
        scraper_results = {}
        
        for scraper_class in self.global_scrapers:
            try:
                instance = scraper_class()
                logger.info(f"🌐 Executing global scraper: {instance.scraper_name}")
                events = await instance.fetch_events(location)
                all_events.extend(events)
                scraper_results[instance.scraper_name] = {
                    "type": "global",
                    "status": "success", 
                    "events": len(events)
                }
            except Exception as e:
                logger.error(f"❌ Global scraper {scraper_class.__name__} failed: {e}")
                scraper_results[scraper_class.__name__] = {
                    "type": "global",
                    "status": "error",
                    "events": 0,
                    "error": str(e)
                }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "events": all_events,
            "scrapers": scraper_results,
            "execution_time": execution_time,
            "global_scrapers_count": len(self.global_scrapers)
        }

# 🚀 FUNCIÓN PRINCIPAL DE INTEGRACIÓN - ARQUITECTURA EN CAPAS
async def fetch_events_by_location(location: str) -> Dict[str, Any]:
    """
    🎯 Función principal - Arquitectura en capas optimizada
    
    1. Scrapers específicos por ciudad (Ole, Marca, Timeout, etc.)
    2. Scrapers globales UNA SOLA VEZ (Eventbrite, Facebook)
    
    Usage:
        result = await fetch_events_by_location("Madrid")
        result = await fetch_events_by_location("Miami")  
        result = await fetch_events_by_location("Buenos Aires")
    """
    parser = LocationParser()
    city_factory = CityScraperFactory()
    global_manager = GlobalScrapersManager()
    
    # Parsear ubicación
    country, city = parser.parse_location(location)
    logger.info(f"🌍 Location parsed: '{location}' → {country}, {city}")
    
    # 🏙️ CAPA 1: Scrapers específicos de ciudad
    city_result = await city_factory.execute_city_scrapers(country, city)
    
    # 🌐 CAPA 2: Scrapers globales (UNA SOLA VEZ)
    global_result = await global_manager.execute_global_scrapers(f"{city}, {country}")
    
    # Combinar resultados
    all_events = []
    all_events.extend(city_result.get("events", []))
    all_events.extend(global_result.get("events", []))
    
    # Eliminar duplicados finales
    unique_events = city_factory._remove_duplicates(all_events)
    
    # Combinar scrapers info
    all_scrapers = {}
    all_scrapers.update(city_result.get("scrapers", {}))
    all_scrapers.update(global_result.get("scrapers", {}))
    
    total_execution_time = city_result.get("execution_time", 0) + global_result.get("execution_time", 0)
    
    return {
        "status": "success",
        "location": city_result.get("location"),
        "country": city_result.get("country"),
        "city": city_result.get("city"),
        "events": unique_events,
        "total_events": len(unique_events),
        "duplicates_removed": len(all_events) - len(unique_events),
        "execution_time": total_execution_time,
        "scrapers": all_scrapers,
        "city_scrapers_count": city_result.get("city_scrapers_count", 0),
        "global_scrapers_count": global_result.get("global_scrapers_count", 0),
        "timestamp": datetime.now().isoformat()
    }