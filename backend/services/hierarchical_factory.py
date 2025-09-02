# Hierarchical Factory module
# Legacy compatibility layer that delegates to IndustrialFactory

from typing import List, Dict, Any, Optional
import logging
from services.industrial_factory import IndustrialFactory

logger = logging.getLogger(__name__)

async def fetch_from_all_sources_internal(
    location: str = "Buenos Aires",
    category: Optional[str] = None,
    limit: int = 30,
    fast: bool = False,  # Legacy parameter, ignored
    detected_country: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Legacy compatibility function for fetch_from_all_sources_internal
    Returns data in the expected format with events and metadata
    """
    try:
        logger.info(f"🔄 fetch_from_all_sources_internal: Delegating to appropriate factory for {location}")
        
        # Fallback to IndustrialFactory for global scrapers
        factory = IndustrialFactory()
        result = await factory.execute_global_scrapers_with_details(location, category, limit, detected_country, context_data)
        
        events = result.get('events', [])
        scrapers_execution = result.get('scrapers_execution', {})
        
        # Return in expected format
        formatted_result = {
            "events": events,
            "count": len(events),
            "scraper_used": "IndustrialFactory-Hierarchical",
            "source_info": [
                {
                    "source": "IndustrialFactory",
                    "count": len(events),
                    "status": "success" if events else "empty"
                }
            ],
            "location": location,
            "scrapers_execution": scrapers_execution  # New detailed execution data
        }
        
        logger.info(f"✅ fetch_from_all_sources_internal: Retrieved {len(events)} events via IndustrialFactory with details")
        return formatted_result
        
    except Exception as e:
        logger.error(f"❌ fetch_from_all_sources_internal error: {e}")
        return {
            "events": [],
            "count": 0,
            "scraper_used": "error",
            "source_info": [],
            "location": location,
            "error": str(e),
            "scrapers_execution": {
                "scrapers_called": [],
                "total_scrapers": 0,
                "scrapers_info": [],
                "summary": f"Error: {str(e)}"
            }
        }

async def get_events_hierarchical(
    location: str = "Buenos Aires", 
    category: Optional[str] = None,
    limit: int = 30
) -> List[Dict[str, Any]]:
    """
    Legacy compatibility function that uses IndustrialFactory
    
    Args:
        location: Location to search events
        category: Optional category filter
        limit: Maximum events per scraper
        
    Returns:
        List of events from all available scrapers
    """
    try:
        logger.info(f"🔄 hierarchical_factory: Delegating to IndustrialFactory for {location}")
        
        # Use the modern IndustrialFactory
        factory = IndustrialFactory()
        events = await factory.execute_global_scrapers(location, category, limit, context_data={})
        
        logger.info(f"✅ hierarchical_factory: Retrieved {len(events)} events via IndustrialFactory")
        return events
        
    except Exception as e:
        logger.error(f"❌ hierarchical_factory error: {e}")
        return []

async def fetch_from_all_sources(
    location: str = "Buenos Aires",
    category: Optional[str] = None,
    limit: int = 30
) -> List[Dict[str, Any]]:
    """
    Legacy compatibility function for fetch_from_all_sources
    Returns list of events directly
    """
    try:
        logger.info(f"🔄 fetch_from_all_sources: Delegating to IndustrialFactory for {location}")
        
        # Use the modern IndustrialFactory
        factory = IndustrialFactory()
        events = await factory.execute_global_scrapers(location, category, limit, context_data={})
        
        logger.info(f"✅ fetch_from_all_sources: Retrieved {len(events)} events via IndustrialFactory")
        return events
        
    except Exception as e:
        logger.error(f"❌ fetch_from_all_sources error: {e}")
        return []