from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from services.eventbrite import EventbriteService
from services.ticketmaster import TicketmasterService

router = APIRouter()

@router.get("/events/search")
async def search_external_events(
    location: Optional[str] = Query(None, description="Location to search (e.g., Buenos Aires)"),
    latitude: Optional[float] = Query(None, description="Latitude for location search"),
    longitude: Optional[float] = Query(None, description="Longitude for location search"),
    radius: Optional[int] = Query(25, ge=1, le=100, description="Radius in km"),
    categories: Optional[List[str]] = Query(None, description="Event categories to filter"),
    source: Optional[str] = Query(None, description="API source: 'eventbrite' or 'ticketmaster'"),
    date_from: Optional[datetime] = Query(None, description="Filter events from date"),
    date_to: Optional[datetime] = Query(None, description="Filter events to date"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Maximum events to return")
):
    """Search events from external APIs (Eventbrite, Ticketmaster)"""
    
    all_events = []
    
    try:
        # Search Eventbrite
        if not source or source == "eventbrite":
            eventbrite_service = EventbriteService()
            try:
                eventbrite_events = await eventbrite_service.search_events(
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    radius=f"{radius}km",
                    categories=categories or [],
                    start_date=date_from,
                    end_date=date_to,
                    page=1
                )
                all_events.extend(eventbrite_events)
            finally:
                await eventbrite_service.close()
        
        # Search Ticketmaster
        if not source or source == "ticketmaster":
            ticketmaster_service = TicketmasterService()
            try:
                ticketmaster_events = await ticketmaster_service.search_events(
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    radius=str(radius),
                    categories=categories or [],
                    start_date=date_from,
                    end_date=date_to,
                    page=0,
                    size=min(limit, 20)
                )
                all_events.extend(ticketmaster_events)
            finally:
                await ticketmaster_service.close()
        
        # Sort by date and limit results
        all_events.sort(key=lambda x: x.get('start_datetime') or datetime.min)
        all_events = all_events[:limit]
        
        return {
            "events": all_events,
            "total": len(all_events),
            "source": source or "all",
            "location": location,
            "radius_km": radius
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching external APIs: {str(e)}"
        )

@router.get("/events/eventbrite")
async def search_eventbrite_events(
    location: Optional[str] = Query("Buenos Aires", description="Location to search"),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius: Optional[int] = Query(25, ge=1, le=100),
    categories: Optional[List[str]] = Query(None),
    page: Optional[int] = Query(1, ge=1)
):
    """Search events specifically from Eventbrite API"""
    
    eventbrite_service = EventbriteService()
    
    try:
        events = await eventbrite_service.search_events(
            location=location,
            latitude=latitude,
            longitude=longitude,
            radius=f"{radius}km",
            categories=categories or [],
            page=page
        )
        
        return {
            "events": events,
            "total": len(events),
            "source": "eventbrite",
            "page": page
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Eventbrite events: {str(e)}"
        )
    finally:
        await eventbrite_service.close()

@router.get("/events/ticketmaster")
async def search_ticketmaster_events(
    location: Optional[str] = Query("Buenos Aires", description="Location to search"),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None), 
    radius: Optional[int] = Query(25, ge=1, le=100),
    categories: Optional[List[str]] = Query(None),
    page: Optional[int] = Query(0, ge=0)
):
    """Search events specifically from Ticketmaster API"""
    
    ticketmaster_service = TicketmasterService()
    
    try:
        events = await ticketmaster_service.search_events(
            location=location,
            latitude=latitude,
            longitude=longitude,
            radius=str(radius),
            categories=categories or [],
            page=page
        )
        
        return {
            "events": events,
            "total": len(events),
            "source": "ticketmaster",
            "page": page
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Ticketmaster events: {str(e)}"
        )
    finally:
        await ticketmaster_service.close()