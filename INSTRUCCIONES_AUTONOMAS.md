# 🤖 INSTRUCCIONES PARA SCRAPING AUTÓNOMO

**Última actualización:** 2025-11-09 08:00

---

## 🎯 OBJETIVO

Completar el scraping de las **49 regiones pendientes** de forma autónoma sin intervención manual.

**Progreso actual:** 31/80 regiones (38.75%)
**Falta:** 49 regiones (61.25%)
**Tiempo estimado:** 2.5 - 3 horas

---

## 🚀 EJECUCIÓN RÁPIDA (UN SOLO COMANDO)

### Opción 1: Modo TEST (Probar con 2 regiones)
```bash
cd backend
python automation/autonomous_scraping_pipeline.py --mode test
```
**Duración:** ~6-8 minutos
**Procesa:** Manabí (Ecuador) + La Paz (Bolivia)

### Opción 2: Modo CONTINUAR (Recomendado)
```bash
cd backend
python automation/autonomous_scraping_pipeline.py --mode continue
```
**Duración:** ~2.5-3 horas
**Procesa:** Las 49 regiones pendientes automáticamente

### Opción 3: Modo COMPLETO
```bash
cd backend
python automation/autonomous_scraping_pipeline.py --mode full
```
**Igual que CONTINUAR** pero reprocesa todo si es necesario

---

## 📋 QUÉ HACE EL PIPELINE AUTÓNOMO

El script `autonomous_scraping_pipeline.py` ejecuta **3 pasos automáticos**:

### 1. 🔍 SCRAPING (Gemini + Playwright)
- Abre Gemini en browser headless
- Envía prompt: "eventos próximos en {región}, {país}..."
- Espera respuesta (20s)
- Guarda en `backend/data/ai_scraped/{region}_gemini_response.json`

### 2. 🧹 CURACIÓN (Validación + Imágenes)
- Valida calidad de eventos (elimina datos pobres)
- Detecta y elimina duplicados
- Busca imágenes de alta calidad (Unsplash)
- Guarda en `backend/data/curated/curated_{region}_gemini_response.json`

### 3. 💾 INSERCIÓN EN MYSQL
- Inserta eventos curados en tabla `events`
- Maneja duplicados (actualiza si existe)
- Registra en tabla `scraping_runs`

**TODO AUTOMÁTICO - SIN INTERVENCIÓN MANUAL**

---

## 📊 ESTADÍSTICAS ACTUALES

### Ya en Base de Datos
```sql
SELECT COUNT(*) FROM events WHERE source = 'gemini_auto';
-- Resultado esperado: ~97 eventos
```

### Archivos Generados
```bash
# Ver scraping bruto
ls backend/data/ai_scraped/*_gemini_response.json
# Resultado: 31 archivos

# Ver eventos curados
ls backend/data/curated/curated_*_gemini_response.json
# Resultado: 31 archivos

# Ver consolidado
cat backend/data/curated/all_curated_*.json | jq '.stats'
```

---

## 🗺️ REGIONES PENDIENTES (49 regiones)

### Ecuador - 1 región
- Manabí (Portoviejo)

### Bolivia - 4 regiones
- La Paz
- Santa Cruz
- Cochabamba
- Chuquisaca

### Paraguay - 4 regiones
- Asunción
- Central
- Alto Paraná
- Itapúa

### Uruguay - 4 regiones
- Montevideo
- Canelones
- Maldonado
- Salto

### Costa Rica - 4 regiones
- San José
- Alajuela
- Cartago
- Heredia

### Panamá - 4 regiones
- Panamá
- Colón
- Chiriquí
- Bocas del Toro

### Guatemala - 4 regiones
- Guatemala
- Quetzaltenango
- Escuintla
- Alta Verapaz

### Honduras - 4 regiones
- Francisco Morazán (Tegucigalpa)
- Cortés (San Pedro Sula)
- Atlántida (La Ceiba)
- Islas de la Bahía (Roatán)

### El Salvador - 4 regiones
- San Salvador
- La Libertad
- Santa Ana
- San Miguel

### Nicaragua - 4 regiones
- Managua
- León
- Granada
- Masaya

### República Dominicana - 4 regiones
- Distrito Nacional (Santo Domingo)
- Santo Domingo
- Santiago
- La Altagracia (Punta Cana)

### Cuba - 4 regiones
- La Habana
- Santiago de Cuba
- Villa Clara
- Matanzas

### Puerto Rico - 4 regiones
- San Juan
- Bayamón
- Ponce
- Mayagüez

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno (.env)
```bash
# MySQL Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/eventos_db

# Gemini API (opcional - usa web interface)
GEMINI_API_KEY=tu_api_key_aqui
```

### Archivos de Configuración
- **Regiones:** `backend/data/latinamerica_regions_sample.json` (80 regiones)
- **Prompt:** `backend/scripts/prompt_config.py` (editable)
- **Pipeline:** `backend/automation/autonomous_scraping_pipeline.py`

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "Playwright no instalado"
```bash
pip install playwright
playwright install
```

### Error: "No se puede conectar a MySQL"
```bash
# Verificar que MySQL está corriendo
netstat -ano | findstr :3306

# Verificar credenciales en .env
cat .env | grep DATABASE_URL
```

### Error: "Browser se queda colgado"
- El script usa `headless=True` (sin UI)
- Cada región tiene timeout de 20s
- Si falla, continúa con la siguiente

