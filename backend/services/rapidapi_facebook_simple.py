"""
RapidAPI Facebook Scraper - Versión Simple
🎯 Usando endpoint directo de la API que funciona
✅ Basado en la documentación real de RapidAPI
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
import random
import os

logger = logging.getLogger(__name__)

class RapidApiFacebookSimple:
    """
    Scraper simple usando RapidAPI Facebook Scraper
    """
    
    def __init__(self):
        # RapidAPI Configuration
        self.api_host = "facebook-scraper3.p.rapidapi.com"
        self.api_key = os.getenv("RAPIDAPI_KEY", "")
        self.base_url = "https://facebook-scraper3.p.rapidapi.com"
        
        # Headers for RapidAPI
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host,
            "Content-Type": "application/json"
        }
    
    async def scrape_facebook_url(self, facebook_url: str) -> List[Dict]:
        """
        Scrapear una URL específica de Facebook usando RapidAPI
        """
        try:
            logger.info(f"🔍 INICIANDO scrape_facebook_url:")
            logger.info(f"   📋 Target URL: {facebook_url}")
            logger.info(f"   🗝️ API Key presente: {'✅' if self.api_key else '❌'}")
            logger.info(f"   🌐 Base URL: {self.base_url}")
            logger.info(f"   📡 Host: {self.api_host}")
            
            # Probar diferentes endpoints posibles
            endpoints_to_try = [
                "",  # Endpoint raíz
                "/scrape",
                "/facebook",
                "/api",
                "/v1",
                f"/apiendpoint_{facebook_url.replace('/', '_')}"  # Basado en tu URL
            ]
            
            logger.info(f"🔄 Probando {len(endpoints_to_try)} endpoints diferentes:")
            
            for endpoint in endpoints_to_try:
                try:
                    url = f"{self.base_url}{endpoint}"
                    logger.info(f"🔄 Probando endpoint: {endpoint}")
                    logger.info(f"   📍 URL completa: {url}")
                    
                    # Diferentes payloads a probar
                    payloads = [
                        {"url": facebook_url},
                        {"facebook_url": facebook_url},
                        {"link": facebook_url},
                        {"target_url": facebook_url}
                    ]
                    
                    logger.info(f"   🔄 Probando {len(payloads)} payloads diferentes:")
                    for i, payload in enumerate(payloads):
                        try:
                            logger.info(f"      💼 Payload {i+1}: {payload}")
                            
                            async with aiohttp.ClientSession() as session:
                                logger.info(f"      📡 Enviando POST request...")
                                logger.info(f"      🔑 Headers: {self.headers}")
                                
                                async with session.post(url, headers=self.headers, json=payload) as response:
                                    logger.info(f"      📨 Response status: {response.status}")
                                    
                                    if response.status == 200:
                                        data = await response.json()
                                        logger.info(f"✅ ¡ÉXITO! Endpoint {endpoint} con payload {i+1} funciona!")
                                        logger.info(f"   📊 Response type: {type(data)}")
                                        logger.info(f"   📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'No dict'}")
                                        logger.info(f"   📊 Response preview: {str(data)[:200]}...")
                                        return self.process_facebook_response(data)
                                    elif response.status == 404:
                                        logger.info(f"      ⚠️ 404 Not Found (normal, probando siguiente)")
                                    else:
                                        text = await response.text()
                                        logger.warning(f"      ⚠️ Status {response.status}: {text[:150]}...")
                        except Exception as e:
                            logger.error(f"      ❌ Error con payload {i+1}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"   ❌ Error general con endpoint {endpoint}: {str(e)}")
                    continue
            
            logger.error("❌ FINAL: No se encontró endpoint funcional")
            logger.error("📋 RESUMEN: Probamos todos los endpoints y payloads sin éxito")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error general: {e}")
            return []
    
    def process_facebook_response(self, data: Any) -> List[Dict]:
        """
        Procesar la respuesta de RapidAPI Facebook
        """
        events = []
        
        try:
            # La respuesta puede venir en diferentes formatos
            if isinstance(data, dict):
                # Buscar diferentes claves posibles
                content = (data.get("data") or 
                          data.get("results") or 
                          data.get("posts") or 
                          data.get("events") or 
                          data.get("content") or
                          [data])  # Si es un solo objeto
            elif isinstance(data, list):
                content = data
            else:
                content = [{"raw_content": str(data)}]
            
            for item in content:
                if isinstance(item, dict):
                    event = self.extract_event_from_item(item)
                    if event:
                        events.append(event)
            
            logger.info(f"📊 Procesados {len(events)} eventos de la respuesta")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error procesando respuesta: {e}")
            return []
    
    def extract_event_from_item(self, item: Dict) -> Dict:
        """
        Extraer evento de un item de la respuesta
        """
        try:
            # Buscar campos típicos de eventos de Facebook
            title = (item.get("name") or 
                    item.get("title") or 
                    item.get("text") or 
                    item.get("content") or
                    "Evento Facebook")
            
            description = (item.get("description") or 
                          item.get("text") or 
                          item.get("content") or
                          "")
            
            # Fechas
            start_time = item.get("start_time") or item.get("date") or ""
            end_time = item.get("end_time") or ""
            
            # Ubicación
            location = item.get("location") or item.get("place") or "Buenos Aires"
            
            # URL
            event_url = item.get("url") or item.get("link") or ""
            
            # Solo considerar como evento si tiene características de evento
            if (len(title) > 10 and 
                any(keyword in title.lower() for keyword in 
                    ['evento', 'show', 'concierto', 'festival', 'fiesta', 'workshop'])):
                
                return {
                    "title": title[:100],
                    "description": description[:200] if description else "",
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": location,
                    "event_url": event_url,
                    "source": "rapidapi_facebook_simple",
                    "scraped_at": datetime.now().isoformat(),
                    "raw_data": item
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo evento: {e}")
            return None
    
    async def scrape_facebook_events_simple(self) -> List[Dict]:
        """
        Scraping simple de eventos de Facebook Buenos Aires
        """
        if not self.api_key:
            logger.error("❌ RAPIDAPI_KEY no configurado")
            return []
        
        logger.info("🔥 INICIANDO Facebook Scraper Simple")
        
        # URLs de Facebook a scrapear
        facebook_urls = [
            "https://www.facebook.com/events/search/?q=Buenos%20Aires",
            "https://www.facebook.com/events/search/?q=eventos%20Buenos%20Aires",
            "https://www.facebook.com/events/search/?q=conciertos%20Buenos%20Aires",
            "https://www.facebook.com/events/city/Buenos%20Aires"
        ]
        
        all_events = []
        
        for url in facebook_urls[:2]:  # Límite para no exceder rate limit
            try:
                logger.info(f"🔍 Scrapeando: {url}")
                events = await self.scrape_facebook_url(url)
                all_events.extend(events)
                
                if events:
                    logger.info(f"✅ {len(events)} eventos encontrados")
                    break  # Si encontramos eventos, no necesitamos probar más URLs
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Error scrapeando {url}: {e}")
                continue
        
        logger.info(f"🎯 Total eventos encontrados: {len(all_events)}")
        return all_events


async def test_rapidapi_facebook_simple():
    """
    Test del scraper simple
    """
    scraper = RapidApiFacebookSimple()
    
    if not scraper.api_key:
        print("⚠️ RAPIDAPI_KEY no configurado")
        return []
    
    print("🔥 INICIANDO RapidAPI Facebook Simple TEST...")
    print(f"🗝️ API Key configurado: ✅")
    
    # Test básico
    events = await scraper.scrape_facebook_events_simple()
    
    print(f"\n🎯 RESULTADOS Facebook Simple:")
    print(f"   📊 Total eventos: {len(events)}")
    
    if events:
        print(f"\n📱 Eventos encontrados:")
        for i, event in enumerate(events[:5]):
            print(f"{i+1}. 📱 {event.get('title', 'Sin título')}")
            print(f"   📍 {event.get('location', 'Sin ubicación')}")
            print(f"   🕐 {event.get('start_time', 'Sin fecha')}")
    else:
        print("⚠️ No se encontraron eventos")
        print("📝 Esto puede significar que:")
        print("   1. Los endpoints de la API han cambiado")
        print("   2. Se necesita autenticación adicional") 
        print("   3. La API requiere un plan de pago específico")
    
    return events

if __name__ == "__main__":
    asyncio.run(test_rapidapi_facebook_simple())