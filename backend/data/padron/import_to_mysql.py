"""
Script para importar eventos de los JSON de barrios a la base de datos MySQL
Incluye curación de datos, normalización de fechas, geocoding y asignación de imágenes
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple
import hashlib
import random
import uuid

# Configurar codificación para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar el directorio backend al path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Import pymysql for MySQL
try:
    import pymysql
    print("OK pymysql disponible")
except ImportError:
    print("ERROR pymysql no instalado. Ejecuta: pip install pymysql")
    sys.exit(1)

# Coordenadas aproximadas de barrios de Buenos Aires
BARRIO_COORDS = {
    "agronomia": (-34.5996, -58.4866),
    "almagro": (-34.6092, -58.4195),
    "balvanera": (-34.6098, -58.3968),
    "barracas": (-34.6432, -58.3736),
    "belgrano": (-34.5628, -58.4573),
    "boedo": (-34.6332, -58.4173),
    "caballito": (-34.6176, -58.4368),
    "chacarita": (-34.5891, -58.4510),
    "coghlan": (-34.5588, -58.4778),
    "colegiales": (-34.5749, -58.4467),
    "constitucion": (-34.6274, -58.3817),
    "flores": (-34.6281, -58.4657),
    "floresta": (-34.6286, -58.4838),
    "la-boca": (-34.6345, -58.3632),
    "laboca": (-34.6345, -58.3632),
    "la-paternal": (-34.5995, -58.4716),
    "lapaternal": (-34.5995, -58.4716),
    "liniers": (-34.6432, -58.5218),
    "mataderos": (-34.6592, -58.5018),
    "monte-castro": (-34.6181, -58.5036),
    "montecastro": (-34.6181, -58.5036),
    "montserrat": (-34.6102, -58.3745),
    "nueva-pompeya": (-34.6596, -58.4194),
    "nuevapompeya": (-34.6596, -58.4194),
    "nunez": (-34.5442, -58.4632),
    "palermo": (-34.5888, -58.4199),
    "parque-avellaneda": (-34.6462, -58.4815),
    "parqueavellaneda": (-34.6462, -58.4815),
    "parque-chacabuco": (-34.6389, -58.4415),
    "parquechacabuco": (-34.6389, -58.4415),
    "parque-chas": (-34.5767, -58.4817),
    "parque-patricios": (-34.6382, -58.3996),
    "puerto-madero": (-34.6118, -58.3636),
    "recoleta": (-34.5889, -58.3937),
    "retiro": (-34.5925, -58.3747),
    "saavedra": (-34.5487, -58.4848),
    "san-cristobal": (-34.6228, -58.3992),
    "san-nicolas": (-34.6032, -58.3748),
    "san-telmo": (-34.6214, -58.3724),
    "velez-sarsfield": (-34.6338, -58.4997),
    "versalles": (-34.6257, -58.5247),
    "villa-crespo": (-34.5999, -58.4386),
    "villa-del-parque": (-34.6047, -58.4912),
    "villa-devoto": (-34.6014, -58.5153),
    "villa-general-mitre": (-34.5921, -58.4744),
    "villa-lugano": (-34.6880, -58.4702),
    "villa-luro": (-34.6388, -58.5018),
    "villa-ortuzar": (-34.5784, -58.4663),
    "villa-pueyrredon": (-34.5869, -58.5019),
    "villa-real": (-34.6181, -58.5128),
    "villa-riachuelo": (-34.6964, -58.4547),
    "villa-santa-rita": (-34.6147, -58.4814),
    "villa-soldati": (-34.6647, -58.4489),
    "villa-urquiza": (-34.5722, -58.4843),
}

# Mapeo de categorías detectadas a categorías estándar
CATEGORY_MAPPING = {
    "gastronomia": "food",
    "gastronomia-cultural": "food",
    "tecnologia": "tech",
    "tech": "tech",
    "cine": "film",
    "teatro": "theater",
    "teatro-show": "theater",
    "rock": "music",
    "musica": "music",
    "electronica": "music",
    "cultural": "cultural",
    "cultural-religioso": "cultural",
    "deportes": "sports",
    "deportes-cultura": "sports",
    "festival": "festival",
    "arte": "art",
    "fiesta": "party",
    "feria": "festival",
    "artesanias": "art",
}


def normalize_barrio_name(nombre: str) -> str:
    """Normaliza nombre de barrio para buscar coordenadas"""
    return nombre.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def get_barrio_coordinates(barrio: str) -> Tuple[float, float]:
    """Obtiene coordenadas del barrio o default de Buenos Aires"""
    normalized = normalize_barrio_name(barrio)
    coords = BARRIO_COORDS.get(normalized)

    if coords:
        # Agregar variación aleatoria pequeña para eventos del mismo barrio
        lat, lng = coords
        lat += random.uniform(-0.005, 0.005)
        lng += random.uniform(-0.005, 0.005)
        return (round(lat, 6), round(lng, 6))

    # Default: Centro de Buenos Aires (Obelisco)
    return (-34.6037, -58.3816)


def normalize_category(categoria: str) -> str:
    """Normaliza categoría a formato estándar"""
    if not categoria:
        return "other"

    categoria_lower = categoria.lower().strip()
    return CATEGORY_MAPPING.get(categoria_lower, "other")


def parse_fecha_text(fecha_text: str, year: int = 2025, month: int = 11) -> Optional[datetime]:
    """
    Parsea textos de fecha a datetime

    Ejemplos:
    - "2025-11-09" -> datetime
    - "Viernes 14 de Noviembre" -> datetime(2025, 11, 14)
    - "Hasta el Sábado 15 de Noviembre" -> datetime(2025, 11, 15)
    - "Jueves 20 al Domingo 30 de Noviembre" -> datetime(2025, 11, 20) # fecha inicio
    """
    if not fecha_text:
        return None

    fecha_text = str(fecha_text).strip()

    # Caso 1: Ya está en formato YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_text):
        try:
            return datetime.strptime(fecha_text, '%Y-%m-%d')
        except:
            return None

    # Caso 2: Extraer números de día
    match = re.search(r'\b(\d{1,2})\b', fecha_text)
    if match:
        day = int(match.group(1))
        if 1 <= day <= 31:
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

    # Caso 3: No se pudo parsear
    return None


def normalize_precio(precio_text: str) -> Tuple[str, bool]:
    """
    Normaliza precio a (valor_texto, is_free)

    La tabla MySQL tiene price como VARCHAR, no como FLOAT

    Returns:
        (precio_texto, is_free)
    """
    if not precio_text:
        return ("gratuito", True)

    precio_lower = str(precio_text).lower().strip()

    # Casos gratuitos
    if precio_lower in ["gratuito", "gratis", "free", "libre"]:
        return ("gratuito", True)

    # Caso pago sin valor específico
    if precio_lower in ["pago", "variable", "consultar"]:
        return ("a consultar", False)

    # Intentar extraer número
    match = re.search(r'\$?\s*(\d+(?:\.\d+)?)', precio_text)
    if match:
        try:
            valor = float(match.group(1))
            if valor == 0:
                return ("gratuito", True)
            else:
                return (f"${int(valor)}", False)
        except:
            pass

    # Default
    return ("a consultar", False)


def generate_picsum_image(event_id: str, width: int = 800, height: int = 600) -> str:
    """
    Genera URL de imagen de Picsum basada en el event_id

    Usa el hash del event_id para tener imágenes consistentes pero variadas
    """
    # Generar número de imagen basado en hash del ID
    hash_num = int(hashlib.md5(event_id.encode()).hexdigest(), 16)
    img_id = (hash_num % 1000) + 1  # IDs de 1 a 1000

    return f"https://picsum.photos/id/{img_id}/{width}/{height}"


def clean_venue_name(venue: str) -> str:
    """Limpia y normaliza nombre del venue"""
    if not venue:
        return "Lugar a confirmar"

    # Eliminar caracteres extraños
    venue = venue.strip()

    # Si es muy largo, tomar solo la primera parte antes del paréntesis
    if "(" in venue:
        parts = venue.split("(")
        return parts[0].strip()

    return venue[:255]  # Límite de la base de datos


def insert_event(cursor, evento_data: Dict) -> bool:
    """
    Inserta un evento en la base de datos MySQL

    Returns:
        True si se insertó exitosamente, False si falló
    """
    try:
        # Generar UUID para el ID
        event_id = str(uuid.uuid4())

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
            event_id,
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
            datetime.now(),
            datetime.now(),
            datetime.now()
        ))
        return True
    except pymysql.err.IntegrityError as e:
        # Duplicado (external_id ya existe)
        if e.args[0] == 1062:  # Duplicate entry
            return False
        else:
            print(f"  ERROR IntegrityError: {e}")
            return False
    except Exception as e:
        print(f"  ERROR insertando evento '{evento_data['title'][:50]}': {e}")
        return False


def process_json_file(filepath: Path, connection) -> Tuple[int, int]:
    """
    Procesa un archivo JSON de barrio e inserta eventos en la DB

    Returns:
        (eventos_procesados, eventos_insertados)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    barrio = data.get('barrio', 'Unknown')
    mes = data.get('mes', 'noviembre')
    año = data.get('año', 2025)

    # Obtener coordenadas base del barrio
    lat_base, lng_base = get_barrio_coordinates(barrio)

    eventos_procesados = 0
    eventos_insertados = 0

    cursor = connection.cursor()

    # Procesar eventos_ferias_festivales
    for evento in data.get('eventos_ferias_festivales', []):
        eventos_procesados += 1

        # Curación de datos
        titulo = evento.get('nombre', 'Evento sin título')[:255]
        descripcion = evento.get('descripcion', '')

        # Normalizar fecha
        fecha_text = evento.get('fecha', '')
        start_datetime = parse_fecha_text(fecha_text, año, 11 if mes == 'noviembre' else 12)

        if not start_datetime:
            # Si no hay fecha válida, skip
            continue

        # Agregar hora si existe
        hora_inicio = evento.get('hora_inicio', '00:00')
        if hora_inicio and hora_inicio != 'Consultar hora' and ':' in str(hora_inicio):
            try:
                hora, minuto = str(hora_inicio).split(':')[:2]
                start_datetime = start_datetime.replace(hour=int(hora), minute=int(minuto))
            except:
                pass

        # End datetime (si existe hora_fin)
        end_datetime = None
        hora_fin = evento.get('hora_fin')
        if hora_fin and ':' in str(hora_fin):
            try:
                hora, minuto = str(hora_fin).split(':')[:2]
                end_datetime = start_datetime.replace(hour=int(hora), minute=int(minuto))
            except:
                pass

        # Venue
        venue_name = clean_venue_name(evento.get('lugar', f'{barrio}'))
        venue_address = evento.get('lugar', '')

        # Coordenadas (con variación del barrio)
        latitude = lat_base + random.uniform(-0.003, 0.003)
        longitude = lng_base + random.uniform(-0.003, 0.003)

        # Categoría
        categoria_raw = evento.get('categoria', 'other')
        category = normalize_category(categoria_raw)
        subcategory = categoria_raw if category != categoria_raw else None

        # Precio (VARCHAR en MySQL)
        precio_raw = evento.get('precio', 'gratuito')
        price, is_free = normalize_precio(precio_raw)

        # External ID único
        external_id = f"padron_{normalize_barrio_name(barrio)}_{mes}_{eventos_procesados}"

        # Imagen de Picsum
        image_url = generate_picsum_image(external_id)

        # Preparar datos
        evento_data = {
            'title': titulo,
            'description': descripcion[:5000] if descripcion else None,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'venue_name': venue_name,
            'venue_address': venue_address,
            'latitude': round(latitude, 8),
            'longitude': round(longitude, 8),
            'category': category,
            'subcategory': subcategory,
            'price': price,
            'is_free': is_free,
            'external_id': external_id,
            'source': 'gemini_padron',
            'image_url': image_url,
            'event_url': None,
            'city': 'Buenos Aires',
            'country': 'Argentina'
        }

        # Insertar en DB
        if insert_event(cursor, evento_data):
            eventos_insertados += 1

    # Procesar recitales_shows_fiestas
    for recital in data.get('recitales_shows_fiestas', []):
        eventos_procesados += 1

        # Curación de datos (similar al anterior)
        titulo = recital.get('nombre', 'Show sin título')[:255]
        descripcion = recital.get('descripcion', '')

        # Normalizar fecha
        fecha_text = recital.get('fecha', '')
        start_datetime = parse_fecha_text(fecha_text, año, 11 if mes == 'noviembre' else 12)

        if not start_datetime:
            continue

        # Agregar hora
        hora_inicio = recital.get('hora_inicio', '20:00')  # Default 8 PM para recitales
        if hora_inicio and hora_inicio != 'Consultar hora' and ':' in str(hora_inicio):
            try:
                hora, minuto = str(hora_inicio).split(':')[:2]
                start_datetime = start_datetime.replace(hour=int(hora), minute=int(minuto))
            except:
                start_datetime = start_datetime.replace(hour=20, minute=0)

        end_datetime = None
        hora_fin = recital.get('hora_fin')
        if hora_fin and ':' in str(hora_fin):
            try:
                hora, minuto = str(hora_fin).split(':')[:2]
                end_datetime = start_datetime.replace(hour=int(hora), minute=int(minuto))
            except:
                pass

        # Venue
        venue_name = clean_venue_name(recital.get('lugar', f'{barrio}'))
        venue_address = recital.get('lugar', '')

        # Coordenadas
        latitude = lat_base + random.uniform(-0.003, 0.003)
        longitude = lng_base + random.uniform(-0.003, 0.003)

        # Categoría (mayoría son música)
        categoria_raw = recital.get('categoria', 'music')
        category = normalize_category(categoria_raw)
        subcategory = categoria_raw if category != categoria_raw else None

        # Precio (mayoría son pagos)
        precio_raw = recital.get('precio', 'a consultar')
        price, is_free = normalize_precio(precio_raw)

        # External ID
        external_id = f"padron_{normalize_barrio_name(barrio)}_{mes}_recital_{eventos_procesados}"

        # Imagen de Picsum
        image_url = generate_picsum_image(external_id)

        # Preparar datos
        evento_data = {
            'title': titulo,
            'description': descripcion[:5000] if descripcion else None,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'venue_name': venue_name,
            'venue_address': venue_address,
            'latitude': round(latitude, 8),
            'longitude': round(longitude, 8),
            'category': category,
            'subcategory': subcategory,
            'price': price,
            'is_free': is_free,
            'external_id': external_id,
            'source': 'gemini_padron',
            'image_url': image_url,
            'event_url': None,
            'city': 'Buenos Aires',
            'country': 'Argentina'
        }

        # Insertar en DB
        if insert_event(cursor, evento_data):
            eventos_insertados += 1

    # Commit cambios
    connection.commit()
    cursor.close()

    return (eventos_procesados, eventos_insertados)