### Ver logs en tiempo real
```bash
cd backend
python automation/autonomous_scraping_pipeline.py --mode continue 2>&1 | tee scraping.log
```

---

## 📈 MONITOREO DEL PROGRESO

### Ver eventos insertados en tiempo real
```sql
-- Abrir MySQL Workbench o CLI
SELECT COUNT(*), country
FROM events
WHERE source = 'gemini_auto'
GROUP BY country
ORDER BY COUNT(*) DESC;
```

### Ver archivos generados
```bash
# Contar regiones procesadas
ls backend/data/ai_scraped/*_gemini_response.json | wc -l

# Ver últimas 5 regiones procesadas
ls -lt backend/data/ai_scraped/*.json | head -5
```

### Verificar scraping_runs
```sql
SELECT * FROM scraping_runs
ORDER BY started_at DESC
LIMIT 10;
```

---

## 🎯 RESULTADOS ESPERADOS

### Al finalizar (80/80 regiones)
```
📊 ESTADÍSTICAS FINALES
═══════════════════════════════════════════════════════════
🔍 Regiones scrapeadas:      49
📥 Eventos encontrados:       ~150-200
✅ Eventos curados:           ~125-170 (85% calidad)
💾 Eventos insertados:        ~125-170
🔄 Eventos actualizados:      ~10-20
❌ Errores:                   <5
═══════════════════════════════════════════════════════════
```

### Base de datos final
```sql
SELECT COUNT(*) FROM events WHERE source = 'gemini_auto';
-- Esperado: ~220-270 eventos totales (97 actuales + 125-170 nuevos)
```

---

## 📝 SIGUIENTE PASO DESPUÉS DEL SCRAPING

Una vez completado el scraping autónomo:

### 1. Verificar calidad de datos
```bash
cd backend
python -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    result = conn.execute('SELECT country, COUNT(*) as total FROM events WHERE source=\"gemini_auto\" GROUP BY country')
    print('\n📊 EVENTOS POR PAÍS:')
    for row in result:
        print(f'{row[0]:25} {row[1]:>5} eventos')
"
```

### 2. Mejorar fechas (opcional)
Las fechas actualmente están en texto ("7 y 8 de noviembre de 2025").
Considerar crear parser de fechas en español.

### 3. Enriquecer con APIs reales (Opcional)
- Eventbrite API
- Ticketmaster API
- Meetup API

### 4. Probar en Frontend
```bash
cd frontend
npm run dev
# Abrir http://localhost:5174
# Buscar eventos por ciudad
```

---

## 🚨 NOTAS IMPORTANTES

### ⚠️ Limitaciones Conocidas
1. **Fechas en texto:** No parseadas a datetime (usa 2025-12-31 genérica)
2. **Brasil bajo rendimiento:** Eventos no pasan validación (info pobre)
3. **Regiones sin eventos:** CABA, Ciudad de México, Mendoza

### ✅ Funcionando Perfectamente
1. **Imágenes:** 100% de eventos con imagen de calidad
2. **Duplicados:** Sistema de detección funcionando (0 duplicados)
3. **Validación:** 83.9% de eventos pasan filtros de calidad
4. **Inserción DB:** Sin errores, manejo de duplicados correcto

### 🔄 Delays y Rate Limiting
- **5 segundos** entre regiones
- **10 segundos** entre países
- **20 segundos** esperando respuesta de Gemini

**Tiempo total estimado:** 2.5-3 horas para 49 regiones

---

## 📞 COMANDOS DE EMERGENCIA

### Cancelar ejecución
```bash
Ctrl + C  # Interrumpir pipeline
```

### Limpiar y reiniciar
```bash
# NO HACER A MENOS QUE SEA NECESARIO
# Esto borra todo el progreso

# Opción 1: Solo limpiar scraped (mantener curated y DB)
rm backend/data/ai_scraped/*_gemini_response.json

# Opción 2: Limpiar todo (PELIGROSO)
rm backend/data/ai_scraped/*_gemini_response.json
rm backend/data/curated/curated_*_gemini_response.json
# DB: DELETE FROM events WHERE source = 'gemini_auto';
```

### Ver proceso corriendo
```bash
# Windows
tasklist | findstr python

# Si necesitas matar el proceso
taskkill /F /PID <pid>
```

---

## 🎉 ÉXITO

Cuando veas este mensaje, el scraping está completo:

```
═══════════════════════════════════════════════════════════
📊 ESTADÍSTICAS FINALES DEL PIPELINE
═══════════════════════════════════════════════════════════
🔍 Regiones scrapeadas:      49
📥 Eventos encontrados:       XXX
✅ Eventos curados:           XXX
💾 Eventos insertados:        XXX
🔄 Eventos actualizados:      XX
❌ Errores:                   X
═══════════════════════════════════════════════════════════
```

**¡Sistema listo para producción!** 🚀

---

## 📚 ARCHIVOS DE REFERENCIA

- `PROGRESS_SCRAPING.md` - Estado actual detallado
- `autonomous_scraping_pipeline.py` - Script principal
- `curate_ai_events.py` - Curador de eventos
- `process_scraped.py` - Inserción a DB
- `latinamerica_regions_sample.json` - 80 regiones

---

**Última ejecución exitosa:** 2025-11-09 08:00
**Eventos en DB:** 97 eventos
**Próximo paso:** Ejecutar `--mode continue` para completar
