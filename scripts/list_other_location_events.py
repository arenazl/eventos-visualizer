"""
Script para listar eventos sin provincia identificada
"""
import pymysql
from collections import Counter

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
            # Obtener todos los eventos
            cursor.execute("""
                SELECT
                    id,
                    title,
                    venue_name,
                    venue_address,
                    city,
                    country,
                    category,
                    source,
                    start_datetime
                FROM events
                ORDER BY start_datetime DESC
            """)

            events = cursor.fetchall()
            print(f">> Total eventos: {len(events)}")

            # Filtrar eventos sin provincia identificada
            other_location_events = []
            city_counter = Counter()

            for event in events:
                location = event.get('city') or event.get('venue_address') or event.get('venue_name') or ''
                province = extract_province_from_location(location)

                if province == "Otra ubicación":
                    other_location_events.append(event)
                    # Contar ciudades
                    city = event.get('city') or 'Sin ciudad'
                    city_counter[city] += 1

            print(f"\n>> Eventos en 'Otra ubicacion': {len(other_location_events)}")

            # Mostrar distribución de ciudades
            print("\n" + "="*80)
            print(">> DISTRIBUCION POR CIUDAD (Top 20)")
            print("="*80)
            for city, count in city_counter.most_common(20):
                print(f"  {city}: {count} eventos")

            # Mostrar primeros 100 eventos detallados
            print("\n" + "="*80)
            print(">> PRIMEROS 100 EVENTOS DETALLADOS")
            print("="*80)

            for i, event in enumerate(other_location_events[:100], 1):
                print(f"\n{i}. {event.get('title') or 'Sin titulo'}[:80]")
                print(f"   Ciudad: {event.get('city') or 'N/A'}")
                print(f"   Venue: {event.get('venue_name') or 'N/A'}[:60]")
                print(f"   Direccion: {event.get('venue_address') or 'N/A'}[:80]")
                print(f"   Pais: {event.get('country') or 'N/A'}")
                print(f"   Categoria: {event.get('category') or 'N/A'}")
                print(f"   Fuente: {event.get('source') or 'N/A'}")
                print(f"   Fecha: {event.get('start_datetime') or 'N/A'}")

            # Guardar listado completo en archivo
            output_file = "eventos_sin_provincia.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write(f"EVENTOS SIN PROVINCIA IDENTIFICADA - TOTAL: {len(other_location_events)}\n")
                f.write("="*80 + "\n\n")

                f.write("DISTRIBUCION POR CIUDAD:\n")
                f.write("-"*80 + "\n")
                for city, count in city_counter.most_common():
                    f.write(f"{city}: {count} eventos\n")

                f.write("\n" + "="*80 + "\n")
                f.write("LISTADO COMPLETO DE EVENTOS:\n")
                f.write("="*80 + "\n\n")

                for i, event in enumerate(other_location_events, 1):
                    f.write(f"\n{i}. {event.get('title') or 'Sin titulo'}\n")
                    f.write(f"   ID: {event.get('id')}\n")
                    f.write(f"   Ciudad: {event.get('city') or 'N/A'}\n")
                    f.write(f"   Venue: {event.get('venue_name') or 'N/A'}\n")
                    f.write(f"   Direccion: {event.get('venue_address') or 'N/A'}\n")
                    f.write(f"   Pais: {event.get('country') or 'N/A'}\n")
                    f.write(f"   Categoria: {event.get('category') or 'N/A'}\n")
                    f.write(f"   Fuente: {event.get('source') or 'N/A'}\n")
                    f.write(f"   Fecha: {event.get('start_datetime')}\n")
                    f.write("-"*80 + "\n")

            print(f"\n>> Listado completo guardado en: {output_file}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'connection' in locals():
            connection.close()
            print("\n>> Conexion cerrada")

if __name__ == "__main__":
    main()
