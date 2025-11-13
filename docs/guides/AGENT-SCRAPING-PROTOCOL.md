<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-11-12 02:05
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-11-12 02:05: Creación de protocolo de scraping para agentes
📋 TAGS: #agent #protocol #scraping #automation #step-by-step
-->

# 🤖 PROTOCOLO DE SCRAPING PARA AGENTES

**Propósito**: Guía paso a paso para que un agente ejecute el proceso completo de scraping de eventos.

**Input**: Lista de ciudades a scrapear
**Output**: Eventos en MySQL con imágenes reales

---

## 📋 PUNTO DE ENTRADA

El usuario proporciona una lista de ciudades en este formato:

```
Ciudad, País
```

**Ejemplo:**
```
París, Francia
Barcelona, España
Roma, Italia
Berlín, Alemania
```

**Límite recomendado**: 7-8 ciudades por sesión (limitación de Gemini)

---

## 🎯 PROCESO COMPLETO

### ETAPA 1: PREPARACIÓN

**Objetivo**: Verificar estructura y preparar entorno

**Acciones**:

1. **Verificar estructura de carpetas existe**:
   ```bash
   ls -la C:\Code\eventos-visualizer\backend\data\scrapper_results
   ```

2. **Para cada ciudad, determinar ruta de guardado**:
   - Europa → `scrapper_results/europa/[región]/[país]/2025-11/`
   - Latinoamérica → `scrapper_results/latinamerica/[región]/[país]/2025-11/`
   - Norteamérica → `scrapper_results/norteamerica/norteamerica/[país]/2025-11/`

3. **Crear carpetas si no existen**:
   ```bash
   mkdir -p "ruta/completa/determinada"
   ```

**Ejemplo para París, Francia**:
```bash
mkdir -p "C:\Code\eventos-visualizer\backend\data\scrapper_results\europa\europa-occidental\francia\2025-11"
```

**Criterio de éxito**: Carpetas creadas y verificadas

---

### ETAPA 2: SCRAPING CON GEMINI

**Objetivo**: Obtener eventos de cada ciudad usando Gemini Web

**Método**: Manual (el agente guía al usuario)

**Acciones para CADA ciudad**:

1. **Informar al usuario**:
   ```
   🔍 Scrapeando: [CIUDAD], [PAÍS]
   📂 Guardará en: [RUTA]
   ```

2. **Proporcionar prompt para Gemini**:
   ```
   Ve a: https://gemini.com

   Usa este prompt:

   ---
   Dame 20-30 eventos reales y confirmados en [CIUDAD], [PAÍS] para los próximos 30 días (noviembre-diciembre 2025).

   IMPORTANTE:
   - Solo eventos CONFIRMADOS con fecha específica
   - Incluye nombre exacto del evento (no genéricos como "concierto de música")
   - Fecha en formato YYYY-MM-DD
   - Lugar/venue específico
   - Descripción breve
   - Categoría (Música, Deportes, Cultural, Tech, Fiestas)
   - Precio aproximado

   Responde SOLO con JSON en este formato:
   {
     "ciudad": "[CIUDAD]",
     "pais": "[PAÍS]",
     "fecha_scraping": "2025-11-12T00:00:00",
     "eventos": [
       {
         "nombre": "Nombre exacto del evento",
         "descripcion": "Descripción del evento",
         "fecha_inicio": "2025-11-20",
         "fecha_fin": "2025-11-20",
         "venue": "Nombre del lugar",
         "direccion": "Dirección completa",
         "ciudad": "[CIUDAD]",
         "pais": "[PAÍS]",
         "categoria": "Música",
         "subcategoria": "Rock",
         "precio": "€50",
         "moneda": "EUR",
         "url": "https://...",
         "source": "gemini_ai"
       }
     ]
   }
   ---
   ```

3. **Esperar que el usuario copie la respuesta de Gemini**

4. **Crear archivo JSON**:
   ```bash
   # Nombre: ciudad_noviembre.json (todo en minúsculas, sin espacios)
   # Ejemplo: paris_noviembre.json
   ```

5. **Escribir contenido**:
   - Usar herramienta Write
   - Ruta completa: `[ruta_determinada]/[ciudad]_noviembre.json`
   - Contenido: JSON copiado de Gemini

6. **Validar JSON**:
   ```bash
   python -m json.tool [ruta_al_archivo.json]
   ```
   Si hay error de formato, corregir.

