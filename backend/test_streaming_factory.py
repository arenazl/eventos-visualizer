#!/usr/bin/env python3
"""
🧪 TEST SCRIPT - Factory con Async Generator Streaming
Prueba que los scrapers se ejecutan en paralelo y devuelven resultados en tiempo real
"""

import asyncio
import time
import logging
from services.industrial_factory import IndustrialFactory

# Configurar logging para ver métricas
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_streaming_factory():
    """
    Prueba el nuevo método execute_streaming con async generator
    """
    print("\n" + "="*60)
    print("🧪 TEST: IndustrialFactory con Async Generator Streaming")
    print("="*60)
    
    # Inicializar factory
    factory = IndustrialFactory()
    
    # Variables para métricas
    start_time = time.time()
    scrapers_times = {}
    total_events = 0
    
    print("\n📊 Iniciando streaming de scrapers en paralelo...")
    print("-" * 40)
    
    # Consumir el async generator
    async for result in factory.execute_streaming(
        location="Buenos Aires",
        limit=10
    ):
        # Tiempo transcurrido desde el inicio
        elapsed = time.time() - start_time
        
        if result['type'] == 'scrapers_discovered':
            print(f"\n🔍 Scrapers disponibles: {result['total_scrapers']}")
            for scraper in result['scraper_names']:
                print(f"   • {scraper}")
            print()
            
        elif result['type'] == 'scraper_completed':
            scraper_name = result['scraper_name']
            exec_time = result['execution_time']
            events_count = len(result.get('events', []))
            
            # Guardar métrica
            scrapers_times[scraper_name] = exec_time
            total_events += events_count
            
            # Mostrar resultado en tiempo real
            print(f"⏱️ [{elapsed:.2f}s] ✅ {scraper_name}: "
                  f"{events_count} eventos en {exec_time:.2f}s")
            
            # Mostrar progreso
            progress = result.get('progress', {})
            print(f"   📊 Progreso: {progress.get('completed')}/{progress.get('total')} "
                  f"({progress.get('percentage')}%) - "
                  f"Total eventos: {progress.get('total_events_so_far')}")
            
        elif result['type'] == 'scraper_timeout':
            scraper_name = result['scraper_name']
            exec_time = result['execution_time']
            
            scrapers_times[scraper_name] = exec_time
            
            print(f"⏱️ [{elapsed:.2f}s] ⏰ {scraper_name}: "
                  f"Timeout después de {exec_time:.2f}s")
            
        elif result['type'] == 'scraper_error':
            scraper_name = result.get('scraper_name', 'Unknown')
            error = result.get('error', 'Unknown error')
            
            print(f"⏱️ [{elapsed:.2f}s] ❌ {scraper_name}: {error}")
            
        elif result['type'] == 'streaming_completed':
            print(f"\n🎉 STREAMING COMPLETADO en {elapsed:.2f}s")
            print(f"   Total eventos: {result['total_events']}")
            print(f"   Scrapers completados: {result['scrapers_completed']}")
    
    # Análisis de cuellos de botella
    print("\n" + "="*60)
    print("📊 ANÁLISIS DE RENDIMIENTO - CUELLOS DE BOTELLA")
    print("="*60)
    
    if scrapers_times:
        # Ordenar por tiempo de ejecución
        sorted_scrapers = sorted(scrapers_times.items(), key=lambda x: x[1], reverse=True)
        
        print("\n🏆 Ranking de tiempos (más lento a más rápido):")
        for i, (scraper, exec_time) in enumerate(sorted_scrapers, 1):
            if i == 1:
                print(f"   🐢 {i}. {scraper}: {exec_time:.2f}s ⚠️ CUELLO DE BOTELLA")
            else:
                print(f"   ⚡ {i}. {scraper}: {exec_time:.2f}s")
        
        # Estadísticas
        avg_time = sum(scrapers_times.values()) / len(scrapers_times)
        max_time = max(scrapers_times.values())
        min_time = min(scrapers_times.values())
        
        print(f"\n📈 Estadísticas:")
        print(f"   • Tiempo promedio: {avg_time:.2f}s")
        print(f"   • Tiempo máximo: {max_time:.2f}s")
        print(f"   • Tiempo mínimo: {min_time:.2f}s")
        print(f"   • Diferencia max-min: {max_time - min_time:.2f}s")
        
        # Tiempo total vs tiempo secuencial
        sequential_time = sum(scrapers_times.values())
        actual_time = time.time() - start_time
        speedup = sequential_time / actual_time if actual_time > 0 else 0
        
        print(f"\n⚡ Optimización por paralelismo:")
        print(f"   • Tiempo secuencial (suma): {sequential_time:.2f}s")
        print(f"   • Tiempo real (paralelo): {actual_time:.2f}s")
        print(f"   • Speedup: {speedup:.2f}x más rápido")
        print(f"   • Tiempo ahorrado: {sequential_time - actual_time:.2f}s")
    
    print("\n" + "="*60)
    print(f"✅ Total de eventos obtenidos: {total_events}")
    print("="*60)

if __name__ == "__main__":
    # Ejecutar test
    asyncio.run(test_streaming_factory())