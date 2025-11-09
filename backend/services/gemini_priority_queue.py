"""
Sistema de cola con prioridades para requests a Gemini AI
Prioriza Análisis Inteligente sobre comentarios de asistentes
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import IntEnum
import time

logger = logging.getLogger(__name__)

class Priority(IntEnum):
    """Niveles de prioridad para requests"""
    CRITICAL = 0   # Análisis Inteligente de eventos (event-insight)
    HIGH = 1       # Recomendaciones importantes
    NORMAL = 2     # Búsquedas normales
    LOW = 3        # Comentarios de Sofia/Juan
    BACKGROUND = 4 # Tareas background

@dataclass(order=True)
class GeminiRequest:
    """Request a Gemini con prioridad"""
    priority: int
    timestamp: float = field(default_factory=time.time)
    prompt: str = field(compare=False)
    request_id: str = field(compare=False)
    callback: Optional[Any] = field(default=None, compare=False)

class GeminiPriorityQueue:
    """
    Cola de prioridad para requests a Gemini
    Garantiza que el Análisis Inteligente se procese primero
    """
    def __init__(self, max_concurrent: int = 2):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.processing: Dict[str, bool] = {}
        self.max_concurrent = max_concurrent
        self.active_requests = 0
        self._lock = asyncio.Lock()

    async def add_request(
        self,
        prompt: str,
        priority: Priority = Priority.NORMAL,
        request_id: str = None
    ) -> str:
        """
        Agrega un request a la cola
        Returns: request_id para tracking
        """
        if request_id is None:
            request_id = f"{priority.name}_{int(time.time() * 1000)}"

        request = GeminiRequest(
            priority=priority.value,
            prompt=prompt,
            request_id=request_id
        )

        await self.queue.put(request)
        logger.info(f"📥 Request agregado: {request_id} (Priority: {priority.name}, Queue size: {self.queue.qsize()})")

        return request_id

    async def process_queue(self, gemini_model):
        """
        Procesa requests de la cola respetando prioridades
        """
        while True:
            try:
                # Esperar si ya hay demasiados requests concurrentes
                async with self._lock:
                    if self.active_requests >= self.max_concurrent:
                        await asyncio.sleep(0.1)
                        continue

                    self.active_requests += 1

                # Obtener el request de mayor prioridad
                request: GeminiRequest = await self.queue.get()

                logger.info(f"⚡ Procesando: {request.request_id} (Priority: {Priority(request.priority).name})")

                try:
                    # Procesar con Gemini
                    response = await asyncio.to_thread(
                        gemini_model.generate_content,
                        request.prompt
                    )

                    logger.info(f"✅ Completado: {request.request_id}")

                    # Marcar como completado
                    self.processing[request.request_id] = True

                except Exception as e:
                    logger.error(f"❌ Error procesando {request.request_id}: {e}")

                finally:
                    async with self._lock:
                        self.active_requests -= 1
                    self.queue.task_done()

            except Exception as e:
                logger.error(f"Error en process_queue: {e}")
                await asyncio.sleep(1)

# Singleton global
_queue_instance: Optional[GeminiPriorityQueue] = None

def get_priority_queue() -> GeminiPriorityQueue:
    """Obtiene la instancia singleton de la cola"""
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = GeminiPriorityQueue(max_concurrent=3)
    return _queue_instance
