"""
LABBAIK AI - Referral Service
==============================
Referral tracking and rewards for viral growth.
"""

import sqlite3
import os
import logging
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "labbaik.db")


class ReferralReward(str, Enum):
    """Types of referral rewards"""
    SIGNUP_BONUS = "signup_bonus"        # Reward when referred user signs up
    PREMIUM_BONUS = "premium_bonus"      # Reward when referred user upgrades
    MILESTONE_5 = "milestone_5"          # 5 referrals milestone
    MILESTONE_10 = "milestone_10"        # 10 referrals milestone
    MILESTONE_25 = "milestone_25"        # 25 referrals milestone

    @property
    def reward_days(self) -> int:
        """Premium days rewarded"""
        rewards = {
            "signup_bonus": 3,      # 3 days for each signup
            "premium_bonus": 7,     # 7 days when referred user upgrades
            "milestone_5": 14,      # 2 weeks at 5 referrals
            "milestone_10": 30,     # 1 month at 10 referrals
            "milestone_25": 90,     # 3 months at 25 referrals
        }
        return rewards.get(self.value, 0)


@dataclass
class Referral:
    """Referral record"""
    id: Optional[int] = None
    referrer_id: int = 0              # User who referred
    referred_id: int = 0              # User who was referred
    referral_code: str = ""           # Code used

    # Status
    signup_rewarded: bool = False     # Did referrer get signup bonus?
    premium_rewarded: bool = False    # Did referrer get premium bonus?

    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    rewarded_at: Optional[datetime] = None


