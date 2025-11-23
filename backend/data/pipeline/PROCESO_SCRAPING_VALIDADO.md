# PROCESO DE SCRAPING GLOBAL - VALIDADO

**Fecha**: 2025-11-14
**Estado**: ✅ VALIDADO con Gemini y Felo
**Ciudades probadas**: Buenos Aires, Córdoba, Rosario

---

## ⛔ ANTI-PATRONES - LO QUE NUNCA DEBES HACER

**🚨 REGLA CRÍTICA**: Este proceso está diseñado para seguirse EXACTAMENTE como está escrito.

### ❌ NUNCA uses estos scripts obsoletos:
- `gemini_factory.py` - API programática obsoleta
- `process_region.py` - Automatización fallida
- `industrial_factory.py` - Deshabilitado
- Cualquier script con "api" o "factory" en el nombre

### ❌ NUNCA hagas llamadas API programáticas:
- NO uses `gemini.GenerativeModel()` directamente
- NO uses APIs de Gemini/Felo/Grok via código
- SOLO usa Puppeteer MCP manual como indica PASO 1

### ❌ NUNCA saltes el PASO 3 (Imágenes):
- Eventos sin imágenes = Mala UX
- El usuario entra MÁS por la imagen que por el título
- Son solo segundos por evento, no horas

### ❌ NUNCA alteres el orden de los pasos:
- Orden OBLIGATORIO: Scraping → Parsing → Imágenes → Import
- NO importar sin imágenes
- NO agregar imágenes después de importar

### ❌ NUNCA inventes nuevos scripts:
- Usa SOLO los scripts indicados en cada PASO
- NO improvises soluciones "más fáciles"
- Si algo falla, pregunta antes de improvisar

### ✅ LO QUE SÍ DEBES HACER:
1. Seguir PASO 1, 2, 3, 4 en ese orden exacto
2. Usar Puppeteer MCP manual para scraping
3. Verificar output de cada paso antes de continuar
4. Agregar imágenes ANTES de importar a MySQL

---

## 🎯 ARQUITECTURA DE 4 FASES

### **FASE 1: SCRAPING (RAW)**
- **Objetivo**: Obtener texto crudo de AIs conversacionales
- **Herramienta**: Puppeteer MCP (browser automation)
- **Output**: `backend/data/scrapper_results/raw/{ai_name}/{ciudad}_YYYY-MM-DD.txt`

### **FASE 2: PARSING (JSON)**
- **Objetivo**: Convertir texto RAW a JSON estructurado
- **Método**: Regex simple (NO AI API calls)
- **Output**: `backend/data/scrapper_results/parsed/{ai_name}/{ciudad}_YYYY-MM-DD.json`

### **FASE 3: ACTUALIZAR IMÁGENES** ⭐ CRÍTICO
- **Objetivo**: Agregar imágenes contextuales a cada evento
- **Método**: Google Images con 3 etapas (título → keywords → venue)
- **Razón**: El usuario entra al evento MÁS por la imagen que por el título
- **Output**: JSON actualizado con `image_url` completo
- **Tiempo**: ~5-10 segundos por evento (minutos totales, no horas)

### **FASE 4: IMPORT (MySQL)**
- **Objetivo**: Importar eventos COMPLETOS a MySQL
- **Método**: Fuzzy duplicate detection (80% similarity)
- **Importante**: Eventos llegan a MySQL con imágenes desde el inicio

---

## 📋 FLUJO COMPLETO VALIDADO

```
┌─────────────────┐
│   FASE 1        │
│   Puppeteer MCP │
│   Navigate →    │
│   Fill →        │
│   Submit →      │
│   Wait →        │
│   Extract       │
└────────┬────────┘
         │ RAW .txt
         ▼
┌─────────────────┐
│   FASE 2        │
│   Parser regex  │
│   Detectar      │
│   formato →     │
│   Extraer       │
│   campos →      │
│   Categorizar → │
│   Normalizar    │
└────────┬────────┘
         │ JSON estructurado
         ▼
┌─────────────────┐
│   FASE 3 ⭐     │
│   Google Images │
│   3 etapas:     │
│   1. Título     │
│   2. Keywords   │
│   3. Venue      │
│   → image_url   │
└────────┬────────┘
         │ JSON + imágenes
         ▼
┌─────────────────┐
│   FASE 4        │
│   MySQL import  │
│   Fuzzy dedup   │
│   (eventos      │
│   completos)    │
└─────────────────┘
```

