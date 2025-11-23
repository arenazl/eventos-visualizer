#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FASE 2: Parser para formato de Felo.ai
Convierte RAW text de Felo a JSON estructurado

🤖 INTEGRACIÓN IA:
- Usa ai_utils.py para extraer ciudad/país del texto cuando no es claro
- Valida eventos con IA para detectar ubicaciones incorrectas
- Fallback a region_utils.py si IA no está disponible
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent.parent
RAW_DIR = DATA_DIR / 'scrapper_results' / 'raw' / 'felo'
PARSED_DIR = DATA_DIR / 'scrapper_results' / 'parsed' / 'felo'

# Crear directorio parsed
PARSED_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# UTILIDADES COMPARTIDAS
# ============================================================================
from region_utils import get_pais_from_ciudad, get_provincia_from_ciudad
from event_utils import categorize_event, normalize_fecha

# ============================================================================
# 🤖 INTEGRACIÓN IA (Ollama/Grok/OpenAI)
# ============================================================================
try:
    from ai_utils import (
        extract_location_from_text,
        validate_event_location,
        categorize_event_ai,
        is_ai_available
    )
    AI_AVAILABLE, AI_PROVIDER = is_ai_available()
except ImportError:
    AI_AVAILABLE = False
    AI_PROVIDER = "No importado"

    def extract_location_from_text(text, filename_hint=None):
        return {'ciudad': None, 'pais': None, 'provincia': None, 'confidence': 0.0}

    def validate_event_location(evento, city, country):
        return (True, "IA no disponible")

    def categorize_event_ai(nombre, descripcion=''):
        return ('General', 'Evento')


