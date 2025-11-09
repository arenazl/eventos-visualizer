"""
Script para analizar eventos por provincia en la base de datos MySQL
"""
import pymysql
from collections import Counter
import re

# Configuración de conexión
DB_CONFIG = {
    'host': 'mysql-aiven-arenazl.e.aivencloud.com',
    'port': 23108,
    'user': 'avnadmin',
    'password': 'AVNS_Fqe0qsChCHnqSnVsvoi',
    'database': 'events',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def extract_province_from_location(location_text):
    """
    Extraer provincia de texto de ubicación
    """
    if not location_text:
        return "Sin ubicación"

    location_text = location_text.lower()

    # Provincias argentinas comunes
    provinces = {
        'buenos aires': 'Buenos Aires',
        'capital federal': 'CABA',
        'caba': 'CABA',
        'mendoza': 'Mendoza',
        'córdoba': 'Córdoba',
        'cordoba': 'Córdoba',
        'santa fe': 'Santa Fe',
        'tucumán': 'Tucumán',
        'tucuman': 'Tucumán',
        'salta': 'Salta',
        'chaco': 'Chaco',
        'corrientes': 'Corrientes',
        'entre ríos': 'Entre Ríos',
        'entre rios': 'Entre Ríos',
        'jujuy': 'Jujuy',
        'la pampa': 'La Pampa',
        'la rioja': 'La Rioja',
        'neuquén': 'Neuquén',
        'neuquen': 'Neuquén',
        'río negro': 'Río Negro',
        'rio negro': 'Río Negro',
        'san juan': 'San Juan',
        'san luis': 'San Luis',
        'santa cruz': 'Santa Cruz',
        'santiago del estero': 'Santiago del Estero',
        'tierra del fuego': 'Tierra del Fuego',
        'chubut': 'Chubut',
        'formosa': 'Formosa',
        'misiones': 'Misiones',
        'catamarca': 'Catamarca'
    }

    for key, province in provinces.items():
        if key in location_text:
            return province

    return "Otra ubicación"

def main():
    try:
        print(">> Conectando a MySQL...")
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            # Obtener total de eventos
            cursor.execute("SELECT COUNT(*) as total FROM events")
            total = cursor.fetchone()['total']
            print(f"\n>> TOTAL DE EVENTOS EN LA BASE DE DATOS: {total}")

            # Obtener estructura de la tabla
            cursor.execute("DESCRIBE events")
            columns = cursor.fetchall()
            print("\n>> COLUMNAS DE LA TABLA EVENTS:")
            for col in columns:
                print(f"  - {col['Field']} ({col['Type']})")

            # Obtener todos los eventos con ubicación
            cursor.execute("""
                SELECT
                    venue_name,
                    venue_address,
                    city,
                    title,
                    source,
                    category
                FROM events
            """)

            events = cursor.fetchall()

            # Analizar por provincia
            province_counter = Counter()
            category_counter = Counter()
            source_counter = Counter()

            events_by_province = {}

            for event in events:
                # Extraer provincia de city, venue_address o venue_name
                location = event.get('city') or event.get('venue_address') or event.get('venue_name') or ''
                province = extract_province_from_location(location)

                province_counter[province] += 1

                if province not in events_by_province:
                    events_by_province[province] = []

                events_by_province[province].append({
                    'title': (event.get('title') or 'Sin título')[:50],
                    'venue': (event.get('venue_name') or 'Sin venue')[:40],
                    'source': event.get('source') or 'desconocido'
                })

                # Contadores adicionales
                if event.get('category'):
                    category_counter[event['category']] += 1
                if event.get('source'):
                    source_counter[event['source']] += 1

            # Mostrar resumen por provincia
            print("\n" + "="*80)
            print(">> EVENTOS POR PROVINCIA")
            print("="*80)

            for province, count in province_counter.most_common():
                print(f"\n>>  {province}: {count} eventos")

                # Mostrar primeros 3 eventos como muestra
                sample_events = events_by_province[province][:3]
                for i, evt in enumerate(sample_events, 1):
                    print(f"   {i}. {evt['title']} | {evt['venue']} | [{evt['source']}]")

                if len(events_by_province[province]) > 3:
                    print(f"   ... y {len(events_by_province[province]) - 3} eventos más")

            # Resumen por categoría
            print("\n" + "="*80)
            print(">> EVENTOS POR CATEGORIA")
            print("="*80)
            for category, count in category_counter.most_common():
                print(f"  {category or 'Sin categoria'}: {count} eventos")

            # Resumen por fuente
            print("\n" + "="*80)
            print(">> EVENTOS POR FUENTE (API/Scraper)")
            print("="*80)
            for source, count in source_counter.most_common():
                print(f"  {source}: {count} eventos")

            print("\n" + "="*80)
            print(">> Analisis completado exitosamente")
            print("="*80)

    except Exception as e:
        print(f"ERROR: Al conectar/consultar la base de datos: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'connection' in locals():
            connection.close()
            print("\n>> Conexion cerrada")

if __name__ == "__main__":
    main()
