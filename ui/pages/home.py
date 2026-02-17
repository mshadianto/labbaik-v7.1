"""
LABBAIK Smart Planner - Home Page
==================================
Satu-satunya AI Companion untuk Umrah Anda
"""

import streamlit as st
from datetime import datetime, date, timedelta
import random
import os
import logging
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

logger = logging.getLogger(__name__)

# =============================================================================
# PERFORMANCE: CACHING
# =============================================================================

@st.cache_data(ttl=120)  # Cache for 2 minutes
def get_cached_db_stats():
    """Get cached database stats for home page."""
    try:
        from services.database.repository import get_db
        db = get_db()
        if db:
            result = db.fetch_one("""
                SELECT
                    COALESCE(SUM(unique_visitors), 0) as total_visitors,
                    COALESCE(SUM(page_views), 0) as total_views,
                    MAX(updated_at) as last_update
                FROM visitor_stats
            """)
            if result:
                return {
                    'total_visitors': int(result.get('total_visitors', 0)),
                    'total_views': int(result.get('total_views', 0)),
                    'last_update': result.get('last_update'),
                    'source': 'database'
                }
    except Exception:
        pass
    return None

# Import dynamic version
try:
    from core.version import get_display_version, APP_VERSION
except ImportError:
    def get_display_version():
        return "v7.8.0"
    APP_VERSION = "7.8.0"

# Brand Identity
BRAND_NAME = "LABBAIK Smart Planner"
BRAND_TAGLINE = "Satu-satunya AI Companion untuk Umrah Anda"
SMART_PREP = "Smart Prep"
SMART_SAVINGS = "Smart Savings"
SMART_JOURNEY = "Smart Journey"

# =============================================================================
# PAGE-SPECIFIC CSS (no <style> tags, no @import – passed to inject_css())
# =============================================================================

HOME_PAGE_CSS = """
/* inject_custom_css — gold card helpers */
.gold-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    border: 1px solid #d4af37;
    border-radius: 15px;
    padding: 1.2rem;
    text-align: center;
}
.gold-text { color: #d4af37; }
.muted-text { color: #b0b0b0; }

/* Hero section v6 */
.hero-section-v6 {
    background: linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 50%, #0d0d0d 100%);
    padding: 2rem 1.5rem;
    border-radius: 20px;
    margin-bottom: 1rem;
    text-align: center;
    color: white;
    border: 1px solid #d4af37;
}
.arabic-calligraphy-v6 {
    font-size: 1.8rem;
    color: #d4af37;
    margin-bottom: 0.3rem;
}
.brand-name-v6 {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: 0.5rem;
    color: #d4af37;
}
.tagline-v6 { font-size: 1rem; color: #d4af37; }
.subtitle-v6 { font-size: 0.85rem; color: #b0b0b0; margin-bottom: 0.8rem; }
.version-badge-v6 {
    display: inline-block;
    background: linear-gradient(135deg, #d4af37 0%, #f4d03f 100%);
    color: #1a1a1a;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.8rem;
}
.stat-card-v6 {
    background: #1a1a1a;
    border: 1px solid #d4af37;
    border-radius: 12px;
    padding: 0.8rem;
    text-align: center;
}
.stat-icon-v6 { font-size: 1.3rem; }
.stat-label-v6 { font-size: 0.7rem; color: #b0b0b0; }
.stat-value-v6 { font-size: 1.1rem; font-weight: bold; color: #d4af37; }

/* Pulse animation for live indicator */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Home page responsive overrides — tablet */
@media (max-width: 768px) {
    .hero-section-v6 { padding: 1.2rem 0.8rem; }
    .brand-name-v6 { font-size: 1.5rem; letter-spacing: 0.15rem; }
    .arabic-calligraphy-v6 { font-size: 1.3rem; }
    .version-badge-v6 { font-size: 0.7rem; padding: 0.2rem 0.6rem; }
    .tagline-v6 { font-size: 0.85rem; }
    .subtitle-v6 { font-size: 0.75rem; }
    .stat-card-v6 { padding: 0.4rem; }
    .stat-icon-v6 { font-size: 1rem; }
    .stat-value-v6 { font-size: 0.8rem; }
    .stat-label-v6 { font-size: 0.55rem; }
    .gold-card { padding: 0.8rem; border-radius: 10px; }

    /* Pilar framework cards */
    .pilar-card { min-height: auto !important; padding: 1rem !important; }
    .pilar-card h3 { font-size: 1rem; }
    .pilar-card p { font-size: 0.82rem; }
    .pilar-icon { font-size: 2rem !important; }

    /* Highlight cards (public) */
    .highlight-card { min-height: auto !important; padding: 1rem !important; }
    .highlight-icon { font-size: 1.8rem !important; }
    .highlight-title { font-size: 0.95rem !important; }
    .highlight-desc { font-size: 0.78rem !important; }

    /* Budget cards */
    .budget-card { min-height: auto !important; padding: 1rem !important; }
    .budget-icon { font-size: 1.5rem !important; }
    .budget-name { font-size: 0.95rem !important; }
    .budget-price { font-size: 1.1rem !important; }
    .budget-desc { font-size: 0.72rem !important; }

    /* Visitor stats cards (internal) */
    .vstats-card { padding: 0.8rem !important; }
    .vstats-icon { font-size: 1.8rem !important; }
    .vstats-value { font-size: 1.3rem !important; }
    .vstats-label { font-size: 0.72rem !important; }
}

/* Home page responsive overrides — small phone */
@media (max-width: 480px) {
    .brand-name-v6 { font-size: 1.2rem; letter-spacing: 0.1rem; }
    .arabic-calligraphy-v6 { font-size: 1.1rem; }
    .tagline-v6 { font-size: 0.78rem; }

    /* Pilar cards stack naturally via shared_styles 100% columns */
    .pilar-card { padding: 0.8rem !important; }
    .pilar-icon { font-size: 1.8rem !important; }

    /* Budget cards */
    .budget-card { padding: 0.8rem !important; }
    .budget-price { font-size: 1rem !important; }

    /* Visitor stats */
    .vstats-card { padding: 0.6rem !important; }
    .vstats-icon { font-size: 1.5rem !important; }
    .vstats-value { font-size: 1.1rem !important; }
    .vstats-label { font-size: 0.68rem !important; }
}
"""

