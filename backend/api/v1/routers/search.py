"""
Router para endpoints de búsqueda inteligente
"""
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any, Union
import logging
import asyncio
import json
from datetime import datetime
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from api.dependencies import (
    get_common_params, 
    CommonParams,
    get_ai_service,
    get_pattern_service
)

logger = logging.getLogger(__name__)

router = APIRouter()


class SmartSearchRequest(BaseModel):
    """
    Modelo para búsqueda inteligente
    """
    query: str = Field(..., description="Consulta en lenguaje natural")
    location: Optional[str] = Field(None, description="Ciudad o ubicación")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros adicionales")
    limit: Optional[int] = Field(20, description="Número máximo de resultados")
    ai_enabled: bool = Field(True, description="Usar IA para mejorar búsqueda")


class ParallelSearchRequest(BaseModel):
    """
    Modelo para búsqueda paralela en múltiples fuentes
    """
    location: str = Field(..., description="Ciudad para búsqueda")
    sources: List[str] = Field(default=["eventbrite", "facebook", "ticketmaster"], description="Fuentes a consultar")
    timeout: Optional[int] = Field(10, description="Timeout en segundos")
    merge_results: bool = Field(True, description="Combinar resultados similares")


@router.post("/smart/search")
async def smart_search(
    request: SmartSearchRequest,
    ai_service = Depends(get_ai_service),
    pattern_service = Depends(get_pattern_service)
):
    """
    Búsqueda inteligente usando procesamiento de lenguaje natural
    """
    try:
        logger.info(f"🧠 Smart search: '{request.query}' in {request.location}")
        
        # Procesar query con IA si está disponible
        processed_query = await _process_smart_query(
            request.query,
            ai_service,
            request.location
        )
        
        # Ejecutar búsqueda mejorada
        results = await _execute_smart_search(
            processed_query,
            request.location,
            request.filters or {},
            request.limit
        )
        
        # Rankear resultados por relevancia
        ranked_results = await _rank_search_results(
            results,
            request.query,
            pattern_service
        )
        
        return {
            "success": True,
            "query": request.query,
            "processed_query": processed_query,
            "location": request.location,
            "results": ranked_results,
            "total": len(ranked_results),
            "ai_enhanced": request.ai_enabled and ai_service is not None,
            "search_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Smart search error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "query": request.query,
                "results": []
            }
        )


@router.get("/events/smart-search")
async def smart_search_get(
    q: str = Query(..., description="Consulta de búsqueda"),
    location: Optional[str] = Query(None, description="Ciudad"),
    category: Optional[str] = Query(None, description="Categoría"),
    limit: int = Query(20, description="Límite de resultados")
):
    """
    Versión GET de la búsqueda inteligente para compatibilidad
    """
    try:
        # Convertir a request model
        search_request = SmartSearchRequest(
            query=q,
            location=location,
            filters={"category": category} if category else None,
            limit=limit
        )
        
        # Reusar lógica del POST
        return await smart_search(search_request)
        
    except Exception as e:
        logger.error(f"Smart search GET error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "query": q,
                "results": []
            }
        )


@router.get("/parallel/search")
async def parallel_search(
    location: str = Query(..., description="Ciudad para búsqueda"),
    sources: str = Query("eventbrite,facebook,ticketmaster", description="Fuentes separadas por coma"),
    timeout: int = Query(10, description="Timeout en segundos"),
    merge: bool = Query(True, description="Combinar resultados similares")
):
    """
    Búsqueda paralela en múltiples fuentes simultáneamente
    """
    try:
        logger.info(f"⚡ Parallel search in {location} from sources: {sources}")
        
        # Parsear fuentes
        source_list = [s.strip() for s in sources.split(",")]
        
        # Crear request
        search_request = ParallelSearchRequest(
            location=location,
            sources=source_list,
            timeout=timeout,
            merge_results=merge
        )
        
        # Ejecutar búsquedas paralelas
        results = await _execute_parallel_search(search_request)
        
        return {
            "success": True,
            "location": location,
            "sources": source_list,
            "results": results,
            "total": len(results),
            "merged": merge,
            "search_time": datetime.now().isoformat()
        }
        
    except asyncio.TimeoutError:
        logger.warning(f"Parallel search timeout for {location}")
        return JSONResponse(
            status_code=408,
            content={
                "success": False,
                "error": "Search timeout - some sources may be slow",
                "location": location,
                "partial_results": []
            }
        )
    except Exception as e:
        logger.error(f"Parallel search error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "location": location,
                "results": []
            }
        )


@router.get("/barcelona")
async def search_barcelona_events(
    limit: int = Query(15, description="Número de eventos")
):
    """
    Búsqueda específica para Barcelona (endpoint especial)
    """
    try:
        logger.info(f"🏛️ Fetching Barcelona events (limit: {limit})")
        
        # Búsqueda optimizada para Barcelona
        events = await _fetch_barcelona_events(limit)
        
        return {
            "success": True,
            "city": "Barcelona",
            "events": events,
            "total": len(events),
            "country": "España",
            "timezone": "Europe/Madrid",
            "special_endpoint": True
        }
        
    except Exception as e:
        logger.error(f"Barcelona search error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "city": "Barcelona",
                "events": []
            }
        )


