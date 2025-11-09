# Post-Scraping: Siguientes Pasos

**Estado**: Scraping completado el 2025-11-09
**Archivos generados**: 48 JSON (uno por barrio de Buenos Aires)
**Fuente**: Gemini AI

---

## 📊 Datos Recopilados

Se han generado 48 archivos JSON con información de eventos de noviembre 2025 para todos los barrios de Buenos Aires:

- **Formato**: `{barrio}_noviembre.json`
- **Estructura**: eventos_ferias_festivales + recitales_shows_fiestas
- **Metadatos**: barrio, comuna, zona, fecha_consulta, característica

---

## 🔄 Próximos Pasos Recomendados

### 1. **Importar a Base de Datos**

Crear script para importar los eventos a la base de datos MySQL del proyecto:

```python
# Ejemplo: import_events_from_padron.py
import json
from pathlib import Path

def import_barrio_events(barrio_file):
    with open(barrio_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Procesar eventos_ferias_festivales
    for evento in data.get('eventos_ferias_festivales', []):
        # INSERT INTO events (...)
        pass

    # Procesar recitales_shows_fiestas
    for recital in data.get('recitales_shows_fiestas', []):
        # INSERT INTO events (...)
        pass
```

**Ubicación sugerida**: `backend/scripts/import_padron_events.py`

---

### 2. **Normalizar Fechas**

Algunos eventos tienen fechas en formato texto ("Viernes 14 y Sábado 15 de Noviembre"). Crear parser para normalizar:

```python
def normalize_date(fecha_str: str) -> str:
    """
    Convierte descripciones de fecha a formato YYYY-MM-DD

    Ejemplos:
    - "Viernes 14 de Noviembre" -> "2025-11-14"
    - "Hasta el Sábado 15 de Noviembre" -> "2025-11-15"
    - "2025-11-09" -> "2025-11-09" (ya normalizado)
    """
    # Implementar lógica de parsing
    pass
```


```python
async def geocode_address(address: str) -> tuple:
    """
    Convierte dirección a coordenadas lat/lng

    Ejemplo:
    "Hipódromo de Palermo (Av. del Libertador 4001)"
    -> (-34.5589, -58.4183)
    """
    pass
```

---

### 4. **Categorización**

Crear sistema de categorías consistente:

**Categorías detectadas**:
- gastronomia
- cultural / cultural-religioso
- tecnologia / tech
- cine
- deportes / deportes-cultura
- teatro / teatro-show
- rock / música / electrónica

**Mapeo sugerido**:
```python
CATEGORY_MAPPING = {
    'gastronomia': 'food',
    'tecnologia': 'tech',
    'tech': 'tech',
    'cine': 'entertainment',
    'teatro': 'entertainment',
    'teatro-show': 'entertainment',
    'rock': 'music',
    'cultural': 'culture',
    'deportes': 'sports',
}
```

---

### 5. **Validación de Datos**

Crear script de validación para detectar:

- ✅ Fechas válidas
- ✅ Coordenadas válidas (después de geocoding)
- ✅ Categorías reconocidas
- ✅ Campos obligatorios presentes
- ⚠️ Eventos duplicados
- ⚠️ Fechas pasadas

```bash
python scripts/validate_padron_events.py
```

---


### 7. **Actualización Mensual**

El script `process_barrios.py` puede reutilizarse cada mes:

```bash
# Diciembre 2025
python backend/data/padron/process_barrios.py --mes diciembre

# Enero 2026
python backend/data/padron/process_barrios.py --mes enero
```

**Mejora sugerida**: Modificar script para aceptar parámetro `--mes`

---

### 8. **Dashboard de Análisis**

Crear visualizaciones:

- **Mapa de calor**: Barrios con más eventos
- **Gráfico temporal**: Distribución de eventos por fecha
- **Categorías populares**: Qué tipo de eventos hay más
- **Cobertura por comuna**: Eventos por comuna (1-15)

**Herramientas**:
- Frontend: Chart.js, D3.js, Mapbox GL
- Backend endpoint: `/api/stats/barrios`

---

### 9. **Limpieza de Archivos Temporales**

Una vez importados a la DB, mover archivos JSON a carpeta de backup:

```bash
mkdir -p backend/data/padron/backup/2025-11/
mv backend/data/padron/*_noviembre.json backend/data/padron/backup/2025-11/
```

---

### 10. **Integración con Frontend**

Agregar filtro por barrio en la UI:

**Componente sugerido**: `BarrioFilter.tsx`