def generate_referral_code(user_id: int = None) -> str:
    """Generate unique referral code"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(6))

    if user_id:
        # Include user ID hash for uniqueness
        user_hash = hex(user_id * 7919)[2:5].upper()  # Prime number hash
        return f"LBK{user_hash}{random_part}"

    return f"LBK{random_part}"


class ReferralService:
    """Referral management service"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize referral tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Referral codes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    code TEXT UNIQUE NOT NULL,
                    total_referrals INTEGER DEFAULT 0,
                    total_premium_referrals INTEGER DEFAULT 0,
                    total_reward_days INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Referrals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    referral_code TEXT NOT NULL,

                    signup_rewarded INTEGER DEFAULT 0,
                    premium_rewarded INTEGER DEFAULT 0,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rewarded_at TIMESTAMP,

                    FOREIGN KEY (referrer_id) REFERENCES users(id),
                    FOREIGN KEY (referred_id) REFERENCES users(id)
                )
            """)

            # Reward history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reward_type TEXT NOT NULL,
                    reward_days INTEGER NOT NULL,
                    referral_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ref_code ON referral_codes(code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ref_user ON referral_codes(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)")

            conn.commit()

    def get_or_create_referral_code(self, user_id: int) -> str:
        """Get existing or create new referral code for user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check existing
            cursor.execute("SELECT code FROM referral_codes WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return row["code"]

            # Create new
            code = generate_referral_code(user_id)
            cursor.execute("""
                INSERT INTO referral_codes (user_id, code) VALUES (?, ?)
            """, (user_id, code))
            conn.commit()

            return code

    def get_referrer_by_code(self, code: str) -> Optional[int]:
        """Get user ID who owns this referral code"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM referral_codes WHERE code = ?", (code.upper(),))
            row = cursor.fetchone()
            return row["user_id"] if row else None

    def record_referral(self, referrer_id: int, referred_id: int, code: str) -> bool:
        """Record a new referral when user signs up"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if already recorded
            cursor.execute("""
                SELECT id FROM referrals
                WHERE referred_id = ?
            """, (referred_id,))
            if cursor.fetchone():
                return False  # Already referred

            # Record referral
            cursor.execute("""
                INSERT INTO referrals (referrer_id, referred_id, referral_code)
                VALUES (?, ?, ?)
            """, (referrer_id, referred_id, code.upper()))

            # Update referrer stats
            cursor.execute("""
                UPDATE referral_codes
                SET total_referrals = total_referrals + 1
                WHERE user_id = ?
            """, (referrer_id,))

            conn.commit()
            return True

    def process_signup_reward(self, referred_id: int) -> Optional[int]:
        """
        Process reward when referred user completes signup.
        Returns referrer_id if rewarded.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get referral record
            cursor.execute("""
                SELECT id, referrer_id FROM referrals
                WHERE referred_id = ? AND signup_rewarded = 0
            """, (referred_id,))
            row = cursor.fetchone()

            if not row:
                return None

            referral_id = row["id"]
            referrer_id = row["referrer_id"]
            reward_days = ReferralReward.SIGNUP_BONUS.reward_days

            # Mark as rewarded
            cursor.execute("""
                UPDATE referrals
                SET signup_rewarded = 1, rewarded_at = datetime('now')
                WHERE id = ?
            """, (referral_id,))

            # Add reward record
            cursor.execute("""
                INSERT INTO referral_rewards (user_id, reward_type, reward_days, referral_id)
                VALUES (?, ?, ?, ?)
            """, (referrer_id, ReferralReward.SIGNUP_BONUS.value, reward_days, referral_id))

            # Update total reward days
            cursor.execute("""
                UPDATE referral_codes
                SET total_reward_days = total_reward_days + ?
                WHERE user_id = ?
            """, (reward_days, referrer_id))

            conn.commit()

            # Apply reward to referrer's subscription
            self._apply_reward_days(referrer_id, reward_days)

            # Check milestones
            self._check_milestones(referrer_id)

            return referrer_id

    def process_premium_reward(self, referred_id: int) -> Optional[int]:
        """
        Process reward when referred user upgrades to premium.
        Returns referrer_id if rewarded.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get referral record
            cursor.execute("""
                SELECT id, referrer_id FROM referrals
                WHERE referred_id = ? AND premium_rewarded = 0
            """, (referred_id,))
            row = cursor.fetchone()

            if not row:
                return None

            referral_id = row["id"]
            referrer_id = row["referrer_id"]
            reward_days = ReferralReward.PREMIUM_BONUS.reward_days

            # Mark as rewarded
            cursor.execute("""
                UPDATE referrals SET premium_rewarded = 1 WHERE id = ?
            """, (referral_id,))

            # Update premium referral count
            cursor.execute("""
                UPDATE referral_codes
                SET total_premium_referrals = total_premium_referrals + 1,
                    total_reward_days = total_reward_days + ?
                WHERE user_id = ?
            """, (reward_days, referrer_id))

            # Add reward record
            cursor.execute("""
                INSERT INTO referral_rewards (user_id, reward_type, reward_days, referral_id)
                VALUES (?, ?, ?, ?)
            """, (referrer_id, ReferralReward.PREMIUM_BONUS.value, reward_days, referral_id))

            conn.commit()

            # Apply reward
            self._apply_reward_days(referrer_id, reward_days)

            return referrer_id

    def _apply_reward_days(self, user_id: int, days: int):
        """Apply reward days to user's premium subscription"""
        try:
            from services.subscription import get_subscription_service, SubscriptionPlan
            from services.user import get_user_service, UserRole
            from datetime import timedelta

            sub_service = get_subscription_service()
            user_service = get_user_service()

            # Get current subscription
            current = sub_service.get_user_subscription(user_id)

            if current and current.is_active:
                # Extend existing subscription
                current.expires_at = current.expires_at + timedelta(days=days)
                sub_service.repo.update(current)
            else:
                # Create new subscription with reward days
                success, _, sub = sub_service.create_subscription(
                    user_id=user_id,
                    plan=SubscriptionPlan.MONTHLY,  # Placeholder
                    payment_method="referral_reward"
                )
                if success and sub:
                    sub.expires_at = datetime.now() + timedelta(days=days)
                    sub_service.activate_subscription(sub.id)

            # Ensure user has premium role
            user = user_service.get_user(user_id)
            if user and user.role == UserRole.FREE:
                user.role = UserRole.PREMIUM
                user_service.repo.update(user)

        except Exception as e:
            logger.error(f"Error applying reward: {e}")

    def _check_milestones(self, user_id: int):
        """Check and award milestone bonuses"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT total_referrals FROM referral_codes WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()

            if not row:
                return

            total = row["total_referrals"]

            # Check each milestone
            milestones = [
                (5, ReferralReward.MILESTONE_5),
                (10, ReferralReward.MILESTONE_10),
                (25, ReferralReward.MILESTONE_25),
            ]

            for count, reward in milestones:
                if total >= count:
                    # Check if already awarded
                    cursor.execute("""
                        SELECT id FROM referral_rewards
                        WHERE user_id = ? AND reward_type = ?
                    """, (user_id, reward.value))

                    if not cursor.fetchone():
                        # Award milestone
                        cursor.execute("""
                            INSERT INTO referral_rewards (user_id, reward_type, reward_days)
                            VALUES (?, ?, ?)
                        """, (user_id, reward.value, reward.reward_days))

                        cursor.execute("""
                            UPDATE referral_codes
                            SET total_reward_days = total_reward_days + ?
                            WHERE user_id = ?
                        """, (reward.reward_days, user_id))

                        conn.commit()
                        self._apply_reward_days(user_id, reward.reward_days)

    def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Get referral statistics for a user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM referral_codes WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()

            if not row:
                code = self.get_or_create_referral_code(user_id)
                return {
                    "code": code,
                    "total_referrals": 0,
                    "total_premium_referrals": 0,
                    "total_reward_days": 0,
                    "referrals": []
                }

            # Get referred users
            cursor.execute("""
                SELECT r.*, u.name, u.email
                FROM referrals r
                JOIN users u ON r.referred_id = u.id
                WHERE r.referrer_id = ?
                ORDER BY r.created_at DESC
            """, (user_id,))

            referrals = []
            for ref in cursor.fetchall():
                referrals.append({
                    "name": ref["name"],
                    "email": ref["email"][:3] + "***@***",  # Masked
                    "date": ref["created_at"],
                    "signup_rewarded": bool(ref["signup_rewarded"]),
                    "premium_rewarded": bool(ref["premium_rewarded"]),
                })

            return {
                "code": row["code"],
                "total_referrals": row["total_referrals"],
                "total_premium_referrals": row["total_premium_referrals"],
                "total_reward_days": row["total_reward_days"],
                "referrals": referrals
            }

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global referral statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            cursor.execute("SELECT COUNT(*) FROM referrals")
            stats["total_referrals"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM referrals WHERE premium_rewarded = 1")
            stats["premium_conversions"] = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(total_reward_days) FROM referral_codes")
            result = cursor.fetchone()[0]
            stats["total_reward_days_given"] = result or 0

            # Top referrers
            cursor.execute("""
                SELECT rc.user_id, u.name, rc.total_referrals, rc.total_reward_days
                FROM referral_codes rc
                JOIN users u ON rc.user_id = u.id
                ORDER BY rc.total_referrals DESC
                LIMIT 10
            """)
            stats["top_referrers"] = [
                {
                    "name": row["name"],
                    "referrals": row["total_referrals"],
                    "reward_days": row["total_reward_days"]
                }
                for row in cursor.fetchall()
            ]

            return stats


# Singleton
_referral_service: Optional[ReferralService] = None


def get_referral_service() -> ReferralService:
    """Get singleton ReferralService instance"""
    global _referral_service
    if _referral_service is None:
        _referral_service = ReferralService()
    return _referral_service
