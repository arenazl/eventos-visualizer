"""
Servicio Agregador Principal de Eventos
Combina todas las fuentes de datos (APIs y Scrapers)
Normaliza, deduplica, geocodifica y enriquece con imágenes
"""

import asyncio
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import logging
from collections import defaultdict

# Importar todos los conectores
from services.buenos_aires_api import BuenosAiresDataConnector
from services.eventbrite_api import EventbriteLatamConnector
from services.ticketek_scraper import TicketekArgentinaScraper
from services.api_manager import APIManager
from services.geocoding_service import GeocodingService
from services.image_generator import EventImageGenerator as ImageGeneratorService
from services.intent_recognition import IntentRecognitionService
from models.universal_event import UniversalEvent, EventTiming, Location, PriceRange

logger = logging.getLogger(__name__)

class EventAggregatorService:
    """
    Servicio principal que:
    1. Obtiene eventos de múltiples fuentes
    2. Normaliza al formato universal
    3. Deduplica eventos similares
    4. Geocodifica ubicaciones
    5. Genera imágenes faltantes
    6. Aplica filtros por radio
    """
    
    def __init__(self):
        # Inicializar conectores
        self.connectors = {
            'buenos_aires_data': BuenosAiresDataConnector(),
            'eventbrite': EventbriteLatamConnector(),
            'ticketek_argentina': TicketekArgentinaScraper()
        }
        
        # Inicializar gestor de APIs adicionales
        self.api_manager = APIManager()
        
        # Servicios de enriquecimiento
        self.geocoding = GeocodingService()
        self.image_generator = ImageGeneratorService()
        self.intent_recognition = IntentRecognitionService()
        
        # Cache de eventos
        self.event_cache = {}
        self.cache_duration = timedelta(minutes=30)
        
        # Estadísticas
        self.stats = defaultdict(int)
        
    async def fetch_all_events(
        self,
        location: Optional[str] = None,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        radius_km: Optional[int] = None,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene todos los eventos aplicando filtros
        
        Returns:
            Dict con eventos, estadísticas y metadatos
        """
        print(f"\n🌐 INICIANDO AGREGACIÓN DE EVENTOS")
        print(f"📍 Ubicación: {location or 'Global LATAM'}")
        print(f"📡 Radio: {radius_km}km" if radius_km else "")
        
        # Resetear estadísticas
        self.stats.clear()
        
        # Verificar cache
        cache_key = f"{location}_{radius_km}_{category}_{date_from}_{date_to}"
        if self._is_cached(cache_key):
            logger.info("📦 Retornando eventos desde cache")
            return self.event_cache[cache_key]['data']
        
        # PASO 1: Obtener eventos de todas las fuentes
        print("\n🔄 PASO 1: Obteniendo eventos de múltiples fuentes...")
        all_raw_events = await self._fetch_from_all_sources(location)
        
        # PASO 2: Normalizar al formato universal
        print("\n⚙️ PASO 2: Normalizando eventos al formato universal...")
        normalized_events = self._normalize_all_events(all_raw_events)
        
        # PASO 3: Deduplicar eventos similares
        print("\n🔍 PASO 3: Deduplicando eventos similares...")
        deduplicated_events = self._deduplicate_events(normalized_events)
        
        # PASO 4: Geocodificar ubicaciones faltantes
        print("\n📍 PASO 4: Geocodificando ubicaciones...")
        geocoded_events = await self._geocode_events(deduplicated_events)
        
        # PASO 5: Generar imágenes faltantes
        print("\n🎨 PASO 5: Generando imágenes faltantes...")
        events_with_images = await self._generate_missing_images(geocoded_events)
        
        # PASO 6: Aplicar filtros
        print("\n🎯 PASO 6: Aplicando filtros...")
        filtered_events = self._apply_filters(
            events_with_images,
            user_lat, user_lon, radius_km,
            category, date_from, date_to
        )
        
        # PASO 7: Ordenar eventos
        sorted_events = self._sort_events(filtered_events)
        
        # Preparar respuesta
        response = {
            'events': sorted_events,
            'total': len(sorted_events),
            'stats': dict(self.stats),
            'metadata': {
                'location': location,
                'radius_km': radius_km,
                'category': category,
                'generated_at': datetime.now().isoformat(),
                'cache_ttl': self.cache_duration.total_seconds()
            }
        }
        
        # Guardar en cache
        self.event_cache[cache_key] = {
            'data': response,
            'timestamp': datetime.now()
        }
        
        # Imprimir resumen
        print(f"\n✅ AGREGACIÓN COMPLETADA")
        print(f"📊 Estadísticas:")
        print(f"   • Total eventos: {self.stats['total_events']}")
        print(f"   • Eventos únicos: {self.stats['unique_events']}")
        print(f"   • Con geocodificación: {self.stats['geocoded']}")
        print(f"   • Imágenes generadas: {self.stats['images_generated']}")
        print(f"   • Fuentes activas: {self.stats['active_sources']}")
        
        return response
    
    async def fetch_events_with_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Obtiene eventos usando reconocimiento de intención del input del usuario
        
        Args:
            user_input: Input natural del usuario (ej: "Buenos Aires", "electrónica", "fiesta techno")
        """
        print(f"\n🤖 ANALIZANDO INTENCIÓN: '{user_input}'")
        
        # Obtener parámetros para todas las APIs
        intent_params = self.intent_recognition.get_all_api_parameters(user_input)
        
        print(f"   • Tipo de búsqueda: {intent_params['intent']['type']}")
        print(f"   • Confianza: {intent_params['intent']['confidence']:.2%}")
        print(f"   • Ubicación detectada: {intent_params['intent']['location']}")
        print(f"   • Categoría detectada: {intent_params['intent']['category']}")
        
        # Usar los parámetros para llamar a las APIs
        return await self._fetch_with_intent_params(intent_params['apis'])
    
    async def _fetch_with_intent_params(self, api_params: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Llama a las APIs con los parámetros específicos de cada una
        """
        all_events = {}
        tasks = []
        
        # Eventbrite
        if api_params.get('eventbrite', {}).get('location'):
            location = api_params['eventbrite']['location']
            tasks.append(('eventbrite', self.connectors['eventbrite'].fetch_events_by_location(location)))
        
        # Ticketek
        if api_params.get('ticketek', {}).get('category'):
            # Por ahora usar el fetch_all_events y filtrar por categoría después
            tasks.append(('ticketek_argentina', self.connectors['ticketek_argentina'].fetch_all_events()))
        
        # APIs adicionales con parámetros específicos
        if api_params.get('ticketmaster'):
            params = api_params['ticketmaster']
            if self.api_manager.apis['ticketmaster']['enabled'] and params.get('city'):
                tasks.append(('ticketmaster', self.api_manager.fetch_ticketmaster_events(params['city'])))
        
        # Ejecutar todas las tareas
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        # Procesar resultados
        for (source_name, _), result in zip(tasks, results):
            if isinstance(result, list):
                all_events[source_name] = result
                print(f"   • {source_name}: {len(result)} eventos")
            elif isinstance(result, Exception):
                logger.error(f"Error en {source_name}: {result}")
        
        # Procesar eventos con normalización, deduplicación, etc.
        normalized_events = self._normalize_all_events(all_events)
        deduplicated_events = self._deduplicate_events(normalized_events)
        geocoded_events = await self._geocode_events(deduplicated_events)
        final_events = await self._generate_missing_images(geocoded_events)
        
        return {
            'events': final_events,
            'total': len(final_events),
            'intent': api_params,
            'stats': dict(self.stats)
        }
    
    async def _fetch_from_all_sources(self, location: Optional[str]) -> Dict[str, List[Dict]]:
        """
        Obtiene eventos de todas las fuentes configuradas
        """
        all_events = {}
        tasks = []
        
        # Buenos Aires Data API (solo para Argentina)
        if not location or 'argentina' in location.lower() or 'buenos aires' in location.lower():
            tasks.append(('buenos_aires_data', self.connectors['buenos_aires_data'].fetch_all_events()))
            tasks.append(('ticketek_argentina', self.connectors['ticketek_argentina'].fetch_all_events()))
        
        # Eventbrite (global LATAM)
        if location:
            tasks.append(('eventbrite', self.connectors['eventbrite'].fetch_events_by_location(location)))
        else:
            tasks.append(('eventbrite', self.connectors['eventbrite'].fetch_all_latam_events()))
        
        # APIs adicionales (Ticketmaster, Bandsintown, SeatGeek)
        if location:
            # Ticketmaster
            if self.api_manager.apis['ticketmaster']['enabled']:
                tasks.append(('ticketmaster', self.api_manager.fetch_ticketmaster_events(location)))
            
            # Bandsintown
            if self.api_manager.apis['bandsintown']['enabled']:
                tasks.append(('bandsintown', self.api_manager.fetch_bandsintown_events(location=location)))
            
            # SeatGeek
            if self.api_manager.apis['seatgeek']['enabled']:
                tasks.append(('seatgeek', self.api_manager.fetch_seatgeek_events(location)))
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        # Procesar resultados
        for (source_name, _), result in zip(tasks, results):
            if isinstance(result, list):
                all_events[source_name] = result
                self.stats['active_sources'] += 1
                self.stats[f'{source_name}_events'] = len(result)
                print(f"   • {source_name}: {len(result)} eventos")
            elif isinstance(result, dict) and 'events' in result:
                all_events[source_name] = result['events']
                self.stats['active_sources'] += 1
                self.stats[f'{source_name}_events'] = len(result['events'])
                print(f"   • {source_name}: {len(result['events'])} eventos")
            elif isinstance(result, Exception):
                logger.error(f"Error en {source_name}: {result}")
                all_events[source_name] = []
        
        return all_events
    
    def _normalize_all_events(self, events_by_source: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Normaliza todos los eventos al formato universal
        """
        normalized = []
        
        for source, events in events_by_source.items():
            for event in events:
                try:
                    # Los conectores ya devuelven formato normalizado
                    # pero agregamos source info adicional
                    event['source'] = source
                    event['aggregated_at'] = datetime.now().isoformat()
                    normalized.append(event)
                    self.stats['total_events'] += 1
                    
                except Exception as e:
                    logger.error(f"Error normalizando evento de {source}: {e}")
                    continue
        
        return normalized
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """
        Deduplica eventos basado en similitud
        """
        unique_events = []
        seen_signatures: Set[str] = set()
        
        for event in events:
            # Crear firma única basada en título, fecha y lugar
            signature = self._generate_event_signature(event)
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_events.append(event)
                self.stats['unique_events'] += 1
            else:
                self.stats['duplicates_removed'] += 1
        
        print(f"   • Duplicados eliminados: {self.stats['duplicates_removed']}")
        return unique_events
    
    def _generate_event_signature(self, event: Dict) -> str:
        """
        Genera una firma única para detectar duplicados
        """
        # Normalizar título
        title = event.get('title', '').lower().strip()
        # Remover palabras comunes
        for word in ['el', 'la', 'de', 'en', 'y', 'con', 'the', 'of', 'and', 'in']:
            title = title.replace(f' {word} ', ' ')
        
        # Usar fecha de inicio
        date = str(event.get('start_datetime', ''))[:10]  # Solo fecha, no hora
        
        # Usar ubicación
        venue = event.get('venue_name', '').lower().strip()
        
        # Crear signature
        signature_string = f"{title}_{date}_{venue}"
        
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    async def _geocode_events(self, events: List[Dict]) -> List[Dict]:
        """
        Geocodifica eventos sin coordenadas
        """
        geocoded = []
        
        for event in events:
            # Si no tiene coordenadas, intentar geocodificar
            if not event.get('latitude') or not event.get('longitude'):
                location_str = f"{event.get('venue_address', '')} {event.get('neighborhood', '')}"
                
                if location_str.strip():
                    coords = self.geocoding.geocode_location(location_str)
                    if coords:
                        event['latitude'] = coords['lat']
                        event['longitude'] = coords['lon']
                        event['geocoding_confidence'] = coords.get('confidence', 0)
                        self.stats['geocoded'] += 1
            
            # Enriquecer con información de localización
            if event.get('latitude') and event.get('longitude'):
                event['location_enriched'] = True
            
            geocoded.append(event)
        
        return geocoded
    
    async def _generate_missing_images(self, events: List[Dict]) -> List[Dict]:
        """
        Genera imágenes para eventos sin imagen
        """
        for event in events:
            if not event.get('image_url'):
                # Generar imagen basada en categoría y título
                image_url = await self.image_generator.generate_placeholder_image(
                    event_data=event
                )
                
                if image_url:
                    event['image_url'] = image_url
                    event['image_generated'] = True
                    self.stats['images_generated'] += 1
        
        return events
    
    def _apply_filters(
        self,
        events: List[Dict],
        user_lat: Optional[float],
        user_lon: Optional[float],
        radius_km: Optional[int],
        category: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> List[Dict]:
        """
        Aplica todos los filtros a los eventos
        """
        filtered = events
        
        # Filtro por radio geográfico
        if user_lat and user_lon and radius_km:
            print(f"   • Aplicando filtro de radio: {radius_km}km desde ({user_lat}, {user_lon})")
            filtered = self.geocoding.filter_events_by_radius(
                filtered, user_lat, user_lon, radius_km
            )
            self.stats['filtered_by_radius'] = len(events) - len(filtered)
        
        # Filtro por categoría
        if category:
            filtered = [e for e in filtered if e.get('category') == category]
            self.stats['filtered_by_category'] = category
        
        # Filtro por fecha
        if date_from:
            filtered = []
            for e in events:
                start_dt = e.get('start_datetime')
                if start_dt:
                    # Handle both string and datetime objects
                    if isinstance(start_dt, str):
                        dt = datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
                    elif isinstance(start_dt, datetime):
                        dt = start_dt
                    else:
                        continue
                    
                    if dt >= date_from:
                        filtered.append(e)
        
        if date_to:
            temp_filtered = []
            for e in (filtered if date_from else events):
                start_dt = e.get('start_datetime')
                if start_dt:
                    # Handle both string and datetime objects
                    if isinstance(start_dt, str):
                        dt = datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
                    elif isinstance(start_dt, datetime):
                        dt = start_dt
                    else:
                        continue
                    
                    if dt <= date_to:
                        temp_filtered.append(e)
            filtered = temp_filtered
        
        return filtered
    
    def _sort_events(self, events: List[Dict]) -> List[Dict]:
        """
        Ordena eventos por fecha y relevancia
        """
        # Ordenar por fecha de inicio
        try:
            events.sort(key=lambda e: e.get('start_datetime', ''), reverse=False)
        except:
            pass
        
        return events
    
    def _is_cached(self, key: str) -> bool:
        """
        Verifica si hay datos en cache válidos
        """
        if key not in self.event_cache:
            return False
        
        cached = self.event_cache[key]
        age = datetime.now() - cached['timestamp']
        
        return age < self.cache_duration
    
    async def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """
        Obtiene un evento específico por ID
        """
        # Buscar en cache primero
        for cache_entry in self.event_cache.values():
            for event in cache_entry.get('data', {}).get('events', []):
                if event.get('source_id') == event_id:
                    return event
        
        # Si no está en cache, buscar en todas las fuentes
        all_events = await self.fetch_all_events()
        
        for event in all_events.get('events', []):
            if event.get('source_id') == event_id:
                return event
        
        return None
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Retorna todas las categorías disponibles
        """
        return [
            {'id': 'music', 'name': 'Música', 'emoji': '🎵'},
            {'id': 'sports', 'name': 'Deportes', 'emoji': '⚽'},
            {'id': 'cultural', 'name': 'Cultural', 'emoji': '🎭'},
            {'id': 'art', 'name': 'Arte', 'emoji': '🎨'},
            {'id': 'tech', 'name': 'Tecnología', 'emoji': '💻'},
            {'id': 'food', 'name': 'Gastronomía', 'emoji': '🍴'},
            {'id': 'nightlife', 'name': 'Vida Nocturna', 'emoji': '🌃'},
            {'id': 'theater', 'name': 'Teatro', 'emoji': '🎭'},
            {'id': 'conference', 'name': 'Conferencias', 'emoji': '🎤'},
            {'id': 'workshop', 'name': 'Talleres', 'emoji': '🛠️'},
            {'id': 'family', 'name': 'Familiar', 'emoji': '👨‍👩‍👧‍👦'},
            {'id': 'festival', 'name': 'Festivales', 'emoji': '🎆'},
            {'id': 'wellness', 'name': 'Bienestar', 'emoji': '🧘'},
            {'id': 'education', 'name': 'Educación', 'emoji': '🎓'}
        ]


# Función de prueba
async def test_aggregator():
    """
    Prueba el servicio agregador completo
    """
    print("🌟 PROBANDO SERVICIO AGREGADOR DE EVENTOS\n")
    
    aggregator = EventAggregatorService()
    
    # Prueba 1: Obtener eventos de Buenos Aires con radio de 50km
    print("📍 TEST 1: Buenos Aires - Radio 50km")
    result = await aggregator.fetch_all_events(
        location="Buenos Aires",
        user_lat=-34.6037,
        user_lon=-58.3816,
        radius_km=50
    )
    
    print(f"\n📦 Eventos encontrados: {result['total']}")
    
    # Mostrar algunos eventos
    for event in result['events'][:5]:
        print(f"\n🎫 {event['title']}")
        print(f"   📍 {event.get('venue_name', 'Sin venue')}")
        print(f"   📅 {event.get('start_datetime', 'Sin fecha')}")
        print(f"   🏷️ {event.get('category', 'Sin categoría')}")
        print(f"   🔗 Fuente: {event['source']}")
        print(f"   🌆 {'Con imagen' if event.get('image_url') else 'Sin imagen'}")
        print(f"   📡 {'Geocodificado' if event.get('location_enriched') else 'Sin geocodificar'}")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_aggregator())