```typescript
interface BarrioFilterProps {
  onBarrioSelect: (barrio: string, comuna: number) => void;
}

// Permite filtrar eventos por barrio/comuna
<BarrioFilter onBarrioSelect={(barrio) => {
  fetchEvents({ barrio, location: 'Buenos Aires' })
}} />
```

---

## 📝 Script de Importación Completo (Ejemplo)

```python
#!/usr/bin/env python3
"""
Import events from padron JSON files to MySQL database
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
import re

async def import_all_barrios():
    """Importa todos los barrios a la base de datos"""

    padron_path = Path(__file__).parent
    json_files = list(padron_path.glob('*_noviembre.json'))

    print(f"📂 Encontrados {len(json_files)} archivos JSON")

    total_imported = 0

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        barrio = data['barrio']
        comuna = data['comuna']

        # Importar eventos
        eventos = data.get('eventos_ferias_festivales', [])
        recitales = data.get('recitales_shows_fiestas', [])

        for evento in eventos:
            # TODO: INSERT INTO events
            total_imported += 1

        for recital in recitales:
            # TODO: INSERT INTO events
            total_imported += 1

        print(f"✅ {barrio}: {len(eventos) + len(recitales)} eventos")

    print(f"\n🎉 Total importado: {total_imported} eventos")

if __name__ == '__main__':
    asyncio.run(import_all_barrios())
```

---

## 🔍 Análisis Preliminar

**Barrios con más eventos** (basado en datos de noviembre):
1. 🥇 Palermo - Centro cultural y de entretenimiento
2. 🥈 Recoleta - Eventos culturales y gastronómicos
3. 🥉 San Telmo - Eventos artísticos y turísticos

**Barrios residenciales** (menos eventos anunciados):
- Villa Luro, Villa Ortúzar, Villa Pueyrredón, Villa Real, etc.
- Nota: Eventos barriales suelen anunciarse con poca anticipación

---

## 📞 Contacto y Mantenimiento

**Script principal**: `process_barrios.py`
**Documentación**: `readme.md`
**Progreso**: `progreso.md`

Para re-ejecutar scraping o actualizar datos:
```bash
cd backend/data/padron
python process_barrios.py
```

---

## ✅ TRABAJO EN PROGRESO - Script de Importación a BD

**Fecha**: 2025-11-09
**Archivos creados**:
- `preview_inserts.py` - Preview de INSERT statements sin ejecutarlos
- `import_to_database.py` - Script real de importación (en desarrollo)

### 🔧 Funcionalidades Implementadas

#### 1. **Normalización de Fechas**

El script normaliza fechas en diferentes formatos:

```python
# Ejemplos de normalización:
"2025-11-09" → "2025-11-09" (ya normalizado)
"Jueves 13 de Noviembre" → "2025-11-13"
"Sábado 15 y Domingo 16" → "2025-11-15" (toma el primero)
"Todos los Domingos" → None (evento recurrente)
"Hasta el Sábado 15" → "2025-11-15"
"Diario" → None (evento recurrente)
```

**Implementación**:
- Mapeo de meses en español a números
- Extracción de días con regex `\b([1-9]|[12]\d|3[01])\b`
- Detección de eventos recurrentes

#### 2. **Normalización de Horarios**

```python
# Ejemplos:
"12:00" → "12:00" (ya normalizado)
"A partir de las 18:00 hs" → "18:00"
"Consultar agenda" → None
"Todo el día" → None
```

#### 3. **Categorización Automática**

Categorías mapeadas:
- `gastronomia` → `gastronomia`
- `cultural` / `cultural-religioso` → `cultural`
- `musica` / `rock` / `jazz` → `musica`
- `cine` → `cine`
- `deportes` / `deportes-cultura` → `deportes`
- `tecnologia` / `tech` → `tecnologia`
- `feria` / `artesanias` → `ferias`
- `teatro` / `teatro-show` → `teatro`
- Otros → `otros`

#### 4. **Extracción de Precios**

```python
# Ejemplos:
"gratuito" / "gratis" → (0.0, True)
"pago" / "variable" → (None, False)
"$1500" → (1500.0, False)
"Gratis entrada" → (0.0, True)
```

#### 5. **Asignación de Imágenes**

Uso de Picsum Photos con seed único por evento:

```python
# Genera URLs consistentes basadas en la descripcion del evento

https://picsum.photos/800/600?random=244
https://picsum.photos/800/600?random=785
https://picsum.photos/800/600?random=63
```

**Ventajas**:
- Mismo evento siempre tiene misma imagen
- No requiere almacenamiento local


### 📊 Ejemplos de INSERT Generados

#### Evento: Festival JOY (Palermo)

