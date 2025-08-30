# 📋 Setup y Configuración - Eventos Visualizer

## 🔑 Variables de Entorno Necesarias

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

### **APIs Externas (OBLIGATORIAS)**
```env
# Eventbrite API
EVENTBRITE_API_KEY=your_eventbrite_personal_oauth_token
EVENTBRITE_API_URL=https://www.eventbriteapi.com/v3

# Ticketmaster Discovery API  
TICKETMASTER_API_KEY=your_ticketmaster_consumer_key
TICKETMASTER_API_URL=https://app.ticketmaster.com/discovery/v2

# Meetup API
MEETUP_API_KEY=your_meetup_api_key
MEETUP_API_URL=https://api.meetup.com

# Facebook Events (Opcional)
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
```

### **Google Services**
```env
# Google Calendar API
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://172.29.228.80:8001/auth/google/callback

# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_javascript_api_key
```

### **Base de Datos**
```env
# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/eventos_db
# O si usas servicio cloud:
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis (para cache)
REDIS_URL=redis://localhost:6379/0
```

### **Aplicación**
```env
# FastAPI
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Origins
CORS_ORIGINS=["http://172.29.228.80:5174", "http://localhost:5174"]

# Push Notifications (Web Push)
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_CLAIMS={"sub": "mailto:your-email@example.com"}
```

## 🚀 Cómo Obtener API Keys

### **1. Eventbrite API Key**
1. Ve a https://www.eventbrite.com/account-settings/apps
2. Crear nueva aplicación
3. Copia tu "Personal OAuth token"

### **2. Ticketmaster API Key**
1. Regístrate en https://developer.ticketmaster.com/
2. Crear nueva aplicación
3. Copia tu "Consumer Key" (esto es tu API key)

### **3. Meetup API Key**  
1. Ve a https://secure.meetup.com/meetup_api/key/
2. Inicia sesión con tu cuenta Meetup
3. Copia tu API key

### **4. Google APIs Setup**
1. Ve a https://console.cloud.google.com/
2. Crear nuevo proyecto
3. Habilitar APIs: Calendar API, Maps JavaScript API
4. Crear credenciales OAuth 2.0
5. Configurar redirect URI

## 🐳 Setup con Docker (Recomendado)

### **docker-compose.yml**
```yaml
version: '3.8'
services:
  postgres:
    image: postgis/postgis:14-3.2
    environment:
      POSTGRES_USER: eventos_user
      POSTGRES_PASSWORD: eventos_pass
      POSTGRES_DB: eventos_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### **Comandos de Setup**
```bash
# 1. Clonar/navegar al proyecto
cd eventos-visualizer

# 2. Iniciar servicios de base
docker-compose up -d postgres redis

# 3. Instalar dependencias backend
cd backend
pip install -r requirements.txt

# 4. Instalar dependencias frontend  
cd ../frontend
npm install

# 5. Configurar base de datos
cd ../backend
alembic upgrade head

# 6. Iniciar servicios
# Terminal 1 - Backend (puerto 8001)
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Frontend (puerto 5174)
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5174
```

## 🗺️ Setup Local sin Docker

### **PostgreSQL con PostGIS**
```bash
# Ubuntu/WSL
sudo apt update
sudo apt install postgresql postgresql-contrib postgis

# Crear base de datos
sudo -u postgres createdb eventos_db
sudo -u postgres psql eventos_db -c "CREATE EXTENSION postgis;"

# Crear usuario
sudo -u postgres psql -c "CREATE USER eventos_user WITH PASSWORD 'eventos_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE eventos_db TO eventos_user;"
```

### **Redis**
```bash
# Ubuntu/WSL
sudo apt install redis-server
sudo systemctl start redis-server
```

## 📱 PWA Setup

### **manifest.json** (se genera automáticamente)
```json
{
  "name": "Eventos Visualizer",
  "description": "Descubre eventos cerca de ti",
  "theme_color": "#8B5CF6",
  "background_color": "#FFFFFF",
  "display": "standalone",
  "start_url": "/",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192", 
      "type": "image/png"
    }
  ]
}
```

## 🔔 Push Notifications Setup

### **Generar VAPID Keys**
```bash
# Con web-push CLI
npm install -g web-push
web-push generate-vapid-keys

# Agregar keys al .env
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
```

## ✅ Verificación de Setup

### **Health Checks**
```bash
# Backend health
curl http://172.29.228.80:8001/health

# Eventbrite API test
curl http://172.29.228.80:8001/api/events?source=eventbrite&limit=3

# Frontend accessible
curl http://172.29.228.80:5174

# Database connection
psql $DATABASE_URL -c "SELECT version();"

# Redis connection  
redis-cli ping
```

## 🚨 Troubleshooting

### **Puerto ya en uso**
```bash
# Liberar puertos
lsof -ti:8001 | xargs kill -9
lsof -ti:5174 | xargs kill -9
```

### **Base de datos no conecta**
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Test connection manual
psql $DATABASE_URL -c "SELECT 1;"
```

### **APIs no responden**
- Verificar que API keys estén en .env correcto
- Check rate limits en documentación de cada API
- Verificar firewall/proxy no bloquee requests

## 📋 Checklist Final

- [ ] Todas las API keys configuradas en .env
- [ ] PostgreSQL + PostGIS funcionando
- [ ] Redis funcionando  
- [ ] Backend inicia en puerto 8001
- [ ] Frontend inicia en puerto 5174
- [ ] Templates HTML en docs/templates/
- [ ] Database migrations aplicadas
- [ ] Health checks pasan

¡Con este setup tienes todo listo para ejecutar los comandos de Claude Code!
