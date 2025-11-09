"""
Verifica los eventos importados en MySQL
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
print("VERIFICACION DE EVENTOS IMPORTADOS")
print("="*70)

# Total de eventos
cur.execute("SELECT COUNT(*) FROM events")
total = cur.fetchone()[0]
print(f"\nTotal eventos en base: {total}")

# Eventos del padrón
cur.execute("SELECT COUNT(*) FROM events WHERE source = 'gemini_padron'")
padron_count = cur.fetchone()[0]
print(f"Eventos del padron: {padron_count}")

# Por categoría
cur.execute("""
    SELECT category, COUNT(*) as count
    FROM events
    WHERE source = 'gemini_padron'
    GROUP BY category
    ORDER BY count DESC
""")

print("\nEventos por categoria:")
print("-"*70)
for row in cur.fetchall():
    print(f"  {row[0]:<20} {row[1]:>5} eventos")

# Eventos gratuitos
cur.execute("SELECT COUNT(*) FROM events WHERE source = 'gemini_padron' AND is_free = 1")
free_count = cur.fetchone()[0]
print(f"\nEventos gratuitos: {free_count} ({free_count/padron_count*100:.1f}%)")

# Próximos eventos
cur.execute("""
    SELECT title, start_datetime, venue_name, category
    FROM events
    WHERE source = 'gemini_padron' AND start_datetime >= CURDATE()
    ORDER BY start_datetime
    LIMIT 10
""")

print("\nProximos 10 eventos:")
print("-"*70)
for row in cur.fetchall():
    print(f"{row[1].strftime('%Y-%m-%d %H:%M'):<20} {row[0]:<35} ({row[3]})")

# Distribución por ciudad
cur.execute("""
    SELECT city, COUNT(*) as count
    FROM events
    WHERE source = 'gemini_padron'
    GROUP BY city
""")

print("\nEventos por ciudad:")
print("-"*70)
for row in cur.fetchall():
    print(f"  {row[0]:<20} {row[1]:>5} eventos")

cur.close()
conn.close()

print("\n" + "="*70)
print("Verificacion completada")
print("="*70)
