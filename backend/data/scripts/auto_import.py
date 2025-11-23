#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de auto-importación: escanea scrapper_results/ y procesa archivos nuevos
Mantiene un log de archivos ya procesados para evitar duplicados

Uso:
    python auto_import.py                    # Procesa TODO scrapper_results/
    python auto_import.py --reset            # Reinicia log y reprocesa todo
    python auto_import.py --dry-run          # Muestra qué se procesaría sin importar
"""

import json
import pymysql
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List, Set
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Cargar .env desde backend/
SCRIPT_DIR = Path(__file__).parent

# Agregar path para importar desde final_guide/scripts/
FINAL_GUIDE_SCRIPTS = SCRIPT_DIR.parent / 'final_guide' / 'scripts'
sys.path.insert(0, str(FINAL_GUIDE_SCRIPTS))

# Importar utilidades compartidas
from event_utils import categorize_event as shared_categorize_event
from region_utils import get_pais_from_ciudad, get_provincia_from_ciudad
BACKEND_DIR = SCRIPT_DIR.parent.parent
ENV_FILE = BACKEND_DIR / '.env'

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Configuración de MySQL desde .env
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'events'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Archivo de log para tracking
LOG_FILE = SCRIPT_DIR / '.imported_files.log'


def get_db_connection():
    """Crea conexión a MySQL"""
    return pymysql.connect(**DB_CONFIG)


def load_imported_files() -> Set[str]:
    """Carga lista de archivos ya importados"""
    if not LOG_FILE.exists():
        return set()

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def mark_as_imported(filepath: Path):
    """Marca un archivo como importado"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{filepath}\n")


def parse_fecha(fecha_str: str) -> str:
    """Convierte fecha a formato ISO 8601"""
    if not fecha_str:
        return datetime.now().isoformat()

    # Formatos posibles
    formatos = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
    ]

    for formato in formatos:
        try:
            dt = datetime.strptime(fecha_str.split('.')[0], formato)
            return dt.isoformat()
        except ValueError:
            continue

    # Si no matchea, usar fecha actual
    return datetime.now().isoformat()


def extract_price(precio_str) -> tuple:
    """Extrae precio numérico y si es gratis"""
    if not precio_str:
        return 0.0, True

    precio_lower = str(precio_str).lower()

    # Detectar eventos gratuitos
    if any(word in precio_lower for word in ['gratis', 'free', 'libre', 'gratuito']):
        return 0.0, True

    # Intentar extraer número
    try:
        # Eliminar símbolos de moneda y espacios
        precio_clean = precio_lower.replace('$', '').replace('€', '').replace('£', '').strip()
        precio_clean = precio_clean.replace(',', '.').split()[0]
        return float(precio_clean), False
    except (ValueError, IndexError):
        return 0.0, False


def categorize_event(nombre: str, descripcion: str = '') -> tuple:
    """
    Wrapper que usa la función compartida de event_utils.py
    Mantiene compatibilidad con el código existente que pasa 'categoria' como primer arg
    """
    return shared_categorize_event(nombre, descripcion)


def extract_city_from_path(filepath: Path) -> str:
    """Extrae nombre de ciudad del path o filename"""
    # Primero intentar del filename
    filename = filepath.stem  # nombre sin extensión

    # Patrones conocidos: palermo_dia_gemini, barcelona_noviembre, etc.
    city_name = filename.split('_')[0]

    # Capitalizar primera letra
    return city_name.replace('-', ' ').title()


def extract_country_from_path(filepath: Path, ciudad: str = None) -> Optional[str]:
    """
    Extrae país usando SOLO region_utils.py para mapeo dinámico ciudad->país.

    REGLA CRÍTICA: NO hay fallbacks hardcodeados.
    Si la ciudad no está en los JSONs de regiones, retorna None.
    Los eventos sin país válido serán RECHAZADOS (no adivinados).

    Returns:
        str: Nombre del país si se encuentra en region_utils
        None: Si la ciudad no está mapeada (evento será rechazado)
    """
    # ÚNICO MÉTODO: Mapeo dinámico desde ciudad usando region_utils.py
    if ciudad:
        pais = get_pais_from_ciudad(ciudad)
        if pais != 'Unknown':
            return pais

    # NO HAY FALLBACKS - Si no está en region_utils, retornar None
    # Esto causará que el evento sea RECHAZADO, no adivinado
    return None


