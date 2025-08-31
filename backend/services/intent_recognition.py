"""
AI Intent Recognition Service - POWERED BY GEMINI 🧠
Interpreta el input del usuario usando IA y lo convierte en parámetros apropiados para cada API
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configurar Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class IntentType(Enum):
    LOCATION_SEARCH = "location"
    CATEGORY_SEARCH = "category"
    ARTIST_SEARCH = "artist"
    VENUE_SEARCH = "venue"
    DATE_SEARCH = "date"
    MIXED_SEARCH = "mixed"

@dataclass
class UserIntent:
    """Estructura de intención del usuario"""
    intent_type: IntentType
    location: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    artist: Optional[str] = None
    venue: Optional[str] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    keywords: List[str] = None
    radius_km: int = 50
    confidence: float = 0.0

class IntentRecognitionService:
    """
    🧠 Servicio de reconocimiento de intenciones POWERED BY GEMINI AI
    Traduce input natural del usuario a parámetros específicos de cada API
    """
    
    def __init__(self):
        # Verificar si Gemini ya está configurado (reutilizar instancia)
        self.api_key = GEMINI_API_KEY
        if self.api_key:
            # Solo configurar si no está ya configurado
            try:
                # Intentar usar modelo existente
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                # Si falla, configurar desde cero
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("🔥 GEMINI NO CONFIGURADO - Usando fallback")
        
        # Categorías EXACTAS que están en el frontend
        self.available_categories = [
            'Todos', 'Música', 'Deportes', 'Cultural', 'Tech', 'Fiestas'
        ]
        
        # MÉTODOS ORIGINALES - Mapeos de ubicaciones para Argentina y LATAM
        self.location_mappings = {
            # Argentina
            'argentina': {'country': 'Argentina', 'code': 'AR'},
            'arg': {'country': 'Argentina', 'code': 'AR'},
            'buenos aires': {'city': 'Buenos Aires', 'country': 'Argentina'},
            'bsas': {'city': 'Buenos Aires', 'country': 'Argentina'},
            'caba': {'city': 'Buenos Aires', 'country': 'Argentina'},
            'capital federal': {'city': 'Buenos Aires', 'country': 'Argentina'},
            'cordoba': {'city': 'Córdoba', 'country': 'Argentina'},
            'rosario': {'city': 'Rosario', 'country': 'Argentina'},
            'mendoza': {'city': 'Mendoza', 'country': 'Argentina'},
            'la plata': {'city': 'La Plata', 'country': 'Argentina'},
            'mar del plata': {'city': 'Mar del Plata', 'country': 'Argentina'},
            'mdq': {'city': 'Mar del Plata', 'country': 'Argentina'},
            'palermo': {'neighborhood': 'Palermo', 'city': 'Buenos Aires'},
            'recoleta': {'neighborhood': 'Recoleta', 'city': 'Buenos Aires'},
            'belgrano': {'neighborhood': 'Belgrano', 'city': 'Buenos Aires'},
            'san telmo': {'neighborhood': 'San Telmo', 'city': 'Buenos Aires'},
            
            # México
            'mexico': {'country': 'México', 'code': 'MX'},
            'méxico': {'country': 'México', 'code': 'MX'},
            'cdmx': {'city': 'Ciudad de México', 'country': 'México'},
            'ciudad de mexico': {'city': 'Ciudad de México', 'country': 'México'},
            'guadalajara': {'city': 'Guadalajara', 'country': 'México'},
            'monterrey': {'city': 'Monterrey', 'country': 'México'},
            'cancun': {'city': 'Cancún', 'country': 'México'},
            
            # Brasil
            'brasil': {'country': 'Brasil', 'code': 'BR'},
            'brazil': {'country': 'Brasil', 'code': 'BR'},
            'sao paulo': {'city': 'São Paulo', 'country': 'Brasil'},
            'rio': {'city': 'Rio de Janeiro', 'country': 'Brasil'},
            'rio de janeiro': {'city': 'Rio de Janeiro', 'country': 'Brasil'},
            
            # Chile
            'chile': {'country': 'Chile', 'code': 'CL'},
            'santiago': {'city': 'Santiago', 'country': 'Chile'},
            'valparaiso': {'city': 'Valparaíso', 'country': 'Chile'},
            
            # Colombia
            'colombia': {'country': 'Colombia', 'code': 'CO'},
            'bogota': {'city': 'Bogotá', 'country': 'Colombia'},
            'medellin': {'city': 'Medellín', 'country': 'Colombia'},
            'cartagena': {'city': 'Cartagena', 'country': 'Colombia'},
            
            # España
            'españa': {'country': 'España', 'code': 'ES'},
            'spain': {'country': 'España', 'code': 'ES'},
            'madrid': {'city': 'Madrid', 'country': 'España'},
            'barcelona': {'city': 'Barcelona', 'country': 'España'},
            'valencia': {'city': 'Valencia', 'country': 'España'},
            'sevilla': {'city': 'Sevilla', 'country': 'España'},
            'bilbao': {'city': 'Bilbao', 'country': 'España'},
            
            # Francia
            'francia': {'country': 'Francia', 'code': 'FR'},
            'france': {'country': 'Francia', 'code': 'FR'},
            'paris': {'city': 'París', 'country': 'Francia'},
            'lyon': {'city': 'Lyon', 'country': 'Francia'},
            'marsella': {'city': 'Marsella', 'country': 'Francia'},
            
            # Estados Unidos
            'usa': {'country': 'Estados Unidos', 'code': 'US'},
            'miami': {'city': 'Miami', 'country': 'Estados Unidos'},
            'new york': {'city': 'New York', 'country': 'Estados Unidos'},
            'los angeles': {'city': 'Los Angeles', 'country': 'Estados Unidos'},
            'chicago': {'city': 'Chicago', 'country': 'Estados Unidos'},
        }
        
        # Categorías y sus variaciones
        self.category_mappings = {
            'musica': ['música', 'music', 'concierto', 'conciertos', 'concert', 'show', 'recital', 'gig'],
            'electronica': ['electrónica', 'techno', 'house', 'edm', 'dance', 'rave', 'dj', 'electronic'],
            'rock': ['rock', 'metal', 'punk', 'indie', 'alternativo'],
            'pop': ['pop', 'mainstream'],
            'jazz': ['jazz', 'blues', 'soul'],
            'reggaeton': ['reggaeton', 'reggaetón', 'urbano', 'trap', 'latin'],
            'folclore': ['folklore', 'folclore', 'tango', 'peña', 'tradicional'],
            
            'deportes': ['deportes', 'sports', 'futbol', 'fútbol', 'football', 'soccer', 'basket', 'tennis', 'rugby'],
            'teatro': ['teatro', 'theater', 'theatre', 'obra', 'musical'],
            'arte': ['arte', 'art', 'exposicion', 'exposición', 'muestra', 'museo', 'galeria'],
            'cultura': ['cultura', 'cultural', 'literature', 'literatura', 'poesia', 'charla'],
            'gastronomia': ['gastronomia', 'gastronomía', 'food', 'comida', 'restaurant', 'cena', 'almuerzo'],
            'tecnologia': ['tecnologia', 'tecnología', 'tech', 'it', 'software', 'startup', 'hackathon'],
            'negocios': ['negocios', 'business', 'conferencia', 'conference', 'networking', 'emprendimiento'],
            'fiesta': ['fiesta', 'party', 'boliche', 'disco', 'club', 'nightlife', 'noche'],
            'familiar': ['familiar', 'family', 'niños', 'kids', 'infantil', 'children'],
            'educacion': ['educacion', 'educación', 'education', 'curso', 'taller', 'workshop', 'seminario'],
            'bienestar': ['bienestar', 'wellness', 'yoga', 'meditacion', 'fitness', 'salud', 'health']
        }
        
        # Venues conocidos
        self.known_venues = {
            # Buenos Aires
            'luna park': 'Luna Park',
            'movistar arena': 'Movistar Arena',
            'estadio unico': 'Estadio Único de La Plata',
            'la bombonera': 'Estadio Alberto J. Armando',
            'monumental': 'Estadio Monumental',
            'teatro colon': 'Teatro Colón',
            'teatro gran rex': 'Teatro Gran Rex',
            'usina del arte': 'Usina del Arte',
            'ccr': 'Centro Cultural Recoleta',
            'konex': 'Ciudad Cultural Konex',
            'niceto': 'Niceto Club',
            'obras': 'Estadio Obras',
            'tecnopolis': 'Tecnópolis',
            'la rural': 'La Rural',
            
            # México
            'foro sol': 'Foro Sol',
            'palacio de los deportes': 'Palacio de los Deportes',
            'auditorio nacional': 'Auditorio Nacional',
            'estadio azteca': 'Estadio Azteca',
        }
        
        # Palabras clave temporales
        self.temporal_keywords = {
            'hoy': 0,
            'mañana': 1,
            'tomorrow': 1,
            'pasado mañana': 2,
            'este fin de semana': 'weekend',
            'esta semana': 'week',
            'este mes': 'month',
            'proximo mes': 'next_month',
            'next month': 'next_month'
        }
        
        # Prompt optimizado para intent recognition
        self.intent_prompt = f"""
        Eres un experto en análisis de intenciones de búsqueda de eventos.
        
        CATEGORÍAS DISPONIBLES (debes elegir UNA de estas EXACTAMENTE):
        {self.available_categories}
        
        INSTRUCCIONES:
        1. Analiza el texto del usuario y detecta:
           - País (nombre completo, ej: "Argentina", "España", "México")
           - Ciudad (si se menciona)
           - Categoría (SOLO una de las disponibles)
           - Tipo de intención
           - Nivel de confianza
        
        2. REGLAS CRÍTICAS:
           - Si mencionan "restaurant", "discoteca", "bar" → categoría "Fiestas"
           - Si mencionan "concierto", "música", "show" → categoría "Música"
           - Si mencionan "fútbol", "deportes" → categoría "Deportes"
           - Si mencionan "teatro", "arte", "cultura" → categoría "Cultural"
           - Si mencionan "tecnología", "hackathon", "conferencia" → categoría "Tech"
           - Si es ambiguo → categoría "Todos"
        
        3. Para PAÍSES, detecta dinámicamente (no limitado):
           - "Buenos Aires" → país "Argentina"
           - "Palermo" → ciudad "Buenos Aires", país "Argentina"
           - "Madrid" → ciudad "Madrid", país "España"
           - "Italia" → país "Italia"
           - "París" → ciudad "París", país "Francia"
        
        RESPONDE SIEMPRE EN ESTE FORMATO JSON EXACTO:
        {{
            "country": "Nombre del país detectado o null",
            "city": "Nombre de la ciudad detectada o null", 
            "category": "Una de las categorías exactas disponibles o Todos",
            "intent_type": "location/category/mixed/venue/artist",
            "confidence": 0.95,
            "keywords": ["palabra1", "palabra2"],
            "reasoning": "Por qué elegiste esa categoría"
        }}
        """
    
    def parse_user_input(self, user_input: str) -> UserIntent:
        """
        Parsea el input del usuario y extrae la intención - CON GEMINI AI
        """
        user_input_clean = user_input.lower().strip()
        
        # 🧠 PRIMERA OPCIÓN: Usar Gemini AI si está disponible
        if self.model:
            try:
                full_prompt = f"{self.intent_prompt}\n\nTEXTO DEL USUARIO: '{user_input}'"
                response = self.model.generate_content(full_prompt)
                gemini_result = self._parse_gemini_response(response.text)
                
                # Crear UserIntent desde respuesta de Gemini
                intent_type_map = {
                    'location': IntentType.LOCATION_SEARCH,
                    'category': IntentType.CATEGORY_SEARCH,
                    'mixed': IntentType.MIXED_SEARCH,
                    'venue': IntentType.VENUE_SEARCH,
                    'artist': IntentType.ARTIST_SEARCH
                }
                
                intent_type = intent_type_map.get(gemini_result.get('intent_type', 'mixed').lower(), IntentType.MIXED_SEARCH)
                
                return UserIntent(
                    intent_type=intent_type,
                    country=gemini_result.get('country'),
                    city=gemini_result.get('city'),
                    location=gemini_result.get('city') or gemini_result.get('country'),
                    category=gemini_result.get('category', 'Todos'),
                    keywords=gemini_result.get('keywords', []),
                    confidence=float(gemini_result.get('confidence', 0.8))
                )
                
            except Exception as e:
                logger.warning(f"Gemini falló, usando método original: {e}")
        
        # 🔄 FALLBACK: Método original si Gemini no funciona
        intent = UserIntent(
            intent_type=IntentType.MIXED_SEARCH,
            keywords=[]
        )
        
        # 1. Detectar ubicación (método original)
        location_data = self._extract_location(user_input_clean)
        if location_data:
            intent.location = location_data.get('location')
            intent.country = location_data.get('country')
            intent.city = location_data.get('city')
            intent.neighborhood = location_data.get('neighborhood')
            if any([intent.city, intent.country]):
                intent.intent_type = IntentType.LOCATION_SEARCH
        
        # 2. Detectar categoría (método original)
        category_data = self._extract_category(user_input_clean)
        if category_data:
            intent.category = category_data['category']
            intent.subcategory = category_data.get('subcategory')
            if intent.intent_type == IntentType.LOCATION_SEARCH:
                intent.intent_type = IntentType.MIXED_SEARCH
            else:
                intent.intent_type = IntentType.CATEGORY_SEARCH
        
        # 3. Detectar venue (método original)
        venue = self._extract_venue(user_input_clean)
        if venue:
            intent.venue = venue
            intent.intent_type = IntentType.VENUE_SEARCH
        
        # 4. Detectar rango temporal (método original)
        date_range = self._extract_date_range(user_input_clean)
        if date_range:
            intent.date_range = date_range
        
        # 5. Extraer keywords (método original)
        intent.keywords = self._extract_keywords(user_input_clean)
        
        # 6. Calcular confianza (método original)
        intent.confidence = self._calculate_confidence(intent)
        
        logger.info(f"Intent parsed: {intent.intent_type.value} - Location: {intent.city or intent.country} - Category: {intent.category}")
        
        return intent
    
    def _extract_location(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extrae información de ubicación del texto (MÉTODO ORIGINAL)
        """
        for location, data in self.location_mappings.items():
            if location in text:
                result = data.copy()
                result['location'] = location
                return result
        return None
    
    def _extract_category(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extrae categoría del texto (MÉTODO ORIGINAL)
        """
        for category, variations in self.category_mappings.items():
            if category in text:
                return {'category': category}
            for variation in variations:
                if variation in text:
                    return {'category': category, 'subcategory': variation}
        return None
    
    def _extract_venue(self, text: str) -> Optional[str]:
        """
        Extrae venue del texto (MÉTODO ORIGINAL)
        """
        for venue_key, venue_name in self.known_venues.items():
            if venue_key in text:
                return venue_name
        return None
    
    def _extract_date_range(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Extrae rango de fechas del texto (MÉTODO ORIGINAL)
        """
        now = datetime.now()
        
        for keyword, value in self.temporal_keywords.items():
            if keyword in text:
                if isinstance(value, int):
                    # Días específicos
                    start = now + timedelta(days=value)
                    end = start + timedelta(days=1)
                    return (start, end)
                elif value == 'weekend':
                    # Próximo fin de semana
                    days_to_saturday = (5 - now.weekday()) % 7
                    if days_to_saturday == 0:
                        days_to_saturday = 7
                    start = now + timedelta(days=days_to_saturday)
                    end = start + timedelta(days=2)
                    return (start, end)
                elif value == 'week':
                    # Esta semana
                    return (now, now + timedelta(days=7))
                elif value == 'month':
                    # Este mes
                    return (now, now + timedelta(days=30))
                elif value == 'next_month':
                    # Próximo mes
                    return (now + timedelta(days=30), now + timedelta(days=60))
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrae palabras clave relevantes (MÉTODO ORIGINAL)
        """
        # Remover palabras comunes
        stopwords = ['el', 'la', 'de', 'en', 'y', 'a', 'para', 'por', 'con', 'un', 'una', 
                     'los', 'las', 'del', 'al', 'es', 'son', 'the', 'in', 'at', 'on', 'for']
        
        words = text.split()
        keywords = []
        
        for word in words:
            if len(word) > 2 and word not in stopwords:
                # No agregar si ya fue identificado como ubicación o categoría
                is_location = any(word in loc for loc in self.location_mappings.keys())
                is_category = any(word in cat for cats in self.category_mappings.values() for cat in cats)
                
                if not is_location and not is_category:
                    keywords.append(word)
        
        return keywords[:5]  # Límite de keywords
    
    def _calculate_confidence(self, intent: UserIntent) -> float:
        """
        Calcula la confianza de la intención detectada (MÉTODO ORIGINAL)
        """
        confidence = 0.0
        
        # Ubicación detectada
        if intent.city:
            confidence += 0.3
        elif intent.country:
            confidence += 0.2
        
        # Categoría detectada
        if intent.category:
            confidence += 0.3
        
        # Venue detectado
        if intent.venue:
            confidence += 0.2
        
        # Fechas detectadas
        if intent.date_range:
            confidence += 0.1
        
        # Keywords detectados
        if intent.keywords:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta JSON de Gemini
        """
        try:
            # Limpiar response si tiene markdown
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1]
            else:
                json_str = response_text
            
            return json.loads(json_str.strip())
        except Exception as e:
            logger.error(f"❌ Error parseando JSON de Gemini: {e}")
            # Fallback
            return {
                "country": None,
                "city": None,
                "category": "Todos",
                "intent_type": "mixed",
                "confidence": 0.3,
                "keywords": [],
                "reasoning": "Error al parsear respuesta"
            }
    
    def _convert_to_user_intent(self, gemini_result: Dict, original_input: str) -> UserIntent:
        """
        Convierte la respuesta de Gemini a UserIntent
        """
        # Determinar tipo de intención
        intent_type_map = {
            'location': IntentType.LOCATION_SEARCH,
            'category': IntentType.CATEGORY_SEARCH,
            'mixed': IntentType.MIXED_SEARCH,
            'venue': IntentType.VENUE_SEARCH,
            'artist': IntentType.ARTIST_SEARCH
        }
        
        intent_type = intent_type_map.get(
            gemini_result.get('intent_type', 'mixed').lower(),
            IntentType.MIXED_SEARCH
        )
        
        return UserIntent(
            intent_type=intent_type,
            country=gemini_result.get('country'),
            city=gemini_result.get('city'),
            location=gemini_result.get('city') or gemini_result.get('country'),
            category=gemini_result.get('category', 'Todos'),
            keywords=gemini_result.get('keywords', []),
            confidence=float(gemini_result.get('confidence', 0.8))
        )
    
    def _fallback_parse(self, user_input: str) -> UserIntent:
        """
        Sistema fallback cuando Gemini no está disponible
        """
        user_lower = user_input.lower()
        
        # Detectar categoría simple
        category = "Todos"
        if any(word in user_lower for word in ['música', 'concierto', 'show', 'cantar']):
            category = "Música"
        elif any(word in user_lower for word in ['deporte', 'fútbol', 'basket', 'tenis']):
            category = "Deportes"
        elif any(word in user_lower for word in ['restaurant', 'bar', 'discoteca', 'fiesta', 'party']):
            category = "Fiestas"
        elif any(word in user_lower for word in ['teatro', 'arte', 'cultura', 'museo']):
            category = "Cultural"
        elif any(word in user_lower for word in ['tech', 'tecnología', 'conferencia', 'startup']):
            category = "Tech"
        
        # Detectar ubicación simple
        country = None
        city = None
        if 'argentina' in user_lower or 'buenos aires' in user_lower:
            country = "Argentina"
            if 'buenos aires' in user_lower:
                city = "Buenos Aires"
        elif 'españa' in user_lower or 'madrid' in user_lower:
            country = "España"
            if 'madrid' in user_lower:
                city = "Madrid"
        elif 'méxico' in user_lower or 'mexico' in user_lower:
            country = "México"
        elif 'italia' in user_lower:
            country = "Italia"
        elif 'francia' in user_lower or 'parís' in user_lower:
            country = "Francia"
            if 'parís' in user_lower:
                city = "París"
        
        return UserIntent(
            intent_type=IntentType.MIXED_SEARCH,
            country=country,
            city=city,
            location=city or country,
            category=category,
            keywords=user_input.split()[:3],
            confidence=0.6
        )
    
    def format_for_eventbrite(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Formatea parámetros para Eventbrite API
        """
        params = {}
        
        # Eventbrite necesita una ubicación como string
        if intent.city:
            params['location'] = intent.city
            if intent.country:
                params['location'] += f", {intent.country}"
        elif intent.country:
            params['location'] = intent.country
        elif intent.neighborhood and intent.city:
            params['location'] = f"{intent.neighborhood}, Buenos Aires"
        else:
            params['location'] = "Buenos Aires"  # Default
        
        # Categoría
        if intent.category:
            params['categories'] = self._map_to_eventbrite_category(intent.category)
        
        # Fechas
        if intent.date_range:
            params['start_date.range_start'] = intent.date_range[0].isoformat()
            params['start_date.range_end'] = intent.date_range[1].isoformat()
        
        # Keywords
        if intent.keywords:
            params['q'] = ' '.join(intent.keywords)
        
        return params
    
    def format_for_ticketmaster(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Formatea parámetros para Ticketmaster API
        """
        params = {}
        
        # Ticketmaster necesita ciudad y código de país
        if intent.city:
            params['city'] = intent.city
        
        if intent.country:
            country_code = self._get_country_code(intent.country)
            if country_code:
                params['countryCode'] = country_code
        
        # Categoría (segment en Ticketmaster)
        if intent.category:
            params['segmentName'] = self._map_to_ticketmaster_segment(intent.category)
        
        # Venue
        if intent.venue:
            params['keyword'] = intent.venue
        elif intent.keywords:
            params['keyword'] = ' '.join(intent.keywords)
        
        # Fechas
        if intent.date_range:
            params['startDateTime'] = intent.date_range[0].strftime('%Y-%m-%dT%H:%M:%SZ')
            params['endDateTime'] = intent.date_range[1].strftime('%Y-%m-%dT%H:%M:%SZ')
        
        params['radius'] = str(intent.radius_km)
        params['unit'] = 'km'
        
        return params
    
    def format_for_facebook_scraper(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Formatea parámetros para Facebook Events scraper
        """
        params = {}
        
        # Facebook necesita una query de búsqueda
        search_terms = []
        
        if intent.city:
            search_terms.append(intent.city)
        elif intent.country:
            search_terms.append(intent.country)
        
        if intent.category:
            search_terms.append(intent.category)
        
        if intent.keywords:
            search_terms.extend(intent.keywords)
        
        params['search_query'] = ' '.join(search_terms) if search_terms else 'Buenos Aires'
        params['location'] = intent.city or intent.country or 'Buenos Aires'
        
        return params
    
    def format_for_instagram_scraper(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Formatea parámetros para Instagram scraper
        """
        params = {}
        
        # Instagram usa hashtags
        hashtags = []
        
        # Hashtag de ubicación
        if intent.city:
            city_tag = intent.city.replace(' ', '').replace('-', '')
            hashtags.append(city_tag.lower())
        
        # Hashtag de categoría
        if intent.category:
            if intent.category == 'electronica':
                hashtags.extend(['techno', 'house', 'rave'])
            elif intent.category == 'rock':
                hashtags.extend(['rock', 'indie', 'livemusic'])
            elif intent.category == 'fiesta':
                hashtags.extend(['party', 'nightlife', 'fiesta'])
            else:
                hashtags.append(intent.category)
        
        # Keywords como hashtags
        if intent.keywords:
            hashtags.extend([k.replace(' ', '') for k in intent.keywords])
        
        params['hashtags'] = hashtags[:5]  # Límite de hashtags
        
        if intent.venue:
            params['location_tag'] = intent.venue
        
        return params
    
    def format_for_ticketek(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Formatea parámetros para Ticketek scraper
        """
        params = {}
        
        # Ticketek usa categorías específicas
        category_map = {
            'musica': '/musica',
            'deportes': '/deportes',
            'teatro': '/teatro',
            'familiar': '/familiar',
            'especiales': '/especiales'
        }
        
        if intent.category and intent.category in category_map:
            params['category'] = category_map[intent.category]
        else:
            params['category'] = '/musica'  # Default
        
        # Ubicación para filtrado posterior
        params['location'] = intent.city or intent.country or 'Argentina'
        
        return params
    
    def get_all_api_parameters(self, user_input: str) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene parámetros formateados para todas las APIs disponibles - CON GEMINI AI
        """
        intent = self.parse_user_input(user_input)
        
        return {
            'intent': {
                'type': intent.intent_type.value,
                'confidence': intent.confidence,
                'location': intent.location,
                'country': intent.country,
                'city': intent.city,
                'category': intent.category,
                'keywords': intent.keywords
            },
            'apis': {
                'eventbrite': self.format_for_eventbrite(intent),
                'ticketmaster': self.format_for_ticketmaster(intent),
                'facebook': self.format_for_facebook_scraper(intent),
                'instagram': self.format_for_instagram_scraper(intent),
                'ticketek': self.format_for_ticketek(intent)
            }
        }
    
    def _get_country_code(self, country: str) -> Optional[str]:
        """
        Obtiene el código ISO del país dinámicamente
        """
        country_codes = {
            'Argentina': 'AR',
            'México': 'MX', 
            'Brasil': 'BR',
            'Chile': 'CL',
            'Colombia': 'CO',
            'España': 'ES',
            'Francia': 'FR',
            'Italia': 'IT',
            'Estados Unidos': 'US',
            'Reino Unido': 'GB',
            'Alemania': 'DE',
            'Perú': 'PE',
            'Uruguay': 'UY'
        }
        return country_codes.get(country, 'AR')  # Argentina por default
    
    def _map_to_eventbrite_category(self, category: str) -> str:
        """
        Mapea categoría frontend a formato Eventbrite
        """
        category_map = {
            'Música': '103',
            'Deportes': '108', 
            'Cultural': '105',
            'Tech': '102',
            'Fiestas': '103'  # Music para fiestas también
        }
        return category_map.get(category, '103')
    
    def _map_to_ticketmaster_segment(self, category: str) -> str:
        """
        Mapea categoría frontend a segmento Ticketmaster
        """
        segment_map = {
            'Música': 'Music',
            'Deportes': 'Sports',
            'Cultural': 'Arts & Theatre', 
            'Tech': 'Miscellaneous',
            'Fiestas': 'Music'
        }
        return segment_map.get(category, 'Music')


# Testing con Gemini AI
if __name__ == "__main__":
    import asyncio
    
    async def test_intent_service():
        service = IntentRecognitionService()
        
        # Casos de prueba para el nuevo sistema
        test_cases = [
            "restaurant en Italia",
            "discoteca en Ámsterdam", 
            "concierto de rock en Buenos Aires",
            "eventos deportivos en Madrid",
            "teatro en París",
            "conferencia tech en Barcelona",
            "fiesta en Palermo",
            "música en México"
        ]
        
        for test in test_cases:
            print(f"\n🧠 Testing: '{test}'")
            result = await service.get_all_api_parameters(test)
            print(f"   Intent: {result['intent']['type']} (confidence: {result['intent']['confidence']:.2f})")
            print(f"   Country: {result['intent']['country']}")
            print(f"   City: {result['intent']['city']}")
            print(f"   Category: {result['intent']['category']}")
            print(f"   Keywords: {result['intent']['keywords']}")
    
    # Ejecutar tests
    asyncio.run(test_intent_service())