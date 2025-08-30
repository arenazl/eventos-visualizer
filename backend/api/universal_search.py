"""
API Universal Search - Endpoint multilenguaje y multicultural
Detecta idioma, tipo de usuario (turista/local) y adapta recomendaciones
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.universal_ai_search import UniversalAISearchService

router = APIRouter()
universal_service = UniversalAISearchService()

class UniversalSearchRequest(BaseModel):
    query: str
    location: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class UniversalSearchResponse(BaseModel):
    query: str
    detected_language: str
    user_type: str
    location: Optional[Dict[str, Any]]
    category: Optional[str]
    response: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: str

@router.post("/search", response_model=UniversalSearchResponse)
async def universal_search(request: UniversalSearchRequest):
    """
    Búsqueda universal que funciona en cualquier idioma
    
    Ejemplos de queries que entiende:
    
    🇦🇷 Español (Local):
    - "Qué hay para hacer este finde"
    - "Bares copados en Palermo"
    - "Algo para hacer con los pibes"
    
    🇦🇷 Español (Turista):
    - "Primera vez en Buenos Aires, qué visitar"
    - "Lugares típicos para conocer"
    - "Dónde comer el mejor asado"
    
    🇺🇸 English (Tourist):
    - "First time in Buenos Aires, what to see"
    - "Best tango shows for tourists"
    - "Safe neighborhoods for dinner"
    
    🇧🇷 Português:
    - "Primeira vez em Buenos Aires"
    - "Onde comer churrasco"
    
    🇫🇷 Français:
    - "Première fois à Buenos Aires"
    - "Restaurants typiques"
    
    🇩🇪 Deutsch:
    - "Erste Mal in Buenos Aires"
    - "Typische Restaurants"
    
    🇨🇳 中文:
    - "布宜诺斯艾利斯旅游"
    - "探戈表演"
    """
    
    try:
        # Procesar query con el servicio universal
        result = await universal_service.process_universal_query(
            query=request.query,
            user_location=request.location
        )
        
        return UniversalSearchResponse(
            query=request.query,
            detected_language=result["detected_language"],
            user_type=result["user_type"],
            location=result.get("location"),
            category=result.get("category"),
            response=result["response"],
            context=result["context"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-languages")
async def get_supported_languages():
    """
    Devuelve los idiomas soportados
    """
    return {
        "languages": [
            {"code": "es", "name": "Español", "native": "Español"},
            {"code": "en", "name": "English", "native": "English"},
            {"code": "pt", "name": "Portuguese", "native": "Português"},
            {"code": "fr", "name": "French", "native": "Français"},
            {"code": "de", "name": "German", "native": "Deutsch"},
            {"code": "it", "name": "Italian", "native": "Italiano"},
            {"code": "zh", "name": "Chinese", "native": "中文"},
            {"code": "ja", "name": "Japanese", "native": "日本語"},
            {"code": "ko", "name": "Korean", "native": "한국어"}
        ],
        "auto_detect": True,
        "default": "es"
    }

@router.post("/analyze-intent")
async def analyze_intent(request: UniversalSearchRequest):
    """
    Analiza la intención del usuario sin ejecutar búsqueda
    Útil para debugging y entender qué detecta el sistema
    """
    try:
        # Detectar componentes
        language = universal_service.detect_language(request.query)
        user_type = universal_service.detect_user_type(request.query, language)
        location = universal_service.extract_location(request.query)
        category = universal_service.extract_category(request.query, language)
        
        return {
            "query": request.query,
            "analysis": {
                "language": {
                    "code": language.value,
                    "name": universal_service.get_language_name(language)
                },
                "user_type": user_type.value,
                "is_tourist": user_type.value == "tourist",
                "location_detected": location,
                "category_detected": category,
                "confidence_scores": {
                    "language": 0.95,  # En producción usar modelo de confianza real
                    "user_type": 0.85,
                    "location": 0.90 if location else 0.0,
                    "category": 0.88 if category else 0.0
                }
            },
            "recommendations_approach": "tourist_friendly" if user_type.value == "tourist" else "local_insider",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate-response")
async def translate_response(data: Dict[str, Any]):
    """
    Traduce una respuesta a otro idioma
    Útil cuando el usuario cambia de idioma mid-conversation
    """
    original_text = data.get("text", "")
    target_language = data.get("target_language", "en")
    
    # Aquí podrías usar Google Translate API o Gemini para traducir
    # Por ahora retornamos un placeholder
    
    return {
        "original": original_text,
        "translated": f"[Translated to {target_language}]: {original_text}",
        "target_language": target_language
    }