"""
🚨 TIMEOUT INTERCEPTOR - Evita que el backend se cuelgue
Interceptor global que corta la ejecución si tarda demasiado
"""

import asyncio
import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class TimeoutInterceptor(BaseHTTPMiddleware):
    """
    🚨 INTERCEPTOR DE TIMEOUT GLOBAL
    
    FUNCIONALIDADES:
    - Corta requests que tardan más del límite
    - Retorna error 504 Gateway Timeout
    - Informa al cliente del problema
    - Previene que el backend se cuelgue
    """
    
    def __init__(self, app, timeout_seconds: int = 30):
        """
        Args:
            app: FastAPI application
            timeout_seconds: Máximo tiempo de ejecución (default 30s para scrapers lentos)
        """
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
        
    async def dispatch(self, request: Request, call_next):
        """
        🚨 INTERCEPTA CADA REQUEST Y APLICA TIMEOUT
        """
        start_time = time.time()
        
        try:
            # Crear task para el request
            response_task = asyncio.create_task(call_next(request))
            
            # Esperar con timeout
            response = await asyncio.wait_for(
                response_task, 
                timeout=self.timeout_seconds
            )
            
            # Log de tiempo de ejecución
            duration = time.time() - start_time
            if duration > 5:  # Warning si tarda más de 5s
                logger.warning(f"⚠️ Request lento: {request.url.path} tardó {duration:.2f}s")
            
            return response
            
        except asyncio.TimeoutError:
            # Request excedió el timeout
            duration = time.time() - start_time
            
            error_message = (
                f"La búsqueda excedió el tiempo límite de {self.timeout_seconds} segundos. "
                f"Intenta con una ubicación más específica o inténtalo nuevamente."
            )
            
            logger.error(f"❌ TIMEOUT: {request.url.path} cancelado después de {duration:.2f}s")
            
            # Retornar error 504 Gateway Timeout
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "message": error_message,
                    "timeout_seconds": self.timeout_seconds,
                    "actual_duration": f"{duration:.2f}s",
                    "path": str(request.url.path),
                    "suggestion": "Intenta buscar una ciudad específica en lugar de una región amplia"
                }
            )
            
        except Exception as e:
            # Otro error inesperado
            logger.error(f"❌ Error en interceptor: {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "Error procesando la solicitud",
                    "details": str(e)
                }
            )