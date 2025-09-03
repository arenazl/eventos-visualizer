# 🚀 GUÍA COMPLETA: DESPLIEGUE EN HEROKU

## ✅ ESTADO ACTUAL
- ✅ **Backend**: Configurado con Procfile y requirements.txt
- ✅ **Frontend**: Build completo en `/frontend/dist/`
- ✅ **Configuración**: Variables de entorno preparadas
- ✅ **APIs**: Integradas y funcionando localmente

---

## 📋 PASO A PASO: DESPLIEGUE HEROKU

### **1. PREPARAR HEROKU CLI**
```bash
# Instalar Heroku CLI (si no lo tienes)
curl https://cli-assets.heroku.com/install.sh | sh

# Hacer login
heroku login

# Verificar
heroku --version
```

### **2. CREAR APLICACIÓN HEROKU**
```bash
cd /mnt/c/Code/eventos-visualizer/backend

# Crear app (cambiar 'tu-nombre' por tu nombre único)
heroku create eventos-visualizer-backend-tu-nombre

# Verificar
heroku apps
```

### **3. CONFIGURAR BASE DE DATOS POSTGRESQL**
```bash
# Agregar PostgreSQL (gratis hasta 10,000 rows)
heroku addons:create heroku-postgresql:essential-0 --app eventos-visualizer-backend-tu-nombre

# Verificar DATABASE_URL se creó automáticamente
heroku config --app eventos-visualizer-backend-tu-nombre
```

### **4. CONFIGURAR VARIABLES DE ENTORNO**
```bash
# Variables esenciales
heroku config:set HOST=0.0.0.0 --app eventos-visualizer-backend-tu-nombre

# API Keys (reemplazar con tus keys reales)
heroku config:set GEMINI_API_KEY=tu_gemini_key_aqui --app eventos-visualizer-backend-tu-nombre
heroku config:set EVENTBRITE_API_KEY=tu_eventbrite_key --app eventos-visualizer-backend-tu-nombre
heroku config:set TICKETMASTER_API_KEY=tu_ticketmaster_key --app eventos-visualizer-backend-tu-nombre

# Variables opcionales
heroku config:set REDIS_URL=redis://localhost:6379 --app eventos-visualizer-backend-tu-nombre
```

### **5. DESPLEGAR BACKEND**
```bash
# Asegurarse de estar en directorio backend
cd /mnt/c/Code/eventos-visualizer/backend

# Inicializar git (si no existe)
git init
git add .
git commit -m "Deploy to Heroku: Backend with EventOrchestrator and Argentina Factory"

# Conectar con Heroku
heroku git:remote -a eventos-visualizer-backend-tu-nombre

# Deploy
git push heroku main
```

### **6. VERIFICAR BACKEND**
```bash
# Ver logs en tiempo real
heroku logs --tail --app eventos-visualizer-backend-tu-nombre

# Abrir app en browser
heroku open --app eventos-visualizer-backend-tu-nombre

# Probar endpoints
curl https://eventos-visualizer-backend-tu-nombre.herokuapp.com/health
curl https://eventos-visualizer-backend-tu-nombre.herokuapp.com/api/events?limit=5
```

### **7. DESPLEGAR FRONTEND**

