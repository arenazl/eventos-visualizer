#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧹 LIMPIEZA DE BASE DE DATOS
- Elimina eventos duplicados (mismo título + fecha + venue)
- Elimina eventos sin título o descripción
- Muestra estadísticas antes y después
"""

import sys
import os
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

load_dotenv()

# Configurar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class DatabaseCleaner:
    def __init__(self):
        self.engine = None
        self.conn = None
        self.stats = {
            'total_inicial': 0,
            'duplicados_eliminados': 0,
            'sin_titulo_eliminados': 0,
            'sin_descripcion_eliminados': 0,
            'total_eliminados': 0,
            'total_final': 0
        }

    def connect(self):
        """Conectar a MySQL usando SQLAlchemy"""
        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                print("❌ DATABASE_URL no encontrada en .env")
                return False

            self.engine = create_engine(db_url, pool_pre_ping=True)
            self.conn = self.engine.connect()
            print("✅ Conectado a MySQL")
            return True
        except Exception as e:
            print(f"❌ Error conectando a MySQL: {e}")
            return False

    def get_stats(self):
        """Obtener estadísticas de la base de datos"""
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
        print("="*70)

        # Total de eventos
        result = self.conn.execute(text("SELECT COUNT(*) FROM events"))
        total = result.fetchone()[0]
        self.stats['total_inicial'] = total
        print(f"Total de eventos: {total:,}")

        # Eventos sin título
        result = self.conn.execute(text("SELECT COUNT(*) FROM events WHERE title IS NULL OR title = ''"))
        sin_titulo = result.fetchone()[0]
        print(f"Sin título: {sin_titulo:,}")

        # Eventos sin descripción
        result = self.conn.execute(text("SELECT COUNT(*) FROM events WHERE description IS NULL OR description = ''"))
        sin_desc = result.fetchone()[0]
        print(f"Sin descripción: {sin_desc:,}")

        # Eventos sin título Y sin descripción
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM events
            WHERE (title IS NULL OR title = '')
            AND (description IS NULL OR description = '')
        """))
        sin_ambos = result.fetchone()[0]
        print(f"Sin título NI descripción: {sin_ambos:,}")

        # Duplicados (mismo título + fecha + venue)
        result = self.conn.execute(text("""
            SELECT COUNT(*) - COUNT(DISTINCT title, start_datetime, venue_name)
            FROM events
            WHERE title IS NOT NULL AND title != ''
        """))
        duplicados = result.fetchone()[0]
        print(f"Eventos duplicados: {duplicados:,}")

        print("="*70)

    def find_duplicates(self):
        """Encontrar eventos duplicados"""
        print("\n🔍 Buscando duplicados...")

        # Encontrar IDs de eventos duplicados (conservar el más antiguo)
        result = self.conn.execute(text("""
            SELECT e1.id
            FROM events e1
            INNER JOIN events e2 ON
                e1.title = e2.title
                AND e1.start_datetime = e2.start_datetime
                AND COALESCE(e1.venue_name, '') = COALESCE(e2.venue_name, '')
                AND e1.id > e2.id
            WHERE e1.title IS NOT NULL
            AND e1.title != ''
        """))

        duplicates = [row[0] for row in result.fetchall()]
        print(f"   Encontrados {len(duplicates):,} duplicados")
        return duplicates

    def delete_duplicates(self, dry_run=True):
        """Eliminar eventos duplicados"""
        duplicates = self.find_duplicates()

        if not duplicates:
            print("   ✅ No hay duplicados para eliminar")
            return 0

        if dry_run:
            print(f"   [DRY RUN] Se eliminarían {len(duplicates):,} eventos duplicados")
            # Mostrar algunos ejemplos
            if duplicates:
                placeholders = ','.join([f"'{d}'" for d in duplicates[:5]])
                result = self.conn.execute(text(f"""
                    SELECT title, start_datetime, venue_name, city
                    FROM events
                    WHERE id IN ({placeholders})
                """))

                print("\n   📋 Ejemplos de duplicados a eliminar:")
                for row in result.fetchall():
                    print(f"      - {row[0]} | {row[1]} | {row[2]} | {row[3]}")
            return len(duplicates)
        else:
            # Eliminar en batches de 1000
            batch_size = 1000
            deleted = 0

            for i in range(0, len(duplicates), batch_size):
                batch = duplicates[i:i+batch_size]
                placeholders = ','.join([f"'{d}'" for d in batch])
                result = self.conn.execute(text(f"DELETE FROM events WHERE id IN ({placeholders})"))
                deleted += result.rowcount
                self.conn.commit()

            print(f"   ✅ Eliminados {deleted:,} eventos duplicados")
            self.stats['duplicados_eliminados'] = deleted
            return deleted

    def delete_without_title_and_description(self, dry_run=True):
        """Eliminar eventos sin título NI descripción"""
        print("\n🗑️ Eliminando eventos sin título NI descripción...")

        # Contar primero
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM events
            WHERE (title IS NULL OR title = '')
            AND (description IS NULL OR description = '')
        """))
        count = result.fetchone()[0]

        if count == 0:
            print("   ✅ No hay eventos sin título ni descripción")
            return 0

        if dry_run:
            print(f"   [DRY RUN] Se eliminarían {count:,} eventos sin título ni descripción")

            # Mostrar ejemplos
            result = self.conn.execute(text("""
                SELECT id, venue_name, city, start_datetime, source
                FROM events
                WHERE (title IS NULL OR title = '')
                AND (description IS NULL OR description = '')
                LIMIT 5
            """))

            print("\n   📋 Ejemplos de eventos a eliminar:")
            for row in result.fetchall():
                print(f"      - ID: {row[0]} | Venue: {row[1]} | Ciudad: {row[2]} | Fecha: {row[3]} | Source: {row[4]}")

            return count
        else:
            result = self.conn.execute(text("""
                DELETE FROM events
                WHERE (title IS NULL OR title = '')
                AND (description IS NULL OR description = '')
            """))
            deleted = result.rowcount
            self.conn.commit()
            print(f"   ✅ Eliminados {deleted:,} eventos sin título ni descripción")
            self.stats['sin_titulo_eliminados'] = deleted
            return deleted

    def delete_only_without_description(self, dry_run=True):
        """Eliminar SOLO eventos que tienen título pero NO tienen descripción"""
        print("\n🗑️ Eliminando eventos con título pero sin descripción...")

        # Contar primero
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM events
            WHERE (title IS NOT NULL AND title != '')
            AND (description IS NULL OR description = '')
        """))
        count = result.fetchone()[0]

        if count == 0:
            print("   ✅ No hay eventos solo sin descripción")
            return 0

        if dry_run:
            print(f"   [DRY RUN] Se eliminarían {count:,} eventos solo sin descripción")

            # Mostrar ejemplos
            result = self.conn.execute(text("""
                SELECT title, venue_name, city, start_datetime
                FROM events
                WHERE (title IS NOT NULL AND title != '')
                AND (description IS NULL OR description = '')
                LIMIT 5
            """))

            print("\n   📋 Ejemplos de eventos a eliminar:")
            for row in result.fetchall():
                print(f"      - {row[0]} | {row[1]} | {row[2]} | {row[3]}")

            return count
        else:
            result = self.conn.execute(text("""
                DELETE FROM events
                WHERE (title IS NOT NULL AND title != '')
                AND (description IS NULL OR description = '')
            """))
            deleted = result.rowcount
            self.conn.commit()
            print(f"   ✅ Eliminados {deleted:,} eventos solo sin descripción")
            self.stats['sin_descripcion_eliminados'] = deleted
            return deleted

    def run_cleanup(self, dry_run=True, delete_only_no_description=False):
        """Ejecutar limpieza completa"""
        print("\n" + "="*70)
        if dry_run:
            print("🧪 MODO DRY RUN - No se eliminará nada, solo se mostrará qué se haría")
        else:
            print("🔥 MODO REAL - SE ELIMINARÁN EVENTOS PERMANENTEMENTE")
        print("="*70)

        # Estadísticas iniciales
        self.get_stats()

        # 1. Eliminar duplicados
        dup_count = self.delete_duplicates(dry_run)

        # 2. Eliminar sin título ni descripción
        no_both_count = self.delete_without_title_and_description(dry_run)

        # 3. (Opcional) Eliminar solo sin descripción
        only_no_desc_count = 0
        if delete_only_no_description:
            only_no_desc_count = self.delete_only_without_description(dry_run)

        # Estadísticas finales
        print("\n" + "="*70)
        print("📊 RESUMEN DE LIMPIEZA")
        print("="*70)
        print(f"Duplicados: {dup_count:,}")
        print(f"Sin título NI descripción: {no_both_count:,}")
        if delete_only_no_description:
            print(f"Solo sin descripción: {only_no_desc_count:,}")
        print(f"\nTotal a eliminar: {dup_count + no_both_count + only_no_desc_count:,}")

        if not dry_run:
            # Estadísticas finales después de eliminar
            result = self.conn.execute(text("SELECT COUNT(*) FROM events"))
            final_total = result.fetchone()[0]
            self.stats['total_final'] = final_total

            print(f"\nTotal eventos antes: {self.stats['total_inicial']:,}")
            print(f"Total eventos después: {final_total:,}")
            print(f"Diferencia: {self.stats['total_inicial'] - final_total:,}")

        print("="*70)

    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()
        print("\n✅ Conexión cerrada")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='🧹 Limpieza de base de datos de eventos')
    parser.add_argument('--real', action='store_true', help='Ejecutar limpieza real (por defecto es dry-run)')
    parser.add_argument('--delete-no-desc', action='store_true', help='También eliminar eventos solo sin descripción')
    args = parser.parse_args()

    cleaner = DatabaseCleaner()

    if not cleaner.connect():
        return

    try:
        dry_run = not args.real

        if dry_run:
            print("\n⚠️  Ejecutando en modo DRY RUN")
            print("   Para ejecutar la limpieza real, usa: python cleanup_database.py --real")
        else:
            print("\n⚠️⚠️⚠️ ADVERTENCIA ⚠️⚠️⚠️")
            print("   Estás a punto de ELIMINAR eventos PERMANENTEMENTE")
            print("   Esta acción NO SE PUEDE DESHACER")

            confirm = input("\n   ¿Estás seguro? Escribe 'SI' para confirmar: ")
            if confirm != 'SI':
                print("   ❌ Operación cancelada")
                return

        cleaner.run_cleanup(dry_run=dry_run, delete_only_no_description=args.delete_no_desc)

    finally:
        cleaner.close()


if __name__ == "__main__":
    main()