# Internal team emails (allowed to see platform stats)
INTERNAL_EMAILS = [
    'admin@labbaik.io',
    'founder@labbaik.io',
    'salam@labbaik.io',
]


def is_internal_user() -> bool:
    """Check if current user is an internal team member."""
    try:
        if 'user' in st.session_state and st.session_state.user:
            user = st.session_state.user
            email = None
            if hasattr(user, 'email'):
                email = user.email
            elif isinstance(user, dict):
                email = user.get('email')

            if email and email.lower() in [e.lower() for e in INTERNAL_EMAILS]:
                return True
    except Exception:
        pass
    return False

# =============================================================================
# VISITOR ANALYTICS - AGGRESSIVE DATABASE DETECTION
# =============================================================================

def get_visitor_stats():
    """
    Get visitor stats - OPTIMIZED with caching.
    Uses cached DB stats for performance.
    """
    # Try cached database stats first
    cached = get_cached_db_stats()
    if cached and cached.get('source') == 'database':
        total_visitors = cached['total_visitors']
        total_views = cached['total_views']

        return {
            "total_visitors": total_visitors,
            "total_views": total_views,
            "visitors_today": 0,
            "visitors_week": 0,
            "visitors_month": total_visitors,
            "popular_pages": [],
            "engagement": {
                "avg_pages_per_visit": round(total_views / max(total_visitors, 1), 1),
                "avg_session_duration": "-",
                "returning_visitors_pct": 0,
                "mobile_users_pct": 0,
                "top_region": "-"
            },
            "source": "database",
            "last_update": str(cached.get('last_update', '')),
        }

    # Fallback: Demo data
    if "visitor_count" not in st.session_state:
        st.session_state.visitor_count = random.randint(50, 100)
    if "page_view_count" not in st.session_state:
        st.session_state.page_view_count = random.randint(100, 150)

    return {
        "total_visitors": st.session_state.visitor_count,
        "total_views": st.session_state.page_view_count,
        "visitors_today": 0,
        "visitors_week": 0,
        "visitors_month": st.session_state.visitor_count,
        "popular_pages": [],
        "engagement": {
            "avg_pages_per_visit": 1.3,
            "avg_session_duration": "-",
            "returning_visitors_pct": 0,
            "mobile_users_pct": 0,
            "top_region": "-"
        },
        "source": "demo"
    }


