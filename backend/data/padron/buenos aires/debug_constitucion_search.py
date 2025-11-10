import pymysql
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"ERROR: .env not found at {env_path}")
    sys.exit(1)

# Conectar a MySQL usando las variables correctas
connection = pymysql.connect(
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE'),
    charset='utf8mb4'
)

try:
    cur = connection.cursor()

    # 1. Total events with NULL source
    print("\n=== DIAGNÓSTICO DE SOURCE ===\n")
    cur.execute("SELECT COUNT(*) FROM events WHERE source IS NULL")
    null_count = cur.fetchone()[0]
    print(f"Total eventos con source NULL: {null_count}")

    # 2. Total events with source set
    cur.execute("SELECT COUNT(*) FROM events WHERE source IS NOT NULL")
    not_null_count = cur.fetchone()[0]
    print(f"Total eventos con source NOT NULL: {not_null_count}")

    # 3. Show some examples of events with NULL source (sin filtro de external_id)
    print("\n=== EJEMPLOS DE EVENTOS CON SOURCE NULL ===\n")
    cur.execute("""
        SELECT id, title, external_id, source, city, venue_address
        FROM events
        WHERE source IS NULL
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  External ID: {row[2]}")
        print(f"  Source: {row[3]}")
        print(f"  City: {row[4]}")
        print(f"  Address: {row[5]}")
        print()

    # 4. Show examples with source set correctly (sin filtro de external_id)
    print("\n=== EJEMPLOS DE EVENTOS CON SOURCE NO NULL ===\n")
    cur.execute("""
        SELECT id, title, external_id, source, city, venue_address
        FROM events
        WHERE source IS NOT NULL
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  External ID: {row[2]}")
        print(f"  Source: {row[3]}")
        print(f"  City: {row[4]}")
        print(f"  Address: {row[5]}")
        print()

    # 5. Contar cuántos eventos tienen barrio names en source
    print("\n=== EVENTOS POR BARRIO ===\n")
    cur.execute("""
        SELECT source, COUNT(*) as count
        FROM events
        WHERE source IS NOT NULL
        GROUP BY source
        ORDER BY count DESC
    """)
    for row in cur.fetchall():
        print(f"{row[0]}: {row[1]} eventos")
    
    # 6. Check what happens when searching "constitución"
    print("\n\n=== BÚSQUEDA 'CONSTITUCIÓN' ===\n")
    search_term = "constitución"
    pattern = f"%{search_term}%"

    cur.execute("""
        SELECT id, title, source, city, venue_address
        FROM events
        WHERE
            city LIKE %s
            OR venue_address LIKE %s
            OR source LIKE %s
        ORDER BY
            CASE
                WHEN source = %s THEN 0
                WHEN source LIKE %s THEN 1
                ELSE 2
            END,
            start_datetime ASC
        LIMIT 20
    """, (pattern, pattern, pattern, "Constitución", pattern))

    results = cur.fetchall()
    print(f"Total resultados: {len(results)}\n")
    for row in results:
        print(f"Title: {row[1]}")
        print(f"  Source: {row[2]}")
        print(f"  City: {row[3]}")
        print(f"  Address: {row[4]}")
        print()

finally:
    cur.close()
    connection.close()
