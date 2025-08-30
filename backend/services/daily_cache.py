"""
Sistema de Cache Diario para Eventos
Una llamada por día a la mañana para evitar bloqueos
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import aiofiles

logger = logging.getLogger(__name__)

class DailyEventCache:
    """
    Cache que se actualiza una vez por día
    Evita saturar Facebook/Instagram
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Archivos de cache por fuente
        self.facebook_cache = self.cache_dir / "facebook_events.json"
        self.instagram_cache = self.cache_dir / "instagram_events.json"
        self.eventbrite_cache = self.cache_dir / "eventbrite_events.json"
        
        # Archivo de metadata (última actualización)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
    
    async def is_cache_fresh(self, hours_threshold: int = 12) -> bool:
        """
        Verifica si el cache es fresco (menos de X horas)
        """
        try:
            if not self.metadata_file.exists():
                return False
            
            async with aiofiles.open(self.metadata_file, 'r') as f:
                metadata = json.loads(await f.read())
            
            last_update = datetime.fromisoformat(metadata.get('last_update', '2000-01-01T00:00:00'))
            threshold = datetime.now() - timedelta(hours=hours_threshold)
            
            is_fresh = last_update > threshold
            
            if is_fresh:
                logger.info(f"✅ Cache is fresh (updated: {last_update.strftime('%H:%M')})")
            else:
                logger.info(f"⏰ Cache is stale (updated: {last_update.strftime('%H:%M')})")
            
            return is_fresh
            
        except Exception as e:
            logger.error(f"Error checking cache freshness: {e}")
            return False
    
    async def update_cache_from_scrapers(self) -> Dict[str, int]:
        """
        Actualiza el cache llamando a los scrapers reales
        SE LLAMA SOLO UNA VEZ POR DÍA
        """
        logger.info("🌅 Starting daily cache update...")
        results = {"facebook": 0, "instagram": 0, "eventbrite": 0}
        
        try:
            # Facebook (con cuidado para no bloquear)
            logger.info("📘 Updating Facebook cache...")
            from services.cloudscraper_events import CloudscraperEvents
            facebook_scraper = CloudscraperEvents()
            
            facebook_events = await facebook_scraper.scrape_facebook_events("Buenos Aires")
            results["facebook"] = len(facebook_events)
            
            async with aiofiles.open(self.facebook_cache, 'w') as f:
                await f.write(json.dumps(facebook_events, indent=2, ensure_ascii=False))
            
            # Delay anti-bloqueo
            await asyncio.sleep(5)
            
            # Instagram (con cuidado para no bloquear)
            logger.info("📸 Updating Instagram cache...")
            instagram_events = await facebook_scraper.scrape_instagram_events("Buenos Aires")
            results["instagram"] = len(instagram_events)
            
            async with aiofiles.open(self.instagram_cache, 'w') as f:
                await f.write(json.dumps(instagram_events, indent=2, ensure_ascii=False))
            
            # Delay anti-bloqueo
            await asyncio.sleep(5)
            
            # Eventbrite (más confiable, se puede llamar más seguido)
            logger.info("🎫 Updating Eventbrite cache...")
            from services.lightweight_scraper import LightweightEventScraper
            eventbrite_scraper = LightweightEventScraper()
            
            eventbrite_events = await eventbrite_scraper.fetch_all_events("Buenos Aires")
            results["eventbrite"] = len(eventbrite_events)
            
            async with aiofiles.open(self.eventbrite_cache, 'w') as f:
                await f.write(json.dumps(eventbrite_events, indent=2, ensure_ascii=False))
            
            # Actualizar metadata
            metadata = {
                "last_update": datetime.now().isoformat(),
                "events_count": results,
                "next_update": (datetime.now() + timedelta(hours=12)).isoformat()
            }
            
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
            
            total_events = sum(results.values())
            logger.info(f"✅ Cache updated: {total_events} total events")
            logger.info(f"📊 Facebook: {results['facebook']}, Instagram: {results['instagram']}, Eventbrite: {results['eventbrite']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error updating cache: {e}")
            return results
    
    async def get_cached_events(self, source: str) -> List[Dict]:
        """
        Obtiene eventos desde cache (sin llamar scrapers)
        """
        cache_files = {
            "facebook": self.facebook_cache,
            "instagram": self.instagram_cache, 
            "eventbrite": self.eventbrite_cache
        }
        
        cache_file = cache_files.get(source)
        if not cache_file or not cache_file.exists():
            logger.warning(f"⚠️ No cache found for {source}")
            return []
        
        try:
            async with aiofiles.open(cache_file, 'r') as f:
                events = json.loads(await f.read())
            
            logger.info(f"📋 Serving {len(events)} cached {source} events")
            return events
            
        except Exception as e:
            logger.error(f"Error reading {source} cache: {e}")
            return []
    
    async def get_all_cached_events(self) -> List[Dict]:
        """
        Obtiene todos los eventos de todas las fuentes desde cache
        """
        all_events = []
        
        sources = ["facebook", "instagram", "eventbrite"]
        for source in sources:
            events = await self.get_cached_events(source)
            all_events.extend(events)
        
        logger.info(f"📦 Total cached events: {len(all_events)}")
        return all_events
    
    async def ensure_cache_is_ready(self) -> bool:
        """
        Se asegura de que el cache esté listo
        Si está stale, lo actualiza
        """
        if await self.is_cache_fresh():
            return True
        
        logger.info("🔄 Cache is stale, updating...")
        await self.update_cache_from_scrapers()
        return True
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache
        """
        try:
            if not self.metadata_file.exists():
                return {"status": "no_cache", "last_update": None}
            
            async with aiofiles.open(self.metadata_file, 'r') as f:
                metadata = json.loads(await f.read())
            
            last_update = datetime.fromisoformat(metadata.get('last_update', '2000-01-01T00:00:00'))
            hours_old = (datetime.now() - last_update).total_seconds() / 3600
            
            return {
                "status": "fresh" if hours_old < 12 else "stale",
                "last_update": metadata.get('last_update'),
                "hours_old": round(hours_old, 1),
                "events_count": metadata.get('events_count', {}),
                "next_update": metadata.get('next_update')
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}

# Instancia global
daily_cache = DailyEventCache()