def process_evento(evento: Dict, filepath: Path, index: int) -> Optional[Dict]:
    """Procesa un evento individual y retorna datos normalizados"""
    # Título (detectar campo: nombre, titulo, title)
    title = (evento.get('nombre') or evento.get('titulo') or evento.get('title') or 'Evento sin título')[:255]

    # Descripción
    description = (evento.get('descripcion') or evento.get('description') or '')[:1000]

    # Fechas
    fecha_inicio = evento.get('fecha_inicio') or evento.get('fecha') or evento.get('start_date') or ''
    fecha_fin = evento.get('fecha_fin') or evento.get('end_date') or ''

    start_datetime = parse_fecha(fecha_inicio)
    end_datetime = parse_fecha(fecha_fin) if fecha_fin else start_datetime

    # Ubicación
    venue_name = (evento.get('venue') or evento.get('lugar') or evento.get('location') or 'Por definir')[:255]
    venue_address = (evento.get('direccion') or evento.get('address') or '')[:500]

    # Ciudad y país - inferir del path si no está en el evento
    city = evento.get('ciudad') or evento.get('city') or extract_city_from_path(filepath)

    # 🔧 UNIFICAR BARRIOS DE BUENOS AIRES → "Buenos Aires"
    barrios_bsas = [
        'palermo', 'recoleta', 'san telmo', 'puerto madero', 'retiro',
        'belgrano', 'villa crespo', 'almagro', 'caballito', 'nunez',
        'colegiales', 'chacarita', 'flores', 'boedo', 'barracas',
        'la boca', 'constitución', 'monserrat', 'san nicolás', 'balvanera',
        'villa urquiza', 'villa devoto', 'saavedra', 'nuñez', 'coghlan'
    ]

    # También verificar campo 'barrio' del JSON
    barrio_original = evento.get('barrio', '')
    barrio_lower = barrio_original.lower()

    # Variable para guardar el barrio
    neighborhood = None

    if city.lower() in barrios_bsas or barrio_lower in barrios_bsas:
        # Guardar el barrio antes de unificar la ciudad
        neighborhood = barrio_original if barrio_original else city
        print(f"    🔧 Unificando barrio '{city}' → Buenos Aires (barrio: {neighborhood})")
        city = 'Buenos Aires'

    city = city[:100]

    # Guardar neighborhood si existe
    if neighborhood:
        neighborhood = neighborhood[:100]

    # País: primero del evento, luego mapeo dinámico ciudad->país
    # REGLA CRÍTICA: Si no hay país válido, el evento se RECHAZA (no se adivina)
    country = evento.get('pais') or evento.get('country') or extract_country_from_path(filepath, city)

    if not country:
        print(f"    ⛔ RECHAZADO: Ciudad '{city}' no está en region_utils - ubicación incompleta")
        return None

    country = country[:100]

    # Provincia: usar mapeo dinámico
    provincia = evento.get('provincia') or get_provincia_from_ciudad(city)

    # Coordenadas
    latitude = evento.get('latitud') or evento.get('latitude')
    longitude = evento.get('longitud') or evento.get('longitude')

    # Categoría
    categoria = evento.get('categoria') or evento.get('category') or ''
    category, subcategory = categorize_event(categoria, description)

    # Precio
    precio_str = evento.get('precio') or evento.get('price') or ''
    price, is_free = extract_price(precio_str)

    # Moneda
    currency = evento.get('moneda') or evento.get('currency') or 'ARS'
    if 'eur' in currency.lower():
        currency = 'EUR'
    elif 'usd' in currency.lower() or 'dol' in currency.lower():
        currency = 'USD'
    elif 'gbp' in currency.lower() or 'pound' in currency.lower():
        currency = 'GBP'

    # Imagen - usar la de Google Images si existe
    image_url = evento.get('image_url')

    # URL del evento
    event_url = evento.get('url') or evento.get('event_url') or evento.get('link')

    return {
        'title': title,
        'description': description,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'venue_name': venue_name,
        'venue_address': venue_address,
        'city': city,
        'neighborhood': neighborhood,
        'country': country,
        'province': provincia,
        'latitude': latitude,
        'longitude': longitude,
        'category': category,
        'subcategory': subcategory,
        'price': price,
        'currency': currency,
        'is_free': is_free,
        'image_url': image_url,
        'event_url': event_url,
        'source_api': 'scraper_auto'
    }


