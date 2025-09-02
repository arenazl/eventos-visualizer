"""
🧠 CHAT MEMORY MANAGER - Gestión inteligente de memoria de conversaciones
Sistema de memoria optimizado para contexto de eventos en tiempo real
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from services.ai_service import GeminiAIService

logger = logging.getLogger(__name__)

class ChatMemoryManager:
    """
    🧠 GESTOR DE MEMORIA DE CHAT
    
    FUNCIONALIDADES:
    - Cache en memoria de conversaciones
    - Contexto persistente por usuario
    - Threading para respuestas rápidas
    - Estadísticas de rendimiento
    """
    
    def __init__(self):
        """Inicializa el gestor de memoria"""
        self.ai_service = GeminiAIService()
        self.user_conversations = {}  # Cache de conversaciones por usuario
        self.memory_stats = {
            "total_conversations": 0,
            "active_users": 0,
            "average_response_time": 0.0,
            "cache_hits": 0,
            "initialized_at": datetime.utcnow().isoformat()
        }
        logger.info("🧠 Chat Memory Manager inicializado")
    
    async def initialize_memory_context(self) -> bool:
        """
        🚀 INICIALIZACIÓN DEL CONTEXTO EN MEMORIA
        
        Returns:
            True si la inicialización fue exitosa
        """
        
        try:
            # Simular carga de contexto inicial
            await asyncio.sleep(0.1)  # Simular tiempo de carga
            
            # Inicializar estructuras básicas
            self.user_conversations = {}
            self.memory_stats["initialized_at"] = datetime.utcnow().isoformat()
            
            logger.info("✅ Memory context initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing memory context: {str(e)}")
            return False
    
    async def chat_with_context(
        self, 
        user_id: str, 
        message: str, 
        use_threading: bool = True
    ) -> Dict[str, Any]:
        """
        💬 CHAT CON CONTEXTO COMPLETO
        
        Args:
            user_id: ID del usuario
            message: Mensaje del usuario
            use_threading: Usar threading para respuesta rápida
            
        Returns:
            Respuesta completa con contexto y metadata
        """
        
        start_time = datetime.utcnow()
        
        try:
            # Obtener o crear conversación del usuario
            if user_id not in self.user_conversations:
                self.user_conversations[user_id] = {
                    "messages": [],
                    "created_at": start_time.isoformat(),
                    "last_active": start_time.isoformat()
                }
                self.memory_stats["active_users"] += 1
            
            conversation = self.user_conversations[user_id]
            
            # Agregar mensaje a la conversación
            conversation["messages"].append({
                "timestamp": start_time.isoformat(),
                "message": message,
                "type": "user"
            })
            conversation["last_active"] = start_time.isoformat()
            
            # Crear contexto desde el historial
            context = self._build_conversation_context(conversation)
            
            # Generar respuesta con contexto
            prompt = f"""
            Conversación en curso con el usuario {user_id}.
            
            Historial reciente:
            {context}
            
            Último mensaje del usuario: "{message}"
            
            Responde como un asistente experto en eventos, manteniendo el contexto
            de la conversación y siendo útil y amigable.
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            # Agregar respuesta a la conversación
            conversation["messages"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": response,
                "type": "assistant"
            })
            
            # Actualizar estadísticas
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            self._update_stats(response_time)
            
            result = {
                "status": "success",
                "response": response,
                "relevant_events": [],  # TODO: Integrar eventos relevantes
                "context_source": "memory_optimized",
                "performance": {
                    "response_time_ms": response_time * 1000,
                    "used_threading": use_threading,
                    "context_messages": len(conversation["messages"])
                },
                "conversation_length": len(conversation["messages"])
            }
            
            logger.info(f"✅ Chat response generated for user {user_id} in {response_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in chat_with_context: {str(e)}")
            return {
                "status": "error",
                "response": "Lo siento, tuve un problema procesando tu mensaje.",
                "error": str(e),
                "context_source": "error_fallback",
                "performance": {"error": True}
            }
    
    def _build_conversation_context(self, conversation: Dict[str, Any]) -> str:
        """
        📝 CONSTRUIR CONTEXTO DE CONVERSACIÓN
        
        Args:
            conversation: Datos de la conversación
            
        Returns:
            Contexto formateado para el prompt
        """
        
        messages = conversation["messages"]
        
        # Tomar últimos 6 mensajes para mantener contexto relevante
        recent_messages = messages[-6:] if len(messages) > 6 else messages
        
        context_lines = []
        for msg in recent_messages:
            msg_type = "Usuario" if msg["type"] == "user" else "Asistente"
            context_lines.append(f"{msg_type}: {msg['message']}")
        
        return "\n".join(context_lines)
    
    def _update_stats(self, response_time: float):
        """Actualizar estadísticas de rendimiento"""
        self.memory_stats["total_conversations"] += 1
        
        # Actualizar tiempo promedio de respuesta
        current_avg = self.memory_stats["average_response_time"]
        total_convs = self.memory_stats["total_conversations"]
        
        new_avg = ((current_avg * (total_convs - 1)) + response_time) / total_convs
        self.memory_stats["average_response_time"] = new_avg
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        📊 OBTENER ESTADÍSTICAS DE MEMORIA
        
        Returns:
            Estadísticas completas del sistema de memoria
        """
        
        return {
            **self.memory_stats,
            "active_users": len(self.user_conversations),
            "total_messages": sum(
                len(conv["messages"]) 
                for conv in self.user_conversations.values()
            ),
            "current_time": datetime.utcnow().isoformat()
        }
    
    async def refresh_memory_context(self):
        """
        🔄 REFRESCAR CONTEXTO EN MEMORIA
        
        Limpia conversaciones antiguas y actualiza el contexto
        """
        
        try:
            # Limpiar conversaciones muy largas (más de 50 mensajes)
            cleaned_conversations = 0
            
            for user_id, conversation in list(self.user_conversations.items()):
                if len(conversation["messages"]) > 50:
                    # Mantener solo los últimos 20 mensajes
                    conversation["messages"] = conversation["messages"][-20:]
                    cleaned_conversations += 1
            
            self.memory_stats["cache_hits"] += 1
            
            logger.info(f"✅ Memory refreshed - cleaned {cleaned_conversations} conversations")
            
        except Exception as e:
            logger.error(f"❌ Error refreshing memory: {str(e)}")
    
    def clear_user_conversation(self, user_id: str):
        """
        🗑️ LIMPIAR CONVERSACIÓN DE USUARIO
        
        Args:
            user_id: ID del usuario
        """
        
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]
            self.memory_stats["active_users"] -= 1
            logger.info(f"✅ Cleared conversation for user {user_id}")

# Instancia singleton
chat_memory_manager = ChatMemoryManager()