#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🤖 PARSE_RAW.PY - Parser Universal con IA

FASE 2 del pipeline: Convierte CUALQUIER archivo RAW a JSON estructurado.

Características:
- Escanea TODO backend/data/scrapper_results/raw/**/*.txt
- Usa IA (Ollama/Grok/OpenAI) para extraer eventos de cualquier formato
- Detecta ciudad, país, provincia automáticamente
- Categoriza eventos con IA
- NO depende del formato del archivo (TSV, línea por línea, markdown, etc.)

Uso:
    python parse_raw.py              # Procesa todos los archivos RAW
    python parse_raw.py --file X     # Procesa solo un archivo específico
    python parse_raw.py --dry-run    # Muestra qué se procesaría
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import requests

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent.parent
RAW_BASE_DIR = DATA_DIR / 'scrapper_results' / 'raw'
PARSED_BASE_DIR = DATA_DIR / 'scrapper_results' / 'parsed'

# Cargar .env
from dotenv import load_dotenv
BACKEND_DIR = DATA_DIR.parent
ENV_FILE = BACKEND_DIR / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# ============================================================================
# CONFIGURACIÓN IA
# ============================================================================
AI_PROVIDER = os.getenv('AI_PROVIDER', 'ollama')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
GROK_API_KEY = os.getenv('GROK_API_KEY', '')
GROK_MODEL = os.getenv('GROK_MODEL', 'grok-beta')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# ============================================================================
# CONFIGURACIÓN GOOGLE IMAGES
# ============================================================================
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_CX = os.getenv('GOOGLE_CX', '')
IMAGES_ENABLED = bool(GOOGLE_API_KEY and GOOGLE_CX)


# ============================================================================
# FUNCIONES DE IA
# ============================================================================
def call_ollama(prompt: str, system: str = None) -> Optional[str]:
    """Llama a Ollama local"""
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False
            },
            timeout=60  # Más tiempo para respuestas largas
        )

        if response.status_code == 200:
            return response.json().get('message', {}).get('content', '')
        return None
    except Exception as e:
        print(f"    ⚠️ Ollama error: {e}")
        return None


def call_grok(prompt: str, system: str = None) -> Optional[str]:
    """Llama a Grok (X.ai)"""
    if not GROK_API_KEY:
        return None
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROK_MODEL,
                "messages": messages,
                "temperature": 0.3
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        print(f"    ⚠️ Grok error: {e}")
        return None


def call_openai(prompt: str, system: str = None) -> Optional[str]:
    """Llama a OpenAI"""
    if not OPENAI_API_KEY:
        return None
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENAI_MODEL,
                "messages": messages,
                "temperature": 0.3
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        print(f"    ⚠️ OpenAI error: {e}")
        return None


def call_ai(prompt: str, system: str = None) -> Optional[str]:
    """Llama al provider de IA con fallback automático"""
    # Intentar en orden: Ollama → Grok → OpenAI
    result = call_ollama(prompt, system)
    if result:
        return result

    result = call_grok(prompt, system)
    if result:
        return result

    return call_openai(prompt, system)


