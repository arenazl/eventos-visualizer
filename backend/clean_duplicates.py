"""
CLEAN DUPLICATES - Eliminar eventos duplicados en MySQL
Mantiene siempre el registro MAS ANTIGUO (mas confiable)
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL')
engine = create_engine(DB_URL, pool_pre_ping=True)

def clean_duplicates(dry_run=True):
    """
    Limpiar eventos duplicados

    Args:
        dry_run: Si es True, solo muestra lo que haria sin eliminar
    """

    print("=" * 80)
    print("LIMPIEZA DE DUPLICADOS EN BASE DE DATOS")
    print("=" * 80)

    if dry_run:
        print("\n[DRY RUN] Modo simulacion - NO se eliminara nada")
        print("Ejecuta con: python clean_duplicates.py --execute para eliminar\n")
    else:
        print("\n[MODO EJECUCION] Se eliminaran duplicados PERMANENTEMENTE\n")

    with engine.connect() as conn:
        total_deleted = 0

        # 1. LIMPIAR DUPLICADOS POR URL
        print("\n1. LIMPIANDO DUPLICADOS POR URL...")
        print("-" * 80)

        # Obtener IDs de duplicados a eliminar (mantiene el id mas bajo = mas antiguo)
        result = conn.execute(text("""
            SELECT e1.id, e1.title, e1.event_url
            FROM events e1
            INNER JOIN (
                SELECT event_url, MIN(id) as keep_id
                FROM events
                WHERE event_url IS NOT NULL AND event_url != ''
                GROUP BY event_url
                HAVING COUNT(*) > 1
            ) e2 ON e1.event_url = e2.event_url
            WHERE e1.id > e2.keep_id
            ORDER BY e1.event_url, e1.id
        """))

        url_duplicates = result.fetchall()
        print(f"Encontrados {len(url_duplicates)} duplicados por URL a eliminar")

        if url_duplicates:
            # Mostrar algunos ejemplos
            print("\nEjemplos de eventos a eliminar:")
            for row in url_duplicates[:5]:
                print(f"  - ID {row[0]}: {row[1][:50]}... ({row[2][:60]}...)")

            if not dry_run:
                # Eliminar en lotes
                ids_to_delete = [row[0] for row in url_duplicates]
                conn.execute(text("""
                    DELETE FROM events WHERE id IN :ids
                """), {"ids": tuple(ids_to_delete)})
                conn.commit()
                print(f"[OK] Eliminados {len(ids_to_delete)} duplicados por URL")
                total_deleted += len(ids_to_delete)

        # 2. LIMPIAR DUPLICADOS POR TITULO + FECHA (solo si tienen titulo valido)
        print("\n2. LIMPIANDO DUPLICADOS POR TITULO + FECHA...")
        print("-" * 80)

        result = conn.execute(text("""
            SELECT e1.id, e1.title, e1.start_datetime
            FROM events e1
            INNER JOIN (
                SELECT title, start_datetime, MIN(id) as keep_id
                FROM events
                WHERE title IS NOT NULL
                    AND title != ''
                    AND title != 'Sin titulo'
                    AND title NOT LIKE 'Sin t%'
                GROUP BY title, start_datetime
                HAVING COUNT(*) > 1
            ) e2 ON e1.title = e2.title AND e1.start_datetime = e2.start_datetime
            WHERE e1.id > e2.keep_id
            ORDER BY e1.title, e1.start_datetime, e1.id
        """))

        title_duplicates = result.fetchall()
        print(f"Encontrados {len(title_duplicates)} duplicados por titulo+fecha a eliminar")

        if title_duplicates:
            # Mostrar algunos ejemplos
            print("\nEjemplos de eventos a eliminar:")
            for row in title_duplicates[:5]:
                print(f"  - ID {row[0]}: {row[1][:50]}... ({row[2]})")

            if not dry_run:
                # Eliminar en lotes
                ids_to_delete = [row[0] for row in title_duplicates]
                conn.execute(text("""
                    DELETE FROM events WHERE id IN :ids
                """), {"ids": tuple(ids_to_delete)})
                conn.commit()
                print(f"[OK] Eliminados {len(ids_to_delete)} duplicados por titulo+fecha")
                total_deleted += len(ids_to_delete)

        # 3. LIMPIAR EVENTOS CON TITULO VACIO O "SIN TITULO" DUPLICADOS
        print("\n3. LIMPIANDO EVENTOS SIN TITULO DUPLICADOS...")
        print("-" * 80)

        result = conn.execute(text("""
            SELECT e1.id, e1.title, e1.start_datetime, e1.venue_name
            FROM events e1
            INNER JOIN (
                SELECT start_datetime, venue_name, MIN(id) as keep_id
                FROM events
                WHERE (title IS NULL OR title = '' OR title = 'Sin titulo' OR title LIKE 'Sin t%')
                    AND venue_name IS NOT NULL
                GROUP BY start_datetime, venue_name
                HAVING COUNT(*) > 1
            ) e2 ON e1.start_datetime = e2.start_datetime
                AND (e1.venue_name = e2.venue_name OR (e1.venue_name IS NULL AND e2.venue_name IS NULL))
            WHERE e1.id > e2.keep_id
                AND (e1.title IS NULL OR e1.title = '' OR e1.title = 'Sin titulo' OR e1.title LIKE 'Sin t%')
            ORDER BY e1.start_datetime, e1.venue_name, e1.id
        """))

        empty_title_duplicates = result.fetchall()
        print(f"Encontrados {len(empty_title_duplicates)} eventos sin titulo duplicados a eliminar")

        if empty_title_duplicates:
            # Mostrar algunos ejemplos
            print("\nEjemplos de eventos a eliminar:")
            for row in empty_title_duplicates[:5]:
                title_display = row[1] if row[1] else "(vacio)"
                venue_display = row[3] if row[3] else "(sin venue)"
                print(f"  - ID {row[0]}: {title_display} - {venue_display} ({row[2]})")

            if not dry_run:
                # Eliminar en lotes
                ids_to_delete = [row[0] for row in empty_title_duplicates]
                conn.execute(text("""
                    DELETE FROM events WHERE id IN :ids
                """), {"ids": tuple(ids_to_delete)})
                conn.commit()
                print(f"[OK] Eliminados {len(ids_to_delete)} eventos sin titulo duplicados")
                total_deleted += len(ids_to_delete)

        # RESUMEN FINAL
        print("\n" + "=" * 80)
        print("RESUMEN DE LIMPIEZA")
        print("=" * 80)

        if dry_run:
            total_would_delete = len(url_duplicates) + len(title_duplicates) + len(empty_title_duplicates)
            print(f"\n[SIMULACION] Se eliminarian un total de: {total_would_delete} eventos duplicados")
            print("\nPara ejecutar la limpieza real, ejecuta:")
            print("  python backend/clean_duplicates.py --execute")
        else:
            print(f"\n[OK] Total eliminados: {total_deleted} eventos duplicados")

            # Verificar resultado final
            result = conn.execute(text("SELECT COUNT(*) FROM events"))
            final_count = result.scalar()
            print(f"[OK] Eventos restantes en BD: {final_count}")

            print("\nVerifica el resultado con:")
            print("  python backend/check_duplicates.py")

if __name__ == "__main__":
    import sys

    # Verificar si se paso --execute
    execute = "--execute" in sys.argv

    if not execute:
        print("\n" + "=" * 80)
        print("ATENCION: Esto es una SIMULACION")
        print("=" * 80)
        print("Para eliminar duplicados realmente, ejecuta:")
        print("  python backend/clean_duplicates.py --execute")
        print("=" * 80 + "\n")

    clean_duplicates(dry_run=not execute)
