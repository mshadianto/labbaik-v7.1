"""
LABBAIK Smart Planner - The Only AI-Powered Umrah Companion You Need
=====================================================================
By MS Hadianto

Satu-satunya AI Companion untuk Umrah Anda

Features:
- Smart Prep: AI-guided preparation & checklist
- Smart Savings: Intelligent budget optimization
- Smart Journey: Real-time AI companion di Tanah Suci
"""

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
from functools import lru_cache
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# PERFORMANCE: CACHING UTILITIES
# =============================================================================

@st.cache_resource(ttl=600)  # Cache for 10 minutes (was 5)
def get_cached_db_connection():
    """Get cached database connection."""
    try:
        from services.database.repository import get_db
        return get_db()
    except:
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes (was 1)
def get_cached_visitor_stats():
    """Get cached visitor analytics stats."""
    try:
        db = get_cached_db_connection()
        if db:
            result = db.fetch_one("""
                SELECT
                    COALESCE(SUM(unique_visitors), 0) as visitors,
                    COALESCE(SUM(page_views), 0) as views,
                    MAX(updated_at) as last_update
                FROM visitor_stats
                WHERE date = CURRENT_DATE
            """)
            if result and result.get('last_update'):
                return {
                    'visitors': result.get('visitors', 0),
                    'views': result.get('views', 0),
                    'last_update': result.get('last_update'),
                    'source': 'database'
                }
    except:
        pass
    return {'source': 'offline'}

# Import version info
try:
    from core.version import get_display_version, APP_VERSION
except ImportError:
    def get_display_version():
        return "v7.1.1"
    APP_VERSION = "7.1.1"

# =============================================================================
# BRAND IDENTITY - LABBAIK Smart Planner
# =============================================================================
BRAND_NAME = "LABBAIK Smart Planner"
BRAND_TAGLINE_EN = "The Only AI-Powered Umrah Companion You Need"
BRAND_TAGLINE_ID = "Satu-satunya AI Companion untuk Umrah Anda"
BRAND_VERSION = "7.1.1"

# Smart Pillars (Premium Messaging)
SMART_PREP = "Smart Prep"           # Persiapan Cerdas
SMART_SAVINGS = "Smart Savings"     # Hemat Cerdas
SMART_JOURNEY = "Smart Journey"     # Perjalanan Cerdas

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="LABBAIK Smart Planner - AI-Powered Umrah Companion",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://labbaik.io/support',
        'Report a bug': 'https://labbaik.io/feedback',
        'About': "LABBAIK Smart Planner - The Only AI-Powered Umrah Companion You Need"
    }
)

# =============================================================================
# PERFORMANCE: SCROLL TO TOP ON PAGE CHANGE (OPTIMIZED)
# =============================================================================
def scroll_to_top():
    """Inject JavaScript to scroll to top - ONLY when page changes."""
    current_page = st.session_state.get("current_page", "home")
    if st.session_state.get("_last_rendered_page") != current_page:
        st.markdown("""
        <script>
            window.scrollTo({top: 0, behavior: 'instant'});
            var main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTo({top: 0, behavior: 'instant'});
        </script>
        """, unsafe_allow_html=True)
        st.session_state._last_rendered_page = current_page

# =============================================================================
# PERFORMANCE: CACHED META TAGS (inject once per session)
# =============================================================================
@st.cache_data
def get_meta_tags():
    """Return static meta tags - cached to avoid re-rendering."""
    return """
<meta property="og:title" content="LABBAIK Smart Planner - AI-Powered Umrah Companion" />
<meta property="og:description" content="The Only AI-Powered Umrah Companion You Need. Plan smarter, save up to 30%, travel better with LABBAIK Smart Planner." />
<meta property="og:image" content="https://labbaik.io/wp-content/uploads/labbaik-og-image.png" />
<meta property="og:url" content="https://app.labbaik.io" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="LABBAIK Smart Planner" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="LABBAIK Smart Planner" />
<meta name="twitter:description" content="AI-Powered Umrah Companion - Plan Smarter, Save More" />
<meta name="twitter:image" content="https://labbaik.io/wp-content/uploads/labbaik-og-image.png" />
<meta name="description" content="LABBAIK Smart Planner - The Only AI-Powered Umrah Companion You Need. Plan umrah mandiri with AI intelligence and save up to 30%." />
<meta name="keywords" content="umrah mandiri, umrah planner, AI umrah, umrah hemat, umrah bareng, labbaik" />
<meta name="author" content="LABBAIK.AI" />
"""

# Inject meta tags only once per session
if "_meta_injected" not in st.session_state:
    st.markdown(get_meta_tags(), unsafe_allow_html=True)
    st.session_state._meta_injected = True

