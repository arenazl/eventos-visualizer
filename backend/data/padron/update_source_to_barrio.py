"""
Actualiza el campo source de 'gemini_padron' al nombre del barrio
Extrae el barrio del external_id que tiene formato: padron_barrio_mes_N
"""
import pymysql
import os
import re
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
print("ACTUALIZANDO SOURCE -> BARRIO")
print("="*70)

# Obtener todos los eventos del padrón
cur.execute("""
    SELECT id, external_id, source
    FROM events
    WHERE source = 'gemini_padron'
""")

eventos = cur.fetchall()
print(f"\nEncontrados {len(eventos)} eventos para actualizar\n")

updated_count = 0

for event_id, external_id, old_source in eventos:
    # Extraer barrio del external_id
    # Formato: padron_barrio_mes_N
    match = re.match(r'padron_([a-z-]+)_\w+_\d+', external_id)

    if match:
        barrio_normalized = match.group(1)

        # Convertir a formato bonito: "palermo", "san-telmo" -> "Palermo", "San Telmo"
        barrio_name = barrio_normalized.replace('-', ' ').title()

        # Actualizar
        cur.execute("""
            UPDATE events
            SET source = %s
            WHERE id = %s
        """, (barrio_name, event_id))

        updated_count += 1

        if updated_count <= 10:  # Mostrar primeros 10
            print(f"  {external_id:<40} -> source = '{barrio_name}'")

if updated_count > 10:
    print(f"  ... y {updated_count - 10} eventos más")

# Commit
conn.commit()

print(f"\nOK {updated_count} eventos actualizados")

# Verificar resultado
print("\nDistribución por barrio:")
print("-"*70)

cur.execute("""
    SELECT source, COUNT(*) as count
    FROM events
    WHERE external_id LIKE 'padron_%'
    GROUP BY source
    ORDER BY count DESC
""")

for row in cur.fetchall():
    print(f"  {row[0]:<25} {row[1]:>3} eventos")

cur.close()
conn.close()

print("\n" + "="*70)
print("COMPLETADO")
print("="*70)
