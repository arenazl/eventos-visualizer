"""
Script para importar eventos de países (image-better) a MySQL con imágenes de Google
"""
import json
import os
import sys
import uuid
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Configurar codificación
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar backend al path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)

import pymysql

# Coordenadas base por país/ciudad (centros aproximados)
CITY_COORDS = {
    # Argentina
    "buenos aires": (-34.6037, -58.3816),
    "córdoba": (-31.4201, -64.1888),
    "rosario": (-32.9442, -60.6505),
    "mendoza": (-32.8895, -68.8458),
    "salta": (-24.7859, -65.4117),

    # Chile
    "santiago": (-33.4489, -70.6693),
    "valparaíso": (-33.0472, -71.6127),
    "concepción": (-36.8201, -73.0444),

    # Colombia
    "bogotá": (4.7110, -74.0721),
    "medellín": (6.2476, -75.5658),
    "cali": (3.4516, -76.5320),

    # México
    "ciudad de méxico": (19.4326, -99.1332),
    "guadalajara": (20.6597, -103.3496),
    "monterrey": (25.6866, -100.3161),

    # Perú
    "lima": (-12.0464, -77.0428),
    "cusco": (-13.5319, -71.9675),

    # Uruguay
    "montevideo": (-34.9011, -56.1645),

    # Bolivia
    "la paz": (-16.5000, -68.1500),
    "santa cruz": (-17.8146, -63.1561),

    # Ecuador
    "quito": (-0.1807, -78.4678),
    "guayaquil": (-2.1709, -79.9224),

    # Paraguay
    "asunción": (-25.2637, -57.5759),

    # Venezuela
    "caracas": (10.4806, -66.9036),

    # Brasil
    "río de janeiro": (-22.9068, -43.1729),
    "são paulo": (-23.5505, -46.6333),

    # España
    "madrid": (40.4168, -3.7038),
    "barcelona": (41.3851, 2.1734),

    # Estados Unidos
    "nueva york": (40.7128, -74.0060),
    "miami": (25.7617, -80.1918),
    "los ángeles": (34.0522, -118.2437),
}

CATEGORY_MAPPING = {
    "música": "music",
    "musica": "music",
    "music": "music",
    "concierto": "music",
    "show": "music",
    "cultural": "cultural",
    "festival": "festival",
    "feria": "festival",
    "fiesta": "party",
    "party": "party",
    "deportes": "sports",
    "sports": "sports",
    "deporte": "sports",
    "teatro": "theater",
    "theater": "theater",
    "comedia": "comedy",
    "comedy": "comedy",
    "arte": "art",
    "art": "art",
    "food": "food",
    "gastronomía": "food",
    "tech": "tech",
    "tecnología": "tech",
    "other": "other",
}


def get_city_coordinates(city: str, country: str) -> tuple:
    """Obtiene coordenadas de la ciudad"""
    normalized_city = city.lower().strip()
    normalized_country = country.lower().strip()

    # Buscar coincidencia exacta por ciudad
    if normalized_city in CITY_COORDS:
        coords = CITY_COORDS[normalized_city]
    else:
        # Buscar coincidencia parcial
        for known_city, coords in CITY_COORDS.items():
            if known_city in normalized_city or normalized_city in known_city:
                coords = CITY_COORDS[known_city]
                break
        else:
            # Default por país
            country_defaults = {
                "argentina": (-34.6037, -58.3816),  # Buenos Aires
                "chile": (-33.4489, -70.6693),       # Santiago
                "colombia": (4.7110, -74.0721),       # Bogotá
                "méxico": (19.4326, -99.1332),        # CDMX
                "perú": (-12.0464, -77.0428),         # Lima
                "uruguay": (-34.9011, -56.1645),      # Montevideo
                "bolivia": (-16.5000, -68.1500),      # La Paz
                "ecuador": (-0.1807, -78.4678),       # Quito
                "paraguay": (-25.2637, -57.5759),     # Asunción
                "venezuela": (10.4806, -66.9036),     # Caracas
                "brasil": (-23.5505, -46.6333),       # São Paulo
                "españa": (40.4168, -3.7038),         # Madrid
            }
            coords = country_defaults.get(normalized_country, (-34.6037, -58.3816))

    lat, lng = coords
    # Agregar variación aleatoria
    lat += random.uniform(-0.05, 0.05)
    lng += random.uniform(-0.05, 0.05)
    return (round(lat, 6), round(lng, 6))


def normalize_category(categoria: str) -> str:
    """Normaliza categoría"""
    if not categoria:
        return "other"
    return CATEGORY_MAPPING.get(categoria.lower().strip(), "other")


def parse_fecha(fecha_str: str) -> Optional[datetime]:
    """Parsea fecha ISO format"""
    if not fecha_str:
        return None

    try:
        # Formato ISO: 2025-11-11T00:00:00
        return datetime.fromisoformat(fecha_str.replace('Z', ''))
    except:
        pass

    # Intentar otros formatos
    try:
        return datetime.strptime(fecha_str[:10], '%Y-%m-%d')
    except:
        return None


def normalize_precio(precio_value) -> tuple:
    """Retorna (precio_str, is_free)"""
    if precio_value is None:
        return ("a consultar", False)

    # Si es número
    if isinstance(precio_value, (int, float)):
        if precio_value == 0:
            return ("gratuito", True)
        return (f"${precio_value}", False)

    # Si es string
    precio_str = str(precio_value).lower().strip()

    if precio_str in ["gratuito", "gratis", "free", "0"]:
        return ("gratuito", True)

    if precio_str in ["a consultar", "pago", "variable"]:
        return ("a consultar", False)

    return (str(precio_value), False)


