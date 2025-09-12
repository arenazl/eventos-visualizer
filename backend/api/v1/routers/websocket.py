"""
Router para WebSocket - Streaming en tiempo real
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Set, Optional, Any
import logging
import asyncio
import json
from datetime import datetime

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Gestión de conexiones WebSocket
class ConnectionManager:
    """
    Gestor de conexiones WebSocket
    """
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_data: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str, location: Optional[str] = None):
        """
        Aceptar nueva conexión WebSocket
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_data[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "location": location,
            "last_heartbeat": datetime.now().isoformat()
        }
        logger.info(f"🔌 WebSocket connected: {client_id} (location: {location})")
        
        # Enviar mensaje de bienvenida
        await self.send_personal_message({
            "type": "welcome",
            "client_id": client_id,
            "message": "Connected to Eventos Visualizer streaming",
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
    def disconnect(self, client_id: str):
        """
        Desconectar cliente
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_data:
            del self.connection_data[client_id]
        logger.info(f"🔌 WebSocket disconnected: {client_id}")
        
    async def send_personal_message(self, message: dict, client_id: str):
        """
        Enviar mensaje a cliente específico
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
                
    async def broadcast(self, message: dict, exclude_client: Optional[str] = None):
        """
        Broadcast mensaje a todos los clientes conectados
        """
        disconnected = []
        
        for client_id, websocket in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue
                
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Limpiar conexiones muertas
        for client_id in disconnected:
            self.disconnect(client_id)
            
    async def send_to_location(self, message: dict, location: str):
        """
        Enviar mensaje a clientes de una ubicación específica
        """
        for client_id, data in self.connection_data.items():
            if data.get("location") == location:
                await self.send_personal_message(message, client_id)
                
    def get_stats(self) -> dict:
        """
        Obtener estadísticas de conexiones
        """
        locations = {}
        for data in self.connection_data.values():
            loc = data.get("location", "unknown")
            locations[loc] = locations.get(loc, 0) + 1
            
        return {
            "total_connections": len(self.active_connections),
            "connections_by_location": locations,
            "active_clients": list(self.active_connections.keys())
        }

# Instancia global del manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(..., description="ID único del cliente"),
    location: Optional[str] = Query(None, description="Ubicación del cliente")
):
    """
    WebSocket principal para streaming de eventos
    """
    await manager.connect(websocket, client_id, location)
    
    try:
        while True:
            # Recibir datos del cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Procesar mensaje del cliente
            await _handle_client_message(message, client_id, location)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


@router.websocket("/ws/events")
async def events_stream_websocket(
    websocket: WebSocket,
    client_id: str = Query(..., description="ID único del cliente"),
    location: str = Query("Buenos Aires", description="Ciudad para eventos"),
    stream_type: str = Query("live", description="Tipo: live, updates, recommendations")
):
    """
    WebSocket específico para streaming de eventos
    """
    await manager.connect(websocket, client_id, location)
    
    try:
        # Iniciar streaming según el tipo
        if stream_type == "live":
            await _start_live_events_stream(client_id, location)
        elif stream_type == "updates":
            await _start_events_updates_stream(client_id, location)
        elif stream_type == "recommendations":
            await _start_recommendations_stream(client_id, location)
            
        # Mantener conexión activa
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Manejar comandos de streaming
            await _handle_streaming_command(message, client_id, location, stream_type)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Events stream client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Events stream error for {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/ws/stats")
async def websocket_stats():
    """
    Estadísticas de conexiones WebSocket activas
    """
    stats = manager.get_stats()
    return {
        "success": True,
        "websocket_stats": stats,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/ws/broadcast")
async def broadcast_message(
    message: dict,
    location: Optional[str] = None
):
    """
    Enviar mensaje broadcast a clientes WebSocket
    """
    try:
        broadcast_data = {
            "type": "broadcast",
            "data": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if location:
            await manager.send_to_location(broadcast_data, location)
            logger.info(f"📡 Broadcast sent to location: {location}")
        else:
            await manager.broadcast(broadcast_data)
            logger.info("📡 Broadcast sent to all clients")
            
        return {
            "success": True,
            "message": "Broadcast sent",
            "recipients": location or "all"
        }
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# Funciones helper para manejo de mensajes

async def _handle_client_message(message: dict, client_id: str, location: Optional[str]):
    """
    Manejar mensaje recibido del cliente
    """
    message_type = message.get("type", "unknown")
    
    if message_type == "heartbeat":
        await _handle_heartbeat(client_id)
    elif message_type == "search":
        await _handle_search_request(message, client_id, location)
    elif message_type == "subscribe":
        await _handle_subscription(message, client_id, location)
    elif message_type == "filter":
        await _handle_filter_update(message, client_id, location)
    else:
        logger.warning(f"Unknown message type: {message_type} from {client_id}")


async def _handle_heartbeat(client_id: str):
    """
    Manejar heartbeat del cliente
    """
    if client_id in manager.connection_data:
        manager.connection_data[client_id]["last_heartbeat"] = datetime.now().isoformat()
        
    await manager.send_personal_message({
        "type": "heartbeat_ack",
        "timestamp": datetime.now().isoformat()
    }, client_id)


async def _handle_search_request(message: dict, client_id: str, location: Optional[str]):
    """
    Manejar búsqueda en tiempo real
    """
    query = message.get("query", "")
    
    # Simular búsqueda en tiempo real
    search_results = await _perform_realtime_search(query, location)
    
    await manager.send_personal_message({
        "type": "search_results",
        "query": query,
        "results": search_results,
        "timestamp": datetime.now().isoformat()
    }, client_id)


async def _handle_subscription(message: dict, client_id: str, location: Optional[str]):
    """
    Manejar suscripción a tipos de eventos
    """
    subscription = message.get("subscription", {})
    
    # Actualizar datos de conexión con suscripción
    if client_id in manager.connection_data:
        manager.connection_data[client_id]["subscription"] = subscription
        
    await manager.send_personal_message({
        "type": "subscription_confirmed",
        "subscription": subscription,
        "timestamp": datetime.now().isoformat()
    }, client_id)


async def _handle_filter_update(message: dict, client_id: str, location: Optional[str]):
    """
    Manejar actualización de filtros
    """
    filters = message.get("filters", {})
    
    # Aplicar filtros y enviar resultados actualizados
    filtered_events = await _apply_filters_and_search(filters, location)
    
    await manager.send_personal_message({
        "type": "filtered_events",
        "filters": filters,
        "events": filtered_events,
        "timestamp": datetime.now().isoformat()
    }, client_id)


async def _handle_streaming_command(message: dict, client_id: str, location: str, stream_type: str):
    """
    Manejar comandos específicos de streaming
    """
    command = message.get("command", "")
    
    if command == "pause":
        await _pause_stream(client_id)
    elif command == "resume":
        await _resume_stream(client_id, location, stream_type)
    elif command == "change_location":
        new_location = message.get("location", location)
        await _change_stream_location(client_id, new_location, stream_type)


# Funciones de streaming

async def _start_live_events_stream(client_id: str, location: str):
    """
    Iniciar streaming de eventos en vivo
    """
    # Simular eventos en tiempo real
    asyncio.create_task(_live_events_loop(client_id, location))


async def _start_events_updates_stream(client_id: str, location: str):
    """
    Iniciar streaming de actualizaciones de eventos
    """
    asyncio.create_task(_events_updates_loop(client_id, location))


async def _start_recommendations_stream(client_id: str, location: str):
    """
    Iniciar streaming de recomendaciones
    """
    asyncio.create_task(_recommendations_loop(client_id, location))


async def _live_events_loop(client_id: str, location: str):
    """
    Loop para enviar eventos en tiempo real
    """
    try:
        while client_id in manager.active_connections:
            # Simular nuevo evento cada 30 segundos
            await asyncio.sleep(30)
            
            # Generar evento simulado
            event = {
                "id": f"live_{datetime.now().timestamp()}",
                "title": f"Nuevo evento en {location}",
                "description": "Evento descubierto en tiempo real",
                "location": location,
                "start_date": datetime.now().isoformat(),
                "category": "general",
                "source": "live_stream"
            }
            
            await manager.send_personal_message({
                "type": "live_event",
                "event": event,
                "timestamp": datetime.now().isoformat()
            }, client_id)
            
    except Exception as e:
        logger.error(f"Live events loop error for {client_id}: {e}")


async def _events_updates_loop(client_id: str, location: str):
    """
    Loop para enviar actualizaciones de eventos
    """
    try:
        while client_id in manager.active_connections:
            await asyncio.sleep(60)  # Cada minuto
            
            update = {
                "type": "events_update",
                "message": f"Actualizaciones disponibles para {location}",
                "count": 3,  # Simulado
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(update, client_id)
            
    except Exception as e:
        logger.error(f"Events updates loop error for {client_id}: {e}")


async def _recommendations_loop(client_id: str, location: str):
    """
    Loop para enviar recomendaciones personalizadas
    """
    try:
        while client_id in manager.active_connections:
            await asyncio.sleep(120)  # Cada 2 minutos
            
            recommendation = {
                "type": "recommendation",
                "event": {
                    "title": f"Recomendado para ti en {location}",
                    "description": "Evento personalizado según tus intereses",
                    "category": "recomendado",
                    "score": 0.85
                },
                "reason": "Basado en tus preferencias anteriores",
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(recommendation, client_id)
            
    except Exception as e:
        logger.error(f"Recommendations loop error for {client_id}: {e}")


# Funciones helper adicionales

async def _perform_realtime_search(query: str, location: Optional[str]) -> List[dict]:
    """
    Búsqueda en tiempo real simulada
    """
    # Simular búsqueda rápida
    await asyncio.sleep(0.5)
    
    return [
        {
            "id": "realtime_1",
            "title": f"Resultado para '{query}'",
            "location": location,
            "relevance": 0.9
        }
    ]


async def _apply_filters_and_search(filters: dict, location: Optional[str]) -> List[dict]:
    """
    Aplicar filtros y retornar eventos filtrados
    """
    # Simular filtrado
    await asyncio.sleep(0.3)
    
    return [
        {
            "id": "filtered_1",
            "title": "Evento filtrado",
            "location": location,
            "filters_applied": filters
        }
    ]


async def _pause_stream(client_id: str):
    """
    Pausar stream para cliente
    """
    await manager.send_personal_message({
        "type": "stream_paused",
        "timestamp": datetime.now().isoformat()
    }, client_id)


async def _resume_stream(client_id: str, location: str, stream_type: str):
    """
    Reanudar stream para cliente
    """
    await manager.send_personal_message({
        "type": "stream_resumed",
        "stream_type": stream_type,
        "location": location,
        "timestamp": datetime.now().isoformat()
    }, client_id)
    
    # Reactivar streaming apropiado
    if stream_type == "live":
        await _start_live_events_stream(client_id, location)


async def _change_stream_location(client_id: str, new_location: str, stream_type: str):
    """
    Cambiar ubicación de streaming
    """
    # Actualizar datos de conexión
    if client_id in manager.connection_data:
        manager.connection_data[client_id]["location"] = new_location
    
    await manager.send_personal_message({
        "type": "location_changed",
        "new_location": new_location,
        "stream_type": stream_type,
        "timestamp": datetime.now().isoformat()
    }, client_id)