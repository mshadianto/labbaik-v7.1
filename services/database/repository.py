"""
LABBAIK AI v6.0 - Database Connection & Repository
==================================================
Database connection pool and base repository pattern.
"""

from __future__ import annotations
import os
import logging
from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from contextlib import contextmanager
from abc import ABC, abstractmethod
from datetime import datetime
import json

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# CUSTOM EXCEPTIONS (inline to avoid circular import)
# =============================================================================

class DatabaseError(Exception):
    """Database operation error."""
    pass

class ConnectionError(Exception):
    """Database connection error."""
    pass

class RecordNotFoundError(Exception):
    """Record not found error."""
    def __init__(self, entity: str, id: str):
        super().__init__(f"{entity} with id {id} not found")


# =============================================================================
# DATABASE CONNECTION MANAGER
# =============================================================================

class DatabaseConnection:
    """
    Database connection manager with connection pooling.
    Supports PostgreSQL (Neon) with psycopg2.
    """
    
    _instance: Optional["DatabaseConnection"] = None
    
    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._pool = None
        self._connection_string = None
        self._initialized = True
    
    def _get_connection_string(self) -> Optional[str]:
        """Get database URL from environment or settings."""
        # Try environment variable first (Streamlit secrets are exposed as env vars)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        
        # Try Streamlit secrets
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
                return st.secrets['DATABASE_URL']
        except Exception:
            pass
        
        # Try settings (may cause circular import, so wrap in try)
        try:
            from core.config import get_settings
            settings = get_settings()
            if settings and hasattr(settings, 'database') and settings.database.url:
                return settings.database.url
        except Exception:
            pass
        
        return None
    
    def initialize(self, connection_string: Optional[str] = None) -> bool:
        """
        Initialize the database connection pool.
        
        Args:
            connection_string: Database URL (auto-detect if not provided)
        
        Returns:
            True if initialization successful
        """
        # Already initialized
        if self._pool:
            return True
        
        try:
            from psycopg2 import pool
            
            self._connection_string = connection_string or self._get_connection_string()
            
            if not self._connection_string:
                logger.warning("No database URL configured")
                return False
            
            # Get pool size from settings or use default (increased for performance)
            pool_size = 15  # was 5 - increased for better concurrency
            try:
                from core.config import get_settings
                pool_size = get_settings().database.pool_size
            except Exception:
                pass

            self._pool = pool.ThreadedConnectionPool(
                minconn=2,  # was 1 - keep more connections warm
                maxconn=pool_size,
                dsn=self._connection_string
            )
            
            logger.info("Database connection pool initialized")
            return True
            
        except ImportError:
            logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        Auto-initializes pool if not already done.
        
        Yields:
            Database connection
        """
        # AUTO-INITIALIZE if not done yet
        if not self._pool:
            if not self.initialize():
                raise ConnectionError("Database pool not initialized. Check DATABASE_URL in secrets.")
        
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(str(e))
        finally:
            if conn:
                self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """
        Get a cursor from a pooled connection.
        
        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor)
        
        Yields:
            Database cursor
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute(self, query: str, params: tuple = None) -> int:
        """
        Execute a query and return affected rows.
        
        Args:
            query: SQL query
            params: Query parameters
        
        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """
        Fetch single row as dictionary.
        
        Args:
            query: SQL query
            params: Query parameters
        
        Returns:
            Row as dictionary or None
        """
        try:
            from psycopg2.extras import RealDictCursor
            
            with self.get_cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        except ImportError:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Fetch all rows as list of dictionaries.
        
        Args:
            query: SQL query
            params: Query parameters
        
        Returns:
            List of rows as dictionaries
        """
        try:
            from psycopg2.extras import RealDictCursor
            
            with self.get_cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except ImportError:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    
    def close(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("Database connections closed")


def get_db() -> DatabaseConnection:
    """Get the database connection singleton."""
    return DatabaseConnection()


# =============================================================================
# BASE REPOSITORY
# =============================================================================

class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with common CRUD operations.
    """
    
    def __init__(self, db: DatabaseConnection = None):
        self.db = db or get_db()
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the table name."""
        pass
    
    @property
    @abstractmethod
    def model_class(self) -> Type[T]:
        """Return the model class."""
        pass
    
    def _to_model(self, data: Dict) -> T:
        """Convert dictionary to model instance."""
        return self.model_class(**data)
    
    def _to_dict(self, model: T) -> Dict:
        """Convert model to dictionary."""
        if hasattr(model, "model_dump"):
            return model.model_dump()
        elif hasattr(model, "dict"):
            return model.dict()
        return dict(model)
    
    def find_by_id(self, id: str) -> Optional[T]:
        """
        Find entity by ID.
        
        Args:
            id: Entity ID
        
        Returns:
            Model instance or None
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        data = self.db.fetch_one(query, (id,))
        return self._to_model(data) if data else None
    
    # Allowed ORDER BY directions
    _VALID_ORDER_DIRS = frozenset({"ASC", "DESC"})

    # Column name pattern — only allow alphanumeric + underscore
    _VALID_COL_RE = __import__("re").compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> List[T]:
        """
        Find all entities with pagination.

        Args:
            limit: Maximum results
            offset: Results offset
            order_by: Column to order by
            order_dir: Order direction (ASC/DESC)

        Returns:
            List of model instances
        """
        if not self._VALID_COL_RE.match(order_by):
            order_by = "created_at"
        if order_dir.upper() not in self._VALID_ORDER_DIRS:
            order_dir = "DESC"
        query = f"""
            SELECT * FROM {self.table_name}
            ORDER BY {order_by} {order_dir}
            LIMIT %s OFFSET %s
        """
        rows = self.db.fetch_all(query, (limit, offset))
        return [self._to_model(row) for row in rows]

    def find_by(self, **conditions) -> List[T]:
        """
        Find entities by conditions.

        Args:
            **conditions: Column=value conditions

        Returns:
            List of matching model instances
        """
        if not conditions:
            return self.find_all()

        # Validate column names to prevent SQL injection
        for col in conditions:
            if not self._VALID_COL_RE.match(col):
                raise ValueError(f"Invalid column name: {col}")

        where_clauses = [f"{col} = %s" for col in conditions.keys()]
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(where_clauses)}
        """
        rows = self.db.fetch_all(query, tuple(conditions.values()))
        return [self._to_model(row) for row in rows]
    
    def find_one_by(self, **conditions) -> Optional[T]:
        """
        Find single entity by conditions.
        
        Args:
            **conditions: Column=value conditions
        
        Returns:
            Model instance or None
        """
        results = self.find_by(**conditions)
        return results[0] if results else None
    
    def create(self, model: T) -> T:
        """
        Create new entity.
        
        Args:
            model: Model instance to create
        
        Returns:
            Created model with ID
        """
        data = self._to_dict(model)
        
        # Handle JSON fields
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                data[key] = json.dumps(value)
        
        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)
        
        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        result = self.db.fetch_one(query, tuple(data.values()))
        return self._to_model(result)
    
    def update(self, id: str, updates: Dict[str, Any]) -> Optional[T]:
        """
        Update entity by ID.
        
        Args:
            id: Entity ID
            updates: Dictionary of updates
        
        Returns:
            Updated model or None
        """
        if not updates:
            return self.find_by_id(id)
        
        # Add updated_at timestamp
        updates["updated_at"] = datetime.utcnow()
        
        # Handle JSON fields
        for key, value in updates.items():
            if isinstance(value, (dict, list)):
                updates[key] = json.dumps(value)
        
        set_clauses = [f"{col} = %s" for col in updates.keys()]
        
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE id = %s
            RETURNING *
        """
        
        params = tuple(updates.values()) + (id,)
        result = self.db.fetch_one(query, params)
        return self._to_model(result) if result else None
    
    def delete(self, id: str) -> bool:
        """
        Delete entity by ID.
        
        Args:
            id: Entity ID
        
        Returns:
            True if deleted
        """
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        affected = self.db.execute(query, (id,))
        return affected > 0
    
    def count(self, **conditions) -> int:
        """
        Count entities.
        
        Args:
            **conditions: Optional filter conditions
        
        Returns:
            Count of matching entities
        """
        if conditions:
            where_clauses = [f"{col} = %s" for col in conditions.keys()]
            query = f"""
                SELECT COUNT(*) as count FROM {self.table_name}
                WHERE {' AND '.join(where_clauses)}
            """
            result = self.db.fetch_one(query, tuple(conditions.values()))
        else:
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            result = self.db.fetch_one(query)
        
        return result["count"] if result else 0
    
    def exists(self, id: str) -> bool:
        """Check if entity exists."""
        query = f"SELECT 1 FROM {self.table_name} WHERE id = %s LIMIT 1"
        result = self.db.fetch_one(query, (id,))
        return result is not None


# =============================================================================
# USER REPOSITORY
# =============================================================================

class UserRepository(BaseRepository):
    """Repository for User entities."""
    
    @property
    def table_name(self) -> str:
        return "users"
    
    @property
    def model_class(self):
        from data.models import User
        return User
    
    def find_by_email(self, email: str):
        """Find user by email."""
        return self.find_one_by(email=email.lower())
    
    def create_with_password(self, user_data: Dict, hashed_password: str):
        """Create user with hashed password."""
        user_data["password_hash"] = hashed_password
        user_data["email"] = user_data["email"].lower()
        
        from data.models import User
        user = User(**user_data)
        return self.create(user)
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        return self.update(user_id, {"last_login": datetime.utcnow()})
    
    def find_active_users(self, limit: int = 100):
        """Find all active users."""
        return self.find_by(is_active=True)[:limit]
    
    def update_points(self, user_id: str, points_to_add: int):
        """Add points to user."""
        query = f"""
            UPDATE {self.table_name}
            SET points = points + %s, updated_at = %s
            WHERE id = %s
            RETURNING *
        """
        result = self.db.fetch_one(query, (points_to_add, datetime.utcnow(), user_id))
        return self._to_model(result) if result else None


# =============================================================================
# CHAT REPOSITORY
# =============================================================================

class ChatRepository(BaseRepository):
    """Repository for Chat entities."""
    
    @property
    def table_name(self) -> str:
        return "conversations"
    
    @property
    def model_class(self):
        from data.models import ChatConversation
        return ChatConversation
    
    def find_by_user(self, user_id: str, limit: int = 20):
        """Find conversations by user."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE user_id = %s AND is_archived = false
            ORDER BY updated_at DESC
            LIMIT %s
        """
        rows = self.db.fetch_all(query, (user_id, limit))
        return [self._to_model(row) for row in rows]
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """Add message to conversation."""
        # First get existing messages
        conv = self.find_by_id(conversation_id)
        if not conv:
            raise RecordNotFoundError("Conversation", conversation_id)
        
        from data.models import ChatMessage, MessageRole
        message = ChatMessage(role=MessageRole(role), content=content)
        conv.messages.append(message)
        
        return self.update(conversation_id, {
            "messages": [m.model_dump() for m in conv.messages]
        })
    
    def archive(self, conversation_id: str):
        """Archive a conversation."""
        return self.update(conversation_id, {"is_archived": True})


# =============================================================================
# BOOKING REPOSITORY
# =============================================================================

class BookingRepository(BaseRepository):
    """Repository for Booking entities."""
    
    @property
    def table_name(self) -> str:
        return "bookings"
    
    @property
    def model_class(self):
        from data.models import Booking
        return Booking
    
    def find_by_user(self, user_id: str):
        """Find bookings by user."""
        return self.find_by(user_id=user_id)
    
    def find_by_booking_number(self, booking_number: str):
        """Find booking by booking number."""
        return self.find_one_by(booking_number=booking_number)
    
    def update_status(self, booking_id: str, status: str):
        """Update booking status."""
        updates = {"status": status}
        
        if status == "confirmed":
            updates["confirmed_at"] = datetime.utcnow()
        elif status == "cancelled":
            updates["cancelled_at"] = datetime.utcnow()
        
        return self.update(booking_id, updates)
    
    def find_pending_bookings(self):
        """Find all pending bookings."""
        return self.find_by(status="pending")
    
    def get_revenue_stats(self, start_date: datetime = None, end_date: datetime = None):
        """Get revenue statistics."""
        query = """
            SELECT 
                COUNT(*) as total_bookings,
                SUM(total_price) as total_revenue,
                AVG(total_price) as avg_booking_value
            FROM bookings
            WHERE status IN ('confirmed', 'paid', 'completed')
        """
        params = []
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
        
        return self.db.fetch_one(query, tuple(params) if params else None)