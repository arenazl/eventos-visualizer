"""
Verifica el estado final de los campos source
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
print("ESTADO FINAL DE CAMPOS source")
print("="*70)

# Total de eventos
cur.execute("SELECT COUNT(*) FROM events")
total = cur.fetchone()[0]
print(f"\nTotal eventos en base: {total}")

# Eventos con source NULL
cur.execute("SELECT COUNT(*) FROM events WHERE source IS NULL")
nulls = cur.fetchone()[0]
print(f"Eventos con source = NULL: {nulls}")

# Eventos del padrón (con barrio)
cur.execute("""
    SELECT COUNT(*) FROM events
    WHERE external_id LIKE 'padron_%'
""")
padron_count = cur.fetchone()[0]
print(f"Eventos del padron (con barrio): {padron_count}")

# Ver barrios únicos
cur.execute("""
    SELECT DISTINCT source
    FROM events
    WHERE external_id LIKE 'padron_%'
    AND source IS NOT NULL
    ORDER BY source
""")

barrios = [row[0] for row in cur.fetchall()]
print(f"\nBarrios unicos en eventos del padron: {len(barrios)}")
print("Ejemplos:", ", ".join(barrios[:10]))

# Ejemplos de eventos del padrón
print("\nEjemplos de eventos del padron con barrio:")
print("-"*70)

cur.execute("""
    SELECT title, source, city, start_datetime
    FROM events
    WHERE external_id LIKE 'padron_%'
    ORDER BY start_datetime
    LIMIT 10
""")

for row in cur.fetchall():
    title = row[0][:40]
    barrio = row[1] or 'N/A'
    ciudad = row[2] or 'N/A'
    fecha = row[3].strftime('%Y-%m-%d') if row[3] else 'N/A'

    print(f"{fecha} | {title:40} | {barrio:20}")

# Verificar que NO haya eventos del padrón con source NULL
cur.execute("""
    SELECT COUNT(*) FROM events
    WHERE external_id LIKE 'padron_%'
    AND source IS NULL
""")
padron_null = cur.fetchone()[0]

if padron_null > 0:
    print(f"\nALERTA: {padron_null} eventos del padron tienen source NULL!")
else:
    print("\nOK Todos los eventos del padron tienen barrio en source")

cur.close()
conn.close()

print("\n" + "="*70)
print("RESUMEN:")
print(f"  - {nulls} eventos internacionales (source = NULL)")
print(f"  - {padron_count} eventos del padron (source = barrio)")
print(f"  - {len(barrios)} barrios diferentes")
print("="*70)
