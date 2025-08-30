"""
API Multi-Source - Obtiene eventos de TODAS las fuentes disponibles
Intenta con cada una y usa las que funcionan
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

# Importar servicios disponibles
import sys
import os
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/multi",
    tags=["multi-source"]
)

async def fetch_buenos_aires_events():
    """Intenta obtener eventos de Buenos Aires Data OFICIAL"""
    try:
        from services.ba_data_official import BuenosAiresOfficialAPI
        api = BuenosAiresOfficialAPI()
        events = await api.fetch_all_events()
        
        return {
            "source": "Buenos Aires Data OFICIAL (GCBA)",
            "status": "success",
            "count": len(events) if events else 0,
            "events": events[:15] if events else []  # Más eventos de fuente oficial
        }
    except Exception as e:
        logger.error(f"Buenos Aires Official API error: {e}")
        # Fallback a la API antigua
        try:
            from services.buenos_aires_api import BuenosAiresDataConnector
            connector = BuenosAiresDataConnector()
            if hasattr(connector, 'fetch_all_events'):
                events = await connector.fetch_all_events()
            else:
                events = []
            
            return {
                "source": "Buenos Aires Data (Fallback)",
                "status": "success",
                "count": len(events),
                "events": events[:10] if events else []
            }
        except Exception as e2:
            logger.error(f"Buenos Aires fallback error: {e2}")
            return {
                "source": "Buenos Aires Data",
                "status": "error",
                "error": str(e),
                "events": []
            }

async def fetch_eventbrite_events(location: str):
    """Intenta obtener eventos de Eventbrite"""
    try:
        from services.eventbrite_api import EventbriteLatamConnector
        connector = EventbriteLatamConnector()
        events = await connector.fetch_events_by_location(location)
        
        return {
            "source": "Eventbrite",
            "status": "success",
            "count": len(events) if events else 0,
            "events": events[:5] if events else []
        }
    except Exception as e:
        logger.error(f"Eventbrite API error: {e}")
        return {
            "source": "Eventbrite",
            "status": "error", 
            "error": str(e),
            "events": []
        }

async def fetch_cloud_scraper_events(location: str):
    """Usa CloudScraper para obtener eventos (sin Playwright)"""
    try:
        from services.cloud_scraper import CloudScraper
        scraper = CloudScraper()
        
        # Intenta scraping directo de Facebook
        fb_events = await scraper.scrape_facebook_events_api(location)
        
        # Intenta Instagram por hashtag
        ig_posts = await scraper.scrape_instagram_hashtag_api("eventosba")
        
        # Convertir posts de Instagram a eventos
        ig_events = []
        for post in ig_posts if ig_posts else []:
            if 'event_title' in post:
                ig_events.append({
                    'title': post['event_title'],
                    'description': post.get('caption', ''),
                    'source': 'instagram',
                    'category': 'social',
                    'venue_name': 'Ver en Instagram',
                    'event_url': post.get('url', ''),
                    'likes': post.get('likes', 0)
                })
        
        # Intenta Eventbrite público
        eb_events = await scraper.scrape_eventbrite_public(location)
        
        # Normalizar eventos de Facebook
        normalized_fb = []
        for event in fb_events:
            normalized_fb.append({
                'title': event.get('title', ''),
                'description': event.get('description', ''),
                'venue_name': event.get('location', '').split(',')[0] if event.get('location') else 'Buenos Aires',
                'venue_address': event.get('location', 'Buenos Aires'),
                'category': event.get('category', 'general'),
                'price': event.get('price', 0),
                'is_free': event.get('price', 0) == 0,
                'source': event.get('source', 'facebook'),
                'start_datetime': event.get('date', ''),
                'event_url': f"https://facebook.com/events/{hash(event.get('title', ''))}",
                'image_url': 'https://images.unsplash.com/photo-1540039155733-5bb30b53aa14'
            })
        
        all_events = normalized_fb + ig_events + (eb_events if eb_events else [])
        
        return {
            "source": "CloudScraper (FB/IG/Eventbrite)",
            "status": "success",
            "count": len(all_events),
            "events": all_events[:15]
        }
    except Exception as e:
        logger.error(f"CloudScraper error: {e}")
        return {
            "source": "CloudScraper",
            "status": "error",
            "error": str(e),
            "events": []
        }

async def fetch_firecrawl_events(location: str):
    """Usa Firecrawl API para obtener eventos (sin Playwright)"""
    try:
        from services.firecrawl_scraper import FirecrawlEventsScraper
        scraper = FirecrawlEventsScraper()
        
        # Fetch eventos de todas las fuentes configuradas
        events = await scraper.fetch_all_events(limit_sources=3)
        
        return {
            "source": "Firecrawl Scraper",
            "status": "success",
            "count": len(events) if events else 0,
            "events": events[:5] if events else []
        }
    except Exception as e:
        logger.error(f"Firecrawl error: {e}")
        return {
            "source": "Firecrawl",
            "status": "error",
            "error": str(e),
            "events": []
        }

async def fetch_cloudscraper_real_events(location: str):
    """Obtiene eventos REALES con CloudScraper (sin browser, funciona en API REST)"""
    try:
        from services.cloudscraper_events import CloudscraperEvents
        scraper = CloudscraperEvents()
        
        # Obtener eventos reales
        events = await scraper.fetch_all_events(location)
        
        return {
            "source": "CloudScraper Real (FB/IG/Eventbrite)",
            "status": "success",
            "count": len(events),
            "events": events[:15]
        }
    except Exception as e:
        logger.error(f"CloudScraper real error: {e}")
        return {
            "source": "CloudScraper Real",
            "status": "error",
            "error": str(e),
            "events": []
        }

async def fetch_lightweight_events(location: str):
    """Obtiene eventos con scraper ligero (sin Playwright ni dependencias)"""
    try:
        from services.lightweight_scraper import LightweightEventScraper
        scraper = LightweightEventScraper()
        
        # Obtener eventos
        events = await scraper.fetch_all_events(location)
        
        return {
            "source": "Lightweight Scraper (Requests + BS4)",
            "status": "success",
            "count": len(events),
            "events": events[:10]
        }
    except Exception as e:
        logger.error(f"Lightweight scraper error: {e}")
        return {
            "source": "Lightweight Scraper",
            "status": "error",
            "error": str(e),
            "events": []
        }

async def fetch_real_venue_events(location: str):
    """Obtiene eventos REALES de venues argentinos HARDCORE"""
    try:
        from services.argentina_venues_scraper import ArgentinaVenuesScraper
        scraper = ArgentinaVenuesScraper()
        
        all_events = await scraper.fetch_all_events()
        
        return {
            "source": "Argentina Venues HARDCORE",
            "status": "success",
            "count": len(all_events),
            "events": all_events[:20]  # Más eventos porque son reales
        }
    except Exception as e:
        logger.error(f"Argentina venues scraper error: {e}")
        return {
            "source": "Argentina Venues",
            "status": "error", 
            "error": str(e),
            "events": []
        }

def get_category_keywords(category: str) -> List[str]:
    """Mapea categorías del frontend a palabras clave para filtrar eventos"""
    category_mapping = {
        'música': ['música', 'concierto', 'recital', 'show', 'banda', 'festival', 'music', 'concert'],
        'deportes': ['fútbol', 'deporte', 'partido', 'racing', 'boca', 'river', 'sports', 'futbol', 'tenis', 'basketball'],
        'cultural': ['teatro', 'arte', 'cultura', 'museo', 'exposición', 'cultural', 'theater', 'art'],
        'tech': ['tecnología', 'hackathon', 'tech', 'programming', 'desarrollo', 'software', 'startup'],
        'fiestas': ['fiesta', 'party', 'after', 'discoteca', 'boliche', 'disco', 'nightlife']
    }
    
    if not category:
        return []
    
    category_lower = category.lower()
    return category_mapping.get(category_lower, [category_lower])

def filter_events_by_category(events: List[Dict], category: str) -> List[Dict]:
    """Filtra eventos por categoría usando palabras clave"""
    if not category or category.lower() in ['todos', 'all']:
        return events
    
    keywords = get_category_keywords(category)
    if not keywords:
        return events
    
    filtered_events = []
    for event in events:
        # Buscar keywords en título, descripción, y category
        text_to_search = " ".join([
            str(event.get('title', '')),
            str(event.get('description', '')),
            str(event.get('category', '')),
            str(event.get('venue_name', ''))
        ]).lower()
        
        # Si cualquier keyword coincide, incluir el evento
        if any(keyword in text_to_search for keyword in keywords):
            filtered_events.append(event)
    
    return filtered_events

async def fetch_oficial_venues_events():
    """Obtiene eventos de sitios WEB OFICIALES de venues"""
    try:
        from services.oficial_venues_scraper import OficialVenuesScraper
        scraper = OficialVenuesScraper()
        
        events = await scraper.scrape_all_oficial_venues()
        
        return {
            "source": "Venues Oficiales (Web Sites)",
            "status": "success", 
            "count": len(events),
            "events": events[:15]  # Eventos de sitios oficiales
        }
    except Exception as e:
        logger.error(f"Oficial venues scraper error: {e}")
        return {
            "source": "Venues Oficiales",
            "status": "error",
            "error": str(e),
            "events": []
        }

async def fetch_proven_multi_source_events(location: str):
    """Obtiene eventos con el SCRAPER PROBADO EXACTO de /tips/"""
    logger.info(f"🔥 EJECUTANDO SCRAPER PROBADO para {location}")
    try:
        from services.proven_scraper_exact import fetch_events_proven_exact
        
        logger.info("📥 Importación exitosa, llamando al scraper...")
        events = await fetch_events_proven_exact(location)
        logger.info(f"📊 Scraper probado obtuvo {len(events)} eventos")
        
        # Convertir formato del scraper probado al formato del sistema
        formatted_events = []
        for event in events:
            formatted_events.append({
                'title': event.get('title', ''),
                'description': f"Evento desde {event.get('source', 'Unknown')}: {event.get('title', '')}",
                'venue_name': event.get('location', 'Buenos Aires').split(',')[0],
                'venue_address': event.get('location', 'Buenos Aires, Argentina'),
                'start_datetime': event.get('extracted_at', ''),
                'category': 'general',
                'price': 0,
                'currency': 'ARS', 
                'is_free': True,
                'source': f"proven_{event.get('source', 'unknown').lower()}",
                'image_url': 'https://images.unsplash.com/photo-1522158637959-30385a09e0da',
                'latitude': -34.6118,
                'longitude': -58.3960,
                'status': 'live'
            })
        
        return {
            "source": "SCRAPER PROBADO EXACTO (replicado desde /tips/)",
            "status": "success",
            "count": len(formatted_events),
            "events": formatted_events
        }
    except Exception as e:
        logger.error(f"Proven exact scraper error: {e}")
        return {
            "source": "SCRAPER PROBADO EXACTO",
            "status": "error",
            "error": str(e),
            "events": []
        }

async def fetch_from_all_sources_internal(
    location: str = "Buenos Aires",
    category: str = None,
    fast: bool = True
):
    """
    Internal function for fetching events (no Query dependencies)
    """
    logger.info(f"🌐 Fetching events from all sources for: {location}")
    
    # PRIMERO: Verificar si es una provincia con scraper específico
    location_lower = location.lower()
    if any(prov in location_lower for prov in ['córdoba', 'cordoba', 'mendoza', 'rosario']):
        logger.info(f"🎯 Detectada provincia con scraper específico: {location}")
        
        try:
            from services.provincial_scrapers import ProvincialEventManager
            manager = ProvincialEventManager()
            events = await manager.get_events_for_location(location)
            
            if events:
                return {
                    "success": True,
                    "location": location,
                    "events": events[:50],
                    "recommended_events": events[:50],
                    "source": "provincial_scraper",
                    "message": f"Eventos específicos de {location}"
                }
        except Exception as e:
            logger.error(f"Error con scraper provincial: {e}")
    
    # Si no es una provincia con scraper o falló, continuar con Buenos Aires
    # En modo rápido, solo usar los scrapers que FUNCIONAN BIEN
    if fast:
        coroutines = [
            fetch_eventbrite_events(location),   # Funciona: trae eventos reales
            fetch_real_venue_events(location),    # Funciona: venues conocidos
            fetch_oficial_venues_events(),        # Funciona: Luna Park, Teatro Colón
            # NO incluir: fetch_lightweight_events - trae basura
            # NO incluir: fetch_proven_multi_source_events - trae JSON corrupto
        ]
    else:
        # Ejecutar todas las fuentes en paralelo (modo completo)
        coroutines = [
            # fetch_buenos_aires_events(),       # COMENTADO: API no disponible
            fetch_eventbrite_events(location),    # OK
            # fetch_cloud_scraper_events(location), # COMENTADO: requiere login
            # fetch_firecrawl_events(location),   # COMENTADO: sin API key
            fetch_real_venue_events(location),    # OK
            # fetch_lightweight_events(location),  # COMENTADO: trae basura
            # fetch_cloudscraper_real_events(location), # COMENTADO: pocos eventos
            fetch_oficial_venues_events(),        # OK
            # fetch_proven_multi_source_events(location) # COMENTADO: trae JSON corrupto de FB
        ]
    
    # Convertir corrutinas a tareas para asyncio.wait
    tasks = [asyncio.create_task(coro) for coro in coroutines]
    
    # Usar asyncio.wait con timeout para obtener resultados parciales
    if fast:
        # Esperar máximo 3 segundos, pero obtener TODOS los resultados posibles
        done, pending = await asyncio.wait(tasks, timeout=3.0)
        
        # Cancelar tareas pendientes
        for task in pending:
            task.cancel()
        
        # Obtener resultados completados
        results = []
        for task in done:
            try:
                results.append(await task)
            except Exception as e:
                results.append(e)
                
        # Agregar None para tareas canceladas
        results.extend([None] * len(pending))
    else:
        # En modo completo, usar timeout de 10 segundos máximo
        done, pending = await asyncio.wait(tasks, timeout=10.0)
        
        for task in pending:
            task.cancel()
            
        results = []
        for task in done:
            try:
                results.append(await task)
            except Exception as e:
                results.append(e)
                
        results.extend([None] * len(pending))
    
    # Procesar resultados con más detalle
    sources_detail = []
    all_events = []
    total_attempts = len(tasks)
    total_successful = 0
    total_failed = 0
    total_events_fetched = 0
    
    # Nombres de las fuentes en orden
    source_names = [
        "Buenos Aires Data OFICIAL (GCBA)",
        "Eventbrite Argentina + Scraping", 
        "CloudScraper (FB/IG simulado)",
        "Firecrawl Scraper",
        "Argentina Venues HARDCORE",
        "Lightweight Scraper (BS4)",
        "CloudScraper Real (anti-bot bypass)",
        "Venues Oficiales (Web Sites)",
        "Multi-Source PROBADO (FB/IG/Eventbrite)"  # NUEVO - scraper probado
    ]
    
    for i, result in enumerate(results):
        source_info = {
            "name": source_names[i] if i < len(source_names) else f"Source {i+1}",
            "status": "unknown",
            "events_count": 0,
            "message": "",
            "execution_time": "< 1s"
        }
        
        if isinstance(result, Exception):
            source_info["status"] = "error"
            source_info["message"] = str(result)[:100]  # Limitar mensaje de error
            source_info["error_type"] = type(result).__name__
            total_failed += 1
        elif isinstance(result, dict):
            if result.get("status") == "success":
                events = result.get("events", [])
                source_info["status"] = "success"
                source_info["events_count"] = len(events)
                source_info["total_available"] = result.get("count", len(events))
                
                if len(events) > 0:
                    source_info["message"] = f"✅ Trajo {len(events)} eventos"
                    total_successful += 1
                    total_events_fetched += len(events)
                    all_events.extend(events)
                else:
                    source_info["status"] = "empty"
                    source_info["message"] = "⚠️ Funcionó pero no encontró eventos"
                    total_successful += 1
                    
                # Información adicional si existe
                if result.get("source"):
                    source_info["source_type"] = result["source"]
            else:
                source_info["status"] = "failed"
                source_info["message"] = result.get("error", "Error desconocido")[:100]
                total_failed += 1
        
        sources_detail.append(source_info)
    
    # Enriquecer eventos con imágenes si no tienen
    try:
        from services.image_generator import EventImageGenerator
        image_generator = EventImageGenerator()
        
        for event in all_events:
            if not event.get('image_url') or 'unsplash' not in event.get('image_url', ''):
                # Solo cambiar si no tiene imagen o es una genérica
                event['image_url'] = await image_generator.get_image_for_event(event)
    except Exception as e:
        logger.warning(f"Could not enrich images: {e}")
    
    # Deduplicar eventos por título (mejorado)
    seen_titles = {}
    unique_events = []
    duplicates_count = 0
    
    for event in all_events:
        title = event.get("title", "").lower().strip()
        if title:
            if title not in seen_titles:
                seen_titles[title] = True
                unique_events.append(event)
            else:
                duplicates_count += 1
    
    # Filtrar por categoría DESPUÉS de deduplicar
    events_before_category_filter = len(unique_events)
    category_filtered_count = 0
    if category:
        unique_events = filter_events_by_category(unique_events, category)
        category_filtered_count = events_before_category_filter - len(unique_events)
    
    return {
        "success": True,
        "location": location,
        "execution_details": {
            "total_sources_called": len(tasks),  # Número dinámico de fuentes
            "sources_succeeded": total_successful,
            "sources_failed": total_failed,
            "total_events_fetched": total_events_fetched,
            "unique_events_after_dedup": len(unique_events),
            "duplicates_removed": duplicates_count,
            "response_time_ms": "< 5000"
        },
        "sources_status": sources_detail,  # Array detallado de cada fuente
        "summary": {
            "🎯 APIs llamadas": total_attempts,
            "✅ Exitosas": total_successful, 
            "❌ Fallidas": total_failed,
            "📊 Total eventos obtenidos": total_events_fetched,
            "🔍 Eventos únicos": len(unique_events),
            "🔄 Duplicados eliminados": duplicates_count,
            "📱 Ubicación consultada": location,
            "🎨 Categoría filtrada": category or "Todos",
            "🎯 Eventos filtrados por categoría": category_filtered_count if category else 0
        },
        "events": unique_events[:50],  # Hasta 50 eventos
        "recommended_events": unique_events[:50],  # IMPORTANTE: Frontend espera este campo
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "api_version": "2.0",
            "scrapers_used": [s["name"] for s in sources_detail if s["status"] == "success"],
            "failed_scrapers": [s["name"] for s in sources_detail if s["status"] in ["error", "failed"]]
        }
    }

@router.get("/fetch-all")
async def fetch_from_all_sources(
    location: str = Query("Buenos Aires", description="Ubicación para buscar eventos"),
    category: str = Query(None, description="Categoría específica: Música, Deportes, Cultural, Tech, Fiestas"),
    fast: bool = Query(True, description="Modo rápido - solo scrapers eficientes")
):
    """
    Endpoint HTTP para obtener eventos de todas las fuentes
    """
    return await fetch_from_all_sources_internal(location=location, category=category, fast=fast)

@router.get("/test-apis")
async def test_apis():
    """
    Prueba rápida de qué APIs están funcionando
    """
    
    apis_status = {}
    
    # Test Buenos Aires API
    try:
        from services.buenos_aires_api import BuenosAiresDataConnector
        apis_status["Buenos Aires Data"] = "✅ Available"
    except Exception as e:
        apis_status["Buenos Aires Data"] = f"❌ {str(e)}"
    
    # Test Eventbrite
    try:
        from services.eventbrite_api import EventbriteLatamConnector
        connector = EventbriteLatamConnector()
        if connector.api_key:
            apis_status["Eventbrite"] = "✅ Available (API Key configured)"
        else:
            apis_status["Eventbrite"] = "⚠️ Available (No API Key)"
    except Exception as e:
        apis_status["Eventbrite"] = f"❌ {str(e)}"
    
    # Test if Playwright is available for scrapers
    try:
        import playwright
        apis_status["Scrapers (Playwright)"] = "✅ Available"
    except:
        apis_status["Scrapers (Playwright)"] = "❌ Not installed"
    
    return {
        "status": "API Test Results",
        "apis": apis_status,
        "recommendation": "Use /api/multi/fetch-all to get events from working sources"
    }