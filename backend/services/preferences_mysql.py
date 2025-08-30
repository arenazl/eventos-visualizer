"""
Motor de Preferencias de Usuario con Machine Learning para MySQL directo
Aprende de las interacciones del usuario para mejorar las recomendaciones
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import math
import aiomysql
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class PreferencesEngine:
    """Motor que aprende y actualiza preferencias del usuario automáticamente"""
    
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool
        
    async def initialize_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Inicializa preferencias para un nuevo usuario"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Verificar si ya existen preferencias
                    await cursor.execute(
                        "SELECT * FROM user_preferences WHERE user_id = %s",
                        (user_id,)
                    )
                    existing = await cursor.fetchone()
                    
                    if existing:
                        return existing
                    
                    # Crear preferencias iniciales
                    initial_prefs = {
                        "category_weights": {
                            "musica": 0.5,
                            "deportes": 0.5, 
                            "cultural": 0.5,
                            "tech": 0.5,
                            "fiestas": 0.5,
                            "hobbies": 0.5,
                            "internacional": 0.5
                        },
                        "preferred_neighborhoods": [],
                        "location_flexibility": 0.7,
                        "preferred_times": {
                            "morning": 0.3,
                            "afternoon": 0.5,
                            "evening": 0.8,
                            "night": 0.4
                        },
                        "price_sensitivity": 0.6,
                        "prefers_free_events": True,
                        "group_size_preference": "any",
                        "social_events_weight": 0.5,
                        "interaction_history": {
                            "viewed_events": [],
                            "clicked_events": [],
                            "saved_events": [],
                            "shared_events": [],
                            "searched_terms": [],
                            "rejected_suggestions": []
                        },
                        "match_score_history": [],
                        "feedback_score": 0.5,
                        "communication_style": "friendly",
                        "prefers_suggestions": True,
                        "max_suggestions_per_query": 3
                    }
                    
                    await cursor.execute('''
                        INSERT INTO user_preferences (
                            user_id, category_weights, preferred_neighborhoods, 
                            location_flexibility, preferred_times, price_sensitivity,
                            prefers_free_events, group_size_preference, social_events_weight,
                            interaction_history, match_score_history, feedback_score,
                            communication_style, prefers_suggestions, max_suggestions_per_query,
                            learning_iterations
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        user_id,
                        json.dumps(initial_prefs["category_weights"]),
                        json.dumps(initial_prefs["preferred_neighborhoods"]),
                        initial_prefs["location_flexibility"],
                        json.dumps(initial_prefs["preferred_times"]),
                        initial_prefs["price_sensitivity"],
                        initial_prefs["prefers_free_events"],
                        initial_prefs["group_size_preference"],
                        initial_prefs["social_events_weight"],
                        json.dumps(initial_prefs["interaction_history"]),
                        json.dumps(initial_prefs["match_score_history"]),
                        initial_prefs["feedback_score"],
                        initial_prefs["communication_style"],
                        initial_prefs["prefers_suggestions"],
                        initial_prefs["max_suggestions_per_query"],
                        0
                    ))
                    
                    # Obtener las preferencias creadas
                    await cursor.execute(
                        "SELECT * FROM user_preferences WHERE user_id = %s",
                        (user_id,)
                    )
                    preferences = await cursor.fetchone()
                    
                    logger.info(f"✅ Preferencias inicializadas para usuario {user_id}")
                    return preferences
                    
        except Exception as e:
            logger.error(f"❌ Error inicializando preferencias: {str(e)}")
            raise

    async def record_interaction(
        self, 
        user_id: str, 
        interaction_type: str, 
        context: Dict = None,
        event_id: str = None,
        ai_query: str = None,
        ai_response: str = None,
        duration_seconds: int = None,
        success: bool = None
    ) -> None:
        """Registra una interacción del usuario para aprendizaje"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Insertar la interacción
                    await cursor.execute('''
                        INSERT INTO user_interactions (
                            user_id, event_id, interaction_type, context,
                            ai_query, ai_response, duration_seconds, success_indicator
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        user_id, event_id, interaction_type, 
                        json.dumps(context or {}),
                        ai_query, ai_response, duration_seconds, success
                    ))
                    
                    # Actualizar historial en preferencias
                    await cursor.execute(
                        "SELECT interaction_history FROM user_preferences WHERE user_id = %s",
                        (user_id,)
                    )
                    result = await cursor.fetchone()
                    
                    if result:
                        history = json.loads(result[0]) if result[0] else {}
                        
                        # Agregar a la lista correspondiente (máximo 100 elementos)
                        timestamp = datetime.utcnow().isoformat()
                        
                        if interaction_type == "view" and event_id:
                            viewed = history.get("viewed_events", [])
                            viewed.append({"event_id": event_id, "timestamp": timestamp})
                            history["viewed_events"] = viewed[-100:]
                        
                        elif interaction_type == "click" and event_id:
                            clicked = history.get("clicked_events", [])
                            clicked.append({"event_id": event_id, "timestamp": timestamp})
                            history["clicked_events"] = clicked[-100:]
                        
                        elif interaction_type == "save" and event_id:
                            saved = history.get("saved_events", [])
                            saved.append({"event_id": event_id, "timestamp": timestamp})
                            history["saved_events"] = saved[-100:]
                        
                        elif interaction_type == "search" and ai_query:
                            searches = history.get("searched_terms", [])
                            searches.append({"query": ai_query, "timestamp": timestamp})
                            history["searched_terms"] = searches[-50:]
                        
                        # Actualizar preferencias
                        await cursor.execute('''
                            UPDATE user_preferences 
                            SET interaction_history = %s, last_interaction = NOW()
                            WHERE user_id = %s
                        ''', (json.dumps(history), user_id))
                    
                    logger.info(f"📝 Interacción registrada: {interaction_type} para usuario {user_id}")
                    
        except Exception as e:
            logger.error(f"❌ Error registrando interacción: {str(e)}")

    async def learn_from_interactions(self, user_id: str) -> None:
        """Analiza interacciones recientes y actualiza preferencias"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Obtener preferencias actuales
                    await cursor.execute(
                        "SELECT * FROM user_preferences WHERE user_id = %s",
                        (user_id,)
                    )
                    preferences = await cursor.fetchone()
                    
                    if not preferences:
                        preferences = await self.initialize_user_preferences(user_id)
                    
                    # Obtener interacciones de los últimos 30 días
                    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                    await cursor.execute('''
                        SELECT * FROM user_interactions 
                        WHERE user_id = %s AND created_at >= %s
                        ORDER BY created_at DESC
                    ''', (user_id, thirty_days_ago))
                    
                    recent_interactions = await cursor.fetchall()
                    
                    if not recent_interactions:
                        logger.info(f"No hay interacciones recientes para usuario {user_id}")
                        return
                    
                    # Analizar categorías más interactuadas
                    category_scores = await self._analyze_category_preferences(cursor, recent_interactions)
                    if category_scores:
                        old_weights = json.loads(preferences.get('category_weights', '{}'))
                        new_weights = await self._update_category_weights(old_weights, category_scores)
                        
                        if new_weights != old_weights:
                            await self._log_preference_update(
                                cursor, user_id, "category_weights", old_weights, new_weights, "ai_learning"
                            )
                            await cursor.execute('''
                                UPDATE user_preferences 
                                SET category_weights = %s 
                                WHERE user_id = %s
                            ''', (json.dumps(new_weights), user_id))
                    
                    # Analizar preferencias de ubicación
                    location_prefs = await self._analyze_location_preferences(recent_interactions)
                    if location_prefs:
                        old_neighborhoods = json.loads(preferences.get('preferred_neighborhoods', '[]'))
                        new_neighborhoods = await self._update_neighborhood_preferences(
                            old_neighborhoods, location_prefs
                        )
                        
                        if new_neighborhoods != old_neighborhoods:
                            await self._log_preference_update(
                                cursor, user_id, "preferred_neighborhoods", old_neighborhoods, 
                                new_neighborhoods, "ai_learning"
                            )
                            await cursor.execute('''
                                UPDATE user_preferences 
                                SET preferred_neighborhoods = %s 
                                WHERE user_id = %s
                            ''', (json.dumps(new_neighborhoods), user_id))
                    
                    # Analizar horarios preferidos
                    time_prefs = await self._analyze_time_preferences(cursor, recent_interactions)
                    if time_prefs:
                        old_times = json.loads(preferences.get('preferred_times', '{}'))
                        new_times = await self._update_time_preferences(old_times, time_prefs)
                        
                        if new_times != old_times:
                            await self._log_preference_update(
                                cursor, user_id, "preferred_times", old_times, new_times, "ai_learning"
                            )
                            await cursor.execute('''
                                UPDATE user_preferences 
                                SET preferred_times = %s 
                                WHERE user_id = %s
                            ''', (json.dumps(new_times), user_id))
                    
                    # Incrementar contador de iteraciones de aprendizaje
                    await cursor.execute('''
                        UPDATE user_preferences 
                        SET learning_iterations = learning_iterations + 1, updated_at = NOW()
                        WHERE user_id = %s
                    ''', (user_id,))
                    
                    logger.info(f"🧠 Preferencias actualizadas para usuario {user_id}")
                    
        except Exception as e:
            logger.error(f"❌ Error en aprendizaje de preferencias: {str(e)}")

    async def _analyze_category_preferences(self, cursor, interactions: List[Dict]) -> Dict[str, float]:
        """Analiza qué categorías prefiere más el usuario basado en interacciones"""
        category_scores = {}
        
        for interaction in interactions:
            if interaction.get('event_id') and interaction.get('interaction_type') in ["click", "save", "share"]:
                # Obtener el evento para conocer su categoría
                await cursor.execute("SELECT category FROM events WHERE id = %s", (interaction['event_id'],))
                event_result = await cursor.fetchone()
                
                if event_result and event_result.get('category'):
                    category = event_result['category'].lower()
                    weight = {
                        "view": 1,
                        "click": 2,
                        "save": 3,
                        "share": 4
                    }.get(interaction['interaction_type'], 1)
                    
                    category_scores[category] = category_scores.get(category, 0) + weight
        
        # Normalizar scores (0-1)
        if category_scores:
            max_score = max(category_scores.values())
            for category in category_scores:
                category_scores[category] = min(category_scores[category] / max_score, 1.0)
        
        return category_scores

    async def _update_category_weights(self, old_weights: Dict, new_scores: Dict) -> Dict:
        """Actualiza pesos de categorías con aprendizaje gradual"""
        learning_rate = 0.2
        updated_weights = old_weights.copy()
        
        for category, new_score in new_scores.items():
            if category in updated_weights:
                current_weight = updated_weights[category]
                updated_weights[category] = round(
                    current_weight * (1 - learning_rate) + new_score * learning_rate, 2
                )
            else:
                updated_weights[category] = round(new_score * learning_rate + 0.5 * (1 - learning_rate), 2)
        
        return updated_weights

    async def _analyze_location_preferences(self, interactions: List[Dict]) -> List[str]:
        """Analiza ubicaciones más frecuentes en interacciones"""
        location_counts = {}
        
        for interaction in interactions:
            if interaction.get('context'):
                try:
                    context = json.loads(interaction['context']) if isinstance(interaction['context'], str) else interaction['context']
                    if context and "location" in context:
                        location = context["location"]
                        if location:
                            location_counts[location] = location_counts.get(location, 0) + 1
                except:
                    continue
        
        # Ordenar por frecuencia y tomar top 5
        sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
        return [location for location, count in sorted_locations[:5]]

    async def _update_neighborhood_preferences(self, old_prefs: List[str], new_locations: List[str]) -> List[str]:
        """Actualiza preferencias de ubicación"""
        # Combinar ubicaciones viejas y nuevas, priorizando las nuevas
        combined = list(set(new_locations + old_prefs))
        return combined[:10]  # Máximo 10

    async def _analyze_time_preferences(self, cursor, interactions: List[Dict]) -> Dict[str, float]:
        """Analiza horarios preferidos del usuario"""
        time_scores = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        
        for interaction in interactions:
            if interaction.get('event_id'):
                await cursor.execute("SELECT start_datetime FROM events WHERE id = %s", (interaction['event_id'],))
                event_result = await cursor.fetchone()
                
                if event_result and event_result.get('start_datetime'):
                    hour = event_result['start_datetime'].hour
                    
                    if 6 <= hour < 12:
                        time_scores["morning"] += 1
                    elif 12 <= hour < 18:
                        time_scores["afternoon"] += 1
                    elif 18 <= hour < 22:
                        time_scores["evening"] += 1
                    else:
                        time_scores["night"] += 1
        
        # Normalizar
        total_interactions = sum(time_scores.values())
        if total_interactions > 0:
            for time_period in time_scores:
                time_scores[time_period] = round(time_scores[time_period] / total_interactions, 2)
        
        return time_scores

    async def _update_time_preferences(self, old_prefs: Dict, new_scores: Dict) -> Dict:
        """Actualiza preferencias de horario con aprendizaje gradual"""
        learning_rate = 0.3
        updated_prefs = old_prefs.copy()
        
        for time_period, new_score in new_scores.items():
            if time_period in updated_prefs:
                current_score = updated_prefs[time_period]
                updated_prefs[time_period] = round(
                    current_score * (1 - learning_rate) + new_score * learning_rate, 2
                )
        
        return updated_prefs

    async def _log_preference_update(
        self, cursor, user_id: str, field: str, old_value: Any, new_value: Any, 
        reason: str, confidence: float = 0.7
    ):
        """Registra cambio en preferencias para auditoría"""
        try:
            await cursor.execute('''
                INSERT INTO preference_updates (
                    user_id, field_changed, old_value, new_value, 
                    update_reason, confidence_score
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                user_id, field, json.dumps(old_value), 
                json.dumps(new_value), reason, confidence
            ))
            
        except Exception as e:
            logger.error(f"Error logging preference update: {str(e)}")

    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene preferencias del usuario"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT * FROM user_preferences WHERE user_id = %s",
                        (user_id,)
                    )
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return None

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas del usuario para mostrar en el perfil"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Obtener preferencias
                    preferences = await self.get_user_preferences(user_id)
                    if not preferences:
                        preferences = await self.initialize_user_preferences(user_id)
                    
                    # Contar eventos guardados
                    await cursor.execute('''
                        SELECT COUNT(*) as saved_events FROM user_events 
                        WHERE user_id = %s AND status IN ('interested', 'going')
                    ''', (user_id,))
                    saved_result = await cursor.fetchone()
                    saved_events = saved_result.get('saved_events', 0) if saved_result else 0
                    
                    await cursor.execute('''
                        SELECT COUNT(*) as favorites FROM user_events 
                        WHERE user_id = %s AND status = 'going'
                    ''', (user_id,))
                    favorites_result = await cursor.fetchone()
                    favorites_count = favorites_result.get('favorites', 0) if favorites_result else 0
                    
                    # Calcular porcentaje de match basado en iteraciones de aprendizaje
                    learning_iterations = preferences.get('learning_iterations', 0)
                    feedback_score = float(preferences.get('feedback_score', 0.5))
                    
                    # El porcentaje mejora con más iteraciones y feedback positivo
                    base_percentage = 60  # Mínimo 60%
                    learning_boost = min(learning_iterations * 2, 30)  # Máximo 30% por aprendizaje
                    feedback_boost = int((feedback_score - 0.5) * 20)  # +/-10% por feedback
                    
                    match_percentage = min(base_percentage + learning_boost + feedback_boost, 99)
                    
                    return {
                        "match_percentage": max(match_percentage, 50),
                        "events_count": saved_events,
                        "favorites_count": favorites_count,
                        "learning_iterations": learning_iterations,
                        "categories_learned": len(json.loads(preferences.get('category_weights', '{}'))) if preferences.get('category_weights') else 0,
                        "locations_learned": len(json.loads(preferences.get('preferred_neighborhoods', '[]'))) if preferences.get('preferred_neighborhoods') else 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {"match_percentage": 50, "events_count": 0, "favorites_count": 0}