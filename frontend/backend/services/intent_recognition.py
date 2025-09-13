"""
🧠 INTENT RECOGNITION SERVICE - Análisis de intenciones con Gemini
Servicio para analizar strings de búsqueda y extraer ubicación estructurada
"""

import logging
from typing import Dict, Any, Optional
from services.ai_service import GeminiAIService

logger = logging.getLogger(__name__)

class IntentRecognitionService:
    """
    🧠 SERVICIO DE RECONOCIMIENTO DE INTENCIONES (SINGLETON)
    
    FUNCIONALIDADES:
    - Analiza strings de búsqueda en lenguaje natural
    - Extrae información estructurada de ubicación
    - Detecta país, provincia/estado, ciudad
    - Retorna confianza del análisis
    - Una sola instancia para toda la aplicación
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IntentRecognitionService, cls).__new__(cls)
            logger.info("🧠 Singleton created: IntentRecognitionService")
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio con Gemini AI (solo una vez)"""
        if not self._initialized:
            self.ai_service = GeminiAIService()
            self.last_analysis = None  # Cache del último análisis
            IntentRecognitionService._initialized = True
            logger.info("🧠 Intent Recognition Service initialized as Singleton")
    
    async def get_all_api_parameters(self, query: str) -> Dict[str, Any]:
        """
        🎯 ANÁLISIS PRINCIPAL DE INTENCIONES
        
        Args:
            query: String de búsqueda del usuario
            
        Returns:
            Diccionario con información estructurada:
            {
                "success": bool,
                "intent": {
                    "location": str,
                    "city": str, 
                    "province": str,
                    "country": str,
                    "confidence": float,
                    "category": str,
                    "type": str
                },
                "apis": dict  # Para compatibilidad
            }
        """
        
        try:
            logger.info(f"🧠 Analizando intent: '{query}'")
            
            # Usar el servicio de IA existente para detectar ubicación
            import time
            start_time = time.time()
            location_info = await self._detect_location_async(query)
            ai_time = time.time() - start_time
            logger.info(f"⏱️ GEMINI TIMING: {ai_time:.3f}s para detectar ubicación de '{query}'")
            
            # Detectar categoría básica (por ahora simple)
            category = self._detect_category(query)
            
            # Construir respuesta estructurada con jerarquía geográfica para factory
            intent = {
                "location": location_info.get('city', query),
                "city": location_info.get('city', ''),
                "province": location_info.get('province', ''),  
                "country": location_info.get('country', ''),
                "confidence": location_info.get('confidence', 0.5),
                "category": category,
                "type": "location_search",
                "keywords": query.split(),
                # Jerarquía para factory pattern
                "geographic_hierarchy": {
                    "country": location_info.get('country', ''),
                    "country_code": self._get_country_code(location_info.get('country', '')),
                    "region": location_info.get('province', ''),
                    "city": location_info.get('city', ''),
                    "full_location": f"{location_info.get('city', '')}, {location_info.get('province', '')}, {location_info.get('country', '')}".strip(', ')
                },
                # Configuración para scrapers
                "scraper_config": {
                    "global_apis": ["eventbrite", "ticketmaster", "meetup", "bandsintown", "dice", "universe", "ticombo", "allevents", "stubhub", "ticketleap", "showpass"],
                    "regional_factory": f"{location_info.get('country', '').lower()}_factory" if location_info.get('country') else "default_factory",
                    "local_scrapers": self._get_local_scrapers(location_info.get('country', ''), location_info.get('province', ''))
                }
            }
            
            result = {
                "success": True,
                "intent": intent,
                "apis": {
                    "location": intent["location"],
                    "category": intent["category"]
                }
            }
            
            logger.info(f"✅ Intent analizado: {intent['location']} ({intent['country']}) - confianza: {intent['confidence']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de intent: {str(e)}")
            return {
                "success": False,
                "intent": {
                    "location": query,
                    "city": "",
                    "province": "",
                    "country": "",
                    "confidence": 0.1,
                    "category": "general",
                    "type": "location_search",
                    "keywords": query.split()
                },
                "apis": {
                    "location": query,
                    "category": "general"
                }
            }
    
    async def _detect_location_async(self, query: str) -> Dict[str, Any]:
        """
        🌍 DETECCIÓN DE UBICACIÓN CON GEMINI API
        
        Usa AI Service para detectar ubicación de forma inteligente
        """
        
        try:
            # Usar AI Service que ya tiene Gemini API implementada
            return await self.ai_service.detect_location_info(query)
        except Exception as e:
            logger.error(f"❌ Error en detección de ubicación async: {e}")
            # Fallback básico
            words = query.split()
            first_word = words[0] if words else query
            
            return {
                'city': first_word.title(),
                'province': '',
                'country': '',
                'confidence': 0.2
            }
    
    def _detect_category(self, query: str) -> str:
        """
        🎯 DETECCIÓN AVANZADA DE CATEGORÍA
        
        Detecta el tipo de evento basado en palabras clave expandidas
        """
        
        query_lower = query.lower()
        
        # Categorías expandidas por palabras clave
        categories = {
            'música': ['música', 'concierto', 'show', 'banda', 'cantante', 'dj', 'festival musical', 'rock', 'pop', 'jazz'],
            'deportes': ['deporte', 'fútbol', 'tenis', 'basket', 'partido', 'copa', 'torneo', 'maratón', 'gimnasio'],
            'cultural': ['teatro', 'cultural', 'arte', 'museo', 'exposición', 'galería', 'ópera', 'ballet', 'danza'],
            'tech': ['tech', 'tecnología', 'conferencia', 'workshop', 'programación', 'startup', 'hackathon', 'coding'],
            'fiestas': ['fiesta', 'party', 'celebración', 'festival', 'carnaval', 'año nuevo', 'halloween'],
            'negocios': ['networking', 'conferencia', 'empresa', 'business', 'emprendimiento', 'marketing'],
            'gastronomía': ['restaurante', 'comida', 'gastronómico', 'vino', 'chef', 'degustación'],
            'hobbies': ['taller', 'curso', 'clase', 'aprender', 'hobby', 'manualidades']
        }
        
        for category, keywords in categories.items():
            if any(word in query_lower for word in keywords):
                return category
                
        return 'general'
    
    def _get_country_code(self, country: str) -> str:
        """
        🌍 CONVERTIR PAÍS A CÓDIGO ISO
        
        Args:
            country: Nombre del país
            
        Returns:
            Código ISO del país
        """
        if not country:
            return "AR"  # Default para Argentina
            
        country_lower = country.lower()
        codes = {
            'argentina': 'AR',
            'españa': 'ES',
            'spain': 'ES',
            'france': 'FR',
            'francia': 'FR',
            'united states': 'US',
            'usa': 'US',
            'méxico': 'MX',
            'mexico': 'MX',
            'chile': 'CL',
            'colombia': 'CO',
            'perú': 'PE',
            'peru': 'PE',
            'brasil': 'BR',
            'brazil': 'BR',
            'uruguay': 'UY'
        }
        return codes.get(country_lower, 'AR')
    
    def _get_local_scrapers(self, country: str, province: str) -> list:
        """
        🏭 OBTENER SCRAPERS LOCALES BASADOS EN UBICACIÓN
        
        Args:
            country: País detectado
            province: Provincia/Estado detectado
            
        Returns:
            Lista de scrapers locales específicos
        """
        
        if not country:
            return []
            
        country_lower = country.lower()
        province_lower = province.lower() if province else ""
        
        # Scrapers específicos por país/región
        local_scrapers = {
            'argentina': {
                'general': ['alternativateatral', 'cartelera_buenos_aires', 'plateanet'],
                'buenos aires': ['agenda_cultural_ba', 'turismo_ba', 'vivamos_cultura'],
                'córdoba': ['cordoba_turismo', 'agenda_cordoba'],
                'rosario': ['rosario_turismo', 'agenda_rosario'],
                'mendoza': ['mendoza_turismo', 'agenda_mendoza']
            },
            'españa': {
                'general': ['atrapalo', 'entradas_com', 'ticketea'],
                'barcelona': ['barcelona_turisme', 'agenda_barcelona'],
                'madrid': ['madrid_es', 'agenda_madrid'],
                'valencia': ['valencia_turismo', 'agenda_valencia']
            },
            'méxico': {
                'general': ['ticketmaster_mx', 'boletia', 'superboletos'],
                'ciudad de méxico': ['cdmx_gob', 'agenda_cdmx'],
                'guadalajara': ['guadalajara_turismo']
            }
        }
        
        country_scrapers = local_scrapers.get(country_lower, {})
        if province_lower and province_lower in country_scrapers:
            return country_scrapers[province_lower] + country_scrapers.get('general', [])
        else:
            return country_scrapers.get('general', [])

# Instancia singleton global
intent_service = IntentRecognitionService()