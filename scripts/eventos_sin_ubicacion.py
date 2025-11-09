"""
Script para identificar eventos SIN ciudad NI país
"""
import pymysql
import json

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

def main():
    try:
        print(">> Conectando a MySQL...")
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            # Buscar eventos sin ciudad Y sin país
            cursor.execute("""
                SELECT
                    id,
                    title,
                    description,
                    venue_name,
                    venue_address,
                    city,
                    country,
                    category,
                    subcategory,
                    source,
                    start_datetime,
                    price,
                    is_free,
                    image_url,
                    event_url,
                    latitude,
                    longitude
                FROM events
                WHERE (city IS NULL OR city = '' OR TRIM(city) = '')
                  AND (country IS NULL OR country = '' OR TRIM(country) = '')
                ORDER BY start_datetime DESC
            """)

            events = cursor.fetchall()

            print(f"\n>> Total eventos SIN ciudad ni pais: {len(events)}")

            if len(events) == 0:
                print(">> No hay eventos sin ubicacion. Todos tienen al menos ciudad o pais!")
                return

            # Guardar en archivo de texto
            txt_file = "C:\\Code\\eventos-visualizer\\scripts\\eventos_sin_ciudad_ni_pais.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write("="*100 + "\n")
                f.write(f"EVENTOS SIN CIUDAD NI PAIS - TOTAL: {len(events)}\n")
                f.write("="*100 + "\n\n")

                for i, event in enumerate(events, 1):
                    f.write(f"\n{'='*100}\n")
                    f.write(f"EVENTO #{i}\n")
                    f.write(f"{'='*100}\n")
                    f.write(f"ID: {event.get('id')}\n")
                    f.write(f"Titulo: {event.get('title') or 'N/A'}\n")
                    f.write(f"Descripcion: {(event.get('description') or 'N/A')[:200]}...\n")
                    f.write(f"\n--- UBICACION ---\n")
                    f.write(f"Ciudad: {event.get('city') or '[VACIO]'}\n")
                    f.write(f"Pais: {event.get('country') or '[VACIO]'}\n")
                    f.write(f"Venue: {event.get('venue_name') or '[VACIO]'}\n")
                    f.write(f"Direccion: {event.get('venue_address') or '[VACIO]'}\n")
                    f.write(f"Latitud: {event.get('latitude') or '[VACIO]'}\n")
                    f.write(f"Longitud: {event.get('longitude') or '[VACIO]'}\n")
                    f.write(f"\n--- DETALLES ---\n")
                    f.write(f"Categoria: {event.get('category') or 'N/A'}\n")
                    f.write(f"Subcategoria: {event.get('subcategory') or 'N/A'}\n")
                    f.write(f"Fuente: {event.get('source') or 'N/A'}\n")
                    f.write(f"Fecha: {event.get('start_datetime') or 'N/A'}\n")
                    f.write(f"Precio: {event.get('price') or 'N/A'}\n")
                    f.write(f"Gratis: {'Si' if event.get('is_free') else 'No'}\n")
                    f.write(f"URL: {event.get('event_url') or 'N/A'}\n")
                    f.write(f"Imagen: {event.get('image_url') or 'N/A'}\n")

            print(f"\n>> Archivo de texto guardado: {txt_file}")

            # Guardar en JSON para análisis programático
            json_file = "C:\\Code\\eventos-visualizer\\scripts\\eventos_sin_ciudad_ni_pais.json"

            # Convertir datetime a string para JSON
            events_json = []
            for event in events:
                event_copy = dict(event)
                if event_copy.get('start_datetime'):
                    event_copy['start_datetime'] = str(event_copy['start_datetime'])
                events_json.append(event_copy)

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total': len(events),
                    'eventos': events_json
                }, f, ensure_ascii=False, indent=2)

            print(f">> Archivo JSON guardado: {json_file}")

            # Mostrar resumen en consola
            print("\n" + "="*100)
            print("RESUMEN DE PRIMEROS 10 EVENTOS:")
            print("="*100)

            for i, event in enumerate(events[:10], 1):
                print(f"\n{i}. {event.get('title') or 'Sin titulo'}[:80]")
                print(f"   Venue: {event.get('venue_name') or '[SIN VENUE]'}")
                print(f"   Direccion: {event.get('venue_address') or '[SIN DIRECCION]'}")
                print(f"   Coords: lat={event.get('latitude') or 'N/A'}, lon={event.get('longitude') or 'N/A'}")
                print(f"   Fuente: {event.get('source') or 'N/A'}")
                print(f"   Categoria: {event.get('category') or 'N/A'}")

            if len(events) > 10:
                print(f"\n... y {len(events) - 10} eventos mas (ver archivos completos)")

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
