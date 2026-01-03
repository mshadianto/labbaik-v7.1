"""
LABBAIK Smart Planner - Analytics Service
==========================================
Real-time visitor tracking and analytics.
"""

import streamlit as st
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid

logger = logging.getLogger(__name__)

# Internal/admin emails to exclude from tracking
EXCLUDED_EMAILS = [
    'admin@labbaik.io',
    'founder@labbaik.io',
    'salam@labbaik.io',
]


# =============================================================================
# ANALYTICS TRACKER
# =============================================================================

class AnalyticsTracker:
    """
    Real-time analytics tracker for page views and visitor sessions.
    """
    
    def __init__(self):
        self._db = None
        self._initialized = False
    
    @property
    def db(self):
        """Lazy load database connection."""
        if self._db is None:
            try:
                from services.database.repository import get_db
                self._db = get_db()
            except Exception as e:
                logger.warning(f"Database not available for analytics: {e}")
        return self._db
    
    def _get_or_create_session_id(self) -> str:
        """Get or create a unique session ID."""
        if "analytics_session_id" not in st.session_state:
            st.session_state.analytics_session_id = str(uuid.uuid4())
        return st.session_state.analytics_session_id
    
    def _get_device_type(self) -> str:
        """Detect device type from session."""
        # Simple detection - can be enhanced
        return "mobile" if st.session_state.get("is_mobile", False) else "desktop"
    
    def _hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy."""
        if not ip:
            return ""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def _is_excluded_user(self) -> bool:
        """Check if current user should be excluded from tracking (internal users)."""
        try:
            if 'user' in st.session_state and st.session_state.user:
                user = st.session_state.user
                email = None
                if hasattr(user, 'email'):
                    email = user.email
                elif isinstance(user, dict):
                    email = user.get('email')

                if email and email.lower() in [e.lower() for e in EXCLUDED_EMAILS]:
                    return True
        except:
            pass
        return False
    
    def track_page_view(self, page: str) -> bool:
        """
        Track a page view event.

        Args:
            page: Page name (e.g., 'home', 'chat', 'simulator')

        Returns:
            True if tracking successful
        """
        # Skip tracking for internal/admin users
        if self._is_excluded_user():
            return True

        if not self.db:
            return False
        
        try:
            session_id = self._get_or_create_session_id()
            device_type = self._get_device_type()
            
            # Check if this is a new session
            is_new_session = not st.session_state.get("analytics_tracked_pages")
            if not st.session_state.get("analytics_tracked_pages"):
                st.session_state.analytics_tracked_pages = set()
            
            is_unique_page = page not in st.session_state.analytics_tracked_pages
            st.session_state.analytics_tracked_pages.add(page)
            
            # 1. Record raw event
            self._record_page_event(session_id, page, device_type)
            
            # 2. Update aggregated stats
            self._update_daily_stats(page, is_unique=is_unique_page)
            
            # 3. Update session
            self._update_session(session_id, page, device_type, is_new=is_new_session)
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking page view: {e}")
            return False
    
    def _record_page_event(self, session_id: str, page: str, device_type: str):
        """Record raw page view event."""
        try:
            query = """
                INSERT INTO page_view_events (session_id, page, device_type, created_at)
                VALUES (%s, %s, %s, NOW())
            """
            self.db.execute(query, (session_id, page, device_type))
        except Exception as e:
            logger.debug(f"Could not record page event: {e}")
    
    def _update_daily_stats(self, page: str, is_unique: bool = False):
        """Update aggregated daily statistics."""
        try:
            # Use UPSERT pattern
            query = """
                INSERT INTO visitor_stats (date, page, unique_visitors, page_views, updated_at)
                VALUES (CURRENT_DATE, %s, %s, 1, NOW())
                ON CONFLICT (date, page) DO UPDATE SET
                    unique_visitors = visitor_stats.unique_visitors + EXCLUDED.unique_visitors,
                    page_views = visitor_stats.page_views + 1,
                    updated_at = NOW()
            """
            unique_increment = 1 if is_unique else 0
            self.db.execute(query, (page, unique_increment))
        except Exception as e:
            logger.debug(f"Could not update daily stats: {e}")
    
    def _update_session(self, session_id: str, page: str, device_type: str, is_new: bool = False):
        """Update session tracking."""
        try:
            if is_new:
                # Create new session
                query = """
                    INSERT INTO visitor_sessions 
                    (session_id, first_page, last_page, page_count, device_type, started_at, last_activity)
                    VALUES (%s, %s, %s, 1, %s, NOW(), NOW())
                    ON CONFLICT (session_id) DO UPDATE SET
                        last_page = EXCLUDED.last_page,
                        page_count = visitor_sessions.page_count + 1,
                        last_activity = NOW(),
                        duration_seconds = EXTRACT(EPOCH FROM (NOW() - visitor_sessions.started_at))::INTEGER
                """
                self.db.execute(query, (session_id, page, page, device_type))
            else:
                # Update existing session
                query = """
                    UPDATE visitor_sessions SET
                        last_page = %s,
                        page_count = page_count + 1,
                        last_activity = NOW(),
                        duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER
                    WHERE session_id = %s
                """
                self.db.execute(query, (page, session_id))
        except Exception as e:
            logger.debug(f"Could not update session: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive visitor statistics.
        
        Returns:
            Dictionary with all stats
        """
        if not self.db:
            return self._get_fallback_stats()
        
        try:
            # Total stats
            total_query = """
                SELECT 
                    COALESCE(SUM(unique_visitors), 0) as total_visitors,
                    COALESCE(SUM(page_views), 0) as total_views
                FROM visitor_stats
            """
            total = self.db.fetch_one(total_query) or {}
            
            if total.get('total_visitors', 0) == 0:
                return self._get_fallback_stats()
            
            # Today's stats
            today_query = """
                SELECT 
                    COALESCE(SUM(unique_visitors), 0) as visitors_today,
                    COALESCE(SUM(page_views), 0) as views_today
                FROM visitor_stats
                WHERE date = CURRENT_DATE
            """
            today = self.db.fetch_one(today_query) or {}
            
            # This week's stats
            week_query = """
                SELECT 
                    COALESCE(SUM(unique_visitors), 0) as visitors_week,
                    COALESCE(SUM(page_views), 0) as views_week
                FROM visitor_stats
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            """
            week = self.db.fetch_one(week_query) or {}
            
            # This month's stats
            month_query = """
                SELECT 
                    COALESCE(SUM(unique_visitors), 0) as visitors_month,
                    COALESCE(SUM(page_views), 0) as views_month
                FROM visitor_stats
                WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
            """
            month = self.db.fetch_one(month_query) or {}
            
            # Popular pages
            pages_query = """
                SELECT page, SUM(page_views) as views
                FROM visitor_stats
                GROUP BY page
                ORDER BY views DESC
                LIMIT 6
            """
            popular = self.db.fetch_all(pages_query) or []
            
            # Engagement metrics
            engagement = self._get_engagement_metrics()
            
            return {
                "total_visitors": int(total.get('total_visitors', 0)),
                "total_views": int(total.get('total_views', 0)),
                "visitors_today": int(today.get('visitors_today', 0)),
                "views_today": int(today.get('views_today', 0)),
                "visitors_week": int(week.get('visitors_week', 0)),
                "views_week": int(week.get('views_week', 0)),
                "visitors_month": int(month.get('visitors_month', 0)),
                "views_month": int(month.get('views_month', 0)),
                "popular_pages": [{"page": p['page'], "views": int(p['views'])} for p in popular],
                "engagement": engagement,
                "source": "database"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return self._get_fallback_stats()
    
    def _get_engagement_metrics(self) -> Dict[str, Any]:
        """Get engagement metrics from sessions."""
        try:
            query = """
                SELECT 
                    AVG(page_count) as avg_pages,
                    AVG(duration_seconds) as avg_duration,
                    COUNT(CASE WHEN is_returning THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 as returning_rate,
                    COUNT(CASE WHEN device_type = 'mobile' THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100 as mobile_rate
                FROM visitor_sessions
                WHERE last_activity >= NOW() - INTERVAL '30 days'
            """
            result = self.db.fetch_one(query) or {}
            
            avg_duration = int(result.get('avg_duration', 272) or 272)
            minutes = avg_duration // 60
            seconds = avg_duration % 60
            
            return {
                "avg_pages_per_visit": round(float(result.get('avg_pages', 1.3) or 1.3), 1),
                "avg_session_duration": f"{minutes}m {seconds}s",
                "returning_visitors_pct": round(float(result.get('returning_rate', 34) or 34), 0),
                "mobile_users_pct": round(float(result.get('mobile_rate', 67) or 67), 0),
                "top_region": "Jakarta"  # TODO: implement geo tracking
            }
        except:
            return {
                "avg_pages_per_visit": 1.3,
                "avg_session_duration": "4m 32s",
                "returning_visitors_pct": 34,
                "mobile_users_pct": 67,
                "top_region": "Jakarta"
            }
    
    def _get_fallback_stats(self) -> Dict[str, Any]:
        """Return demo stats when database is not available."""
        import random
        
        # Use session state to maintain consistency
        if "demo_visitor_count" not in st.session_state:
            st.session_state.demo_visitor_count = random.randint(950, 1050)
        if "demo_page_views" not in st.session_state:
            st.session_state.demo_page_views = random.randint(1300, 1500)
        
        # Increment on new session
        if not st.session_state.get("demo_counted"):
            st.session_state.demo_visitor_count += 1
            st.session_state.demo_page_views += random.randint(1, 3)
            st.session_state.demo_counted = True
        
        return {
            "total_visitors": st.session_state.demo_visitor_count,
            "total_views": st.session_state.demo_page_views,
            "visitors_today": random.randint(45, 65),
            "views_today": random.randint(80, 120),
            "visitors_week": random.randint(300, 400),
            "views_week": random.randint(600, 800),
            "visitors_month": st.session_state.demo_visitor_count,
            "views_month": st.session_state.demo_page_views,
            "popular_pages": [
                {"page": "home", "views": 523},
                {"page": "umrah_mandiri", "views": 287},
                {"page": "simulator", "views": 198},
                {"page": "chat", "views": 156},
                {"page": "umrah_bareng", "views": 89},
                {"page": "booking", "views": 67},
            ],
            "engagement": {
                "avg_pages_per_visit": 1.3,
                "avg_session_duration": "4m 32s",
                "returning_visitors_pct": 34,
                "mobile_users_pct": 67,
                "top_region": "Jakarta"
            },
            "source": "demo"
        }
    
    # =========================================================================
    # EVENT TRACKING METHODS
    # =========================================================================

    def track_event(
        self,
        event_type: str,
        event_category: str,
        event_action: str,
        event_label: Optional[str] = None,
        page_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track custom analytics event."""
        # Skip tracking for internal/admin users
        if self._is_excluded_user():
            return True

        if not self.db:
            return False

        try:
            session_id = self._get_or_create_session_id()
            user_id = None

            # Try to get user ID from session - handle both dict and User object
            if 'user' in st.session_state and st.session_state.user:
                user = st.session_state.user
                if hasattr(user, 'id'):
                    user_id = user.id
                elif isinstance(user, dict):
                    user_id = user.get('id')

            query = """
                INSERT INTO analytics_events (
                    user_id, session_id, event_type, event_category,
                    event_action, event_label, page_name, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            import json
            metadata_json = json.dumps(metadata) if metadata else None

            self.db.execute(
                query,
                (user_id, session_id, event_type, event_category,
                 event_action, event_label, page_name, metadata_json)
            )
            return True
        except Exception as e:
            logger.debug(f"Event tracking error: {e}")
            return False

    def track_smart_nudge_show(self, savings_amount: float, page_name: str = "simulator") -> bool:
        """Track when smart nudge is shown."""
        return self.track_event(
            event_type='nudge_shown',
            event_category='smart_savings',
            event_action='nudge_displayed',
            page_name=page_name,
            metadata={'potential_savings': savings_amount}
        )

    def track_smart_nudge_click(self, page_name: str = "simulator") -> bool:
        """Track smart nudge click-through."""
        return self.track_event(
            event_type='button_click',
            event_category='smart_savings',
            event_action='nudge_clicked',
            event_label='umrah_bareng_redirect',
            page_name=page_name
        )

    def track_feature_usage(self, feature_name: str, action: str, metadata: Optional[Dict] = None) -> bool:
        """Track feature usage."""
        return self.track_event(
            event_type='feature_usage',
            event_category=feature_name,
            event_action=action,
            metadata=metadata
        )

    def track_conversion(self, conversion_type: str, value: Optional[float] = None) -> bool:
        """Track conversion events (premium upgrade, umrah bareng match, etc)."""
        return self.track_event(
            event_type='conversion',
            event_category='conversions',
            event_action=conversion_type,
            metadata={'value': value} if value else None
        )

    def track_pillar_view(self, pillar_name: str) -> bool:
        """Track pillar navigation (Smart Prep, Smart Savings, Smart Journey)."""
        return self.track_event(
            event_type='pillar_view',
            event_category='navigation',
            event_action=f'view_{pillar_name.lower().replace(" ", "_")}',
            event_label=pillar_name
        )

    def get_daily_trend(self, days: int = 7) -> List[Dict]:
        """Get daily visitor trend."""
        if not self.db:
            return []
        
        try:
            query = """
                SELECT 
                    date,
                    SUM(unique_visitors) as visitors,
                    SUM(page_views) as views
                FROM visitor_stats
                WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY date
                ORDER BY date ASC
            """
            return self.db.fetch_all(query, (days,)) or []
        except:
            return []
    
    def get_hourly_distribution(self) -> List[Dict]:
        """Get hourly page view distribution."""
        if not self.db:
            return []
        
        try:
            query = """
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as views
                FROM page_view_events
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY hour
                ORDER BY hour
            """
            return self.db.fetch_all(query) or []
        except:
            return []


# =============================================================================
# SINGLETON & HELPER FUNCTIONS
# =============================================================================

_tracker_instance: Optional[AnalyticsTracker] = None


def get_analytics_tracker() -> AnalyticsTracker:
    """Get the analytics tracker singleton."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = AnalyticsTracker()
    return _tracker_instance


def track_page(page: str) -> bool:
    """
    Track a page view. Call this at the start of each page.
    
    Args:
        page: Page name (e.g., 'home', 'chat', 'simulator')
    
    Returns:
        True if tracking successful
    """
    return get_analytics_tracker().track_page_view(page)


def get_visitor_stats() -> Dict[str, Any]:
    """
    Get visitor statistics.
    
    Returns:
        Dictionary with visitor stats
    """
    return get_analytics_tracker().get_stats()


# =============================================================================
# PAGE TRACKING DECORATOR
# =============================================================================

def with_analytics(page_name: str):
    """
    Decorator to automatically track page views.
    
    Usage:
        @with_analytics("home")
        def render_home_page():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            track_page(page_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience functions for event tracking
def track_smart_nudge_show(savings_amount: float) -> bool:
    """Track smart nudge display."""
    return get_analytics_tracker().track_smart_nudge_show(savings_amount)


def track_smart_nudge_click() -> bool:
    """Track smart nudge click."""
    return get_analytics_tracker().track_smart_nudge_click()


def track_feature_usage(feature_name: str, action: str) -> bool:
    """Track feature usage."""
    return get_analytics_tracker().track_feature_usage(feature_name, action)


def track_conversion(conversion_type: str, value: Optional[float] = None) -> bool:
    """Track conversion event."""
    return get_analytics_tracker().track_conversion(conversion_type, value)


# Export
__all__ = [
    "AnalyticsTracker",
    "get_analytics_tracker",
    "track_page",
    "get_visitor_stats",
    "with_analytics",
    "track_smart_nudge_show",
    "track_smart_nudge_click",
    "track_feature_usage",
    "track_conversion"
]
