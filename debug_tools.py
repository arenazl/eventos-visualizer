#!/usr/bin/env python3
"""
🔧 EVENTOS VISUALIZER - DEBUG TOOLS
Herramientas para debugging y monitoreo del sistema
"""

import requests
import json
from datetime import datetime
import subprocess
import sys
import time

# Configuración
BACKEND_URL = "http://172.29.228.80:8001"
FRONTEND_URL = "http://172.29.228.80:5174"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def test_backend_health():
    """Probar health check del backend"""
    print_header("BACKEND HEALTH CHECK")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend funcionando en puerto {data.get('port', 'unknown')}")
            print_info(f"Database: {data.get('database', 'unknown')}")
            print_info(f"Version: {data.get('version', 'unknown')}")
            return True
        else:
            print_error(f"Backend respondió con código {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"No se puede conectar al backend: {e}")
        return False

def test_frontend():
    """Probar frontend"""
    print_header("FRONTEND CHECK")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print_success("Frontend funcionando correctamente")
            return True
        else:
            print_error(f"Frontend respondió con código {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"No se puede conectar al frontend: {e}")
        return False

def test_database_connection():
    """Probar conexión a base de datos"""
    print_header("DATABASE CONNECTION TEST")
    try:
        response = requests.get(f"{BACKEND_URL}/api/events?limit=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('events') is not None:
                print_success(f"Database conectada - {data.get('total', 0)} eventos disponibles")
                return True
            else:
                print_warning("Database conectada pero sin eventos")
                return True
        else:
            print_error(f"Error al consultar eventos: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Error de conexión: {e}")
        return False

def test_api_endpoints():
    """Probar endpoints principales"""
    print_header("API ENDPOINTS TEST")
    
    endpoints = [
        ("/health", "Health Check"),
        ("/api/events?limit=5", "Eventos"),
        ("/api/location/detect", "Detección de ubicación"),
        ("/api/multi/test-apis", "Test APIs externas")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print_success(f"{name}: OK")
                results[endpoint] = "OK"
            else:
                print_error(f"{name}: Error {response.status_code}")
                results[endpoint] = f"Error {response.status_code}"
        except requests.exceptions.RequestException as e:
            print_error(f"{name}: {e}")
            results[endpoint] = f"Exception: {e}"
        time.sleep(0.5)  # Evitar rate limiting
    
    return results

def show_running_processes():
    """Mostrar procesos relacionados corriendo"""
    print_header("RUNNING PROCESSES")
    
    try:
        # Buscar procesos de Python y Node
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        lines = result.stdout.split('\n')
        relevant_processes = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['python', 'node', 'npm']):
                if any(keyword in line for keyword in ['main_mysql.py', 'complete_server.py', 'vite', 'npm start']):
                    relevant_processes.append(line)
        
        if relevant_processes:
            for process in relevant_processes:
                print_info(f"📊 {process}")
        else:
            print_warning("No se encontraron procesos relevantes")
            
    except subprocess.CalledProcessError as e:
        print_error(f"Error al obtener procesos: {e}")

def check_ports():
    """Verificar que los puertos estén ocupados correctamente"""
    print_header("PORT STATUS CHECK")
    
    ports = [8001, 5174]
    
    for port in ports:
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print_success(f"Puerto {port}: OCUPADO")
                # Mostrar qué proceso está usando el puerto
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            print_info(f"  📌 Proceso: {parts[0]} (PID: {parts[1]})")
            else:
                print_error(f"Puerto {port}: LIBRE (debería estar ocupado)")
                
        except subprocess.CalledProcessError:
            print_error(f"Error al verificar puerto {port}")

def debug_api_responses():
    """Debuggear respuestas de APIs con detalle"""
    print_header("API RESPONSE DEBUG")
    
    endpoints = [
        "/api/events?limit=2",
        "/api/location/detect",
        "/health"
    ]
    
    for endpoint in endpoints:
        print(f"\n{Colors.PURPLE}🔍 Testing {endpoint}{Colors.END}")
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            print_info(f"Status: {response.status_code}")
            print_info(f"Headers: {dict(response.headers)}")
            
            try:
                data = response.json()
                print_info(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            except:
                print_info(f"Response (text): {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print_error(f"Error: {e}")
        
        print("-" * 40)

def run_full_debug():
    """Ejecutar debugging completo"""
    print(f"{Colors.BOLD}{Colors.WHITE}")
    print("🚀 EVENTOS VISUALIZER - FULL DEBUG SCAN")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.END}")
    
    # Ejecutar todas las pruebas
    backend_ok = test_backend_health()
    frontend_ok = test_frontend()
    db_ok = test_database_connection()
    
    check_ports()
    show_running_processes()
    test_api_endpoints()
    
    # Resumen final
    print_header("RESUMEN FINAL")
    
    if backend_ok:
        print_success("Backend: Funcionando")
    else:
        print_error("Backend: Con problemas")
        
    if frontend_ok:
        print_success("Frontend: Funcionando")
    else:
        print_error("Frontend: Con problemas")
        
    if db_ok:
        print_success("Database: Conectada")
    else:
        print_error("Database: Con problemas")
    
    overall_status = backend_ok and frontend_ok and db_ok
    
    if overall_status:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SISTEMA LISTO PARA DEBUGGING{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️ SISTEMA CON PROBLEMAS - REVISAR ERRORES{Colors.END}")

def quick_test():
    """Prueba rápida de funcionalidad básica"""
    print_header("QUICK TEST")
    
    tests = [
        (f"{BACKEND_URL}/health", "Backend Health"),
        (f"{FRONTEND_URL}", "Frontend"),
        (f"{BACKEND_URL}/api/events?limit=1", "Database Connection")
    ]
    
    all_ok = True
    
    for url, name in tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{name}: OK")
            else:
                print_error(f"{name}: Error {response.status_code}")
                all_ok = False
        except:
            print_error(f"{name}: FAIL")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            quick_test()
        elif command == "debug":
            debug_api_responses()
        elif command == "ports":
            check_ports()
        elif command == "processes":
            show_running_processes()
        else:
            print(f"Comandos disponibles: quick, debug, ports, processes")
    else:
        run_full_debug()