def insert_event(cursor, evento_data: Dict) -> tuple:
    """
    Inserta evento en MySQL con detección inteligente de duplicados

    Returns:
        tuple: (inserted: bool, reason: str)
        - (True, 'inserted') si se insertó
        - (False, 'duplicate_exact') si título exacto existe
        - (False, 'duplicate_partial') si título similar existe
    """
    try:
        title = evento_data['title']
        city = evento_data['city']
        fecha = evento_data['start_datetime']

        # PASO 1: Verificar duplicado EXACTO (título completo igual)
        check_exact_sql = '''
            SELECT id, title FROM events
            WHERE title = %s
            AND city = %s
            AND DATE(start_datetime) = DATE(%s)
            LIMIT 1
        '''
        cursor.execute(check_exact_sql, (title, city, fecha))

        if cursor.fetchone():
            return (False, 'duplicate_exact')

        # PASO 2: Verificar duplicado PARCIAL (títulos similares)
        # Buscar eventos con mismo city y fecha, comparar títulos
        check_partial_sql = '''
            SELECT id, title FROM events
            WHERE city = %s
            AND DATE(start_datetime) = DATE(%s)
        '''
        cursor.execute(check_partial_sql, (city, fecha))

        existing_events = cursor.fetchall()

        for existing in existing_events:
            existing_title = existing['title'].lower()
            new_title = title.lower()

            # Comparación de similitud (al menos 80% de palabras en común)
            existing_words = set(existing_title.split())
            new_words = set(new_title.split())

            if len(new_words) == 0:
                continue

            common_words = existing_words & new_words
            similarity = len(common_words) / len(new_words)

            if similarity >= 0.8:
                return (False, f'duplicate_partial:{existing["title"]}')

        # PASO 3: No hay duplicados, insertar evento

        # Generar UUID para el id
        import uuid
        event_id = str(uuid.uuid4())

        # Insertar nuevo evento
        insert_sql = '''
            INSERT INTO events (
                id,
                title, description, start_datetime, end_datetime,
                venue_name, venue_address, city, neighborhood, country, province,
                latitude, longitude,
                category, subcategory,
                price, is_free,
                image_url, event_url, source,
                created_at, updated_at
            ) VALUES (
                %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                NOW(), NOW()
            )
        '''

        cursor.execute(insert_sql, (
            event_id,
            evento_data['title'],
            evento_data['description'],
            evento_data['start_datetime'],
            evento_data['end_datetime'],
            evento_data['venue_name'],
            evento_data['venue_address'],
            evento_data['city'],
            evento_data['neighborhood'],
            evento_data['country'],
            evento_data['province'],
            evento_data['latitude'],
            evento_data['longitude'],
            evento_data['category'],
            evento_data['subcategory'],
            str(evento_data['price']),
            evento_data['is_free'],
            evento_data['image_url'],
            evento_data['event_url'],
            'gemini_scraper'
        ))

        return (True, 'inserted')

    except Exception as e:
        error_msg = str(e)[:80]
        return (False, f'error:{error_msg}')


