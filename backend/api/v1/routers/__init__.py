"""
Routers package - Importa todos los routers disponibles
"""
try:
    from . import system, events, sources, search, websocket
    
    __all__ = [
        "system",
        "events", 
        "sources",
        "search",
        "websocket"
    ]
    
    print("✅ All routers imported successfully")
    
except ImportError as e:
    print(f"⚠️ Warning: Some routers could not be imported: {e}")
    # Importar los disponibles
    try:
        from . import system
        __all__ = ["system"]
    except ImportError:
        __all__ = []