# =============================================================================
# LAZY IMPORTS & FEATURE FLAGS
# =============================================================================

# Core Pages Imports
try:
    from ui.pages.home import render_home_page
    from ui.pages.chat import render_chat_page
    from ui.pages.simulator import render_simulator_page
    from ui.pages.umrah_mandiri import render_umrah_mandiri_page
    from ui.pages.umrah_bareng import render_umrah_bareng_page
    from ui.pages.booking import render_booking_page
except ImportError:
    # Fallback for core pages if development environment is incomplete
    def render_home_page(): st.title("🏠 Beranda (Dev Mode)")
    def render_chat_page(): st.title("🤖 Chat (Dev Mode)")
    def render_simulator_page(): st.title("💰 Simulator (Dev Mode)")
    def render_umrah_mandiri_page(): st.title("🧭 Umrah Mandiri (Dev Mode)")
    def render_umrah_bareng_page(): st.title("👥 Umrah Bareng (Dev Mode)")
    def render_booking_page(): st.title("📦 Booking (Dev Mode)")

# =============================================================================
# 🆕 AI Itinerary Builder
# =============================================================================
try:
    from ui.pages.itinerary_builder import render_itinerary_builder_page
    HAS_ITINERARY = True
except ImportError:
    HAS_ITINERARY = False
    def render_itinerary_builder_page():
        st.markdown("# 🗓️ AI Itinerary Builder")
        st.warning("⚠️ Fitur AI Itinerary Builder belum tersedia")
        st.info("Segera hadir: Generate jadwal Umrah harian otomatis!")

# =============================================================================
# 🆕 Hotel Price Comparison (Makcorps API)
# =============================================================================
try:
    from ui.pages.hotel_compare import render_hotel_compare_page
    HAS_HOTEL_COMPARE = True
except ImportError:
    HAS_HOTEL_COMPARE = False
    def render_hotel_compare_page():
        st.markdown("# 🏨 Hotel Price Comparison")
        st.warning("⚠️ Fitur Hotel Comparison belum tersedia")
        st.info("Segera hadir: Bandingkan harga hotel dari 200+ OTA!")

# =============================================================================
# 🆕 Unified Price Hub (replaces hotel_compare + price_comparison)
# =============================================================================
try:
    from ui.pages.price_hub import render_price_hub_page
    HAS_PRICE_HUB = True
except ImportError:
    HAS_PRICE_HUB = False
    def render_price_hub_page():
        st.markdown("# 💰 Pusat Perbandingan Harga")
        st.warning("⚠️ Fitur Price Hub belum tersedia")
        st.info("Segera hadir: Bandingkan hotel, penerbangan & paket!")

# =============================================================================
# Smart Checklist
# =============================================================================
try:
    from ui.pages.smart_checklist import render_smart_checklist_page
    HAS_CHECKLIST = True
except ImportError:
    HAS_CHECKLIST = False
    def render_smart_checklist_page():
        st.markdown("# 📋 Smart Checklist")
        st.warning("⚠️ Fitur Smart Checklist belum tersedia")
        st.info("Segera hadir: Checklist packing Umrah yang dipersonalisasi!")

# =============================================================================
# Hasan.VC Demo Features
# =============================================================================

# AI Umrah Readiness Score
try:
    from ui.pages.readiness_checker import render_readiness_checker_page
    HAS_READINESS = True
except ImportError:
    HAS_READINESS = False
    def render_readiness_checker_page():
        st.markdown("# 🎯 AI Umrah Readiness Score")
        st.warning("⚠️ Fitur AI Readiness Score belum tersedia")
        st.info("Segera hadir: Cek kesiapan umrah Anda dengan AI!")

# Umrah Cost Tracker
try:
    from ui.pages.cost_tracker import render_cost_tracker_page
    HAS_COST_TRACKER = True
except ImportError:
    HAS_COST_TRACKER = False
    def render_cost_tracker_page():
        st.markdown("# 💰 Umrah Cost Tracker")
        st.warning("⚠️ Fitur Cost Tracker belum tersedia")
        st.info("Segera hadir: Pantau pengeluaran umrah real-time!")

# Community Tanya Ustadz AI
try:
    from ui.pages.tanya_ustadz import render_tanya_ustadz_page
    HAS_TANYA_USTADZ = True
except ImportError:
    HAS_TANYA_USTADZ = False
    def render_tanya_ustadz_page():
        st.markdown("# 🤲 Tanya Ustadz AI")
        st.warning("⚠️ Fitur Tanya Ustadz belum tersedia")
        st.info("Segera hadir: Forum tanya jawab fiqih umrah!")

