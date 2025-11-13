#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Procesa archivos *_felo.json que tienen respuesta_raw
Parsea el texto estructurado y convierte a formato JSON estándar
(Mismo flujo que eventos de Gemini: parsear → add_images → import_generic)

Uso:
    python process_felo_raw.py                    # Procesa todos los archivos felo pendientes
    python process_felo_raw.py --folder latinamerica/sudamerica/argentina/buenos-aires/2025-11
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent


def parse_felo_events(respuesta_raw: str, barrio: str) -> list:
    """
    Parsea eventos del texto estructurado de felo.ai
    Soporta dos formatos:
    1. Con números: "1. Nombre\nFecha: ..."
    2. Sin números: "Nombre\n\nFecha: ..."
    """
    eventos = []

    # Split por líneas
    lineas = respuesta_raw.split('\n')

    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()

        # Detectar inicio de evento (dos formatos)
        es_evento_numerado = re.match(r'^\d+\.\s+', linea)
        es_evento_sin_numero = (
            linea and  # No vacía
            not linea.startswith(('Fecha:', 'Descripción:', 'Dirección:', 'Convert', 'Ask', 'Felo', 'Search', 'Answer', 'Image', 'Video', 'Source', 'New', 'Export', '¿', 'Pro')) and
            i + 2 < len(lineas) and
            lineas[i + 1].strip() == '' and  # Línea vacía después
            lineas[i + 2].strip().startswith('Fecha:')  # Seguido de "Fecha:"
        )

        if es_evento_numerado or es_evento_sin_numero:
            # Extraer nombre
            if es_evento_numerado:
                nombre = re.sub(r'^\d+\.\s+', '', linea).strip()
            else:
                nombre = linea

            fecha_str = None
            descripcion = None
            direccion = None

            # Leer las siguientes líneas
            i += 1
            while i < len(lineas):
                siguiente = lineas[i].strip()

                # Si encontramos otro evento, terminar este
                if re.match(r'^\d+\.\s+', siguiente):
                    break

                # Para formato sin números, terminar si encontramos título + línea vacía + Fecha:
                if (siguiente and
                    not siguiente.startswith(('Fecha:', 'Descripción:', 'Dirección:')) and
                    i + 2 < len(lineas) and
                    lineas[i + 1].strip() == '' and
                    lineas[i + 2].strip().startswith('Fecha:')):
                    break

                # Extraer campos
                if siguiente.startswith('Fecha:'):
                    fecha_str = siguiente.replace('Fecha:', '').strip()
                elif siguiente.startswith('Descripción:'):
                    descripcion = siguiente.replace('Descripción:', '').strip()
                elif siguiente.startswith('Dirección:'):
                    direccion = siguiente.replace('Dirección:', '').strip()

                i += 1

            # Si tenemos los datos mínimos, crear evento
            if nombre and fecha_str:
                fecha = parse_fecha_felo(fecha_str)
                lugar = extraer_lugar(direccion) if direccion else barrio
                categoria = inferir_categoria(nombre, descripcion or '')

                evento = {
                    'nombre': nombre,
                    'fecha': fecha,
                    'hora_inicio': None,
                    'hora_fin': None,
                    'lugar': lugar,
                    'descripcion': descripcion or 'Sin descripción',
                    'categoria': categoria,
                    'precio': 'Por confirmar',
                    'estado': 'confirmado'
                }

                eventos.append(evento)
        else:
            i += 1

    return eventos


def parse_fecha_felo(fecha_str: str) -> str:
    """
    Parsea fechas como "8 y 9 de noviembre" → "2025-11-08"
    """
    match = re.search(r'(\d+)', fecha_str)
    if match:
        dia = int(match.group(1))
        return f'2025-11-{dia:02d}'

    return datetime.now().strftime('%Y-%m-%d')


def extraer_lugar(direccion: str) -> str:
    """Extrae el nombre del lugar de la dirección"""
    if ',' in direccion:
        return direccion.split(',')[0].strip()
    return direccion.strip()


