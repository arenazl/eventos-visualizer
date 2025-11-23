"""
PROCESS REGION - Pipeline completo de eventos por region

Uso:
    python backend/data/scripts/process_region.py --country argentina
    python backend/data/scripts/process_region.py --country argentina --limit 10
    python backend/data/scripts/process_region.py --country brasil --skip-images

Proceso:
    1. Lee archivo JSON de region (ej: latinamerica/sudamerica/argentina.json)
    2. Para cada ciudad:
       - Scraping de eventos (Gemini AI)
       - Parseo a formato comun
       - Insercion en MySQL (evita duplicados)
       - Actualizacion de imagenes (Google Images 3 etapas)
    3. Genera reporte detallado
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import pymysql
from typing import List, Dict, Any
import unicodedata

# Fix Windows encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Imports de servicios
try:
    from services.gemini_factory import gemini_factory
    from services.google_images_service import search_google_image
except ImportError as e:
    print(f"Error: No se pudieron importar los servicios: {e}")
    print("Asegurate de estar en el directorio correcto.")
    sys.exit(1)


class RegionProcessor:
    """Procesa eventos de una región completa"""

    def __init__(self, region_path: str, limit: int = None, skip_images: bool = False):
        self.region_path = Path(region_path)
        self.limit = limit
        self.skip_images = skip_images
        self.stats = {
            'cities_processed': 0,
            'events_scraped': 0,
            'events_inserted': 0,
            'events_duplicated': 0,
            'images_updated': 0,
            'images_failed': 0,
            'errors': []
        }

    def get_country_files(self) -> List[Path]:
        """Obtiene lista de archivos JSON a procesar"""
        if not self.region_path.exists():
            raise FileNotFoundError(f" Ruta no existe: {self.region_path}")

        # Si es un archivo JSON, retornar solo ese
        if self.region_path.is_file() and self.region_path.suffix == '.json':
            return [self.region_path]

        # Si es directorio, buscar todos los JSON recursivamente
        if self.region_path.is_dir():
            json_files = list(self.region_path.rglob("*.json"))
            if not json_files:
                raise FileNotFoundError(f" No se encontraron archivos JSON en: {self.region_path}")
            return json_files

        raise ValueError(f" Ruta inválida: {self.region_path}")

    def get_mysql_connection(self):
        """Crea conexión a MySQL"""
        return pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'events'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    async def scrape_city_events(self, city_name: str, country: str) -> List[Dict]:
        """Scrapea eventos de una ciudad usando Gemini"""
        print(f"\n Scrapeando eventos: {city_name}, {country}")

        try:
            # Llamar al Gemini Factory (retorna lista directamente)
            events = await gemini_factory.execute_global_scrapers(
                location=city_name,
                limit=self.limit or 20
            )

            print(f"    {len(events)} eventos encontrados")
            self.stats['events_scraped'] += len(events)

            return events
        except Exception as e:
            error_msg = f"Error scrapeando {city_name}: {e}"
            print(f"    {error_msg}")
            self.stats['errors'].append(error_msg)
            return []

    def insert_event_to_mysql(self, event: Dict) -> bool:
        """Inserta evento en MySQL (evita duplicados)"""
        try:
            connection = self.get_mysql_connection()
            cursor = connection.cursor()

            # Normalizar título para búsqueda de duplicados
            title_normalized = ''.join(
                c for c in unicodedata.normalize('NFD', event.get('title', ''))
                if unicodedata.category(c) != 'Mn'
            )

            # Verificar si ya existe
            check_query = """
                SELECT id FROM events
                WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                    title, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u'),
                    'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U'))
                LIKE LOWER(%s)
                LIMIT 1
            """
            cursor.execute(check_query, (f"%{title_normalized}%",))
            existing = cursor.fetchone()

            if existing:
                self.stats['events_duplicated'] += 1
                cursor.close()
                connection.close()
                return False

            # Insertar nuevo evento
            insert_query = """
                INSERT INTO events (
                    id, title, description, start_datetime, end_datetime,
                    venue_name, venue_address, city, category, subcategory,
                    price, is_free, image_url, source, created_at, updated_at
                ) VALUES (
                    UUID(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """

            cursor.execute(insert_query, (
                event.get('title', 'Sin título'),
                event.get('description', ''),
                event.get('start_datetime'),
                event.get('end_datetime'),
                event.get('venue_name', ''),
                event.get('venue_address', ''),
                event.get('city', ''),
                event.get('category', 'other'),
                event.get('subcategory', 'other'),
                event.get('price', '0.0'),
                event.get('is_free', True),
                event.get('image_url', ''),
                event.get('source', 'gemini_scraper')
            ))

            connection.commit()
            cursor.close()
            connection.close()

            self.stats['events_inserted'] += 1
            return True

        except Exception as e:
            error_msg = f"Error insertando '{event.get('title', 'unknown')}': {e}"
            print(f"    {error_msg}")
            self.stats['errors'].append(error_msg)
            return False

    async def update_event_image(self, event: Dict) -> bool:
        """Actualiza imagen del evento con Google Images (3 etapas)"""
        if self.skip_images:
            return False

        try:
            title = event.get('title', '')
            venue = event.get('venue_name', '')
            city = event.get('city', '')
            description = event.get('description', '')

            print(f"   ️ Buscando imagen para: {title}")

            # Buscar imagen con sistema de 3 etapas
            image_url = await search_google_image(
                title,
                venue=venue,
                city=city,
                description=description
            )

            if image_url and 'gstatic' not in image_url:
                # Actualizar en MySQL
                connection = self.get_mysql_connection()
                cursor = connection.cursor()

                title_normalized = ''.join(
                    c for c in unicodedata.normalize('NFD', title)
                    if unicodedata.category(c) != 'Mn'
                )

                update_query = """
                    UPDATE events
                    SET image_url = %s, updated_at = NOW()
                    WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                        title, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u'),
                        'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U'))
                    LIKE LOWER(%s)
                """

                cursor.execute(update_query, (image_url, f"%{title_normalized}%"))
                connection.commit()
                cursor.close()
                connection.close()

                self.stats['images_updated'] += 1
                print(f"    Imagen actualizada")
                return True
            else:
                self.stats['images_failed'] += 1
                print(f"   ️ No se encontró imagen")
                return False

        except Exception as e:
            error_msg = f"Error actualizando imagen para '{event.get('title', 'unknown')}': {e}"
            print(f"    {error_msg}")
            self.stats['errors'].append(error_msg)
            self.stats['images_failed'] += 1
            return False

    async def process_city(self, city: Dict, country: str):
        """Procesa una ciudad completa"""
        city_name = city['name']
        print(f"\n{'='*60}")
        print(f" PROCESANDO: {city_name}, {country}")
        print(f"{'='*60}")

        # 1. Scraping
        events = await self.scrape_city_events(city_name, country)

        # Aplicar límite si existe
        if self.limit:
            events = events[:self.limit]
            print(f"   ℹ️ Limitado a {len(events)} eventos")

        # 2. Inserción en MySQL
        print(f"\n Insertando en MySQL...")
        for event in events:
            self.insert_event_to_mysql(event)

        # 3. Actualización de imágenes
        if not self.skip_images and events:
            print(f"\n️ Actualizando imágenes...")
            for event in events:
                await self.update_event_image(event)

        self.stats['cities_processed'] += 1

    def extract_cities_from_config(self, config: Dict) -> List[Dict]:
        """Extrae todas las ciudades de cualquier estructura de JSON"""
        all_cities = []

        # Todas las posibles claves de agrupacion regional
        group_keys = [
            'communities', 'provinces', 'states', 'regions', 'countries',
            'departments', 'cantons', 'voivodeships', 'districts', 'counties',
            'territories', 'prefectures'
        ]

        found = False
        for group_key in group_keys:
            if group_key in config:
                found = True
                for group in config[group_key]:
                    if isinstance(group, dict) and 'cities' in group:
                        for city in group['cities']:
                            all_cities.append(city)

        # Estructura directa: cities[] en root
        if not found and 'cities' in config:
            for city in config['cities']:
                all_cities.append(city)

        return all_cities

    async def process_country_file(self, json_file: Path):
        """Procesa un archivo JSON de país"""
        print(f"\n{'='*60}")
        print(f" PROCESANDO: {json_file.name}")
        print(f"{'='*60}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            error_msg = f"Error cargando {json_file}: {e}"
            print(f" {error_msg}")
            self.stats['errors'].append(error_msg)
            return

        country = config.get('country', 'Unknown')

        # Extraer ciudades de cualquier estructura
        cities = self.extract_cities_from_config(config)

        print(f" País: {country}")
        print(f" Ciudades: {len(cities)}")

        # Procesar cada ciudad
        for city in cities:
            await self.process_city(city, country)

            # Si la ciudad tiene barrios (ej: Buenos Aires), procesarlos también
            if 'barrios' in city:
                print(f"\n    Procesando barrios de {city['name']}...")
                for barrio in city['barrios']:
                    await self.process_city(
                        {'name': f"{barrio['name']}, {city['name']}"},
                        country
                    )

    async def process_region(self):
        """Procesa todas las ciudades de la región"""
        print(f"\n{'='*60}")
        print(f"PROCESS REGION")
        print(f"{'='*60}\n")
        print(f"Ruta: {self.region_path}")

        # Obtener archivos a procesar
        try:
            country_files = self.get_country_files()
        except (FileNotFoundError, ValueError) as e:
            print(e)
            return

        print(f" Archivos a procesar: {len(country_files)}")
        if self.limit:
            print(f"️ Límite de eventos por ciudad: {self.limit}")
        if self.skip_images:
            print(f"⏭️ Actualización de imágenes: DESACTIVADA")
        print()

        # Procesar cada archivo de país
        for json_file in country_files:
            await self.process_country_file(json_file)

        # Reporte final
        self.print_report()

    def print_report(self):
        """Imprime reporte final"""
        print(f"\n{'='*60}")
        print(f" REPORTE FINAL")
        print(f"{'='*60}")
        print(f" Ciudades procesadas:     {self.stats['cities_processed']}")
        print(f" Eventos scrapeados:      {self.stats['events_scraped']}")
        print(f" Eventos insertados:      {self.stats['events_inserted']}")
        print(f"⏭️ Eventos duplicados:      {self.stats['events_duplicated']}")
        print(f"️ Imágenes actualizadas:   {self.stats['images_updated']}")
        print(f" Imágenes fallidas:       {self.stats['images_failed']}")
        print(f"️ Errores totales:         {len(self.stats['errors'])}")

        if self.stats['errors']:
            print(f"\n️ ERRORES:")
            for error in self.stats['errors'][:10]:  # Mostrar solo primeros 10
                print(f"   - {error}")

        print(f"\n{'='*60}\n")


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Procesar eventos de una región completa'
    )
    parser.add_argument(
        '--region',
        required=True,
        help='Ruta completa a región, sub-región o archivo JSON (ej: C:\\Code\\eventos-visualizer\\backend\\data\\regions\\latinamerica)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Límite de eventos por ciudad (para testing)'
    )
    parser.add_argument(
        '--skip-images',
        action='store_true',
        help='Saltar actualización de imágenes'
    )

    args = parser.parse_args()

    # Crear y ejecutar procesador
    processor = RegionProcessor(
        region_path=args.region,
        limit=args.limit,
        skip_images=args.skip_images
    )

    await processor.process_region()


if __name__ == "__main__":
    asyncio.run(main())
