"""
Script para actualizar imágenes faltantes en eventos existentes
Busca eventos sin image_url y les agrega imágenes de Google
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Configurar codificación
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar backend al path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)

import pymysql
import subprocess
import json
import time


def get_first_image_from_google(query: str) -> str:
    """Usa Node.js para buscar imagen en Google"""
    try:
        # Crear script temporal de Node.js
        node_script = """
const axios = require('axios');

async function obtenerPrimeraImagen(query) {
  try {
    const response = await axios.get(
      `https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=isch`,
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      }
    );

    const jpgMatch = response.data.match(/(https:\\/\\/[^\\s"'<>)]+\\.jpg)/i);
    if (jpgMatch) return jpgMatch[1];

    const pngMatch = response.data.match(/(https:\\/\\/[^\\s"'<>)]+\\.png)/i);
    if (pngMatch) return pngMatch[1];

    const jpegMatch = response.data.match(/(https:\\/\\/[^\\s"'<>)]+\\.jpeg)/i);
    if (jpegMatch) return jpegMatch[1];

    return null;
  } catch (error) {
    return null;
  }
}

const query = process.argv[2];
obtenerPrimeraImagen(query).then(url => {
  console.log(url || '');
  process.exit(0);
}).catch(() => {
  console.log('');
  process.exit(1);
});
"""

        # Guardar script temporal
        temp_script = backend_path / 'temp_image_search.js'
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(node_script)

        # Ejecutar con Node.js
        result = subprocess.run(
            ['node', str(temp_script), query],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(backend_path)
        )

        # Limpiar script temporal
        if temp_script.exists():
            temp_script.unlink()

        image_url = result.stdout.strip()

        # Verificar que no sea logo de Google
        if image_url and 'gstatic' not in image_url:
            return image_url

        return None

    except Exception as e:
        print(f"    ❌ Error buscando imagen: {e}")
        return None


def update_event_image(cursor, connection, event_id: str, image_url: str) -> bool:
    """Actualiza la imagen de un evento"""
    try:
        sql = "UPDATE events SET image_url = %s WHERE id = %s"
        cursor.execute(sql, (image_url, event_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"    ❌ Error actualizando: {e}")
        return False


def main():
    """Función principal"""
    print("📸 Actualizando imágenes faltantes en eventos")
    print("="*70)

    # Conectar a MySQL
    connection = pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        charset='utf8mb4'
    )
    print("✅ Conexión a MySQL establecida\n")

    # Obtener eventos sin imagen
    cursor = connection.cursor()
    sql = """
        SELECT id, title, city, country
        FROM events
        WHERE image_url IS NULL OR image_url = ''
        LIMIT 100
    """
    cursor.execute(sql)
    eventos_sin_imagen = cursor.fetchall()

    total = len(eventos_sin_imagen)
    print(f"📊 Encontrados {total} eventos sin imagen (procesando primeros 100)\n")

    if total == 0:
        print("✅ Todos los eventos tienen imagen!")
        connection.close()
        return

    actualizados = 0
    errores = 0

    for i, (event_id, title, city, country) in enumerate(eventos_sin_imagen, 1):
        # Mostrar progreso
        title_short = title[:40] if len(title) > 40 else title
        print(f"[{i}/{total}] {title_short}...")

        # Buscar imagen
        image_url = get_first_image_from_google(title)

        if image_url:
            # Actualizar en la base
            if update_event_image(cursor, connection, event_id, image_url):
                print(f"  ✅ Imagen actualizada")
                actualizados += 1
            else:
                errores += 1
        else:
            print(f"  ⚠️  No se encontró imagen")
            errores += 1

        # Pausa para no ser bloqueado
        time.sleep(2)

        # Progreso cada 10
        if i % 10 == 0:
            print(f"\n  💾 Progreso: {actualizados} actualizados, {errores} sin imagen\n")

    connection.close()

    # Resumen
    print("\n" + "="*70)
    print("✅ ACTUALIZACIÓN COMPLETADA")
    print("="*70)
    print(f"📊 Eventos procesados: {total}")
    print(f"✅ Imágenes agregadas: {actualizados}")
    print(f"⚠️  Sin imagen: {errores}")

    if total > 0:
        print(f"📈 Tasa de éxito: {(actualizados / total) * 100:.1f}%")


if __name__ == "__main__":
    main()
