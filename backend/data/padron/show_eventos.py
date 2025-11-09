"""
Muestra los eventos del padrón importados en MySQL
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
print("EVENTOS DEL PADRON DE BARRIOS EN MYSQL")
print("="*90)

# Mostrar 20 eventos
cur.execute("""
    SELECT title, start_datetime, venue_name, category, price, is_free, city
    FROM events
    WHERE source = 'gemini_padron'
    ORDER BY start_datetime
    LIMIT 20
""")

print(f"\n{'TITULO':<40} {'FECHA':<12} {'LUGAR':<25} {'CATEGORIA':<12} {'PRECIO':<15}")
print("-"*90)

for row in cur.fetchall():
    title = row[0][:38]
    fecha = row[1].strftime('%Y-%m-%d')
    lugar = row[2][:23] if row[2] else ''
    categoria = row[3]
    precio = 'GRATIS' if row[5] else row[4]

    print(f"{title:<40} {fecha:<12} {lugar:<25} {categoria:<12} {precio:<15}")

print("\n" + "="*90)
print("BASE DE DATOS: MySQL (Aiven Cloud)")
print("HOST: mysql-aiven-arenazl.e.aivencloud.com:23108")
print("DATABASE: events")
print("TABLA: events")
print("FILTRO: source = 'gemini_padron'")
print("="*90)

cur.close()
conn.close()
