"""
🏭 Country Scraper Factory - Patrón Factory con Reflection
Crea scrapers dinámicamente por país usando reflection
No más hardcoding - completamente dinámico
"""

import importlib
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

def distinct_by(lista, key):
    """Elimina duplicados usando una función key personalizada"""
    return list({key(x): x for x in lista}.values())

logger = logging.getLogger(__name__)

class ScraperResult:
    """
    📊 CLASE BASE PARA RESULTADOS - Como .NET/Java
    OBLIGATORIA para todos los scrapers - propiedades de debugging
    """
    def __init__(self, scraper_name: str):
        self.scraper_name = scraper_name
        
        # 🔍 PROPIEDADES OBLIGATORIAS (como .NET properties)
        self.status = "not_started"      # "not_started", "running", "completed", "failed" 
        self.event_count = 0             # Cantidad de eventos obtenidos
        self.execution_time = 0.0        # Tiempo en segundos
        self.error_message = None        # Si falló, por qué
        self.last_execution = None       # Timestamp ISO
        self.events = []                 # Lista de eventos obtenidos
    
    def to_dict(self) -> Dict[str, Any]:
        """Para inspector - convierte a dict"""
        return {
            "scraper_name": self.scraper_name,
            "status": self.status,
            "event_count": self.event_count,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "last_execution": self.last_execution,
            "events": self.events
        }

class BaseScraper(ABC):
    """
    🏗️ CLASE BASE SCRAPER - Como en .NET/Java
    Todos los scrapers HEREDAN de esta clase
    """
    
    def __init__(self, country: str, city: str):
        self.country = country
        self.city = city
        self.currency = self._get_currency()
        self.timezone = self._get_timezone()
        self.language = self._get_language()
        
        # 🔍 RESULTADO OBLIGATORIO - Cada scraper HEREDA esto
        self.result = ScraperResult(self.__class__.__name__)
    
    async def execute(self) -> List[Dict[str, Any]]:
        """
        🎯 TEMPLATE METHOD PATTERN - Wrapper que mide todo automáticamente
        Los hijos NO sobreescriben este método, sobreescriben _do_scraping()
        """
        import time
        from datetime import datetime
        
        # 🔍 ACTUALIZAR RESULTADO - status y timestamps
        self.result.status = "running"
        self.result.last_execution = datetime.now().isoformat()
        start_time = time.time()
        
        try:
            # Llamar al método abstracto que cada hijo implementa
            results = await self._do_scraping()
            
            # 🔍 ACTUALIZAR RESULTADO - event_count y status
            self.result.event_count = len(results) if results else 0
            self.result.status = "completed"
            self.result.error_message = None
            
            logger.info(f"✅ {self.result.scraper_name}: {self.result.event_count} eventos en {self.result.execution_time:.2f}s")
            return results
            
        except Exception as e:
            # 🔍 ACTUALIZAR RESULTADO - error y status
            self.result.status = "failed"
            self.result.error_message = str(e)
            self.result.event_count = 0
            
            logger.error(f"❌ {self.result.scraper_name}: FALLÓ - {self.result.error_message}")
            return []
            
        finally:
            # 🔍 ACTUALIZAR RESULTADO - execution_time
            self.result.execution_time = round(time.time() - start_time, 2)
    
    @abstractmethod
    async def _do_scraping(self) -> List[Dict[str, Any]]:
        """
        🎯 MÉTODO ABSTRACTO - Los hijos DEBEN implementar este método
        Acá va la lógica específica de scraping de cada hijo
        """
        pass
    
    def get_debug_info(self) -> Dict[str, Any]:
        """
        🔍 PARA INSPECTOR - Información de debugging
        Usa el ScraperResult para datos consistentes
        """
        debug_data = self.result.to_dict()
        debug_data.update({
            "country": self.country,
            "city": self.city,
            "currency": self.currency
        })
        return debug_data
    
    def _get_currency(self) -> str:
        currencies = {
            "USA": "USD",
            "Spain": "EUR", 
            "Argentina": "ARS",
            "UK": "GBP",
            "France": "EUR"
        }
        return currencies.get(self.country, "USD")
    
    def _get_timezone(self) -> str:
        timezones = {
            "USA": "America/New_York",
            "Spain": "Europe/Madrid",
            "Argentina": "America/Argentina/Buenos_Aires", 
            "UK": "Europe/London",
            "France": "Europe/Paris"
        }
        return timezones.get(self.country, "UTC")
    
    def _get_language(self) -> str:
        languages = {
            "USA": "en",
            "Spain": "es",
            "Argentina": "es",
            "UK": "en", 
            "France": "fr"
        }
        return languages.get(self.country, "en")


