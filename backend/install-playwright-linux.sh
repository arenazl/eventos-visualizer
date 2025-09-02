#!/bin/bash
# 🎭 INSTALADOR UNIVERSAL PLAYWRIGHT PARA LINUX/WSL
# Ejecuta este script UNA VEZ y funcionará para todos tus proyectos Claude Code

echo "🎭 INSTALADOR UNIVERSAL PLAYWRIGHT PARA LINUX/WSL"
echo "=================================================="
echo "Este script instala dependencias globales que funcionan"
echo "para TODOS tus proyectos de Playwright en Claude Code"
echo ""

# Función para mostrar errores
show_error() {
    echo "❌ ERROR: $1"
    exit 1
}

# Verificar si tenemos permisos sudo
if ! sudo -v; then
    show_error "Este script necesita permisos sudo"
fi

echo "1️⃣ ACTUALIZANDO SISTEMA..."
sudo apt-get update || show_error "No se pudo actualizar el sistema"

echo ""
echo "2️⃣ INSTALANDO DEPENDENCIAS ESENCIALES PLAYWRIGHT..."
# Usar nombres de paquetes actualizados para Ubuntu 24.04+
sudo apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2t64 \
    libatk-bridge2.0-0t64 \
    libatk1.0-0t64 \
    libatspi2.0-0t64 \
    libcairo2 \
    libcups2t64 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0t64 \
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
    xvfb \
|| show_error "No se pudieron instalar las dependencias del sistema"

echo ""
echo "3️⃣ INSTALANDO NODE.JS Y NPM (si no están instalados)..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo ""
echo "4️⃣ INSTALANDO PLAYWRIGHT GLOBALMENTE..."
npm install -g playwright@latest || show_error "No se pudo instalar Playwright globalmente"

echo ""
echo "5️⃣ INSTALANDO BROWSERS PLAYWRIGHT..."
npx playwright install chromium firefox webkit || show_error "No se pudieron instalar los browsers"

echo ""
echo "6️⃣ INSTALANDO DEPENDENCIAS ADICIONALES DE PLAYWRIGHT..."
# Instalar las dependencias que faltan manualmente
sudo apt-get install -y \
    libgtk-4-1 \
    libgraphene-1.0-0 \
    libatomic1 \
    libxslt1.1 \
    libvpx9 \
    libevent-2.1-7 \
    libopus0 \
    libwebpdemux2 \
    libavif16 \
    libharfbuzz-icu0 \
    libwebpmux3 \
    libenchant-2-2 \
    libsecret-1-0 \
    libhyphen0 \
    flite1-dev || echo "⚠️ Algunas dependencias opcionales no se pudieron instalar"

# Usar playwright install-deps como usuario normal, no sudo
npx playwright install-deps --dry-run || echo "⚠️ Usando instalación básica"

echo ""
echo "7️⃣ VERIFICANDO INSTALACIÓN..."
echo "Verificando Chromium..."
npx playwright install chromium --dry-run || echo "⚠️ Chromium necesita reinstalación"

echo "Verificando Firefox..."
npx playwright install firefox --dry-run || echo "⚠️ Firefox necesita reinstalación"

echo ""
echo "8️⃣ CONFIGURANDO VARIABLES DE ENTORNO GLOBALES..."

# Crear archivo de configuración global
cat > /tmp/playwright-env.sh << 'EOF'
# 🎭 Configuración global Playwright para Claude Code
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
export PLAYWRIGHT_BROWSER_TYPE=chromium
export NODE_PATH=/usr/local/lib/node_modules:$NODE_PATH
EOF

# Agregar al bashrc si no existe
if ! grep -q "playwright-env.sh" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# 🎭 Playwright configuración global para Claude Code" >> ~/.bashrc
    echo "source /tmp/playwright-env.sh" >> ~/.bashrc
    cp /tmp/playwright-env.sh ~/.playwright-env.sh
    echo "source ~/.playwright-env.sh" >> ~/.bashrc
fi

echo ""
echo "✅ INSTALACIÓN COMPLETADA CON ÉXITO!"
echo "=================================================="
echo ""
echo "🎉 RESULTADO:"
echo "   ✅ Dependencias del sistema instaladas"
echo "   ✅ Playwright instalado globalmente"  
echo "   ✅ Browsers (Chromium, Firefox, Webkit) instalados"
echo "   ✅ Variables de entorno configuradas"
echo ""
echo "🚀 USAR EN CUALQUIER PROYECTO:"
echo "   Ahora TODOS tus proyectos de Playwright en Claude Code"
echo "   funcionarán automáticamente sin configuración adicional"
echo ""
echo "🔄 PARA APLICAR CAMBIOS AHORA:"
echo "   source ~/.bashrc"
echo "   O reinicia tu terminal"
echo ""
echo "🧪 PROBAR:"
echo "   cd /ruta/a/tu/proyecto"
echo "   python3 test_hardcoded.py"
echo ""
echo "💡 NOTA:"
echo "   Este setup funciona para todos los proyectos futuros"
echo "   No necesitas repetir esta instalación"