#### **OPCIÓN A: NETLIFY (Recomendado)**
1. Ve a [netlify.com](https://netlify.com)
2. Haz login con GitHub/Google
3. Arrastra la carpeta `/frontend/dist/` a la página
4. En Site Settings → Environment Variables:
   - `VITE_API_URL`: `https://eventos-visualizer-backend-tu-nombre.herokuapp.com`

#### **OPCIÓN B: VERCEL**
```bash
cd /mnt/c/Code/eventos-visualizer/frontend

# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Durante setup, configurar:
# VITE_API_URL=https://eventos-visualizer-backend-tu-nombre.herokuapp.com
```

#### **OPCIÓN C: GitHub Pages**
```bash
# Push frontend a repo GitHub
cd /mnt/c/Code/eventos-visualizer/frontend
git init
git add .
git commit -m "Frontend build"
git remote add origin https://github.com/tu-usuario/eventos-frontend.git
git push -u origin main

# Ir a GitHub → Settings → Pages → Deploy from main/dist
```

---

## 🔧 CONFIGURACIÓN AVANZADA

### **Variables de Entorno Completas**
```bash
# APIs Esenciales
heroku config:set GEMINI_API_KEY=tu_key
heroku config:set EVENTBRITE_API_KEY=tu_key  
heroku config:set TICKETMASTER_API_KEY=tu_key
heroku config:set MEETUP_API_KEY=tu_key

# APIs Adicionales (Opcionales)
heroku config:set SPOTIFY_CLIENT_ID=tu_id
heroku config:set SPOTIFY_CLIENT_SECRET=tu_secret
heroku config:set GOOGLE_MAPS_API_KEY=tu_key
heroku config:set OPENAI_API_KEY=tu_key

# Configuración
heroku config:set HOST=0.0.0.0
heroku config:set ENVIRONMENT=production
```

### **Comandos Útiles Post-Deploy**
```bash
# Ver logs
heroku logs --tail --app tu-app

# Ejecutar comandos en servidor
heroku run python -c "print('Hello Heroku')" --app tu-app

# Escalar dynos
heroku ps:scale web=1 --app tu-app

# Info de la app
heroku info --app tu-app

# Variables actuales
heroku config --app tu-app
```

---

## 🎯 TESTING FINAL

### **Backend Endpoints a Probar**
```bash
# Health check
curl https://tu-app.herokuapp.com/health

# Eventos por ubicación
curl https://tu-app.herokuapp.com/api/events?location=Buenos%20Aires&limit=10

# EventOrchestrator completo
curl https://tu-app.herokuapp.com/api/events?location=Mendoza&limit=30

# Argentina Factory
curl https://tu-app.herokuapp.com/api/events?location=Córdoba&limit=20

# Smart search
curl -X POST https://tu-app.herokuapp.com/api/smart/search \
  -H "Content-Type: application/json" \
  -d '{"query": "conciertos", "location": "Buenos Aires"}'
```

### **Frontend URLs a Verificar**
```
https://tu-frontend-url.netlify.app/
https://tu-frontend-url.netlify.app/?location=Buenos%20Aires
https://tu-frontend-url.netlify.app/?search=música
```

---

## 🚨 TROUBLESHOOTING

### **Error: Build Failed**
```bash
# Ver logs detallados
heroku logs --tail --app tu-app

# Verificar requirements.txt
cat requirements.txt

# Rebuild
git add . && git commit -m "fix" && git push heroku main
```

### **Error: Database Connection**
```bash
# Verificar DATABASE_URL
heroku config:get DATABASE_URL --app tu-app

# Conectar a DB manualmente
heroku pg:psql --app tu-app
```

### **Error: App Crash**
```bash
# Ver estado
heroku ps --app tu-app

# Restart
heroku restart --app tu-app

# Logs específicos
heroku logs --source app --app tu-app
```

---

## ✅ CHECKLIST FINAL

- [ ] Heroku CLI instalado y login exitoso
- [ ] App Heroku creada
- [ ] PostgreSQL addon agregado
- [ ] Variables de entorno configuradas
- [ ] Backend deployado exitosamente
- [ ] Health endpoint responde OK
- [ ] Frontend deployado en Netlify/Vercel
- [ ] Frontend conecta con backend en Heroku
- [ ] URLs de producción funcionando
- [ ] EventOrchestrator ejecutándose
- [ ] Argentina Factory integrado
- [ ] APIs externas funcionando

---

**🎉 ¡Felicitaciones! Tu aplicación está en producción.**

**URLs Finales:**
- Backend: `https://eventos-visualizer-backend-tu-nombre.herokuapp.com`
- Frontend: `https://tu-app.netlify.app`
- Health: `https://eventos-visualizer-backend-tu-nombre.herokuapp.com/health`