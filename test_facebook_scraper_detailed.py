#!/usr/bin/env python3
"""
Script de prueba para Facebook Scraper con logs super detallados
🔍 Para ver exactamente qué está pasando en cada paso
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Configurar logging SÚPER DETALLADO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'/mnt/c/Code/eventos-visualizer/logs/facebook_scraper_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

# Add backend to path
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

from services.rapidapi_facebook_scraper import RapidApiFacebookScraper
from services.rapidapi_facebook_simple import RapidApiFacebookSimple

async def test_detailed_facebook_scraping():
    """
    Test súper detallado con logs completos
    """
    print("🚀" + "="*80)
    print("🚀 FACEBOOK SCRAPER DETAILED TEST")
    print("🚀" + "="*80)
    print(f"📅 Fecha/Hora: {datetime.now()}")
    print(f"🗝️ RAPIDAPI_KEY configurado: {'✅' if os.getenv('RAPIDAPI_KEY') else '❌'}")
    print()
    
    # Test 1: RapidAPI Facebook Scraper (el complejo con 2 pasos)
    print("🔥" + "="*60)
    print("🔥 TEST 1: RapidAPI Facebook Scraper (2 pasos)")
    print("🔥" + "="*60)
    
    scraper = RapidApiFacebookScraper()
    
    print(f"✅ Scraper inicializado")
    print(f"🗝️ API Key presente: {'✅' if scraper.api_key else '❌'}")
    print(f"🌐 Base URL: {scraper.base_url}")
    print(f"📡 Host: {scraper.api_host}")
    print()
    
    # Ejecutar scraping completo
    try:
        print("🚀 INICIANDO SCRAPING COMPLETO...")
        events = await scraper.scrape_facebook_events_rapidapi(
            city_name="Buenos Aires", 
            limit=10,
            max_time_seconds=30.0
        )
        
        print(f"🎯 RESULTADO FINAL:")
        print(f"   📊 Total eventos obtenidos: {len(events)}")
        
        if events:
            print(f"   🔍 Primeros 5 eventos:")
            for i, event in enumerate(events[:5]):
                title = event.get('title', 'Sin título')[:60]
                venue = event.get('venue_name', 'Sin venue')
                category = event.get('category', 'Sin categoría')
                print(f"      {i+1}. {title}... | {venue} | {category}")
        else:
            print(f"   ⚠️ No se obtuvieron eventos")
            
    except Exception as e:
        print(f"❌ ERROR EN TEST 1: {e}")
    
    print()
    print("🔥" + "="*60)
    print("🔥 TEST 2: RapidAPI Facebook Simple")
    print("🔥" + "="*60)
    
    # Test 2: RapidAPI Simple (el que prueba diferentes endpoints)
    scraper_simple = RapidApiFacebookSimple()
    
    try:
        print("🚀 INICIANDO SCRAPING SIMPLE...")
        events_simple = await scraper_simple.scrape_facebook_events_simple()
        
        print(f"🎯 RESULTADO SIMPLE:")
        print(f"   📊 Total eventos obtenidos: {len(events_simple)}")
        
        if events_simple:
            print(f"   🔍 Eventos encontrados:")
            for i, event in enumerate(events_simple[:3]):
                title = event.get('title', 'Sin título')[:60]
                location = event.get('location', 'Sin ubicación')
                print(f"      {i+1}. {title}... | {location}")
        else:
            print(f"   ⚠️ No se obtuvieron eventos con método simple")
            
    except Exception as e:
        print(f"❌ ERROR EN TEST 2: {e}")
    
    print()
    print("🏁" + "="*80)
    print("🏁 RESUMEN FINAL DE TESTS")
    print("🏁" + "="*80)
    print(f"📊 Eventos del scraper complejo: {len(events) if 'events' in locals() else 0}")
    print(f"📊 Eventos del scraper simple: {len(events_simple) if 'events_simple' in locals() else 0}")
    print(f"📅 Test finalizado: {datetime.now()}")
    print()
    
    if not os.getenv('RAPIDAPI_KEY'):
        print("⚠️" + "="*60)
        print("⚠️ NOTA IMPORTANTE:")
        print("   🗝️ No se detectó RAPIDAPI_KEY en variables de entorno")
        print("   📋 Para usar este scraper necesitas:")
        print("   1. Ir a: https://rapidapi.com/krasnoludkolo/api/facebook-scraper3")
        print("   2. Obtener API key gratuita")
        print("   3. Agregarlo al .env: RAPIDAPI_KEY=tu_key_aqui")
        print("   4. Reiniciar el servidor")
        print("⚠️" + "="*60)

if __name__ == "__main__":
    # Crear directorio de logs si no existe
    os.makedirs('/mnt/c/Code/eventos-visualizer/logs', exist_ok=True)
    
    asyncio.run(test_detailed_facebook_scraping())