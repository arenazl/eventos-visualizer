"""
🧠 CHAT MEMORY MANAGER
Sistema de chat inteligente que carga toda la base de datos en memoria
al inicio y maneja conversaciones con hilos para máxima eficiencia
"""

import asyncio
import threading
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

@dataclass
class EventContext:
    """Estructura optimizada para eventos en memoria"""
    id: str
    titulo: str
    descripcion: str
    venue: str
    categoria: str
    subcategoria: str
    precio: float
    moneda: str
    es_gratis: bool
    fecha_inicio: str
    fecha_fin: str
    latitud: float
    longitud: float
    tags: List[str]
    imagen_url: str
    barrio: str
    fuente: str

class ChatMemoryManager:
    """
    🎯 MANAGER PRINCIPAL: Chat con contexto completo en memoria
    """
    
    def __init__(self):
        self.events_in_memory: List[EventContext] = []
        self.user_conversations: Dict[str, List[Dict]] = {}
        self.memory_loaded = False
        self.last_refresh = None
        self.thread_executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()
        
        # Estadísticas de performance
        self.stats = {
            "total_events_loaded": 0,
            "memory_size_mb": 0,
            "queries_served": 0,
            "avg_response_time": 0.0,
            "load_time_seconds": 0.0
        }
    
    async def initialize_memory_context(self):
        """
        🔥 INICIALIZACIÓN: Carga toda la BD en memoria al arranque
        """
        start_time = time.time()
        logger.info("🧠 Inicializando contexto completo en memoria...")
        
        try:
            # PASO 1: Cargar desde endpoint ultrarrápido (simulando vista de BD)
            events_data = await self._load_events_from_database()
            
            # PASO 2: Convertir a estructura optimizada para chat
            with self._lock:
                self.events_in_memory.clear()
                
                for event_data in events_data:
                    event_context = EventContext(
                        id=event_data.get("id", f"evt_{hash(event_data.get('title', ''))}"),
                        titulo=event_data.get("title", ""),
                        descripcion=event_data.get("description", ""),
                        venue=event_data.get("venue_name", ""),
                        categoria=event_data.get("category", ""),
                        subcategoria=event_data.get("subcategory", ""),
                        precio=float(event_data.get("price", 0)),
                        moneda=event_data.get("currency", "ARS"),
                        es_gratis=event_data.get("is_free", False),
                        fecha_inicio=event_data.get("start_datetime", ""),
                        fecha_fin=event_data.get("end_datetime", ""),
                        latitud=float(event_data.get("latitude", 0)),
                        longitud=float(event_data.get("longitude", 0)),
                        tags=event_data.get("tags", []),
                        imagen_url=event_data.get("image_url", ""),
                        barrio=event_data.get("neighborhood", ""),
                        fuente=event_data.get("source", "")
                    )
                    self.events_in_memory.append(event_context)
                
                self.memory_loaded = True
                self.last_refresh = datetime.now()
                
                # Estadísticas
                load_time = time.time() - start_time
                self.stats.update({
                    "total_events_loaded": len(self.events_in_memory),
                    "memory_size_mb": self._calculate_memory_usage(),
                    "load_time_seconds": round(load_time, 3)
                })
                
            logger.info(f"✅ Contexto cargado: {len(self.events_in_memory)} eventos en {load_time:.2f}s")
            logger.info(f"📊 Memoria utilizada: {self.stats['memory_size_mb']:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando contexto en memoria: {e}")
            return False
    
    async def _load_events_from_database(self) -> List[Dict]:
        """
        📊 CARGA DESDE 'VISTA' DE BD: En producción será SELECT optimizado
        """
        try:
            # SIMULACIÓN: En producción será algo como:
            # SELECT id, title, description, venue_name, category, price, currency, 
            #        is_free, start_datetime, latitude, longitude, tags, image_url, source
            # FROM events_optimized_view 
            # WHERE status = 'active' AND start_datetime >= NOW()
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://172.29.228.80:8001/api/events-fast?limit=50") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("events", [])
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error cargando eventos desde BD: {e}")
            return []
    
    async def chat_with_context(self, user_id: str, message: str, use_threading: bool = True) -> Dict:
        """
        💬 CHAT PRINCIPAL: Usa contexto en memoria + hilos para eficiencia
        """
        if not self.memory_loaded:
            await self.initialize_memory_context()
        
        start_time = time.time()
        
        try:
            if use_threading:
                # Usar hilo separado para procesamiento pesado
                result = await asyncio.get_event_loop().run_in_executor(
                    self.thread_executor,
                    self._process_chat_in_thread,
                    user_id, message
                )
            else:
                # Procesamiento directo
                result = self._process_chat_sync(user_id, message)
            
            # Actualizar estadísticas
            response_time = time.time() - start_time
            self.stats["queries_served"] += 1
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["queries_served"] - 1) + response_time)
                / self.stats["queries_served"]
            )
            
            result["performance"] = {
                "response_time_ms": round(response_time * 1000, 2),
                "events_in_memory": len(self.events_in_memory),
                "memory_usage_mb": self.stats["memory_size_mb"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en chat con contexto: {e}")
            return {
                "status": "error",
                "error": str(e),
                "fallback_message": "Lo siento, hubo un problema técnico. Intenta de nuevo."
            }
    
    def _process_chat_in_thread(self, user_id: str, message: str) -> Dict:
        """
        🧵 PROCESAMIENTO EN HILO: Para no bloquear el servidor principal
        """
        return self._process_chat_sync(user_id, message)
    
    def _process_chat_sync(self, user_id: str, message: str) -> Dict:
        """
        ⚡ PROCESAMIENTO SINCRÓNICO: Lógica principal del chat
        """
        with self._lock:
            # 1. Guardar conversación del usuario
            if user_id not in self.user_conversations:
                self.user_conversations[user_id] = []
            
            self.user_conversations[user_id].append({
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "type": "user_input"
            })
            
            # 2. Buscar eventos relevantes en memoria
            relevant_events = self._find_relevant_events(message)
            
            # 3. Generar respuesta contextual
            response = self._generate_contextual_response(user_id, message, relevant_events)
            
            # 4. Guardar respuesta
            self.user_conversations[user_id].append({
                "timestamp": datetime.now().isoformat(),
                "message": response,
                "type": "ai_response"
            })
            
            return {
                "status": "success",
                "response": response,
                "relevant_events": relevant_events[:5],  # Top 5 más relevantes
                "conversation_length": len(self.user_conversations[user_id]),
                "context_source": "memory_optimized"
            }
    
    def _find_relevant_events(self, message: str) -> List[Dict]:
        """
        🔍 BÚSQUEDA INTELIGENTE: Encuentra eventos relevantes en memoria
        """
        message_lower = message.lower()
        relevant_events = []
        
        for event in self.events_in_memory:
            relevance_score = 0
            
            # Scoring por keywords
            if any(keyword in event.titulo.lower() for keyword in message_lower.split()):
                relevance_score += 50
            
            if any(keyword in event.descripcion.lower() for keyword in message_lower.split()):
                relevance_score += 30
            
            if any(keyword in event.venue.lower() for keyword in message_lower.split()):
                relevance_score += 40
            
            # Scoring por categoría
            if event.categoria.lower() in message_lower:
                relevance_score += 60
            
            # Scoring por precio (si mencionan "gratis", "barato", etc.)
            if "gratis" in message_lower and event.es_gratis:
                relevance_score += 25
            if "barato" in message_lower and event.precio < 1000:
                relevance_score += 20
            
            if relevance_score > 20:  # Threshold mínimo
                relevant_events.append({
                    "event": event.__dict__,
                    "score": relevance_score
                })
        
        # Ordenar por relevancia
        relevant_events.sort(key=lambda x: x["score"], reverse=True)
        return [evt["event"] for evt in relevant_events[:10]]
    
    def _generate_contextual_response(self, user_id: str, message: str, relevant_events: List[Dict]) -> str:
        """
        💡 GENERADOR DE RESPUESTAS: Basado en contexto y eventos encontrados
        """
        if not relevant_events:
            return ("¡Hola! No encontré eventos específicos para lo que buscás, "
                   "pero tengo muchas opciones interesantes. ¿Podrías contarme más "
                   "sobre qué tipo de evento te interesa?")
        
        # Respuesta personalizada basada en eventos encontrados
        event_types = list(set([evt["categoria"] for evt in relevant_events[:3]]))
        
        response = f"¡Genial! Encontré {len(relevant_events)} opciones que podrían interesarte. "
        
        if len(relevant_events) >= 3:
            top_event = relevant_events[0]
            response += (f"Te recomiendo especialmente '{top_event['titulo']}' "
                        f"en {top_event['venue']}. ")
        
        response += f"Tengo eventos de {', '.join(event_types)}. ¿Cuál te llama más la atención?"
        
        return response
    
    def _calculate_memory_usage(self) -> float:
        """Calcular uso aproximado de memoria en MB"""
        import sys
        total_size = sum(sys.getsizeof(event.__dict__) for event in self.events_in_memory)
        return total_size / (1024 * 1024)  # Convert to MB
    
    def get_memory_stats(self) -> Dict:
        """📊 Estadísticas del sistema de memoria"""
        return {
            **self.stats,
            "memory_loaded": self.memory_loaded,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "active_conversations": len(self.user_conversations),
            "thread_pool_size": self.thread_executor._max_workers
        }
    
    async def refresh_memory_context(self):
        """🔄 Refrescar contexto (ejecutar cada X horas)"""
        logger.info("🔄 Refrescando contexto en memoria...")
        await self.initialize_memory_context()

# 🌍 INSTANCIA GLOBAL
chat_memory_manager = ChatMemoryManager()