"""
Routers package - Importa todos los routers disponibles
"""
# Solo importar los routers que existen
from . import sources, search, websocket

__all__ = [
    "sources",
    "search",
    "websocket"
]

print("✅ Routers cargados: sources, search, websocket")