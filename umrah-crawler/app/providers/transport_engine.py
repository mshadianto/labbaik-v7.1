"""
LABBAIK AI - Transport Engine V1.3
==================================
JSON-first scraping with HTML fallback and snapshot cache.
Strategy: JSON endpoint → HTML parse → last-known snapshot
"""

import json
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FetchMethod(str, Enum):
    """How data was obtained."""
    JSON = "JSON"
    HTML = "HTML"
    SNAPSHOT = "SNAPSHOT"
    FAILED = "FAILED"


@dataclass
class TransportRow:
    """Single transport schedule entry."""
    operator: str           # 'HARAMAIN', 'SAPTCO'
    mode: str               # 'TRAIN', 'BUS'
    route: str              # 'MAKKAH_MADINAH', 'MADINAH_MAKKAH'
    depart_time: Optional[datetime] = None
    arrive_time: Optional[datetime] = None
    duration_min: Optional[int] = None
    price_sar: Optional[float] = None
    travel_class: str = "ECONOMY"
    availability: str = "AVAILABLE"
    source_url: str = ""
    source_method: FetchMethod = FetchMethod.JSON
    raw_payload: Dict = field(default_factory=dict)


@dataclass
class FetchResult:
    """Result of a fetch attempt."""
    success: bool
    method: FetchMethod
    rows: List[TransportRow] = field(default_factory=list)
    source_url: str = ""
    error: Optional[str] = None
    raw_response: Optional[str] = None


# Default headers for requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8,id;q=0.7",
}


async def try_json_endpoint(
    url: str,
    headers: Optional[Dict] = None,
    timeout: float = 30.0
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Try to fetch JSON from an endpoint.

    Returns:
        (json_data, error_message)
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    merged_headers["Accept"] = "application/json"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=merged_headers)
            resp.raise_for_status()

            # Check content type
            content_type = resp.headers.get("content-type", "")
            if "json" in content_type or resp.text.strip().startswith(("{", "[")):
                data = resp.json()
                logger.info(f"JSON endpoint success: {url}")
                return data, None
            else:
                return None, f"Not JSON: {content_type[:50]}"

    except httpx.HTTPStatusError as e:
        return None, f"HTTP {e.response.status_code}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {str(e)[:50]}"
    except Exception as e:
        return None, f"Request failed: {str(e)[:50]}"


async def try_html_parse(
    url: str,
    parser_func: callable,
    headers: Optional[Dict] = None,
    timeout: float = 30.0
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Try to fetch HTML and parse with custom function.

    Args:
        url: Page URL
        parser_func: Function(soup) -> List[Dict]
        headers: Optional headers
        timeout: Request timeout

    Returns:
        (parsed_data, error_message)
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    merged_headers["Accept"] = "text/html,application/xhtml+xml"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=merged_headers)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            data = parser_func(soup)

            if data:
                logger.info(f"HTML parse success: {url}, {len(data)} rows")
                return data, None
            else:
                return None, "No data extracted from HTML"

    except Exception as e:
        return None, f"HTML parse failed: {str(e)[:100]}"


