#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script automatizado para scrapear eventos con Gemini usando Bright Data

Uso:
    python scraper_automated.py argentina
    python scraper_automated.py europa/francia
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Configuración
REGIONS_DIR = Path(__file__).parent.parent / "regions"
SCRAPPER_RESULTS_DIR = Path(__file__).parent.parent / "scrapper_results"
GEMINI_URL = "https://gemini.com"

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def get_prompt_template(location, country):
    """Genera prompt para Gemini"""
    return f"""que hay para hacer, eventos, fiestas en {location}, {country} desde hoy a fin de mes, que se sepa la fecha, lugar, etc"""


async def scrape_with_gemini(location, country, output_path):
    """
    Scrapea eventos usando Gemini

    Args:
        location: Ciudad o barrio
        country: País
        output_path: Ruta donde guardar el JSON
    """
    print(f"\n🔍 Scrapeando: {location}, {country}")
    print(f"📂 Guardará en: {output_path.relative_to(SCRAPPER_RESULTS_DIR.parent)}")

    async with async_playwright() as p:
        # Configurar navegador
        # TODO: Agregar configuración de Bright Data proxy si es necesario
        browser = await p.chromium.launch(
            headless=False,  # Cambiar a True para producción
            args=['--start-maximized', '--no-sandbox']
        )

        context = await browser.new_context(
            viewport=None,  # Usar ventana completa (maximizada)
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        try:
            # 1. Ir a Gemini
            print("  📍 Abriendo gemini.com...")
            await page.goto(GEMINI_URL, wait_until='domcontentloaded')

            # Esperar más tiempo para que cargue completamente
            print("  ⏳ Esperando carga completa...")
            await asyncio.sleep(5)

            # 2. Buscar textarea (puede variar según la interfaz de Gemini)
            print("  ⌨️  Buscando textarea...")

            # Intentar varios selectores posibles de Gemini (actualizados 2025)
            selectors = [
                'div.ql-editor[contenteditable="true"]',  # Selector más común de Gemini
                'textarea',
                '[contenteditable="true"]',
                '.ql-editor',
                'div[role="textbox"]',
                'textarea[placeholder*="prompt"]',
                'textarea[aria-label*="prompt"]',
            ]

            textarea = None
            for selector in selectors:
                try:
                    print(f"    Intentando selector: {selector}")
                    textarea = await page.wait_for_selector(selector, timeout=3000)
                    if textarea:
                        # Verificar que sea visible
                        is_visible = await textarea.is_visible()
                        if is_visible:
                            print(f"  ✅ Encontrado textarea: {selector}")
                            break
                        else:
                            textarea = None
                except:
                    continue

            if not textarea:
                # Tomar screenshot para debug
                screenshot_path = Path(__file__).parent / f"debug_gemini_{location.replace(' ', '_')}.png"
                await page.screenshot(path=str(screenshot_path))
                print(f"  📸 Screenshot guardado: {screenshot_path.name}")

                print("  ❌ No se encontró textarea - Esperando input manual del usuario")
                print("\n" + "="*70)
                print("🚨 ACCIÓN MANUAL REQUERIDA:")
                print("="*70)
                print(f"\n1. En la ventana del navegador, copia este prompt:\n")
                print("-" * 70)
                print(get_prompt_template(location, country))
                print("-" * 70)
                print("\n2. Pégalo en Gemini y presiona Enter")
                print("3. Espera la respuesta completa")
                print("4. Presiona Enter aquí cuando esté listo...")
                print("="*70)
                input()

            else:
                # 3. Escribir prompt
                prompt = get_prompt_template(location, country)
                print(f"  📝 Escribiendo prompt ({len(prompt)} caracteres)...")
                await textarea.fill(prompt)
                await asyncio.sleep(1)

                # 4. Enviar (buscar botón de envío)
                print("  🚀 Enviando prompt...")
                send_selectors = [
                    'button[aria-label*="Send"]',
                    'button[type="submit"]',
                    'button:has-text("Send")',
                ]

                for selector in send_selectors:
                    try:
                        send_btn = await page.wait_for_selector(selector, timeout=2000)
                        if send_btn:
                            await send_btn.click()
                            break
                    except:
                        continue
                else:
                    # Si no encuentra botón, intentar Enter
                    await textarea.press('Enter')

                # 5. Esperar respuesta
                print("  ⏳ Esperando respuesta de Gemini...")
                await asyncio.sleep(10)  # Dar tiempo para que genere respuesta

            # 6. Extraer respuesta
            print("  📋 Extrayendo respuesta...")

            # Intentar obtener el texto de la respuesta
            response_selectors = [
                '.model-response',
                '[data-test-id="response"]',
                '.markdown-content',
                'pre code',
            ]

            response_text = None
            for selector in response_selectors:
                try:
                    response_elem = await page.wait_for_selector(selector, timeout=3000)
                    if response_elem:
                        response_text = await response_elem.inner_text()
                        break
                except:
                    continue

            if not response_text:
                # Fallback: obtener todo el texto de la página
                print("  ⚠️  No se encontró selector de respuesta - Usando fallback")
                response_text = await page.inner_text('body')

            # 7. Guardar respuesta en texto plano
            print("  💾 Guardando respuesta...")

            # Crear estructura para guardar
            output_data = {
                "location": location,
                "country": country,
                "query": get_prompt_template(location, country),
                "response_text": response_text,
                "scraped_at": datetime.now().isoformat(),
                "method": "gemini_playwright"
            }

            # 8. Guardar
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"  ✅ Guardado: {output_path.name}")
            print(f"  📊 Respuesta de {len(response_text)} caracteres")

            return True

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

        finally:
            await browser.close()