def render_public_highlights_section():
    """Render highlights section for public users (non-internal)."""

    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #d4af37; margin-bottom: 0.5rem;">🌟 Kenapa LABBAIK Smart Planner?</h2>
        <p style="color: #b0b0b0;">Platform AI #1 untuk perencanaan umrah di Indonesia</p>
    </div>
    """, unsafe_allow_html=True)

    # Highlight Cards
    col1, col2, col3, col4 = st.columns(4)

    highlights = [
        ("🤖", "AI Assistant 24/7", "Tanya apa saja tentang umrah, dijawab AI cerdas kapan saja"),
        ("💰", "Hemat Hingga 50%", "Bandingkan harga & temukan paket terbaik sesuai budget"),
        ("👥", "Umrah Bareng", "Cari teman perjalanan dengan matching AI otomatis"),
        ("📋", "Panduan Lengkap", "Dari persiapan sampai pulang, semua ada di sini"),
    ]

    for col, (icon, title, desc) in zip([col1, col2, col3, col4], highlights):
        with col:
            st.markdown(f"""
            <div class="highlight-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                        border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center; min-height: 180px;">
                <div class="highlight-icon" style="font-size: 2.5rem;">{icon}</div>
                <div class="highlight-title" style="font-size: 1.1rem; font-weight: bold; color: #d4af37; margin: 0.5rem 0;">{title}</div>
                <div class="highlight-desc" style="color: #b0b0b0; font-size: 0.85rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # Info Section - Realistic for new app
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">🚀 Baru Diluncurkan!</h4>
        </div>
        """, unsafe_allow_html=True)

        launch_info = [
            ("🆕", "Early Access", "Jadilah yang pertama mencoba"),
            ("🆓", "100% Gratis", "Semua fitur terbuka untuk Anda"),
            ("💡", "Terus Berkembang", "Update fitur setiap minggu"),
            ("📢", "Feedback Welcome", "Bantu kami jadi lebih baik"),
        ]

        for icon, title, desc in launch_info:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid #333;">
                <span style="font-size: 1.3rem; margin-right: 0.8rem;">{icon}</span>
                <div>
                    <div style="color: #fafafa; font-weight: bold; font-size: 0.9rem;">{title}</div>
                    <div style="color: #b0b0b0; font-size: 0.8rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">🎯 Mulai Sekarang</h4>
        </div>
        """, unsafe_allow_html=True)

        steps = [
            ("1️⃣", "Daftar Gratis", "Buat akun dalam 30 detik"),
            ("2️⃣", "Simulasi Budget", "Hitung estimasi biaya umrah Anda"),
            ("3️⃣", "Konsultasi AI", "Tanya apa saja tentang persiapan"),
            ("4️⃣", "Berangkat!", "Siap menuju Tanah Suci"),
        ]

        for num, title, desc in steps:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid #333;">
                <span style="font-size: 1.5rem; margin-right: 1rem;">{num}</span>
                <div>
                    <div style="color: #d4af37; font-weight: bold;">{title}</div>
                    <div style="color: #b0b0b0; font-size: 0.8rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # CTA
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Mulai Perencanaan Umrah Gratis", type="primary", use_container_width=True):
            st.session_state.current_page = "simulator"
            st.rerun()


