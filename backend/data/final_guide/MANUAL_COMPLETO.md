# 📖 MANUAL COMPLETO - SISTEMA ELÁSTICO DE SCRAPING DE EVENTOS

**Versión:** 1.2
**Fecha:** 2025-11-23
**Sistema:** Independiente de sitios e independiente de regiones

---

## ⚡ CHECKLIST RÁPIDO - COPIAR Y PEGAR

### 🔴 REGLA #1: LEER ESTE DOCUMENTO PRIMERO
Antes de ejecutar CUALQUIER comando, lee este documento completo.

---

### Para scrapear UNA ciudad nueva:

#### FASE 1 - SCRAPING (Gemini/Felo)
```
1. Ir a: https://felo.ai o http://gemini.google.com

2. Usar EXACTAMENTE este prompt (reemplazar {CIUDAD, PAIS}):

   me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {CIUDAD, PAIS} desde hoy hasta las las proximas semanas, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, precio y alguna info extra que tengas!

3. Copiar respuesta completa
4. Guardar en: backend/data/scrapper_results/raw/{sitio}/{ciudad}_YYYY-MM-DD.txt
```

#### FASE 2 - PARSING + IMÁGENES (🤖 CON IA)
```bash
cd backend/data/final_guide/scripts && python parse_raw.py
```
> **Características:**
> - Usa IA (Ollama/Grok/OpenAI) para parsear CUALQUIER formato
> - Extrae ciudad, país, provincia automáticamente
> - Busca imágenes con Google Images API
> - Categoriza eventos con IA
>
> **Requisitos:**
> - `ollama serve` corriendo, o GROK_API_KEY/OPENAI_API_KEY en .env
> - GOOGLE_API_KEY y GOOGLE_CX en .env (para imágenes)
>
> **Opciones:**
> - `--file archivo.txt` - Procesa solo un archivo
> - `--no-images` - Omite búsqueda de imágenes (más rápido)
> - `--dry-run` - Solo muestra qué se procesaría

#### FASE 3 - IMPORT MYSQL
```bash
cd backend/data/scripts && python auto_import.py
```

## 🎯 FILOSOFÍA DEL SISTEMA

Este sistema está diseñado para ser **100% elástico y configurable**:

- ✅ **Independiente de sitios**: Agregar nuevos scrapers sin modificar código core
- ✅ **Independiente de regiones**: Funciona con cualquier país/ciudad/barrio
- ✅ **Fases separadas**: Scrape → Parse → Import (cada fase independiente)
- ✅ **Configurable**: Todos los parámetros en archivos de configuración
- ✅ **Escalable**: De 1 ciudad a 100+ ciudades sin cambios de arquitectura

---

## 📂 ESTRUCTURA DE ARCHIVOS

```
backend/data/
├── final_guide/                    # 📚 GUÍAS Y SCRIPTS MAESTROS
│   ├── MANUAL_COMPLETO.md         # Este archivo
│   ├── config/
│   │   ├── sites.json             # Configuración de sitios a scrapear
│   │   └── regions.json           # Configuración de regiones
│   ├── scripts/
│   │   │
│   │   │   # === MÓDULOS COMPARTIDOS ===
│   │   ├── region_utils.py        # 🌍 Mapeo dinámico Ciudad→País→Provincia (lee de regions/)
│   │   ├── event_utils.py         # 🏷️ Categorización y normalización de eventos
│   │   │
│   │   │   # === SCRIPTS POR FUENTE ===
│   │   ├── scrape_gemini.js       # Scraping: Instrucciones Puppeteer para Gemini
│   │   ├── parse_gemini.py        # Parsing: RAW (tabs) → JSON para Gemini
│   │   │
│   │   ├── scrape_felo.js         # Scraping: Instrucciones Puppeteer para Felo
│   │   ├── parse_felo.py          # Parsing: RAW (TSV o líneas) → JSON para Felo
│   │   │
│   │   ├── scrape_grok.js         # Scraping: Puppeteer para Grok (DISABLED - captcha)
│   │   │
│   │   │   # === SCRIPTS GENERALES ===
│   │   ├── fase4_import.py        # FASE 3: Import a MySQL
│   │   └── pipeline_completo.py   # Pipeline automatizado
│   │
│   └── readme.md                   # Referencias rápidas
│
├── reports/                        # FASE 5: Reportes HTML generados
│   └── eventos_2025-11-23.html
│
├── scrapper_results/
│   ├── raw/                        # FASE 1: Respuestas crudas
│   │   ├── gemini/
│   │   │   └── buenosaires_2025-11-22.txt
│   │   └── felo/
│   │       └── cordoba_2025-11-22.txt
│   │
│   └── parsed/                     # FASE 2: JSON estructurados
│       ├── gemini/
│       │   └── buenosaires_2025-11-22.json
│       └── felo/
│           └── cordoba_2025-11-22.json
│
└── regions/                        # Definición de regiones
    └── latinamerica/
        └── sudamerica/
            └── argentina.json
```

---

## 🌍 MÓDULOS COMPARTIDOS

### 1. region_utils.py - Mapeo Ciudad→País→Provincia