# Funciones helper para lógica de búsqueda

async def _process_smart_query(query: str, ai_service, location: Optional[str]) -> Dict[str, Any]:
    """
    Procesar query usando IA para extraer intención y parámetros
    """
    if not ai_service:
        # Procesamiento básico sin IA
        return {
            "original": query,
            "keywords": query.lower().split(),
            "intent": "search_events",
            "extracted_filters": {}
        }
    
    try:
        # Usar AI service para procesamiento avanzado
        processed = await ai_service.process_search_query(query, location)
        return processed
    except Exception as e:
        logger.warning(f"AI processing failed, using basic: {e}")
        return {
            "original": query,
            "keywords": query.lower().split(),
            "intent": "search_events",
            "extracted_filters": {},
            "ai_error": str(e)
        }


async def _execute_smart_search(
    processed_query: Dict[str, Any], 
    location: Optional[str], 
    filters: Dict[str, Any],
    limit: int
) -> List[Dict[str, Any]]:
    """
    Ejecutar búsqueda basada en query procesada
    """
    # Combinar filtros de query procesada y filtros explícitos
    all_filters = {**processed_query.get("extracted_filters", {}), **filters}
    
    # Simular búsqueda inteligente
    keywords = processed_query.get("keywords", [])
    
    # Generar eventos relevantes basados en keywords
    smart_results = []
    
    for keyword in keywords[:3]:  # Top 3 keywords
        if keyword in ["música", "concierto", "festival"]:
            smart_results.extend(_generate_music_events(location, keyword))
        elif keyword in ["arte", "cultura", "exposición"]:
            smart_results.extend(_generate_cultural_events(location, keyword))
        elif keyword in ["tech", "tecnología", "programación"]:
            smart_results.extend(_generate_tech_events(location, keyword))
        elif keyword in ["deporte", "fútbol", "running"]:
            smart_results.extend(_generate_sports_events(location, keyword))
    
    # Si no hay resultados específicos, eventos generales
    if not smart_results:
        smart_results = _generate_general_events(location)
    
    return smart_results[:limit]


async def _rank_search_results(
    results: List[Dict[str, Any]], 
    original_query: str,
    pattern_service
) -> List[Dict[str, Any]]:
    """
    Rankear resultados por relevancia
    """
    if not pattern_service:
        return results
    
    try:
        # Usar pattern service para scoring
        ranked = await pattern_service.rank_events_by_relevance(results, original_query)
        return ranked
    except Exception as e:
        logger.warning(f"Ranking failed: {e}")
        return results


async def _execute_parallel_search(request: ParallelSearchRequest) -> List[Dict[str, Any]]:
    """
    Ejecutar búsquedas paralelas en múltiples fuentes
    """
    tasks = []
    
    for source in request.sources:
        if source == "eventbrite":
            tasks.append(_search_eventbrite_parallel(request.location))
        elif source == "facebook":
            tasks.append(_search_facebook_parallel(request.location))
        elif source == "ticketmaster":
            tasks.append(_search_ticketmaster_parallel(request.location))
        elif source == "meetup":
            tasks.append(_search_meetup_parallel(request.location))
    
    # Ejecutar en paralelo con timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=request.timeout
        )
        
        # Combinar resultados exitosos
        all_events = []
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif not isinstance(result, Exception):
                logger.warning(f"Unexpected result type: {type(result)}")
        
        # Merge similares si está habilitado
        if request.merge_results:
            all_events = _merge_similar_events(all_events)
        
        return all_events
        
    except asyncio.TimeoutError:
        logger.error(f"Parallel search timeout after {request.timeout}s")
        raise


# Funciones helper para generar eventos por categoría

def _generate_music_events(location: Optional[str], keyword: str) -> List[Dict[str, Any]]:
    """Generar eventos de música"""
    location = location or "Buenos Aires"
    return [
        {
            "id": f"music_{keyword}_1",
            "title": f"Festival de {keyword.title()} - {location}",
            "description": f"Gran evento de {keyword} con artistas destacados",
            "start_date": "2025-09-28T20:00:00",
            "venue": f"Teatro Principal - {location}",
            "category": "música",
            "price": 80.0,
            "source": "smart_search",
            "relevance_score": 0.9,
            "matched_keywords": [keyword]
        }
    ]


def _generate_cultural_events(location: Optional[str], keyword: str) -> List[Dict[str, Any]]:
    """Generar eventos culturales"""
    location = location or "Buenos Aires"
    return [
        {
            "id": f"cultural_{keyword}_1",
            "title": f"Exposición de {keyword.title()} - {location}",
            "description": f"Muestra cultural de {keyword}",
            "start_date": "2025-09-26T15:00:00",
            "venue": f"Museo de {location}",
            "category": "cultural",
            "price": 0,
            "is_free": True,
            "source": "smart_search",
            "relevance_score": 0.85,
            "matched_keywords": [keyword]
        }
    ]


