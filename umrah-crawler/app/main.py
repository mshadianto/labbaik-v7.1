from fastapi import FastAPI, Query, HTTPException
from datetime import date
import os
from typing import Optional

from app.db import init_db, get_session, is_db_configured
from app.crud import (
    search_hotels, get_hotel_offers, get_calendar, get_transport
)
from app.jobs import bootstrap_jobs, dequeue_and_run, start_scheduler

app = FastAPI(title="Umrah Hotel & Transport API")

# =============================================================================
# AMADEUS API (Optional - requires AMADEUS_CLIENT_ID/SECRET)
# =============================================================================

_amadeus_client = None


def get_amadeus_client():
    """Get or create Amadeus client (lazy initialization)."""
    global _amadeus_client
    if _amadeus_client is None:
        if not os.getenv("AMADEUS_CLIENT_ID"):
            return None
        from app.amadeus.auth import AmadeusAuth
        from app.amadeus.client import AmadeusClient
        _amadeus_client = AmadeusClient(AmadeusAuth())
    return _amadeus_client


@app.on_event("startup")
async def startup():
    await init_db()
    start_scheduler()


@app.get("/health")
async def health():
    return {
        "ok": True,
        "database": "connected" if is_db_configured() else "not_configured"
    }


@app.get("/search_hotels")
async def api_search_hotels(
    city: str = Query(..., pattern="^(MAKKAH|MADINAH)$"),
    checkin: date = Query(...),
    checkout: date = Query(...),
    adults: int = 2,
    children: int = 0,
    max_hotels: int = 50,
):
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="Database not configured")
    async with get_session() as session:
        return await search_hotels(session, city, checkin, checkout, adults, children, max_hotels)


@app.get("/hotel/{hotel_id}/offers")
async def api_hotel_offers(hotel_id: str, limit: int = 50):
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="Database not configured")
    async with get_session() as session:
        return await get_hotel_offers(session, hotel_id, limit)


@app.get("/availability/calendar")
async def api_calendar(
    hotel_id: str,
    start: date,
    end: date,
    provider: str | None = None
):
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="Database not configured")
    async with get_session() as session:
        return await get_calendar(session, hotel_id, start, end, provider)


@app.get("/transport/makkah-madinah")
async def api_transport(mode: str = Query("TRAIN", pattern="^(TRAIN|BUS)$"), limit: int = 50):
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="Database not configured")
    async with get_session() as session:
        return await get_transport(session, "MAKKAH_MADINAH", mode, limit)


@app.post("/crawl/bootstrap")
async def api_bootstrap_jobs():
    """Bootstrap all crawl jobs for hotels and transport."""
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="Database not configured")
    await bootstrap_jobs()
    return {"status": "jobs_queued", "message": "Crawl jobs for Makkah and Madinah have been queued"}


@app.post("/crawl/run")
async def api_run_jobs(batch: int = 10):
    """Manually trigger job processing."""
    if not is_db_configured():
        raise HTTPException(status_code=503, detail="Database not configured")
    await dequeue_and_run(batch)
    return {"status": "processed", "batch_size": batch}


# =============================================================================
# AMADEUS DIRECT API ENDPOINTS
# =============================================================================

@app.get("/amadeus/hotels")
async def amadeus_hotels(
    city: str = Query(..., pattern="^(MAKKAH|MADINAH)$"),
    checkin: date = Query(...),
    checkout: date = Query(...),
    adults: int = 2,
    radius_km: int = 6,
):
    """
    Search hotels via Amadeus API (direct, no DB).
    Returns hotels sorted by distance to Haram/Nabawi.
    """
    client = get_amadeus_client()
    if not client:
        raise HTTPException(status_code=503, detail="Amadeus API not configured")

    from app.amadeus.hotels import hotel_search_by_city
    return await hotel_search_by_city(
        client, city, str(checkin), str(checkout), adults=adults, radius_km=radius_km
    )


@app.get("/amadeus/flights")
async def amadeus_flights(
    origin: str = Query(..., description="Origin airport code (e.g., CGK, JKT)"),
    dest: str = Query(..., description="Destination airport code (e.g., JED, MED)"),
    depart: date = Query(...),
    ret: Optional[date] = Query(None, description="Return date for round trip"),
    adults: int = 2,
    currency: str = "SAR",
):
    """
    Search flights via Amadeus API.
    """
    client = get_amadeus_client()
    if not client:
        raise HTTPException(status_code=503, detail="Amadeus API not configured")

    from app.amadeus.flights import flight_offers_search
    return await flight_offers_search(
        client, origin, dest, str(depart),
        ret=str(ret) if ret else None,
        adults=adults,
        currency=currency,
    )


@app.get("/amadeus/transfers")
async def amadeus_transfers(
    city: str = Query(..., pattern="^(MAKKAH|MADINAH)$"),
    pickup: str = Query(..., description="Pickup datetime ISO format (e.g., 2026-01-09T10:00:00)"),
    passengers: int = 2,
    transfer_type: str = Query("PRIVATE", pattern="^(PRIVATE|SHARED)$"),
):
    """
    Search airport transfers via Amadeus API.
    Returns transfer offers from airport (JED/MED) to city center (Haram/Nabawi).
    """
    client = get_amadeus_client()
    if not client:
        raise HTTPException(status_code=503, detail="Amadeus API not configured")

    from app.amadeus.transfers import transfer_search_to_city
    return await transfer_search_to_city(
        client, city, pickup, passengers=passengers, transfer_type=transfer_type
    )


@app.get("/amadeus/status")
async def amadeus_status():
    """Check Amadeus API configuration status."""
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    env = os.getenv("AMADEUS_ENV", "test")

    return {
        "configured": bool(client_id),
        "environment": env,
        "client_id_prefix": client_id[:8] + "..." if client_id else None,
    }
