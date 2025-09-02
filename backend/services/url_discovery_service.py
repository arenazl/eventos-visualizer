"""
🔗 URL DISCOVERY SERVICE - Servicio de Descubrimiento de URLs
Servicio que genera URLs inteligentes para scrapers usando IA con caché persistente
"""

import logging
import json
import os
from typing import Optional, Protocol, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class UrlDiscoveryRequest:
    """📝 Request para descubrimiento de URL"""
    platform: str
    location: str
    category: Optional[str] = None
    detected_country: Optional[str] = None  # País detectado por intent recognition

class IUrlDiscoveryService(Protocol):
    """🔌 Interfaz para servicio de descubrimiento de URLs"""
    
    async def discover_url(self, request: UrlDiscoveryRequest) -> Optional[str]:
        """Descubre URL para una plataforma y ubicación"""
        pass

class UrlDiscoveryService:
    """
    🔗 SERVICIO DE DESCUBRIMIENTO DE URLs CON CACHÉ PERSISTENTE
    
    FUNCIONALIDADES:
    - Cache JSON persistente (elimina 6s de overhead por cada llamada)
    - Genera URLs inteligentes usando IA SOLO UNA VEZ
    - Adapta URLs por plataforma y ubicación
    - Actualización mensual automática de patrones
    - Estadísticas de cache hits/misses
    """
    
    def __init__(self, ai_service):
        """
        Constructor con dependency injection
        
        Args:
            ai_service: Servicio de IA inyectado
        """
        self.ai_service = ai_service
        self.cache_file = "/mnt/c/Code/eventos-visualizer/backend/data/url_patterns_cache.json"
        self._cache = self._load_cache()
        logger.info("🔗 URL Discovery Service initialized with persistent cache")
        logger.info(f"📋 Cache cargado: {self._cache['metadata']['total_patterns']} patrones, {self._cache['metadata']['cache_hits']} hits")
    
    def _load_cache(self) -> Dict[str, Any]:
        """🗃️ Carga el caché desde JSON"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("⚠️ Cache file not found, creating empty cache")
                return self._create_empty_cache()
        except Exception as e:
            logger.error(f"❌ Error loading cache: {e}")
            return self._create_empty_cache()
    
    def _create_empty_cache(self) -> Dict[str, Any]:
        """📝 Crea un caché vacío"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "patterns": {},
            "metadata": {
                "total_patterns": 0,
                "cache_hits": 0,
                "ai_calls_saved": 0,
                "next_update": datetime.now().replace(month=datetime.now().month + 1).strftime("%Y-%m-%d")
            }
        }
    
    def _save_cache(self):
        """💾 Guarda el caché en JSON"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving cache: {e}")
    
    def _get_from_cache(self, platform: str, location: str, detected_country: Optional[str] = None) -> Optional[str]:
        """🔍 Busca patrón en caché SOLO para Argentina"""
        
        # 🌍 Si el intent detectó un país diferente a Argentina, NO usar caché
        if detected_country and detected_country.lower() not in ['argentina', 'arg']:
            logger.info(f"🌍 CACHE SKIP: Intent detectó {detected_country}, usando IA directamente")
            return None
            
        # 🇦🇷 Solo usar caché para Argentina
        pattern_data = self._cache['patterns'].get(platform)
        if not pattern_data:
            return None
        
        try:
            # Detectar si es Argentina por nombre de ciudad (fallback)
            location_lower = location.lower()
            argentine_cities = [
                'buenos aires', 'córdoba', 'cordoba', 'mendoza', 'rosario', 
                'la plata', 'mar del plata', 'salta', 'tucumán', 'tucuman',
                'bariloche', 'neuquén', 'neuquen'
            ]
            
            is_argentina = any(city in location_lower for city in argentine_cities)
            
            if not is_argentina:
                logger.info(f"🌍 CACHE SKIP: {location} no parece Argentina, usando IA")
                return None
            
            # Aplicar patrón argentino
            city = location.split(',')[0].strip().lower().replace(' ', '-')
            pattern = pattern_data['pattern']
            url = pattern.replace('{city}', city).replace('{location}', city)
            
            # Estadísticas
            self._cache['metadata']['cache_hits'] += 1
            self._cache['metadata']['ai_calls_saved'] += 1
            self._save_cache()
            
            logger.info(f"✅ CACHE HIT (Argentina): {platform} → {url}")
            return url
            
        except Exception as e:
            logger.warning(f"⚠️ Error applying pattern: {e}")
            return None
    
    def _save_to_cache(self, platform: str, pattern: str, url: str):
        """💾 Guarda nuevo patrón en caché"""
        try:
            self._cache['patterns'][platform] = {
                "pattern": pattern,
                "example": url,
                "confidence": 0.8,
                "last_tested": datetime.now().strftime("%Y-%m-%d"),
                "status": "working"
            }
            
            self._cache['metadata']['total_patterns'] = len(self._cache['patterns'])
            self._cache['last_updated'] = datetime.now().strftime("%Y-%m-%d")
            self._save_cache()
            
            logger.info(f"💾 PATTERN SAVED: {platform} → {pattern}")
            
        except Exception as e:
            logger.error(f"❌ Error saving pattern for {platform}: {e}")

    async def discover_url(self, request: UrlDiscoveryRequest) -> Optional[str]:
        """
        🎯 DESCUBRIMIENTO INTELIGENTE DE URL CON CACHÉ
        
        PROCESO:
        1. 🔍 Buscar primero en caché JSON (0.001s)
        2. 🤖 Solo si no existe, llamar a IA (6s+)
        3. 💾 Guardar patrón para próximas veces
        
        Args:
            request: Información de la plataforma y ubicación
            
        Returns:
            URL generada inteligentemente o None si falla
        """
        
        try:
            # 1. 🔍 BUSCAR PRIMERO EN CACHÉ (súper rápido)
            cached_url = self._get_from_cache(request.platform, request.location, request.detected_country)
            if cached_url:
                logger.info(f"🚀 CACHE HIT - NO AI CALL: {request.platform}")
                return cached_url
            
            # 2. 🤖 NO EXISTE EN CACHÉ - LLAMAR IA (lento, solo una vez)
            logger.info(f"🤖 CACHE MISS - Calling AI for: {request.platform}")
            
            url = await self.ai_service.generate_search_url(
                platform=request.platform,
                location=request.location,
                category=request.category
            )
            
            if url:
                # 3. 💾 GUARDAR PATRÓN PARA PRÓXIMAS VECES
                self._extract_and_save_pattern(request.platform, url, request.location)
                logger.info(f"🌐 URL discovered and cached: {url}")
                return url
            else:
                logger.warning(f"⚠️ No se pudo generar URL para {request.platform}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en descubrimiento de URL: {e}")
            return None
    
    def _extract_and_save_pattern(self, platform: str, url: str, location: str):
        """🔧 Extrae patrón de URL y lo guarda en caché"""
        try:
            # Extraer ciudad de ubicación
            city = location.split(',')[0].strip()
            city_normalized = city.lower().replace(' ', '-')
            
            # Generar patrón reemplazando la ciudad específica con placeholder
            pattern = url
            
            # Reemplazar variaciones de la ciudad
            for city_variant in [city_normalized, city.lower(), city]:
                if city_variant in pattern:
                    pattern = pattern.replace(city_variant, '{city}')
                    break
            
            # NUEVO: También reemplazar países conocidos con {country}
            country_mappings = {
                'france': '{country}',
                'brazil': '{country}',
                'brasil': '{country}',
                'spain': '{country}',
                'españa': '{country}',
                'argentina': '{country}',
                'colombia': '{country}',
                'mexico': '{country}',
                'méxico': '{country}'
            }
            
            for country_name, placeholder in country_mappings.items():
                if country_name in pattern:
                    pattern = pattern.replace(country_name, placeholder)
                    logger.info(f"🏳️ Replaced country '{country_name}' with '{placeholder}' in pattern")
                    break
                    
            logger.info(f"🔧 Pattern extraction: '{url}' → '{pattern}'")
            
            # Guardar patrón
            self._save_to_cache(platform, pattern, url)
            
        except Exception as e:
            logger.error(f"❌ Error extracting pattern: {e}")