# Scripts Genéricos para Procesamiento de Eventos

Scripts reutilizables para agregar imágenes e importar eventos de cualquier región del mundo.

## 🚨 DIFERENCIA CRÍTICA: Imágenes REALES vs Genéricas

### ❌ LO QUE NO HACEMOS (Unsplash/Pexels/Placeholder):
```json
{
  "nombre": "Festival de Jazz de Barcelona 2025",
  "image_url": "https://unsplash.com/random?music"
}
```
**Resultado**: Foto genérica de un saxofón random que NO tiene nada que ver con el evento.

### ✅ LO QUE SÍ HACEMOS (Google Images con título exacto):
```json
{
  "nombre": "Festival de Jazz de Barcelona 2025",
  "image_url": "https://real-site.com/festival-jazz-bcn-2025-poster.jpg"
}
```
**Resultado**: Poster OFICIAL del festival, foto del año pasado, imagen promocional REAL.

### Por qué es importante:
- 🎯 **Fidelidad**: Usuario ve la imagen real del evento que está buscando
- 🔍 **Credibilidad**: No parece fake/generada, es contenido auténtico
- 👁️ **Reconocimiento**: Si el usuario conoce el evento, reconoce la imagen
- 📈 **Conversión**: Mayor probabilidad de comprar tickets si ve contenido real

**Método**: Búsqueda en Google Images usando el título exacto del evento como query.

## 🎯 Características

- **Genéricos**: Funcionan con Europa, Latinoamérica, Norteamérica, y cualquier región nueva
- **Imágenes fieles**: Buscan en Google Images usando el título exacto del evento
- **Detección automática**: Reconocen múltiples estructuras de JSON
- **Duplicados**: Verifican título + ciudad + fecha antes de insertar
- **Progresivo**: Guardan cada 10 eventos para no perder progreso

## 📁 Estructura Soportada

Los scripts funcionan con la estructura organizada:

```
scrapper_results/
├── europa/
│   ├── europa-occidental/
│   │   └── francia/
│   │       └── 2025-11/
│   │           └── paris_noviembre.json
│   └── europa-meridional/
│       └── espana/
│           └── 2025-11/
│               └── barcelona_noviembre.json
├── latinamerica/
│   ├── sudamerica/
│   │   └── argentina/
│   │       └── 2025-11/
│   │           └── buenos-aires_noviembre.json
│   └── caribe/
│       └── puertorico/
│           └── 2025-11/
│               └── san-juan_noviembre.json
└── norteamerica/
    └── norteamerica/
        └── usa/
            └── 2025-11/
                └── miami_noviembre.json
```

## 🔧 Script 1: Agregar Imágenes (`add_images_generic.js`)

Busca imágenes reales en Google Images para cada evento que no tenga `image_url`.

### Uso

```bash
# Toda una región
node add_images_generic.js europa
node add_images_generic.js latinamerica
node add_images_generic.js norteamerica

# Una subregiónregión específica
node add_images_generic.js scrapper_results/europa/europa-meridional
node add_images_generic.js scrapper_results/latinamerica/sudamerica/argentina

# Una ciudad específica
node add_images_generic.js scrapper_results/europa/europa-meridional/espana/2025-11
```

### Proceso

1. Busca todos los JSONs con "noviembre" recursivamente
2. Para cada evento SIN `image_url`:
   - Hace búsqueda en Google Images con el título
   - Extrae la primera imagen JPG real (no logos)
   - Agrega el campo `image_url` al evento
3. Guarda progreso cada 10 eventos
4. Pausa 2 segundos entre requests (evita bloqueos)

### Estructuras JSON Soportadas

```javascript
// Estructura 1: {ciudad, pais, eventos: [...]}
{
  "ciudad": "Barcelona",
  "pais": "España",
  "eventos": [
    {"nombre": "Festival de Jazz", ...}
  ]
}

// Estructura 2: [...eventos...]
[
  {"titulo": "Concierto de Rock", ...},
  {"title": "Art Exhibition", ...}
]

// Estructura 3: Puerto Rico
{
  "eventos_ferias_festivales": [...],
  "recitales_shows_fiestas": [...]
}
```

### Campos de Título Detectados

- `nombre` (Europa, Latinoamérica)
- `titulo` (algunos JSONs)
- `title` (estándar internacional)

## 🤖 Script 2: Auto-Importación (`auto_import.py`) ⭐ RECOMENDADO

**Escanea automáticamente** scrapper_results/ y procesa **solo archivos nuevos**.
Mantiene un log de archivos ya importados para evitar duplicados.

### Uso

```bash
# Procesar todos los archivos nuevos automáticamente
python auto_import.py

# Ver qué se procesaría sin importar (preview)
python auto_import.py --dry-run

# Reiniciar log y reprocesar TODOS los archivos
python auto_import.py --reset
```

### Ventajas