**Criterio de éxito**:
- ✅ Archivo JSON creado
- ✅ JSON válido (sin errores de sintaxis)
- ✅ Mínimo 10 eventos por ciudad
- ✅ Eventos tienen campos obligatorios (nombre, fecha, ciudad)

**Contador de sesión**: Llevar cuenta de ciudades scrapeadas. Si llega a 8, PAUSAR y avisar:
```
⚠️ Alcanzado límite de Gemini (8 búsquedas)
⏸️ Se recomienda pausar 2-4 horas antes de continuar
📊 Progreso: [X]/[TOTAL] ciudades completadas
```

---

### ETAPA 3: AGREGAR IMÁGENES REALES

**Objetivo**: Agregar `image_url` a cada evento usando Google Images

**Método**: Script genérico de Node.js

**Acciones**:

1. **Determinar scope** (¿una ciudad, un país, toda la región?):
   - Una ciudad: Ruta específica al mes
   - Un país: Ruta al país
   - Toda región: Ruta a región (europa, latinamerica, etc.)

2. **Ejecutar script de imágenes**:
   ```bash
   cd C:\Code\eventos-visualizer\backend\data\scripts
   node add_images_generic.js [ruta_relativa]
   ```

   **Ejemplos**:
   ```bash
   # Una ciudad específica
   node add_images_generic.js scrapper_results/europa/europa-occidental/francia/2025-11

   # Todo un país
   node add_images_generic.js scrapper_results/europa/europa-occidental/francia

   # Toda Europa
   node add_images_generic.js scrapper_results/europa
   ```

3. **Monitorear salida**:
   - Contar eventos actualizados
   - Detectar errores (rate limiting, etc.)
   - Si hay muchos errores: pausar o reducir scope

4. **Verificar resultado**:
   ```bash
   # Contar eventos con imagen agregada
   grep -r "image_url" [ruta] | grep -v '""' | wc -l
   ```

**Criterio de éxito**:
- ✅ Mínimo 70% de eventos tienen `image_url`
- ✅ URLs no son logos de Google (`gstatic`)
- ✅ Script completó sin errores críticos

**Tiempo estimado**: 2 segundos por evento (pausa anti-rate-limit)

---

### ETAPA 4: IMPORTAR A MYSQL

**Objetivo**: Insertar eventos en base de datos con detección de duplicados

**Método**: Script genérico de Python

**Acciones**:

1. **Verificar conexión MySQL**:
   ```bash
   python -c "import pymysql; pymysql.connect(host='localhost', user='root', password='Look2025', database='eventos_visualizer'); print('✅ MySQL OK')"
   ```

2. **Ejecutar importador**:
   ```bash
   cd C:\Code\eventos-visualizer\backend\data\scripts
   python import_generic.py [ruta_relativa]
   ```

   **Ejemplos**:
   ```bash
   # Una ciudad
   python import_generic.py scrapper_results/europa/europa-occidental/francia/2025-11

   # Todo un país
   python import_generic.py scrapper_results/europa/europa-occidental/francia

   # Toda Europa
   python import_generic.py scrapper_results/europa
   ```

3. **Analizar salida**:
   - Eventos insertados (nuevos)
   - Eventos duplicados (ya existían)
   - Errores (si los hay)

4. **Verificar en base de datos**:
   ```sql
   SELECT
     city,
     COUNT(*) as total,
     SUM(CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END) as con_imagen,
     ROUND(SUM(CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as porcentaje_imagen
   FROM events
   WHERE city IN ('Paris', 'Barcelona', 'Roma')
   GROUP BY city;
   ```

**Criterio de éxito**:
- ✅ Eventos insertados > 0 (si son nuevos)
- ✅ Tasa de éxito > 80%
- ✅ Errores < 20%
- ✅ Eventos tienen `image_url` en DB

---

### ETAPA 5: REPORTE FINAL

**Objetivo**: Informar al usuario del resultado completo

**Acciones**:

1. **Calcular estadísticas totales**:
   ```sql
   SELECT
     COUNT(*) as total_eventos,
     COUNT(DISTINCT city) as ciudades,
     COUNT(DISTINCT country) as paises,
     SUM(CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END) as con_imagen,
     MIN(start_datetime) as evento_mas_proximo,
     MAX(start_datetime) as evento_mas_lejano
   FROM events
   WHERE created_at >= CURDATE();
   ```

