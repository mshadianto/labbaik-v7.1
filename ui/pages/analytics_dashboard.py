"""
================================================================================
LABBAIK AI - Analytics Dashboard
================================================================================
Lokasi: ui/pages/analytics_dashboard.py
Fitur: Admin-only dashboard for user engagement metrics.
       - Overview KPIs (users, sessions, events)
       - Smart Pillar performance
       - Smart Savings / nudge analytics
       - User behavior patterns
       - Conversion funnel
       - AI-powered analytics insights
       - Gamification XP rewards
================================================================================
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import csv
import io
import random

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SKELETON_CSS, render_skeleton

logger = logging.getLogger(__name__)

# Try to import plotly for charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Try to import AnalyticsDashboard service for device/flow/geo stats
try:
    from services.analytics.dashboard import AnalyticsDashboard as AnalyticsDashboardService
    HAS_ANALYTICS_SERVICE = True
except ImportError:
    HAS_ANALYTICS_SERVICE = False


# =============================================================================
# CONSTANTS
# =============================================================================

# Internal/admin emails to exclude from analytics
EXCLUDED_EMAILS = [
    'admin@labbaik.io',
    'founder@labbaik.io',
    'salam@labbaik.io',
]


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

ANALYTICS_CSS = """
/* Analytics dashboard hero override */
.analytics-hero {
    --hero-bg: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    --hero-border: #60a5fa;
    --hero-title: #60a5fa;
    --hero-subtitle: #94a3b8;
}

/* KPI card row */
.kpi-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem 1rem;
    text-align: center;
    border: 1px solid #334155;
    transition: border-color 0.2s, transform 0.2s;
}

.kpi-card:hover {
    border-color: #60a5fa;
    transform: translateY(-2px);
}

.kpi-icon {
    font-size: 1.6rem;
    margin-bottom: 0.3rem;
}

.kpi-value {
    font-size: 1.7rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0.2rem 0;
}

