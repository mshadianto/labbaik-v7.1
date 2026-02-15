"""
LABBAIK AI v6.0 - Data Services Layer
=====================================
Centralized data management for all features.
Supports both mock data and real database connections.
"""

import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import random
import string
import hashlib
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

class DatabaseMode(str, Enum):
    MOCK = "mock"
    POSTGRES = "postgres"
    SQLITE = "sqlite"


class Database:
    """
    Database connection manager.
    Supports mock mode for demo and real DB for production.
    """
    
    _instance = None
    _connection = None
    _mode = DatabaseMode.MOCK
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._mode = self._detect_mode()
    
    def _detect_mode(self) -> DatabaseMode:
        """Detect database mode from environment."""
        db_url = os.environ.get("DATABASE_URL", "")
        
        if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
            return DatabaseMode.POSTGRES
        elif db_url.startswith("sqlite://"):
            return DatabaseMode.SQLITE
        else:
            return DatabaseMode.MOCK
    
    def connect(self) -> bool:
        """Establish database connection."""
        if self._mode == DatabaseMode.MOCK:
            logger.info("Using MOCK database mode")
            return True
        
        try:
            if self._mode == DatabaseMode.POSTGRES:
                import psycopg2
                from psycopg2 import pool
                
                db_url = os.environ.get("DATABASE_URL")
                self._connection = psycopg2.pool.SimpleConnectionPool(1, 10, db_url)
                logger.info("Connected to PostgreSQL")
                return True
                
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            logger.info("Falling back to MOCK mode")
            self._mode = DatabaseMode.MOCK
            return True
        
        return False
    
    def get_connection(self):
        """Get database connection."""
        if self._mode == DatabaseMode.MOCK:
            return MockConnection()
        return self._connection.getconn() if self._connection else None
    
    def release_connection(self, conn):
        """Release connection back to pool."""
        if self._mode != DatabaseMode.MOCK and self._connection:
            self._connection.putconn(conn)
    
    @property
    def is_mock(self) -> bool:
        return self._mode == DatabaseMode.MOCK
    
    @property
    def mode(self) -> DatabaseMode:
        return self._mode


class MockConnection:
    """Mock database connection for demo mode."""
    
    def cursor(self):
        return MockCursor()
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
    
    def close(self):
        pass


class MockCursor:
    """Mock database cursor."""
    
    def __init__(self):
        self._results = []
    
    def execute(self, query: str, params: tuple = None):
        pass
    
    def fetchone(self):
        return None
    
    def fetchall(self):
        return []
    
    def close(self):
        pass


# =============================================================================
# IN-MEMORY DATA STORE (for mock mode)
# =============================================================================

