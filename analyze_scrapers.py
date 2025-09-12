#!/usr/bin/env python3
"""
Análisis de tiempos de ejecución de scrapers
"""
import requests
import json
from datetime import datetime

def analyze_scrapers(location="Buenos Aires", limit=10):
    """Analiza los tiempos de ejecución de cada scraper"""
    
    print(f"\n🔍 ANÁLISIS DE SCRAPERS - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)
    print(f"📍 Ubicación: {location}")
    print(f"📊 Límite: {limit} eventos por scraper")
    print("=" * 70)
    
    # Hacer request con detalles de scrapers
    url = f"http://172.29.228.80:8001/api/events?location={location}&limit={limit}&include_scrapers=true"
    
    try:
        response = requests.get(url, timeout=30)
        data = response.json()
        
        if 'scrapers_execution' in data:
            exec_data = data['scrapers_execution']
            
            print(f"\n📊 RESUMEN GENERAL:")
            print(f"  • Total de scrapers: {exec_data.get('total_scrapers', 0)}")
            print(f"  • Scrapers exitosos: {exec_data.get('successful_scrapers', 0)}")
            print(f"  • Tiempo total: {exec_data.get('total_time', 'N/A')}")
            print(f"  • Eventos totales: {data.get('total', 0)}")
            
            print(f"\n📋 DETALLES POR SCRAPER:")
            print("-" * 70)
            print(f"{'Scraper':<25} {'Status':<10} {'Eventos':<10} {'Tiempo':<10} {'Mensaje'}")
            print("-" * 70)
            
            scrapers_info = exec_data.get('scrapers_info', [])
            
            # Ordenar por tiempo de respuesta
            scrapers_info.sort(key=lambda x: float(x.get('response_time', '0s').replace('s', '')), reverse=True)
            
            for scraper in scrapers_info:
                name = scraper.get('name', 'Unknown')
                status = scraper.get('status', 'unknown')
                events = scraper.get('events_count', 0)
                time = scraper.get('response_time', 'N/A')
                
                # Color coding por status
                if status == 'success':
                    icon = '✅'
                elif status == 'timeout':
                    icon = '⏰'
                else:
                    icon = '❌'
                
                print(f"{icon} {name:<23} {status:<10} {events:<10} {time:<10}", end="")
                
                if status != 'success' and 'message' in scraper:
                    msg = scraper['message'][:30]
                    print(f" {msg}...")
                else:
                    print()
            
            print("-" * 70)
            
            # Análisis de performance
            print(f"\n⚡ ANÁLISIS DE PERFORMANCE:")
            
            successful = [s for s in scrapers_info if s.get('status') == 'success']
            failed = [s for s in scrapers_info if s.get('status') == 'failed']
            timeout = [s for s in scrapers_info if s.get('status') == 'timeout']
            
            if successful:
                times = [float(s.get('response_time', '0s').replace('s', '')) for s in successful]
                avg_time = sum(times) / len(times) if times else 0
                max_time = max(times) if times else 0
                min_time = min(times) if times else 0
                
                print(f"  • Tiempo promedio (exitosos): {avg_time:.2f}s")
                print(f"  • Tiempo máximo: {max_time:.2f}s")
                print(f"  • Tiempo mínimo: {min_time:.2f}s")
            
            if timeout:
                print(f"\n⚠️ TIMEOUTS DETECTADOS:")
                for s in timeout:
                    print(f"  • {s.get('name', 'Unknown')}: Timeout después de {s.get('response_time', 'N/A')}")
            
            if failed:
                print(f"\n❌ SCRAPERS FALLIDOS:")
                for s in failed:
                    print(f"  • {s.get('name', 'Unknown')}: {s.get('message', 'Error desconocido')[:50]}...")
            
            # Identificar cuellos de botella
            print(f"\n🔥 CUELLOS DE BOTELLA IDENTIFICADOS:")
            bottlenecks = [s for s in scrapers_info if float(s.get('response_time', '0s').replace('s', '')) > 3.0]
            if bottlenecks:
                for s in bottlenecks:
                    print(f"  • {s.get('name', 'Unknown')}: {s.get('response_time', 'N/A')} (>3s)")
            else:
                print("  • No se detectaron scrapers lentos (>3s)")
            
        else:
            print("⚠️ No hay información detallada de scrapers")
            print(f"Eventos encontrados: {data.get('total', 0)}")
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout al contactar el servidor (>30s)")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    # Analizar con diferentes ciudades
    cities = ["Buenos Aires", "Madrid", "Barcelona", "Miami"]
    
    for city in cities:
        analyze_scrapers(city, limit=5)
        print("\n" + "="*70 + "\n")