def render_visitor_stats_section():
    """Render live visitor statistics section (internal only) or alternative content."""

    st.markdown("---")

    # Check if user is internal - only show stats to internal team
    if not is_internal_user():
        render_public_highlights_section()
        return

    # Get stats (internal users only)
    stats = get_visitor_stats()
    is_live = stats.get("source") == "database"
    engagement = stats.get("engagement", {})
    
    # Section Header
    status_badge = "🟢 Live Data" if is_live else "📊 Demo Data"
    badge_bg = "#1a5f3c" if is_live else "#444"
    header_html = (
        '<div style="text-align: center; margin-bottom: 1.5rem;">'
        '<h2 style="color: #d4af37; margin-bottom: 0.5rem;">📊 Statistik Platform</h2>'
        '<p style="color: #b0b0b0;">Antusiasme jamaah terhadap LABBAIK AI</p>'
        '<span style="background: ' + badge_bg + '; color: white; padding: 0.25rem 0.75rem; '
        'border-radius: 20px; font-size: 0.75rem;">' + status_badge + '</span>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Main Stats Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="vstats-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;">👥</div>
            <div class="vstats-value" style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats['total_visitors']:,}</div>
            <div class="vstats-label" style="color: #b0b0b0; font-size: 0.85rem;">Total Pengunjung</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="vstats-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;">👁️</div>
            <div class="vstats-value" style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats['total_views']:,}</div>
            <div class="vstats-label" style="color: #b0b0b0; font-size: 0.85rem;">Total Page Views</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="vstats-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;">📅</div>
            <div class="vstats-value" style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats.get('visitors_today', 47)}</div>
            <div class="vstats-label" style="color: #b0b0b0; font-size: 0.85rem;">Hari Ini</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="vstats-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;">📈</div>
            <div class="vstats-value" style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats.get('visitors_week', 312)}</div>
            <div class="vstats-label" style="color: #b0b0b0; font-size: 0.85rem;">Minggu Ini</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Popular Pages & Engagement
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">🔥 Halaman Populer</h4>
        </div>
        """, unsafe_allow_html=True)
        
        popular_pages = stats.get('popular_pages', [])
        page_icons = {
            "home": "🏠",
            "beranda": "🏠",
            "umrah_mandiri": "🧭",
            "simulator": "💰",
            "chat": "🤖",
            "umrah_bareng": "👥",
            "booking": "📦",
        }
        
        for i, page in enumerate(popular_pages[:6], 1):
            icon = page_icons.get(page['page'], "📄")
            page_name = page['page'].replace("_", " ").title()
            views = page['views']
            
            # Progress bar width based on views
            max_views = popular_pages[0]['views'] if popular_pages else 100
            width_pct = (views / max_views) * 100
            
            st.markdown(f"""
            <div style="margin-bottom: 0.8rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                    <span style="color: #fafafa;">{icon} {page_name}</span>
                    <span style="color: #d4af37; font-weight: bold;">{views:,}</span>
                </div>
                <div style="background: #333; border-radius: 10px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #d4af37, #f4d03f); width: {width_pct}%; height: 100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">⚡ Engagement Metrics</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Get engagement metrics
        avg_pages = engagement.get('avg_pages_per_visit', 1.3)
        avg_duration = engagement.get('avg_session_duration', '4m 32s')
        returning_pct = engagement.get('returning_visitors_pct', 34)
        mobile_pct = engagement.get('mobile_users_pct', 67)
        top_region = engagement.get('top_region', 'Jakarta')
        
        metrics = [
            ("📊", "Rata-rata halaman/visitor", f"{avg_pages:.1f}"),
            ("⏱️", "Avg. session duration", avg_duration),
            ("🔄", "Returning visitors", f"{returning_pct:.0f}%"),
            ("📱", "Mobile users", f"{mobile_pct:.0f}%"),
            ("🌍", "Top region", top_region),
        ]
        
        for icon, label, value in metrics:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; border-bottom: 1px solid #333;">
                <span style="color: #b0b0b0;">{icon} {label}</span>
                <span style="color: #d4af37; font-weight: bold;">{value}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Live indicator — pulse keyframes now in HOME_PAGE_CSS
    indicator_color = "#4ade80" if is_live else "#fbbf24"
    indicator_text = "Data realtime dari Neon Database" if is_live else "Demo mode - Connect database for live data"

    live_html = (
        '<div style="text-align: center; margin-top: 1.5rem;">'
        '<span style="display: inline-flex; align-items: center; background: #1a1a1a; '
        'padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #333;">'
        '<span style="width: 8px; height: 8px; background: ' + indicator_color + '; border-radius: 50%; '
        'margin-right: 0.5rem; animation: pulse 2s infinite;"></span>'
        '<span style="color: #b0b0b0; font-size: 0.85rem;">' + indicator_text + '</span>'
        '</span>'
        '</div>'
    )
    st.markdown(live_html, unsafe_allow_html=True)


# =============================================================================
# 🔧 FIX: DEBUG WIDGET (NEW)
# =============================================================================

