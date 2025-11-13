#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script que lee sources-felo.md y procesa todas las URLs con sus prompts
Cada fuente tiene su URL y prompt específico

Uso:
    python scrape_from_sources.py
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Cargar .env
SCRIPT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = SCRIPT_DIR / '.env'

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Configurar Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print('❌ Error: GEMINI_API_KEY no encontrado en .env')
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def parse_sources_file(filepath):
    """
    Lee sources-felo.md y extrae pares de URL y PROMPT

    Formato esperado:
    ## Nombre del sitio
    url=https://example.com
    prompt=Extrae eventos...
    """
    sources = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_name = None
    current_url = None
    current_prompt = None

    for line in lines:
        line = line.strip()

        # Detectar nombre (## Título)
        if line.startswith('##') and not line.startswith('###'):
            current_name = line.replace('##', '').strip()

        # Detectar URL
        elif line.startswith('url='):
            current_url = line.replace('url=', '').strip()

        # Detectar PROMPT
        elif line.startswith('prompt='):
            current_prompt = line.replace('prompt=', '').strip()

            # Si tenemos URL y PROMPT, agregar a la lista
            if current_url and current_prompt:
                sources.append({
                    'name': current_name or 'Sin nombre',
                    'url': current_url,
                    'prompt': current_prompt
                })

                # Reset para siguiente fuente
                current_name = None
                current_url = None
                current_prompt = None

    return sources


def fetch_url_content(url):
    """
    Descarga el contenido de una URL
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remover scripts y styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Obtener texto limpio
        text = soup.get_text()

        # Limpiar espacios
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    except Exception as e:
        print(f'  ❌ Error descargando: {str(e)}')
        return None


def scrape_with_gemini(url, prompt, content):
    """
    Usa Gemini para extraer eventos según el prompt
    """
    # Limitar contenido si es muy largo
    if len(content) > 30000:
        content = content[:30000]

    # Crear prompt completo para Gemini
    system_prompt = f"""
Eres un experto extractor de información de eventos.

INSTRUCCIÓN DEL USUARIO:
{prompt}

Analiza el siguiente contenido HTML/texto y extrae la información solicitada.

IMPORTANTE:
- Responde SOLO con un JSON válido
- Estructura: {{"eventos": [...]}}
- Cada evento debe tener: nombre, fecha, lugar
- Campos opcionales: descripcion, precio, categoria, hora
- Si no encuentras eventos, responde: {{"eventos": []}}
- NO agregues texto adicional, SOLO JSON

Contenido a analizar:
{content}
"""

    try:
        response = model.generate_content(system_prompt)

        # Extraer JSON de la respuesta
        response_text = response.text.strip()

        # Limpiar markdown
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        # Parsear JSON
        data = json.loads(response_text)
        eventos = data.get('eventos', [])

        return eventos

    except json.JSONDecodeError as e:
        print(f'  ❌ Error parseando JSON: {str(e)}')
        return None
    except Exception as e:
        print(f'  ❌ Error con Gemini: {str(e)}')
        return None


def save_results(source_name, eventos, url):
    """
    Guarda los eventos en un archivo JSON
    """
    if not eventos:
        return

    # Crear nombre de archivo
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')

    # Limpiar nombre de la fuente para usar como filename
    safe_name = source_name.lower().replace(' ', '_')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')

    filename = f'{safe_name}_{timestamp}.json'

    output_dir = Path(__file__).parent.parent / 'scrapper_results' / 'argentina_felo'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / filename

    # Crear estructura de datos
    output_data = {
        'fuente': source_name,
        'url': url,
        'timestamp': timestamp,
        'total_eventos': len(eventos),
        'eventos': eventos
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f'  💾 Guardado: {filename} ({len(eventos)} eventos)')


def main():
    """Main function"""
    print('=' * 70)
    print('🔍 SCRAPER AUTOMÁTICO DESDE sources-felo.md')
    print('=' * 70)

    # Leer archivo de fuentes
    sources_file = Path(__file__).parent / 'sources-felo.md'

    if not sources_file.exists():
        print(f'❌ No se encontró: {sources_file}')
        sys.exit(1)

    print(f'\n📄 Leyendo: {sources_file.name}')

    sources = parse_sources_file(sources_file)

    if not sources:
        print('❌ No se encontraron fuentes en el archivo')
        sys.exit(1)

    print(f'✅ {len(sources)} fuentes encontradas\n')

    # Procesar cada fuente
    total_eventos = 0

    for i, source in enumerate(sources):
        print(f'\n[{i + 1}/{len(sources)}] 🌐 {source["name"]}')
        print(f'  📍 URL: {source["url"]}')
        print(f'  💬 Prompt: {source["prompt"][:60]}...')

        # Descargar contenido
        print(f'  📡 Descargando...')
        content = fetch_url_content(source['url'])

        if not content:
            print(f'  ⚠️  Saltando (error de descarga)')
            continue

        print(f'  ✅ Descargado ({len(content)} caracteres)')

        # Procesar con Gemini
        print(f'  🤖 Procesando con Gemini...')
        eventos = scrape_with_gemini(source['url'], source['prompt'], content)

        if eventos is None:
            print(f'  ⚠️  Error procesando')
            continue

        print(f'  ✅ {len(eventos)} eventos encontrados')

        # Guardar resultados
        if eventos:
            save_results(source['name'], eventos, source['url'])
            total_eventos += len(eventos)

        # Pausa para no saturar la API
        if i < len(sources) - 1:
            print(f'  ⏸️  Esperando 3 segundos...')
            time.sleep(3)

    # Resumen final
    print('\n' + '=' * 70)
    print('🎉 PROCESO COMPLETADO')
    print(f'✅ Total eventos extraídos: {total_eventos}')
    print(f'📂 Resultados en: scrapper_results/argentina_felo/')
    print('=' * 70 + '\n')


if __name__ == "__main__":
    main()
