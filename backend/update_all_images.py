#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para actualizar TODAS las imágenes de eventos en MySQL
Busca eventos con image_url = NULL y les agrega imágenes de Google

Uso:
    python update_all_images.py --limit 500    # Procesar 500 eventos
    python update_all_images.py --all          # Procesar TODOS
    python update_all_images.py --city "Paris" # Solo una ciudad
"""

import pymysql
import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Cargar .env
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / '.env'

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Configuración de MySQL
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'events'),
    'charset': 'utf8mb4'
}


def get_db_connection():
    """Crea conexión a MySQL"""
    return pymysql.connect(**DB_CONFIG)


def buscar_imagen_google(titulo):
    """
    Busca imagen en Google usando Node.js
    Llama al script buscar-primera-imagen.js
    """
    import subprocess
    import json

    # Path al script Node.js
    node_script = SCRIPT_DIR / 'buscar-primera-imagen.js'

    if not node_script.exists():
        print(f"  ⚠️  Script Node.js no encontrado: {node_script}")
        return None

    try:
        # Ejecutar Node.js para buscar imagen
        result = subprocess.run(
            ['node', '-e', f"""
const {{ obtenerPrimeraImagen }} = require('{str(node_script).replace(chr(92), '/')}');
obtenerPrimeraImagen('{titulo.replace("'", "")}').then(url => {{
    if (url) console.log(url);
}}).catch(() => {{}});
            """],
            capture_output=True,
            text=True,
            timeout=10
        )

        url = result.stdout.strip()

        if url and 'http' in url and 'gstatic' not in url:
            return url
        return None

    except Exception as e:
        print(f"  ⚠️  Error buscando imagen: {str(e)[:50]}")
        return None


def actualizar_imagenes(limit=None, ciudad=None):
    """Actualiza imágenes de eventos sin imagen"""

    print('🚀 Actualizando imágenes de eventos en MySQL\n')

    # Conectar a MySQL
    connection = get_db_connection()
    cursor = connection.cursor()

    print('✅ Conectado a MySQL\n')

    # Construir query
    query = """
        SELECT id, title, city, country
        FROM events
        WHERE (image_url IS NULL OR image_url LIKE '%picsum%' OR image_url LIKE '%placeholder%')
    """

    params = []

    if ciudad:
        query += " AND city = %s"
        params.append(ciudad)

    if limit:
        query += f" LIMIT {limit}"

    # Buscar eventos
    cursor.execute(query, params if params else None)
    eventos = cursor.fetchall()

    print(f'📊 {len(eventos)} eventos a procesar\n')

    if len(eventos) == 0:
        print('✅ No hay eventos para procesar')
        cursor.close()
        connection.close()
        return

    updated = 0
    errors = 0
    no_image = 0

    for i, evento in enumerate(eventos):
        event_id, title, city, country = evento
        display_name = title[:50] if title else 'Sin título'

        print(f'🔍 [{i + 1}/{len(eventos)}] {display_name}... ({city})')

        try:
            # Buscar imagen en Google
            image_url = buscar_imagen_google(title)

            if image_url:
                # Actualizar en MySQL
                cursor.execute(
                    'UPDATE events SET image_url = %s WHERE id = %s',
                    (image_url, event_id)
                )
                connection.commit()
                print(f'  ✅ Imagen actualizada')
                updated += 1
            else:
                print(f'  ⚠️  No se encontró imagen válida')
                no_image += 1

        except Exception as error:
            print(f'  ❌ Error: {str(error)[:50]}')
            errors += 1

        # Pausa para no ser bloqueado (2 segundos)
        import time
        time.sleep(2)

        # Mostrar progreso cada 50 eventos
        if (i + 1) % 50 == 0:
            porcentaje = ((i + 1) / len(eventos) * 100)
            print(f'\n💾 Progreso: {i + 1}/{len(eventos)} ({porcentaje:.1f}%) - {updated} actualizados, {no_image} sin imagen, {errors} errores\n')

    # Cerrar conexión
    cursor.close()
    connection.close()

    # Resumen final
    print('\n' + '=' * 60)
    print('🎉 Proceso completado!')
    print(f'✅ Imágenes actualizadas: {updated}')
    print(f'⚠️  Sin imagen válida: {no_image}')
    print(f'❌ Errores: {errors}')
    print('=' * 60 + '\n')


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Actualizar imágenes de eventos en MySQL'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Número máximo de eventos a procesar (ej: 500)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Procesar TODOS los eventos sin límite'
    )

    parser.add_argument(
        '--city',
        type=str,
        help='Procesar solo eventos de una ciudad específica (ej: "Paris")'
    )

    args = parser.parse_args()

    # Determinar límite
    limit = None
    if not args.all:
        limit = args.limit if args.limit else 100  # Default 100

    # Confirmación si es --all
    if args.all:
        print('⚠️  ATENCIÓN: Vas a procesar TODOS los eventos sin límite')
        confirm = input('¿Estás seguro? (si/no): ')
        if confirm.lower() not in ['si', 'sí', 's', 'yes', 'y']:
            print('❌ Cancelado')
            return

    # Ejecutar
    actualizar_imagenes(limit=limit, ciudad=args.city)


if __name__ == "__main__":
    main()
