"""
🌎 Contexto Cultural para IA - El Amigo Local Inteligente
Detecta si el usuario es local o turista y adapta el lenguaje/recomendaciones
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime

class UserType(Enum):
    LOCAL = "local"           # Vive en la ciudad
    TOURIST = "tourist"       # Visitando la ciudad  
    EXPAT = "expat"          # Vive pero es extranjero
    UNKNOWN = "unknown"       # No se puede determinar

class CulturalLevel(Enum):
    NATIVE = "native"         # Conoce toda la jerga local
    FAMILIAR = "familiar"     # Entiende pero no usa jerga
    LEARNING = "learning"     # Sabe algunas cosas básicas
    NEWCOMER = "newcomer"     # No conoce nada local

@dataclass
class UserContext:
    user_type: UserType
    cultural_level: CulturalLevel  
    location: str
    detected_language: str
    confidence: float          # 0.0 - 1.0 que tan seguro estamos

# 🇦🇷 CONTEXTO CULTURAL ARGENTINA
ARGENTINA_CULTURAL_DATA = {
    "slang": {
        # Eventos y entretenimiento
        "recital": "concierto",
        "boliche": "nightclub", 
        "previa": "pre-party drinks",
        "after": "after-party",
        "carrete": "party", # chileno, indica turista
        "fiesta": "party",
        
        # Tiempo y horarios  
        "finde": "weekend",
        "madrugada": "early morning (2-6 AM)",
        "tardecita": "evening",
        
        # Dinero y precios
        "luca": "1000 pesos",
        "gambas": "money", 
        "barato": "cheap",
        "salado": "expensive",
        
        # Expresiones
        "copado": "cool/awesome",
        "zarpado": "amazing",
        "un caño": "excellent",
        "está piola": "it's cool",
        "dale": "ok/let's go",
        "che": "hey/dude"
    },
    
    "cultural_patterns": {
        "dinner_time": "21:00-23:00",
        "nightlife_start": "02:00",  # Sí, 2 AM!
        "weekend_nights": ["viernes", "sábado", "domingo"],
        "casual_greetings": ["che", "qué tal", "cómo andás"],
        "time_references": ["finde", "el sábado", "la semana que viene"]
    },
    
    "local_knowledge": {
        "neighborhoods": {
            "Palermo": "trendy, young crowd, bars",
            "San Telmo": "tango, tourists, historic", 
            "Recoleta": "upscale, cultural",
            "Villa Crick": "alternative, underground",
            "Puerto Madero": "business, expensive"
        },
        "venues": {
            "Luna Park": "iconic venue",
            "Niceto": "electronic music",
            "El Querandí": "tango shows",
            "Teatro Colón": "opera house"
        },
        "transport": {
            "subte": "subway",
            "bondis": "buses", 
            "remis": "taxi/uber"
        }
    },
    
    "tourist_explanations": {
        "asado": "Argentine BBQ - social gathering with grilled meat",
        "tango": "passionate dance originated in Buenos Aires",  
        "mate": "traditional herbal tea shared among friends",
        "choripán": "chorizo sandwich - street food staple",
        "empanadas": "stuffed pastries - must try!"
    }
}

def detect_user_type(query: str, user_agent: str = "", location_context: Dict = None) -> UserContext:
    """
    Detectar si el usuario es local o turista basado en su query y contexto
    """
    query_lower = query.lower()
    
    # Indicadores de TURISTA
    tourist_signals = [
        # Idioma extranjero
        r'\b(what|where|when|how|best|tourist|visit|recommend)\b',
        
        # Preguntas típicas de turista
        r'authentic\s+\w+',
        r'local\s+experience',
        r'traditional\s+\w+',
        r'must\s+(see|do|visit)',
        r'hidden\s+gems',
        
        # Español formal/no local
        r'\b(espectáculo|presentación)\b',  # vs "recital"
        r'\bdiscoteca\b',                   # vs "boliche"
        r'\bconcierto\b',                   # vs "recital"
    ]
    
    # Indicadores de LOCAL  
    local_signals = [
        # Jerga argentina
        r'\b(che|dale|copado|zarpado|piola|finde|boliche|recital|previa|after)\b',
        
        # Referencias locales específicas
        r'\b(subte|bondi|remis)\b',
        r'\b(palermo|san telmo|recoleta|puerto madero)\b',
        
        # Formas casuales
        r'qué\s+onda',
        r'hay\s+algo',
        r'algún\s+\w+',
        r'está\s+bueno'
    ]
    
    # Calcular scores
    tourist_score = sum(len(re.findall(pattern, query_lower, re.IGNORECASE)) 
                       for pattern in tourist_signals)
    local_score = sum(len(re.findall(pattern, query_lower, re.IGNORECASE)) 
                     for pattern in local_signals)
    
    # Determinar tipo de usuario
    if local_score > tourist_score and local_score > 0:
        user_type = UserType.LOCAL
        cultural_level = CulturalLevel.NATIVE if local_score >= 2 else CulturalLevel.FAMILIAR
        confidence = min(0.9, 0.6 + (local_score * 0.1))
        
    elif tourist_score > local_score and tourist_score > 0:
        user_type = UserType.TOURIST  
        cultural_level = CulturalLevel.NEWCOMER if tourist_score >= 2 else CulturalLevel.LEARNING
        confidence = min(0.9, 0.6 + (tourist_score * 0.1))
        
    else:
        user_type = UserType.UNKNOWN
        cultural_level = CulturalLevel.FAMILIAR
        confidence = 0.3
    
    # Detectar idioma
    english_patterns = len(re.findall(r'\b(what|where|when|best|show|event)\b', query_lower))
    spanish_patterns = len(re.findall(r'\b(qué|dónde|cuándo|mejor|evento|show)\b', query_lower))
    
    detected_language = "en" if english_patterns > spanish_patterns else "es"
    
    return UserContext(
        user_type=user_type,
        cultural_level=cultural_level,
        location=location_context.get('location', 'Buenos Aires') if location_context else 'Buenos Aires',
        detected_language=detected_language,
        confidence=confidence
    )

def get_cultural_prompt(user_context: UserContext, original_query: str, country_code: str = "AR") -> str:
    """
    Generar prompt culturalmente apropiado basado en el contexto del usuario
    """
    
    location = user_context.location
    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M")
    
    if user_context.user_type == UserType.LOCAL and user_context.detected_language == "es":
        # PROMPT PARA LOCAL ARGENTINO
        prompt = f"""