def is_ai_available() -> tuple:
    """Verifica si hay IA disponible"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            return (True, f"Ollama ({OLLAMA_MODEL})")
    except:
        pass

    if GROK_API_KEY:
        return (True, f"Grok ({GROK_MODEL})")

    if OPENAI_API_KEY:
        return (True, f"OpenAI ({OPENAI_MODEL})")

    return (False, "Ninguno")


# ============================================================================
# FUNCIONES DE GOOGLE IMAGES
# ============================================================================
import time

def get_google_image(search_query: str) -> Optional[str]:
    """Busca una imagen en Google Custom Search"""
    if not IMAGES_ENABLED:
        return None

    try:
        response = requests.get(
            'https://www.googleapis.com/customsearch/v1',
            params={
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CX,
                'q': search_query,
                'searchType': 'image',
                'num': 1,
                'imgSize': 'large'
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('items') and len(data['items']) > 0:
                return data['items'][0]['link']

        # Rate limit
        if response.status_code == 429:
            print("    ⚠️ Google Images rate limit - esperando...")
            time.sleep(5)

        return None
    except Exception as e:
        print(f"    ⚠️ Google Images error: {e}")
        return None


def get_event_image(title: str, venue: str, city: str) -> Optional[str]:
    """
    Busca imagen del evento con triple fallback:
    1. Título completo + venue + ciudad
    2. Título reducido + ciudad
    3. Solo venue + ciudad
    """
    if not IMAGES_ENABLED:
        return None

    # Intento 1: Título completo
    search_query = f"{title} {venue} {city} event"
    image_url = get_google_image(search_query)
    if image_url:
        return image_url

    time.sleep(0.3)  # Rate limiting

    # Intento 2: Título reducido (primeras 3 palabras)
    reduced_title = ' '.join(title.split()[:3])
    if reduced_title and reduced_title != title:
        search_query = f"{reduced_title} {city} event"
        image_url = get_google_image(search_query)
        if image_url:
            return image_url

        time.sleep(0.3)

    # Intento 3: Solo venue + ciudad
    if venue:
        search_query = f"{venue} {city}"
        image_url = get_google_image(search_query)
        if image_url:
            return image_url

    return None


# ============================================================================
# PROMPT PRINCIPAL PARA EXTRAER EVENTOS
# ============================================================================
SYSTEM_PROMPT = """Eres un experto en extracción de datos de eventos. Tu tarea es analizar texto y extraer información estructurada de eventos.

REGLAS CRÍTICAS:
1. SOLO responde con JSON válido, sin texto adicional
2. Extrae TODOS los eventos que encuentres en el texto
3. Si un campo no está disponible, usa null
4. Las fechas deben estar en formato "YYYY-MM-DD" o "YYYY-MM-DD HH:MM"
5. Para precios: si es gratis usa "Gratis", si no tiene precio usa null
6. Detecta la ciudad y país PRINCIPAL donde ocurren los eventos
7. Categorías válidas: Música, Fiestas, Cultural, Deportes, Tech, Gastronomía, Familiar, Negocios, General

IMPORTANTE sobre ubicación:
- Los barrios NO son ciudades (Palermo → Buenos Aires, Wynwood → Miami)
- Si el texto dice "eventos en Miami, FL" → ciudad: "Miami", pais: "USA", provincia: "Florida"
- Si el texto menciona múltiples ciudades, usa la que aparece primero o más frecuentemente
"""

def build_extraction_prompt(raw_text: str, filename: str) -> str:
    """Construye el prompt para extraer eventos"""
    # Limitar texto a ~4000 caracteres para no saturar
    text_sample = raw_text[:4000] if len(raw_text) > 4000 else raw_text

    return f"""Analiza el siguiente texto de eventos y extrae la información.

Archivo: {filename}

TEXTO:
{text_sample}

