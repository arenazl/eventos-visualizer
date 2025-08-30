"""
API Endpoints para el Sistema de Agregación de Eventos
Expone todos los eventos normalizados de múltiples fuentes
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
import logging

# Importar el servicio agregador
try:
    from services.event_aggregator import EventAggregatorService
except ImportError:
    import sys
    sys.path.append('/mnt/c/Code/eventos-visualizer/backend')
    from services.event_aggregator import EventAggregatorService

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/api/events",
    tags=["events"],
    responses={404: {"description": "Not found"}}
)

# Inicializar servicio agregador
aggregator = EventAggregatorService()

@router.get("/search/intent")
async def search_events_with_intent(
    q: str = Query(..., description="Búsqueda natural del usuario (ej: 'Buenos Aires', 'electrónica', 'fiesta techno este fin de semana')")
):
    """
    Busca eventos usando reconocimiento de intención con IA.
    Interpreta el input del usuario y adapta los parámetros para cada API.
    
    Ejemplos de búsqueda:
    - "Buenos Aires" - Busca todos los eventos en Buenos Aires
    - "electrónica" - Busca eventos de música electrónica
    - "fiesta techno en Palermo" - Busca fiestas techno en el barrio Palermo
    - "conciertos este fin de semana" - Busca conciertos próximos
    - "eventos gratis en México" - Busca eventos gratuitos en México
    """
    try:
        logger.info(f"🤖 Búsqueda con intención: {q}")
        
        # Usar el servicio de reconocimiento de intención
        result = await aggregator.fetch_events_with_intent(q)
        
        return {
            "success": True,
            "query": q,
            "intent": result.get('intent'),
            "total": result.get('total', 0),
            "events": result.get('events', []),
            "stats": result.get('stats', {})
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda con intención: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_events(
    location: Optional[str] = Query(None, description="Ciudad o región (ej: Buenos Aires, México)"),
    lat: Optional[float] = Query(None, description="Latitud del usuario"),
    lon: Optional[float] = Query(None, description="Longitud del usuario"),
    radius: Optional[int] = Query(None, description="Radio de búsqueda en km (30, 50, 500, 1000)"),
    category: Optional[str] = Query(None, description="Categoría de eventos (music, sports, cultural, etc)"),
    date_from: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="Límite de resultados"),
    offset: Optional[int] = Query(0, description="Offset para paginación")
):
    """
    Obtiene eventos agregados de múltiples fuentes:
    - Buenos Aires Data (eventos gratuitos Argentina)
    - Eventbrite (eventos LATAM)
    - Ticketek, Ticketmaster (próximamente)
    
    Features:
    - Geocodificación automática de ubicaciones
    - Búsqueda por radio geográfico
    - Imágenes generadas para eventos sin imagen
    - Deduplicación inteligente
    """
    try:
        # Parsear fechas si se proporcionan
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        
        if date_to:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
        
        # Obtener eventos del agregador
        result = await aggregator.fetch_all_events(
            location=location,
            user_lat=lat,
            user_lon=lon,
            radius_km=radius,
            category=category,
            date_from=parsed_date_from,
            date_to=parsed_date_to
        )
        
        # Aplicar paginación
        events = result['events'][offset:offset + limit]
        
        # Preparar respuesta
        response = {
            'success': True,
            'data': {
                'events': events,
                'total': result['total'],
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < result['total']
            },
            'metadata': result['metadata'],
            'stats': result['stats']
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error obteniendo eventos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_events(
    q: str = Query(..., description="Término de búsqueda"),
    location: Optional[str] = Query(None, description="Ciudad o región"),
    radius: Optional[int] = Query(50, description="Radio de búsqueda en km")
):
    """
    Busca eventos por texto en título y descripción
    """
    try:
        # Obtener todos los eventos
        result = await aggregator.fetch_all_events(location=location)
        
        # Filtrar por término de búsqueda
        q_lower = q.lower()
        filtered = [
            event for event in result['events']
            if q_lower in event.get('title', '').lower() or
               q_lower in event.get('description', '').lower() or
               q_lower in event.get('venue_name', '').lower()
        ]
        
        return {
            'success': True,
            'data': {
                'events': filtered[:50],  # Limitar a 50 resultados
                'total': len(filtered),
                'query': q
            }
        }
        
    except Exception as e:
        logger.error(f"Error buscando eventos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories():
    """
    Obtiene todas las categorías disponibles
    """
    return {
        'success': True,
        'data': aggregator.get_categories()
    }

@router.get("/locations")
async def get_popular_locations():
    """
    Obtiene ubicaciones populares en LATAM
    """
    locations = [
        # Argentina
        {'country': 'Argentina', 'city': 'Buenos Aires', 'lat': -34.6037, 'lon': -58.3816},
        {'country': 'Argentina', 'city': 'Córdoba', 'lat': -31.4201, 'lon': -64.1888},
        {'country': 'Argentina', 'city': 'Rosario', 'lat': -32.9442, 'lon': -60.6505},
        {'country': 'Argentina', 'city': 'Mendoza', 'lat': -32.8895, 'lon': -68.8458},
        
        # México
        {'country': 'México', 'city': 'Ciudad de México', 'lat': 19.4326, 'lon': -99.1332},
        {'country': 'México', 'city': 'Guadalajara', 'lat': 20.6597, 'lon': -103.3496},
        {'country': 'México', 'city': 'Monterrey', 'lat': 25.6866, 'lon': -100.3161},
        
        # Colombia
        {'country': 'Colombia', 'city': 'Bogotá', 'lat': 4.7110, 'lon': -74.0721},
        {'country': 'Colombia', 'city': 'Medellín', 'lat': 6.2442, 'lon': -75.5812},
        {'country': 'Colombia', 'city': 'Cali', 'lat': 3.4516, 'lon': -76.5320},
        
        # Chile
        {'country': 'Chile', 'city': 'Santiago', 'lat': -33.4489, 'lon': -70.6693},
        {'country': 'Chile', 'city': 'Valparaíso', 'lat': -33.0458, 'lon': -71.6197},
        
        # Brasil
        {'country': 'Brasil', 'city': 'São Paulo', 'lat': -23.5505, 'lon': -46.6333},
        {'country': 'Brasil', 'city': 'Rio de Janeiro', 'lat': -22.9068, 'lon': -43.1729},
        
        # Perú
        {'country': 'Perú', 'city': 'Lima', 'lat': -12.0464, 'lon': -77.0428},
        
        # Uruguay
        {'country': 'Uruguay', 'city': 'Montevideo', 'lat': -34.9011, 'lon': -56.1645},
    ]
    
    return {
        'success': True,
        'data': locations
    }

@router.get("/nearby")
async def get_nearby_events(
    lat: float = Query(..., description="Latitud del usuario"),
    lon: float = Query(..., description="Longitud del usuario"),
    radius: int = Query(50, description="Radio en km (default: 50)")
):
    """
    Obtiene eventos cercanos a las coordenadas del usuario
    """
    try:
        result = await aggregator.fetch_all_events(
            user_lat=lat,
            user_lon=lon,
            radius_km=radius
        )
        
        return {
            'success': True,
            'data': {
                'events': result['events'][:100],  # Limitar a 100 eventos
                'total': result['total'],
                'center': {'lat': lat, 'lon': lon},
                'radius_km': radius
            },
            'stats': result['stats']
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo eventos cercanos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upcoming")
async def get_upcoming_events(
    location: Optional[str] = Query(None, description="Ciudad o región"),
    days: int = Query(7, description="Número de días hacia adelante (default: 7)")
):
    """
    Obtiene eventos próximos en los siguientes N días
    """
    try:
        date_from = datetime.now()
        date_to = date_from + timedelta(days=days)
        
        result = await aggregator.fetch_all_events(
            location=location,
            date_from=date_from,
            date_to=date_to
        )
        
        return {
            'success': True,
            'data': {
                'events': result['events'],
                'total': result['total'],
                'date_range': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat(),
                    'days': days
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo eventos próximos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/free")
async def get_free_events(
    location: Optional[str] = Query(None, description="Ciudad o región")
):
    """
    Obtiene solo eventos gratuitos
    """
    try:
        result = await aggregator.fetch_all_events(location=location)
        
        # Filtrar solo eventos gratuitos
        free_events = [
            event for event in result['events']
            if event.get('is_free', False) or event.get('price', 1) == 0
        ]
        
        return {
            'success': True,
            'data': {
                'events': free_events[:100],  # Limitar a 100 eventos
                'total': len(free_events)
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo eventos gratuitos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{event_id}")
async def get_event_detail(
    event_id: str
):
    """
    Obtiene el detalle completo de un evento específico
    """
    try:
        event = await aggregator.get_event_by_id(event_id)
        
        if not event:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        return {
            'success': True,
            'data': event
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo detalle de evento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_stats_summary():
    """
    Obtiene estadísticas generales del sistema de agregación
    """
    try:
        # Obtener eventos de muestra para estadísticas
        result = await aggregator.fetch_all_events()
        
        # Calcular estadísticas
        categories_count = {}
        sources_count = {}
        cities_count = {}
        
        for event in result['events']:
            # Contar por categoría
            cat = event.get('category', 'unknown')
            categories_count[cat] = categories_count.get(cat, 0) + 1
            
            # Contar por fuente
            src = event.get('source', 'unknown')
            sources_count[src] = sources_count.get(src, 0) + 1
            
            # Contar por ciudad
            city = event.get('neighborhood', 'unknown')
            cities_count[city] = cities_count.get(city, 0) + 1
        
        return {
            'success': True,
            'data': {
                'total_events': result['total'],
                'categories': categories_count,
                'sources': sources_count,
                'top_cities': dict(sorted(cities_count.items(), 
                                         key=lambda x: x[1], 
                                         reverse=True)[:10]),
                'stats': result['stats']
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))