#!/usr/bin/env python3
"""
Script para investigar la discrepancia en la base de datos
"""
import mysql.connector
import os
from datetime import datetime

def connect_to_mysql():
    """Conectar a MySQL con las credenciales del .env"""
    try:
        connection = mysql.connector.connect(
            host='mysql-aiven-arenazl.e.aivencloud.com',
            port=2310,
            user='avnadmin',
            password='AVNS_Fqe0qsChCHnqSnVsvoi',
            database='eventviewd'
        )
        return connection
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

def investigate_events():
    """Investigar la discrepancia de eventos"""
    connection = connect_to_mysql()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        print("🔍 INVESTIGACIÓN DE EVENTOS EN BD")
        print("=" * 50)
        
        # 1. Total de eventos
        cursor.execute("SELECT COUNT(*) as total FROM events")
        total = cursor.fetchone()
        print(f"📊 Total eventos en BD: {total['total']}")
        
        # 2. Eventos por fuente
        cursor.execute("""
            SELECT source_api, COUNT(*) as count 
            FROM events 
            GROUP BY source_api 
            ORDER BY count DESC
        """)
        sources = cursor.fetchall()
        print("\n📋 Eventos por fuente:")
        for source in sources:
            print(f"   • {source['source_api']}: {source['count']}")
        
        # 3. Eventos recientes
        cursor.execute("""
            SELECT COUNT(*) as recent_count 
            FROM events 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        recent = cursor.fetchone()
        print(f"\n⏰ Eventos creados en la última hora: {recent['recent_count']}")
        
        # 4. Últimos eventos agregados
        cursor.execute("""
            SELECT title, source_api, created_at 
            FROM events 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        latest = cursor.fetchall()
        print("\n🆕 Últimos 10 eventos agregados:")
        for event in latest:
            print(f"   • {event['title'][:50]}... ({event['source_api']}) - {event['created_at']}")
        
        # 5. Verificar duplicados por título
        cursor.execute("""
            SELECT title, COUNT(*) as duplicates 
            FROM events 
            GROUP BY title 
            HAVING COUNT(*) > 1 
            ORDER BY duplicates DESC
            LIMIT 5
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print("\n🔄 Posibles duplicados por título:")
            for dup in duplicates:
                print(f"   • '{dup['title']}': {dup['duplicates']} copias")
        else:
            print("\n✅ No hay duplicados evidentes por título")
        
        # 6. Verificar source_id duplicados
        cursor.execute("""
            SELECT source_id, COUNT(*) as duplicates 
            FROM events 
            GROUP BY source_id 
            HAVING COUNT(*) > 1 
            ORDER BY duplicates DESC
            LIMIT 5
        """)
        source_id_dups = cursor.fetchall()
        if source_id_dups:
            print("\n🔄 Duplicados por source_id:")
            for dup in source_id_dups:
                print(f"   • source_id '{dup['source_id']}': {dup['duplicates']} copias")
        else:
            print("\n✅ No hay duplicados por source_id")
        
    except Exception as e:
        print(f"❌ Error en investigación: {e}")
    
    finally:
        connection.close()

if __name__ == "__main__":
    investigate_events()