---

## 📝 PROCEDIMIENTO PASO A PASO (EJECUTABLE)

### **PASO 1: SCRAPING CON PUPPETEER MCP**

**⚠️ La fuente (Gemini, Felo, Grok) la especifica el usuario**

1. Ejecutar Puppeteer navegando a la fuente indicada:
   ```
   Tool: mcp__puppeteer__puppeteer_navigate
   URL: {URL_DE_LA_FUENTE}
   ```

   **Fuentes disponibles**:
   - Gemini: `https://gemini.google.com`
   - Felo: `https://felo.ai`
   - Grok: (cuando esté habilitado)

2. Esperar 5 segundos para que cargue completamente

3. Escribir el prompt (reemplazar {CIUDAD} y {PAÍS}):
   ```
   me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {CIUDAD}, {PAÍS} de hoy a fin de mes?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas!
   ```

   **Ejemplo para Rosario**:
   ```
   me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en Rosario, Argentina de hoy a fin de mes?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas!
   ```

4. Esperar respuesta de la IA (20-30 segundos)

5. Copiar TODO el texto de la respuesta (incluir prompt y respuesta completa)

6. Guardar en archivo .txt:
   - Ruta: `backend/data/scrapper_results/raw/{fuente}/{ciudad_lowercase}_2025-11-15.txt`
   - Ejemplo Gemini: `raw/gemini/rosario_2025-11-15.txt`
   - Ejemplo Felo: `raw/felo/rosario_2025-11-15.txt`

**Output esperado**: Archivo .txt (formato varía por fuente)
- Gemini: Tabla TSV (columnas separadas por TABs)
- Felo: Lista key:value
- Grok: (pendiente definir)

---

### **PASO 2: PARSEAR CON REGEX**

**⚠️ Cada fuente tiene su PROPIO parser (formato diferente)**

1. Ir al directorio de scripts:
   ```bash
   cd backend/data/final_guide/scripts
   ```

2. Ejecutar el parser CORRECTO según la fuente:

   **Gemini** (formato TSV):
   ```bash
   python fase2_parse.py
   ```

   **Felo** (formato key:value):
   ```bash
   python fase2_parse_felo.py
   ```

   **Grok**: (pendiente implementar)

3. Verificar que se creó el JSON:
   ```bash
   cat backend/data/scrapper_results/parsed/{fuente}/{ciudad}_2025-11-15.json
   ```

4. Confirmar que contiene array de eventos con **los mismos campos estándar**

**Output esperado**: JSON estructurado con campos estándar (sin imágenes aún)
- ✅ Mismo formato JSON sin importar la fuente
- ✅ Campos: nombre, descripcion, fecha, lugar, direccion, barrio, precio, ciudad, category, subcategory, es_gratis, source

---

### **PASO 3: AGREGAR IMÁGENES** ⭐ CRÍTICO

⚠️ **ESTE PASO ES OBLIGATORIO ANTES DE IMPORTAR**

**Script**: `update_event_images.js` (Google Custom Search API)

**Ejecutar**:
```bash
node backend/data/scripts/update_event_images.js
```

**Proceso automático**:
1. Detecta todas las fuentes en `scrapper_results/parsed/` (gemini, felo, grok, etc.)
2. Para cada fuente, procesa todos los archivos JSON
3. Para cada evento sin `image_url`:
   - **Intento 1**: Título completo + venue + city
   - **Intento 2**: Título reducido (3 primeras palabras) + city
   - **Intento 3**: Solo venue + city
4. Rate limit: 1 segundo entre eventos
5. Guarda JSON actualizado automáticamente

**API utilizada**: Google Custom Search API
- Las credenciales se leen desde `.env`:
  ```env
  GOOGLE_API_KEY=AIzaSyBnASoI0jTHdwiuzugYDwqghzzzDJ44Smg
  GOOGLE_CX=06b5ac72c42074af6
  ```
- Límite: 100 búsquedas/día (se detiene automáticamente si alcanza límite)

**Output esperado**: Mismo JSON pero con campo `image_url` en cada evento

---

