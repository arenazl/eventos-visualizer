"""
🔍 AUTO-DISCOVERY ENGINE - Descubrimiento Automático de Scrapers
Sistema que descubre e instancia scrapers automáticamente desde el filesystem
"""

import os
import sys
import logging
import importlib
import inspect
from typing import Dict, Any, List, Type
from services.scraper_interface import BaseGlobalScraper

logger = logging.getLogger(__name__)

class AutoDiscoveryEngine:
    """
    🔍 MOTOR DE AUTO-DESCUBRIMIENTO
    
    FUNCIONALIDADES:
    - Escanea carpetas de scrapers automáticamente
    - Instancia scrapers dinámicamente
    - Categoriza por scope (global, regional, local)
    - Manejo de errores robusto
    - Patrón de inyección de dependencias
    """
    
    def __init__(self, base_path: str = None):
        """
        Inicializa el engine de auto-discovery
        
        Args:
            base_path: Ruta base de scrapers (default: auto-detectar)
        """
        if base_path:
            self.base_path = base_path
        else:
            # Auto-detectar ruta base - ahora apunta a services
            current_file = os.path.abspath(__file__)
            self.base_path = os.path.dirname(current_file)
        
        logger.info(f"🔍 Auto-Discovery inicializado en: {self.base_path}")
        
        # Cargar configuración de scrapers habilitados/deshabilitados
        self._load_scrapers_config()
        
        # Servicios que se inyectan a los scrapers
        self._initialize_services()
    
    def _load_scrapers_config(self):
        """🔧 Carga configuración de scrapers enabled/disabled desde JSON"""
        import json
        
        try:
            config_path = os.path.join(self.base_path, '../data/url_patterns_cache.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.scrapers_config = cache_data.get('patterns', {})
                    enabled_count = sum(1 for config in self.scrapers_config.values() if config.get('enabled', True))
                    disabled_count = len(self.scrapers_config) - enabled_count
                    logger.info(f"🔧 Config cargada: {enabled_count} habilitados, {disabled_count} deshabilitados")
            else:
                self.scrapers_config = {}
                logger.warning("⚠️ No se encontró config de scrapers, todos habilitados por defecto")
        except Exception as e:
            logger.error(f"❌ Error cargando config de scrapers: {e}")
            self.scrapers_config = {}
    
    def _is_scraper_enabled(self, scraper_name: str) -> bool:
        """🎯 Verifica si un scraper está habilitado"""
        config = self.scrapers_config.get(scraper_name, {})
        enabled = config.get('enabled', True)  # Por defecto habilitado si no está en config
        
        if not enabled:
            reason = config.get('disable_reason', 'Deshabilitado por configuración')
            logger.info(f"⛔ {scraper_name.title()}Scraper DESHABILITADO: {reason}")
        
        return enabled
    
    def _initialize_services(self):
        """Inicializa servicios para inyección de dependencias"""
        try:
            from services.url_discovery_service import UrlDiscoveryService
            from services.ai_service import GeminiAIService
            
            self.ai_service = GeminiAIService()
            self.url_discovery_service = UrlDiscoveryService(self.ai_service)
            
        except ImportError as e:
            logger.warning(f"⚠️ No se pudieron cargar servicios: {e}")
            self.ai_service = None
            self.url_discovery_service = None
    
    def discover_all_scrapers(self) -> Dict[str, Dict[str, Any]]:
        """
        🌟 DESCUBRIMIENTO COMPLETO DE SCRAPERS
        
        Returns:
            Diccionario organizado por categorías:
            {
                'global': {scraper_name: instance, ...},
                'regional': {country: {scraper_name: instance}},
                'local': {scraper_name: instance}
            }
        """
        
        scrapers_map = {
            'global': {},
            'regional': {},
            'local': {}
        }
        
        # 🌍 Descobrir scrapers globales
        global_scrapers = self._discover_global_scrapers()
        scrapers_map['global'] = global_scrapers
        logger.info(f"🌍 Encontrados {len(global_scrapers)} scrapers globales")
        
        # 🏛️ Descobrir scrapers regionales
        regional_scrapers = self._discover_regional_scrapers()
        scrapers_map['regional'] = regional_scrapers
        total_regional = sum(len(country_scrapers) for country_scrapers in regional_scrapers.values())
        logger.info(f"🏛️ Encontrados {total_regional} scrapers regionales en {len(regional_scrapers)} países")
        
        # 🏙️ Descobrir scrapers locales
        local_scrapers = self._discover_local_scrapers()
        scrapers_map['local'] = local_scrapers
        logger.info(f"🏙️ Encontrados {len(local_scrapers)} scrapers locales")
        
        # 📊 Resumen final
        total_scrapers = (
            len(global_scrapers) + 
            total_regional + 
            len(local_scrapers)
        )
        
        logger.info("📊 RESUMEN AUTO-DISCOVERY:")
        logger.info("=" * 50)
        logger.info(f"🌍 GLOBALES: {len(global_scrapers)} scrapers")
        for name in global_scrapers.keys():
            logger.info(f"  • {name.title()}Scraper ({name})")
        logger.info(f"🏛️ REGIONALES: {total_regional} scrapers en {len(regional_scrapers)} países")
        for country, scrapers in regional_scrapers.items():
            for scraper_name in scrapers.keys():
                logger.info(f"  • {scraper_name.title()}Scraper ({country})")
        logger.info(f"🏙️ LOCALES: {len(local_scrapers)} scrapers")
        for name in local_scrapers.keys():
            logger.info(f"  • {name.title()}Scraper ({name})")
        logger.info(f"🎯 TOTAL: {total_scrapers} scrapers descubiertos automáticamente")
        logger.info("=" * 50)
        
        return scrapers_map
    
    def _discover_global_scrapers(self) -> Dict[str, Any]:
        """
        🌍 DESCUBRIR SCRAPERS GLOBALES
        
        Busca scrapers en /global/ que funcionen en cualquier ubicación mundial
        """
        logger.info("🌍 Descubriendo scrapers GLOBALES...")
        
        global_path = os.path.join(self.base_path, 'global_scrapers')  # Buscar en /global_scrapers/
        
        if not os.path.exists(global_path):
            logger.warning(f"📁 Carpeta {global_path} no existe, saltando...")
            return {}
        
        scrapers = {}
        python_files = [f for f in os.listdir(global_path) if f.endswith('_scraper.py') and f != '__init__.py']
        
        logger.info(f"🔍 Buscando en {global_path}: {len(python_files)} archivos encontrados")
        
        for filename in python_files:
            try:
                scraper_name = filename.replace('.py', '').replace('_scraper', '')
                
                # 🎯 VERIFICAR FLAG ENABLED ANTES DE CARGAR
                if not self._is_scraper_enabled(scraper_name):
                    continue  # Saltar scrapers deshabilitados
                
                class_name = f"{scraper_name.title()}Scraper"
                module_name = f"services.global_scrapers.{filename[:-3]}"
                
                # Importar módulo dinámicamente
                module = importlib.import_module(module_name)
                scraper_class = getattr(module, class_name)
                
                # Verificar que hereda de BaseGlobalScraper
                if issubclass(scraper_class, BaseGlobalScraper):
                    # Instanciar con dependency injection
                    scraper_instance = scraper_class(self.url_discovery_service)
                    scrapers[scraper_name] = scraper_instance
                    logger.info(f"  ✅ Cargado: {class_name}")
                else:
                    logger.warning(f"  ⚠️ {class_name} no hereda de BaseGlobalScraper")
                    
            except Exception as e:
                logger.warning(f"  ❌ Error cargando {filename}: {str(e)}")
        
        return scrapers
    
    def _discover_regional_scrapers(self) -> Dict[str, Dict[str, Any]]:
        """
        🏛️ DESCUBRIR SCRAPERS REGIONALES
        
        Busca scrapers organizados por países en /regional/
        """
        logger.info("🏛️ Descubriendo scrapers REGIONALES...")
        
        regional_path = os.path.join(self.base_path, 'regional')
        
        if not os.path.exists(regional_path):
            logger.info("📁 Carpeta /regional/ no existe, saltando...")
            return {}
        
        regional_scrapers = {}
        
        # Iterar por países
        for country_folder in os.listdir(regional_path):
            country_path = os.path.join(regional_path, country_folder)
            
            if os.path.isdir(country_path):
                country_scrapers = self._load_scrapers_from_directory(
                    country_path, 
                    f"scrapers.regional.{country_folder}"
                )
                
                if country_scrapers:
                    regional_scrapers[country_folder] = country_scrapers
        
        return regional_scrapers
    
    def _discover_local_scrapers(self) -> Dict[str, Any]:
        """
        🏙️ DESCUBRIR SCRAPERS LOCALES
        
        Busca scrapers específicos de ciudades en /local/
        """
        logger.info("🏙️ Descubriendo scrapers LOCALES...")
        
        local_path = os.path.join(self.base_path, 'local')
        
        if not os.path.exists(local_path):
            logger.info("📁 Carpeta /local/ no existe, saltando...")
            return {}
        
        return self._load_scrapers_from_directory(local_path, "scrapers.local")
    
    def _load_scrapers_from_directory(self, directory: str, module_prefix: str) -> Dict[str, Any]:
        """
        📂 CARGADOR GENÉRICO DE SCRAPERS
        
        Carga scrapers desde un directorio específico
        """
        scrapers = {}
        
        if not os.path.exists(directory):
            return scrapers
        
        python_files = [f for f in os.listdir(directory) if f.endswith('.py') and f != '__init__.py']
        
        for filename in python_files:
            try:
                scraper_name = filename.replace('.py', '').replace('_scraper', '')
                class_name = f"{scraper_name.title()}Scraper"
                module_name = f"{module_prefix}.{filename[:-3]}"
                
                module = importlib.import_module(module_name)
                scraper_class = getattr(module, class_name)
                
                # Instanciar scraper
                scraper_instance = scraper_class(self.url_discovery_service)
                scrapers[scraper_name] = scraper_instance
                
            except Exception as e:
                logger.warning(f"❌ Error cargando {filename}: {str(e)}")
        
        return scrapers