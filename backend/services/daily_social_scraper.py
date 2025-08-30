"""
Daily Social Media Scraper - Facebook & Instagram
Scraping una vez por día, guardado en base de datos
Estrategia: Datos reales almacenados, no simulados
"""

import asyncio
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
import hashlib

logger = logging.getLogger(__name__)

class DailySocialScraper:
    """
    Scraper que ejecuta una vez por día y guarda eventos reales en BD
    """
    
    def __init__(self):
        # 🎯 Venues argentinos REALES (sin generar eventos falsos)
        self.target_venues = {
            'facebook': [
                'lunaparkoficial',
                'teatrocolonoficial', 
                'nicetoclub',
                'CCRecoleta',
                'latrasienda',
                'teatrosanmartin',
                'movistararenar',
                'hipodromoargentino'
            ],
            'instagram': [
                'lunapark_oficial',
                'teatrocolon',
                'nicetoclub', 
                'ccrecoleta',
                'latrasienda',
                'teatrosanmartin',
                'movistararenar',
                'hipodromoargentino'
            ]
        }
        
        # Headers para parecer un navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def scrape_facebook_daily(self) -> List[Dict]:
        """
        Scraping diario de Facebook (solo datos reales)
        """
        logger.info("📘 Iniciando scraping DIARIO de Facebook...")
        real_events = []
        
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'android', 'mobile': True}
        )
        scraper.headers.update(self.headers)
        
        for venue in self.target_venues['facebook']:
            try:
                logger.info(f"🎯 Facebook: {venue}")
                
                # URLs móviles (menos protecciones)
                urls = [
                    f"https://m.facebook.com/{venue}/events",
                    f"https://touch.facebook.com/{venue}",
                    f"https://m.facebook.com/{venue}"
                ]
                
                venue_events = await self._scrape_facebook_venue(scraper, venue, urls)
                
                if venue_events:
                    real_events.extend(venue_events)
                    logger.info(f"✅ {venue}: {len(venue_events)} eventos reales extraídos")
                else:
                    logger.warning(f"⚠️ {venue}: No se pudieron extraer eventos")
                
                # Delay humano entre venues
                await asyncio.sleep(random.uniform(5, 12))
                
            except Exception as e:
                logger.error(f"❌ Error scraping {venue}: {e}")
                continue
        
        logger.info(f"📘 Facebook scraping completado: {len(real_events)} eventos totales")
        return real_events
    
    async def _scrape_facebook_venue(self, scraper, venue: str, urls: List[str]) -> List[Dict]:
        """
        Scraper real de un venue específico de Facebook
        """
        events = []
        
        for url in urls:
            try:
                logger.debug(f"  🌐 Intentando: {url}")
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: scraper.get(url, timeout=30)
                )
                
                if response.status_code != 200:
                    logger.debug(f"  ⚠️ Status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar eventos usando múltiples patrones
                venue_events = self._extract_facebook_events(soup, venue, url)
                
                if venue_events:
                    events.extend(venue_events)
                    logger.debug(f"  ✅ {len(venue_events)} eventos extraídos de {url}")
                    break  # Si encontramos eventos, no necesitamos probar más URLs
                    
            except Exception as e:
                logger.debug(f"  ❌ Error con {url}: {e}")
                continue
        
        return self._deduplicate_events(events)
    
    def _extract_facebook_events(self, soup: BeautifulSoup, venue: str, url: str) -> List[Dict]:
        """
        Extrae eventos reales del HTML de Facebook
        """
        events = []
        page_text = soup.get_text()
        
        # Patrones para detectar eventos reales
        event_patterns = [
            # Patrón 1: Fechas + eventos
            r'(\d{1,2}[/\-]\d{1,2}[/\-]?\d{0,4}[^\n]{10,100}(?:evento|show|concierto|festival|función|espectáculo))[^\n]{0,50}',
            
            # Patrón 2: Eventos con horarios
            r'([^\n]{15,80}(?:evento|show|concierto|festival|función|espectáculo)[^\n]{0,50}\d{1,2}:\d{2})',
            
            # Patrón 3: Títulos de eventos típicos
            r'([A-Z][^\n]{20,120}(?:en vivo|presenta|estrena|festival|2025)[^\n]{0,50})',
            
            # Patrón 4: Eventos con precios
            r'([^\n]{15,100}(?:entrada|precio|$\d+|gratis|free)[^\n]{0,50})'
        ]
        
        found_events = set()
        
        for pattern in event_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                event_text = match.strip()
                
                # Filtrar texto que claramente no son eventos
                if self._is_valid_event_text(event_text):
                    # Crear hash único para deduplicar
                    event_hash = hashlib.md5(event_text.lower().encode()).hexdigest()
                    
                    if event_hash not in found_events:
                        found_events.add(event_hash)
                        
                        event = {
                            'title': event_text,
                            'venue': venue,
                            'source': 'facebook_daily_scraper',
                            'source_url': url,
                            'scraped_at': datetime.now().isoformat(),
                            'event_hash': event_hash,
                            'raw_extraction': True
                        }
                        
                        events.append(event)
        
        # También buscar en elementos específicos de Facebook
        fb_specific_events = self._extract_fb_structured_data(soup, venue)
        events.extend(fb_specific_events)
        
        return events[:10]  # Máximo 10 eventos por venue
    
    def _is_valid_event_text(self, text: str) -> bool:
        """
        Valida si el texto extraído es realmente un evento
        """
        # Filtros de calidad
        if len(text) < 20 or len(text) > 200:
            return False
        
        # Palabras que indican que NO es un evento
        bad_indicators = [
            'javascript', 'function', 'window.', 'document.',
            'null', 'undefined', 'var ', 'const ', 'let ',
            '<script', '</script>', '{', '}', 'require(',
            'login', 'password', 'email', 'signup',
            'cookie', 'privacy', 'terms', 'copyright'
        ]
        
        if any(bad in text.lower() for bad in bad_indicators):
            return False
        
        # Debe contener palabras relevantes a eventos
        event_words = [
            'evento', 'show', 'concierto', 'festival', 'fiesta',
            'recital', 'función', 'espectáculo', 'música', 'teatro',
            'presenta', 'en vivo', 'estrena', 'entrada', 'precio'
        ]
        
        if not any(word in text.lower() for word in event_words):
            return False
        
        return True
    
    def _extract_fb_structured_data(self, soup: BeautifulSoup, venue: str) -> List[Dict]:
        """
        Busca datos estructurados específicos de Facebook
        """
        events = []
        
        # Buscar JSON-LD (datos estructurados)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Event':
                    event = {
                        'title': data.get('name', 'Evento sin título'),
                        'venue': venue,
                        'source': 'facebook_structured_data',
                        'start_date': data.get('startDate'),
                        'location': data.get('location', {}).get('name'),
                        'description': data.get('description', ''),
                        'scraped_at': datetime.now().isoformat()
                    }
                    events.append(event)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return events
    
    async def scrape_instagram_daily(self) -> List[Dict]:
        """
        Scraping diario de Instagram (solo datos reales)
        """
        logger.info("📸 Iniciando scraping DIARIO de Instagram...")
        real_events = []
        
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'android', 'mobile': True}
        )
        scraper.headers.update(self.headers)
        
        for venue in self.target_venues['instagram']:
            try:
                logger.info(f"🎯 Instagram: {venue}")
                
                url = f"https://www.instagram.com/{venue}/"
                venue_events = await self._scrape_instagram_venue(scraper, venue, url)
                
                if venue_events:
                    real_events.extend(venue_events)
                    logger.info(f"✅ {venue}: {len(venue_events)} eventos reales extraídos")
                else:
                    logger.warning(f"⚠️ {venue}: No se pudieron extraer eventos")
                
                # Delay humano entre venues
                await asyncio.sleep(random.uniform(8, 15))
                
            except Exception as e:
                logger.error(f"❌ Error scraping Instagram {venue}: {e}")
                continue
        
        logger.info(f"📸 Instagram scraping completado: {len(real_events)} eventos totales")
        return real_events
    
    async def _scrape_instagram_venue(self, scraper, venue: str, url: str) -> List[Dict]:
        """
        Scraper real de un venue específico de Instagram
        """
        events = []
        
        try:
            logger.debug(f"  🌐 Instagram: {url}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: scraper.get(url, timeout=30)
            )
            
            if response.status_code != 200:
                logger.debug(f"  ⚠️ Instagram Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer eventos usando patrones específicos de Instagram
            events = self._extract_instagram_events(soup, venue, url)
            
        except Exception as e:
            logger.debug(f"  ❌ Error con Instagram {url}: {e}")
        
        return self._deduplicate_events(events)
    
    def _extract_instagram_events(self, soup: BeautifulSoup, venue: str, url: str) -> List[Dict]:
        """
        Extrae eventos reales del HTML de Instagram
        """
        events = []
        
        # Instagram tiene datos JSON embebidos
        scripts = soup.find_all('script')
        
        for script in scripts:
            try:
                script_content = script.string if script.string else ""
                
                # Buscar JSON con información de posts
                if '"edge_owner_to_timeline_media"' in script_content:
                    # Extraer texto de posts que podrían contener eventos
                    post_texts = re.findall(
                        r'"text":"([^"]{50,200}[^"]*(?:evento|show|concierto|festival)[^"]{0,100})"',
                        script_content,
                        re.IGNORECASE
                    )
                    
                    for post_text in post_texts:
                        # Limpiar texto (Instagram escapa caracteres)
                        clean_text = post_text.replace('\\n', ' ').replace('\\u', ' ')
                        
                        if self._is_valid_event_text(clean_text):
                            event = {
                                'title': clean_text,
                                'venue': venue,
                                'source': 'instagram_daily_scraper',
                                'source_url': url,
                                'scraped_at': datetime.now().isoformat(),
                                'event_hash': hashlib.md5(clean_text.lower().encode()).hexdigest(),
                                'raw_extraction': True
                            }
                            events.append(event)
            
            except Exception as e:
                logger.debug(f"Error processing Instagram script: {e}")
                continue
        
        # También buscar en el texto visible de la página
        page_text = soup.get_text()
        visible_events = self._extract_instagram_visible_events(page_text, venue, url)
        events.extend(visible_events)
        
        return events[:8]  # Máximo 8 eventos por venue de Instagram
    
    def _extract_instagram_visible_events(self, text: str, venue: str, url: str) -> List[Dict]:
        """
        Extrae eventos del texto visible de Instagram
        """
        events = []
        
        # Patrones específicos para Instagram
        ig_patterns = [
            r'([^\n]{20,120}(?:próximo|next|este|this)[^\n]{0,50}(?:evento|show|concert))[^\n]{0,50}',
            r'([^\n]{15,100}(?:tickets|entradas|disponibles|available)[^\n]{0,50})',
            r'([A-Z][^\n]{25,150}(?:2025|enero|febrero|marzo|abril|mayo)[^\n]{0,50})'
        ]
        
        for pattern in ig_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches[:3]:  # Máximo 3 por patrón
                clean_text = match.strip()
                
                if self._is_valid_event_text(clean_text):
                    event = {
                        'title': clean_text,
                        'venue': venue,
                        'source': 'instagram_visible_text',
                        'source_url': url,
                        'scraped_at': datetime.now().isoformat(),
                        'event_hash': hashlib.md5(clean_text.lower().encode()).hexdigest()
                    }
                    events.append(event)
        
        return events
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """
        Elimina eventos duplicados basándose en el hash
        """
        seen_hashes = set()
        unique_events = []
        
        for event in events:
            event_hash = event.get('event_hash')
            if not event_hash:
                # Crear hash si no existe
                title = event.get('title', '').lower()
                event_hash = hashlib.md5(title.encode()).hexdigest()
                event['event_hash'] = event_hash
            
            if event_hash not in seen_hashes:
                seen_hashes.add(event_hash)
                unique_events.append(event)
        
        return unique_events
    
    async def run_daily_scraping(self) -> Dict[str, Any]:
        """
        Ejecuta el scraping diario completo (Facebook + Instagram)
        """
        logger.info("🚀 Iniciando SCRAPING DIARIO de redes sociales...")
        
        start_time = datetime.now()
        
        # Ejecutar ambos scrapers en paralelo
        facebook_task = asyncio.create_task(self.scrape_facebook_daily())
        instagram_task = asyncio.create_task(self.scrape_instagram_daily())
        
        facebook_events, instagram_events = await asyncio.gather(
            facebook_task, 
            instagram_task,
            return_exceptions=True
        )
        
        # Procesar resultados
        if isinstance(facebook_events, Exception):
            logger.error(f"Facebook scraping falló: {facebook_events}")
            facebook_events = []
        
        if isinstance(instagram_events, Exception):
            logger.error(f"Instagram scraping falló: {instagram_events}")
            instagram_events = []
        
        all_events = []
        all_events.extend(facebook_events or [])
        all_events.extend(instagram_events or [])
        
        # Deduplicar entre plataformas
        unique_events = self._deduplicate_events(all_events)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            'status': 'success',
            'scraping_date': start_time.date().isoformat(),
            'total_events_found': len(unique_events),
            'facebook_events': len(facebook_events or []),
            'instagram_events': len(instagram_events or []),
            'execution_time_seconds': duration,
            'venues_facebook': len(self.target_venues['facebook']),
            'venues_instagram': len(self.target_venues['instagram']),
            'events': unique_events,
            'next_scraping': (start_time + timedelta(days=1)).isoformat()
        }
        
        logger.info(f"✅ Scraping diario completado: {len(unique_events)} eventos únicos en {duration:.1f}s")
        
        return result


