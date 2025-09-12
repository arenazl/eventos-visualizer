#!/usr/bin/env python3
"""
🚀 TEST WEBSOCKET STREAMING - Prueba del streaming optimizado
Prueba el nuevo sistema de streaming con caché y flags
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_streaming():
    uri = "ws://172.29.228.80:8001/ws/search-events"
    
    print("🚀 Conectando a WebSocket streaming optimizado...")
    print(f"📍 URI: {uri}")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Conexión establecida!")
            
            # Esperar mensaje de conexión
            connection_msg = await websocket.recv()
            data = json.loads(connection_msg)
            print(f"🔌 {data.get('message', 'Conectado')}")
            
            # Enviar solicitud de búsqueda
            search_request = {
                "action": "search",
                "location": "Buenos Aires",
                "message": "eventos en Buenos Aires"
            }
            
            await websocket.send(json.dumps(search_request))
            print(f"📨 Solicitud enviada: {search_request}")
            print("=" * 60)
            
            # Escuchar mensajes de streaming
            events_received = 0
            scrapers_completed = 0
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    msg_type = data.get('type', 'unknown')
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    if msg_type == "search_started":
                        print(f"🚀 [{timestamp}] BÚSQUEDA INICIADA")
                        print(f"   📍 Ubicación: {data.get('location')}")
                        print(f"   🔧 Scrapers habilitados: {data.get('enabled_scrapers')}")
                        
                    elif msg_type == "scrapers_discovered":
                        print(f"🔍 [{timestamp}] SCRAPERS DESCUBIERTOS")
                        print(f"   🛠️ Scrapers: {data.get('scrapers')}")
                        print(f"   📊 Progreso: {data.get('progress', 0)}%")
                        
                    elif msg_type == "scraper_started":
                        print(f"⚡ [{timestamp}] SCRAPER INICIADO")
                        print(f"   🔧 Scraper: {data.get('scraper')}")
                        print(f"   📊 Progreso: {data.get('progress', 0)}%")
                        
                    elif msg_type == "events_batch":
                        events_count = data.get('count', 0)
                        events_received += events_count
                        execution_time = data.get('execution_time', '0s')
                        total_events = data.get('total_events', events_received)
                        
                        print(f"🎉 [{timestamp}] EVENTOS RECIBIDOS!")
                        print(f"   🔧 Scraper: {data.get('scraper')}")
                        print(f"   📊 Eventos: {events_count} (Total: {total_events})")
                        print(f"   ⏱️ Tiempo: {execution_time}")
                        print(f"   📈 Progreso: {data.get('progress', 0)}%")
                        
                    elif msg_type == "scraper_completed":
                        scrapers_completed += 1
                        print(f"✅ [{timestamp}] SCRAPER COMPLETADO")
                        print(f"   🔧 Scraper: {data.get('scraper')}")
                        print(f"   📊 Eventos: {data.get('count', 0)}")
                        print(f"   ⏱️ Tiempo: {data.get('execution_time', '0s')}")
                        
                    elif msg_type == "scraper_timeout":
                        scrapers_completed += 1
                        print(f"⏰ [{timestamp}] SCRAPER TIMEOUT")
                        print(f"   🔧 Scraper: {data.get('scraper')}")
                        print(f"   💬 Mensaje: {data.get('message')}")
                        
                    elif msg_type == "scraper_error":
                        scrapers_completed += 1
                        print(f"❌ [{timestamp}] SCRAPER ERROR")
                        print(f"   🔧 Scraper: {data.get('scraper')}")
                        print(f"   💬 Mensaje: {data.get('message')}")
                        
                    elif msg_type == "search_completed":
                        print("=" * 60)
                        print(f"🎯 [{timestamp}] BÚSQUEDA COMPLETADA!")
                        print(f"   📊 Total eventos: {data.get('total_events')}")
                        print(f"   🔧 Scrapers usados: {data.get('scrapers_used')}")
                        print(f"   💬 {data.get('message')}")
                        break
                        
                    elif msg_type == "search_error":
                        print(f"❌ [{timestamp}] ERROR EN BÚSQUEDA")
                        print(f"   💬 Mensaje: {data.get('message')}")
                        break
                        
                    else:
                        print(f"❓ [{timestamp}] MENSAJE DESCONOCIDO: {msg_type}")
                        print(f"   📝 Data: {data}")
                    
                    print()  # Línea en blanco para separar mensajes
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout esperando mensaje - finalizando prueba")
                    break
                    
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    print("=" * 60)
    print("🏁 Prueba de WebSocket streaming completada")
    print(f"📊 Eventos recibidos: {events_received}")
    print(f"🔧 Scrapers completados: {scrapers_completed}")

if __name__ == "__main__":
    asyncio.run(test_websocket_streaming())