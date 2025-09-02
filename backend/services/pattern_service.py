"""
🎯 PATTERN SERVICE - Aplicación de patrones de empresas sin AI
Usa patrones predefinidos con información de IntentRecognitionService
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

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
        """📂 Carga patrones desde JSON"""
        try:
            patterns_file = Path(__file__).parent.parent / "data" / "company_patterns.json"
            
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = data.get('patterns', {})
                    logger.info(f"📂 Loaded {len(self.patterns)} company patterns")
            else:
                logger.warning("⚠️ Company patterns file not found")
                self.patterns = {}
                
        except Exception as e:
            logger.error(f"❌ Error loading patterns: {e}")
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
        """🤝 Aplica patrón específico de Meetup"""
        
        # Obtener locale por país
        locale = config.get('locales', {}).get(country, config.get('locales', {}).get('default', 'en-US'))
        
        # Obtener código de país
        country_code = config.get('country_codes', {}).get(country, config.get('country_codes', {}).get('default', 'us'))
        
        # Aplicar patrón
        url = pattern.replace('{locale}', locale)
        url = url.replace('{country_code}', country_code)
        url = url.replace('{city}', city.replace(' ', ''))
        
        logger.info(f"🤝 Meetup URL generated: {url}")
        return url
    
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