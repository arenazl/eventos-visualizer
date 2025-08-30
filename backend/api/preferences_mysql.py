"""
API endpoints para manejo de preferencias de usuario y machine learning con MySQL
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import json
from decimal import Decimal

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
        from main_mysql import pool
        from services.preferences_mysql import PreferencesEngine
        
        engine = PreferencesEngine(pool)
        preferences = await engine.initialize_user_preferences(user_id)
        
        return {
            "status": "success",
            "message": "Preferencias inicializadas correctamente",
            "preferences": {
                "user_id": preferences.get("user_id"),
                "category_weights": json.loads(preferences.get("category_weights", "{}")),
                "preferred_neighborhoods": json.loads(preferences.get("preferred_neighborhoods", "[]")),
                "location_flexibility": float(preferences.get("location_flexibility", 0.7)),
                "preferred_times": json.loads(preferences.get("preferred_times", "{}")),
                "match_percentage": 60,
                "learning_iterations": preferences.get("learning_iterations", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error initializing preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando preferencias")

@router.get("/{user_id}")
async def get_user_preferences(user_id: str):
    """Obtiene las preferencias actuales del usuario"""
    try:
        from main_mysql import pool
        from services.preferences_mysql import PreferencesEngine
        
        engine = PreferencesEngine(pool)
        preferences = await engine.get_user_preferences(user_id)
        
        if not preferences:
            # Auto-inicializar si no existen
            preferences = await engine.initialize_user_preferences(user_id)
        
        # Obtener estadísticas del usuario
        stats = await engine.get_user_stats(user_id)
        
        # Convertir tipos de datos
        def convert_decimal(value):
            if isinstance(value, Decimal):
                return float(value)
            return value
        
        return {
            "status": "success",
            "preferences": {
                "user_id": preferences.get("user_id"),
                "category_weights": json.loads(preferences.get("category_weights", "{}")),
                "preferred_neighborhoods": json.loads(preferences.get("preferred_neighborhoods", "[]")),
                "location_flexibility": convert_decimal(preferences.get("location_flexibility")),
                "preferred_times": json.loads(preferences.get("preferred_times", "{}")),
                "price_sensitivity": convert_decimal(preferences.get("price_sensitivity")),
                "max_preferred_price": convert_decimal(preferences.get("max_preferred_price")) if preferences.get("max_preferred_price") else None,
                "prefers_free_events": preferences.get("prefers_free_events"),
                "communication_style": preferences.get("communication_style"),
                "max_suggestions_per_query": preferences.get("max_suggestions_per_query"),
                "learning_iterations": preferences.get("learning_iterations"),
                "last_interaction": preferences.get("last_interaction").isoformat() if preferences.get("last_interaction") else None,
                "created_at": preferences.get("created_at").isoformat() if preferences.get("created_at") else None
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
    request: Request
):
    """Registra una interacción del usuario para aprendizaje automático"""
    try:
        from main_mysql import pool
        from services.preferences_mysql import PreferencesEngine
        
        engine = PreferencesEngine(pool)
        
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
        learning_triggered = False
        if interaction.interaction_type in ["save", "share", "search"]:
            await engine.learn_from_interactions(user_id)
            learning_triggered = True
        
        return {
            "status": "success",
            "message": "Interacción registrada correctamente",
            "learning_triggered": learning_triggered
        }
        
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Error registrando interacción")

@router.put("/{user_id}")
async def update_user_preferences(
    user_id: str,
    updates: PreferencesUpdateRequest
):
    """Actualiza preferencias del usuario manualmente"""
    try:
        from main_mysql import pool
        import aiomysql
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Verificar si existen preferencias
                await cursor.execute(
                    "SELECT id FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                exists = await cursor.fetchone()
                
                if not exists:
                    # Inicializar preferencias primero
                    from services.preferences_mysql import PreferencesEngine
                    engine = PreferencesEngine(pool)
                    await engine.initialize_user_preferences(user_id)
                
                # Aplicar actualizaciones
                update_fields = []
                update_values = []
                
                if updates.category_weights is not None:
                    update_fields.append("category_weights = %s")
                    update_values.append(json.dumps(updates.category_weights))
                
                if updates.preferred_neighborhoods is not None:
                    update_fields.append("preferred_neighborhoods = %s")
                    update_values.append(json.dumps(updates.preferred_neighborhoods))
                
                if updates.location_flexibility is not None:
                    update_fields.append("location_flexibility = %s")
                    update_values.append(updates.location_flexibility)
                
                if updates.preferred_times is not None:
                    update_fields.append("preferred_times = %s")
                    update_values.append(json.dumps(updates.preferred_times))
                
                if updates.price_sensitivity is not None:
                    update_fields.append("price_sensitivity = %s")
                    update_values.append(updates.price_sensitivity)
                
                if updates.max_preferred_price is not None:
                    update_fields.append("max_preferred_price = %s")
                    update_values.append(updates.max_preferred_price)
                
                if updates.prefers_free_events is not None:
                    update_fields.append("prefers_free_events = %s")
                    update_values.append(updates.prefers_free_events)
                
                if updates.communication_style is not None:
                    update_fields.append("communication_style = %s")
                    update_values.append(updates.communication_style)
                
                if updates.max_suggestions_per_query is not None:
                    update_fields.append("max_suggestions_per_query = %s")
                    update_values.append(updates.max_suggestions_per_query)
                
                if update_fields:
                    update_fields.append("updated_at = NOW()")
                    update_values.append(user_id)
                    
                    query = f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = %s"
                    await cursor.execute(query, update_values)
        
        return {
            "status": "success",
            "message": "Preferencias actualizadas correctamente",
            "updated_fields": len(update_fields) - 1  # -1 para no contar updated_at
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error actualizando preferencias")

@router.post("/{user_id}/feedback")
async def submit_user_feedback(
    user_id: str,
    feedback: FeedbackRequest
):
    """Recibe feedback del usuario para mejorar el algoritmo"""
    try:
        from main_mysql import pool
        from services.preferences_mysql import PreferencesEngine
        import aiomysql
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Obtener feedback score actual
                await cursor.execute(
                    "SELECT feedback_score FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                result = await cursor.fetchone()
                
                if not result:
                    # Inicializar preferencias
                    engine = PreferencesEngine(pool)
                    await engine.initialize_user_preferences(user_id)
                    current_score = 0.5
                else:
                    current_score = float(result[0]) if result[0] else 0.5
                
                # Ajustar score de feedback basado en el tipo
                feedback_adjustment = {
                    "love_it": 0.1,
                    "helpful": 0.05,
                    "partially": 0.0,
                    "not_helpful": -0.05,
                    "hate_it": -0.1
                }.get(feedback.feedback_type, 0.0)
                
                # Actualizar feedback score con límites
                new_score = max(0.0, min(1.0, current_score + feedback_adjustment))
                
                await cursor.execute('''
                    UPDATE user_preferences 
                    SET feedback_score = %s 
                    WHERE user_id = %s
                ''', (new_score, user_id))
                
                # Registrar la interacción de feedback
                engine = PreferencesEngine(pool)
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
                learning_triggered = False
                if feedback.feedback_type in ["not_helpful", "hate_it"]:
                    await engine.learn_from_interactions(user_id)
                    learning_triggered = True
        
        return {
            "status": "success",
            "message": "Feedback registrado correctamente",
            "new_feedback_score": round(new_score, 2),
            "learning_triggered": learning_triggered
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Error procesando feedback")

@router.post("/{user_id}/learn")
async def trigger_learning(user_id: str):
    """Ejecuta manualmente el proceso de aprendizaje para el usuario"""
    try:
        from main_mysql import pool
        from services.preferences_mysql import PreferencesEngine
        
        engine = PreferencesEngine(pool)
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
async def get_user_stats(user_id: str):
    """Obtiene estadísticas del usuario para el menú de perfil"""
    try:
        from main_mysql import pool
        from services.preferences_mysql import PreferencesEngine
        
        engine = PreferencesEngine(pool)
        stats = await engine.get_user_stats(user_id)
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")

@router.delete("/{user_id}/reset")
async def reset_user_preferences(user_id: str):
    """Resetea las preferencias del usuario a valores por defecto"""
    try:
        from main_mysql import pool
        from services.preferences_mysql import PreferencesEngine
        import aiomysql
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Eliminar preferencias existentes
                await cursor.execute("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))
                await cursor.execute("DELETE FROM user_interactions WHERE user_id = %s", (user_id,))
                await cursor.execute("DELETE FROM preference_updates WHERE user_id = %s", (user_id,))
        
        # Inicializar nuevas preferencias
        engine = PreferencesEngine(pool)
        preferences = await engine.initialize_user_preferences(user_id)
        
        return {
            "status": "success",
            "message": "Preferencias reseteadas correctamente",
            "preferences": {
                "user_id": preferences.get("user_id"),
                "category_weights": json.loads(preferences.get("category_weights", "{}")),
                "match_percentage": 60
            }
        }
        
    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reseteando preferencias")