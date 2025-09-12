#!/bin/bash

echo "🎭 INSTALADOR DE PLAYWRIGHT PARA TICKETMASTER SCRAPER"
echo "===================================================="
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

# Verificar Python
echo "1️⃣ VERIFICANDO PYTHON..."
if check_command python3; then
    python3 --version
else
    echo "❌ ERROR: Python3 es requerido"
    exit 1
fi

# Verificar pip
echo ""
echo "2️⃣ VERIFICANDO PIP..."
if check_command pip3; then
    echo "✅ pip3 disponible"
else
    echo "⚠️ Instalando pip3..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# Instalar Playwright
echo ""
echo "3️⃣ INSTALANDO PLAYWRIGHT..."
echo "Esto puede tomar varios minutos..."
pip3 install playwright

# Instalar navegadores
echo ""
echo "4️⃣ INSTALANDO NAVEGADORES PLAYWRIGHT..."
echo "Instalando Chromium, Firefox y WebKit..."
python3 -m playwright install

# Instalar dependencias del sistema
echo ""
echo "5️⃣ INSTALANDO DEPENDENCIAS DEL SISTEMA..."
python3 -m playwright install-deps

# Verificar instalación
echo ""
echo "6️⃣ VERIFICANDO INSTALACIÓN..."
python3 -c "from playwright.sync_api import sync_playwright; print('✅ Playwright instalado correctamente')" 2>/dev/null && echo "✅ Instalación exitosa" || echo "❌ Error en la instalación"

# Información adicional
echo ""
echo "📋 INSTALACIÓN COMPLETADA"
echo "========================="
echo ""
echo "📦 Paquetes instalados:"
echo "   - playwright (Python package)"
echo "   - chromium (navegador)"
echo "   - firefox (navegador)" 
echo "   - webkit (navegador)"
echo ""
echo "🚀 Para probar el scraper:"
echo "   cd /mnt/c/Code/eventos-visualizer/backend"
echo "   python3 services/ticketmaster_playwright_scraper.py"
echo ""
echo "🎪 El scraper está listo para usar con Ticketmaster!"

# Hacer el script ejecutable
chmod +x "$0"

echo ""
echo "✅ INSTALACIÓN COMPLETADA EXITOSAMENTE"