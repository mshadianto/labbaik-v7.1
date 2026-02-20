"""
Haramain Railway timetable provider.

Strategy: Portlet JSON endpoint → HTML parse → static schedule fallback.
Uses haramain_portlet.py for real-time data, falls back to known schedules.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from sqlalchemy import text

from app.db import get_session, is_db_configured
from app.utils.http import get

logger = logging.getLogger(__name__)

HARAMAIN_URL = "https://sar.hhr.sa/#/timetable"

# Static fallback schedule (known Haramain timetable)
STATIC_SCHEDULES = [
    {"depart": "06:30", "arrive": "08:30", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "08:00", "arrive": "10:00", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "10:00", "arrive": "12:00", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "12:00", "arrive": "14:00", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "14:00", "arrive": "16:00", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "16:00", "arrive": "18:00", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "18:00", "arrive": "20:00", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "20:00", "arrive": "22:00", "duration": 120, "class": "ECONOMY", "price": 75},
    {"depart": "06:30", "arrive": "08:30", "duration": 120, "class": "BUSINESS", "price": 150},
    {"depart": "12:00", "arrive": "14:00", "duration": 120, "class": "BUSINESS", "price": 150},
    {"depart": "18:00", "arrive": "20:00", "duration": 120, "class": "BUSINESS", "price": 150},
]


def _parse_html_timetable(soup: BeautifulSoup) -> List[Dict]:
    """
    Parse Haramain HTML timetable page.

    Tries multiple CSS selector strategies to extract schedule rows.
    """
    rows = []

    # Strategy 1: table rows
    for selector in [
        "table.timetable tr", "table.schedule tr",
        ".timetable-row", ".trip-row", ".schedule-item",
        "tr[data-trip]", ".journey-item",
    ]:
        items = soup.select(selector)
        if not items:
            continue

        for item in items:
            cells = item.select("td")
            if len(cells) < 2:
                continue

            depart_text = cells[0].get_text(strip=True)
            arrive_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            if not depart_text or ":" not in depart_text:
                continue

            row = {"depart": depart_text, "arrive": arrive_text}

            if len(cells) > 2:
                price_text = cells[2].get_text(strip=True)
                import re
                price_match = re.search(r"[\d,.]+", price_text)
                if price_match:
                    row["price"] = float(price_match.group().replace(",", ""))

            rows.append(row)

        if rows:
            break

    # Strategy 2: JSON embedded in script tags
    if not rows:
        import json
        import re
        for script in soup.select("script"):
            script_text = script.get_text()
            json_match = re.search(
                r"(?:timetable|schedule|trips)\s*[:=]\s*(\[[\s\S]*?\])",
                script_text
            )
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    for item in data:
                        if isinstance(item, dict):
                            rows.append({
                                "depart": item.get("departureTime") or item.get("depart", ""),
                                "arrive": item.get("arrivalTime") or item.get("arrive", ""),
                                "price": item.get("price"),
                            })
                except (json.JSONDecodeError, TypeError):
                    pass

    return rows


async def fetch_haramain_timetable():
    """
    Fetch Haramain High Speed Railway timetable.

    Strategy:
    1. Try portlet endpoint (real-time JSON data)
    2. Fallback to HTML parsing
    3. Last resort: static schedule
    """
    trips_stored = 0
    source_method = "STATIC"

    # Strategy 1: Try portlet endpoint for real schedule
    try:
        from .haramain_portlet import fetch_haramain_portlet

        for from_city, to_city in [("MAKKAH", "MADINAH"), ("MADINAH", "MAKKAH")]:
            result = await fetch_haramain_portlet(
                from_city=from_city,
                to_city=to_city,
                departure_date=date.today() + timedelta(days=1),
            )

            if result.success and result.trips:
                source_method = "PORTLET"
                logger.info(
                    f"Portlet: {len(result.trips)} trips for {from_city}→{to_city}"
                )

                if is_db_configured():
                    from .haramain_portlet import store_haramain_trips

                    async with get_session() as session:
                        stored = await store_haramain_trips(result.trips, session)
                        trips_stored += stored

        if source_method == "PORTLET" and trips_stored > 0:
            return {
                "status": "done",
                "source": "portlet",
                "source_url": HARAMAIN_URL,
                "trips_stored": trips_stored,
            }

    except ImportError:
        logger.warning("haramain_portlet not available, trying HTML")
    except Exception as e:
        logger.warning(f"Portlet fetch failed: {e}")

    # Strategy 2: Try HTML parsing
    try:
        r = await get(HARAMAIN_URL, headers={"User-Agent": "umrah-crawler/1.3"})
        soup = BeautifulSoup(r.text, "html.parser")
        html_rows = _parse_html_timetable(soup)

        if html_rows:
            source_method = "HTML"
            logger.info(f"HTML parsed {len(html_rows)} schedule rows")

            if is_db_configured():
                async with get_session() as session:
                    for row in html_rows:
                        for from_city, to_city in [("MAKKAH", "MADINAH"), ("MADINAH", "MAKKAH")]:
                            await session.execute(text("""
                                INSERT INTO transport_schedule
                                (mode, operator, route, duration_min, price_sar, source_url, source_method)
                                VALUES ('TRAIN', 'HARAMAIN', :route, :dur, :price, :url, 'HTML')
                            """), {
                                "route": f"{from_city}_{to_city}",
                                "dur": row.get("duration", 120),
                                "price": row.get("price"),
                                "url": HARAMAIN_URL,
                            })
                            trips_stored += 1
                    await session.commit()

            return {
                "status": "done",
                "source": "html",
                "source_url": HARAMAIN_URL,
                "html_rows": len(html_rows),
                "trips_stored": trips_stored,
            }
    except Exception as e:
        logger.warning(f"HTML fetch/parse failed: {e}")

    # Strategy 3: Static schedule fallback
    logger.warning("Using static Haramain schedule as fallback")

    if is_db_configured():
        async with get_session() as session:
            for sched in STATIC_SCHEDULES:
                for from_city, to_city in [("MAKKAH", "MADINAH"), ("MADINAH", "MAKKAH")]:
                    await session.execute(text("""
                        INSERT INTO transport_schedule
                        (mode, operator, route, duration_min, price_sar, class, source_url, source_method)
                        VALUES ('TRAIN', 'HARAMAIN', :route, :dur, :price, :cls, :url, 'SNAPSHOT')
                    """), {
                        "route": f"{from_city}_{to_city}",
                        "dur": sched["duration"],
                        "price": sched["price"],
                        "cls": sched["class"],
                        "url": HARAMAIN_URL,
                    })
                    trips_stored += 1
            await session.commit()

    return {
        "status": "done",
        "source": "static",
        "source_url": HARAMAIN_URL,
        "trips_stored": trips_stored,
    }