# Smart Visa & Doc Checker
try:
    from ui.pages.doc_checker import render_doc_checker_page
    HAS_DOC_CHECKER = True
except ImportError:
    HAS_DOC_CHECKER = False
    def render_doc_checker_page():
        st.markdown("# 📋 Smart Visa & Doc Checker")
        st.warning("⚠️ Fitur Doc Checker belum tersedia")
        st.info("Segera hadir: Cek kelengkapan dokumen umrah!")

# Interactive Map (Makkah & Madinah)
try:
    from ui.pages.peta_interaktif import render_peta_interaktif_page
    HAS_PETA = True
except ImportError:
    HAS_PETA = False
    def render_peta_interaktif_page():
        st.markdown("# 🗺️ Peta Interaktif")
        st.warning("⚠️ Fitur Peta Interaktif belum tersedia")
        st.info("Segera hadir: Peta lokasi penting di Makkah & Madinah!")

# Crowd Prediction
try:
    from features.crowd_prediction import (
        render_crowd_prediction_page,
        render_crowd_widget,
    )
    HAS_CROWD_PREDICTION = True
except ImportError:
    HAS_CROWD_PREDICTION = False
    def render_crowd_prediction_page(): st.warning("⚠️ Fitur Crowd Prediction belum tersedia")
    def render_crowd_widget(location="makkah", compact=True): pass

# SOS Emergency
try:
    from features.sos_emergency import (
        render_sos_page,
        render_sos_button,
    )
    HAS_SOS = True
except ImportError:
    HAS_SOS = False
    def render_sos_page(): st.warning("⚠️ Fitur SOS Emergency belum tersedia")
    def render_sos_button(size="small"): pass

# Group Tracking
try:
    from features.group_tracking import (
        render_group_tracking_page,
        render_tracking_mini_widget,
    )
    HAS_TRACKING = True
except ImportError:
    HAS_TRACKING = False
    def render_group_tracking_page(): st.warning("⚠️ Fitur Group Tracking belum tersedia")
    def render_tracking_mini_widget(): pass

# 3D Manasik
try:
    from features.manasik_3d import (
        render_manasik_page,
        render_manasik_mini_widget,
    )
    HAS_MANASIK = True
except ImportError:
    HAS_MANASIK = False
    def render_manasik_page(): st.warning("⚠️ Fitur 3D Manasik belum tersedia")
    def render_manasik_mini_widget(): pass

# Smart Comparison
try:
    from features.smart_comparison import render_smart_comparison_page
    HAS_COMPARISON = True
except ImportError:
    HAS_COMPARISON = False
    def render_smart_comparison_page(): st.warning("⚠️ Fitur Smart Comparison belum tersedia")

# Analytics Dashboard
try:
    from ui.pages.analytics_dashboard import render_analytics_dashboard
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False
    def render_analytics_dashboard(): st.warning("⚠️ Fitur Analytics Dashboard belum tersedia")

# User Auth & Management
try:
    from ui.pages.auth_page import (
        render_auth_page,
        render_login_widget,
        render_user_badge,
    )
    from ui.pages.user_analytics import render_user_analytics_page
    from services.user.user_service import get_current_user, is_logged_in
    from services.user.access_control import (
        check_page_access,
        render_access_denied,
        get_page_access_role,
    )
    HAS_USER_MANAGEMENT = True
except ImportError:
    HAS_USER_MANAGEMENT = False
    def render_auth_page(): st.warning("⚠️ Fitur User Management belum tersedia")
    def render_login_widget(): pass
    def render_user_badge(): pass
    def render_user_analytics_page(): st.warning("⚠️ Fitur User Analytics belum tersedia")
    def get_current_user(): return None
    def is_logged_in(): return False
    def check_page_access(page): return True, ""
    def render_access_denied(reason, name=""): st.error("Access denied")
    def get_page_access_role(page): return None

# Subscription & Referral
try:
    from ui.pages.subscription_page import render_subscription_page, render_subscription_widget
    from ui.pages.referral_page import render_referral_page, render_referral_widget
    HAS_SUBSCRIPTION = True
except ImportError:
    HAS_SUBSCRIPTION = False
    def render_subscription_page(): st.warning("⚠️ Fitur Subscription belum tersedia")
    def render_subscription_widget(): pass
    def render_referral_page(): st.warning("⚠️ Fitur Referral belum tersedia")
    def render_referral_widget(): pass

# Partner System
try:
    from ui.pages.partnership import render_partnership_page
    from ui.pages.partner_dashboard import render_partner_dashboard
    from ui.pages.package_builder import render_package_builder_page
    from ui.pages.api_docs import render_api_docs_page
    HAS_PARTNER_SYSTEM = True