Mapea **dinámicamente** ciudad → país → provincia leyendo los archivos JSON de `backend/data/regions/`.

**Características:**
- Sin hardcodeo: Lee de los archivos de regiones existentes
- Recursivo: Funciona con cualquier estructura (regions, provinces, communities, states)
- Normalizado: Maneja acentos, mayúsculas, guiones automáticamente
- Cache: Carga una vez, reutiliza en toda la sesión

**Uso:**
```python
from region_utils import get_pais_from_ciudad, get_provincia_from_ciudad

pais = get_pais_from_ciudad('Paris')           # -> 'Francia'
pais = get_pais_from_ciudad('Barcelona')       # -> 'España'
pais = get_pais_from_ciudad('Florianopolis')   # -> 'Brasil'

provincia = get_provincia_from_ciudad('Barcelona')     # -> 'Cataluña'
provincia = get_provincia_from_ciudad('Florianopolis') # -> 'Santa Catarina'
provincia = get_provincia_from_ciudad('Mendoza')       # -> 'Mendoza'
```

**Agregar nuevas ciudades:**
Editar el archivo JSON en `backend/data/regions/`:
- regions/europa/europa-occidental/francia.json
- regions/latinamerica/sudamerica/argentina.json

---

### 2. event_utils.py - Categorización y Normalización

Funciones compartidas para categorizar eventos y normalizar fechas.

**Funciones:**
- `categorize_event(nombre, descripcion)` - Retorna (category, subcategory)
- `normalize_fecha(fecha_str)` - Convierte fechas a formato YYYY-MM-DD

**Categorías disponibles:**
| Category | Subcategories |
|----------|---------------|
| music | rock, pop, jazz, electronic, folk, classical, hiphop, other |
| sports | football, basketball, tennis, running, other |
| cultural | theater, museum, exhibition, literature, cinema, other |
| nightlife | party, club, bar, other |
| entertainment | comedy, circus, magic, other |
| food | restaurant, festival, market, other |
| tech | conference, hackathon, meetup, other |
| other | general |

**Uso:**
```python
from event_utils import categorize_event, normalize_fecha

# Categorización automática por keywords
categorize_event('Concierto de Rock', 'Banda de rock')  # -> ('music', 'rock')
categorize_event('SC21K', 'Media maratón 21km')         # -> ('sports', 'running')
categorize_event('Hans Zimmer', 'Concierto orquestal')  # -> ('music', 'classical')

# Normalización de fechas
normalize_fecha('8 noviembre 2025')       # -> '2025-11-08'
normalize_fecha('Del 7 al 9 de noviembre') # -> '2025-11-07'
```

**⚠️ IMPORTANTE:** Todos los parsers (`parse_felo.py`, `parse_gemini.py`) y `auto_import.py` usan estas funciones compartidas. NO duplicar código.

---

## 📜 SCRIPTS POR FUENTE

### Principio fundamental:
**CADA FUENTE TIENE 2 ARCHIVOS:**
1. `scrape_{fuente}.js` - Instrucciones para Puppeteer MCP (selectores, pasos)
2. `parse_{fuente}.py` - Parser específico para el formato de respuesta de esa fuente

### 📁 Gemini
| Archivo | Descripción |
|---------|-------------|
| `scrape_gemini.js` | Selectores: `.ql-editor`, `button[aria-label='Enviar mensaje']` |
| `parse_gemini.py` | Parsea formato TABLA con tabs (N° \t Nombre \t Descripción \t ...) |

### 📁 Felo
| Archivo | Descripción |
|---------|-------------|
| `scrape_felo.js` | Selectores: `textarea`, `button[aria-label="Send"]`, `.prose` |
| `parse_felo.py` | Parsea formato TSV (tabs) o LÍNEAS (auto-detecta) |

### 📁 Grok (DISABLED)
| Archivo | Descripción |
|---------|-------------|
| `scrape_grok.js` | Selectores documentados pero NO USAR - tiene captcha Cloudflare |

### ⚠️ IMPORTANTE:
- `parse_felo.py` auto-detecta el formato (TSV con tabs o línea por línea)
- `parse_gemini.py` parsea tablas con tabs
- Ambos usan `region_utils.py` para mapear ciudad → país dinámicamente

---

## 🔧 CONFIGURACIÓN

### 1. Archivo `config/sites.json`

Define QUÉ sitios scrapear y CÓMO hacerlo:

```json
{
  "ai_scrapers": [
    {
      "id": "gemini",
      "name": "Google Gemini",
      "url": "https://gemini.google.com",
      "method": "puppeteer",
      "selectors": {
        "input": ".ql-editor",
        "submit": "button[aria-label='Enviar mensaje']",
        "response": ".model-response-text"
      },
      "wait_time": 15,
      "enabled": true
    },
    {
      "id": "felo",
      "name": "Felo AI",
      "url": "https://felo.ai",
      "method": "puppeteer",
      "selectors": {
        "input": "textarea[placeholder*='search']",
        "submit": "button[type='submit']",
        "response": ".answer-content"
      },
      "wait_time": 20,
      "enabled": true
    },
    {
      "id": "grok",
      "name": "Grok",
      "url": "https://grok.com",
      "method": "puppeteer",
      "selectors": {
        "input": "textarea",
        "submit": "button[aria-label='Send']",
        "response": ".response-text"
      },
      "wait_time": 15,
      "enabled": false,
      "disabled_reason": "Captcha de Cloudflare no se puede automatizar"
    }
  ],

  "traditional_scrapers": [
    {
      "id": "buenosaliens",
      "name": "Buenos Aliens Agenda",
      "url": "https://www.buenosaliens.com/#agenda",
      "method": "selenium",
      "selectors": {
        "event_cards": ".event-item",
        "title": "h3.event-title",
        "date": ".event-date",
        "venue": ".event-venue"
      },
      "enabled": true
    }
  ]
}
```

