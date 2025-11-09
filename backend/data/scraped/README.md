# 📂 Carpeta de Eventos Scrapeados

Esta carpeta contiene eventos scrapeados manualmente con **Claude Desktop + BrightData MCP**.

## 🔄 WORKFLOW COMPLETO

### **1️⃣ SCRAPEAR (en Claude Desktop)**

Porque Claude Code no tiene acceso a MCPs, **scrapear en Claude Desktop**:

```
Prompt para Claude Desktop:
"Usá BrightData para scrapear eventos en Buenos Aires para diciembre 2025.
Dame el resultado en JSON con esta estructura:

{
  "ubicacion": "Buenos Aires, Argentina",
  "fecha_consulta": "2025-11-02",
  "fuente": "BrightData (Google)",
  "eventos_confirmados_o_tradicionales": [
    {
      "numero": 1,
      "nombre": "Lollapalooza Argentina 2025",
      "fecha": "Sábado 14 de diciembre de 2025",
      "descripcion": "Festival de música internacional",
      "tipo": "Música",
      "lugar": "Hipódromo de San Isidro",
      "precio": "Desde $50000",
      "hora": "12:00"
    }
  ]
}
"
```

### **2️⃣ GUARDAR JSON**

Guardar el resultado en:
```
backend/data/scraped/buenos_aires_2025-11-02.json
```

Formato de nombre: `ciudad_fecha.json`

### **3️⃣ PROCESAR (desde VSCode/Claude Code)**

```bash
# Opción 1: Procesar un archivo específico
cd c:/Code/eventos-visualizer/backend/batch
python process_scraped.py ../data/scraped/buenos_aires_2025-11-02.json

# Opción 2: Procesar todos los pendientes
python process_scraped.py --all
```

El script automáticamente:
- ✅ Lee el JSON
- ✅ Normaliza eventos al formato DB
- ✅ Sube a MySQL Aiven
- ✅ Registra la corrida en `scraping_runs`
- ✅ Evita duplicados (por `external_id`)

## 📊 VERIFICAR RESULTADOS

```bash
# Ver stats de eventos
curl http://localhost:8001/api/db/events/stats

# Ver eventos de una ciudad
curl "http://localhost:8001/api/db/events/?city=Buenos%20Aires&limit=10"

# Ver última corrida de scraping
SELECT * FROM scraping_runs ORDER BY started_at DESC LIMIT 1;
```

## 🗂️ ESTRUCTURA JSON ACEPTADA

El procesador acepta múltiples formatos:

### Formato 1 (BrightData):
```json
{
  "ubicacion": "Buenos Aires, Argentina",
  "eventos_confirmados_o_tradicionales": [
    {
      "nombre": "Evento",
      "fecha": "2025-12-14",
      "tipo": "Música",
      "lugar": "Venue"
    }
  ]
}
```

### Formato 2 (Simple):
```json
{
  "city": "Buenos Aires",
  "country": "Argentina",
  "events": [
    {
      "title": "Evento",
      "date": "2025-12-14",
      "category": "Música",
      "venue": "Venue"
    }
  ]
}
```

## ⚠️ NOTA IMPORTANTE

**Esta carpeta está en `.gitignore`** para no commitear datos privados.

Solo se commitea este README.
