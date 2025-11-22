<!-- AUDIT_HEADER
🕒 ÚLTIMA ACTUALIZACIÓN: 2025-11-22 12:00
📊 STATUS: ACTIVE
📝 HISTORIAL:
- 2025-11-22 12:00: Creación de guía completa Netlify + Heroku
📋 TAGS: #deployment #netlify #heroku #frontend #backend #produccion
-->

# 🚀 Guía Completa de Deployment: Netlify + Heroku

## 📋 Arquitectura de Producción

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCCIÓN                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────┐         ┌─────────────────┐           │
│   │    NETLIFY      │         │     HEROKU      │           │
│   │   (Frontend)    │ ──────▶ │    (Backend)    │           │
│   │   React + Vite  │   API   │    FastAPI      │           │
│   │   Puerto: 443   │         │    Puerto: $PORT│           │
│   └─────────────────┘         └────────┬────────┘           │
│                                        │                     │
│                               ┌────────▼────────┐           │
│                               │   PostgreSQL    │           │
│                               │  (Heroku Add-on)│           │
│                               └─────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 PARTE 1: Frontend en Netlify

### 1.1 Pre-requisitos

- Cuenta en [Netlify](https://netlify.com)
- Repositorio en GitHub/GitLab/Bitbucket
- Node.js 18+ instalado localmente

### 1.2 Preparar el Frontend

#### Crear archivo `netlify.toml` en `/frontend/`:

```toml
[build]
  base = "frontend"
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"

# Redirecciones para SPA (React Router)
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

# Headers de seguridad
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"

# Cache para assets estáticos
[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

#### Crear archivo `.env.production` en `/frontend/`:

```env
# URL del backend en Heroku (reemplazar con tu URL real)
VITE_API_URL=https://tu-app-backend.herokuapp.com

# Frontend en producción:
# https://funaroundyou.netlify.app/
```

#### Verificar `vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false, // Desactivar en producción
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['lucide-react', '@heroicons/react']
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})
```

### 1.3 Deploy en Netlify

#### Opción A: Deploy desde CLI

```bash
# Instalar Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Inicializar proyecto (desde /frontend)
cd frontend
netlify init

# Build local para verificar
npm run build

# Deploy preview
netlify deploy

# Deploy a producción
netlify deploy --prod
```

#### Opción B: Deploy desde Dashboard

1. Ve a [app.netlify.com](https://app.netlify.com)
2. Click en **"Add new site"** → **"Import an existing project"**
3. Conecta tu repositorio de GitHub
4. Configura:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
5. En **"Environment variables"** agrega:
   - `VITE_API_URL` = `https://tu-backend.herokuapp.com`
6. Click **"Deploy site"**

### 1.4 Configurar Dominio Personalizado (Opcional)

```bash
# Agregar dominio
netlify domains:add tu-dominio.com

# Verificar DNS
netlify dns
```

O desde el Dashboard:
1. **Site settings** → **Domain management**
2. **Add custom domain**
3. Configura los DNS según las instrucciones

### 1.5 Variables de Entorno en Netlify

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `VITE_API_URL` | `https://tu-backend.herokuapp.com` | URL del backend |
| `NODE_VERSION` | `18` | Versión de Node.js |

---

## 🔧 PARTE 2: Backend en Heroku

### 2.1 Pre-requisitos