def render_debug_widget():
    """🔧 FIX: Temporary debug widget - only for internal users."""
    # Only show debug widget to internal team
    if not is_internal_user():
        return

    with st.sidebar.expander("🔍 DB Debug", expanded=False):
        st.caption("Debug Mode - Remove after fixing")
        
        if st.button("🔄 Test Database", use_container_width=True):
            try:
                from services.database.repository import get_db
                
                db = get_db()
                
                if not db:
                    st.error("❌ DB connection is None")
                else:
                    # Test 1: Connection
                    try:
                        test = db.fetch_one("SELECT NOW() as time")
                        st.success(f"✅ Connected: {test.get('time')}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")
                        return
                    
                    # Test 2: Count rows
                    try:
                        count = db.fetch_one("""
                            SELECT 
                                COUNT(*) as rows,
                                COALESCE(SUM(unique_visitors), 0) as visitors,
                                COALESCE(SUM(page_views), 0) as views,
                                MAX(updated_at) as last_update
                            FROM visitor_stats
                        """)
                        
                        st.write("📊 **Database Stats:**")
                        st.json(count)
                        
                        if count and count.get('rows', 0) > 0:
                            st.success(f"✅ Found {count['rows']} rows in visitor_stats")
                        else:
                            st.warning("⚠️ visitor_stats table is EMPTY!")
                            
                    except Exception as e:
                        st.error(f"❌ Query failed: {e}")
                    
                    # Test 3: Today's data
                    try:
                        today = db.fetch_all("""
                            SELECT page, unique_visitors, page_views, 
                                   updated_at, date
                            FROM visitor_stats 
                            WHERE date = CURRENT_DATE
                            ORDER BY updated_at DESC
                        """)
                        
                        if today:
                            st.write(f"📅 **Today's Data ({len(today)} rows):**")
                            for row in today:
                                st.caption(f"• {row['page']}: {row['unique_visitors']}v / {row['page_views']}pv @ {row['updated_at']}")
                        else:
                            st.warning("⚠️ No data for TODAY's date!")
                            
                            # Check if there's ANY data
                            all_data = db.fetch_all("""
                                SELECT date, page, unique_visitors, page_views
                                FROM visitor_stats
                                ORDER BY date DESC
                                LIMIT 5
                            """)
                            
                            if all_data:
                                st.write("📋 **Most recent data:**")
                                for row in all_data:
                                    st.caption(f"• {row['date']} - {row['page']}: {row['unique_visitors']}v / {row['page_views']}pv")
                            else:
                                st.error("❌ Table is completely EMPTY!")
                                
                    except Exception as e:
                        st.error(f"❌ Today check failed: {e}")
                        
            except Exception as e:
                st.error(f"❌ Debug error: {e}")
                import traceback
                st.code(traceback.format_exc())


# =============================================================================
# PRICE INTELLIGENCE SECTION
# =============================================================================

def render_price_intelligence_section():
    """Render live price intelligence section."""
    try:
        from services.price.monitoring import get_cached_health_status
        from services.price.repository import get_cached_packages, format_price_idr
        
        status = get_cached_health_status()
        packages = get_cached_packages(limit=3)
        
        if not packages:
            return  # Skip if no data
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: #d4af37; margin-bottom: 0.5rem;">💰 Harga Paket Umrah Terkini</h2>
            <p style="color: #b0b0b0;">Data live dari berbagai travel agent</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show health status
        overall = status.get('overall', 'unknown')
        if overall == 'healthy':
            st.success("🟢 Data Harga Live - Update otomatis setiap 6 jam")
        elif overall in ['warning', 'degraded']:
            st.warning("🟡 Data mungkin tertunda")
        
        # Show top 3 packages
        cols = st.columns(3)
        for col, pkg in zip(cols, packages[:3]):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {pkg.get('package_name', 'Paket')[:25]}...")
                    st.caption(f"🏢 {pkg.get('source_name', 'Travel Agent')}")
                    
                    price = float(pkg.get('price_idr', 0))
                    st.markdown(f"## {format_price_idr(price)}")
                    
                    duration = pkg.get('duration_days', 0)
                    city = pkg.get('departure_city', '')
                    st.caption(f"📅 {duration} hari | 🛫 {city}")
        
        # CTA
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Lihat Semua Harga", type="primary", use_container_width=True):
                st.session_state.current_page = "simulator"
                st.rerun()
                
    except Exception as e:
        pass  # Skip section if price intelligence not available


# =============================================================================
# PAGE CONFIG & STYLING
# =============================================================================

def inject_custom_css():
    """Inject page CSS via shared inject_css() helper."""
    # Skip if already injected
    if st.session_state.get('_home_css_injected'):
        return
    st.session_state._home_css_injected = True

    inject_css(HERO_CSS, CARD_CSS, HOME_PAGE_CSS)


# =============================================================================
# COMPONENTS
# =============================================================================

