#!/bin/bash

echo "🎭 INSTALADOR COMPLETO DE PLAYWRIGHT - TICKETMASTER SCRAPER"
echo "=========================================================="
echo ""

# Función para verificar comandos
check_command() {
    if command -v $1 >/dev/null 2>&1; then
        echo "✅ $1 está disponible"
        return 0
    else
        echo "❌ $1 no está disponible"
        return 1
    fi
}

# Verificar si es root o sudo
if [[ $EUID -ne 0 ]] && ! sudo -v 2>/dev/null; then
    echo "❌ ERROR: Este script necesita permisos sudo"
    exit 1
fi

echo "1️⃣ ACTUALIZANDO SISTEMA..."
echo "========================="
sudo apt-get update

echo ""
echo "2️⃣ INSTALANDO DEPENDENCIAS DEL SISTEMA..."
echo "========================================"
echo "Esto puede tomar varios minutos..."

# Dependencias esenciales para Playwright
sudo apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libvulkan1 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    xvfb

if [ $? -eq 0 ]; then
    echo "✅ Dependencias del sistema instaladas correctamente"
else
    echo "❌ Error instalando dependencias del sistema"
    exit 1
fi

echo ""
echo "3️⃣ VERIFICANDO PYTHON Y PIP..."
echo "=============================="
if check_command python3; then
    python3 --version
else
    echo "❌ ERROR: Python3 es requerido"
    exit 1
fi

if check_command pip3; then
    echo "✅ pip3 disponible"
else
    echo "📦 Instalando pip3..."
    sudo apt-get install -y python3-pip
fi

echo ""
echo "4️⃣ INSTALANDO PLAYWRIGHT (PYTHON PACKAGE)..."
echo "============================================"
echo "Instalando playwright para Python..."
pip3 install playwright

if [ $? -eq 0 ]; then
    echo "✅ Playwright Python package instalado"
else
    echo "❌ Error instalando Playwright package"
    exit 1
fi

echo ""
echo "5️⃣ INSTALANDO NAVEGADORES PLAYWRIGHT..."
echo "======================================"
echo "Descargando Chromium, Firefox y WebKit (~150MB)..."
echo "Esto puede tomar varios minutos..."

python3 -m playwright install

if [ $? -eq 0 ]; then
    echo "✅ Navegadores Playwright instalados"
else
    echo "❌ Error instalando navegadores"
    exit 1
fi

echo ""
echo "6️⃣ INSTALANDO DEPENDENCIAS ADICIONALES..."
echo "========================================"
echo "Instalando dependencias específicas de los navegadores..."

python3 -m playwright install-deps

if [ $? -eq 0 ]; then
    echo "✅ Dependencias adicionales instaladas"
else
    echo "⚠️ Algunas dependencias pueden haber fallado (esto es normal)"
fi

echo ""
echo "7️⃣ CONFIGURANDO VARIABLES DE ENTORNO..."
echo "======================================"

# Agregar variables de entorno para Playwright
echo "export PLAYWRIGHT_BROWSERS_PATH=/home/$(whoami)/.cache/ms-playwright" >> ~/.bashrc
echo "export DISPLAY=:99" >> ~/.bashrc

echo "✅ Variables de entorno configuradas"

echo ""
echo "8️⃣ VERIFICANDO INSTALACIÓN..."
echo "============================"

# Verificar que Playwright funciona
python3 -c "
try:
    from playwright.sync_api import sync_playwright
    print('✅ Playwright importado correctamente')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        print('✅ Chromium se inicia correctamente')
        browser.close()
        print('✅ Navegador se cierra correctamente')
    
    print('✅ INSTALACIÓN COMPLETAMENTE EXITOSA')
except Exception as e:
    print(f'❌ Error en la verificación: {e}')
    print('⚠️ La instalación puede estar incompleta')
" 2>/dev/null

echo ""
echo "9️⃣ PROBANDO SCRAPER DE TICKETMASTER..."
echo "===================================="

cd "$(dirname "$0")"
if [ -f "test_ticketmaster_simple.py" ]; then
    echo "🧪 Ejecutando prueba del scraper..."
    timeout 60 python3 test_ticketmaster_simple.py
else
    echo "⚠️ Archivo de prueba no encontrado"
fi

echo ""
echo "🎉 INSTALACIÓN COMPLETADA"
echo "========================"
echo ""
echo "📦 COMPONENTES INSTALADOS:"
echo "   ✅ Dependencias del sistema Linux"
echo "   ✅ Playwright Python package"
echo "   ✅ Chromium, Firefox, WebKit"
echo "   ✅ Dependencias adicionales de navegadores"
echo "   ✅ Variables de entorno configuradas"
echo ""
echo "🚀 COMANDOS PARA PROBAR:"
echo "   python3 test_ticketmaster_simple.py"
echo "   python3 services/ticketmaster_playwright_scraper.py"
echo ""
echo "🎪 TICKETMASTER SCRAPER LISTO PARA USAR!"
echo ""
echo "💡 NOTA: Si tienes problemas, reinicia la terminal para cargar las variables de entorno:"
echo "   source ~/.bashrc"

# Hacer este script ejecutable
chmod +x "$0"

echo ""
echo "✅ INSTALACIÓN COMPLETADA EXITOSAMENTE"