### 2. Archivo `config/regions.json`

Define DÓNDE scrapear (reutiliza estructura existente):

```json
{
  "source": "../regions/latinamerica/sudamerica/argentina.json",
  "selection": {
    "mode": "all",
    "cities": ["Buenos Aires", "Córdoba", "Rosario"],
    "include_barrios": true
  }
}
```

### 3. Archivo `config/prompts.json`

Define el PROMPT para cada tipo de scraper:

```json
{
  "ai_scrapers": {
    "default_template": "me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} desde hoy hasta las las proximas semanas, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, precio y alguna info extra que tengas!",

    "variations": {
      "gemini": "me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} desde hoy hasta las las proximas semanas, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, precio y alguna info extra que tengas!",

      "felo": "me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} desde hoy hasta las las proximas semanas, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, precio y alguna info extra que tengas!",

      "grok": "me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} desde hoy hasta las las proximas semanas, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, precio y alguna info extra que tengas!"
    }
  }
}
```

---

## 🚀 FASES DEL PROCESO

### FASE 1: SCRAPING (Obtener respuestas crudas)

**Objetivo**: Navegar a cada sitio y guardar respuestas RAW sin procesar

**Método**: Usar Puppeteer MCP siguiendo las instrucciones de `scrape_{fuente}.js`

**Scripts de referencia**:
| Fuente | Script | Descripción |
|--------|--------|-------------|
| Gemini | `scrape_gemini.js` | Selectores y pasos para gemini.google.com |
| Felo | `scrape_felo.js` | Selectores y pasos para felo.ai |
| Grok | `scrape_grok.js` | ⚠️ DISABLED - captcha Cloudflare |


**Proceso manual con Puppeteer MCP**:
```javascript
// 1. Navegar (ejemplo Gemini)
mcp__puppeteer__puppeteer_navigate({ url: "https://gemini.google.com" })

// 2. Llenar prompt
mcp__puppeteer__puppeteer_fill({ selector: ".ql-editor", value: "eventos en Buenos Aires..." })

// 3. Click enviar
mcp__puppeteer__puppeteer_click({ selector: "button[aria-label='Enviar mensaje']" })

// 4. Esperar y extraer
// Esperar 15-30 segundos
mcp__puppeteer__puppeteer_evaluate({ script: "document.querySelector('.model-response-text')?.innerText" })

// 5. Guardar en: raw/{fuente}/{ciudad}_{fecha}.txt
```

**Salida**: Archivos `.txt` en `scrapper_results/raw/{site_id}/{ciudad}_{fecha}.txt`

**Ejemplo de salida**:
```
scrapper_results/raw/gemini/buenosaires_2025-11-22.txt
scrapper_results/raw/felo/cordoba_2025-11-22.txt
```

---

### FASE 2: PARSING (Convertir RAW a JSON estructurado)

**Objetivo**: Leer archivos RAW y convertirlos a JSON con estructura estándar

**Scripts por fuente**:
| Fuente | Parser | Formato que procesa |
|--------|--------|---------------------|
| Gemini | `parse_gemini.py` | Tablas con tabs (N° \t Nombre \t Descripción...) |
| Felo | `parse_felo.py` | Líneas con prefijos (Descripción: ...\nFecha: ...) |

**Comandos**:
```bash
# Parsear archivos de Gemini (formato tabla)
cd backend/data/final_guide/scripts
python parse_gemini.py

# Parsear archivos de Felo (formato líneas)
python parse_felo.py

# Con opciones
python parse_gemini.py --reparse     # Re-parsear todo
python parse_gemini.py --debug       # Mostrar detalles
```

**⚠️ IMPORTANTE - Elegir el parser correcto**:
- Si el archivo RAW tiene tabs (`\t`) entre campos → usar `parse_gemini.py`
- Si el archivo RAW tiene líneas tipo `Descripción: ...` → usar `parse_felo.py`
- `parse_felo.py` también procesa archivos de Gemini que vengan en formato líneas

**Salida**: Archivos `.json` en `scrapper_results/parsed/{site_id}/{ciudad}_{fecha}.json`

**Estructura JSON estándar**:
```json
[
  {
    "nombre": "Festival de Jazz en Palermo",
    "descripcion": "Gran festival de jazz al aire libre",
    "fecha": "2025-11-20",
    "lugar": "Parque 3 de Febrero",
    "direccion": "Av. del Libertador 3260",
    "barrio": "Palermo",
    "precio": "Gratis",
    "ciudad": "Buenos Aires",
    "provincia": "Ciudad Autónoma de Buenos Aires",
    "neighborhood": "Palermo",
    "category": "music",
    "subcategory": "jazz",
    "pais": "Argentina",
    "es_gratis": true,
    "source": "gemini"
  }
]
```

