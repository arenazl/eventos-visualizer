#!/usr/bin/env python3
"""
🌐 WEBSOCKET STREAMING CON ASYNC GENERATOR
Nueva implementación optimizada del WebSocket que usa el streaming factory
"""

from fastapi import WebSocket
import logging
import time
from services.industrial_factory import IndustrialFactory
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def websocket_search_streaming(websocket: WebSocket, location: str):
    """
    🚀 WEBSOCKET CON STREAMING OPTIMIZADO
    
    Usa async generator para entregar resultados en tiempo real
    sin esperar que terminen todos los scrapers
    """
    
    try:
        # 1. Inicialización
        await websocket.send_json({
            "type": "search_started",
            "message": f"🚀 Streaming iniciado para {location}",
            "location": location,
            "timestamp": time.time()
        })
        
        factory = IndustrialFactory()
        total_events = 0
        scrapers_completed = 0
        first_result_time = None
        start_time = time.time()
        
        # 2. Streaming con async generator
        async for result in factory.execute_streaming(
            location=location,
            limit=10  # 10 eventos por scraper
        ):
            scrapers_completed += 1
            current_time = time.time() - start_time
            
            # Record first result time
            if first_result_time is None:
                first_result_time = current_time
            
            # Extract result data
            scraper_name = result.get('scraper', 'unknown')
            events = result.get('events', [])
            events_count = len(events)
            execution_time = result.get('execution_time', 0)
            success = result.get('success', False)
            
            total_events += events_count
            
            # Send real-time result
            if success and events_count > 0:
                await websocket.send_json({
                    "type": "scraper_completed",
                    "scraper": scraper_name.title(),
                    "events": events,
                    "count": events_count,
                    "execution_time": f"{execution_time:.2f}s",
                    "progress": int(scrapers_completed * 100 / 6),  # 6 scrapers expected
                    "total_events": total_events,
                    "timestamp": current_time,
                    "message": f"✅ {scraper_name.title()}: {events_count} eventos"
                })
                
                logger.info(f"📡 WebSocket - {scraper_name.title()}: {events_count} eventos enviados instantáneamente")
                
            elif success:
                # Scraper completed but no events
                await websocket.send_json({
                    "type": "scraper_empty",
                    "scraper": scraper_name.title(),
                    "count": 0,
                    "execution_time": f"{execution_time:.2f}s",
                    "progress": int(scrapers_completed * 100 / 6),
                    "total_events": total_events,
                    "timestamp": current_time,
                    "message": f"⚪ {scraper_name.title()}: Sin eventos"
                })
                
            else:
                # Scraper failed
                error_msg = result.get('error', 'Error desconocido')
                await websocket.send_json({
                    "type": "scraper_error",
                    "scraper": scraper_name.title(),
                    "error": error_msg,
                    "execution_time": f"{execution_time:.2f}s",
                    "progress": int(scrapers_completed * 100 / 6),
                    "total_events": total_events,
                    "timestamp": current_time,
                    "message": f"❌ {scraper_name.title()}: Error"
                })
                
                logger.warning(f"❌ WebSocket - {scraper_name.title()}: {error_msg}")
        
        # 3. Completion summary
        total_time = time.time() - start_time
        
        await websocket.send_json({
            "type": "search_completed",
            "total_events": total_events,
            "scrapers_completed": scrapers_completed,
            "total_time": f"{total_time:.2f}s",
            "first_result_time": f"{first_result_time:.2f}s" if first_result_time else "0s",
            "progress": 100,
            "message": f"🎯 Completado: {total_events} eventos de {scrapers_completed} scrapers",
            "performance_stats": {
                "streaming_efficiency": first_result_time < 2.0 if first_result_time else False,
                "average_events_per_scraper": round(total_events / max(scrapers_completed, 1), 1),
                "total_duration": f"{total_time:.2f}s"
            }
        })
        
        logger.info(f"🏁 WebSocket - Streaming completado: {total_events} eventos, {scrapers_completed} scrapers, {total_time:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Error en WebSocket streaming: {e}")
        await websocket.send_json({
            "type": "streaming_error",
            "message": f"❌ Error en streaming: {str(e)}",
            "error": str(e),
            "progress": 100
        })

async def websocket_recommend_streaming(websocket: WebSocket, location: str):
    """
    💡 WEBSOCKET PARA RECOMENDACIONES STREAMING
    
    Busca eventos en ciudades aledañas usando streaming real
    """
    
    try:
        await websocket.send_json({
            "type": "recommend_started",
            "message": f"💡 Buscando recomendaciones cerca de {location}",
            "location": location
        })
        
        # 🗺️ OBTENER CIUDADES ALEDAÑAS REALES DEL SERVICIO
        from services.nearby_cities_service import nearby_cities_service
        
        nearby_locations = nearby_cities_service.get_cached_nearby_cities(location)
        
        if not nearby_locations:
            # Si no están en cache, generarlas
            nearby_locations = await nearby_cities_service.get_nearby_cities(location)
            logger.info(f"🗺️ Ciudades aledañas generadas para {location}: {nearby_locations}")
        else:
            logger.info(f"🗺️ Ciudades aledañas desde cache para {location}: {nearby_locations}")
        
        # Fallback si no se encontraron ciudades aledañas
        if not nearby_locations:
            nearby_locations = [f"{location} Centro", f"{location} Norte", f"{location} Sur"]
            logger.warning(f"⚠️ Usando ubicaciones fallback para {location}")
        
        await websocket.send_json({
            "type": "recommend_cities_detected",
            "nearby_cities": nearby_locations,
            "message": f"🏙️ Ciudades detectadas: {', '.join(nearby_locations)}"
        })
        
        factory = IndustrialFactory()
        total_recommendations = 0
        
        for i, nearby_location in enumerate(nearby_locations):
            await websocket.send_json({
                "type": "recommend_location_started",
                "location": nearby_location,
                "progress": int(i * 100 / len(nearby_locations)),
                "message": f"🔍 Buscando en {nearby_location}..."
            })
            
            # Use streaming for each nearby location with limited events
            location_events = 0
            async for result in factory.execute_streaming(
                location=nearby_location,
                limit=3  # Solo 3 eventos por scraper en recomendaciones
            ):
                events = result.get('events', [])
                if events:
                    location_events += len(events)
                    total_recommendations += len(events)
                    
                    await websocket.send_json({
                        "type": "recommend_events",
                        "location": nearby_location,
                        "scraper": result.get('scraper', '').title(),
                        "events": events,
                        "count": len(events),
                        "total_recommendations": total_recommendations,
                        "message": f"💡 {len(events)} recomendaciones de {nearby_location}"
                    })
            
            # Limit total recommendations to avoid overwhelming
            if total_recommendations >= 30:
                break
                
        await websocket.send_json({
            "type": "recommend_completed",
            "total_recommendations": total_recommendations,
            "locations_searched": len(nearby_locations),
            "progress": 100,
            "message": f"💡 {total_recommendations} recomendaciones encontradas"
        })
        
        logger.info(f"💡 WebSocket - Recomendaciones completadas: {total_recommendations} eventos")
        
    except Exception as e:
        logger.error(f"❌ Error en WebSocket recomendaciones: {e}")
        await websocket.send_json({
            "type": "recommend_error",
            "message": f"❌ Error en recomendaciones: {str(e)}",
            "error": str(e)
        })