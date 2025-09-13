"""
🔍 REQUEST/RESPONSE LOGGER MIDDLEWARE
Muestra detalladamente todas las requests y responses del backend
"""

import json
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute
import logging

logger = logging.getLogger(__name__)

class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            
            # Capturar body del request
            body = await request.body()
            
            # Log de entrada
            print("\n" + "="*80)
            print(f"📥 REQUEST ENTRANTE")
            print("="*80)
            print(f"🔵 MÉTODO: {request.method}")
            print(f"🌐 URL: {request.url.path}")
            print(f"🔗 URL COMPLETA: {request.url}")
            print(f"📍 IP CLIENTE: {request.client.host}")
            
            if request.query_params:
                print(f"❓ QUERY PARAMS:")
                for key, value in request.query_params.items():
                    print(f"   • {key}: {value}")
            
            if body:
                try:
                    body_json = json.loads(body)
                    print(f"📦 BODY:")
                    print(json.dumps(body_json, indent=2, ensure_ascii=False))
                except:
                    print(f"📦 BODY (raw): {body.decode()[:200]}...")
            
            print("-"*80)
            
            # Restaurar body para que el endpoint lo pueda leer
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
            
            # Ejecutar el endpoint
            response = await original_route_handler(request)
            
            # Calcular tiempo de procesamiento
            process_time = time.time() - start_time
            
            # Log de salida
            print("\n" + "="*80)
            print(f"📤 RESPONSE SALIENTE")
            print("="*80)
            print(f"✅ STATUS: {response.status_code}")
            print(f"⏱️ TIEMPO: {process_time:.3f} segundos")
            
            # Intentar parsear el body del response
            if hasattr(response, 'body'):
                try:
                    response_body = json.loads(response.body)
                    print(f"📨 RESPONSE:")
                    
                    # Formatear respuesta según el endpoint
                    if request.url.path == "/api/ai/analyze-intent":
                        if response_body.get('success'):
                            intent = response_body.get('intent', {})
                            print(f"   🎯 QUERY: '{intent.get('query', '')}'")
                            print(f"   📍 CIUDAD: {intent.get('detected_city', 'N/A')}")
                            print(f"   🏛️ PROVINCIA: {intent.get('detected_province', 'N/A')}")
                            print(f"   🌎 PAÍS: {intent.get('detected_country', 'N/A')}")
                            print(f"   📊 CONFIANZA: {intent.get('confidence', 0)*100:.0f}%")
                            hierarchy = intent.get('geographic_hierarchy', {})
                            if hierarchy:
                                print(f"   📌 UBICACIÓN COMPLETA: {hierarchy.get('full_location', 'N/A')}")
                        else:
                            print(f"   ❌ ERROR: {response_body.get('error', 'Unknown error')}")
                    else:
                        # Para otros endpoints, mostrar resumen
                        print(json.dumps(response_body, indent=2, ensure_ascii=False)[:500])
                        if len(json.dumps(response_body)) > 500:
                            print("   ... (respuesta truncada)")
                except:
                    print(f"📨 RESPONSE (raw): {response.body[:200]}...")
            
            print("="*80 + "\n")
            
            return response

        return custom_route_handler


async def log_request_middleware(request: Request, call_next):
    """
    Middleware alternativo más simple
    """
    start_time = time.time()
    
    # Log simple de entrada
    print(f"\n🔹 {request.method} {request.url.path} desde {request.client.host}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"🔸 Respondido en {process_time:.3f}s con status {response.status_code}")
    
    return response