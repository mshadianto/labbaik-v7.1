# app/providers/saptco.py
import logging
from sqlalchemy import text
from app.db import get_session
from app.utils.http import get

logger = logging.getLogger(__name__)

SAPTCO_URL = "https://saptco.com.sa/"

ROUTES = ["MAKKAH_MADINAH", "MADINAH_MAKKAH"]


async def fetch_saptco_schedule(route: str = "MAKKAH_MADINAH"):
    """Fetch SAPTCO bus schedule and store in transport_schedule."""
    if route not in ROUTES:
        logger.warning(f"Unknown route: {route}, defaulting to MAKKAH_MADINAH")
        route = "MAKKAH_MADINAH"

    r = await get(SAPTCO_URL, headers={"User-Agent": "umrah-crawler/1.0"})
    async with get_session() as session:
        await session.execute(text("""
          INSERT INTO transport_schedule(mode, operator, route, source_url, source_method)
          VALUES ('BUS', 'SAPTCO', :route, :url, 'HTML')
        """), {"route": route, "url": SAPTCO_URL})
        await session.commit()
    return {"ok": True, "html_len": len(r.text)}
