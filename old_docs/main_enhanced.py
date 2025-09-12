import os
import asyncio
import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging
import httpx

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
HOST = os.getenv("HOST", "172.29.228.80")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))
DB_PATH = "backend/eventos_visualizer.db"

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

def init_sqlite_db():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            start_datetime TEXT,
            end_datetime TEXT,
            venue_name TEXT,
            venue_address TEXT,
            latitude REAL,
            longitude REAL,
            category TEXT,
            subcategory TEXT,
            price REAL,
            currency TEXT DEFAULT 'ARS',
            is_free BOOLEAN DEFAULT 0,
            external_id TEXT,
            source_api TEXT,
            image_url TEXT,
            event_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ SQLite database initialized")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Eventos Visualizer Backend with Enhanced Features...")
    
    # Initialize database
    init_sqlite_db()
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Eventos Visualizer Backend...")

app = FastAPI(
    title="Eventos Visualizer API - Enhanced",
    description="Sistema de eventos con geolocalización automática y búsqueda inteligente",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
try:
    from api.geolocation import router as geo_router
    app.include_router(geo_router, prefix="/api/location", tags=["Geolocation"])
    logger.info("✅ Geolocation API loaded")
except ImportError as e:
    logger.warning(f"Could not import geolocation router: {e}")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "server": f"http://{HOST}:{BACKEND_PORT}",
        "service": "eventos-visualizer-backend-enhanced",
        "version": "2.0.0",
        "features": ["geolocation", "smart-search", "real-time-data"]
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🎉 Eventos Visualizer API - Enhanced Edition",
        "version": "2.0.0",
        "docs": "/docs",
        "features": {
            "geolocation": "Detección automática por IP",
            "smart_search": "Búsqueda inteligente con NLP",
            "real_time": "Datos en tiempo real"
        },
        "endpoints": [
            "/api/location/detect - Detecta ubicación automática",
            "/api/location/cities - Lista ciudades disponibles",
            "/api/events/smart-search - Búsqueda inteligente",
            "/api/events - Eventos por ubicación"
        ]
    }

# Smart search endpoint
@app.get("/api/events/smart-search")
async def smart_search(q: str, location: Optional[str] = None):
    """
    Búsqueda inteligente que entiende queries como:
    - "bares en Mendoza"
    - "restaurantes en Palermo"
    - "conciertos este fin de semana"
    """
    
    # Parse the query to extract intent
    query_lower = q.lower()
    
    # Extract location from query if not provided
    detected_location = location
    locations = {
        "mendoza": "Mendoza",
        "buenos aires": "Buenos Aires",
        "palermo": "Palermo, Buenos Aires",
        "recoleta": "Recoleta, Buenos Aires",
        "córdoba": "Córdoba",
        "rosario": "Rosario"
    }
    
    for key, value in locations.items():
        if key in query_lower:
            detected_location = value
            break
    
    # Extract category
    category = None
    categories = {
        "bar": "bars",
        "restaurante": "restaurants",
        "concierto": "music",
        "teatro": "theater",
        "fiesta": "party"
    }
    
    for key, value in categories.items():
        if key in query_lower:
            category = value
            break
    
    # For now, return sample events based on the search
    sample_events = []
    
    if "bar" in query_lower or "restaurante" in query_lower:
        sample_events = [
            {
                "id": f"smart_1",
                "title": f"Bar Notable en {detected_location or 'Buenos Aires'}",
                "description": "Bar histórico con música en vivo",
                "venue_name": "El Preferido",
                "venue_address": f"{detected_location or 'Buenos Aires'}",
                "category": "bars",
                "price": 0,
                "is_free": True,
                "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b"
            },
            {
                "id": f"smart_2",
                "title": f"Cervecería Artesanal en {detected_location or 'Buenos Aires'}",
                "description": "Happy hour de 18 a 20hs",
                "venue_name": "Cervecería Patagonia",
                "venue_address": f"{detected_location or 'Buenos Aires'}",
                "category": "bars",
                "price": 2500,
                "image_url": "https://images.unsplash.com/photo-1518176258769-f227c798150e"
            }
        ]
    elif "concierto" in query_lower or "música" in query_lower:
        sample_events = [
            {
                "id": f"smart_3",
                "title": f"Concierto de Rock en {detected_location or 'Buenos Aires'}",
                "description": "Bandas locales en vivo",
                "venue_name": "Teatro Flores",
                "venue_address": f"{detected_location or 'Buenos Aires'}",
                "category": "music",
                "price": 8000,
                "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f"
            }
        ]
    
    return {
        "query": q,
        "detected_location": detected_location,
        "detected_category": category,
        "results": sample_events if sample_events else [
            {
                "id": "default_1",
                "title": f"Evento en {detected_location or 'Buenos Aires'}",
                "description": f"Resultado para: {q}",
                "venue_name": "Lugar",
                "venue_address": detected_location or "Buenos Aires",
                "category": category or "general",
                "price": 0,
                "is_free": True,
                "image_url": "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4"
            }
        ],
        "total": len(sample_events) if sample_events else 1,
        "search_metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "method": "smart_nlp"
        }
    }