**⚠️ CAMPOS OBLIGATORIOS generados automáticamente por los parsers:**
- `pais`: Detectado dinámicamente desde `region_utils.py`
- `provincia`: Detectado dinámicamente desde `region_utils.py`
- `category/subcategory`: Inferidos desde `event_utils.py`

---

### FASE 3: IMPORT (Insertar en MySQL con detección de duplicados)

**Objetivo**: Leer JSONs parseados e insertar en MySQL evitando duplicados

**Script**: `backend/data/scripts/auto_import.py`

**⚠️ IMPORTANTE**: Este script usa las funciones compartidas de `event_utils.py` y `region_utils.py`

**Comando**:
```bash
# Importar TODO lo que está en parsed/
cd backend/data/scripts
python auto_import.py

# Ver qué se importaría sin hacerlo
python auto_import.py --dry-run

# Reiniciar log y reprocesar todo
python auto_import.py --reset
```

**Detección de duplicados**:
- ✅ **Duplicado exacto**: Mismo título, ciudad y fecha
- ✅ **Duplicado parcial**: Títulos con 80%+ palabras en común
- ✅ **Log detallado**: Muestra qué pasó con cada evento

**Ejemplo de salida**:
```
================================================================================
✨ IMPORTACIÓN COMPLETADA
================================================================================

📊 Archivos procesados: 3
✅ Eventos insertados: 42
⏭️  Eventos duplicados (ya existían): 18
   • Duplicados exactos (título completo igual): 12
   • Duplicados parciales (títulos similares ~80%): 6
❌ Errores: 2

📈 Tasa de éxito: 95.5%
================================================================================
```

---

### FASE 4: IMÁGENES (Agregar imágenes a eventos)

**Objetivo**: Buscar y agregar imágenes de Google para cada evento

**Script**: `backend/data/scripts/update_event_images.js`

**Requisitos en `.env`**:
```bash
GOOGLE_API_KEY=tu_api_key_de_google
GOOGLE_CX=tu_custom_search_engine_id
```

**Cómo obtener las credenciales**:
1. **GOOGLE_API_KEY**:
   - Ir a https://console.cloud.google.com/apis/credentials
   - Crear una API Key
   - Habilitar "Custom Search API"
2. **GOOGLE_CX**:
   - Ir a https://programmablesearchengine.google.com/
   - Crear un motor de búsqueda
   - Copiar el "Search engine ID"

**Comando**:
```bash
cd backend/data/scripts
node update_event_images.js
```

**Lógica de búsqueda (Triple Fallback)**:
1. **Intento 1**: `{título completo} {venue} {ciudad} event`
2. **Intento 2**: `{primeras 3 palabras del título} {ciudad} event`
3. **Intento 3**: `{venue} {ciudad}`

**Rate Limiting**:
- 1 segundo entre cada búsqueda
- Si Google devuelve 429 (rate limit), guarda progreso y se detiene
- Los eventos que ya tienen `image_url` se skipean

**Ejemplo de salida**:
```
======================================================================
🖼️  AGREGANDO IMÁGENES A EVENTOS
======================================================================
📂 Carpeta base: scrapper_results/parsed

🔍 Fuentes encontradas: gemini, felo

📁 Procesando fuente: GEMINI
──────────────────────────────────────────────────────────────────────
📊 5 archivos JSON encontrados en gemini

📄 Procesando: buenosaires_2025-11-22.json
  [1/20] Festival del Sándwich...
    ✅ Imagen (título completo)
  [2/20] FUTCON 2025...
    ✅ Imagen (título reducido)
  💾 18 imágenes agregadas

======================================================================
🎉 PROCESO COMPLETADO
======================================================================
📁 Fuentes procesadas: 2 (gemini, felo)
📊 Archivos procesados: 11
🖼️  Total imágenes agregadas: 145
======================================================================
```

**⚠️ LÍMITES DE GOOGLE CUSTOM SEARCH API**:
- **Gratis**: 100 búsquedas/día
- **Pago**: $5 por cada 1000 búsquedas adicionales
- **Recomendación**: Ejecutar después de cada batch de parsing, no todo junto

---

### FASE 4.5: LIMPIAR URLs INVÁLIDAS (CRÍTICO)

**Problema descubierto**: Google Custom Search API devuelve URLs que **NO son públicamente accesibles**:

| Patrón de URL | Problema |
|---------------|----------|
| `x-raw-image:///...` | URLs internas de Google, no son HTTP válidas |
| `lookaside.fbsbx.com` | Facebook bloquea hotlinking |
| `lookaside.instagram.com` | Instagram bloquea hotlinking |
| `tiktok.com/api/img` | TikTok requiere autenticación |
| `p16-common-sign.tiktokcdn` | CDN de TikTok con tokens temporales |

**Síntoma**: Las imágenes se ven en la consola como "agregadas" pero NO cargan en el HTML.

