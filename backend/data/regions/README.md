# Regions - Metadata Geográfica Global

**Propósito**: Estructura normalizada de países y ciudades principales para scraping de eventos.

**Última actualización**: 2025-11-12

---

## 📂 Estructura

```
regions/
├── europa/
│   ├── europa-occidental/
│   │   ├── francia.json
│   │   ├── alemania.json
│   │   ├── belgica.json
│   │   ├── paises-bajos.json
│   │   ├── suiza.json
│   │   └── austria.json
│   ├── europa-meridional/
│   │   ├── espana.json
│   │   ├── italia.json
│   │   ├── grecia.json
│   │   └── portugal.json
│   ├── europa-septentrional/
│   │   ├── reino-unido.json
│   │   ├── irlanda.json
│   │   ├── suecia.json
│   │   ├── noruega.json
│   │   ├── dinamarca.json
│   │   └── finlandia.json
│   ├── europa-oriental/
│   │   ├── polonia.json
│   │   ├── chequia.json
│   │   ├── hungria.json
│   │   └── rumania.json
│   └── europa-nororiental/
│       └── rusia.json
├── latinamerica/
│   ├── sudamerica/
│   │   ├── argentina.json    (con barrios de Buenos Aires)
│   │   ├── brasil.json
│   │   ├── chile.json
│   │   ├── colombia.json
│   │   ├── peru.json
│   │   ├── venezuela.json
│   │   ├── ecuador.json
│   │   ├── uruguay.json
│   │   ├── paraguay.json
│   │   └── bolivia.json
│   ├── centroamerica/
│   │   ├── mexico.json
│   │   ├── panama.json
│   │   ├── costa-rica.json
│   │   └── guatemala.json
│   └── caribe/
│       ├── puerto-rico.json
│       ├── cuba.json
│       └── republica-dominicana.json
└── norteamerica/
    └── norteamerica/
        ├── usa.json
        └── canada.json
```

---

## 📋 Formato de Archivos

### Estructura Estándar

Cada archivo JSON contiene:
- **country**: Nombre del país
- **country_code**: Código ISO 3166-1 alpha-2
- **region**: Región geográfica
- **cities**: Array con las 3 ciudades principales

```json
{
  "country": "España",
  "country_code": "ES",
  "region": "Europa Meridional",
  "cities": [
    {
      "name": "Madrid",
      "latitude": 40.4168,
      "longitude": -3.7038
    },
    {
      "name": "Barcelona",
      "latitude": 41.3874,
      "longitude": 2.1686
    },
    {
      "name": "Valencia",
      "latitude": 39.4699,
      "longitude": -0.3763
    }
  ]
}
```

### Estructura Especial: Argentina

Argentina incluye un nivel adicional con los barrios principales de Buenos Aires:

```json
{
  "country": "Argentina",
  "country_code": "AR",
  "region": "Sudamérica",
  "cities": [
    {
      "name": "Buenos Aires",
      "latitude": -34.6037,
      "longitude": -58.3816,
      "barrios": [
        {"name": "Palermo", "latitude": -34.5889, "longitude": -58.4267},
        {"name": "Recoleta", "latitude": -34.5883, "longitude": -58.3958},
        {"name": "San Telmo", "latitude": -34.6217, "longitude": -58.3719},
        {"name": "Puerto Madero", "latitude": -34.6095, "longitude": -58.3634},
        {"name": "Belgrano", "latitude": -34.5630, "longitude": -58.4539},
        {"name": "Caballito", "latitude": -34.6195, "longitude": -58.4393},
        {"name": "Retiro", "latitude": -34.5957, "longitude": -58.3770},
        {"name": "Almagro", "latitude": -34.6056, "longitude": -58.4195},
        {"name": "Villa Crespo", "latitude": -34.5996, "longitude": -58.4390},
        {"name": "Núñez", "latitude": -34.5447, "longitude": -58.4570}
      ]
    },
    {
      "name": "Córdoba",
      "latitude": -31.4201,
      "longitude": -64.1888
    },
    {
      "name": "Rosario",
      "latitude": -32.9468,
      "longitude": -60.6393
    }
  ]
}
```

---

## 🌍 Cobertura Geográfica

### Europa (19 países)

