"""
🚀 API V1 ENDPOINTS
SSE Streaming for real-time event search
"""

from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
import json
import asyncio
import os
from datetime import datetime

# Import Gemini for intent detection
import google.generativeai as genai

# Import scraper discovery
from scrapers.discovery import discovery
from scrapers.base import Event

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA1UUEuBJVLYBAMGWXeneEJkmva7fEv-F8")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize discovery on startup
discovery.discover_all()


@router.post("/intent")
async def detect_intent(request: Request):
    """
    Detecta la intención del usuario y extrae ubicación usando Gemini
    
    Request body:
    {
        "query": "eventos en Villa Gesell para este fin de semana"
    }
    
    Response:
    {
        "location": {
            "city": "Villa Gesell",
            "state": "Buenos Aires",
            "country": "Argentina"
        },
        "intent": "search_events",
        "filters": {
            "date_range": "weekend",
            "categories": []
        }
    }
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Prompt para Gemini
        prompt = f"""
        Analiza esta consulta sobre eventos y extrae la información:
        
        Consulta: "{query}"
        
        Responde SOLO en formato JSON con esta estructura exacta:
        {{
            "location": {{
                "city": "nombre de la ciudad",
                "state": "provincia o estado",
                "country": "país"
            }},
            "intent": "search_events",
            "filters": {{
                "date_range": "today|tomorrow|weekend|week|month|specific_date",
                "categories": ["música", "deportes", "cultura", "tech", "fiesta"],
                "keywords": ["palabras clave extraídas"]
            }}
        }}
        
        Si no se menciona ubicación, usa null para city/state/country.
        Si no hay filtros específicos, usa arrays vacíos y "all" para date_range.
        """
        
        # Llamar a Gemini
        response = model.generate_content(prompt)
        
        # Parsear respuesta
        try:
            # Limpiar respuesta (quitar markdown si existe)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            
            # Validar estructura
            if "location" not in result:
                result["location"] = {"city": None, "state": None, "country": None}
            if "intent" not in result:
                result["intent"] = "search_events"
            if "filters" not in result:
                result["filters"] = {"date_range": "all", "categories": [], "keywords": []}
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON de Gemini: {e}")
            print(f"Respuesta raw: {response.text}")
            
            # Fallback: búsqueda simple
            return {
                "location": {
                    "city": query,
                    "state": None,
                    "country": None
                },
                "intent": "search_events",
                "filters": {
                    "date_range": "all",
                    "categories": [],
                    "keywords": []
                }
            }
            
    except Exception as e:
        print(f"❌ Error en intent detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_events_sse(
    location: str = Query(..., description="Ubicación para buscar eventos"),
    limit: int = Query(10, description="Límite de eventos por scraper"),
    categories: Optional[str] = Query(None, description="Categorías separadas por comas")
):
    """
    Busca eventos usando SSE (Server-Sent Events) para streaming en tiempo real
    
    Ejemplo: /api/v1/search?location=Villa Gesell, Buenos Aires, Argentina&limit=10
    
    Response: SSE stream con eventos en tiempo real
    """
    
    async def event_generator():
        """Generador de eventos SSE"""
        try:
            # Enviar evento inicial
            yield f"data: {json.dumps({'type': 'start', 'message': f'Buscando eventos en {location}...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Obtener scrapers para la ubicación
            scrapers = discovery.get_scrapers_for_location(location)
            
            if not scrapers:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No hay scrapers disponibles para esta ubicación'})}\n\n"
                return
            
            # Informar cantidad de scrapers
            yield f"data: {json.dumps({'type': 'info', 'message': f'Consultando {len(scrapers)} fuentes de eventos...', 'scrapers': [s.name for s in scrapers]})}\n\n"
            
            # Crear tareas para cada scraper
            tasks = []
            scraper_instances = []
            
            for scraper_class in scrapers:
                try:
                    scraper = scraper_class()
                    scraper_instances.append(scraper)
                    task = asyncio.create_task(
                        _run_scraper_with_timeout(scraper, location, limit)
                    )
                    tasks.append(task)
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'scraper': scraper_class.name, 'message': str(e)})}\n\n"
            
            # Procesar resultados conforme van llegando
            completed_count = 0
            total_events = 0
            
            while tasks:
                # Esperar a que termine alguna tarea
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    tasks.remove(task)
                    completed_count += 1
                    
                    try:
                        scraper_index = list(done).index(task)
                        scraper = scraper_instances[scraper_index] if scraper_index < len(scraper_instances) else None
                        scraper_name = scraper.name if scraper else "unknown"
                        
                        result = await task
                        
                        if isinstance(result, Exception):
                            # Error en el scraper
                            yield f"data: {json.dumps({'type': 'scraper_error', 'scraper': scraper_name, 'error': str(result)})}\n\n"
                        elif result:
                            # Eventos encontrados
                            events_data = []
                            for event in result:
                                if isinstance(event, Event):
                                    events_data.append(event.model_dump())
                                    total_events += 1
                            
                            if events_data:
                                yield f"data: {json.dumps({'type': 'events', 'scraper': scraper_name, 'events': events_data, 'count': len(events_data)})}\n\n"
                            else:
                                yield f"data: {json.dumps({'type': 'no_events', 'scraper': scraper_name, 'message': 'No se encontraron eventos'})}\n\n"
                        else:
                            # Sin resultados
                            yield f"data: {json.dumps({'type': 'no_events', 'scraper': scraper_name, 'message': 'No se encontraron eventos'})}\n\n"
                            
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'Error procesando resultado: {str(e)}'})}\n\n"
                    
                    # Enviar progreso
                    progress = (completed_count / len(scraper_instances)) * 100 if scraper_instances else 100
                    yield f"data: {json.dumps({'type': 'progress', 'completed': completed_count, 'total': len(scraper_instances), 'percentage': progress})}\n\n"
            
            # Enviar resumen final
            yield f"data: {json.dumps({'type': 'complete', 'message': f'Búsqueda completada. {total_events} eventos encontrados de {completed_count} fuentes.', 'total_events': total_events})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Error general: {str(e)}'})}\n\n"
    
    # Retornar SSE stream
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no"  # Desactivar buffering en nginx
        }
    )


@router.post("/recommend")
async def recommend_events(request: Request):
    """
    Recomienda eventos basados en preferencias del usuario (futuro)
    
    Request body:
    {
        "location": "Villa Gesell, Buenos Aires, Argentina",
        "preferences": ["música", "deportes"],
        "history": []
    }
    
    Response:
    {
        "recommendations": [Event, ...],
        "reasoning": "Basado en tu interés en música y deportes..."
    }
    """
    try:
        data = await request.json()
        location = data.get("location", "")
        preferences = data.get("preferences", [])
        
        if not location:
            raise HTTPException(status_code=400, detail="Location is required")
        
        # Por ahora, simplemente buscar eventos y filtrar por preferencias
        results = await discovery.run_scrapers_parallel(location, limit=20)
        
        all_events = []
        for scraper_events in results.values():
            all_events.extend(scraper_events)
        
        # Filtrar por preferencias si hay
        if preferences:
            filtered_events = []
            for event in all_events:
                # Verificar si alguna preferencia coincide con la categoría
                if any(pref.lower() in str(event.category).lower() for pref in preferences):
                    filtered_events.append(event)
                # O en el título/descripción
                elif any(pref.lower() in (event.title + " " + (event.description or "")).lower() for pref in preferences):
                    filtered_events.append(event)
            
            all_events = filtered_events
        
        # Limitar a 10 recomendaciones
        recommendations = all_events[:10]
        
        return {
            "recommendations": [e.model_dump() if hasattr(e, 'model_dump') else e for e in recommendations],
            "reasoning": f"Basado en tu búsqueda en {location}" + (f" y tu interés en {', '.join(preferences)}" if preferences else ""),
            "total_found": len(all_events)
        }
        
    except Exception as e:
        print(f"❌ Error en recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_scraper_with_timeout(scraper, location: str, limit: int):
    """
    Ejecuta un scraper con timeout y manejo de errores
    """
    try:
        timeout = getattr(scraper, 'timeout', 10)
        
        async with asyncio.timeout(timeout):
            # Ejecutar scraping
            raw_data = await scraper.scrape(location, limit)
            
            # Normalizar output
            events = scraper.normalize_output(raw_data)
            
            return events
            
    except asyncio.TimeoutError:
        return Exception(f"Timeout después de {timeout}s")
    except Exception as e:
        return Exception(str(e))


@router.get("/scrapers")
async def list_scrapers():
    """
    Lista todos los scrapers disponibles y su estado
    """
    scrapers_info = []
    
    for name, scraper_class in discovery.scrapers.items():
        info = {
            "name": name,
            "class": scraper_class.__name__,
            "enabled": getattr(scraper_class, 'enabled', True),
            "priority": getattr(scraper_class, 'priority', 999),
            "timeout": getattr(scraper_class, 'timeout', 10),
            "type": "global" if name in discovery.global_scrapers else "regional/local"
        }
        scrapers_info.append(info)
    
    # Ordenar por prioridad
    scrapers_info.sort(key=lambda x: x['priority'])
    
    return {
        "total": len(scrapers_info),
        "scrapers": scrapers_info
    }