# 🌎 Process Region - Guía de Uso

Script unificado para procesar eventos de cualquier región del mundo.

## 📋 ¿Qué hace este script?

**Pipeline completo**:
1. ✅ Lee configuración de región desde `backend/data/regions/`
2. ✅ Scrapea eventos para cada ciudad usando Gemini AI
3. ✅ Parsea a formato JSON común
4. ✅ Inserta en MySQL (evita duplicados)
5. ✅ Actualiza imágenes con Google Images (3 etapas)
6. ✅ Genera reporte detallado

---

## 🚀 Uso Básico

### Procesar Argentina completa (Buenos Aires + Córdoba + Rosario + barrios)

```bash
python backend/data/scripts/process_region.py --country argentina
```

**Salida esperada**:
```
============================================================
🌎 PROCESS REGION - ARGENTINA
============================================================

📋 País: Argentina
📍 Ciudades a procesar: 3

============================================================
🌆 PROCESANDO: Buenos Aires, Argentina
============================================================

🔍 Scrapeando eventos: Buenos Aires, Argentina
   ✅ 235 eventos encontrados

📝 Insertando en MySQL...
   ✅ Evento insertado: Burger Fest
   ✅ Evento insertado: Rock en Buenos Aires
   ...

🖼️ Actualizando imágenes...
   🖼️ Buscando imagen para: Burger Fest
   ✅ Imagen actualizada
   ...

============================================================
📊 REPORTE FINAL
============================================================
🌆 Ciudades procesadas:     13  (3 ciudades + 10 barrios)
🔍 Eventos scrapeados:      523
✅ Eventos insertados:      487
⏭️ Eventos duplicados:      36
🖼️ Imágenes actualizadas:   450
❌ Imágenes fallidas:       37
⚠️ Errores totales:         0
============================================================
```

---

## 🎯 Ejemplos de Uso

### 1. Testing con límite de eventos

```bash
# Solo 5 eventos por ciudad (para probar rápido)
python backend/data/scripts/process_region.py --country argentina --limit 5
```

### 2. Solo scraping e inserción (sin actualizar imágenes)

```bash
# Más rápido, sin búsqueda de imágenes en Google
python backend/data/scripts/process_region.py --country argentina --skip-images
```

### 3. Procesar otros países

```bash
# Brasil
python backend/data/scripts/process_region.py --country brasil

# España
python backend/data/scripts/process_region.py --country espana

# México
python backend/data/scripts/process_region.py --country mexico

# Estados Unidos
python backend/data/scripts/process_region.py --country usa
```

### 4. Procesar múltiples países en secuencia

```bash
# Bash script para procesar toda Sudamérica
for country in argentina brasil chile colombia peru uruguay paraguay bolivia ecuador venezuela; do
  echo "Procesando $country..."
  python backend/data/scripts/process_region.py --country $country --limit 10
done
```

---

## 🔧 Opciones del Script

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--country` | **REQUERIDO**. Código del país a procesar | `--country argentina` |
| `--limit` | Límite de eventos por ciudad (testing) | `--limit 10` |
| `--skip-images` | Saltar actualización de imágenes | `--skip-images` |

---

## 📂 Estructura de Archivos Región

El script busca automáticamente en:

```
backend/data/regions/
├── latinamerica/
│   └── sudamerica/
│       ├── argentina.json    ← Lee desde aquí
│       ├── brasil.json
│       └── chile.json
├── europa/
│   └── europa-meridional/
│       └── espana.json
└── norteamerica/
    └── norteamerica/
        └── usa.json
```

---

## 🔄 Flujo Interno del Script

```
INICIO
  ↓
1. Cargar argentina.json
  ↓
2. Para cada ciudad (Buenos Aires, Córdoba, Rosario):
     ↓
   2.1 Scraping Gemini → eventos
     ↓
   2.2 Parsear a formato común
     ↓
   2.3 Insertar en MySQL (evitar duplicados)
     ↓
   2.4 Actualizar imágenes Google (3 etapas)
     ↓
3. Si ciudad tiene barrios (ej: Buenos Aires):
     ↓
   3.1 Repetir proceso para cada barrio
     ↓
4. Generar reporte final
  ↓
FIN
```

---

## ⚙️ Configuración MySQL

El script usa variables de entorno:

```bash
# .env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=events
```

---

## 🖼️ Sistema de Actualización de Imágenes

**3 Etapas de búsqueda en Google Images**:

1. **Etapa 1**: Solo título del evento
   - `"Burger Fest"` → Buscar en Google Images

2. **Etapa 2**: Keywords de descripción
   - Extraer palabras clave → `"hamburguesas street food festival"`

3. **Etapa 3**: Solo venue
   - `"Puerto Madero"` → Buscar imagen del lugar

4. **Fallback**: Si todo falla → `https://picsum.photos/800/600`

---

## 🚨 Manejo de Duplicados

El script **NO inserta duplicados**:

- Compara títulos normalizados (sin acentos)
- Si encuentra evento similar → `events_duplicated++`
- Solo inserta eventos nuevos → `events_inserted++`

---

## 📊 Estadísticas del Reporte

| Métrica | Descripción |
|---------|-------------|
| `cities_processed` | Ciudades + barrios procesados |
| `events_scraped` | Total eventos obtenidos de Gemini |
| `events_inserted` | Eventos nuevos insertados en MySQL |
| `events_duplicated` | Eventos que ya existían (omitidos) |
| `images_updated` | Imágenes actualizadas exitosamente |
| `images_failed` | Imágenes que no se pudieron obtener |
| `errors` | Lista de errores encontrados |

---

## 💡 Tips

### Procesar solo una ciudad específica

Edita temporalmente el JSON para incluir solo esa ciudad:

```json
{
  "country": "Argentina",
  "cities": [
    {
      "name": "Córdoba",
      "latitude": -31.4201,
      "longitude": -64.1888
    }
  ]
}
```

### Procesar en horarios de baja carga

```bash
# Ejecutar a las 3 AM
echo "0 3 * * * cd /path/to/eventos-visualizer && python backend/data/scripts/process_region.py --country argentina" | crontab
```

### Monitorear progreso

```bash
# En otra terminal, ver logs en tiempo real
tail -f logs/process_region.log
```

---

## ⚠️ Troubleshooting

### Error: "No se encontró archivo para país"

**Causa**: El nombre del país no coincide con el archivo JSON.

**Solución**: Verificar nombre exacto:
```bash
ls backend/data/regions/**/*.json
```

### Error: "No se pudieron importar los servicios"

**Causa**: El script no puede importar `gemini_factory` o `google_images_service`.

**Solución**: Ejecutar desde el directorio raíz:
```bash
cd C:\Code\eventos-visualizer
python backend/data/scripts/process_region.py --country argentina
```

### Error: MySQL connection refused

**Causa**: MySQL no está corriendo o credenciales incorrectas.

**Solución**: Verificar .env y que MySQL esté activo.

---

## 🎯 Siguiente Paso

**Ejecutar para Argentina con límite de 5 eventos (testing)**:

```bash
python backend/data/scripts/process_region.py --country argentina --limit 5
```

**Si funciona, ejecutar completo**:

```bash
python backend/data/scripts/process_region.py --country argentina
```

---

**Creado**: 2025-11-15
**Autor**: Sistema automatizado de scraping
**Versión**: 1.0
