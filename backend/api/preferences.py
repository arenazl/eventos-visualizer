"""
API endpoints para manejo de preferencias de usuario y machine learning
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import aiomysql
from decimal import Decimal

from services.preferences_mysql import PreferencesEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/preferences", tags=["preferences"])

# Pydantic models para requests
class UserInteractionRequest(BaseModel):
    interaction_type: str  # 'view', 'click', 'save', 'share', 'search', 'ai_chat'
    event_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    ai_query: Optional[str] = None
    ai_response: Optional[str] = None
    duration_seconds: Optional[int] = None
    success: Optional[bool] = None

class PreferencesUpdateRequest(BaseModel):
    category_weights: Optional[Dict[str, float]] = None
    preferred_neighborhoods: Optional[List[str]] = None
    location_flexibility: Optional[float] = None
    preferred_times: Optional[Dict[str, float]] = None
    price_sensitivity: Optional[float] = None
    max_preferred_price: Optional[float] = None
    prefers_free_events: Optional[bool] = None
    communication_style: Optional[str] = None
    max_suggestions_per_query: Optional[int] = None

class FeedbackRequest(BaseModel):
    feedback_type: str  # 'helpful', 'not_helpful', 'partially', 'love_it', 'hate_it'
    context: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None

@router.post("/initialize/{user_id}")
async def initialize_user_preferences(user_id: str):
    """Inicializa preferencias para un nuevo usuario"""
    try:
        # Obtener el pool global
        from main_mysql import pool
        engine = PreferencesEngine(pool)
        preferences = await engine.initialize_user_preferences(user_id)
        
        return {
            "status": "success",
            "message": "Preferencias inicializadas correctamente",
            "preferences": {
                "user_id": preferences.user_id,
                "category_weights": preferences.category_weights,
                "preferred_neighborhoods": preferences.preferred_neighborhoods,
                "location_flexibility": preferences.location_flexibility,
                "preferred_times": preferences.preferred_times,
                "match_percentage": 60,  # Inicial
                "learning_iterations": preferences.learning_iterations
            }
        }
    except Exception as e:
        logger.error(f"Error initializing preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando preferencias")

@router.get("/{user_id}")
async def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    """Obtiene las preferencias actuales del usuario"""
    try:
        engine = PreferencesEngine(db)
        preferences = await engine.get_user_preferences(user_id)
        
        if not preferences:
            # Auto-inicializar si no existen
            preferences = await engine.initialize_user_preferences(user_id)
        
        # Obtener estadísticas del usuario
        stats = await engine.get_user_stats(user_id)
        
        return {
            "status": "success",
            "preferences": {
                "user_id": preferences.user_id,
                "category_weights": preferences.category_weights,
                "preferred_neighborhoods": preferences.preferred_neighborhoods,
                "location_flexibility": preferences.location_flexibility,
                "preferred_times": preferences.preferred_times,
                "price_sensitivity": preferences.price_sensitivity,
                "max_preferred_price": float(preferences.max_preferred_price) if preferences.max_preferred_price else None,
                "prefers_free_events": preferences.prefers_free_events,
                "communication_style": preferences.communication_style,
                "max_suggestions_per_query": preferences.max_suggestions_per_query,
                "learning_iterations": preferences.learning_iterations,
                "last_interaction": preferences.last_interaction.isoformat() if preferences.last_interaction else None,
                "created_at": preferences.created_at.isoformat() if preferences.created_at else None
            },
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo preferencias")

@router.post("/{user_id}/interaction")
async def record_user_interaction(
    user_id: str, 
    interaction: UserInteractionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Registra una interacción del usuario para aprendizaje automático"""
    try:
        engine = PreferencesEngine(db)
        
        # Enriquecer contexto con información de la request
        context = interaction.context or {}
        context.update({
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await engine.record_interaction(
            user_id=user_id,
            interaction_type=interaction.interaction_type,
            context=context,
            event_id=interaction.event_id,
            ai_query=interaction.ai_query,
            ai_response=interaction.ai_response,
            duration_seconds=interaction.duration_seconds,
            success=interaction.success
        )
        
        # Si es una interacción significativa, ejecutar aprendizaje
        if interaction.interaction_type in ["save", "share", "search"]:
            await engine.learn_from_interactions(user_id)
        
        return {
            "status": "success",
            "message": "Interacción registrada correctamente",
            "learning_triggered": interaction.interaction_type in ["save", "share", "search"]
        }
        
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Error registrando interacción")

@router.put("/{user_id}")
async def update_user_preferences(
    user_id: str,
    updates: PreferencesUpdateRequest,
    db: Session = Depends(get_db)
):
    """Actualiza preferencias del usuario manualmente"""
    try:
        engine = PreferencesEngine(db)
        preferences = await engine.get_user_preferences(user_id)
        
        if not preferences:
            preferences = await engine.initialize_user_preferences(user_id)
        
        # Aplicar actualizaciones
        update_fields = []
        
        if updates.category_weights is not None:
            preferences.category_weights = updates.category_weights
            update_fields.append("category_weights")
        
        if updates.preferred_neighborhoods is not None:
            preferences.preferred_neighborhoods = updates.preferred_neighborhoods
            update_fields.append("preferred_neighborhoods")
        
        if updates.location_flexibility is not None:
            preferences.location_flexibility = updates.location_flexibility
            update_fields.append("location_flexibility")
        
        if updates.preferred_times is not None:
            preferences.preferred_times = updates.preferred_times
            update_fields.append("preferred_times")
        
        if updates.price_sensitivity is not None:
            preferences.price_sensitivity = updates.price_sensitivity
            update_fields.append("price_sensitivity")
        
        if updates.max_preferred_price is not None:
            preferences.max_preferred_price = updates.max_preferred_price
            update_fields.append("max_preferred_price")
        
        if updates.prefers_free_events is not None:
            preferences.prefers_free_events = updates.prefers_free_events
            update_fields.append("prefers_free_events")
        
        if updates.communication_style is not None:
            preferences.communication_style = updates.communication_style
            update_fields.append("communication_style")
        
        if updates.max_suggestions_per_query is not None:
            preferences.max_suggestions_per_query = updates.max_suggestions_per_query
            update_fields.append("max_suggestions_per_query")
        
        preferences.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": "Preferencias actualizadas correctamente",
            "updated_fields": update_fields
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error actualizando preferencias")

@router.post("/{user_id}/feedback")
async def submit_user_feedback(
    user_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Recibe feedback del usuario para mejorar el algoritmo"""
    try:
        engine = PreferencesEngine(db)
        preferences = await engine.get_user_preferences(user_id)
        
        if not preferences:
            preferences = await engine.initialize_user_preferences(user_id)
        
        # Ajustar score de feedback basado en el tipo
        feedback_adjustment = {
            "love_it": 0.1,
            "helpful": 0.05,
            "partially": 0.0,
            "not_helpful": -0.05,
            "hate_it": -0.1
        }.get(feedback.feedback_type, 0.0)
        
        # Actualizar feedback score con límites
        current_score = preferences.feedback_score or 0.5
        new_score = max(0.0, min(1.0, current_score + feedback_adjustment))
        preferences.feedback_score = new_score
        
        # Registrar la interacción de feedback
        await engine.record_interaction(
            user_id=user_id,
            interaction_type="feedback",
            context={
                "feedback_type": feedback.feedback_type,
                "comment": feedback.comment,
                **feedback.context
            } if feedback.context else {
                "feedback_type": feedback.feedback_type,
                "comment": feedback.comment
            },
            success=feedback.feedback_type in ["helpful", "love_it"]
        )
        
        # Si el feedback es negativo, ejecutar aprendizaje para ajustar
        if feedback.feedback_type in ["not_helpful", "hate_it"]:
            await engine.learn_from_interactions(user_id)
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Feedback registrado correctamente",
            "new_feedback_score": round(new_score, 2),
            "learning_triggered": feedback.feedback_type in ["not_helpful", "hate_it"]
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error procesando feedback")

@router.post("/{user_id}/learn")
async def trigger_learning(user_id: str, db: Session = Depends(get_db)):
    """Ejecuta manualmente el proceso de aprendizaje para el usuario"""
    try:
        engine = PreferencesEngine(db)
        await engine.learn_from_interactions(user_id)
        
        # Obtener estadísticas actualizadas
        stats = await engine.get_user_stats(user_id)
        
        return {
            "status": "success",
            "message": "Aprendizaje ejecutado correctamente",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error triggering learning: {str(e)}")
        raise HTTPException(status_code=500, detail="Error ejecutando aprendizaje")

@router.get("/{user_id}/stats")
async def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """Obtiene estadísticas del usuario para el menú de perfil"""
    try:
        engine = PreferencesEngine(db)
        stats = await engine.get_user_stats(user_id)
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")

@router.get("/{user_id}/match-score/{event_id}")
async def calculate_event_match_score(
    user_id: str, 
    event_id: str, 
    db: Session = Depends(get_db)
):
    """Calcula el score de match entre el usuario y un evento específico"""
    try:
        from models.events import Event
        
        engine = PreferencesEngine(db)
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        match_score = await engine.calculate_match_score(user_id, event)
        
        return {
            "status": "success",
            "event_id": event_id,
            "match_score": round(match_score, 3),
            "match_percentage": round(match_score * 100, 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating match score: {str(e)}")
        raise HTTPException(status_code=500, detail="Error calculando score de match")

@router.delete("/{user_id}/reset")
async def reset_user_preferences(user_id: str, db: Session = Depends(get_db)):
    """Resetea las preferencias del usuario a valores por defecto"""
    try:
        # Eliminar preferencias existentes
        db.query(UserPreferences).filter(UserPreferences.user_id == user_id).delete()
        db.query(UserInteraction).filter(UserInteraction.user_id == user_id).delete()
        
        # Inicializar nuevas preferencias
        engine = PreferencesEngine(db)
        preferences = await engine.initialize_user_preferences(user_id)
        
        return {
            "status": "success",
            "message": "Preferencias reseteadas correctamente",
            "preferences": {
                "user_id": preferences.user_id,
                "category_weights": preferences.category_weights,
                "match_percentage": 60
            }
        }
        
    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error reseteando preferencias")