class CountryScraperFactory:
    """
    🏭 Factory que crea scrapers por país usando reflection
    """
    
    def __init__(self):
        # 🏭 FACTORY JERÁRQUICA COMPLETA - País → Región → Especialidad
        self.scraper_config = {
            "USA": {
                "Miami": {
                    "sports": "MiamiSportsScraper",
                    "music": "MiamiMusicScraper",
                    "cultural": "MiamiCulturalScraper",
                    "beach": "MiamiBeachScraper"
                },
                "NewYork": {
                    "sports": "NewYorkSportsScraper", 
                    "music": "NewYorkMusicScraper",
                    "broadway": "NewYorkBroadwayScraper",
                    "cultural": "NewYorkCulturalScraper"
                },
                "LosAngeles": {
                    "sports": "LosAngelesSportsScraper",
                    "music": "LosAngelesMusicScraper", 
                    "hollywood": "LosAngelesHollywoodScraper"
                }
            },
            "Spain": {
                "Barcelona": {
                    "sports": "BarcelonaSportsScraper",
                    "cultural": "BarcelonaCulturalScraper",
                    "beach": "BarcelonaBeachScraper",
                    "gaudi": "BarcelonaGaudiScraper"
                },
                "Madrid": {
                    "sports": "MadridSportsScraper",
                    "cultural": "MadridCulturalScraper", 
                    "nightlife": "MadridNightlifeScraper",
                    "museums": "MadridMuseumsScraper"
                },
                "Valencia": {
                    "cultural": "ValenciaCulturalScraper",
                    "beach": "ValenciaBeachScraper",
                    "paella": "ValenciaPaellaScraper"
                }
            },
            "Argentina": {
                "BuenosAires": {
                    "sports": "BuenosAiresSportsScraper",
                    "tango": "BuenosAiresTangoScraper",
                    "cultural": "BuenosAiresCulturalScraper",
                    "gastronomy": "BuenosAiresGastronomyScraper"
                },
                "Cordoba": {
                    "cultural": "CordobaCulturalScraper",
                    "music": "CordobaMusicScraper",
                    "universities": "CordobaUniversitiesScraper"
                },
                "Mendoza": {
                    "wine": "MendozaWineScraper",
                    "mountain": "MendozaMountainScraper",
                    "cultural": "MendozaCulturalScraper"
                }
            }
        }
    
    def create_country_scrapers(self, country: str, city: str, categories: List[str] = None) -> List[BaseScraper]:
        """
        🏭 FACTORY METHOD - Crea scrapers por reflection
        
        Args:
            country: "USA", "Spain", "Argentina"
            city: "Miami", "Barcelona", "BuenosAires" 
            categories: ["sports", "music"] o None para todos
        
        Returns:
            Lista de scrapers instanciados listos para .execute()
        """
        scrapers = []
        
        try:
            # Verificar si el país/ciudad existe
            if country not in self.scraper_config:
                logger.warning(f"⚠️ País '{country}' no configurado")
                return []
                
            if city not in self.scraper_config[country]:
                logger.warning(f"⚠️ Ciudad '{city}' no configurada para {country}")
                return []
            
            city_config = self.scraper_config[country][city]
            
            # Si no se especifican categorías, usar todas
            if not categories:
                categories = list(city_config.keys())
            
            # 🏭 FACTORY REAL: Usar scrapers reales que funcionan
            try:
                # Importar scrapers reales aquí para evitar circular imports
                from .real_scrapers import RealArgentinaScraper, RealSpainScraper, RealUSAScraper, GenericScraper
                
                # 🇦🇷 ARGENTINA - Usar scrapers argentinos reales
                if country.lower() in ["argentina", "arg"]:
                    scraper_instance = RealArgentinaScraper(country=country, city=city)
                    scrapers.append(scraper_instance)
                    logger.info(f"✅ FACTORY SUCCESS: Argentina scraper creado para {city}")
                    
                # 🇪🇸 ESPAÑA - Usar scrapers españoles reales  
                elif country.lower() in ["spain", "españa", "espana"]:
                    scraper_instance = RealSpainScraper(country=country, city=city)
                    scrapers.append(scraper_instance)
                    logger.info(f"✅ FACTORY SUCCESS: Spain scraper creado para {city}")
                    
                # 🇺🇸 USA - Usar scrapers USA reales
                elif country.lower() in ["usa", "united states", "us"]:
                    scraper_instance = RealUSAScraper(country=country, city=city)
                    scrapers.append(scraper_instance)
                    logger.info(f"✅ FACTORY SUCCESS: USA scraper creado para {city}")
                
                else:
                    # Scraper genérico para países no específicos
                    scraper_instance = GenericScraper(country=country, city=city)
                    scrapers.append(scraper_instance)
                    logger.info(f"✅ FACTORY SUCCESS: Generic scraper creado para {city}, {country}")
                    
            except ImportError as e:
                logger.error(f"❌ Error importando scrapers reales: {e}")
                return []
                        
        except Exception as e:
            logger.error(f"❌ Error en factory: {e}")
        
        return scrapers
    
    async def execute_all(self, country: str, city: str, categories: List[str] = None) -> Dict[str, Any]:
        """
        🚀 EXECUTE ALL - Ejecuta todos los scrapers de un país/ciudad
        """
        scrapers = self.create_country_scrapers(country, city, categories)
        
        if not scrapers:
            return {
                "status": "success",
                "country": country,
                "city": city,
                "events": [],
                "total_events": 0,
                "scrapers_executed": {},
                "message": f"No specific scrapers available for {city}, {country}. Try Buenos Aires for Argentine events."
            }
        
        all_events = []
        results = {}
        
        # 🔄 FOREACH PURO - Ejecutar todos los scrapers (como dijo el usuario)
        # Factory NO SABE qué hace cada scraper, solo llama execute()
        import asyncio
        tasks = []
        
        # 🔄 FOREACH: Cada scraper implementa BaseScraper.execute()
        for scraper in scrapers:
            task = self._execute_scraper_safe(scraper)
            tasks.append(task)
        
        scraper_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 🔄 FOREACH: Procesar ScraperResult sin saber qué scrapeó cada uno
        for i, result in enumerate(scraper_results):
            scraper = scrapers[i]
            scraper_name = scraper.__class__.__name__
            
            if isinstance(result, Exception):
                logger.error(f"❌ {scraper_name}: {result}")
                results[scraper_name] = {"status": "error", "events": 0}
            elif isinstance(result, ScraperResult):
                # Usar la propiedad events del ScraperResult
                events = result.events if hasattr(result, 'events') else []
                all_events.extend(events)
                results[scraper_name] = {"status": result.status, "events": len(events)}
                logger.info(f"✅ {scraper_name}: {len(events)} eventos (status: {result.status})")
            else:
                # Fallback para compatibilidad
                events = result if isinstance(result, list) else []
                all_events.extend(events)
                results[scraper_name] = {"status": "success", "events": len(events)}
                logger.info(f"✅ {scraper_name}: {len(events)} eventos (fallback)")
        
        # 🧹 ELIMINAR DUPLICADOS - Aplicar distinct_by por título del evento
        unique_events = distinct_by(all_events, lambda event: event.get('title', ''))
        logger.info(f"🧹 Duplicados eliminados: {len(all_events)} → {len(unique_events)} eventos únicos")
        
        # 🔍 DEBUG INFO - Agregar info de debugging al JSON existente
        debug_info = []
        for scraper in scrapers:
            debug_info.append(scraper.get_debug_info())
        
        return {
            "status": "success",
            "country": country,
            "city": city, 
            "events": unique_events,
            "total_events": len(unique_events),
            "duplicates_removed": len(all_events) - len(unique_events),
            "scrapers_executed": results,
            "currency": scrapers[0].currency if scrapers else "USD",
            "timezone": scrapers[0].timezone if scrapers else "UTC",
            # 🔍 DEBUG INFO - Solo para inspector (no se muestra en UI)
            "debug_scrapers": debug_info
        }
    
    async def _execute_scraper_safe(self, scraper: BaseScraper) -> ScraperResult:
        """Ejecuta un scraper de forma segura y devuelve ScraperResult"""
        try:
            result = await scraper.execute()
            return result
        except Exception as e:
            # Crear ScraperResult de error
            error_result = ScraperResult(scraper.__class__.__name__)
            error_result.status = "failed"
            error_result.error_message = str(e)
            error_result.events = []
            logger.error(f"Error executing {scraper.__class__.__name__}: {e}")
            return error_result