2. **Generar reporte**:
   ```markdown
   # 📊 Reporte de Scraping Completado

   **Fecha**: [FECHA]
   **Ciudades procesadas**: [X] ciudades

   ## Resultados por Ciudad

   | Ciudad | País | Eventos | Con Imagen | %   |
   |--------|------|---------|------------|-----|
   | París  | Francia | 25 | 23 | 92% |
   | ...    | ...     | ... | ... | ... |

   ## Estadísticas Globales

   - **Total eventos insertados**: [X]
   - **Total con imagen**: [X] ([X]%)
   - **Duplicados detectados**: [X]
   - **Errores**: [X]

   ## Archivos Generados

   - `scrapper_results/europa/.../paris_noviembre.json`
   - ...

   ## Próximos Pasos

   - [ ] Verificar eventos en frontend
   - [ ] Revisar eventos sin imagen (si hay)
   - [ ] Documentar en PROGRESS_SCRAPING.md

   ## Notas

   [Cualquier observación relevante]
   ```

3. **Actualizar documentación de progreso**:
   - Agregar ciudades procesadas a `PROGRESS_SCRAPING.md`
   - Actualizar contador de regiones completadas
   - Marcar países completados si corresponde

**Criterio de éxito**:
- ✅ Reporte generado y presentado al usuario
- ✅ Documentación actualizada
- ✅ Usuario tiene visibilidad completa del resultado

---

## 🔄 FLUJO COMPLETO RESUMIDO

```
ENTRADA: Lista de ciudades
    ↓
ETAPA 1: Preparación
    ↓ (crear carpetas)
ETAPA 2: Scraping con Gemini
    ↓ (generar JSONs, máx 7-8 ciudades)
ETAPA 3: Agregar imágenes
    ↓ (Google Images real)
ETAPA 4: Importar a MySQL
    ↓ (con detección duplicados)
ETAPA 5: Reporte
    ↓
SALIDA: Eventos en DB + Reporte
```

---

## 📊 EJEMPLO COMPLETO

**Input del usuario**:
```
París, Francia
Lyon, Francia
Marsella, Francia
```

**Ejecución del agente**:

### Paso 1: Preparación
```
✅ Estructura verificada
📂 Creada: scrapper_results/europa/europa-occidental/francia/2025-11
```

### Paso 2: Scraping
```
🔍 Scrapeando 1/3: París, Francia
📋 Prompt proporcionado al usuario
⏳ Esperando respuesta de Gemini...
✅ JSON creado: paris_noviembre.json (28 eventos)

🔍 Scrapeando 2/3: Lyon, Francia
📋 Prompt proporcionado al usuario
⏳ Esperando respuesta de Gemini...
✅ JSON creado: lyon_noviembre.json (22 eventos)

🔍 Scrapeando 3/3: Marsella, Francia
📋 Prompt proporcionado al usuario
⏳ Esperando respuesta de Gemini...
✅ JSON creado: marsella_noviembre.json (25 eventos)

📊 Total: 75 eventos en 3 archivos JSON
```

### Paso 3: Imágenes
```
🖼️ Agregando imágenes reales desde Google Images...
📂 Procesando: scrapper_results/europa/europa-occidental/francia/2025-11

✅ paris_noviembre.json: 26/28 imágenes agregadas (92.8%)
✅ lyon_noviembre.json: 20/22 imágenes agregadas (90.9%)
✅ marsella_noviembre.json: 23/25 imágenes agregadas (92.0%)

📊 Total: 69/75 eventos con imagen (92.0%)
```

### Paso 4: Import MySQL
```
📥 Importando a MySQL...
📂 Procesando: scrapper_results/europa/europa-occidental/francia/2025-11

✅ paris_noviembre.json: 28 insertados, 0 duplicados
✅ lyon_noviembre.json: 22 insertados, 0 duplicados
✅ marsella_noviembre.json: 25 insertados, 0 duplicados

📊 Total: 75 eventos insertados (100% éxito)
```

