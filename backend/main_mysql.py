import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import aiomysql
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
HOST = os.getenv("HOST", "172.29.228.80")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))

# MySQL configuration
MYSQL_CONFIG = {
    'host': os.getenv("MYSQL_HOST"),
    'port': int(os.getenv("MYSQL_PORT", "3306")),
    'user': os.getenv("MYSQL_USER"),
    'password': os.getenv("MYSQL_PASSWORD"),
    'db': os.getenv("MYSQL_DATABASE"),
    'autocommit': True,
    'charset': 'utf8mb4'
}

# Connection pool for MySQL
pool = None


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

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    try:
        # Create connection pool on startup
        logger.info("🚀 Starting Eventos Visualizer Backend with MySQL...")
        logger.info(f"📊 Connecting to MySQL at {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
        
        pool = await aiomysql.create_pool(
            **MYSQL_CONFIG,
            minsize=5,
            maxsize=20
        )
        logger.info("✅ MySQL pool created successfully")
        
        # Initialize database schema
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Create events table
                await cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        start_datetime DATETIME,
                        end_datetime DATETIME,
                        venue_name VARCHAR(255),
                        venue_address TEXT,
                        latitude DECIMAL(10, 8),
                        longitude DECIMAL(11, 8),
                        category VARCHAR(100),
                        subcategory VARCHAR(100),
                        price DECIMAL(10,2),
                        currency CHAR(3) DEFAULT 'ARS',
                        is_free BOOLEAN DEFAULT false,
                        external_id VARCHAR(255),
                        source_api VARCHAR(50),
                        image_url TEXT,
                        event_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_location (latitude, longitude),
                        INDEX idx_datetime (start_datetime),
                        INDEX idx_category (category)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Create users table
                await cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        avatar_url TEXT,
                        google_id VARCHAR(255),
                        latitude DECIMAL(10, 8),
                        longitude DECIMAL(11, 8),
                        radius_km INTEGER DEFAULT 25,
                        timezone VARCHAR(100) DEFAULT 'America/Argentina/Buenos_Aires',
                        locale VARCHAR(10) DEFAULT 'es-AR',
                        push_enabled BOOLEAN DEFAULT false,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Create user_events table
                await cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_events (
                        user_id VARCHAR(36),
                        event_id VARCHAR(36),
                        status VARCHAR(50) DEFAULT 'interested',
                        notification_24h_sent BOOLEAN DEFAULT false,
                        notification_1h_sent BOOLEAN DEFAULT false,
                        calendar_synced BOOLEAN DEFAULT false,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, event_id),
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Create user_preferences table for AI learning
                await cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
                        user_id VARCHAR(36) NOT NULL UNIQUE,
                        category_weights JSON,
                        preferred_neighborhoods JSON,
                        location_flexibility DECIMAL(3,2) DEFAULT 0.7,
                        preferred_times JSON,
                        price_sensitivity DECIMAL(3,2) DEFAULT 0.6,
                        max_preferred_price DECIMAL(10,2),
                        prefers_free_events BOOLEAN DEFAULT true,
                        group_size_preference VARCHAR(20) DEFAULT 'any',
                        social_events_weight DECIMAL(3,2) DEFAULT 0.5,
                        interaction_history JSON,
                        match_score_history JSON,
                        feedback_score DECIMAL(3,2) DEFAULT 0.5,
                        learning_iterations INTEGER DEFAULT 0,
                        communication_style VARCHAR(20) DEFAULT 'friendly',
                        prefers_suggestions BOOLEAN DEFAULT true,
                        max_suggestions_per_query INTEGER DEFAULT 3,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        last_interaction TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_last_interaction (last_interaction)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Create user_interactions table for learning
                await cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
                        user_id VARCHAR(36) NOT NULL,
                        event_id VARCHAR(36),
                        interaction_type VARCHAR(50) NOT NULL,
                        context JSON,
                        interaction_data JSON,
                        ai_query TEXT,
                        ai_response TEXT,
                        user_feedback VARCHAR(20),
                        duration_seconds INTEGER,
                        success_indicator BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL,
                        INDEX idx_user_interaction (user_id, interaction_type),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Create preference_updates table for audit
                await cursor.execute('''
                    CREATE TABLE IF NOT EXISTS preference_updates (
                        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
                        user_id VARCHAR(36) NOT NULL,
                        field_changed VARCHAR(100) NOT NULL,
                        old_value JSON,
                        new_value JSON,
                        update_reason VARCHAR(100),
                        confidence_score DECIMAL(3,2),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_updates (user_id, created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Insert sample data if events table is empty
                await cursor.execute("SELECT COUNT(*) FROM events")
                (count,) = await cursor.fetchone()
                
                if count == 0:
                    logger.info("📝 Inserting sample events...")
                    sample_events = [
                        ('Festival de Rock en Buenos Aires', 'Gran festival con las mejores bandas locales',
                         '2025-02-15 20:00:00', 'Luna Park', 'Av. Madero 470, Buenos Aires',
                         -34.6037, -58.3816, 'music', 15000.00, False,
                         'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f'),
                        ('Hackathon Tech 2025', '48 horas de innovación tecnológica',
                         '2025-02-20 09:00:00', 'Ciudad Cultural Konex', 'Sarmiento 3131, Buenos Aires',
                         -34.6107, -58.4107, 'tech', 0.00, True,
                         'https://images.unsplash.com/photo-1504384764586-bb4cdc1707b0'),
                        ('Copa Argentina - River vs Boca', 'El superclásico del fútbol argentino',
                         '2025-02-25 18:00:00', 'Estadio Monumental', 'Av. Pres. Figueroa Alcorta 7597',
                         -34.5453, -58.4498, 'sports', 25000.00, False,
                         'https://images.unsplash.com/photo-1508098682722-e99c43a406b2'),
                        ('Fiesta Electrónica Sunset', 'Los mejores DJs internacionales en una noche única',
                         '2025-02-18 22:00:00', 'Costa Salguero', 'Av. Costanera Rafael Obligado',
                         -34.5657, -58.3645, 'party', 18000.00, False,
                         'https://images.unsplash.com/photo-1574391884720-bbc3740c59d1'),
                        ('Exposición de Arte Moderno', 'Obras de artistas latinoamericanos contemporáneos',
                         '2025-02-22 10:00:00', 'MALBA', 'Av. Pres. Figueroa Alcorta 3415',
                         -34.5776, -58.4025, 'cultural', 5000.00, False,
                         'https://images.unsplash.com/photo-1561214115-f2f134cc4912')
                    ]
                    
                    for event in sample_events:
                        await cursor.execute('''
                            INSERT INTO events (title, description, start_datetime, venue_name, 
                                              venue_address, latitude, longitude, category, 
                                              price, is_free, image_url)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', event)
                    
                    logger.info("✅ Sample events inserted")
                
                logger.info("✅ Database schema initialized")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        raise
    finally:
        if pool:
            pool.close()
            await pool.wait_closed()
            logger.info("Database pool closed")

app = FastAPI(
    title="Eventos Visualizer API",
    description="Sistema completo de eventos mobile-first con PWA - MySQL Edition",
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
    global pool
    try:
        if not pool:
            return {"status": "unhealthy", "error": "No database pool"}
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                await cursor.fetchone()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server": f"http://{HOST}:{BACKEND_PORT}",
            "service": "eventos-visualizer-backend",
            "database": "MySQL (Aiven)",
            "version": "1.0.0",
            "port": BACKEND_PORT,
            "message": "🎉 Eventos Visualizer API with MySQL is running!"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Import routers
from api import ai
from api import location
from api import preferences_mysql

# Import service connectors
from services.ticketek_scraper import TicketekArgentinaScraper
from services.facebook_api_scraper import FacebookAPIEventsScraper
from services.instagram_scraper import InstagramEventsScraper
from services.firecrawl_scraper import FirecrawlEventsScraper

# Include routes
app.include_router(ai.router, prefix="/api/ai", tags=["AI Assistant"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(preferences_mysql.router, tags=["User Preferences"])

# NEW: Smart Search con Gemini
from api import smart_search, smart_recommendations
app.include_router(smart_search.router, prefix="/api/smart", tags=["Smart Search with Gemini"])
app.include_router(smart_recommendations.router, prefix="/api/ai", tags=["AI Recommendations & Intent Analysis"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🎉 Eventos Visualizer API (MySQL Edition)",
        "version": "1.0.0",
        "database": "MySQL on Aiven Cloud",
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
            "/api/location/detect",
            "/api/location/nearest",
            "/api/location/parse-text",
            "/api/preferences/{user_id}",
            "/api/preferences/{user_id}/interaction",
            "/api/preferences/{user_id}/feedback",
            "/api/preferences/{user_id}/stats",
            "/api/preferences/{user_id}/learn",
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
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if category:
                    query = '''
                        SELECT * FROM events
                        WHERE category = %s
                        ORDER BY start_datetime ASC
                        LIMIT %s OFFSET %s
                    '''
                    await cursor.execute(query, (category, limit, offset))
                else:
                    query = '''
                        SELECT * FROM events
                        ORDER BY start_datetime ASC
                        LIMIT %s OFFSET %s
                    '''
                    await cursor.execute(query, (limit, offset))
                
                events = await cursor.fetchall()
                
                # Convert datetime objects to ISO format
                for event in events:
                    if event.get('start_datetime'):
                        event['start_datetime'] = event['start_datetime'].isoformat()
                    if event.get('end_datetime') and event['end_datetime']:
                        event['end_datetime'] = event['end_datetime'].isoformat()
                    # Convert decimal to float
                    if event.get('price'):
                        event['price'] = float(event['price'])
                    if event.get('latitude'):
                        event['latitude'] = float(event['latitude'])
                    if event.get('longitude'):
                        event['longitude'] = float(event['longitude'])
            
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
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = '''
                    SELECT * FROM events
                    WHERE 
                        (title LIKE %s OR description LIKE %s)
                        AND start_datetime > NOW()
                    ORDER BY start_datetime ASC
                    LIMIT 50
                '''
                
                search_pattern = f"%{q}%"
                await cursor.execute(query, (search_pattern, search_pattern))
                events = await cursor.fetchall()
                
                # Convert datetime to ISO format
                for event in events:
                    if event.get('start_datetime'):
                        event['start_datetime'] = event['start_datetime'].isoformat()
                    if event.get('price'):
                        event['price'] = float(event['price'])
                
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

# Get single event
@app.get("/api/events/{event_id}")
async def get_event(event_id: str):
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = "SELECT * FROM events WHERE id = %s"
                await cursor.execute(query, (event_id,))
                event = await cursor.fetchone()
                
                if not event:
                    raise HTTPException(status_code=404, detail="Event not found")
                
                # Convert datetime to ISO format
                if event.get('start_datetime'):
                    event['start_datetime'] = event['start_datetime'].isoformat()
                if event.get('end_datetime') and event['end_datetime']:
                    event['end_datetime'] = event['end_datetime'].isoformat()
                if event.get('price'):
                    event['price'] = float(event['price'])
                if event.get('latitude'):
                    event['latitude'] = float(event['latitude'])
                if event.get('longitude'):
                    event['longitude'] = float(event['longitude'])
                
                return {
                    "status": "success",
                    "event": event
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Categories endpoint
@app.get("/api/events/categories")
async def get_categories():
    return {
        "categories": [
            {"id": "music", "name": "Música", "icon": "🎵"},
            {"id": "theater", "name": "Teatro", "icon": "🎭"},
            {"id": "sports", "name": "Deportes", "icon": "⚽"},
            {"id": "family", "name": "Familiares", "icon": "👨‍👩‍👧‍👦"},
            {"id": "cultural", "name": "Cultural", "icon": "🎨"},
            {"id": "tech", "name": "Tecnología", "icon": "💻"},
            {"id": "party", "name": "Fiestas", "icon": "🎉"},
            {"id": "general", "name": "General", "icon": "📅"}
        ]
    }

# Refresh events from external sources
@app.post("/api/events/refresh")
async def refresh_events():
    """Manually refresh events from all sources"""
    global pool
    try:
        logger.info("🔄 Starting event refresh from sources...")
        
        all_events = []
        
        # 1. Get events from Ticketek Argentina scraper
        try:
            ticketek_scraper = TicketekArgentinaScraper()
            ticketek_events = await ticketek_scraper.fetch_all_events()
            all_events.extend(ticketek_events)
            logger.info(f"✅ Ticketek: {len(ticketek_events)} events fetched")
        except Exception as e:
            logger.error(f"❌ Error fetching Ticketek events: {e}")
        
        # 2. Get events from Facebook API scraper
        try:
            facebook_scraper = FacebookAPIEventsScraper()
            facebook_events = await facebook_scraper.fetch_all_events()
            all_events.extend(facebook_events)
            logger.info(f"✅ Facebook: {len(facebook_events)} events fetched")
        except Exception as e:
            logger.error(f"❌ Error fetching Facebook events: {e}")
        
        # 3. Get events from Instagram scraper
        try:
            instagram_scraper = InstagramEventsScraper()
            instagram_events = await instagram_scraper.fetch_all_events(hashtags_limit=3, posts_per_hashtag=4)
            all_events.extend(instagram_events)
            logger.info(f"✅ Instagram: {len(instagram_events)} events fetched")
        except Exception as e:
            logger.error(f"❌ Error fetching Instagram events: {e}")
        
        # 4. Get events from Firecrawl scraper (NEW!)
        try:
            firecrawl_scraper = FirecrawlEventsScraper()
            firecrawl_events = await firecrawl_scraper.fetch_all_events(limit_sources=2)
            all_events.extend(firecrawl_events)
            logger.info(f"✅ Firecrawl: {len(firecrawl_events)} events fetched")
        except Exception as e:
            logger.error(f"❌ Error fetching Firecrawl events: {e}")
        
        # Store events in database
        stored_count = 0
        if all_events:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    for event in all_events:
                        try:
                            await cursor.execute('''
                                INSERT INTO events (title, description, start_datetime, end_datetime, 
                                                  venue_name, venue_address, latitude, longitude, 
                                                  category, subcategory, price, currency, is_free,
                                                  external_id, source_api, image_url, event_url)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                updated_at = NOW()
                            ''', (
                                event['title'], 
                                event.get('description', ''),
                                event['start_datetime'], 
                                event.get('end_datetime'),
                                event.get('venue_name', ''), 
                                event.get('venue_address', ''),
                                event.get('latitude'), 
                                event.get('longitude'),
                                event.get('category', 'general'), 
                                event.get('subcategory', ''),
                                event.get('price', 0), 
                                event.get('currency', 'ARS'), 
                                1 if event.get('is_free') else 0,
                                event.get('external_id', ''), 
                                event.get('source', 'ticketek_argentina'),
                                event.get('image_url', ''), 
                                event.get('event_url', '')
                            ))
                            stored_count += 1
                        except Exception as e:
                            logger.error(f"Error storing event {event.get('title', 'unknown')}: {e}")
        
        return {
            "status": "success",
            "message": f"Refreshed events from external sources",
            "events_fetched": len(all_events),
            "events_stored": stored_count,
            "sources": ["Ticketek Argentina", "Facebook Events", "Instagram Events"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error refreshing events: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# Multi-source scraper endpoint
@app.get("/api/multi/fetch-all")
async def multi_fetch_all(location: str = "Buenos Aires"):
    """Fetch events from multiple sources with progressive loading"""
    try:
        # Import and use the cloudscraper that was working
        import sys
        sys.path.append('/mnt/c/Code/eventos-visualizer/backend')
        
        from services.progressive_sync_scraper import ProgressiveSyncScraper
        scraper = ProgressiveSyncScraper()
        events = await scraper.fetch_progressive_sync(location=location)
        result = {"events": events, "message": f"Progressive sync completed with {len(events)} events"}
        
        return {
            "status": "success",
            "location": location,
            "events": result.get("events", []),
            "count": len(result.get("events", [])),
            "message": result.get("message", "Multi-source fetch completed"),
            "strategy": result.get("strategy", "progressive_sync"),
            "phases": result.get("phases", ["cache", "fast_sources"]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Multi-source fetch error: {e}")
        return {
            "status": "error",
            "location": location,
            "events": [],
            "count": 0,
            "message": f"Error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

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
    print(f"\n🚀 Starting Eventos Visualizer Backend with MySQL")
    print(f"📊 Database: MySQL on Aiven Cloud")
    print(f"📍 Server: http://{HOST}:{BACKEND_PORT}")
    print(f"📊 Health: http://{HOST}:{BACKEND_PORT}/health")
    print(f"📝 Docs: http://{HOST}:{BACKEND_PORT}/docs")
    print(f"🔌 WebSocket: ws://{HOST}:{BACKEND_PORT}/ws/notifications")
    print(f"🧠 AI: Gemini Brain Integration Active\n")
    
    uvicorn.run(
        "main_mysql:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
        log_level="info"
    )