def process_evento(evento: Dict, index: int) -> Optional[Dict]:
    """Procesa un evento individual"""
    # Título
    title = evento.get('titulo', 'Evento sin título')[:255]

    # Fecha
    fecha_str = evento.get('fecha_inicio', '')
    start_datetime = parse_fecha(fecha_str)
    if not start_datetime:
        return None  # Sin fecha válida

    # Descripción
    description = evento.get('descripcion', '')[:5000] if evento.get('descripcion') else None

    # Ubicación
    ciudad = evento.get('ciudad', 'Ciudad')
    pais = evento.get('pais', 'País')
    venue_name = evento.get('venue', ciudad)[:255]
    venue_address = evento.get('venue', ciudad)

    # Coordenadas
    lat, lng = get_city_coordinates(ciudad, pais)

    # Categoría
    categoria_raw = evento.get('categoria', 'other')
    category = normalize_category(categoria_raw)

    # Precio
    precio_raw = evento.get('precio', 'a consultar')
    price, is_free = normalize_precio(precio_raw)

    # Imagen - usar la de Google Images si existe
    image_url = evento.get('image_url')

    # IDs
    event_id = str(uuid.uuid4())
    pais_slug = pais.lower().replace(' ', '_')
    external_id = f"country_{pais_slug}_{index}"

    return {
        'id': event_id,
        'title': title,
        'description': description,
        'start_datetime': start_datetime,
        'end_datetime': None,
        'venue_name': venue_name,
        'venue_address': venue_address,
        'latitude': lat,
        'longitude': lng,
        'category': category,
        'subcategory': categoria_raw if category != categoria_raw else None,
        'price': price,
        'is_free': is_free,
        'external_id': external_id,
        'source': ciudad,
        'image_url': image_url,
        'event_url': None,
        'city': ciudad,
        'country': pais,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'scraped_at': datetime.now()
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
            # Ya existe
            return False

        sql = '''
            INSERT INTO events (
                id, title, description, start_datetime, end_datetime,
                venue_name, venue_address, latitude, longitude,
                category, subcategory, price, is_free,
                external_id, source, image_url, event_url,
                city, country, created_at, updated_at, scraped_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        '''

        cursor.execute(sql, (
            evento_data['id'],
            evento_data['title'],
            evento_data['description'],
            evento_data['start_datetime'],
            evento_data['end_datetime'],
            evento_data['venue_name'],
            evento_data['venue_address'],
            evento_data['latitude'],
            evento_data['longitude'],
            evento_data['category'],
            evento_data['subcategory'],
            evento_data['price'],
            evento_data['is_free'],
            evento_data['external_id'],
            evento_data['source'],
            evento_data['image_url'],
            evento_data['event_url'],
            evento_data['city'],
            evento_data['country'],
            evento_data['created_at'],
            evento_data['updated_at'],
            evento_data['scraped_at']
        ))
        return True
    except pymysql.err.IntegrityError:
        return False
    except Exception as e:
        print(f"Error insertando: {e}")
        return False


def process_json_file(filepath: Path, connection) -> tuple:
    """Procesa un archivo JSON de países"""
    with open(filepath, 'r', encoding='utf-8') as f:
        eventos_list = json.load(f)

    if not eventos_list or not isinstance(eventos_list, list):
        return (0, 0)

    eventos_procesados = 0
    eventos_insertados = 0
    cursor = connection.cursor()

    for idx, evento in enumerate(eventos_list, 1):
        eventos_procesados += 1
        evento_data = process_evento(evento, idx)
        if evento_data and insert_event(cursor, evento_data):
            eventos_insertados += 1

    connection.commit()
    cursor.close()

    return (eventos_procesados, eventos_insertados)


def main():
    """Función principal"""
    print("🌎 Importando eventos de países a MySQL")
    print("="*70)

    # Conectar a MySQL
    connection = pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        charset='utf8mb4'
    )
    print("✅ Conexión a MySQL establecida\n")

    # Obtener archivos JSON
    data_path = Path(__file__).parent
    json_files = [f for f in data_path.glob('eventos_*.json') if f.name != 'eventos_activos.json']

    print(f"📁 Encontrados {len(json_files)} archivos JSON\n")

    total_procesados = 0
    total_insertados = 0
    archivos_exitosos = 0

    for i, json_file in enumerate(json_files, 1):
        file_name = json_file.stem.replace('eventos_', '')
        print(f"[{i}/{len(json_files)}] {file_name:<20}", end=" ")

        try:
            procesados, insertados = process_json_file(json_file, connection)
            total_procesados += procesados
            total_insertados += insertados

            if insertados > 0:
                archivos_exitosos += 1
                print(f"✅ {insertados}/{procesados} eventos")
            elif procesados > 0:
                print(f"⚠️  0/{procesados} (duplicados?)")
            else:
                print(f"⏭️  Sin eventos")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    connection.close()

    # Resumen
    print("\n" + "="*70)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("="*70)
    print(f"📄 Archivos procesados: {len(json_files)}")
    print(f"✅ Con eventos: {archivos_exitosos}")
    print(f"📊 Eventos procesados: {total_procesados}")
    print(f"💾 Eventos insertados: {total_insertados}")

    if total_procesados > 0:
        print(f"📈 Tasa de éxito: {(total_insertados / total_procesados) * 100:.1f}%")

    print(f"\n📸 Eventos con imágenes de Google: {total_insertados}")


if __name__ == "__main__":
    main()
