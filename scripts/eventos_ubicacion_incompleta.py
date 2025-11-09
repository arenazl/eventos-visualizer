"""
Script para identificar eventos con ubicación INCOMPLETA
(tienen ciudad pero no país, o país pero no ciudad)
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
            # 1. Eventos CON ciudad pero SIN país
            print("\n" + "="*80)
            print("BUSCANDO: Eventos con CIUDAD pero SIN PAIS")
            print("="*80)

            cursor.execute("""
                SELECT COUNT(*) as total
                FROM events
                WHERE (city IS NOT NULL AND city != '' AND TRIM(city) != '')
                  AND (country IS NULL OR country = '' OR TRIM(country) = '')
            """)
            con_ciudad_sin_pais = cursor.fetchone()['total']
            print(f">> Total: {con_ciudad_sin_pais} eventos")

            # 2. Eventos CON país pero SIN ciudad
            print("\n" + "="*80)
            print("BUSCANDO: Eventos con PAIS pero SIN CIUDAD")
            print("="*80)

            cursor.execute("""
                SELECT COUNT(*) as total
                FROM events
                WHERE (country IS NOT NULL AND country != '' AND TRIM(country) != '')
                  AND (city IS NULL OR city = '' OR TRIM(city) = '')
            """)
            con_pais_sin_ciudad = cursor.fetchone()['total']
            print(f">> Total: {con_pais_sin_ciudad} eventos")

            # 3. Eventos SIN ciudad NI país
            print("\n" + "="*80)
            print("BUSCANDO: Eventos SIN ciudad NI pais")
            print("="*80)

            cursor.execute("""
                SELECT COUNT(*) as total
                FROM events
                WHERE (city IS NULL OR city = '' OR TRIM(city) = '')
                  AND (country IS NULL OR country = '' OR TRIM(country) = '')
            """)
            sin_ambos = cursor.fetchone()['total']
            print(f">> Total: {sin_ambos} eventos")

            # Obtener detalles de eventos CON ciudad pero SIN país
            if con_ciudad_sin_pais > 0:
                cursor.execute("""
                    SELECT
                        id,
                        title,
                        city,
                        country,
                        venue_name,
                        venue_address,
                        category,
                        source,
                        start_datetime
                    FROM events
                    WHERE (city IS NOT NULL AND city != '' AND TRIM(city) != '')
                      AND (country IS NULL OR country = '' OR TRIM(country) = '')
                    ORDER BY start_datetime DESC
                    LIMIT 500
                """)

                eventos_sin_pais = cursor.fetchall()

                # Guardar en archivo
                output_file = "C:\\Code\\eventos-visualizer\\scripts\\eventos_sin_pais.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("="*100 + "\n")
                    f.write(f"EVENTOS CON CIUDAD PERO SIN PAIS - TOTAL: {con_ciudad_sin_pais}\n")
                    f.write("="*100 + "\n\n")

                    for i, event in enumerate(eventos_sin_pais, 1):
                        f.write(f"\n{i}. {event.get('title') or 'Sin titulo'}\n")
                        f.write(f"   ID: {event.get('id')}\n")
                        f.write(f"   Ciudad: {event.get('city')}\n")
                        f.write(f"   Pais: [VACIO]\n")
                        f.write(f"   Venue: {event.get('venue_name') or 'N/A'}\n")
                        f.write(f"   Direccion: {event.get('venue_address') or 'N/A'}\n")
                        f.write(f"   Categoria: {event.get('category') or 'N/A'}\n")
                        f.write(f"   Fuente: {event.get('source') or 'N/A'}\n")
                        f.write(f"   Fecha: {event.get('start_datetime')}\n")
                        f.write("-"*100 + "\n")

                print(f"\n>> Archivo guardado: {output_file}")

                # Mostrar muestra en consola
                print("\n" + "="*80)
                print("MUESTRA DE EVENTOS CON CIUDAD PERO SIN PAIS (primeros 20):")
                print("="*80)
                for i, event in enumerate(eventos_sin_pais[:20], 1):
                    print(f"{i}. Ciudad: {event.get('city')} | {event.get('title')[:50]}")

            # Obtener detalles de eventos CON país pero SIN ciudad
            if con_pais_sin_ciudad > 0:
                cursor.execute("""
                    SELECT
                        id,
                        title,
                        city,
                        country,
                        venue_name,
                        venue_address,
                        category,
                        source,
                        start_datetime
                    FROM events
                    WHERE (country IS NOT NULL AND country != '' AND TRIM(country) != '')
                      AND (city IS NULL OR city = '' OR TRIM(city) = '')
                    ORDER BY start_datetime DESC
                    LIMIT 500
                """)

                eventos_sin_ciudad = cursor.fetchall()

                # Guardar en archivo
                output_file = "C:\\Code\\eventos-visualizer\\scripts\\eventos_sin_ciudad.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("="*100 + "\n")
                    f.write(f"EVENTOS CON PAIS PERO SIN CIUDAD - TOTAL: {con_pais_sin_ciudad}\n")
                    f.write("="*100 + "\n\n")

                    for i, event in enumerate(eventos_sin_ciudad, 1):
                        f.write(f"\n{i}. {event.get('title') or 'Sin titulo'}\n")
                        f.write(f"   ID: {event.get('id')}\n")
                        f.write(f"   Ciudad: [VACIO]\n")
                        f.write(f"   Pais: {event.get('country')}\n")
                        f.write(f"   Venue: {event.get('venue_name') or 'N/A'}\n")
                        f.write(f"   Direccion: {event.get('venue_address') or 'N/A'}\n")
                        f.write(f"   Categoria: {event.get('category') or 'N/A'}\n")
                        f.write(f"   Fuente: {event.get('source') or 'N/A'}\n")
                        f.write(f"   Fecha: {event.get('start_datetime')}\n")
                        f.write("-"*100 + "\n")

                print(f"\n>> Archivo guardado: {output_file}")

                # Mostrar muestra en consola
                print("\n" + "="*80)
                print("MUESTRA DE EVENTOS CON PAIS PERO SIN CIUDAD (primeros 20):")
                print("="*80)
                for i, event in enumerate(eventos_sin_ciudad[:20], 1):
                    print(f"{i}. Pais: {event.get('country')} | {event.get('title')[:50]}")

            # Resumen final
            print("\n" + "="*80)
            print("RESUMEN FINAL:")
            print("="*80)
            print(f"Eventos con ciudad pero SIN pais: {con_ciudad_sin_pais}")
            print(f"Eventos con pais pero SIN ciudad: {con_pais_sin_ciudad}")
            print(f"Eventos SIN ciudad NI pais: {sin_ambos}")
            print(f"Total eventos a arreglar: {con_ciudad_sin_pais + con_pais_sin_ciudad + sin_ambos}")

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
