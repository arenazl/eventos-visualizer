"""
🧠 GEMINI BRAIN - El cerebro IA-First del sistema
Sistema de recomendación inteligente para gente indecisa
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
from dataclasses import dataclass, asdict
import hashlib

# Configurar Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

@dataclass
class UserContext:
    """Contexto del usuario que se va construyendo con el tiempo"""
    user_id: str
    conversation_history: List[str] = None
    preferences: Dict[str, Any] = None
    past_events: List[str] = None
    rejected_suggestions: List[str] = None
    personality_profile: str = ""
    decision_style: str = "indeciso"  # indeciso, aventurero, conservador, social
    budget_range: str = "medio"
    energy_level: str = "medio"
    
    def __post_init__(self):
        self.conversation_history = self.conversation_history or []
        self.preferences = self.preferences or {}
        self.past_events = self.past_events or []
        self.rejected_suggestions = self.rejected_suggestions or []

class GeminiBrain:
    """
    El cerebro central con Gemini que:
    1. Entiende conversación natural
    2. Aprende preferencias implícitas
    3. Recomienda para indecisos
    4. Mejora con cada interacción
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            
        # Storage de contextos de usuario (en producción sería Redis/DB)
        self.user_contexts: Dict[str, UserContext] = {}
        
        # Prompt base para el sistema
        self.system_prompt = """
        Sos un asistente experto en recomendar actividades y eventos en Buenos Aires.
        Tu especialidad es ayudar a gente INDECISA que no sabe qué hacer.
        
        PERSONALIDAD:
        - Súper amigable y entusiasta 
        - Hablás como un amigo argentino copado
        - Usás emojis para dar energía
        - Das opciones concretas, no vagas
        
        ESTRATEGIA PARA INDECISOS:
        1. Si detectás indecisión → Das máximo 3 opciones SUPER claras
        2. Explicás por qué cada opción es genial
        3. Si siguen indecisos → Elegís UNA y la vendés con pasión
        4. Siempre das un "plan B" por las dudas
        
        INFORMACIÓN QUE EXTRAÉS:
        - Mood actual (energético, relajado, social, introspectivo)
        - Presupuesto (sin decirlo directamente)
        - Con quién va (solo, pareja, amigos, familia)
        - Preferencias ocultas (las inferís de cómo hablan)
        - Nivel de aventura (conservador vs experimental)
        
        FORMATO DE RESPUESTA:
        {
            "mensaje": "Tu respuesta conversacional aquí",
            "recomendaciones": [
                {
                    "titulo": "Nombre del evento/actividad",
                    "porque_te_va_a_encantar": "Razón personalizada",
                    "vibe": "energético/relajado/romántico/etc",
                    "precio_estimado": "$$",
                    "match_score": 0.95
                }
            ],
            "preferencias_detectadas": {
                "mood": "detectado",
                "presupuesto": "bajo/medio/alto",
                "tipo_persona": "social/introspectivo/aventurero",
                "intereses": ["música", "arte", "etc"]
            },
            "pregunta_follow_up": "¿Pregunta para conocerlos mejor?"
        }
        """
    
    async def process_indecisive_user(self, 
                                      user_message: str, 
                                      user_id: str,
                                      available_events: List[Dict] = None) -> Dict[str, Any]:
        """
        Procesa mensaje de usuario indeciso y devuelve recomendaciones ultra personalizadas
        """
        
        # Obtener o crear contexto del usuario
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(user_id=user_id)
        
        context = self.user_contexts[user_id]
        
        # Si no tenemos Gemini configurado, usar lógica fallback inteligente
        if not self.model:
            return await self._fallback_recommendations(user_message, context, available_events)
        
        try:
            # Construir prompt con contexto completo
            prompt = self._build_contextual_prompt(user_message, context, available_events)
            
            # Llamar a Gemini
            response = self.model.generate_content(prompt)
            
            # Parsear respuesta
            result = self._parse_gemini_response(response.text)
            
            # Actualizar contexto del usuario con lo aprendido
            self._update_user_context(context, user_message, result)
            
            return result
            
        except Exception as e:
            print(f"Error con Gemini: {e}")
            return await self._fallback_recommendations(user_message, context, available_events)
    
    def _build_contextual_prompt(self, 
                                 message: str, 
                                 context: UserContext,
                                 events: List[Dict]) -> str:
        """
        Construye un prompt rico en contexto
        """
        
        prompt = f"{self.system_prompt}\n\n"
        
        # Agregar historial de conversación
        if context.conversation_history:
            prompt += "HISTORIAL DE CONVERSACIÓN:\n"
            for msg in context.conversation_history[-5:]:  # Últimos 5 mensajes
                prompt += f"- {msg}\n"
            prompt += "\n"
        
        # Agregar preferencias conocidas
        if context.preferences:
            prompt += f"PREFERENCIAS CONOCIDAS:\n{json.dumps(context.preferences, indent=2)}\n\n"
        
        # Agregar eventos disponibles
        if events:
            prompt += "EVENTOS DISPONIBLES HOY:\n"
            for event in events[:10]:  # Top 10 eventos
                prompt += f"- {event.get('title')}: {event.get('description')[:100]}\n"
            prompt += "\n"
        
        # Agregar mensaje actual
        prompt += f"MENSAJE DEL USUARIO:\n{message}\n\n"
        prompt += "RESPONDE EN FORMATO JSON EXACTO como se especificó arriba."
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta de Gemini a nuestro formato
        """
        try:
            # Intentar parsear JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            else:
                json_str = response_text
            
            return json.loads(json_str)
        except:
            # Si falla, crear respuesta estructurada desde texto
            return {
                "mensaje": response_text,
                "recomendaciones": [],
                "preferencias_detectadas": {},
                "pregunta_follow_up": "¿Qué tipo de actividad preferís?"
            }
    
    def _update_user_context(self, 
                            context: UserContext, 
                            message: str,
                            gemini_result: Dict):
        """
        Actualiza el contexto del usuario con lo aprendido
        """
        
        # Agregar a historial
        context.conversation_history.append(message)
        
        # Actualizar preferencias
        if "preferencias_detectadas" in gemini_result:
            for key, value in gemini_result["preferencias_detectadas"].items():
                context.preferences[key] = value
        
        # Actualizar perfil de personalidad
        if "tipo_persona" in gemini_result.get("preferencias_detectadas", {}):
            context.personality_profile = gemini_result["preferencias_detectadas"]["tipo_persona"]
    
    async def _fallback_recommendations(self, 
                                       message: str, 
                                       context: UserContext,
                                       events: List[Dict]) -> Dict[str, Any]:
        """
        Sistema de recomendación fallback cuando Gemini no está disponible
        """
        
        message_lower = message.lower()
        
        # Detectar mood e intención
        mood = self._detect_mood(message_lower)
        is_indecisive = self._detect_indecision(message_lower)
        
        # Respuestas para indecisos
        if is_indecisive:
            return {
                "mensaje": "🎯 ¡Perfecto! Te voy a hacer súper fácil la decisión. Te doy 3 opciones GENIALES y diferentes:",
                "recomendaciones": [
                    {
                        "titulo": "🎉 Fiesta Rooftop en Palermo",
                        "porque_te_va_a_encantar": "Música increíble, vista de la ciudad, gente copada. Imposible aburrirse.",
                        "vibe": "energético",
                        "precio_estimado": "$$$",
                        "match_score": 0.92
                    },
                    {
                        "titulo": "🍷 Noche de Jazz y Vinos",
                        "porque_te_va_a_encantar": "Relajado pero interesante. Perfecto para charlar y conocer gente nueva.",
                        "vibe": "relajado",
                        "precio_estimado": "$$",
                        "match_score": 0.88
                    },
                    {
                        "titulo": "🎮 Arcade Bar Retro",
                        "porque_te_va_a_encantar": "Nostalgia, competencia amistosa, tragos temáticos. Diferente y divertido.",
                        "vibe": "casual",
                        "precio_estimado": "$$",
                        "match_score": 0.85
                    }
                ],
                "preferencias_detectadas": {
                    "mood": mood,
                    "decision_style": "indeciso",
                    "busca": "opciones_variadas"
                },
                "pregunta_follow_up": "¿Cuál te llamó más la atención? ¿O querés que elija yo por vos? 😊"
            }
        
        # Respuesta para decisivos
        return {
            "mensaje": f"💫 ¡Genial! Detecté que estás con mood {mood}. Te tengo LA actividad perfecta:",
            "recomendaciones": self._get_mood_based_recommendations(mood, events),
            "preferencias_detectadas": {
                "mood": mood,
                "decision_style": "decisivo"
            },
            "pregunta_follow_up": "¿Te copa? ¿O preferís algo más tranqui/movido?"
        }
    
    def _detect_mood(self, message: str) -> str:
        """
        Detecta el mood del usuario desde el mensaje
        """
        moods = {
            "energético": ["fiesta", "bailar", "salir", "joda", "boliche"],
            "relajado": ["tranqui", "relax", "descansar", "chill"],
            "romántico": ["cita", "pareja", "romántico", "amor"],
            "cultural": ["museo", "teatro", "arte", "cultura"],
            "social": ["amigos", "grupo", "gente", "conocer"],
            "aventurero": ["nuevo", "diferente", "probar", "aventura"]
        }
        
        for mood, keywords in moods.items():
            if any(kw in message for kw in keywords):
                return mood
        
        return "exploratorio"
    
    def _detect_indecision(self, message: str) -> bool:
        """
        Detecta si el usuario está indeciso
        """
        indecision_phrases = [
            "no sé", "no se", "qué hago", "que hago", "estoy aburrido",
            "indeciso", "ayuda", "decidir", "opciones", "sugerime",
            "recomenda", "alguna idea", "ni idea", "whatever",
            "lo que sea", "cualquier cosa", "algo", "nose"
        ]
        
        return any(phrase in message for phrase in indecision_phrases)
    
    def _get_mood_based_recommendations(self, mood: str, events: List[Dict]) -> List[Dict]:
        """
        Obtiene recomendaciones basadas en mood
        """
        mood_recommendations = {
            "energético": [
                {
                    "titulo": "Festival Electrónico Open Air",
                    "porque_te_va_a_encantar": "La energía está al máximo, DJs internacionales, producción increíble",
                    "vibe": "épico",
                    "precio_estimado": "$$$",
                    "match_score": 0.95
                }
            ],
            "relajado": [
                {
                    "titulo": "Sunset Yoga en Costanera",
                    "porque_te_va_a_encantar": "Conectás con vos mismo, vista al río, paz total",
                    "vibe": "zen",
                    "precio_estimado": "$",
                    "match_score": 0.90
                }
            ],
            "romántico": [
                {
                    "titulo": "Cena con Show de Tango",
                    "porque_te_va_a_encantar": "Súper íntimo, comida increíble, ambiente mágico",
                    "vibe": "romántico",
                    "precio_estimado": "$$$$",
                    "match_score": 0.93
                }
            ]
        }
        
        return mood_recommendations.get(mood, [
            {
                "titulo": "Festival Gastronómico en Palermo",
                "porque_te_va_a_encantar": "Variedad total, podés probar de todo, ambiente relajado",
                "vibe": "foodie",
                "precio_estimado": "$$",
                "match_score": 0.87
            }
        ])
    
    async def learn_from_feedback(self, user_id: str, event_id: str, feedback: str):
        """
        Aprende de la retroalimentación del usuario
        """
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(user_id=user_id)
        
        context = self.user_contexts[user_id]
        
        if feedback == "liked":
            context.past_events.append(event_id)
        elif feedback == "disliked":
            context.rejected_suggestions.append(event_id)
        
        # Ajustar preferencias basándose en feedback
        # Aquí podrías usar ML más sofisticado
        
        return {"status": "learned", "user_id": user_id}
    
    async def simple_prompt(self, prompt: str) -> str:
        """
        Método simple para hacer consultas directas a Gemini
        """
        if not self.model:
            print("🔥 GEMINI NO CONFIGURADO")
            return "Gemini no está configurado"
        
        try:
            print(f"🚀 ENVIANDO PROMPT A GEMINI: {prompt[:100]}...")
            response = self.model.generate_content(prompt)
            print(f"🎯 GEMINI RESPONSE RAW: {response.text}")
            return response.text
        except Exception as e:
            print(f"Error con Gemini simple prompt: {e}")
            return f"Error: {str(e)}"
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene el perfil completo del usuario
        """
        if user_id not in self.user_contexts:
            return {"status": "new_user"}
        
        context = self.user_contexts[user_id]
        return {
            "user_id": user_id,
            "personality": context.personality_profile,
            "preferences": context.preferences,
            "decision_style": context.decision_style,
            "interaction_count": len(context.conversation_history),
            "liked_events": len(context.past_events),
            "rejected_suggestions": len(context.rejected_suggestions)
        }

# Instancia global del cerebro
gemini_brain = GeminiBrain()