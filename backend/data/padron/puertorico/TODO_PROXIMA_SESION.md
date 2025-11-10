# ✅ TODO para la Próxima Sesión

## 🎯 Objetivo Principal

**Implementar Puppeteer para scraping de eventos sin límites de API**

---

## 📝 Prompt Base para Gemini

**Archivo**: `prompt.md`

```
que hay para hacer, eventos, fiestas en {location}, Puerto Rico desde hoy a fin de mes, que se sepa la fecha, lugar, etc
```

**Variables**:
- `{location}` - Se reemplaza con el nombre de la ciudad (San Juan, Ponce, etc.)

**Ejemplo de uso**:
```python
# En process_locaciones.py línea ~82
prompt_template = "que hay para hacer, eventos, fiestas en {location}, Puerto Rico desde hoy a fin de mes, que se sepa la fecha, lugar, etc"
prompt_final = prompt_template.replace('{location}', 'San Juan')
```

**Prompt completo que se envía a Gemini** incluye:
1. Template base del archivo `prompt.md`
2. Instrucciones de formato JSON
3. Estructura esperada de respuesta
4. Ejemplos de eventos

---

## 📋 Tareas Prioritarias

### 1. ⚡ URGENTE: Implementar Puppeteer en `ai_service.py`

**Archivo**: `backend/services/ai_service.py`

**Qué hacer**:
```python
# Agregar método nuevo a la clase GeminiAIService

async def _call_gemini_via_puppeteer(self, prompt: str) -> Optional[str]:
    """
    Usa Puppeteer MCP para consultar Gemini web (sin límites)
    """
    # Ver PUPPETEER_VS_API.md para implementación completa
    pass
```

**Herramientas MCP disponibles**:
- `mcp__puppeteer__puppeteer_navigate`
- `mcp__puppeteer__puppeteer_fill`
- `mcp__puppeteer__puppeteer_click`
- `mcp__puppeteer__puppeteer_evaluate`

**Referencia**: `PUPPETEER_VS_API.md` líneas 50-100

---

### 2. 🔧 Actualizar `process_locaciones.py`

**Archivo**: `backend/data/padron/puertorico/process_locaciones.py`

**Cambio necesario**:
```python
# Línea actual (aprox. 133):
response = await ai_service._call_gemini_api(prompt)

# Cambiar a:
response = await ai_service._call_gemini_smart(prompt)  # Usa Puppeteer primero
```

---

### 3. 🌐 Verificar Selectores de Gemini Web

**Acción**: Abrir https://gemini.google.com y verificar selectores CSS actuales

**Verificar**:
```javascript
// En DevTools de Chrome:
document.querySelector('textarea')  // Input del chat
document.querySelector('button[type="submit"]')  // Botón enviar
document.querySelector('.response-text')  // Respuesta
```

**Guardar selectores en**: `backend/config/gemini_selectors.py`

---

### 4. 🧪 Testing Completo

**Comandos**:
```bash
# 1. Activar modo Puppeteer
cd backend
echo "USE_PUPPETEER_FOR_GEMINI=true" >> .env

# 2. Ejecutar scraping de Puerto Rico
cd data/padron/puertorico
python process_locaciones.py

# 3. Verificar archivos JSON generados
ls -la *.json

# 4. Ver estadísticas
python analyze_results.py
```

**Resultado esperado**:
- ✅ 5 archivos JSON creados (uno por ciudad)
- ✅ Sin errores HTTP 429
- ✅ Eventos scrapeados exitosamente

---

### 5. 📊 Importar a Base de Datos

**Una vez completado el scraping**:

```bash
cd backend/data/padron/puertorico
python import_all_structures.py
python verify_import.py
```

**Verificar en MySQL**:
```sql
SELECT source, COUNT(*) as total
FROM events
WHERE external_id LIKE 'padron_pr_%'
GROUP BY source;
```

---

## 🎨 Mejoras Opcionales (Si hay tiempo)

### A. Crear script genérico para cualquier país

**Archivo**: `backend/data/padron/create_country_scraping.py`

**Función**:
```python
def create_country_scraping(country_code: str, cities: list):
    """
    Crea estructura completa de scraping para un país

    Args:
        country_code: 'pr', 'mx', 'co', etc.
        cities: Lista de ciudades con coordenadas
    """
    # Crear carpeta
    # Copiar templates
    # Generar ciudades.json
    # Generar README.md
    pass
```

### B. Dashboard de progreso

**Crear**: `backend/data/padron/dashboard.html`

**Mostrar**:
- Total de países configurados
- Progreso de scraping por país
- Eventos totales importados
- Gráficos de categorías

### C. Scraping incremental

**Actualizar solo eventos nuevos**:
```python
# Verificar si evento ya existe antes de scrapear
existing_event_ids = get_existing_event_ids()
new_events = [e for e in scraped if e['id'] not in existing_event_ids]
```

---

## 🚨 Errores Conocidos a Resolver

### Error 1: HTTP 429 (Ya sabemos la solución)
**Solución**: Usar Puppeteer en lugar de API REST

### Error 2: Fechas en español mal parseadas
**Ejemplo**: "15 de noviembre" → `None`

**Solución**: Mejorar parser de fechas
```python
# En import_all_structures.py
MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}
```

### Error 3: Coordenadas duplicadas
**Problema**: Todos los eventos de una ciudad tienen mismas coordenadas exactas

**Solución**: Agregar variación aleatoria pequeña
```python
import random
latitude = base_lat + random.uniform(-0.01, 0.01)
longitude = base_lon + random.uniform(-0.01, 0.01)
```

---

## 📚 Documentación a Crear

- [ ] `ARQUITECTURA.md` - Explicar flujo completo de scraping
- [ ] `API.md` - Endpoints disponibles para frontend
- [ ] `DEPLOYMENT.md` - Cómo deployar en producción
- [ ] `CONTRIBUTING.md` - Cómo agregar nuevos países

---

## 🎯 Métricas de Éxito

Al final de la próxima sesión deberías tener:

✅ **Puppeteer funcionando** - Sin límites de API
✅ **5 ciudades de Puerto Rico scrapeadas** - Con eventos reales
✅ **Eventos importados a MySQL** - Verificados en base de datos
✅ **Proceso documentado** - Listo para replicar en otros países
✅ **Frontend mostrando eventos** - De San Juan, Ponce, etc.

---

## 💡 Comando Rápido para Claude

**Copiar y pegar esto en la próxima sesión**:

```
Lee backend/data/padron/puertorico/PUPPETEER_VS_API.md y
backend/data/padron/puertorico/TODO_PROXIMA_SESION.md

Implementa el método _call_gemini_via_puppeteer en
backend/services/ai_service.py usando las herramientas MCP de Puppeteer.

Luego ejecuta el scraping de Puerto Rico con:
cd backend/data/padron/puertorico && python process_locaciones.py
```

---

**Estado actual**: ⏸️ Bloqueado por límite de API (250/día)
**Próxima acción**: 🚀 Implementar Puppeteer para continuar sin límites
**Tiempo estimado**: 1-2 horas de trabajo
**Prioridad**: 🔴 ALTA