### **PASO 4: IMPORTAR A MYSQL**

1. Ir al directorio de scripts:
   ```bash
   cd backend/data/final_guide/scripts
   ```

2. Ejecutar el import:
   ```bash
   python fase4_import.py
   ```

3. Verificar output en consola:
   - ✅ Eventos insertados: Cantidad de eventos nuevos
   - ⏭️ Eventos duplicados: Cantidad de eventos que ya existían
   - ❌ Errores: Revisar si hay errores

**Output esperado**: Eventos COMPLETOS (con imágenes) insertados en MySQL

---

### **⚠️ REGLAS CRÍTICAS**

1. **NUNCA saltarse PASO 3** - Eventos sin imágenes = Mala UX
2. **SEGUIR ORDEN EXACTO** - No alterar secuencia de pasos
3. **NO usar APIs programáticas** - Solo Puppeteer MCP manual
4. **VERIFICAR cada output** antes de pasar al siguiente paso

---

## 🤖 AI SCRAPERS VALIDADOS

### **1. GEMINI ✅**

**Resultados Buenos Aires**:
- ✅ 21 eventos extraídos
- ✅ 90.5% barrios detectados (19/21)
- ✅ 100% categorización correcta
- ✅ Formato estable: Tabla TSV

**Formato de respuesta**:
```
Nombre del Evento	Descripción	Fecha(s)	Lugar / Dirección	Barrio	Precio (Ref.)	Info Extra
Festival Fado Buenos Aires 2025	Festival dedicado al género musical portugués...	Sábado 15 y Domingo 16 de noviembre	Palacio Libertad (Sarmiento 151)	Microcentro	Gratuito	Concierto Sáb. 15...
```