def load_argentina_barrios():
    """Carga barrios de Buenos Aires desde argentina.json"""
    argentina_path = REGIONS_DIR / "latinamerica/sudamerica/argentina.json"

    with open(argentina_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Buscar Buenos Aires
    for city in data['cities']:
        if city['name'] == 'Buenos Aires':
            barrios = city.get('barrios', [])
            return [(b['name'], 'Argentina') for b in barrios]

    return []


def load_country_cities(country_path):
    """Carga ciudades de un país"""
    with open(country_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    country = data['country']
    cities = []

    for city in data['cities']:
        # Si tiene barrios (caso Argentina), agregarlos
        if 'barrios' in city:
            for barrio in city['barrios']:
                cities.append((barrio['name'], country))
        else:
            cities.append((city['name'], country))

    return cities


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("❌ Uso: python scraper_automated.py <pais|region> [--yes]")
        print("\nEjemplos:")
        print("  python scraper_automated.py argentina")
        print("  python scraper_automated.py europa --yes")
        sys.exit(1)

    target = sys.argv[1].lower()
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    print("=" * 70)
    print("🤖 SCRAPER AUTOMATIZADO CON GEMINI")
    print("=" * 70)
    print(f"\n📍 Target: {target}")

    # Determinar qué scrapear
    locations = []

    if target == 'argentina':
        # Caso especial: Argentina con barrios
        print("\n🇦🇷 Cargando barrios de Buenos Aires...")
        locations = load_argentina_barrios()
        base_path = SCRAPPER_RESULTS_DIR / "latinamerica/sudamerica/argentina/2025-11"

    elif target.startswith('europa'):
        # Caso Europa: cargar todas las ciudades europeas
        print("\n🌍 Cargando ciudades europeas...")
        locations = []
        europa_regions = [
            'europa-occidental',
            'europa-meridional',
            'europa-septentrional',
            'europa-oriental',
            'europa-nororiental'
        ]

        for region in europa_regions:
            region_path = REGIONS_DIR / 'europa' / region
            if region_path.exists():
                for json_file in region_path.glob('*.json'):
                    cities = load_country_cities(json_file)
                    locations.extend(cities)

        base_path = SCRAPPER_RESULTS_DIR / "europa"

    else:
        # Caso general: país o región
        print(f"❌ Aún no implementado para: {target}")
        print("Opciones disponibles: argentina, europa")
        sys.exit(1)

    if not locations:
        print("❌ No se encontraron ubicaciones para scrapear")
        sys.exit(1)

    print(f"\n📊 Total ubicaciones a scrapear: {len(locations)}")
    print(f"📂 Guardará en: {base_path.relative_to(SCRAPPER_RESULTS_DIR.parent)}")

    # Confirmar
    print("\n" + "="*70)
    print("Ubicaciones:")
    for i, (location, country) in enumerate(locations[:10], 1):
        print(f"  {i}. {location}, {country}")
    if len(locations) > 10:
        print(f"  ... y {len(locations) - 10} más")
    print("="*70)

    if not auto_confirm:
        confirm = input("\n¿Continuar? (s/n): ").lower()
        if confirm != 's':
            print("❌ Cancelado")
            sys.exit(0)
    else:
        print("\n✅ Auto-confirmado (--yes)")
        await asyncio.sleep(2)

    # Scrapear
    success_count = 0
    fail_count = 0

    for i, (location, country) in enumerate(locations, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(locations)}] {location}, {country}")
        print('='*70)

        # Determinar nombre de archivo y ruta
        location_slug = location.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        country_slug = country.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        today = datetime.now().strftime('%Y%m%d')
        filename = f"{location_slug}_dia_gemini.json"

        # Para Europa, organizar por país
        if target.startswith('europa'):
            # Determinar región del país
            region_map = {
                'alemania': 'europa-occidental',
                'francia': 'europa-occidental',
                'bélgica': 'europa-occidental',
                'países-bajos': 'europa-occidental',
                'suiza': 'europa-occidental',
                'austria': 'europa-occidental',
                'españa': 'europa-meridional',
                'italia': 'europa-meridional',
                'grecia': 'europa-meridional',
                'portugal': 'europa-meridional',
                'reino-unido': 'europa-septentrional',
                'irlanda': 'europa-septentrional',
                'suecia': 'europa-septentrional',
                'noruega': 'europa-septentrional',
                'dinamarca': 'europa-septentrional',
                'finlandia': 'europa-septentrional',
                'polonia': 'europa-oriental',
                'chequia': 'europa-oriental',
                'hungría': 'europa-oriental',
                'rumania': 'europa-oriental',
                'rusia': 'europa-nororiental'
            }
            region = region_map.get(country_slug, 'europa-occidental')
            output_path = base_path / region / country_slug / filename
        else:
            output_path = base_path / filename

        # Verificar si ya existe
        if output_path.exists():
            print(f"  ⏭️  Ya existe: {filename}")
            if not auto_confirm:
                overwrite = input("  ¿Sobrescribir? (s/n): ").lower()
                if overwrite != 's':
                    print("  ⏭️  Saltando...")
                    continue
            else:
                print("  ⏭️  Saltando (ya existe)...")
                continue

        # Scrapear
        success = await scrape_with_gemini(location, country, output_path)

        if success:
            success_count += 1
        else:
            fail_count += 1

        # Pausa entre requests (evitar rate limiting)
        if i < len(locations):
            wait_time = 10
            print(f"\n  ⏸️  Pausando {wait_time} segundos antes del siguiente...")
            await asyncio.sleep(wait_time)

    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN FINAL")
    print("="*70)
    print(f"✅ Exitosos: {success_count}")
    print(f"❌ Fallidos: {fail_count}")
    print(f"📁 Guardados en: {base_path}")
    print("\n🖼️  Próximo paso: Agregar imágenes")
    print(f"   cd backend/data/scripts")
    print(f"   node add_images_generic.js scrapper_results/latinamerica/sudamerica/argentina/2025-11")
    print("\n📥 Siguiente: Importar a MySQL")
    print(f"   python import_generic.py scrapper_results/latinamerica/sudamerica/argentina/2025-11")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