class DataStore:
    """
    In-memory data store for mock mode.
    Simulates database operations.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize data store with mock data."""
        self.users: Dict[str, Dict] = {}
        self.trips: Dict[str, Dict] = {}
        self.bookings: Dict[str, Dict] = {}
        self.chats: Dict[str, List[Dict]] = {}
        self.notifications: Dict[str, List[Dict]] = {}
        self.simulations: Dict[str, List[Dict]] = {}
        
        # Generate initial mock data
        self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate initial mock data."""
        
        # Sample users
        sample_users = [
            {"id": "user_1", "name": "Ahmad Fauzi", "email": "ahmad@email.com", "city": "Jakarta"},
            {"id": "user_2", "name": "Siti Nurhaliza", "email": "siti@email.com", "city": "Surabaya"},
            {"id": "user_3", "name": "Budi Santoso", "email": "budi@email.com", "city": "Bandung"},
            {"id": "user_4", "name": "Dewi Kartika", "email": "dewi@email.com", "city": "Medan"},
            {"id": "user_5", "name": "Muhammad Rizki", "email": "rizki@email.com", "city": "Makassar"},
        ]
        
        for user in sample_users:
            self.users[user["id"]] = {
                **user,
                "created_at": datetime.now().isoformat(),
                "points": random.randint(0, 1000),
                "is_verified": random.choice([True, False]),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "trips_completed": random.randint(0, 5),
            }
        
        # Sample trips
        cities = ["Jakarta", "Surabaya", "Bandung", "Medan", "Makassar"]
        titles = [
            "Umrah Ramadan Penuh Berkah 🌙",
            "Umrah Hemat Backpacker 🎒",
            "Umrah Keluarga Bahagia 👨‍👩‍👧‍👦",
            "Umrah VIP Executive 👑",
            "Umrah Muda Semangat 🔥",
        ]
        
        for i in range(20):
            trip_id = f"trip_{i+1}"
            dep_date = date.today() + timedelta(days=random.randint(30, 180))
            
            self.trips[trip_id] = {
                "id": trip_id,
                "title": random.choice(titles),
                "leader_id": f"user_{random.randint(1, 5)}",
                "departure_city": random.choice(cities),
                "departure_date": dep_date.isoformat(),
                "return_date": (dep_date + timedelta(days=random.choice([9, 10, 12, 14]))).isoformat(),
                "min_members": random.choice([5, 10]),
                "max_members": random.choice([15, 20, 30, 45]),
                "current_members": random.randint(1, 15),
                "trip_type": random.choice(["public", "private", "family", "youth"]),
                "travel_style": random.choice(["ibadah", "balanced", "ziarah", "shopping"]),
                "budget_range": random.choice(["ekonomis", "standar", "premium", "vip"]),
                "hotel_star": random.choice([3, 4, 5]),
                "price_estimate": random.choice([20000000, 25000000, 30000000, 35000000, 45000000]),
                "status": "open",
                "created_at": datetime.now().isoformat(),
                "likes": random.randint(0, 500),
                "views": random.randint(50, 5000),
                "tags": random.sample(["ramadan", "hemat", "keluarga", "muda", "premium"], k=3),
            }
    
    def reset(self):
        """Reset all data."""
        self._initialize()


# Global instances
db = Database()
store = DataStore()


# =============================================================================
# USER SERVICE
# =============================================================================

class UserService:
    """Service for user-related operations."""
    
    @staticmethod
    def get_user(user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        if db.is_mock:
            return store.users.get(user_id)
        # Real DB query would go here
        return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email."""
        if db.is_mock:
            for user in store.users.values():
                if user.get("email") == email:
                    return user
        return None
    
    @staticmethod
    def create_user(name: str, email: str, password: str, city: str = "") -> Optional[Dict]:
        """Create new user."""
        user_id = f"user_{len(store.users) + 1}"
        
        user = {
            "id": user_id,
            "name": name,
            "email": email,
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
            "city": city,
            "created_at": datetime.now().isoformat(),
            "points": 0,
            "is_verified": False,
            "rating": 0.0,
            "trips_completed": 0,
            "badges": [],
        }
        
        if db.is_mock:
            store.users[user_id] = user
            return user
        
        # Real DB insert would go here
        return None
    
    @staticmethod
    def update_user(user_id: str, data: Dict) -> bool:
        """Update user data."""
        if db.is_mock:
            if user_id in store.users:
                store.users[user_id].update(data)
                return True
        return False
    
    @staticmethod
    def authenticate(email: str, password: str) -> Optional[Dict]:
        """Authenticate user."""
        user = UserService.get_user_by_email(email)
        if user:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user.get("password_hash") == password_hash:
                return user
            # For demo, allow any password
            if db.is_mock:
                return user
        return None
    
    @staticmethod
    def add_points(user_id: str, points: int, reason: str = "") -> int:
        """Add points to user."""
        if db.is_mock:
            if user_id in store.users:
                store.users[user_id]["points"] += points
                return store.users[user_id]["points"]
        return 0
    
    @staticmethod
    def get_leaderboard(limit: int = 10) -> List[Dict]:
        """Get top users by points."""
        if db.is_mock:
            users = list(store.users.values())
            users.sort(key=lambda x: x.get("points", 0), reverse=True)
            return users[:limit]
        return []


# =============================================================================
# TRIP SERVICE (Umrah Bareng)
# =============================================================================