**Script de limpieza**: `scripts/fix_invalid_images.py`

**Comando**:
```bash
cd backend/data/scripts

# 1. Limpiar URLs inválidas (borra image_url de eventos con URLs malas)
python fix_invalid_images.py

# 2. Re-ejecutar búsqueda de imágenes (ahora buscará nuevas para los limpiados)
node update_event_images.js
```

**Qué hace el script**:
1. Recorre todos los JSONs en `parsed/`
2. Detecta URLs con patrones inválidos
3. **Elimina** el campo `image_url` de esos eventos
4. Guarda el JSON actualizado
5. Ahora `update_event_images.js` los detectará como "sin imagen" y buscará nuevas

**Ejemplo de salida**:
```
============================================================
LIMPIANDO URLs DE IMAGENES INVALIDAS
============================================================

[DIR] Procesando: gemini

  [FILE] buenosaires_2025-11-22.json
  - Limpiando: Festival del Sandwich...
    URL invalida: x-raw-image:///cff9756fc87d8e92752bb...
  - Limpiando: Dia Nacional del Kimchi...
    URL invalida: https://lookaside.instagram.com/seo/...
  [OK] 8 URLs limpiadas

============================================================
TOTAL URLs LIMPIADAS: 58
============================================================
```

**⚠️ IMPORTANTE**: Siempre ejecutar `fix_invalid_images.py` DESPUÉS de `update_event_images.js` para limpiar las URLs malas, y luego re-ejecutar `update_event_images.js` para buscar reemplazos.

---

### FASE 5: GENERAR REPORTE HTML

**Objetivo**: Crear un reporte visual de todos los eventos con imágenes

**Script**: `scripts/generar_reporte_html.py`

**Comando**:
```bash
cd backend/data/scripts
python generar_reporte_html.py
```

**Salida**: `reports/eventos_YYYY-MM-DD.html`

**Para ver el reporte con imágenes** (importante por CORS):
```bash
cd backend/data/reports
python -m http.server 8080
# Abrir: http://localhost:8080/eventos_2025-11-23.html
```

**⚠️ NOTA**: Si abres el HTML directamente desde el explorador de archivos (`file://`), muchas imágenes no cargarán por restricciones de CORS. Siempre servir con un servidor HTTP.

---

## 🔄 FLUJO COMPLETO RECOMENDADO

### Resumen de las 6 Fases

| Fase | Script | Ubicación | Input | Output |
|------|--------|-----------|-------|--------|
| **FASE 1** | Puppeteer MCP + `scrape_{fuente}.js` | `final_guide/scripts/` | Prompt + Ciudad | `raw/{fuente}/{ciudad}_{fecha}.txt` |
| **FASE 2** | `parse_gemini.py` / `parse_felo.py` | `final_guide/scripts/` | Archivos RAW | `parsed/{fuente}/{ciudad}_{fecha}.json` |
| **FASE 3** | `auto_import.py` | `data/scripts/` | Archivos JSON | Registros en MySQL |
| **FASE 4** | `update_event_images.js` | `data/scripts/` | Archivos JSON | JSON con `image_url` agregado |
| **FASE 4.5** | `fix_invalid_images.py` | `data/scripts/` | JSON con URLs malas | JSON con URLs válidas |
| **FASE 5** | `generar_reporte_html.py` | `data/scripts/` | Archivos JSON | `reports/eventos_YYYY-MM-DD.html` |

**Módulos compartidos** (en `final_guide/scripts/`):
- `region_utils.py` - Mapeo ciudad→país→provincia
- `event_utils.py` - Categorización y normalización

### Flujo paso a paso (RECOMENDADO)

```bash
# ═══════════════════════════════════════════════════════════════════
# FASE 1: SCRAPING (usar Puppeteer MCP manualmente)
# ═══════════════════════════════════════════════════════════════════
# Ver instrucciones en final_guide/scripts/scrape_gemini.js o scrape_felo.js
# Guardar respuesta en: scrapper_results/raw/{fuente}/{ciudad}_{fecha}.txt

# ═══════════════════════════════════════════════════════════════════
# FASE 2: PARSING (usa event_utils.py y region_utils.py automáticamente)
# ═══════════════════════════════════════════════════════════════════
cd backend/data/final_guide/scripts

# Si el RAW tiene formato tabla (tabs):
python parse_gemini.py

# Si el RAW tiene formato líneas (Descripción: ...):
python parse_felo.py

# ═══════════════════════════════════════════════════════════════════
# FASE 3: IMPORT A MYSQL
# ═══════════════════════════════════════════════════════════════════
cd backend/data/scripts
python auto_import.py           # Importar nuevos
python auto_import.py --dry-run # Ver qué se importaría
python auto_import.py --reset   # Reimportar todo

# ═══════════════════════════════════════════════════════════════════
# FASE 4: IMÁGENES (buscar imágenes de Google)
# ═══════════════════════════════════════════════════════════════════
cd backend/data/scripts
node update_event_images.js      # Agregar imágenes a JSONs

# ═══════════════════════════════════════════════════════════════════
# FASE 4.5: LIMPIAR URLs INVÁLIDAS (CRÍTICO - siempre ejecutar)
# ═══════════════════════════════════════════════════════════════════
python fix_invalid_images.py     # Elimina URLs que no cargan (Facebook, Instagram, TikTok, x-raw)
node update_event_images.js      # Re-buscar imágenes para los limpiados

# ═══════════════════════════════════════════════════════════════════
# FASE 5: GENERAR REPORTE HTML
# ═══════════════════════════════════════════════════════════════════
python generar_reporte_html.py   # Genera reports/eventos_YYYY-MM-DD.html

# Para ver el reporte (necesario por CORS):
cd ../reports && python -m http.server 8080
# Abrir: http://localhost:8080/eventos_2025-11-23.html
```

