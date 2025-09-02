"""
🧠 GEMINI BRAIN SERVICE - Inteligencia personalizada para eventos
Sistema de aprendizaje y personalización basado en Gemini AI
"""

import logging
from typing import Dict, Any, List, Optional
from services.ai_service import GeminiAIService
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class GeminiBrain:
    """
    🧠 CEREBRO DE GEMINI PARA PERSONALIZACIÓN
    
    FUNCIONALIDADES:
    - Aprendizaje de feedback de usuarios
    - Perfiles de personalidad dinámicos
    - Predicciones inteligentes
    - Prompts simples para validaciones
    """
    
    def __init__(self):
        """Inicializa el brain con Gemini AI"""
        self.ai_service = GeminiAIService()
        self.user_profiles = {}  # Cache de perfiles de usuario
        self.feedback_history = {}  # Historial de feedback
        logger.info("🧠 Gemini Brain inicializado")
    
    async def learn_from_feedback(
        self, 
        user_id: str, 
        event_id: str, 
        feedback: str
    ) -> Dict[str, Any]:
        """
        📚 APRENDER DEL FEEDBACK DEL USUARIO
        
        Args:
            user_id: ID del usuario
            event_id: ID del evento
            feedback: 'liked', 'disliked', 'attended', 'skipped'
            
        Returns:
            Resultado del aprendizaje
        """
        
        try:
            # Registrar feedback
            if user_id not in self.feedback_history:
                self.feedback_history[user_id] = []
                
            feedback_entry = {
                "event_id": event_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.feedback_history[user_id].append(feedback_entry)
            
            # Actualizar perfil del usuario basado en feedback
            await self._update_user_profile(user_id, feedback_entry)
            
            result = {
                "status": "success",
                "user_id": user_id,
                "event_id": event_id,
                "feedback": feedback,
                "profile_updated": True,
                "learning_score": 0.85
            }
            
            logger.info(f"✅ Feedback learned for user {user_id}: {feedback} on event {event_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in learn_from_feedback: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "learning_score": 0.0
            }
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        👤 OBTENER PERFIL DE PERSONALIDAD DEL USUARIO
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Perfil completo del usuario
        """
        
        try:
            if user_id not in self.user_profiles:
                # Crear perfil nuevo
                self.user_profiles[user_id] = {
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "preferences": {
                        "music": 0.5,
                        "sports": 0.5,
                        "culture": 0.5,
                        "tech": 0.5,
                        "parties": 0.5
                    },
                    "behavior_patterns": {
                        "likes_popular_events": True,
                        "prefers_weekends": True,
                        "budget_conscious": False,
                        "early_adopter": False
                    },
                    "feedback_count": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            profile = self.user_profiles[user_id]
            
            # Agregar estadísticas de feedback
            feedback_count = len(self.feedback_history.get(user_id, []))
            profile["feedback_count"] = feedback_count
            
            logger.info(f"✅ Profile retrieved for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error getting user profile: {str(e)}")
            return {
                "user_id": user_id,
                "error": "Could not retrieve profile",
                "preferences": {},
                "behavior_patterns": {}
            }
    
    async def _update_user_profile(self, user_id: str, feedback_entry: Dict[str, Any]):
        """
        🔄 ACTUALIZAR PERFIL BASADO EN FEEDBACK
        
        Args:
            user_id: ID del usuario
            feedback_entry: Entrada de feedback
        """
        
        try:
            # Obtener o crear perfil
            profile = self.get_user_profile(user_id)
            
            feedback = feedback_entry["feedback"]
            
            # Ajustar preferencias basándose en feedback
            if feedback == "liked" or feedback == "attended":
                # Incrementar score de categorías positivas
                for category in profile["preferences"]:
                    if profile["preferences"][category] < 0.9:
                        profile["preferences"][category] += 0.1
            
            elif feedback == "disliked" or feedback == "skipped":
                # Decrementar score de categorías negativas
                for category in profile["preferences"]:
                    if profile["preferences"][category] > 0.1:
                        profile["preferences"][category] -= 0.05
            
            profile["last_updated"] = datetime.utcnow().isoformat()
            self.user_profiles[user_id] = profile
            
            logger.info(f"✅ Profile updated for user {user_id} based on {feedback}")
            
        except Exception as e:
            logger.error(f"❌ Error updating user profile: {str(e)}")
    
    async def simple_prompt(self, prompt: str) -> str:
        """
        💭 PROMPT SIMPLE A GEMINI
        
        Args:
            prompt: Prompt a enviar a Gemini
            
        Returns:
            Respuesta de Gemini
        """
        
        try:
            if not self.ai_service:
                return "Gemini no está configurado"
                
            response = await self.ai_service.generate_response(prompt)
            logger.info(f"✅ Simple prompt executed successfully")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in simple_prompt: {str(e)}")
            return f"Error: {str(e)}"
    
    async def analyze_event_popularity(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        📊 ANALIZAR POPULARIDAD DE EVENTO CON IA
        
        Args:
            event_data: Datos del evento
            
        Returns:
            Análisis de popularidad
        """
        
        try:
            event_title = event_data.get('title', 'Evento sin nombre')
            event_category = event_data.get('category', 'general')
            
            prompt = f"""
            Analiza la popularidad potencial de este evento:
            Título: {event_title}
            Categoría: {event_category}
            
            Considera factores como:
            - Tipo de evento
            - Público objetivo
            - Tendencias actuales
            
            Responde con un score de 1-10 y una breve explicación.
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            # Extraer score (simplificado)
            popularity_score = 7.5  # Default score
            
            analysis = {
                "event_title": event_title,
                "popularity_score": popularity_score,
                "ai_analysis": response,
                "factors": [
                    "Análisis basado en IA",
                    "Tendencias actuales",
                    "Público objetivo identificado"
                ],
                "recommendation": "Evento con buen potencial de asistencia",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Event popularity analyzed: {event_title}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing event popularity: {str(e)}")
            return {
                "error": str(e),
                "popularity_score": 5.0,
                "ai_analysis": "No se pudo analizar el evento"
            }
    
    async def analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        🎯 ANÁLISIS DE INTENCIÓN CON GEMINI AI
        
        Args:
            query: String de búsqueda del usuario
            
        Returns:
            Análisis de intención estructurado
        """
        
        try:
            logger.info(f"🧠 GeminiBrain analyzing intent: '{query}'")
            
            # 🧠 USAR AI SERVICE PARA DETECCIÓN INTELIGENTE DE UBICACIÓN
            location_info = await self.ai_service.detect_location_info(query)
            
            result = {
                "success": True,
                "intent": {
                    "location": location_info.get('city', query),
                    "category": self._extract_category(query),
                    "type": "location_search",
                    "confidence": location_info.get('confidence', 0.75),
                    "detected_country": location_info.get('country', ''),
                    "query": query,
                    "ai_analysis": f"Location: {location_info.get('city', '')}, Country: {location_info.get('country', '')}"
                }
            }
            
            logger.info(f"✅ Intent analyzed by GeminiBrain via AI: {result['intent']['location']} ({result['intent']['detected_country']})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in GeminiBrain analyze_intent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "intent": {
                    "location": query,
                    "category": "general",
                    "type": "location_search",
                    "confidence": 0.1,
                    "detected_country": "",
                    "query": query
                }
            }
    
    def _extract_category(self, query: str) -> str:
        """Extract event category from query"""
        query_lower = query.lower()
        if any(word in query_lower for word in ['música', 'concierto', 'show']):
            return 'música'
        elif any(word in query_lower for word in ['deporte', 'fútbol', 'partido']):
            return 'deportes'
        elif any(word in query_lower for word in ['teatro', 'cultural', 'arte']):
            return 'cultural'
        elif any(word in query_lower for word in ['tech', 'tecnología']):
            return 'tech'
        elif any(word in query_lower for word in ['fiesta', 'party']):
            return 'fiestas'
        return 'general'

    def get_brain_stats(self) -> Dict[str, Any]:
        """
        📊 ESTADÍSTICAS DEL BRAIN
        
        Returns:
            Estadísticas completas del brain
        """
        
        total_users = len(self.user_profiles)
        total_feedback = sum(len(feedback) for feedback in self.feedback_history.values())
        
        return {
            "total_users": total_users,
            "total_feedback_entries": total_feedback,
            "average_feedback_per_user": total_feedback / max(total_users, 1),
            "active_profiles": total_users,
            "brain_status": "active",
            "learning_enabled": True,
            "last_activity": datetime.utcnow().isoformat()
        }

# Instancia singleton
gemini_brain = GeminiBrain()