def inferir_categoria(nombre: str, descripcion: str) -> str:
    """Infiere categoría del evento"""
    texto = (nombre + ' ' + descripcion).lower()

    if any(word in texto for word in ['música', 'festival', 'concierto', 'recital', 'music']):
        return 'música'
    elif any(word in texto for word in ['museo', 'arte', 'exposición', 'cultural', 'cultura']):
        return 'cultural'
    elif any(word in texto for word in ['literatura', 'libro', 'lectura']):
        return 'cultural'
    elif any(word in texto for word in ['tech', 'tecnología', 'innovación', 'hackathon']):
        return 'tech'
    elif any(word in texto for word in ['deporte', 'sport', 'futbol', 'basketball']):
        return 'deportes'
    elif any(word in texto for word in ['gastronomía', 'comida', 'food', 'restaurante']):
        return 'gastronomía'
    elif any(word in texto for word in ['fiesta', 'celebración', 'barco']):
        return 'otro'
    else:
        return 'otro'


def process_felo_file(filepath: Path) -> dict:
    """
    Procesa un archivo *_felo.json con respuesta_raw
    Convierte a formato JSON estructurado (como eventos de Gemini)
    """
    print(f"\n📄 {filepath.name}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error leyendo JSON: {e}")
        return {'procesado': False, 'eventos': 0}

    # Verificar si necesita procesamiento
    if not data.get('necesita_procesamiento'):
        print("  ⏭️  Ya procesado, saltando...")
        return {'procesado': False, 'eventos': 0}

    # Extraer datos
    barrio = data.get('barrio', 'Buenos Aires')
    respuesta_raw = data.get('respuesta_raw', '')

    if not respuesta_raw:
        print("  ⚠️  Sin respuesta_raw")
        return {'procesado': False, 'eventos': 0}

    # Parsear eventos
    print(f"  🔍 Parseando eventos...")
    eventos = parse_felo_events(respuesta_raw, barrio)

    if not eventos:
        print(f"  ❌ No se pudieron extraer eventos")
        return {'procesado': False, 'eventos': 0}

    print(f"  ✅ {len(eventos)} eventos extraídos")

    # Crear estructura JSON (formato Gemini)
    processed_data = {
        "eventos": eventos
    }

    # Guardar archivo procesado (REEMPLAZAR contenido, como Gemini)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        print(f"  💾 Guardado: {filepath.name}")
        return {'procesado': True, 'eventos': len(eventos)}
    except Exception as e:
        print(f"  ❌ Error guardando: {e}")
        return {'procesado': False, 'eventos': 0}


def find_felo_files(base_dir: Path, folder_filter: str = None) -> list:
    """
    Encuentra todos los *_felo.json en scrapper_results
    """
    scrapper_results = base_dir / 'scrapper_results'

    if not scrapper_results.exists():
        return []

    if folder_filter:
        search_path = scrapper_results / folder_filter
        if not search_path.exists():
            print(f"❌ No existe la carpeta: {folder_filter}")
            return []
    else:
        search_path = scrapper_results

    # Buscar todos los *_felo.json
    felo_files = list(search_path.rglob('*_felo.json'))

    return felo_files


def main():
    """Main function"""
    folder_filter = None
    if '--folder' in sys.argv:
        idx = sys.argv.index('--folder')
        if idx + 1 < len(sys.argv):
            folder_filter = sys.argv[idx + 1]

    base_dir = SCRIPT_DIR.parent

    print("=" * 80)
    print("🔍 PROCESADOR DE ARCHIVOS FELO.AI (Raw → JSON)")
    print("=" * 80)

    # Buscar archivos
    felo_files = find_felo_files(base_dir, folder_filter)
    print(f"\n📂 {len(felo_files)} archivos *_felo.json encontrados")

    if not felo_files:
        print("\n⚠️  No hay archivos para procesar")
        return

    # Mostrar archivos a procesar
    print("\n📋 Archivos:")
    for i, f in enumerate(felo_files[:10], 1):
        print(f"  {i}. {f.name}")
    if len(felo_files) > 10:
        print(f"  ... y {len(felo_files) - 10} más")

    # Procesar archivos
    total_procesados = 0
    total_eventos = 0

    for felo_file in felo_files:
        result = process_felo_file(felo_file)
        if result['procesado']:
            total_procesados += 1
            total_eventos += result['eventos']

    # Resumen final
    print("\n" + "=" * 80)
    print("✨ PROCESAMIENTO COMPLETADO")
    print("=" * 80)
    print(f"\n📊 Archivos procesados: {total_procesados}")
    print(f"🎉 Total eventos extraídos: {total_eventos}")
    print("\n📥 Próximos pasos:")
    print(f"   1. cd backend/data")
    print(f"   2. node scripts/add_images_generic.js scrapper_results/latinamerica/sudamerica/argentina/buenos-aires")
    print(f"   3. python scripts/import_generic.py scrapper_results/latinamerica/sudamerica/argentina/buenos-aires")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
