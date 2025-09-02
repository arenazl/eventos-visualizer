# 🎪 TICKETMASTER PLAYWRIGHT SCRAPER

Scraper avanzado para extraer eventos de Ticketmaster usando Playwright para manejar contenido dinámico.

## 🚀 INSTALACIÓN RÁPIDA

### 1. Ejecutar instalador automático:
```bash
./install_playwright.sh
```

### 2. Probar el scraper:
```bash
python3 test_ticketmaster_simple.py
```

## 📋 INSTALACIÓN MANUAL

Si prefieres instalar manualmente:

```bash
# Instalar Playwright
pip3 install playwright

# Descargar navegadores (~100MB)
python3 -m playwright install

# Instalar dependencias del sistema
python3 -m playwright install-deps
```

## 🎯 CARACTERÍSTICAS

### ✅ **Funcionalidades:**
- Búsqueda por query (ciudad, artista, evento)
- Soporte para múltiples dominios por país
- Extracción automática de datos de eventos
- Manejo de contenido dinámico con JavaScript
- Fallback jerárquico (Ciudad → Provincia → País)

### 🌍 **Países Soportados:**
- 🇺🇸 Estados Unidos: `ticketmaster.com`
- 🇪🇸 España: `ticketmaster.es` 
- 🇫🇷 Francia: `ticketmaster.fr`
- 🇩🇪 Alemania: `ticketmaster.de`
- 🇲🇽 México: `ticketmaster.com.mx`
- 🇨🇦 Canadá: `ticketmaster.ca`
- 🇬🇧 Reino Unido: `ticketmaster.co.uk`
- 🇦🇺 Australia: `ticketmaster.com.au`

## 💡 USO BÁSICO

### Importar y usar:
```python
from services.ticketmaster_playwright_scraper import TicketmasterPlaywrightScraper

# Crear scraper
scraper = TicketmasterPlaywrightScraper()

# Buscar eventos
events = await scraper.search_events("concerts", "usa", max_events=10)

# Buscar por ubicación
events = await scraper.search_by_location("New York", "usa")
```

### Ejemplo de evento extraído:
```json
{
  "title": "Taylor Swift - Eras Tour",
  "date": "2025-07-15 20:00",
  "venue": "MetLife Stadium",
  "price": "$89.50 - $250.00",
  "url": "https://www.ticketmaster.com/event/abc123",
  "source": "ticketmaster",
  "scraped_at": "2025-09-02T18:30:00.000Z"
}
```

## 🔧 INTEGRACIÓN CON SISTEMA DE INTENT

### Integrar con el sistema de fallback jerárquico:
```python
# En tu factory pattern
async def get_ticketmaster_events(hierarchy):
    scraper = TicketmasterPlaywrightScraper()
    
    # 1. Intentar con ciudad específica
    events = await scraper.search_by_location(
        hierarchy['city'], 
        hierarchy['country']
    )
    
    # 2. Fallback a provincia si no hay eventos
    if not events and hierarchy['region']:
        events = await scraper.search_by_location(
            hierarchy['region'], 
            hierarchy['country']
        )
    
    # 3. Fallback a país completo
    if not events:
        events = await scraper.search_events(
            hierarchy['country'], 
            hierarchy['country']
        )
    
    return events
```

## ⚠️ CONSIDERACIONES

### **Rendimiento:**
- Primera ejecución: ~10-15 segundos (carga navegador)
- Búsquedas subsecuentes: ~5-8 segundos
- Memoria: ~150-200MB durante scraping

### **Limitaciones:**
- Ticketmaster puede detectar y bloquear bots
- Estructura de la página puede cambiar
- Requiere conexión a internet estable
- Algunos eventos pueden requerir login

### **Recomendaciones:**
- Usar delays entre requests
- Implementar retry logic
- Rotar user agents
- Cache resultados para evitar requests repetidos

## 🐛 TROUBLESHOOTING

### Error: "Chromium distribution not found"
```bash
python3 -m playwright install chromium
```

### Error: "playwright not installed"
```bash
pip3 install playwright
```

### Error: "Permission denied"
```bash
chmod +x install_playwright.sh
```

### Error: "No events found"
- Verificar que la página carga correctamente
- Probar con diferentes queries
- Revisar logs para ver selectores CSS

## 📊 LOGS Y DEBUG

Para ver logs detallados:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎯 ROADMAP

- [ ] Soporte para filtros (fecha, precio, categoría)
- [ ] Integración con proxy rotation
- [ ] Cache inteligente de resultados  
- [ ] Soporte para múltiples páginas de resultados
- [ ] Detección automática de cambios en selectores

---

**¡El scraper está listo para usar con tu sistema de Intent Recognition y Factory Pattern!** 🚀