"""
API Multi-Source - Obtiene eventos de TODAS las fuentes disponibles
Intenta con cada una, mide velocidad, y ordena por llegada
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging
import time

# Importar servicios disponibles
import sys
import os
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/multi",
    tags=["multi-source"]
)

# 🚀 Performance Tracking System
class APIPerformanceTracker:
    def __init__(self):
        self.source_speeds = {}  # Store average response times
        self.completion_order = []  # Track order of completion
        
    async def track_source(self, source_name: str, fetch_function):
        """Track performance of a data source"""
        start_time = time.time()
        try:
            result = await fetch_function()
            end_time = time.time()
            response_time = end_time - start_time
            
            # Update performance metrics
            if source_name not in self.source_speeds:
                self.source_speeds[source_name] = []
            self.source_speeds[source_name].append(response_time)
            
            # Track completion order
            self.completion_order.append({
                "source": source_name,
                "completion_time": end_time,
                "response_time": response_time,
                "event_count": result.get("count", 0) if result else 0,
                "status": "success"
            })
            
            logger.info(f"⚡ {source_name}: {response_time:.2f}s, {result.get('count', 0) if result else 0} eventos")
            return result
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            self.completion_order.append({
                "source": source_name,
                "completion_time": end_time,
                "response_time": response_time,
                "event_count": 0,
                "status": "error",
                "error": str(e)
            })
            
            logger.error(f"❌ {source_name}: {response_time:.2f}s, ERROR: {e}")
            return {"source": source_name, "status": "error", "count": 0, "events": []}
    
    def get_performance_ranking(self):
        """Get sources ranked by speed (fastest first)"""
        ranking = []
        for source, times in self.source_speeds.items():
            avg_time = sum(times) / len(times)
            ranking.append({
                "source": source,
                "avg_response_time": avg_time,
                "total_calls": len(times),
                "fastest_time": min(times),
                "slowest_time": max(times)
            })
        
        # Sort by average response time (fastest first)
        ranking.sort(key=lambda x: x["avg_response_time"])
        return ranking
    
    def get_completion_order(self):
        """Get the order in which sources completed"""
        return sorted(self.completion_order, key=lambda x: x["completion_time"])

# Global performance tracker
performance_tracker = APIPerformanceTracker()

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
    """Intenta obtener eventos de Eventbrite WEB SCRAPER (87+ eventos)"""
    try:
        from services.eventbrite_web_scraper import EventbriteWebScraper
        scraper = EventbriteWebScraper()
        events = await scraper.fetch_events_by_location(location, limit=20)
        
        logger.info(f"🎟️ Eventbrite Web {location}: {len(events)} eventos")
        
        return {
            "source": "Eventbrite Web",
            "status": "success", 
            "count": len(events) if events else 0,
            "events": events
        }
    except Exception as e:
        logger.error(f"❌ Eventbrite Web Scraper error: {e}")
        # Fallback al API viejo
        try:
            from services.eventbrite_api import EventbriteLatamConnector
            connector = EventbriteLatamConnector()
            events = await connector.fetch_events_by_location(location)
            
            return {
                "source": "Eventbrite API (fallback)",
                "status": "success",
                "count": len(events) if events else 0,
                "events": events[:5] if events else []
            }
        except:
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

async def fetch_facebook_events_rapidapi(location: str):
    """
    🔥 FACEBOOK SCRAPER - SIEMPRE EJECUTAR 
    Usa RapidAPI Facebook Scraper para obtener eventos reales
    """
    try:
        logger.info(f"🔥 EJECUTANDO Facebook RapidAPI para: {location}")
        from services.rapidapi_facebook_scraper import RapidApiFacebookScraper
        
        scraper = RapidApiFacebookScraper()
        
        # Intenta scrapear eventos de Facebook con timeout
        events = await scraper.scrape_facebook_events_rapidapi(
            city_name=location, 
            limit=20, 
            max_time_seconds=8.0  # Timeout más generoso
        )
        
        if events:
            logger.info(f"✅ Facebook RapidAPI: {len(events)} eventos obtenidos")
            return {
                "source": "Facebook RapidAPI",
                "status": "success", 
                "count": len(events),
                "events": events[:15]
            }
        else:
            logger.warning(f"⚠️ Facebook RapidAPI: Sin eventos para {location}")
            return {
                "source": "Facebook RapidAPI",
                "status": "success",
                "count": 0,
                "events": []
            }
            
    except Exception as e:
        logger.error(f"❌ Facebook RapidAPI error: {e}")
        return {
            "source": "Facebook RapidAPI", 
            "status": "error",
            "error": str(e),
            "count": 0,
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
        # from services.argentina_venues_scraper import ArgentinaVenuesScraper  # DELETED - was fake data generator
        # scraper = ArgentinaVenuesScraper()  # DELETED - was fake data generator
        # all_events = await scraper.fetch_all_events()  # DISABLED
        all_events = []  # No fake events
        
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
    
    # 🚀 BARRA DE PROGRESO INICIAL - SCRAPERS A EJECUTAR
    logger.info(f"")
    logger.info(f"╔═════════════════════════════════════════════════════════════════╗")
    logger.info(f"║ 🚀 INICIANDO MULTI-SOURCE SCRAPING                             ║")
    logger.info(f"╠═════════════════════════════════════════════════════════════════╣")
    logger.info(f"║ 📍 Ubicación: {location:<48} ║")
    logger.info(f"║ 🎯 Objetivo: Obtener eventos de múltiples fuentes              ║")
    logger.info(f"║ ⚡ Modo: {'Rápido (fast=True)' if fast else 'Completo (fast=False)':<44} ║")
    logger.info(f"╚═════════════════════════════════════════════════════════════════╝")
    logger.info(f"")
    
    # PRIMERO: Verificar si es una PROVINCIA ARGENTINA con scraper específico
    location_lower = location.lower()
    if any(prov in location_lower for prov in ['córdoba', 'cordoba', 'mendoza', 'rosario']):
        logger.info(f"🎯 Detectada provincia con scraper específico: {location}")
        
        try:
            # 🔥 EJECUTAR FACEBOOK PRIMERO, DESPUÉS PROVINCIAL
            facebook_result = await fetch_facebook_events_rapidapi(location)
            
            from services.provincial_scrapers import ProvincialEventManager
            manager = ProvincialEventManager()
            events = await manager.get_events_for_location(location)
            
            # Combinar eventos de Facebook + Provinciales
            all_events = []
            scrapers_info = []
            
            # Facebook
            if facebook_result and facebook_result.get("events"):
                all_events.extend(facebook_result["events"])
                scrapers_info.append({
                    "name": "🔥 Facebook RapidAPI",
                    "status": "success",
                    "events_count": len(facebook_result["events"]),
                    "response_time": "unknown",
                    "message": f"Obtuvo {len(facebook_result['events'])} eventos de Facebook"
                })
            else:
                scrapers_info.append({
                    "name": "🔥 Facebook RapidAPI", 
                    "status": "failed",
                    "events_count": 0,
                    "response_time": "unknown",
                    "message": "No pudo obtener eventos de Facebook"
                })
            
            # Provincial
            if events:
                all_events.extend(events[:30])  # Limitar para no sobrecargar
                scrapers_info.append({
                    "name": f"Provincial Scraper ({location})",
                    "status": "success", 
                    "events_count": len(events),
                    "response_time": "unknown",
                    "message": f"Obtuvo {len(events)} eventos locales"
                })
            else:
                scrapers_info.append({
                    "name": f"Provincial Scraper ({location})",
                    "status": "failed",
                    "events_count": 0,
                    "response_time": "unknown", 
                    "message": "No pudo obtener eventos provinciales"
                })
            
            if all_events:
                return {
                    "success": True,
                    "location": location,
                    "events": all_events[:50],
                    "recommended_events": all_events[:50],
                    "source": "facebook_plus_provincial",
                    "message": f"Facebook + Eventos específicos de {location}",
                    "scrapers_execution": {
                        "scrapers_called": ["🔥 Facebook RapidAPI", f"Provincial Scraper ({location})"],
                        "total_scrapers": 2,
                        "scrapers_info": scrapers_info,
                        "summary": f"Se ejecutaron 2 scrapers, {len([s for s in scrapers_info if s['status'] == 'success'])} exitosos"
                    }
                }
        except Exception as e:
            logger.error(f"Error con scraper provincial: {e}")
    
    # SEGUNDO: Verificar si es una CIUDAD GLOBAL con scraper específico
    global_cities = {
        'barcelona': 'Barcelona',
        # 'madrid': 'Madrid',  # ❌ DISABLED - No tiene scraper específico 
        'paris': 'Paris',
        'méxico': 'Mexico City',
        'mexico city': 'Mexico City',
        'miami': 'Miami',
        'miami beach': 'Miami',
        'south beach': 'Miami'
    }
    
    logger.info(f"🔍 DEBUG GLOBAL - Buscando en location_lower: '{location_lower}'")
    logger.info(f"🔍 DEBUG GLOBAL - Cities disponibles: {list(global_cities.keys())}")
    
    for city_key, city_name in global_cities.items():
        logger.info(f"🔍 CHECKING: '{city_key}' in '{location_lower}' = {city_key in location_lower}")
        if city_key in location_lower:
            logger.info(f"🌍 Detectada ciudad global: {city_name}")
            
            try:
                # 🔥 EJECUTAR FACEBOOK PRIMERO PARA CIUDADES GLOBALES
                facebook_result = await fetch_facebook_events_rapidapi(location)
                
                if city_name == 'Barcelona':
                    from services.barcelona_scraper import BarcelonaScraper
                    scraper = BarcelonaScraper()
                    barcelona_events = await scraper.scrape_all_sources()
                    
                    # Combinar Facebook + Barcelona
                    all_events = []
                    scrapers_info = []
                    
                    if facebook_result and facebook_result.get("events"):
                        all_events.extend(facebook_result["events"])
                        scrapers_info.append({
                            "name": "🔥 Facebook RapidAPI",
                            "status": "success",
                            "events_count": len(facebook_result["events"]),
                            "response_time": "unknown",
                            "message": f"Facebook Barcelona: {len(facebook_result['events'])} eventos"
                        })
                    
                    if barcelona_events:
                        all_events.extend(barcelona_events[:30])
                        scrapers_info.append({
                            "name": "Barcelona Scraper",
                            "status": "success", 
                            "events_count": len(barcelona_events),
                            "response_time": "unknown",
                            "message": f"Barcelona local: {len(barcelona_events)} eventos"
                        })
                    
                    if all_events:
                        return {
                            "success": True,
                            "location": location,
                            "events": all_events[:50],
                            "recommended_events": all_events[:50], 
                            "source": "facebook_plus_barcelona",
                            "message": f"Facebook + Barcelona: {len(all_events)} eventos",
                            "scrapers_execution": {
                                "scrapers_called": ["🔥 Facebook RapidAPI", "Barcelona Scraper"],
                                "total_scrapers": 2,
                                "scrapers_info": scrapers_info,
                                "summary": f"Se ejecutaron 2 scrapers, {len([s for s in scrapers_info if s['status'] == 'success'])} exitosos"
                            }
                        }
                
                elif city_name == 'Miami':
                    from services.miami_scraper import MiamiScraper
                    scraper = MiamiScraper()
                    miami_events = await scraper.scrape_all_sources()
                    
                    # Combinar Facebook + Miami
                    all_events = []
                    scrapers_info = []
                    
                    if facebook_result and facebook_result.get("events"):
                        all_events.extend(facebook_result["events"])
                        scrapers_info.append({
                            "name": "🔥 Facebook RapidAPI",
                            "status": "success",
                            "events_count": len(facebook_result["events"]),
                            "response_time": "unknown",
                            "message": f"Facebook Miami: {len(facebook_result['events'])} eventos"
                        })
                    
                    if miami_events:
                        all_events.extend(miami_events[:30])
                        scrapers_info.append({
                            "name": "Miami Scraper",
                            "status": "success",
                            "events_count": len(miami_events), 
                            "response_time": "unknown",
                            "message": f"Miami local: {len(miami_events)} eventos"
                        })
                    
                    if all_events:
                        return {
                            "success": True,
                            "location": location,
                            "events": all_events[:50],
                            "recommended_events": all_events[:50], 
                            "source": "facebook_plus_miami",
                            "message": f"Facebook + Miami 🏖️: {len(all_events)} eventos",
                            "scrapers_execution": {
                                "scrapers_called": ["🔥 Facebook RapidAPI", "Miami Scraper"],
                                "total_scrapers": 2,
                                "scrapers_info": scrapers_info,
                                "summary": f"Se ejecutaron 2 scrapers, {len([s for s in scrapers_info if s['status'] == 'success'])} exitosos"
                            }
                        }
            except Exception as e:
                logger.error(f"Error con scraper global {city_name}: {e}")
            
            break  # Solo procesar la primera ciudad encontrada
    
    # 🔥 FACEBOOK SIEMPRE PRIMERO - OBLIGATORIO EN TODAS LAS UBICACIONES
    source_definitions = [
        ("🔥 Facebook RapidAPI", lambda: fetch_facebook_events_rapidapi(location)),
    ]
    
    # 🔍 Agregar scrapers específicos por ubicación
    if any(arg in location_lower for arg in ['buenos aires', 'argentina', 'bsas', 'caba']) or location == "Buenos Aires":
        logger.info(f"✅ Location is Argentina/Buenos Aires - Adding local scrapers + Facebook")
        # Agregar fuentes locales DESPUÉS de Facebook
        source_definitions.extend([
            ("Eventbrite Real API", lambda: fetch_eventbrite_events(location)),
            ("Official Venues Only", lambda: fetch_oficial_venues_events()),
        ])
    else:
        logger.warning(f"⚠️ Location '{location}' is not Argentina - Using Facebook + Eventbrite genérico")
        # Para otras ciudades, Facebook + eventbrite genérico
        source_definitions.extend([
            ("Eventbrite Masivo", lambda: fetch_eventbrite_events(location))
        ])
    
    # Si no es modo rápido, agregar fuentes adicionales
    if not fast:
        source_definitions.extend([
            # Solo agregar si están disponibles y funcionan
        ])
    
    # Crear tareas con tracking de performance y información inicial
    tracked_tasks = []
    scrapers_called = []  # Lista de scrapers que se van a ejecutar
    
    for source_name, fetch_func in source_definitions:
        scrapers_called.append(source_name)
        task = asyncio.create_task(
            performance_tracker.track_source(source_name, fetch_func)
        )
        tracked_tasks.append((source_name, task))
    
    # 🏃‍♂️ RESPUESTA INSTANTÁNEA: Procesar resultados conforme van llegando
    all_events = []
    completed_sources = []
    scrapers_execution_info = []  # Información detallada de cada scraper
    timeout_limit = 3.0 if fast else 8.0
    
    # Usar as_completed para procesar tan pronto como lleguen
    async def process_results():
        for coro in asyncio.as_completed([task for _, task in tracked_tasks], timeout=timeout_limit):
            try:
                result = await coro
                
                # Encontrar el nombre del scraper que completó
                source_name = "Unknown"
                for name, task in tracked_tasks:
                    if task == coro or task.done():
                        source_name = name
                        break
                
                if result and result.get("status") == "success" and result.get("events"):
                    events = result.get("events", [])
                    
                    # 🎯 BARRA DE PROGRESO VISUAL CON CONTADORES
                    progress_bar = "█" * min(len(events) // 2, 20) + "░" * max(0, 20 - len(events) // 2)
                    logger.info(f"")
                    logger.info(f"┌─────────────────────────────────────────────────────────────────")
                    logger.info(f"│ ✅ {source_name}")
                    logger.info(f"│ 📊 Eventos obtenidos: {len(events)}")
                    logger.info(f"│ 📈 Progress: [{progress_bar}] {len(events)} eventos")
                    logger.info(f"│ 🔢 Total acumulado: {len(all_events)} → {len(all_events) + len(events)}")
                    logger.info(f"└─────────────────────────────────────────────────────────────────")
                    logger.info(f"")
                    
                    all_events.extend(events)
                    
                    # Información detallada del scraper exitoso
                    scraper_info = {
                        "name": source_name,
                        "status": "success", 
                        "events_count": len(events),
                        "response_time": result.get("response_time", "unknown"),
                        "message": f"Obtuvo {len(events)} eventos exitosamente"
                    }
                    scrapers_execution_info.append(scraper_info)
                    
                    completed_sources.append({
                        "source": source_name,
                        "count": len(events),
                        "status": "success"
                    })
                else:
                    # Scraper falló o no devolvió eventos
                    error_msg = result.get("error", "No devolvió eventos") if result else "No response"
                    scraper_info = {
                        "name": source_name,
                        "status": "failed",
                        "events_count": 0,
                        "response_time": result.get("response_time", "unknown") if result else "timeout",
                        "message": f"Error: {error_msg}"
                    }
                    scrapers_execution_info.append(scraper_info)
                    
                    # Devolver datos inmediatamente disponibles (para WebSocket)
                    yield {
                        "source": source_name,
                        "events": events,
                        "count": len(events),
                        "total_so_far": len(all_events)
                    }
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Timeout alcanzado, devolviendo eventos disponibles")
                # Agregar información de scrapers que no completaron por timeout
                for name, task in tracked_tasks:
                    if not task.done():
                        scrapers_execution_info.append({
                            "name": name,
                            "status": "timeout",
                            "events_count": 0,
                            "response_time": f">{timeout_limit}s",
                            "message": f"Timeout después de {timeout_limit}s"
                        })
                break
            except Exception as e:
                logger.error(f"❌ Error procesando fuente: {e}")
                continue
    
    # Procesar en modo streaming (para esta función devolvemos el resultado final)
    async for partial_result in process_results():
        # En una implementación real con WebSocket, aquí enviarías partial_result
        pass
    
    # Cancelar cualquier tarea pendiente
    for _, task in tracked_tasks:
        if not task.done():
            task.cancel()
    
    # 🎯 BARRA DE PROGRESO FINAL - RESUMEN COMPLETO
    total_events = len(all_events)
    success_count = len([s for s in scrapers_execution_info if s.get('status') == 'success'])
    total_scrapers = len(scrapers_called)
    
    final_progress_bar = "█" * min(total_events // 3, 25) + "░" * max(0, 25 - total_events // 3)
    
    logger.info(f"")
    logger.info(f"╔═════════════════════════════════════════════════════════════════╗")
    logger.info(f"║ 🏁 MULTI-SOURCE COMPLETADO                                     ║")
    logger.info(f"╠═════════════════════════════════════════════════════════════════╣")
    logger.info(f"║ 📊 Total eventos: {total_events:>3} eventos                                  ║")
    logger.info(f"║ 📈 Progress: [{final_progress_bar}]           ║")
    logger.info(f"║ ✅ Scrapers exitosos: {success_count}/{total_scrapers}                                   ║")
    logger.info(f"║ 📍 Ubicación: {location:<20}                            ║")
    logger.info(f"╚═════════════════════════════════════════════════════════════════╝")
    logger.info(f"")
    
    # Aplicar filtro de categoría si existe
    filtered_events = all_events
    if category and category not in ['todos', 'all']:
        filtered_events = filter_events_by_category(all_events, category)
        logger.info(f"📊 FILTRO CATEGORÍA: '{category}' → {len(all_events)} → {len(filtered_events)} eventos")
    
    # Obtener ranking de performance actualizado
    performance_ranking = performance_tracker.get_performance_ranking()
    completion_order = performance_tracker.get_completion_order()
    
    # Devolver resultado final con información detallada de scrapers
    return {
        "success": True,
        "location": location,
        "events": filtered_events,
        "recommended_events": filtered_events[:50],
        "total_events": len(filtered_events),
        "sources_completed": completed_sources,
        "performance_ranking": performance_ranking,
        "completion_order": completion_order[-len(completed_sources):] if completion_order else [],
        "strategy": "async_streaming_with_performance_tracking",
        "response_time": f"{timeout_limit}s max",
        "timestamp": datetime.utcnow().isoformat(),
        
        # ✨ NUEVA INFO PARA EL USUARIO
        "scrapers_execution": {
            "scrapers_called": scrapers_called,
            "total_scrapers": len(scrapers_called),
            "scrapers_info": scrapers_execution_info,
            "summary": f"Se ejecutaron {len(scrapers_called)} scrapers, {len([s for s in scrapers_execution_info if s['status'] == 'success'])} exitosos"
        }
    }

# 📊 Nuevo endpoint para ranking de performance
@router.get("/performance-ranking")
async def get_performance_ranking():
    """
    Obtiene el ranking de velocidad de todas las fuentes
    Ordenado de más rápida a más lenta
    """
    ranking = performance_tracker.get_performance_ranking()
    completion_history = performance_tracker.get_completion_order()
    
    return {
        "status": "success",
        "strategy": "Performance-based source prioritization", 
        "fastest_sources": ranking[:3] if len(ranking) >= 3 else ranking,
        "full_ranking": ranking,
        "recent_completion_order": completion_history[-10:],  # Últimas 10
        "total_tracked_calls": sum(source.get("total_calls", 0) for source in ranking),
        "recommendation": "Sources are automatically prioritized based on response time",
        "timestamp": datetime.utcnow().isoformat()
    }

# 🎯 Endpoint para WebSocket streaming (la clave del éxito)  
@router.get("/stream-events")
async def stream_events_info():
    """
    Información sobre el endpoint de streaming por WebSocket
    """
    return {
        "message": "Para streaming en tiempo real usar WebSocket",
        "websocket_endpoint": "ws://172.29.228.80:8001/ws/search-events",
        "strategy": "Cada fuente envía datos conforme van llegando",
        "features": [
            "Barra de progreso en tiempo real",
            "Nombre de fuente actual", 
            "Eventos conforme llegan",
            "Ordenamiento por velocidad de respuesta",
            "Cancelación automática después de timeout"
        ],
        "frontend_integration": "EventsStore.tsx ya implementado con WebSocket"
    }

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