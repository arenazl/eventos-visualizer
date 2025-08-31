"""
🏗️ Hierarchical Factory Architecture - Arquitectura Factory Jerárquica
- IScraper: Interfaz común con execute()
- CountryFactory: Factory por país que delega a provincias
- ProvincialFactory: Factory provincial específico
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

# 🔌 INTERFACE COMÚN
class IScraper(ABC):
    """
    🔌 Interfaz común - TODOS implementan execute()
    """
    
    @abstractmethod
    async def execute(self) -> List[Dict[str, Any]]:
        """Ejecutar scraper y retornar eventos"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del scraper para logging"""
        pass

# 🏭 FACTORY ABSTRACTO BASE
class BaseFactory(IScraper):
    """
    🏭 Factory base - maneja timing y logging automáticamente
    """
    
    def __init__(self, location: str):
        self.location = location
        self.start_time = None
        self.events = []
        
    async def execute(self) -> List[Dict[str, Any]]:
        """Template method - mide tiempo y logs automáticamente"""
        self.start_time = datetime.now()
        logger.info(f"🚀 INICIANDO: {self.name} para {self.location}")
        
        try:
            # Delegar a implementación específica
            self.events = await self._execute_internal()
            
            elapsed = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"✅ COMPLETADO: {self.name} - {len(self.events)} eventos en {elapsed:.2f}s")
            
            return self.events
            
        except Exception as e:
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            logger.error(f"❌ ERROR: {self.name} - {str(e)} ({elapsed:.2f}s)")
            return []
    
    @abstractmethod
    async def _execute_internal(self) -> List[Dict[str, Any]]:
        """Implementación específica del factory"""
        pass

# 🇦🇷 ARGENTINA COUNTRY FACTORY
class ArgentinaFactory(BaseFactory):
    """
    🇦🇷 Factory Argentina - maneja todo el país
    Si se especifica provincia, delega a ProvincialFactory
    Si no, ejecuta scrapers nacionales
    """
    
    def __init__(self, location: str, province: Optional[str] = None):
        super().__init__(location)
        self.province = province
        
    @property
    def name(self) -> str:
        if self.province:
            return f"Argentina_{self.province}_Factory"
        return "Argentina_National_Factory"
        
    async def _execute_internal(self) -> List[Dict[str, Any]]:
        """
        Lógica de Argentina:
        - Si tiene provincia específica -> usar ProvincialFactory
        - Si no -> usar scrapers nacionales
        """
        if self.province:
            logger.info(f"🏛️ Provincia específica detectada: {self.province}")
            provincial_factory = ArgentinaProvincialFactory(self.location, self.province)
            return await provincial_factory.execute()
        else:
            logger.info(f"🇦🇷 Ejecutando scrapers nacionales de Argentina")
            return await self._execute_national_scrapers()
    
    async def _execute_national_scrapers(self) -> List[Dict[str, Any]]:
        """Ejecutar scrapers a nivel nacional argentino"""
        try:
            # Import dinámico para evitar circular imports
            from api.multi_source import fetch_all_progressive
            
            # Usar multi_source para nivel nacional
            result = await fetch_all_progressive(location="Buenos Aires", fast=True)
            
            if result and "events" in result:
                return result["events"]
            return []
            
        except Exception as e:
            logger.error(f"❌ Error en scrapers nacionales Argentina: {e}")
            return []

