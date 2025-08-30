#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MULTI-SOURCE EVENT SCRAPER - REPLICA EXACTA DEL PROBADO
Replicación exacta desde /tips/multi_source_scraper.py
SOLO adaptado para async donde es necesario
"""

from playwright.async_api import async_playwright
import json
import re
from datetime import datetime, timedelta
import time
import random
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import shutil
import os

logger = logging.getLogger(__name__)

class ProvenScraperExact:
    def __init__(self):
        self.events = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.chromium_path = self._find_chromium_path()
    
    def _find_chromium_path(self):
        """Encuentra automáticamente la ruta de Chromium instalado"""
        possible_paths = [
            '/snap/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            shutil.which('chromium'),
            shutil.which('chromium-browser'),
            shutil.which('google-chrome'),
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                print(f"✅ Chromium encontrado en: {path}")
                return path
        
        print("⚠️ No se encontró Chromium, usando el de Playwright")
        return None
    
    async def scrape_all_sources(self, location="palermo buenos aires", max_per_source=15):
        """
        Scraper principal que combina todas las fuentes - REPLICA EXACTA
        """
        
        print(f"🚀 INICIANDO SCRAPING MULTI-FUENTE")
        print(f"📍 Ubicación: {location}")
        print(f"🎯 Máximo por fuente: {max_per_source}")
        print("="*80)
        
        all_events = {}
        
        # 1. Facebook Events
        print("\n📘 SCRAPEANDO FACEBOOK...")
        facebook_events = await self.scrape_facebook_events(location, max_per_source)
        all_events['facebook'] = facebook_events
        print(f"✅ Facebook: {len(facebook_events)} eventos")
        
        # 2. Eventbrite  
        print("\n🎫 SCRAPEANDO EVENTBRITE...")
        eventbrite_events = await self.scrape_eventbrite_events(location, max_per_source)
        all_events['eventbrite'] = eventbrite_events
        print(f"✅ Eventbrite: {len(eventbrite_events)} eventos")
        
        # 3. Instagram hashtags públicos
        print("\n📸 SCRAPEANDO INSTAGRAM...")
        instagram_events = await self.scrape_instagram_events(location, max_per_source)
        all_events['instagram'] = instagram_events
        print(f"✅ Instagram: {len(instagram_events)} eventos")
        
        # 4. Fuentes argentinas específicas
        print("\n🇦🇷 SCRAPEANDO FUENTES ARGENTINAS...")
        argentina_events = await self.scrape_argentina_sources(location, max_per_source)
        all_events['argentina'] = argentina_events
        print(f"✅ Fuentes Argentinas: {len(argentina_events)} eventos")
        
        # Resumen
        total_events = sum(len(events) for events in all_events.values())
        print(f"\n🎉 TOTAL COMBINADO: {total_events} eventos de {len(all_events)} fuentes")
        
        return all_events
    
    async def scrape_facebook_events(self, location, max_events):
        """Scraper de Facebook Events - REPLICA EXACTA adaptada async"""
        
        try:
            async with async_playwright() as p:
                launch_options = {
                    'headless': True,
                    'args': [
                        '--no-sandbox',
                        '--disable-setuid-sandbox', 
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-blink-features=AutomationControlled',
                        '--no-first-run',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',
                    ]
                }
                
                # Usar Chromium del sistema si está disponible
                if self.chromium_path:
                    launch_options['executable_path'] = self.chromium_path
                
                browser = await p.chromium.launch(**launch_options)
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=self.headers['User-Agent'],
                    locale='es-AR',
                    extra_http_headers=self.headers
                )
                
                page = await context.new_page()
                
                try:
                    search_query = location.replace(' ', '%20')
                    url = f"https://www.facebook.com/events/search/?q={search_query}"
                    
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(3)
                    
                    # Scroll para cargar más - EXACTO como el original
                    for _ in range(3):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(1)
                    
                    content = await page.text_content('body')
                    events = self._parse_facebook_content(content, max_events)
                    
                    return events
                    
                except Exception as e:
                    print(f"⚠️ Error Facebook: {e}")
                    return []
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"⚠️ Error Facebook general: {e}")
            return []
    
    async def scrape_eventbrite_events(self, location, max_events):
        """Scraper de Eventbrite - REPLICA EXACTA con aiohttp"""
        
        events = []
        
        try:
            # URLs de Eventbrite Argentina - Actualizadas para fechas ACTUALES
            urls = [
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/events/",
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/septiembre/",
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/octubre/",
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/this-weekend/",
                "https://www.eventbrite.com.ar/d/argentina--buenos-aires/tomorrow/"
            ]
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                for url in urls:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                page_events = self._parse_eventbrite_page(soup)
                                events.extend(page_events)
                                
                                if len(events) >= max_events:
                                    break
                                    
                        await asyncio.sleep(random.uniform(1, 2))
                        
                    except Exception as e:
                        print(f"⚠️ Error en URL {url}: {e}")
                        continue
            
            return events[:max_events]
            
        except Exception as e:
            print(f"⚠️ Error general Eventbrite: {e}")
            return []
    
    async def scrape_instagram_events(self, location, max_events):
        """Scraper de Instagram - REPLICA EXACTA con async"""
        
        try:
            async with async_playwright() as p:
                launch_options = {'headless': True}
                if self.chromium_path:
                    launch_options['executable_path'] = self.chromium_path
                    launch_options['args'] = ['--no-sandbox', '--disable-setuid-sandbox']
                
                browser = await p.chromium.launch(**launch_options)
                context = await browser.new_context(user_agent=self.headers['User-Agent'])
                page = await context.new_page()
                
                events = []
                
                try:
                    # Hashtags relevantes para Palermo - EXACTOS
                    hashtags = ['palermo', 'palermosoho', 'palermohollywood', 'eventospalermo', 'buenosaires']
                    
                    for hashtag in hashtags[:2]:  # Limitar para evitar bloqueos - EXACTO
                        try:
                            url = f"https://www.instagram.com/explore/tags/{hashtag}/"
                            await page.goto(url, timeout=20000)
                            await asyncio.sleep(2)
                            
                            # Buscar posts que mencionen eventos
                            content = await page.text_content('body')
                            hashtag_events = self._parse_instagram_content(content, hashtag)
                            events.extend(hashtag_events)
                            
                            if len(events) >= max_events:
                                break
                                
                        except Exception as e:
                            print(f"⚠️ Error hashtag {hashtag}: {e}")
                            continue
                    
                    return events[:max_events]
                    
                except Exception as e:
                    print(f"⚠️ Error Instagram: {e}")
                    return []
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"⚠️ Error Instagram general: {e}")
            return []
    
    async def scrape_argentina_sources(self, location, max_events):
        """Scraper de fuentes argentinas específicas - REPLICA EXACTA"""
        
        events = []
        
        try:
            # Fuentes argentinas confiables - EXACTAS
            sources = [
                {
                    'name': 'Buenos Aires Turismo',
                    'url': 'https://turismo.buenosaires.gob.ar/es/eventos2025',
                    'parser': self._parse_buenosaires_gov
                },
                {
                    'name': 'TimeOut Buenos Aires', 
                    'url': 'https://www.timeout.com/buenos-aires/events',
                    'parser': self._parse_timeout_ba
                },
                {
                    'name': 'La Rural Buenos Aires',
                    'url': 'https://larural.com.ar/calendario/',
                    'parser': self._parse_larural
                }
            ]
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                for source in sources:
                    try:
                        print(f"   📡 Scrapeando {source['name']}...")
                        async with session.get(source['url']) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                source_events = source['parser'](soup, source['name'])
                                events.extend(source_events)
                                print(f"      ✅ {len(source_events)} eventos de {source['name']}")
                        
                        await asyncio.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        print(f"   ⚠️ Error {source['name']}: {e}")
                        continue
            
            return events[:max_events]
            
        except Exception as e:
            print(f"⚠️ Error fuentes argentinas: {e}")
            return []
    
    def _parse_facebook_content(self, content, max_events):
        """Parser para contenido de Facebook - EXACTO"""
        events = []
        lines = content.split('\n')
        
        date_patterns = [
            r'[A-Z][a-z]{2,3}, \d{1,2} de [a-z]{3,4}\.? a las \d{1,2}:\d{2}',
            r'[A-Z][a-z]{2,3}, \d{1,2} de [a-z]{3,4}\.?',
        ]
        
        i = 0
        while i < len(lines) and len(events) < max_events:
            line = lines[i].strip()
            
            for pattern in date_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    event = self._extract_facebook_event(lines, i)
                    if event:
                        events.append(event)
                        i += 5
                        break
            else:
                i += 1
        
        return events
    
    def _extract_facebook_event(self, lines, start_idx):
        """Extraer evento individual de Facebook - EXACTO"""
        try:
            max_idx = min(start_idx + 8, len(lines))
            event_lines = [lines[i].strip() for i in range(start_idx, max_idx)]
            
            date_line = event_lines[0] if event_lines else ""
            title = ""
            location = "Palermo, Buenos Aires"
            attendance = ""
            
            # Buscar título
            for line in event_lines[1:]:
                if line and len(line) > 10 and not self._is_facebook_metadata(line):
                    title = line
                    break
            
            # Buscar ubicación y asistencia
            for line in event_lines:
                if any(loc in line.lower() for loc in ['palermo', 'buenos aires', 'cabrera', 'avenida']):
                    location = line
                elif re.search(r'\d+\s*(interesados|asistirán)', line):
                    attendance = line
            
            if not title or len(title) < 10:
                return None
            
            return {
                'title': title[:150],
                'date': date_line[:100],
                'location': location[:100],
                'attendance': attendance or "Sin datos",
                'source': 'Facebook',
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception:
            return None
    
    def _is_facebook_metadata(self, line):
        """Detectar metadata de Facebook - EXACTO"""
        meta_words = ['facebook', 'iniciar sesión', 'contraseña', 'eventos', 'buscar']
        return any(word in line.lower() for word in meta_words)
    
    def _parse_eventbrite_page(self, soup):
        """Parser para páginas de Eventbrite - EXACTO"""
        events = []
        
        try:
            # Buscar contenedores de eventos
            event_containers = soup.find_all(['div', 'article'], class_=lambda x: x and 'event' in str(x).lower() if x else False)
            
            for container in event_containers:
                try:
                    title_elem = container.find(['h1', 'h2', 'h3', 'a'])
                    title = title_elem.get_text().strip() if title_elem else ""
                    
                    if len(title) > 10:
                        events.append({
                            'title': title[:150],
                            'date': "Verificar en Eventbrite",
                            'location': "Palermo, Buenos Aires",
                            'attendance': "Ver en plataforma",
                            'source': 'Eventbrite',
                            'extracted_at': datetime.now().isoformat()
                        })
                
                except Exception:
                    continue
            
            return events
            
        except Exception:
            return []
    
    def _parse_instagram_content(self, content, hashtag):
        """Parser para contenido de Instagram - EXACTO"""
        events = []
        
        try:
            # DEBUG: Ver qué contenido recibimos
            print(f"🔍 Instagram content para #{hashtag} (primeros 500 chars):")
            print(content[:500] if content else "CONTENIDO VACÍO")
            print("=" * 50)
            
            # Buscar menciones de eventos en el contenido
            event_keywords = ['evento', 'show', 'concierto', 'festival', 'expo', 'feria']
            
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in event_keywords):
                    # Buscar fechas más amplias: meses ACTUALES y futuros
                    month_keywords = ['septiembre', 'octubre', 'noviembre', 'diciembre', 'hoy', 'mañana', 'weekend']
                    if len(line.strip()) > 20 and any(month in line.lower() for month in month_keywords):
                        events.append({
                            'title': f"Evento vía #{hashtag}: {line.strip()[:100]}",
                            'date': "Verificar en Instagram",
                            'location': "Palermo, Buenos Aires", 
                            'attendance': "Ver en Instagram",
                            'source': 'Instagram',
                            'hashtag': hashtag,
                            'extracted_at': datetime.now().isoformat()
                        })
                        
                        if len(events) >= 5:  # Limitar por hashtag
                            break
            
            return events
            
        except Exception:
            return []
    
    def _parse_buenosaires_gov(self, soup, source_name):
        """Parser para sitio del gobierno de Buenos Aires - EXACTO"""
        events = []
        
        try:
            # Buscar eventos mencionando Palermo
            text_content = soup.get_text()
            
            if 'palermo' in text_content.lower():
                # Buscar patrones de eventos
                lines = text_content.split('\n')
                for line in lines:
                    if 'palermo' in line.lower() and any(word in line.lower() for word in ['septiembre', 'octubre', 'evento', 'festival', '2025']):
                        if len(line.strip()) > 20:
                            events.append({
                                'title': line.strip()[:150],
                                'date': "Septiembre-Octubre 2025",
                                'location': "Palermo, Buenos Aires",
                                'attendance': "Evento oficial",
                                'source': source_name,
                                'extracted_at': datetime.now().isoformat()
                            })
                            
                            if len(events) >= 3:
                                break
            
            return events
            
        except Exception:
            return []
    
    def _parse_timeout_ba(self, soup, source_name):
        """Parser para TimeOut Buenos Aires - EXACTO"""
        return []  # Implementar según estructura real
    
    def _parse_larural(self, soup, source_name):
        """Parser para La Rural - EXACTO"""
        return []  # Implementar según estructura real
    
    def combine_and_deduplicate(self, all_events):
        """Combinar y deduplificar eventos de todas las fuentes - EXACTO"""
        
        print("\n🔄 COMBINANDO Y DEDUPLICANDO...")
        
        combined = []
        seen_titles = set()
        
        for source, events in all_events.items():
            for event in events:
                title_clean = re.sub(r'\W+', '', event['title'].lower())
                
                if title_clean not in seen_titles and len(title_clean) > 10:
                    seen_titles.add(title_clean)
                    combined.append(event)
        
        # Ordenar por fuente (Facebook primero) - EXACTO
        source_priority = {'Facebook': 1, 'Eventbrite': 2, 'Instagram': 3, 'Argentina': 4}
        combined.sort(key=lambda x: source_priority.get(x['source'], 5))
        
        print(f"✅ {len(combined)} eventos únicos después de deduplicar")
        
        return combined

# Función principal de acceso
async def fetch_events_proven_exact(location="palermo buenos aires"):
    """
    REPLICA EXACTA del scraper probado que funciona
    """
    scraper = ProvenScraperExact()
    
    # Ejecutar scraping de todas las fuentes - EXACTO
    all_events = await scraper.scrape_all_sources(location, max_per_source=10)
    
    # Combinar y deduplificar - EXACTO
    combined_events = scraper.combine_and_deduplicate(all_events)
    
    return combined_events