- Cuenta en [Heroku](https://heroku.com)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalado
- Git configurado

### 2.2 Archivos de Configuración

#### `Procfile` (en `/backend/`):

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### `runtime.txt` (en `/backend/`):

```
python-3.11.7
```

#### Verificar `requirements.txt`:

El archivo ya existe con todas las dependencias necesarias.

### 2.3 Deploy en Heroku

```bash
# Login
heroku login

# Crear app
heroku create eventos-visualizer-api

# Agregar PostgreSQL
heroku addons:create heroku-postgresql:essential-0

# Configurar variables de entorno
heroku config:set HOST=0.0.0.0
heroku config:set GEMINI_API_KEY=tu_gemini_api_key
heroku config:set EVENTBRITE_API_KEY=tu_eventbrite_key
heroku config:set GOOGLE_MAPS_API_KEY=tu_google_maps_key

# Configurar CORS para Netlify
heroku config:set CORS_ORIGINS=https://funaroundyou.netlify.app

# Deploy (desde la raíz del proyecto)
git subtree push --prefix backend heroku main

# O si solo quieres deployar el backend:
cd backend
git init
heroku git:remote -a eventos-visualizer-api
git add .
git commit -m "Deploy backend"
git push heroku main
```

### 2.4 Variables de Entorno en Heroku

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `DATABASE_URL` | (automático) | URL de PostgreSQL |
| `PORT` | (automático) | Puerto asignado por Heroku |
| `HOST` | `0.0.0.0` | Host del servidor |
| `GEMINI_API_KEY` | `AIza...` | API Key de Google Gemini |
| `EVENTBRITE_API_KEY` | (opcional) | Para eventos de Eventbrite |
| `GOOGLE_MAPS_API_KEY` | (opcional) | Para geolocalización |
| `CORS_ORIGINS` | `https://funaroundyou.netlify.app` | Orígenes permitidos |
| `DEBUG` | `false` | Modo debug |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

### 2.5 Configurar CORS en el Backend

Asegúrate de que `main.py` tenga CORS configurado correctamente:

```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Obtener orígenes permitidos desde variables de entorno
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔗 PARTE 3: Conectar Frontend y Backend

### 3.1 Flujo de Configuración

1. **Primero**: Deploy el backend en Heroku
2. **Segundo**: Obtén la URL del backend (ej: `https://eventos-visualizer-api.herokuapp.com`)
3. **Tercero**: Configura `VITE_API_URL` en Netlify con esa URL
4. **Cuarto**: Deploy el frontend en Netlify

### 3.2 Verificar Conexión

```bash
# Verificar backend
curl https://tu-backend.herokuapp.com/health

# Respuesta esperada:
# {"status": "healthy", "timestamp": "..."}

# Verificar frontend
# Abrir https://tu-frontend.netlify.app en el navegador
# Verificar en DevTools > Network que las llamadas van al backend correcto
```

---

## 📊 PARTE 4: Monitoreo y Logs

### 4.1 Logs en Heroku

```bash
# Ver logs en tiempo real
heroku logs --tail

# Ver últimos 100 logs
heroku logs -n 100

# Filtrar por tipo
heroku logs --source app
```

### 4.2 Logs en Netlify

1. Dashboard → Tu sitio → **Deploys**
2. Click en un deploy → **Deploy log**
3. O en **Functions** → **Function logs** (si usas Netlify Functions)

### 4.3 Métricas

**Heroku:**
- Dashboard → Tu app → **Metrics**
- Muestra: Response time, throughput, memory, dyno load

**Netlify:**
- Dashboard → Tu sitio → **Analytics**
- Muestra: Page views, bandwidth, top pages

---

## 🔧 PARTE 5: Troubleshooting

### 5.1 Errores Comunes en Netlify

| Error | Causa | Solución |
|-------|-------|----------|
| `404 on refresh` | SPA routing | Agregar `_redirects` o `netlify.toml` |
| `Build failed` | Dependencies | Verificar `package.json` y Node version |
| `CORS error` | Backend no permite origen | Configurar CORS en backend |
| `API undefined` | Variable de entorno | Verificar `VITE_API_URL` |

**Archivo `_redirects`** (alternativa a netlify.toml):
```
/*    /index.html   200
```

### 5.2 Errores Comunes en Heroku

| Error | Causa | Solución |
|-------|-------|----------|
| `H10 - App crashed` | Error en código | `heroku logs --tail` |
| `H12 - Request timeout` | Proceso lento | Optimizar queries |
| `H14 - No web dynos` | Sin dynos activos | `heroku ps:scale web=1` |
| `R14 - Memory quota` | Mucha memoria | Optimizar código o upgrade plan |

```bash
# Reiniciar app
heroku restart

# Ver estado de dynos
heroku ps

# Escalar dynos
heroku ps:scale web=1
```

### 5.3 CORS Issues

Si tienes problemas de CORS:

1. **Verificar variable de entorno**:
```bash
heroku config:get CORS_ORIGINS
```

2. **Verificar en el código** que el middleware esté antes de las rutas:
```python
# PRIMERO middleware
app.add_middleware(CORSMiddleware, ...)

# DESPUÉS las rutas
@app.get("/health")
```

3. **Verificar headers en respuesta**:
```bash
curl -I -X OPTIONS https://tu-backend.herokuapp.com/api/events \
  -H "Origin: https://tu-frontend.netlify.app" \
  -H "Access-Control-Request-Method: GET"
```

---

## 🚀 PARTE 6: Deploy Automatizado (CI/CD)

### 6.1 GitHub Actions para Heroku

Crear `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy Backend to Heroku

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.14
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: "eventos-visualizer-api"
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
          appdir: "backend"
```

### 6.2 Netlify Auto-Deploy

Netlify automáticamente hace deploy cuando pusheas a la rama conectada. Para configurar:

1. Dashboard → **Site settings** → **Build & deploy**
2. **Continuous Deployment** → **Build settings**
3. Configurar rama y comandos

---

## 📝 PARTE 7: Checklist de Deploy

### Pre-Deploy

- [ ] Variables de entorno configuradas localmente
- [ ] Build local funciona (`npm run build` / `uvicorn main:app`)
- [ ] Tests pasan (si los hay)
- [ ] CORS configurado correctamente
- [ ] API Keys válidas

### Deploy Backend (Heroku)

- [ ] `Procfile` existe y es correcto
- [ ] `runtime.txt` con versión de Python
- [ ] `requirements.txt` actualizado
- [ ] Variables de entorno configuradas en Heroku
- [ ] PostgreSQL addon agregado
- [ ] `heroku logs --tail` no muestra errores
- [ ] `/health` responde correctamente

### Deploy Frontend (Netlify)

- [ ] `netlify.toml` o `_redirects` configurado
- [ ] `VITE_API_URL` apunta al backend de Heroku
- [ ] Build pasa sin errores
- [ ] Sitio carga correctamente
- [ ] Llamadas API funcionan (verificar en DevTools)

### Post-Deploy

- [ ] Probar flujo completo en producción
- [ ] Verificar que eventos cargan
- [ ] Probar búsqueda de eventos
- [ ] Verificar en móvil
- [ ] Configurar alertas/monitoreo

---

## 🔗 URLs de Referencia

- **Netlify Docs**: https://docs.netlify.com/
- **Heroku Docs**: https://devcenter.heroku.com/
- **Vite Deploy Guide**: https://vitejs.dev/guide/static-deploy.html
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/

---

## 💡 Tips Finales

1. **Usa staging environments**: Crea apps separadas para testing
2. **Monitorea costos**: Heroku y Netlify tienen límites en planes gratuitos
3. **Backups**: Configura backups automáticos de PostgreSQL
4. **SSL**: Ambos servicios proveen SSL automático
5. **Custom domains**: Configura HTTPS para dominios personalizados

---

**Última actualización**: 2025-11-22