class TripService:
    """Service for trip/Umrah Bareng operations."""
    
    @staticmethod
    def get_trip(trip_id: str) -> Optional[Dict]:
        """Get trip by ID."""
        if db.is_mock:
            return store.trips.get(trip_id)
        return None
    
    @staticmethod
    def get_all_trips(
        filters: Dict = None,
        sort_by: str = "created_at",
        limit: int = 50
    ) -> List[Dict]:
        """Get all trips with optional filters."""
        if db.is_mock:
            trips = list(store.trips.values())
            
            # Apply filters
            if filters:
                if filters.get("city"):
                    trips = [t for t in trips if t["departure_city"] == filters["city"]]
                if filters.get("budget"):
                    trips = [t for t in trips if t["budget_range"] == filters["budget"]]
                if filters.get("style"):
                    trips = [t for t in trips if t["travel_style"] == filters["style"]]
                if filters.get("status"):
                    trips = [t for t in trips if t["status"] == filters["status"]]
            
            # Sort
            if sort_by == "price":
                trips.sort(key=lambda x: x.get("price_estimate", 0))
            elif sort_by == "date":
                trips.sort(key=lambda x: x.get("departure_date", ""))
            elif sort_by == "popular":
                trips.sort(key=lambda x: x.get("likes", 0), reverse=True)
            else:
                trips.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return trips[:limit]
        return []
    
    @staticmethod
    def create_trip(data: Dict) -> Optional[Dict]:
        """Create new trip."""
        trip_id = f"trip_{len(store.trips) + 1}_{random.randint(1000, 9999)}"
        
        trip = {
            "id": trip_id,
            **data,
            "current_members": 1,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "likes": 0,
            "views": 0,
        }
        
        if db.is_mock:
            store.trips[trip_id] = trip
            return trip
        
        return None
    
    @staticmethod
    def update_trip(trip_id: str, data: Dict) -> bool:
        """Update trip."""
        if db.is_mock:
            if trip_id in store.trips:
                store.trips[trip_id].update(data)
                return True
        return False
    
    @staticmethod
    def join_trip(trip_id: str, user_id: str) -> Tuple[bool, str]:
        """Join a trip."""
        if db.is_mock:
            trip = store.trips.get(trip_id)
            if not trip:
                return False, "Trip tidak ditemukan"
            
            if trip["status"] != "open":
                return False, "Trip tidak tersedia"
            
            if trip["current_members"] >= trip["max_members"]:
                return False, "Trip sudah penuh"
            
            trip["current_members"] += 1
            if trip["current_members"] >= trip["max_members"]:
                trip["status"] = "full"
            
            return True, "Berhasil bergabung"
        
        return False, "Database error"
    
    @staticmethod
    def like_trip(trip_id: str) -> int:
        """Like a trip."""
        if db.is_mock:
            if trip_id in store.trips:
                store.trips[trip_id]["likes"] += 1
                return store.trips[trip_id]["likes"]
        return 0
    
    @staticmethod
    def increment_views(trip_id: str) -> int:
        """Increment trip views."""
        if db.is_mock:
            if trip_id in store.trips:
                store.trips[trip_id]["views"] += 1
                return store.trips[trip_id]["views"]
        return 0
    
    @staticmethod
    def search_trips(query: str) -> List[Dict]:
        """Search trips by keyword."""
        if db.is_mock:
            query = query.lower()
            results = []
            for trip in store.trips.values():
                if (query in trip["title"].lower() or 
                    query in trip["departure_city"].lower() or
                    any(query in tag for tag in trip.get("tags", []))):
                    results.append(trip)
            return results
        return []
    
    @staticmethod
    def get_user_trips(user_id: str) -> Dict[str, List[Dict]]:
        """Get trips created and joined by user."""
        if db.is_mock:
            created = [t for t in store.trips.values() if t["leader_id"] == user_id]
            # For demo, randomly assign some trips as joined
            joined = random.sample(list(store.trips.values()), k=min(3, len(store.trips)))
            return {"created": created, "joined": joined}
        return {"created": [], "joined": []}


# =============================================================================
# BOOKING SERVICE
# =============================================================================

class BookingService:
    """Service for booking operations."""
    
    @staticmethod
    def generate_booking_number() -> str:
        """Generate unique booking number."""
        chars = string.ascii_uppercase + string.digits
        return "LBK-" + "".join(random.choices(chars, k=8))
    
    @staticmethod
    def create_booking(user_id: str, data: Dict) -> Optional[Dict]:
        """Create new booking."""
        booking_id = BookingService.generate_booking_number()
        
        booking = {
            "id": booking_id,
            "user_id": user_id,
            **data,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "payment_status": "unpaid",
        }
        
        if db.is_mock:
            store.bookings[booking_id] = booking
            return booking
        
        return None
    
    @staticmethod
    def get_booking(booking_id: str) -> Optional[Dict]:
        """Get booking by ID."""
        if db.is_mock:
            return store.bookings.get(booking_id)
        return None
    
    @staticmethod
    def get_user_bookings(user_id: str) -> List[Dict]:
        """Get all bookings for a user."""
        if db.is_mock:
            return [b for b in store.bookings.values() if b["user_id"] == user_id]
        return []
    
    @staticmethod
    def update_booking_status(booking_id: str, status: str) -> bool:
        """Update booking status."""
        if db.is_mock:
            if booking_id in store.bookings:
                store.bookings[booking_id]["status"] = status
                store.bookings[booking_id]["updated_at"] = datetime.now().isoformat()
                return True
        return False
    
    @staticmethod
    def process_payment(booking_id: str, payment_data: Dict) -> Tuple[bool, str]:
        """Process payment for booking."""
        if db.is_mock:
            booking = store.bookings.get(booking_id)
            if not booking:
                return False, "Booking tidak ditemukan"
            
            booking["payment_status"] = "paid"
            booking["payment_data"] = payment_data
            booking["paid_at"] = datetime.now().isoformat()
            booking["status"] = "confirmed"
            
            return True, "Pembayaran berhasil"
        
        return False, "Database error"


# =============================================================================
# CHAT SERVICE
# =============================================================================

