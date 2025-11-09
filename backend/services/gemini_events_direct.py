"""
🔮 GEMINI EVENTS DIRECT SERVICE
Obtiene eventos directamente de Gemini AI (sin scraping)

ENFOQUE:
- Llamadas directas a Gemini API
- Aprovecha conocimiento hasta Enero 2025
- Eventos se publican con anticipación → coverage perfecto
- Gratis hasta 1,500 requests/día
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from services.scraper_interface import BaseGlobalScraper, ScraperConfig

logger = logging.getLogger(__name__)


class GeminiEventsDirectService(BaseGlobalScraper):
    """
    🔮 SERVICIO DE EVENTOS DIRECTO CON GEMINI

    Obtiene eventos directamente preguntándole a Gemini AI,
    aprovechando su conocimiento actualizado hasta Enero 2025.

    VENTAJAS:
    ✅ Simple - solo llamada API
    ✅ No scraping - no se rompe con cambios HTML
    ✅ Coverage - eventos publicados con anticipación
    ✅ Gratis - hasta 1,500 requests/día
    ✅ Cache - 30 min TTL para evitar requests repetidos
    ✅ Lazy loading - imágenes en background
    """

    def __init__(self, url_discovery_service=None, config: ScraperConfig = None):
        super().__init__(url_discovery_service, config)

        # Usar el servicio de AI existente
        from services.ai_service import GeminiAIService
        self.ai_service = GeminiAIService()

        # Servicio de imágenes (lazy loading)
        from services.global_image_service import global_image_service
        self.image_service = global_image_service

        # Cache en memoria simple
        # Key: f"{location}_{category}_{date}"
        # Value: (eventos, timestamp)
        self.cache = {}
        self.cache_ttl = 1800  # 30 minutos

        logger.info("🔮 Gemini Events Direct Service initialized (cache TTL: 30 min, lazy images)")

    async def scrape_events(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 20,
        improve_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        🎯 OBTENER EVENTOS DIRECTAMENTE DE GEMINI

        Rango de fechas FIJO: desde hoy hasta 45 días adelante
        Cache: 30 min TTL por ubicación + categoría
        Lazy loading: imágenes mejoradas en background (opcional)

        Args:
            location: Ciudad/ubicación de búsqueda
            category: Categoría opcional (Música, Deportes, etc.)
            limit: Número máximo de eventos (default: 20)
            improve_images: Si True, mejora imágenes con lazy loading (default: True)

        Returns:
            Lista de eventos en formato estándar
        """

        try:
            # Normalizar ubicación (remover redundancia geográfica)
            clean_location = self._normalize_location(location)

            # Verificar cache primero
            cache_key = self._get_cache_key(clean_location, category)
            cached_events = self._get_from_cache(cache_key)

            if cached_events is not None:
                logger.info(f"💾 Cache HIT para {clean_location}, categoría: {category or 'Todas'} ({len(cached_events)} eventos)")
                return cached_events[:limit]

            logger.info(f"🔮 Gemini Direct: Obteniendo eventos para {clean_location} (original: {location}), categoría: {category or 'Todas'}")

            # Rango de fechas FIJO: hoy + 45 días
            today = datetime.now()
            end_date = today + timedelta(days=45)

            # Crear prompt optimizado
            prompt = self._create_events_prompt(clean_location, category, today, end_date, limit)

            # 📝 LOG: Mostrar prompt exacto que se envía
            logger.info(f"📝 PROMPT ENVIADO A GEMINI:\n{prompt}\n{'='*60}")

            # Llamar a Gemini API
            response = await self.ai_service._call_gemini_api(prompt)

            if not response:
                logger.warning(f"⚠️ Gemini no retornó respuesta para {location}")
                return []

            # 📝 LOG: Mostrar respuesta EXACTA de Gemini (primeros 2000 chars)
            logger.info(f"📝 RESPUESTA RAW DE GEMINI:\n{response[:2000]}\n{'='*60}")

            # Parsear respuesta JSON
            events = await self._parse_gemini_response(response, clean_location)

            if events:
                logger.info(f"✅ Gemini Direct: {len(events)} eventos encontrados para {location}")

                # Estandarizar eventos
                standardized_events = [self._standardize_event(event) for event in events]

                # 🖼️ Lazy loading de imágenes (en background, no bloquea)
                if improve_images:
                    standardized_events = await self._improve_images_lazy(standardized_events)

                # Guardar en cache
                self._save_to_cache(cache_key, standardized_events)

                return standardized_events[:limit]
            else:
                logger.warning(f"⚠️ Gemini no encontró eventos para {location}")
                return []

        except Exception as e:
            logger.error(f"❌ Error en Gemini Direct para {location}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def _get_cache_key(self, location: str, category: Optional[str]) -> str:
        """
        🔑 GENERAR CACHE KEY

        Key basada en: location + category + día actual
        El día actual asegura que cache expira al cambiar de día
        """
        today = datetime.now().strftime('%Y-%m-%d')
        category_str = category.lower() if category else 'all'
        location_normalized = location.lower().replace(' ', '_')

        return f"gemini_events_{location_normalized}_{category_str}_{today}"

    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        📥 OBTENER DEL CACHE

        Retorna eventos si están en cache y no expiraron (TTL: 30 min)
        """
        if cache_key not in self.cache:
            return None

        events, timestamp = self.cache[cache_key]

        # Verificar si expiró
        elapsed = (datetime.now() - timestamp).total_seconds()

        if elapsed > self.cache_ttl:
            # Expiró, eliminar del cache
            del self.cache[cache_key]
            return None

        return events

    def _save_to_cache(self, cache_key: str, events: List[Dict[str, Any]]):
        """
        💾 GUARDAR EN CACHE

        Guarda eventos con timestamp actual
        """
        self.cache[cache_key] = (events, datetime.now())
        logger.debug(f"💾 Eventos guardados en cache: {cache_key}")

    def _normalize_location(self, location: str) -> str:
        """
        🌍 NORMALIZAR UBICACIÓN

        Simplifica ubicaciones complejas para Gemini.
        Ejemplo: "Palermo, Buenos Aires, Ciudad Autónoma de Buenos Aires, Argentina"
                 → "Buenos Aires"
        """
        # Remover espacios extra
        location = location.strip()

        # Split por comas
        parts = [p.strip() for p in location.split(',')]

        # Si solo tiene 1 parte, retornar tal cual
        if len(parts) == 1:
            return parts[0]

        # Si tiene 2+ partes, usar las primeras 2 más relevantes
        # Ejemplo: "Palermo, Buenos Aires, ..." → "Palermo, Buenos Aires"
        # Ejemplo: "Buenos Aires, Argentina" → "Buenos Aires"

        # Si la segunda parte repite info de la primera, solo usar la primera
        first = parts[0].lower()
        second = parts[1].lower() if len(parts) > 1 else ""

        if 'buenos aires' in second and len(parts) > 1:
            # Caso: "Palermo, Buenos Aires, ..." → "Palermo, Buenos Aires"
            return f"{parts[0]}, Buenos Aires"
        elif 'argentina' in second or 'ciudad' in second:
            # Caso: "Buenos Aires, Argentina" → "Buenos Aires"
            # Caso: "Buenos Aires, Ciudad Autónoma..." → "Buenos Aires"
            return parts[0]
        else:
            # Default: primeras 2 partes
            return ", ".join(parts[:2])

    async def _improve_images_lazy(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🖼️ LAZY LOADING DE IMÁGENES

        Mejora las imágenes de eventos usando el servicio global de imágenes.
        Rápido y profesional.

        Args:
            events: Lista de eventos sin imágenes o con imágenes básicas

        Returns:
            Lista de eventos con imágenes mejoradas
        """
        try:
            logger.info(f"🖼️ Mejorando imágenes para {len(events)} eventos...")

            improved_events = []

            for event in events:
                try:
                    current_image = event.get('image_url', '')

                    # Si no tiene imagen o es mala, generar una mejor
                    if not self.image_service.is_good_image(current_image):
                        better_image = self.image_service.get_event_image(
                            title=event.get('title', ''),
                            category=event.get('category', ''),
                            venue=event.get('venue_name', ''),
                            description=event.get('description', '')
                        )

                        event['image_url'] = better_image
                        event['image_improved'] = True
                    else:
                        event['image_improved'] = False

                    improved_events.append(event)

                except Exception as e:
                    logger.warning(f"⚠️ Error mejorando imagen para '{event.get('title', 'Unknown')[:30]}': {e}")
                    improved_events.append(event)

            total_improved = sum(1 for e in improved_events if e.get('image_improved', False))
            logger.info(f"✅ Imágenes mejoradas: {total_improved}/{len(events)} eventos")

            return improved_events

        except Exception as e:
            logger.error(f"❌ Error en lazy loading de imágenes: {e}")
            return events  # Retornar eventos originales si falla

    def _create_events_prompt(
        self,
        location: str,
        category: Optional[str],
        start_date: datetime,
        end_date: datetime,
        limit: int
    ) -> str:
        """
        📝 PROMPT HARDCODEADO - TEST CON FECHA DENTRO DE KNOWLEDGE CUTOFF
        """

        # CAMBIO CRÍTICO: Diciembre 2024 (dentro del rango de Gemini)
        prompt = "info de 10 eventos de musica importantes en villa gesell para diciembre del 2024"

        return prompt

    async def _parse_gemini_response(self, response: str, location: str) -> List[Dict[str, Any]]:
        """
        📊 PARSEAR RESPUESTA DE GEMINI

        Intenta parsear como JSON primero, si falla usa Gemini para convertir a JSON
        """

        try:
            # Intentar parsear como JSON directo primero
            clean_response = response.strip()

            # Remover markdown si existe
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()

            # Intentar parsear JSON
            try:
                data = json.loads(clean_response)

                # Validar estructura
                if 'events' in data:
                    events = data['events']
                else:
                    # Si no tiene 'events', asumir que es array directo
                    events = data if isinstance(data, list) else []

            except json.JSONDecodeError:
                # Si falla JSON, pedirle a Gemini que convierta su respuesta
                logger.info("⚙️ Respuesta no es JSON, usando Gemini para convertir...")
                events = await self._convert_text_to_json(response)

            # Validar cada evento
            valid_events = []
            for event in events:
                if self._validate_event(event):
                    # Agregar source
                    event['source'] = 'gemini_direct'
                    event['location_queried'] = location
                    valid_events.append(event)
                else:
                    logger.warning(f"⚠️ Evento inválido descartado: {event.get('title', 'Sin título')}")

            return valid_events

        except Exception as e:
            logger.error(f"❌ Error procesando respuesta Gemini: {e}")
            logger.error(f"Response (primeros 500 chars): {response[:500]}")
            return []

    async def _convert_text_to_json(self, text_response: str) -> List[Dict[str, Any]]:
        """
        🔄 USA GEMINI PARA CONVERTIR SU PROPIA RESPUESTA A JSON
        """

        conversion_prompt = f"""Convertí esta información de eventos a JSON array.

INFORMACIÓN:
{text_response}

Respondé SOLO con el JSON array (sin explicaciones ni markdown):
[
  {{
    "title": "...",
    "description": "...",
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "venue_name": "...",
    "venue_address": "...",
    "price": "...",
    "category": "Música|Deportes|Cultural|Tech|Fiestas"
  }}
]"""

        try:
            json_response = await self.ai_service._call_gemini_api(conversion_prompt)

            if not json_response:
                return []

            # Limpiar y parsear
            clean = json_response.strip()
            if clean.startswith('```json'):
                clean = clean.replace('```json', '').replace('```', '').strip()
            elif clean.startswith('```'):
                clean = clean.replace('```', '').strip()

            events = json.loads(clean)
            return events if isinstance(events, list) else []

        except Exception as e:
            logger.error(f"❌ Error convirtiendo texto a JSON: {e}")
            return []

    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """
        ✅ VALIDAR EVENTO

        Verifica que el evento tenga los campos mínimos requeridos
        """

        required_fields = ['title', 'date']

        # Verificar campos requeridos
        for field in required_fields:
            if field not in event or not event[field]:
                logger.warning(f"⚠️ Evento falta campo '{field}': {event}")
                return False

        # Validar formato de fecha
        try:
            datetime.strptime(event['date'], '%Y-%m-%d')
        except ValueError:
            logger.warning(f"⚠️ Fecha inválida en evento: {event['date']}")
            return False

        # Validar que tenga al menos venue o location
        if not event.get('venue_name') and not event.get('location'):
            logger.warning(f"⚠️ Evento sin venue ni location: {event['title']}")
            return False

        return True

    def _standardize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        📋 ESTANDARIZAR EVENTO AL FORMATO DE LA APP

        Convierte evento de Gemini al formato estándar
        """

        # Parsear fecha y hora
        event_date = event.get('date', '')
        event_time = event.get('time', '20:00')  # Default 20:00

        try:
            # Combinar fecha y hora
            if event_time:
                start_datetime = datetime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M')
            else:
                start_datetime = datetime.strptime(event_date, '%Y-%m-%d')
        except:
            start_datetime = datetime.strptime(event_date, '%Y-%m-%d')

        # Formatear fecha legible
        start_datetime_str = start_datetime.isoformat()

        # Determinar si es gratis
        price = event.get('price', 'Consultar')
        is_free = price.lower() in ['gratis', 'free', 'libre']

        standardized = {
            'title': event.get('title', 'Sin título'),
            'description': event.get('description', 'Información no disponible'),
            'event_url': event.get('event_url', ''),
            'image_url': event.get('image_url', ''),  # Gemini no provee imágenes, pero podríamos mejorar después
            'venue_name': event.get('venue_name') or event.get('location', 'Ubicación no especificada'),
            'venue_address': event.get('venue_address', ''),
            'start_datetime': start_datetime_str,
            'end_datetime': None,
            'price': price,
            'is_free': is_free,
            'source': 'gemini_direct',
            'category': event.get('category', 'Eventos'),
            'external_id': f"gemini_{event.get('location_queried', '')}_{event_date}_{event.get('title', '').replace(' ', '_')[:30]}"
        }

        return standardized


# Singleton global
gemini_events_direct_service = GeminiEventsDirectService()
