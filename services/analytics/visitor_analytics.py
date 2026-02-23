"""
LABBAIK AI v6.0 - Visitor Analytics Service
============================================
Track and display visitor statistics from Neon DB
"""

import streamlit as st
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class VisitorAnalytics:
    """
    Visitor analytics service connected to Neon PostgreSQL.
    Tables used: visitor_stats, visitor_logs, page_views
    """
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL", "")
        self._conn = None
    
    def _get_connection(self):
        """Get database connection."""
        if not self.db_url:
            return None
        
        try:
            import psycopg2
            if not self._conn or self._conn.closed:
                self._conn = psycopg2.connect(self.db_url)
            return self._conn
        except Exception as e:
            logger.error(f"DB connection error: {e}")
            return None
    
    def _execute_query(self, query: str, params: tuple = None, fetch: str = "one") -> Any:
        """Execute query and return results."""
        conn = self._get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetch == "one":
                    return cur.fetchone()
                elif fetch == "all":
                    return cur.fetchall()
                else:
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Query error: {e}")
            conn.rollback()
            return None
    
    # =========================================================================
    # VISITOR STATS
    # =========================================================================
    
    def get_total_visitors(self) -> int:
        """Get total unique visitors."""
        result = self._execute_query(
            "SELECT stat_value FROM visitor_stats WHERE stat_key = 'total_visitors'"
        )
        return result[0] if result else 0
    
    def get_total_views(self) -> int:
        """Get total page views."""
        result = self._execute_query(
            "SELECT stat_value FROM visitor_stats WHERE stat_key = 'total_views'"
        )
        return result[0] if result else 0
    
    def increment_visitor(self) -> bool:
        """Increment visitor count."""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE visitor_stats 
                    SET stat_value = stat_value + 1, last_updated = NOW()
                    WHERE stat_key = 'total_visitors'
                """)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Increment visitor error: {e}")
            conn.rollback()
            return False
    
    def increment_views(self) -> bool:
        """Increment page views count."""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE visitor_stats 
                    SET stat_value = stat_value + 1, last_updated = NOW()
                    WHERE stat_key = 'total_views'
                """)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Increment views error: {e}")
            conn.rollback()
            return False
    
    def get_all_stats(self) -> Dict[str, int]:
        """Get all visitor stats."""
        results = self._execute_query(
            "SELECT stat_key, stat_value FROM visitor_stats",
            fetch="all"
        )
        if results:
            return {row[0]: row[1] for row in results}
        return {"total_visitors": 0, "total_views": 0}
    
    # =========================================================================
    # VISITOR LOGS
    # =========================================================================
    
    def log_visitor(self, session_id: str, page: str = "home", 
                    user_agent: str = None, ip_hash: str = None) -> bool:
        """Log a visitor entry."""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO visitor_logs (session_id, page, user_agent, ip_hash, visited_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (session_id, page, user_agent, ip_hash))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Log visitor error: {e}")
            conn.rollback()
            return False
    
    def get_visitors_today(self) -> int:
        """Get unique visitors today."""
        result = self._execute_query("""
            SELECT COUNT(DISTINCT session_id) 
            FROM visitor_logs 
            WHERE visited_at >= CURRENT_DATE
        """)
        return result[0] if result else 0
    
    def get_visitors_this_week(self) -> int:
        """Get unique visitors this week."""
        result = self._execute_query("""
            SELECT COUNT(DISTINCT session_id) 
            FROM visitor_logs 
            WHERE visited_at >= CURRENT_DATE - INTERVAL '7 days'
        """)
        return result[0] if result else 0
    
    def get_visitors_this_month(self) -> int:
        """Get unique visitors this month."""
        result = self._execute_query("""
            SELECT COUNT(DISTINCT session_id) 
            FROM visitor_logs 
            WHERE visited_at >= DATE_TRUNC('month', CURRENT_DATE)
        """)
        return result[0] if result else 0
    
    # =========================================================================
    # PAGE VIEWS
    # =========================================================================
    
    def log_page_view(self, page: str, session_id: str = None) -> bool:
        """Log a page view."""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO page_views (page_name, session_id, viewed_at)
                    VALUES (%s, %s, NOW())
                """, (page, session_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Log page view error: {e}")
            conn.rollback()
            return False
    
    def get_popular_pages(self, limit: int = 5) -> List[Dict]:
        """Get most popular pages."""
        results = self._execute_query("""
            SELECT page_name, COUNT(*) as views
            FROM page_views
            GROUP BY page_name
            ORDER BY views DESC
            LIMIT %s
        """, (limit,), fetch="all")
        
        if results:
            return [{"page": row[0], "views": row[1]} for row in results]
        return []
    
    def get_views_by_day(self, days: int = 7) -> List[Dict]:
        """Get page views by day."""
        results = self._execute_query("""
            SELECT DATE(viewed_at) as date, COUNT(*) as views
            FROM page_views
            WHERE viewed_at >= CURRENT_DATE - INTERVAL '1 day' * %s
            GROUP BY DATE(viewed_at)
            ORDER BY date ASC
        """, params=(days,), fetch="all")
        
        if results:
            return [{"date": str(row[0]), "views": row[1]} for row in results]
        return []
    
    # =========================================================================
    # ANALYTICS SUMMARY
    # =========================================================================
    
    def get_analytics_summary(self) -> Dict:
        """Get comprehensive analytics summary."""
        return {
            "total_visitors": self.get_total_visitors(),
            "total_views": self.get_total_views(),
            "visitors_today": self.get_visitors_today(),
            "visitors_week": self.get_visitors_this_week(),
            "visitors_month": self.get_visitors_this_month(),
            "popular_pages": self.get_popular_pages(),
            "views_trend": self.get_views_by_day(7),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_analytics_instance = None

def get_analytics() -> VisitorAnalytics:
    """Get singleton analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = VisitorAnalytics()
    return _analytics_instance