# 🔥 FUNCIONES DE TESTING Y USO

async def test_daily_scraper():
    """
    Test del scraper diario
    """
    scraper = DailySocialScraper()
    
    print("🚀 DAILY SOCIAL SCRAPER - DATOS REALES SOLAMENTE")
    print("📘 Facebook + 📸 Instagram")
    print("🎯 Una ejecución por día -> Base de datos")
    
    # Ejecutar scraping completo
    result = await scraper.run_daily_scraping()
    
    print(f"\n✅ RESULTADO:")
    print(f"   📊 Total eventos únicos: {result['total_events_found']}")
    print(f"   📘 Facebook: {result['facebook_events']} eventos")
    print(f"   📸 Instagram: {result['instagram_events']} eventos") 
    print(f"   ⏱️ Tiempo ejecución: {result['execution_time_seconds']:.1f}s")
    print(f"   🎯 Venues Facebook: {result['venues_facebook']}")
    print(f"   🎯 Venues Instagram: {result['venues_instagram']}")
    
    # Mostrar algunos eventos de ejemplo
    print(f"\n🎭 EVENTOS EXTRAÍDOS (muestra):")
    for i, event in enumerate(result['events'][:10]):
        platform = "📘" if "facebook" in event['source'] else "📸"
        print(f"\n{i+1:2d}. {platform} {event['title'][:70]}...")
        print(f"     🏢 {event['venue']}")
        print(f"     🔗 {event['source']}")
    
    print(f"\n🗓️ Próximo scraping: {result['next_scraping']}")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_daily_scraper())