# 🔄 Post-Scraping: Siguientes Pasos

## 📋 Checklist Post-Scraping

Después de ejecutar `process_locaciones.py` y tener los archivos JSON:

### 1. ✅ Validación de Datos

```bash
# Analizar estructuras JSON generadas
python analyze_json_structures.py

# Verificar que todos los archivos sean válidos
python validate_jsons.py
```

### 2. 📊 Normalización

**Tareas**:
- [ ] Normalizar fechas en español a formato ISO (YYYY-MM-DD)
- [ ] Validar coordenadas GPS
- [ ] Estandarizar categorías de eventos
- [ ] Limpiar duplicados

**Script recomendado**: `normalize_data.py`

### 3. 🗄️ Importación a Base de Datos

```bash
# Importar eventos a MySQL
python import_all_structures.py

# Verificar importación
python verify_import.py

# Ver eventos por locación
python show_eventos_by_location.py
```

### 4. 🧪 Verificación Final

```bash
# Estadísticas generales
python verify_import.py

# Consultas SQL de verificación
mysql -h mysql-aiven-arenazl.e.aivencloud.com -P 23108 -u avnadmin -p events
```

**Queries útiles**:
```sql
-- Contar eventos por locación
SELECT source, COUNT(*) as total
FROM events
WHERE external_id LIKE 'padron_pr_%'
GROUP BY source;

-- Eventos gratuitos
SELECT * FROM events
WHERE external_id LIKE 'padron_pr_%'
AND is_free = 1;

-- Top categorías
SELECT category, COUNT(*) as total
FROM events
WHERE external_id LIKE 'padron_pr_%'
GROUP BY category
ORDER BY total DESC;
```

### 5. 🔗 Integración con Frontend

**Endpoint API**:
```
GET /api/events?location={ciudad}&source={ciudad}
```

**Ejemplo**:
```bash
curl "http://localhost:8001/api/events?location=San%20Juan&source=San%20Juan"
```

### 6. 📅 Actualización Mensual

**Proceso recomendado**:
1. Crear script `update_monthly.py` para automatizar
2. Configurar cron job o tarea programada
3. Actualizar solo eventos futuros
4. Archivar eventos pasados

```bash
# Ejecutar actualización mensual
python update_monthly.py --mes diciembre --year 2025
```

### 7. 🎨 Mejoras Opcionales

- [ ] Agregar imágenes reales de eventos (en lugar de placeholders)
- [ ] Implementar cache de eventos populares
- [ ] Agregar sistema de favoritos por usuario
- [ ] Notificaciones push para eventos nuevos
- [ ] Integración con Google Calendar
- [ ] Sistema de reseñas y ratings

## 📈 Métricas de Éxito

**KPIs a medir**:
- Número total de eventos importados
- % de eventos con toda la información completa
- Distribución geográfica de eventos
- Categorías más populares
- Tasa de actualización mensual

## 🚨 Troubleshooting

### Problema: JSON inválido
**Solución**: Revisar respuesta raw de Gemini en campo `raw_response`

### Problema: Fechas incorrectas
**Solución**: Mejorar parser de fechas en español

### Problema: Coordenadas duplicadas
**Solución**: Agregar variación aleatoria pequeña (+/- 0.01°)

### Problema: Eventos duplicados
**Solución**: Mejorar generación de `external_id` único

## 📚 Scripts Necesarios

Crear estos scripts en la carpeta:

1. `analyze_json_structures.py` - Analizar estructuras
2. `validate_jsons.py` - Validar archivos JSON
3. `normalize_data.py` - Normalizar fechas y datos
4. `import_all_structures.py` - Importar a MySQL
5. `verify_import.py` - Verificar importación
6. `show_eventos_by_location.py` - Listar por locación
7. `update_monthly.py` - Actualización mensual

## ✅ Estado Actual

- [x] Script de scraping (`process_locaciones.py`)
- [ ] Scraping completado
- [ ] Validación de datos
- [ ] Normalización
- [ ] Importación a BD
- [ ] Verificación final
- [ ] Integración frontend

---

**Próximo paso**: Ejecutar `python process_locaciones.py` para comenzar el scraping.