except ImportError:
    HAS_PARTNER_SYSTEM = False
    def render_partnership_page(): st.warning("⚠️ Partnership Portal belum tersedia")
    def render_partner_dashboard(): st.warning("⚠️ Partner Dashboard belum tersedia")
    def render_package_builder_page(): st.warning("⚠️ Package Builder belum tersedia")
    def render_api_docs_page(): st.warning("⚠️ API Docs belum tersedia")

# =============================================================================
# CRM & Travel Operations System
# =============================================================================
try:
    from ui.pages.crm_leads import render_crm_leads_page
    from ui.pages.crm_bookings import render_crm_bookings_page
    from ui.pages.crm_jamaah import render_crm_jamaah_page
    from ui.pages.crm_quotes import render_crm_quotes_page
    from ui.pages.crm_analytics import render_crm_analytics_page
    from ui.pages.crm_broadcast import render_crm_broadcast_page
    from ui.pages.crm_competitors import render_crm_competitors_page
    HAS_CRM = True
except ImportError:
    HAS_CRM = False
    def render_crm_leads_page(): st.warning("⚠️ CRM Leads belum tersedia")
    def render_crm_bookings_page(): st.warning("⚠️ CRM Bookings belum tersedia")
    def render_crm_jamaah_page(): st.warning("⚠️ CRM Jamaah belum tersedia")
    def render_crm_quotes_page(): st.warning("⚠️ CRM Quotes belum tersedia")
    def render_crm_analytics_page(): st.warning("⚠️ CRM Analytics belum tersedia")
    def render_crm_broadcast_page(): st.warning("⚠️ CRM Broadcast belum tersedia")
    def render_crm_competitors_page(): st.warning("⚠️ CRM Competitors belum tersedia")

# =============================================================================
# v7.5 Price Aggregation System
# =============================================================================
try:
    from ui.pages.price_comparison import render_price_comparison_page, render_best_prices_widget
    HAS_PRICE_AGGREGATION = True
except ImportError:
    HAS_PRICE_AGGREGATION = False
    def render_price_comparison_page(): st.warning("⚠️ Price Comparison belum tersedia")
    def render_best_prices_widget(): pass

# WhatsApp Integration
try:
    from services.whatsapp import (
        render_whatsapp_settings,
        render_whatsapp_status,
        get_whatsapp_service,
    )
    HAS_WHATSAPP = True
except ImportError:
    HAS_WHATSAPP = False
    def render_whatsapp_settings(): st.warning("⚠️ WhatsApp Integration belum tersedia")
    def render_whatsapp_status(): pass
    def get_whatsapp_service(): return None

# Doa Player
try:
    from features.doa_player import (
        render_doa_player_page,
        render_doa_mini_widget,
    )
    HAS_DOA_PLAYER = True
except ImportError:
    HAS_DOA_PLAYER = False
    def render_doa_player_page():
        st.markdown("# 🤲 Doa & Dzikir")
        st.info("🚧 Fitur ini sedang dalam pengembangan...")
    def render_doa_mini_widget(): pass

# PWA Support
try:
    from features.pwa_support import (
        init_pwa,
        render_pwa_settings_page,
        render_install_button,
    )
    HAS_PWA = True
except ImportError:
    HAS_PWA = False
    def init_pwa(): pass
    def render_pwa_settings_page(): st.warning("⚠️ PWA Support belum tersedia")
    def render_install_button(): pass

# Page Tracking Service
try:
    from services.analytics import track_page
    HAS_TRACKING_SERVICE = True
except ImportError:
    HAS_TRACKING_SERVICE = False
    def track_page(page_name): pass


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        # Navigation
        "current_page": "home",
        
        # Authentication
        "user": None,
        "user_role": None,
        "is_authenticated": False,
        "auth_mode": "login",
        
        # Chat
        "chat_messages": [],
        
        # Visitor tracking
        "visitor_counted": False,
        
        # Gamification
        "xp": 0,
        "level": 1,
        "achievements": [],
        "daily_challenges_completed": [],
        
        # Theme
        "theme": "dark",
        
        # SOS Emergency
        "sos_contacts": [],
        "sos_user_info": {},
        "sos_triggered": False,
        
        # Group Tracking
        "tracking_groups": {},
        "current_group_id": None,
        "my_member_id": None,
        
        # Manasik Progress
        "manasik_progress": {},
        
        # Analytics
        "tracked_pages": set(),
        
        # Crowd Prediction
        "crowd_location": "makkah",
        
        # Itinerary Builder
        "itinerary_generated": False,
        "current_itinerary": None,
        
        # 🆕 Smart Checklist
        "checklist_items": {},
        "checklist_profile": {
            "gender": "male",
            "duration": 9,
            "season": "normal",
            "health_conditions": []
        },

        # Feature-specific state is lazy-initialized by each page's own init function
        # (e.g. init_readiness_state, init_cost_tracker_state, init_tanya_ustadz_state,
        #  init_doc_checker_state, init_peta_state)
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# VISITOR TRACKING
# =============================================================================

