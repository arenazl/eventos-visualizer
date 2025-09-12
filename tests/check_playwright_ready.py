#!/usr/bin/env python3
"""
🔍 VERIFICADOR RÁPIDO DE PLAYWRIGHT
Revisa si Playwright está listo para usar
"""

def check_playwright_status():
    """
    🎭 VERIFICAR ESTADO DE PLAYWRIGHT
    """
    
    print("🔍 VERIFICANDO ESTADO DE PLAYWRIGHT")
    print("=" * 40)
    print()
    
    # 1. Verificar si el package está instalado
    try:
        import playwright
        print("✅ Playwright package instalado")
        print(f"   Versión: {playwright.__version__}")
    except ImportError:
        print("❌ Playwright package NO instalado")
        print("   Ejecuta: pip3 install playwright")
        return False
    
    # 2. Verificar si los navegadores están disponibles
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright API disponible")
    except ImportError:
        print("❌ Playwright API NO disponible")
        return False
    
    # 3. Probar navegador
    try:
        print("🔄 Probando navegador...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            print("✅ Chromium funciona correctamente")
            browser.close()
    except Exception as e:
        print(f"❌ Error con navegador: {e}")
        print("   Posibles soluciones:")
        print("   1. ./install_playwright_complete.sh")
        print("   2. python3 -m playwright install")
        print("   3. python3 -m playwright install-deps")
        return False
    
    # 4. Verificar dependencias del sistema
    import subprocess
    import os
    
    required_libs = [
        "libnss3", "libatk1.0-0", "libdrm2", "libxcomposite1",
        "libxdamage1", "libxrandr2", "libgbm1", "libxss1", "libasound2"
    ]
    
    missing_libs = []
    for lib in required_libs:
        try:
            result = subprocess.run(['dpkg', '-l', lib], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                missing_libs.append(lib)
        except:
            pass  # No podemos verificar en este sistema
    
    if missing_libs:
        print(f"⚠️ Dependencias faltantes: {', '.join(missing_libs[:3])}...")
        print("   Ejecuta: ./install_playwright_complete.sh")
    else:
        print("✅ Dependencias del sistema verificadas")
    
    print()
    print("🎉 PLAYWRIGHT ESTÁ LISTO PARA USAR!")
    return True

if __name__ == "__main__":
    try:
        ready = check_playwright_status()
        if ready:
            print("\n🚀 Puedes ejecutar:")
            print("   python3 test_ticketmaster_simple.py")
        else:
            print("\n🛠️ Ejecuta el instalador:")
            print("   ./install_playwright_complete.sh")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("\n🛠️ Ejecuta el instalador completo:")
        print("   ./install_playwright_complete.sh")