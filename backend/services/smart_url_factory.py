"""
🏭 SMART URL FACTORY - Generación inteligente de URLs con Gemini + Patrones JSON
Sistema híbrido que combina análisis de intenciones con patrones preconfigurados
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SmartUrlFactory:
    """
    🏭 FACTORY INTELIGENTE DE URLs
    
    CARACTERÍSTICAS:
    - Usa datos de Gemini (país-provincia-ciudad) para determinar factory
    - Carga patrones JSON para cada servicio
    - Genera URLs globales y regionales automáticamente
    - Aplica reglas de formateo por servicio
    """
    
    def __init__(self):
        """Inicializa el factory con patrones JSON"""
        self.patterns = {}
        self.load_patterns()
        self.ticketmaster_scraper = None  # Lazy loading del scraper
        logger.info("🏭 Smart URL Factory inicializado")
    
    def load_patterns(self):
        """
        📂 CARGAR PATRONES DESDE JSON
        
        Carga los patrones de URL desde el archivo JSON
        """
        try:
            patterns_file = Path(__file__).parent.parent / "data" / "url_patterns_cache.json"
            
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
                    logger.info(f"✅ Patrones cargados: {len(self.patterns.get('global_services', {}))} servicios globales")
            else:
                logger.warning("⚠️ Archivo de patrones no encontrado, usando fallbacks")
                self.patterns = self._get_fallback_patterns()
                
        except Exception as e:
            logger.error(f"❌ Error cargando patrones: {e}")
            self.patterns = self._get_fallback_patterns()
    
    async def generate_urls_for_location(self, intent_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        🌐 GENERAR URLs PARA UBICACIÓN DETECTADA
        
        Args:
            intent_result: Resultado del análisis de intenciones con Gemini
            
        Returns:
            Dict con URLs organizadas por tipo (global, regional)
        """
        
        try:
            intent = intent_result.get('intent', {})
            hierarchy = intent.get('geographic_hierarchy', {})
            scraper_config = intent.get('scraper_config', {})
            
            # Datos geográficos de Gemini
            country = hierarchy.get('country', '').lower()
            city = hierarchy.get('city', '')
            region = hierarchy.get('region', '')
            country_code = hierarchy.get('country_code', '')
            
            logger.info(f"🏭 Generando URLs para: {city}, {region}, {country}")
            
            result = {
                "global_urls": [],
                "regional_urls": [],
                "metadata": {
                    "location": f"{city}, {country}",
                    "country_code": country_code,
                    "total_services": 0
                }
            }
            
            # 1. GENERAR URLs GLOBALES Y EXTRAER EVENTOS
            global_services = scraper_config.get('global_apis', [])
            for service in global_services:
                if service == 'ticketmaster':
                    # Para Ticketmaster, extraer eventos directamente con Playwright
                    events = await self._extract_ticketmaster_events(hierarchy)
                    result["global_urls"].extend([{"service": service, "events": events, "urls": []}])
                else:
                    # Para otros servicios, generar URLs como antes
                    urls = self._generate_global_urls(service, hierarchy)
                    if urls:
                        result["global_urls"].extend([{"service": service, "urls": urls, "events": []}])
                    
            # 2. GENERAR URLs REGIONALES
            local_scrapers = scraper_config.get('local_scrapers', [])
            for scraper in local_scrapers:
                urls = self._generate_regional_urls(scraper, hierarchy, country)
                if urls:
                    result["regional_urls"].extend([{"service": scraper, "urls": urls}])
            
            result["metadata"]["total_services"] = len(result["global_urls"]) + len(result["regional_urls"])
            
            logger.info(f"✅ URLs generadas: {result['metadata']['total_services']} servicios")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generando URLs: {e}")
            return {"global_urls": [], "regional_urls": [], "metadata": {"error": str(e)}}
    
    def _generate_global_urls(self, service: str, hierarchy: Dict[str, Any]) -> List[str]:
        """
        🌍 GENERAR URLs DE SERVICIOS GLOBALES CON FALLBACK JERÁRQUICO
        
        Args:
            service: Nombre del servicio (eventbrite, ticketmaster, etc.)
            hierarchy: Jerarquía geográfica de Gemini
            
        Returns:
            Lista de URLs generadas para el servicio (con fallbacks)
        """
        
        try:
            global_services = self.patterns.get('global_services', {})
            service_config = global_services.get(service.lower())
            
            if not service_config:
                logger.warning(f"⚠️ Servicio global no encontrado: {service}")
                return []
            
            country = hierarchy.get('country', '').lower()
            city = hierarchy.get('city', '')
            region = hierarchy.get('region', '')  # Provincia/Estado
            country_code = hierarchy.get('country_code', '')
            
            # Aplicar reglas de formateo
            formatted_city = self._format_location(city, 'city')
            formatted_region = self._format_location(region, 'province')
            formatted_country = self._format_location(country, 'country')
            
            # Obtener dominio específico por país
            domains = service_config.get('domains', {})
            domain = domains.get(country, domains.get('default', 'com'))
            
            # Construir URL base
            base_url = service_config.get('base_url', '').format(domain=domain)
            pattern = service_config.get('pattern', '')
            
            urls = []
            
            # SISTEMA DE FALLBACK JERÁRQUICO
            if service.lower() == 'eventbrite':
                urls = self._generate_eventbrite_fallback_urls(
                    base_url, pattern, service_config, country, 
                    formatted_city, formatted_region, formatted_country
                )
            elif service.lower() == 'meetup':
                urls = self._generate_meetup_fallback_urls(
                    base_url, pattern, service_config, country,
                    formatted_city, formatted_region, country_code
                )
            elif service.lower() == 'ticketmaster':
                urls = self._generate_ticketmaster_fallback_urls(
                    base_url, pattern, city, region, country
                )
            else:
                # Servicios sin fallback especial
                url_path = pattern.format(
                    city=formatted_city,
                    country=formatted_country,
                    country_code=country_code
                )
                urls = [f"{base_url}{url_path}"]
            
            for i, url in enumerate(urls, 1):
                logger.info(f"🔗 {service.upper()} (Nivel {i}): {url}")
            
            return urls
            
        except Exception as e:
            logger.error(f"❌ Error generando URL global para {service}: {e}")
            return []
    
    def _generate_eventbrite_fallback_urls(self, base_url: str, pattern: str, config: Dict, 
                                         country: str, city: str, region: str, country_name: str) -> List[str]:
        """
        🎫 GENERAR URLs DE EVENTBRITE CON FALLBACK JERÁRQUICO
        
        Fallback: Ciudad → Región/Provincia → País
        FORMATO REAL QUE FUNCIONA: /d/argentina--santa-fe/all-events/
        """
        
        urls = []
        country_mapping = config.get('country_names', {})
        final_country_name = country_mapping.get(country, country_name)
        
        # 1. NIVEL 1: Ciudad específica (Rosario)
        if city:
            # Formato: /d/argentina--rosario/all-events/
            url_path = f"{final_country_name}--{city}/all-events/"
            urls.append(f"{base_url}{url_path}")
        
        # 2. NIVEL 2: Región/Provincia (Santa Fe) - FORMATO COMPROBADO
        if region and region != city:
            # Formato: /d/argentina--santa-fe/all-events/
            url_path = f"{final_country_name}--{region}/all-events/"
            urls.append(f"{base_url}{url_path}")
        
        # 3. NIVEL 3: País completo (Argentina)
        if final_country_name:
            # Formato: /d/argentina/events/
            url_path = f"{final_country_name}/events/"
        else:
            url_path = "events/"
        urls.append(f"{base_url}{url_path}")
        
        return urls
    
    def _generate_meetup_fallback_urls(self, base_url: str, pattern: str, config: Dict,
                                     country: str, city: str, region: str, country_code: str) -> List[str]:
        """
        👥 GENERAR URLs DE MEETUP CON FALLBACK JERÁRQUICO
        """
        
        urls = []
        locales = config.get('locales', {})
        locale = locales.get(country, locales.get('default', 'en-US'))
        
        # 1. NIVEL 1: Ciudad específica
        if city:
            url_path = pattern.format(locale=locale, country_code=country_code, city=city)
            urls.append(f"{base_url}{url_path}")
        
        # 2. NIVEL 2: Región/Provincia
        if region and region != city:
            url_path = pattern.format(locale=locale, country_code=country_code, city=region)
            urls.append(f"{base_url}{url_path}")
        
        # 3. NIVEL 3: Búsqueda general por país
        url_path = f"{locale}/find/?source=EVENTS&location={country_code}"
        urls.append(f"{base_url}{url_path}")
        
        return urls
    
    def _generate_ticketmaster_fallback_urls(self, base_url: str, pattern: str, 
                                           city: str, region: str, country: str) -> List[str]:
        """
        🎪 GENERAR URLs DE TICKETMASTER CON FALLBACK JERÁRQUICO
        """
        
        urls = []
        
        # 1. NIVEL 1: Ciudad específica
        if city:
            url_path = pattern.format(city=city)
            urls.append(f"{base_url}{url_path}")
        
        # 2. NIVEL 2: Región/Provincia
        if region and region != city:
            url_path = pattern.format(city=region)
            urls.append(f"{base_url}{url_path}")
        
        # 3. NIVEL 3: Búsqueda general
        url_path = "discovery/events/"
        urls.append(f"{base_url}{url_path}")
        
        return urls
    
    def _generate_regional_urls(self, scraper: str, hierarchy: Dict[str, Any], country: str) -> List[str]:
        """
        🏛️ GENERAR URLs DE SERVICIOS REGIONALES
        
        Args:
            scraper: Nombre del scraper regional
            hierarchy: Jerarquía geográfica de Gemini
            country: País detectado
            
        Returns:
            Lista de URLs generadas para el scraper regional
        """
        
        try:
            regional_services = self.patterns.get('regional_services', {})
            country_services = regional_services.get(country.lower(), {})
            service_config = country_services.get(scraper.lower())
            
            if not service_config:
                logger.warning(f"⚠️ Scraper regional no encontrado: {scraper} para {country}")
                return []
            
            city = hierarchy.get('city', '')
            region = hierarchy.get('region', '')
            
            # Aplicar reglas de formateo
            formatted_city = self._format_location(city, 'city')
            formatted_region = self._format_location(region, 'province')
            
            # Construir URL
            base_url = service_config.get('base_url', '')
            pattern = service_config.get('pattern', '')
            
            # Reemplazar variables
            url_path = pattern.format(
                city=formatted_city,
                province=formatted_region,
                region=formatted_region
            )
            
            final_url = f"{base_url}{url_path}"
            logger.info(f"🏛️ {scraper.upper()} ({country}): {final_url}")
            
            return [final_url]
            
        except Exception as e:
            logger.error(f"❌ Error generando URL regional para {scraper}: {e}")
            return []
    
    async def _extract_ticketmaster_events(self, hierarchy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        🎪 EXTRAER EVENTOS DE TICKETMASTER CON FALLBACK JERÁRQUICO
        
        Args:
            hierarchy: Jerarquía geográfica de Gemini
            
        Returns:
            Lista de eventos extraídos de Ticketmaster
        """
        
        try:
            # Lazy loading del scraper
            if not self.ticketmaster_scraper:
                from services.ticketmaster_playwright_scraper import TicketmasterPlaywrightScraper
                self.ticketmaster_scraper = TicketmasterPlaywrightScraper()
                logger.info("🎪 Ticketmaster scraper inicializado en Factory")
            
            country = hierarchy.get('country', '').lower()
            city = hierarchy.get('city', '')
            region = hierarchy.get('region', '')
            
            logger.info(f"🎪 Ticketmaster Factory: Extrayendo eventos para {city}, {region}, {country}")
            
            # FALLBACK JERÁRQUICO AUTOMÁTICO
            events = []
            max_events = 10
            
            # 1. NIVEL 1: Ciudad específica
            if city:
                logger.info(f"🥇 Ticketmaster: Probando ciudad '{city}'")
                events = await self.ticketmaster_scraper.search_by_location(city, country)
                if events:
                    logger.info(f"✅ Ticketmaster ciudad: {len(events)} eventos encontrados")
                    return events[:max_events]
            
            # 2. NIVEL 2: Región/Provincia (fallback)
            if not events and region and region != city:
                logger.info(f"🥈 Ticketmaster: Probando provincia '{region}' (fallback)")
                events = await self.ticketmaster_scraper.search_by_location(region, country)
                if events:
                    logger.info(f"✅ Ticketmaster provincia: {len(events)} eventos encontrados")
                    return events[:max_events]
            
            # 3. NIVEL 3: País completo (último fallback)
            if not events and country:
                logger.info(f"🥉 Ticketmaster: Probando país '{country}' (último fallback)")
                events = await self.ticketmaster_scraper.search_events(country, country, max_events)
                if events:
                    logger.info(f"✅ Ticketmaster país: {len(events)} eventos encontrados")
                    return events[:max_events]
            
            logger.warning("⚠️ Ticketmaster: No se encontraron eventos en ningún nivel del fallback")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo eventos de Ticketmaster en Factory: {e}")
            return []
    
    def _format_location(self, location: str, location_type: str) -> str:
        """
        ✨ FORMATEAR UBICACIÓN SEGÚN REGLAS
        
        Args:
            location: Ubicación a formatear
            location_type: Tipo (city, country, province)
            
        Returns:
            Ubicación formateada según las reglas
        """
        
        if not location:
            return ""
        
        try:
            formatting_rules = self.patterns.get('formatting_rules', {})
            rules = formatting_rules.get(location_type, {})
            
            formatted = location
            
            # Aplicar reglas
            if rules.get('case') == 'lowercase':
                formatted = formatted.lower()
            
            if rules.get('spaces') == 'replace_with_dash':
                formatted = formatted.replace(' ', '-')
            elif rules.get('spaces') == 'replace_with_underscore':
                formatted = formatted.replace(' ', '_')
            
            # Remover acentos si es necesario
            if rules.get('accents') == 'remove':
                import unicodedata
                formatted = unicodedata.normalize('NFD', formatted)
                formatted = ''.join(c for c in formatted if unicodedata.category(c) != 'Mn')
            
            # Remover caracteres especiales
            if rules.get('special_chars') == 'remove':
                import re
                formatted = re.sub(r'[^a-zA-Z0-9\-_]', '', formatted)
            
            return formatted
            
        except Exception as e:
            logger.error(f"❌ Error formateando ubicación: {e}")
            return location.lower().replace(' ', '-')
    
    def _get_fallback_patterns(self) -> Dict[str, Any]:
        """
        🔄 PATRONES DE FALLBACK
        
        Returns:
            Patrones básicos si no se puede cargar el JSON
        """
        
        return {
            "global_services": {
                "eventbrite": {
                    "pattern": "{country}--{city}--events",
                    "base_url": "https://www.eventbrite.com/d/",
                    "domains": {"default": "com"}
                },
                "meetup": {
                    "pattern": "find/?location={city}&source=EVENTS",
                    "base_url": "https://www.meetup.com/",
                    "domains": {"default": "com"}
                }
            },
            "regional_services": {},
            "formatting_rules": {
                "city": {"case": "lowercase", "spaces": "replace_with_dash"},
                "country": {"case": "lowercase", "spaces": "replace_with_dash"}
            }
        }
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """
        📊 ESTADÍSTICAS DEL FACTORY
        
        Returns:
            Estadísticas del factory
        """
        
        global_count = len(self.patterns.get('global_services', {}))
        regional_count = sum(
            len(services) for services in self.patterns.get('regional_services', {}).values()
        )
        
        return {
            "global_services": global_count,
            "regional_services": regional_count,
            "total_services": global_count + regional_count,
            "supported_countries": list(self.patterns.get('regional_services', {}).keys()),
            "patterns_version": self.patterns.get('version', 'unknown')
        }

# Instancia singleton global
smart_factory = SmartUrlFactory()