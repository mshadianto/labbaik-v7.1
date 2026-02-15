"""
LABBAIK AI v6.0 - State Manager
===============================
Centralized state management integrating all services
with Streamlit session state.
"""

import logging
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
import json

# Import services
try:
    from services.data_service import (
        init_database,
        UserService,
        TripService,
        BookingService,
        ChatService,
        SimulationService,
        NotificationService,
        AnalyticsService,
        db,
        store,
    )
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    logging.getLogger(__name__).info("Data services not available, using local state only")


# =============================================================================
# STATE KEYS
# =============================================================================

class StateKeys:
    """Constants for session state keys."""
    
    # App state
    INITIALIZED = "app_initialized"
    CURRENT_PAGE = "current_page"
    THEME = "theme"
    
    # User state
    USER = "user"
    IS_AUTHENTICATED = "is_authenticated"
    AUTH_TOKEN = "auth_token"
    
    # Gamification
    POINTS = "points"
    BADGES = "badges"
    LEVEL = "level"
    
    # UI state
    SHOW_LOGIN = "show_login"
    SHOW_REGISTER = "show_register"
    SIDEBAR_STATE = "sidebar_state"
    
    # Feature state
    CHAT_MESSAGES = "chat_messages"
    CHAT_CONTEXT = "chat_context"
    
    BOOKING_STEP = "booking_step"
    BOOKING_DATA = "booking_data"
    
    UB_VIEW = "ub_view"
    UB_TRIPS = "ub_trips"
    UB_PROFILE = "ub_profile"
    UB_FILTERS = "ub_filters"
    UB_SELECTED_TRIP = "ub_selected_trip"
    UB_MY_TRIPS = "ub_my_trips"
    UB_JOINED_TRIPS = "ub_joined_trips"
    UB_NOTIFICATIONS = "ub_notifications"
    
    SIM_HISTORY = "sim_history"
    SIM_SAVED = "sim_saved"
    
    # Notifications
    NOTIFICATIONS = "notifications"
    UNREAD_COUNT = "unread_count"


# =============================================================================
# STATE MANAGER
# =============================================================================

