import os
import asyncio
import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging
import aiofiles
import httpx
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
HOST = os.getenv("HOST", "172.29.228.80")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))
DB_PATH = "backend/eventos_visualizer.db"

# Buenos Aires Data API
BUENOS_AIRES_API = "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/cultura/agenda-cultural/agenda-cultural.json"

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
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            avatar_url TEXT,
            google_id TEXT,
            latitude REAL,
            longitude REAL,
            radius_km INTEGER DEFAULT 25,
            timezone TEXT DEFAULT 'America/Argentina/Buenos_Aires',
            locale TEXT DEFAULT 'es-AR',
            push_enabled BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_events (
            user_id TEXT,
            event_id TEXT,
            status TEXT DEFAULT 'interested',
            notification_24h_sent BOOLEAN DEFAULT 0,
            notification_1h_sent BOOLEAN DEFAULT 0,
            calendar_synced BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, event_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ SQLite database initialized")

async def fetch_buenos_aires_events():
    """Fetch events from Buenos Aires Open Data API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(BUENOS_AIRES_API)
            response.raise_for_status()
            data = response.json()
            
            events = []
            for item in data[:10]:  # Limit to first 10 events
                try:
                    event = {
                        "id": f"ba_{item.get('id', len(events))}",
                        "title": item.get('titulo', 'Evento sin título'),
                        "description": item.get('descripcion', ''),
                        "start_datetime": item.get('fecha_inicio', ''),
                        "end_datetime": item.get('fecha_fin', ''),
                        "venue_name": item.get('lugar', ''),
                        "venue_address": item.get('direccion', ''),
                        "latitude": float(item.get('lat', 0)) if item.get('lat') else -34.6037,
                        "longitude": float(item.get('lng', 0)) if item.get('lng') else -58.3816,
                        "category": "cultural",
                        "subcategory": item.get('categoria', 'general'),
                        "price": 0.0,
                        "currency": "ARS",
                        "is_free": True,
                        "external_id": item.get('id', ''),
                        "source_api": "buenos_aires_data",
                        "image_url": item.get('imagen', 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4'),
                        "event_url": item.get('link', ''),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Error processing event item: {e}")
                    continue
            
            return events
    except Exception as e:
        logger.error(f"Error fetching Buenos Aires events: {e}")
        return []

async def store_events_in_db(events: List[Dict]):
    """Store events in SQLite database"""
    if not events:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for event in events:
        try:
            # Insert or replace event
            cursor.execute('''
                INSERT OR REPLACE INTO events 
                (id, title, description, start_datetime, end_datetime, venue_name, venue_address,
                 latitude, longitude, category, subcategory, price, currency, is_free,
                 external_id, source_api, image_url, event_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['id'], event['title'], event['description'],
                event['start_datetime'], event['end_datetime'],
                event['venue_name'], event['venue_address'],
                event['latitude'], event['longitude'],
                event['category'], event['subcategory'],
                event['price'], event['currency'], event['is_free'],
                event['external_id'], event['source_api'],
                event['image_url'], event['event_url'],
                event['created_at'], event['updated_at']
            ))
        except Exception as e:
            logger.error(f"Error storing event {event.get('id', 'unknown')}: {e}")
    
    conn.commit()
    conn.close()
    logger.info(f"✅ Stored {len(events)} events in database")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    try:
        logger.info("🚀 Starting Eventos Visualizer Backend with SQLite...")
        
        # Create database directory if not exists
        os.makedirs("backend", exist_ok=True)
        
        # Initialize SQLite database
        init_sqlite_db()
        
        # Fetch and store Buenos Aires events
        ba_events = await fetch_buenos_aires_events()
        await store_events_in_db(ba_events)
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

app = FastAPI(
    title="Eventos Visualizer API",
    description="Sistema completo de eventos mobile-first con PWA - Argentina",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for WSL IP
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://{HOST}:5174",
        "http://172.29.228.80:5174",
        "http://localhost:5174",
        "https://eventos-visualizer.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Test database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server": f"http://{HOST}:{BACKEND_PORT}",
            "service": "eventos-visualizer-backend-sqlite",
            "version": "1.0.0",
            "port": BACKEND_PORT,
            "database": "SQLite",
            "event_count": event_count,
            "message": "🎉 Eventos Visualizer API is running!"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🎉 Eventos Visualizer API - Argentina",
        "version": "1.0.0",
        "database": "SQLite",
        "apis_integradas": ["Buenos Aires Open Data"],
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/api/events",
            "/api/events/search",
            "/api/events/categories",
            "/api/events/refresh",
            "/ws/notifications"
        ]
    }

# Events endpoints
@app.get("/api/events")
async def get_events(
    location: str = "Buenos Aires",
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM events
                WHERE category = ?
                ORDER BY start_datetime ASC
                LIMIT ? OFFSET ?
            ''', (category, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM events
                ORDER BY start_datetime ASC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        rows = cursor.fetchall()
        events = [dict(row) for row in rows]
        
        # Add sample events if database is empty
        if not events:
            events = [
                {
                    "id": "sample_1",
                    "title": "Festival de Rock en Luna Park",
                    "description": "Gran festival con las mejores bandas locales de rock argentino",
                    "start_datetime": "2025-01-15T20:00:00",
                    "venue_name": "Luna Park",
                    "venue_address": "Av. Madero 470, Buenos Aires",
                    "category": "music",
                    "price": 15000.00,
                    "currency": "ARS",
                    "is_free": False,
                    "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
                    "latitude": -34.6037,
                    "longitude": -58.3816,
                    "source_api": "sample"
                },
                {
                    "id": "sample_2",
                    "title": "Teatro: El Avaro",
                    "description": "Clásica obra de Molière en el Teatro San Martín",
                    "start_datetime": "2025-01-18T21:00:00",
                    "venue_name": "Teatro General San Martín",
                    "venue_address": "Av. Corrientes 1530, Buenos Aires",
                    "category": "cultural",
                    "price": 8000.00,
                    "currency": "ARS",
                    "is_free": False,
                    "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",
                    "latitude": -34.6049,
                    "longitude": -58.3837,
                    "source_api": "sample"
                }
            ]
        
        conn.close()
        
        return {
            "status": "success",
            "location": location,
            "category": category,
            "total": len(events),
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return {
            "status": "error",
            "message": str(e),
            "events": []
        }

# Search events endpoint
@app.get("/api/events/search")
async def search_events(
    q: str,
    location: str = "Buenos Aires",
    radius_km: int = 25
):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_pattern = f"%{q}%"
        cursor.execute('''
            SELECT * FROM events
            WHERE (title LIKE ? OR description LIKE ?)
            ORDER BY start_datetime ASC
            LIMIT 50
        ''', (search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        events = [dict(row) for row in rows]
        conn.close()
        
        return {
            "query": q,
            "location": location,
            "radius_km": radius_km,
            "results": len(events),
            "events": events
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "error": str(e),
            "events": []
        }

# Categories endpoint
@app.get("/api/events/categories")
async def get_categories():
    return {
        "categories": [
            {"id": "music", "name": "Música", "icon": "🎵"},
            {"id": "sports", "name": "Deportes", "icon": "⚽"},
            {"id": "cultural", "name": "Cultural", "icon": "🎭"},
            {"id": "tech", "name": "Tecnología", "icon": "💻"},
            {"id": "party", "name": "Fiestas", "icon": "🎉"},
            {"id": "hobbies", "name": "Hobbies", "icon": "🎨"},
            {"id": "international", "name": "Internacional", "icon": "🌍"}
        ]
    }

# Refresh events from external APIs
@app.post("/api/events/refresh")
async def refresh_events():
    """Manually refresh events from Buenos Aires API"""
    try:
        ba_events = await fetch_buenos_aires_events()
        await store_events_in_db(ba_events)
        
        return {
            "status": "success",
            "message": f"Refreshed {len(ba_events)} events from Buenos Aires Data",
            "events_count": len(ba_events),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error refreshing events: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# WebSocket endpoint for notifications
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            notification = {
                "type": "event_reminder",
                "message": message.get("message", "New event notification"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast(json.dumps(notification))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    print(f"\n🚀 Starting Eventos Visualizer Backend (SQLite)")
    print(f"📍 Server: http://{HOST}:{BACKEND_PORT}")
    print(f"📊 Health: http://{HOST}:{BACKEND_PORT}/health")
    print(f"📝 Docs: http://{HOST}:{BACKEND_PORT}/docs")
    print(f"🔌 WebSocket: ws://{HOST}:{BACKEND_PORT}/ws/notifications")
    print(f"💾 Database: SQLite - {DB_PATH}")
    print(f"🌐 API: Buenos Aires Open Data integrated\n")
    
    uvicorn.run(
        "main_sqlite:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
        log_level="info"
    )