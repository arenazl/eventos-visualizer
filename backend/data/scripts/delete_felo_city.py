#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Elimina eventos con 'Felo' en el campo city (error de parsing)
"""

import pymysql
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Cargar .env
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
ENV_FILE = BACKEND_DIR / '.env'

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'events'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def main():
    print("=" * 80)
    print("🗑️  ELIMINAR EVENTOS CON 'FELO' EN CIUDAD")
    print("=" * 80)

    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Conectado a MySQL\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    try:
        # Primero mostrar qué se va a eliminar
        select_sql = "SELECT id, title, city FROM events WHERE city LIKE '%Felo%'"
        cursor.execute(select_sql)
        eventos = cursor.fetchall()

        print(f"📋 EVENTOS A ELIMINAR: {len(eventos)}\n")

        for i, evento in enumerate(eventos[:20], 1):
            print(f"{i}. [{evento['city']}] {evento['title'][:60]}")

        if len(eventos) > 20:
            print(f"... y {len(eventos) - 20} más\n")
        else:
            print()

        # Confirmar
        print("=" * 80)
        confirm = input(f"¿Eliminar {len(eventos)} eventos? (s/n): ").lower()

        if confirm != 's':
            print("❌ Cancelado")
            cursor.close()
            connection.close()
            return

        # DELETE
        delete_sql = "DELETE FROM events WHERE city LIKE '%Felo%'"
        cursor.execute(delete_sql)
        connection.commit()

        print(f"\n✅ {cursor.rowcount} eventos eliminados")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()