def track_visitor():
    """Track unique visitors."""
    if not st.session_state.get("visitor_counted"):
        st.session_state.visitor_counted = True
        
        # Track with analytics service
        if HAS_TRACKING_SERVICE:
            try:
                track_page("home")
            except:
                pass


# =============================================================================
# GAMIFICATION SYSTEM
# =============================================================================

def get_level_title(level: int) -> str:
    """Get title based on level."""
    titles = {
        1: "Pemula", 2: "Pelajar", 3: "Praktisi", 4: "Ahli", 5: "Master",
        6: "Guru", 7: "Ulama", 8: "Syaikh", 9: "Mufti", 10: "Grand Master"
    }
    return titles.get(level, "Legend")


def add_xp(amount: int, reason: str = ""):
    """Add XP and check for level up."""
    st.session_state.xp = st.session_state.get("xp", 0) + amount
    
    # Check level up
    current_level = st.session_state.get("level", 1)
    xp_needed = current_level * 100
    
    if st.session_state.xp >= xp_needed and current_level < 10:
        st.session_state.level = current_level + 1
        st.session_state.xp = st.session_state.xp - xp_needed
        st.toast(f"🎉 Level Up! Sekarang Level {st.session_state.level}!", icon="⬆️")
    
    if reason:
        st.toast(f"🎯 +{amount} poin! {reason}", icon="✨")


# =============================================================================
# VISITOR ANALYTICS STATUS
# =============================================================================

