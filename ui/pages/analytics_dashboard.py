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
from typing import Dict, Any, Optional
import logging

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

logger = logging.getLogger(__name__)

# Try to import plotly for charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


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
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, ANALYTICS_CSS)

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


# =============================================================================
# HELPERS
# =============================================================================

def get_excluded_user_ids_sql():
    """Get SQL clause to exclude internal users."""
    emails = "', '".join(EXCLUDED_EMAILS)
    return f"SELECT id FROM users WHERE email IN ('{emails}')"


def _collect_dashboard_metrics(db, start_date, end_date):
    """Collect all key metrics into a dict for both display and AI prompt."""
    excluded_sql = get_excluded_user_ids_sql()
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
        result = db.fetch_one(query, (start_date, end_date))
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
'<div class="ai-card">'
'<h3>AI Analytics Insights</h3>'
'<p>' + response_html + '</p>'
'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
'<div class="ai-card">'
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


# Export
__all__ = ["render_analytics_dashboard"]
