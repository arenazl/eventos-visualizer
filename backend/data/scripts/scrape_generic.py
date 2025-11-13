#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper genérico con 2 parámetros: URL y PROMPT
Usa Gemini AI para extraer eventos de cualquier URL según el prompt

Uso:
    python scrape_generic.py "URL" "PROMPT"

Ejemplos:
    python scrape_generic.py "https://buenosaires.gob.ar/agenda" "Extrae eventos de noviembre"
    python scrape_generic.py "https://alternativateatral.com" "Dame obras de teatro"
"""

import sys
import os
import json
import argparse
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


def fetch_url_content(url):
    """
    Obtiene el contenido de una URL usando requests
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        print(f'📡 Descargando contenido de: {url}')
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

        print(f'✅ Contenido descargado ({len(text)} caracteres)')
        return text

    except Exception as e:
        print(f'❌ Error descargando URL: {str(e)}')
        return None


def scrape_with_gemini(url, user_prompt):
    """
    Usa Gemini para extraer eventos de una URL según el prompt del usuario
    """
    print(f'\n🚀 Iniciando scraping con Gemini')
    print(f'📍 URL: {url}')
    print(f'💬 Prompt: {user_prompt}\n')

    # Obtener contenido de la URL
    content = fetch_url_content(url)

    if not content:
        return None

    # Limitar contenido si es muy largo (Gemini tiene límites)
    if len(content) > 30000:
        content = content[:30000]
        print(f'⚠️  Contenido truncado a 30000 caracteres')

    # Crear prompt completo para Gemini
    system_prompt = f"""
Eres un experto extractor de información de eventos.

El usuario te ha dado esta instrucción:
"{user_prompt}"

Analiza el siguiente contenido HTML/texto y extrae la información solicitada.

IMPORTANTE:
- Responde SOLO con un JSON válido
- Estructura: {{"eventos": [...]}}
- Cada evento debe tener al mínimo: nombre, fecha, lugar
- Si no encuentras eventos, responde: {{"eventos": []}}
- NO agregues texto adicional, SOLO JSON

Contenido a analizar:
{content}
"""

    try:
        print('🤖 Enviando a Gemini...')
        response = model.generate_content(system_prompt)

        # Extraer JSON de la respuesta
        response_text = response.text.strip()

        # Limpiar markdown si viene con ```json
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
        print(f'✅ Gemini encontró {len(eventos)} eventos')

        return eventos

    except json.JSONDecodeError as e:
        print(f'❌ Error parseando JSON: {str(e)}')
        print(f'Respuesta recibida: {response_text[:500]}...')
        return None
    except Exception as e:
        print(f'❌ Error con Gemini: {str(e)}')
        return None


def save_results(eventos, url, prompt):
    """
    Guarda los eventos en un archivo JSON
    """
    if not eventos:
        print('⚠️  No hay eventos para guardar')
        return

    # Crear nombre de archivo basado en URL y timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Extraer dominio de la URL para el nombre del archivo
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')

    filename = f'{domain}_{timestamp}.json'
    output_dir = Path(__file__).parent.parent / 'scrapper_results' / 'generic'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / filename

    # Agregar metadata
    output_data = {
        'url': url,
        'prompt': prompt,
        'timestamp': timestamp,
        'total_eventos': len(eventos),
        'eventos': eventos
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f'\n💾 Guardado en: {output_file}')
    print(f'📊 Total eventos: {len(eventos)}')


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Scraper genérico con URL y PROMPT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scrape_generic.py "https://buenosaires.gob.ar/agenda" "Eventos de noviembre"
  python scrape_generic.py "https://alternativateatral.com" "Obras de teatro este mes"
        """
    )

    parser.add_argument('url', help='URL a scrapear')
    parser.add_argument('prompt', help='Instrucción para Gemini sobre qué extraer')

    args = parser.parse_args()

    print('=' * 70)
    print('🔍 SCRAPER GENÉRICO CON GEMINI AI')
    print('=' * 70)

    # Scrapear
    eventos = scrape_with_gemini(args.url, args.prompt)

    # Guardar resultados
    if eventos:
        save_results(eventos, args.url, args.prompt)
        print('\n✅ Proceso completado exitosamente!')
    else:
        print('\n❌ No se encontraron eventos')
        sys.exit(1)


if __name__ == "__main__":
    main()
