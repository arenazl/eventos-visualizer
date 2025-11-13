#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper específico para BuenosAliens.com
Extrae eventos de música electrónica de Buenos Aires

Uso:
    python scrape_buenosaliens.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
import json
from playwright.async_api import async_playwright

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / 'scrapper_results' / 'latinamerica' / 'sudamerica' / 'argentina' / 'buenosaliens'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


async def scrape_buenosaliens():
    """
    Scrapea todos los eventos de BuenosAliens.com
    """
    print('='*70)
    print('🎧 SCRAPER BUENOSALIENS.COM - EVENTOS ELECTRÓNICOS')
    print('='*70)

    async with async_playwright() as p:
        # Lanzar navegador MAXIMIZADO
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--no-sandbox']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # Maximizar con JavaScript
        await page.evaluate('() => { window.moveTo(0, 0); window.resizeTo(screen.width, screen.height); }')

        try:
            # 1. Navegar a la página
            print('\n📍 Navegando a BuenosAliens.com...')
            await page.goto('https://www.buenosaliens.com/#agenda', wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)  # Más tiempo para cargar

            # 2. Obtener todos los eventos
            print('🔍 Buscando eventos...')

            # Selector de eventos
            eventos = await page.query_selector_all('div.item')
            print(f'✅ Encontrados {len(eventos)} eventos\n')

            eventos_data = []

            # 3. Iterar sobre cada evento
            for i, evento in enumerate(eventos, 1):
                try:
                    print(f'[{i}/{len(eventos)}] Procesando evento...')

                    # Click para expandir
                    await evento.click()
                    await asyncio.sleep(0.5)

                    # Extraer información expandida
                    evento_html = await evento.inner_html()
                    evento_text = await evento.inner_text()

                    # Parsear información
                    lines = evento_text.split('\n')

                    # Estructura típica:
                    # Línea 0: Título del evento
                    # Línea 1: Fecha (ej: "DOM 16 NOV")
                    # Línea 2: Lugar
                    # Siguientes: Line up, horario, dirección

                    titulo = lines[0] if len(lines) > 0 else ''
                    fecha_raw = lines[1] if len(lines) > 1 else ''
                    lugar = lines[2] if len(lines) > 2 else ''

                    # Extraer line up, horario, dirección
                    lineup = []
                    horario = ''
                    direccion = ''

                    for line in lines[3:]:
                        if 'Line up' in line:
                            continue
                        elif '(Italia)' in line or '(Argentina)' in line or '(España)' in line:
                            # Es un artista
                            lineup.append(line.strip())
                        elif 'Desde las' in line or 'hs' in line.lower():
                            horario = line.strip()
                        elif 'km' in line or 'Av.' in line or 'Calle' in line:
                            direccion = line.strip()

                    # Parsear fecha
                    # Formato: "DOM 16 NOV"
                    fecha_iso = None
                    if fecha_raw:
                        try:
                            # Extraer día y mes
                            parts = fecha_raw.split()
                            if len(parts) >= 3:
                                dia = parts[1]
                                mes_str = parts[2]

                                meses = {
                                    'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
                                    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
                                    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
                                }

                                mes = meses.get(mes_str, '11')
                                ano = '2025'

                                fecha_iso = f"{ano}-{mes}-{dia.zfill(2)}"
                        except:
                            pass

                    evento_info = {
                        'title': titulo,
                        'date': fecha_iso,
                        'date_raw': fecha_raw,
                        'venue': lugar,
                        'address': direccion,
                        'lineup': lineup,
                        'time': horario,
                        'category': 'música electrónica',
                        'city': 'Buenos Aires',
                        'country': 'Argentina',
                        'source': 'buenosaliens.com',
                        'scraped_at': datetime.now().isoformat()
                    }

                    eventos_data.append(evento_info)

                    print(f'  ✅ {titulo}')
                    print(f'     📅 {fecha_raw}')
                    print(f'     📍 {lugar}')

                    # Click de nuevo para colapsar (opcional)
                    await evento.click()
                    await asyncio.sleep(0.3)

                except Exception as e:
                    print(f'  ❌ Error: {str(e)[:100]}')
                    continue

            # 4. Guardar resultados
            if eventos_data:
                output_file = RESULTS_DIR / 'nightclub.json'

                output_data = {
                    'source': 'buenosaliens.com',
                    'url': 'https://www.buenosaliens.com/#agenda',
                    'scraped_at': datetime.now().isoformat(),
                    'total_events': len(eventos_data),
                    'events': eventos_data
                }

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)

                print(f'\n{"="*70}')
                print(f'✅ SCRAPING COMPLETADO')
                print(f'{"="*70}')
                print(f'📊 Total eventos: {len(eventos_data)}')
                print(f'💾 Guardado en: {output_file}')
                print(f'{"="*70}\n')

                return eventos_data
            else:
                print('\n⚠️  No se encontraron eventos')
                return []

        except Exception as e:
            print(f'\n❌ Error general: {e}')
            return []

        finally:
            await browser.close()


async def main():
    """Main function"""
    eventos = await scrape_buenosaliens()

    if eventos:
        print(f'\n🎉 {len(eventos)} eventos extraídos exitosamente!')
        print('\n📋 Primeros 5 eventos:')
        for i, evento in enumerate(eventos[:5], 1):
            print(f'\n{i}. {evento["title"]}')
            print(f'   📅 {evento["date_raw"]}')
            print(f'   📍 {evento["venue"]}')
            if evento['lineup']:
                print(f'   🎤 Line up: {", ".join(evento["lineup"][:3])}')


if __name__ == "__main__":
    asyncio.run(main())
