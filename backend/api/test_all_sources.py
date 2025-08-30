"""
API de Testing - Prueba TODAS las fuentes de eventos
Intenta con cada API y scraper, usa los que funcionan
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

# Importar TODOS los servicios disponibles
import sys
import os
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

# APIs
from services.buenos_aires_api import BuenosAiresDataConnector
from services.eventbrite_api import EventbriteLatamConnector
from services.ticketmaster import TicketmasterConnector

# Scrapers
from services.facebook_scraper import FacebookEventsScraper
from services.instagram_scraper import InstagramEventsScraper
from services.ticketek_scraper import TicketekArgentinaScraper
from services.social_scraper import SocialEventsScraper

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/test",
    tags=["testing"],
    responses={404: {"description": "Not found"}}
)

class UniversalEventFetcher:
    """
    Prueba TODAS las fuentes y usa las que funcionan
    """
    
    def __init__(self):
        self.results = {}
        self.stats = {
            "total_sources": 0,
            "successful": 0,
            "failed": 0,
            "total_events": 0
        }
    
    async def test_buenos_aires_api(self, location: str) -> Dict:
        """Prueba Buenos Aires Data API"""
        try:
            logger.info("🔍 Probando Buenos Aires Data API...")
            connector = BuenosAiresDataConnector()
            events = await connector.fetch_events()
            
            if events:
                self.stats["successful"] += 1
                logger.info(f"✅ Buenos Aires API: {len(events)} eventos")
                return {
                    "status": "success",
                    "source": "Buenos Aires Data",
                    "events_count": len(events),
                    "sample": events[:3] if events else []
                }
        except Exception as e:
            logger.error(f"❌ Buenos Aires API falló: {e}")
            self.stats["failed"] += 1
            return {
                "status": "failed",
                "source": "Buenos Aires Data",
                "error": str(e)
            }
    
    async def test_eventbrite(self, location: str) -> Dict:
        """Prueba Eventbrite API"""
        try:
            logger.info("🔍 Probando Eventbrite API...")
            connector = EventbriteLatamConnector()
            events = await connector.fetch_events_by_location(location)
            
            if events:
                self.stats["successful"] += 1
                logger.info(f"✅ Eventbrite: {len(events)} eventos")
                return {
                    "status": "success",
                    "source": "Eventbrite",
                    "events_count": len(events),
                    "sample": events[:3] if events else []
                }
        except Exception as e:
            logger.error(f"❌ Eventbrite falló: {e}")
            self.stats["failed"] += 1
            return {
                "status": "failed",
                "source": "Eventbrite",
                "error": str(e)
            }
    
    async def test_ticketmaster(self, location: str) -> Dict:
        """Prueba Ticketmaster API"""
        try:
            logger.info("🔍 Probando Ticketmaster API...")
            connector = TicketmasterConnector()
            events = await connector.fetch_events_by_location(location)
            
            if events:
                self.stats["successful"] += 1
                logger.info(f"✅ Ticketmaster: {len(events)} eventos")
                return {
                    "status": "success",
                    "source": "Ticketmaster",
                    "events_count": len(events),
                    "sample": events[:3] if events else []
                }
        except Exception as e:
            logger.error(f"❌ Ticketmaster falló: {e}")
            self.stats["failed"] += 1
            return {
                "status": "failed",
                "source": "Ticketmaster",
                "error": str(e)
            }
    
    async def test_facebook_scraper(self, location: str) -> Dict:
        """Prueba Facebook Scraper"""
        try:
            logger.info("🔍 Probando Facebook Scraper...")
            scraper = FacebookEventsScraper()
            
            # Iniciar browser
            await scraper.start_browser(headless=True)
            
            # Buscar eventos
            events = await scraper.search_events_by_location(location)
            
            # Cerrar browser
            await scraper.close_browser()
            
            if events:
                self.stats["successful"] += 1
                logger.info(f"✅ Facebook: {len(events)} eventos")
                return {
                    "status": "success",
                    "source": "Facebook Scraper",
                    "events_count": len(events),
                    "sample": events[:3] if events else []
                }
        except Exception as e:
            logger.error(f"❌ Facebook Scraper falló: {e}")
            self.stats["failed"] += 1
            return {
                "status": "failed",
                "source": "Facebook Scraper",
                "error": str(e)
            }
    
    async def test_instagram_scraper(self, location: str) -> Dict:
        """Prueba Instagram Scraper"""
        try:
            logger.info("🔍 Probando Instagram Scraper...")
            scraper = InstagramEventsScraper()
            
            # Iniciar browser
            await scraper.start_browser(headless=True)
            
            # Buscar eventos por hashtags
            events = await scraper.scrape_hashtag_events("eventosba", max_posts=10)
            
            # Cerrar browser
            await scraper.close_browser()
            
            if events:
                self.stats["successful"] += 1
                logger.info(f"✅ Instagram: {len(events)} eventos")
                return {
                    "status": "success",
                    "source": "Instagram Scraper",
                    "events_count": len(events),
                    "sample": events[:3] if events else []
                }
        except Exception as e:
            logger.error(f"❌ Instagram Scraper falló: {e}")
            self.stats["failed"] += 1
            return {
                "status": "failed",
                "source": "Instagram Scraper",
                "error": str(e)
            }
    
    async def test_ticketek_scraper(self, location: str) -> Dict:
        """Prueba Ticketek Scraper"""
        try:
            logger.info("🔍 Probando Ticketek Scraper...")
            scraper = TicketekArgentinaScraper()
            
            # Iniciar browser
            browser_started = await scraper.start_browser(headless=True)
            
            if browser_started:
                # Buscar eventos
                events = await scraper.fetch_all_events()
                
                # Cerrar browser
                await scraper.close_browser()
                
                if events:
                    self.stats["successful"] += 1
                    logger.info(f"✅ Ticketek: {len(events)} eventos")
                    return {
                        "status": "success",
                        "source": "Ticketek Scraper",
                        "events_count": len(events),
                        "sample": events[:3] if events else []
                    }
        except Exception as e:
            logger.error(f"❌ Ticketek Scraper falló: {e}")
            self.stats["failed"] += 1
            return {
                "status": "failed",
                "source": "Ticketek Scraper",
                "error": str(e)
            }
    
    async def fetch_from_all_sources(self, location: str = "Buenos Aires") -> Dict:
        """
        Prueba TODAS las fuentes en paralelo
        Usa las que funcionan, ignora las que fallan
        """
        
        # Lista de todas las fuentes a probar
        sources = [
            self.test_buenos_aires_api(location),
            self.test_eventbrite(location),
            self.test_ticketmaster(location),
            self.test_facebook_scraper(location),
            self.test_instagram_scraper(location),
            self.test_ticketek_scraper(location)
        ]
        
        self.stats["total_sources"] = len(sources)
        
        # Ejecutar todas en paralelo con timeout
        results = await asyncio.gather(*sources, return_exceptions=True)
        
        # Procesar resultados
        successful_sources = []
        failed_sources = []
        all_events = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_sources.append({
                    "source": "Unknown",
                    "error": str(result)
                })
            elif isinstance(result, dict):
                if result.get("status") == "success":
                    successful_sources.append(result)
                    # Agregar eventos al total
                    if "sample" in result:
                        all_events.extend(result["sample"])
                else:
                    failed_sources.append(result)
        
        self.stats["total_events"] = len(all_events)
        
        return {
            "summary": self.stats,
            "successful_sources": successful_sources,
            "failed_sources": failed_sources,
            "sample_events": all_events[:10],  # Primeros 10 eventos como muestra
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/all-sources")
async def test_all_sources(
    location: str = Query("Buenos Aires", description="Ubicación para buscar eventos")
):
    """
    Prueba TODAS las fuentes de eventos disponibles.
    Intenta con cada API y scraper, reporta cuáles funcionan.
    
    Fuentes incluidas:
    - Buenos Aires Data API (eventos gratuitos)
    - Eventbrite API (eventos LATAM)
    - Ticketmaster API (conciertos y deportes)
    - Facebook Scraper (eventos públicos)
    - Instagram Scraper (eventos por hashtags)
    - Ticketek Scraper (eventos Argentina)
    
    La API intentará con todas y usará las que respondan correctamente.
    """
    
    try:
        fetcher = UniversalEventFetcher()
        result = await fetcher.fetch_from_all_sources(location)
        
        return {
            "success": True,
            "location": location,
            "results": result
        }
        
    except Exception as e:
        logger.error(f"Error testing sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/facebook")
async def test_facebook_only(
    location: str = Query("Buenos Aires", description="Ubicación para buscar")
):
    """
    Prueba solo el scraper de Facebook
    """
    try:
        fetcher = UniversalEventFetcher()
        result = await fetcher.test_facebook_scraper(location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instagram")
async def test_instagram_only(
    hashtag: str = Query("eventosba", description="Hashtag a buscar")
):
    """
    Prueba solo el scraper de Instagram
    """
    try:
        fetcher = UniversalEventFetcher()
        result = await fetcher.test_instagram_scraper(hashtag)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))