Responde SOLO con este JSON (sin markdown, sin ```):
{{
  "ciudad": "nombre de la ciudad principal",
  "pais": "nombre del país",
  "provincia": "estado/provincia si aplica",
  "eventos": [
    {{
      "nombre": "nombre del evento",
      "descripcion": "descripción breve",
      "fecha": "YYYY-MM-DD o YYYY-MM-DD HH:MM",
      "fecha_fin": "YYYY-MM-DD o null si es un solo día",
      "lugar": "nombre del venue/lugar",
      "direccion": "dirección completa",
      "barrio": "barrio/zona o null",
      "precio": "precio o Gratis",
      "categoria": "una de las categorías válidas",
      "subcategoria": "subcategoría específica"
    }}
  ]
}}"""


def parse_ai_response(response: str) -> Optional[Dict]:
    """Parsea la respuesta JSON de la IA"""
    if not response:
        return None

    try:
        # Limpiar respuesta (a veces viene con markdown)
        cleaned = response.strip()

        # Remover bloques de código markdown
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            # Encontrar inicio y fin del JSON
            start = 1 if lines[0].startswith('```') else 0
            end = len(lines) - 1 if lines[-1] == '```' else len(lines)
            cleaned = '\n'.join(lines[start:end])

        # Encontrar el JSON en la respuesta
        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = cleaned[json_start:json_end]
            return json.loads(json_str)

        return None
    except json.JSONDecodeError as e:
        print(f"    ⚠️ Error parseando JSON: {e}")
        return None


def process_raw_file(filepath: Path, dry_run: bool = False) -> Dict:
    """
    Procesa un archivo RAW usando IA.

    Returns:
        {
            'success': bool,
            'eventos': int,
            'ciudad': str,
            'pais': str,
            'output_file': Path or None,
            'error': str or None
        }
    """
    result = {
        'success': False,
        'eventos': 0,
        'ciudad': None,
        'pais': None,
        'output_file': None,
        'error': None
    }

    # Leer archivo
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except Exception as e:
        result['error'] = f"Error leyendo archivo: {e}"
        return result

    if len(raw_text.strip()) < 50:
        result['error'] = "Archivo muy pequeño o vacío"
        return result

    if dry_run:
        result['success'] = True
        result['error'] = "[DRY-RUN] No procesado"
        return result

    # Llamar a la IA
    print(f"   🤖 Enviando a IA...")
    prompt = build_extraction_prompt(raw_text, filepath.name)
    ai_response = call_ai(prompt, SYSTEM_PROMPT)

    if not ai_response:
        result['error'] = "IA no respondió"
        return result

    # Parsear respuesta
    parsed = parse_ai_response(ai_response)

    if not parsed:
        result['error'] = "No se pudo parsear respuesta de IA"
        return result

    # Validar que tenga eventos
    eventos = parsed.get('eventos', [])
    if not eventos:
        result['error'] = "IA no encontró eventos"
        return result

    # Extraer ubicación
    ciudad = parsed.get('ciudad')
    pais = parsed.get('pais')
    provincia = parsed.get('provincia')

    if not ciudad or not pais:
        result['error'] = f"Ubicación incompleta: ciudad={ciudad}, pais={pais}"
        return result

    result['ciudad'] = ciudad
    result['pais'] = pais

    # Enriquecer eventos con ubicación e imágenes
    eventos_completos = []
    images_found = 0

    if IMAGES_ENABLED:
        print(f"   🖼️  Buscando imágenes para {len(eventos)} eventos...")

    for i, evento in enumerate(eventos, 1):
        evento['ciudad'] = ciudad
        evento['pais'] = pais
        evento['provincia'] = provincia
        evento['source'] = 'ai_parser'

        # Buscar imagen si no tiene y está habilitado
        if IMAGES_ENABLED and not evento.get('image_url'):
            title = evento.get('nombre', '')
            venue = evento.get('lugar', '')

            image_url = get_event_image(title, venue, ciudad)
            if image_url:
                evento['image_url'] = image_url
                images_found += 1
                print(f"      [{i}/{len(eventos)}] ✅ {title[:30]}...")
            else:
                print(f"      [{i}/{len(eventos)}] ⚠️ Sin imagen: {title[:30]}...")

            time.sleep(0.5)  # Rate limiting entre eventos

        eventos_completos.append(evento)

    if IMAGES_ENABLED:
        print(f"   🖼️  Imágenes encontradas: {images_found}/{len(eventos)}")

    result['eventos'] = len(eventos_completos)
    result['images'] = images_found

    # Determinar carpeta de salida (mantener estructura de raw/)
    # raw/felo/miami.txt → parsed/felo/miami.json
    relative_path = filepath.relative_to(RAW_BASE_DIR)
    output_dir = PARSED_BASE_DIR / relative_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / filepath.name.replace('.txt', '.json')

    # Guardar JSON
    output_data = {
        'ciudad': ciudad,
        'pais': pais,
        'provincia': provincia,
        'parsed_at': datetime.now().isoformat(),
        'source_file': str(filepath.name),
        'eventos': eventos_completos
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    result['success'] = True
    result['output_file'] = output_file

    return result


def find_raw_files() -> List[Path]:
    """Encuentra todos los archivos RAW para procesar"""
    if not RAW_BASE_DIR.exists():
        return []

    # Buscar todos los .txt recursivamente
    all_files = list(RAW_BASE_DIR.rglob('*.txt'))

    # Filtrar archivos muy pequeños
    valid_files = [f for f in all_files if f.stat().st_size > 100]

    return sorted(valid_files, key=lambda x: x.stat().st_mtime, reverse=True)


def main():
    """Main function"""
    global IMAGES_ENABLED
    import argparse

    parser = argparse.ArgumentParser(description='Parser universal con IA')
    parser.add_argument('--file', type=str, help='Procesar solo este archivo')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué se procesaría')
    parser.add_argument('--no-images', action='store_true', help='No buscar imágenes (más rápido)')
    args = parser.parse_args()

    # Desactivar imágenes si se especifica
    if args.no_images:
        IMAGES_ENABLED = False

    print("=" * 80)
    print("🤖 PARSE_RAW.PY - Parser Universal con IA + Imágenes")
    print("=" * 80)

    # Verificar IA
    ai_available, ai_provider = is_ai_available()
    if ai_available:
        print(f"\n✅ IA disponible: {ai_provider}")
    else:
        print(f"\n❌ IA NO disponible")
        print("   Opciones:")
        print("   1. Iniciar Ollama: ollama serve")
        print("   2. Configurar GROK_API_KEY en .env")
        print("   3. Configurar OPENAI_API_KEY en .env")
        sys.exit(1)

    # Verificar Google Images
    if IMAGES_ENABLED:
        print(f"✅ Google Images: Habilitado")
    else:
        if args.no_images:
            print(f"⏭️  Google Images: Desactivado (--no-images)")
        else:
            print(f"⚠️  Google Images: No configurado (GOOGLE_API_KEY/GOOGLE_CX faltantes)")

    # Encontrar archivos
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"\n❌ Archivo no encontrado: {filepath}")
            sys.exit(1)
        raw_files = [filepath]
    else:
        raw_files = find_raw_files()

    if not raw_files:
        print("\n❌ No se encontraron archivos RAW")
        print(f"   Directorio: {RAW_BASE_DIR}")
        sys.exit(1)

    print(f"\n📁 Archivos encontrados: {len(raw_files)}")

    if args.dry_run:
        print("\n🔍 MODO DRY-RUN - Solo mostrando archivos:")
        for f in raw_files[:20]:
            rel_path = f.relative_to(RAW_BASE_DIR)
            print(f"   📄 {rel_path}")
        if len(raw_files) > 20:
            print(f"   ... y {len(raw_files) - 20} más")
        return

    # Procesar archivos
    total_ok = 0
    total_fail = 0
    total_eventos = 0
    total_images = 0

    for raw_file in raw_files:
        rel_path = raw_file.relative_to(RAW_BASE_DIR)
        print(f"\n📄 {rel_path}")
        print(f"   Tamaño: {raw_file.stat().st_size / 1024:.1f} KB")

        result = process_raw_file(raw_file, dry_run=args.dry_run)

        if result['success']:
            total_ok += 1
            total_eventos += result['eventos']
            total_images += result.get('images', 0)
            img_info = f" | 🖼️ {result.get('images', 0)} imgs" if IMAGES_ENABLED else ""
            print(f"   ✅ {result['eventos']} eventos{img_info} → {result['ciudad']}, {result['pais']}")
            if result['output_file']:
                print(f"   💾 {result['output_file'].name}")
        else:
            total_fail += 1
            print(f"   ❌ {result['error']}")

    # Resumen
    print("\n" + "=" * 80)
    print("✨ PARSING COMPLETADO")
    print("=" * 80)
    print(f"✅ Archivos procesados: {total_ok}")
    print(f"❌ Archivos fallidos: {total_fail}")
    print(f"📊 Total eventos extraídos: {total_eventos}")
    if IMAGES_ENABLED:
        print(f"🖼️  Total imágenes encontradas: {total_images}")
    print("=" * 80)


if __name__ == "__main__":
    main()