# Events endpoint with automatic location
@app.get("/api/events")
async def get_events(
    request: Request,
    location: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20
):
    """
    Get events with automatic location detection
    If no location is provided, tries to detect from IP
    """
    
    # If no location provided, try to detect from IP
    if not location:
        try:
            # Get client IP
            client_ip = request.client.host
            
            # If localhost, get public IP
            if client_ip in ["127.0.0.1", "localhost"] or client_ip.startswith("172."):
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.ipify.org?format=json")
                    if response.status_code == 200:
                        client_ip = response.json().get("ip", client_ip)
            
            # Get location from IP
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://ip-api.com/json/{client_ip}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        location = f"{data.get('city', 'Buenos Aires')}, {data.get('country', 'Argentina')}"
        except:
            location = "Buenos Aires, Argentina"
    
    # Return sample events for the location
    events = [
        {
            "id": f"evt_1_{location}",
            "title": f"Festival de Música en {location}",
            "description": "Gran festival con artistas locales",
            "start_datetime": "2025-01-20T20:00:00",
            "venue_name": "Centro Cultural",
            "venue_address": location,
            "category": category or "music",
            "price": 5000,
            "currency": "ARS",
            "is_free": False,
            "image_url": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea",
            "latitude": -34.6037,
            "longitude": -58.3816
        },
        {
            "id": f"evt_2_{location}",
            "title": f"Exposición de Arte en {location}",
            "description": "Muestra de artistas emergentes",
            "start_datetime": "2025-01-22T18:00:00",
            "venue_name": "Galería de Arte",
            "venue_address": location,
            "category": "cultural",
            "price": 0,
            "currency": "ARS",
            "is_free": True,
            "image_url": "https://images.unsplash.com/photo-1531243269054-5ebf6f34081e",
            "latitude": -34.5890,
            "longitude": -58.3820
        },
        {
            "id": f"evt_3_{location}",
            "title": f"Stand Up Comedy en {location}",
            "description": "Noche de humor con los mejores comediantes",
            "start_datetime": "2025-01-19T21:30:00",
            "venue_name": "Teatro Metropolitan",
            "venue_address": location,
            "category": "entertainment",
            "price": 7500,
            "currency": "ARS",
            "is_free": False,
            "image_url": "https://images.unsplash.com/photo-1585699324551-f6c309eedeca",
            "latitude": -34.5975,
            "longitude": -58.3925
        }
    ]
    
    # Filter by category if provided
    if category:
        events = [e for e in events if e["category"] == category]
    
    return {
        "status": "success",
        "location": location,
        "detected_from_ip": not bool(request.url.query.get("location")),
        "category": category,
        "total": len(events),
        "events": events[:limit]
    }

# WebSocket for notifications
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Notification: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    print(f"\n🚀 Starting Eventos Visualizer Backend - Enhanced Edition")
    print(f"📍 Server: http://{HOST}:{BACKEND_PORT}")
    print(f"🌍 Geolocation: http://{HOST}:{BACKEND_PORT}/api/location/detect")
    print(f"🔍 Smart Search: http://{HOST}:{BACKEND_PORT}/api/events/smart-search?q=bares+en+mendoza")
    print(f"📊 Health: http://{HOST}:{BACKEND_PORT}/health")
    print(f"📝 Docs: http://{HOST}:{BACKEND_PORT}/docs\n")
    
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
        log_level="info"
    )