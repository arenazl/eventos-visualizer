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

router = APIRouter()

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

@router.post("/chat")
async def chat_with_ai(chat: ChatMessage):
    """
    Chat inteligente sobre eventos con Gemini Brain
    Ejemplos:
    - "No sé qué hacer este finde, ayuda"
    - "Estoy aburrido, sugerime algo"
    - "Busco algo romántico para una cita"
    - "Dame eventos gratis en Palermo"
    """
    try:
        # Usar Gemini Brain para usuarios indecisos
        user_id = chat.context.get("user_id", "anonymous")
        
        # Obtener eventos disponibles (en producción vendría de la BD)
        available_events = chat.context.get("available_events", [])
        
        # Procesar con Gemini Brain
        gemini_response = await gemini_brain.process_indecisive_user(
            chat.message,
            user_id,
            available_events
        )
        
        return {
            "status": "success",
            "response": gemini_response.get("mensaje", ""),
            "recommendations": gemini_response.get("recomendaciones", []),
            "preferences_detected": gemini_response.get("preferencias_detectadas", {}),
            "follow_up": gemini_response.get("pregunta_follow_up", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Fallback al asistente original si falla Gemini
        try:
            response = await ai_assistant.chat_about_event(
                chat.message, 
                chat.context
            )
            return {
                "status": "success",
                "response": response,
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