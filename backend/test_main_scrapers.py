#!/usr/bin/env python3
"""
🔍 TEST DE LOS 3 SCRAPERS PRINCIPALES 
Probar solo: eventbrite, meetup, events (Facebook API)
"""

import asyncio
import time
from typing import Dict, Any
from services.industrial_factory import IndustrialFactory

async def test_main_scrapers():
    """Test con solo los 3 scrapers principales esperados"""
    
    print("🔍 TESTING: 3 SCRAPERS PRINCIPALES")
    print("=" * 50)
    
    factory = IndustrialFactory()
    
    # Target scrapers esperados por el usuario
    main_scrapers = ['eventbrite', 'meetup', 'events']
    
    location = "Barcelona"
    limit = 5
    
    print(f"📍 Location: {location}")
    print(f"📊 Limit: {limit} events per scraper")
    print(f"🎯 Target scrapers: {main_scrapers}")
    print("\n" + "🚀 EJECUTANDO SCRAPERS..." + "\n")
    
    # Test streaming factory con async generator
    start_time = time.time()
    total_events = 0
    scraper_results = {}
    
    async for result in factory.execute_streaming(
        location=location,
        limit=limit
    ):
        scraper_name = result.get('scraper', 'unknown')
        events_count = len(result.get('events', []))
        execution_time = result.get('execution_time', 0)
        success = result.get('success', False)
        
        # Solo mostrar resultados de los 3 principales
        if scraper_name in main_scrapers:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{status} {scraper_name.upper()}")
            print(f"   ⏱️ Tiempo: {execution_time:.2f}s")
            print(f"   📊 Eventos: {events_count}")
            
            if not success and result.get('error'):
                print(f"   🚨 Error: {result['error']}")
            
            print()
            
            total_events += events_count
            scraper_results[scraper_name] = {
                'events': events_count,
                'time': execution_time,
                'success': success
            }
    
    total_time = time.time() - start_time
    
    # Resumen final
    print("=" * 50)
    print("📊 RESUMEN DE LOS 3 SCRAPERS PRINCIPALES:")
    print(f"⏱️  Tiempo total: {total_time:.2f}s")
    print(f"📊 Total eventos: {total_events}")
    
    # Identificar el más lento (cuello de botella)
    if scraper_results:
        slowest = max(scraper_results.items(), key=lambda x: x[1]['time'])
        fastest = min(scraper_results.items(), key=lambda x: x[1]['time'])
        
        print(f"🐌 Más lento: {slowest[0]} ({slowest[1]['time']:.2f}s)")
        print(f"⚡ Más rápido: {fastest[0]} ({fastest[1]['time']:.2f}s)")
        
        # Calcular speedup si fueran secuenciales
        sequential_time = sum(r['time'] for r in scraper_results.values())
        speedup = sequential_time / total_time
        print(f"🚀 Speedup: {speedup:.2f}x (vs secuencial: {sequential_time:.2f}s)")
    
    print("\n✅ Test completado")

if __name__ == "__main__":
    asyncio.run(test_main_scrapers())