#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UTILIDAD: Mapeo dinamico Ciudad -> Pais

Lee los archivos JSON de backend/data/regions/ para construir
el mapeo sin hardcodear nada.

BUSCA 'cities' DE FORMA RECURSIVA - funciona con cualquier estructura:
- regions, provinces, communities, states, etc.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
import unicodedata

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent.parent  # backend/data
REGIONS_DIR = DATA_DIR / 'regions'

# Cache global para el mapeo
_CIUDAD_PAIS_CACHE: Dict[str, str] = {}
_CIUDAD_PROVINCIA_CACHE: Dict[str, str] = {}  # ciudad -> provincia/state
_CACHE_LOADED = False


def normalize_city_name(name: str) -> str:
    """
    Normaliza nombre de ciudad para busqueda:
    - Minusculas
    - Sin acentos
    - Sin guiones/espacios extras
    """
    if not name:
        return ''

    # Minusculas
    name = name.lower().strip()

    # Remover acentos
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')

    # Normalizar separadores
    name = name.replace('-', ' ').replace('_', ' ')
    name = ' '.join(name.split())  # Multiples espacios -> uno

    return name


def extract_cities_recursive(data, country: str, current_province: str = None) -> List[tuple]:
    """
    Extrae ciudades de cualquier estructura JSON de forma recursiva.
    Busca 'cities' en cualquier nivel del JSON, sin importar
    si esta bajo 'regions', 'provinces', 'communities', 'states', etc.

    Returns:
        List of tuples: (city_name, province_name)
    """
    cities_found = []

    if isinstance(data, dict):
        # Detectar si este nivel es una provincia/state/region
        province_name = data.get('name', current_province)

        # Si este dict tiene 'cities', extraerlas con su provincia
        if 'cities' in data:
            for city in data['cities']:
                if isinstance(city, dict) and 'name' in city:
                    cities_found.append((city['name'], province_name))

        # Buscar recursivamente en todos los valores
        for key, value in data.items():
            # Si es una lista de estados/provincias/regiones, pasar el contexto
            if key in ('states', 'provinces', 'regions', 'communities', 'departments'):
                cities_found.extend(extract_cities_recursive(value, country, current_province))
            else:
                cities_found.extend(extract_cities_recursive(value, country, province_name))

    elif isinstance(data, list):
        # Buscar en cada elemento de la lista
        for item in data:
            cities_found.extend(extract_cities_recursive(item, country, current_province))

    return cities_found


def load_regions_cache():
    """
    Carga todos los archivos JSON de regions/ y construye el mapeo ciudad->pais y ciudad->provincia
    Busca 'cities' de forma RECURSIVA, sin importar la estructura del JSON.
    """
    global _CIUDAD_PAIS_CACHE, _CIUDAD_PROVINCIA_CACHE, _CACHE_LOADED

    if _CACHE_LOADED:
        return

    if not REGIONS_DIR.exists():
        print(f"Warning: Regions directory not found at {REGIONS_DIR}")
        _CACHE_LOADED = True
        return

    # Buscar todos los JSON recursivamente
    json_files = list(REGIONS_DIR.glob('**/*.json'))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            country = data.get('country', '')
            if not country:
                continue

            # Extraer ciudades de forma recursiva (sin importar estructura)
            # Ahora retorna tuplas: (city_name, province_name)
            cities_with_provinces = extract_cities_recursive(data, country)

            for city_name, province_name in cities_with_provinces:
                if city_name:
                    # Agregar variante normalizada
                    normalized = normalize_city_name(city_name)
                    _CIUDAD_PAIS_CACHE[normalized] = country

                    # Guardar provincia si existe
                    if province_name:
                        _CIUDAD_PROVINCIA_CACHE[normalized] = province_name

                    # Tambien agregar sin espacios
                    no_spaces = normalized.replace(' ', '')
                    if no_spaces != normalized:
                        _CIUDAD_PAIS_CACHE[no_spaces] = country
                        if province_name:
                            _CIUDAD_PROVINCIA_CACHE[no_spaces] = province_name

        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    _CACHE_LOADED = True
    print(f"[OK] Loaded {len(_CIUDAD_PAIS_CACHE)} cities from {len(json_files)} region files")


def get_pais_from_ciudad(ciudad: str) -> str:
    """
    Obtiene el pais basandose en la ciudad.
    Lee dinamicamente de los archivos de regiones.

    Args:
        ciudad: Nombre de la ciudad (puede tener acentos, mayusculas, etc.)

    Returns:
        Nombre del pais o 'Unknown' si no se encuentra
    """
    # Cargar cache si no esta cargado
    load_regions_cache()

    # Normalizar ciudad para busqueda
    normalized = normalize_city_name(ciudad)

    # Buscar en cache
    return _CIUDAD_PAIS_CACHE.get(normalized, 'Unknown')


def get_provincia_from_ciudad(ciudad: str) -> str:
    """
    Obtiene la provincia/state basandose en la ciudad.
    Lee dinamicamente de los archivos de regiones.

    Args:
        ciudad: Nombre de la ciudad (puede tener acentos, mayusculas, etc.)

    Returns:
        Nombre de la provincia/state o None si no se encuentra
    """
    # Cargar cache si no esta cargado
    load_regions_cache()

    # Normalizar ciudad para busqueda
    normalized = normalize_city_name(ciudad)

    # Buscar en cache
    return _CIUDAD_PROVINCIA_CACHE.get(normalized, None)


def get_all_cities() -> Dict[str, str]:
    """
    Retorna todo el mapeo ciudad->pais

    Returns:
        Dict con {ciudad_normalizada: pais}
    """
    load_regions_cache()
    return _CIUDAD_PAIS_CACHE.copy()


# Test
if __name__ == '__main__':
    print("=" * 60)
    print("TEST: region_utils.py - Mapeo dinamico Ciudad -> Pais + Provincia")
    print("=" * 60)

    # Cargar
    load_regions_cache()

    # Test algunas ciudades
    test_cities = [
        'Paris', 'Buenos Aires', 'buenosaires',
        'Barcelona', 'Sevilla', 'Madrid',
        'Berlin', 'Amsterdam', 'Roma',
        'Lisboa', 'Londres', 'Mendoza',
        'Cordoba', 'Florianopolis', 'Florianópolis',
        'São Paulo', 'Rio de Janeiro',
        'Ciudad Inexistente'
    ]

    print("\nResultados:")
    for city in test_cities:
        pais = get_pais_from_ciudad(city)
        provincia = get_provincia_from_ciudad(city)
        status = "[OK]" if pais != 'Unknown' else "[??]"
        prov_str = provincia if provincia else "N/A"
        print(f"  {status} {city:25} -> {pais:15} | Provincia: {prov_str}")