def render_visitor_analytics_status():
    """Render live visitor analytics status - CACHED for performance."""
    try:
        # Use cached stats instead of direct DB query
        stats = get_cached_visitor_stats()

        if stats.get('source') == 'database':
            last_update = stats.get('last_update')
            if isinstance(last_update, datetime):
                wib_time = last_update + timedelta(hours=7)
                time_str = wib_time.strftime('%d %b %H:%M')

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a5f3c 0%, #2d8659 100%);
                            padding: 0.5rem; border-radius: 10px; text-align: center;
                            border: 1px solid #4ade80;">
                    <div style="color: #4ade80; font-weight: bold; font-size: 0.9rem;">
                        🟢 Live
                    </div>
                </div>
                """, unsafe_allow_html=True)
                return

        # Fallback: Show simple status
        st.caption("📊 Active")

    except Exception:
        st.caption("📊 Active")


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

def render_sidebar():
    """Render sidebar with Smart Planner navigation structure."""
    with st.sidebar:
        # Logo & Brand - Premium Identity
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 3rem;">🕋</div>
            <h2 style="color: #d4af37; margin: 0;">{BRAND_NAME}</h2>
            <p style="color: #888; font-size: 0.8rem; margin-top: 0.25rem;">{BRAND_TAGLINE_ID}</p>
            <span style="background: linear-gradient(135deg, #d4af37, #f5d77a); color: #000;
                        padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.65rem;
                        font-weight: bold;">v{BRAND_VERSION}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # User Login Widget
        if HAS_USER_MANAGEMENT:
            render_login_widget()
            st.markdown("")

        # Get user info for access control
        user = get_current_user() if HAS_USER_MANAGEMENT else None
        user_role = user.role.value if user else "guest"

        # 🆘 SOS Emergency Button (Always Visible at Top)
        if HAS_SOS:
            if st.button("🆘 DARURAT / SOS", key="sos_sidebar_main", use_container_width=True, type="primary"):
                st.session_state.current_page = "sos"
                st.rerun()
            st.markdown("")

        # Live Visitor Analytics Status
        render_visitor_analytics_status()

        st.markdown("---")

        # 🏠 Home Button
        is_home = st.session_state.get("current_page") == "home"
        if st.button("🏠 Beranda", key="nav_home", use_container_width=True, type="primary" if is_home else "secondary"):
            st.session_state.current_page = "home"
            st.rerun()

        st.markdown("")

        # =====================================================================
        # SMART PREP - Persiapan Cerdas
        # =====================================================================
        with st.expander(f"📋 {SMART_PREP}", expanded=False):
            st.caption("Persiapan cerdas dengan panduan AI personal")

            pilar1_items = [
                ("📋", "Smart Checklist", "checklist", HAS_CHECKLIST),
                ("📖", "Panduan Manasik", "umrah_mandiri", True),
                ("🕋", "Manasik 3D", "manasik", HAS_MANASIK),
                ("🎯", "Readiness Score", "readiness", HAS_READINESS),
                ("📄", "Doc Checker", "doc_checker", HAS_DOC_CHECKER),
            ]

            for icon, label, page_key, is_available in pilar1_items:
                if is_available:
                    is_active = st.session_state.get("current_page") == page_key
                    if st.button(f"{icon} {label}", key=f"p1_{page_key}", use_container_width=True,
                                type="primary" if is_active else "secondary"):
                        st.session_state.current_page = page_key
                        st.rerun()

        # =====================================================================
        # SMART SAVINGS - Hemat Cerdas (Expanded by Default - Main Focus)
        # =====================================================================
        with st.expander(f"💰 {SMART_SAVINGS}", expanded=True):
            # LOSS AVERSION NUDGE - Creates urgency
            st.markdown("""
            <div style="background: linear-gradient(90deg, #8B0000 0%, #4a1010 100%);
                        padding: 0.6rem 0.8rem; border-radius: 8px; margin-bottom: 0.8rem;
                        border-left: 3px solid #ff4444;">
                <span style="color: #ffcc00; font-size: 0.85rem;">
                    ⚠️ <strong>Waspada:</strong> Biaya Umrah naik rata-rata 5% tiap tahun karena inflasi.
                    Kunci estimasi hargamu sekarang agar rencana tidak meleset.
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Primary CTA - Budget Optimizer
            is_simulator = st.session_state.get("current_page") == "simulator"
            if st.button("📉 Kunci Estimasi Harga Sekarang", key="p2_simulator", use_container_width=True,
                        type="primary"):
                st.session_state.current_page = "simulator"
                st.rerun()

            # Umrah Bareng
            is_bareng = st.session_state.get("current_page") == "umrah_bareng"
            if st.button("👥 Umrah Bareng", key="p2_umrah_bareng", use_container_width=True,
                        type="primary" if is_bareng else "secondary"):
                st.session_state.current_page = "umrah_bareng"
                st.rerun()

            # Unified Price Hub (Hotel + Flight + Package)
            if HAS_PRICE_HUB:
                is_price_hub = st.session_state.get("current_page") == "price_hub"
                if st.button("💰 Pusat Harga", key="p2_price_hub", use_container_width=True,
                            type="primary" if is_price_hub else "secondary"):
                    st.session_state.current_page = "price_hub"
                    st.rerun()

            # Booking
            is_booking = st.session_state.get("current_page") == "booking"
            if st.button("📦 Booking", key="p2_booking", use_container_width=True,
                        type="primary" if is_booking else "secondary"):
                st.session_state.current_page = "booking"
                st.rerun()

            # Cost Tracker
            if HAS_COST_TRACKER:
                is_tracker = st.session_state.get("current_page") == "cost_tracker"
                if st.button("💳 Cost Tracker", key="p2_cost_tracker", use_container_width=True,
                            type="primary" if is_tracker else "secondary"):
                    st.session_state.current_page = "cost_tracker"
                    st.rerun()

        # =====================================================================
        # SMART JOURNEY - Perjalanan Cerdas
        # =====================================================================
        with st.expander(f"🕌 {SMART_JOURNEY}", expanded=False):
            st.caption("AI companion 24/7 selama di Tanah Suci")

            pilar3_items = [
                ("🤖", "AI Assistant", "chat", True, False),
                ("🧑‍🏫", "Tanya Ustadz", "tanya_ustadz", HAS_TANYA_USTADZ, False),
                ("📊", "Prediksi Keramaian", "crowd", HAS_CROWD_PREDICTION, False),
                ("🗺️", "Peta Interaktif", "peta", HAS_PETA, False),
                ("🤲", "Doa & Dzikir", "doa", HAS_DOA_PLAYER, False),
                ("📍", "Group Tracking", "tracking", HAS_TRACKING, True),  # Premium
            ]

            for icon, label, page_key, is_available, is_premium in pilar3_items:
                if is_available:
                    is_active = st.session_state.get("current_page") == page_key
                    premium_locked = is_premium and user_role not in ["premium", "partner", "admin"]
                    lock_icon = " 🔒" if premium_locked else ""

                    if st.button(f"{icon} {label}{lock_icon}", key=f"p3_{page_key}", use_container_width=True,
                                type="primary" if is_active else "secondary"):
                        st.session_state.current_page = page_key
                        st.rerun()

        st.markdown("---")

        # =====================================================================
        # AKUN SECTION
        # =====================================================================
        with st.expander("👤 Akun Saya", expanded=False):
            if HAS_USER_MANAGEMENT:
                is_auth = st.session_state.get("current_page") == "auth"
                if st.button("👤 Profile", key="acc_auth", use_container_width=True,
                            type="primary" if is_auth else "secondary"):
                    st.session_state.current_page = "auth"
                    st.rerun()

            # Upgrade Premium (only for free users)
            if HAS_SUBSCRIPTION and user_role in ["guest", "free", "user"]:
                is_sub = st.session_state.get("current_page") == "subscription"
                if st.button("⭐ Upgrade Premium", key="acc_subscription", use_container_width=True,
                            type="primary" if is_sub else "secondary"):
                    st.session_state.current_page = "subscription"
                    st.rerun()

            # Referral
            if HAS_SUBSCRIPTION:
                is_ref = st.session_state.get("current_page") == "referral"
                if st.button("🎁 Referral", key="acc_referral", use_container_width=True,
                            type="primary" if is_ref else "secondary"):
                    st.session_state.current_page = "referral"
                    st.rerun()

            # PWA Install
            if HAS_PWA:
                is_install = st.session_state.get("current_page") == "install"
                if st.button("📲 Install App", key="acc_install", use_container_width=True,
                            type="primary" if is_install else "secondary"):
                    st.session_state.current_page = "install"
                    st.rerun()

        # =====================================================================
        # ADMIN/PARTNER SECTION (Only for authorized users)
        # =====================================================================
        if HAS_USER_MANAGEMENT and is_logged_in() and user and user.role.value in ["admin", "partner"]:
            with st.expander("🔐 Admin/Mitra", expanded=False):
                if user.role.value in ["partner", "admin"]:
                    if st.button("📊 Partner Dashboard", key="adm_partner_dash", use_container_width=True):
                        st.session_state.current_page = "partner_dashboard"
                        st.rerun()
                    if st.button("📦 Package Builder", key="adm_package_builder", use_container_width=True):
                        st.session_state.current_page = "package_builder"
                        st.rerun()
                    if st.button("📖 API Docs", key="adm_api_docs", use_container_width=True):
                        st.session_state.current_page = "api_docs"
                        st.rerun()

                if user.role.value == "admin":
                    if st.button("👥 User Analytics", key="adm_user_analytics", use_container_width=True):
                        st.session_state.current_page = "user_analytics"
                        st.rerun()
                    if st.button("📈 Analytics", key="adm_analytics", use_container_width=True):
                        st.session_state.current_page = "analytics"
                        st.rerun()

                if st.button("📱 WhatsApp", key="adm_whatsapp", use_container_width=True):
                    st.session_state.current_page = "whatsapp"
                    st.rerun()

            # CRM Menu for Partners/Admins
            if HAS_CRM:
                with st.expander("💼 CRM Travel", expanded=False):
                    crm_items = [
                        ("📊", "Dashboard CRM", "crm_analytics"),
                        ("👥", "Manajemen Lead", "crm_leads"),
                        ("📅", "Booking & Bayar", "crm_bookings"),
                        ("👤", "Database Jamaah", "crm_jamaah"),
                        ("📋", "Quote & Invoice", "crm_quotes"),
                        ("📢", "WA Broadcast", "crm_broadcast"),
                        ("📈", "Monitor Kompetitor", "crm_competitors"),
                    ]

                    for icon, label, page_key in crm_items:
                        if st.button(f"{icon} {label}", key=f"crm_{page_key}", use_container_width=True):
                            st.session_state.current_page = page_key
                            st.rerun()

        # Partner CTA for non-partners (B2B promotion)
        if not user or (user and user.role.value not in ["partner", "admin"]):
            if HAS_PARTNER_SYSTEM:
                st.markdown("---")
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                                padding: 0.75rem; border-radius: 12px; text-align: center;">
                        <div style="color: #000; font-weight: bold; font-size: 0.9rem;">Jadi Mitra Travel</div>
                        <div style="color: #333; font-size: 0.75rem;">Komisi hingga 15%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("🤝 Gabung Mitra", key="nav_partner_cta", use_container_width=True):
                    st.session_state.current_page = "partner"
                    st.rerun()

        st.markdown("---")

        # Gamification Stats
        st.markdown("### 🏆 Progress Anda")

        level = st.session_state.get("level", 1)
        xp = st.session_state.get("xp", 0)
        xp_for_next = level * 100

        st.markdown(f"**Level {level}** - {get_level_title(level)}")
        st.progress(min(xp / xp_for_next, 1.0))
        st.caption(f"{xp}/{xp_for_next} XP")

        achievements = st.session_state.get("achievements", [])
        if achievements:
            badges = " ".join(achievements[:5])
            st.caption(f"🎖️ {badges}")

        st.markdown("---")

        # Footer
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <p style="color: #666; font-size: 0.75rem;">
                {get_display_version()}<br>
                © 2025 MS Hadianto
            </p>
            <p style="color: #444; font-size: 0.65rem;">
                Platform Umrah Cerdas Indonesia<br>
                Powered by AI
            </p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# PAGE ROUTER
