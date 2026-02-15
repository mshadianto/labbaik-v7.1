"""
LABBAIK AI v7.5 - n8n Price Intelligence Adapter
=================================================
Adapter to fetch data from n8n Price Intelligence workflow tables.

Tables:
- prices_hotels: Hotel pricing data
- prices_flights: Flight pricing data
- prices_packages: Umrah package pricing

Workflow runs every 6 hours to populate these tables.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from services.price_aggregation.models import (
    AggregatedOffer,
    SourceType,
    OfferType,
    AvailabilityStatus,
    convert_idr_to_sar
)

logger = logging.getLogger(__name__)


class N8nPriceAdapter:
    """
    Adapter to fetch and convert n8n Price Intelligence data.

    The n8n workflow populates:
    - prices_hotels: 20 hotels in Makkah & Madinah
    - prices_flights: Flight routes from Indonesia
    - prices_packages: Umrah packages from 5 travel agents
    """

    def __init__(self, db_connection=None):
        self._db = db_connection
        self._source_mapping = {
            # source_id -> (source_name, source_type)
            'fcd48791-ddb3-4499-a29f-daa0b3370141': ('booking', SourceType.SCRAPER),
            '793c8f20-5e9d-48b2-80d5-9ab1a780f352': ('aviationstack', SourceType.API),
            'a090eb50-1dcb-4483-a775-947cc43ba35a': ('cheria-travel', SourceType.PARTNER),
            '11876b62-d274-438a-b3e0-e3b7f5543aca': ('alhijaz', SourceType.PARTNER),
            '0c785f27-e17c-4b83-8c0a-1fb045888e1b': ('patuna', SourceType.PARTNER),
            '43919d05-260a-42f2-8fbf-433b929c0d5f': ('maktour', SourceType.PARTNER),
            'f2b49933-4daf-4555-9e98-0d6284dd6f13': ('arminareka', SourceType.PARTNER),
        }

    @property
    def db(self):
        """Lazy-load database connection."""
        if self._db is None:
            try:
                from services.database import get_db_connection
                self._db = get_db_connection()
            except Exception as e:
                logger.error(f"Failed to get database connection: {e}")
        return self._db

    def fetch_hotels(
        self,
        city: str = None,
        min_stars: int = None,
        limit: int = 50
    ) -> Tuple[List[AggregatedOffer], Dict[str, int]]:
        """
        Fetch hotel prices from n8n prices_hotels table.

        Returns:
            Tuple of (offers list, source stats dict)
        """
        offers = []
        stats = {}

        if not self.db:
            logger.warning("No database connection for n8n adapter")
            return offers, stats

        try:
            # Build query
            query = """
                SELECT
                    id, source_id, hotel_name, city, star_rating,
                    distance_to_haram, distance_meters, rating_score,
                    room_type, room_capacity, price_per_night_idr,
                    includes_breakfast, meal_plan, check_in_date,
                    is_available, view_type, source_url, scraped_at
                FROM prices_hotels
                WHERE 1=1
            """
            params = []

            if city:
                query += " AND LOWER(city) = LOWER(%s)"
                params.append(city)

            if min_stars:
                query += " AND star_rating >= %s"
                params.append(min_stars)

            query += " ORDER BY price_per_night_idr ASC LIMIT %s"
            params.append(limit)

            # Execute query
            cursor = self.db.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            for row in rows:
                data = dict(zip(columns, row))
                offer = self._convert_hotel(data)
                if offer:
                    offers.append(offer)
                    source = offer.source_name
                    stats[source] = stats.get(source, 0) + 1

            cursor.close()
            logger.info(f"n8n adapter: fetched {len(offers)} hotels")

        except Exception as e:
            logger.error(f"Failed to fetch n8n hotels: {e}")

        return offers, stats

    def fetch_flights(
        self,
        origin_city: str = None,
        destination_city: str = None,
        limit: int = 50
    ) -> Tuple[List[AggregatedOffer], Dict[str, int]]:
        """
        Fetch flight prices from n8n prices_flights table.

        Returns:
            Tuple of (offers list, source stats dict)
        """
        offers = []
        stats = {}

        if not self.db:
            return offers, stats

        try:
            query = """
                SELECT
                    id, source_id, airline, airline_code, flight_code,
                    origin_city, origin_airport, destination_city, destination_airport,
                    departure_date, departure_time, arrival_time,
                    duration_minutes, is_direct, transit_cities,
                    price_idr, ticket_class, fare_type,
                    is_available, source_url, scraped_at
                FROM prices_flights
                WHERE 1=1
            """
            params = []

            if origin_city:
                query += " AND LOWER(origin_city) = LOWER(%s)"
                params.append(origin_city)

            if destination_city:
                query += " AND LOWER(destination_city) = LOWER(%s)"
                params.append(destination_city)

            query += " ORDER BY price_idr ASC LIMIT %s"
            params.append(limit)

            cursor = self.db.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            for row in rows:
                data = dict(zip(columns, row))
                offer = self._convert_flight(data)
                if offer:
                    offers.append(offer)
                    source = offer.source_name
                    stats[source] = stats.get(source, 0) + 1

            cursor.close()
            logger.info(f"n8n adapter: fetched {len(offers)} flights")

        except Exception as e:
            logger.error(f"Failed to fetch n8n flights: {e}")

        return offers, stats

    def fetch_packages(
        self,
        departure_city: str = None,
        min_stars: int = None,
        limit: int = 50
    ) -> Tuple[List[AggregatedOffer], Dict[str, int]]:
        """
        Fetch package prices from n8n prices_packages table.

        Returns:
            Tuple of (offers list, source stats dict)
        """
        offers = []
        stats = {}

        if not self.db:
            return offers, stats

        try:
            query = """
                SELECT
                    id, source_id, package_name, price_idr,
                    duration_days, departure_city, airline,
                    hotel_makkah, hotel_makkah_stars,
                    hotel_madinah, hotel_madinah_stars,
                    includes, is_available, source_url, scraped_at
                FROM prices_packages
                WHERE 1=1
            """
            params = []

            if departure_city:
                query += " AND LOWER(departure_city) = LOWER(%s)"
                params.append(departure_city)

            if min_stars:
                query += " AND (hotel_makkah_stars >= %s OR hotel_madinah_stars >= %s)"
                params.extend([min_stars, min_stars])

            query += " ORDER BY price_idr ASC LIMIT %s"
            params.append(limit)

            cursor = self.db.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            for row in rows:
                data = dict(zip(columns, row))
                offer = self._convert_package(data)
                if offer:
                    offers.append(offer)
                    source = offer.source_name
                    stats[source] = stats.get(source, 0) + 1

            cursor.close()
            logger.info(f"n8n adapter: fetched {len(offers)} packages")

        except Exception as e:
            logger.error(f"Failed to fetch n8n packages: {e}")

        return offers, stats

    def fetch_all(
        self,
        city: str = None,
        offer_type: str = None,
        min_stars: int = None,
        limit: int = 50
    ) -> Tuple[List[AggregatedOffer], Dict[str, int]]:
        """
        Fetch all price data from n8n tables.

        Args:
            city: Filter by city (for hotels/packages)
            offer_type: Filter by type (hotel/flight/package)
            min_stars: Minimum hotel stars
            limit: Maximum results per type

        Returns:
            Tuple of (all offers, combined stats)
        """
        all_offers = []
        all_stats = {}

        # Fetch hotels
        if offer_type is None or offer_type == "hotel":
            hotels, hotel_stats = self.fetch_hotels(
                city=city,
                min_stars=min_stars,
                limit=limit
            )
            all_offers.extend(hotels)
            for k, v in hotel_stats.items():
                all_stats[k] = all_stats.get(k, 0) + v

        # Fetch flights
        if offer_type is None or offer_type == "flight":
            flights, flight_stats = self.fetch_flights(
                destination_city=city,
                limit=limit
            )
            all_offers.extend(flights)
            for k, v in flight_stats.items():
                all_stats[k] = all_stats.get(k, 0) + v

        # Fetch packages
        if offer_type is None or offer_type == "package":
            packages, pkg_stats = self.fetch_packages(
                min_stars=min_stars,
                limit=limit
            )
            all_offers.extend(packages)
            for k, v in pkg_stats.items():
                all_stats[k] = all_stats.get(k, 0) + v

        logger.info(f"n8n adapter: fetched {len(all_offers)} total offers")
        return all_offers, all_stats

    def _get_source_info(self, source_id: str) -> Tuple[str, SourceType]:
        """Get source name and type from source_id."""
        if source_id in self._source_mapping:
            return self._source_mapping[source_id]
        return ('n8n', SourceType.API)

    def _convert_hotel(self, data: Dict[str, Any]) -> Optional[AggregatedOffer]:
        """Convert hotel row to AggregatedOffer."""
        try:
            source_name, source_type = self._get_source_info(data.get('source_id', ''))
            price_idr = float(data.get('price_per_night_idr') or 0)

            # Build amenities list
            amenities = []
            if data.get('includes_breakfast'):
                amenities.append('breakfast')
            if data.get('view_type'):
                amenities.append(data['view_type'].replace('_', ' '))

            return AggregatedOffer(
                source_type=source_type,
                source_name=source_name,
                source_offer_id=str(data.get('id', '')),
                offer_type=OfferType.HOTEL,
                name=data.get('hotel_name', ''),
                city=data.get('city', ''),
                stars=data.get('star_rating'),
                distance_to_haram_m=data.get('distance_meters'),
                amenities=amenities,
                price_idr=price_idr,
                price_sar=convert_idr_to_sar(price_idr),
                price_per_night_idr=price_idr,
                price_per_night_sar=convert_idr_to_sar(price_idr),
                currency_original="IDR",
                check_in_date=data.get('check_in_date'),
                is_available=data.get('is_available', True),
                availability_status=AvailabilityStatus.AVAILABLE if data.get('is_available') else AvailabilityStatus.SOLD_OUT,
                source_url=data.get('source_url'),
                scraped_at=data.get('scraped_at') or datetime.now(),
                confidence_score=0.9
            )
        except Exception as e:
            logger.warning(f"Failed to convert hotel: {e}")
            return None

    def _convert_flight(self, data: Dict[str, Any]) -> Optional[AggregatedOffer]:
        """Convert flight row to AggregatedOffer."""
        try:
            source_name, source_type = self._get_source_info(data.get('source_id', ''))
            price_idr = float(data.get('price_idr') or 0)

            # Build flight name
            flight_name = f"{data.get('airline', '')} {data.get('flight_code', '')}"
            flight_name += f" ({data.get('origin_airport', '')} → {data.get('destination_airport', '')})"

            # Parse transit cities
            transit = data.get('transit_cities')
            inclusions = []
            if data.get('is_direct'):
                inclusions.append('Direct Flight')
            elif transit:
                if isinstance(transit, str):
                    try:
                        transit = json.loads(transit)
                    except Exception:
                        pass
                if isinstance(transit, list):
                    inclusions.append(f"Transit: {', '.join(transit)}")

            inclusions.append(data.get('ticket_class', 'economy').title())

            return AggregatedOffer(
                source_type=source_type,
                source_name=source_name,
                source_offer_id=str(data.get('id', '')),
                offer_type=OfferType.FLIGHT,
                name=flight_name,
                city=data.get('destination_city', ''),
                departure_city=data.get('origin_city'),
                airline=data.get('airline'),
                inclusions=inclusions,
                price_idr=price_idr,
                price_sar=convert_idr_to_sar(price_idr),
                currency_original="IDR",
                check_in_date=data.get('departure_date'),
                is_available=data.get('is_available', True),
                availability_status=AvailabilityStatus.AVAILABLE if data.get('is_available') else AvailabilityStatus.SOLD_OUT,
                source_url=data.get('source_url'),
                scraped_at=data.get('scraped_at') or datetime.now(),
                confidence_score=0.85
            )
        except Exception as e:
            logger.warning(f"Failed to convert flight: {e}")
            return None

    def _convert_package(self, data: Dict[str, Any]) -> Optional[AggregatedOffer]:
        """Convert package row to AggregatedOffer."""
        try:
            source_name, source_type = self._get_source_info(data.get('source_id', ''))
            price_idr = float(data.get('price_idr') or 0)

            # Parse inclusions
            includes = data.get('includes')
            if isinstance(includes, str):
                try:
                    includes = json.loads(includes)
                except Exception:
                    includes = []

            return AggregatedOffer(
                source_type=source_type,
                source_name=source_name,
                source_offer_id=str(data.get('id', '')),
                offer_type=OfferType.PACKAGE,
                name=data.get('package_name', ''),
                city=data.get('departure_city', 'Jakarta'),
                duration_days=data.get('duration_days'),
                departure_city=data.get('departure_city'),
                airline=data.get('airline'),
                hotel_makkah=data.get('hotel_makkah'),
                hotel_makkah_stars=data.get('hotel_makkah_stars'),
                hotel_madinah=data.get('hotel_madinah'),
                hotel_madinah_stars=data.get('hotel_madinah_stars'),
                inclusions=includes or [],
                price_idr=price_idr,
                price_sar=convert_idr_to_sar(price_idr),
                currency_original="IDR",
                is_available=data.get('is_available', True),
                availability_status=AvailabilityStatus.AVAILABLE if data.get('is_available') else AvailabilityStatus.SOLD_OUT,
                source_url=data.get('source_url'),
                scraped_at=data.get('scraped_at') or datetime.now(),
                confidence_score=0.95
            )
        except Exception as e:
            logger.warning(f"Failed to convert package: {e}")
            return None

    def get_source_stats(self) -> Dict[str, Any]:
        """Get statistics about n8n data sources."""
        stats = {
            "hotels": {"count": 0, "last_update": None},
            "flights": {"count": 0, "last_update": None},
            "packages": {"count": 0, "last_update": None},
        }

        if not self.db:
            return stats

        try:
            cursor = self.db.cursor()

            # Hotels count and last update
            cursor.execute("""
                SELECT COUNT(*), MAX(scraped_at) FROM prices_hotels
            """)
            row = cursor.fetchone()
            if row:
                stats["hotels"]["count"] = row[0] or 0
                stats["hotels"]["last_update"] = row[1].isoformat() if row[1] else None

            # Flights count and last update
            cursor.execute("""
                SELECT COUNT(*), MAX(scraped_at) FROM prices_flights
            """)
            row = cursor.fetchone()
            if row:
                stats["flights"]["count"] = row[0] or 0
                stats["flights"]["last_update"] = row[1].isoformat() if row[1] else None

            # Packages count and last update
            cursor.execute("""
                SELECT COUNT(*), MAX(scraped_at) FROM prices_packages
            """)
            row = cursor.fetchone()
            if row:
                stats["packages"]["count"] = row[0] or 0
                stats["packages"]["last_update"] = row[1].isoformat() if row[1] else None

            cursor.close()

        except Exception as e:
            logger.error(f"Failed to get n8n source stats: {e}")

        return stats


# Singleton instance
_n8n_adapter: Optional[N8nPriceAdapter] = None


def get_n8n_adapter() -> N8nPriceAdapter:
    """Get singleton n8n adapter."""
    global _n8n_adapter
    if _n8n_adapter is None:
        _n8n_adapter = N8nPriceAdapter()
    return _n8n_adapter
