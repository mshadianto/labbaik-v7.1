"""
LABBAIK AI - Subscription Repository
======================================
Database operations for subscription management.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

from services.subscription.subscription_service import (
    Subscription, SubscriptionPlan, SubscriptionStatus
)

# Database path - same as user db
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "labbaik.db")


class SubscriptionRepository:
    """Repository for subscription database operations"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize subscription tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Subscriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',

                    started_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    cancelled_at TIMESTAMP,

                    payment_method TEXT,
                    payment_id TEXT,
                    amount_paid INTEGER DEFAULT 0,

                    promo_code TEXT,
                    discount_percent INTEGER DEFAULT 0,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Payment transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER,
                    user_id INTEGER NOT NULL,

                    transaction_id TEXT UNIQUE,
                    payment_method TEXT,
                    amount INTEGER NOT NULL,
                    currency TEXT DEFAULT 'IDR',

                    status TEXT DEFAULT 'pending',
                    payment_data TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Promo codes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS promo_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    discount_percent INTEGER NOT NULL,
                    max_uses INTEGER DEFAULT 0,
                    current_uses INTEGER DEFAULT 0,
                    valid_from TIMESTAMP,
                    valid_until TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_user ON subscriptions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_status ON subscriptions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_expires ON subscriptions(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_user ON payment_transactions(user_id)")

            conn.commit()

    def _row_to_subscription(self, row: sqlite3.Row) -> Subscription:
        """Convert database row to Subscription object"""
        return Subscription(
            id=row["id"],
            user_id=row["user_id"],
            plan=SubscriptionPlan(row["plan"]) if row["plan"] else SubscriptionPlan.FREE,
            status=SubscriptionStatus(row["status"]) if row["status"] else SubscriptionStatus.PENDING,
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            cancelled_at=datetime.fromisoformat(row["cancelled_at"]) if row["cancelled_at"] else None,
            payment_method=row["payment_method"],
            payment_id=row["payment_id"],
            amount_paid=row["amount_paid"] or 0,
            promo_code=row["promo_code"],
            discount_percent=row["discount_percent"] or 0,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
        )

    def create(self, sub: Subscription) -> Optional[Subscription]:
        """Create new subscription"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO subscriptions (
                        user_id, plan, status,
                        started_at, expires_at,
                        payment_method, payment_id, amount_paid,
                        promo_code, discount_percent,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sub.user_id, sub.plan.value, sub.status.value,
                    sub.started_at.isoformat() if sub.started_at else None,
                    sub.expires_at.isoformat() if sub.expires_at else None,
                    sub.payment_method, sub.payment_id, sub.amount_paid,
                    sub.promo_code, sub.discount_percent,
                    sub.created_at.isoformat(), sub.updated_at.isoformat()
                ))
                conn.commit()
                sub.id = cursor.lastrowid
                return sub
            except Exception as e:
                logger.error(f"Error creating subscription: {e}")
                return None

    def get_by_id(self, sub_id: int) -> Optional[Subscription]:
        """Get subscription by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,))
            row = cursor.fetchone()
            return self._row_to_subscription(row) if row else None

    def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get active subscription for user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions
                WHERE user_id = ?
                AND status = 'active'
                AND (expires_at IS NULL OR expires_at > datetime('now'))
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            return self._row_to_subscription(row) if row else None

    def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        """Get all subscriptions for user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            return [self._row_to_subscription(row) for row in cursor.fetchall()]

    def update(self, sub: Subscription) -> bool:
        """Update subscription"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE subscriptions SET
                    status = ?,
                    cancelled_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                sub.status.value,
                sub.cancelled_at.isoformat() if sub.cancelled_at else None,
                sub.updated_at.isoformat(),
                sub.id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def get_expired_subscriptions(self) -> List[Subscription]:
        """Get subscriptions that have expired but not yet marked"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions
                WHERE status = 'active'
                AND expires_at < datetime('now')
            """)
            return [self._row_to_subscription(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Get subscription statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total subscriptions
            cursor.execute("SELECT COUNT(*) FROM subscriptions")
            stats["total_subscriptions"] = cursor.fetchone()[0]

            # Active subscriptions
            cursor.execute("""
                SELECT COUNT(*) FROM subscriptions
                WHERE status = 'active'
                AND (expires_at IS NULL OR expires_at > datetime('now'))
            """)
            stats["active_subscriptions"] = cursor.fetchone()[0]

            # By plan
            cursor.execute("""
                SELECT plan, COUNT(*) as count
                FROM subscriptions
                WHERE status = 'active'
                GROUP BY plan
            """)
            stats["by_plan"] = {row["plan"]: row["count"] for row in cursor.fetchall()}

            # Total revenue
            cursor.execute("""
                SELECT COALESCE(SUM(amount_paid), 0)
                FROM subscriptions
                WHERE status = 'active'
            """)
            stats["total_revenue"] = cursor.fetchone()[0]

            # Monthly revenue (last 30 days)
            cursor.execute("""
                SELECT COALESCE(SUM(amount_paid), 0)
                FROM subscriptions
                WHERE status = 'active'
                AND created_at >= datetime('now', '-30 days')
            """)
            stats["monthly_revenue"] = cursor.fetchone()[0]

            # Conversion rate
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            if total_users > 0:
                stats["conversion_rate"] = round(stats["active_subscriptions"] / total_users * 100, 2)
            else:
                stats["conversion_rate"] = 0

            return stats


# Singleton
_subscription_repository: Optional[SubscriptionRepository] = None


def get_subscription_repository() -> SubscriptionRepository:
    """Get singleton SubscriptionRepository instance"""
    global _subscription_repository
    if _subscription_repository is None:
        _subscription_repository = SubscriptionRepository()
    return _subscription_repository