### Paso 5: Reporte
```markdown
# 📊 Reporte de Scraping - Francia

**Fecha**: 2025-11-12
**Ciudades**: 3 (París, Lyon, Marsella)

## Resultados

| Ciudad   | Eventos | Con Imagen | %    |
|----------|---------|------------|------|
| París    | 28      | 26         | 92.8% |
| Lyon     | 22      | 20         | 90.9% |
| Marsella | 25      | 23         | 92.0% |

## Totales

- ✅ **75 eventos** insertados
- ✅ **69 eventos** con imagen (92.0%)
- ✅ **0 duplicados**
- ✅ **0 errores**

## Archivos

- `scrapper_results/europa/europa-occidental/francia/2025-11/paris_noviembre.json`
- `scrapper_results/europa/europa-occidental/francia/2025-11/lyon_noviembre.json`
- `scrapper_results/europa/europa-occidental/francia/2025-11/marsella_noviembre.json`

🎉 Proceso completado exitosamente!
```

---

## ⚠️ MANEJO DE ERRORES

### Error: Límite de Gemini alcanzado

**Síntoma**: Gemini da respuestas genéricas o sin fechas específicas

**Acción**:
1. PAUSAR inmediatamente
2. Informar al usuario:
   ```
   ⚠️ Límite de Gemini alcanzado después de [X] ciudades
   ⏸️ Se procesaron: [lista de ciudades completadas]
   ⏳ Pendientes: [lista de ciudades faltantes]
   💡 Recomendación: Pausar 2-4 horas y continuar con las pendientes
   ```
3. Completar Etapas 3-5 con las ciudades ya scrapeadas
4. NO continuar scrapeando con Gemini degradado

### Error: Rate limiting de Google Images

**Síntoma**: Muchos eventos consecutivos sin imagen ("Solo logo de Google")

**Acción**:
1. Si > 50% eventos sin imagen: PAUSAR
2. Informar al usuario
3. Ofrecer:
   - Aumentar pausa entre requests (2s → 4s)
   - Dividir en lotes más pequeños
   - Continuar más tarde

### Error: MySQL connection failed

**Síntoma**: Script de import no puede conectar a base de datos

**Acción**:
1. Verificar que MySQL está corriendo
2. Verificar credenciales en `import_generic.py`
3. Ofrecer al usuario ejecutar manualmente o corregir config

### Error: JSON inválido de Gemini

**Síntoma**: Gemini no responde en formato JSON o tiene errores de sintaxis

**Acción**:
1. Intentar parsear y corregir automáticamente (comillas, comas)
2. Si no se puede: pedir al usuario que repita el prompt en Gemini
3. Sugerir usar "Responde SOLO en JSON, sin texto adicional"

---

## 📝 CHECKLIST PARA EL AGENTE

Usar esto para cada sesión de scraping:

### Pre-Scraping
- [ ] Lista de ciudades recibida
- [ ] Determinar región de cada ciudad (Europa/Latinoamérica/Norteamérica)
- [ ] Verificar estructura de carpetas existe
- [ ] Crear carpetas necesarias
- [ ] Estimar número de ciudades (¿cabe en límite de Gemini?)

### Durante Scraping (por cada ciudad)
- [ ] Proporcionar prompt específico para la ciudad
- [ ] Esperar respuesta de Gemini del usuario
- [ ] Crear archivo JSON en ruta correcta
- [ ] Validar JSON (sintaxis)
- [ ] Validar contenido (mínimo 10 eventos, campos obligatorios)
- [ ] Incrementar contador de sesión (máx 8)

### Post-Scraping
- [ ] Ejecutar script de imágenes
- [ ] Verificar % de eventos con imagen (>70%)
- [ ] Ejecutar script de import MySQL
- [ ] Verificar eventos insertados en DB
- [ ] Generar reporte completo
- [ ] Actualizar documentación de progreso
- [ ] Informar al usuario

### En Caso de Error
- [ ] Identificar tipo de error
- [ ] Aplicar solución correspondiente
- [ ] Informar al usuario claramente
- [ ] Ofrecer alternativas o próximos pasos

---

## 🎯 OBJETIVO FINAL

Al completar este protocolo, el resultado debe ser:

✅ Eventos de todas las ciudades solicitadas en MySQL
✅ Mínimo 70% de eventos con imágenes reales
✅ Detección automática de duplicados
✅ Reporte claro de resultados
✅ Documentación actualizada
✅ Usuario satisfecho con el proceso

---

**Última actualización**: 2025-11-12
**Versión**: 1.0
**Para**: Agentes de IA ejecutando scraping de eventos
