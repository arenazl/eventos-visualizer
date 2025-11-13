#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper de felo.ai usando Playwright (estilo scraper_automated.py)
Va a felo.ai y pregunta por eventos en barrios de Argentina

Uso:
    python scrape_felo_playwright.py argentina
    python scrape_felo_playwright.py --barrio "Palermo"
"""

import sys
import json
import re
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Configuración
REGIONS_DIR = Path(__file__).parent.parent / "regions"
SCRAPPER_RESULTS_DIR = Path(__file__).parent.parent / "scrapper_results"
FELO_URL = "https://felo.ai"

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def get_prompt_template(barrio):
    """Genera prompt para Felo - NATURAL y directo"""
    return f"10 eventos importantes en {barrio}, Buenos Aires, Argentina este mes ordenado por popularidad, si puede ser con fecha, descripcion y direccion"


async def scrape_with_felo(barrio, output_path, headless=False, wait_manual=True):
    """
    Scrapea eventos usando Felo.ai

    Args:
        barrio: Barrio de Buenos Aires
        output_path: Ruta donde guardar el JSON
        headless: Si True, ejecuta en modo headless
        wait_manual: Si False, no espera input manual cuando falla
    """
    print(f"\n🔍 Scrapeando: {barrio}")
    print(f"📂 Guardará en: {output_path.relative_to(SCRAPPER_RESULTS_DIR.parent)}")

    async with async_playwright() as p:
        # Configurar navegador
        browser = await p.chromium.launch(
            headless=False,  # Cambiar a True para producción
            args=['--no-sandbox']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        try:
            # 1. Ir a Felo
            print("  📍 Abriendo felo.ai...")
            await page.goto(FELO_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)

            # 2. Buscar textarea
            print("  ⌨️  Buscando textarea...")

            selectors = [
                'textarea[placeholder*="Ask"]',
                'textarea[placeholder*="Search"]',
                'textarea[aria-label*="search"]',
                'textarea',
                '.ql-editor',
                '[contenteditable="true"]'
            ]

            textarea = None
            for selector in selectors:
                try:
                    textarea = await page.wait_for_selector(selector, timeout=5000)
                    if textarea:
                        print(f"  ✅ Encontrado textarea: {selector}")
                        break
                except:
                    continue

            if not textarea:
                print("  ❌ No se encontró textarea")
                if wait_manual:
                    print("  ⏳ Esperando input manual")
                    print("\n" + "="*70)
                    print("🚨 ACCIÓN MANUAL REQUERIDA:")
                    print("="*70)
                    print(f"\n1. En la ventana del navegador, copia este prompt:\n")
                    print("-" * 70)
                    print(get_prompt_template(barrio))
                    print("-" * 70)
                    print("\n2. Pégalo en Felo y presiona Enter")
                    print("3. Espera la respuesta completa")
                    print("4. Presiona Enter aquí cuando esté listo...")
                    print("="*70)
                    try:
                        input()
                    except (EOFError, KeyboardInterrupt):
                        print("\n❌ Cancelado por usuario")
                        return False
                else:
                    print("  ⏭️  Saltando (modo automático)")
                    return False

            else:
                # 3. Escribir prompt
                prompt = get_prompt_template(barrio)
                print(f"  📝 Escribiendo prompt ({len(prompt)} caracteres)...")
                await textarea.fill(prompt)
                await asyncio.sleep(1)

                # 4. Enviar
                print("  🚀 Enviando prompt...")
                send_selectors = [
                    'button[aria-label*="Send"]',
                    'button[type="submit"]',
                    'button:has-text("Send")',
                    'button:has-text("Search")',
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
                    # Fallback: Enter
                    await textarea.press('Enter')

                # 5. Esperar respuesta
                print("  ⏳ Esperando respuesta de Felo...")
                await asyncio.sleep(15)  # Dar tiempo para generar

            # 6. Extraer respuesta
            print("  📋 Extrayendo respuesta...")

            response_selectors = [
                '.model-response',
                '.response-content',
                '[data-test-id="response"]',
                '.markdown-content',
                'pre code',
                'code',
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
                # Fallback: todo el body
                print("  ⚠️  No se encontró selector - Usando fallback")
                response_text = await page.inner_text('body')

            # 7. Parsear JSON
            print("  🔍 Parseando JSON...")

            # Buscar JSON en la respuesta
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response_text)
            if not json_match:
                json_match = re.search(r'\{[\s\S]*"eventos"[\s\S]*\}', response_text)

            if json_match:
                json_str = json_match.group(1) if '```' in response_text else json_match.group(0)
                eventos_data = json.loads(json_str)

                # 8. Guardar
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(eventos_data, f, indent=2, ensure_ascii=False)

                eventos_count = len(eventos_data.get('eventos', []))
                print(f"  ✅ Guardado: {eventos_count} eventos en {output_path.name}")

                return True
            else:
                print("  ⚠️  No se encontró JSON, guardando respuesta raw...")

                # Guardar respuesta raw como JSON para procesar después
                raw_data = {
                    "barrio": barrio,
                    "respuesta_raw": response_text,
                    "fecha_scraping": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "necesita_procesamiento": True
                }

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(raw_data, f, indent=2, ensure_ascii=False)

                print(f"  ✅ Respuesta raw guardada en: {output_path.name}")
                print(f"  📝 Procesar después con Gemini")

                return True

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

        finally:
            await browser.close()


def load_argentina_barrios():
    """Carga barrios de Buenos Aires desde argentina.json"""
    argentina_path = REGIONS_DIR / "latinamerica/sudamerica/argentina.json"

    if not argentina_path.exists():
        print(f"❌ No se encontró: {argentina_path}")
        return []

    with open(argentina_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Buscar Buenos Aires
    for city in data.get('cities', []):
        if city.get('name') == 'Buenos Aires':
            barrios = city.get('barrios', [])
            return [b['name'] for b in barrios]

    return []


async def main():
    """Main function"""
    print("=" * 70)
    print("🎭 SCRAPER FELO.AI CON PLAYWRIGHT")
    print("=" * 70)

    # Determinar qué scrapear
    barrios = []
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if len(sys.argv) > 1:
        args = [a for a in sys.argv[1:] if a not in ['--yes', '-y']]

        if 'argentina' in sys.argv:
            # Cargar todos los barrios
            print("\n🇦🇷 Cargando barrios de Buenos Aires...")
            barrios = load_argentina_barrios()
            base_path = SCRAPPER_RESULTS_DIR / "latinamerica/sudamerica/argentina/buenos-aires/2025-11"

        elif '--barrio' in sys.argv and len(args) > 1:
            # Un solo barrio
            barrio_idx = sys.argv.index('--barrio') + 1
            barrios = [sys.argv[barrio_idx]]
            base_path = SCRAPPER_RESULTS_DIR / "latinamerica/sudamerica/argentina/buenos-aires/2025-11"

        else:
            print("❌ Uso: python scrape_felo_playwright.py argentina [--yes]")
            print("   o:  python scrape_felo_playwright.py --barrio 'Palermo' [--yes]")
            sys.exit(1)
    else:
        print("❌ Uso: python scrape_felo_playwright.py argentina [--yes]")
        print("   o:  python scrape_felo_playwright.py --barrio 'Palermo' [--yes]")
        sys.exit(1)

    if not barrios:
        print("❌ No se encontraron barrios para scrapear")
        sys.exit(1)

    print(f"\n📊 Total barrios a scrapear: {len(barrios)}")
    print(f"📂 Guardará en: {base_path.relative_to(SCRAPPER_RESULTS_DIR.parent)}")

    # Mostrar preview
    print("\n" + "="*70)
    print("Barrios:")
    for i, barrio in enumerate(barrios[:10], 1):
        print(f"  {i}. {barrio}")
    if len(barrios) > 10:
        print(f"  ... y {len(barrios) - 10} más")
    print("="*70)

    if len(barrios) > 1 and not auto_confirm:
        try:
            confirm = input("\n¿Continuar? (s/n): ").lower()
            if confirm != 's':
                print("❌ Cancelado")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Cancelado")
            sys.exit(0)
    elif len(barrios) > 1 and auto_confirm:
        print("\n✅ Auto-confirmado con --yes")

    # Scrapear
    success_count = 0
    fail_count = 0

    for i, barrio in enumerate(barrios, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(barrios)}] {barrio}")
        print('='*70)

        # Nombre de archivo
        barrio_slug = barrio.lower().replace(' ', '-')
        filename = f"{barrio_slug}_felo.json"
        output_path = base_path / filename

        # Verificar si existe
        if output_path.exists():
            print(f"  ⏭️  Ya existe: {filename}")
            if auto_confirm:
                print("  ⏩ Saltando (ya existe)...")
                continue
            else:
                try:
                    overwrite = input("  ¿Sobrescribir? (s/n): ").lower()
                    if overwrite != 's':
                        print("  ⏭️  Saltando...")
                        continue
                except (EOFError, KeyboardInterrupt):
                    print("  ⏭️  Saltando...")
                    continue

        # Scrapear
        success = await scrape_with_felo(barrio, output_path, headless=False, wait_manual=not auto_confirm)

        if success:
            success_count += 1
        else:
            fail_count += 1

        # Pausa entre requests
        if i < len(barrios):
            wait_time = 10
            print(f"\n  ⏸️  Pausando {wait_time} segundos...")
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
    print(f"   node add_images_generic.js ../scrapper_results/latinamerica/sudamerica/argentina/buenos-aires")
    print("\n📥 Siguiente: Importar a MySQL")
    print(f"   python import_generic.py scrapper_results/latinamerica/sudamerica/argentina/buenos-aires")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
