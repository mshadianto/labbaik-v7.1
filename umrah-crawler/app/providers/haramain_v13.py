"""
LABBAIK AI - Haramain Railway V1.3 Provider
============================================
JSON-first scraping for Haramain High-Speed Railway.
Fallback: HTML parse → snapshot.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup

from .transport_engine import (
    TransportEngine, TransportRow, FetchResult, FetchMethod,
    get_transport_engine
)

logger = logging.getLogger(__name__)

# =============================================================================
# ENDPOINT DISCOVERY
# =============================================================================

# Haramain official site (may require session/token)
HARAMAIN_WEB_URL = "https://sar.hhr.sa"
HARAMAIN_TIMETABLE_URL = "https://sar.hhr.sa/#/timetable"

# JSON API endpoints — populated when actual endpoints are discovered
HARAMAIN_JSON_ENDPOINTS: list[str] = []

# Route codes
ROUTES = {
    "MAKKAH_MADINAH": {"from": "MAK", "to": "MED"},
    "MADINAH_MAKKAH": {"from": "MED", "to": "MAK"},
}

# Known schedule (static fallback when APIs fail)
# Based on typical Haramain timetable
KNOWN_SCHEDULE = {
    "MAKKAH_MADINAH": [
        {"depart": "06:30", "arrive": "08:30", "class": "ECONOMY", "price": 75},
        {"depart": "08:00", "arrive": "10:00", "class": "ECONOMY", "price": 75},
        {"depart": "10:00", "arrive": "12:00", "class": "ECONOMY", "price": 75},
        {"depart": "12:00", "arrive": "14:00", "class": "ECONOMY", "price": 75},
        {"depart": "14:00", "arrive": "16:00", "class": "ECONOMY", "price": 75},
        {"depart": "16:00", "arrive": "18:00", "class": "ECONOMY", "price": 75},
        {"depart": "18:00", "arrive": "20:00", "class": "ECONOMY", "price": 75},
        {"depart": "20:00", "arrive": "22:00", "class": "ECONOMY", "price": 75},
        {"depart": "06:30", "arrive": "08:30", "class": "BUSINESS", "price": 150},
        {"depart": "12:00", "arrive": "14:00", "class": "BUSINESS", "price": 150},
        {"depart": "18:00", "arrive": "20:00", "class": "BUSINESS", "price": 150},
    ],
    "MADINAH_MAKKAH": [
        {"depart": "06:00", "arrive": "08:00", "class": "ECONOMY", "price": 75},
        {"depart": "08:00", "arrive": "10:00", "class": "ECONOMY", "price": 75},
        {"depart": "10:00", "arrive": "12:00", "class": "ECONOMY", "price": 75},
        {"depart": "12:00", "arrive": "14:00", "class": "ECONOMY", "price": 75},
        {"depart": "14:00", "arrive": "16:00", "class": "ECONOMY", "price": 75},
        {"depart": "16:00", "arrive": "18:00", "class": "ECONOMY", "price": 75},
        {"depart": "18:00", "arrive": "20:00", "class": "ECONOMY", "price": 75},
        {"depart": "20:30", "arrive": "22:30", "class": "ECONOMY", "price": 75},
        {"depart": "08:00", "arrive": "10:00", "class": "BUSINESS", "price": 150},
        {"depart": "14:00", "arrive": "16:00", "class": "BUSINESS", "price": 150},
        {"depart": "20:30", "arrive": "22:30", "class": "BUSINESS", "price": 150},
    ]
}


# =============================================================================
# JSON MAPPER
# =============================================================================

def map_haramain_json(
    data: Any,
    operator: str,
    route: str,
    source_url: str
) -> List[TransportRow]:
    """
    Map Haramain JSON response to TransportRow objects.

    Adjust this based on actual API response structure.
    """
    rows = []

    # Handle various response formats
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Common patterns: data.schedules, data.trips, data.results
        items = (
            data.get("schedules") or
            data.get("trips") or
            data.get("results") or
            data.get("data") or
            []
        )
        if isinstance(items, dict):
            items = [items]

    for item in items:
        try:
            # Map fields - adjust based on actual response
            depart_str = item.get("departureTime") or item.get("depart") or item.get("departure")
            arrive_str = item.get("arrivalTime") or item.get("arrive") or item.get("arrival")

            depart_time = None
            arrive_time = None

            if depart_str:
                depart_time = _parse_time(depart_str)
            if arrive_str:
                arrive_time = _parse_time(arrive_str)

            duration = item.get("duration") or item.get("durationMin")
            if duration and isinstance(duration, str):
                # Parse "2h 00m" format
                duration = _parse_duration(duration)

            price = item.get("price") or item.get("fare") or item.get("priceSar")
            if price:
                price = float(str(price).replace(",", "").replace("SAR", "").strip())

            travel_class = (
                item.get("class") or
                item.get("seatClass") or
                item.get("travelClass") or
                "ECONOMY"
            ).upper()

            availability = item.get("availability") or "AVAILABLE"
            if item.get("soldOut") or item.get("isSoldOut"):
                availability = "SOLD_OUT"

            rows.append(TransportRow(
                operator=operator,
                mode="TRAIN",
                route=route,
                depart_time=depart_time,
                arrive_time=arrive_time,
                duration_min=duration,
                price_sar=price,
                travel_class=travel_class,
                availability=availability,
                source_url=source_url,
                source_method=FetchMethod.JSON,
                raw_payload=item
            ))

        except Exception as e:
            logger.warning(f"Failed to map item: {e}")
            continue

    return rows


def _parse_time(time_str: str) -> Optional[datetime]:
    """Parse time string to datetime (today's date)."""
    if not time_str:
        return None

    today = datetime.now().date()

    # Try common formats
    for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"]:
        try:
            t = datetime.strptime(time_str.strip(), fmt)
            return datetime.combine(today, t.time())
        except ValueError:
            continue

    # Try ISO format
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except ValueError:
        pass

    return None


def _parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string to minutes."""
    if not duration_str:
        return None

    total_min = 0

    # Match "2h", "2 hours", "2hr"
    h_match = re.search(r"(\d+)\s*(h|hr|hour)", duration_str, re.I)
    if h_match:
        total_min += int(h_match.group(1)) * 60

    # Match "30m", "30 min", "30 minutes"
    m_match = re.search(r"(\d+)\s*(m|min|minute)", duration_str, re.I)
    if m_match:
        total_min += int(m_match.group(1))

    return total_min if total_min > 0 else None


# =============================================================================
# HTML PARSER
# =============================================================================

def parse_haramain_html(soup: BeautifulSoup) -> List[Dict]:
    """
    Parse Haramain HTML timetable page.

    Returns list of schedule dicts.
    """
    rows = []

    # Try to find schedule table/list
    # Adjust selectors based on actual page structure
    schedule_items = soup.select(".schedule-item, .trip-row, .timetable-row, tr.schedule")

    for item in schedule_items:
        try:
            depart = item.select_one(".departure, .depart-time, td:nth-child(1)")
            arrive = item.select_one(".arrival, .arrive-time, td:nth-child(2)")
            price = item.select_one(".price, .fare, td:nth-child(3)")
            travel_class = item.select_one(".class, .seat-class, td:nth-child(4)")

            row = {}

            if depart:
                row["depart_time"] = _parse_time(depart.get_text(strip=True))
            if arrive:
                row["arrive_time"] = _parse_time(arrive.get_text(strip=True))
            if price:
                price_text = price.get_text(strip=True)
                price_num = re.search(r"[\d,.]+", price_text)
                if price_num:
                    row["price_sar"] = float(price_num.group().replace(",", ""))
            if travel_class:
                row["travel_class"] = travel_class.get_text(strip=True).upper()

            if row:
                rows.append(row)

        except Exception as e:
            logger.debug(f"Failed to parse HTML row: {e}")
            continue

    return rows


# =============================================================================
# MAIN FETCH FUNCTION
# =============================================================================

async def fetch_haramain_schedule(
    route: str = "MAKKAH_MADINAH",
    travel_date: Optional[datetime] = None
) -> FetchResult:
    """
    Fetch Haramain train schedule.

    Strategy:
    1. Try JSON endpoints
    2. Fallback to HTML parsing
    3. Use cached snapshot / known schedule

    Args:
        route: 'MAKKAH_MADINAH' or 'MADINAH_MAKKAH'
        travel_date: Optional specific date

    Returns:
        FetchResult with schedule rows
    """
    engine = get_transport_engine()

    # Build date-specific endpoints if needed
    json_urls = list(HARAMAIN_JSON_ENDPOINTS)
    if travel_date:
        date_str = travel_date.strftime("%Y-%m-%d")
        route_codes = ROUTES.get(route, {})
        # Add date-parameterized URLs if base endpoints exist
        # json_urls.append(f"https://api.example.com/schedule?date={date_str}")

    result = await engine.fetch(
        operator="HARAMAIN",
        route=route,
        json_endpoints=json_urls,
        html_url=HARAMAIN_TIMETABLE_URL,
        html_parser=parse_haramain_html,
        json_mapper=map_haramain_json
    )

    # If all strategies failed, use known schedule
    if not result.success or not result.rows:
        logger.warning(f"Using known schedule for HARAMAIN {route}")
        rows = _get_known_schedule_rows(route, travel_date)
        return FetchResult(
            success=True,
            method=FetchMethod.SNAPSHOT,
            rows=rows,
            source_url="known_schedule"
        )

    return result


def _get_known_schedule_rows(
    route: str,
    travel_date: Optional[datetime] = None
) -> List[TransportRow]:
    """Convert known schedule to TransportRow objects."""
    schedule = KNOWN_SCHEDULE.get(route, [])
    base_date = (travel_date or datetime.now()).date()

    rows = []
    for item in schedule:
        depart_time = None
        arrive_time = None

        if item.get("depart"):
            h, m = map(int, item["depart"].split(":"))
            depart_time = datetime.combine(base_date, datetime.min.time().replace(hour=h, minute=m))

        if item.get("arrive"):
            h, m = map(int, item["arrive"].split(":"))
            arrive_time = datetime.combine(base_date, datetime.min.time().replace(hour=h, minute=m))
            # Handle overnight
            if arrive_time < depart_time:
                arrive_time += timedelta(days=1)

        duration_min = None
        if depart_time and arrive_time:
            duration_min = int((arrive_time - depart_time).total_seconds() / 60)

        rows.append(TransportRow(
            operator="HARAMAIN",
            mode="TRAIN",
            route=route,
            depart_time=depart_time,
            arrive_time=arrive_time,
            duration_min=duration_min,
            price_sar=float(item.get("price", 75)),
            travel_class=item.get("class", "ECONOMY"),
            availability="AVAILABLE",
            source_url="known_schedule",
            source_method=FetchMethod.SNAPSHOT
        ))

    return rows


async def fetch_all_routes() -> Dict[str, FetchResult]:
    """Fetch schedule for all routes."""
    results = {}
    for route in ROUTES.keys():
        results[route] = await fetch_haramain_schedule(route)
    return results
