#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Borra eventos de BuenosAliens con fechas incorrectas
"""
import sys
import pymysql

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Shadowhunter2025!',
        database='eventos_db',
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # Borrar eventos de BuenosAliens
    cursor.execute('DELETE FROM events WHERE source=%s', ('buenosaliens.com',))
    conn.commit()

    print(f'✅ Borrados {cursor.rowcount} eventos de BuenosAliens')

    conn.close()
except Exception as e:
    print(f'❌ Error: {e}')