def _generate_tech_events(location: Optional[str], keyword: str) -> List[Dict[str, Any]]:
    """Generar eventos tech"""
    location = location or "Buenos Aires"
    return [
        {
            "id": f"tech_{keyword}_1",
            "title": f"Meetup de {keyword.title()} - {location}",
            "description": f"Encuentro sobre {keyword} y desarrollo",
            "start_date": "2025-09-25T19:00:00",
            "venue": f"Co-working {location}",
            "category": "tech",
            "price": 0,
            "is_free": True,
            "source": "smart_search",
            "relevance_score": 0.8,
            "matched_keywords": [keyword]
        }
    ]


def _generate_sports_events(location: Optional[str], keyword: str) -> List[Dict[str, Any]]:
    """Generar eventos deportivos"""
    location = location or "Buenos Aires"
    return [
        {
            "id": f"sports_{keyword}_1",
            "title": f"Evento de {keyword.title()} - {location}",
            "description": f"Competencia de {keyword}",
            "start_date": "2025-09-29T10:00:00",
            "venue": f"Estadio de {location}",
            "category": "deportes",
            "price": 45.0,
            "source": "smart_search",
            "relevance_score": 0.75,
            "matched_keywords": [keyword]
        }
    ]


def _generate_general_events(location: Optional[str]) -> List[Dict[str, Any]]:
    """Generar eventos generales cuando no hay match específico"""
    location = location or "Buenos Aires"
    return [
        {
            "id": "general_1",
            "title": f"Evento Destacado - {location}",
            "description": "Evento popular en la ciudad",
            "start_date": "2025-09-30T18:00:00",
            "venue": f"Centro de {location}",
            "category": "general",
            "price": 25.0,
            "source": "smart_search",
            "relevance_score": 0.5
        }
    ]


# Funciones para búsqueda paralela por fuente

async def _search_eventbrite_parallel(location: str) -> List[Dict[str, Any]]:
    """Búsqueda paralela en Eventbrite"""
    await asyncio.sleep(0.5)  # Simular latencia
    return [
        {
            "id": "eb_parallel_1",
            "title": f"Eventbrite Event - {location}",
            "source": "eventbrite",
            "location": location
        }
    ]


async def _search_facebook_parallel(location: str) -> List[Dict[str, Any]]:
    """Búsqueda paralela en Facebook"""
    await asyncio.sleep(0.8)  # Simular latencia
    return [
        {
            "id": "fb_parallel_1", 
            "title": f"Facebook Event - {location}",
            "source": "facebook",
            "location": location
        }
    ]


async def _search_ticketmaster_parallel(location: str) -> List[Dict[str, Any]]:
    """Búsqueda paralela en Ticketmaster"""
    await asyncio.sleep(0.3)  # Simular latencia
    return [
        {
            "id": "tm_parallel_1",
            "title": f"Ticketmaster Event - {location}",
            "source": "ticketmaster", 
            "location": location
        }
    ]


async def _search_meetup_parallel(location: str) -> List[Dict[str, Any]]:
    """Búsqueda paralela en Meetup"""
    await asyncio.sleep(0.6)  # Simular latencia
    return [
        {
            "id": "meetup_parallel_1",
            "title": f"Meetup Event - {location}",
            "source": "meetup",
            "location": location
        }
    ]


async def _fetch_barcelona_events(limit: int) -> List[Dict[str, Any]]:
    """Eventos específicos para Barcelona"""
    barcelona_events = [
        {
            "id": "bcn_sagrada_1",
            "title": "Tour Nocturno Sagrada Familia",
            "description": "Visita especial nocturna a la Sagrada Familia",
            "start_date": "2025-09-27T20:30:00",
            "venue": "Sagrada Familia",
            "category": "cultural",
            "price": 35.0,
            "currency": "EUR",
            "source": "barcelona_tourism"
        },
        {
            "id": "bcn_music_1",
            "title": "Festa Major de Gràcia",
            "description": "Festival tradicional del barrio de Gràcia",
            "start_date": "2025-09-28T17:00:00",
            "venue": "Barrio de Gràcia",
            "category": "música",
            "price": 0,
            "is_free": True,
            "source": "barcelona_festivals"
        },
        {
            "id": "bcn_food_1",
            "title": "Mercado de La Boquería - Tour Gastronómico",
            "description": "Tour culinario por el famoso mercado",
            "start_date": "2025-09-26T11:00:00",
            "venue": "La Boquería",
            "category": "gastronomía",
            "price": 45.0,
            "currency": "EUR",
            "source": "barcelona_food"
        }
    ]
    
    return barcelona_events[:limit]


def _merge_similar_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Combinar eventos similares para evitar duplicados
    """
    # Implementación básica - en el futuro usar algoritmos más sofisticados
    unique_events = []
    seen_titles = set()
    
    for event in events:
        title = event.get("title", "").lower()
        if title not in seen_titles:
            unique_events.append(event)
            seen_titles.add(title)
    
    return unique_events