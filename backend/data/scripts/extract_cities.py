#!/usr/bin/env python3
"""
Extrae todas las ciudades de una región para scrapear.
Lee los JSONs de la carpeta de región y genera lista de ciudades.
"""

import json
from pathlib import Path

def extract_cities_from_region(region_path):
    """Extrae todas las ciudades de una región."""
    region_path = Path(region_path)

    all_cities = []

    # Recorrer todos los JSONs de la región
    for json_file in region_path.rglob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            country = data.get('country', json_file.stem.title())
            country_code = data.get('country_code', '')

            # Buscar en todas las posibles estructuras de agrupacion
            group_keys = ['communities', 'provinces', 'states', 'regions', 'countries', 'departments', 'cantons', 'voivodeships', 'districts', 'counties', 'territories', 'prefectures']

            found = False
            for group_key in group_keys:
                if group_key in data:
                    found = True
                    for group in data[group_key]:
                        group_name = group.get('name', '') if isinstance(group, dict) else ''
                        cities_list = group.get('cities', []) if isinstance(group, dict) else []

                        for city in cities_list:
                            city_name = city.get('name', city) if isinstance(city, dict) else city
                            all_cities.append({
                                'city': city_name,
                                'country': country,
                                'country_code': country_code,
                                'region': group_name,
                                'source_file': str(json_file)
                            })

            # Estructura directa: cities[] en root
            if not found and 'cities' in data:
                for city in data['cities']:
                    city_name = city.get('name', city) if isinstance(city, dict) else city
                    all_cities.append({
                        'city': city_name,
                        'country': country,
                        'country_code': country_code,
                        'region': '',
                        'source_file': str(json_file)
                    })

        except Exception as e:
            print(f"Error leyendo {json_file}: {e}")

    return all_cities

def safe_print(text):
    """Print con encoding seguro para Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

def main():
    import sys

    if len(sys.argv) < 2:
        print("Uso: python extract_cities.py <ruta_region>")
        print("Ejemplo: python extract_cities.py ../regions/europa")
        sys.exit(1)

    region_path = sys.argv[1]
    cities = extract_cities_from_region(region_path)

    print("=" * 70)
    print(f"CIUDADES EN: {region_path}")
    print("=" * 70)

    # Agrupar por pais
    by_country = {}
    for c in cities:
        country = c['country']
        if country not in by_country:
            by_country[country] = []
        by_country[country].append(c['city'])

    total = 0
    for country, city_list in sorted(by_country.items()):
        safe_print(f"\n{country} ({len(city_list)} ciudades):")
        for city in city_list:
            safe_print(f"  - {city}")
        total += len(city_list)

    print("\n" + "=" * 70)
    print(f"TOTAL: {len(by_country)} paises, {total} ciudades")
    print("=" * 70)

if __name__ == "__main__":
    main()
