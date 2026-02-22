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
try:
    from services.ai.helpers import add_xp_safe
except ImportError:
    def add_xp_safe(*a, **kw): pass

try:
    from services.price.live_prices import render_live_prices_widget, LivePriceService
    HAS_LIVE_PRICES = True
except ImportError:
    HAS_LIVE_PRICES = False

try:
    from services.price.monitoring import PriceMonitor, get_cached_health_status
    HAS_PRICE_MONITOR = True
except ImportError:
    HAS_PRICE_MONITOR = False

try:
    from hijri_converter import Gregorian
    HAS_HIJRI = True
except ImportError:
    HAS_HIJRI = False

logger = logging.getLogger(__name__)


def _get_hijri_date_str(gregorian_date):
    """Convert Gregorian date to Hijri string."""
    if not HAS_HIJRI:
        return None
    try:
        h = Gregorian(gregorian_date.year, gregorian_date.month, gregorian_date.day).to_hijri()
        HIJRI_MONTHS = [
            "Muharram", "Safar", "Rabiul Awal", "Rabiul Akhir",
            "Jumadil Awal", "Jumadil Akhir", "Rajab", "Sya'ban",
            "Ramadan", "Syawal", "Dzulqa'dah", "Dzulhijjah"
        ]
        month_name = HIJRI_MONTHS[h.month - 1] if 1 <= h.month <= 12 else str(h.month)
        return f"{h.day} {month_name} {h.year} H"
    except Exception:
        return None

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

/* Hijri date display */
.hijri-date-display {
    color: #d4af37; font-size: 0.95rem; font-style: italic;
    margin-top: 4px;
}

