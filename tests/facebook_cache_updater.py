#!/usr/bin/env python3
"""
Heroku Scheduler Script - Facebook Cache Updater
🚀 Se ejecuta cada 6 horas via Heroku Scheduler add-on
⚡ Actualiza cache de eventos Facebook en background

Comando para Heroku Scheduler:
python facebook_cache_updater.py
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add backend to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.rapidapi_facebook_scraper import RapidApiFacebookScraper

# Load environment variables
load_dotenv()

# Configure logging for Heroku
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def update_facebook_cache():
    """
    Actualiza cache de Facebook para Heroku
    🕰️ Ejecutado por Heroku Scheduler cada 6 horas
    """
    try:
        logger.info("🔥 HEROKU SCHEDULER: Iniciando actualización Facebook cache...")
        
        # Verificar API key
        if not os.getenv("RAPIDAPI_KEY"):
            logger.error("❌ RAPIDAPI_KEY no configurado en Heroku config vars")
            return
        
        # Crear scraper
        facebook_scraper = RapidApiFacebookScraper()
        
        # Hacer scraping (puede tardar 20s, no hay problema aquí)
        default_city = os.getenv("DEFAULT_CITY", "Buenos Aires")
        events = await facebook_scraper.scrape_facebook_events_rapidapi(
            city_name=default_city, 
            limit=50, 
            max_time_seconds=30.0
        )
        
        if events:
            logger.info(f"✅ HEROKU SCHEDULER: Cache actualizado con {len(events)} eventos")
            logger.info(f"📅 Próxima ejecución: +6 horas")
        else:
            logger.warning("⚠️ HEROKU SCHEDULER: No se obtuvieron eventos")
            
    except Exception as e:
        logger.error(f"❌ HEROKU SCHEDULER ERROR: {e}")
        # Heroku logs el error pero no crashea

def main():
    """
    Entry point para Heroku Scheduler
    """
    logger.info("🚀 Facebook Cache Updater - Heroku Scheduler")
    logger.info(f"📅 Ejecutado en: {datetime.now()}")
    
    # Run async function
    asyncio.run(update_facebook_cache())
    
    logger.info("🎯 Facebook Cache Updater completado")

if __name__ == "__main__":
    main()