def find_all_json_files(base_dir: Path) -> List[Path]:
    """Encuentra todos los JSONs recursivamente en scrapper_results"""
    scrapper_results = base_dir / 'scrapper_results'

    if not scrapper_results.exists():
        return []

    # Buscar todos los .json recursivamente
    all_jsons = list(scrapper_results.rglob('*.json'))

    # Filtrar archivos que probablemente sean eventos (no configs, etc.)
    event_jsons = [
        f for f in all_jsons
        if f.stat().st_size > 100  # Al menos 100 bytes
        and 'config' not in f.name.lower()
        and 'schema' not in f.name.lower()
    ]

    return event_jsons


def process_json_file(filepath: Path, cursor, dry_run: bool = False) -> dict:
    """Procesa un archivo JSON con logging detallado"""
    relative_path = filepath.relative_to(filepath.parents[5])  # Relativo a proyecto
    print(f"\n📄 {relative_path}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error leyendo JSON: {e}")
        return {
            'insertados': 0,
            'duplicate_exact': 0,
            'duplicate_partial': 0,
            'errores': 1,
            'detalles': []
        }

    # Detectar estructura del JSON
    events = []

    if isinstance(data, dict):
        if 'eventos' in data and isinstance(data['eventos'], list):
            # Estructura: {ciudad, pais, eventos: [...]}
            events = data['eventos']
        elif 'eventos_ferias_festivales' in data or 'recitales_shows_fiestas' in data:
            # Estructura Puerto Rico
            events = (data.get('eventos_ferias_festivales', []) +
                     data.get('recitales_shows_fiestas', []))
    elif isinstance(data, list):
        # Estructura: [...eventos...]
        events = data

    if not events:
        print("  ⚠️  No se encontraron eventos")
        return {
            'insertados': 0,
            'duplicate_exact': 0,
            'duplicate_partial': 0,
            'errores': 0,
            'detalles': []
        }

    print(f"  📊 {len(events)} eventos encontrados")

    if dry_run:
        print(f"  🔍 [DRY-RUN] Se procesarían {len(events)} eventos")
        return {
            'insertados': 0,
            'duplicate_exact': 0,
            'duplicate_partial': 0,
            'errores': 0,
            'detalles': []
        }

    # Contadores detallados
    insertados = 0
    duplicate_exact = 0
    duplicate_partial = 0
    errores = 0
    detalles = []  # Lista de (titulo, reason) para log detallado

    for i, evento in enumerate(events, 1):
        evento_data = process_evento(evento, filepath, i)
        if not evento_data:
            errores += 1
            titulo_truncado = str(evento.get('nombre') or evento.get('title', 'Unknown'))[:50]
            detalles.append((titulo_truncado, 'error:parsing_failed'))
            continue

        # Insertar y capturar resultado
        success, reason = insert_event(cursor, evento_data)

        titulo_truncado = evento_data['title'][:50]

        if success:
            insertados += 1
            detalles.append((titulo_truncado, 'inserted'))
        elif reason == 'duplicate_exact':
            duplicate_exact += 1
            detalles.append((titulo_truncado, 'duplicate_exact'))
        elif reason.startswith('duplicate_partial'):
            duplicate_partial += 1
            # Extraer título existente del reason
            existing_title = reason.split(':', 1)[1] if ':' in reason else 'similar'
            detalles.append((titulo_truncado, f'duplicate_partial:{existing_title[:30]}'))
        elif reason.startswith('error'):
            errores += 1
            error_msg = reason.split(':', 1)[1] if ':' in reason else reason
            detalles.append((titulo_truncado, f'error:{error_msg[:50]}'))
        else:
            errores += 1
            detalles.append((titulo_truncado, f'unknown:{reason}'))

    # Mostrar resumen del batch
    total_duplicados = duplicate_exact + duplicate_partial
    print(f"  ✅ {insertados} nuevos | ⏭️  {total_duplicados} duplicados ({duplicate_exact} exactos, {duplicate_partial} parciales) | ❌ {errores} errores")

    # Mostrar detalles si hay duplicados parciales o errores
    if duplicate_partial > 0 or errores > 0:
        print(f"\n  📋 DETALLES DEL BATCH:")
        for titulo, reason in detalles:
            if reason.startswith('duplicate_partial'):
                existing = reason.split(':', 1)[1] if ':' in reason else 'similar'
                print(f"    ⏭️  PARCIAL: '{titulo}' ~ '{existing}'")
            elif reason.startswith('error'):
                error_msg = reason.split(':', 1)[1] if ':' in reason else reason
                print(f"    ❌ ERROR: '{titulo}' → {error_msg}")

    return {
        'insertados': insertados,
        'duplicate_exact': duplicate_exact,
        'duplicate_partial': duplicate_partial,
        'errores': errores,
        'detalles': detalles
    }