# =============================================================================
# STREAMLIT TRACKING HELPERS
# =============================================================================

def track_visitor():
    """Track unique visitor (call once per session)."""
    if not st.session_state.get("visitor_tracked"):
        analytics = get_analytics()
        
        # Generate session ID
        import hashlib
        import time
        session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:16]
        st.session_state.session_id = session_id
        
        # Increment stats and log
        analytics.increment_visitor()
        analytics.log_visitor(session_id, "home")
        
        st.session_state.visitor_tracked = True


def track_page_view(page: str):
    """Track page view."""
    analytics = get_analytics()
    session_id = st.session_state.get("session_id", "anonymous")
    
    # Track unique page views per session
    viewed_pages = st.session_state.get("viewed_pages", set())
    if page not in viewed_pages:
        analytics.increment_views()
        analytics.log_page_view(page, session_id)
        viewed_pages.add(page)
        st.session_state.viewed_pages = viewed_pages


# =============================================================================
# DEMO/OFFLINE MODE
# =============================================================================

def get_demo_stats() -> Dict:
    """Get demo stats when DB is not available."""
    return {
        "total_visitors": 975,
        "total_views": 1328,
        "visitors_today": 47,
        "visitors_week": 312,
        "visitors_month": 975,
        "popular_pages": [
            {"page": "home", "views": 523},
            {"page": "umrah_mandiri", "views": 287},
            {"page": "simulator", "views": 198},
            {"page": "chat", "views": 156},
            {"page": "umrah_bareng", "views": 89},
        ],
        "views_trend": [
            {"date": "2025-12-04", "views": 156},
            {"date": "2025-12-05", "views": 189},
            {"date": "2025-12-06", "views": 234},
            {"date": "2025-12-07", "views": 178},
            {"date": "2025-12-08", "views": 201},
            {"date": "2025-12-09", "views": 245},
            {"date": "2025-12-10", "views": 125},
        ],
    }
