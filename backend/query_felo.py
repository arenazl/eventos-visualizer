import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM events WHERE city LIKE '%Buenos Aires%' AND created_at >= '2025-11-12 20:00:00'")
total = cursor.fetchone()[0]

cursor.execute("SELECT title, city, DATE(start_datetime) as fecha FROM events WHERE city LIKE '%Buenos Aires%' AND created_at >= '2025-11-12 20:00:00' ORDER BY created_at DESC LIMIT 30")
eventos = cursor.fetchall()

print(f"\n📊 Total eventos Buenos Aires desde 2025-11-12 20:00: {total}")
print("\n🎉 Últimos 30 eventos:")
for i, (title, city, fecha) in enumerate(eventos, 1):
    print(f"{i}. {title} - {city} - {fecha}")

cursor.close()
conn.close()
