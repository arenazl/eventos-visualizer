"""
Muestra eventos agrupados por barrio (source)
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

print("="*90)
print("EVENTOS DEL PADRON POR BARRIO")
print("="*90)

# Mostrar por barrio
cur.execute("""
    SELECT source, COUNT(*) as count
    FROM events
    WHERE external_id LIKE 'padron_%'
    GROUP BY source
    ORDER BY count DESC
""")

print("\nDISTRIBUCION POR BARRIO:")
print("-"*90)

for row in cur.fetchall():
    barrio = row[0]
    count = row[1]
    print(f"  {barrio:<30} {count:>3} eventos")

# Mostrar algunos ejemplos de cada tipo
print("\n" + "="*90)
print("EJEMPLOS DE EVENTOS POR BARRIO:")
print("="*90)

barrios_ejemplo = ['Palermo', 'Recoleta', 'San Telmo', 'Belgrano']

for barrio in barrios_ejemplo:
    print(f"\n{barrio.upper()}:")
    print("-"*90)

    cur.execute("""
        SELECT title, start_datetime, venue_name, category, is_free
        FROM events
        WHERE source = %s
        ORDER BY start_datetime
        LIMIT 3
    """, (barrio,))

    for row in cur.fetchall():
        title = row[0][:40]
        fecha = row[1].strftime('%Y-%m-%d')
        lugar = row[2][:25] if row[2] else ''
        categoria = row[3]
        precio = 'GRATIS' if row[4] else 'PAGO'

        print(f"  {fecha} | {title:<42} | {categoria:<10} | {precio}")

print("\n" + "="*90)
print("AHORA PODES FILTRAR POR BARRIO:")
print("  SELECT * FROM events WHERE source = 'Palermo'")
print("  SELECT * FROM events WHERE source = 'Recoleta'")
print("  GET /api/events?source=Palermo")
print("="*90)

cur.close()
conn.close()