# =============================================================================

def render_page():
    """Render the current page based on session state."""
    page = st.session_state.get("current_page", "home")

    # SCROLL TO TOP - Critical for UX
    scroll_to_top()

    # Track page view - ONLY when page changes (performance optimization)
    if HAS_TRACKING_SERVICE and st.session_state.get("_tracked_page") != page:
        try:
            track_page(page)
            st.session_state._tracked_page = page
        except:
            pass
    
    # Page routing map
    page_map = {
        # Core pages
        "home": render_home_page,
        "chat": render_chat_page,
        "simulator": render_simulator_page,
        "umrah_mandiri": render_umrah_mandiri_page,
        "umrah_bareng": render_umrah_bareng_page,
        "booking": render_booking_page,

        # New feature pages
        "itinerary": render_itinerary_builder_page,
        "checklist": render_smart_checklist_page,
        "crowd": render_crowd_prediction_page,
        "sos": render_sos_page,
        "tracking": render_group_tracking_page,
        "manasik": render_manasik_page,
        "compare": render_smart_comparison_page,
        "analytics": render_analytics_dashboard,
        "whatsapp": render_whatsapp_settings,
        "doa": render_doa_player_page,
        "install": render_pwa_settings_page,

        # User management pages
        "auth": render_auth_page,
        "user_analytics": render_user_analytics_page,

        # Subscription & Growth
        "subscription": render_subscription_page,
        "referral": render_referral_page,

        # Partner System
        "partner": render_partnership_page,
        "partner_dashboard": render_partner_dashboard,
        "package_builder": render_package_builder_page,
        "api_docs": render_api_docs_page,

        # CRM System
        "crm_analytics": render_crm_analytics_page,
        "crm_leads": render_crm_leads_page,
        "crm_bookings": render_crm_bookings_page,
        "crm_jamaah": render_crm_jamaah_page,
        "crm_quotes": render_crm_quotes_page,
        "crm_broadcast": render_crm_broadcast_page,
        "crm_competitors": render_crm_competitors_page,

        # v7.5 Price Aggregation
        "price_comparison": render_price_comparison_page,

        # v7.1 Hotel Comparison (Makcorps)
        "hotel_compare": render_hotel_compare_page,

        # v7.6 Unified Price Hub
        "price_hub": render_price_hub_page,

        # Hasan.VC Demo Features
        "readiness": render_readiness_checker_page,
        "cost_tracker": render_cost_tracker_page,
        "tanya_ustadz": render_tanya_ustadz_page,
        "doc_checker": render_doc_checker_page,
        "peta": render_peta_interaktif_page,
    }
    
    renderer = page_map.get(page, render_home_page)

    # Check page access control
    if HAS_USER_MANAGEMENT and page not in ["home", "auth"]:
        has_access, reason = check_page_access(page)
        if not has_access:
            page_names = {
                "chat": "AI Chat",
                "tracking": "Group Tracking",
                "itinerary": "AI Itinerary",
                "user_analytics": "User Analytics",
                "analytics": "Analytics Dashboard",
                "whatsapp": "WhatsApp Settings",
                "partner_dashboard": "Partner Dashboard",
                "readiness": "AI Readiness Score",
                "cost_tracker": "Cost Tracker",
                "tanya_ustadz": "Tanya Ustadz",
                "doc_checker": "Doc Checker",
                "peta": "Peta Interaktif",
            }
            render_access_denied(reason, page_names.get(page, page))
            return

    try:
        renderer()
    except Exception as e:
        # Improved Error Handling UI
        st.error(f"❌ Terjadi kesalahan saat memuat halaman: {str(e)}")
        st.info("Sistem telah mencatat error ini. Silakan kembali ke Beranda.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Kembali ke Beranda", key="err_home", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()
        with col2:
            if st.button("🆘 Emergency", key="err_sos", type="primary", use_container_width=True):
                st.session_state.current_page = "sos"
                st.rerun()


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Initialize PWA support
    if HAS_PWA:
        init_pwa()
    
    # Track visitor
    track_visitor()
    
    # Award XP for visiting (once per session per page)
    page = st.session_state.get("current_page", "home")
    visit_key = f"visited_{page}"
    if not st.session_state.get(visit_key):
        st.session_state[visit_key] = True
        add_xp(5, f"Mengunjungi {page}")
    
    # Check for SOS trigger from any page
    if st.session_state.get("sos_triggered") and st.session_state.get("current_page") != "sos":
        st.session_state.current_page = "sos"
        st.rerun()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_page()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
