"""
Progressive Sync Scraper - Sistema de carga progresiva por velocidad
Envía datos en 3 fases según tiempo de respuesta de cada fuente:
1. 2 segundos: Cache + BD (INMEDIATO)
2. 4 segundos: Fuentes nacionales + Eventbrite (RÁPIDO)  
3. 8 segundos: Facebook + Instagram (LENTO)
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, AsyncGenerator, Callable
import logging
import random

# from .argentina_venues_scraper import ArgentinaVenuesScraper  # DELETED - was fake data generator
from .eventbrite_massive_scraper import EventbriteMassiveScraper
from .cloudscraper_stealth import CloudscraperStealth

logger = logging.getLogger(__name__)

class ProgressiveSyncScraper:
    """
    Scraper que retorna eventos progresivamente según velocidad de fuente:
    - Fase 1 (0-2s): Cache + DB local
    - Fase 2 (2-4s): Fuentes confiables (nacionales + Eventbrite)
    - Fase 3 (4-8s): Fuentes sociales (Facebook + Instagram)
    """
    
    def __init__(self):
        self.cache_file = "/tmp/events_progressive_cache.json"
        self.timing_stats_file = "/tmp/source_timing_stats.json"
        
        # Inicializar scrapers
        # self.argentina_venues = ArgentinaVenuesScraper()  # DELETED - FAKE DATA GENERATOR
        self.eventbrite = EventbriteMassiveScraper()
        self.social_stealth = CloudscraperStealth()
        
        # Configuración de fases por tiempo de respuesta
        self.phases = {
            'instant': {  # 0-2 segundos
                'max_time': 2,
                'sources': ['cache', 'database'],
                'priority': 1
            },
            'fast': {     # 2-4 segundos  
                'max_time': 4,
                'sources': ['argentina_venues', 'eventbrite'],
                'priority': 2
            },
            'slow': {     # 4-8 segundos
                'max_time': 8,
                'sources': ['facebook', 'instagram'],
                'priority': 3
            }
        }
    
    def _load_cache(self) -> List[Dict]:
        """Carga cache instantáneo"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Eventos frescos de últimos 3 días
                cutoff = datetime.now() - timedelta(days=3)
                fresh_events = [
                    event for event in data 
                    if datetime.fromisoformat(event.get('cached_at', cutoff.isoformat())) > cutoff
                ]
                
                logger.info(f"⚡ Cache instantáneo: {len(fresh_events)} eventos")
                return fresh_events
        except:
            pass
        return []
    
    def _save_timing_stats(self, source: str, duration: float):
        """Guarda estadísticas de tiempo de respuesta"""
        try:
            stats = {}
            if os.path.exists(self.timing_stats_file):
                with open(self.timing_stats_file, 'r') as f:
                    stats = json.load(f)
            
            if source not in stats:
                stats[source] = {'times': [], 'avg': 0}
            
            # Mantener últimas 10 mediciones
            stats[source]['times'].append(duration)
            stats[source]['times'] = stats[source]['times'][-10:]
            stats[source]['avg'] = sum(stats[source]['times']) / len(stats[source]['times'])
            stats[source]['last_update'] = datetime.now().isoformat()
            
            with open(self.timing_stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving timing stats: {e}")
    
    async def _fetch_with_timing(self, source_name: str, fetch_func: Callable) -> Dict:
        """Ejecuta función de fetch y mide tiempo"""
        start_time = time.time()
        try:
            events = await fetch_func()
            duration = time.time() - start_time
            
            self._save_timing_stats(source_name, duration)
            
            return {
                'source': source_name,
                'events': events or [],
                'count': len(events or []),
                'duration': duration,
                'status': 'success'
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error in {source_name}: {e}")
            
            return {
                'source': source_name,
                'events': [],
                'count': 0,
                'duration': duration,
                'status': 'error',
                'error': str(e)
            }
    
    async def phase_1_instant(self, location: str) -> Dict:
        """Fase 1: Datos instantáneos (0-2 segundos)"""
        logger.info("⚡ FASE 1: Carga instantánea")
        
        # Solo cache - debe ser instantáneo
        cached_events = self._load_cache()
        
        return {
            'phase': 1,
            'name': 'instant',
            'sources': [{
                'source': 'cache',
                'events': cached_events,
                'count': len(cached_events),
                'duration': 0.1,
                'status': 'success'
            }],
            'total_events': len(cached_events),
            'duration': 0.1
        }
    
    async def phase_2_fast(self, location: str) -> Dict:
        """Fase 2: Fuentes rápidas (2-4 segundos)"""
        logger.info("🚀 FASE 2: Fuentes rápidas")
        
        # Ejecutar fuentes rápidas en paralelo
        # argentina_task = self._fetch_with_timing(  # DELETED - FAKE DATA GENERATOR
        #     'argentina_venues',  # DELETED - FAKE DATA GENERATOR
        #     lambda: self.argentina_venues.scrape_all_sources()  # DELETED - FAKE DATA GENERATOR
        # )  # DELETED - FAKE DATA GENERATOR
        argentina_task = self._fetch_with_timing(
            'argentina_venues_disabled', 
            lambda: []  # Return empty - no fake data
        )
        
        eventbrite_task = self._fetch_with_timing(
            'eventbrite', 
            lambda: self.eventbrite.fetch_all_events(location)
        )
        
        # Timeout de 5 segundos para fuentes "rápidas"
        try:
            sources_results = await asyncio.wait_for(
                asyncio.gather(argentina_task, eventbrite_task),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout en fase rápida")
            sources_results = []
        
        # Combinar eventos
        all_events = []
        total_duration = 0
        
        for result in sources_results:
            if result['events']:
                all_events.extend(result['events'])
            total_duration = max(total_duration, result['duration'])
        
        return {
            'phase': 2,
            'name': 'fast',
            'sources': sources_results,
            'total_events': len(all_events),
            'duration': total_duration
        }
    
    async def phase_3_slow(self, location: str) -> Dict:
        """Fase 3: Fuentes lentas (4-8 segundos)"""
        logger.info("🐌 FASE 3: Fuentes lentas (social media)")
        
        # Solo redes sociales con timeout estricto
        social_task = self._fetch_with_timing(
            'social_media',
            lambda: self.social_stealth.fetch_stealth_events(location)
        )
        
        # Timeout de 10 segundos para redes sociales
        try:
            social_result = await asyncio.wait_for(social_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout en redes sociales")
            social_result = {
                'source': 'social_media',
                'events': [],
                'count': 0,
                'duration': 10.0,
                'status': 'timeout'
            }
        
        return {
            'phase': 3,
            'name': 'slow',
            'sources': [social_result],
            'total_events': social_result['count'],
            'duration': social_result['duration']
        }
    
    async def progressive_fetch_stream(self, location: str = "Buenos Aires") -> AsyncGenerator[Dict, None]:
        """
        Generator que devuelve eventos progresivamente en 3 fases
        Permite al frontend mostrar datos inmediatamente y actualizar progresivamente
        """
        logger.info("🎯 Iniciando Progressive Sync Stream")
        total_start = time.time()
        
        # FASE 1: INSTANTÁNEO (0-2s)
        phase1_start = time.time()
        phase1_result = await self.phase_1_instant(location)
        phase1_result['cumulative_time'] = time.time() - total_start
        
        logger.info(f"✅ Fase 1 completada: {phase1_result['total_events']} eventos en {phase1_result['duration']:.2f}s")
        yield phase1_result
        
        # FASE 2: RÁPIDO (2-4s)
        phase2_start = time.time()
        phase2_result = await self.phase_2_fast(location)
        phase2_result['cumulative_time'] = time.time() - total_start
        
        logger.info(f"✅ Fase 2 completada: {phase2_result['total_events']} eventos en {phase2_result['duration']:.2f}s")
        yield phase2_result
        
        # FASE 3: LENTO (4-8s) 
        phase3_start = time.time()
        phase3_result = await self.phase_3_slow(location)
        phase3_result['cumulative_time'] = time.time() - total_start
        
        logger.info(f"✅ Fase 3 completada: {phase3_result['total_events']} eventos en {phase3_result['duration']:.2f}s")
        yield phase3_result
        
        # RESUMEN FINAL
        total_time = time.time() - total_start
        total_events = (phase1_result['total_events'] + 
                       phase2_result['total_events'] + 
                       phase3_result['total_events'])
        
        final_summary = {
            'phase': 'summary',
            'name': 'final',
            'total_events': total_events,
            'total_duration': total_time,
            'phases_summary': {
                'instant': {
                    'events': phase1_result['total_events'],
                    'time': phase1_result['duration']
                },
                'fast': {
                    'events': phase2_result['total_events'], 
                    'time': phase2_result['duration']
                },
                'slow': {
                    'events': phase3_result['total_events'],
                    'time': phase3_result['duration']
                }
            }
        }
        
        logger.info(f"🎉 Progressive Sync completado: {total_events} eventos en {total_time:.2f}s")
        yield final_summary
    
    async def fetch_progressive_sync(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Versión no-stream que recolecta todos los resultados progresivos
        Para compatibilidad con APIs existentes
        """
        all_events = []
        phase_results = []
        
        async for phase_result in self.progressive_fetch_stream(location):
            if phase_result['phase'] != 'summary':
                phase_results.append(phase_result)
                
                # Extraer eventos de cada fuente
                for source in phase_result.get('sources', []):
                    if source['events']:
                        # Normalizar eventos con info de fase
                        for event in source['events']:
                            event['fetch_phase'] = phase_result['phase']
                            event['fetch_source'] = source['source']
                            event['fetch_duration'] = source['duration']
                            all_events.append(event)
        
        # Eliminar duplicados por título
        seen_titles = set()
        unique_events = []
        
        for event in all_events:
            title_key = event.get('title', '').lower().strip()
            if title_key and title_key not in seen_titles and len(title_key) > 5:
                seen_titles.add(title_key)
                unique_events.append(event)
        
        # Ordenar por fase (prioridad) y likes
        def event_priority(event):
            return (
                event.get('fetch_phase', 999),  # Fase más temprana primero
                -event.get('likes', 0)          # Más likes = mayor prioridad
            )
        
        unique_events.sort(key=event_priority)
        
        # Actualizar cache con eventos nuevos
        try:
            for event in unique_events:
                event['cached_at'] = datetime.now().isoformat()
                
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(unique_events[-100:], f, ensure_ascii=False, indent=2)
        except:
            pass
        
        logger.info(f"🔥 Progressive Sync Final: {len(unique_events)} eventos únicos")
        return unique_events


# Testing
async def test_progressive():
    scraper = ProgressiveSyncScraper()
    
    print("🎯 Testing Progressive Stream:")
    async for phase in scraper.progressive_fetch_stream():
        if phase['phase'] == 'summary':
            print(f"\n🎉 RESUMEN FINAL:")
            print(f"   Total: {phase['total_events']} eventos")
            print(f"   Tiempo total: {phase['total_duration']:.2f}s")
            for phase_name, stats in phase['phases_summary'].items():
                print(f"   {phase_name}: {stats['events']} eventos en {stats['time']:.2f}s")
        else:
            print(f"\n✅ Fase {phase['phase']} ({phase['name']}): {phase['total_events']} eventos en {phase.get('cumulative_time', 0):.2f}s")
    
    print("\n" + "="*50)
    print("🔥 Testing Progressive Sync (unified):")
    events = await scraper.fetch_progressive_sync()
    print(f"Total eventos: {len(events)}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_progressive())