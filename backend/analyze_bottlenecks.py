#!/usr/bin/env python3
"""
🔍 ANÁLISIS DE CUELLOS DE BOTELLA - 2 SCRAPERS ACTIVOS
Eventbrite vs Meetup - Cuál es más lento y por qué
"""

import asyncio
import time
from typing import Dict, Any
from services.industrial_factory import IndustrialFactory

async def analyze_individual_scrapers():
    """Análisis detallado de cada scraper individualmente"""
    
    print("🔍 ANÁLISIS DE CUELLOS DE BOTELLA")
    print("=" * 50)
    
    factory = IndustrialFactory()
    location = "Barcelona"
    limit = 5
    
    # Probar cada scraper por separado
    scrapers_to_test = ['eventbrite', 'meetup']
    results = {}
    
    for scraper_name in scrapers_to_test:
        print(f"\n🎯 TESTING: {scraper_name.upper()}")
        print("-" * 30)
        
        start_time = time.time()
        
        try:
            # Test individual de cada scraper
            if scraper_name == 'eventbrite':
                from services.global_scrapers.eventbrite_scraper import EventbriteScraper
                scraper = EventbriteScraper()
                events = await scraper.search_events(location=location, limit=limit)
                
            elif scraper_name == 'meetup':
                from services.global_scrapers.meetup_scraper import MeetupScraper
                scraper = MeetupScraper()
                events = await scraper.search_events(location=location, limit=limit)
            
            execution_time = time.time() - start_time
            
            print(f"✅ {scraper_name}: {len(events)} events en {execution_time:.2f}s")
            
            # Mostrar algunos eventos de muestra
            if events:
                print(f"📋 Muestra de eventos:")
                for i, event in enumerate(events[:2], 1):
                    title = event.get('title', 'Sin título')[:50]
                    print(f"   {i}. {title}...")
            
            results[scraper_name] = {
                'events_count': len(events),
                'execution_time': execution_time,
                'success': True,
                'avg_time_per_event': execution_time / max(len(events), 1)
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {scraper_name}: ERROR en {execution_time:.2f}s")
            print(f"   Error: {str(e)}")
            
            results[scraper_name] = {
                'events_count': 0,
                'execution_time': execution_time,
                'success': False,
                'error': str(e),
                'avg_time_per_event': 0
            }
    
    # Análisis comparativo
    print(f"\n{'=' * 50}")
    print("📊 ANÁLISIS COMPARATIVO:")
    
    if len(results) >= 2:
        # Encontrar el más lento y el más rápido
        by_time = sorted(results.items(), key=lambda x: x[1]['execution_time'], reverse=True)
        slowest = by_time[0]
        fastest = by_time[-1]
        
        print(f"🐌 MÁS LENTO: {slowest[0]} ({slowest[1]['execution_time']:.2f}s)")
        print(f"⚡ MÁS RÁPIDO: {fastest[0]} ({fastest[1]['execution_time']:.2f}s)")
        
        # Calcular diferencia
        time_diff = slowest[1]['execution_time'] - fastest[1]['execution_time']
        print(f"⏰ DIFERENCIA: {time_diff:.2f}s ({time_diff/fastest[1]['execution_time']*100:.1f}% más lento)")
        
        # Eficiencia por evento
        print(f"\n📈 EFICIENCIA POR EVENTO:")
        for name, data in results.items():
            if data['success'] and data['events_count'] > 0:
                print(f"   {name}: {data['avg_time_per_event']:.2f}s por evento")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if slowest[1]['execution_time'] > 2.0:
            print(f"   ⚠️ {slowest[0]} tarda más de 2s - considerar optimizar")
        
        if slowest[1]['events_count'] < fastest[1]['events_count']:
            print(f"   📊 {slowest[0]} retorna menos eventos pero tarda más")
            print(f"   💭 Revisar si la lentitud está justificada por calidad de datos")

async def test_streaming_performance():
    """Test del streaming con async generator"""
    
    print(f"\n{'=' * 50}")
    print("🚀 TEST DE STREAMING PERFORMANCE")
    print("-" * 30)
    
    factory = IndustrialFactory()
    location = "Barcelona"
    
    start_time = time.time()
    scrapers_completed = 0
    first_result_time = None
    
    async for result in factory.execute_streaming(location=location, limit=3):
        scrapers_completed += 1
        current_time = time.time() - start_time
        
        if first_result_time is None:
            first_result_time = current_time
        
        scraper = result.get('scraper', 'unknown')
        events = len(result.get('events', []))
        
        if scraper in ['eventbrite', 'meetup']:  # Solo mostrar los que funcionan
            print(f"⚡ #{scrapers_completed} {scraper}: {events} events a los {current_time:.2f}s")
    
    total_time = time.time() - start_time
    
    print(f"\n📊 STREAMING METRICS:")
    print(f"⏱️  Tiempo al primer resultado: {first_result_time:.2f}s")
    print(f"⏱️  Tiempo total: {total_time:.2f}s")
    print(f"📊 Scrapers completados: {scrapers_completed}")
    
    if first_result_time and first_result_time < 2.0:
        print(f"✅ Streaming eficiente: primer resultado en < 2s")
    else:
        print(f"⚠️ Streaming lento: primer resultado > 2s")

if __name__ == "__main__":
    asyncio.run(analyze_individual_scrapers())
    asyncio.run(test_streaming_performance())