class ChatService:
    """Service for AI chat operations."""
    
    @staticmethod
    def save_message(user_id: str, role: str, content: str) -> Dict:
        """Save chat message."""
        message = {
            "id": f"msg_{datetime.now().timestamp()}",
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        if db.is_mock:
            if user_id not in store.chats:
                store.chats[user_id] = []
            store.chats[user_id].append(message)
        
        return message
    
    @staticmethod
    def get_chat_history(user_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for user."""
        if db.is_mock:
            messages = store.chats.get(user_id, [])
            return messages[-limit:]
        return []
    
    @staticmethod
    def clear_chat(user_id: str) -> bool:
        """Clear chat history."""
        if db.is_mock:
            store.chats[user_id] = []
            return True
        return False


# =============================================================================
# SIMULATION SERVICE
# =============================================================================

class SimulationService:
    """Service for cost simulation operations."""
    
    @staticmethod
    def save_simulation(user_id: str, params: Dict, result: Dict) -> Dict:
        """Save cost simulation."""
        simulation = {
            "id": f"sim_{datetime.now().timestamp()}",
            "params": params,
            "result": result,
            "created_at": datetime.now().isoformat(),
        }
        
        if db.is_mock:
            if user_id not in store.simulations:
                store.simulations[user_id] = []
            store.simulations[user_id].append(simulation)
        
        return simulation
    
    @staticmethod
    def get_simulations(user_id: str, limit: int = 10) -> List[Dict]:
        """Get saved simulations for user."""
        if db.is_mock:
            sims = store.simulations.get(user_id, [])
            return sims[-limit:]
        return []


# =============================================================================
# NOTIFICATION SERVICE
# =============================================================================

class NotificationService:
    """Service for notification operations."""
    
    @staticmethod
    def create_notification(user_id: str, type: str, message: str, data: Dict = None) -> Dict:
        """Create notification."""
        notification = {
            "id": f"notif_{datetime.now().timestamp()}",
            "type": type,
            "message": message,
            "data": data or {},
            "read": False,
            "created_at": datetime.now().isoformat(),
        }
        
        if db.is_mock:
            if user_id not in store.notifications:
                store.notifications[user_id] = []
            store.notifications[user_id].insert(0, notification)
        
        return notification
    
    @staticmethod
    def get_notifications(user_id: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for user."""
        if db.is_mock:
            notifs = store.notifications.get(user_id, [])
            if unread_only:
                notifs = [n for n in notifs if not n["read"]]
            return notifs
        return []
    
    @staticmethod
    def mark_as_read(user_id: str, notification_id: str) -> bool:
        """Mark notification as read."""
        if db.is_mock:
            for notif in store.notifications.get(user_id, []):
                if notif["id"] == notification_id:
                    notif["read"] = True
                    return True
        return False
    
    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        """Mark all notifications as read."""
        count = 0
        if db.is_mock:
            for notif in store.notifications.get(user_id, []):
                if not notif["read"]:
                    notif["read"] = True
                    count += 1
        return count


# =============================================================================
# ANALYTICS SERVICE
# =============================================================================

class AnalyticsService:
    """Service for analytics and statistics."""
    
    @staticmethod
    def get_platform_stats() -> Dict:
        """Get platform-wide statistics."""
        if db.is_mock:
            return {
                "total_users": len(store.users),
                "total_trips": len(store.trips),
                "total_bookings": len(store.bookings),
                "active_trips": len([t for t in store.trips.values() if t["status"] == "open"]),
                "total_jamaah": sum(t.get("current_members", 0) for t in store.trips.values()),
            }
        return {}
    
    @staticmethod
    def get_popular_destinations() -> List[Dict]:
        """Get popular departure cities."""
        if db.is_mock:
            cities = {}
            for trip in store.trips.values():
                city = trip["departure_city"]
                cities[city] = cities.get(city, 0) + 1
            
            sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)
            return [{"city": c, "count": n} for c, n in sorted_cities[:5]]
        return []
    
    @staticmethod
    def get_price_trends() -> Dict:
        """Get price trend data."""
        if db.is_mock:
            prices = [t["price_estimate"] for t in store.trips.values()]
            if prices:
                return {
                    "min": min(prices),
                    "max": max(prices),
                    "avg": sum(prices) // len(prices),
                    "count": len(prices),
                }
        return {"min": 0, "max": 0, "avg": 0, "count": 0}


# =============================================================================
# INITIALIZE & EXPORTS
# =============================================================================

def init_database():
    """Initialize database connection."""
    return db.connect()


# Exports
__all__ = [
    "Database",
    "DatabaseMode",
    "DataStore",
    "db",
    "store",
    "init_database",
    "UserService",
    "TripService",
    "BookingService",
    "ChatService",
    "SimulationService",
    "NotificationService",
    "AnalyticsService",
]