### Orden de rotación de fuentes (evitar detección)

```
Ciudad 1 → Gemini
Ciudad 2 → Felo
Ciudad 3 → Gemini
Ciudad 4 → Felo
...
```

**⚠️ NO usar Grok** - tiene captcha de Cloudflare que no se puede automatizar

---

## 📊 MONITOREO Y LOGS

### Logs automáticos generados:

```
logs/
├── fase1_scrape_2025-11-14.log      # Qué se scrapeó, errores, tiempos
├── fase2_parse_2025-11-14.log       # Qué se parseó, eventos por archivo
└── fase3_import_2025-11-14.log      # Detalles de importación, duplicados
```

### Verificar estado del sistema:

```bash
# Ver archivos RAW disponibles
ls backend/data/scrapper_results/raw/*/

# Ver archivos PARSED disponibles
ls backend/data/scrapper_results/parsed/*/

# Ver cuántos eventos hay por fuente
for file in backend/data/scrapper_results/parsed/*/*.json; do
  echo "$file: $(cat "$file" | grep -c '"nombre"') eventos"
done

# Ver distribución de países en la DB
mysql -u root -p events -e "SELECT country, COUNT(*) as cnt FROM events GROUP BY country ORDER BY cnt DESC LIMIT 10;"
```

---

## 🛠️ AGREGAR NUEVOS SITIOS

### Ejemplo: Agregar "Perplexity AI"

**1. Editar `config/sites.json`**:

```json
{
  "id": "perplexity",
  "name": "Perplexity AI",
  "url": "https://perplexity.ai",
  "method": "puppeteer",
  "selectors": {
    "input": "textarea[placeholder*='Ask']",
    "submit": "button[type='submit']",
    "response": ".answer-container"
  },
  "wait_time": 12,
  "enabled": true
}
```

**2. Agregar prompt en `config/prompts.json`**:

```json
"perplexity": "lista eventos en {lugar} este mes con nombre, fecha, lugar y precio"
```

**3. Ejecutar scraping manualmente** usando Puppeteer MCP siguiendo las instrucciones del documento.

**¡Listo!** No hace falta modificar código del parser - usa auto-detección de formato.

---

## 🌎 AGREGAR NUEVAS REGIONES

### Ejemplo: Agregar ciudades de México

**1. Crear archivo de región** (`regions/latinamerica/norteamerica/mexico.json`):

```json
{
  "country": "México",
  "cities": [
    {
      "name": "Ciudad de México",
      "barrios": [
        {"name": "Roma Norte"},
        {"name": "Condesa"},
        {"name": "Polanco"}
      ]
    },
    {
      "name": "Guadalajara",
      "barrios": []
    }
  ]
}
```

**2. Actualizar `config/regions.json`**:

```json
{
  "sources": [
    "../regions/latinamerica/sudamerica/argentina.json",
    "../regions/latinamerica/norteamerica/mexico.json"
  ],
  "selection": {
    "mode": "all"
  }
}
```

**3. Ejecutar scraping manualmente** con Puppeteer MCP y luego:

```bash
# Parsear los archivos RAW
cd backend/data/final_guide/scripts
python parse_felo.py    # Si tiene formato líneas
python parse_gemini.py  # Si tiene formato tabla con tabs
```

---

## ⚙️ CONFIGURACIÓN AVANZADA

### Delays y rate limiting

**En `config/sites.json`**:
```json
{
  "id": "gemini",
  "rate_limit": {
    "requests_per_minute": 3,
    "delay_between_requests": 20,
    "delay_on_error": 60,
    "max_retries": 3
  }
}
```

### Proxy y headers

**En `config/sites.json`**:
```json
{
  "id": "gemini",
  "proxy": {
    "enabled": true,
    "url": "http://proxy.example.com:8080"
  },
  "headers": {
    "User-Agent": "Mozilla/5.0...",
    "Accept-Language": "es-AR,es;q=0.9"
  }
}
```

---

## 🐛 TROUBLESHOOTING

### Problema: Scraping falla con "timeout"

**Solución**: Aumentar `wait_time` en `config/sites.json`

```json
"wait_time": 30  // Aumentar de 15 a 30 segundos
```

### Problema: No se detectan eventos en parsing

**Solución**: Ejecutar con `--debug` para ver el raw text

```bash
cd backend/data/final_guide/scripts
python parse_gemini.py --debug    # Para archivos de Gemini
python parse_felo.py              # Para archivos de Felo (auto-detecta formato)
```

