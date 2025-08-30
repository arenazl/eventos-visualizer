"""
Motor de Preferencias de Usuario con Machine Learning
Aprende de las interacciones del usuario para mejorar las recomendaciones
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import math
from sqlalchemy.orm import Session
from models.users import User
from models.preferences import UserPreferences, UserInteraction, PreferenceUpdate
from models.events import Event
import logging

logger = logging.getLogger(__name__)

class PreferencesEngine:
    """Motor que aprende y actualiza preferencias del usuario automáticamente"""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def initialize_user_preferences(self, user_id: str) -> UserPreferences:
        """Inicializa preferencias para un nuevo usuario"""
        try:
            # Verificar si ya existen preferencias
            existing = self.db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            if existing:
                return existing
            
            # Crear preferencias iniciales
            preferences = UserPreferences(
                user_id=user_id,
                category_weights={
                    "musica": 0.5,
                    "deportes": 0.5, 
                    "cultural": 0.5,
                    "tech": 0.5,
                    "fiestas": 0.5,
                    "hobbies": 0.5,
                    "internacional": 0.5
                },
                preferred_neighborhoods=[],
                location_flexibility=0.7,
                preferred_times={
                    "morning": 0.3,
                    "afternoon": 0.5,
                    "evening": 0.8,
                    "night": 0.4
                },
                price_sensitivity=0.6,
                prefers_free_events=True,
                group_size_preference="any",
                social_events_weight=0.5,
                interaction_history={
                    "viewed_events": [],
                    "clicked_events": [],
                    "saved_events": [],
                    "shared_events": [],
                    "searched_terms": [],
                    "rejected_suggestions": []
                },
                match_score_history=[],
                feedback_score=0.5,
                communication_style="friendly",
                prefers_suggestions=True,
                max_suggestions_per_query=3
            )
            
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"✅ Preferencias inicializadas para usuario {user_id}")
            return preferences
            
        except Exception as e:
            logger.error(f"❌ Error inicializando preferencias: {str(e)}")
            self.db.rollback()
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
            interaction = UserInteraction(
                user_id=user_id,
                event_id=event_id,
                interaction_type=interaction_type,
                context=context or {},
                ai_query=ai_query,
                ai_response=ai_response,
                duration_seconds=duration_seconds,
                success_indicator=success
            )
            
            self.db.add(interaction)
            
            # Actualizar historial en preferencias
            preferences = await self.get_user_preferences(user_id)
            if preferences:
                history = preferences.interaction_history or {}
                
                # Agregar a la lista correspondiente (máximo 100 elementos)
                if interaction_type == "view" and event_id:
                    viewed = history.get("viewed_events", [])
                    viewed.append({"event_id": event_id, "timestamp": datetime.utcnow().isoformat()})
                    history["viewed_events"] = viewed[-100:]  # Mantener solo los últimos 100
                
                elif interaction_type == "click" and event_id:
                    clicked = history.get("clicked_events", [])
                    clicked.append({"event_id": event_id, "timestamp": datetime.utcnow().isoformat()})
                    history["clicked_events"] = clicked[-100:]
                
                elif interaction_type == "save" and event_id:
                    saved = history.get("saved_events", [])
                    saved.append({"event_id": event_id, "timestamp": datetime.utcnow().isoformat()})
                    history["saved_events"] = saved[-100:]
                
                elif interaction_type == "search" and ai_query:
                    searches = history.get("searched_terms", [])
                    searches.append({"query": ai_query, "timestamp": datetime.utcnow().isoformat()})
                    history["searched_terms"] = searches[-50:]  # Últimas 50 búsquedas
                
                preferences.interaction_history = history
                preferences.last_interaction = datetime.utcnow()
                
            self.db.commit()
            logger.info(f"📝 Interacción registrada: {interaction_type} para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error registrando interacción: {str(e)}")
            self.db.rollback()

    async def learn_from_interactions(self, user_id: str) -> None:
        """Analiza interacciones recientes y actualiza preferencias"""
        try:
            preferences = await self.get_user_preferences(user_id)
            if not preferences:
                preferences = await self.initialize_user_preferences(user_id)
            
            # Obtener interacciones de los últimos 30 días
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_interactions = self.db.query(UserInteraction).filter(
                UserInteraction.user_id == user_id,
                UserInteraction.created_at >= thirty_days_ago
            ).order_by(UserInteraction.created_at.desc()).all()
            
            if not recent_interactions:
                logger.info(f"No hay interacciones recientes para usuario {user_id}")
                return
            
            # Analizar categorías más interactuadas
            category_scores = await self._analyze_category_preferences(recent_interactions)
            if category_scores:
                old_weights = preferences.category_weights or {}
                new_weights = await self._update_category_weights(old_weights, category_scores)
                
                if new_weights != old_weights:
                    self._log_preference_update(
                        user_id, "category_weights", old_weights, new_weights, "ai_learning"
                    )
                    preferences.category_weights = new_weights
            
            # Analizar preferencias de ubicación
            location_prefs = await self._analyze_location_preferences(recent_interactions)
            if location_prefs:
                old_neighborhoods = preferences.preferred_neighborhoods or []
                new_neighborhoods = await self._update_neighborhood_preferences(
                    old_neighborhoods, location_prefs
                )
                
                if new_neighborhoods != old_neighborhoods:
                    self._log_preference_update(
                        user_id, "preferred_neighborhoods", old_neighborhoods, 
                        new_neighborhoods, "ai_learning"
                    )
                    preferences.preferred_neighborhoods = new_neighborhoods
            
            # Analizar horarios preferidos
            time_prefs = await self._analyze_time_preferences(recent_interactions)
            if time_prefs:
                old_times = preferences.preferred_times or {}
                new_times = await self._update_time_preferences(old_times, time_prefs)
                
                if new_times != old_times:
                    self._log_preference_update(
                        user_id, "preferred_times", old_times, new_times, "ai_learning"
                    )
                    preferences.preferred_times = new_times
            
            # Incrementar contador de iteraciones de aprendizaje
            preferences.learning_iterations = (preferences.learning_iterations or 0) + 1
            preferences.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"🧠 Preferencias actualizadas para usuario {user_id} (iteración {preferences.learning_iterations})")
            
        except Exception as e:
            logger.error(f"❌ Error en aprendizaje de preferencias: {str(e)}")
            self.db.rollback()

    async def _analyze_category_preferences(self, interactions: List[UserInteraction]) -> Dict[str, float]:
        """Analiza qué categorías prefiere más el usuario basado en interacciones"""
        category_scores = {}
        
        for interaction in interactions:
            if interaction.event_id and interaction.interaction_type in ["click", "save", "share"]:
                event = self.db.query(Event).filter(Event.id == interaction.event_id).first()
                if event and event.category:
                    category = event.category.lower()
                    weight = {
                        "view": 1,
                        "click": 2,
                        "save": 3,
                        "share": 4
                    }.get(interaction.interaction_type, 1)
                    
                    category_scores[category] = category_scores.get(category, 0) + weight
        
        # Normalizar scores (0-1)
        if category_scores:
            max_score = max(category_scores.values())
            for category in category_scores:
                category_scores[category] = min(category_scores[category] / max_score, 1.0)
        
        return category_scores

    async def _update_category_weights(self, old_weights: Dict, new_scores: Dict) -> Dict:
        """Actualiza pesos de categorías con aprendizaje gradual"""
        learning_rate = 0.2  # Qué tan rápido aprende (0-1)
        updated_weights = old_weights.copy()
        
        for category, new_score in new_scores.items():
            if category in updated_weights:
                # Promedio ponderado entre peso actual y nueva evidencia
                current_weight = updated_weights[category]
                updated_weights[category] = round(
                    current_weight * (1 - learning_rate) + new_score * learning_rate, 2
                )
            else:
                # Nueva categoría
                updated_weights[category] = round(new_score * learning_rate + 0.5 * (1 - learning_rate), 2)
        
        return updated_weights

    async def _analyze_location_preferences(self, interactions: List[UserInteraction]) -> List[str]:
        """Analiza ubicaciones más frecuentes en interacciones"""
        location_counts = {}
        
        for interaction in interactions:
            if interaction.context and "location" in interaction.context:
                location = interaction.context["location"]
                if location:
                    location_counts[location] = location_counts.get(location, 0) + 1
        
        # Ordenar por frecuencia y tomar top 5
        sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
        return [location for location, count in sorted_locations[:5]]

    async def _update_neighborhood_preferences(self, old_prefs: List[str], new_locations: List[str]) -> List[str]:
        """Actualiza preferencias de ubicación"""
        # Combinar ubicaciones viejas y nuevas, priorizando las nuevas
        combined = list(set(new_locations + old_prefs))
        
        # Mantener máximo 10 ubicaciones preferidas
        return combined[:10]

    async def _analyze_time_preferences(self, interactions: List[UserInteraction]) -> Dict[str, float]:
        """Analiza horarios preferidos del usuario"""
        time_scores = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        
        for interaction in interactions:
            if interaction.event_id:
                event = self.db.query(Event).filter(Event.id == interaction.event_id).first()
                if event and event.start_datetime:
                    hour = event.start_datetime.hour
                    
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

    def _log_preference_update(
        self, user_id: str, field: str, old_value: Any, new_value: Any, 
        reason: str, confidence: float = 0.7
    ):
        """Registra cambio en preferencias para auditoría"""
        try:
            update_log = PreferenceUpdate(
                user_id=user_id,
                field_changed=field,
                old_value=old_value,
                new_value=new_value,
                update_reason=reason,
                confidence_score=confidence
            )
            self.db.add(update_log)
            
        except Exception as e:
            logger.error(f"Error logging preference update: {str(e)}")

    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Obtiene preferencias del usuario"""
        return self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()

    async def calculate_match_score(self, user_id: str, event: Event) -> float:
        """Calcula score de match entre usuario y evento (0-1)"""
        preferences = await self.get_user_preferences(user_id)
        if not preferences:
            return 0.5  # Score neutro sin preferencias
        
        score = 0.0
        weight_total = 0.0
        
        # Score por categoría (peso 40%)
        if event.category and preferences.category_weights:
            category_weight = preferences.category_weights.get(event.category.lower(), 0.5)
            score += category_weight * 0.4
            weight_total += 0.4
        
        # Score por horario (peso 20%)
        if event.start_datetime and preferences.preferred_times:
            hour = event.start_datetime.hour
            time_period = self._get_time_period(hour)
            time_score = preferences.preferred_times.get(time_period, 0.5)
            score += time_score * 0.2
            weight_total += 0.2
        
        # Score por precio (peso 15%)
        if preferences.price_sensitivity:
            price_score = self._calculate_price_score(event, preferences)
            score += price_score * 0.15
            weight_total += 0.15
        
        # Score por ubicación (peso 25%)
        if preferences.preferred_neighborhoods and event.venue_address:
            location_score = self._calculate_location_score(event, preferences)
            score += location_score * 0.25
            weight_total += 0.25
        
        # Normalizar score
        final_score = score / weight_total if weight_total > 0 else 0.5
        return min(max(final_score, 0.0), 1.0)

    def _get_time_period(self, hour: int) -> str:
        """Convierte hora a período del día"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _calculate_price_score(self, event: Event, preferences: UserPreferences) -> float:
        """Calcula score basado en precio del evento"""
        if event.is_free and preferences.prefers_free_events:
            return 1.0
        
        if event.price is None:
            return 0.7  # Precio desconocido
        
        price_sensitivity = preferences.price_sensitivity or 0.5
        max_price = preferences.max_preferred_price or 10000
        
        if float(event.price) <= float(max_price):
            # Precio aceptable, score basado en sensibilidad
            price_ratio = float(event.price) / float(max_price)
            return 1.0 - (price_ratio * price_sensitivity)
        else:
            # Precio alto, penalizar según sensibilidad
            return 1.0 - price_sensitivity
    
    def _calculate_location_score(self, event: Event, preferences: UserPreferences) -> float:
        """Calcula score basado en ubicación del evento"""
        if not event.venue_address or not preferences.preferred_neighborhoods:
            return 0.5
        
        venue_address = event.venue_address.lower()
        
        # Buscar si algún barrio preferido está en la dirección
        for neighborhood in preferences.preferred_neighborhoods:
            if neighborhood.lower() in venue_address:
                return 0.9
        
        # Si no coincide exactamente, usar flexibilidad de ubicación
        return preferences.location_flexibility or 0.5

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas del usuario para mostrar en el perfil"""
        try:
            preferences = await self.get_user_preferences(user_id)
            if not preferences:
                return {"match_percentage": 50, "events_count": 0, "favorites_count": 0}
            
            # Contar eventos guardados
            from models.users import UserEvent
            saved_events = self.db.query(UserEvent).filter(
                UserEvent.user_id == user_id,
                UserEvent.status.in_(["interested", "going"])
            ).count()
            
            favorites_count = self.db.query(UserEvent).filter(
                UserEvent.user_id == user_id,
                UserEvent.status == "going"
            ).count()
            
            # Calcular porcentaje de match basado en iteraciones de aprendizaje
            learning_iterations = preferences.learning_iterations or 0
            feedback_score = preferences.feedback_score or 0.5
            
            # El porcentaje mejora con más iteraciones y feedback positivo
            base_percentage = 60  # Mínimo 60%
            learning_boost = min(learning_iterations * 2, 30)  # Máximo 30% por aprendizaje
            feedback_boost = int((feedback_score - 0.5) * 20)  # +/-10% por feedback
            
            match_percentage = min(base_percentage + learning_boost + feedback_boost, 99)
            
            return {
                "match_percentage": max(match_percentage, 50),  # Mínimo 50%
                "events_count": saved_events,
                "favorites_count": favorites_count,
                "learning_iterations": learning_iterations,
                "categories_learned": len(preferences.category_weights or {}),
                "locations_learned": len(preferences.preferred_neighborhoods or [])
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {"match_percentage": 50, "events_count": 0, "favorites_count": 0}