def main():
    """Main function"""
    # Parsear argumentos
    reset_log = '--reset' in sys.argv
    dry_run = '--dry-run' in sys.argv

    base_dir = SCRIPT_DIR.parent

    print("=" * 80)
    print("🤖 AUTO-IMPORTADOR DE EVENTOS")
    print("=" * 80)

    if dry_run:
        print("\n🔍 MODO DRY-RUN: Mostrará qué se procesaría sin importar a la BD")

    if reset_log:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            print("\n🔄 Log de archivos importados reiniciado")

    # Cargar archivos ya procesados
    imported_files = load_imported_files()
    print(f"\n📋 Archivos previamente importados: {len(imported_files)}")

    # Buscar todos los JSONs
    all_json_files = find_all_json_files(base_dir)
    print(f"📂 Total JSONs encontrados: {len(all_json_files)}")

    # Filtrar solo los nuevos
    new_files = [f for f in all_json_files if str(f) not in imported_files]
    print(f"🆕 Archivos nuevos para procesar: {len(new_files)}")

    if not new_files:
        print("\n✅ No hay archivos nuevos para procesar")
        print("💡 Usa --reset para reprocesar todos los archivos")
        return

    # Mostrar preview de archivos a procesar
    print("\n📋 Archivos que se procesarán:")
    for i, f in enumerate(new_files[:10], 1):
        rel_path = f.relative_to(base_dir / 'scrapper_results')
        print(f"  {i}. {rel_path}")

    if len(new_files) > 10:
        print(f"  ... y {len(new_files) - 10} más")

    if dry_run:
        print("\n🔍 [DRY-RUN] No se importará nada, solo se muestra qué se procesaría")
        return

    # Conectar a MySQL
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("\n✅ Conectado a MySQL")
    except Exception as e:
        print(f"\n❌ Error conectando a MySQL: {e}")
        sys.exit(1)

    # Procesar archivos nuevos
    total_insertados = 0
    total_duplicate_exact = 0
    total_duplicate_partial = 0
    total_errores = 0
    archivos_procesados = 0

    for json_file in new_files:
        try:
            stats = process_json_file(json_file, cursor, dry_run=False)
            total_insertados += stats['insertados']
            total_duplicate_exact += stats['duplicate_exact']
            total_duplicate_partial += stats['duplicate_partial']
            total_errores += stats['errores']

            # Commit después de cada archivo
            connection.commit()

            # Marcar como importado
            mark_as_imported(json_file)
            archivos_procesados += 1

        except Exception as e:
            print(f"  ❌ Error procesando: {e}")
            connection.rollback()

    # Cerrar conexión
    cursor.close()
    connection.close()

    # Resumen final
    total_duplicados = total_duplicate_exact + total_duplicate_partial
    print("\n" + "=" * 80)
    print("✨ IMPORTACIÓN COMPLETADA")
    print("=" * 80)
    print(f"\n📊 Archivos procesados: {archivos_procesados}")
    print(f"✅ Eventos insertados: {total_insertados}")
    print(f"⏭️  Eventos duplicados (ya existían): {total_duplicados}")
    print(f"   • Duplicados exactos (título completo igual): {total_duplicate_exact}")
    print(f"   • Duplicados parciales (títulos similares ~80%): {total_duplicate_partial}")
    print(f"❌ Errores: {total_errores}")

    if total_insertados + total_errores > 0:
        tasa_exito = (total_insertados / (total_insertados + total_errores)) * 100
        print(f"\n📈 Tasa de éxito: {tasa_exito:.1f}%")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