- ✅ **Automático**: No necesitas especificar región ni path
- ✅ **Inteligente**: Solo procesa archivos nuevos (tracking con `.imported_files.log`)
- ✅ **Universal**: Funciona con CUALQUIER estructura de carpetas
- ✅ **Seguro**: Preview con --dry-run antes de importar
- ✅ **Flexible**: Soporta todos los patrones de nombres de archivo
- ✅ **Inferencia**: Detecta ciudad y país automáticamente del path

### Tracking de Archivos

El script crea `.imported_files.log` que contiene:
```
backend/data/scrapper_results/latinamerica/sudamerica/argentina/2025-11/palermo_dia_gemini.json
backend/data/scrapper_results/latinamerica/sudamerica/argentina/2025-11/recoleta_dia_gemini.json
...
```

Cada archivo se procesa **solo una vez** a menos que uses `--reset`.

## 📊 Script 3: Importar Manual (`import_generic.py`)

Importa eventos de una región/path específico. **Usa auto_import.py si prefieres automático.**

### Uso

```bash
# Toda una región
python import_generic.py europa
python import_generic.py latinamerica
python import_generic.py norteamerica

# Una subregión específica
python import_generic.py scrapper_results/europa/europa-meridional
python import_generic.py scrapper_results/latinamerica/caribe/puertorico

# Una ciudad específica
python import_generic.py scrapper_results/europa/europa-meridional/espana/2025-11
```

### Limitaciones

- ⚠️ Solo busca archivos con patrón `*noviembre*.json`
- ⚠️ No hace tracking de archivos procesados (puede duplicar si se ejecuta múltiples veces)

### Proceso

1. Busca todos los JSONs con "noviembre" recursivamente
2. Para cada evento:
   - Normaliza datos (fechas, precios, categorías)
   - Verifica duplicados (título + ciudad + fecha)
   - Inserta solo si es nuevo
3. Commit por archivo (seguridad)
4. Reporta estadísticas finales

### Detección de Duplicados

**Criterio**: Un evento es duplicado si coinciden:
- `title` (exacto)
- `city` (exacto)
- `start_datetime` (solo fecha, ignora hora)

**Ventaja**: Evita insertar el mismo evento múltiples veces.

### Normalización de Datos

#### Fechas
Formatos soportados:
- `2025-11-15`
- `15/11/2025`
- `2025-11-15T20:00:00`
- `2025-11-15 20:00:00`

#### Precios
Detección automática:
- Gratis: "gratis", "free", "libre", "gratuito" → `is_free = true`, `price = 0`
- Con precio: "$500", "€20", "£15" → extrae número

#### Categorías
Mapeo automático basado en palabras clave:
- **music**: "música", "concierto", "festival" → subcategorías: rock, pop, jazz, electronic
- **sports**: "deporte", "fútbol", "basketball"
- **cultural**: "arte", "museo", "teatro"
- **tech**: "hackathon", "conferencia", "tech"
- **other**: si no matchea

#### Monedas
- ARS (default para Argentina)
- EUR (Europa)
- USD (USA, algunos internacionales)
- GBP (UK)

## 🎯 Workflow Completo Automatizado ⚡

### Paso 1: Scraping con Gemini (Manual o Agente)
Sigue el proceso de `docs/guides/AGENT-SCRAPING-PROTOCOL.md`:
- Usa Gemini AI con prompts naturales
- Guarda JSONs en `scrapper_results/[continente]/[subregion]/[pais]/[año-mes]/`

### Paso 2: Auto-importar TODO (Recomendado) ⭐
```bash
cd backend/data/scripts

# Ver qué archivos nuevos se procesarían
python auto_import.py --dry-run

# Importar todos los archivos nuevos automáticamente
python auto_import.py
```

**Resultado**:
- ✅ Escanea TODO scrapper_results/ automáticamente
- ✅ Solo procesa archivos nuevos (tracking inteligente)
- ✅ Inserta eventos con detección de duplicados
- ✅ Infiere ciudad/país del path automáticamente

### Paso 3: Agregar imágenes (Batch final)
```bash
# Procesar solo archivos que necesiten imágenes
node add_images_generic.js scrapper_results
```

**Resultado**:
- Agrega imágenes reales de Google a eventos sin `image_url`
- Pausa 2 segundos entre requests (evita bloqueos)

---

## 🎯 Workflow Manual (Región Específica)

Si prefieres procesar una región específica manualmente:

### Paso 1: Obtener datos (scraping)
```bash
# Ejemplo: scrapear ciudades de Europa
cd scripts/europa
python automated_city_scraper.py
```

### Paso 2: Agregar imágenes
```bash
cd scripts
node add_images_generic.js europa
```

**Resultado**:
- 257 eventos con `image_url` agregado
- Imágenes fieles al título del evento
- JSONs actualizados progresivamente

### Paso 3: Importar a MySQL
```bash
python import_generic.py europa
```

**Resultado**:
- 231 eventos insertados (ejemplo real)
- 0 duplicados (si es primera vez)
- Verificación automática de existencia

## 📈 Estadísticas Reales (Noviembre 2025)

