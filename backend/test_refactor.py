#!/usr/bin/env python3
"""
Test simple del servidor refactorizado
"""
import sys
sys.path.append('/mnt/c/Code/eventos-visualizer/backend')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# App simple para test
app = FastAPI(title="Test Refactorizado")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Test refactorizado funcionando", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "server": "refactorizado"}

@app.get("/api/events")
async def get_events():
    return {
        "success": True,
        "events": [
            {
                "id": "test_1",
                "title": "Evento de prueba refactorizado",
                "date": "2025-09-15T20:00:00",
                "venue": "Test Venue"
            }
        ],
        "total": 1,
        "message": "Servidor refactorizado funcionando correctamente"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting test refactored server on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)