def render_hero_section():
    """Render hero section with call-to-action - BLACK GOLD theme (OPTIMIZED)."""

    # CSS now in HOME_PAGE_CSS, injected via inject_custom_css()

    # Hero content - Premium Brand Identity
    st.markdown(f"""
    <div class="hero-section-v6">
        <div class="arabic-calligraphy-v6">لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ</div>
        <div class="brand-name-v6">LABBAIK</div>
        <div class="tagline-v6">Smart Planner</div>
        <div class="subtitle-v6">{BRAND_TAGLINE}</div>
        <div class="version-badge-v6">{get_display_version()} - The Only AI Umrah Companion</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats using Streamlit columns
    col1, col2, col3, col4 = st.columns(4)
    
    stats = [
        ("🕋", "Panduan Manasik", "8 Rukun"),
        ("💰", "Budget Simulator", "Real-time"),
        ("👥", "Smart Matching", "AI-Powered"),
        ("🤲", "Koleksi Doa", "20+ Doa"),
    ]
    
    for col, (icon, label, value) in zip([col1, col2, col3, col4], stats):
        with col:
            st.markdown(f"""
            <div class="stat-card-v6">
                <div class="stat-icon-v6">{icon}</div>
                <div class="stat-value-v6">{value}</div>
                <div class="stat-label-v6">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")  # Spacer
    
    # CTA Buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🤖 AI Chat", type="primary", use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
    
    with col2:
        if st.button("💰 Simulasi Biaya", use_container_width=True):
            st.session_state.current_page = "simulator"
            st.rerun()
    
    with col3:
        if st.button("🧭 Umrah Mandiri", use_container_width=True):
            st.session_state.current_page = "umrah_mandiri"
            st.rerun()
    
    with col4:
        if st.button("👥 Umrah Bareng", use_container_width=True):
            st.session_state.current_page = "umrah_bareng"
            st.rerun()


def render_stats_counter():
    """Render animated stats counter."""
    
    # Skip - stats already in hero section
    pass


def render_3_pilar_framework():
    """Render Smart Planner Framework section - BLACK GOLD theme."""

    st.markdown("---")
    st.markdown("## 🧠 LABBAIK Smart Planner Framework")
    st.caption("Sistem AI cerdas yang menemani perjalanan umrah Anda dari awal hingga akhir:")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="pilar-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; min-height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div class="pilar-icon" style="font-size: 3rem;">📋</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_PREP}</h3>
            <p style="color: #b0b0b0; font-size: 0.9rem;">Persiapan cerdas dengan panduan AI personal & checklist otomatis</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="pilar-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; min-height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div class="pilar-icon" style="font-size: 3rem;">💰</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_SAVINGS}</h3>
            <p style="color: #b0b0b0; font-size: 0.9rem;">Optimasi budget cerdas, hemat hingga jutaan rupiah</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="pilar-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; min-height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div class="pilar-icon" style="font-size: 3rem;">🕌</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_JOURNEY}</h3>
            <p style="color: #b0b0b0; font-size: 0.9rem;">AI companion 24/7 selama di Tanah Suci</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CTA to Umrah Mandiri
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🧭 Buka Panduan Umrah Mandiri", type="primary", use_container_width=True):
            st.session_state.current_page = "umrah_mandiri"
            st.rerun()


def render_features_showcase():
    """Render features showcase section - only real features."""

    st.markdown("## ✨ Fitur yang Tersedia")
    st.caption("Tools untuk membantu perencanaan umrah Anda")

    # CORE FEATURES - Actually exist
    core_features = [
        {
            "icon": "🤖",
            "title": "AI Chat Assistant",
            "description": "Tanya jawab seputar umrah dengan AI. Dari tata cara ibadah, tips persiapan, hingga estimasi biaya.",
        },
        {
            "icon": "💰",
            "title": "Simulasi Biaya",
            "description": "Hitung estimasi biaya umrah: tiket, hotel, transport, dan kebutuhan lainnya.",
        },
        {
            "icon": "🕋",
            "title": "3D Manasik Virtual",
            "description": "Visualisasi Ka'bah 3D interaktif dengan panduan tata cara umrah langkah demi langkah.",
        },
        {
            "icon": "🤲",
            "title": "Koleksi Doa",
            "description": "Kumpulan doa umrah dengan teks Arab, transliterasi latin, dan terjemahan Indonesia.",
        },
        {
            "icon": "👥",
            "title": "Umrah Bareng",
            "description": "Fitur untuk mencari dan menemukan teman perjalanan umrah dengan jadwal serupa.",
        },
        {
            "icon": "📊",
            "title": "Prediksi Keramaian",
            "description": "Estimasi tingkat keramaian Masjidil Haram untuk membantu perencanaan waktu ibadah.",
        },
    ]

    for i in range(0, len(core_features), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(core_features):
                f = core_features[i + j]
                with col:
                    with st.container(border=True):
                        st.markdown(f"### {f['icon']} {f['title']}")
                        st.write(f['description'])


def render_package_preview():
    """Render budget range information section."""

    st.markdown("---")
    st.markdown("## 💰 Kisaran Budget Umrah")
    st.caption("Estimasi biaya umrah mandiri berdasarkan kelas layanan (harga dapat berubah)")

    # Informational budget ranges - not fake packages
    budget_info = [
        {
            "name": "Hemat",
            "icon": "🎒",
            "range": "15-20 Juta",
            "desc": "Hotel bintang 3, jarak jauh dari Masjid, transport sharing"
        },
        {
            "name": "Standar",
            "icon": "⭐",
            "range": "20-30 Juta",
            "desc": "Hotel bintang 4, jarak sedang, transport lebih nyaman"
        },
        {
            "name": "Nyaman",
            "icon": "🌟",
            "range": "30-45 Juta",
            "desc": "Hotel bintang 5, dekat Masjid, transport VIP"
        },
        {
            "name": "Premium",
            "icon": "👑",
            "range": "45 Juta+",
            "desc": "Hotel premium, sangat dekat Masjid, layanan eksklusif"
        },
    ]

    cols = st.columns(4)

    for col, info in zip(cols, budget_info):
        with col:
            st.markdown(f"""
            <div class="budget-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                        border: 1px solid #333; border-radius: 15px; padding: 1.2rem; text-align: center; min-height: 200px;">
                <div class="budget-icon" style="font-size: 2rem;">{info['icon']}</div>
                <div class="budget-name" style="color: #d4af37; font-size: 1.1rem; font-weight: bold; margin: 0.5rem 0;">{info['name']}</div>
                <div class="budget-price" style="color: #fafafa; font-size: 1.3rem; font-weight: bold;">Rp {info['range']}</div>
                <div class="budget-desc" style="color: #b0b0b0; font-size: 0.8rem; margin-top: 0.5rem;">{info['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    st.caption("💡 *Gunakan Simulasi Biaya untuk kalkulasi detail sesuai kebutuhan Anda*")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💰 Hitung Budget Saya", type="primary", use_container_width=True):
            st.session_state.current_page = "simulator"
            st.rerun()


def render_testimonials():
    """Render community invitation section (replacing fake testimonials)."""

    st.markdown("---")
    st.markdown("## 🤝 Bergabung dengan Komunitas")
    st.caption("Jadilah bagian dari generasi pertama pengguna LABBAIK Smart Planner")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 🎁 Keuntungan Early Adopter")
            benefits = [
                "✅ Akses gratis ke semua fitur premium",
                "✅ Prioritas mendapat fitur baru",
                "✅ Langsung terhubung dengan tim developer",
                "✅ Suara Anda membentuk masa depan app",
            ]
            for b in benefits:
                st.markdown(b)

    with col2:
        with st.container(border=True):
            st.markdown("### 📢 Sampaikan Feedback")
            st.markdown("Kami ingin mendengar pengalaman Anda!")
            st.caption("Temukan bug? Punya ide fitur? Butuh bantuan?")

            feedback_email = "founder@labbaik.io"
            st.markdown(f"📧 Email: **{feedback_email}**")
            st.caption("Setiap feedback akan kami baca dan tindaklanjuti.")


def render_upcoming_trips():
    """Render Umrah Bareng invitation section."""

    st.markdown("---")
    st.markdown("## 👥 Umrah Bareng - Cari Teman Perjalanan")
    st.caption("Fitur untuk menemukan jamaah dengan jadwal & budget yang sama")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 🤝 Tidak Perlu Umrah Sendirian

        **Umrah Bareng** membantu Anda menemukan teman perjalanan yang cocok:

        - 🎯 **Smart Matching** - AI mencocokkan berdasarkan jadwal, budget, dan kota asal
        - 💰 **Hemat Biaya** - Berbagi biaya hotel, transport, dan guide
        - 👥 **Komunitas** - Kenalan dengan sesama jamaah dari berbagai kota
        - 🛡️ **Lebih Aman** - Perjalanan berkelompok lebih nyaman

        *Buat trip Anda sendiri atau gabung dengan trip yang sudah ada!*
        """)

        if st.button("🚀 Mulai Cari Teman Umrah", type="primary", use_container_width=True):
            st.session_state.current_page = "umrah_bareng"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 3rem;">👥</div>
            <div style="color: #d4af37; font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">Umrah Bareng</div>
            <div style="color: #b0b0b0; font-size: 0.85rem; margin-bottom: 1rem;">Hemat hingga 30% dengan berbagi biaya</div>
            <div style="background: #333; padding: 0.5rem; border-radius: 8px;">
                <div style="color: #fafafa; font-size: 0.8rem;">💡 Tips: Buat trip 3-6 bulan sebelum keberangkatan</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_quick_chat():
    """Render quick AI chat widget."""
    
    st.markdown("---")
    st.markdown("## 🤖 Tanya AI Sekarang")
    st.caption("Punya pertanyaan tentang umrah? Tanya langsung!")
    
    # Quick questions
    quick_questions = [
        "Apa syarat umrah?",
        "Berapa biaya umrah?",
        "Kapan waktu terbaik umrah?",
        "Apa yang harus dibawa?",
        "Bagaimana tata cara ihram?",
    ]
    
    st.markdown("**Pertanyaan populer:**")
    cols = st.columns(5)
    
    for col, q in zip(cols, quick_questions):
        with col:
            if st.button(q, key=f"quick_{q}", use_container_width=True):
                st.session_state.quick_question = q
                st.session_state.current_page = "chat"
                st.rerun()
    
    # Custom question
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_question = st.text_input(
            "Atau ketik pertanyaan Anda:",
            placeholder="Contoh: Apa saja rukun umrah?",
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("Tanya 🚀", type="primary", use_container_width=True):
            if user_question:
                st.session_state.quick_question = user_question
                st.session_state.current_page = "chat"
                st.rerun()


def render_partners():
    """Render technology section - only factual claims."""

    st.markdown("---")
    st.markdown("## 🛠️ Dibangun Dengan")

    badges = [
        ("🤖", "AI-Powered", "Groq LLM"),
        ("🐍", "Python", "Streamlit"),
        ("🗄️", "Database", "PostgreSQL"),
        ("☁️", "Cloud", "Railway"),
    ]

    cols = st.columns(4)

    for col, (icon, title, desc) in zip(cols, badges):
        with col:
            st.markdown(f"**{icon} {title}**")
            st.caption(desc)


def render_newsletter():
    """Render contact/follow section."""

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📱 Ikuti Perkembangan LABBAIK")
        st.caption("Dapatkan tips umrah, update fitur, dan info menarik lainnya")

    with col2:
        st.markdown("**Follow Instagram kami:**")
        st.markdown("[@labbaik.ai](https://instagram.com/labbaik.ai)")
        st.caption("atau email ke founder@labbaik.io")


def render_footer():
    """Render footer section."""

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🕋 LABBAIK Smart Planner")
        st.caption("Satu-satunya AI Companion untuk Umrah Anda")
        st.caption("© 2025 LABBAIK")

    with col2:
        st.markdown("**Fitur Utama**")
        st.caption("🤖 AI Chat Assistant")
        st.caption("💰 Simulasi Biaya")
        st.caption("👥 Umrah Bareng")
        st.caption("🧭 Panduan Mandiri")

    with col3:
        st.markdown("**Kontak**")
        st.caption("📧 founder@labbaik.io")
        st.caption("🌐 app.labbaik.io")
        st.caption("📱 Instagram: [@labbaik.ai](https://instagram.com/labbaik.ai)")
        st.caption("*Dibuat dengan ❤️ di Indonesia*")


# =============================================================================
# MAIN PAGE RENDERER - 🔧 FIX: WITH DEBUG WIDGET
# =============================================================================

def render_home_page():
    """Main home page renderer - OPTIMIZED for speed."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("home")
    except Exception:
        pass

    # Debug widget (internal only)
    render_debug_widget()

    # Inject CSS (cached)
    inject_custom_css()

    # === CORE SECTIONS (Always render) ===
    render_hero_section()

    # Quick Chat - Most important action
    render_quick_chat()

    # Framework overview
    render_3_pilar_framework()

    # === CONDITIONAL SECTIONS ===
    # Stats for internal, highlights for public
    render_visitor_stats_section()

    # Features (compact)
    render_features_showcase()

    # Umrah Bareng CTA
    render_upcoming_trips()

    # Footer only
    render_footer()


# Export
__all__ = ["render_home_page"]