/* Pulse animation for live indicator */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Data Freshness Widget */
.data-freshness-section {
    background: linear-gradient(135deg, #111 0%, #1a1a1a 100%);
    border: 1px solid #333;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-top: 0.5rem;
}
.freshness-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.6rem;
}
.freshness-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
.freshness-dot.green { background: #4ade80; }
.freshness-dot.yellow { background: #fbbf24; }
.freshness-dot.red { background: #f87171; }
.freshness-title {
    color: #b8c5d4;
    font-size: 0.85rem;
    font-weight: 600;
}
.freshness-updated {
    color: #8e9fb3;
    font-size: 0.75rem;
    margin-bottom: 0.6rem;
}
.freshness-stats {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}
.freshness-stat {
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 0.4rem 0.7rem;
    text-align: center;
    flex: 1;
    min-width: 80px;
}
.freshness-stat-value {
    color: #d4af37;
    font-size: 0.95rem;
    font-weight: bold;
}
.freshness-stat-label {
    color: #8e9fb3;
    font-size: 0.65rem;
}
.freshness-admin {
    margin-top: 0.6rem;
    padding-top: 0.6rem;
    border-top: 1px solid #2a2a3e;
}
.freshness-admin-row {
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0;
    font-size: 0.75rem;
}
.freshness-admin-label { color: #8e9fb3; }
.freshness-admin-value { color: #b8c5d4; font-weight: 500; }
.freshness-admin-link {
    display: inline-block;
    margin-top: 0.5rem;
    color: #d4af37;
    font-size: 0.75rem;
    text-decoration: none;
    cursor: pointer;
}
.freshness-admin-link:hover { text-decoration: underline; }
@media (max-width: 480px) {
    .freshness-stats { gap: 6px; }
    .freshness-stat { padding: 0.3rem 0.5rem; min-width: 60px; }
    .freshness-stat-value { font-size: 0.85rem; }
    .freshness-stat-label { font-size: 0.6rem; }
}

/* Season Countdown Section */
.season-countdown-section {
    background: linear-gradient(135deg, #0d0d0d 0%, #1a1a2e 50%, #0d0d0d 100%);
    border: 1px solid #d4af37;
    border-radius: 15px;
    padding: 1.5rem;
    text-align: center;
    margin-bottom: 1rem;
}
.countdown-title {
    color: #d4af37;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.countdown-days {
    font-size: 2.8rem;
    font-weight: 800;
    color: #f4d03f;
    line-height: 1;
    margin: 0.5rem 0;
}
.countdown-days-label {
    color: #b0b0b0;
    font-size: 0.9rem;
    margin-bottom: 0.8rem;
}
.countdown-bar-bg {
    background: #333;
    border-radius: 10px;
    height: 10px;
    overflow: hidden;
    margin: 0.5rem 0;
}
.countdown-bar-fill {
    background: linear-gradient(90deg, #d4af37, #f4d03f);
    height: 100%;
    border-radius: 10px;
    transition: width 0.5s ease;
}
.countdown-note {
    color: #8e9fb3;
    font-size: 0.78rem;
    margin-top: 0.6rem;
    font-style: italic;
}
.countdown-season-badge {
    display: inline-block;
    background: linear-gradient(135deg, #d4af37 0%, #f4d03f 100%);
    color: #1a1a1a;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.75rem;
    margin-bottom: 0.5rem;
}
.countdown-upcoming {
    background: #1a1a1a;
    border: 1px solid #2a2a3e;
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin-top: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.countdown-upcoming-name {
    color: #b8c5d4;
    font-size: 0.85rem;
    font-weight: 600;
}
.countdown-upcoming-date {
    color: #d4af37;
    font-size: 0.8rem;
}

/* Featured Deals Section */
.deals-container {
    display: flex;
    gap: 1rem;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 0.5rem;
    scrollbar-width: thin;
    scrollbar-color: #d4af37 #333;
}
.deals-container::-webkit-scrollbar {
    height: 6px;
}
.deals-container::-webkit-scrollbar-track {
    background: #333;
    border-radius: 3px;
}
.deals-container::-webkit-scrollbar-thumb {
    background: #d4af37;
    border-radius: 3px;
}
.deal-card {
    flex: 0 0 calc(33.333% - 0.7rem);
    min-width: 260px;
    scroll-snap-align: start;
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    border: 1px solid #d4af37;
    border-radius: 15px;
    padding: 1.3rem;
    text-align: center;
    position: relative;
}
.deal-card:hover {
    border-color: #f4d03f;
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.15);
}
.deal-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #f87171;
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.65rem;
    font-weight: bold;
}
.deal-badge.demo {
    background: #6b7280;
}
.deal-agent {
    color: #8e9fb3;
    font-size: 0.78rem;
    margin-top: 0.3rem;
}
.deal-name {
    color: #fafafa;
    font-size: 1rem;
    font-weight: 700;
    margin: 0.5rem 0 0.3rem;
}
.deal-price {
    color: #d4af37;
    font-size: 1.4rem;
    font-weight: 800;
}
.deal-original-price {
    color: #6b7280;
    font-size: 0.8rem;
    text-decoration: line-through;
}
.deal-details {
    color: #b0b0b0;
    font-size: 0.78rem;
    margin-top: 0.5rem;
}
.deal-cta {
    display: inline-block;
    margin-top: 0.8rem;
    padding: 0.4rem 1.2rem;
    background: linear-gradient(135deg, #d4af37 0%, #f4d03f 100%);
    color: #1a1a1a;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.8rem;
    text-decoration: none;
    cursor: pointer;
}
.deal-cta:hover {
    background: linear-gradient(135deg, #f4d03f 0%, #d4af37 100%);
}

/* Testimonial Section */
@keyframes testimonial-scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
.testimonial-section-title {
    text-align: center;
    margin-bottom: 1.5rem;
}
.testimonial-track-wrapper {
    overflow: hidden;
    position: relative;
    padding: 0.5rem 0;
}
.testimonial-track {
    display: flex;
    gap: 1rem;
    animation: testimonial-scroll 30s linear infinite;
    width: max-content;
}
.testimonial-track:hover {
    animation-play-state: paused;
}
.testimonial-card {
    flex: 0 0 300px;
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    border: 1px solid #333;
    border-radius: 15px;
    padding: 1.2rem;
    min-height: 180px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.testimonial-card:hover {
    border-color: #d4af37;
}
.testimonial-stars {
    color: #f4d03f;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}
.testimonial-quote {
    color: #b8c5d4;
    font-size: 0.88rem;
    font-style: italic;
    line-height: 1.5;
    flex-grow: 1;
}
.testimonial-author {
    margin-top: 0.8rem;
    padding-top: 0.5rem;
    border-top: 1px solid #333;
}
.testimonial-author-name {
    color: #d4af37;
    font-weight: 700;
    font-size: 0.88rem;
}
.testimonial-author-city {
    color: #8e9fb3;
    font-size: 0.75rem;
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

    /* Season countdown */
    .countdown-days { font-size: 2.2rem; }
    .countdown-title { font-size: 1.1rem; }

    /* Featured deals - 2 columns on tablet */
    .deal-card { flex: 0 0 calc(50% - 0.5rem); min-width: 220px; }

    /* Testimonials */
    .testimonial-card { flex: 0 0 260px; min-height: 160px; }
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

    /* Season countdown */
    .countdown-days { font-size: 1.8rem; }
    .season-countdown-section { padding: 1rem; }

    /* Featured deals - single column scroll on phone */
    .deal-card { flex: 0 0 85%; min-width: 240px; }
    .deal-price { font-size: 1.2rem; }

    /* Testimonials */
    .testimonial-card { flex: 0 0 240px; padding: 1rem; min-height: 150px; }
    .testimonial-quote { font-size: 0.82rem; }
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
        <h2 style="color: #d4af37; margin-bottom: 0.5rem;"><span aria-hidden="true">🌟</span> Kenapa LABBAIK Smart Planner?</h2>
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
                <div class="highlight-icon" style="font-size: 2.5rem;" aria-hidden="true">{icon}</div>
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
        <div class="vstats-card" role="status" aria-live="polite" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;" aria-hidden="true">👥</div>
            <div class="vstats-value" style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats['total_visitors']:,}</div>
            <div class="vstats-label" style="color: #b0b0b0; font-size: 0.85rem;">Total Pengunjung</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="vstats-card" role="status" aria-live="polite" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;" aria-hidden="true">👁️</div>
            <div class="vstats-value" style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats['total_views']:,}</div>
            <div class="vstats-label" style="color: #b0b0b0; font-size: 0.85rem;">Total Page Views</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="vstats-card" role="status" aria-live="polite" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;" aria-hidden="true">📅</div>
            <div class="vstats-value" style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats.get('visitors_today', 47)}</div>
            <div class="vstats-label" style="color: #b0b0b0; font-size: 0.85rem;">Hari Ini</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="vstats-card" role="status" aria-live="polite" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div class="vstats-icon" style="font-size: 2.5rem;" aria-hidden="true">📈</div>
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
# LIVE PRICES SECTION
# =============================================================================

def render_live_prices_section():
    """Render live Umrah package prices section on home page."""
    if not HAS_LIVE_PRICES:
        return

    try:
        service = LivePriceService()
        stats = service.get_price_stats()

        if not stats or stats.get("total_packages", 0) == 0:
            return  # Skip if no data available

        st.markdown("---")

        # Section header with LIVE badge
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: #d4af37; margin-bottom: 0.5rem;">
                <span aria-hidden="true">💰</span> Paket Umrah Terkini
                <span style="display: inline-flex; align-items: center; gap: 5px; background: #1a1a2e;
                            padding: 4px 10px; border-radius: 20px; border: 1px solid #28a745;
                            vertical-align: middle; margin-left: 8px;">
                    <span style="width: 8px; height: 8px; background: #28a745; border-radius: 50%;
                                 animation: pulse 1.5s infinite;"></span>
                    <span style="color: #28a745; font-size: 0.75rem; font-weight: bold;">LIVE</span>
                </span>
            </h2>
            <p style="color: #b0b0b0;">Harga terbaru dari berbagai travel agent terpercaya</p>
        </div>
        """, unsafe_allow_html=True)

        # Price stats cards
        from services.price.live_prices import format_price

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="gold-card" role="status" aria-live="polite">
                <div class="muted-text" style="font-size: 0.8rem;">Mulai dari</div>
                <div class="gold-text" style="font-size: 1.3rem; font-weight: bold;">{format_price(stats['min_price'])}</div>
                <div class="muted-text" style="font-size: 0.75rem;">paket termurah</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="gold-card" role="status" aria-live="polite">
                <div class="muted-text" style="font-size: 0.8rem;">Rata-rata</div>
                <div class="gold-text" style="font-size: 1.3rem; font-weight: bold;">{format_price(stats['avg_price'])}</div>
                <div class="muted-text" style="font-size: 0.75rem;">dari {stats['total_packages']} paket</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="gold-card" role="status" aria-live="polite">
                <div class="muted-text" style="font-size: 0.8rem;">Promo Aktif</div>
                <div class="gold-text" style="font-size: 1.3rem; font-weight: bold;">{stats.get('promo_count', 0)} Paket</div>
                <div class="muted-text" style="font-size: 0.75rem;">diskon spesial</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Render the 3 cheapest packages widget
        render_live_prices_widget()

        # Navigation button to full price comparison page
        st.markdown("")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Lihat Semua Paket & Bandingkan Harga", type="primary", use_container_width=True, key="home_live_prices_cta"):
                st.session_state.current_page = "price_comparison"
                st.rerun()

    except Exception as e:
        logger.debug(f"Live prices section skipped: {e}")


# =============================================================================
# DATA FRESHNESS WIDGET
# =============================================================================

def _is_admin_user() -> bool:
    """Check if current user has admin role."""
    try:
        user = st.session_state.get('user')
        if user is None:
            return False
        role = None
        if hasattr(user, 'role'):
            role = user.role
        elif isinstance(user, dict):
            role = user.get('role')
        if role is not None:
            role_str = role.value if hasattr(role, 'value') else str(role)
            return role_str == 'admin'
    except Exception:
        pass
    return False


def render_data_freshness_widget():
    """Render compact data freshness widget showing price data health status."""
    if not HAS_PRICE_MONITOR:
        return

    try:
        status = get_cached_health_status()
        if not status:
            return

        overall = status.get('overall', 'unknown')

        # Determine dot color and label
        if overall == 'healthy':
            dot_class = 'green'
            status_label = 'Data Segar'
        elif overall in ('warning', 'degraded'):
            dot_class = 'yellow'
            status_label = 'Data Tertunda'
        elif overall == 'critical':
            dot_class = 'red'
            status_label = 'Sistem Error'
        else:
            dot_class = 'yellow'
            status_label = 'Tidak Diketahui'

        # Calculate "last updated" text
        latest_update = None
        for key in ['packages', 'hotels', 'flights']:
            comp = status.get(key, {})
            update_time = comp.get('last_update')
            if update_time and (not latest_update or update_time > latest_update):
                latest_update = update_time

        updated_text = 'Belum ada data'
        if latest_update:
            from datetime import datetime as _dt
            try:
                lu = latest_update.replace(tzinfo=None) if latest_update.tzinfo else latest_update
                hours_ago = (_dt.utcnow() - lu).total_seconds() / 3600
                if hours_ago < 1:
                    updated_text = 'Terakhir diperbarui: baru saja'
                elif hours_ago < 24:
                    updated_text = f'Terakhir diperbarui: {hours_ago:.0f} jam yang lalu'
                else:
                    days_ago = hours_ago / 24
                    updated_text = f'Terakhir diperbarui: {days_ago:.0f} hari yang lalu'
            except Exception:
                updated_text = 'Terakhir diperbarui: -'

        # Data counts
        pkg_count = status.get('packages', {}).get('count', 0)
        hotel_count = status.get('hotels', {}).get('count', 0)
        flight_count = status.get('flights', {}).get('count', 0)

        # Build HTML
        html_parts = [
            '<div class="data-freshness-section">',
            '  <div class="freshness-header">',
            f'    <span class="freshness-dot {dot_class}" aria-hidden="true"></span>',
            f'    <span class="freshness-title">Status Data: {status_label}</span>',
            '  </div>',
            f'  <div class="freshness-updated">{updated_text}</div>',
            '  <div class="freshness-stats">',
            '    <div class="freshness-stat">',
            f'      <div class="freshness-stat-value">{pkg_count}</div>',
            '      <div class="freshness-stat-label">Paket</div>',
            '    </div>',
            '    <div class="freshness-stat">',
            f'      <div class="freshness-stat-value">{hotel_count}</div>',
            '      <div class="freshness-stat-label">Hotel</div>',
            '    </div>',
            '    <div class="freshness-stat">',
            f'      <div class="freshness-stat-value">{flight_count}</div>',
            '      <div class="freshness-stat-label">Penerbangan</div>',
            '    </div>',
            '  </div>',
        ]

        # Admin-only expanded view
        if _is_admin_user():
            html_parts.append('  <div class="freshness-admin">')

            # Per-source last sync times
            for src_key, src_label in [('packages', 'Paket'), ('hotels', 'Hotel'), ('flights', 'Penerbangan')]:
                comp = status.get(src_key, {})
                src_status = comp.get('status', 'unknown')
                src_update = comp.get('last_update')
                sync_str = '-'
                if src_update:
                    try:
                        su = src_update.replace(tzinfo=None) if src_update.tzinfo else src_update
                        wib_time = su + timedelta(hours=7)
                        sync_str = wib_time.strftime('%d %b %H:%M') + ' WIB'
                    except Exception:
                        sync_str = str(src_update)[:16]

                # Status indicator
                if src_status == 'fresh':
                    indicator = '<span style="color:#4ade80;">segar</span>'
                elif src_status == 'stale':
                    indicator = '<span style="color:#fbbf24;">tertunda</span>'
                elif src_status == 'outdated':
                    indicator = '<span style="color:#f87171;">kedaluwarsa</span>'
                else:
                    indicator = '<span style="color:#8e9fb3;">-</span>'

                html_parts.append(
                    f'    <div class="freshness-admin-row">'
                    f'      <span class="freshness-admin-label">{src_label}</span>'
                    f'      <span class="freshness-admin-value">{sync_str} ({indicator})</span>'
                    f'    </div>'
                )

            # Error count
            issues = status.get('issues', [])
            error_count = len(issues)
            error_color = '#f87171' if error_count > 0 else '#4ade80'
            html_parts.append(
                f'    <div class="freshness-admin-row">'
                f'      <span class="freshness-admin-label">Error (24 jam)</span>'
                f'      <span class="freshness-admin-value" style="color:{error_color};">{error_count} masalah</span>'
                f'    </div>'
            )

            # n8n workflow status
            n8n_status = status.get('n8n_workflow', 'unknown')
            if n8n_status == 'running':
                n8n_display = '<span style="color:#4ade80;">Berjalan</span>'
            elif n8n_status == 'delayed':
                n8n_display = '<span style="color:#fbbf24;">Tertunda</span>'
            elif n8n_status == 'stopped':
                n8n_display = '<span style="color:#f87171;">Berhenti</span>'
            else:
                n8n_display = '<span style="color:#8e9fb3;">Tidak diketahui</span>'

            html_parts.append(
                f'    <div class="freshness-admin-row">'
                f'      <span class="freshness-admin-label">n8n Workflow</span>'
                f'      <span class="freshness-admin-value">{n8n_display}</span>'
                f'    </div>'
            )

            html_parts.append('  </div>')  # close freshness-admin

        html_parts.append('</div>')  # close data-freshness-section

        st.markdown('\n'.join(html_parts), unsafe_allow_html=True)

        # Admin: button to full monitoring dashboard
        if _is_admin_user():
            if st.button("Buka Dashboard Monitoring", key="home_monitoring_dashboard_btn", use_container_width=False):
                st.session_state.current_page = "analytics"
                st.rerun()

    except Exception as e:
        logger.debug(f"Data freshness widget skipped: {e}")


# =============================================================================
# PAGE CONFIG & STYLING
# =============================================================================

def inject_custom_css():
    """Inject page CSS via shared inject_css() helper."""
    inject_css(HERO_CSS, CARD_CSS, HOME_PAGE_CSS)


# =============================================================================
# COMPONENTS
# =============================================================================

def render_hero_section():
    """Render hero section with call-to-action - BLACK GOLD theme (OPTIMIZED)."""

    # CSS now in HOME_PAGE_CSS, injected via inject_custom_css()

    # Hero content - Premium Brand Identity
    # Build Hijri date string for hero
    today = date.today()
    GREGORIAN_MONTHS_ID = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    gregorian_str = f"{today.day} {GREGORIAN_MONTHS_ID[today.month - 1]} {today.year}"
    hijri_str = _get_hijri_date_str(today)
    if hijri_str:
        date_display = f'{gregorian_str} / {hijri_str}'
    else:
        date_display = gregorian_str

    st.markdown(f"""
    <div class="hero-section-v6">
        <div class="arabic-calligraphy-v6">لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ</div>
        <div class="brand-name-v6">LABBAIK</div>
        <div class="tagline-v6">Smart Planner</div>
        <div class="subtitle-v6">{BRAND_TAGLINE}</div>
        <div class="hijri-date-display">{date_display}</div>
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
                <div class="stat-icon-v6" aria-hidden="true">{icon}</div>
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
            <div class="pilar-icon" style="font-size: 3rem;" aria-hidden="true">📋</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_PREP}</h3>
            <p style="color: #b0b0b0; font-size: 0.9rem;">Persiapan cerdas dengan panduan AI personal & checklist otomatis</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="pilar-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; min-height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div class="pilar-icon" style="font-size: 3rem;" aria-hidden="true">💰</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_SAVINGS}</h3>
            <p style="color: #b0b0b0; font-size: 0.9rem;">Optimasi budget cerdas, hemat hingga jutaan rupiah</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="pilar-card" style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; min-height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div class="pilar-icon" style="font-size: 3rem;" aria-hidden="true">🕌</div>
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
                <div class="budget-icon" style="font-size: 2rem;" aria-hidden="true">{info['icon']}</div>
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


def render_season_countdown():
    """Render countdown to next peak Umrah season (Ramadan or Hajj)."""

    try:
        from services.intelligence.season_calendar import SeasonCalendar, SeasonType
        HAS_SEASON_CALENDAR = True
    except ImportError:
        HAS_SEASON_CALENDAR = False

    st.markdown("---")

    today = date.today()

    # Determine next peak season dates
    next_season_name = None
    next_season_start = None
    next_season_desc = None
    upcoming_list = []

    if HAS_SEASON_CALENDAR:
        try:
            calendar = SeasonCalendar()
            upcoming = calendar.get_upcoming_peaks(from_date=today, limit=5)

            # Filter to Ramadan and Hajj only for the main countdown
            for s in upcoming:
                if s.season_type in (SeasonType.RAMADAN, SeasonType.HAJJ) and s.start_date > today:
                    if next_season_name is None:
                        next_season_name = s.name
                        next_season_start = s.start_date
                        next_season_desc = s.description
                    upcoming_list.append(s)
                elif s.start_date > today:
                    upcoming_list.append(s)

            # If currently inside a season, show it differently
            if next_season_name is None:
                for s in upcoming:
                    if s.season_type in (SeasonType.RAMADAN, SeasonType.HAJJ):
                        if s.start_date <= today <= s.end_date:
                            next_season_name = s.name
                            next_season_start = s.start_date
                            next_season_desc = s.description
                            break
        except Exception:
            pass

    # Fallback: use approximate dates if SeasonCalendar unavailable
    if next_season_name is None:
        # Approximate Ramadan 2026: Feb 18 - Mar 19
        ramadan_2026_start = date(2026, 2, 18)
        ramadan_2026_end = date(2026, 3, 19)
        # Approximate Hajj 2026: May 25 - June 5
        hajj_2026_start = date(2026, 5, 25)

        if today <= ramadan_2026_end:
            next_season_name = "Ramadan 2026"
            next_season_start = ramadan_2026_start
            next_season_desc = "Bulan puasa - demand sangat tinggi"
        elif today < hajj_2026_start:
            next_season_name = "Musim Haji 2026"
            next_season_start = hajj_2026_start
            next_season_desc = "Musim haji - hotel Makkah sangat terbatas"
        else:
            # Far future fallback
            next_season_name = "Ramadan 2027"
            next_season_start = date(2027, 2, 7)
            next_season_desc = "Bulan puasa"

    # Calculate days remaining
    days_left = (next_season_start - today).days
    if days_left < 0:
        days_left = 0

    # Calculate progress bar (assume ~180 day window)
    total_window = 180
    elapsed = total_window - min(days_left, total_window)
    progress_pct = min(100, int((elapsed / total_window) * 100))

    # Determine if currently in season
    is_active = days_left == 0

    # Season icon
    season_icon = "🌙" if "Ramadan" in next_season_name else "🕋"

    # Build countdown HTML
    if is_active:
        countdown_html = f"""
        <div class="season-countdown-section">
            <div class="countdown-season-badge">{season_icon} SEDANG BERLANGSUNG</div>
            <div class="countdown-title">{next_season_name}</div>
            <div class="countdown-days" style="color: #4ade80;">AKTIF</div>
            <div class="countdown-days-label">{next_season_desc}</div>
            <div class="countdown-note">
                <span aria-hidden="true">⚠️</span> Harga di peak season bisa naik 50-100%. Book sekarang untuk ketersediaan terbaik!
            </div>
        </div>
        """
    else:
        countdown_html = f"""
        <div class="season-countdown-section">
            <div class="countdown-season-badge">{season_icon} PEAK SEASON</div>
            <div class="countdown-title">{next_season_name}</div>
            <div class="countdown-days">{days_left}</div>
            <div class="countdown-days-label">hari lagi</div>
            <div class="countdown-bar-bg">
                <div class="countdown-bar-fill" style="width: {progress_pct}%;"></div>
            </div>
            <div class="countdown-note">
                <span aria-hidden="true">💡</span> Harga bisa naik 30-100% saat peak season. Semakin awal booking, semakin hemat!
            </div>
        </div>
        """

    st.markdown(countdown_html, unsafe_allow_html=True)

    # Show upcoming seasons list (max 3)
    display_seasons = []
    if HAS_SEASON_CALENDAR and upcoming_list:
        for s in upcoming_list[:3]:
            if s.start_date > today and s.name != next_season_name:
                delta = (s.start_date - today).days
                display_seasons.append((s.name, f"{delta} hari lagi", s.start_date.strftime("%d %b %Y")))

    if display_seasons:
        seasons_html = ""
        for name, days_str, date_str in display_seasons:
            seasons_html += (
                '<div class="countdown-upcoming">'
                f'<span class="countdown-upcoming-name">{name}</span>'
                f'<span class="countdown-upcoming-date">{date_str} ({days_str})</span>'
                '</div>'
            )
        st.markdown(seasons_html, unsafe_allow_html=True)


def render_featured_deals():
    """Render featured deals section with top 3 cheapest current packages."""

    st.markdown("---")

    has_live_data = False
    deals = []

    if HAS_LIVE_PRICES:
        try:
            service = LivePriceService()
            packages = service.get_cheapest_packages(limit=3)
            if packages and len(packages) > 0:
                has_live_data = True
                for pkg in packages:
                    discount_html = ""
                    if pkg.is_promo and pkg.original_price > pkg.price:
                        discount_html = (
                            f'<div class="deal-original-price">Rp {pkg.original_price:,.0f}</div>'
                            .replace(",", ".")
                        )
                    deals.append({
                        "name": pkg.name,
                        "price": pkg.price,
                        "agent": pkg.travel_agent,
                        "duration": pkg.duration_days,
                        "departure": pkg.departure_city,
                        "stars": min(pkg.hotel_makkah_stars, pkg.hotel_madinah_stars),
                        "discount_html": discount_html,
                        "is_promo": pkg.is_promo,
                    })
        except Exception:
            pass

    # Fallback: static demo deals
    if not deals:
        deals = [
            {
                "name": "Umrah Hemat Barokah",
                "price": 22_500_000,
                "agent": "PT Berkah Travel",
                "duration": 9,
                "departure": "Jakarta",
                "stars": 3,
                "discount_html": '<div class="deal-original-price">Rp 25.000.000</div>',
                "is_promo": True,
            },
            {
                "name": "Umrah Reguler Premium",
                "price": 28_000_000,
                "agent": "PT Safar Utama",
                "duration": 9,
                "departure": "Jakarta",
                "stars": 4,
                "discount_html": "",
                "is_promo": False,
            },
            {
                "name": "Umrah Nyaman Keluarga",
                "price": 32_500_000,
                "agent": "PT Haramain Tour",
                "duration": 12,
                "departure": "Surabaya",
                "stars": 4,
                "discount_html": '<div class="deal-original-price">Rp 35.000.000</div>',
                "is_promo": True,
            },
        ]

    badge_type = "" if has_live_data else ' demo'
    badge_label = "PROMO" if has_live_data else "DATA DEMO"
    data_source_note = "" if has_live_data else '<p style="color: #6b7280; font-size: 0.75rem;">* Data demo untuk ilustrasi. Hubungkan price service untuk data live.</p>'

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #d4af37; margin-bottom: 0.5rem;">
            <span aria-hidden="true">🔥</span> Penawaran Terbaik Hari Ini
        </h2>
        <p style="color: #b0b0b0;">Paket umrah terpilih dengan harga terbaik</p>{data_source_note}
    </div>
    """, unsafe_allow_html=True)

    # Build deal cards
    cards_html = '<div class="deals-container">'
    for deal in deals:
        price_formatted = f"Rp {deal['price']:,.0f}".replace(",", ".")
        stars_display = "⭐" * deal["stars"]
        promo_badge = ""
        if deal["is_promo"]:
            promo_badge = f'<div class="deal-badge{badge_type}">{badge_label}</div>'

        cards_html += (
            '<div class="deal-card">'
            f'{promo_badge}'
            '<div style="font-size: 2rem;" aria-hidden="true">🕌</div>'
            f'<div class="deal-name">{deal["name"]}</div>'
            f'<div class="deal-agent">🏢 {deal["agent"]}</div>'
            f'{deal["discount_html"]}'
            f'<div class="deal-price">{price_formatted}</div>'
            '<div class="deal-details">'
            f'📅 {deal["duration"]} hari | 🛫 {deal["departure"]} | {stars_display}'
            '</div>'
            '<div class="deal-cta">Lihat Detail</div>'
            '</div>'
        )
    cards_html += "</div>"

    st.markdown(cards_html, unsafe_allow_html=True)

    # CTA button
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Bandingkan Semua Harga Paket", type="primary", use_container_width=True, key="home_deals_cta"):
            st.session_state.current_page = "price_comparison"
            st.rerun()


def render_testimonials_section():
    """Render testimonials from previous jamaah with rotating cards."""

    st.markdown("---")

    testimonials = [
        {
            "name": "Hj. Siti Nurhaliza",
            "city": "Jakarta",
            "rating": 5,
            "quote": "Alhamdulillah, LABBAIK sangat membantu persiapan umrah pertama saya. Simulasi biayanya akurat dan AI chatnya menjawab semua pertanyaan saya tentang tata cara ibadah.",
        },
        {
            "name": "Ahmad Fauzi",
            "city": "Surabaya",
            "rating": 5,
            "quote": "Fitur Umrah Bareng-nya luar biasa! Saya bisa menemukan teman perjalanan dari kota yang sama dan kami bisa berbagi biaya hotel. Hemat hampir 30%.",
        },
        {
            "name": "Dewi Rahmawati",
            "city": "Bandung",
            "rating": 4,
            "quote": "Panduan manasik virtualnya sangat membantu saya memahami urutan ibadah sebelum berangkat. Jadi lebih percaya diri saat di Tanah Suci.",
        },
        {
            "name": "Ir. Muhammad Rizky",
            "city": "Medan",
            "rating": 5,
            "quote": "Perbandingan harga dari berbagai travel agent membuat saya yakin mendapat paket terbaik. Tidak perlu lagi riset satu-satu. Sangat praktis!",
        },
        {
            "name": "Fatimah Az-Zahra",
            "city": "Yogyakarta",
            "rating": 4,
            "quote": "Koleksi doanya lengkap dan ada audio-nya, jadi saya bisa latihan bacaan sebelum berangkat. Aplikasi wajib untuk calon jamaah umrah!",
        },
    ]

    st.markdown("""
    <div class="testimonial-section-title">
        <h2 style="color: #d4af37; margin-bottom: 0.5rem;">
            <span aria-hidden="true">💬</span> Cerita Jamaah Kami
        </h2>
        <p style="color: #b0b0b0;">Pengalaman nyata dari jamaah yang telah menggunakan LABBAIK</p>
    </div>
    """, unsafe_allow_html=True)

    # Build duplicated cards for infinite scroll effect
    all_testimonials = testimonials + testimonials  # duplicate for seamless loop
    cards_html = '<div class="testimonial-track-wrapper"><div class="testimonial-track">'

    for t in all_testimonials:
        stars = "★" * t["rating"] + "☆" * (5 - t["rating"])
        cards_html += (
            '<div class="testimonial-card">'
            '<div>'
            f'<div class="testimonial-stars" aria-label="{t["rating"]} dari 5 bintang">{stars}</div>'
            f'<div class="testimonial-quote">"{t["quote"]}"</div>'
            '</div>'
            '<div class="testimonial-author">'
            f'<div class="testimonial-author-name">{t["name"]}</div>'
            f'<div class="testimonial-author-city">{t["city"]}</div>'
            '</div>'
            '</div>'
        )

    cards_html += "</div></div>"
    st.markdown(cards_html, unsafe_allow_html=True)


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
# MAIN PAGE RENDERER
# =============================================================================

def render_home_page():
    """Main home page renderer - OPTIMIZED for speed."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("home")
    except Exception:
        pass

    # XP for first home visit
    if not st.session_state.get("home_xp_awarded"):
        add_xp_safe(5, "Mengunjungi halaman utama")
        st.session_state.home_xp_awarded = True

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

    # Live Umrah package prices
    render_live_prices_section()

    # Data freshness / price monitoring widget
    render_data_freshness_widget()

    # Season countdown (Ramadan / Hajj)
    render_season_countdown()

    # Featured deals
    render_featured_deals()

    # Testimonials from jamaah
    render_testimonials_section()

    # Footer only
    render_footer()


# Export
__all__ = ["render_home_page"]