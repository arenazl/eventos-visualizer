# 🚀 Deploy Eventos Visualizer Backend a Heroku

## 📋 Prerequisites

1. **Heroku CLI** ✅ (Ya instalado)
2. **Git** ✅ (Ya configurado)
3. **Cuenta Heroku** (necesaria)

## 🚀 Pasos para Deploy

### 1. Login a Heroku
```bash
heroku login
```

### 2. Crear App de Heroku
```bash
heroku create eventos-visualizer-backend-[timestamp]
```

### 3. Agregar PostgreSQL
```bash
heroku addons:create heroku-postgresql:essential-0
```

### 4. Configurar Variables de Entorno
```bash
# Variables básicas
heroku config:set HOST=0.0.0.0
heroku config:set BACKEND_PORT=$PORT

# APIs (reemplaza con tus keys reales)
heroku config:set EVENTBRITE_API_KEY=tu_key_aqui
heroku config:set GEMINI_API_KEY=tu_key_aqui
heroku config:set GOOGLE_MAPS_API_KEY=tu_key_aqui

# Opcional - para debugging
heroku config:set DEBUG=false
heroku config:set LOG_LEVEL=INFO
```

### 5. Deploy el Código
```bash
# Commit cambios actuales
git add .
git commit -m "Deploy to Heroku: Clean Factory System"

# Deploy a Heroku
git push heroku main
```

### 6. Verificar Deploy
```bash
# Ver logs
heroku logs --tail

# Abrir app
heroku open

# Verificar health
curl https://your-app.herokuapp.com/health
```

## 📱 URLs de Producción

Una vez deployado tendrás:

- **App**: `https://eventos-visualizer-backend-[timestamp].herokuapp.com`
- **Health**: `https://eventos-visualizer-backend-[timestamp].herokuapp.com/health`  
- **Docs**: `https://eventos-visualizer-backend-[timestamp].herokuapp.com/docs`
- **Madrid Test**: `https://eventos-visualizer-backend-[timestamp].herokuapp.com/api/smart/search` (POST)
- **Events**: `https://eventos-visualizer-backend-[timestamp].herokuapp.com/api/multi/fetch-all?location=Madrid`

## 🔧 Configuración Avanzada

### Variables de Entorno Importantes
- `DATABASE_URL`: Automático con PostgreSQL addon
- `PORT`: Automático de Heroku
- `DYNO`: Automático de Heroku
- `EVENTBRITE_API_KEY`: Para eventos reales
- `GEMINI_API_KEY`: Para IA contextual

### Scaling (opcional)
```bash
# Scale up
heroku ps:scale web=2

# Scale down
heroku ps:scale web=1
```

## 🐛 Troubleshooting

### Si el deploy falla:
```bash
heroku logs --tail
```

### Si la base de datos no conecta:
```bash
heroku config:get DATABASE_URL
heroku pg:info
```

### Si los endpoints no responden:
```bash
heroku ps
heroku restart
```

## 🎯 Testing Post-Deploy

```bash
# Health check
curl https://your-app.herokuapp.com/health

# Madrid (should return empty array, not Buenos Aires events)
curl -X POST https://your-app.herokuapp.com/api/smart/search \
  -H "Content-Type: application/json" \
  -d '{"query":"eventos en madrid","location":"Madrid","limit":5}'

# Buenos Aires (should return empty array, not fake events)  
curl -X POST https://your-app.herokuapp.com/api/smart/search \
  -H "Content-Type: application/json" \
  -d '{"query":"eventos en buenos aires","location":"Buenos Aires","limit":5}'
```

## ✅ Success Criteria

- ✅ Health endpoint returns success
- ✅ Madrid search returns `factory_Spain_Madrid` source
- ✅ Buenos Aires search returns `factory_Argentina_BuenosAires` source  
- ✅ No fake data generation
- ✅ Geographic integrity maintained
- ✅ System honest about data availability

## 🎉 ¡Listo!

Tu backend estará corriendo en Heroku con:
- ✅ Factory Pattern funcionando
- ✅ Sistema de datos limpio y honesto
- ✅ Integridad geográfica
- ✅ PostgreSQL configurado
- ✅ APIs de eventos listas para keys reales