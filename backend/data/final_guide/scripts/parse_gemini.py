#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FASE 2: PARSING ELÁSTICO
Convierte respuestas RAW a JSON estructurado

Sistema INDEPENDIENTE de sitios e INDEPENDIENTE de regiones
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / 'config'
DATA_DIR = SCRIPT_DIR.parent.parent
RAW_DIR = DATA_DIR / 'scrapper_results' / 'raw'
PARSED_DIR = DATA_DIR / 'scrapper_results' / 'parsed'

# Cargar .env para Gemini API key
# DATA_DIR = backend/data, entonces backend = DATA_DIR.parent
BACKEND_DIR = DATA_DIR.parent
ENV_FILE = BACKEND_DIR / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    print(f"⚠️  Warning: .env not found at {ENV_FILE}")

# Crear directorio PARSED si no existe
PARSED_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# UTILIDADES COMPARTIDAS (desde event_utils.py y region_utils.py)
# ============================================================================
from event_utils import categorize_event, normalize_fecha as normalize_fecha_util
from region_utils import get_pais_from_ciudad, get_provincia_from_ciudad


def parse_gemini_table(raw_text: str) -> Optional[List[Dict]]:
    """
    Parsea tabla de eventos de Gemini con regex simple

    Formato de tabla de Gemini (CON BARRIO):
    Variante 1: #\tNombre\tDescripción\tFecha\tLugar/Dirección\tBarrio\tPrecio\tInfo Extra
    Variante 2: Nombre\tDescripción\tFecha\tLugar/Dirección\tBarrio\tPrecio\tInfo Extra

    Returns:
        Lista de eventos en formato JSON, o None si falla
    """

    try:
        eventos = []
        lines = raw_text.split('\n')

        for line in lines:
            # Skip líneas vacías o headers
            if not line.strip() or '📅' in line or 'Nombre del Evento' in line or line.startswith('#\t'):
                continue

            # Separar por tabs
            parts = line.split('\t')

            # Necesitamos al menos 6 campos (nombre, desc, fecha, lugar, barrio, precio)
            if len(parts) < 6:
                continue

            # Detectar si hay número al inicio
            tiene_numero = parts[0].strip().isdigit()

            if tiene_numero:
                # Formato: #\tNombre\t...
                idx_offset = 1  # Saltar el número

                # DETECTAR si el nombre se derrama al campo siguiente
                nombre_completo = parts[1]
                descripcion_idx = 2

                # Si parts[2] termina con **, es parte del nombre
                if len(parts) > 2 and parts[2].strip().endswith('**'):
                    nombre_completo = parts[1] + ' ' + parts[2]
                    descripcion_idx = 3

                # Limpiar nombre
                nombre = nombre_completo.replace('**', '').strip()

                # Ajustar índices según si hubo derrame
                if descripcion_idx == 3:
                    descripcion = parts[3].strip() if len(parts) > 3 else ''
                    fecha = parts[4].strip() if len(parts) > 4 else ''
                    lugar = parts[5].strip() if len(parts) > 5 else ''
                    barrio = parts[6].strip() if len(parts) > 6 else ''
                    precio = parts[7].strip() if len(parts) > 7 else 'Consultar'
                else:
                    descripcion = parts[2].replace('**', '').strip()
                    fecha = parts[3].strip()
                    lugar = parts[4].strip()
                    barrio = parts[5].strip()
                    precio = parts[6].strip()

            else:
                # Formato sin número: Nombre\tDescripción\t...
                # Verificar que no sea un header
                if 'Nombre del Evento' in parts[0] or 'Descripción' in parts[0]:
                    continue

                nombre = parts[0].strip()
                descripcion = parts[1].strip()
                fecha = parts[2].strip()
                lugar = parts[3].strip()
                barrio = parts[4].strip()
                precio = parts[5].strip()

            # Validar que tenga datos mínimos
            if not nombre or not fecha:
                continue

            evento = {
                'nombre': nombre,
                'descripcion': descripcion,
                'fecha': fecha,
                'lugar': lugar,
                'direccion': lugar,  # Gemini mezcla lugar y dirección
                'barrio': barrio,
                'precio': precio
            }

            eventos.append(evento)

        return eventos if eventos else None

    except Exception as e:
        print(f"      ❌ Error parseando tabla: {e}")
        return None


def parse_with_regex(raw_text: str) -> Optional[List[Dict]]:
    """
    Parsing con regex - llama al parser específico de Gemini

    Returns:
        Lista de eventos o None si falla
    """

    print("      🔧 Parseando con regex...")

    # Usar el parser de tabla de Gemini
    return parse_gemini_table(raw_text)


