"""
🔮 GEMINI FACTORY - El Único Scraper que Necesitas
Factory ultra-simplificado que SOLO usa Gemini Direct
"""

import logging
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class GeminiFactory:
    """
    🔮 GEMINI FACTORY - SIMPLE Y PODEROSO

    FILOSOFÍA:
    - Un solo scraper (Gemini Direct)
    - Ultra rápido (sin auto-discovery ni paralelización innecesaria)
    - Cache integrado (30 min TTL)
    - Lazy loading de imágenes automático

    VENTAJAS:
    ✅ Simple - solo 1 scraper, 0 complejidad
    ✅ Rápido - sin overhead de múltiples scrapers
    ✅ Gratis - hasta 1,500 req/día
    ✅ Global - funciona con cualquier ciudad del mundo
    ✅ Confiable - no se rompe con cambios de sitios web
    """

    # Cache en memoria para resultados de get_parent_location
    _parent_city_cache: Dict[str, Optional[str]] = {}

    def __init__(self):
        """Inicializa Gemini Factory"""
        logger.info("🔮 Gemini Factory inicializado - UN SOLO SCRAPER")

        # Importar Gemini Direct
        from services.gemini_events_direct import gemini_events_direct_service
        self.gemini_scraper = gemini_events_direct_service

        logger.info("✅ Gemini Direct Service cargado")

    async def execute_global_scrapers(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 10,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        🚀 EJECUTAR GEMINI DIRECT (ÚNICO SCRAPER)

        Args:
            location: Ubicación de búsqueda
            category: Categoría opcional (Música, Deportes, etc.)
            limit: Límite de eventos (default: 20)
            detected_country: País detectado (opcional)
            context_data: Contexto adicional (opcional)

        Returns:
            Lista de eventos de Gemini
        """

        start_time = time.time()

        logger.info(f"🔮 Ejecutando Gemini Direct para '{location}'")

        try:
            # Llamar a Gemini Direct (con improve_images=True por default)
            events = await self.gemini_scraper.scrape_events(
                location=location,
                category=category,
                limit=limit,
                improve_images=True  # Lazy loading de imágenes
            )

            execution_time = time.time() - start_time

            logger.info(f"✅ Gemini Direct: {len(events)} eventos en {execution_time:.2f}s")

            return events

        except Exception as e:
            logger.error(f"❌ Error en Gemini Direct: {e}")
            return []

    async def execute_global_scrapers_with_details(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 20,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        🚀 EJECUTAR CON DETALLES COMPLETOS

        Returns:
            Dict con eventos y detalles de ejecución
        """

        start_time = time.time()

        logger.info(f"🔮 Ejecutando Gemini Direct (con detalles) para '{location}'")

        try:
            # Llamar a Gemini Direct
            events = await self.gemini_scraper.scrape_events(
                location=location,
                category=category,
                limit=limit,
                improve_images=True
            )

            execution_time = time.time() - start_time

            # Preparar detalles
            scrapers_execution = {
                'scrapers_called': ['gemini_direct'],
                'total_scrapers': 1,
                'scrapers_info': [
                    {
                        'name': 'Gemini Direct',
                        'status': 'success',
                        'events_count': len(events),
                        'response_time': f"{execution_time:.2f}s",
                        'message': f'{len(events)} eventos obtenidos exitosamente'
                    }
                ],
                'summary': f'1/1 scrapers exitosos en {execution_time:.2f}s - {len(events)} eventos totales'
            }

            logger.info(f"✅ Gemini Direct: {len(events)} eventos en {execution_time:.2f}s")

            return {
                'events': events,
                'scrapers_execution': scrapers_execution
            }

        except Exception as e:
            logger.error(f"❌ Error en Gemini Direct: {e}")

            # Retornar error con detalles
            scrapers_execution = {
                'scrapers_called': ['gemini_direct'],
                'total_scrapers': 1,
                'scrapers_info': [
                    {
                        'name': 'Gemini Direct',
                        'status': 'failed',
                        'events_count': 0,
                        'response_time': '0.0s',
                        'message': str(e)
                    }
                ],
                'summary': f'0/1 scrapers exitosos - Error: {str(e)}'
            }

            return {
                'events': [],
                'scrapers_execution': scrapers_execution
            }

    async def execute_streaming(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 20,
        detected_country: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """
        🌊 STREAMING MODE (PARA COMPATIBILIDAD)

        Como solo hay un scraper, simplemente yield los resultados una vez

        Yields:
            Dict con resultados de Gemini Direct
        """

        logger.info(f"🌊 STREAMING MODE: Iniciando para '{location}'")

        start_time = time.time()

        try:
            # Llamar a Gemini Direct
            events = await self.gemini_scraper.scrape_events(
                location=location,
                category=category,
                limit=limit,
                improve_images=True
            )

            execution_time = time.time() - start_time

            # Yield único resultado
            yield {
                'scraper': 'gemini_direct',
                'events': events,
                'execution_time': f"{execution_time:.2f}s",
                'success': True,
                'error': None,
                'count': len(events)
            }

            logger.info(f"📡 STREAMED: Gemini Direct - {len(events)} eventos en {execution_time:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error streaming Gemini Direct: {e}")

            yield {
                'scraper': 'gemini_direct',
                'events': [],
                'execution_time': '0.0s',
                'success': False,
                'error': str(e),
                'count': 0
            }

        logger.info("🏁 Streaming completado - Gemini Direct procesado")

    async def _enrich_location_once(
        self,
        location: str,
        detected_country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        🌍 ENRIQUECIMIENTO DE UBICACIÓN CON CIUDADES CERCANAS O TOP CIUDADES DEL PAÍS

        Si la ubicación es un país → Muestra top 3 ciudades con más eventos
        Si la ubicación es una ciudad → Usa Gemini AI para ciudades cercanas

        Returns:
            Dict con ciudades cercanas o top ciudades del país
        """
        # Extraer país del location si viene con formato "Ciudad, País"
        if not detected_country and ',' in location:
            parts = location.split(',')
            if len(parts) >= 2:
                detected_country = parts[-1].strip()

        nearby_cities = []

        # 🌍 PASO 1: Verificar si la búsqueda es un PAÍS (no una ciudad)
        # Si es un país, mostrar las TOP 3 CIUDADES con más eventos
        try:
            from services.events_db_service import get_db_connection

            # Extraer solo el nombre del país/ciudad (eliminar ", country" o ", city")
            clean_location = location.split(',')[0].strip() if ',' in location else location

            conn = await get_db_connection()
            if conn:
                cursor = conn.cursor()

                # Buscar si hay eventos donde country = location (ej: "Peru", "Argentina")
                # Normalizar búsqueda para manejar acentos
                cursor.execute(
                    """SELECT COUNT(*) as event_count
                       FROM events
                       WHERE country = %s
                          OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(country, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') = %s""",
                    (clean_location, clean_location.lower())
                )
                country_event_count = cursor.fetchone()

                # Si encontramos eventos con ese país, obtener top 3 ciudades
                if country_event_count and country_event_count[0] > 0:
                    logger.info(f"🌍 '{clean_location}' es un país con {country_event_count[0]} eventos")

                    cursor.execute(
                        """SELECT city, COUNT(*) as event_count
                           FROM events
                           WHERE (country = %s OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(country, 'á','a'), 'é','e'), 'í','i'), 'ó','o'), 'ú','u') = %s)
                             AND city IS NOT NULL
                             AND city != ''
                           GROUP BY city
                           ORDER BY event_count DESC
                           LIMIT 3""",
                        (clean_location, clean_location.lower())
                    )
                    top_cities = cursor.fetchall()
                    nearby_cities = [city[0] for city in top_cities if city[0]]

                    cursor.close()
                    conn.close()

                    logger.info(f"✅ Top ciudades de {clean_location}: {', '.join(nearby_cities)}")

                    return {
                        'original': location,
                        'city': clean_location,
                        'state': '',
                        'country': clean_location,
                        'nearby_cities': nearby_cities[:3],
                        'needs_expansion': False
                    }

                cursor.close()
                conn.close()
        except Exception as db_err:
            logger.warning(f"⚠️ No se pudo verificar si '{location}' es un país: {db_err}")

        # 🏙️ PASO 2: Si no es un país, usar Gemini para ciudades cercanas
        try:
            from services.ai_service import GeminiAIService

            # Prompt para Gemini: Pedir CIUDADES POPULARES Y GRANDES
            prompt = f"""Dame las 3 CIUDADES MÁS GRANDES, POPULARES Y CONOCIDAS cercanas a "{location}" (máximo 200km).

🎯 PRIORIDAD ABSOLUTA:
- Ciudades GRANDES con más de 100,000 habitantes
- Ciudades CONOCIDAS internacionalmente o turísticas
- Ciudades con eventos culturales/deportivos importantes

❌ TOTALMENTE PROHIBIDO:
- Barrios de {location}
- Pueblos pequeños o suburbios
- Ciudades con menos de 50,000 habitantes

✅ OBLIGATORIO:
- SOLO ciudades importantes y conocidas
- Máximo 200km de distancia

EJEMPLOS:

Para "Lima" → {{"nearby_cities": ["Arequipa", "Cusco", "Trujillo"]}}
❌ MAL: ["Callao", "Huaral", "Chosica"]
✅ BIEN: ["Arequipa", "Cusco", "Trujillo"]

Para "Buenos Aires" → {{"nearby_cities": ["La Plata", "Rosario", "Córdoba"]}}
❌ MAL: ["San Isidro", "Tigre", "Quilmes"]
✅ BIEN: ["La Plata", "Rosario", "Córdoba"]

Para "Barcelona" → {{"nearby_cities": ["Valencia", "Zaragoza", "Tarragona"]}}
❌ MAL: ["Hospitalet", "Badalona", "Sabadell"]
✅ BIEN: ["Valencia", "Zaragoza", "Tarragona"]

Responde SOLO para "{location}":

{{
    "nearby_cities": ["Ciudad1", "Ciudad2", "Ciudad3"]
}}

RECUERDA: Solo ciudades GRANDES y CONOCIDAS. Solo el JSON."""

            # Crear instancia y llamar a Gemini
            service = GeminiAIService()
            response_text = await service._call_gemini_api(prompt)

            # Parsear JSON (limpiando markdown si existe)
            import json
            import re

            nearby_cities = []

            if response_text:
                # Limpiar markdown code blocks si existen (```json ... ``` o ``` ... ```)
                cleaned_text = response_text.strip()
                if cleaned_text.startswith('```'):
                    cleaned_text = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_text)
                    cleaned_text = re.sub(r'\n?```\s*$', '', cleaned_text)

                try:
                    # Parsear JSON limpio
                    data = json.loads(cleaned_text)
                    nearby_cities = data.get('nearby_cities', [])
                    if nearby_cities:
                        logger.info(f"✅ Ciudades para {location}: {', '.join(nearby_cities)}")
                except json.JSONDecodeError:
                    # Si aún falla, extraer con regex
                    json_match = re.search(r'\{[\s\S]*"nearby_cities"[\s\S]*\}', response_text)
                    if json_match:
                        try:
                            data = json.loads(json_match.group())
                            nearby_cities = data.get('nearby_cities', [])
                            if nearby_cities:
                                logger.info(f"✅ Ciudades para {location}: {', '.join(nearby_cities)}")
                        except:
                            pass

            return {
                'original': location,
                'city': location,
                'state': '',
                'country': detected_country or 'Argentina',
                'nearby_cities': nearby_cities[:3],  # Asegurar solo 3 ciudades máximo
                'needs_expansion': False
            }

        except Exception as e:
            # Si Gemini falla, consultar tabla cities en MySQL
            nearby_cities = []

            if detected_country:
                try:
                    from services.events_db_service import get_db_connection

                    conn = await get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT name FROM cities WHERE country = %s ORDER BY population DESC LIMIT 3",
                            (detected_country,)
                        )
                        rows = cursor.fetchall()
                        nearby_cities = [row[0] for row in rows]
                        cursor.close()
                        conn.close()
                except:
                    pass  # Si falla MySQL también, devuelve vacío

            return {
                'original': location,
                'city': location,
                'state': '',
                'country': detected_country or 'Argentina',
                'nearby_cities': nearby_cities,
                'needs_expansion': False
            }

    async def get_parent_location(self, location: str) -> Optional[str]:
        """
        🏙️ DETECTAR CIUDAD PRINCIPAL - Para ubicaciones que son parte de una ciudad más grande

        Ejemplos:
        - "Merlo" → "Buenos Aires"
        - "Tigre" → "Buenos Aires"
        - "La Boca" → "Buenos Aires"
        - "Medellín Centro" → "Medellín"

        Usa Gemini AI para detectar inteligentemente la ciudad principal.
        Con cache en memoria para evitar llamadas repetidas.

        Returns:
            Nombre de la ciudad principal, o None si la ubicación ya es la ciudad principal
        """
        # Normalizar para usar como key del cache (lowercase, sin espacios extras)
        cache_key = location.lower().strip()

        # 1. Revisar cache primero
        if cache_key in self._parent_city_cache:
            cached_result = self._parent_city_cache[cache_key]
            if cached_result:
                logger.info(f"⚡ Ciudad principal (cache): {location} → {cached_result}")
            else:
                logger.info(f"⚡ {location} es ciudad principal (cache)")
            return cached_result

        # 2. Si no está en cache, llamar a Gemini
        try:
            from services.ai_service import GeminiAIService

            logger.info(f"🔍 Consultando Gemini para detectar ciudad principal de: {location}")

            prompt = f"""¿Cuál es la ciudad/provincia principal de {location}?

Si {location} ya es la ciudad/provincia principal, responde: "PRINCIPAL"
Si {location} es parte de una ciudad/provincia más grande, responde SOLO con el nombre de esa ciudad/provincia."""

            service = GeminiAIService()
            response_text = await service._call_gemini_api(prompt)

            if response_text:
                response_cleaned = response_text.strip().strip('"').strip()

                # Si es principal, no hay ciudad padre
                if response_cleaned.upper() == "PRINCIPAL":
                    logger.info(f"ℹ️ {location} es ciudad principal")
                    # Guardar en cache
                    self._parent_city_cache[cache_key] = None
                    return None

                # Si hay respuesta, es la ciudad padre
                if response_cleaned and len(response_cleaned) < 100:
                    logger.info(f"✅ Ciudad principal detectada: {location} → {response_cleaned}")
                    # Guardar en cache
                    self._parent_city_cache[cache_key] = response_cleaned
                    return response_cleaned

            # Si no hay respuesta, asumir que es principal
            self._parent_city_cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"⚠️ Error detectando ciudad principal para {location}: {e}")
            # No guardar en cache si hay error, para poder reintentar
            return None


# Singleton global
gemini_factory = GeminiFactory()
 
 
