# Backend Data - Estructura Organizada

**Última actualización:** 2025-11-12 01:44

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