### Europa
- **Archivos procesados**: 18 ciudades
- **Eventos con imágenes**: 257
- **Eventos insertados**: 231 (86.8% éxito)
- **Errores**: 35 (precio demasiado largo)

### Latinoamérica
- **Ciudades**: 80+
- **Países**: 15+
- **Eventos estimados**: 5000+

### Norteamérica
- **Ciudades**: 8
- **Países**: 2 (USA, México)
- **Eventos estimados**: 500+

## 🔍 Debugging

### Ver qué JSONs se procesarían
```bash
# Linux/Mac
find scrapper_results/europa -name "*noviembre.json"

# Windows
dir /s /b scrapper_results\europa\*noviembre.json
```

### Verificar estructura de un JSON
```bash
# Linux/Mac/Git Bash
head -n 30 scrapper_results/europa/europa-meridional/espana/2025-11/barcelona_noviembre.json

# Windows PowerShell
Get-Content scrapper_results\europa\europa-meridional\espana\2025-11\barcelona_noviembre.json | Select-Object -First 30
```

### Contar eventos sin imagen
```bash
node -e "
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('ruta/al/archivo.json', 'utf8'));
const eventos = data.eventos || data;
const sinImagen = eventos.filter(e => !e.image_url).length;
console.log(\`\${sinImagen} eventos sin imagen de \${eventos.length} totales\`);
"
```

## 🚨 Errores Conocidos

### 1. "Data too long for column 'price'"
**Causa**: Campo `precio` en JSON tiene texto muy largo
**Solución**: El script extrae solo número, pero algunos eventos tenían strings de 500+ caracteres
**Fix futuro**: Aumentar tamaño de columna en MySQL o truncar más agresivamente

### 2. Rate limiting de Google
**Síntoma**: Muchos eventos seguidos con "⚠️ Solo logo de Google"
**Causa**: Google detecta scraping
**Solución**:
- El script ya tiene pause de 2 segundos
- Si persiste, aumentar a 3-4 segundos
- Dividir regiones en múltiples sesiones

### 3. Eventos duplicados (0 insertados)
**NO ES ERROR**: Significa que esos eventos ya están en la base
**Verificar con**:
```sql
SELECT COUNT(*) FROM events WHERE city = 'Barcelona';
```

## 📝 Configuración MySQL

Los scripts esperan esta configuración en `import_generic.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Look2025',
    'database': 'eventos_visualizer',
    'charset': 'utf8mb4'
}
```

**Cambiar si tu configuración es diferente.**

## 🎨 Módulo de Imágenes (`buscar-primera-imagen.js`)

Ubicado en `europa/buscar-primera-imagen.js`, usado por `add_images_generic.js`.

### Funcionamiento

1. Hace GET a `https://www.google.com/search?q=<titulo>&tbm=isch`
2. User-Agent: Mozilla (simula navegador real)
3. Busca regex: `/(https:\/\/[^\s"'<>)]+\.jpg)/i`
4. Fallbacks: JPG → PNG → JPEG
5. Filtra: Excluye logos de Google (`gstatic`)

### Ventajas
- ✅ Sin API keys necesarias
- ✅ Imágenes reales y relevantes
- ✅ Totalmente gratis
- ✅ Funcionamiento verificado (257 eventos procesados)

### Limitaciones
- ⚠️ Puede ser bloqueado si se abusa (por eso pause de 2 seg)
- ⚠️ Requiere internet
- ⚠️ Calidad variable (depende de Google)

## 🌍 Expansión a Nuevas Regiones

Para agregar Asia, África u Oceanía:

1. **Crear estructura** en `scrapper_results/`:
   ```bash
   mkdir -p scrapper_results/asia/asia-oriental/japon/2025-11
   ```

2. **Agregar JSONs** con estructura compatible

3. **Procesar con scripts genéricos**:
   ```bash
   node add_images_generic.js asia
   python import_generic.py asia
   ```

¡Listo! No hace falta modificar código.

## 📊 Ventajas de esta Arquitectura

1. ✅ **DRY**: Un solo código para todas las regiones
2. ✅ **Escalable**: Agregar nuevas regiones sin cambiar scripts
3. ✅ **Mantenible**: Bugs se arreglan una vez para todos
4. ✅ **Flexible**: Soporta múltiples estructuras JSON
5. ✅ **Robusto**: Maneja errores, duplicados, progreso
6. ✅ **Rápido**: Procesamiento paralelo posible (múltiples terminales)

## 🎯 Próximos Pasos

- [ ] Aumentar columna `price` en MySQL para textos largos
- [ ] Agregar soporte para imágenes PNG/WebP si JPG falla
- [ ] Implementar caché de imágenes ya buscadas
- [ ] Script de actualización: agregar imágenes a eventos ya insertados sin ellas
- [ ] Paralelización: procesar múltiples ciudades simultáneamente

---

**Última actualización**: 2025-11-12
**Scripts funcionando**: ✅ Verificado con 257 eventos Europa