def normalize_date(fecha_str: str) -> str:
    """
    Normaliza fecha a formato YYYY-MM-DD

    Ejemplos:
        "Viernes 14 de Nov." → "2025-11-14"
        "Sábado 15 y Domingo 16 de Nov." → "2025-11-15"
        "Del 20 al 30 de Nov." → "2025-11-20"
    """

    # Mapa de meses en español
    meses = {
        'enero': '01', 'ene': '01',
        'febrero': '02', 'feb': '02',
        'marzo': '03', 'mar': '03',
        'abril': '04', 'abr': '04',
        'mayo': '05', 'may': '05',
        'junio': '06', 'jun': '06',
        'julio': '07', 'jul': '07',
        'agosto': '08', 'ago': '08',
        'septiembre': '09', 'sep': '09', 'sept': '09',
        'octubre': '10', 'oct': '10',
        'noviembre': '11', 'nov': '11',
        'diciembre': '12', 'dic': '12',
    }

    fecha_lower = fecha_str.lower()

    # Intentar extraer día y mes
    # Patrón: "14 de Nov"
    match = re.search(r'(\d{1,2})\s+de\s+(\w+)', fecha_lower)

    if match:
        dia = match.group(1).zfill(2)
        mes_str = match.group(2)

        mes = meses.get(mes_str[:3], '01')

        # Año actual o siguiente
        año = datetime.now().year

        return f"{año}-{mes}-{dia}"

    # Si ya está en formato YYYY-MM-DD, retornar as-is
    if re.match(r'\d{4}-\d{2}-\d{2}', fecha_str):
        return fecha_str

    # Fallback: fecha actual
    return datetime.now().strftime('%Y-%m-%d')


def enhance_evento(evento: Dict, ciudad: str) -> Dict:
    """
    Mejora y normaliza un evento individual

    Args:
        evento: Dict con datos raw del evento
        ciudad: Ciudad inferida del filename

    Returns:
        Dict con datos normalizados
    """

    # Normalizar fecha si no está en formato correcto
    fecha = evento.get('fecha', '')
    if not re.match(r'\d{4}-\d{2}-\d{2}', fecha):
        evento['fecha'] = normalize_date(fecha)

    # Agregar ciudad si no está
    if 'ciudad' not in evento:
        evento['ciudad'] = ciudad

    # Usar el barrio que vino de Gemini, o inferirlo si es "A verificar"
    barrio_raw = evento.get('barrio', '').strip()
    neighborhood = None

    # Si Gemini proporcionó un barrio válido, usarlo
    if barrio_raw and barrio_raw.lower() not in ['a verificar', 'consultar', '']:
        # Limpiar el barrio (ej: "Centro / San Nicolás" → "Centro")
        neighborhood = barrio_raw.split('/')[0].strip()
        # Normalizar variantes
        if 'centro' in neighborhood.lower():
            neighborhood = 'San Nicolás'
    else:
        # Fallback: Inferir del lugar/dirección si Gemini no proporcionó barrio
        lugar = evento.get('lugar', '').lower()
        direccion = evento.get('direccion', '').lower()
        texto_completo = f"{lugar} {direccion}"

        # Barrios explícitos en el texto
        barrios_bsas = [
            'palermo', 'recoleta', 'san telmo', 'puerto madero', 'retiro',
            'belgrano', 'villa crespo', 'almagro', 'caballito', 'nuñez',
            'colegiales', 'chacarita', 'flores', 'boedo', 'barracas',
            'la boca', 'constitución', 'monserrat', 'san nicolás', 'balvanera',
            'villa urquiza', 'villa devoto', 'saavedra', 'coghlan'
        ]

        for barrio in barrios_bsas:
            if barrio in texto_completo:
                neighborhood = barrio.title().replace('_', ' ')
                break

        # Mapeo de lugares conocidos
        if not neighborhood:
            lugares_conocidos = {
                'sarmiento 151': 'San Nicolás',
                'palacio libertad': 'San Nicolás',
                'av. del libertador 19': 'Recoleta',
                'libertador 19': 'Recoleta',
                'sarmiento 3131': 'Almagro',
                'konex': 'Almagro',
                'costanera': 'Costanera Norte',
                'el muelle': 'Costanera Norte',
                'microcentro': 'San Nicolás',
                'olivos': 'Olivos'
            }

            for lugar_key, barrio_value in lugares_conocidos.items():
                if lugar_key in texto_completo:
                    neighborhood = barrio_value
                    break

    evento['neighborhood'] = neighborhood

    # Categorizar evento
    category, subcategory = categorize_event(evento.get('nombre', ''), evento.get('descripcion', ''))
    evento['category'] = category
    evento['subcategory'] = subcategory

    # Agregar país y provincia según ciudad (DINÁMICO desde archivos de regiones)
    evento['pais'] = get_pais_from_ciudad(ciudad)
    evento['provincia'] = get_provincia_from_ciudad(ciudad)

    # Normalizar precio
    precio = evento.get('precio', 'Consultar')
    if 'gratis' in precio.lower() or 'gratuito' in precio.lower():
        evento['es_gratis'] = True
        evento['precio'] = 'Gratis'
    else:
        evento['es_gratis'] = False

    # Agregar source
    evento['source'] = 'gemini'

    return evento


