"""
Middleware JWT para autenticación
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
import logging

from utils.config import settings

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que verifica JWT tokens en rutas protegidas
    """

    # Rutas públicas que no requieren autenticación
    PUBLIC_ROUTES = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/auth/google/login",
        "/auth/google/callback",
        "/api/events",  # Listar eventos público
        "/api/location",
        "/api/smart/search",
        "/api/ai",
    ]

    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada request y verifica autenticación si es necesario
        """
        path = request.url.path

        # Verificar si es una ruta pública
        is_public = any(path.startswith(route) for route in self.PUBLIC_ROUTES)

        if not is_public:
            # Verificar token JWT
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "No autenticado. Token no proporcionado."},
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Extraer token (formato: "Bearer <token>")
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    raise ValueError("Esquema de autenticación inválido")
            except (ValueError, AttributeError):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Formato de token inválido. Use: Bearer <token>"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Verificar token
            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret_key,
                    algorithms=[settings.jwt_algorithm]
                )
                # Agregar payload al request state para uso posterior
                request.state.user_id = payload.get("sub")
                request.state.email = payload.get("email")
            except JWTError as e:
                logger.warning(f"⚠️ Token JWT inválido: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token inválido o expirado"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

        # Continuar con el request
        response = await call_next(request)
        return response


class CORSMiddleware:
    """
    Middleware personalizado para CORS
    (Nota: FastAPI ya tiene CORSMiddleware, esto es un ejemplo)
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))

            # Agregar headers CORS
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers_list = list(message.get("headers", []))
                    headers_list.append((b"access-control-allow-origin", b"*"))
                    headers_list.append((b"access-control-allow-credentials", b"true"))
                    message["headers"] = headers_list
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
