"""
LABBAIK AI v7.5 - Price Aggregation Repository
================================================
Database operations for aggregated prices.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import json

from services.price_aggregation.models import (
    AggregatedOffer, PriceHistoryEntry, PartnerPriceFeed,
    ScrapingJob, PriceAlert, DataSourceStats, PriceTrend, TrendDirection
)

logger = logging.getLogger(__name__)


class AggregatedPriceRepository:
    """Repository for aggregated price operations."""

    def __init__(self):
        self._db = None

    @property
    def db(self):
        """Lazy load database connection."""
        if self._db is None:
            try:
                from services.database import get_db_connection
                self._db = get_db_connection()
            except Exception as e:
                logger.error(f"Failed to get DB connection: {e}")
        return self._db

    def _execute(self, query: str, params: tuple = None) -> int:
        """Execute query and return affected rows."""
        if not self.db or not self.db.pool:
            logger.error("Database not available")
            return 0

        try:
            conn = self.db.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    affected = cur.rowcount
                    conn.commit()
                    return affected
            finally:
                self.db.pool.putconn(conn)
        except Exception as e:
            logger.error(f"Execute error: {e}")
            return 0

    def _fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch single row."""
        if not self.db or not self.db.pool:
            return None

        try:
            conn = self.db.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    if row:
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, row))
                    return None
            finally:
                self.db.pool.putconn(conn)
        except Exception as e:
            logger.error(f"Fetch one error: {e}")
            return None

    def _fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows."""
        if not self.db or not self.db.pool:
            return []

        try:
            conn = self.db.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    if rows:
                        columns = [desc[0] for desc in cur.description]
                        return [dict(zip(columns, row)) for row in rows]
                    return []
            finally:
                self.db.pool.putconn(conn)
        except Exception as e:
            logger.error(f"Fetch all error: {e}")
            return []

    # =========================================================================
    # AGGREGATED PRICES CRUD
    # =========================================================================

    def upsert_offer(self, offer: AggregatedOffer) -> Optional[str]:
        """Insert or update an aggregated offer."""
        query = """
            INSERT INTO aggregated_prices (
                offer_hash, source_type, source_name, source_offer_id,
                offer_type, name, name_normalized, city,
                stars, distance_to_haram_m, walking_time_minutes, amenities,
                duration_days, departure_city, airline,
                hotel_makkah, hotel_makkah_stars, hotel_madinah, hotel_madinah_stars,
                inclusions, price_sar, price_idr,
                price_per_night_sar, price_per_night_idr, currency_original,
                check_in_date, check_out_date, valid_from, valid_until,
                is_available, availability_status, rooms_left, quota,
                source_url, raw_data, confidence_score, scraped_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (offer_hash, source_name, check_in_date)
            DO UPDATE SET
                price_sar = EXCLUDED.price_sar,
                price_idr = EXCLUDED.price_idr,
                is_available = EXCLUDED.is_available,
                availability_status = EXCLUDED.availability_status,
                rooms_left = EXCLUDED.rooms_left,
                scraped_at = EXCLUDED.scraped_at,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """

        data = offer.to_dict()
        params = (
            data["offer_hash"], data["source_type"], data["source_name"], data["source_offer_id"],
            data["offer_type"], data["name"], data["name_normalized"], data["city"],
            data["stars"], data["distance_to_haram_m"], data["walking_time_minutes"], data["amenities"],
            data["duration_days"], data["departure_city"], data["airline"],
            data["hotel_makkah"], data["hotel_makkah_stars"], data["hotel_madinah"], data["hotel_madinah_stars"],
            data["inclusions"], data["price_sar"], data["price_idr"],
            data["price_per_night_sar"], data["price_per_night_idr"], data["currency_original"],
            data["check_in_date"], data["check_out_date"], data["valid_from"], data["valid_until"],
            data["is_available"], data["availability_status"], data["rooms_left"], data["quota"],
            data["source_url"], data["raw_data"], data["confidence_score"], data["scraped_at"]
        )

        result = self._fetch_one(query, params)
        return str(result["id"]) if result else None

    def upsert_batch(self, offers: List[AggregatedOffer]) -> int:
        """Upsert multiple offers. Returns count of saved offers."""
        saved = 0
        for offer in offers:
            if self.upsert_offer(offer):
                saved += 1
        return saved

    def get_by_id(self, offer_id: str) -> Optional[AggregatedOffer]:
        """Get offer by ID."""
        query = "SELECT * FROM aggregated_prices WHERE id = %s"
        result = self._fetch_one(query, (offer_id,))
        return AggregatedOffer.from_dict(result) if result else None

    def search(
        self,
        city: str = None,
        offer_type: str = None,
        check_in: date = None,
        min_price: float = None,
        max_price: float = None,
        min_stars: int = None,
        max_stars: int = None,
        sources: List[str] = None,
        is_available: bool = True,
        sort_by: str = "price",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0
    ) -> List[AggregatedOffer]:
        """Search aggregated offers with filters."""
        conditions = ["1=1"]
        params = []

        if city:
            conditions.append("city = %s")
            params.append(city)

        if offer_type:
            conditions.append("offer_type = %s")
            params.append(offer_type)

        if check_in:
            conditions.append("(check_in_date IS NULL OR check_in_date = %s)")
            params.append(check_in)

        if min_price is not None:
            conditions.append("price_idr >= %s")
            params.append(min_price)

        if max_price is not None:
            conditions.append("price_idr <= %s")
            params.append(max_price)

        if min_stars is not None:
            conditions.append("stars >= %s")
            params.append(min_stars)

        if max_stars is not None:
            conditions.append("stars <= %s")
            params.append(max_stars)

        if sources:
            placeholders = ",".join(["%s"] * len(sources))
            conditions.append(f"source_name IN ({placeholders})")
            params.extend(sources)

        if is_available is not None:
            conditions.append("is_available = %s")
            params.append(is_available)

        # Sort mapping
        sort_columns = {
            "price": "price_idr",
            "stars": "stars",
            "distance": "distance_to_haram_m",
            "name": "name",
            "updated": "updated_at"
        }
        sort_col = sort_columns.get(sort_by, "price_idr")
        sort_dir = "DESC" if sort_order.lower() == "desc" else "ASC"

        # Handle nulls in sorting
        null_handling = "NULLS LAST" if sort_dir == "ASC" else "NULLS FIRST"

        query = f"""
            SELECT * FROM aggregated_prices
            WHERE {" AND ".join(conditions)}
            ORDER BY {sort_col} {sort_dir} {null_handling}
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        results = self._fetch_all(query, tuple(params))
        return [AggregatedOffer.from_dict(r) for r in results]

    def get_best_by_source(
        self,
        city: str,
        offer_type: str = "hotel",
        check_in: date = None
    ) -> Dict[str, AggregatedOffer]:
        """Get best (cheapest) offer from each source."""
        query = """
            SELECT DISTINCT ON (source_name) *
            FROM aggregated_prices
            WHERE city = %s AND offer_type = %s AND is_available = true
            ORDER BY source_name, price_idr ASC
        """
        params = [city, offer_type]

        results = self._fetch_all(query, tuple(params))
        return {r["source_name"]: AggregatedOffer.from_dict(r) for r in results}

    def get_sources_summary(self) -> List[Dict]:
        """Get summary of offers by source."""
        query = """
            SELECT
                source_name,
                source_type,
                COUNT(*) as total_offers,
                COUNT(*) FILTER (WHERE is_available) as active_offers,
                ROUND(AVG(price_idr)::numeric) as avg_price_idr,
                MIN(price_idr) as min_price_idr,
                MAX(price_idr) as max_price_idr,
                MAX(updated_at) as last_updated
            FROM aggregated_prices
            GROUP BY source_name, source_type
            ORDER BY total_offers DESC
        """
        return self._fetch_all(query)

    def delete_stale_offers(self, hours: int = 48) -> int:
        """Delete offers not updated in the last N hours."""
        query = """
            DELETE FROM aggregated_prices
            WHERE updated_at < NOW() - INTERVAL '1 hour' * %s
        """
        return self._execute(query, (hours,))

    # =========================================================================
    # PRICE HISTORY
    # =========================================================================

    def record_price_history(self, offer: AggregatedOffer) -> bool:
        """Record price snapshot for history tracking."""
        if not offer.id:
            return False

        # Get previous price
        prev = self._fetch_one("""
            SELECT price_idr FROM price_history
            WHERE aggregated_price_id = %s
            ORDER BY recorded_at DESC LIMIT 1
        """, (offer.id,))

        prev_price = prev.get("price_idr") if prev else None
        change_percent = None

        if prev_price and prev_price > 0:
            change_percent = round((offer.price_idr - prev_price) / prev_price * 100, 2)

        query = """
            INSERT INTO price_history (
                aggregated_price_id, price_sar, price_idr,
                availability_status, rooms_left, source_name,
                price_change_percent, recorded_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._execute(query, (
            offer.id, offer.price_sar, offer.price_idr,
            offer.availability_status.value if hasattr(offer.availability_status, 'value') else offer.availability_status,
            offer.rooms_left, offer.source_name,
            change_percent, datetime.now()
        )) > 0

    def get_price_trend(self, offer_id: str, days: int = 7) -> Optional[PriceTrend]:
        """Get price trend for an offer."""
        query = """
            SELECT price_idr, recorded_at
            FROM price_history
            WHERE aggregated_price_id = %s
              AND recorded_at > NOW() - INTERVAL '1 day' * %s
            ORDER BY recorded_at DESC
            LIMIT 2
        """
        results = self._fetch_all(query, (offer_id, days))

        if len(results) < 2:
            return None

        current = results[0]
        previous = results[1]

        current_price = float(current["price_idr"])
        previous_price = float(previous["price_idr"])

        if previous_price == 0:
            return None

        change_percent = round((current_price - previous_price) / previous_price * 100, 2)
        change_amount = current_price - previous_price

        if change_percent > 1:
            direction = TrendDirection.UP
        elif change_percent < -1:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        return PriceTrend(
            direction=direction,
            change_percent=change_percent,
            change_amount_idr=change_amount,
            previous_price_idr=previous_price,
            recorded_at=previous["recorded_at"]
        )

    def get_price_history(
        self,
        offer_id: str,
        days: int = 30
    ) -> List[PriceHistoryEntry]:
        """Get full price history for an offer."""
        query = """
            SELECT * FROM price_history
            WHERE aggregated_price_id = %s
              AND recorded_at > NOW() - INTERVAL '1 day' * %s
            ORDER BY recorded_at DESC
        """
        results = self._fetch_all(query, (offer_id, days))
        return [PriceHistoryEntry(
            id=str(r["id"]),
            aggregated_price_id=str(r["aggregated_price_id"]),
            price_sar=float(r["price_sar"]),
            price_idr=float(r["price_idr"]),
            availability_status=r.get("availability_status", "available"),
            rooms_left=r.get("rooms_left"),
            source_name=r.get("source_name", ""),
            price_change_percent=float(r["price_change_percent"]) if r.get("price_change_percent") else None,
            recorded_at=r["recorded_at"]
        ) for r in results]

    # =========================================================================
    # PARTNER FEEDS
    # =========================================================================

    def create_partner_feed(self, feed: PartnerPriceFeed) -> Optional[str]:
        """Create a new partner price feed."""
        query = """
            INSERT INTO partner_price_feeds (
                partner_id, feed_name, feed_type, price_idr, price_sar,
                package_name, description, hotel_makkah, hotel_makkah_stars,
                hotel_madinah, hotel_madinah_stars, duration_days,
                departure_city, departure_dates, airline, flight_class,
                room_type, inclusions, exclusions, quota, is_available,
                valid_from, valid_until, commission_rate, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, 'pending'
            ) RETURNING id
        """
        result = self._fetch_one(query, (
            feed.partner_id, feed.feed_name, feed.feed_type,
            feed.price_idr, feed.price_sar,
            feed.package_name, feed.description,
            feed.hotel_makkah, feed.hotel_makkah_stars,
            feed.hotel_madinah, feed.hotel_madinah_stars,
            feed.duration_days, feed.departure_city,
            json.dumps(feed.departure_dates),
            feed.airline, feed.flight_class, feed.room_type,
            json.dumps(feed.inclusions), json.dumps(feed.exclusions),
            feed.quota, feed.is_available,
            feed.valid_from, feed.valid_until, feed.commission_rate
        ))
        return str(result["id"]) if result else None

    def get_approved_feeds(self) -> List[PartnerPriceFeed]:
        """Get all approved partner feeds."""
        query = """
            SELECT * FROM partner_price_feeds
            WHERE status = 'approved'
              AND (valid_until IS NULL OR valid_until >= CURRENT_DATE)
            ORDER BY submitted_at DESC
        """
        results = self._fetch_all(query)
        # Convert to PartnerPriceFeed objects (simplified)
        return results

    def approve_feed(self, feed_id: str, admin_id: str) -> bool:
        """Approve a partner feed."""
        query = """
            UPDATE partner_price_feeds
            SET status = 'approved', approved_at = NOW(), approved_by = %s
            WHERE id = %s AND status = 'pending'
        """
        return self._execute(query, (admin_id, feed_id)) > 0

    def reject_feed(self, feed_id: str, reason: str) -> bool:
        """Reject a partner feed."""
        query = """
            UPDATE partner_price_feeds
            SET status = 'rejected', rejection_reason = %s
            WHERE id = %s AND status = 'pending'
        """
        return self._execute(query, (reason, feed_id)) > 0

    # =========================================================================
    # SCRAPING JOBS
    # =========================================================================

    def create_job(self, job: ScrapingJob) -> Optional[str]:
        """Create a scraping job record."""
        query = """
            INSERT INTO scraping_jobs (
                job_type, job_name, status, priority, config,
                target_sources, scheduled_at, triggered_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self._fetch_one(query, (
            job.job_type, job.job_name, job.status, job.priority,
            json.dumps(job.config) if job.config else None,
            json.dumps(job.target_sources) if job.target_sources else None,
            job.scheduled_at, job.triggered_by
        ))
        return str(result["id"]) if result else None

    def update_job_status(
        self,
        job_id: str,
        status: str,
        items_found: int = None,
        items_saved: int = None,
        errors: List[str] = None
    ) -> bool:
        """Update job status and results."""
        updates = ["status = %s"]
        params = [status]

        if status == "running":
            updates.append("started_at = NOW()")
        elif status in ("completed", "failed"):
            updates.append("completed_at = NOW()")
            updates.append("duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::int")

        if items_found is not None:
            updates.append("items_found = %s")
            params.append(items_found)

        if items_saved is not None:
            updates.append("items_saved = %s")
            params.append(items_saved)

        if errors:
            updates.append("errors = %s")
            params.append(json.dumps(errors))

        params.append(job_id)

        query = f"UPDATE scraping_jobs SET {', '.join(updates)} WHERE id = %s"
        return self._execute(query, tuple(params)) > 0

    def get_last_job(self, job_type: str) -> Optional[Dict]:
        """Get last job of a specific type."""
        query = """
            SELECT * FROM scraping_jobs
            WHERE job_type = %s AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 1
        """
        return self._fetch_one(query, (job_type,))


# Singleton instance
_repository: Optional[AggregatedPriceRepository] = None


def get_price_repository() -> AggregatedPriceRepository:
    """Get singleton repository instance."""
    global _repository
    if _repository is None:
        _repository = AggregatedPriceRepository()
    return _repository


# Alias for backward compatibility
get_aggregated_price_repository = get_price_repository