def parse_tsv_format(raw_text: str, ciudad: str) -> Optional[List[Dict]]:
    """
    Parsea formato TSV (Tab-Separated Values)

    Formato esperado:
    N°	Nombre del Evento	Descripción	Fecha	Lugar / Dirección	Barrio	Precio	Info Extra
    1	The Offspring	Concierto...	8 noviembre 2025	Paris La Défense Arena	La Défense	Desde €50	Presentan...
    """
    try:
        eventos = []
        lines = raw_text.strip().split('\n')

        if len(lines) < 2:
            return None

        # Detectar si la primera línea es header
        first_line = lines[0]
        if '\t' not in first_line:
            return None

        # Parsear header para saber qué columnas hay
        headers = [h.strip().lower() for h in first_line.split('\t')]

        # Mapeo de headers posibles
        col_map = {}
        for i, h in enumerate(headers):
            if 'nombre' in h or h == 'n°':
                if 'nombre' in h:
                    col_map['nombre'] = i
                else:
                    col_map['numero'] = i
            elif 'descripci' in h:
                col_map['descripcion'] = i
            elif 'fecha' in h:
                col_map['fecha'] = i
            elif 'lugar' in h or 'direcci' in h:
                col_map['lugar'] = i
            elif 'barrio' in h:
                col_map['barrio'] = i
            elif 'precio' in h:
                col_map['precio'] = i
            elif 'info' in h or 'extra' in h:
                col_map['info_extra'] = i

        # Si la primera columna es "N°", la segunda es el nombre
        if 'numero' in col_map and 'nombre' not in col_map:
            col_map['nombre'] = col_map.get('numero', 0) + 1

        # Parsear filas de datos (saltar header)
        for line in lines[1:]:
            if not line.strip():
                continue

            cols = line.split('\t')
            if len(cols) < 3:
                continue

            # Extraer campos dinámicamente según el header detectado
            def get_col(key, default=''):
                idx = col_map.get(key)
                if idx is not None and idx < len(cols):
                    return cols[idx].strip()
                return default

            nombre = get_col('nombre', '')
            descripcion = get_col('descripcion', '')
            fecha_raw = get_col('fecha', '')
            lugar = get_col('lugar', '')
            barrio = get_col('barrio', '')
            precio = get_col('precio', '')

            # Skip si no hay nombre válido
            if not nombre or nombre.startswith('N°') or nombre == '':
                continue

            # Limpiar número del inicio del nombre (ej: "1" o "1.")
            nombre_clean = re.sub(r'^\d+\.?\s*', '', nombre).strip()
            if not nombre_clean:
                nombre_clean = nombre

            # Normalizar fecha
            fecha_norm = normalize_fecha(fecha_raw)

            # Categorizar
            category, subcategory = categorize_event(nombre_clean, descripcion)

            # Determinar si es gratis
            es_gratis = any(word in precio.lower() for word in ['gratis', 'free', 'entrada libre', 'gratuito'])

            # Obtener país y provincia dinámicamente
            pais = get_pais_from_ciudad(ciudad)
            provincia = get_provincia_from_ciudad(ciudad)

            evento = {
                'nombre': nombre_clean,
                'descripcion': descripcion,
                'fecha': fecha_norm,
                'lugar': lugar,
                'direccion': lugar,
                'barrio': barrio if barrio else None,
                'precio': precio if precio else None,
                'ciudad': ciudad,
                'provincia': provincia,  # NUEVO: provincia/state dinámico
                'neighborhood': barrio if barrio else None,
                'category': category,
                'subcategory': subcategory,
                'pais': pais,
                'es_gratis': es_gratis,
                'source': 'felo'
            }

            eventos.append(evento)

        return eventos if eventos else None

    except Exception as e:
        print(f"      ❌ Error parseando formato TSV: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_felo_format(raw_text: str, ciudad: str) -> Optional[List[Dict]]:
    """
    Parsea formato de Felo.ai (línea por línea)

    Formato:
    Nombre del Evento

    Descripción: texto
    Fecha: texto
    Lugar: texto
    Dirección: texto
    Barrio: texto
    Precio: texto
    """
    try:
        eventos = []
        lines = raw_text.split('\n')

        current_event = None
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip líneas vacías o de header
            if not line or line.startswith('Aquí tienes') or line == 'Eventos en Buenos Aires':
                i += 1
                continue

            # Si la línea NO tiene ":", es un nombre de evento
            if ':' not in line:
                # Guardar evento anterior si existe
                if current_event and 'nombre' in current_event and 'fecha' in current_event:
                    eventos.append(current_event)

                # Iniciar nuevo evento
                current_event = {
                    'nombre': line,
                    'descripcion': '',
                    'fecha': '',
                    'lugar': '',
                    'direccion': '',
                    'barrio': 'A confirmar',
                    'precio': 'Gratis'
                }

            # Si tiene ":", es un campo
            elif current_event and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if 'descripci' in key:
                    current_event['descripcion'] = value
                elif 'fecha' in key:
                    current_event['fecha'] = value
                elif 'lugar' in key:
                    current_event['lugar'] = value
                elif 'direcci' in key:
                    current_event['direccion'] = value
                elif 'barrio' in key:
                    current_event['barrio'] = value
                elif 'precio' in key:
                    current_event['precio'] = value

            i += 1

        # Agregar último evento
        if current_event and 'nombre' in current_event and 'fecha' in current_event:
            eventos.append(current_event)

        # Normalizar y enriquecer eventos
        eventos_normalizados = []
        for e in eventos:
            nombre = e['nombre']
            descripcion = e['descripcion']
            fecha_raw = e['fecha']
            lugar = e['lugar']
            direccion = e['direccion']
            barrio = e['barrio']
            precio = e['precio']

            # Normalizar barrio (quitar puntos finales)
            barrio = barrio.rstrip('.')

            # Normalizar fecha
            fecha_norm = normalize_fecha(fecha_raw)

            # Categorizar
            category, subcategory = categorize_event(nombre, descripcion)

            # Determinar si es gratis
            es_gratis = any(word in precio.lower() for word in ['gratis', 'free', 'entrada libre'])

            # Obtener país y provincia dinámicamente
            pais = get_pais_from_ciudad(ciudad)
            provincia = get_provincia_from_ciudad(ciudad)

            evento = {
                'nombre': nombre,
                'descripcion': descripcion,
                'fecha': fecha_norm,
                'lugar': lugar,
                'direccion': direccion,
                'barrio': barrio if barrio else None,
                'precio': precio if precio else None,
                'ciudad': ciudad,
                'provincia': provincia,  # NUEVO: provincia/state dinámico
                'neighborhood': barrio if barrio else None,
                'category': category,
                'subcategory': subcategory,
                'pais': pais,
                'es_gratis': es_gratis,
                'source': 'felo'
            }

            eventos_normalizados.append(evento)

        return eventos_normalizados if eventos_normalizados else None

    except Exception as e:
        print(f"      ❌ Error parseando formato Felo: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_ciudad_from_filename(filename: str, raw_text: str = None) -> Dict[str, str]:
    """
    Extrae ciudad, país y provincia usando IA si está disponible.

    Args:
        filename: Nombre del archivo (ej: 'miami_2025-11-22.txt')
        raw_text: Contenido del archivo para análisis con IA

    Returns:
        {
            'ciudad': 'Miami',
            'pais': 'USA',
            'provincia': 'Florida',
            'method': 'ai' | 'fallback'
        }
    """
    # MÉTODO 1: Usar IA si está disponible
    if AI_AVAILABLE and raw_text:
        print(f"   🤖 Usando IA ({AI_PROVIDER}) para detectar ubicación...")
        ai_result = extract_location_from_text(raw_text, filename)

        if ai_result.get('confidence', 0) >= 0.7:
            ciudad = ai_result.get('ciudad')
            pais = ai_result.get('pais')
            provincia = ai_result.get('provincia')

            if ciudad and pais:
                print(f"   ✅ IA detectó: {ciudad}, {pais} (confianza: {ai_result.get('confidence', 0):.0%})")
                return {
                    'ciudad': ciudad,
                    'pais': pais,
                    'provincia': provincia,
                    'method': 'ai'
                }

    # MÉTODO 2: Fallback - extraer del filename + region_utils
    print(f"   📋 Usando fallback (filename + region_utils)...")
    ciudad_slug = filename.split('_')[0].replace('.txt', '')

    # Mapeo manual para casos conocidos
    ciudad_map = {
        'buenosaires': 'Buenos Aires',
        'buenos-aires': 'Buenos Aires',
        'cordoba': 'Córdoba',
        'rosario': 'Rosario',
        'mendoza': 'Mendoza',
        'mardelplata': 'Mar del Plata',
        'newyork': 'New York',
        'new-york': 'New York',
        'losangeles': 'Los Angeles',
        'sanfrancisco': 'San Francisco',
        'saopaulo': 'São Paulo',
        'riodejaneiro': 'Rio de Janeiro',
    }
    ciudad = ciudad_map.get(ciudad_slug, ciudad_slug.replace('-', ' ').title())

    # Obtener país y provincia de region_utils
    pais = get_pais_from_ciudad(ciudad)
    provincia = get_provincia_from_ciudad(ciudad)

    # Si region_utils no encuentra el país, marcar como Unknown
    if pais == 'Unknown':
        print(f"   ⚠️  Ciudad '{ciudad}' no encontrada en region_utils")

    return {
        'ciudad': ciudad,
        'pais': pais if pais != 'Unknown' else None,
        'provincia': provincia if provincia != 'Unknown' else None,
        'method': 'fallback'
    }


def auto_parse(raw_text: str, ciudad: str) -> Optional[List[Dict]]:
    """
    Auto-detecta el formato del archivo y usa el parser correcto.

    - Si tiene tabs en la primera línea → formato TSV
    - Si tiene "Descripción:" → formato línea por línea
    """
    lines = raw_text.strip().split('\n')
    if not lines:
        return None

    first_line = lines[0]

    # Detectar formato TSV (tiene tabs)
    if '\t' in first_line:
        print("   🔧 Formato detectado: TSV (tabla con tabs)")
        return parse_tsv_format(raw_text, ciudad)

    # Detectar formato línea por línea
    if any('Descripción:' in line or 'Fecha:' in line for line in lines[:20]):
        print("   🔧 Formato detectado: Línea por línea")
        return parse_felo_format(raw_text, ciudad)

    # Default: intentar TSV primero, luego línea por línea
    print("   🔧 Formato no detectado, intentando TSV...")
    eventos = parse_tsv_format(raw_text, ciudad)
    if eventos:
        return eventos

    print("   🔧 TSV falló, intentando línea por línea...")
    return parse_felo_format(raw_text, ciudad)


def main():
    """Parsea TODOS los archivos RAW de Felo con auto-detección de formato"""

    print("=" * 80)
    print("🔄 FASE 2: PARSING DE FELO.AI (AUTO-DETECCIÓN DE FORMATO)")
    print("=" * 80)

    # Buscar TODOS los archivos RAW de felo
    raw_files_felo = list(RAW_DIR.glob('*.txt'))

    # También buscar archivos en gemini que tengan formato línea por línea (sin tabs con "Descripción:")
    gemini_dir = DATA_DIR / 'scrapper_results' / 'raw' / 'gemini'
    raw_files_gemini = []
    for f in gemini_dir.glob('*.txt'):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            # Si no tiene tabs pero tiene "Descripción:" o "Fecha:", es formato línea por línea
            if '\t' not in content and ('Descripción:' in content or 'Fecha:' in content):
                raw_files_gemini.append(f)

    all_files = [(f, 'felo') for f in raw_files_felo] + [(f, 'gemini') for f in raw_files_gemini]

    if not all_files:
        print("❌ No se encontraron archivos RAW")
        return

    print(f"\n📁 Archivos encontrados: {len(all_files)}")

    total_eventos = 0
    archivos_ok = 0
    archivos_fail = 0

    for raw_file, source in all_files:
        print(f"\n📄 [{source.upper()}] {raw_file.name}")
        print(f"   Tamaño: {raw_file.stat().st_size / 1024:.1f} KB")

        # Extraer ciudad del filename PRIMERO
        ciudad = extract_ciudad_from_filename(raw_file.name)
        print(f"   🏙️  Ciudad: {ciudad} → País: {get_pais_from_ciudad(ciudad)}")

        # Leer contenido
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        # Parsear con auto-detección de formato
        eventos = auto_parse(raw_text, ciudad)

        if not eventos:
            print("   ❌ No se pudo parsear")
            archivos_fail += 1
            continue

        # FILTRAR eventos basura (headers, sin datos válidos)
        eventos_validos = []
        eventos_filtrados = 0
        for e in eventos:
            # Verificar que tenga datos mínimos: nombre, fecha
            nombre = e.get('nombre', '')
            fecha = e.get('fecha')

            # Skip si es un header genérico
            if nombre.lower().startswith('eventos en '):
                eventos_filtrados += 1
                continue

            # Skip si no tiene fecha
            if not fecha:
                eventos_filtrados += 1
                continue

            # Skip si nombre es muy corto o vacío
            if len(nombre.strip()) < 3:
                eventos_filtrados += 1
                continue

            eventos_validos.append(e)

        if eventos_filtrados > 0:
            print(f"   🗑️  Filtrados {eventos_filtrados} eventos basura (headers/sin datos)")

        eventos = eventos_validos

        if not eventos:
            print("   ❌ Todos los eventos fueron filtrados")
            archivos_fail += 1
            continue

        # Actualizar source según de dónde viene el archivo
        for e in eventos:
            e['source'] = source

        print(f"   ✅ {len(eventos)} eventos extraídos")
        total_eventos += len(eventos)
        archivos_ok += 1

        # Guardar en carpeta correspondiente
        output_dir = PARSED_DIR if source == 'felo' else (DATA_DIR / 'scrapper_results' / 'parsed' / 'gemini')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / raw_file.name.replace('.txt', '.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(eventos, f, indent=2, ensure_ascii=False)

        print(f"   💾 Guardado: {output_file.name}")

    print(f"\n" + "=" * 80)
    print(f"✨ PARSING COMPLETADO")
    print("=" * 80)
    print(f"✅ Archivos parseados: {archivos_ok}")
    print(f"❌ Archivos fallidos: {archivos_fail}")
    print(f"📊 Total eventos: {total_eventos}")
    print("=" * 80)


if __name__ == "__main__":
    main()
