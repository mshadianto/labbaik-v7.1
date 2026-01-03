"""
LABBAIK Smart Planner - Analytics Dashboard
============================================
Admin-only dashboard for user engagement metrics.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import plotly for charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def render_analytics_dashboard():
    """Render comprehensive analytics dashboard (admin only)."""

    # Check admin access
    user = st.session_state.get('user')
    if not user or user.get('role') != 'admin':
        st.error("Akses ditolak. Halaman ini hanya untuk Admin.")
        st.info("Silakan login dengan akun admin untuk melihat dashboard analytics.")
        return

    st.title("📊 LABBAIK Analytics Dashboard")
    st.caption("Real-time user engagement & feature performance metrics")

    # Get database connection
    try:
        from services.database.repository import get_db
        db = get_db()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return

    if not db:
        st.warning("Database tidak tersedia. Analytics membutuhkan koneksi database.")
        return

    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input(
            "Dari",
            value=datetime.now() - timedelta(days=7),
            key="analytics_start"
        )
    with col2:
        end_date = st.date_input(
            "Sampai",
            value=datetime.now(),
            key="analytics_end"
        )
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.divider()

    # Tabs for different analytics sections
    tabs = st.tabs([
        "📈 Overview",
        "🎯 Smart Pillars",
        "💎 Smart Savings",
        "👥 User Behavior",
        "🔄 Conversions"
    ])

    # TAB 1: Overview
    with tabs[0]:
        render_overview_metrics(db, start_date, end_date)

    # TAB 2: Pillar Analytics
    with tabs[1]:
        render_pillar_analytics(db, start_date, end_date)

    # TAB 3: Smart Savings Performance
    with tabs[2]:
        render_smart_savings_analytics(db, start_date, end_date)

    # TAB 4: User Behavior
    with tabs[3]:
        render_user_behavior(db, start_date, end_date)

    # TAB 5: Conversion Funnel
    with tabs[4]:
        render_conversion_metrics(db, start_date, end_date)


def render_overview_metrics(db, start_date, end_date):
    """Overview KPIs."""
    st.subheader("📊 Key Metrics")

    try:
        # Try to get data from analytics_events table
        query = """
        SELECT
            COUNT(DISTINCT COALESCE(user_id::text, session_id)) as total_users,
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(*) as total_events
        FROM analytics_events
        WHERE event_timestamp::date BETWEEN %s AND %s
        """
        metrics = db.fetch_one(query, (start_date, end_date))

        if not metrics or metrics.get('total_events', 0) == 0:
            # Fallback to visitor_stats
            query = """
            SELECT
                COALESCE(SUM(unique_visitors), 0) as total_users,
                COALESCE(SUM(page_views), 0) as total_events
            FROM visitor_stats
            WHERE date BETWEEN %s AND %s
            """
            metrics = db.fetch_one(query, (start_date, end_date)) or {}
            metrics['total_sessions'] = metrics.get('total_users', 0)

    except Exception as e:
        logger.warning(f"Could not fetch analytics: {e}")
        # Use visitor_stats as fallback
        try:
            query = """
            SELECT
                COALESCE(SUM(unique_visitors), 0) as total_users,
                COALESCE(SUM(page_views), 0) as total_events
            FROM visitor_stats
            WHERE date BETWEEN %s AND %s
            """
            metrics = db.fetch_one(query, (start_date, end_date)) or {}
            metrics['total_sessions'] = metrics.get('total_users', 0)
        except:
            metrics = {'total_users': 0, 'total_sessions': 0, 'total_events': 0}

    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Users",
            f"{metrics.get('total_users', 0):,}",
            help="Unique users dalam periode terpilih"
        )

    with col2:
        st.metric(
            "Total Sessions",
            f"{metrics.get('total_sessions', 0):,}",
            help="Jumlah sesi pengguna"
        )

    with col3:
        st.metric(
            "Total Events",
            f"{metrics.get('total_events', 0):,}",
            help="Semua event yang tercatat"
        )

    with col4:
        # Calculate engagement rate
        users = metrics.get('total_users', 0) or 1
        events = metrics.get('total_events', 0)
        engagement = round(events / users, 1)
        st.metric(
            "Events/User",
            f"{engagement}",
            help="Rata-rata events per user"
        )

    st.divider()

    # Daily trend chart
    st.subheader("📈 Daily Active Users Trend")

    try:
        query = """
        SELECT
            date,
            COALESCE(SUM(unique_visitors), 0) as dau,
            COALESCE(SUM(page_views), 0) as views
        FROM visitor_stats
        WHERE date BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date
        """
        df = pd.DataFrame(db.fetch_all(query, (start_date, end_date)) or [])

        if not df.empty and HAS_PLOTLY:
            fig = px.line(
                df, x='date', y='dau',
                title="Daily Active Users",
                labels={'dau': 'Users', 'date': 'Tanggal'}
            )
            fig.update_traces(line_color='#d4af37')
            st.plotly_chart(fig, use_container_width=True)
        elif not df.empty:
            st.line_chart(df.set_index('date')['dau'])
        else:
            st.info("Belum ada data untuk periode ini.")

    except Exception as e:
        st.warning(f"Tidak dapat memuat trend: {e}")


def render_pillar_analytics(db, start_date, end_date):
    """Pillar navigation analytics."""
    st.subheader("🎯 Smart Pillar Performance")

    # Define pillar mappings
    pillar_pages = {
        'Smart Prep': ['checklist', 'smart_checklist', 'umrah_mandiri', 'manasik'],
        'Smart Savings': ['simulator', 'umrah_bareng', 'price_comparison', 'booking'],
        'Smart Journey': ['chat', 'crowd', 'doa', 'tracking', 'sos']
    }

    try:
        query = """
        SELECT
            page,
            COALESCE(SUM(page_views), 0) as views,
            COALESCE(SUM(unique_visitors), 0) as unique_users
        FROM visitor_stats
        WHERE date BETWEEN %s AND %s
        GROUP BY page
        ORDER BY views DESC
        """
        df = pd.DataFrame(db.fetch_all(query, (start_date, end_date)) or [])

        if df.empty:
            st.info("Belum ada data navigasi untuk periode ini.")
            return

        # Map pages to pillars
        def get_pillar(page):
            for pillar, pages in pillar_pages.items():
                if page in pages:
                    return pillar
            return 'Other'

        df['pillar'] = df['page'].apply(get_pillar)

        # Aggregate by pillar
        pillar_stats = df.groupby('pillar').agg({
            'views': 'sum',
            'unique_users': 'sum'
        }).reset_index()

        # Filter out 'Other' if empty
        pillar_stats = pillar_stats[pillar_stats['pillar'] != 'Other']

        col1, col2 = st.columns(2)

        with col1:
            if HAS_PLOTLY and not pillar_stats.empty:
                fig = px.pie(
                    pillar_stats,
                    values='views',
                    names='pillar',
                    title="Page Views by Pillar",
                    color_discrete_sequence=['#d4af37', '#4ade80', '#60a5fa']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(pillar_stats, use_container_width=True)

        with col2:
            if HAS_PLOTLY and not df.empty:
                top_pages = df.head(8)
                fig = px.bar(
                    top_pages,
                    x='page',
                    y='views',
                    title="Top Pages by Views",
                    color='views',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(df.head(8), use_container_width=True)

        # Detailed table
        st.subheader("📋 Detail per Halaman")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.warning(f"Tidak dapat memuat data pillar: {e}")


def render_smart_savings_analytics(db, start_date, end_date):
    """Smart Savings & Nudge performance."""
    st.subheader("💎 Smart Savings Performance")

    try:
        # Try to get nudge stats from analytics_events
        query = """
        SELECT
            COUNT(*) FILTER (WHERE event_action = 'nudge_displayed') as nudge_shows,
            COUNT(*) FILTER (WHERE event_action = 'nudge_clicked') as nudge_clicks
        FROM analytics_events
        WHERE event_category = 'smart_savings'
            AND event_timestamp::date BETWEEN %s AND %s
        """
        stats = db.fetch_one(query, (start_date, end_date))

        if stats and (stats.get('nudge_shows', 0) > 0 or stats.get('nudge_clicks', 0) > 0):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Nudge Ditampilkan", f"{stats.get('nudge_shows', 0):,}")

            with col2:
                st.metric("Nudge Diklik", f"{stats.get('nudge_clicks', 0):,}")

            with col3:
                shows = stats.get('nudge_shows', 0) or 1
                clicks = stats.get('nudge_clicks', 0)
                ctr = round((clicks / shows) * 100, 1)
                st.metric("Click-Through Rate", f"{ctr}%")

            # Funnel visualization
            if HAS_PLOTLY:
                st.subheader("🔄 Smart Savings Funnel")

                funnel_data = {
                    'Step': ['Nudge Shown', 'Nudge Clicked', 'Umrah Bareng Page', 'Match Completed'],
                    'Count': [
                        stats.get('nudge_shows', 0),
                        stats.get('nudge_clicks', 0),
                        int(stats.get('nudge_clicks', 0) * 0.7),  # Estimated
                        int(stats.get('nudge_clicks', 0) * 0.2),  # Estimated
                    ]
                }

                fig = go.Figure(go.Funnel(
                    y=funnel_data['Step'],
                    x=funnel_data['Count'],
                    textinfo="value+percent initial"
                ))
                fig.update_layout(title="Conversion Funnel")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data smart nudge. Data akan muncul setelah pengguna melihat Budget Optimizer.")

            # Show Budget Optimizer usage instead
            query = """
            SELECT
                COALESCE(SUM(page_views), 0) as views,
                COALESCE(SUM(unique_visitors), 0) as users
            FROM visitor_stats
            WHERE page = 'simulator'
                AND date BETWEEN %s AND %s
            """
            simulator_stats = db.fetch_one(query, (start_date, end_date))

            if simulator_stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Budget Optimizer Views", f"{simulator_stats.get('views', 0):,}")
                with col2:
                    st.metric("Unique Users", f"{simulator_stats.get('users', 0):,}")

    except Exception as e:
        st.warning(f"Tidak dapat memuat data Smart Savings: {e}")
        logger.error(f"Smart Savings analytics error: {e}")


def render_user_behavior(db, start_date, end_date):
    """User behavior patterns."""
    st.subheader("👥 User Behavior Patterns")

    try:
        # Popular pages
        query = """
        SELECT
            page,
            SUM(page_views) as views,
            SUM(unique_visitors) as users
        FROM visitor_stats
        WHERE date BETWEEN %s AND %s
        GROUP BY page
        ORDER BY views DESC
        LIMIT 10
        """
        df = pd.DataFrame(db.fetch_all(query, (start_date, end_date)) or [])

        if not df.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🔥 Top 10 Pages**")
                st.dataframe(df, use_container_width=True)

            with col2:
                if HAS_PLOTLY:
                    fig = px.bar(
                        df,
                        x='views',
                        y='page',
                        orientation='h',
                        title="Page Views Distribution",
                        color='views',
                        color_continuous_scale='Oranges'
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # Session stats
        st.divider()
        st.markdown("**📊 Session Metrics**")

        try:
            query = """
            SELECT
                AVG(page_count) as avg_pages,
                AVG(duration_seconds) as avg_duration,
                COUNT(*) as total_sessions
            FROM visitor_sessions
            WHERE last_activity::date BETWEEN %s AND %s
            """
            sessions = db.fetch_one(query, (start_date, end_date))

            if sessions and sessions.get('total_sessions', 0) > 0:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Sessions", f"{sessions.get('total_sessions', 0):,}")

                with col2:
                    avg_pages = round(sessions.get('avg_pages', 0) or 0, 1)
                    st.metric("Avg Pages/Session", f"{avg_pages}")

                with col3:
                    duration = int(sessions.get('avg_duration', 0) or 0)
                    mins = duration // 60
                    secs = duration % 60
                    st.metric("Avg Duration", f"{mins}m {secs}s")
            else:
                st.info("Belum ada data sesi untuk periode ini.")

        except Exception as e:
            logger.debug(f"Session stats error: {e}")

    except Exception as e:
        st.warning(f"Tidak dapat memuat user behavior: {e}")


def render_conversion_metrics(db, start_date, end_date):
    """Conversion metrics."""
    st.subheader("🎯 Conversion Metrics")

    try:
        # Get user counts
        query = """
        SELECT
            COUNT(DISTINCT id) as total_users,
            COUNT(DISTINCT CASE WHEN role = 'premium' THEN id END) as premium_users,
            COUNT(DISTINCT CASE WHEN role = 'free' THEN id END) as free_users
        FROM users
        WHERE created_at::date BETWEEN %s AND %s
        """
        users = db.fetch_one(query, (start_date, end_date))

        if users:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("New Users", f"{users.get('total_users', 0):,}")

            with col2:
                st.metric("Free Users", f"{users.get('free_users', 0):,}")

            with col3:
                total = users.get('total_users', 0) or 1
                premium = users.get('premium_users', 0)
                rate = round((premium / total) * 100, 1)
                st.metric(
                    "Premium Users",
                    f"{premium}",
                    f"{rate}% conversion"
                )

        # Conversion events
        st.divider()
        st.markdown("**📈 Conversion Events**")

        try:
            query = """
            SELECT
                event_action as conversion_type,
                COUNT(*) as count
            FROM analytics_events
            WHERE event_type = 'conversion'
                AND event_timestamp::date BETWEEN %s AND %s
            GROUP BY event_action
            ORDER BY count DESC
            """
            conversions = db.fetch_all(query, (start_date, end_date))

            if conversions:
                df = pd.DataFrame(conversions)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Belum ada conversion events tercatat.")

        except Exception as e:
            logger.debug(f"Conversion events error: {e}")
            st.info("Tabel analytics_events belum tersedia. Jalankan migration schema.")

    except Exception as e:
        st.warning(f"Tidak dapat memuat conversion metrics: {e}")


# Export
__all__ = ["render_analytics_dashboard"]
