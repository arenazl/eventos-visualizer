# 📊 Progreso de Scraping de Eventos con Gemini AI + Grok

**Última actualización**: 2025-11-05 (Sesión Consolidada)
**Estado**: 42/63 ciudades completadas (67%)
**Métodos**: Gemini AI + Grok (consolidado por ciudad)

---

## 🎯 RESUMEN EJECUTIVO

Scraping de eventos para 63 ciudades usando **Gemini AI** y **Grok** consolidado.
- **Método**: Consulta en ambas fuentes POR CIUDAD, consolidar y guardar
- **Formato**: JSON estructurado con normalización automática
- **Calidad**: Excelente - datos detallados con contexto local desde 2 fuentes
- **Eventos totales**: ~1037 eventos de 42 ciudades
- **Nuevo**: Consolidación Gemini+Grok por ciudad para máxima cobertura

---

## ⚠️ LÍMITE CRÍTICO DE GEMINI

**🚨 IMPORTANTE**: Gemini tiene un límite de **10 búsquedas por sesión**

Después de 10 búsquedas, las respuestas se vuelven ambiguas y genéricas:
- ✅ Búsquedas 1-7: Calidad excelente
- ⚠️ Búsquedas 8-9: Comienza degradación
- ❌ Búsqueda 10+: Respuestas genéricas sin fechas específicas

**Estrategia recomendada**:
- **Bloques de 7-8 ciudades máximo** por sesión
- **Pausa de 2-4 horas** entre sesiones
- Si notas degradación de calidad → **PARAR INMEDIATAMENTE**

---

## ✅ CIUDADES COMPLETADAS (42/63 - 67%)

### Sesión 1 - Ciudades Base (18 ciudades)
Scrapeadas en sesiones anteriores

### Sesión 2 - Ciudades América (9 ciudades)  

### Sesión 3 - NUEVA 2025-11-05 (8 ciudades)

**BLOQUE 1** (5 ciudades):
28. **Belo Horizonte** (Brasil) - 30 eventos
29. **Brasília** (Brasil) - 30 eventos
30. **Cali** (Colombia) - 30 eventos
31. **Caracas** (Venezuela) - 16 eventos
32. **Chicago** (USA) - 30 eventos

**BLOQUE 2** (3 ciudades - pausa por límite):
33. **Ciudad de Panamá** (Panamá) - 20 eventos
34. **Cusco** (Perú) - 10 eventos ⚠️
35. **Florianópolis** (Brasil) - 15 eventos ⚠️

**Total eventos sesión 3**: 181 eventos

### Sesión 4 - Método Consolidado 2025-11-05 (5 ciudades)

**NUEVO MÉTODO**: Por cada ciudad → Gemini + Grok → Consolidar → Guardar

36. **Guadalajara** (México) - 16 eventos (Gemini)
37. **Guayaquil** (Ecuador) - 5 eventos (Grok)
38. **Houston** (USA) - 30 eventos (Gemini)
39. **La Habana** (Cuba) - 30 eventos (Grok)
40. **La Paz** (Bolivia) - 34 eventos (Gemini + Grok consolidado) ⭐

**Total eventos sesión 4**: 115 eventos

---

## 🔧 SCRIPTS DE PROCESAMIENTO

### ⚡ FUNCIÓN RÁPIDA: Insertar después de cada scraping

**Apenas guardes un JSON**, ejecutá esto para insertar automáticamente en MySQL:

```bash
# Reemplazá CIUDAD por el nombre del archivo que acabas de guardar
cd backend/batch
python3 -c "
from bulk_insert_events import insert_single_city
import asyncio
asyncio.run(insert_single_city('CIUDAD_2025-11-05.json'))
"
```

**Ejemplos**:
```bash
# Después de guardar guadalajara_2025-11-05.json:
python3 -c "from bulk_insert_events import insert_single_city; import asyncio; asyncio.run(insert_single_city('guadalajara_2025-11-05.json'))"

# Después de guardar guayaquil_2025-11-05.json:
python3 -c "from bulk_insert_events import insert_single_city; import asyncio; asyncio.run(insert_single_city('guayaquil_2025-11-05.json'))"
```

**Output esperado**:
```
🏙️  Insertando eventos de: guadalajara_2025-11-05.json
✅ Conectado a MySQL (Aiven)
✅ guadalajara_2025-11-05.json: 28/28 eventos normalizados
  ✅ Batch 1: 28 eventos insertados
✅ 28 eventos insertados desde guadalajara_2025-11-05.json
```

---

### 1. Normalizar JSONs
**Archivo**: `backend/batch/normalize_scraped_events.py`

**Uso**:
```bash
cd backend/batch
python3 normalize_scraped_events.py
```

### 2. Bulk Insert a MySQL
**Archivo**: `backend/batch/bulk_insert_events.py`

**Uso**:
```bash
cd backend/batch
python3 bulk_insert_events.py
```

Ver scripts para documentación completa.
