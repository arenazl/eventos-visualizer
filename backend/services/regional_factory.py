"""
🌍 REGIONAL FACTORY - Location-Specific Scraper Factory
Factory pattern for creating and managing region-specific event scrapers
"""

import asyncio
import logging
import importlib
import os
from typing import List, Dict, Any, Optional, Type
from pathlib import Path

from services.scraper_interface import BaseGlobalScraper
from services.url_discovery_service import UrlDiscoveryService

logger = logging.getLogger(__name__)

class RegionalFactory:
    """
    🌍 FÁBRICA REGIONAL DE SCRAPERS
    
    CARACTERÍSTICAS:
    - Auto-discovery de scrapers regionales
    - Factory pattern para instanciación por país/región
    - Mapeo inteligente de ubicación → scrapers específicos
    - Integración con scraper_interface estándar
    - Fallback a scrapers globales si no hay regionales
    """
    
    def __init__(self):
        """Inicializa la factory regional con auto-discovery"""
        self.regional_scrapers = {}  # Cache de scrapers por región
        self.country_mappings = {}   # Mapeo de países → scrapers
        # UrlDiscoveryService requires ai_service - skip for now since regional factory isn't being used
        self.url_discovery_service = None  # Will be injected when needed
        
        logger.info("🌍 Regional Factory inicializado")
        self._discover_regional_scrapers()
    
    def _discover_regional_scrapers(self):
        """
        🔍 AUTO-DISCOVERY DE SCRAPERS REGIONALES
        
        Busca automáticamente scrapers en regional_scrapers/ siguiendo convención:
        - argentina_scraper.py → Argentina
        - spain_scraper.py → España  
        - mexico_scraper.py → México
        """
        
        try:
            regional_path = Path(__file__).parent / "regional_scrapers"
            
            if not regional_path.exists():
                logger.info("📁 Directorio regional_scrapers no existe, creando...")
                regional_path.mkdir(exist_ok=True)
                return
            
            scraper_count = 0
            
            # Buscar archivos *_scraper.py
            for scraper_file in regional_path.glob("*_scraper.py"):
                try:
                    # Extraer nombre del país/región del filename
                    region_name = scraper_file.stem.replace("_scraper", "")
                    
                    # Importar el módulo dinámicamente
                    module_path = f"services.regional_scrapers.{scraper_file.stem}"
                    module = importlib.import_module(module_path)
                    
                    # Buscar la clase scraper (convención: {Region}Scraper)
                    class_name = f"{region_name.title()}Scraper"
                    
                    if hasattr(module, class_name):
                        scraper_class = getattr(module, class_name)
                        
                        # Verificar que hereda de BaseGlobalScraper
                        if issubclass(scraper_class, BaseGlobalScraper):
                            self.regional_scrapers[region_name] = scraper_class
                            scraper_count += 1
                            logger.info(f"✅ Regional scraper discovered: {region_name} → {class_name}")
                        else:
                            logger.warning(f"⚠️ {class_name} no hereda de BaseGlobalScraper")
                    else:
                        logger.warning(f"⚠️ Clase {class_name} no encontrada en {scraper_file}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error importando {scraper_file}: {str(e)}")
            
            logger.info(f"🌍 Regional Factory: {scraper_count} scrapers regionales descubiertos")
            
        except Exception as e:
            logger.error(f"❌ Error en discovery de scrapers regionales: {str(e)}")
    
    def _detect_region_from_location(self, location: str, detected_country: Optional[str] = None) -> Optional[str]:
        """
        🌏 DETECCIÓN INTELIGENTE DE REGIÓN
        
        Args:
            location: Ubicación de búsqueda
            detected_country: País detectado por IA (si disponible)
            
        Returns:
            Nombre de la región para buscar scraper específico
        """
        
        location_lower = location.lower()
        
        # Mapeo directo por país detectado por IA
        if detected_country:
            country_lower = detected_country.lower()
            
            country_mappings = {
                'argentina': 'argentina',
                'spain': 'spain',
                'españa': 'spain',
                'mexico': 'mexico',
                'méxico': 'mexico',
                'chile': 'chile',
                'colombia': 'colombia',
                'peru': 'peru',
                'perú': 'peru',
                'brazil': 'brazil',
                'brasil': 'brazil',
                'uruguay': 'uruguay',
                'ecuador': 'ecuador',
                'bolivia': 'bolivia',
                'venezuela': 'venezuela',
                'usa': 'usa',
                'united states': 'usa',
                'canada': 'canada',
                'france': 'france',
                'francia': 'france',
                'italy': 'italy',
                'italia': 'italy',
                'germany': 'germany',
                'alemania': 'germany',
                'uk': 'uk',
                'united kingdom': 'uk',
                'reino unido': 'uk'
            }
            
            for country_key, region_name in country_mappings.items():
                if country_key in country_lower:
                    if region_name in self.regional_scrapers:
                        logger.info(f"🎯 Región detectada por país IA: {detected_country} → {region_name}")
                        return region_name
        
        # Fallback: detección por ciudades conocidas
        city_mappings = {
            # Argentina
            'buenos aires': 'argentina',
            'córdoba': 'argentina', 
            'cordoba': 'argentina',
            'rosario': 'argentina',
            'mendoza': 'argentina',
            'salta': 'argentina',
            'tucumán': 'argentina',
            'tucuman': 'argentina',
            
            # España
            'madrid': 'spain',
            'barcelona': 'spain',
            'valencia': 'spain',
            'sevilla': 'spain',
            'bilbao': 'spain',
            
            # México
            'ciudad de mexico': 'mexico',
            'guadalajara': 'mexico',
            'monterrey': 'mexico',
            'cancun': 'mexico',
            'tijuana': 'mexico',
            
            # USA
            'new york': 'usa',
            'los angeles': 'usa',
            'chicago': 'usa',
            'miami': 'usa',
            'las vegas': 'usa',
            'san francisco': 'usa',
            
            # Brasil
            'são paulo': 'brazil',
            'rio de janeiro': 'brazil',
            'salvador': 'brazil',
            'brasília': 'brazil',
            'fortaleza': 'brazil'
        }
        
        for city_key, region_name in city_mappings.items():
            if city_key in location_lower:
                if region_name in self.regional_scrapers:
                    logger.info(f"🏙️ Región detectada por ciudad: {location} → {region_name}")
                    return region_name
        
        logger.info(f"🌐 No se detectó región específica para: {location}")
        return None
    
    async def get_regional_scrapers_for_location(
        self,
        location: str,
        detected_country: Optional[str] = None
    ) -> List[BaseGlobalScraper]:
        """
        🎯 OBTENER SCRAPERS REGIONALES PARA UBICACIÓN
        
        Args:
            location: Ubicación de búsqueda
            detected_country: País detectado por IA
            
        Returns:
            Lista de scrapers regionales instanciados para la ubicación
        """
        
        region = self._detect_region_from_location(location, detected_country)
        
        if not region:
            logger.info("🌍 No hay scrapers regionales específicos, usando solo globales")
            return []
        
        try:
            scraper_class = self.regional_scrapers[region]
            
            # Instanciar scraper con dependency injection
            # TODO: Properly inject ai_service when regional factory is implemented
            try:
                scraper_instance = scraper_class(url_discovery_service=self.url_discovery_service)
            except TypeError:
                # Fallback: try without url_discovery_service if constructor doesn't accept it
                scraper_instance = scraper_class()
            
            # Configurar contexto de región
            scraper_instance.context = {
                'region': region,
                'detected_country': detected_country or '',
                'detected_province': '',
                'location': location
            }
            
            logger.info(f"✅ Scraper regional instanciado: {region} para {location}")
            return [scraper_instance]
            
        except Exception as e:
            logger.error(f"❌ Error instanciando scraper regional {region}: {str(e)}")
            return []
    
    async def execute_regional_scrapers(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30,
        detected_country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        🚀 EJECUTAR SCRAPERS REGIONALES EN PARALELO
        
        Args:
            location: Ubicación de búsqueda
            category: Categoría opcional
            limit: Límite por scraper
            detected_country: País detectado por IA
            
        Returns:
            Lista consolidada de eventos regionales
        """
        
        regional_scrapers = await self.get_regional_scrapers_for_location(
            location, detected_country
        )
        
        if not regional_scrapers:
            logger.info("🌐 No hay scrapers regionales disponibles")
            return []
        
        logger.info(f"🌍 Ejecutando {len(regional_scrapers)} scrapers regionales para {location}")
        
        # Ejecutar scrapers en paralelo
        tasks = []
        for scraper in regional_scrapers:
            task = scraper.scrape_events(location, category, limit)
            tasks.append(task)
        
        # Esperar resultados con timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), 
                timeout=15.0
            )
            
            # Consolidar eventos exitosos
            all_events = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ Scraper regional {i} falló: {str(result)}")
                elif isinstance(result, list):
                    all_events.extend(result)
                    logger.info(f"✅ Scraper regional {i}: {len(result)} eventos")
            
            logger.info(f"🌍 Total eventos regionales: {len(all_events)}")
            return all_events
            
        except asyncio.TimeoutError:
            logger.warning("⚠️ Timeout en scrapers regionales")
            return []
        except Exception as e:
            logger.error(f"❌ Error ejecutando scrapers regionales: {str(e)}")
            return []
    
    def get_available_regions(self) -> List[str]:
        """
        📋 OBTENER REGIONES DISPONIBLES
        
        Returns:
            Lista de regiones con scrapers disponibles
        """
        return list(self.regional_scrapers.keys())
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """
        📊 ESTADÍSTICAS DE LA FACTORY REGIONAL
        
        Returns:
            Estadísticas de scrapers regionales disponibles
        """
        return {
            "total_regional_scrapers": len(self.regional_scrapers),
            "available_regions": self.get_available_regions(),
            "factory_status": "active",
            "discovery_method": "auto_scan",
            "scrapers_by_region": {
                region: scraper_class.__name__ 
                for region, scraper_class in self.regional_scrapers.items()
            }
        }

# Instancia singleton global
regional_factory = RegionalFactory()