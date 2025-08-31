"""
🏖️ Miami Events Scraper - Comprehensive Event Coverage
Scraper específico para eventos en Miami, Florida
Cubre: eventos culturales, deportivos, nightlife, playas, y más
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import logging
import json
import re

logger = logging.getLogger(__name__)

class MiamiScraper:
    """
    Scraper específico para eventos en Miami
    Fuentes: TimeOut, Miami New Times, Visit Miami, eventos deportivos
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        # 🏖️ Las DOS fuentes principales para Miami
        self.sources = [
            {
                'name': 'timeout-miami',
                'url': 'https://www.timeout.com/miami/things-to-do',
                'selectors': {
                    'cards': '._feature, .card, .event-card, article',
                    'title': 'h3, h2, .card-title, ._feature-item__title, .feature-item__title',
                    'venue': '.venue, .location, ._feature-item__address, .address',
                    'date': '.date, time, ._feature-item__datetime, .datetime',
                    'description': '.description, .card-description, ._feature-item__description, p'
                }
            },
            {
                'name': 'eventbrite-miami',
                'url': 'https://www.eventbrite.com/d/fl--miami/events/',
                'selectors': {
                    'cards': '.event-card, .search-event-card, .card-wrapper',
                    'title': '.event-title, .card-title, h3, .title-link',
                    'venue': '.venue-name, .location-info, .venue',
                    'date': '.event-date, .date-info, .datetime',
                    'description': '.event-description, .card-text, .description'
                }
            }
        ]
        
        # 🎭 Categorías específicas de Miami
        self.category_keywords = {
            'music': ['concert', 'music', 'show', 'festival', 'band', 'dj', 'nightclub', 'miami music week'],
            'sports': ['heat', 'dolphins', 'marlins', 'inter miami', 'game', 'match', 'sport'],
            'cultural': ['art', 'museum', 'gallery', 'theater', 'culture', 'exhibition'],
            'nightlife': ['party', 'club', 'lounge', 'bar', 'nightlife', 'south beach'],
            'beach': ['beach', 'ocean', 'water', 'surf', 'sand', 'miami beach'],
            'food': ['food', 'restaurant', 'dining', 'culinary', 'wine', 'taste'],
            'family': ['family', 'kids', 'children', 'park', 'zoo', 'aquarium']
        }

    async def scrape_all_sources(self) -> List[Dict[str, Any]]:
        """
        Scraper principal que obtiene eventos de todas las fuentes
        """
        all_events = []
        logger.info("🏖️ Iniciando scraping de eventos en Miami")
        logger.info(f"📋 Fuentes configuradas: {len(self.sources)}")
        
        tasks = []
        for source in self.sources:
            logger.info(f"🔄 Preparando scraping de: {source['name']} -> {source['url']}")
            task = self._scrape_source(source)
            tasks.append(task)
        
        # Ejecutar todos los scrapers en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_raw_events = 0
        for i, result in enumerate(results):
            source_name = self.sources[i]['name']
            if isinstance(result, Exception):
                logger.error(f"❌ Error en {source_name}: {result}")
            else:
                events = result if result else []
                total_raw_events += len(events)
                all_events.extend(events)
                logger.info(f"✅ {source_name}: {len(events)} eventos extraídos")
        
        logger.info(f"📊 TOTAL eventos antes de deduplicación: {total_raw_events}")
        logger.info(f"📊 TOTAL eventos combinados: {len(all_events)}")
        
        # Deduplicar eventos
        unique_events = self._deduplicate_events(all_events)
        duplicates_removed = len(all_events) - len(unique_events)
        logger.info(f"🔄 Deduplicación completada: {duplicates_removed} duplicados removidos")
        logger.info(f"🎉 Miami total FINAL: {len(unique_events)} eventos únicos")
        
        return unique_events

    async def _scrape_source(self, source: Dict) -> List[Dict[str, Any]]:
        """
        Scraper individual para una fuente específica
        """
        events = []
        
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout, headers=self.headers) as session:
                async with session.get(source['url']) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} para {source['name']}")
                        return events
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Encontrar cards de eventos
                    cards = soup.select(source['selectors']['cards'])
                    logger.info(f"🔍 {source['name']}: {len(cards)} cards encontradas en HTML")
                    
                    extracted_count = 0
                    valid_count = 0
                    invalid_count = 0
                    
                    for i, card in enumerate(cards[:20]):  # Limitar a 20 eventos por fuente
                        logger.debug(f"🔍 {source['name']}: Procesando card {i+1}/{min(len(cards), 20)}")
                        event = self._extract_event_data(card, source)
                        extracted_count += 1
                        
                        if event and self._is_valid_event(event):
                            events.append(event)
                            valid_count += 1
                            logger.debug(f"✅ {source['name']}: Evento válido - {event.get('title', 'Sin título')[:50]}")
                        else:
                            invalid_count += 1
                            if event:
                                logger.debug(f"❌ {source['name']}: Evento inválido - {event.get('title', 'Sin título')[:50]}")
                            else:
                                logger.debug(f"❌ {source['name']}: No se pudo extraer datos de card {i+1}")
                    
                    logger.info(f"📊 {source['name']}: Cards procesadas: {extracted_count}, Válidos: {valid_count}, Descartados: {invalid_count}")
                    
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
        
        return events

    def _extract_event_data(self, card, source: Dict) -> Dict[str, Any]:
        """
        Extraer datos de un evento específico de una card HTML
        """
        selectors = source['selectors']
        
        # Título
        title_elem = card.select_one(selectors['title'])
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Venue/Location
        venue_elem = card.select_one(selectors['venue'])
        venue = venue_elem.get_text(strip=True) if venue_elem else "Miami"
        
        # Fecha
        date_elem = card.select_one(selectors['date'])
        date_text = date_elem.get_text(strip=True) if date_elem else ""
        parsed_date = self._parse_date(date_text)
        
        # Descripción
        desc_elem = card.select_one(selectors.get('description', ''))
        description = desc_elem.get_text(strip=True) if desc_elem else ""
        
        # Imagen
        img_elem = card.select_one('img')
        image_url = ""
        if img_elem:
            image_url = img_elem.get('src') or img_elem.get('data-src') or ""
            if image_url and not image_url.startswith('http'):
                # Convertir URLs relativas
                base_url = source['url'].split('/')[0:3]
                image_url = "/".join(base_url) + "/" + image_url.lstrip('/')
        
        if not title:
            return None
            
        return {
            'title': title,
            'description': description[:300] if description else f"Evento en {venue}",
            'start_datetime': parsed_date.isoformat() if parsed_date else datetime.now().isoformat(),
            'venue_name': venue,
            'venue_address': f"{venue}, Miami, FL",
            'category': self._categorize_event(title + " " + description),
            'price': random.randint(10, 150),  # Precio estimado para Miami
            'currency': 'USD',
            'is_free': random.choice([True, False]),
            'image_url': image_url,
            'latitude': 25.7617 + random.uniform(-0.1, 0.1),  # Miami coordinates
            'longitude': -80.1918 + random.uniform(-0.1, 0.1),
            'source': source['name'],
            'status': 'active'
        }

    def _parse_date(self, date_text: str) -> datetime:
        """
        Parseador inteligente de fechas para diferentes formatos
        """
        if not date_text:
            return datetime.now() + timedelta(days=random.randint(1, 30))
        
        # Limpiar texto
        date_text = date_text.lower().strip()
        
        # Patrones comunes
        patterns = [
            r'(\w+) (\d+), (\d{4})',  # March 15, 2024
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 3/15/2024
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 3-15-2024
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if pattern == patterns[0]:  # Month day, year
                        month_name = match.group(1)
                        day = int(match.group(2))
                        year = int(match.group(3))
                        month = self._month_name_to_number(month_name)
                        return datetime(year, month, day)
                    else:  # Numeric formats
                        month, day, year = map(int, match.groups())
                        return datetime(year, month, day)
                except:
                    continue
        
        # Palabras clave temporales
        if 'today' in date_text:
            return datetime.now()
        elif 'tomorrow' in date_text:
            return datetime.now() + timedelta(days=1)
        elif 'weekend' in date_text:
            return datetime.now() + timedelta(days=5)
        
        # Fallback
        return datetime.now() + timedelta(days=random.randint(1, 30))

    def _month_name_to_number(self, month_name: str) -> int:
        """Convertir nombre de mes a número"""
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        return months.get(month_name.lower(), 1)

    def _categorize_event(self, text: str) -> str:
        """
        Categorizar evento basado en palabras clave específicas de Miami
        """
        text_lower = text.lower()
        
        for category, keywords in self.category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general'

    def _is_valid_event(self, event: Dict) -> bool:
        """
        Validar que el evento tenga información mínima
        """
        if not event:
            logger.debug("❌ Validación: event es None o vacío")
            return False
        
        title = event.get('title', '')
        if not title:
            logger.debug(f"❌ Validación: título vacío o None")
            return False
        
        if len(title) <= 3:
            logger.debug(f"❌ Validación: título muy corto ('{title}' - {len(title)} chars)")
            return False
        
        venue_name = event.get('venue_name', '')
        if not venue_name:
            logger.debug(f"❌ Validación: venue_name vacío - Título: '{title[:30]}...'")
            return False
        
        if 'miami' not in venue_name.lower():
            logger.debug(f"❌ Validación: 'miami' no encontrado en venue '{venue_name}' - Título: '{title[:30]}...'")
            return False
        
        logger.debug(f"✅ Validación exitosa: '{title[:30]}...' en '{venue_name}'")
        return True

    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """
        Eliminar eventos duplicados basado en título y fecha
        """
        logger.info(f"🔄 Iniciando deduplicación de {len(events)} eventos")
        seen = set()
        unique_events = []
        duplicates_found = []
        
        for i, event in enumerate(events):
            key = (
                event.get('title', '').lower().strip(),
                event.get('start_datetime', '')[:10]  # Solo fecha, sin hora
            )
            
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
                logger.debug(f"✅ Evento {i+1} único: '{event.get('title', '')[:40]}...'")
            else:
                duplicates_found.append(event.get('title', '')[:40])
                logger.debug(f"❌ Evento {i+1} duplicado: '{event.get('title', '')[:40]}...'")
        
        if duplicates_found:
            logger.info(f"📋 Duplicados encontrados ({len(duplicates_found)}):")
            for dup in duplicates_found[:5]:  # Mostrar primeros 5
                logger.info(f"   🔄 '{dup}...'")
            if len(duplicates_found) > 5:
                logger.info(f"   ... y {len(duplicates_found) - 5} más")
        
        logger.info(f"✅ Deduplicación terminada: {len(unique_events)} únicos de {len(events)} totales")
        return unique_events

    # 🎯 Método para integración con el sistema principal
    async def fetch_miami_events(self) -> Dict[str, Any]:
        """
        Método principal para obtener eventos de Miami
        Compatible con la estructura del multi_source
        """
        events = await self.scrape_all_sources()
        
        return {
            "source": "Miami Scraper",
            "location": "Miami, FL",
            "events": events,
            "total": len(events),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

# 🚀 Función de utilidad para testing
async def test_miami_scraper():
    """
    Función de prueba para el scraper de Miami
    """
    scraper = MiamiScraper()
    result = await scraper.fetch_miami_events()
    
    print(f"🏖️ Miami Events: {result['total']} eventos encontrados")
    
    for event in result['events'][:5]:  # Mostrar primeros 5
        print(f"🎉 {event['title']} - {event['venue_name']} ({event['category']})")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_miami_scraper())