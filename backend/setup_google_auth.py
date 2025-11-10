"""
Script de setup para autenticación con Google OAuth2
Configura todo lo necesario para autenticación de usuarios
"""
import os
import sys
import subprocess
from pathlib import Path

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def print_step(step, message):
    """Imprime un paso del proceso"""
    print(f"\n{'='*60}")
    print(f"PASO {step}: {message}")
    print(f"{'='*60}")

def install_dependencies():
    """Instala las dependencias necesarias para Google OAuth"""
    print_step(1, "Instalando dependencias de autenticación")

    dependencies = [
        "authlib",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "httpx"
    ]

    for dep in dependencies:
        print(f"  📦 Instalando {dep}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"  ✅ {dep} instalado")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error instalando {dep}: {e}")
            return False

    return True

def update_env_file():
    """Actualiza el archivo .env con las variables necesarias"""
    print_step(2, "Configurando variables de entorno")

    env_path = Path(__file__).parent / ".env"
    env_example_path = Path(__file__).parent / ".env.example"

    # Leer .env actual si existe
    env_content = ""
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()

    # Variables necesarias para Google OAuth
    required_vars = {
        "GOOGLE_CLIENT_ID": "your-google-client-id-here",
        "GOOGLE_CLIENT_SECRET": "your-google-client-secret-here",
        "GOOGLE_REDIRECT_URI": "http://localhost:8001/auth/google/callback",
        "JWT_SECRET_KEY": "your-super-secret-jwt-key-change-this-in-production",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "1440",
    }

    # Agregar variables si no existen
    needs_update = False

    # Agregar comentarios de sección si no existen
    if "# Google OAuth Configuration" not in env_content:
        env_content += "\n\n# Google OAuth Configuration\n"
        needs_update = True

    if "# JWT Configuration" not in env_content:
        env_content += "\n# JWT Configuration\n"
        needs_update = True

    for key, default_value in required_vars.items():
        if key not in env_content:
            env_content += f"\n{key}={default_value}"
            needs_update = True
            print(f"  ➕ Agregada variable: {key}")

    if needs_update:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"  ✅ Archivo .env actualizado")
    else:
        print(f"  ℹ️  Todas las variables ya existen en .env")

    # Actualizar .env.example también
    if env_example_path.exists():
        with open(env_example_path, 'r', encoding='utf-8') as f:
            example_content = f.read()

        for key, default_value in required_vars.items():
            if key not in example_content:
                example_content += f"\n{key}={default_value}"

        with open(env_example_path, 'w', encoding='utf-8') as f:
            f.write(example_content)
        print(f"  ✅ Archivo .env.example actualizado")

def create_database_tables():
    """Crea las tablas de base de datos"""
    print_step(3, "Creando tablas de base de datos")

    try:
        from database.connection import Base, engine
        from models import users, events

        print("  📊 Creando tablas...")
        Base.metadata.create_all(bind=engine)
        print("  ✅ Tablas creadas exitosamente")

        # Verificar tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("\n  📋 Tablas en la base de datos:")
        for table in tables:
            print(f"    - {table}")

        return True
    except Exception as e:
        print(f"  ❌ Error creando tablas: {e}")
        return False

def print_next_steps():
    """Imprime los siguientes pasos para completar la configuración"""
    print_step(4, "Configuración de Google Cloud Console")

    print("""
  Para completar la configuración, necesitas:

  1. 🌐 Ir a Google Cloud Console:
     https://console.cloud.google.com/

  2. 📝 Crear un nuevo proyecto o seleccionar uno existente

  3. 🔑 Habilitar Google+ API:
     - Ir a "APIs & Services" > "Library"
     - Buscar "Google+ API" y habilitarla
     - Buscar "Google Calendar API" y habilitarla (opcional)

  4. 🎫 Crear credenciales OAuth 2.0:
     - Ir a "APIs & Services" > "Credentials"
     - Click en "Create Credentials" > "OAuth client ID"
     - Tipo de aplicación: "Web application"
     - Nombre: "Eventos Visualizer"

  5. 🔗 Configurar URIs autorizadas:
     JavaScript origins:
       - http://localhost:8001
       - http://172.29.228.80:8001
       - http://localhost:5174
       - http://172.29.228.80:5174

     Redirect URIs:
       - http://localhost:8001/auth/google/callback
       - http://172.29.228.80:8001/auth/google/callback

  6. 📋 Copiar credenciales:
     - Client ID
     - Client Secret
     - Actualizar en el archivo .env:
       GOOGLE_CLIENT_ID=tu-client-id
       GOOGLE_CLIENT_SECRET=tu-client-secret

  7. 🔐 Generar JWT Secret Key segura:
     - Ejecutar en Python:
       import secrets
       print(secrets.token_urlsafe(32))
     - Actualizar JWT_SECRET_KEY en .env con el valor generado

  8. 🚀 Reiniciar el servidor backend para aplicar cambios

  ✅ Archivos creados:
     - backend/api/auth.py          → Endpoints OAuth2
     - backend/middleware/jwt.py    → Middleware JWT
     - backend/utils/auth_utils.py  → Utilidades de autenticación
     - frontend/src/components/GoogleLoginButton.tsx → Botón de login
     - frontend/src/contexts/AuthContext.tsx → Context de autenticación
    """)

def main():
    """Función principal del script"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   SETUP AUTENTICACIÓN CON GOOGLE OAUTH2                 ║
    ║   Eventos Visualizer                                     ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Verificar que estamos en el directorio correcto
    if not Path("main.py").exists():
        print("❌ Error: Este script debe ejecutarse desde el directorio backend/")
        sys.exit(1)

    # Ejecutar pasos
    success = True

    if not install_dependencies():
        success = False
        print("\n⚠️  Algunas dependencias no se pudieron instalar")

    update_env_file()

    if not create_database_tables():
        success = False
        print("\n⚠️  Las tablas de base de datos no se pudieron crear")

    print_next_steps()

    if success:
        print("\n✅ ¡Setup completado exitosamente!")
        print("\n📝 Siguiente paso: Configurar credenciales de Google en .env")
    else:
        print("\n⚠️  Setup completado con algunos errores. Revisa los mensajes arriba.")

if __name__ == "__main__":
    main()
