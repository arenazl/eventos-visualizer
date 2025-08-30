import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging
import sys

# Add backend to path for imports
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
HOST = os.getenv("HOST", "172.29.228.80")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))

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

# In-memory storage for development
events_storage = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Eventos Visualizer Backend (Dev Mode)...")
    
    # Initialize sample data
    global events_storage
    events_storage = [
     
    ]
    
    logger.info("✅ Sample data loaded")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Eventos Visualizer Backend...")

app = FastAPI(
    title="Eventos Visualizer API",
    description="Sistema completo de eventos mobile-first con PWA",
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
        "https://eventos-visualizer.vercel.app",
        "*"  # Allow all origins in dev mode
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "server": f"http://{HOST}:{BACKEND_PORT}",
        "service": "eventos-visualizer-backend",
        "version": "1.0.0",
        "port": BACKEND_PORT,
        "mode": "development",
        "message": "🎉 Eventos Visualizer API is running!"
    }

# Import AI router
from api import ai

# Include AI routes
app.include_router(ai.router, prefix="/api/ai", tags=["AI Assistant"])

# Import the new events aggregator API endpoints
try:
    from api.events_endpoints import router as events_router
    app.include_router(events_router)
    logger.info("✅ Events aggregator API endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Could not import events_endpoints router: {e}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🎉 Eventos Visualizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/api/events",
            "/api/events/search",
            "/api/events/categories",
            "/api/ai/chat",
            "/api/ai/recommendations",
            "/api/ai/plan-weekend",
            "/api/ai/trending-now",
            "/api/ai/gemini/feedback",
            "/api/ai/gemini/profile/{user_id}",
            "/ws/notifications"
        ]
    }

# Events endpoints - Commented out because we're using the aggregator endpoints
# @app.get("/api/events")
# async def get_events(
#     location: str = "Buenos Aires",
#     category: Optional[str] = None,
#     limit: int = 20,
#     offset: int = 0
# ):
#     global events_storage
#     
#     # Filter by category if provided
#     filtered_events = events_storage
#     if category:
#         filtered_events = [e for e in events_storage if e.get("category") == category]
#     
#     # Apply pagination
#     paginated_events = filtered_events[offset:offset + limit]
#     
#     return {
#         "status": "success",
#         "location": location,
#         "category": category,
#         "total": len(paginated_events),
#         "events": paginated_events
#     }

# Search events endpoint - Commented out because we're using the aggregator endpoints
# @app.get("/api/events/search")
# async def search_events(
#     q: str,
#     location: str = "Buenos Aires",
#     radius_km: int = 25
# ):
#     global events_storage
#     
#     # Simple search in title and description
#     search_results = []
#     query_lower = q.lower()
#     
#     for event in events_storage:
#         if (query_lower in event.get("title", "").lower() or 
#             query_lower in event.get("description", "").lower()):
#             search_results.append(event)
#     
#     return {
#         "query": q,
#         "location": location,
#         "radius_km": radius_km,
#         "results": len(search_results),
#         "events": search_results
#     }

# Get single event - Commented out because we're using the aggregator endpoints
# @app.get("/api/events/{event_id}")
# async def get_event(event_id: str):
#     global events_storage
#     
#     for event in events_storage:
#         if event.get("id") == event_id:
#             return {
#                 "status": "success",
#                 "event": event
#             }
#     
#     raise HTTPException(status_code=404, detail="Event not found")

# Categories endpoint - Commented out because we're using the aggregator endpoints
# @app.get("/api/events/categories")
# async def get_categories():
#     return {
#         "categories": [
#             {"id": "music", "name": "Música", "icon": "🎵"},
#             {"id": "sports", "name": "Deportes", "icon": "⚽"},
#             {"id": "cultural", "name": "Cultural", "icon": "🎭"},
#             {"id": "tech", "name": "Tecnología", "icon": "💻"},
#             {"id": "party", "name": "Fiestas", "icon": "🎉"},
#             {"id": "hobbies", "name": "Hobbies", "icon": "🎨"},
#             {"id": "international", "name": "Internacional", "icon": "🌍"}
#         ]
#     }

# WebSocket endpoint for notifications
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process received message
            message = json.loads(data)
            
            # Broadcast notification to all connected clients
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
    print(f"\n🚀 Starting Eventos Visualizer Backend (Development Mode)")
    print(f"📍 Server: http://{HOST}:{BACKEND_PORT}")
    print(f"📊 Health: http://{HOST}:{BACKEND_PORT}/health")
    print(f"📝 Docs: http://{HOST}:{BACKEND_PORT}/docs")
    print(f"🔌 WebSocket: ws://{HOST}:{BACKEND_PORT}/ws/notifications")
    print(f"⚠️  Running in development mode with sample data\n")
    
    uvicorn.run(
        "main_dev:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
        log_level="info"
    )