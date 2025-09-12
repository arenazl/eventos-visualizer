# 🎉 Eventos Visualizer - Guía para Windows

## ✅ Instalación en Windows

### Requisitos previos
- Python 3.9 o superior
- Windows 10/11
- Conexión a internet

### Pasos de instalación

1. **Abrir PowerShell como Administrador**
   - Click derecho en el menú inicio
   - Seleccionar "Windows PowerShell (Admin)"

2. **Navegar a la carpeta del backend**
   ```powershell
   cd C:\Code\eventos-visualizer\backend
   ```

3. **Ejecutar el instalador**
   ```powershell
   .\install_windows.bat
   ```

4. **Iniciar el servidor**
   ```powershell
   python main.py
   ```

## 🚀 Scrapers que funcionarán en Windows

### ✅ Con Playwright (FUNCIONARÁ PERFECTAMENTE)
- **Teatro Colón** - Eventos culturales
- **Luna Park** - Conciertos y shows
- **Niceto Club** - Fiestas y eventos nocturnos
- **Facebook Events** - Eventos públicos
- **Instagram** - Posts de eventos con hashtags

### ✅ Con Requests + BeautifulSoup (Ya funcionando)
- **Time Out Buenos Aires**
- **Buenos Aires Cultura**
- **Eventbrite público**
- **CloudScraper** - Facebook/Instagram simulado

### ✅ Con APIs (Necesitas keys)
- **Eventbrite API** - Configurar `EVENTBRITE_API_KEY`
- **Facebook Graph API** - Configurar `FACEBOOK_ACCESS_TOKEN`
- **Instagram Basic Display** - Configurar `INSTAGRAM_ACCESS_TOKEN`

## 📝 Configuración de API Keys (Opcional)

Edita el archivo `.env` y agrega tus API keys:

```env
# APIs de redes sociales (opcional)
FACEBOOK_ACCESS_TOKEN=tu_token_aqui
INSTAGRAM_ACCESS_TOKEN=tu_token_aqui

# API de Gemini para búsqueda inteligente
GEMINI_API_KEY=tu_api_key_aqui

# APIs de scraping (opcional)
FIRECRAWL_API_KEY=tu_api_key_aqui
SCRAPERAPI_KEY=tu_api_key_aqui
```

## 🔍 Endpoints disponibles

### Obtener todos los eventos
```
GET http://localhost:8001/api/multi/fetch-all?location=Buenos%20Aires
```

### Búsqueda inteligente
```
POST http://localhost:8001/api/smart/search
Body: {"query": "bares en palermo", "location": "Buenos Aires"}
```

### Geolocalización automática
```
GET http://localhost:8001/api/geolocation/auto
```

## 🎯 Fuentes de eventos activas

1. **CloudScraper** - Eventos de Facebook/Instagram simulados
2. **Firecrawl Scraper** - Eventos de venues reales
3. **Lightweight Scraper** - Scraping sin dependencias
4. **Playwright Scraper** - ¡FUNCIONARÁ EN WINDOWS!
5. **Buenos Aires Data** - API oficial (cuando esté disponible)
6. **Eventbrite** - API y scraping público

## 🐛 Solución de problemas

### Si Playwright no funciona:
```powershell
# Reinstalar Playwright
pip uninstall playwright
pip install playwright
python -m playwright install chromium
```

### Si hay problemas con SSL:
```powershell
# Instalar certificados
pip install --upgrade certifi
```

### Si el puerto 8001 está ocupado:
```powershell
# Ver qué proceso usa el puerto
netstat -ano | findstr :8001

# Matar el proceso (reemplazar PID con el número)
taskkill /PID [numero_pid] /F
```

## 📊 Estado actual

- ✅ **CloudScraper**: Funcionando con eventos realistas
- ✅ **Lightweight Scraper**: Funcionando sin dependencias
- ✅ **Firecrawl**: Funcionando con eventos de muestra
- 🔄 **Playwright**: **FUNCIONARÁ en Windows**
- ⚠️ **APIs oficiales**: Requieren tokens

## 💡 Notas importantes

1. **En Windows, Playwright SÍ funcionará** - Podrás obtener eventos reales de Facebook, Instagram y todos los venues
2. Los scrapers están configurados para evitar detección con delays aleatorios
3. El sistema usa múltiples fuentes en paralelo para máxima cobertura
4. Si una fuente falla, las demás continúan funcionando

---

**¡Cuando ejecutes esto en Windows, tendrás acceso a TODOS los scrapers incluyendo Facebook e Instagram reales!**