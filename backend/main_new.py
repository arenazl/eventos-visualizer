"""
Main entry point para Eventos Visualizer API - Versión Refactorizada
Archivo principal simplificado después de la refactorización modular
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar backend al path
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

# Heroku configuration
try:
    from heroku_config import apply_heroku_config, is_heroku
    apply_heroku_config()
    if is_heroku():
        print("🌐 Running on Heroku - Production mode activated")
except ImportError:
    print("📱 Running locally - Development mode")

# Importar la app desde el factory
from app import app
from app.config import settings

# Mensaje de inicio
print("🚀 Starting Eventos Visualizer API")
print(f"📊 Environment: {settings.ENVIRONMENT}")
print(f"🌐 Host: {settings.HOST}:{settings.PORT}")
print(f"🔧 Debug mode: {settings.DEBUG}")

# Función principal para ejecutar la aplicación
def run_server():
    """
    Ejecutar el servidor con la configuración apropiada
    """
    try:
        uvicorn.run(
            "main_new:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.RELOAD and settings.is_development(),
            log_level=settings.LOG_LEVEL.lower(),
            access_log=settings.DEBUG
        )
    except KeyboardInterrupt:
        print("\n🔄 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Verificar configuración crítica
    if not settings.EVENTBRITE_API_KEY:
        print("⚠️ Warning: EVENTBRITE_API_KEY not configured")
    
    if not settings.RAPIDAPI_KEY:
        print("⚠️ Warning: RAPIDAPI_KEY not configured")
    
    # Ejecutar servidor
    run_server()