"""
REQUEST/RESPONSE LOGGER MIDDLEWARE
Muestra detalladamente todas las requests y responses del backend
"""

import json
import time
import sys
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute
import logging
from colorama import Fore, Back, Style
from datetime import datetime

logger = logging.getLogger(__name__)

# Request counter for tracking
request_counter = 0

# Safe print function for Windows
def safe_print(text):
    """Print with fallback for encoding errors"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove problematic Unicode characters
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text)

class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            global request_counter
            request_counter += 1
            start_time = time.time()

            # Capturar body del request
            body = await request.body()

            # Log de entrada con colores y mejor formato
            timestamp = datetime.now().strftime("%H:%M:%S")
            safe_print("\n" + Fore.CYAN + "=" + "="*78 + "=")
            safe_print(Fore.CYAN + "|" + Fore.YELLOW + f" REQUEST #{request_counter} [{timestamp}]".center(78) + Fore.CYAN + "|")
            safe_print(Fore.CYAN + "=" + "="*78 + "=" + Style.RESET_ALL)
            safe_print(Fore.CYAN + "|" + Fore.GREEN + f" METHOD: {request.method:<10}" + Fore.WHITE + f" PATH: {request.url.path:<40}" + Fore.CYAN + "|")
            safe_print(Fore.CYAN + "|" + Fore.BLUE + f" CLIENT: {request.client.host:<20}" + Fore.WHITE + f" FULL: {str(request.url)[:45]:<45}" + Fore.CYAN + "|")
            
            if request.query_params:
                safe_print(Fore.CYAN + "|" + Fore.MAGENTA + " QUERY PARAMS:" + " "*61 + Fore.CYAN + "|")
                for key, value in request.query_params.items():
                    param_str = f"   * {key}: {value}"
                    safe_print(Fore.CYAN + "|" + Fore.WHITE + f"{param_str:<78}" + Fore.CYAN + "|")

            if body:
                try:
                    body_json = json.loads(body)
                    safe_print(Fore.CYAN + "|" + Fore.MAGENTA + " BODY:" + " "*68 + Fore.CYAN + "|")
                    body_lines = json.dumps(body_json, indent=2, ensure_ascii=False).split('\n')
                    for line in body_lines[:5]:  # Show first 5 lines
                        safe_print(Fore.CYAN + "|" + Fore.WHITE + f"   {line[:74]:<75}" + Fore.CYAN + "|")
                    if len(body_lines) > 5:
                        safe_print(Fore.CYAN + "|" + Fore.YELLOW + "   ... (truncated)" + " "*59 + Fore.CYAN + "|")
                except:
                    safe_print(Fore.CYAN + "|" + Fore.WHITE + f" BODY (raw): {body.decode()[:60]}..." + " "*10 + Fore.CYAN + "|")

            safe_print(Fore.CYAN + "=" + "="*78 + "=" + Style.RESET_ALL)
            
            # Restaurar body para que el endpoint lo pueda leer
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
            
            # Ejecutar el endpoint
            response = await original_route_handler(request)
            
            # Calcular tiempo de procesamiento
            process_time = time.time() - start_time
            
            # Log de salida con colores
            status_color = Fore.GREEN if response.status_code < 400 else Fore.RED
            time_color = Fore.GREEN if process_time < 1 else Fore.YELLOW if process_time < 3 else Fore.RED

            safe_print("\n" + Fore.CYAN + "=" + "="*78 + "=")
            safe_print(Fore.CYAN + "|" + Fore.GREEN + f" RESPONSE [{timestamp}]".center(78) + Fore.CYAN + "|")
            safe_print(Fore.CYAN + "=" + "="*78 + "=" + Style.RESET_ALL)
            safe_print(Fore.CYAN + "|" + status_color + f" STATUS: {response.status_code:<10}" + time_color + f" TIME: {process_time:.3f}s" + " "*43 + Fore.CYAN + "|")
            
            # Intentar parsear el body del response
            if hasattr(response, 'body'):
                try:
                    response_body = json.loads(response.body)
                    safe_print(f"RESPONSE:")

                    # Formatear respuesta según el endpoint
                    if request.url.path == "/api/ai/analyze-intent":
                        if response_body.get('success'):
                            intent = response_body.get('intent', {})
                            safe_print(f"   QUERY: '{intent.get('query', '')}'")
                            safe_print(f"   CIUDAD: {intent.get('detected_city', 'N/A')}")
                            safe_print(f"   PROVINCIA: {intent.get('detected_province', 'N/A')}")
                            safe_print(f"   PAIS: {intent.get('detected_country', 'N/A')}")
                            safe_print(f"   CONFIANZA: {intent.get('confidence', 0)*100:.0f}%")
                            hierarchy = intent.get('geographic_hierarchy', {})
                            if hierarchy:
                                safe_print(f"   UBICACION COMPLETA: {hierarchy.get('full_location', 'N/A')}")
                        else:
                            safe_print(f"   ERROR: {response_body.get('error', 'Unknown error')}")
                    else:
                        # Para otros endpoints, mostrar resumen
                        safe_print(json.dumps(response_body, indent=2, ensure_ascii=False)[:500])
                        if len(json.dumps(response_body)) > 500:
                            safe_print("   ... (respuesta truncada)")
                except:
                    safe_print(f"RESPONSE (raw): {response.body[:200]}...")

            safe_print(Fore.CYAN + "=" + "="*78 + "=" + Style.RESET_ALL)
            safe_print(Fore.BLUE + "-"*80 + Style.RESET_ALL)  # Separator between requests
            
            return response

        return custom_route_handler


async def log_request_middleware(request: Request, call_next):
    """
    Middleware alternativo más simple con colores
    """
    start_time = time.time()
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Log simple de entrada con línea separadora
    print(Fore.BLUE + "\n" + "─"*80)
    print(Fore.CYAN + f"[{timestamp}] " + Fore.GREEN + f"{request.method:7}" + Fore.WHITE + f" {request.url.path:<40}" + Fore.YELLOW + f" from {request.client.host}")

    response = await call_next(request)

    process_time = time.time() - start_time
    status_color = Fore.GREEN if response.status_code < 400 else Fore.RED
    time_color = Fore.GREEN if process_time < 1 else Fore.YELLOW if process_time < 3 else Fore.RED

    print(status_color + f"[{timestamp}] Status {response.status_code}" + time_color + f" in {process_time:.3f}s" + Style.RESET_ALL)

    return response