### Problema: Muchos duplicados parciales

**Solución**: Ajustar threshold de similitud en `config/import.json`

```json
{
  "duplicate_detection": {
    "partial_match_threshold": 0.85  // De 0.80 a 0.85 (más estricto)
  }
}
```

---

## 📝 MEJORES PRÁCTICAS

### ✅ HACER:
- Ejecutar FASE 1 completa antes de pasar a FASE 2
- Usar `--dry-run` antes de importar a producción
- Mantener logs por al menos 30 días
- Ejecutar en horarios de bajo tráfico (madrugada)
- Usar delays de 20+ segundos entre AI requests

### ❌ NO HACER:
- Ejecutar las 3 fases simultáneamente (riesgo de bloqueo)
- Modificar archivos RAW manualmente
- Eliminar logs antes de verificar imports
- Scrapear más de 10 ciudades sin delays

---

## 🔮 ROADMAP

**v1.1** (Próxima versión):
- [ ] Soporte para scraping con Bright Data
- [ ] Parser con GPT-4 para mejor extracción
- [ ] Dashboard web para monitoreo
- [ ] Notificaciones por Telegram cuando termina scraping

**v2.0** (Futuro):
- [ ] Auto-scaling según volumen de ciudades
- [ ] Machine learning para detectar duplicados
- [ ] API REST para ejecutar fases remotamente
- [ ] Integración con Google Calendar automática

---

## 📞 SOPORTE

**Logs**: Todos los logs están en `logs/`
**Config**: Toda la config está en `config/`
**Scripts**: Scripts maestros en `scripts/`

---

## 🤖 INSTRUCCIONES ESPECÍFICAS POR SITIO (Puppeteer MCP)

### Configuración General del Browser

```javascript
// SIEMPRE usar ventana incógnito y maximizada para evitar detección
launchOptions: {
  "headless": false,
  "args": ["--incognito", "--start-maximized"]
}
```

**IMPORTANTE**: Rotar el orden de los sitios entre ejecuciones para evitar patrones detectables.

---

### 🔷 GEMINI (gemini.google.com)

**URL**: `https://gemini.google.com`

**Paso a paso**:
1. Navegar a la URL con incógnito + maximizado
2. Esperar 2-3 segundos para que cargue
3. Llenar el campo de texto:
   - Selector: `.ql-editor, textarea, [contenteditable='true']`
4. Hacer clic en enviar:
   - Selector: `button[aria-label='Enviar mensaje']`
5. Esperar 15-30 segundos para la respuesta
6. Extraer texto de respuesta:
   - Buscar elementos con clase `.model-response-text` o `[data-message-author-role="model"]`

**Prompt a usar**:
```
me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} a partir de hoy y las próximas semanas?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas! En formato de tabla con tabs separando las columnas: N°	Nombre del Evento	Descripción	Fecha	Lugar / Dirección	Barrio	Precio (ARS)	Info Extra
```

**Notas**:
- Gemini puede pedir login ocasionalmente - ignorar y usar sin login
- El formato de tabla con tabs facilita el parsing posterior

---

### 🔶 FELO (felo.ai) - PROCESO VERIFICADO ✅

**URL**: `https://felo.ai`

**Configuración del browser**:
```javascript
// IMPORTANTE: Viewport grande para ver toda la interfaz
launchOptions: {
  "headless": false,
  "args": ["--incognito", "--start-maximized", "--window-size=1920,1080"]
}
// Screenshot con width: 1920, height: 1080
```

**Paso a paso VERIFICADO (2025-11-22)**:
1. Navegar a `https://felo.ai` con incógnito + viewport 1920x1080
2. Esperar 2-3 segundos para que cargue
3. Llenar el campo de texto:
   - Selector: `textarea` (campo "Ask anything...")
4. **CRÍTICO**: Hacer clic en el botón de enviar:
   - Selector: `button[aria-label="Send"]` ✅ FUNCIONA
   - ❌ NO usar: `button[class*='bg-primary']` (no funciona)
   - ❌ NO usar: `form.submit()` (recarga la página)
5. **⚠️ POPUP DE SUSCRIPCIÓN**: A veces aparece una página para elegir plan
   - Buscar y hacer clic en el botón que contenga "gratis" o "free"
   - Ver código JavaScript abajo
6. Esperar 20-30 segundos para la respuesta (usa 49 fuentes)
7. Extraer texto de respuesta:
   - Selector: `.prose` o buscar en el contenedor principal
   - La respuesta aparece con formato estructurado (eventos numerados)

**Prompt a usar**:
```
dame por lo menos 20 eventos en {lugar} a partir de hoy y las próximas semanas, necesito nombre, descripción, fecha, lugar, dirección, barrio y precio
```

**Selectores verificados**:
```javascript
// 1. Llenar textarea
await puppeteer_fill({ selector: 'textarea', value: prompt });

// 2. Hacer clic en Send (USAR ESTE)
await puppeteer_click({ selector: 'button[aria-label="Send"]' });

// 3. Extraer respuesta (después de esperar)
const content = document.querySelector('.prose')?.innerText;
```