class TransportEngine:
    """
    Multi-strategy transport data fetcher.

    Strategy priority:
    1. JSON endpoints (most stable)
    2. HTML parsing (fallback)
    3. Cached snapshot (last resort)
    """

    def __init__(self):
        self._snapshots: Dict[str, Dict] = {}  # route -> last good data
        self._last_success: Dict[str, datetime] = {}

    def set_snapshot(self, route: str, data: Dict):
        """Store snapshot for fallback."""
        self._snapshots[route] = {
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_snapshot(self, route: str) -> Optional[Dict]:
        """Get cached snapshot."""
        snap = self._snapshots.get(route)
        if snap:
            return snap["data"]
        return None

    async def fetch(
        self,
        operator: str,
        route: str,
        json_endpoints: List[str],
        html_url: Optional[str] = None,
        html_parser: Optional[callable] = None,
        json_mapper: Optional[callable] = None
    ) -> FetchResult:
        """
        Fetch transport data with multi-strategy fallback.

        Args:
            operator: 'HARAMAIN' or 'SAPTCO'
            route: 'MAKKAH_MADINAH' or 'MADINAH_MAKKAH'
            json_endpoints: List of JSON API URLs to try
            html_url: HTML page URL for fallback
            html_parser: Function(soup) -> List[Dict]
            json_mapper: Function(json_data) -> List[TransportRow]

        Returns:
            FetchResult with rows and metadata
        """
        # Strategy 1: Try JSON endpoints
        for url in json_endpoints:
            data, error = await try_json_endpoint(url)
            if data and json_mapper:
                try:
                    rows = json_mapper(data, operator, route, url)
                    if rows:
                        # Update snapshot on success
                        self.set_snapshot(route, {"rows": [asdict(r) for r in rows]})
                        self._last_success[route] = datetime.utcnow()
                        return FetchResult(
                            success=True,
                            method=FetchMethod.JSON,
                            rows=rows,
                            source_url=url
                        )
                except Exception as e:
                    logger.error(f"JSON mapper error: {e}")
                    continue

        # Strategy 2: Try HTML parsing
        if html_url and html_parser:
            data, error = await try_html_parse(html_url, html_parser)
            if data:
                rows = [
                    TransportRow(
                        operator=operator,
                        route=route,
                        mode="TRAIN" if operator == "HARAMAIN" else "BUS",
                        source_url=html_url,
                        source_method=FetchMethod.HTML,
                        **row
                    ) for row in data
                ]
                if rows:
                    self.set_snapshot(route, {"rows": [asdict(r) for r in rows]})
                    self._last_success[route] = datetime.utcnow()
                    return FetchResult(
                        success=True,
                        method=FetchMethod.HTML,
                        rows=rows,
                        source_url=html_url
                    )

        # Strategy 3: Use cached snapshot
        snapshot = self.get_snapshot(route)
        if snapshot:
            rows_data = snapshot.get("rows", [])
            rows = [TransportRow(**r) for r in rows_data]
            logger.warning(f"Using snapshot for {operator} {route}")
            return FetchResult(
                success=True,
                method=FetchMethod.SNAPSHOT,
                rows=rows,
                source_url="snapshot"
            )

        # All strategies failed
        return FetchResult(
            success=False,
            method=FetchMethod.FAILED,
            error="All fetch strategies failed"
        )


# Singleton engine
_transport_engine: Optional[TransportEngine] = None


def get_transport_engine() -> TransportEngine:
    """Get or create transport engine singleton."""
    global _transport_engine
    if _transport_engine is None:
        _transport_engine = TransportEngine()
    return _transport_engine


# Database storage helper
async def store_transport_rows(
    rows: List[TransportRow],
    db_session=None
) -> int:
    """
    Store transport rows to database.

    Uses the transport_schedule table schema (schema_v1_3.sql):
    - operator, mode, route, depart_time_local, arrive_time_local,
      duration_min, price_sar, class, availability, source_url,
      source_method, payload

    Args:
        rows: List of TransportRow objects
        db_session: Optional SQLAlchemy async session

    Returns:
        Number of rows stored
    """
    if not rows:
        return 0

    # If no db_session provided, just log
    if db_session is None:
        logger.info(f"Would store {len(rows)} transport rows (no db session)")
        return len(rows)

    from sqlalchemy import text
    import json as _json

    stored = 0
    for row in rows:
        try:
            await db_session.execute(text("""
                INSERT INTO transport_schedule
                (operator, mode, route, depart_time_local, arrive_time_local,
                 duration_min, price_sar, class, availability,
                 source_url, source_method, payload)
                VALUES (:operator, :mode, :route, :depart, :arrive,
                        :duration, :price, :cls, :avail,
                        :url, :method, :payload::jsonb)
            """), {
                "operator": row.operator,
                "mode": row.mode,
                "route": row.route,
                "depart": row.depart_time,
                "arrive": row.arrive_time,
                "duration": row.duration_min,
                "price": row.price_sar,
                "cls": row.travel_class,
                "avail": row.availability,
                "url": row.source_url,
                "method": row.source_method.value if row.source_method else None,
                "payload": _json.dumps(row.raw_payload, default=str) if row.raw_payload else None,
            })
            stored += 1
        except Exception as e:
            logger.error(f"Failed to store transport row ({row.operator} {row.route}): {e}")

    if stored > 0:
        try:
            await db_session.commit()
        except Exception as e:
            logger.error(f"Failed to commit transport rows: {e}")
            await db_session.rollback()
            return 0

    logger.info(f"Stored {stored}/{len(rows)} transport rows to database")
    return stored


def format_schedule_for_display(rows: List[TransportRow]) -> List[Dict]:
    """
    Format transport rows for UI display.

    Returns:
        List of display-friendly dicts
    """
    result = []
    for row in rows:
        depart_str = ""
        arrive_str = ""

        if row.depart_time:
            depart_str = row.depart_time.strftime("%H:%M")
        if row.arrive_time:
            arrive_str = row.arrive_time.strftime("%H:%M")

        result.append({
            "operator": row.operator,
            "mode": row.mode,
            "route": row.route,
            "departure": depart_str,
            "arrival": arrive_str,
            "duration": f"{row.duration_min} min" if row.duration_min else "~",
            "price": f"SAR {row.price_sar:.0f}" if row.price_sar else "~",
            "class": row.travel_class,
            "availability": row.availability,
            "source": row.source_method.value,
        })

    return result
