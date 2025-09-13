"""
🔍 SCRAPER DISCOVERY SYSTEM
Dynamic scraper loading and management
"""

import os
import importlib
import inspect
from typing import Dict, List, Type, Optional
from pathlib import Path
import asyncio

from .base import IScraper

class ScraperDiscovery:
    """
    Sistema de descubrimiento dinámico de scrapers
    """
    
    def __init__(self):
        self.scrapers: Dict[str, Type[IScraper]] = {}
        self.global_scrapers: Dict[str, Type[IScraper]] = {}
        self.regional_scrapers: Dict[str, Dict[str, Type[IScraper]]] = {}
        self.local_scrapers: Dict[str, Dict[str, Type[IScraper]]] = {}
        
    def discover_all(self) -> None:
        """
        Descubre todos los scrapers disponibles
        """
        base_path = Path(__file__).parent
        
        # Descubrir scrapers globales
        self._discover_in_folder(base_path / "global", self.global_scrapers)
        
        # Descubrir scrapers regionales (futuro)
        regional_path = base_path / "regional"
        if regional_path.exists():
            for region_folder in regional_path.iterdir():
                if region_folder.is_dir():
                    region_name = region_folder.name
                    self.regional_scrapers[region_name] = {}
                    self._discover_in_folder(region_folder, self.regional_scrapers[region_name])
        
        # Descubrir scrapers locales (futuro)
        local_path = base_path / "local"
        if local_path.exists():
            for country_folder in local_path.iterdir():
                if country_folder.is_dir():
                    country_name = country_folder.name
                    self.local_scrapers[country_name] = {}
                    self._discover_in_folder(country_folder, self.local_scrapers[country_name])
        
        # Combinar todos los scrapers
        self.scrapers.update(self.global_scrapers)
        for region_scrapers in self.regional_scrapers.values():
            self.scrapers.update(region_scrapers)
        for local_scrapers in self.local_scrapers.values():
            self.scrapers.update(local_scrapers)
            
    def _discover_in_folder(self, folder_path: Path, target_dict: Dict[str, Type[IScraper]]) -> None:
        """
        Descubre scrapers en una carpeta específica
        """
        if not folder_path.exists():
            return
            
        for file_path in folder_path.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
                
            module_name = file_path.stem
            
            try:
                # Construir el path del módulo relativo al directorio scrapers/
                # Si estamos en scrapers/discovery.py, el parent es scrapers/
                # Entonces los módulos en global/ serían scrapers.global.nombre
                relative_to_scrapers = file_path.relative_to(Path(__file__).parent)
                module_path = f"scrapers.{str(relative_to_scrapers).replace(os.sep, '.').replace('.py', '')}"
                
                # Importar el módulo
                module = importlib.import_module(module_path)
                
                # Buscar clases que implementen IScraper
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, IScraper) and 
                        obj != IScraper and
                        hasattr(obj, 'name')):
                        
                        scraper_name = obj.name
                        target_dict[scraper_name] = obj
                        print(f"✅ Descubierto scraper: {scraper_name} ({obj.__name__})")
                        
            except Exception as e:
                print(f"❌ Error cargando {module_name}: {e}")
    
    def get_scrapers_for_location(self, location: str, enabled_only: bool = True) -> List[Type[IScraper]]:
        """
        Obtiene scrapers apropiados para una ubicación
        
        Args:
            location: Ciudad, provincia/estado, país
            enabled_only: Solo devolver scrapers habilitados
            
        Returns:
            Lista de clases scraper
        """
        scrapers = []
        
        # Parsear ubicación
        parts = [p.strip() for p in location.split(",")]
        city = parts[0] if len(parts) > 0 else ""
        state = parts[1] if len(parts) > 1 else ""
        country = parts[2] if len(parts) > 2 else ""
        
        # Siempre incluir scrapers globales
        scrapers.extend(self.global_scrapers.values())
        
        # Agregar scrapers regionales si aplican
        # Por ejemplo, si es Argentina, buscar en regional/latam
        if country.lower() in ["argentina", "chile", "uruguay", "brasil", "mexico"]:
            if "latam" in self.regional_scrapers:
                scrapers.extend(self.regional_scrapers["latam"].values())
        
        # Agregar scrapers locales específicos del país
        country_key = self._normalize_country_name(country)
        if country_key in self.local_scrapers:
            scrapers.extend(self.local_scrapers[country_key].values())
        
        # Filtrar por habilitados si se requiere
        if enabled_only:
            scrapers = [s for s in scrapers if getattr(s, 'enabled', True)]
        
        # Ordenar por prioridad (menor número = mayor prioridad)
        scrapers.sort(key=lambda s: getattr(s, 'priority', 999))
        
        return scrapers
    
    def _normalize_country_name(self, country: str) -> str:
        """
        Normaliza el nombre del país para búsqueda
        """
        country_map = {
            "argentina": "argentina",
            "brasil": "brazil",
            "brazil": "brazil",
            "chile": "chile",
            "uruguay": "uruguay",
            "mexico": "mexico",
            "españa": "spain",
            "spain": "spain",
            "estados unidos": "usa",
            "united states": "usa",
            "usa": "usa"
        }
        
        return country_map.get(country.lower(), country.lower())
    
    async def run_scrapers_parallel(self, location: str, limit: int = 10) -> Dict[str, List]:
        """
        Ejecuta scrapers en paralelo para una ubicación
        
        Returns:
            Dict con resultados de cada scraper
        """
        scrapers = self.get_scrapers_for_location(location)
        results = {}
        
        if not scrapers:
            print(f"⚠️ No se encontraron scrapers para {location}")
            return results
        
        print(f"🔍 Ejecutando {len(scrapers)} scrapers para {location}")
        
        # Crear tareas para cada scraper
        tasks = []
        scraper_names = []
        
        for scraper_class in scrapers:
            try:
                scraper = scraper_class()
                task = asyncio.create_task(self._run_scraper_safe(scraper, location, limit))
                tasks.append(task)
                scraper_names.append(scraper.name)
            except Exception as e:
                print(f"❌ Error inicializando {scraper_class.__name__}: {e}")
        
        # Ejecutar todos en paralelo
        if tasks:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(scraper_names, completed_results):
                if isinstance(result, Exception):
                    print(f"❌ {name}: {result}")
                    results[name] = []
                else:
                    results[name] = result
                    print(f"✅ {name}: {len(result)} eventos")
        
        return results
    
    async def _run_scraper_safe(self, scraper: IScraper, location: str, limit: int) -> List:
        """
        Ejecuta un scraper con manejo de errores y timeout
        """
        try:
            # Aplicar timeout del scraper
            timeout = getattr(scraper, 'timeout', 10)
            
            async with asyncio.timeout(timeout):
                # Ejecutar scraping
                raw_data = await scraper.scrape(location, limit)
                
                # Normalizar output
                events = scraper.normalize_output(raw_data)
                
                return events
                
        except asyncio.TimeoutError:
            print(f"⏰ {scraper.name}: Timeout después de {timeout}s")
            return []
        except Exception as e:
            print(f"❌ {scraper.name}: {e}")
            return []


# Singleton para discovery
discovery = ScraperDiscovery()