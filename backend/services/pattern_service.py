"""
🎯 PATTERN SERVICE - Aplicación de patrones de empresas sin AI
Usa patrones predefinidos con información de IntentRecognitionService
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from urllib.parse import quote
import pycountry

logger = logging.getLogger(__name__)

class PatternService:
    """
    🎯 SERVICIO DE PATRONES DE EMPRESAS
    
    Aplica patrones predefinidos usando localidad, provincia, país
    de IntentRecognitionService SIN llamar AI adicionales
    """
    
    def __init__(self):
        """Inicializa el servicio y carga patrones"""
        self.patterns = {}
        self._load_patterns()
        logger.info("🎯 Pattern Service initialized")
    
    def _load_patterns(self):
        """📂 Carga patrones desde JSON de scrapers"""
        try:
            patterns_file = Path(__file__).parent.parent / "data" / "scraper_url_formats.json"
            
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = data.get('formats', {})
                    logger.info(f"📂 Loaded {len(self.patterns)} scraper URL formats")
            else:
                logger.warning("⚠️ Scraper URL formats file not found")
                self.patterns = {}
                
        except Exception as e:
            logger.error(f"❌ Error loading scraper patterns: {e}")
            self.patterns = {}
    
    def generate_url(
        self, 
        platform: str, 
        localidad: str, 
        provincia: str = "", 
        pais: str = ""
    ) -> Optional[str]:
        """
        🔗 GENERA URL USANDO PATRÓN PREDEFINIDO
        
        Args:
            platform: Nombre de la plataforma (eventbrite, meetup, etc)
            localidad: Ciudad detectada por IntentRecognitionService
            provincia: Provincia/estado detectada 
            pais: País detectado
            
        Returns:
            URL generada o None si no hay patrón
        """
        
        try:
            pattern_config = self.patterns.get(platform.lower())
            
            if not pattern_config or not pattern_config.get('enabled', True):
                logger.info(f"⚠️ No pattern available for {platform}")
                return None
            
            pattern = pattern_config.get('pattern', '')
            if not pattern:
                return None
            
            # Normalizar valores
            city_normalized = localidad.lower().replace(' ', '-') if localidad else ''
            country_normalized = pais if pais else ''
            
            # Aplicar patrón específico por plataforma
            if platform.lower() == 'eventbrite':
                return self._apply_eventbrite_pattern(
                    pattern, pattern_config, city_normalized, country_normalized
                )
            elif platform.lower() == 'meetup':
                return self._apply_meetup_pattern(
                    pattern, pattern_config, localidad, country_normalized
                )
            else:
                # Patrón genérico
                url = pattern.replace('{city}', city_normalized)
                url = url.replace('{country}', country_normalized.lower())
                return url
                
        except Exception as e:
            logger.error(f"❌ Error generating URL for {platform}: {e}")
            return None
    
    def _apply_eventbrite_pattern(
        self, 
        pattern: str, 
        config: Dict[str, Any], 
        city: str, 
        country: str
    ) -> str:
        """🎫 Aplica patrón específico de Eventbrite"""
        
        # Obtener dominio por país
        domain = config.get('domains', {}).get(country, config.get('domains', {}).get('default', 'com'))
        
        # Obtener mapeo de país para URL
        country_mapped = config.get('country_mapping', {}).get(country, country.lower())
        
        # Aplicar patrón
        url = pattern.replace('{domain}', domain)
        url = url.replace('{country}', country_mapped)
        url = url.replace('{city}', city)
        
        logger.info(f"🎫 Eventbrite URL generated: {url}")
        return url
    
    def _apply_meetup_pattern(
        self, 
        pattern: str, 
        config: Dict[str, Any], 
        city: str, 
        country: str
    ) -> str:
        """🤝 Aplica patrón específico de Meetup con pycountry ISO codes"""
        
        # Obtener código ISO del país usando pycountry
        country_code = self._get_country_code_iso(country)
        if not country_code:
            country_code = config.get('default_country', 'us')
        
        # Aplicar patrón - URL encoding para caracteres especiales
        city_encoded = quote(city, safe='')  # URL encode completo
        url = pattern.replace('{country_code}', country_code.lower())
        url = url.replace('{city}', city_encoded)
        
        logger.info(f"🤝 Meetup URL generated: {url}")
        return url
    
    def _get_country_code_iso(self, country_name: str) -> Optional[str]:
        """🌍 Obtiene código ISO de país usando pycountry"""
        if not country_name:
            return None
        
        # Diccionario de traducciones español -> inglés
        spanish_to_english = {
            'españa': 'spain',
            'estados unidos': 'united states', 
            'méxico': 'mexico',
            'brasil': 'brazil',
            'francia': 'france',
            'alemania': 'germany',
            'italia': 'italy',
            'reino unido': 'united kingdom',
            'canadá': 'canada',
            'argentina': 'argentina'
        }
        
        # Normalizar el nombre (minúsculas)
        normalized = country_name.lower().strip()
        
        # Buscar primero en el diccionario español
        english_name = spanish_to_english.get(normalized, normalized)
            
        try:
            # Intentar búsqueda fuzzy para nombres en diferentes idiomas
            countries = pycountry.countries.search_fuzzy(english_name)
            if countries:
                return countries[0].alpha_2.lower()
        except LookupError:
            # Si falla fuzzy search, intentar búsqueda exacta
            try:
                country = pycountry.countries.get(name=english_name)
                if country:
                    return country.alpha_2.lower()
            except (KeyError, AttributeError):
                pass
        
        # Fallback: usar "us" por defecto
        logger.warning(f"⚠️ No se encontró código ISO para país: {country_name}, usando 'us' por defecto")
        return "us"
    
    def get_available_platforms(self) -> list:
        """📋 Obtiene lista de plataformas con patrones habilitados"""
        return [
            platform for platform, config in self.patterns.items() 
            if config.get('enabled', False)
        ]
    
    def get_pattern_info(self, platform: str) -> Dict[str, Any]:
        """ℹ️ Obtiene información del patrón de una plataforma"""
        return self.patterns.get(platform.lower(), {})

# Instancia singleton
pattern_service = PatternService()