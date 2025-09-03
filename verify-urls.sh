#!/bin/bash
# 🔍 VERIFICADOR DE URLs - Desarrollo vs Producción

echo "🔍 VERIFICANDO CONFIGURACIONES DE URLs..."
echo "============================================"

echo ""
echo "📁 ARCHIVOS DE CONFIGURACIÓN:"
echo "------------------------------"

echo "1. netlify.toml:"
grep -n "VITE_API_URL" netlify.toml || echo "   ❌ VITE_API_URL no encontrado"

echo ""
echo "2. frontend/src/config/api.ts:"
grep -n "API_BASE_URL" frontend/src/config/api.ts || echo "   ❌ API_BASE_URL no encontrado"

echo ""
echo "3. frontend/src/services/api.ts:"
grep -n "API_BASE_URL" frontend/src/services/api.ts || echo "   ❌ API_BASE_URL no encontrado"

echo ""
echo "4. frontend/src/config.ts:"
grep -n -A2 -B2 "API_URLS" frontend/src/config.ts || echo "   ❌ API_URLS no encontrado"

echo ""
echo "5. backend/.env.production:"
grep -n "BACKEND_URL" backend/.env.production || echo "   ❌ BACKEND_URL no encontrado"

echo ""
echo "🎯 VERIFICACIONES:"
echo "------------------"

# Verificar que no haya URLs hardcodeadas de desarrollo en producción
HARDCODED_DEV_URLS=$(grep -r "172.29.228.80" frontend/src/ | wc -l)
if [ $HARDCODED_DEV_URLS -gt 0 ]; then
    echo "⚠️  URLs de desarrollo hardcodeadas encontradas:"
    grep -r "172.29.228.80" frontend/src/
else
    echo "✅ No se encontraron URLs de desarrollo hardcodeadas"
fi

echo ""
echo "🚀 CONFIGURACIÓN CORRECTA ESPERADA:"
echo "-----------------------------------"
echo "DESARROLLO:"
echo "  - Fallback: http://172.29.228.80:8001"
echo "  - VITE_API_URL: No configurado (usa fallback)"
echo ""
echo "PRODUCCIÓN:"
echo "  - netlify.toml: VITE_API_URL=https://funaroundyou-f21e91cae36c.herokuapp.com"
echo "  - Netlify Dashboard: VITE_API_URL=https://funaroundyou-f21e91cae36c.herokuapp.com"
echo ""
echo "✅ Configuración completada - Commit y push para aplicar cambios"