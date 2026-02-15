"""
LABBAIK AI v6.0 - Price Intelligence Monitoring
================================================
Monitoring dan audit trail untuk memastikan data harga selalu terupdate.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from services.database.repository import get_db

logger = logging.getLogger(__name__)


class PriceMonitor:
    """
    Monitor untuk memastikan Price Intelligence berfungsi dengan baik.
    """
    
    def __init__(self):
        self.db = get_db()
    
    def get_health_status(self) -> Dict:
        """
        Cek kesehatan sistem Price Intelligence.
        
        Returns:
            Dictionary dengan status kesehatan
        """
        status = {
            'overall': 'healthy',
            'database': 'unknown',
            'packages': {'status': 'unknown', 'count': 0, 'last_update': None},
            'hotels': {'status': 'unknown', 'count': 0, 'last_update': None},
            'flights': {'status': 'unknown', 'count': 0, 'last_update': None},
            'n8n_workflow': 'unknown',
            'issues': []
        }
        
        try:
            # Check database connection
            result = self.db.fetch_one("SELECT 1 as ok")
            status['database'] = 'connected' if result else 'error'
        except Exception as e:
            status['database'] = 'error'
            status['issues'].append(f"Database connection failed: {e}")
            status['overall'] = 'critical'
            return status
        
        # Check packages
        try:
            pkg_result = self.db.fetch_one("""
                SELECT COUNT(*) as count, MAX(scraped_at) as last_update
                FROM prices_packages WHERE is_available = true
            """)
            if pkg_result:
                status['packages']['count'] = pkg_result.get('count', 0)
                status['packages']['last_update'] = pkg_result.get('last_update')
                status['packages']['status'] = self._check_freshness(pkg_result.get('last_update'))
        except Exception as e:
            status['packages']['status'] = 'error'
            status['issues'].append(f"Packages check failed: {e}")
        
        # Check hotels
        try:
            hotel_result = self.db.fetch_one("""
                SELECT COUNT(*) as count, MAX(scraped_at) as last_update
                FROM prices_hotels WHERE is_available = true
            """)
            if hotel_result:
                status['hotels']['count'] = hotel_result.get('count', 0)
                status['hotels']['last_update'] = hotel_result.get('last_update')
                status['hotels']['status'] = self._check_freshness(hotel_result.get('last_update'))
        except Exception as e:
            status['hotels']['status'] = 'error'
            status['issues'].append(f"Hotels check failed: {e}")
        
        # Check flights
        try:
            flight_result = self.db.fetch_one("""
                SELECT COUNT(*) as count, MAX(scraped_at) as last_update
                FROM prices_flights WHERE is_available = true
            """)
            if flight_result:
                status['flights']['count'] = flight_result.get('count', 0)
                status['flights']['last_update'] = flight_result.get('last_update')
                status['flights']['status'] = self._check_freshness(flight_result.get('last_update'))
        except Exception as e:
            status['flights']['status'] = 'error'
            status['issues'].append(f"Flights check failed: {e}")
        
        # Check n8n workflow (based on scraping_logs or last update time)
        try:
            log_result = self.db.fetch_one("""
                SELECT MAX(scraped_at) as last_run
                FROM (
                    SELECT MAX(scraped_at) as scraped_at FROM prices_packages
                    UNION ALL SELECT MAX(scraped_at) FROM prices_hotels
                    UNION ALL SELECT MAX(scraped_at) FROM prices_flights
                ) t
            """)
            if log_result and log_result.get('last_run'):
                last_run = log_result['last_run']
                hours_ago = (datetime.utcnow() - last_run.replace(tzinfo=None)).total_seconds() / 3600
                
                if hours_ago <= 7:  # Should run every 6 hours + 1 hour buffer
                    status['n8n_workflow'] = 'running'
                elif hours_ago <= 13:
                    status['n8n_workflow'] = 'delayed'
                    status['issues'].append(f"n8n workflow delayed ({hours_ago:.1f} hours since last run)")
                else:
                    status['n8n_workflow'] = 'stopped'
                    status['issues'].append(f"n8n workflow may be stopped ({hours_ago:.1f} hours since last run)")
        except Exception as e:
            status['n8n_workflow'] = 'unknown'
        
        # Determine overall status
        statuses = [
            status['packages']['status'],
            status['hotels']['status'],
            status['flights']['status']
        ]
        
        if 'error' in statuses or status['database'] == 'error':
            status['overall'] = 'critical'
        elif 'stale' in statuses or status['n8n_workflow'] == 'stopped':
            status['overall'] = 'warning'
        elif all(s == 'fresh' for s in statuses):
            status['overall'] = 'healthy'
        else:
            status['overall'] = 'degraded'
        
        return status
    
    def _check_freshness(self, last_update: Optional[datetime]) -> str:
        """Check if data is fresh (within 7 hours)."""
        if not last_update:
            return 'no_data'
        
        # Handle timezone
        if last_update.tzinfo:
            last_update = last_update.replace(tzinfo=None)
        
        hours_ago = (datetime.utcnow() - last_update).total_seconds() / 3600
        
        if hours_ago <= 7:
            return 'fresh'
        elif hours_ago <= 24:
            return 'stale'
        else:
            return 'outdated'
    
    def get_update_history(self, days: int = 7) -> List[Dict]:
        """
        Ambil history update untuk audit trail.
        
        Args:
            days: Jumlah hari ke belakang
        
        Returns:
            List of update records
        """
        try:
            # Get distinct scraped_at timestamps grouped by date
            query = """
                SELECT 
                    DATE(scraped_at) as date,
                    COUNT(DISTINCT scraped_at) as update_count,
                    MIN(scraped_at) as first_update,
                    MAX(scraped_at) as last_update
                FROM (
                    SELECT scraped_at FROM prices_packages
                    UNION ALL SELECT scraped_at FROM prices_hotels
                    UNION ALL SELECT scraped_at FROM prices_flights
                ) all_updates
                WHERE scraped_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(scraped_at)
                ORDER BY date DESC
            """
            return self.db.fetch_all(query, (days,))
        except Exception as e:
            logger.error(f"Failed to get update history: {e}")
            return []
    
    def get_data_summary(self) -> Dict:
        """Get summary of all price data."""
        try:
            summary = self.db.fetch_one("""
                SELECT
                    (SELECT COUNT(*) FROM prices_packages WHERE is_available = true) as total_packages,
                    (SELECT COUNT(*) FROM prices_hotels WHERE is_available = true) as total_hotels,
                    (SELECT COUNT(*) FROM prices_flights WHERE is_available = true AND departure_date >= CURRENT_DATE) as total_flights,
                    (SELECT COUNT(DISTINCT source_id) FROM prices_packages) as package_sources,
                    (SELECT MIN(price_idr) FROM prices_packages WHERE is_available = true) as min_package_price,
                    (SELECT MAX(price_idr) FROM prices_packages WHERE is_available = true) as max_package_price
            """)
            return summary or {}
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {}


# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================

def render_health_indicator():
    """
    Render small health indicator di sidebar atau header.
    Shows: 🟢 Live | 🟡 Delayed | 🔴 Error
    """
    try:
        monitor = PriceMonitor()
        status = monitor.get_health_status()
        
        overall = status.get('overall', 'unknown')
        
        if overall == 'healthy':
            st.success("🟢 Harga Live")
        elif overall == 'warning' or overall == 'degraded':
            st.warning("🟡 Data Tertunda")
        elif overall == 'critical':
            st.error("🔴 Sistem Error")
        else:
            st.info("⚪ Status Unknown")
        
        # Show last update time
        packages = status.get('packages', {})
        if packages.get('last_update'):
            last_update = packages['last_update']
            if isinstance(last_update, datetime):
                # Convert to WIB (UTC+7)
                wib_time = last_update + timedelta(hours=7)
                st.caption(f"Update: {wib_time.strftime('%d %b %H:%M')} WIB")
    except Exception:
        st.caption("📊 Mode offline")


def render_monitoring_dashboard():
    """
    Render full monitoring dashboard untuk admin.
    """
    st.markdown("## 🔍 Price Intelligence Monitoring")
    
    try:
        monitor = PriceMonitor()
        status = monitor.get_health_status()
        
        # Overall Status
        overall = status.get('overall', 'unknown')
        status_colors = {
            'healthy': ('🟢', 'success', 'Semua sistem berjalan normal'),
            'warning': ('🟡', 'warning', 'Ada keterlambatan update'),
            'degraded': ('🟠', 'warning', 'Beberapa komponen bermasalah'),
            'critical': ('🔴', 'error', 'Sistem mengalami error'),
            'unknown': ('⚪', 'info', 'Status tidak diketahui')
        }
        
        icon, msg_type, msg = status_colors.get(overall, status_colors['unknown'])
        
        if msg_type == 'success':
            st.success(f"{icon} **Status: HEALTHY** - {msg}")
        elif msg_type == 'warning':
            st.warning(f"{icon} **Status: WARNING** - {msg}")
        elif msg_type == 'error':
            st.error(f"{icon} **Status: CRITICAL** - {msg}")
        else:
            st.info(f"{icon} **Status: UNKNOWN** - {msg}")
        
        st.markdown("---")
        
        # Component Status
        st.markdown("### 📊 Status Komponen")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            db_status = status.get('database', 'unknown')
            db_icon = "🟢" if db_status == 'connected' else "🔴"
            st.metric("Database", f"{db_icon} {db_status.title()}")
        
        with col2:
            n8n_status = status.get('n8n_workflow', 'unknown')
            n8n_icon = "🟢" if n8n_status == 'running' else ("🟡" if n8n_status == 'delayed' else "🔴")
            st.metric("n8n Workflow", f"{n8n_icon} {n8n_status.title()}")
        
        with col3:
            pkg = status.get('packages', {})
            pkg_icon = "🟢" if pkg.get('status') == 'fresh' else "🟡"
            st.metric("Packages", f"{pkg_icon} {pkg.get('count', 0)}")
        
        with col4:
            hotel = status.get('hotels', {})
            hotel_icon = "🟢" if hotel.get('status') == 'fresh' else "🟡"
            st.metric("Hotels", f"{hotel_icon} {hotel.get('count', 0)}")
        
        st.markdown("---")
        
        # Data Summary
        st.markdown("### 📈 Ringkasan Data")
        
        summary = monitor.get_data_summary()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Paket", summary.get('total_packages', 0))
            if summary.get('min_package_price'):
                min_price = float(summary['min_package_price'])
                st.caption(f"Termurah: Rp {min_price:,.0f}")
        
        with col2:
            st.metric("Total Hotel", summary.get('total_hotels', 0))
            st.caption("Makkah & Madinah")
        
        with col3:
            st.metric("Total Penerbangan", summary.get('total_flights', 0))
            st.caption("Upcoming flights")
        
        st.markdown("---")
        
        # Update History (Audit Trail)
        st.markdown("### 📅 History Update (7 Hari)")
        
        history = monitor.get_update_history(days=7)
        
        if history:
            for record in history:
                date = record.get('date')
                count = record.get('update_count', 0)
                last = record.get('last_update')
                
                if isinstance(date, datetime):
                    date_str = date.strftime('%d %b %Y')
                else:
                    date_str = str(date)
                
                if isinstance(last, datetime):
                    last_str = last.strftime('%H:%M')
                else:
                    last_str = str(last)[:5] if last else '-'
                
                # Show as expandable
                with st.expander(f"📅 {date_str} - {count} updates"):
                    st.write(f"Update terakhir: {last_str} UTC")
                    st.write(f"Jumlah batch: {count}")
        else:
            st.info("Belum ada history update")
        
        # Issues
        if status.get('issues'):
            st.markdown("---")
            st.markdown("### ⚠️ Issues Terdeteksi")
            for issue in status['issues']:
                st.warning(issue)
        
    except Exception as e:
        st.error(f"Gagal memuat monitoring: {e}")
        st.info("Pastikan database terhubung dengan benar")


def render_last_update_badge():
    """
    Render badge kecil yang menunjukkan kapan data terakhir diupdate.
    Untuk ditampilkan di halaman manapun.
    """
    try:
        monitor = PriceMonitor()
        status = monitor.get_health_status()
        
        # Get most recent update
        latest = None
        for key in ['packages', 'hotels', 'flights']:
            comp = status.get(key, {})
            update_time = comp.get('last_update')
            if update_time:
                if not latest or update_time > latest:
                    latest = update_time
        
        if latest:
            # Convert to WIB
            if isinstance(latest, datetime):
                wib_time = latest + timedelta(hours=7)
                time_str = wib_time.strftime('%d %b %Y, %H:%M WIB')
                
                # Calculate hours ago
                hours_ago = (datetime.utcnow() - latest.replace(tzinfo=None)).total_seconds() / 3600
                
                if hours_ago < 1:
                    freshness = "🟢 Baru saja"
                elif hours_ago < 7:
                    freshness = f"🟢 {hours_ago:.0f} jam lalu"
                elif hours_ago < 24:
                    freshness = f"🟡 {hours_ago:.0f} jam lalu"
                else:
                    freshness = f"🔴 {hours_ago/24:.0f} hari lalu"
                
                st.caption(f"📊 Data: {freshness} | {time_str}")
        else:
            st.caption("📊 Data belum tersedia")
    except Exception:
        pass  # Silent fail


# =============================================================================
# CACHED FUNCTIONS
# =============================================================================

@st.cache_data(ttl=60)  # Cache 1 menit untuk monitoring
def get_cached_health_status() -> Dict:
    """Get cached health status."""
    monitor = PriceMonitor()
    return monitor.get_health_status()