# 🔍 LOCATION PARSER - Convierte "Miami" → ("USA", "Miami")
class LocationParser:
    """Mapea ubicaciones a países/ciudades"""
    
    def __init__(self):
        self.location_mapping = {
            # 🇺🇸 USA
            "miami": ("USA", "Miami"),
            "miami beach": ("USA", "Miami"),
            "south beach": ("USA", "Miami"),
            "new york": ("USA", "NewYork"),
            "nyc": ("USA", "NewYork"),
            "manhattan": ("USA", "NewYork"),
            "brooklyn": ("USA", "NewYork"),
            "los angeles": ("USA", "LosAngeles"),
            "la": ("USA", "LosAngeles"),
            "hollywood": ("USA", "LosAngeles"),
            "beverly hills": ("USA", "LosAngeles"),
            
            # 🇪🇸 Spain
            "barcelona": ("Spain", "Barcelona"),
            "bcn": ("Spain", "Barcelona"),
            "madrid": ("Spain", "Madrid"),
            "valencia": ("Spain", "Valencia"),
            "sevilla": ("Spain", "Sevilla"),
            "seville": ("Spain", "Sevilla"),
            "bilbao": ("Spain", "Bilbao"),
            
            # 🇦🇷 Argentina  
            "buenos aires": ("Argentina", "BuenosAires"),
            "ba": ("Argentina", "BuenosAires"),
            "bsas": ("Argentina", "BuenosAires"),
            "caba": ("Argentina", "BuenosAires"),
            "córdoba": ("Argentina", "Cordoba"),
            "cordoba": ("Argentina", "Cordoba"),
            "mendoza": ("Argentina", "Mendoza"),
            "rosario": ("Argentina", "Rosario"),
            "la plata": ("Argentina", "LaPlata"),
            
            # 🇫🇷 France
            "paris": ("France", "Paris"),
            "marseille": ("France", "Marseille"),
            "lyon": ("France", "Lyon"),
            
            # 🇬🇧 UK
            "london": ("UK", "London"),
            "manchester": ("UK", "Manchester"),
            "liverpool": ("UK", "Liverpool")
        }
    
    def parse_location(self, location_str: str) -> tuple:
        """
        Convierte "Miami" → ("USA", "Miami")  
        """
        location_lower = location_str.lower().strip()
        
        # Debug print
        logger.info(f"🔍 LocationParser: Parsing '{location_str}' -> '{location_lower}'")
        
        for key, (country, city) in self.location_mapping.items():
            if key in location_lower:
                logger.info(f"✅ LocationParser: Match '{key}' -> {country}, {city}")
                return country, city
        
        # Fallback a Argentina Buenos Aires
        logger.warning(f"⚠️ LocationParser: No match found for '{location_str}', using fallback")
        return "Argentina", "BuenosAires"


# 🚀 FUNCIÓN PRINCIPAL PARA INTEGRATION
async def get_events_by_location(location: str, categories: List[str] = None) -> Dict[str, Any]:
    """
    🎯 FUNCIÓN PRINCIPAL - Entry point del sistema
    
    Usage:
        events = await get_events_by_location("Miami")
        events = await get_events_by_location("Barcelona", ["sports", "music"])
    """
    parser = LocationParser()
    factory = CountryScraperFactory()
    
    # Parse location
    country, city = parser.parse_location(location)
    logger.info(f"🌍 Parsed '{location}' → {country}, {city}")
    
    # Execute scrapers
    result = await factory.execute_all(country, city, categories)
    
    return result