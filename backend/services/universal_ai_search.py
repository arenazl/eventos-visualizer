"""
Universal AI Search Service - Multilenguaje y Multicultural
Combina Intent Recognition + Smart Search + Gemini Brain
Detecta idioma, nacionalidad y adapta recomendaciones para turistas vs locales
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai
import os
import logging
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Configurar Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class UserType(Enum):
    LOCAL = "local"
    TOURIST = "tourist"
    EXPAT = "expat"
    BUSINESS = "business"

class Language(Enum):
    SPANISH = "es"
    ENGLISH = "en"
    PORTUGUESE = "pt"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"

@dataclass
class UserContext:
    """Contexto completo del usuario"""
    language: Language
    user_type: UserType
    nationality: Optional[str] = None
    current_location: Optional[str] = None
    preferences: Dict = None
    budget_level: Optional[str] = None  # low, medium, high, luxury
    group_type: Optional[str] = None  # solo, couple, family, friends, business
    
class UniversalAISearchService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash') if GEMINI_API_KEY else None
        
        # Mapeo de ciudades expandido (de intent_recognition.py)
        self.location_mappings = {
            # Argentina
            'buenos aires': {'city': 'Buenos Aires', 'country': 'Argentina'},
            'mendoza': {'city': 'Mendoza', 'country': 'Argentina'},
            'córdoba': {'city': 'Córdoba', 'country': 'Argentina'},
            'cordoba': {'city': 'Córdoba', 'country': 'Argentina'},
            'rosario': {'city': 'Rosario', 'country': 'Argentina'},
            'bariloche': {'city': 'Bariloche', 'country': 'Argentina'},
            'palermo': {'neighborhood': 'Palermo', 'city': 'Buenos Aires'},
            'recoleta': {'neighborhood': 'Recoleta', 'city': 'Buenos Aires'},
            'san telmo': {'neighborhood': 'San Telmo', 'city': 'Buenos Aires'},
            
            # México
            'ciudad de méxico': {'city': 'Ciudad de México', 'country': 'México'},
            'mexico city': {'city': 'Ciudad de México', 'country': 'México'},
            'cdmx': {'city': 'Ciudad de México', 'country': 'México'},
            'guadalajara': {'city': 'Guadalajara', 'country': 'México'},
            'cancún': {'city': 'Cancún', 'country': 'México'},
            'cancun': {'city': 'Cancún', 'country': 'México'},
            
            # Brasil
            'são paulo': {'city': 'São Paulo', 'country': 'Brasil'},
            'sao paulo': {'city': 'São Paulo', 'country': 'Brasil'},
            'rio de janeiro': {'city': 'Rio de Janeiro', 'country': 'Brasil'},
            'rio': {'city': 'Rio de Janeiro', 'country': 'Brasil'},
            
            # Chile
            'santiago': {'city': 'Santiago', 'country': 'Chile'},
            'valparaíso': {'city': 'Valparaíso', 'country': 'Chile'},
            'valparaiso': {'city': 'Valparaíso', 'country': 'Chile'},
        }
        
        # Frases clave para detectar turistas
        self.tourist_keywords = {
            'es': ['primera vez', 'visito', 'turista', 'viajo', 'vacaciones', 'conocer', 'típico'],
            'en': ['first time', 'visiting', 'tourist', 'travel', 'vacation', 'typical', 'must see'],
            'pt': ['primeira vez', 'visitando', 'turista', 'viagem', 'férias', 'típico'],
            'fr': ['première fois', 'visite', 'touriste', 'voyage', 'vacances', 'typique'],
            'de': ['erste mal', 'besuche', 'tourist', 'reise', 'urlaub', 'typisch'],
        }
        
        # Categorías en múltiples idiomas
        self.category_translations = {
            'music': {
                'es': ['música', 'concierto', 'recital', 'show', 'banda'],
                'en': ['music', 'concert', 'gig', 'show', 'band'],
                'pt': ['música', 'concerto', 'show', 'banda'],
                'fr': ['musique', 'concert', 'spectacle'],
                'de': ['musik', 'konzert', 'show'],
            },
            'food': {
                'es': ['restaurante', 'comida', 'cena', 'almuerzo', 'bar', 'café'],
                'en': ['restaurant', 'food', 'dinner', 'lunch', 'bar', 'cafe'],
                'pt': ['restaurante', 'comida', 'jantar', 'almoço', 'bar', 'café'],
                'fr': ['restaurant', 'nourriture', 'dîner', 'déjeuner', 'bar', 'café'],
                'de': ['restaurant', 'essen', 'abendessen', 'mittagessen', 'bar', 'café'],
            },
            'culture': {
                'es': ['museo', 'arte', 'cultura', 'teatro', 'exposición'],
                'en': ['museum', 'art', 'culture', 'theater', 'exhibition'],
                'pt': ['museu', 'arte', 'cultura', 'teatro', 'exposição'],
                'fr': ['musée', 'art', 'culture', 'théâtre', 'exposition'],
                'de': ['museum', 'kunst', 'kultur', 'theater', 'ausstellung'],
            },
            'sports': {
                'es': ['deporte', 'fútbol', 'partido', 'estadio'],
                'en': ['sports', 'football', 'soccer', 'match', 'stadium'],
                'pt': ['esporte', 'futebol', 'jogo', 'estádio'],
                'fr': ['sport', 'football', 'match', 'stade'],
                'de': ['sport', 'fußball', 'spiel', 'stadion'],
            },
            'nightlife': {
                'es': ['fiesta', 'boliche', 'club', 'noche', 'bailar'],
                'en': ['party', 'club', 'night', 'dance', 'nightlife'],
                'pt': ['festa', 'balada', 'clube', 'noite', 'dançar'],
                'fr': ['fête', 'club', 'nuit', 'danser'],
                'de': ['party', 'club', 'nacht', 'tanzen'],
            }
        }
    
    def detect_language(self, text: str) -> Language:
        """Detecta el idioma del texto"""
        try:
            lang_code = detect(text)
            lang_map = {
                'es': Language.SPANISH,
                'en': Language.ENGLISH,
                'pt': Language.PORTUGUESE,
                'fr': Language.FRENCH,
                'de': Language.GERMAN,
                'it': Language.ITALIAN,
                'zh': Language.CHINESE,
                'ja': Language.JAPANESE,
                'ko': Language.KOREAN,
            }
            return lang_map.get(lang_code, Language.SPANISH)
        except LangDetectException:
            return Language.SPANISH  # Default
    
    def detect_user_type(self, query: str, language: Language) -> UserType:
        """Detecta si es turista o local basándose en el query"""
        query_lower = query.lower()
        
        # Buscar keywords de turista
        tourist_words = self.tourist_keywords.get(language.value, [])
        for word in tourist_words:
            if word in query_lower:
                return UserType.TOURIST
        
        # Si menciona trabajo o negocios
        business_words = {
            'es': ['trabajo', 'negocio', 'reunión', 'conferencia'],
            'en': ['work', 'business', 'meeting', 'conference'],
        }
        
        for word in business_words.get(language.value, []):
            if word in query_lower:
                return UserType.BUSINESS
        
        # Default: local
        return UserType.LOCAL
    
    def extract_location(self, query: str) -> Optional[Dict]:
        """Extrae la ubicación del query"""
        query_lower = query.lower()
        
        for location, data in self.location_mappings.items():
            if location in query_lower:
                return data
        
        return None
    
    def extract_category(self, query: str, language: Language) -> Optional[str]:
        """Extrae la categoría basándose en el idioma"""
        query_lower = query.lower()
        
        for category, translations in self.category_translations.items():
            keywords = translations.get(language.value, [])
            for keyword in keywords:
                if keyword in query_lower:
                    return category
        
        return None
    
    async def process_universal_query(self, query: str, user_location: Optional[Dict] = None) -> Dict:
        """
        Procesa cualquier query en cualquier idioma
        Adapta las recomendaciones según si es turista o local
        """
        
        # 1. Detectar idioma
        language = self.detect_language(query)
        
        # 2. Detectar tipo de usuario
        user_type = self.detect_user_type(query, language)
        
        # 3. Extraer ubicación
        location = self.extract_location(query) or user_location
        
        # 4. Extraer categoría
        category = self.extract_category(query, language)
        
        # 5. Crear contexto
        user_context = UserContext(
            language=language,
            user_type=user_type,
            current_location=location,
            preferences={'category': category} if category else {}
        )
        
        # 6. Generar respuesta con Gemini adaptada al contexto
        if self.model:
            response = await self.generate_ai_response(query, user_context)
        else:
            response = self.generate_fallback_response(query, user_context)
        
        return {
            "query": query,
            "detected_language": language.value,
            "user_type": user_type.value,
            "location": location,
            "category": category,
            "response": response,
            "context": {
                "is_tourist": user_type == UserType.TOURIST,
                "language_name": self.get_language_name(language),
                "recommendations_style": "tourist_friendly" if user_type == UserType.TOURIST else "local_insider"
            }
        }
    
    async def generate_ai_response(self, query: str, context: UserContext) -> Dict:
        """Genera respuesta con Gemini adaptada al contexto del usuario"""
        
        # Prompt adaptado según tipo de usuario e idioma
        system_prompt = self.build_culturally_aware_prompt(query, context)
        
        try:
            response = await self.model.generate_content_async(system_prompt)
            
            # Parsear respuesta JSON de Gemini
            response_text = response.text
            # Limpiar markdown si existe
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            
            return json.loads(response_text)
            
        except Exception as e:
            logger.error(f"Error with Gemini: {e}")
            return self.generate_fallback_response(query, context)
    
    def build_culturally_aware_prompt(self, query: str, context: UserContext) -> str:
        """Construye un prompt culturalmente consciente"""
        
        location_str = ""
        if context.current_location:
            location_str = f"en {context.current_location.get('city', 'Buenos Aires')}, {context.current_location.get('country', 'Argentina')}"
        
        # Adaptar el prompt según el tipo de usuario
        if context.user_type == UserType.TOURIST:
            user_profile = f"""
            El usuario es un TURISTA que habla {self.get_language_name(context.language)}.
            Query: "{query}"
            
            IMPORTANTE para turistas:
            - Recomendar lugares ICÓNICOS y TÍPICOS de {location_str}
            - Incluir los "must-see" y experiencias auténticas
            - Dar contexto cultural sobre cada recomendación
            - Incluir tips de seguridad y transporte
            - Mencionar si aceptan tarjetas o necesitan efectivo
            - Horarios típicos del país (ej: en Argentina se cena tarde)
            - Nivel de español/idioma local necesario
            """
        else:
            user_profile = f"""
            El usuario es LOCAL de {location_str} que habla {self.get_language_name(context.language)}.
            Query: "{query}"
            
            IMPORTANTE para locales:
            - Recomendar lugares que frecuentan los locales (no tourist traps)
            - Incluir opciones nuevas o trending
            - Mencionar promociones o días especiales
            - Dar alternativas menos conocidas pero buenas
            - Usar jerga local si corresponde
            """
        
        return f"""
        {user_profile}
        
        Responde en {self.get_language_name(context.language)} con este formato JSON:
        {{
            "message": "Respuesta personalizada y amigable",
            "recommendations": [
                {{
                    "name": "Nombre del lugar/evento",
                    "why_perfect": "Por qué es perfecto para este usuario",
                    "cultural_note": "Nota cultural relevante",
                    "practical_info": "Info práctica (horarios, precios, tips)",
                    "local_secret": "Secreto local o tip insider",
                    "tourist_friendly_score": 0-10 (solo para turistas),
                    "authenticity_score": 0-10
                }}
            ],
            "general_tips": ["Tips generales para la experiencia"],
            "follow_up_suggestions": ["Otras cosas que podría interesarle"]
        }}
        
        Responde SOLO en JSON válido, sin markdown.
        """
    
    def generate_fallback_response(self, query: str, context: UserContext) -> Dict:
        """Respuesta fallback sin IA"""
        
        tourist_recommendations = {
            "en": {
                "message": "Here are some must-see places for tourists!",
                "recommendations": [
                    {
                        "name": "Teatro Colón",
                        "why_perfect": "World-renowned opera house, architectural gem",
                        "cultural_note": "One of the best acoustic venues globally",
                        "practical_info": "Tours available in English daily at 11am"
                    }
                ]
            },
            "es": {
                "message": "¡Aquí están los lugares imperdibles para turistas!",
                "recommendations": [
                    {
                        "name": "Teatro Colón",
                        "why_perfect": "Casa de ópera mundialmente famosa",
                        "cultural_note": "Una de las mejores acústicas del mundo",
                        "practical_info": "Tours en varios idiomas todos los días"
                    }
                ]
            }
        }
        
        local_recommendations = {
            "es": {
                "message": "Te tiro unos lugares que están buenos ahora",
                "recommendations": [
                    {
                        "name": "Mercado de San Telmo (pero el domingo temprano)",
                        "why_perfect": "Antes de que se llene de turistas",
                        "cultural_note": "Los anticuarios de verdad están en las calles laterales",
                        "practical_info": "Andá tipo 10am, después es un caos"
                    }
                ]
            }
        }
        
        if context.user_type == UserType.TOURIST:
            return tourist_recommendations.get(context.language.value, tourist_recommendations["en"])
        else:
            return local_recommendations.get(context.language.value, local_recommendations["es"])
    
    def get_language_name(self, language: Language) -> str:
        """Obtiene el nombre del idioma"""
        names = {
            Language.SPANISH: "español",
            Language.ENGLISH: "English",
            Language.PORTUGUESE: "português",
            Language.FRENCH: "français",
            Language.GERMAN: "Deutsch",
            Language.ITALIAN: "italiano",
            Language.CHINESE: "中文",
            Language.JAPANESE: "日本語",
            Language.KOREAN: "한국어"
        }
        return names.get(language, "español")