def main():
    """Función principal"""
    print("Iniciando importacion de eventos de barrios a MySQL...")
    print("="*70)

    # Conectar a MySQL
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_database = os.getenv('MYSQL_DATABASE', 'events')
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')

    print(f"\nConectando a MySQL...")
    print(f"   Host: {mysql_host}:{mysql_port}")
    print(f"   Database: {mysql_database}")

    try:
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            database=mysql_database,
            user=mysql_user,
            password=mysql_password,
            charset='utf8mb4'
        )
        print("OK Conexion exitosa a MySQL\n")
    except Exception as e:
        print(f"ERROR conectando a MySQL: {e}")
        print("\nVerifica las variables de entorno en .env:")
        print("   MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD")
        return

    # Obtener archivos JSON
    padron_path = Path(__file__).parent
    json_files = sorted(padron_path.glob('*_noviembre.json'))

    print(f"Encontrados {len(json_files)} archivos JSON\n")

    total_procesados = 0
    total_insertados = 0
    archivos_exitosos = 0

    # Procesar cada archivo
    for i, json_file in enumerate(json_files, 1):
        barrio_name = json_file.stem.replace('_noviembre', '').replace('-', ' ').title()
        print(f"[{i}/{len(json_files)}] {barrio_name}")

        try:
            procesados, insertados = process_json_file(json_file, connection)
            total_procesados += procesados
            total_insertados += insertados

            if insertados > 0:
                archivos_exitosos += 1
                print(f"  OK {insertados}/{procesados} eventos insertados")
            else:
                print(f"  SKIP 0/{procesados} eventos (sin fechas validas o duplicados)")

        except Exception as e:
            print(f"  ERROR procesando archivo: {e}")
            import traceback
            traceback.print_exc()

    # Cerrar conexión
    connection.close()

    # Resumen final
    print("\n" + "="*70)
    print("IMPORTACION COMPLETADA")
    print("="*70)
    print(f"Archivos procesados: {len(json_files)}")
    print(f"Archivos con eventos: {archivos_exitosos}")
    print(f"Eventos procesados: {total_procesados}")
    print(f"Eventos insertados: {total_insertados}")

    if total_procesados > 0:
        tasa = (total_insertados / total_procesados) * 100
        print(f"Tasa de exito: {tasa:.1f}%")

    print("\nProximos pasos:")
    print("   1. Verificar eventos en la base de datos")
    print("   2. Probar endpoint: GET /api/events?location=Buenos Aires")
    print("   3. Filtrar por barrio en el frontend")


if __name__ == "__main__":
    main()
