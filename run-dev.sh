#!/bin/bash

# Script para ejecutar el desarrollo desde WSL
echo "🚀 Iniciando Eventos Visualizer desde WSL..."

# Backend en puerto 8001
echo "📱 Iniciando Backend en puerto 8001..."
cd /mnt/c/Code/eventos-visualizer/backend
python3 main.py &
BACKEND_PID=$!

# Frontend en puerto 5174 (si quieres ejecutarlo desde aquí también)
echo "🌐 Frontend debe ejecutarse en Windows:"
echo "   cd C:\\Code\\eventos-visualizer\\frontend"
echo "   npm run dev"

echo ""
echo "✅ Backend iniciado con PID: $BACKEND_PID"
echo "📍 Backend: http://172.29.228.80:8001"
echo "📊 Health: http://172.29.228.80:8001/health"
echo "📖 Docs: http://172.29.228.80:8001/docs"
echo ""
echo "Para detener el backend: kill $BACKEND_PID"

# Esperar para mantener el script vivo
wait $BACKEND_PID