# Padrón de Eventos por Locación

## 📋 Proceso de Scraping

1. Lee el archivo `ciudades.json` (contiene las locaciones del padrón)
2. Toma el prompt de `prompt.md` y reemplaza la locación
3. Usa Gemini AI para buscar eventos de la locación
4. Genera un JSON con la respuesta en esta carpeta: `{locacion}_noviembre.json`

## 🤖 Script Automatizado

Para procesar múltiples locaciones automáticamente:

```bash
cd backend/data/padron/puertorico
python process_locaciones.py
```

**Requisitos**:
- GEMINI_API_KEY configurada en `.env`
- Python 3.8+
- Dependencias: `aiohttp`, `python-dotenv`

## 📊 Estado Actual

Ver `progreso.md` para estado detallado del scraping.

**Total locaciones**: 5
**Completado**: 0/5 locaciones ⏳

## 🔄 Siguientes Pasos

**Ver `postscrap.md`** para:
- Importación a base de datos
- Normalización de fechas
- Geolocalización de eventos
- Categorización y validación
- Integración con frontend
- Actualización mensual

---

# 🗄️ IMPORTACIÓN A BASE DE DATOS

## 📋 Resumen

Sistema para importar eventos de las locaciones desde archivos JSON hacia MySQL.

**Estado**: Pendiente de ejecución

## 🚀 Cómo Importar Eventos

### Script Principal

```bash
cd backend/data/padron/puertorico
python import_all_structures.py
```

**Características**:
- ✅ Maneja múltiples estructuras JSON diferentes
- ✅ Normaliza fechas en español a datetime
- ✅ Asigna coordenadas por locación
- ✅ Usa **nombre de la locación** como campo `source`
- ✅ Evita duplicados por `external_id`

### Verificar Importación

```bash
python verify_import.py           # Estadísticas generales
python show_eventos_by_location.py  # Ver por locación
```

## 🗄️ Base de Datos

**Ubicación**: MySQL (Aiven Cloud)
```
HOST: mysql-aiven-arenazl.e.aivencloud.com:23108
DATABASE: events
TABLA: events
```

**Campo clave**: `source` = Nombre de la locación

### Queries Útiles

```sql
-- Eventos de una locación
SELECT * FROM events WHERE source = 'San Juan'

-- Eventos gratuitos por locación
SELECT * FROM events WHERE source = 'Ponce' AND is_free = 1

-- Todos los eventos del padrón
SELECT * FROM events WHERE external_id LIKE 'padron_pr_%'
```

## 📊 Estadísticas

- **Locaciones totales**: 5
- **Eventos importados**: 0 (pendiente)
- **Locaciones con eventos**: 0

**Locaciones incluidas**:
1. San Juan (Capital)
2. Bayamón
3. Carolina
4. Ponce
5. Caguas

**Categorías populares**:
- Música
- Deportes
- Cultural
- Fiestas
- Playa

## 📁 Scripts Disponibles

| Script | Función |
|--------|---------|
| `process_locaciones.py` | Scraping con Gemini AI ⏳ |
| `import_all_structures.py` | Importación universal ⏳ |
| `analyze_json_structures.py` | Analiza estructuras JSON ⏳ |
| `verify_import.py` | Verifica datos importados ⏳ |
| `show_eventos_by_location.py` | Lista eventos por locación ⏳ |

## 🎯 Formato de Datos

**External ID**: `padron_pr_{locacion}_{mes}_N`
**Source**: Nombre de la locación capitalizado
**Coordenadas**: Centro de cada locación + variación aleatoria
**Imágenes**: Picsum Photos (basado en hash del ID)

## 🌍 Metadata del Padrón

- **País**: Puerto Rico
- **Código**: PR
- **Moneda**: USD
- **Idioma**: es-PR
- **Zona horaria**: America/Puerto_Rico
- **Radio de búsqueda**: 25 km (por defecto)