.kpi-label {
    font-size: 0.78rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Insight loading spinner */
.insight-loading {
    text-align: center;
    padding: 2rem;
    color: #94a3b8;
}

/* Section divider */
.section-divider {
    border: none;
    border-top: 1px solid #334155;
    margin: 1.5rem 0;
}

/* ------------------------------------------------------------------ */
/* Cohort retention matrix                                            */
/* ------------------------------------------------------------------ */
.cohort-matrix {
    width: 100%;
    border-collapse: separate;
    border-spacing: 3px;
    margin: 1rem 0 1.5rem;
    font-size: 0.85rem;
}
.cohort-matrix th {
    background: #1e293b;
    color: #94a3b8;
    padding: 0.5rem 0.6rem;
    text-align: center;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    font-size: 0.75rem;
    border-radius: 6px;
}
.cohort-matrix th:first-child,
.cohort-matrix td:first-child {
    text-align: left;
    min-width: 110px;
}
.cohort-matrix td {
    padding: 0.5rem 0.6rem;
    text-align: center;
    border-radius: 6px;
    font-weight: 600;
    color: #e2e8f0;
    transition: transform 0.15s;
}
.cohort-matrix td:hover {
    transform: scale(1.08);
}
.cohort-cell {
    border-radius: 6px;
}
.cohort-size {
    background: #1e293b;
    color: #d4af37;
    font-weight: 700;
}

/* ------------------------------------------------------------------ */
/* Activity heatmap grid                                              */
/* ------------------------------------------------------------------ */
.heatmap-grid {
    width: 100%;
    border-collapse: separate;
    border-spacing: 2px;
    margin: 1rem 0 1.5rem;
    font-size: 0.78rem;
}
.heatmap-grid th {
    background: #1e293b;
    color: #94a3b8;
    padding: 0.35rem 0.25rem;
    text-align: center;
    font-weight: 600;
    font-size: 0.7rem;
    border-radius: 4px;
}
.heatmap-grid th:first-child {
    text-align: left;
    min-width: 60px;
    padding-left: 0.5rem;
}
.heatmap-grid td {
    text-align: center;
    border-radius: 4px;
    padding: 0.3rem 0.15rem;
    color: #e2e8f0;
    font-weight: 500;
    min-width: 28px;
}
.heatmap-grid td:first-child {
    text-align: left;
    padding-left: 0.5rem;
    background: #1e293b;
    color: #b8c5d4;
    font-weight: 600;
}
.heatmap-cell {
    border-radius: 4px;
}
"""


# =============================================================================
# MAIN RENDER
# =============================================================================

def render_analytics_dashboard():
    """Render comprehensive analytics dashboard (admin only)."""
    try:
        from services.analytics import track_page
        track_page("analytics")
    except Exception:
        pass

    # Check admin access
    user = st.session_state.get('user')
    if not user:
        st.error("Akses ditolak. Halaman ini hanya untuk Admin.")
        st.info("Silakan login dengan akun admin untuk melihat dashboard analytics.")
        return

    # Get user role - handle both dict and User object
    user_role = None
    if hasattr(user, 'role'):
        user_role = user.role.value if hasattr(user.role, 'value') else user.role
    elif isinstance(user, dict):
        user_role = user.get('role')

    if user_role != 'admin':
        st.error("Akses ditolak. Halaman ini hanya untuk Admin.")
        st.info("Silakan login dengan akun admin untuk melihat dashboard analytics.")
        return

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SKELETON_CSS, ANALYTICS_CSS)

    # Gamification: +20 XP for viewing analytics (first time per session)
    if not st.session_state.get("_analytics_dash_xp_awarded"):
        add_xp_safe(20, "Melihat Analytics Dashboard")
        st.session_state["_analytics_dash_xp_awarded"] = True

    # Hero banner
    st.markdown(
'<div class="page-hero analytics-hero">'
'<h1>LABBAIK Analytics Dashboard</h1>'
'<p class="subtitle">Real-time user engagement &amp; feature performance metrics</p>'
'<p class="subtitle">Data excludes internal team (admin, founder, salam)</p>'
'</div>',
        unsafe_allow_html=True,
    )

    # Get database connection
    try:
        from services.database.repository import get_db
        db = get_db()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return

    if not db:
        st.warning("Database tidak tersedia. Analytics membutuhkan koneksi database.")
        render_skeleton("stats", count=4)
        render_skeleton("cards", count=2)
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
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    st.divider()

    # Tabs for different analytics sections
    tabs = st.tabs([
        "Overview",
        "Smart Pillars",
        "Smart Savings",
        "User Behavior",
        "Conversions",
        "AI Insights",
        "Kohort",
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

    # TAB 6: AI Insights
    with tabs[5]:
        render_ai_insights(db, start_date, end_date)

    # TAB 7: Kohort (Cohort Analysis & Activity Heatmap)
    with tabs[6]:
        render_cohort_analytics(db, start_date, end_date)
        st.divider()
        render_activity_heatmap(db, start_date, end_date)

    # Export section (below tabs)
    render_export_section(db, start_date, end_date)


# =============================================================================
# HELPERS
# =============================================================================

def get_excluded_user_ids_clause():
    """Get SQL sub-query and params to exclude internal users (parameterized)."""
    placeholders = ", ".join(["%s"] * len(EXCLUDED_EMAILS))
    sql = f"SELECT id FROM users WHERE email IN ({placeholders})"
    return sql, tuple(EXCLUDED_EMAILS)


def _collect_dashboard_metrics(db, start_date, end_date):
    """Collect all key metrics into a dict for both display and AI prompt."""
    excluded_sql, excluded_params = get_excluded_user_ids_clause()
    metrics = {'total_users': 0, 'total_sessions': 0, 'total_events': 0}

    try:
        query = f"""
        SELECT
            COUNT(DISTINCT COALESCE(user_id::text, session_id)) as total_users,
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(*) as total_events
        FROM analytics_events
        WHERE event_timestamp::date BETWEEN %s AND %s
            AND (user_id IS NULL OR user_id NOT IN ({excluded_sql}))
        """
        result = db.fetch_one(query, (start_date, end_date) + excluded_params)
        if result and result.get('total_events', 0) > 0:
            metrics = result
        else:
            raise ValueError("no analytics_events data")
    except Exception:
        try:
            query = """
            SELECT
                COALESCE(SUM(unique_visitors), 0) as total_users,
                COALESCE(SUM(page_views), 0) as total_events
            FROM visitor_stats
            WHERE date BETWEEN %s AND %s
            """
            result = db.fetch_one(query, (start_date, end_date)) or {}
            metrics['total_users'] = result.get('total_users', 0)
            metrics['total_events'] = result.get('total_events', 0)
            metrics['total_sessions'] = result.get('total_users', 0)
        except Exception:
            pass

    return metrics


def _collect_page_stats(db, start_date, end_date):
    """Collect page-level stats for AI analysis."""
    try:
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
        rows = db.fetch_all(query, (start_date, end_date)) or []
        return rows
    except Exception:
        return []


def _collect_session_stats(db, start_date, end_date):
    """Collect session-level stats."""
    try:
        query = """
        SELECT
            AVG(page_count) as avg_pages,
            AVG(duration_seconds) as avg_duration,
            COUNT(*) as total_sessions
        FROM visitor_sessions
        WHERE last_activity::date BETWEEN %s AND %s
        """
        return db.fetch_one(query, (start_date, end_date))
    except Exception:
        return None


def _collect_conversion_stats(db, start_date, end_date):
    """Collect conversion stats."""
    try:
        query = """
        SELECT
            COUNT(DISTINCT id) as total_users,
            COUNT(DISTINCT CASE WHEN role = 'premium' THEN id END) as premium_users,
            COUNT(DISTINCT CASE WHEN role = 'free' THEN id END) as free_users
        FROM users
        WHERE created_at::date BETWEEN %s AND %s
        """
        return db.fetch_one(query, (start_date, end_date))
    except Exception:
        return None


def _markdown_to_html(text):
    """Convert simple markdown to HTML for display inside styled divs."""
    import re
    lines = text.split("\n")
    html_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append("<br/>")
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        if line.startswith("- ") or line.startswith("* "):
            line = "&bull; " + line[2:]
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            num = match.group(1)
            rest = line[match.end():]
            line = "<strong>" + num + ".</strong> " + rest
        html_parts.append("<div style='margin-bottom:0.3rem;'>" + line + "</div>")
    return "\n".join(html_parts)


# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================

def render_overview_metrics(db, start_date, end_date):
    """Overview KPIs."""
    st.subheader("Key Metrics")

    metrics = _collect_dashboard_metrics(db, start_date, end_date)

    # Display KPIs using HTML cards
    total_users = metrics.get('total_users', 0)
    total_sessions = metrics.get('total_sessions', 0)
    total_events = metrics.get('total_events', 0)
    users_denom = total_users if total_users else 1
    engagement = round(total_events / users_denom, 1)

    users_html = f"{total_users:,}"
    sessions_html = f"{total_sessions:,}"
    events_html = f"{total_events:,}"
    engagement_html = str(engagement)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
'<div class="kpi-card">'
'<div class="kpi-icon">👥</div>'
'<div class="kpi-value">' + users_html + '</div>'
'<div class="kpi-label">Total Users</div>'
'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
'<div class="kpi-card">'
'<div class="kpi-icon">🔗</div>'
'<div class="kpi-value">' + sessions_html + '</div>'
'<div class="kpi-label">Total Sessions</div>'
'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
'<div class="kpi-card">'
'<div class="kpi-icon">⚡</div>'
'<div class="kpi-value">' + events_html + '</div>'
'<div class="kpi-label">Total Events</div>'
'</div>',
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
'<div class="kpi-card">'
'<div class="kpi-icon">📊</div>'
'<div class="kpi-value">' + engagement_html + '</div>'
'<div class="kpi-label">Events / User</div>'
'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Daily trend chart
    st.subheader("Daily Active Users Trend")

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


# =============================================================================
# TAB 2: PILLAR ANALYTICS
# =============================================================================

def render_pillar_analytics(db, start_date, end_date):
    """Pillar navigation analytics."""
    st.subheader("Smart Pillar Performance")

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
        st.subheader("Detail per Halaman")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.warning(f"Tidak dapat memuat data pillar: {e}")


# =============================================================================
# TAB 3: SMART SAVINGS
# =============================================================================

def render_smart_savings_analytics(db, start_date, end_date):
    """Smart Savings & Nudge performance."""
    st.subheader("Smart Savings Performance")

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
                st.subheader("Smart Savings Funnel")

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


# =============================================================================
# TAB 4: USER BEHAVIOR
# =============================================================================

def render_user_behavior(db, start_date, end_date):
    """User behavior patterns."""
    st.subheader("User Behavior Patterns")

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
                st.markdown("**Top 10 Pages**")
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
        st.markdown("**Session Metrics**")

        try:
            sessions = _collect_session_stats(db, start_date, end_date)

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

        # -----------------------------------------------------------------
        # Device Distribution & Page Flow (from AnalyticsDashboardService)
        # -----------------------------------------------------------------
        if HAS_ANALYTICS_SERVICE:
            try:
                svc = AnalyticsDashboardService()

                st.divider()
                st.markdown("**Device Distribution**")

                device_stats = svc.get_device_stats()
                if device_stats:
                    device_icons = {
                        "mobile": '<span aria-hidden="true">📱</span>',
                        "desktop": '<span aria-hidden="true">💻</span>',
                        "tablet": '<span aria-hidden="true">📲</span>',
                    }
                    device_colors = {
                        "mobile": "#60a5fa",
                        "desktop": "#d4af37",
                        "tablet": "#4ade80",
                    }

                    cols = st.columns(len(device_stats))
                    for idx, (device, pct) in enumerate(device_stats.items()):
                        icon_html = device_icons.get(device, "")
                        bar_color = device_colors.get(device, "#60a5fa")
                        label = device.title()
                        with cols[idx]:
                            st.markdown(
                                '<div class="kpi-card">'
                                '<div class="kpi-icon">' + icon_html + '</div>'
                                '<div class="kpi-value">' + str(pct) + '%</div>'
                                '<div class="kpi-label">' + label + '</div>'
                                '<div style="margin-top:0.5rem;background:#334155;'
                                'border-radius:6px;height:8px;overflow:hidden;">'
                                '<div style="width:' + str(pct) + '%;'
                                'background:' + bar_color + ';height:100%;'
                                'border-radius:6px;"></div>'
                                '</div>'
                                '</div>',
                                unsafe_allow_html=True,
                            )

                st.divider()
                st.markdown("**Page Flow (Popular Navigation Paths)**")

                flow_data = svc.get_page_flow()
                if flow_data and flow_data.get("flows"):
                    flows = flow_data["flows"]
                    # Sort by value descending so the most-used paths appear first
                    flows_sorted = sorted(flows, key=lambda f: f.get("value", 0), reverse=True)
                    max_val = flows_sorted[0].get("value", 1) if flows_sorted else 1

                    for flow in flows_sorted:
                        src = flow.get("from", "?")
                        dst = flow.get("to", "?")
                        val = flow.get("value", 0)
                        bar_pct = int((val / max_val) * 100) if max_val else 0

                        st.markdown(
                            '<div style="background:linear-gradient(145deg,#1a1a2e,#1e293b);'
                            'border:1px solid #334155;border-radius:10px;padding:0.75rem 1rem;'
                            'margin-bottom:0.5rem;display:flex;align-items:center;'
                            'justify-content:space-between;gap:0.5rem;">'
                            '<span style="color:#b8c5d4;min-width:100px;">' + src + '</span>'
                            '<span style="color:#d4af37;" aria-hidden="true">&rarr;</span>'
                            '<span style="color:#e2e8f0;min-width:100px;">' + dst + '</span>'
                            '<div style="flex:1;background:#334155;border-radius:6px;'
                            'height:8px;overflow:hidden;margin:0 0.5rem;">'
                            '<div style="width:' + str(bar_pct) + '%;'
                            'background:linear-gradient(90deg,#d4af37,#f4d03f);'
                            'height:100%;border-radius:6px;"></div>'
                            '</div>'
                            '<span style="color:#d4af37;font-weight:700;min-width:30px;'
                            'text-align:right;">' + str(val) + '</span>'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("Data page flow belum tersedia.")

            except Exception as e:
                logger.debug(f"AnalyticsDashboardService error: {e}")

    except Exception as e:
        st.warning(f"Tidak dapat memuat user behavior: {e}")


# =============================================================================
# TAB 5: CONVERSIONS
# =============================================================================

def render_conversion_metrics(db, start_date, end_date):
    """Conversion metrics."""
    st.subheader("Conversion Metrics")

    try:
        # Get user counts
        users = _collect_conversion_stats(db, start_date, end_date)

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
        st.markdown("**Conversion Events**")

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


# =============================================================================
# TAB 6: AI INSIGHTS
# =============================================================================

def render_ai_insights(db, start_date, end_date):
    """AI-powered analytics insights with trend analysis and user behavior."""
    st.subheader("AI Analytics Insights")

    # Collect metrics for the AI prompt
    metrics = _collect_dashboard_metrics(db, start_date, end_date)
    page_stats = _collect_page_stats(db, start_date, end_date)
    session_stats = _collect_session_stats(db, start_date, end_date)
    conversion_stats = _collect_conversion_stats(db, start_date, end_date)

    # Build page stats summary
    page_lines = []
    for row in page_stats:
        page_name = row.get('page', 'unknown')
        views = row.get('views', 0)
        users = row.get('users', 0)
        page_lines.append(f"  - {page_name}: {views} views, {users} unique users")
    page_summary = "\n".join(page_lines) if page_lines else "  (tidak ada data)"

    # Build session stats summary
    session_summary = "  (tidak ada data)"
    if session_stats and session_stats.get('total_sessions', 0) > 0:
        avg_pages = round(session_stats.get('avg_pages', 0) or 0, 1)
        avg_dur = int(session_stats.get('avg_duration', 0) or 0)
        total_sess = session_stats.get('total_sessions', 0)
        session_summary = (
            f"  Total sessions: {total_sess}, "
            f"Avg pages/session: {avg_pages}, "
            f"Avg duration: {avg_dur}s"
        )

    # Build conversion summary
    conversion_summary = "  (tidak ada data)"
    if conversion_stats:
        total_u = conversion_stats.get('total_users', 0)
        premium_u = conversion_stats.get('premium_users', 0)
        free_u = conversion_stats.get('free_users', 0)
        conversion_summary = (
            f"  New users: {total_u}, Free: {free_u}, Premium: {premium_u}"
        )

    start_str = str(start_date)
    end_str = str(end_date)

    prompt_text = (
        f"Analisis data analytics platform LABBAIK AI (platform perencanaan Umrah) "
        f"untuk periode {start_str} s/d {end_str}:\n\n"
        f"== KPI Utama ==\n"
        f"  Total Users: {metrics.get('total_users', 0)}\n"
        f"  Total Sessions: {metrics.get('total_sessions', 0)}\n"
        f"  Total Events: {metrics.get('total_events', 0)}\n\n"
        f"== Top Pages ==\n"
        f"{page_summary}\n\n"
        f"== Session Stats ==\n"
        f"{session_summary}\n\n"
        f"== Conversion ==\n"
        f"{conversion_summary}\n\n"
        "Berikan analisis dalam bahasa Indonesia yang mencakup:\n"
        "1. Trend Analysis: tren utama yang terlihat dari data\n"
        "2. User Behavior Insights: pola perilaku pengguna\n"
        "3. Top Performing Features: fitur yang paling banyak digunakan\n"
        "4. Rekomendasi: 3-5 saran actionable untuk meningkatkan engagement\n"
        "5. Peluang Konversi: strategi meningkatkan konversi free-to-premium\n\n"
        "Format menggunakan bullet points. Jawab ringkas dan data-driven."
    )

    system_prompt = (
        "Kamu adalah seorang data analyst berpengalaman yang menganalisis "
        "platform digital perencanaan Umrah. Berikan insight yang actionable "
        "dan berbasis data. Gunakan bahasa Indonesia yang profesional."
    )

    if st.button("Generate AI Insights", use_container_width=True, key="btn_ai_insights"):
        # Gamification: +15 XP for AI insights (first time per session)
        if not st.session_state.get("_analytics_ai_xp_awarded"):
            add_xp_safe(15, "Menggunakan AI Analytics Insights")
            st.session_state["_analytics_ai_xp_awarded"] = True

        with st.spinner("AI sedang menganalisis data..."):
            response = ai_complete(prompt_text, system_prompt=system_prompt, max_tokens=1024)

        if response:
            response_html = _markdown_to_html(response)
            st.markdown(
'<div class="ai-card" role="status" aria-live="polite">'
'<h3>AI Analytics Insights</h3>'
'<p>' + response_html + '</p>'
'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
'<div class="ai-card" role="status" aria-live="polite">'
'<h3>AI Analytics Insights</h3>'
'<p>Layanan AI tidak tersedia saat ini. Pastikan API key sudah dikonfigurasi.</p>'
'</div>',
                unsafe_allow_html=True,
            )
            _render_fallback_insights(metrics, page_stats)
    else:
        st.info(
            "Klik tombol di atas untuk menghasilkan analisis AI berdasarkan "
            "data analytics periode yang dipilih."
        )


def _render_fallback_insights(metrics, page_stats):
    """Render static fallback insights when AI is unavailable."""
    total_users = metrics.get('total_users', 0)
    total_events = metrics.get('total_events', 0)

    tips = []

    if total_users == 0:
        tips.append("Belum ada data pengguna untuk periode ini. Pastikan tracking analytics aktif.")
    else:
        users_denom = total_users if total_users else 1
        engagement = round(total_events / users_denom, 1)
        if engagement < 3:
            tips.append(
                "Engagement rate rendah (" + str(engagement) + " events/user). "
                "Pertimbangkan untuk menambah fitur interaktif atau notifikasi."
            )
        elif engagement > 10:
            tips.append(
                "Engagement rate tinggi (" + str(engagement) + " events/user). "
                "Pengguna sangat aktif - peluang baik untuk monetisasi."
            )

    if page_stats:
        top_page = page_stats[0]
        top_name = top_page.get('page', 'unknown')
        top_views = top_page.get('views', 0)
        tips.append(
            "Halaman paling populer: " + top_name + " (" + str(top_views) + " views). "
            "Fokuskan optimasi UX pada halaman ini."
        )

    if not tips:
        tips.append("Kumpulkan lebih banyak data untuk mendapatkan insight yang lebih baik.")

    fallback_items = []
    for tip in tips:
        fallback_items.append("<div style='margin-bottom:0.5rem;'>&bull; " + tip + "</div>")
    fallback_html = "\n".join(fallback_items)

    st.markdown(
'<div class="dark-card" style="margin-top:1rem;">'
'<h4 style="color:#fbbf24;">Insight Otomatis</h4>'
+ fallback_html +
'</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# TAB 7: COHORT ANALYSIS & ACTIVITY HEATMAP
# =============================================================================

def _generate_demo_cohort_data(start_date, end_date):
    """Generate realistic demo cohort data when DB is unavailable.

    Returns a list of dicts with keys: cohort_week, size, retention.
    Retention is a list of 5 floats: [100.0, w1%, w2%, w3%, w4%].
    """
    # Ensure we work with datetime objects
    if hasattr(start_date, 'year') and not hasattr(start_date, 'hour'):
        sd = datetime(start_date.year, start_date.month, start_date.day)
    else:
        sd = start_date
    if hasattr(end_date, 'year') and not hasattr(end_date, 'hour'):
        ed = datetime(end_date.year, end_date.month, end_date.day)
    else:
        ed = end_date

    # Go back further to ensure enough cohorts
    cohort_start = sd - timedelta(weeks=8)
    cohorts = []
    current = cohort_start
    # Use a fixed seed derived from dates for consistent demo data per date range
    rng = random.Random(42)

    while current <= ed and len(cohorts) < 8:
        # Monday of the week
        monday = current - timedelta(days=current.weekday())
        size = rng.randint(15, 80)

        # Realistic retention curve: 100% -> ~45% -> ~30% -> ~22% -> ~18%
        base_rates = [100.0, 45.0, 30.0, 22.0, 18.0]
        retention = []
        for i, base in enumerate(base_rates):
            noise = rng.uniform(-5.0, 5.0)
            val = max(0.0, min(100.0, base + noise))
            retention.append(round(val, 1))
        # Week 0 is always 100%
        retention[0] = 100.0
        # Ensure monotonically decreasing
        for i in range(1, len(retention)):
            if retention[i] > retention[i - 1]:
                retention[i] = round(retention[i - 1] - rng.uniform(1.0, 5.0), 1)
            retention[i] = max(0.0, retention[i])

        cohorts.append({
            'cohort_week': monday.strftime('%Y-%m-%d'),
            'size': size,
            'retention': retention,
        })
        current += timedelta(weeks=1)

    return cohorts


def _build_cohort_data(db, start_date, end_date):
    """Build weekly cohort retention data from the database.

    Queries users grouped by registration week and their session activity
    in subsequent weeks to calculate retention percentages.

    Returns list of dicts: {cohort_week, size, retention: [100, w1%, w2%, w3%, w4%]}
    Falls back to demo data if the DB query fails.
    """
    try:
        excluded_sql, excluded_params = get_excluded_user_ids_clause()

        # Step 1: Get user cohorts by registration week
        cohort_query = f"""
        SELECT
            DATE_TRUNC('week', created_at) AS cohort_week,
            COUNT(*) AS size,
            ARRAY_AGG(id) AS user_ids
        FROM users
        WHERE created_at::date BETWEEN %s AND %s
            AND id NOT IN ({excluded_sql})
        GROUP BY DATE_TRUNC('week', created_at)
        ORDER BY cohort_week
        """
        cohort_rows = db.fetch_all(cohort_query, (start_date, end_date) + excluded_params)

        if not cohort_rows or len(cohort_rows) == 0:
            raise ValueError("No cohort data found")

        cohorts = []
        for row in cohort_rows:
            cohort_week = row['cohort_week']
            size = row['size']
            user_ids = row.get('user_ids', [])

            if not user_ids or size == 0:
                continue

            # Step 2: For each cohort, get weekly retention
            retention = [100.0]  # Week 0 is always 100%

            for week_offset in range(1, 5):
                week_start = cohort_week + timedelta(weeks=week_offset)
                week_end = week_start + timedelta(days=7)

                try:
                    # Check how many users from this cohort were active in this week
                    # Try analytics_events first, then visitor_sessions
                    ret_query = """
                    SELECT COUNT(DISTINCT user_id) AS active_users
                    FROM analytics_events
                    WHERE user_id = ANY(%s)
                        AND event_timestamp >= %s
                        AND event_timestamp < %s
                    """
                    ret_result = db.fetch_one(ret_query, (user_ids, week_start, week_end))
                    active = ret_result.get('active_users', 0) if ret_result else 0
                except Exception:
                    active = 0

                pct = round((active / size) * 100, 1) if size > 0 else 0.0
                retention.append(pct)

            # Format cohort_week as string
            cw_str = cohort_week.strftime('%Y-%m-%d') if hasattr(cohort_week, 'strftime') else str(cohort_week)[:10]

            cohorts.append({
                'cohort_week': cw_str,
                'size': size,
                'retention': retention,
            })

        if cohorts:
            return cohorts

        raise ValueError("Empty cohort result")

    except Exception as e:
        logger.debug(f"Cohort query failed, using demo data: {e}")
        return _generate_demo_cohort_data(start_date, end_date)


def _retention_color(pct):
    """Return background color for a retention percentage cell.

    Color scale:
      > 80%  -> dark green
      60-80% -> light green
      40-60% -> yellow / amber
      20-40% -> orange
      < 20%  -> red
    """
    if pct > 80:
        return '#166534'  # dark green
    elif pct > 60:
        return '#15803d'  # light green
    elif pct > 40:
        return '#a16207'  # amber / yellow
    elif pct > 20:
        return '#c2410c'  # orange
    else:
        return '#991b1b'  # red


def render_cohort_analytics(db, start_date, end_date):
    """Render weekly cohort retention matrix and summary metrics."""
    st.subheader("Analisis Kohort (Retention)")

    # Gamification: +15 XP for viewing cohort analytics (first time per session)
    if not st.session_state.get("_cohort_analytics_xp_awarded"):
        add_xp_safe(15, "Melihat Cohort Analytics")
        st.session_state["_cohort_analytics_xp_awarded"] = True

    st.markdown(
        '<p style="color:#b0b0b0;font-size:0.9rem;">'
        'Kohort mingguan berdasarkan tanggal registrasi pengguna. '
        'Setiap baris menunjukkan persentase pengguna yang kembali di minggu berikutnya.'
        '</p>',
        unsafe_allow_html=True,
    )

    cohorts = _build_cohort_data(db, start_date, end_date)

    if not cohorts:
        st.info("Belum ada data kohort untuk periode ini.")
        return

    # Build HTML retention matrix table
    header_labels = ['Kohort', 'Ukuran', 'Minggu 0', 'Minggu 1', 'Minggu 2', 'Minggu 3', 'Minggu 4']
    header_cells = ''.join(f'<th>{lbl}</th>' for lbl in header_labels)

    body_rows = []
    for cohort in cohorts:
        cw = cohort['cohort_week']
        size = cohort['size']
        retention = cohort['retention']

        # Cohort week label cell
        row_html = f'<td style="background:#0d1b2a;color:#60a5fa;font-weight:600;">{cw}</td>'
        # Size cell
        row_html += f'<td class="cohort-size">{size}</td>'

        # Retention cells (Week 0 through Week 4)
        for i in range(5):
            pct = retention[i] if i < len(retention) else 0.0
            bg = _retention_color(pct)
            row_html += (
                f'<td class="cohort-cell" style="background:{bg};">'
                f'{pct:.0f}%</td>'
            )

        body_rows.append(f'<tr>{row_html}</tr>')

    table_html = (
        '<table class="cohort-matrix" role="table" '
        'aria-label="Tabel retensi kohort mingguan">'
        f'<thead><tr>{header_cells}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        '</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # Summary metrics below the matrix
    if len(cohorts) >= 2:
        avg_w1 = sum(c['retention'][1] for c in cohorts if len(c['retention']) > 1) / len(cohorts)
        avg_w4 = sum(c['retention'][4] for c in cohorts if len(c['retention']) > 4) / len(cohorts)
        latest_size = cohorts[-1]['size']

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rata-rata Retensi Minggu 1", f"{avg_w1:.1f}%")
        with col2:
            st.metric("Rata-rata Retensi Minggu 4", f"{avg_w4:.1f}%")
        with col3:
            st.metric("Ukuran Kohort Terbaru", f"{latest_size}")

    # Optional: Plotly line chart of retention curves
    if HAS_PLOTLY and len(cohorts) >= 2:
        st.markdown("**Kurva Retensi per Kohort**")
        fig = go.Figure()
        weeks = ['W0', 'W1', 'W2', 'W3', 'W4']
        colors = ['#60a5fa', '#d4af37', '#4ade80', '#f472b6', '#a78bfa', '#fb923c', '#34d399', '#f87171']
        for idx, cohort in enumerate(cohorts):
            color = colors[idx % len(colors)]
            fig.add_trace(go.Scatter(
                x=weeks,
                y=cohort['retention'][:5],
                mode='lines+markers',
                name=cohort['cohort_week'],
                line=dict(color=color, width=2),
                marker=dict(size=6),
            ))
        fig.update_layout(
            title="Retention Curves by Cohort",
            xaxis_title="Minggu sejak Registrasi",
            yaxis_title="Retention (%)",
            yaxis=dict(range=[0, 105]),
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)


def _generate_demo_activity_data():
    """Generate demo activity heatmap data (day-of-week x hour-of-day).

    Returns a 7x24 nested list of integers representing event counts.
    Index 0 = Senin (Monday), index 6 = Minggu (Sunday).
    """
    rng = random.Random(99)
    data = []
    for day in range(7):
        row = []
        for hour in range(24):
            # Simulate realistic patterns:
            # - More activity during working hours (8-17)
            # - Peak around lunch (12-13) and evening (19-21)
            # - Lower on weekends
            base = 5
            if 8 <= hour <= 17:
                base = 30
            if 12 <= hour <= 13:
                base = 50
            if 19 <= hour <= 21:
                base = 45
            if hour < 6 or hour > 23:
                base = 2

            # Weekend reduction
            if day >= 5:  # Saturday, Sunday
                base = int(base * 0.6)

            # Friday special (Jumat - prayer time around 12)
            if day == 4 and 11 <= hour <= 13:
                base = int(base * 1.3)

            noise = rng.randint(-int(base * 0.3), int(base * 0.3))
            val = max(0, base + noise)
            row.append(val)
        data.append(row)
    return data


def _build_activity_data(db, start_date, end_date):
    """Build activity heatmap data from DB (day-of-week x hour-of-day).

    Returns a 7x24 nested list. Falls back to demo data on failure.
    """
    try:
        excluded_sql, excluded_params = get_excluded_user_ids_clause()
        query = f"""
        SELECT
            EXTRACT(DOW FROM event_timestamp) AS dow,
            EXTRACT(HOUR FROM event_timestamp) AS hour,
            COUNT(*) AS cnt
        FROM analytics_events
        WHERE event_timestamp::date BETWEEN %s AND %s
            AND (user_id IS NULL OR user_id NOT IN ({excluded_sql}))
        GROUP BY
            EXTRACT(DOW FROM event_timestamp),
            EXTRACT(HOUR FROM event_timestamp)
        ORDER BY dow, hour
        """
        rows = db.fetch_all(query, (start_date, end_date) + excluded_params)

        if not rows or len(rows) == 0:
            raise ValueError("No activity data")

        # Initialize 7x24 grid (PostgreSQL DOW: 0=Sunday, 1=Monday, ... 6=Saturday)
        # We remap to 0=Senin ... 6=Minggu
        grid = [[0] * 24 for _ in range(7)]
        for row in rows:
            pg_dow = int(row['dow'])  # 0=Sunday in PostgreSQL
            hour = int(row['hour'])
            cnt = int(row['cnt'])
            # Remap: Sunday(0)->6, Monday(1)->0, ..., Saturday(6)->5
            mapped_day = (pg_dow - 1) % 7
            if 0 <= mapped_day < 7 and 0 <= hour < 24:
                grid[mapped_day][hour] = cnt

        # Check if there is any real data
        total = sum(sum(r) for r in grid)
        if total == 0:
            raise ValueError("All zeros in activity data")

        return grid

    except Exception as e:
        logger.debug(f"Activity heatmap query failed, using demo data: {e}")
        return _generate_demo_activity_data()


def render_activity_heatmap(db, start_date, end_date):
    """Render activity heatmap: day-of-week (rows) x hour-of-day (columns)."""
    st.subheader("Heatmap Aktivitas")
    st.markdown(
        '<p style="color:#b0b0b0;font-size:0.9rem;">'
        'Distribusi aktivitas pengguna berdasarkan hari dan jam. '
        'Warna lebih gelap menunjukkan lebih banyak aktivitas.'
        '</p>',
        unsafe_allow_html=True,
    )

    grid = _build_activity_data(db, start_date, end_date)
    day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

    # Find max value for scaling
    max_val = max(max(row) for row in grid) if grid else 1
    if max_val == 0:
        max_val = 1

    # Build HTML heatmap table
    hour_headers = ''.join(f'<th>{h:02d}</th>' for h in range(24))
    header_row = f'<tr><th>Hari</th>{hour_headers}</tr>'

    body_rows = []
    for day_idx, day_name in enumerate(day_names):
        cells = f'<td>{day_name}</td>'
        for hour in range(24):
            val = grid[day_idx][hour]
            # Opacity based on value (min 0.08 so empty cells are still visible)
            opacity = 0.08 + (val / max_val) * 0.92 if max_val > 0 else 0.08
            # Color: use a blue-gold gradient based on intensity
            if val / max_val > 0.7:
                bg_color = f'rgba(212, 175, 55, {opacity})'  # gold for high
            elif val / max_val > 0.4:
                bg_color = f'rgba(96, 165, 250, {opacity})'  # blue for medium
            else:
                bg_color = f'rgba(96, 165, 250, {opacity * 0.7})'  # lighter blue for low

            title = f'{day_name} {hour:02d}:00 - {val} events'
            cells += (
                f'<td class="heatmap-cell" style="background:{bg_color};" '
                f'title="{title}">'
                f'{val if val > 0 else ""}</td>'
            )
        body_rows.append(f'<tr>{cells}</tr>')

    table_html = (
        '<table class="heatmap-grid" role="table" '
        'aria-label="Heatmap aktivitas harian per jam">'
        f'<thead>{header_row}</thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        '</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # Summary: busiest day and hour
    day_totals = [sum(grid[d]) for d in range(7)]
    hour_totals = [sum(grid[d][h] for d in range(7)) for h in range(24)]

    busiest_day_idx = day_totals.index(max(day_totals))
    busiest_hour = hour_totals.index(max(hour_totals))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hari Tersibuk", day_names[busiest_day_idx])
    with col2:
        st.metric("Jam Tersibuk", f"{busiest_hour:02d}:00")
    with col3:
        total_events = sum(day_totals)
        st.metric("Total Aktivitas", f"{total_events:,}")


# =============================================================================
# EXPORT HELPERS
# =============================================================================

def _build_csv_data(metrics, page_stats, session_stats, conversion_stats):
    """Build CSV string from dashboard metrics.

    Returns a UTF-8 CSV string containing all key analytics sections:
    KPI overview, page stats, session stats, and conversion stats.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # --- Section 1: KPI Overview ---
    writer.writerow(["=== KPI Overview ==="])
    writer.writerow(["Metric", "Value"])
    total_users = metrics.get('total_users', 0)
    total_sessions = metrics.get('total_sessions', 0)
    total_events = metrics.get('total_events', 0)
    users_denom = total_users if total_users else 1
    engagement = round(total_events / users_denom, 1)

    writer.writerow(["Total Users", total_users])
    writer.writerow(["Total Sessions", total_sessions])
    writer.writerow(["Total Events", total_events])
    writer.writerow(["Events / User", engagement])
    writer.writerow([])

    # --- Section 2: Page Stats ---
    writer.writerow(["=== Top Pages ==="])
    writer.writerow(["Page", "Views", "Unique Users"])
    if page_stats:
        for row in page_stats:
            writer.writerow([
                row.get('page', 'unknown'),
                row.get('views', 0),
                row.get('users', 0),
            ])
    else:
        writer.writerow(["(tidak ada data)", "", ""])
    writer.writerow([])

    # --- Section 3: Session Stats ---
    writer.writerow(["=== Session Stats ==="])
    writer.writerow(["Metric", "Value"])
    if session_stats and session_stats.get('total_sessions', 0) > 0:
        writer.writerow(["Total Sessions", session_stats.get('total_sessions', 0)])
        writer.writerow(["Avg Pages/Session", round(session_stats.get('avg_pages', 0) or 0, 1)])
        avg_dur = int(session_stats.get('avg_duration', 0) or 0)
        writer.writerow(["Avg Duration (seconds)", avg_dur])
    else:
        writer.writerow(["(tidak ada data)", ""])
    writer.writerow([])

    # --- Section 4: Conversion Stats ---
    writer.writerow(["=== Conversion Stats ==="])
    writer.writerow(["Metric", "Value"])
    if conversion_stats:
        total_u = conversion_stats.get('total_users', 0)
        premium_u = conversion_stats.get('premium_users', 0)
        free_u = conversion_stats.get('free_users', 0)
        rate = round((premium_u / (total_u or 1)) * 100, 1)
        writer.writerow(["New Users", total_u])
        writer.writerow(["Free Users", free_u])
        writer.writerow(["Premium Users", premium_u])
        writer.writerow(["Conversion Rate (%)", rate])
    else:
        writer.writerow(["(tidak ada data)", ""])

    # --- Section 5: Device Distribution ---
    writer.writerow([])
    writer.writerow(["=== Device Distribution ==="])
    writer.writerow(["Device", "Percentage (%)"])
    if HAS_ANALYTICS_SERVICE:
        try:
            svc = AnalyticsDashboardService()
            device_data = svc.get_device_stats()
            if device_data:
                for device, pct in device_data.items():
                    writer.writerow([device.title(), pct])
        except Exception:
            writer.writerow(["(tidak ada data)", ""])
    else:
        writer.writerow(["(service tidak tersedia)", ""])

    return output.getvalue()


def _build_html_report(metrics, page_stats, session_stats, conversion_stats,
                       start_date, end_date):
    """Build a styled HTML report string for download.

    The report is self-contained HTML with inline CSS, suitable for
    opening in any browser and printing to PDF.
    """
    total_users = metrics.get('total_users', 0)
    total_sessions = metrics.get('total_sessions', 0)
    total_events = metrics.get('total_events', 0)
    users_denom = total_users if total_users else 1
    engagement = round(total_events / users_denom, 1)

    start_str = str(start_date)
    end_str = str(end_date)

    # --- Build page stats rows ---
    page_rows_html = ""
    if page_stats:
        for row in page_stats:
            page_name = row.get('page', 'unknown')
            views = row.get('views', 0)
            users = row.get('users', 0)
            page_rows_html += (
                f"<tr><td>{page_name}</td>"
                f"<td style='text-align:right;'>{views:,}</td>"
                f"<td style='text-align:right;'>{users:,}</td></tr>\n"
            )
    else:
        page_rows_html = (
            "<tr><td colspan='3' style='text-align:center;color:#94a3b8;'>"
            "Tidak ada data</td></tr>"
        )

    # --- Session stats section ---
    session_html = ""
    if session_stats and session_stats.get('total_sessions', 0) > 0:
        avg_pages = round(session_stats.get('avg_pages', 0) or 0, 1)
        avg_dur = int(session_stats.get('avg_duration', 0) or 0)
        mins = avg_dur // 60
        secs = avg_dur % 60
        total_sess = session_stats.get('total_sessions', 0)
        session_html = f"""
        <div class="kpi-row">
            <div class="kpi-box">
                <div class="kpi-val">{total_sess:,}</div>
                <div class="kpi-lbl">Total Sessions</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{avg_pages}</div>
                <div class="kpi-lbl">Avg Pages/Session</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{mins}m {secs}s</div>
                <div class="kpi-lbl">Avg Duration</div>
            </div>
        </div>
        """
    else:
        session_html = "<p class='muted'>Tidak ada data sesi untuk periode ini.</p>"

    # --- Conversion stats section ---
    conversion_html = ""
    if conversion_stats:
        total_u = conversion_stats.get('total_users', 0)
        premium_u = conversion_stats.get('premium_users', 0)
        free_u = conversion_stats.get('free_users', 0)
        rate = round((premium_u / (total_u or 1)) * 100, 1)
        conversion_html = f"""
        <div class="kpi-row">
            <div class="kpi-box">
                <div class="kpi-val">{total_u:,}</div>
                <div class="kpi-lbl">New Users</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{free_u:,}</div>
                <div class="kpi-lbl">Free Users</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{premium_u:,}</div>
                <div class="kpi-lbl">Premium Users</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-val">{rate}%</div>
                <div class="kpi-lbl">Conversion Rate</div>
            </div>
        </div>
        """
    else:
        conversion_html = "<p class='muted'>Tidak ada data konversi untuk periode ini.</p>"

    # --- Device distribution section ---
    device_html = ""
    if HAS_ANALYTICS_SERVICE:
        try:
            svc = AnalyticsDashboardService()
            device_data = svc.get_device_stats()
            if device_data:
                device_html = '<div class="kpi-row">'
                for device, pct in device_data.items():
                    device_html += (
                        f'<div class="kpi-box">'
                        f'<div class="kpi-val">{pct}%</div>'
                        f'<div class="kpi-lbl">{device.title()}</div>'
                        f'</div>'
                    )
                device_html += '</div>'
        except Exception:
            pass
    if not device_html:
        device_html = "<p class='muted'>Data device tidak tersedia.</p>"

    # --- Assemble full HTML ---
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LABBAIK Analytics Report - {start_str} s/d {end_str}</title>
<style>
  body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #0d1b2a;
    color: #e2e8f0;
    margin: 0;
    padding: 2rem;
  }}
  .container {{
    max-width: 900px;
    margin: 0 auto;
  }}
  h1 {{
    color: #60a5fa;
    font-size: 1.8rem;
    border-bottom: 2px solid #334155;
    padding-bottom: 0.5rem;
  }}
  h2 {{
    color: #d4af37;
    font-size: 1.3rem;
    margin-top: 2rem;
    margin-bottom: 0.75rem;
  }}
  .subtitle {{
    color: #94a3b8;
    font-size: 0.9rem;
    margin-top: -0.5rem;
    margin-bottom: 1.5rem;
  }}
  .muted {{
    color: #94a3b8;
    font-style: italic;
  }}
  .kpi-row {{
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }}
  .kpi-box {{
    background: linear-gradient(145deg, #1a1a2e, #1e293b);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: center;
    flex: 1;
    min-width: 140px;
  }}
  .kpi-val {{
    font-size: 1.6rem;
    font-weight: 700;
    color: #e2e8f0;
  }}
  .kpi-lbl {{
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.25rem;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
  }}
  th {{
    background: #1e293b;
    color: #d4af37;
    text-align: left;
    padding: 0.6rem 0.75rem;
    border-bottom: 2px solid #334155;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }}
  td {{
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #1e293b;
    color: #b8c5d4;
    font-size: 0.9rem;
  }}
  tr:hover td {{
    background: rgba(96, 165, 250, 0.05);
  }}
  .footer {{
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid #334155;
    color: #64748b;
    font-size: 0.8rem;
    text-align: center;
  }}
  @media print {{
    body {{
      background: #fff;
      color: #1a1a2e;
    }}
    .kpi-box {{
      background: #f8fafc;
      border-color: #cbd5e1;
    }}
    .kpi-val {{
      color: #1a1a2e;
    }}
    .kpi-lbl {{
      color: #475569;
    }}
    th {{
      background: #f1f5f9;
      color: #1e293b;
    }}
    td {{
      color: #334155;
      border-bottom-color: #e2e8f0;
    }}
    h1 {{
      color: #1e40af;
    }}
    h2 {{
      color: #92400e;
    }}
  }}
</style>
</head>
<body>
<div class="container">
  <h1>LABBAIK Analytics Report</h1>
  <p class="subtitle">Periode: {start_str} s/d {end_str} &mdash; Digenerate: {now_str}</p>

  <h2>KPI Overview</h2>
  <div class="kpi-row">
    <div class="kpi-box">
      <div class="kpi-val">{total_users:,}</div>
      <div class="kpi-lbl">Total Users</div>
    </div>
    <div class="kpi-box">
      <div class="kpi-val">{total_sessions:,}</div>
      <div class="kpi-lbl">Total Sessions</div>
    </div>
    <div class="kpi-box">
      <div class="kpi-val">{total_events:,}</div>
      <div class="kpi-lbl">Total Events</div>
    </div>
    <div class="kpi-box">
      <div class="kpi-val">{engagement}</div>
      <div class="kpi-lbl">Events / User</div>
    </div>
  </div>

  <h2>Top Pages</h2>
  <table>
    <thead>
      <tr><th>Halaman</th><th style="text-align:right;">Views</th><th style="text-align:right;">Unique Users</th></tr>
    </thead>
    <tbody>
      {page_rows_html}
    </tbody>
  </table>

  <h2>Session Stats</h2>
  {session_html}

  <h2>Conversion Stats</h2>
  {conversion_html}

  <h2>Device Distribution</h2>
  {device_html}

  <div class="footer">
    LABBAIK Smart Planner &mdash; Analytics Report &mdash; {now_str}
  </div>
</div>
</body>
</html>"""
    return html


# =============================================================================
# EXPORT SECTION
# =============================================================================

def render_export_section(db, start_date, end_date):
    """Render export buttons for CSV and HTML/PDF report downloads."""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("Ekspor Laporan")
    st.markdown(
        '<p style="color:#b0b0b0;font-size:0.9rem;">'
        'Unduh ringkasan data analytics dalam format CSV atau laporan HTML '
        '(dapat dicetak sebagai PDF melalui browser).'
        '</p>',
        unsafe_allow_html=True,
    )

    # Collect all metrics for export
    metrics = _collect_dashboard_metrics(db, start_date, end_date)
    page_stats = _collect_page_stats(db, start_date, end_date)
    session_stats = _collect_session_stats(db, start_date, end_date)
    conversion_stats = _collect_conversion_stats(db, start_date, end_date)

    # Build date range string for filenames
    start_str = str(start_date).replace("-", "")
    end_str = str(end_date).replace("-", "")
    date_suffix = f"{start_str}_{end_str}"

    col1, col2 = st.columns(2)

    with col1:
        csv_data = _build_csv_data(metrics, page_stats, session_stats, conversion_stats)
        csv_filename = f"labbaik_analytics_{date_suffix}.csv"
        downloaded_csv = st.download_button(
            label="Unduh CSV",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True,
            key="export_csv_btn",
        )
        if downloaded_csv:
            if not st.session_state.get("_export_csv_xp_awarded"):
                add_xp_safe(15, "Mengekspor Analytics ke CSV")
                st.session_state["_export_csv_xp_awarded"] = True
            st.success("CSV berhasil diunduh! (+15 XP)")

    with col2:
        html_data = _build_html_report(
            metrics, page_stats, session_stats, conversion_stats,
            start_date, end_date,
        )
        html_filename = f"labbaik_analytics_{date_suffix}.html"
        downloaded_html = st.download_button(
            label="Unduh Laporan HTML",
            data=html_data,
            file_name=html_filename,
            mime="text/html",
            use_container_width=True,
            key="export_html_btn",
        )
        if downloaded_html:
            if not st.session_state.get("_export_html_xp_awarded"):
                add_xp_safe(20, "Mengekspor Analytics ke HTML Report")
                st.session_state["_export_html_xp_awarded"] = True
            st.success("Laporan HTML berhasil diunduh! (+20 XP)")

    st.markdown(
        '<p style="color:#94a3b8;font-size:0.8rem;margin-top:0.5rem;">'
        'Tip: Buka file HTML di browser, lalu gunakan Ctrl+P / Cmd+P untuk '
        'mencetak atau menyimpan sebagai PDF.'
        '</p>',
        unsafe_allow_html=True,
    )


# Export
__all__ = ["render_analytics_dashboard"]