Sos un amigo porteño que conoce toda la movida de {location}. 
Hablá como un local: usá jerga argentina, sé informal y copado.

QUERY DEL USER: "{original_query}"
MOMENTO: {current_time}
UBICACIÓN: {location}

COMO RESPONDER:
- Usá jerga: "recital" (no concierto), "boliche" (no discoteca), "finde", "che", "copado", "zarpado"
- Sé específico con lugares: mencioná barrios, venues conocidos  
- Horarios reales: "arranca a las 2 de la mañana" (horarios porteños)
- Precios en contexto: "$15K está salado" o "$5K re accesible"
- Consejos de local: cómo llegar, dónde hacer previa, qué evitar

EJEMPLOS DE TU ESTILO:
- "Che, mirá, hay un recital zarpado en Niceto el finde..."
- "Para hacer previa, andá a los bares de Palermo..."  
- "Ojo que arranca tarde, tipo 2 AM, pero vale la pena..."

NO uses lenguaje formal o turístico. Hablá como hablaría tu amigo porteño.
        """
        
    elif user_context.user_type == UserType.TOURIST and user_context.detected_language == "en":
        # PROMPT PARA TURISTA INGLÉS
        prompt = f"""
You're a knowledgeable local friend in {location} helping a tourist discover authentic experiences.
Be friendly, explain local customs, and give cultural context.

USER QUERY: "{original_query}"
CURRENT TIME: {current_time}  
LOCATION: {location}

HOW TO RESPOND:
- Mix English with key Spanish terms (with explanations)
- Explain Argentine culture: "tango", "asado", late nightlife
- Give context: "Porteños (Buenos Aires locals) party LATE - clubs start at 2 AM!"
- Price context: "$15K ARS ≈ $15 USD" 
- Cultural tips: how locals do it, what to expect, etiquette

EXAMPLES OF YOUR STYLE:
- "Hey! There's an amazing 'recital' (that's what Argentines call concerts) at Niceto..."
- "Pro tip: Start with 'previa' (pre-party drinks) in Palermo around 10 PM..."
- "Fair warning: Argentine nightlife starts LATE (2 AM), but it's worth it!"

Help them experience Buenos Aires like a local, not a tourist trap.
        """
        
    else:
        # PROMPT GENÉRICO CON ADAPTACIÓN CULTURAL
        lang = "español" if user_context.detected_language == "es" else "English"
        prompt = f"""
Sos un asistente de eventos que conoce muy bien {location}.
Adaptá tu respuesta al nivel cultural del usuario.

CONSULTA: "{original_query}"
MOMENTO: {current_time}
IDIOMA: {lang}
NIVEL CULTURAL: {user_context.cultural_level.value}

Dá recomendaciones específicas para {location}, explicando contexto cultural cuando sea necesario.
Si el usuario parece turista, explicá costumbres locales.
Si parece local, usá referencias que entendería alguien de acá.
        """
    
    return prompt.strip()

def localize_event_description(event_data: Dict, user_context: UserContext) -> Dict:
    """
    Localizar descripción de evento según contexto cultural del usuario
    """
    
    if user_context.user_type == UserType.LOCAL and user_context.detected_language == "es":
        # Para locales: jerga y referencias conocidas
        translations = {
            "concert": "recital",
            "party": "fiesta", 
            "nightclub": "boliche",
            "expensive": "salado",
            "cheap": "barato",
            "awesome": "zarpado",
            "cool": "copado"
        }
        
    elif user_context.user_type == UserType.TOURIST and user_context.detected_language == "en":
        # Para turistas: explicaciones culturales  
        translations = {
            "recital": "concert (local term)",
            "boliche": "nightclub (local term)", 
            "previa": "pre-party drinks (Argentine tradition)",
            "asado": "Argentine BBQ",
            "milonga": "tango social dance event"
        }
        
    else:
        translations = {}
    
    # Aplicar traducciones al evento
    localized_event = event_data.copy()
    
    for original, localized in translations.items():
        if 'description' in localized_event:
            localized_event['description'] = localized_event['description'].replace(original, localized)
        if 'title' in localized_event:
            localized_event['title'] = localized_event['title'].replace(original, localized)
            
    return localized_event