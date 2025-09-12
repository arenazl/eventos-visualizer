"""
Schemas para respuestas de la API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from api.v1.schemas.events import EventSchema, EventListSchema


class BaseResponse(BaseModel):
    """
    Response base para todas las respuestas de la API
    """
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Timestamp de la respuesta")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class SuccessResponse(BaseResponse):
    """
    Response genérica exitosa
    """
    message: str = Field(..., description="Mensaje de éxito")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "timestamp": "2025-09-06T10:30:00",
                "data": {"processed": 100}
            }
        }


class ErrorResponse(BaseResponse):
    """
    Response para errores
    """
    success: bool = Field(False, description="Siempre False para errores")
    error: str = Field(..., description="Mensaje de error")
    error_code: Optional[str] = Field(None, description="Código de error específico")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid parameters provided",
                "error_code": "INVALID_PARAMS",
                "timestamp": "2025-09-06T10:30:00",
                "details": {"field": "location", "message": "Location is required"}
            }
        }


class HealthResponse(BaseResponse):
    """
    Response para health check
    """
    status: str = Field(..., description="Estado del sistema: healthy, degraded, unhealthy")
    version: str = Field(..., description="Versión de la API")
    environment: str = Field(..., description="Ambiente: development, staging, production")
    services: Dict[str, str] = Field(..., description="Estado de servicios individuales")
    uptime: Optional[str] = Field(None, description="Tiempo activo del sistema")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "status": "healthy",
                "version": "1.0.0",
                "environment": "development",
                "services": {
                    "database": "healthy",
                    "scrapers": "healthy",
                    "cache": "healthy"
                },
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class EventsResponse(BaseResponse):
    """
    Response para endpoints de eventos
    """
    events: List[EventSchema] = Field(..., description="Lista de eventos")
    total: int = Field(..., description="Número total de eventos encontrados", ge=0)
    location: Optional[str] = Field(None, description="Ubicación consultada")
    source: Optional[str] = Field(None, description="Fuente de los datos")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filtros aplicados en la búsqueda")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "events": [
                    {
                        "id": "event_123",
                        "title": "Concierto de Rock",
                        "start_date": "2025-09-15T20:00:00",
                        "venue": "Teatro Principal",
                        "category": "música",
                        "source": "eventbrite"
                    }
                ],
                "total": 1,
                "location": "Buenos Aires",
                "source": "eventbrite",
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class EventDetailResponse(BaseResponse):
    """
    Response para detalle de un evento específico
    """
    event: EventSchema = Field(..., description="Detalles completos del evento")
    related_events: Optional[List[EventSchema]] = Field(None, description="Eventos relacionados")
    recommendations: Optional[List[EventSchema]] = Field(None, description="Recomendaciones basadas en este evento")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "event": {
                    "id": "event_123",
                    "title": "Concierto de Rock Nacional",
                    "description": "Gran concierto con bandas locales",
                    "start_date": "2025-09-15T20:00:00",
                    "venue": "Luna Park",
                    "category": "música"
                },
                "related_events": [],
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class SearchResponse(BaseResponse):
    """
    Response para búsquedas (inteligentes y regulares)
    """
    query: str = Field(..., description="Query de búsqueda original")
    processed_query: Optional[Dict[str, Any]] = Field(None, description="Query procesada por IA")
    results: List[EventSchema] = Field(..., description="Resultados de la búsqueda")
    total: int = Field(..., description="Total de resultados encontrados", ge=0)
    location: Optional[str] = Field(None, description="Ubicación consultada")
    search_time_ms: Optional[float] = Field(None, description="Tiempo de búsqueda en millisegundos")
    ai_enhanced: bool = Field(False, description="Si la búsqueda fue mejorada con IA")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "query": "conciertos de rock esta semana",
                "processed_query": {
                    "keywords": ["conciertos", "rock"],
                    "time_filter": "this_week",
                    "category": "música"
                },
                "results": [],
                "total": 5,
                "location": "Buenos Aires",
                "search_time_ms": 145.2,
                "ai_enhanced": True,
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class SourcesResponse(BaseResponse):
    """
    Response para endpoints de fuentes específicas
    """
    source: str = Field(..., description="Fuente consultada")
    events: List[EventSchema] = Field(..., description="Eventos de la fuente")
    total: int = Field(..., description="Total de eventos de la fuente", ge=0)
    location: Optional[str] = Field(None, description="Ubicación consultada")
    api_status: Optional[str] = Field(None, description="Estado de la API externa")
    rate_limit_remaining: Optional[int] = Field(None, description="Requests restantes en rate limit")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "source": "eventbrite",
                "events": [],
                "total": 12,
                "location": "Buenos Aires",
                "api_status": "healthy",
                "rate_limit_remaining": 95,
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class CategoriesResponse(BaseResponse):
    """
    Response para listado de categorías
    """
    categories: List[Dict[str, str]] = Field(..., description="Lista de categorías disponibles")
    total: int = Field(..., description="Número total de categorías")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "categories": [
                    {"id": "musica", "name": "Música", "icon": "🎵"},
                    {"id": "deportes", "name": "Deportes", "icon": "⚽"}
                ],
                "total": 2,
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class WebSocketStatsResponse(BaseResponse):
    """
    Response para estadísticas de WebSocket
    """
    websocket_stats: Dict[str, Any] = Field(..., description="Estadísticas de conexiones WebSocket")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "websocket_stats": {
                    "total_connections": 5,
                    "connections_by_location": {
                        "Buenos Aires": 3,
                        "Madrid": 2
                    },
                    "active_clients": ["client_1", "client_2"]
                },
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class ParallelSearchResponse(BaseResponse):
    """
    Response para búsqueda paralela en múltiples fuentes
    """
    location: str = Field(..., description="Ubicación consultada")
    sources: List[str] = Field(..., description="Fuentes consultadas")
    results: List[EventSchema] = Field(..., description="Resultados combinados")
    total: int = Field(..., description="Total de eventos encontrados", ge=0)
    merged: bool = Field(..., description="Si los resultados fueron combinados/deduplicados")
    source_stats: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Estadísticas por fuente")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "location": "Buenos Aires",
                "sources": ["eventbrite", "facebook", "ticketmaster"],
                "results": [],
                "total": 25,
                "merged": True,
                "source_stats": {
                    "eventbrite": {"count": 10, "response_time_ms": 250},
                    "facebook": {"count": 8, "response_time_ms": 180},
                    "ticketmaster": {"count": 7, "response_time_ms": 320}
                },
                "timestamp": "2025-09-06T10:30:00"
            }
        }


class BroadcastResponse(BaseResponse):
    """
    Response para broadcast de WebSocket
    """
    message: str = Field(..., description="Mensaje de confirmación")
    recipients: Union[str, int] = Field(..., description="Destinatarios del broadcast")
    broadcast_type: str = Field(..., description="Tipo de broadcast: all, location, specific")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Broadcast sent successfully",
                "recipients": "all",
                "broadcast_type": "all",
                "timestamp": "2025-09-06T10:30:00"
            }
        }