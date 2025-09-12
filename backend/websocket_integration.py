#!/usr/bin/env python3
"""
🔗 WEBSOCKET INTEGRATION
Integración completa del streaming optimizado en main.py
"""

from fastapi import WebSocket, WebSocketDisconnect
import logging
from websocket_streaming import websocket_search_streaming, websocket_recommend_streaming

logger = logging.getLogger(__name__)

async def integrated_search_websocket(websocket: WebSocket, manager):
    """
    🚀 WEBSOCKET SEARCH INTEGRADO CON STREAMING OPTIMIZADO
    
    Reemplaza la función websocket_search_events del main.py
    con la nueva implementación streaming
    """
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "🚀 Streaming optimizado - Listo para búsqueda real-time"
        })
        
        while True:
            # Wait for search request
            data = await websocket.receive_json()
            
            if data.get("action") == "search":
                # Extract location from message or use default
                message = data.get("message", "")
                base_location = data.get("location", "Buenos Aires")
                detected_location = base_location
                
                # Simple location detection for global cities
                if message:
                    message_lower = message.lower()
                    location_mapping = {
                        "barcelona": "Barcelona", "bcn": "Barcelona",
                        "madrid": "Madrid", "paris": "Paris",
                        "córdoba": "Córdoba", "cordoba": "Córdoba",
                        "mendoza": "Mendoza", "rosario": "Rosario",
                        "buenos aires": "Buenos Aires", "caba": "Buenos Aires"
                    }
                    
                    for keyword, city in location_mapping.items():
                        if keyword in message_lower:
                            detected_location = city
                            break
                
                # Use the new optimized streaming
                await websocket_search_streaming(websocket, detected_location)
                
    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected from search streaming")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Error in search WebSocket: {e}")
        try:
            await websocket.send_json({
                "type": "connection_error", 
                "message": f"Error de conexión: {str(e)}"
            })
        except:
            pass

async def integrated_recommend_websocket(websocket: WebSocket, manager, location: str):
    """
    💡 WEBSOCKET RECOMMEND INTEGRADO
    
    Para recomendaciones basadas en ciudades aledañas
    """
    await manager.connect(websocket)
    try:
        # Use the new recommend streaming
        await websocket_recommend_streaming(websocket, location)
                
    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected from recommend streaming")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Error in recommend WebSocket: {e}")
        try:
            await websocket.send_json({
                "type": "connection_error",
                "message": f"Error de conexión: {str(e)}"
            })
        except:
            pass