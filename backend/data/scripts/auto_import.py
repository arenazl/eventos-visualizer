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


def categorize_event(categoria: str, descripcion: str = '') -> tuple:
    """Retorna (category, subcategory)"""
    cat_lower = categoria.lower() if categoria else ''
    desc_lower = descripcion.lower() if descripcion else ''

    # Música
    if any(word in cat_lower + desc_lower for word in ['música', 'music', 'concierto', 'concert', 'festival']):
        if 'rock' in cat_lower + desc_lower:
            return 'music', 'rock'
        elif 'pop' in cat_lower + desc_lower:
            return 'music', 'pop'
        elif 'jazz' in cat_lower + desc_lower:
            return 'music', 'jazz'
        elif 'electrónica' in cat_lower + desc_lower or 'electronic' in cat_lower + desc_lower:
            return 'music', 'electronic'
        else:
            return 'music', 'other'

    # Deportes
    if any(word in cat_lower + desc_lower for word in ['deporte', 'sport', 'fútbol', 'football', 'basketball', 'polo']):
        return 'sports', 'other'

    # Cultural
    if any(word in cat_lower + desc_lower for word in ['cultural', 'cultura', 'arte', 'art', 'museo', 'museum', 'teatro', 'theater', 'turismo', 'tourism']):
        return 'cultural', 'other'

    # Gastronomía
    if any(word in cat_lower + desc_lower for word in ['gastronomía', 'gastronomy', 'food', 'alfajor', 'comida', 'restaurante']):
        return 'food', 'other'

    # Tech
    if any(word in cat_lower + desc_lower for word in ['tech', 'tecnología', 'hackathon', 'conferencia']):
        return 'tech', 'conference'

    # Default
    return 'other', 'general'


def extract_city_from_path(filepath: Path) -> str:
    """Extrae nombre de ciudad del path o filename"""
    # Primero intentar del filename
    filename = filepath.stem  # nombre sin extensión

    # Patrones conocidos: palermo_dia_gemini, barcelona_noviembre, etc.
    city_name = filename.split('_')[0]

    # Capitalizar primera letra
    return city_name.replace('-', ' ').title()


def extract_country_from_path(filepath: Path) -> str:
    """Extrae país del path del archivo"""
    parts = filepath.parts

    # Buscar en el path: scrapper_results/latinamerica/sudamerica/argentina/...
    if 'argentina' in parts:
        return 'Argentina'
    elif 'espana' in parts or 'españa' in parts:
        return 'España'
    elif 'francia' in parts:
        return 'Francia'
    elif 'puertorico' in parts:
        return 'Puerto Rico'
    elif 'usa' in parts:
        return 'USA'
    elif 'mexico' in parts or 'méxico' in parts:
        return 'México'

    # Default
    return 'Unknown'


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

    country = evento.get('pais') or evento.get('country') or extract_country_from_path(filepath)
    country = country[:100]

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


def insert_event(cursor, evento_data: Dict) -> bool:
    """Inserta evento en MySQL"""
    try:
        # Verificar si ya existe un evento con el mismo título, ciudad y fecha
        check_sql = '''
            SELECT id FROM events
            WHERE title = %s
            AND city = %s
            AND DATE(start_datetime) = DATE(%s)
            LIMIT 1
        '''
        cursor.execute(check_sql, (
            evento_data['title'],
            evento_data['city'],
            evento_data['start_datetime']
        ))

        if cursor.fetchone():
            return False  # Ya existe

        # Generar UUID para el id
        import uuid
        event_id = str(uuid.uuid4())

        # Insertar nuevo evento
        insert_sql = '''
            INSERT INTO events (
                id,
                title, description, start_datetime, end_datetime,
                venue_name, venue_address, city, neighborhood, country,
                latitude, longitude,
                category, subcategory,
                price, is_free,
                image_url, event_url, source,
                created_at, updated_at
            ) VALUES (
                %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
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

        return True

    except Exception as e:
        print(f"    ❌ Error: {str(e)[:80]}")
        return False


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
    """Procesa un archivo JSON"""
    relative_path = filepath.relative_to(filepath.parents[5])  # Relativo a proyecto
    print(f"\n📄 {relative_path}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error leyendo JSON: {e}")
        return {'insertados': 0, 'duplicados': 0, 'errores': 1}

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
        return {'insertados': 0, 'duplicados': 0, 'errores': 0}

    print(f"  📊 {len(events)} eventos encontrados")

    if dry_run:
        print(f"  🔍 [DRY-RUN] Se procesarían {len(events)} eventos")
        return {'insertados': 0, 'duplicados': 0, 'errores': 0}

    insertados = 0
    duplicados = 0
    errores = 0

    for i, evento in enumerate(events):
        evento_data = process_evento(evento, filepath, i)
        if not evento_data:
            errores += 1
            continue

        if insert_event(cursor, evento_data):
            insertados += 1
        else:
            duplicados += 1

    print(f"  ✅ {insertados} nuevos | ⏭️  {duplicados} duplicados | ❌ {errores} errores")

    return {'insertados': insertados, 'duplicados': duplicados, 'errores': errores}


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
    total_duplicados = 0
    total_errores = 0
    archivos_procesados = 0

    for json_file in new_files:
        try:
            stats = process_json_file(json_file, cursor, dry_run=False)
            total_insertados += stats['insertados']
            total_duplicados += stats['duplicados']
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
    print("\n" + "=" * 80)
    print("✨ IMPORTACIÓN COMPLETADA")
    print("=" * 80)
    print(f"\n📊 Archivos procesados: {archivos_procesados}")
    print(f"✅ Eventos insertados: {total_insertados}")
    print(f"⏭️  Eventos duplicados (ya existían): {total_duplicados}")
    print(f"❌ Errores: {total_errores}")

    if total_insertados + total_errores > 0:
        tasa_exito = (total_insertados / (total_insertados + total_errores)) * 100
        print(f"\n📈 Tasa de éxito: {tasa_exito:.1f}%")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