def parse_raw_file(filepath: Path, debug: bool = False) -> Optional[List[Dict]]:
    """
    Parsea un archivo RAW y retorna lista de eventos

    Args:
        filepath: Path al archivo raw
        debug: Si True, muestra información de debugging

    Returns:
        Lista de eventos o None si falla
    """

    print(f"\n  📄 {filepath.name}")

    # Leer archivo raw
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except Exception as e:
        print(f"     ❌ Error leyendo archivo: {e}")
        return None

    if debug:
        print(f"     📊 Texto raw ({len(raw_text)} caracteres):")
        print(f"     {raw_text[:200]}...")

    # Parsear con regex simple (sin llamar a APIs)
    print(f"     🔧 Parseando con regex...")
    eventos = parse_with_regex(raw_text)

    if not eventos:
        print(f"     ❌ No se pudo parsear el archivo")
        return None

    # Extraer ciudad del filename
    # Ejemplo: "buenos-aires_2025-11-14.txt" → "Buenos Aires"
    ciudad_slug = filepath.stem.split('_')[0]
    ciudad = ciudad_slug.replace('-', ' ').title()

    # Mejorar cada evento
    eventos_mejorados = [enhance_evento(e, ciudad) for e in eventos]

    print(f"     ✅ {len(eventos_mejorados)} eventos parseados")

    if debug and eventos_mejorados:
        print(f"     📋 Primer evento:")
        print(f"        {json.dumps(eventos_mejorados[0], indent=2, ensure_ascii=False)[:300]}...")

    return eventos_mejorados


def save_parsed_json(site_id: str, source_file: Path, eventos: List[Dict]):
    """Guarda eventos parseados en JSON"""

    # Crear carpeta del sitio
    site_dir = PARSED_DIR / site_id
    site_dir.mkdir(exist_ok=True)

    # Usar mismo nombre que el archivo raw
    json_filename = source_file.stem + '.json'
    filepath = site_dir / json_filename

    # Guardar
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(eventos, f, indent=2, ensure_ascii=False)

    print(f"     💾 JSON guardado: {filepath.relative_to(DATA_DIR)}")


def run_parsing(sites_filter: Optional[List[str]] = None, debug: bool = False, reparse: bool = False):
    """
    Ejecuta parsing de archivos RAW

    Args:
        sites_filter: Lista de site_ids a parsear (None = todos)
        debug: Si True, muestra información detallada
        reparse: Si True, reparsea archivos ya procesados
    """

    print("=" * 80)
    print("🔧 FASE 2: PARSING ELÁSTICO")
    print("=" * 80)

    # Buscar todos los archivos RAW
    all_raw_files = []

    for site_dir in RAW_DIR.iterdir():
        if not site_dir.is_dir():
            continue

        site_id = site_dir.name

        # Filtrar por sitio si se especificó
        if sites_filter and site_id not in sites_filter:
            continue

        # Buscar archivos .txt
        raw_files = list(site_dir.glob('*.txt'))

        for raw_file in raw_files:
            all_raw_files.append((site_id, raw_file))

    print(f"\n📊 Total archivos RAW encontrados: {len(all_raw_files)}")

    if not all_raw_files:
        print("\n⚠️  No hay archivos RAW para parsear")
        print(f"💡 Ejecuta primero FASE 1 (scraping)")
        return

    # Filtrar archivos ya parseados si no es reparse
    files_to_parse = []

    for site_id, raw_file in all_raw_files:
        parsed_file = PARSED_DIR / site_id / f"{raw_file.stem}.json"

        if parsed_file.exists() and not reparse:
            print(f"  ⏭️  Ya parseado: {raw_file.name}")
        else:
            files_to_parse.append((site_id, raw_file))

    if not files_to_parse:
        print("\n✅ Todos los archivos ya están parseados")
        print(f"💡 Usa --reparse para reprocesar")
        return

    print(f"📋 Archivos a parsear: {len(files_to_parse)}")

    # Parsear archivos
    print("\n" + "=" * 80)
    print("🤖 INICIANDO PARSING")
    print("=" * 80)

    total_parseado = 0
    total_eventos = 0
    total_fallidos = 0

    for site_id, raw_file in files_to_parse:
        print(f"\n🌐 [{site_id.upper()}]")

        eventos = parse_raw_file(raw_file, debug=debug)

        if eventos:
            save_parsed_json(site_id, raw_file, eventos)
            total_parseado += 1
            total_eventos += len(eventos)
        else:
            total_fallidos += 1

    # Resumen
    print("\n" + "=" * 80)
    print("✨ PARSING COMPLETADO")
    print("=" * 80)
    print(f"\n✅ Archivos parseados exitosamente: {total_parseado}")
    print(f"📊 Total eventos extraídos: {total_eventos}")
    print(f"❌ Archivos fallidos: {total_fallidos}")
    print(f"📁 JSONs guardados en: {PARSED_DIR}")
    print("=" * 80 + "\n")


def main():
    """Main function"""

    # Parsear argumentos
    sites_filter = None
    debug = '--debug' in sys.argv
    reparse = '--reparse' in sys.argv

    if '--sites' in sys.argv:
        idx = sys.argv.index('--sites')
        if idx + 1 < len(sys.argv):
            sites_filter = sys.argv[idx + 1].split(',')

    # Ejecutar
    run_parsing(sites_filter, debug, reparse)


if __name__ == "__main__":
    main()
