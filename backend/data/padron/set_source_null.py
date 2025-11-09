"""
Pone source = NULL para eventos con source='gemini' o source='brightdata' o similar
"""
import pymysql
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
backend_path = Path(__file__).parent.parent.parent
load_dotenv(backend_path / '.env')

# Conectar
conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT', '3306')),
    database=os.getenv('MYSQL_DATABASE'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD')
)

cur = conn.cursor()

print("="*70)
print("ACTUALIZANDO source A NULL")
print("="*70)

# Contar cuántos hay antes
cur.execute("""
    SELECT COUNT(*) FROM events
    WHERE source LIKE '%gemini%' OR source LIKE '%brightdata%'
""")
total_antes = cur.fetchone()[0]

print(f"\nEventos con 'gemini' o 'brightdata' en source: {total_antes}")

if total_antes > 0:
    # Actualizar a NULL
    cur.execute("""
        UPDATE events
        SET source = NULL
        WHERE source LIKE '%gemini%' OR source LIKE '%brightdata%'
    """)

    affected = cur.rowcount
    conn.commit()

    print(f"OK {affected} eventos actualizados a source = NULL")

    # Verificar
    cur.execute("""
        SELECT COUNT(*) FROM events
        WHERE source IS NULL
    """)
    nulls = cur.fetchone()[0]

    print(f"\nEventos con source = NULL: {nulls}")

    # Ver algunos ejemplos
    cur.execute("""
        SELECT title, city, source
        FROM events
        WHERE source IS NULL
        LIMIT 5
    """)

    print("\nEjemplos de eventos con source = NULL:")
    print("-"*70)
    for row in cur.fetchall():
        print(f"  {row[0][:50]:50} | {row[1]:20} | {row[2]}")
else:
    print("No hay eventos con 'gemini' o 'brightdata' en source")

cur.close()
conn.close()

print("\n" + "="*70)
print("COMPLETADO")
print("="*70)