**Manejo de popup de suscripción**:
```javascript
// Si aparece página de suscripción, buscar botón con "gratis"
const buttons = document.querySelectorAll('button');
for (const btn of buttons) {
  if (btn.textContent.toLowerCase().includes('gratis') ||
      btn.textContent.toLowerCase().includes('free')) {
    btn.click();
    break;
  }
}
```

**Formato de respuesta esperado**:
```
Eventos en {lugar} a partir de hoy

1. Nombre del Evento
Descripción: ...
Fecha: DD de mes de YYYY
Lugar: ...
Dirección: ...
Barrio: ...
Precio: ...

2. Siguiente evento...
```

**Notas importantes**:
- Felo usa 49+ fuentes para buscar información
- La respuesta tarda 15-30 segundos en generarse
- Genera eventos bien estructurados con todos los campos
- NO requiere login para funcionar

**⚠️ PROBLEMAS CONOCIDOS**:
- Felo puede detectar automatización y generar respuestas incompletas
- Si la respuesta se corta antes de los 20 eventos:
  1. Probar manualmente en el navegador
  2. Reducir la frecuencia de screenshots (causan flickering)
  3. Esperar más tiempo entre requests
  4. Alternar con otros sources (Gemini, Grok)

---

### 🟣 GROK (grok.com) - ✅ NO REQUIERE AUTH

**URL**: `https://grok.com`

**Paso a paso**:
1. Navegar a la URL con incógnito + maximizado
2. Esperar 2-3 segundos
3. Llenar el campo de texto:
   - Selector: `textarea`
4. Hacer clic en enviar:
   - Selector: `button[aria-label='Send']`
5. Esperar 15-20 segundos
6. Extraer respuesta:
   - Selector: `.response-text`

**Prompt a usar** (MISMO QUE GEMINI):
```
me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} a partir de hoy y las próximas semanas?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas! En formato de tabla con tabs separando las columnas: N°	Nombre del Evento	Descripción	Fecha	Lugar / Dirección	Barrio	Precio (ARS)	Info Extra
```

**Notas**:
- Grok NO requiere autenticación
- Funciona directamente sin login
- Usar el mismo prompt que Gemini para consistencia

**⚠️ PROBLEMA CONOCIDO**:
- Grok tiene captcha de Cloudflare que NO se puede automatizar con Puppeteer
- El checkbox está en un iframe protegido
- **Solución**: Usar Gemini como alternativa principal hasta resolver

---

### 🌐 BUENOS ALIENS (buenosaliens.com)

**URL**: `https://www.buenosaliens.com/#agenda`

**Tipo**: Scraping tradicional (no AI, solo extraer datos de la página)

**Paso a paso**:
1. Navegar a la URL
2. Esperar que cargue la agenda (5 segundos)
3. Extraer eventos directamente del DOM:
   - Cards de eventos: `.event-item`
   - Título: `h3.event-title`
   - Fecha: `.event-date`
   - Lugar: `.event-venue`

**NO requiere prompt** - es scraping directo de la página.

---

## 🔄 ORDEN DE ROTACIÓN POR LLAMADO

**⚠️ IMPORTANTE: USAR SOLO GEMINI Y FELO (Grok tiene captcha bloqueante)**

Para evitar detección de automatización, rotar el sitio en CADA llamado:

**Ejemplo para Buenos Aires (ciudad con barrios):**
1. Palermo, Buenos Aires → **Gemini**
2. Recoleta, Buenos Aires → **Felo**
3. San Telmo, Buenos Aires → **Gemini**
4. Belgrano, Buenos Aires → **Felo**
... y así alternando

**Ejemplo para ciudades sin barrios:**
1. Buenos Aires → **Gemini**
2. Córdoba → **Felo**
3. Rosario → **Gemini**
4. Mendoza → **Felo**
... y así alternando

**Orden de rotación**: Gemini → Felo → Gemini → Felo (NO usar Grok - tiene captcha)

---

## ⚠️ TROUBLESHOOTING COMÚN

### Problema: Página de suscripción en Felo
**Solución**: Buscar y clickear botón con texto "gratis" o "free"

### Problema: Gemini pide login
**Solución**: Refrescar página o usar nueva ventana incógnito

### Problema: Timeout en respuesta
**Solución**: Aumentar wait_time en config/sites.json

### Problema: Pantalla negra/vacía
**Solución**: La página perdió foco, navegar nuevamente a la URL

---

## 🧹 SCRIPTS DE MANTENIMIENTO

### fix_countries_db.py - Corregir países/provincias en DB existente

Si tienes eventos con países incorrectos (códigos ISO, Unknown, etc.), ejecutar:

```bash
cd backend/data/scripts
python fix_countries_db.py
```

**Qué hace:**
1. Convierte códigos ISO a nombres completos (ES → España, DE → Alemania)
2. Corrige ciudades truncadas (Sao → São Paulo, Rio → Rio de Janeiro)
3. Usa `region_utils.py` para mapear ciudad → país dinámicamente
4. Agrega columna `province` si no existe y la llena automáticamente

---

**Última actualización**: 2025-11-23
**Versión**: 1.2.0
**Mantenedor**: Sistema de Eventos