```sql
INSERT INTO events (title, description, start_date, start_time, end_time, venue_name, venue_address, latitude, longitude, category, price, is_free, image_url, source)
VALUES (
  'Festival JOY',
  'Más de 35 propuestas gastronómicas de todo tipo (clásicas, innovadoras, cocina de bodegón, asiática, etc.). Entrada libre y gratuita',
  '2025-11-09',
  '12:00',
  '23:00',
  'Hipódromo de Palermo (Av. del Libertador 4001)',
  'Hipódromo de Palermo (Av. del Libertador 4001)',
  -34.6037,
  -58.3816,
  'gastronomia',
  0.0,
  TRUE,
  'https://picsum.photos/800/600?random=244',
  'Gemini AI - Padrón Palermo'
);
```

#### Evento: Virginia Innocenti (San Telmo)

```sql
INSERT INTO events (title, description, start_date, start_time, end_time, venue_name, venue_address, latitude, longitude, category, price, is_free, image_url, source)
VALUES (
  'Virginia Innocenti - Canta a Gabo Ferro',
  'Concierto dedicado a Gabo Ferro y otras cositas nuestras',
  '2025-11-09',
  '21:00',
  NULL,
  'La Carbonera',
  'Carlos Calvo 299',
  -34.6037,
  -58.3816,
  'musica',
  NULL,
  FALSE,
  'https://picsum.photos/800/600?random=487',
  'Gemini AI - Padrón San Telmo'
);
```

#### Evento Recurrente: Feria de San Telmo

```sql
INSERT INTO events (title, description, start_date, start_time, end_time, venue_name, venue_address, latitude, longitude, category, price, is_free, image_url, source)
VALUES (
  'Feria de San Telmo',
  'Feria tradicional de antigüedades y artesanías con shows de tango y arte callejero',
  NULL,  -- Evento recurrente sin fecha específica
  NULL,
  NULL,
  'Plaza Dorrego y Calle Defensa',
  'Plaza Dorrego y Calle Defensa',
  -34.6037,
  -58.3816,
  'cultural',
  NULL,
  FALSE,
  'https://picsum.photos/800/600?random=108',
  'Gemini AI - Padrón San Telmo'
);
```

---

### 📈 Estadísticas del Preview (3 barrios ejemplo)

#### Palermo
- Total eventos: 9
- Con fecha específica: 9
- Eventos gratuitos: 3
- Categorías: deportes, gastronomia, tecnologia, teatro, cine, cultural, musica

#### Recoleta
- Total eventos: 11
- Con fecha específica: 7
- Eventos recurrentes: 4
- Eventos gratuitos: 11 (todos!)
- Categorías: cultural

#### San Telmo
- Total eventos: 9
- Con fecha específica: 7
- Eventos recurrentes: 2
- Eventos gratuitos: 0
- Categorías: cultural, musica, cine

---

### 🚀 Cómo Ejecutar

#### 1. Preview de INSERT statements (sin ejecutar):

```bash
cd backend/data/padron
python preview_inserts.py
```

Muestra:
- Normalización de datos
- INSERT SQL generados
- Estadísticas por barrio
- NO inserta nada en la BD

#### 2. Importación real (próximo paso):

```bash
cd backend/data/padron
python import_to_database.py
```

**Requisitos**:
- `.env` con `DB_POOL` configurado
- MySQL corriendo
- Tabla `events` creada

---

### ⚠️ Problemas Detectados y Soluciones

#### Problema 1: Encoding en Windows
**Error**: `UnicodeEncodeError: 'charmap' codec can't encode character`
**Solución**: Eliminados emojis del output del script

#### Problema 2: Parsing de fechas en español
**Error**: `ValueError: time data 'noviembre' does not match format '%B'`
**Solución**: Mapeo manual de meses en español a números

#### Problema 3: Eventos recurrentes
**Ejemplo**: "Todos los Domingos", "Diario"
**Solución**: `start_date = NULL` para eventos sin fecha específica



### 📁 Estructura de Archivos

```
backend/data/padron/
├── barrios-buenos-aires.json      # Lista de 48 barrios
├── prompt.md                       # Prompt usado con Gemini
├── process_barrios.py              # Script de scraping automático
├── preview_inserts.py              # Preview de INSERT (creado hoy)
├── import_to_database.py           # Importación real (en desarrollo)
├── readme.md                       # Documentación del proceso
├── progreso.md                     # Estado del scraping
├── postscrap.md                    # Este archivo
├── palermo_noviembre.json          # Eventos de Palermo
├── recoleta_noviembre.json         # Eventos de Recoleta
├── san-telmo_noviembre.json        # Eventos de San Telmo
└── ... (45 archivos más)
```

---

**Última actualización**: 2025-11-09 18:30
