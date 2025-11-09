"""
🎟️ TICKETMASTER DISCOVERY API - Official API Integration
Scraper usando la API oficial de Ticketmaster Discovery para eventos globales
"""

import asyncio
import aiohttp
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# Imports de interfaces y servicios
from services.scraper_interface import (
    BaseGlobalScraper,
    ScraperRequest,
    ScraperResult,
    ScraperConfig
)

logger = logging.getLogger(__name__)

class TicketmasterAPIScraper(BaseGlobalScraper):
    """
    🎟️ TICKETMASTER API SCRAPER

    CARACTERÍSTICAS:
    - API oficial de Ticketmaster Discovery
    - 5,000 llamadas/día gratis
    - Cobertura global masiva
    - Eventos de deportes, música, teatro, familia
    - Búsqueda geográfica por ciudad o coordenadas
    - Rate limit: 5 requests/segundo
    """

    def __init__(self, url_discovery_service=None, config: ScraperConfig = None):
        """
        Constructor - No necesita URL discovery porque usa API directa

        Args:
            url_discovery_service: Ignorado (API no necesita discovery)
            config: Configuración específica del scraper
        """
        super().__init__(url_discovery_service, config)

        # API Key de Ticketmaster
        self.api_key = os.getenv('TICKETMASTER_API_KEY', 'BnAVSbJZ7dVvPwFh91UVOmwX4CU1Ft5g')

        # DOS APIs diferentes:
        # - Discovery API (USA/Canada principalmente)
        # - MFX API (Europa, Latam, Asia, resto del mundo)
        self.discovery_url = 'https://app.ticketmaster.com/discovery/v2'
        self.mfx_url = 'https://app.ticketmaster.eu/mfxapi/v2'

        # Rate limiting: 5 req/segundo
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms entre requests

    async def scrape_events(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🎯 SCRAPING CON TICKETMASTER API

        Proceso:
        1. Parsear ubicación (ciudad, país)
        2. Llamar a Ticketmaster Discovery API
        3. Transformar response a formato estándar
        4. Retornar eventos

        Args:
            location: "Buenos Aires, Argentina" o "Paris, France"
            category: "music", "sports", "arts", "theatre"
            limit: Cantidad de eventos (max 200)
        """

        logger.info(f"🎟️ Ticketmaster API: Buscando eventos en '{location}'")

        try:
            # 1. Parsear ubicación
            city, country_code = self._parse_location(location)

            # 2. Llamar a API
            events_data = await self._fetch_events_from_api(
                city=city,
                country_code=country_code,
                category=category,
                size=min(limit, 200)  # Ticketmaster max 200
            )

            # 3. Transformar a formato estándar
            events = self._transform_events(events_data, location)

            logger.info(f"✅ Ticketmaster: {len(events)} eventos encontrados en '{location}'")

            return events[:limit]

        except Exception as e:
            logger.error(f"❌ Ticketmaster API error: {e}")
            return []

    def _parse_location(self, location: str) -> tuple:
        """
        Parsear ubicación a ciudad y código de país

        Ejemplos:
            "Buenos Aires, Argentina" → ("Buenos Aires", "AR")
            "Paris, France" → ("Paris", "FR")
            "New York, USA" → ("New York", "US")
        """
        parts = [p.strip() for p in location.split(',')]

        if len(parts) >= 2:
            city = parts[0]
            country = parts[-1]
        else:
            city = location
            country = "Argentina"  # Fallback

        # Mapeo de países a códigos ISO
        country_codes = {
            'argentina': 'AR',
            'brasil': 'BR',
            'brazil': 'BR',
            'chile': 'CL',
            'uruguay': 'UY',
            'méxico': 'MX',
            'mexico': 'MX',
            'colombia': 'CO',
            'perú': 'PE',
            'peru': 'PE',
            'españa': 'ES',
            'spain': 'ES',
            'francia': 'FR',
            'france': 'FR',
            'uk': 'GB',
            'reino unido': 'GB',
            'united kingdom': 'GB',
            'usa': 'US',
            'estados unidos': 'US',
            'united states': 'US',
            'canada': 'CA',
            'canadá': 'CA',
            'alemania': 'DE',
            'germany': 'DE',
            'italia': 'IT',
            'italy': 'IT',
            'portugal': 'PT',
            'netherlands': 'NL',
            'holanda': 'NL',
            'australia': 'AU',
        }

        country_code = country_codes.get(country.lower(), 'AR')

        logger.info(f"📍 Ubicación parseada: ciudad='{city}', país='{country_code}'")

        return city, country_code

    async def _fetch_events_from_api(
        self,
        city: str,
        country_code: str,
        category: Optional[str] = None,
        size: int = 50
    ) -> List[Dict]:
        """
        Llamar a Ticketmaster API (Discovery o MFX según región)

        USA/Canada → Discovery API
        Resto del mundo → MFX API (Europa, Latam, Asia)
        """

        # Rate limiting (5 req/segundo)
        await self._apply_rate_limit()

        # Determinar qué API usar según el país
        usa_canada_countries = ['US', 'CA']

        if country_code in usa_canada_countries:
            # USA/Canada: Discovery API
            return await self._fetch_from_discovery_api(city, country_code, category, size)
        else:
            # Resto del mundo: MFX API
            return await self._fetch_from_mfx_api(city, country_code, category, size)

    async def _fetch_from_discovery_api(
        self,
        city: str,
        country_code: str,
        category: Optional[str] = None,
        size: int = 50
    ) -> List[Dict]:
        """Discovery API (USA/Canada)"""

        # Preparar parámetros
        params = {
            'apikey': self.api_key,
            'city': city,
            'countryCode': country_code,
            'size': size,
            'sort': 'date,asc',
        }

        # Agregar categoría si existe
        if category:
            category_map = {
                'música': 'music',
                'musica': 'music',
                'music': 'music',
                'concierto': 'music',
                'deportes': 'sports',
                'sports': 'sports',
                'deporte': 'sports',
                'arte': 'arts',
                'arts': 'arts',
                'cultura': 'arts',
                'teatro': 'theatre',
                'theatre': 'theatre',
                'theater': 'theatre',
            }
            classification = category_map.get(category.lower())
            if classification:
                params['classificationName'] = classification

        url = f"{self.discovery_url}/events.json"

        logger.info(f"🌐 Llamando Discovery API (USA/Canada): {url}")
        logger.debug(f"   Params: city={city}, country={country_code}, size={size}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:

                    if response.status == 200:
                        data = await response.json()

                        # Extraer eventos del response
                        embedded = data.get('_embedded', {})
                        events = embedded.get('events', [])

                        logger.info(f"✅ Discovery API Response: {len(events)} eventos")

                        return events

                    elif response.status == 429:
                        logger.warning(f"⚠️ Rate limit exceeded (429)")
                        return []

                    else:
                        logger.error(f"❌ Discovery API error {response.status}: {await response.text()}")
                        return []

        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout llamando Discovery API")
            return []
        except Exception as e:
            logger.error(f"❌ Error en request Discovery API: {e}")
            return []

    async def _fetch_from_mfx_api(
        self,
        city: str,
        country_code: str,
        category: Optional[str] = None,
        size: int = 50
    ) -> List[Dict]:
        """MFX API (Europa, Latam, Asia, resto del mundo)"""

        # Preparar parámetros para MFX API (diferentes a Discovery)
        params = {
            'apikey': self.api_key,
            'domain': '',  # Vacío para búsqueda global
            'lang': 'es-es',  # Idioma español por defecto
            'rows': size,  # MFX usa 'rows' en lugar de 'size'
            'sort_by': 'eventdate',
            'order': 'asc',
        }

        # MFX API requiere country_ids (códigos numéricos)
        # Mapeo de códigos ISO a IDs de Ticketmaster
        country_id_map = {
            'AR': '30',  # Argentina
            'BR': '31',  # Brazil
            'CL': '32',  # Chile
            'CO': '33',  # Colombia
            'MX': '34',  # Mexico
            'PE': '35',  # Peru
            'UY': '36',  # Uruguay
            'ES': '9',   # Spain
            'FR': '10',  # France
            'DE': '11',  # Germany
            'IT': '12',  # Italy
            'GB': '7',   # UK
            'PT': '13',  # Portugal
            'NL': '14',  # Netherlands
            'AU': '15',  # Australia
        }

        country_id = country_id_map.get(country_code, '30')  # Default Argentina
        params['country_ids'] = country_id

        # Para city, MFX usa city_ids o simplemente busca por texto
        # Como no tenemos IDs de ciudades, usamos event_name para filtrar
        # O simplemente dejamos que retorne eventos del país y filtramos después

        url = f"{self.mfx_url}/events"

        logger.info(f"🌐 Llamando MFX API (Internacional): {url}")
        logger.debug(f"   Params: country_id={country_id}, rows={size}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:

                    if response.status == 200:
                        data = await response.json()

                        # Extraer eventos del response MFX
                        # Formato diferente a Discovery API
                        events = data.get('events', [])

                        # Filtrar por ciudad (case insensitive)
                        if city and events:
                            city_lower = city.lower()
                            events = [
                                e for e in events
                                if city_lower in e.get('venue', {}).get('city', '').lower() or
                                   city_lower in e.get('properties', {}).get('venue', {}).get('city', '').lower()
                            ]

                        logger.info(f"✅ MFX API Response: {len(events)} eventos (filtrados por ciudad)")

                        return events

                    elif response.status == 429:
                        logger.warning(f"⚠️ Rate limit exceeded (429)")
                        return []

                    else:
                        logger.error(f"❌ MFX API error {response.status}: {await response.text()}")
                        return []

        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout llamando MFX API")
            return []
        except Exception as e:
            logger.error(f"❌ Error en request MFX API: {e}")
            return []

    async def _apply_rate_limit(self):
        """
        Rate limiting: 5 requests/segundo
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    def _transform_events(self, api_events: List[Dict], location: str) -> List[Dict[str, Any]]:
        """
        Transformar eventos de Ticketmaster API a formato estándar

        Ticketmaster format:
        {
          "name": "Event Name",
          "dates": {"start": {"localDate": "2025-03-15", "localTime": "20:00"}},
          "_embedded": {"venues": [{"name": "Venue", "city": {...}}]},
          "priceRanges": [{"min": 50, "max": 150, "currency": "USD"}],
          "images": [{"url": "..."}],
          "url": "..."
        }

        Formato estándar:
        {
          "title": "...",
          "date": "2025-03-15",
          "time": "20:00",
          "location": "...",
          "venue": "...",
          "price": "$50-150",
          "image_url": "...",
          "event_url": "...",
          "source": "ticketmaster"
        }
        """

        transformed = []

        for event in api_events:
            try:
                # Título
                title = event.get('name', 'Sin título')

                # Fecha y hora
                dates = event.get('dates', {}).get('start', {})
                date_str = dates.get('localDate', '')
                time_str = dates.get('localTime', '')

                # Venue
                venues = event.get('_embedded', {}).get('venues', [])
                venue_name = venues[0].get('name', '') if venues else ''
                venue_city = venues[0].get('city', {}).get('name', '') if venues else ''

                # Precio
                price_ranges = event.get('priceRanges', [])
                if price_ranges:
                    pr = price_ranges[0]
                    min_price = pr.get('min', 0)
                    max_price = pr.get('max', 0)
                    currency = pr.get('currency', 'USD')

                    if currency == 'USD':
                        symbol = '$'
                    elif currency == 'EUR':
                        symbol = '€'
                    elif currency == 'GBP':
                        symbol = '£'
                    elif currency == 'ARS':
                        symbol = '$'
                    else:
                        symbol = currency

                    if min_price and max_price and min_price != max_price:
                        price = f"{symbol}{min_price:.0f}-{max_price:.0f}"
                    elif min_price:
                        price = f"{symbol}{min_price:.0f}"
                    else:
                        price = "Ver precios"
                else:
                    price = "Ver precios"

                # Imagen
                images = event.get('images', [])
                image_url = images[0].get('url', '') if images else ''

                # URL
                event_url = event.get('url', '')

                # Categoría
                classifications = event.get('classifications', [])
                category = ''
                if classifications:
                    segment = classifications[0].get('segment', {})
                    category = segment.get('name', '')

                # Crear evento transformado
                transformed_event = {
                    'title': title,
                    'date': date_str,
                    'time': time_str or None,
                    'location': venue_city or location,
                    'venue': venue_name,
                    'description': f"{category}" if category else None,
                    'price': price,
                    'image_url': image_url or None,
                    'event_url': event_url,
                    'source': 'ticketmaster',
                    'source_api': 'ticketmaster_api',
                    'category': category or None
                }

                transformed.append(transformed_event)

            except Exception as e:
                logger.warning(f"⚠️ Error transformando evento: {e}")
                continue

        return transformed

# Para testing directo
async def test_ticketmaster():
    """Test básico del scraper"""
    scraper = TicketmasterAPIScraper()

    locations = [
        "Buenos Aires, Argentina",
        "New York, USA",
        "Paris, France"
    ]

    for location in locations:
        print(f"\n{'='*80}")
        print(f"🎟️ Testing Ticketmaster API: {location}")
        print('='*80)

        events = await scraper.scrape_events(location, limit=5)

        print(f"\n✅ Encontrados {len(events)} eventos:\n")

        for i, event in enumerate(events[:5], 1):
            print(f"{i}. {event['title']}")
            print(f"   📅 {event['date']} {event.get('time', '')}")
            print(f"   📍 {event.get('venue', 'Sin venue')}")
            print(f"   💰 {event['price']}")
            print(f"   🔗 {event['event_url'][:60]}...")
            print()

if __name__ == "__main__":
    asyncio.run(test_ticketmaster())
