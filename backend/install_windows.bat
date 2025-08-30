@echo off
echo ========================================
echo Instalador de Eventos Visualizer para Windows
echo ========================================
echo.

echo [1/4] Instalando dependencias de Python...
pip install fastapi uvicorn aiohttp beautifulsoup4 python-dotenv asyncpg

echo.
echo [2/4] Instalando Playwright para scraping real...
pip install playwright
python -m playwright install chromium
python -m playwright install-deps

echo.
echo [3/4] Instalando otras dependencias...
pip install requests selenium python-dateutil

echo.
echo [4/4] Configurando variables de entorno...
if not exist .env (
    echo # Configuracion de APIs > .env
    echo GEMINI_API_KEY=tu_api_key_aqui >> .env
    echo FACEBOOK_ACCESS_TOKEN= >> .env
    echo INSTAGRAM_ACCESS_TOKEN= >> .env
    echo FIRECRAWL_API_KEY= >> .env
    echo DATABASE_URL=postgresql://postgres:postgres@localhost:5432/eventos_db >> .env
    echo HOST=localhost >> .env
    echo BACKEND_PORT=8001 >> .env
    echo.
    echo Archivo .env creado. Por favor, agrega tus API keys.
)

echo.
echo ========================================
echo Instalacion completada!
echo ========================================
echo.
echo Para iniciar el servidor:
echo   python main.py
echo.
echo El servidor estara disponible en:
echo   http://localhost:8001
echo.
pause