# 🏛️ ARGENTINA PROVINCIAL FACTORY  
class ArgentinaProvincialFactory(BaseFactory):
    """
    🏛️ Factory Provincial Argentina - scrapers específicos por provincia
    """
    
    def __init__(self, location: str, province: str):
        super().__init__(location)
        self.province = province
        
    @property
    def name(self) -> str:
        return f"Argentina_{self.province}_Provincial"
        
    async def _execute_internal(self) -> List[Dict[str, Any]]:
        """
        Ejecutar scrapers provinciales específicos
        """
        logger.info(f"🏛️ Ejecutando scrapers provinciales para {self.province}")
        
        # Mapear provincia a scrapers específicos
        if self.province.lower() in ["córdoba", "cordoba"]:
            return await self._execute_cordoba_scrapers()
        elif self.province.lower() in ["mendoza"]:
            return await self._execute_mendoza_scrapers() 
        elif self.province.lower() in ["buenos aires", "buenosaires", "caba"]:
            return await self._execute_buenos_aires_scrapers()
        elif self.province.lower() == "generic":
            logger.info(f"🔍 Provincia genérica, intentando detectar desde ubicación: {self.location}")
            return await self._execute_generic_argentina_scrapers()
        else:
            logger.warning(f"⚠️ No hay scrapers específicos para {self.province}, usando genérico")
            return await self._execute_generic_argentina_scrapers()
    
    async def _execute_cordoba_scrapers(self) -> List[Dict[str, Any]]:
        """Scrapers específicos de Córdoba - usa multi_source que sabemos que funciona"""
        try:
            # Import local para evitar problemas
            import sys
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            # Usar multi_source directamente que sabemos que trae 15 eventos para Córdoba
            from api.multi_source import fetch_all_progressive
            
            result = await fetch_all_progressive(location="Córdoba", fast=True)
            
            if result and "events" in result:
                events = result["events"]
                logger.info(f"✅ Córdoba scrapers: {len(events)} eventos")
                return events
            else:
                logger.info("⚠️ Córdoba scrapers: 0 eventos")
                return []
            
        except Exception as e:
            logger.error(f"❌ Error en scrapers Córdoba: {e}")
            return []
    
    async def _execute_mendoza_scrapers(self) -> List[Dict[str, Any]]:
        """Scrapers específicos de Mendoza"""
        # TODO: Implementar scrapers Mendoza específicos
        logger.info("🍷 Mendoza scrapers - TODO")
        return []
    
    async def _execute_buenos_aires_scrapers(self) -> List[Dict[str, Any]]:
        """Scrapers específicos de Buenos Aires"""
        try:
            # Usar venues oficiales + multi_source
            from services.oficial_venues_scraper import OficialVenuesScraper
            from api.multi_source import fetch_all_progressive
            
            # Ejecutar en paralelo
            tasks = [
                self._get_oficial_venues_events(),
                fetch_all_progressive(location="Buenos Aires", fast=True)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_events = []
            for result in results:
                if isinstance(result, dict) and "events" in result:
                    all_events.extend(result["events"])
                elif isinstance(result, list):
                    all_events.extend(result)
            
            logger.info(f"✅ Buenos Aires scrapers: {len(all_events)} eventos")
            return all_events
            
        except Exception as e:
            logger.error(f"❌ Error en scrapers Buenos Aires: {e}")
            return []
    
    async def _get_oficial_venues_events(self) -> List[Dict[str, Any]]:
        """Helper para venues oficiales"""
        try:
            from services.oficial_venues_scraper import OficialVenuesScraper
            scraper = OficialVenuesScraper()
            return await scraper.scrape_all_venues()
        except Exception as e:
            logger.error(f"❌ Error venues oficiales: {e}")
            return []
    
    async def _execute_generic_argentina_scrapers(self) -> List[Dict[str, Any]]:
        """Scrapers genéricos para provincias sin implementación específica"""
        try:
            from api.multi_source import fetch_all_progressive
            
            result = await fetch_all_progressive(location=self.location, fast=True)
            
            if result and "events" in result:
                return result["events"]
            return []
            
        except Exception as e:
            logger.error(f"❌ Error scrapers genéricos Argentina: {e}")
            return []

# 🇪🇸 ESPAÑA COUNTRY FACTORY
class SpainFactory(BaseFactory):
    """
    🇪🇸 Factory España - maneja todo el país
    """
    
    def __init__(self, location: str, region: Optional[str] = None):
        super().__init__(location)
        self.region = region
        
    @property
    def name(self) -> str:
        if self.region:
            return f"Spain_{self.region}_Factory"
        return "Spain_National_Factory"
        
    async def _execute_internal(self) -> List[Dict[str, Any]]:
        """Lógica de España"""
        try:
            from api.multi_source import fetch_all_progressive
            
            # Usar multi_source para España
            result = await fetch_all_progressive(location=self.location, fast=True)
            
            if result and "events" in result:
                return result["events"]
            return []
            
        except Exception as e:
            logger.error(f"❌ Error en scrapers España: {e}")
            return []

# 🇺🇸 USA COUNTRY FACTORY  
class USAFactory(BaseFactory):
    """
    🇺🇸 Factory USA - maneja todo el país
    """
    
    def __init__(self, location: str, state: Optional[str] = None):
        super().__init__(location)
        self.state = state
        
    @property
    def name(self) -> str:
        if self.state:
            return f"USA_{self.state}_Factory"
        return "USA_National_Factory"
        
    async def _execute_internal(self) -> List[Dict[str, Any]]:
        """Lógica de USA"""
        try:
            from api.multi_source import fetch_all_progressive
            
            # Usar multi_source para USA
            result = await fetch_all_progressive(location=self.location, fast=True)
            
            if result and "events" in result:
                return result["events"]
            return []
            
        except Exception as e:
            logger.error(f"❌ Error en scrapers USA: {e}")
            return []

# 🌍 MASTER FACTORY - Entry Point
class MasterFactory:
    """
    🌍 Master Factory - Entry point que decide qué country factory usar
    """
    
    @staticmethod
    def create_scraper(location: str) -> IScraper:
        """
        Factory method principal - detecta país vs provincia
        🎯 REGLA CLAVE: Si es provincia específica → IR DIRECTO al Provincial Factory
        """
        location_lower = location.lower().strip()
        
        # 🏛️ PROVINCIAS ARGENTINAS - VAN DIRECTO AL PROVINCIAL (NO PASAN POR PAÍS)
        if any(keyword in location_lower for keyword in ["córdoba", "cordoba"]):
            logger.info("🏛️ Provincia específica detectada: Córdoba - DIRECTO a Provincial Factory")
            return ArgentinaProvincialFactory(location, province="Córdoba")
            
        elif any(keyword in location_lower for keyword in ["mendoza"]):
            logger.info("🏛️ Provincia específica detectada: Mendoza - DIRECTO a Provincial Factory")  
            return ArgentinaProvincialFactory(location, province="Mendoza")
            
        elif any(keyword in location_lower for keyword in ["buenos aires", "buenosaires", "caba"]):
            logger.info("🏛️ Provincia específica detectada: Buenos Aires - DIRECTO a Provincial Factory")
            return ArgentinaProvincialFactory(location, province="Buenos Aires")
            
        # 🇦🇷 ARGENTINA PAÍS COMPLETO - USA COUNTRY FACTORY
        elif any(keyword in location_lower for keyword in ["argentina", "arg"]):
            logger.info("🇦🇷 País completo detectado: Argentina - usando Country Factory")
            return ArgentinaFactory(location)
            
        # 🇪🇸 ESPAÑA
        elif any(keyword in location_lower for keyword in ["barcelona", "madrid", "valencia", "españa", "spain"]):
            return SpainFactory(location)
            
        # 🇺🇸 USA
        elif any(keyword in location_lower for keyword in ["miami", "new york", "los angeles", "usa", "united states"]):
            return USAFactory(location)
            
        # Fallback a Argentina provincial (más específico)
        else:
            logger.warning(f"⚠️ Ubicación no reconocida '{location}', usando Argentina Provincial como fallback")
            return ArgentinaProvincialFactory(location, province="Generic")

# 🎯 FUNCIÓN PRINCIPAL - Entry Point
async def get_events_hierarchical(location: str) -> Dict[str, Any]:
    """
    🎯 Entry point principal - usa architecture jerárquica
    """
    try:
        # Crear factory apropiado
        scraper = MasterFactory.create_scraper(location)
        
        # Ejecutar
        events = await scraper.execute()
        
        # Formato de respuesta
        return {
            "status": "success",
            "location": location,
            "scraper_used": scraper.name,
            "events": events,
            "count": len(events),
            "message": f"✅ {scraper.name}: {len(events)} eventos"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en factory jerárquico: {e}")
        return {
            "status": "error",
            "location": location,
            "events": [],
            "count": 0,
            "error": str(e),
            "message": f"❌ Error: {str(e)}"
        }