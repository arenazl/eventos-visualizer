#!/usr/bin/env python3
"""
Test script para el WebSocket de streaming de eventos
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    uri = "ws://172.29.228.80:8001/ws/search-events"
    
    try:
        print("🔥 Conectando a WebSocket streaming...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Conectado!")
            
            # Recibir mensaje de conexiónºº
            connection_msg = await websocket.recv()
            data = json.loads(connection_msg)
            print(f"📨 Conexión: {data.get('message', '')}")
            
            # Enviar solicitud de búsqueda
            search_request = {
                "action": "search",
                "location": "Buenos Aires"
            }
            
            await websocket.send(json.dumps(search_request))
            print("📤 Solicitud de búsqueda enviada...")
            
            # Escuchar mensajes
            event_count = 0
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=45.0)
                    data = json.loads(message)
                    
                    msg_type = data.get('type', 'unknown')
                    
                    if msg_type == 'search_started':
                        print(f"🚀 {data.get('message', '')}")
                        
                    elif msg_type == 'source_started':
                        source = data.get('source', '')
                        emoji = '🎫' if source == 'eventbrite' else '🔥' if source == 'facebook' else '📸'
                        print(f"{emoji} {data.get('message', '')} (Progreso: {data.get('progress', 0)}%)")
                        
                    elif msg_type == 'events_batch':
                        events = data.get('events', [])
                        event_count += len(events)
                        source = data.get('source', '')
                        progress = data.get('progress', 0)
                        
                        print(f"📦 {len(events)} eventos de {source} - Total: {event_count} (Progreso: {progress}%)")
                        
                        # Mostrar algunos eventos de ejemplo
                        for i, event in enumerate(events[:2]):  # Solo primeros 2
                            title = event.get('title', 'Sin título')[:50]
                            venue = event.get('venue_name', 'Sin venue')
                            print(f"   {i+1}. {title}... ({venue})")
                        
                        if len(events) > 2:
                            print(f"   ... y {len(events)-2} eventos más")
                            
                    elif msg_type == 'search_completed':
                        total = data.get('total_events', 0)
                        print(f"🎉 {data.get('message', '')} - Total final: {total} eventos")
                        break
                        
                    elif msg_type == 'search_error':
                        print(f"❌ Error: {data.get('message', '')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏱️ Timeout - cerrando conexión")
                    break
                    
    except Exception as e:
        print(f"❌ Error conectando a WebSocket: {e}")

if __name__ == "__main__":
    print("🧪 Test WebSocket Streaming de Eventos")
    print("=" * 50)
    asyncio.run(test_websocket())
    print("=" * 50)
    print("✅ Test completado")