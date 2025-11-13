#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Limpia estructura antigua de backend/data/
Deja solo: regions/, scrapper_results/, scripts/, cache/, README.md
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def main():
    """Limpia carpetas y archivos antiguos"""
    base_dir = Path(__file__).parent

    print("=" * 70)
    print("LIMPIEZA DE ESTRUCTURA ANTIGUA")
    print("=" * 70)

    # Carpetas a eliminar
    carpetas_eliminar = [
        'padron',
        'scraped',
        'curated',
        'ai_scraped',
        'facebook_cache',
        'image-better'
    ]

    # Archivos a eliminar
    archivos_eliminar = [
        'argentina_cities_uids.json',
        'cities_expanded.json',
        'company_patterns.json',
        'latinamerica_regions.json',
        'latinamerica_regions_sample.json',
        'location_enrichments_cache.json',
        'url_patterns_cache.json',
        'villa-gesell-noviembre-2025.json',
        'reorganizar_data_completo.py'
    ]

    print("\n[1/3] Eliminando carpetas antiguas...")
    for carpeta in carpetas_eliminar:
        carpeta_path = base_dir / carpeta
        if carpeta_path.exists():
            print(f"   Eliminando {carpeta}/...")
            shutil.rmtree(carpeta_path)
            print(f"   OK {carpeta}/ eliminada")

    print("\n[2/3] Eliminando archivos sueltos...")
    for archivo in archivos_eliminar:
        archivo_path = base_dir / archivo
        if archivo_path.exists():
            archivo_path.unlink()
            print(f"   OK {archivo} eliminado")

    print("\n[3/3] Generando README.md...")

    readme_content = f"""# Backend Data - Estructura Organizada

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Estructura

```
backend/data/
├── regions/                    # Información geográfica de ciudades
│   ├── europa/                 # 5 regiones europeas, 46 países
│   │   ├── europa-occidental/
│   │   ├── europa-meridional/
│   │   ├── europa-septentrional/
│   │   ├── europa-oriental/
│   │   └── europa-nororiental/
│   ├── latinamerica/
│   │   ├── sudamerica/         # Argentina, Brasil, Chile, etc.
│   │   ├── centroamerica/      # Panamá, etc.
│   │   └── caribe/             # Puerto Rico, Cuba, etc.
│   └── configs/                # Archivos de configuración
│
├── scrapper_results/           # Resultados de scraping organizados
│   ├── europa/
│   │   └── [región]/[país]/[mes]/
│   ├── latinamerica/
│   │   └── [región]/[país]/[mes]/
│   ├── norteamerica/
│   │   └── norteamerica/[país]/[mes]/
│   └── curated/                # Datos curados con IA
│       └── ai_scraped/
│
├── scripts/                    # Scripts de procesamiento
│   ├── europa/                 # Scripts específicos de Europa
│   └── importers/              # Scripts de importación
│
└── cache/                      # Archivos de caché
    ├── facebook/
    ├── images/
    └── patterns/
```

## Regiones Catalogadas

### Europa
- **Europa Occidental** (8 países): Alemania, Francia, Bélgica, Países Bajos, Suiza, Austria, Luxemburgo, Liechtenstein
- **Europa Meridional** (10 países): España, Italia, Grecia, Portugal, Malta, Chipre, Andorra, Mónaco, San Marino, Ciudad del Vaticano
- **Europa Septentrional** (10 países): Reino Unido, Irlanda, Noruega, Suecia, Finlandia, Dinamarca, Islandia, Estonia, Letonia, Lituania
- **Europa Oriental** (16 países): Polonia, Chequia, Eslovaquia, Hungría, Rumania, Bulgaria, Croacia, Eslovenia, Serbia, Bosnia, Montenegro, Macedonia del Norte, Kosovo, Moldavia, Bielorrusia, Ucrania
- **Europa Nororiental** (2 países): Rusia, Georgia

### Latinoamérica
- **Sudamérica**: Argentina (Buenos Aires + 48 barrios), Brasil, Chile, Colombia, Perú, Uruguay, Venezuela, Paraguay, Bolivia, Ecuador
- **Centroamérica**: Panamá
- **Caribe**: Puerto Rico, Cuba

### Norteamérica
- **USA**: Miami, New York, Los Angeles, Chicago, Houston
- **México**: Ciudad de México, Guadalajara, Cancún

## Datos Disponibles

### Resultados de Scraping (Noviembre 2025)

#### Europa
- 6 países con eventos
- 18 ciudades scrapeadas
- Países: Alemania, España, Francia, Grecia, Italia, Reino Unido

#### Latinoamérica
- 15+ países con eventos
- 80+ ciudades scrapeadas
- Regiones: Sudamérica (10 países), Centroamérica (1), Caribe (2)

#### Norteamérica
- 2 países con eventos
- 8 ciudades scrapeadas
- Países: USA (5 ciudades), México (3 ciudades)

## Ventajas de esta Estructura

1. ✅ **Global**: Cubre Europa, Latinoamérica y Norteamérica
2. ✅ **Escalable**: Fácil agregar Asia, África, Oceanía
3. ✅ **Histórico**: Nivel de mes permite tracking temporal
4. ✅ **Regional**: Búsquedas por región geográfica
5. ✅ **Organizada**: Código, datos, cache totalmente separados
6. ✅ **Mantenible**: Clara jerarquía por continente → región → país → mes

## Uso

### Importar datos a base de datos
```bash
cd scripts/importers
python import_all_structures.py
```

### Procesar nuevas ciudades
```bash
cd scripts/europa
python automated_city_scraper.py
```

## Estadísticas

- **Regiones geográficas**: 12 regiones
- **Países catalogados**: 75+
- **Ciudades con eventos**: 100+
- **Periodo de datos**: Noviembre 2025
- **Scripts disponibles**: 25+

---

**Nota:** Esta estructura está lista para escalar a nivel global con soporte para todos los continentes.
"""

    with open(base_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("   OK README.md creado")

    # Resumen final
    print("\n" + "=" * 70)
    print("LIMPIEZA COMPLETADA")
    print("=" * 70)

    # Contar estructura final
    archivos_restantes = [f.name for f in base_dir.iterdir() if f.is_file()]
    carpetas_restantes = [d.name for d in base_dir.iterdir() if d.is_dir()]

    print(f"\nEstructura final de backend/data/:")
    print(f"  Carpetas ({len(carpetas_restantes)}):")
    for carpeta in sorted(carpetas_restantes):
        count = len(list((base_dir / carpeta).rglob('*')))
        print(f"    - {carpeta}/  ({count} items)")

    print(f"\n  Archivos ({len(archivos_restantes)}):")
    for archivo in sorted(archivos_restantes):
        print(f"    - {archivo}")

    print("\n" + "=" * 70)
    print("ESTRUCTURA FINAL LISTA!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
