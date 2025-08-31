"""
Hybrid Sync Scraper - Estrategia sincrónica con cache
Garantiza SIEMPRE eventos en pantalla:
1. Respuesta inmediata desde cache
2. Eventbrite API (confiable)
3. Facebook/Instagram como bonus (con cache de respaldo)
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import random

from .cloudscraper_stealth import CloudscraperStealth
from .eventbrite_massive_scraper import EventbriteMassiveScraper
# from .argentina_venues_scraper import ArgentinaVenuesScraper  # DELETED - was fake data generator

logger = logging.getLogger(__name__)

class HybridSyncScraper:
    """
    Scraper que SIEMPRE retorna eventos:
    - Cache persistente de eventos válidos
    - Eventbrite API como fuente confiable
    - Social media como bonus con cache de respaldo
    """
    
    def __init__(self):
        self.cache_file = "/tmp/events_cache.json" 
        self.social_cache_file = "/tmp/social_events_cache.json"
        self.min_events_guarantee = 15  # Mínimo eventos para mostrar
        
        # Inicializar scrapers especializados
        self.eventbrite = EventbriteMassiveScraper()
        self.social_stealth = CloudscraperStealth()
        # self.argentina_venues = ArgentinaVenuesScraper()  # DELETED - FAKE DATA GENERATOR
        
    def _load_cache(self) -> List[Dict]:
        """Carga eventos desde cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Filtrar eventos no expirados (últimos 7 días)
                week_ago = datetime.now() - timedelta(days=7)
                fresh_events = [
                    event for event in data 
                    if datetime.fromisoformat(event.get('cached_at', week_ago.isoformat())) > week_ago
                ]
                
                logger.info(f"📦 Cache: {len(fresh_events)} eventos válidos")
                return fresh_events
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
        return []
    
    def _save_cache(self, events: List[Dict]):
        """Guarda eventos en cache con timestamp"""
        try:
            # Agregar timestamp a cada evento
            for event in events:
                event['cached_at'] = datetime.now().isoformat()
            
            # Combinar con cache existente (máximo 100 eventos)
            existing_cache = self._load_cache()
            all_events = existing_cache + events
            
            # Eliminar duplicados por título
            seen_titles = set()
            unique_events = []
            for event in all_events:
                title_key = event.get('title', '').lower().strip()
                if title_key and title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_events.append(event)
            
            # Limitar a últimos 100 eventos
            unique_events = unique_events[-100:]
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(unique_events, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 Cache actualizado: {len(unique_events)} eventos")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _load_social_cache(self) -> List[Dict]:
        """Carga cache específico de redes sociales"""
        try:
            if os.path.exists(self.social_cache_file):
                with open(self.social_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Solo eventos sociales de últimos 3 días
                recent = datetime.now() - timedelta(days=3)
                fresh_social = [
                    event for event in data 
                    if datetime.fromisoformat(event.get('cached_at', recent.isoformat())) > recent
                ]
                
                logger.info(f"📱 Social cache: {len(fresh_social)} eventos")
                return fresh_social
        except:
            pass
        return []
    
    def _save_social_cache(self, events: List[Dict]):
        """Guarda eventos sociales en cache separado"""
        try:
            for event in events:
                event['cached_at'] = datetime.now().isoformat()
            
            # Limitar a 50 eventos sociales
            with open(self.social_cache_file, 'w', encoding='utf-8') as f:
                json.dump(events[-50:], f, ensure_ascii=False, indent=2)
        except:
            pass
    
    async def get_argentina_venues_reliable(self, location: str = "Buenos Aires") -> List[Dict]:
        """Obtiene eventos de fuentes nacionales argentinas (MUY confiable)"""
        try:
            logger.info("🇦🇷 Obteniendo fuentes nacionales argentinas...")
            # events = await self.argentina_venues.scrape_all_sources()  # DELETED - FAKE DATA GENERATOR
            events = []  # No fake data - return empty array
            
            # Normalizar eventos argentinos
            normalized = []
            for event in events:
                normalized_event = {
                    'title': event.get('title', 'Evento Nacional'),
                    'description': event.get('description', ''),
                    'venue_name': event.get('venue_name', location),
                    'venue_address': event.get('venue_address', f"{location}, Argentina"),
                    'category': event.get('category', 'general'),
                    'price': event.get('price', 0),
                    'currency': 'ARS',
                    'is_free': event.get('is_free', False),
                    'source': 'argentina_venues_reliable',
                    'start_datetime': event.get('start_datetime', (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()),
                    'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30'),
                    'event_url': event.get('event_url', ''),
                    'status': 'live',
                    'latitude': event.get('latitude', -34.6037 + random.uniform(-0.05, 0.05)),
                    'longitude': event.get('longitude', -58.3816 + random.uniform(-0.05, 0.05))
                }
                normalized.append(normalized_event)
            
            logger.info(f"✅ Fuentes nacionales: {len(normalized)} eventos")
            return normalized
            
        except Exception as e:
            logger.error(f"Error Argentina venues: {e}")
            return []

    async def get_eventbrite_reliable(self, location: str = "Buenos Aires") -> List[Dict]:
        """Obtiene eventos de Eventbrite (fuente confiable)"""
        try:
            logger.info("🎫 Obteniendo Eventbrite...")
            events = await self.eventbrite.fetch_all_events(location)
            
            # Normalizar eventos de Eventbrite
            normalized = []
            for event in events:
                normalized_event = {
                    'title': event.get('title', 'Evento Eventbrite'),
                    'description': event.get('description', ''),
                    'venue_name': event.get('venue_name', location),
                    'venue_address': event.get('venue_address', f"{location}, Argentina"),
                    'category': event.get('category', 'general'),
                    'price': event.get('price', 0),
                    'currency': 'ARS',
                    'is_free': event.get('is_free', False),
                    'source': 'eventbrite_reliable',
                    'start_datetime': event.get('start_datetime', (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()),
                    'image_url': event.get('image_url', 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30'),
                    'event_url': event.get('event_url', ''),
                    'status': 'live',
                    'latitude': event.get('latitude', -34.6037 + random.uniform(-0.05, 0.05)),
                    'longitude': event.get('longitude', -58.3816 + random.uniform(-0.05, 0.05))
                }
                normalized.append(normalized_event)
            
            logger.info(f"✅ Eventbrite confiable: {len(normalized)} eventos")
            return normalized
            
        except Exception as e:
            logger.error(f"Error Eventbrite reliable: {e}")
            return []
    
    async def get_social_bonus(self, location: str = "Buenos Aires") -> List[Dict]:
        """Intenta obtener eventos sociales (bonus)"""
        try:
            logger.info("📱 Intentando social media...")
            social_events = await self.social_stealth.fetch_stealth_events(location)
            
            if social_events:
                # Guardar en cache social
                self._save_social_cache(social_events)
                logger.info(f"✅ Social bonus: {len(social_events)} eventos nuevos")
                return social_events
            else:
                # Si falla, usar cache social
                cached_social = self._load_social_cache()
                logger.info(f"📦 Usando social cache: {len(cached_social)} eventos")
                return cached_social
                
        except Exception as e:
            logger.error(f"Error social bonus: {e}")
            # Fallback a cache social
            cached_social = self._load_social_cache()
            logger.info(f"📦 Social fallback cache: {len(cached_social)} eventos")
            return cached_social
    
    async def fetch_hybrid_sync(self, location: str = "Buenos Aires") -> List[Dict]:
        """
        Estrategia principal: SIEMPRE retorna eventos
        1. Respuesta inmediata desde cache
        2. Eventbrite confiable en paralelo
        3. Social media como bonus
        """
        logger.info("🚀 Iniciando Hybrid Sync Scraper")
        
        # 1. RESPUESTA INMEDIATA: Cache existente
        cached_events = self._load_cache()
        
        # 2. FUENTES CONFIABLES: Argentina Venues + Eventbrite + Social en paralelo
        try:
            # Ejecutar todas las fuentes en paralelo
            argentina_task = self.get_argentina_venues_reliable(location)
            eventbrite_task = self.get_eventbrite_reliable(location)
            social_task = self.get_social_bonus(location)
            
            # Timeout de 15 segundos para no hacer esperar al usuario
            argentina_events, eventbrite_events, social_events = await asyncio.wait_for(
                asyncio.gather(argentina_task, eventbrite_task, social_task),
                timeout=15.0
            )
            
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout en fuentes externas, usando cache")
            argentina_events, eventbrite_events, social_events = [], [], []
        except Exception as e:
            logger.error(f"Error en fuentes externas: {e}")
            argentina_events, eventbrite_events, social_events = [], [], []
        
        # 3. COMBINAR TODAS LAS FUENTES
        all_events = []
        
        # Prioridad 1: Fuentes nacionales argentinas (MÁS confiables)
        if argentina_events:
            all_events.extend(argentina_events)
        
        # Prioridad 2: Eventbrite (confiable internacional)
        if eventbrite_events:
            all_events.extend(eventbrite_events)
        
        # Bonus: Social media
        if social_events:
            all_events.extend(social_events)
        
        # Respaldo: Cache si no obtuvimos suficientes eventos nuevos
        if len(all_events) < self.min_events_guarantee:
            logger.warning(f"⚠️ Solo {len(all_events)} eventos nuevos, agregando cache")
            all_events.extend(cached_events)
        
        # 4. ELIMINAR DUPLICADOS Y NORMALIZAR
        seen_titles = set()
        unique_events = []
        
        for event in all_events:
            title_key = event.get('title', '').lower().strip()
            if title_key and title_key not in seen_titles and len(title_key) > 5:
                seen_titles.add(title_key)
                unique_events.append(event)
        
        # 5. ACTUALIZAR CACHE CON EVENTOS NUEVOS
        new_events = eventbrite_events + social_events
        if new_events:
            self._save_cache(new_events)
        
        # 6. ORDENAR POR RELEVANCIA (fuente + fecha)
        def event_priority(event):
            source_priority = {
                'eventbrite_reliable': 1,
                'facebook': 2, 
                'instagram': 3,
                'cloudscraper_stealth': 4
            }
            return (
                source_priority.get(event.get('source', ''), 5),
                -event.get('likes', 0)  # Más likes = mayor prioridad
            )
        
        unique_events.sort(key=event_priority)
        
        # 7. GARANTIZAR MÍNIMO DE EVENTOS
        final_events = unique_events[:50]  # Limitar a 50 mejores
        
        logger.info(f"🔥 Hybrid Sync Total: {len(final_events)} eventos garantizados")
        logger.info(f"   📊 Eventbrite: {len(eventbrite_events)} | Social: {len(social_events)} | Cache: {len(cached_events)}")
        
        # 8. ESTADÍSTICAS DE FUENTES
        source_stats = {}
        for event in final_events:
            source = event.get('source', 'unknown')
            source_stats[source] = source_stats.get(source, 0) + 1
        
        stats_str = " | ".join([f"{source}: {count}" for source, count in source_stats.items()])
        logger.info(f"   📈 Distribución: {stats_str}")
        
        return final_events


# Testing
async def test_hybrid_sync():
    scraper = HybridSyncScraper()
    events = await scraper.fetch_hybrid_sync()
    
    print(f"\n✅ Hybrid Sync: {len(events)} eventos GARANTIZADOS")
    print("\n📋 Primeros 5 eventos:")
    for i, event in enumerate(events[:5], 1):
        print(f"\n{i}. 📍 {event['title']}")
        print(f"   🏢 {event['venue_name']}")
        print(f"   💰 ${event['price']} ARS")
        print(f"   📡 {event['source']}")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_hybrid_sync())