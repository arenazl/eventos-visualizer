"""
🔮 GEMINI UNIVERSAL SCRAPER - LA ARMA SECRETA
Scraper universal que usa Gemini AI para extraer eventos de CUALQUIER sitio web
"""

import asyncio
import aiohttp
import logging
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

# CloudScraper para bypass de anti-bot
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    logger.warning("⚠️ cloudscraper no disponible, algunos sitios pueden bloquear")

# Imports de interfaces y servicios
from services.scraper_interface import (
    BaseGlobalScraper,
    ScraperRequest,
    ScraperResult,
    ScraperConfig
)
from services.ai_service import GeminiAIService

logger = logging.getLogger(__name__)

class GeminiUniversalScraper(BaseGlobalScraper):
    """
    🔮 GEMINI UNIVERSAL SCRAPER

    CARACTERÍSTICAS:
    - Funciona con CUALQUIER sitio de eventos
    - No necesita configuración específica por sitio
    - No se rompe cuando cambia el HTML
    - Gratis hasta 1,500 requests/día (Gemini Flash 2.0)
    - ~$0.10 por 1,000 eventos después

    VENTAJAS:
    ✅ Universal - un solo scraper para todos los sitios
    ✅ Barato/Gratis - Gemini Flash 2.0 es casi gratuito
    ✅ Rápido - responde en <1 segundo
    ✅ Mantenimiento mínimo - no rompe con cambios HTML
    ✅ Datos estructurados - retorna JSON directamente

    USO:
    ```python
    scraper = GeminiUniversalScraper()
    events = await scraper.scrape_url(
        url="https://cualquier-sitio.com/eventos",
        location="Buenos Aires, Argentina"
    )
    ```
    """

    def __init__(self, url_discovery_service=None, config: ScraperConfig = None):
        """
        Constructor - Inicializa Gemini AI Service

        Args:
            url_discovery_service: Ignorado (no necesitamos discovery)
            config: Configuración específica del scraper
        """
        super().__init__(url_discovery_service, config)

        # Servicio de Gemini AI
        self.ai = GeminiAIService()

        # Límite de tokens HTML (Gemini Flash puede manejar hasta 32K)
        self.max_html_tokens = 8000  # ~8K caracteres de HTML

    async def scrape_events(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🎯 SCRAPING ESTÁNDAR (cumple con BaseGlobalScraper)

        Este método se llama desde IndustrialFactory para un sitio genérico.
        Por defecto retorna vacío porque necesita una URL específica.
        Usar scrape_url() directamente para URLs específicas.

        Args:
            location: Ubicación de búsqueda
            category: Categoría opcional
            limit: Cantidad de eventos

        Returns:
            Lista vacía (usar scrape_url() en su lugar)
        """
        logger.info(f"🔮 Gemini Universal: Necesita URL específica, usar scrape_url() directamente")
        return []

    async def scrape_url(
        self,
        url: str,
        location: str,
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🔮 SCRAPING UNIVERSAL CON GEMINI

        Proceso:
        1. Fetch HTML del sitio
        2. Limpiar y truncar HTML a límite de tokens
        3. Enviar a Gemini con prompt estructurado
        4. Recibir JSON de eventos
        5. Validar y retornar

        Args:
            url: URL del sitio a scrapear
            location: "Ciudad, País" para filtrar eventos
            category: "música", "deportes", etc.
            limit: Cantidad de eventos (max 200)

        Returns:
            Lista de eventos en formato estándar
        """

        logger.info(f"🔮 Gemini Universal: Scrapeando '{url}' para '{location}'")

        try:
            # 1. Fetch HTML
            html = await self._fetch_html(url)

            if not html:
                logger.warning(f"⚠️ No se pudo obtener HTML de {url}")
                return []

            # 2. Preparar prompt optimizado
            prompt = self._build_extraction_prompt(html, location, category)

            # 3. Llamar a Gemini
            logger.info(f"🤖 Enviando HTML a Gemini para análisis...")
            response = await self.ai._call_gemini_api(prompt)

            if not response:
                logger.warning(f"⚠️ Gemini no respondió para {url}")
                return []

            # 4. Parsear JSON de respuesta
            events = self._parse_gemini_response(response, location)

            logger.info(f"✅ Gemini Universal: {len(events)} eventos encontrados en '{url}'")

            return events[:limit]

        except Exception as e:
            logger.error(f"❌ Gemini Universal error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML de un sitio web con anti-bot bypass

        Intenta primero con aiohttp, si falla (403, 429) usa CloudScraper

        Args:
            url: URL del sitio

        Returns:
            HTML crudo o None si falla
        """
        # Intento 1: aiohttp normal
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers=headers
                ) as response:

                    if response.status == 200:
                        html = await response.text()
                        logger.info(f"✅ HTML obtenido (aiohttp): {len(html)} caracteres")
                        return html
                    elif response.status in [403, 429]:
                        logger.warning(f"⚠️ Anti-bot detectado (HTTP {response.status}), intentando CloudScraper...")
                        # Intentar con CloudScraper
                        return await self._fetch_html_cloudscraper(url)
                    else:
                        logger.error(f"❌ HTTP {response.status} al obtener {url}")
                        return None

        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout obteniendo HTML de {url}")
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo HTML: {e}")
            # Último intento con CloudScraper
            return await self._fetch_html_cloudscraper(url)

    async def _fetch_html_cloudscraper(self, url: str) -> Optional[str]:
        """
        Fetch HTML usando CloudScraper para bypass de Cloudflare/anti-bot

        Args:
            url: URL del sitio

        Returns:
            HTML o None si falla
        """
        if not CLOUDSCRAPER_AVAILABLE:
            logger.warning("⚠️ CloudScraper no disponible, no se puede bypasear anti-bot")
            return None

        try:
            # CloudScraper es síncrono, ejecutar en thread pool
            loop = asyncio.get_event_loop()

            def fetch_sync():
                scraper = cloudscraper.create_scraper(
                    browser={
                        'browser': 'chrome',
                        'platform': 'windows',
                        'mobile': False
                    }
                )
                response = scraper.get(url, timeout=15)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.error(f"❌ CloudScraper HTTP {response.status_code}")
                    return None

            html = await loop.run_in_executor(None, fetch_sync)

            if html:
                logger.info(f"✅ HTML obtenido (CloudScraper): {len(html)} caracteres")
                return html
            else:
                return None

        except Exception as e:
            logger.error(f"❌ Error con CloudScraper: {e}")
            return None

    def _map_category(self, category: Optional[str]) -> str:
        """
        Mapea categoría del usuario a categorías estándar del sistema

        Args:
            category: Categoría del usuario

        Returns:
            Categoría mapeada
        """
        if not category:
            return "todas"

        category_lower = category.lower()

        # Mapeo de categorías
        mapping = {
            # Música
            'musica': 'Música',
            'música': 'Música',
            'music': 'Música',
            'concierto': 'Música',
            'conciertos': 'Música',
            'festival': 'Música',
            'recital': 'Música',

            # Deportes
            'deportes': 'Deportes',
            'deporte': 'Deportes',
            'sports': 'Deportes',
            'futbol': 'Deportes',
            'fútbol': 'Deportes',
            'basquet': 'Deportes',
            'tenis': 'Deportes',

            # Cultural
            'cultural': 'Cultural',
            'cultura': 'Cultural',
            'teatro': 'Cultural',
            'exposicion': 'Cultural',
            'exposición': 'Cultural',
            'museo': 'Cultural',
            'arte': 'Cultural',
            'cine': 'Cultural',

            # Tech
            'tech': 'Tech',
            'tecnologia': 'Tech',
            'tecnología': 'Tech',
            'meetup': 'Tech',
            'hackathon': 'Tech',
            'conferencia': 'Tech',

            # Fiestas
            'fiestas': 'Fiestas',
            'fiesta': 'Fiestas',
            'party': 'Fiestas',
            'club': 'Fiestas',
            'clubbing': 'Fiestas',
            'after': 'Fiestas',

            # Hobbies
            'hobbies': 'Hobbies',
            'hobby': 'Hobbies',
            'taller': 'Hobbies',
            'clase': 'Hobbies',
            'workshop': 'Hobbies',

            # Internacional
            'internacional': 'Internacional',
            'international': 'Internacional'
        }

        return mapping.get(category_lower, category)

    def _clean_html(self, html: str) -> str:
        """
        Limpia HTML removiendo scripts, styles, comentarios

        Args:
            html: HTML crudo

        Returns:
            HTML limpio
        """
        # Remover scripts
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remover styles
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remover comentarios HTML
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        # Remover múltiples espacios/newlines
        html = re.sub(r'\s+', ' ', html)

        return html.strip()

    def _build_extraction_prompt(
        self,
        html: str,
        location: str,
        category: Optional[str]
    ) -> str:
        """
        🎯 PROMPT OPTIMIZADO PARA EXTRACCIÓN DE EVENTOS

        Este es el prompt clave que hace la magia.
        Diseñado con:
        - Instrucciones claras
        - Formato JSON estricto
        - Ejemplos (few-shot learning)
        - Validación de campos
        - Date range de 15 días (enfoque simplificado)

        Args:
            html: HTML del sitio
            location: Ubicación de búsqueda
            category: Categoría opcional

        Returns:
            Prompt para Gemini
        """

        # Limpiar HTML
        clean_html = self._clean_html(html)

        # Truncar a límite de tokens
        truncated_html = clean_html[:self.max_html_tokens]

        # Date range: hoy + 15 días
        from datetime import timedelta
        today = datetime.now()
        end_date = today + timedelta(days=15)

        today_str = today.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Construir prompt
        prompt = f"""Eres un experto extractor de información de eventos.

TAREA:
Extrae eventos de este HTML y devuelve JSON válido.

UBICACIÓN: {location}
CATEGORÍA: {self._map_category(category) if category else "todas"}
RANGO DE FECHAS: {today_str} a {end_date_str} (próximos 15 días)

CATEGORÍAS VÁLIDAS (asignar una de estas):
- Música (conciertos, festivales, recitales)
- Deportes (partidos, competencias, carreras)
- Cultural (teatro, exposiciones, museos, cine)
- Tech (conferencias, meetups, hackathons)
- Fiestas (clubbing, after office, fiestas temáticas)
- Hobbies (talleres, clases, grupos de interés)
- Internacional (eventos de otras ciudades/países)

FORMATO DE SALIDA (JSON estricto):
{{
  "events": [
    {{
      "title": "Nombre completo del evento",
      "date": "YYYY-MM-DD",
      "time": "HH:MM" o null,
      "location": "Venue o lugar exacto",
      "venue": "Nombre del venue",
      "description": "Descripción breve del evento",
      "price": "Precio formateado ($100, €50, Gratis, etc.)",
      "image_url": "URL completa de imagen" o null,
      "event_url": "URL completa del evento"
    }}
  ]
}}

REGLAS CRÍTICAS:
1. SOLO eventos entre {today_str} y {end_date_str} (próximos 15 días)
2. SOLO eventos en o cerca de: {location}
3. Campos requeridos: title, date, location, event_url
4. Si falta información → usar null (NO inventar datos)
5. Fechas en formato ISO: YYYY-MM-DD
6. Horas en formato 24h: HH:MM
7. Precios: "$100", "€50-80", "Gratis", "Ver precio", etc.
8. URLs: Completas y válidas (empiezan con http)
9. Máximo 30 eventos más relevantes
10. Priorizar eventos próximos en el tiempo

EJEMPLOS VÁLIDOS:

Evento completo:
{{
  "title": "Concierto Coldplay - Music of the Spheres",
  "date": "2025-03-15",
  "time": "21:00",
  "location": "Buenos Aires, Argentina",
  "venue": "Estadio River Plate",
  "description": "World Tour 2025 - Argentina",
  "price": "$15000-45000",
  "image_url": "https://example.com/coldplay.jpg",
  "event_url": "https://example.com/events/coldplay-2025"
}}

Evento mínimo (info parcial):
{{
  "title": "Stand-up Comedy Night",
  "date": "2025-02-10",
  "time": null,
  "location": "Buenos Aires, Argentina",
  "venue": "Teatro Gran Rex",
  "description": null,
  "price": "Gratis",
  "image_url": null,
  "event_url": "https://example.com/events/comedy-night"
}}

HTML A ANALIZAR:
{truncated_html}

IMPORTANTE:
- Devuelve SOLO el JSON válido
- NO agregues explicaciones antes o después del JSON
- NO uses markdown (```json)
- Asegúrate de cerrar correctamente todos los brackets
- Si no encuentras eventos, devuelve: {{"events": []}}

RESPUESTA (SOLO JSON):"""

        return prompt

    def _parse_gemini_response(
        self,
        response: str,
        location: str
    ) -> List[Dict[str, Any]]:
        """
        Parsea respuesta de Gemini y valida eventos

        Args:
            response: Respuesta cruda de Gemini
            location: Ubicación para metadata

        Returns:
            Lista de eventos validados
        """
        try:
            # Limpiar respuesta
            clean_response = response.strip()

            # Remover markdown si existe
            if clean_response.startswith('```'):
                clean_response = re.sub(r'^```json\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)
                clean_response = clean_response.strip()

            # Intentar extraer JSON
            json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)
            if not json_match:
                logger.warning("⚠️ No se encontró JSON en respuesta de Gemini")
                return []

            # Parsear JSON
            data = json.loads(json_match.group())

            # Validar estructura
            if 'events' not in data:
                logger.warning("⚠️ Respuesta sin campo 'events'")
                return []

            events = data['events']

            if not isinstance(events, list):
                logger.warning("⚠️ Campo 'events' no es una lista")
                return []

            # Validar y transformar eventos
            validated_events = []
            for event in events:
                validated = self._validate_and_transform_event(event, location)
                if validated:
                    validated_events.append(validated)

            logger.info(f"✅ Gemini parseado: {len(validated_events)}/{len(events)} eventos válidos")

            return validated_events

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON de Gemini: {e}")
            logger.debug(f"Respuesta raw: {response[:200]}...")
            return []
        except Exception as e:
            logger.error(f"❌ Error procesando respuesta Gemini: {e}")
            return []

    def _validate_and_transform_event(
        self,
        event: Dict[str, Any],
        location: str
    ) -> Optional[Dict[str, Any]]:
        """
        Valida evento y lo transforma a formato estándar

        Args:
            event: Evento crudo de Gemini
            location: Ubicación para metadata

        Returns:
            Evento validado y transformado, o None si inválido
        """
        try:
            # Campos requeridos
            required_fields = ['title', 'date', 'event_url']
            for field in required_fields:
                if not event.get(field):
                    logger.debug(f"⚠️ Evento sin campo requerido: {field}")
                    return None

            # Validar fecha
            try:
                datetime.strptime(event['date'], '%Y-%m-%d')
            except ValueError:
                logger.debug(f"⚠️ Fecha inválida: {event.get('date')}")
                return None

            # Validar URL
            event_url = event['event_url']
            if not event_url.startswith('http'):
                logger.debug(f"⚠️ URL inválida: {event_url}")
                return None

            # Transformar a formato estándar
            transformed = {
                'title': event['title'][:200],  # Max 200 chars
                'date': event['date'],
                'time': event.get('time') or None,
                'location': event.get('location') or location,
                'venue': event.get('venue') or '',
                'description': (event.get('description') or '')[:500],  # Max 500 chars
                'price': event.get('price') or 'Ver precio',
                'image_url': event.get('image_url') or None,
                'event_url': event_url,
                'source': 'gemini_universal',
                'source_api': 'gemini_scraper',
                'category': event.get('category') or None
            }

            return transformed

        except Exception as e:
            logger.debug(f"⚠️ Error validando evento: {e}")
            return None


# Para testing directo
async def test_gemini_universal():
    """Test básico del scraper universal"""
    scraper = GeminiUniversalScraper()

    # Sitios para testear
    test_sites = [
        {
            'url': 'https://ra.co/events/ar/buenosaires',
            'location': 'Buenos Aires, Argentina',
            'name': 'Resident Advisor'
        },
        {
            'url': 'https://www.timeout.com/buenos-aires/things-to-do/events-in-buenos-aires-today',
            'location': 'Buenos Aires, Argentina',
            'name': 'TimeOut Buenos Aires'
        }
    ]

    for site in test_sites:
        print(f"\n{'='*80}")
        print(f"🔮 Testing Gemini Universal: {site['name']}")
        print(f"   URL: {site['url']}")
        print('='*80)

        events = await scraper.scrape_url(
            url=site['url'],
            location=site['location'],
            limit=5
        )

        print(f"\n✅ Encontrados {len(events)} eventos:\n")

        for i, event in enumerate(events[:5], 1):
            print(f"{i}. {event['title']}")
            print(f"   📅 {event['date']} {event.get('time', '')}")
            print(f"   📍 {event.get('venue', 'Sin venue')}")
            print(f"   💰 {event['price']}")
            print(f"   🔗 {event['event_url'][:60]}...")
            print()

if __name__ == "__main__":
    asyncio.run(test_gemini_universal())
