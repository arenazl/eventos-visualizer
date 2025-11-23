# 📋 PROCEDIMIENTO MANUAL DE SCRAPING - VALIDADO

**Fecha**: 2025-11-15
**Estado**: ✅ PROCEDIMIENTO OFICIAL
**Validado con**: Córdoba (18 eventos exitosos)

---

## 🎯 ARQUITECTURA DE 4 FASES (ORDEN CRÍTICO)

### **FASE 1: SCRAPING CON PUPPETEER MCP**
**Input**: Ciudad (ej: "Rosario, Argentina")
**Output**: `backend/data/scrapper_results/raw/gemini/{ciudad}_YYYY-MM-DD.txt`
**Tiempo**: ~30 segundos

#### Pasos:
1. Abrir Puppeteer con Gemini:
```bash
mcp__puppeteer__puppeteer_navigate
url: https://gemini.google.com
```

2. Esperar carga completa (5 segundos)

3. Enviar prompt (copiar exacto):
```
me podrías pasar por lo menos 20 eventos, fiestas, festivales, encuentros en {CIUDAD}, {PAIS} de hoy a fin de mes?, si puede ser que incluya su nombre, descripción, fecha, lugar, dirección, barrio, precio y alguna info extra que tengas!
```

4. Esperar respuesta de Gemini (20-30 segundos)

5. Extraer texto completo y guardarlo en:
   - `backend/data/scrapper_results/raw/gemini/{ciudad_lowercase}_2025-11-15.txt`

**Formato esperado de Gemini**: Tabla TSV con columnas separadas por TAB

---

### **FASE 2: PARSING CON REGEX**
**Input**: RAW .txt de FASE 1
**Output**: `backend/data/scrapper_results/parsed/gemini/{ciudad}_YYYY-MM-DD.json`
**Tiempo**: <1 segundo

#### Comando:
```bash
cd backend/data/final_guide/scripts
python fase2_parse.py
```

#### Verificar output:
```bash
cat backend/data/scrapper_results/parsed/gemini/{ciudad}_2025-11-15.json
```

**Debe contener**: Array de eventos con campos: nombre, descripcion, fecha, lugar, direccion, barrio, precio, ciudad, category, subcategory, es_gratis, source

---

### **FASE 3: ACTUALIZAR IMÁGENES** ⭐ CRÍTICO
**Input**: JSON de FASE 2
**Output**: JSON actualizado con `image_url` completo
**Tiempo**: ~5-10 segundos por evento

#### 🚨 **REGLA DE ORO**:
**"El usuario entra al evento MÁS por la imagen que por el título"**

#### Pasos:
1. Leer JSON de FASE 2
2. Para cada evento:
   - Buscar imagen con Google Images (3 etapas):
     1. Título del evento
     2. Keywords de descripción
     3. Solo venue
   - Agregar `image_url` al JSON
3. Guardar JSON actualizado (mismo archivo)

#### Script (crear si no existe):
```bash
python backend/data/scripts/fase3_update_images.py --input parsed/gemini/{ciudad}_2025-11-15.json
```

**Importante**: Eventos SIN imágenes = eventos incompletos = mala UX

---

### **FASE 4: IMPORT A MYSQL**
**Input**: JSON con imágenes de FASE 3
**Output**: Eventos completos en MySQL
**Tiempo**: ~1 segundo

#### Comando:
```bash
cd backend/data/final_guide/scripts
python fase3_import.py
```

**Nota**: Este script debería renombrarse a `fase4_import.py` en el futuro

#### Verificación:
- ✅ Eventos insertados: Nuevos en DB
- ⏭️ Eventos duplicados: Ya existían (fuzzy 80%)
- ❌ Errores: Revisar logs

---

## 📊 CHECKLIST POR CIUDAD

### ✅ **Córdoba** (COMPLETADO - PERO SIN IMÁGENES)
- [x] FASE 1: Scraping → 18 eventos en RAW
- [x] FASE 2: Parsing → 18 eventos en JSON
- [ ] **FASE 3: Imágenes** ⚠️ SALTADO (ERROR)
- [x] FASE 4: Import → 18 eventos en MySQL

**Estado**: ⚠️ Eventos en MySQL SIN imágenes - necesita corrección retroactiva

---

### ⏳ **Rosario** (EN PROGRESO)
- [ ] FASE 1: Scraping → RAW .txt
- [ ] FASE 2: Parsing → JSON
- [ ] FASE 3: Imágenes → JSON completo
- [ ] FASE 4: Import → MySQL

---

### ⏸️ **Buenos Aires** (PENDIENTE)
- [ ] FASE 1: Scraping → RAW .txt
- [ ] FASE 2: Parsing → JSON
- [ ] FASE 3: Imágenes → JSON completo
- [ ] FASE 4: Import → MySQL

**Nota**: Buenos Aires tiene 10 barrios adicionales que también deben procesarse

---

## 🚨 ERRORES COMUNES A EVITAR

### ❌ **ERROR 1: Importar sin imágenes**
- **Síntoma**: Eventos en MySQL con `image_url` vacío
- **Causa**: Saltarse FASE 3
- **Consecuencia**: Mala UX, usuarios no clickean eventos
- **Solución**: SIEMPRE ejecutar FASE 3 antes de FASE 4

### ❌ **ERROR 2: Usar API programática en lugar de Puppeteer**
- **Síntoma**: `gemini_factory.execute_global_scrapers()` retorna 0 eventos
- **Causa**: Intentar automatizar sin validar primero
- **Solución**: Usar Puppeteer MCP manualmente

### ❌ **ERROR 3: Cambiar orden de fases**
- **Síntoma**: Procesos fallidos, datos incompletos
- **Causa**: No seguir orden: Scraping → Parsing → Imágenes → Import
- **Solución**: Seguir SIEMPRE este procedimiento exacto

---

## 📁 ESTRUCTURA DE ARCHIVOS ESPERADA

```
backend/data/scrapper_results/
├── raw/
│   └── gemini/
│       ├── cordoba_2025-11-15.txt      (6 KB, 18 eventos)
│       ├── rosario_2025-11-15.txt      (pendiente)
│       └── buenos-aires_2025-11-15.txt (pendiente)
└── parsed/
    └── gemini/
        ├── cordoba_2025-11-15.json     (12 KB, 18 eventos - SIN imágenes)
        ├── rosario_2025-11-15.json     (pendiente)
        └── buenos-aires_2025-11-15.json (pendiente)
```

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Crear script `fase3_update_images.py`
2. ⚠️ Corregir eventos de Córdoba (agregar imágenes retroactivamente)
3. ⏳ Completar Rosario siguiendo procedimiento correcto
4. ⏳ Completar Buenos Aires siguiendo procedimiento correcto
5. ⏳ Completar 10 barrios de Buenos Aires
6. 🔄 Renombrar `fase3_import.py` → `fase4_import.py` (para claridad)

---

**REGLA DE ORO**:
**NUNCA saltarse FASE 3 - Eventos sin imágenes = Eventos incompletos**

---

**Última actualización**: 2025-11-15 06:30
**Creado por**: Claude Code
**Validado con**: Córdoba (18 eventos)
