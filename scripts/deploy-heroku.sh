#!/bin/bash

# Script de Deploy para Heroku - Eventos Visualizer Backend
echo "🚀 Iniciando deploy de Eventos Visualizer Backend a Heroku..."

# 1. Login a Heroku (necesario hacer manualmente)
echo "🔐 Ejecuta manualmente: heroku login"
echo "Presiona Enter cuando hayas hecho login..."
read -p ""

# 2. Crear la app de Heroku
echo "📱 Creando app de Heroku..."
APP_NAME="eventos-visualizer-backend-$(date +%s)"
heroku create $APP_NAME

# 3. Agregar PostgreSQL addon
echo "🐘 Configurando PostgreSQL..."
heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME

# 4. Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
heroku config:set HOST=0.0.0.0 --app $APP_NAME
heroku config:set BACKEND_PORT=$PORT --app $APP_NAME
heroku config:set EVENTBRITE_API_KEY=your_key_here --app $APP_NAME
heroku config:set GEMINI_API_KEY=your_key_here --app $APP_NAME

# 5. Commit cambios actuales
echo "📝 Haciendo commit de cambios..."
git add .
git commit -m "Deploy to Heroku: Factory Pattern + Clean Data System 🎉"

# 6. Deploy a Heroku
echo "🚀 Deploying to Heroku..."
heroku git:remote --app $APP_NAME
git push heroku main

# 7. Abrir la app
echo "🌐 Abriendo la app..."
heroku open --app $APP_NAME

echo "✅ Deploy completado!"
echo "📱 App Name: $APP_NAME"
echo "🌐 URL: https://$APP_NAME.herokuapp.com"
echo "📊 Health Check: https://$APP_NAME.herokuapp.com/health"
echo "📖 Docs: https://$APP_NAME.herokuapp.com/docs"