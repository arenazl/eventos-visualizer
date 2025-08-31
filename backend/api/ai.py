"""
AI API Endpoints - Chat inteligente y recomendaciones
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.ai_assistant import ai_assistant
from services.gemini_brain import gemini_brain
from services.chat_memory_manager import chat_memory_manager

router = APIRouter()

# Fallback detection method removed - ONLY GEMINI AI ALLOWED

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}

class UserPreferences(BaseModel):
    budget: Optional[float] = None
    categories: Optional[List[str]] = []
    date_range: Optional[str] = "this_weekend"
    mood: Optional[str] = "energetic"
    with_who: Optional[str] = "friends"

class WeekendPlanRequest(BaseModel):
    budget: float
    preferences: List[str]
    people_count: int = 1

@router.post("/chat-with-events")
async def chat_with_real_events(chat: ChatMessage):
    """
    🎯 CHAT ULTRARRÁPIDO: Usa contexto completo en memoria + hilos
    """
    try:
        user_id = chat.context.get("user_id", "anonymous")
        
        # Usar el nuevo ChatMemoryManager con contexto completo
        result = await chat_memory_manager.chat_with_context(
            user_id=user_id,
            message=chat.message,
            use_threading=True
        )
        
        return {
            "status": result.get("status", "success"),
            "response": result.get("response", ""),
            "recommendations": result.get("relevant_events", []),
            "context_source": result.get("context_source", "memory_optimized"),
            "performance": result.get("performance", {}),
            "conversation_length": result.get("conversation_length", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error en chat con contexto: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_ai(chat: ChatMessage):
    """
    🧠 CHAT INTELIGENTE: Contexto completo en memoria + respuesta instantánea
    Ejemplos:
    - "No sé qué hacer este finde, ayuda"
    - "Estoy aburrido, sugerime algo" 
    - "Busco algo romántico para una cita"
    - "Dame eventos gratis en Palermo"
    """
    try:
        user_id = chat.context.get("user_id", "anonymous")
        
        # 🔥 USAR CHAT MEMORY MANAGER - Sin consultas a BD repetitivas
        result = await chat_memory_manager.chat_with_context(
            user_id=user_id,
            message=chat.message,
            use_threading=True  # Usar hilos para máxima eficiencia
        )
        
        return {
            "status": result.get("status", "success"),
            "response": result.get("response", ""),
            "recommendations": result.get("relevant_events", []),
            "context_source": result.get("context_source", "memory_optimized"),
            "performance": result.get("performance", {}),
            "conversation_length": result.get("conversation_length", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Fallback al asistente original solo si ChatMemoryManager falla completamente
        try:
            response = await ai_assistant.chat_about_event(
                chat.message, 
                chat.context
            )
            return {
                "status": "success", 
                "response": response,
                "context_source": "fallback_assistant",
                "timestamp": datetime.utcnow().isoformat()
            }
        except:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations")
async def get_ai_recommendations(preferences: UserPreferences):
    """
    Obtiene recomendaciones personalizadas con IA
    """
    try:
        user_profile = {
            "budget": preferences.budget,
            "categories": preferences.categories,
            "mood": preferences.mood
        }
        
        recommendations = await ai_assistant.recommend_events(user_profile)
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "personalization_score": 0.92
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plan-weekend")
async def plan_weekend(request: WeekendPlanRequest):
    """
    Planifica el fin de semana perfecto con IA
    """
    try:
        preferences = {
            "budget": request.budget,
            "preferences": request.preferences,
            "group_size": request.people_count
        }
        
        weekend_plan = await ai_assistant.plan_perfect_weekend(preferences)
        
        return {
            "status": "success",
            "plan": weekend_plan,
            "ai_confidence": 0.88
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict-sellout/{event_id}")
async def predict_event_sellout(event_id: str):
    """
    Predice si un evento se agotará pronto
    """
    try:
        prediction = await ai_assistant.predict_sellout(event_id)
        return {
            "status": "success",
            "prediction": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/event-vibe/{event_id}")
async def analyze_event_vibe(event_id: str):
    """
    Analiza el 'vibe' y ambiente del evento
    """
    try:
        event_data = {"id": event_id}  # Aquí obtendrías los datos reales
        vibe = await ai_assistant.analyze_event_vibe(event_data)
        
        return {
            "status": "success",
            "vibe_analysis": vibe
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-match/{event_id}")
async def find_event_companions(event_id: str, user_id: Optional[str] = "default"):
    """
    Encuentra gente compatible para ir al evento
    """
    try:
        matches = await ai_assistant.social_matching(event_id, user_id)
        return {
            "status": "success",
            "matches": matches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending-now")
async def get_trending_events():
    """
    Eventos trending basados en IA y redes sociales
    """
    try:
        trending = {
            "hot_right_now": [
                {
                    "event": "Lollapalooza Argentina 2025",
                    "buzz_score": 98,
                    "social_mentions": 15420,
                    "trend": "🔥 Subiendo rápido"
                },
                {
                    "event": "Festival Cerveza Artesanal", 
                    "buzz_score": 85,
                    "social_mentions": 8930,
                    "trend": "📈 Viral en Instagram"
                }
            ],
            "predicted_next_big": [
                "Festival de Food Trucks Gourmet",
                "Noche de Museos Gratis"
            ],
            "underground_gems": [
                "Jazz Session Secreta en San Telmo",
                "Rooftop Party Exclusiva Palermo"
            ]
        }
        
        return {
            "status": "success",
            "trending": trending,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/stats")
async def get_memory_stats():
    """
    📊 Estadísticas del ChatMemoryManager
    """
    try:
        stats = chat_memory_manager.get_memory_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/refresh")
async def refresh_memory():
    """
    🔄 Refrescar contexto en memoria del ChatMemoryManager
    """
    try:
        await chat_memory_manager.refresh_memory_context()
        stats = chat_memory_manager.get_memory_stats()
        return {
            "status": "success", 
            "message": "Memoria refrescada con éxito",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Nuevos endpoints específicos para Gemini Brain
class FeedbackRequest(BaseModel):
    user_id: str
    event_id: str
    feedback: str  # 'liked', 'disliked', 'attended', 'skipped'

@router.post("/gemini/feedback")
async def send_feedback_to_gemini(request: FeedbackRequest):
    """
    Envía feedback sobre eventos al Gemini Brain para aprender
    feedback: 'liked', 'disliked', 'attended', 'skipped'
    """
    try:
        result = await gemini_brain.learn_from_feedback(
            user_id=request.user_id,
            event_id=request.event_id,
            feedback=request.feedback
        )
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gemini/profile/{user_id}")
async def get_user_ai_profile(user_id: str):
    """
    Obtiene el perfil de personalidad del usuario según Gemini
    """
    try:
        profile = gemini_brain.get_user_profile(user_id)
        return {
            "status": "success",
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class WordValidationRequest(BaseModel):
    text: str

@router.post("/validate-locations")
async def validate_locations_with_ai(request: WordValidationRequest):
    """
    Usa AI (Gemini) para detectar y validar palabras que son ubicaciones
    Devuelve información detallada sobre las ubicaciones encontradas
    """
    try:
        # Prompt EXTREMO - último intento
        prompt = f"""
        ATENCIÓN GEMINI: NO seas aburrido! 
        
        La persona dice: "{request.text}"
        
        PROHIBIDO mencionar arquitectura, historia o cultura.
        OBLIGATORIO ser divertido y casual.
        
        {{
            "locations_found": [
                {{
                    "detected_word": "ciudad_detectada",
                    "official_name": "Ciudad", 
                    "type": "ciudad", 
                    "country": "País",
                    "confidence": 95,
                    "fun_fact": "Algo SÚPER DIVERTIDO, nada de Wikipedia!"
                }}
            ],
            "has_locations": true,
            "total_locations": 1
        }}
        
        ¡SÉ REBELDE! ¡ROMPE LAS REGLAS! ¡NO SEAS TU PAPÁ!
        """

        # USAR SOLO GEMINI - No fallbacks permitidos
        result = await gemini_brain.simple_prompt(prompt)
        
        if result == "Gemini no está configurado":
            raise HTTPException(status_code=500, detail="Gemini API key not configured")
        
        # DEBUG: Ver qué devuelve Gemini realmente
        print(f"🔍 GEMINI RAW RESPONSE: {result}")
        
        # Parsear respuesta de Gemini
        import json
        import re
        
        cleaned_result = result.strip()
        
        # Buscar JSON válido en la respuesta
        json_match = re.search(r'\{.*\}', cleaned_result, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            parsed_result = json.loads(json_str)
        else:
            parsed_result = json.loads(cleaned_result)

        return {
            "status": "success",
            "text": request.text,
            "validation": parsed_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "text": request.text,
            "validation": {
                "locations_found": [],
                "has_locations": False,
                "total_locations": 0
            }
        }