"""
Analiza las estructuras de los JSON de barrios para entender cómo procesarlos
"""
import json
from pathlib import Path
from collections import defaultdict

padron_path = Path(__file__).parent
json_files = sorted(padron_path.glob('*_noviembre.json'))

print(f"Analizando {len(json_files)} archivos JSON...")
print("="*70)

structures = defaultdict(list)

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    barrio = json_file.stem.replace('_noviembre', '')

    # Encontrar keys que contienen eventos
    event_keys = []
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            event_keys.append(f"{key} (array[{len(value)}])")
        elif isinstance(value, dict):
            # Buscar eventos en objetos anidados
            for subkey, subvalue in value.items():
                if isinstance(subvalue, list) and len(subvalue) > 0:
                    event_keys.append(f"{key}.{subkey} (array[{len(subvalue)}])")

    if event_keys:
        structure_str = " | ".join(event_keys)
        structures[structure_str].append(barrio)
        print(f"{barrio:25} -> {structure_str}")
    else:
        print(f"{barrio:25} -> VACIO")

print("\n" + "="*70)
print("RESUMEN DE ESTRUCTURAS:")
print("="*70)

for i, (structure, barrios) in enumerate(structures.items(), 1):
    print(f"\nEstructura {i}: {structure}")
    print(f"Barrios ({len(barrios)}): {', '.join(barrios)}")