#### Europa Occidental (6 países)
- Francia (París, Lyon, Marsella)
- Alemania (Berlín, Múnich, Hamburgo)
- Bélgica (Bruselas, Amberes, Gante)
- Países Bajos (Ámsterdam, Róterdam, La Haya)
- Suiza (Zúrich, Ginebra, Basilea)
- Austria (Viena, Salzburgo, Innsbruck)

#### Europa Meridional (4 países)
- España (Madrid, Barcelona, Valencia)
- Italia (Roma, Milán, Nápoles)
- Grecia (Atenas, Salónica, Patras)
- Portugal (Lisboa, Oporto, Braga)

#### Europa Septentrional (6 países)
- Reino Unido (Londres, Manchester, Edimburgo)
- Irlanda (Dublín, Cork, Galway)
- Suecia (Estocolmo, Gotemburgo, Malmö)
- Noruega (Oslo, Bergen, Trondheim)
- Dinamarca (Copenhague, Aarhus, Odense)
- Finlandia (Helsinki, Espoo, Tampere)

#### Europa Oriental (4 países)
- Polonia (Varsovia, Cracovia, Gdansk)
- Chequia (Praga, Brno, Ostrava)
- Hungría (Budapest, Debrecen, Szeged)
- Rumania (Bucarest, Cluj-Napoca, Timișoara)

#### Europa Nororiental (1 país)
- Rusia (Moscú, San Petersburgo, Kazán)

### Latinoamérica (17 países)

#### Sudamérica (10 países)
- Argentina (Buenos Aires + barrios, Córdoba, Rosario)
- Brasil (São Paulo, Río de Janeiro, Brasília)
- Chile (Santiago, Valparaíso, Concepción)
- Colombia (Bogotá, Medellín, Cali)
- Perú (Lima, Cusco, Arequipa)
- Venezuela (Caracas, Maracaibo, Valencia)
- Ecuador (Quito, Guayaquil, Cuenca)
- Uruguay (Montevideo, Punta del Este, Colonia)
- Paraguay (Asunción, Ciudad del Este, Encarnación)
- Bolivia (La Paz, Santa Cruz, Cochabamba)

#### Centroamérica (4 países)
- México (Ciudad de México, Guadalajara, Monterrey)
- Panamá (Ciudad de Panamá, Colón, David)
- Costa Rica (San José, Heredia, Cartago)
- Guatemala (Ciudad de Guatemala, Antigua, Quetzaltenango)

#### Caribe (3 países)
- Puerto Rico (San Juan, Ponce, Bayamón)
- Cuba (La Habana, Santiago de Cuba, Varadero)
- República Dominicana (Santo Domingo, Punta Cana, Santiago)

### Norteamérica (2 países)

- Estados Unidos (New York, Los Angeles, Chicago)
- Canadá (Toronto, Montreal, Vancouver)

---

## 📊 Estadísticas

- **Total continentes**: 3 (Europa, Latinoamérica, Norteamérica)
- **Total regiones**: 12
- **Total países**: 38
- **Total ciudades principales**: 114 (3 por país)
- **Barrios de Buenos Aires**: 10

---

## 🎯 Uso

### 1. Listar todas las ciudades de un país

```bash
# Leer archivo de país
cat europa/europa-meridional/espana.json | jq '.cities[].name'
```

**Output**:
```
"Madrid"
"Barcelona"
"Valencia"
```

### 2. Obtener coordenadas de una ciudad

```bash
cat europa/europa-occidental/francia.json | jq '.cities[] | select(.name == "París")'
```

**Output**:
```json
{
  "name": "París",
  "latitude": 48.8566,
  "longitude": 2.3522
}
```

### 3. Listar todos los países de una región

```bash
ls europa/europa-occidental/*.json | xargs -I {} basename {} .json
```

**Output**:
```
francia
alemania
belgica
paises-bajos
suiza
austria
```

### 4. Acceder a barrios de Buenos Aires (caso especial)

```bash
cat latinamerica/sudamerica/argentina.json | jq '.cities[] | select(.name == "Buenos Aires") | .barrios[].name'
```

**Output**:
```
"Palermo"
"Recoleta"
"San Telmo"
"Puerto Madero"
...
```

### 5. Contar total de ciudades por continente

