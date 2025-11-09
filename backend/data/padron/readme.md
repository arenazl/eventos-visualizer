# Padrón de Eventos por Barrio de Buenos Aires

## 📋 Proceso de Scraping

1. Lee el archivo `barrios-buenos-aires.json` (48 barrios de Buenos Aires)
2. Toma el prompt de `prompt.md` y reemplaza el barrio
3. Usa Gemini AI para buscar eventos del barrio
4. Genera un JSON con la respuesta en esta carpeta: `{barrio}_noviembre.json`

## 🤖 Script Automatizado

Para procesar múltiples barrios automáticamente:

```bash
cd backend/data/padron
python process_barrios.py
```

**Requisitos**:
- GEMINI_API_KEY configurada en `.env`
- Python 3.8+
- Dependencias: `aiohttp`, `python-dotenv`

## 📊 Estado Actual

Ver `progreso.md` para estado detallado del scraping.

**Completado**: 48/48 barrios ✅

## 🔄 Siguientes Pasos

**Ver `postscrap.md`** para:
- Importación a base de datos
- Normalización de fechas
- Geolocalización de eventos
- Categorización y validación
- Integración con frontend
- Actualización mensual

---

# 🗄️ IMPORTACIÓN A BASE DE DATOS (Completado ✅)

## 📋 Resumen

Sistema para importar eventos de los 48 barrios desde archivos JSON hacia MySQL.

**Estado**: 211 eventos importados correctamente

## 🚀 Cómo Importar Eventos

### Script Principal

```bash
cd backend/data/padron
python import_all_structures.py
```

**Características**:
- ✅ Maneja 38+ estructuras JSON diferentes
- ✅ Normaliza fechas en español a datetime
- ✅ Asigna coordenadas por barrio
- ✅ Usa **nombre del barrio** como campo `source`
- ✅ Evita duplicados por `external_id`

### Verificar Importación

```bash
python verify_import.py           # Estadísticas generales
python show_eventos_by_barrio.py  # Ver por barrio
```

## 🗄️ Base de Datos

**Ubicación**: MySQL (Aiven Cloud)
```
HOST: mysql-aiven-arenazl.e.aivencloud.com:23108
DATABASE: events
TABLA: events
```

**Campo clave**: `source` = Nombre del barrio ("Palermo", "Recoleta", etc.)

### Queries Útiles

```sql
-- Eventos de un barrio
SELECT * FROM events WHERE source = 'Palermo'

-- Eventos gratuitos por barrio
SELECT * FROM events WHERE source = 'San Telmo' AND is_free = 1

-- Todos los eventos del padrón
SELECT * FROM events WHERE external_id LIKE 'padron_%'
```

## 📊 Estadísticas (2025-11-09)

- **48 barrios** procesados
- **211 eventos** importados
- **38 barrios** con eventos

**Top barrios**:
1. Constitución - 13 eventos
2. Belgrano - 12 eventos
3. Palermo - 11 eventos

**Categorías**:
- Cultural: 61 eventos
- Festival: 27 eventos
- Music: 20 eventos
- Film: 14 eventos

## 📁 Scripts Disponibles

| Script | Función |
|--------|---------|
| `import_all_structures.py` | Importación universal ✅ |
| `analyze_json_structures.py` | Analiza estructuras JSON |
| `verify_import.py` | Verifica datos importados |
| `show_eventos_by_barrio.py` | Lista eventos por barrio |

## 🎯 Formato de Datos

**External ID**: `padron_barrio_mes_N`
**Source**: Nombre del barrio capitalizado
**Coordenadas**: Centro de cada barrio + variación aleatoria
**Imágenes**: Picsum Photos (basado en hash del ID)