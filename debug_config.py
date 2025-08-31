#!/usr/bin/env python3
"""
🔧 DEBUGGING CONFIG CHECKER
Verifica configuración para debugging
"""

import os
from dotenv import load_dotenv
import requests
import mysql.connector
import json

# Load environment variables
load_dotenv()

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m' 
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def check_env_vars():
    """Verificar variables de entorno críticas"""
    print(f"{Colors.BOLD}🔍 CHECKING ENVIRONMENT VARIABLES{Colors.END}")
    
    critical_vars = [
        "HOST",
        "BACKEND_PORT", 
        "MYSQL_HOST",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE"
    ]
    
    api_keys = [
        "EVENTBRITE_API_KEY",
        "TICKETMASTER_API_KEY", 
        "MEETUP_API_KEY"
    ]
    
    print("\n📋 Critical Variables:")
    for var in critical_vars:
        value = os.getenv(var)
        if value and value != "your_key_here":
            print(f"{Colors.GREEN}✅ {var}: {value[:20]}...{Colors.END}")
        else:
            print(f"{Colors.RED}❌ {var}: NOT SET{Colors.END}")
    
    print("\n🔑 API Keys:")  
    for var in api_keys:
        value = os.getenv(var)
        if value and "your_" not in value:
            print(f"{Colors.GREEN}✅ {var}: SET{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️ {var}: NOT CONFIGURED{Colors.END}")

def test_mysql_connection():
    """Probar conexión directa a MySQL"""
    print(f"\n{Colors.BOLD}🗄️ MYSQL CONNECTION TEST{Colors.END}")
    
    config = {
        'host': os.getenv("MYSQL_HOST"),
        'port': int(os.getenv("MYSQL_PORT", "3306")), 
        'user': os.getenv("MYSQL_USER"),
        'password': os.getenv("MYSQL_PASSWORD"),
        'database': os.getenv("MYSQL_DATABASE")
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Test básico
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"{Colors.GREEN}✅ MySQL Connection: SUCCESS{Colors.END}")
        
        # Verificar tablas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"{Colors.BLUE}📊 Tables found: {len(tables)}{Colors.END}")
        
        for table in tables[:5]:  # Mostrar máximo 5
            print(f"   • {table[0]}")
            
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ MySQL Connection: FAILED{Colors.END}")
        print(f"   Error: {e}")
        return False

def check_backend_endpoints():
    """Verificar endpoints específicos del backend"""
    print(f"\n{Colors.BOLD}🌐 BACKEND ENDPOINTS CHECK{Colors.END}")
    
    base_url = f"http://{os.getenv('HOST', '172.29.228.80')}:{os.getenv('BACKEND_PORT', '8001')}"
    
    endpoints = [
        "/health",
        "/api/events?limit=1", 
        "/api/location/detect",
        "/docs",  # FastAPI docs
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"{Colors.GREEN}✅ {endpoint}: OK{Colors.END}")
                results[endpoint] = True
            else:
                print(f"{Colors.YELLOW}⚠️ {endpoint}: HTTP {response.status_code}{Colors.END}")
                results[endpoint] = False
        except Exception as e:
            print(f"{Colors.RED}❌ {endpoint}: FAILED - {e}{Colors.END}")
            results[endpoint] = False
    
    return results

def show_debug_commands():
    """Mostrar comandos útiles para debugging"""
    print(f"\n{Colors.BOLD}🛠️ DEBUGGING COMMANDS{Colors.END}")
    
    host = os.getenv('HOST', '172.29.228.80')
    backend_port = os.getenv('BACKEND_PORT', '8001')
    frontend_port = os.getenv('FRONTEND_PORT', '5174')
    
    commands = [
        f"curl http://{host}:{backend_port}/health",
        f"curl http://{host}:{backend_port}/api/events?limit=5",
        f"curl http://{host}:{backend_port}/docs",
        f"python3 debug_tools.py quick",
        f"python3 debug_tools.py debug", 
        f"lsof -i :{backend_port}",
        f"lsof -i :{frontend_port}",
        "ps aux | grep python | grep -v grep",
        "ps aux | grep node | grep -v grep"
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"{Colors.BLUE}{i:2d}. {cmd}{Colors.END}")

def generate_debug_summary():
    """Generar resumen completo para debugging"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("🚀 EVENTOS VISUALIZER - DEBUG CONFIGURATION")  
    print("=" * 60)
    print(f"{Colors.END}")
    
    # Verificar todo
    check_env_vars()
    mysql_ok = test_mysql_connection()
    endpoints_ok = check_backend_endpoints()
    show_debug_commands()
    
    # Resumen final
    print(f"\n{Colors.BOLD}📋 DEBUG SUMMARY{Colors.END}")
    
    if mysql_ok:
        print(f"{Colors.GREEN}✅ Database: Connected{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Database: Connection Issues{Colors.END}")
        
    if all(endpoints_ok.values()):
        print(f"{Colors.GREEN}✅ Backend: All endpoints working{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️ Backend: Some endpoints have issues{Colors.END}")
    
    # Recomendaciones
    print(f"\n{Colors.BOLD}💡 DEBUGGING TIPS{Colors.END}")
    print("1. Use 'python3 debug_tools.py quick' for fast health check")
    print("2. Check logs with 'python3 debug_tools.py debug'")
    print("3. Visit FastAPI docs at http://172.29.228.80:8001/docs")
    print("4. Monitor processes with 'python3 debug_tools.py processes'")

if __name__ == "__main__":
    generate_debug_summary()