```bash
# Europa
find europa -name "*.json" -exec cat {} \; | jq '.cities | length' | awk '{sum+=$1} END {print sum}'

# Latinoamérica
find latinamerica -name "*.json" -exec cat {} \; | jq '.cities | length' | awk '{sum+=$1} END {print sum}'

# Norteamérica
find norteamerica -name "*.json" -exec cat {} \; | jq '.cities | length' | awk '{sum+=$1} END {print sum}'
```

---

## 🔧 Uso en Scripts de Scraping

### Ejemplo: Iterar por todas las ciudades de Europa

```python
import json
from pathlib import Path

regions_dir = Path("backend/data/regions/europa")

for region_folder in regions_dir.iterdir():
    if region_folder.is_dir():
        for country_file in region_folder.glob("*.json"):
            with open(country_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                country = data['country']
                cities = data['cities']

                for city in cities:
                    print(f"Scrapeando: {city['name']}, {country}")
                    # Aquí iría la lógica de scraping
```

### Ejemplo: Generar lista de ciudades para Gemini

```python
import json
from pathlib import Path

def get_cities_list(region_path):
    """
    Genera lista de ciudades en formato:
    Ciudad, País
    """
    cities_list = []

    for country_file in Path(region_path).rglob("*.json"):
        with open(country_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            country = data['country']

            for city in data['cities']:
                cities_list.append(f"{city['name']}, {country}")

    return cities_list

# Uso:
europa_cities = get_cities_list("backend/data/regions/europa")
print("\n".join(europa_cities[:10]))  # Primeras 10
```

**Output**:
```
París, Francia
Lyon, Francia
Marsella, Francia
Berlín, Alemania
Múnich, Alemania
...
```

---

## ✅ Validación

### Verificar que todos los JSONs son válidos

```bash
find . -name "*.json" -type f -exec sh -c 'python -m json.tool "$1" > /dev/null || echo "Error en: $1"' _ {} \;
```

### Verificar estructura de campos obligatorios

```bash
for file in $(find . -name "*.json" -type f); do
    if ! jq -e '.country and .country_code and .region and .cities' "$file" > /dev/null 2>&1; then
        echo "Campos faltantes en: $file"
    fi
done
```

---

## 🌟 Características

1. **Normalizada**: Estructura consistente en todos los archivos
2. **Escalable**: Fácil agregar nuevos países/ciudades
3. **Completa**: Cubre los principales destinos de eventos del mundo
4. **Coordenadas GPS**: Todas las ciudades tienen lat/long
5. **Códigos ISO**: Country codes estándar ISO 3166-1
6. **Caso especial**: Argentina con barrios de Buenos Aires

---

## 📝 Mantenimiento

### Agregar un nuevo país

1. Identificar región apropiada
2. Crear archivo `pais.json` con estructura estándar
3. Incluir 3 ciudades principales con coordenadas
4. Actualizar este README

### Agregar ciudades a un país existente

⚠️ **NO RECOMENDADO**: Mantener solo 3 ciudades principales por país.

Si es absolutamente necesario, editar el JSON y agregar al array `cities`.

### Agregar una nueva región

1. Crear carpeta en el continente correspondiente
2. Agregar archivos de países
3. Actualizar estructura y estadísticas en README

---

## 🚨 Reglas Importantes

1. **Solo 3 ciudades por país** (excepto Argentina con barrios)
2. **Formato de nombres**: kebab-case para archivos (ej: `costa-rica.json`)
3. **Nombres de ciudades**: Sin acentos en nombres de archivo, con acentos en JSON
4. **Coordenadas**: Siempre incluir latitude y longitude
5. **Country codes**: Usar ISO 3166-1 alpha-2 (2 letras)

---

## 📚 Referencias

- **ISO 3166-1 Codes**: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
- **Coordenadas**: OpenStreetMap / Google Maps
- **División regional Europa**: Naciones Unidas (UN M49)
- **División regional América**: Organización de Estados Americanos (OEA)

---

## 🎯 Próximos Pasos

- [ ] Agregar Asia (5 regiones, ~20 países)
- [ ] Agregar África (5 regiones, ~20 países)
- [ ] Agregar Oceanía (4 regiones, ~10 países)
- [ ] Considerar agregar ciudades secundarias (opcional)
- [ ] Integrar con API de geocoding para validación automática

---

**Última actualización**: 2025-11-12
**Total archivos**: 38 países + 1 README
**Mantenedor**: Sistema automatizado de scraping