class StateManager:
    """
    Centralized state manager for LABBAIK AI.
    Integrates Streamlit session state with data services.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
            self._callbacks: Dict[str, List[Callable]] = {}
    
    def initialize(self) -> bool:
        """Initialize state manager and all services."""
        
        if st.session_state.get(StateKeys.INITIALIZED):
            return True
        
        # Initialize database
        if SERVICES_AVAILABLE:
            init_database()
        
        # Initialize all session state
        self._init_app_state()
        self._init_user_state()
        self._init_gamification_state()
        self._init_chat_state()
        self._init_booking_state()
        self._init_umrah_bareng_state()
        self._init_simulator_state()
        self._init_notification_state()
        
        st.session_state[StateKeys.INITIALIZED] = True
        self._initialized = True
        
        return True
    
    # =========================================================================
    # INITIALIZATION METHODS
    # =========================================================================
    
    def _init_app_state(self):
        """Initialize app-level state."""
        if StateKeys.CURRENT_PAGE not in st.session_state:
            st.session_state[StateKeys.CURRENT_PAGE] = "home"
        
        if StateKeys.THEME not in st.session_state:
            st.session_state[StateKeys.THEME] = "light"
    
    def _init_user_state(self):
        """Initialize user-related state."""
        if StateKeys.USER not in st.session_state:
            st.session_state[StateKeys.USER] = None
        
        if StateKeys.IS_AUTHENTICATED not in st.session_state:
            st.session_state[StateKeys.IS_AUTHENTICATED] = False
    
    def _init_gamification_state(self):
        """Initialize gamification state."""
        if StateKeys.POINTS not in st.session_state:
            st.session_state[StateKeys.POINTS] = 0
        
        if StateKeys.BADGES not in st.session_state:
            st.session_state[StateKeys.BADGES] = []
        
        if StateKeys.LEVEL not in st.session_state:
            st.session_state[StateKeys.LEVEL] = 1
    
    def _init_chat_state(self):
        """Initialize chat state."""
        if StateKeys.CHAT_MESSAGES not in st.session_state:
            st.session_state[StateKeys.CHAT_MESSAGES] = [
                {
                    "role": "assistant",
                    "content": "Assalamu'alaikum! 👋 Saya asisten AI LABBAIK yang siap membantu Anda merencanakan ibadah umrah.",
                    "timestamp": datetime.now().isoformat(),
                }
            ]
        
        if StateKeys.CHAT_CONTEXT not in st.session_state:
            st.session_state[StateKeys.CHAT_CONTEXT] = "default"
    
    def _init_booking_state(self):
        """Initialize booking state."""
        if StateKeys.BOOKING_STEP not in st.session_state:
            st.session_state[StateKeys.BOOKING_STEP] = "package"
        
        if StateKeys.BOOKING_DATA not in st.session_state:
            st.session_state[StateKeys.BOOKING_DATA] = {
                "package_type": None,
                "departure_city": "Jakarta",
                "departure_date": None,
                "return_date": None,
                "travelers": [],
                "hotel_star": 4,
                "days_makkah": 5,
                "days_madinah": 4,
                "addons": [],
            }
    
    def _init_umrah_bareng_state(self):
        """Initialize Umrah Bareng state."""
        if StateKeys.UB_VIEW not in st.session_state:
            st.session_state[StateKeys.UB_VIEW] = "discover"
        
        if StateKeys.UB_TRIPS not in st.session_state:
            # Load from service or generate mock
            if SERVICES_AVAILABLE:
                trips = TripService.get_all_trips(limit=25)
                st.session_state[StateKeys.UB_TRIPS] = trips
            else:
                st.session_state[StateKeys.UB_TRIPS] = []
        
        if StateKeys.UB_PROFILE not in st.session_state:
            st.session_state[StateKeys.UB_PROFILE] = self._create_default_profile()
        
        if StateKeys.UB_FILTERS not in st.session_state:
            st.session_state[StateKeys.UB_FILTERS] = {}
        
        if StateKeys.UB_SELECTED_TRIP not in st.session_state:
            st.session_state[StateKeys.UB_SELECTED_TRIP] = None
        
        if StateKeys.UB_MY_TRIPS not in st.session_state:
            st.session_state[StateKeys.UB_MY_TRIPS] = []
        
        if StateKeys.UB_JOINED_TRIPS not in st.session_state:
            st.session_state[StateKeys.UB_JOINED_TRIPS] = []
        
        if StateKeys.UB_NOTIFICATIONS not in st.session_state:
            st.session_state[StateKeys.UB_NOTIFICATIONS] = [
                {"type": "info", "message": "Selamat datang di Umrah Bareng!", "time": "Baru saja"},
            ]
    
    def _init_simulator_state(self):
        """Initialize simulator state."""
        if StateKeys.SIM_HISTORY not in st.session_state:
            st.session_state[StateKeys.SIM_HISTORY] = []
        
        if StateKeys.SIM_SAVED not in st.session_state:
            st.session_state[StateKeys.SIM_SAVED] = []
    
    def _init_notification_state(self):
        """Initialize notification state."""
        if StateKeys.NOTIFICATIONS not in st.session_state:
            st.session_state[StateKeys.NOTIFICATIONS] = []
        
        if StateKeys.UNREAD_COUNT not in st.session_state:
            st.session_state[StateKeys.UNREAD_COUNT] = 0
    
    def _create_default_profile(self) -> Dict:
        """Create default user profile for Umrah Bareng."""
        return {
            "user_id": "guest",
            "name": "Guest User",
            "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=guest",
            "city": "Jakarta",
            "bio": "Jamaah LABBAIK",
            "trips_created": 0,
            "trips_joined": 0,
            "trips_completed": 0,
            "rating": 0.0,
            "reviews_count": 0,
            "is_verified": False,
            "is_premium": False,
            "followers": 0,
            "following": 0,
            "badges": [],
        }
    
    # =========================================================================
    # GETTER METHODS
    # =========================================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from session state."""
        return st.session_state.get(key, default)
    
    def get_user(self) -> Optional[Dict]:
        """Get current user."""
        return st.session_state.get(StateKeys.USER)
    
    def get_current_page(self) -> str:
        """Get current page."""
        return st.session_state.get(StateKeys.CURRENT_PAGE, "home")
    
    def get_points(self) -> int:
        """Get user points."""
        return st.session_state.get(StateKeys.POINTS, 0)
    
    def get_badges(self) -> List[Dict]:
        """Get user badges."""
        return st.session_state.get(StateKeys.BADGES, [])
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get(StateKeys.IS_AUTHENTICATED, False)
    
    # =========================================================================
    # SETTER METHODS
    # =========================================================================
    
    def set(self, key: str, value: Any):
        """Set value in session state."""
        st.session_state[key] = value
        self._trigger_callbacks(key)
    
    def set_page(self, page: str):
        """Set current page."""
        st.session_state[StateKeys.CURRENT_PAGE] = page
    
    def set_user(self, user: Optional[Dict]):
        """Set current user."""
        st.session_state[StateKeys.USER] = user
        st.session_state[StateKeys.IS_AUTHENTICATED] = user is not None
        
        if user:
            # Update Umrah Bareng profile - handle both dict and User object
            if hasattr(user, 'id'):
                # User object
                user_id = user.id
                name = getattr(user, 'name', 'User')
                city = getattr(user, 'city', 'Jakarta')
                is_verified = getattr(user, 'is_verified', False)
            else:
                # Dict
                user_id = user.get("id", "guest")
                name = user.get("name", "User")
                city = user.get("city", "Jakarta")
                is_verified = user.get("is_verified", False)

            st.session_state[StateKeys.UB_PROFILE] = {
                **self._create_default_profile(),
                "user_id": user_id,
                "name": name,
                "city": city,
                "is_verified": is_verified,
            }
    
    # =========================================================================
    # ACTION METHODS
    # =========================================================================
    
    def login(self, email: str, password: str) -> Tuple[bool, str]:
        """Login user."""
        if SERVICES_AVAILABLE:
            user = UserService.authenticate(email, password)
            if user:
                self.set_user(user)
                self.add_points(50, "Login bonus")
                return True, "Login berhasil"
            return False, "Email atau password salah"
        else:
            # Mock login
            user = {
                "id": "mock_user",
                "name": email.split("@")[0].title(),
                "email": email,
            }
            self.set_user(user)
            return True, "Login berhasil (demo mode)"
    
    def logout(self):
        """Logout user."""
        self.set_user(None)
        st.session_state[StateKeys.POINTS] = 0
        st.session_state[StateKeys.BADGES] = []
    
    def register(self, name: str, email: str, password: str) -> Tuple[bool, str]:
        """Register new user."""
        if SERVICES_AVAILABLE:
            existing = UserService.get_user_by_email(email)
            if existing:
                return False, "Email sudah terdaftar"
            
            user = UserService.create_user(name, email, password)
            if user:
                self.set_user(user)
                self.add_points(100, "Welcome bonus")
                self.add_badge("first_visit", "First Visit", "🌟")
                return True, "Registrasi berhasil"
            return False, "Gagal membuat akun"
        else:
            # Mock register
            user = {"id": "mock_user", "name": name, "email": email}
            self.set_user(user)
            return True, "Registrasi berhasil (demo mode)"
    
    def add_points(self, points: int, reason: str = ""):
        """Add points to user."""
        current = st.session_state.get(StateKeys.POINTS, 0)
        st.session_state[StateKeys.POINTS] = current + points
        
        # Show toast
        st.toast(f"🎉 +{points} poin! {reason}")
        
        # Check for badges
        self._check_badges()
        
        # Sync with service
        user = self.get_user()
        if user and SERVICES_AVAILABLE:
            user_id = user.id if hasattr(user, 'id') else user.get("id")
            UserService.add_points(user_id, points, reason)
    
    def add_badge(self, badge_id: str, name: str, icon: str):
        """Add badge to user."""
        badges = st.session_state.get(StateKeys.BADGES, [])
        
        if not any(b["id"] == badge_id for b in badges):
            badges.append({"id": badge_id, "name": name, "icon": icon})
            st.session_state[StateKeys.BADGES] = badges
            st.balloons()
            st.toast(f"🏅 Badge baru: {icon} {name}")
    
    def _check_badges(self):
        """Check and award badges based on points."""
        points = st.session_state.get(StateKeys.POINTS, 0)
        badges = st.session_state.get(StateKeys.BADGES, [])
        badge_ids = [b["id"] for b in badges]
        
        badge_thresholds = [
            (10, "first_visit", "First Visit", "🌟"),
            (100, "explorer", "Explorer", "🔍"),
            (500, "learner", "Learner", "📚"),
            (1000, "planner", "Planner", "📋"),
            (5000, "champion", "Champion", "🏆"),
        ]
        
        for threshold, badge_id, name, icon in badge_thresholds:
            if points >= threshold and badge_id not in badge_ids:
                self.add_badge(badge_id, name, icon)
    
    def add_notification(self, type: str, message: str):
        """Add notification."""
        notifications = st.session_state.get(StateKeys.NOTIFICATIONS, [])
        notifications.insert(0, {
            "type": type,
            "message": message,
            "time": datetime.now().isoformat(),
            "read": False,
        })
        st.session_state[StateKeys.NOTIFICATIONS] = notifications[:50]  # Keep last 50
        st.session_state[StateKeys.UNREAD_COUNT] = sum(1 for n in notifications if not n["read"])
    
    # =========================================================================
    # CALLBACK SYSTEM
    # =========================================================================
    
    def on_change(self, key: str, callback: Callable):
        """Register callback for state change."""
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)
    
    def _trigger_callbacks(self, key: str):
        """Trigger callbacks for a key."""
        for callback in self._callbacks.get(key, []):
            try:
                callback(st.session_state.get(key))
            except Exception as e:
                logging.getLogger(__name__).debug(f"Callback error: {e}")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def reset(self):
        """Reset all state."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        self._initialized = False
        self.initialize()
    
    def export_state(self) -> str:
        """Export state as JSON."""
        exportable = {}
        for key, value in st.session_state.items():
            try:
                json.dumps(value)  # Test serializable
                exportable[key] = value
            except Exception:
                pass
        return json.dumps(exportable, indent=2, default=str)
    
    def get_stats(self) -> Dict:
        """Get state statistics."""
        return {
            "total_keys": len(st.session_state),
            "user": self.get_user().get("name") if self.get_user() else None,
            "points": self.get_points(),
            "badges": len(self.get_badges()),
            "current_page": self.get_current_page(),
        }


# Missing import

# Global instance
state_manager = StateManager()


def init_state() -> StateManager:
    """Initialize and return state manager."""
    state_manager.initialize()
    return state_manager


# Exports
__all__ = [
    "StateManager",
    "StateKeys",
    "state_manager",
    "init_state",
]
