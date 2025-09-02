#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA SIMPLE PARA TICKETMASTER SCRAPER
Prueba el scraper sin necesidad de instalación previa
"""

import asyncio
import sys
import os

# Agregar el directorio de servicios al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

async def test_ticketmaster_without_install():
    """
    🎪 PRUEBA DEL SCRAPER SIN PLAYWRIGHT INSTALADO
    """
    
    print("🎪 TICKETMASTER PLAYWRIGHT SCRAPER - PRUEBA")
    print("=" * 50)
    print()
    
    try:
        # Intentar importar el scraper
        from ticketmaster_playwright_scraper import TicketmasterPlaywrightScraper
        
        # Crear instancia
        scraper = TicketmasterPlaywrightScraper()
        
        print("✅ Scraper creado exitosamente")
        print(f"🌍 Países soportados: {', '.join(scraper.get_supported_countries())}")
        print()
        
        # Intentar búsqueda
        print("🔍 Intentando búsqueda de eventos...")
        events = await scraper.search_events("concerts", "usa", max_events=3)
        
        print(f"📊 Eventos encontrados: {len(events)}")
        
        if events:
            print("\n🎫 EVENTOS EXTRAÍDOS:")
            print("-" * 40)
            for i, event in enumerate(events, 1):
                print(f"\n{i}. {event['title']}")
                if event['date']:
                    print(f"   📅 Fecha: {event['date']}")
                if event['venue']:
                    print(f"   🏛️ Venue: {event['venue']}")
                if event['price']:
                    print(f"   💰 Precio: {event['price']}")
                if event['url']:
                    print(f"   🔗 URL: {event['url']}")
        else:
            print("⚠️ No se encontraron eventos")
        
    except ImportError as e:
        print("❌ ERROR: Playwright no está instalado")
        print(f"   Detalles: {e}")
        print()
        print("🛠️ INSTRUCCIONES DE INSTALACIÓN:")
        print("   1. chmod +x install_playwright.sh")
        print("   2. ./install_playwright.sh")
        print("   3. python3 test_ticketmaster_simple.py")
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        print()
        print("🐛 Esto podría indicar:")
        print("   - Problema de red")
        print("   - Cambios en la estructura de Ticketmaster")
        print("   - Bloqueo por detección de bot")

def main():
    """Función principal"""
    print("🎭 INICIANDO PRUEBA DE TICKETMASTER SCRAPER")
    print()
    
    # Verificar si Playwright está disponible
    try:
        import playwright
        print("✅ Playwright está disponible")
        asyncio.run(test_ticketmaster_without_install())
    except ImportError:
        print("⚠️ Playwright no está instalado")
        print()
        print("📋 PASOS PARA INSTALACIÓN:")
        print("   1. Hacer ejecutable: chmod +x install_playwright.sh")
        print("   2. Ejecutar instalador: ./install_playwright.sh")
        print("   3. Probar scraper: python3 test_ticketmaster_simple.py")
        print()
        print("💡 El instalador descargará ~100MB de navegadores")

if __name__ == "__main__":
    main()