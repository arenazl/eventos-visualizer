<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-11-12 01:55
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-11-12 01:55: Creación de guía completa de scraping
📋 TAGS: #scraping #guide #automation #eventos #apis
-->

# 🕷️ Guía Completa de Scraping de Eventos

Guía práctica paso a paso para obtener eventos de cualquier fuente y región del mundo.

---

## 📋 Índice

1. [Métodos de Scraping](#métodos-de-scraping)
2. [Estructura JSON Esperada](#estructura-json-esperada)
3. [Método 1: APIs Oficiales](#método-1-apis-oficiales)
4. [Método 2: Web Scraping con Puppeteer](#método-2-web-scraping-con-puppeteer)
5. [Método 3: Gemini AI (Recomendado)](#método-3-gemini-ai-recomendado)
6. [Procesamiento Post-Scraping](#procesamiento-post-scraping)
7. [Mejores Prácticas](#mejores-prácticas)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Métodos de Scraping

### Comparación Rápida

| Método | Calidad | Velocidad | Costo | Dificultad | Recomendado |
|--------|---------|-----------|-------|------------|-------------|
| **APIs Oficiales** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | 💰💰 | 🔧 Fácil | ✅ Si hay API |
| **Web Scraping** | ⭐⭐⭐ | ⚡⚡ | 💰 | 🔧🔧🔧 Difícil | ⚠️ Si no hay API |
| **Gemini AI** | ⭐⭐⭐⭐ | ⚡⚡⚡⚡ | 💰 Gratis | 🔧 Muy fácil | ✅✅ **MEJOR** |

---

## 📄 Estructura JSON Esperada

Todos los métodos deben generar JSONs con esta estructura:

### Estructura Base (Recomendada)

```json
{
  "ciudad": "Barcelona",
  "pais": "España",
  "region": "Cataluña",
  "fecha_scraping": "2025-11-12T01:00:00",
  "eventos": [
    {
      "nombre": "Festival Primavera Sound 2025",
      "descripcion": "Festival de música alternativa con artistas internacionales",
      "fecha_inicio": "2025-06-01",
      "fecha_fin": "2025-06-03",
      "venue": "Parc del Fòrum",
      "direccion": "Parc del Fòrum, Barcelona",
      "ciudad": "Barcelona",
      "pais": "España",
      "categoria": "Música",
      "subcategoria": "Festival",
      "precio": "€280",
      "moneda": "EUR",
      "url": "https://primaverasound.com",
      "image_url": "",
      "latitud": 41.4099,
      "longitud": 2.2169,
      "source": "gemini_ai"
    }
  ]
}
```

### Estructura Alternativa (Array Simple)

```json
[
  {
    "titulo": "Concierto de Coldplay",
    "descripcion": "...",
    "fecha_inicio": "2025-12-15",
    "ciudad": "Madrid",
    "pais": "España",
    "venue": "Estadio Santiago Bernabéu",
    "precio": "€120",
    "url": "https://...",
    "categoria": "Música"
  }
]
```

### Campos Obligatorios

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `nombre/titulo` | string | Nombre del evento | "Festival de Jazz 2025" |
| `fecha_inicio` | string | Fecha ISO o DD/MM/YYYY | "2025-11-20" |
| `ciudad` | string | Ciudad del evento | "Barcelona" |
| `pais` | string | País del evento | "España" |

### Campos Opcionales (Pero Recomendados)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `descripcion` | string | Descripción del evento |
| `fecha_fin` | string | Fecha de finalización |
| `venue` | string | Lugar/recinto |
| `direccion` | string | Dirección completa |
| `categoria` | string | Música, Deportes, Cultural, Tech, etc. |
| `precio` | string | Precio en texto o número |
| `moneda` | string | EUR, USD, ARS, etc. |
| `url` | string | URL oficial del evento |
| `image_url` | string | URL de imagen (se agrega después) |
| `latitud` | float | Coordenadas GPS |
| `longitud` | float | Coordenadas GPS |

---

## 🔧 Método 1: APIs Oficiales

### Ventajas
- ✅ Datos estructurados y confiables
- ✅ Actualización en tiempo real
- ✅ Imágenes oficiales incluidas
- ✅ Legal y permitido

### Desventajas
- ❌ Requiere API key (a veces de pago)
- ❌ Rate limiting (límites de requests)
- ❌ Solo cubre eventos de esa plataforma

### APIs Recomendadas

#### 1. Eventbrite API
**Cobertura**: Global, 180+ países

```bash
# Obtener API key:
# 1. Ir a https://www.eventbrite.com/platform/api
# 2. Crear app
# 3. Copiar Private Token

# Configurar en .env:
EVENTBRITE_API_KEY=tu_api_key_aqui
```

**Ejemplo de Request**:
```bash
curl -X GET "https://www.eventbriteapi.com/v3/events/search/?location.address=Barcelona&expand=venue,category" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### 2. Ticketmaster Discovery API
**Cobertura**: USA, Canadá, Europa, México

```bash
# Obtener API key:
# 1. Ir a https://developer.ticketmaster.com/
# 2. Registrarse
# 3. Crear app
# 4. Copiar API Key

# Configurar en .env:
TICKETMASTER_API_KEY=tu_api_key_aqui
```

**Ejemplo de Request**:
```bash
curl "https://app.ticketmaster.com/discovery/v2/events.json?city=Madrid&apikey=YOUR_API_KEY"
```

#### 3. Meetup API
**Cobertura**: Global (eventos comunitarios)

**Ejemplo**: Ver `backend/services/meetup_scraper.py`

### Script de Ejemplo (Eventbrite)

```python
import requests
import json
from datetime import datetime

def scrape_eventbrite(city, country_code='ES'):
    """
    Scrape eventos de Eventbrite

    Args:
        city: Ciudad (ej: "Barcelona")
        country_code: Código país ISO (ej: "ES")

    Returns:
        dict: JSON con estructura esperada
    """
    api_key = os.getenv('EVENTBRITE_API_KEY')
    url = 'https://www.eventbriteapi.com/v3/events/search/'

    params = {
        'location.address': f"{city}, {country_code}",
        'location.within': '25km',
        'expand': 'venue,category',
        'page_size': 50
    }

    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    eventos = []
    for event in data.get('events', []):
        evento = {
            'nombre': event['name']['text'],
            'descripcion': event['description']['text'][:500],
            'fecha_inicio': event['start']['local'],
            'fecha_fin': event['end']['local'],
            'venue': event['venue']['name'] if event.get('venue') else '',
            'direccion': event['venue']['address']['localized_address_display'] if event.get('venue') else '',
            'ciudad': city,
            'pais': country_code,
            'categoria': event['category']['name'] if event.get('category') else 'General',
            'precio': 'Consultar',
            'url': event['url'],
            'image_url': event['logo']['url'] if event.get('logo') else '',
            'source': 'eventbrite_api'
        }
        eventos.append(evento)

    return {
        'ciudad': city,
        'pais': country_code,
        'fecha_scraping': datetime.now().isoformat(),
        'eventos': eventos
    }

# Uso:
resultado = scrape_eventbrite('Barcelona', 'ES')

# Guardar:
with open(f"barcelona_eventbrite_{datetime.now().strftime('%Y%m%d')}.json", 'w', encoding='utf-8') as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)
```

---

## 🌐 Método 2: Web Scraping con Puppeteer

### Cuándo Usar
- ⚠️ Solo si NO existe API oficial
- ⚠️ Para sitios específicos de eventos locales
- ⚠️ Requiere mantenimiento (cambios en el sitio rompen el scraper)

### Herramientas Necesarias

```bash
# Instalar Node.js y dependencias
npm install puppeteer axios cheerio

# O usar Playwright
pip install playwright
playwright install chromium
```

### Script de Ejemplo (Puppeteer)

```javascript
const puppeteer = require('puppeteer');
const fs = require('fs');

async function scrapeSitioLocal(url, ciudad, pais) {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox']
    });

    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'networkidle2' });

    // Extraer eventos (adaptar selectores según sitio)
    const eventos = await page.evaluate(() => {
        const items = Array.from(document.querySelectorAll('.event-item'));

        return items.map(item => ({
            nombre: item.querySelector('.event-title')?.innerText || '',
            descripcion: item.querySelector('.event-description')?.innerText || '',
            fecha_inicio: item.querySelector('.event-date')?.innerText || '',
            venue: item.querySelector('.event-venue')?.innerText || '',
            precio: item.querySelector('.event-price')?.innerText || 'Gratis',
            url: item.querySelector('a')?.href || ''
        }));
    });

    await browser.close();

    // Estructura final
    const resultado = {
        ciudad: ciudad,
        pais: pais,
        fecha_scraping: new Date().toISOString(),
        eventos: eventos.map(e => ({
            ...e,
            ciudad: ciudad,
            pais: pais,
            source: 'web_scraping'
        }))
    };

    // Guardar
    fs.writeFileSync(
        `${ciudad.toLowerCase()}_${Date.now()}.json`,
        JSON.stringify(resultado, null, 2)
    );

    console.log(`✅ ${eventos.length} eventos scrapeados de ${ciudad}`);
    return resultado;
}

// Uso:
scrapeSitioLocal('https://ejemplo-eventos.com/barcelona', 'Barcelona', 'España');
```

### Desafíos Comunes

1. **Selectores cambian**: Sitios web cambian su HTML
2. **Rate limiting**: Bloqueos por demasiadas requests
3. **JavaScript dinámico**: Contenido cargado async
4. **CAPTCHAs**: Protección anti-bot

**Solución**: Usar Método 3 (Gemini AI) en su lugar.

---

## 🤖 Método 3: Gemini AI (Recomendado)

### ¿Por Qué Es el Mejor?

- ✅ **Gratis**: Sin API keys de pago
- ✅ **Rápido**: Obtiene eventos de cualquier ciudad en segundos
- ✅ **Inteligente**: Entiende contexto local y encuentra eventos actuales
- ✅ **Sin mantenimiento**: No depende de HTML/selectores
- ✅ **Global**: Funciona para cualquier ciudad del mundo

### Limitaciones

- ⚠️ Límite de ~10 búsquedas por sesión (pausa 2-4 horas después)
- ⚠️ Calidad variable (revisar eventos generados)
- ⚠️ Fechas a veces genéricas (requiere curación)

### Método Manual (Gemini Web)

#### Paso 1: Ir a Gemini

Acceder a **Gemini** en cualquiera de estas URLs:
- https://gemini.google.com (oficial)
- https://gemini.com (redirect)

O simplemente buscar "Gemini" en Google.

#### Paso 2: Prompt Optimizado

```
Dame 20 eventos reales próximos en [CIUDAD], [PAÍS] en los próximos 30 días.

Incluye solo eventos confirmados con:
- Nombre exacto del evento
- Fecha específica (día/mes/año)
- Lugar/venue específico
- Breve descripción
- Categoría (Música, Deportes, Cultural, Tech, Fiestas)
- Precio aproximado

Formato JSON:
{
  "ciudad": "[CIUDAD]",
  "pais": "[PAÍS]",
  "eventos": [
    {
      "nombre": "...",
      "fecha_inicio": "YYYY-MM-DD",
      "venue": "...",
      "descripcion": "...",
      "categoria": "...",
      "precio": "..."
    }
  ]
}
```

**Ejemplo Real**:
```
Dame 20 eventos reales próximos en Barcelona, España en los próximos 30 días.

Incluye solo eventos confirmados con fecha específica, lugar y descripción.

Formato JSON con campos: nombre, fecha_inicio, venue, descripcion, categoria, precio
```

#### Paso 3: Copiar Respuesta

Gemini responderá con algo como:

```json
{
  "ciudad": "Barcelona",
  "pais": "España",
  "eventos": [
    {
      "nombre": "Primavera Sound 2025",
      "fecha_inicio": "2025-06-01",
      "venue": "Parc del Fòrum",
      "descripcion": "Festival de música alternativa con The Strokes, Lorde...",
      "categoria": "Música",
      "precio": "€280"
    },
    {
      "nombre": "FC Barcelona vs Real Madrid - El Clásico",
      "fecha_inicio": "2025-11-25",
      "venue": "Camp Nou",
      "descripcion": "Partido de LaLiga entre los dos grandes rivales",
      "categoria": "Deportes",
      "precio": "€150-500"
    }
  ]
}
```

#### Paso 4: Guardar JSON

```bash
# Crear archivo
nano barcelona_noviembre.json

# Pegar contenido
# Ctrl+O para guardar
# Ctrl+X para salir
```

### Método Automatizado (Playwright + Gemini)

**Script**: `backend/scripts/gemini_scraper_automated.py`

```bash
# Instalar dependencias
pip install playwright python-dotenv
playwright install chromium

# Configurar credenciales Google
# Editar .env:
GOOGLE_EMAIL=tu_email@gmail.com
GOOGLE_PASSWORD=tu_password

# Ejecutar
cd backend/scripts
python gemini_scraper_automated.py
```

**El script**:
1. Abre Gemini Web en navegador headless
2. Hace login automático
3. Envía prompt para cada ciudad
4. Extrae JSON de respuesta
5. Guarda en `backend/data/ai_scraped/`

### Curación Post-Gemini

**IMPORTANTE**: Eventos de Gemini pueden ser genéricos o con fechas aproximadas.

**Script de Curación**: `backend/automation/curate_ai_events.py`

```bash
cd backend
python automation/curate_ai_events.py --input data/ai_scraped --output data/curated
```

**Qué hace**:
- ✅ Valida que eventos tengan fecha específica
- ✅ Elimina eventos con nombres genéricos ("Concierto de música")
- ✅ Detecta duplicados (85% similitud)
- ✅ Agrega imágenes automáticamente
- ✅ Normaliza formato para DB

---

## ⚙️ Procesamiento Post-Scraping

### Paso 1: Agregar Imágenes Reales

**NUNCA usar Unsplash/Pexels genéricos**. Usar Google Images con título exacto.

```bash
cd backend/data/scripts
node add_images_generic.js scrapper_results/europa
```

**Resultado**:
- Busca cada evento en Google Images
- Extrae primera imagen JPG real
- Agrega campo `image_url` al JSON
- Pausa 2 seg entre requests (evita rate limit)

### Paso 2: Importar a MySQL

```bash
cd backend/data/scripts
python import_generic.py scrapper_results/europa
```

**Resultado**:
- Lee todos los JSONs recursivamente
- Normaliza datos (fechas, precios, categorías)
- Verifica duplicados (título + ciudad + fecha)
- Inserta solo eventos nuevos
- Reporta estadísticas

### Paso 3: Verificar Importación

```sql
-- En MySQL
SELECT
  city,
  COUNT(*) as total_eventos,
  SUM(CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END) as con_imagen
FROM events
GROUP BY city
ORDER BY total_eventos DESC;
```

---

## 📊 Workflow Completo Recomendado

### Para Una Ciudad Nueva

```bash
# 1. Scrapear con Gemini (manual o automatizado)
# → Genera: barcelona_noviembre.json

# 2. Guardar en estructura correcta
mkdir -p backend/data/scrapper_results/europa/europa-meridional/espana/2025-11
mv barcelona_noviembre.json backend/data/scrapper_results/europa/europa-meridional/espana/2025-11/

# 3. Agregar imágenes reales
cd backend/data/scripts
node add_images_generic.js scrapper_results/europa/europa-meridional/espana/2025-11

# 4. Importar a MySQL
python import_generic.py scrapper_results/europa/europa-meridional/espana/2025-11

# 5. Verificar en base de datos
mysql -u root -p eventos_visualizer -e "SELECT COUNT(*) FROM events WHERE city='Barcelona';"
```

### Para Múltiples Ciudades (Región Completa)

```bash
# 1. Scrapear todas las ciudades (Gemini automatizado recomendado)
cd backend/scripts
python gemini_scraper_automated.py
# → Genera múltiples JSONs en data/ai_scraped/

# 2. Curar eventos
cd backend
python automation/curate_ai_events.py --input data/ai_scraped --output data/curated

# 3. Mover a estructura correcta
# (Organizar manualmente en scrapper_results/region/pais/mes/)

# 4. Agregar imágenes a TODA la región
cd backend/data/scripts
node add_images_generic.js scrapper_results/europa

# 5. Importar TODO
python import_generic.py scrapper_results/europa
```

---

## 🎯 Mejores Prácticas

### 1. Nombrado de Archivos

```
✅ BIEN:
barcelona_noviembre.json
madrid_2025-11.json
paris_noviembre_2025.json

❌ MAL:
eventos.json
data.json
scraping_final_v2_real.json
```

### 2. Organización de Carpetas

```
✅ BIEN:
scrapper_results/
└── europa/
    └── europa-meridional/
        └── espana/
            └── 2025-11/
                ├── barcelona_noviembre.json
                ├── madrid_noviembre.json
                └── valencia_noviembre.json

❌ MAL:
data/
├── barcelona.json
├── madrid.json
└── todos_eventos_europa_final.json
```

### 3. Frecuencia de Scraping

- **APIs**: Diario (si hay rate limit generoso)
- **Web Scraping**: Semanal (evita bloqueos)
- **Gemini AI**: Por demanda (límite de sesión)

### 4. Validación de Datos

**SIEMPRE validar antes de importar**:

```python
def validar_evento(evento):
    """Valida que evento tenga datos mínimos"""
    if not evento.get('nombre') or not evento.get('titulo'):
        return False

    if not evento.get('fecha_inicio'):
        return False

    if not evento.get('ciudad') or not evento.get('city'):
        return False

    # Detectar eventos genéricos
    nombres_genericos = ['evento', 'concierto', 'festival', 'partido']
    nombre_lower = evento.get('nombre', '').lower()
    if nombre_lower in nombres_genericos:
        return False

    return True
```

### 5. Detección de Duplicados

**En la base de datos**:
```sql
-- Verificar duplicados antes de importar
SELECT title, city, DATE(start_datetime), COUNT(*)
FROM events
GROUP BY title, city, DATE(start_datetime)
HAVING COUNT(*) > 1;
```

**En los scripts** (ya implementado en `import_generic.py`):
- Verificar título + ciudad + fecha
- Solo insertar si no existe

---

## 🛠️ Troubleshooting

### Problema 1: Gemini da eventos genéricos

**Síntoma**:
```json
{
  "nombre": "Concierto de música",
  "fecha_inicio": "Próximamente"
}
```

**Solución**:
- Mejorar prompt: "Dame EVENTOS CONFIRMADOS con FECHA ESPECÍFICA"
- Agregar: "Incluye nombre exacto del artista/equipo"
- Pausar sesión (límite de 10 búsquedas alcanzado)

### Problema 2: Rate Limiting de Google Images

**Síntoma**: Muchos eventos con "⚠️ Solo logo de Google"

**Solución**:
```javascript
// En add_images_generic.js, aumentar pausa:
await new Promise(resolve => setTimeout(resolve, 4000)); // De 2000 a 4000ms
```

### Problema 3: Eventos duplicados en DB

**Síntoma**: `import_generic.py` reporta "0 insertados, 100 duplicados"

**Causa**: Eventos ya existen en base de datos

**Verificar**:
```bash
python import_generic.py scrapper_results/europa 2>&1 | grep "duplicados"
```

**Si son duplicados reales**: ✅ Todo bien, script funciona correctamente

**Si deberían ser nuevos**: Revisar criterio de duplicados (título + ciudad + fecha)

### Problema 4: Imágenes no se agregan

**Síntoma**: `add_images_generic.js` reporta "0 actualizados"

**Causas posibles**:
1. Eventos ya tienen `image_url`
2. Estructura JSON no reconocida
3. Error en módulo `buscar-primera-imagen.js`

**Debug**:
```bash
node -e "
const data = require('./ruta/al/archivo.json');
const eventos = data.eventos || data;
console.log('Total eventos:', eventos.length);
console.log('Sin imagen:', eventos.filter(e => !e.image_url).length);
"
```

### Problema 5: Script de importación falla

**Síntoma**: Error de MySQL connection

**Solución**:
```python
# Verificar credenciales en import_generic.py:
DB_CONFIG = {
    'host': 'localhost',  # O tu host
    'user': 'root',       # Tu usuario
    'password': 'TuPassword',  # CAMBIAR ESTO
    'database': 'eventos_visualizer',
    'charset': 'utf8mb4'
}
```

---

## 📚 Recursos Adicionales

### Documentación Relacionada

- `backend/data/scripts/README.md` - Guía de scripts genéricos
- `docs/00-INDEX.md` - Índice maestro de documentación
- `PROGRESS_SCRAPING.md` - Progreso de scraping América Latina
- `docs/scraping-gemini-progress.md` - Progreso Gemini AI

### APIs de Eventos

- **Eventbrite**: https://www.eventbrite.com/platform/api
- **Ticketmaster**: https://developer.ticketmaster.com/
- **Meetup**: https://www.meetup.com/api/
- **Facebook Events**: https://developers.facebook.com/docs/graph-api/reference/event/

### Herramientas de Scraping

- **Puppeteer**: https://pptr.dev/
- **Playwright**: https://playwright.dev/
- **Beautiful Soup**: https://www.crummy.com/software/BeautifulSoup/
- **Scrapy**: https://scrapy.org/

### Gemini AI

- **Gemini Web**: https://gemini.google.com
- **Gemini API**: https://ai.google.dev/

---

## 🎯 Checklist de Scraping

Usa esto cada vez que scrapes una nueva región:

- [ ] **Elegir método** (API > Gemini AI > Web Scraping)
- [ ] **Preparar prompt/script** según método
- [ ] **Scrapear eventos** (mínimo 10-15 por ciudad)
- [ ] **Guardar JSON** en estructura correcta (`scrapper_results/`)
- [ ] **Validar estructura** (campos obligatorios presentes)
- [ ] **Curar datos** (si es Gemini AI)
- [ ] **Agregar imágenes** (`node add_images_generic.js`)
- [ ] **Importar a MySQL** (`python import_generic.py`)
- [ ] **Verificar en DB** (count de eventos y con imagen)
- [ ] **Documentar progreso** (actualizar PROGRESS_SCRAPING.md)

---

## 🚀 Próximos Pasos

1. **Automatización completa**: Script maestro que ejecute todo el pipeline
2. **Scheduler**: Cron job para scraping diario/semanal
3. **Monitoring**: Alertas de eventos nuevos
4. **Caché inteligente**: Evitar re-scrapear eventos ya procesados
5. **Multi-source**: Combinar APIs + Gemini para máxima cobertura

---

**Última actualización**: 2025-11-12
**Próxima revisión**: Después de automatizar pipeline completo
