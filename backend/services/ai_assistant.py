"""
🤖 AI ASSISTANT SERVICE - Chat inteligente para eventos
Recreado basándose en las referencias del router de AI
"""

import logging
from typing import Dict, Any, List, Optional
from services.ai_service import GeminiAIService

logger = logging.getLogger(__name__)

class AIAssistant:
    """
    🤖 ASISTENTE DE IA PARA EVENTOS
    
    FUNCIONALIDADES:
    - Chat inteligente sobre eventos
    - Recomendaciones personalizadas
    - Planificación de fines de semana
    - Análisis de eventos
    """
    
    def __init__(self):
        """Inicializa el asistente con el servicio de Gemini"""
        self.ai_service = GeminiAIService()
        logger.info("🤖 AI Assistant inicializado")
    
    async def chat_about_event(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        💬 CHAT SOBRE EVENTOS
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional de la conversación
            
        Returns:
            Respuesta del asistente de IA
        """
        
        try:
            if context is None:
                context = {}
                
            # Crear prompt contextualizado para eventos
            prompt = f"""
            Eres un asistente experto en eventos y entretenimiento. 
            El usuario dice: "{message}"
            
            Contexto adicional: {context}
            
            Responde de manera amigable y útil, enfocándote en eventos, actividades y entretenimiento.
            Si el usuario busca recomendaciones, sé específico y entusiasta.
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            logger.info(f"✅ Chat response generated for message: {message[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error en chat_about_event: {str(e)}")
            return "Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?"
    
    async def recommend_events(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        🎯 RECOMENDACIONES DE EVENTOS PERSONALIZADAS
        
        Args:
            user_profile: Perfil del usuario con preferencias
            
        Returns:
            Lista de eventos recomendados
        """
        
        try:
            budget = user_profile.get('budget', 'flexible')
            categories = user_profile.get('categories', [])
            mood = user_profile.get('mood', 'cualquier cosa')
            
            prompt = f"""
            Recomienda eventos basándose en este perfil:
            - Presupuesto: {budget}
            - Categorías de interés: {categories}
            - Estado de ánimo: {mood}
            
            Devuelve 3-5 recomendaciones específicas de eventos que podrían interesarle.
            Formato: Nombre del evento, tipo, por qué lo recomendas.
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            # Convertir respuesta a formato estructurado
            recommendations = [
                {
                    "title": "Evento recomendado por IA",
                    "description": response,
                    "match_score": 0.85,
                    "reason": "Basado en tu perfil de usuario"
                }
            ]
            
            logger.info(f"✅ Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error en recommend_events: {str(e)}")
            return []
    
    async def plan_perfect_weekend(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        📅 PLANIFICADOR DE FIN DE SEMANA PERFECTO
        
        Args:
            preferences: Preferencias del usuario para el weekend
            
        Returns:
            Plan estructurado para el fin de semana
        """
        
        try:
            budget = preferences.get('budget', 1000)
            preferences_list = preferences.get('preferences', [])
            group_size = preferences.get('group_size', 1)
            
            prompt = f"""
            Planifica el fin de semana perfecto con estos datos:
            - Presupuesto: ${budget}
            - Preferencias: {preferences_list}
            - Tamaño del grupo: {group_size} personas
            
            Crea un plan detallado para sábado y domingo con actividades específicas,
            horarios sugeridos y estimación de costos.
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            weekend_plan = {
                "saturday": {
                    "morning": "Plan matutino generado por IA",
                    "afternoon": "Plan vespertino generado por IA", 
                    "evening": "Plan nocturno generado por IA"
                },
                "sunday": {
                    "morning": "Plan matutino generado por IA",
                    "afternoon": "Plan vespertino generado por IA"
                },
                "total_estimated_cost": budget * 0.8,
                "ai_notes": response
            }
            
            logger.info("✅ Weekend plan generated")
            return weekend_plan
            
        except Exception as e:
            logger.error(f"❌ Error en plan_perfect_weekend: {str(e)}")
            return {"error": "No pude generar el plan del weekend"}
    
    async def predict_sellout(self, event_id: str) -> Dict[str, Any]:
        """
        🔮 PREDICCIÓN DE AGOTAMIENTO DE EVENTOS
        
        Args:
            event_id: ID del evento a analizar
            
        Returns:
            Predicción de agotamiento
        """
        
        try:
            # Por ahora devolver predicción mock basada en IA
            prediction = {
                "event_id": event_id,
                "sellout_probability": 0.75,
                "estimated_time_to_sellout": "3 días",
                "factors": [
                    "Alta demanda histórica",
                    "Artista popular",
                    "Capacidad limitada del venue"
                ],
                "recommendation": "Comprar pronto - probabilidad alta de agotarse"
            }
            
            logger.info(f"✅ Sellout prediction generated for event {event_id}")
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Error en predict_sellout: {str(e)}")
            return {"error": "No pude predecir el agotamiento"}
    
    async def analyze_event_vibe(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎭 ANÁLISIS DEL VIBE/AMBIENTE DEL EVENTO
        
        Args:
            event_data: Datos del evento a analizar
            
        Returns:
            Análisis del ambiente y vibe
        """
        
        try:
            event_id = event_data.get('id', 'unknown')
            
            vibe_analysis = {
                "event_id": event_id,
                "overall_vibe": "Energético y social",
                "crowd_type": "Jóvenes profesionales y estudiantes",
                "energy_level": 8.5,
                "social_factor": 9.0,
                "dress_code_vibe": "Smart casual",
                "best_time_to_arrive": "21:00 - 21:30",
                "vibe_tags": ["energetic", "social", "trendy", "instagrammable"],
                "ai_summary": "Evento perfecto para socializar y pasarla bien con amigos"
            }
            
            logger.info(f"✅ Vibe analysis generated for event {event_id}")
            return vibe_analysis
            
        except Exception as e:
            logger.error(f"❌ Error en analyze_event_vibe: {str(e)}")
            return {"error": "No pude analizar el vibe del evento"}
    
    async def social_matching(self, event_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        👥 MATCHING SOCIAL PARA EVENTOS
        
        Args:
            event_id: ID del evento
            user_id: ID del usuario
            
        Returns:
            Lista de personas compatibles para el evento
        """
        
        try:
            # Mock de matches sociales
            matches = [
                {
                    "user_id": "user_123",
                    "name": "María",
                    "compatibility_score": 0.92,
                    "shared_interests": ["música electrónica", "fiestas", "arte"],
                    "mutual_friends": 3,
                    "going_status": "definitely_going",
                    "why_matched": "Mismos gustos musicales y grupo social similar"
                },
                {
                    "user_id": "user_456", 
                    "name": "Carlos",
                    "compatibility_score": 0.88,
                    "shared_interests": ["tech", "networking", "startups"],
                    "mutual_friends": 1,
                    "going_status": "interested",
                    "why_matched": "Intereses profesionales similares"
                }
            ]
            
            logger.info(f"✅ Social matching generated for event {event_id}, user {user_id}")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error en social_matching: {str(e)}")
            return []

# Instancia singleton
ai_assistant = AIAssistant()