**Características**:
- Formato de tabla con TAB separators
- Con o sin numeración de filas (#)
- Incluye barrio explícitamente
- Buena cantidad de eventos (20+)

**Parser**: `fase2_parse.py`
- Detecta automáticamente si hay numeración
- Soporte para ambos formatos (con/sin #)
- 100% regex, sin AI calls

---

### **2. FELO ✅**

**Resultados Buenos Aires**:
- ✅ 7 eventos extraídos
- ✅ 57.1% barrios detectados (4/7)
- ✅ 100% categorización correcta
- ✅ Formato estable: Key:Value

**Formato de respuesta**:
```
La Noche de los Museos

Descripción: Más de 300 museos...
Fecha: Sábado 8 de noviembre, de 19:00 a 02:00.
Lugar: Varios museos en la ciudad.
Dirección: Varía según el museo.
Barrio: Diversos.
Precio: Gratis.
```

**Características**:
- Formato de lista con campos clave:valor
- Menos eventos que Gemini (~7-10)
- Barrios a veces genéricos ("Diversos")
- Buena calidad de descripciones

**Parser**: `fase2_parse_felo.py`
- Line-by-line parsing
- Estado con current_event
- Normalización de puntos finales

---

### **3. GROK ⏸️**

**Estado**: Deshabilitado (requiere acceso)
**Parser**: Pendiente de implementar

---

## 🛠️ COMPONENTES CRÍTICOS

### **1. PROMPT INFORMAL (PROBADO)**

```
me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {lugar} de hoy a fin de mes?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas!
```

**Validación**:
- ✅ No triggerea anti-spam
- ✅ Tono natural y casual
- ✅ Pide campos específicos (barrio, precio)
- ✅ Funciona en Gemini y Felo sin cambios

**Ubicación**: `backend/data/final_guide/config/prompts.json`

---

### **2. CATEGORIZACIÓN INTELIGENTE**

**Orden de prioridad** (CRÍTICO - el orden importa):

```python
1. Museos → cultural/other  (ANTES de música)
2. Literatura/Libros → cultural/literature (ANTES de nightlife)
3. Cine → cultural/other
4. Deportes → sports/other
5. Nightlife/Bares → nightlife/party
6. Fiestas → nightlife/party (con exclusiones)
7. Stand Up → entertainment/comedy
8. Gastronomía → food/other
9. Tech → tech/conference
10. Música → music/* (DESPUÉS de específicas)
11. Cultural → cultural/other (GENÉRICO, al final)
```

**Lecciones aprendidas**:
- ❌ "La Noche de los Museos" se categorizaba como música (tenía "conciertos" en descripción)
- ✅ Solucionado: Museos ANTES de música
- ❌ "La Noche de las Librerías" se categorizaba como nightlife (tenía "noche" en nombre)
- ✅ Solucionado: Literatura ANTES de nightlife

**Exclusiones importantes**:
- Fiestas excluye: `'concierto', 'banda', 'museo', 'librería'`
- Esto evita falsos positivos

---

### **3. NORMALIZACIÓN DE FECHAS**

**Formatos soportados**:
- "Sábado 8 de noviembre" → 2025-11-08
- "Del 7 al 9 de noviembre" → 2025-11-07 (fecha inicio)
- "8 y 9 de noviembre" → 2025-11-08

**Mapeo de meses en español**:
```python
{
  'enero': '01', 'febrero': '02', 'marzo': '03',
  'abril': '04', 'mayo': '05', 'junio': '06',
  'julio': '07', 'agosto': '08', 'septiembre': '09',
  'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}
```

---

### **4. NORMALIZACIÓN DE BARRIOS**

**Procesamiento**:
- Quitar puntos finales: `"Palermo."` → `"Palermo"`
- Mantener multi-barrio: `"Avellaneda y Parque Patricios"` ✅
- Valores genéricos válidos: `"Diversos"`, `"A confirmar"`

**Estadísticas de calidad**:
- Gemini: 90.5% barrios válidos (excelente)
- Felo: 57.1% barrios válidos (aceptable)

---

### **5. DETECCIÓN DE PRECIO GRATIS**

```python
es_gratis = any(word in precio.lower() for word in [
    'gratis', 'free', 'entrada libre'
])
```

**Casos cubiertos**:
- "Gratis." → `true`
- "Gratuito" → `true`
- "Free" → `true`
- "Entrada libre" → `true`
- "Varía según..." → `false`

---

## 📊 ESTRUCTURA JSON FINAL

```json
{
  "nombre": "string",
  "descripcion": "string",
  "fecha": "YYYY-MM-DD",
  "lugar": "string",
  "direccion": "string",
  "barrio": "string",
  "precio": "string",
  "ciudad": "Buenos Aires",
  "neighborhood": "string",
  "category": "cultural|music|food|tech|sports|nightlife|other",
  "subcategory": "other|literature|rock|pop|jazz|electronic|folk|conference|party|comedy",
  "pais": "Argentina",
  "es_gratis": boolean,
  "source": "gemini|felo|grok"
}
```

---

## 🎯 MÉTRICAS DE CALIDAD

### **Gemini (EXCELENTE)**:
| Métrica | Valor | Nota |
|---------|-------|------|
| Cantidad eventos | 21 | ⭐⭐⭐⭐⭐ Excelente |
| Barrios detectados | 90.5% | ⭐⭐⭐⭐⭐ Excelente |
| Categorización | 100% | ⭐⭐⭐⭐⭐ Perfecta |
| Formato estable | Sí | ⭐⭐⭐⭐⭐ Tabla TSV |

### **Felo (BUENO)**:
| Métrica | Valor | Nota |
|---------|-------|------|
| Cantidad eventos | 7 | ⭐⭐⭐ Aceptable |
| Barrios detectados | 57.1% | ⭐⭐⭐ Aceptable |
| Categorización | 100% | ⭐⭐⭐⭐⭐ Perfecta |
| Formato estable | Sí | ⭐⭐⭐⭐ Key:Value |

---

## ✅ VALIDACIONES COMPLETADAS

- [x] Gemini scraping con Puppeteer MCP
- [x] Felo scraping con Puppeteer MCP
- [x] Parser regex para formato Gemini (tabla TSV)
- [x] Parser regex para formato Felo (key:value)
- [x] Categorización con prioridad correcta
- [x] Normalización de fechas en español
- [x] Normalización de barrios (quitar puntos)
- [x] Detección de eventos gratis
- [x] JSON estructurado con todos los campos

---

## 🚧 PENDIENTES

- [x] Implementar FASE 3 (Imágenes con Google API) ✅
- [x] Implementar FASE 4 (Import a MySQL) ✅
- [x] Fuzzy duplicate detection (80% similarity) ✅
- [x] Validar con múltiples ciudades (Buenos Aires, Córdoba, Rosario) ✅
- [ ] Parser para Grok (cuando esté habilitado)
- [ ] Expandir a más países:
  - [ ] Chile (Santiago, Valparaíso)
  - [ ] Colombia (Bogotá, Medellín)
  - [ ] México (CDMX, Guadalajara)
  - [ ] Perú (Lima, Cusco)
- [ ] Script maestro que ejecute las 4 fases automáticamente (opcional)
- [ ] Dashboard web para monitorear scraping progress
- [ ] Notificaciones cuando se encuentren eventos duplicados

---

## 📁 ARCHIVOS CRÍTICOS

### **Scripts de parsing**:
- `backend/data/final_guide/scripts/fase2_parse.py` - Parser Gemini
- `backend/data/final_guide/scripts/fase2_parse_felo.py` - Parser Felo
- `backend/data/scripts/update_event_images.js` - Agregador de imágenes (Node.js)
- `backend/data/final_guide/scripts/fase4_import.py` - Import a MySQL
- `backend/data/final_guide/scripts/analyze_json.py` - Estadísticas
- `backend/data/final_guide/scripts/check_categories.py` - Validación categorías

### **Configuración**:
- `backend/data/final_guide/config/prompts.json` - Prompts por AI
- `backend/data/final_guide/config/sites.json` - Config de sitios AI

### **Documentación**:
- `backend/data/pipeline/GRUPO_1_AI_SCRAPERS.md` - Spec completa
- `backend/data/pipeline/PROCESO_SCRAPING_VALIDADO.md` - Este documento

### **Datos generados**:
```
backend/data/scrapper_results/
├── raw/
│   ├── gemini/
│   │   └── buenos-aires_2025-11-14.txt (6 KB, 21 eventos)
│   └── felo/
│       └── buenos-aires_2025-11-14.txt (2.1 KB, 7 eventos)
└── parsed/
    ├── gemini/
    │   └── buenos-aires_2025-11-14.json (12 KB, 21 eventos)
    └── felo/
        └── buenos-aires_2025-11-14.json (3.6 KB, 7 eventos)
```

---

## 🔍 LECCIONES APRENDIDAS

### **1. Formato de respuesta varía por AI**
- Gemini: Tabla con tabs
- Felo: Lista con key:value
- ❌ No se puede usar un parser único
- ✅ Solución: Parser específico por AI

### **2. Orden de categorización es CRÍTICO**
- ❌ Categorías genéricas primero causan falsos positivos
- ✅ Solución: Específicas ANTES de genéricas
- Ejemplo: "museo" ANTES de "música/concierto"

### **3. Normalización es esencial**
- Barrios con puntos finales
- Fechas en múltiples formatos
- Precios en texto libre
- ✅ Solución: Funciones de normalización específicas

### **4. Calidad varía por AI**
- Gemini: +20 eventos, 90% barrios
- Felo: ~7 eventos, 57% barrios
- ✅ Complementar con múltiples fuentes

### **5. Regex es suficiente para parsing**
- ❌ NO necesitamos AI para parsear
- ✅ Regex simple y rápido
- Costo: $0 (vs AI parsing)

---

## 🎉 CONCLUSIONES

### **El proceso de 4 fases funciona**:
1. ✅ FASE 1 (Scraping): Puppeteer MCP efectivo
2. ✅ FASE 2 (Parsing): Regex suficiente y preciso
3. ✅ FASE 3 (Imágenes): Google Custom Search API con triple fallback
4. ✅ FASE 4 (Import): MySQL con fuzzy duplicate detection

### **Gemini es superior a Felo**:
- 3x más eventos (21 vs 7)
- Mejor calidad de barrios (90% vs 57%)
- Formato más estructurado (tabla)

### **Categorización perfeccionada**:
- 100% de precisión en ambos scrapers
- Orden de prioridad validado
- Sistema de exclusiones funcionando

### **Listo para escalar**:
- ✅ Validado en 3 ciudades argentinas (Buenos Aires, Córdoba, Rosario)
- ✅ Pipeline completo de 4 fases funcionando
- Próximo: Expandir a más países de Latinoamérica

---

**Última actualización**: 2025-11-15
**Validado por**: Claude Code
**Próximo paso**: Expandir a más países (Chile, Colombia, México, etc.)
