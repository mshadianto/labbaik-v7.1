"""
LABBAIK AI - User Repository
=============================
Database operations for user management.
Uses PostgreSQL (Supabase) when DATABASE_URL is available, SQLite as fallback.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import streamlit as st

# Import user models
from services.user.user_service import User, UserRole, UserStatus


def get_database_url() -> Optional[str]:
    """Get DATABASE_URL from environment or secrets"""
    # Try environment variable first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # Try Streamlit secrets
    try:
        if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            return st.secrets['DATABASE_URL']
    except Exception:
        pass

    return None


# Check if PostgreSQL should be used
DATABASE_URL = get_database_url()
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        print(f"[DB] Using PostgreSQL: {DATABASE_URL[:50]}...")
    except ImportError:
        print("[DB] psycopg2 not available, falling back to SQLite")
        USE_POSTGRES = False

if not USE_POSTGRES:
    import sqlite3
    # Database path for SQLite fallback
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "labbaik.db")
    print(f"[DB] Using SQLite: {DB_PATH}")


def ensure_db_dir():
    """Ensure database directory exists (SQLite only)"""
    if not USE_POSTGRES:
        db_dir = os.path.dirname(DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)


class UserRepository:
    """Repository for user database operations"""

    def __init__(self):
        self.use_postgres = USE_POSTGRES
        if USE_POSTGRES:
            self.db_url = DATABASE_URL
        else:
            self.db_path = DB_PATH
            ensure_db_dir()
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        if self.use_postgres:
            conn = psycopg2.connect(self.db_url)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def _init_db(self):
        """Initialize database schema"""
        if self.use_postgres:
            # PostgreSQL - tables should already exist from migration
            # Just ensure admin exists
            self._ensure_admin_exists()
            return

        # SQLite initialization
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'free',
                    status TEXT DEFAULT 'pending',

                    -- Profile
                    city TEXT,
                    province TEXT,

                    -- Umrah preferences
                    preferred_departure_city TEXT,
                    budget_range TEXT,
                    travel_style TEXT,

                    -- Tracking
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_count INTEGER DEFAULT 0,

                    -- Analytics/UTM
                    source TEXT,
                    referral_code TEXT,
                    utm_source TEXT,
                    utm_medium TEXT,
                    utm_campaign TEXT
                )
            """)

            # User activities table for tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    activity_type TEXT NOT NULL,
                    activity_data TEXT,
                    page TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # User sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_user ON user_activities(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)")

            conn.commit()

            # Auto-create admin from secrets
            self._ensure_admin_exists()

    def _ensure_admin_exists(self):
        """Auto-create admin user from Streamlit secrets if not exists"""
        import hashlib
        import secrets as sec

        try:
            # Try to get admin credentials from Streamlit secrets
            admin_email = None
            admin_password = None
            admin_name = "Admin"

            if hasattr(st, 'secrets'):
                admin_email = st.secrets.get("ADMIN_EMAIL")
                admin_password = st.secrets.get("ADMIN_PASSWORD")
                admin_name = st.secrets.get("ADMIN_NAME", "Admin")

            # Also check environment variables
            if not admin_email:
                admin_email = os.environ.get("ADMIN_EMAIL")
            if not admin_password:
                admin_password = os.environ.get("ADMIN_PASSWORD")
            if not admin_name or admin_name == "Admin":
                admin_name = os.environ.get("ADMIN_NAME", "Admin")

            if not admin_email or not admin_password:
                return  # No admin credentials configured

            admin_email = admin_email.lower().strip()

            # Check if admin already exists
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if self.use_postgres:
                    cursor.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
                else:
                    cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))

                if cursor.fetchone():
                    return  # Admin already exists

                # Hash password
                salt = sec.token_hex(16)
                hash_obj = hashlib.pbkdf2_hmac(
                    'sha256',
                    admin_password.encode('utf-8'),
                    salt.encode('utf-8'),
                    100000
                )
                password_hash = f"{salt}${hash_obj.hex()}"

                # Create admin user
                now = datetime.now().isoformat()

                if self.use_postgres:
                    cursor.execute("""
                        INSERT INTO users (email, name, password_hash, role, status, created_at, updated_at, login_count, source)
                        VALUES (%s, %s, %s, 'admin', 'active', %s, %s, 0, 'system')
                    """, (admin_email, admin_name, password_hash, now, now))
                else:
                    cursor.execute("""
                        INSERT INTO users (email, name, password_hash, role, status, created_at, updated_at, login_count, source)
                        VALUES (?, ?, ?, 'admin', 'active', ?, ?, 0, 'system')
                    """, (admin_email, admin_name, password_hash, now, now))

                conn.commit()
                print(f"[AUTO] Admin user created: {admin_email}")

        except Exception as e:
            # Silently fail - don't break app startup
            print(f"[WARN] Auto-admin creation failed: {e}")

    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        if self.use_postgres:
            # PostgreSQL returns dict-like rows with RealDictCursor or tuple
            if isinstance(row, dict):
                data = row
            else:
                # Fallback for tuple rows
                data = {
                    "id": row[0], "email": row[1], "name": row[2], "phone": row[3],
                    "password_hash": row[4], "role": row[5], "status": row[6],
                    "city": row[7], "province": row[8], "preferred_departure_city": row[9],
                    "budget_range": row[10], "travel_style": row[11],
                    "created_at": row[12], "updated_at": row[13], "last_login": row[14],
                    "login_count": row[15], "source": row[16], "referral_code": row[17],
                    "utm_source": row[18], "utm_medium": row[19], "utm_campaign": row[20]
                }
        else:
            data = dict(row)

        return User(
            id=data.get("id"),
            email=data.get("email", ""),
            name=data.get("name", ""),
            phone=data.get("phone"),
            password_hash=data.get("password_hash", ""),
            role=UserRole(data.get("role", "free")) if data.get("role") else UserRole.FREE,
            status=UserStatus(data.get("status", "pending")) if data.get("status") else UserStatus.PENDING,
            city=data.get("city"),
            province=data.get("province"),
            preferred_departure_city=data.get("preferred_departure_city"),
            budget_range=data.get("budget_range"),
            travel_style=data.get("travel_style"),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            last_login=self._parse_datetime(data.get("last_login")),
            login_count=data.get("login_count") or 0,
            source=data.get("source"),
            referral_code=data.get("referral_code"),
            utm_source=data.get("utm_source"),
            utm_medium=data.get("utm_medium"),
            utm_campaign=data.get("utm_campaign"),
        )

    def _parse_datetime(self, value) -> Optional[datetime]:
        """Parse datetime from various formats"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except Exception:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return datetime.now()
        return datetime.now()

    def create(self, user: User) -> Optional[User]:
        """Create new user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                if self.use_postgres:
                    cursor.execute("""
                        INSERT INTO users (
                            email, name, phone, password_hash, role, status,
                            city, province, preferred_departure_city, budget_range, travel_style,
                            created_at, updated_at, login_count,
                            source, referral_code, utm_source, utm_medium, utm_campaign
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        user.email, user.name, user.phone, user.password_hash,
                        user.role.value, user.status.value,
                        user.city, user.province, user.preferred_departure_city,
                        user.budget_range, user.travel_style,
                        user.created_at.isoformat(), user.updated_at.isoformat(),
                        user.login_count,
                        user.source, user.referral_code,
                        user.utm_source, user.utm_medium, user.utm_campaign
                    ))
                    result = cursor.fetchone()
                    user.id = result[0] if result else None
                else:
                    cursor.execute("""
                        INSERT INTO users (
                            email, name, phone, password_hash, role, status,
                            city, province, preferred_departure_city, budget_range, travel_style,
                            created_at, updated_at, login_count,
                            source, referral_code, utm_source, utm_medium, utm_campaign
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user.email, user.name, user.phone, user.password_hash,
                        user.role.value, user.status.value,
                        user.city, user.province, user.preferred_departure_city,
                        user.budget_range, user.travel_style,
                        user.created_at.isoformat(), user.updated_at.isoformat(),
                        user.login_count,
                        user.source, user.referral_code,
                        user.utm_source, user.utm_medium, user.utm_campaign
                    ))
                    user.id = cursor.lastrowid

                conn.commit()
                return user
            except Exception as e:
                print(f"[ERROR] Create user failed: {e}")
                return None

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with self._get_connection() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with self._get_connection() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM users WHERE email = %s", (email.lower(),))
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))

            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def update(self, user: User) -> bool:
        """Update user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if self.use_postgres:
                cursor.execute("""
                    UPDATE users SET
                        name = %s, phone = %s, role = %s, status = %s,
                        city = %s, province = %s, preferred_departure_city = %s,
                        budget_range = %s, travel_style = %s,
                        updated_at = %s, last_login = %s, login_count = %s
                    WHERE id = %s
                """, (
                    user.name, user.phone, user.role.value, user.status.value,
                    user.city, user.province, user.preferred_departure_city,
                    user.budget_range, user.travel_style,
                    user.updated_at.isoformat(),
                    user.last_login.isoformat() if user.last_login else None,
                    user.login_count,
                    user.id
                ))
            else:
                cursor.execute("""
                    UPDATE users SET
                        name = ?, phone = ?, role = ?, status = ?,
                        city = ?, province = ?, preferred_departure_city = ?,
                        budget_range = ?, travel_style = ?,
                        updated_at = ?, last_login = ?, login_count = ?
                    WHERE id = ?
                """, (
                    user.name, user.phone, user.role.value, user.status.value,
                    user.city, user.province, user.preferred_departure_city,
                    user.budget_range, user.travel_style,
                    user.updated_at.isoformat(),
                    user.last_login.isoformat() if user.last_login else None,
                    user.login_count,
                    user.id
                ))

            conn.commit()
            return cursor.rowcount > 0

    def delete(self, user_id: int) -> bool:
        """Delete user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if self.use_postgres:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            else:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

            conn.commit()
            return cursor.rowcount > 0

    def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        with self._get_connection() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (limit, offset)
                )
            else:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )

            return [self._row_to_user(row) for row in cursor.fetchall()]

    def search(self, query: str) -> List[User]:
        """Search users by name or email"""
        with self._get_connection() as conn:
            search_term = f"%{query}%"

            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT * FROM users
                    WHERE name ILIKE %s OR email ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (search_term, search_term))
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM users
                    WHERE name LIKE ? OR email LIKE ?
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (search_term, search_term))

            return [self._row_to_user(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}

            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            stats["total_users"] = cursor.fetchone()[0]

            # Users by role
            if self.use_postgres:
                cursor.execute("""
                    SELECT role, COUNT(*) as count
                    FROM users
                    GROUP BY role
                """)
            else:
                cursor.execute("""
                    SELECT role, COUNT(*) as count
                    FROM users
                    GROUP BY role
                """)

            rows = cursor.fetchall()
            stats["by_role"] = {row[0]: row[1] for row in rows}

            # Users by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM users
                GROUP BY status
            """)
            rows = cursor.fetchall()
            stats["by_status"] = {row[0]: row[1] for row in rows}

            # Active users (logged in last 7 days)
            if self.use_postgres:
                cursor.execute("""
                    SELECT COUNT(*) FROM users
                    WHERE last_login >= NOW() - INTERVAL '7 days'
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM users
                    WHERE last_login >= datetime('now', '-7 days')
                """)
            stats["active_7d"] = cursor.fetchone()[0]

            # New users today
            if self.use_postgres:
                cursor.execute("""
                    SELECT COUNT(*) FROM users
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM users
                    WHERE DATE(created_at) = DATE('now')
                """)
            stats["new_today"] = cursor.fetchone()[0]

            return stats

    def log_activity(self, user_id: Optional[int], activity_type: str,
                     activity_data: str = None, page: str = None):
        """Log user activity"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if self.use_postgres:
                cursor.execute("""
                    INSERT INTO user_activities (user_id, activity_type, activity_data, page)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, activity_type, activity_data, page))
            else:
                cursor.execute("""
                    INSERT INTO user_activities (user_id, activity_type, activity_data, page)
                    VALUES (?, ?, ?, ?)
                """, (user_id, activity_type, activity_data, page))

            conn.commit()

    def get_user_activities(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user activities"""
        with self._get_connection() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT * FROM user_activities
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM user_activities
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]


# Singleton instance
_user_repository: Optional[UserRepository] = None


def get_user_repository() -> UserRepository:
    """Get singleton UserRepository instance"""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository
