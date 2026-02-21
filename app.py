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
import logging
from datetime import datetime, timedelta
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# PERFORMANCE: CACHING UTILITIES
# =============================================================================

@st.cache_resource(ttl=600)  # Cache for 10 minutes
def get_cached_db_connection():
    """Get cached database connection."""
    try:
        from services.database.repository import get_db
        return get_db()
    except Exception as e:
        logger.warning(f"Database connection unavailable: {e}")
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
    except Exception as e:
        logger.debug(f"Visitor stats unavailable: {e}")
    return {'source': 'offline'}

# Import version info
try:
    from core.version import get_display_version, APP_VERSION
except ImportError:
    def get_display_version():
        return "v7.8.0"
    APP_VERSION = "7.8.0"

# =============================================================================
# BRAND IDENTITY - LABBAIK Smart Planner
# =============================================================================
BRAND_NAME = "LABBAIK Smart Planner"
BRAND_TAGLINE_EN = "The Only AI-Powered Umrah Companion You Need"
BRAND_TAGLINE_ID = "Satu-satunya AI Companion untuk Umrah Anda"
BRAND_VERSION = APP_VERSION

# Smart Pillars (Premium Messaging)
SMART_PREP = "Smart Prep"           # Persiapan Cerdas
SMART_SAVINGS = "Smart Savings"     # Hemat Cerdas
SMART_JOURNEY = "Smart Journey"     # Perjalanan Cerdas

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="LABBAIK Smart Planner - AI-Powered Umrah Companion",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="auto",
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
            window.scrollTo({top: 0, behavior: 'smooth'});
            var main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTo({top: 0, behavior: 'smooth'});
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

# Inject meta tags on every rerun (Streamlit rebuilds the page each time)
st.markdown(get_meta_tags(), unsafe_allow_html=True)

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

# Kalkulator Kurs & Harga
try:
    from ui.pages.kurs_calculator import render_kurs_calculator_page
    HAS_KURS = True
except ImportError:
    HAS_KURS = False
    def render_kurs_calculator_page():
        st.markdown("# 🏦 Kalkulator Kurs & Harga")
        st.warning("⚠️ Fitur Kalkulator Kurs belum tersedia")
        st.info("Segera hadir: Konversi kurs dan referensi harga di Saudi!")

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

# Umrah Complete Guide
try:
    from features.umrah_complete import render_umrah_complete_page
    HAS_UMRAH_COMPLETE = True
except ImportError:
    HAS_UMRAH_COMPLETE = False
    def render_umrah_complete_page():
        st.markdown("# 🕋 Panduan Umrah Lengkap")
        st.info("🚧 Fitur ini sedang dalam pengembangan.")

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
    from ui.pages.doa_player import (
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

# User Settings Page
try:
    from ui.pages.settings_page import render_settings_page
    HAS_SETTINGS = True
except ImportError:
    HAS_SETTINGS = False
    def render_settings_page():
        st.markdown("# ⚙️ Pengaturan")
        st.info("Fitur pengaturan sedang dalam pengembangan.")

# Group Matching
try:
    from ui.pages.group_matching import render_group_matching_page
    HAS_GROUP_MATCHING = True
except ImportError:
    HAS_GROUP_MATCHING = False
    def render_group_matching_page():
        st.markdown("# 🤝 Group Matching")
        st.info("Fitur group matching sedang dalam pengembangan.")


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

        # First visit welcome
        "is_first_visit": True,
        "first_visit_dismissed": False,

        # Onboarding tour
        "onboarding_step": 0,  # 0=not started, 1-5=active steps, 6=done
        
        # Gamification
        "xp": 0,
        "level": 1,
        "achievements": [],
        "xp_log": [],  # List of {"amount": int, "reason": str, "timestamp": str}
        "daily_streak": 0,
        "last_active_date": None,
        "unlocked_badges": set(),       # Set of badge IDs from ACHIEVEMENT_BADGES
        "completed_challenges": set(),  # Set of weekly challenge IDs

        # User Preferences (Settings)
        "pref_notif_email": True,
        "pref_notif_whatsapp": False,
        "pref_notif_inapp": True,
        "pref_display_compact": False,
        
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

        # Page Feedback
        "page_feedback": {},
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
            except Exception as e:
                logger.debug(f"Visitor tracking failed: {e}")


# =============================================================================
# ACHIEVEMENT BADGES
# =============================================================================

ACHIEVEMENT_BADGES = [
    {
        "id": "penjelajah_pertama",
        "name": "Penjelajah Pertama",
        "icon": "\U0001F9ED",  # compass
        "description": "Kunjungi 5 halaman berbeda",
        "xp_reward": 25,
        "condition_key": "pages_visited_count",
    },
    {
        "id": "perencana_handal",
        "name": "Perencana Handal",
        "icon": "\U0001F3AF",  # bullseye
        "description": "Selesaikan readiness checker",
        "xp_reward": 30,
        "condition_key": "readiness_completed",
    },
    {
        "id": "ahli_budget",
        "name": "Ahli Budget",
        "icon": "\U0001F4B0",  # money bag
        "description": "Atur budget di cost tracker",
        "xp_reward": 20,
        "condition_key": "budget_set",
    },
    {
        "id": "penghafal_doa",
        "name": "Penghafal Doa",
        "icon": "\U0001F4D6",  # open book
        "description": "Lihat 10 frase Arab",
        "xp_reward": 15,
        "condition_key": "arabic_phrases_viewed",
    },
    {
        "id": "pembanding_cerdas",
        "name": "Pembanding Cerdas",
        "icon": "\U0001F50D",  # magnifying glass
        "description": "Bandingkan 3+ hotel",
        "xp_reward": 20,
        "condition_key": "hotels_compared",
    },
    {
        "id": "jamaah_sosial",
        "name": "Jamaah Sosial",
        "icon": "\U0001F4E2",  # loudspeaker
        "description": "Bagikan via WhatsApp",
        "xp_reward": 15,
        "condition_key": "whatsapp_shared",
    },
    {
        "id": "streak_master",
        "name": "Streak Master",
        "icon": "\U0001F525",  # fire
        "description": "3 hari berturut-turut aktif",
        "xp_reward": 50,
        "condition_key": "streak_3_days",
    },
    {
        "id": "guru_manasik",
        "name": "Guru Manasik",
        "icon": "\U0001F393",  # graduation cap
        "description": "Selesaikan panduan manasik",
        "xp_reward": 30,
        "condition_key": "manasik_completed",
    },
]

# =============================================================================
# WEEKLY CHALLENGES
# =============================================================================

WEEKLY_CHALLENGES = [
    {
        "id": "challenge_readiness",
        "title": "Cek kesiapan umrah Anda",
        "description": "Gunakan AI Readiness Score untuk mengevaluasi kesiapan umrah Anda.",
        "target_page": "readiness",
        "xp_reward": 30,
    },
    {
        "id": "challenge_hotel_compare",
        "title": "Bandingkan 3 hotel",
        "description": "Bandingkan minimal 3 hotel di Makkah atau Madinah.",
        "target_page": "hotel_compare",
        "xp_reward": 25,
    },
    {
        "id": "challenge_simulator",
        "title": "Hitung budget umrah",
        "description": "Gunakan simulasi biaya untuk menghitung estimasi budget umrah Anda.",
        "target_page": "simulator",
        "xp_reward": 20,
    },
    {
        "id": "challenge_arabic",
        "title": "Pelajari 5 frase Arab",
        "description": "Pelajari minimal 5 frase Arab melalui AI Chat atau Doa Player.",
        "target_page": "chat",
        "xp_reward": 20,
    },
    {
        "id": "challenge_itinerary",
        "title": "Buat itinerary umrah",
        "description": "Buat jadwal perjalanan umrah Anda dengan AI Itinerary Builder.",
        "target_page": "itinerary",
        "xp_reward": 25,
    },
]

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
    """Add XP and check for level up. Logs activity to xp_log."""
    st.session_state.xp = st.session_state.get("xp", 0) + amount

    # Log the XP activity
    if "xp_log" not in st.session_state:
        st.session_state.xp_log = []
    st.session_state.xp_log.append({
        "amount": amount,
        "reason": reason or "Aktivitas",
        "timestamp": datetime.now().isoformat(),
    })
    # Keep only last 20 entries to avoid unbounded growth
    if len(st.session_state.xp_log) > 20:
        st.session_state.xp_log = st.session_state.xp_log[-20:]

    # Track daily streak
    today_str = datetime.now().strftime("%Y-%m-%d")
    last_active = st.session_state.get("last_active_date")
    if last_active != today_str:
        if last_active:
            try:
                last_dt = datetime.strptime(last_active, "%Y-%m-%d")
                diff = (datetime.now() - last_dt).days
                if diff == 1:
                    st.session_state.daily_streak = st.session_state.get("daily_streak", 0) + 1
                elif diff > 1:
                    st.session_state.daily_streak = 1
            except (ValueError, TypeError):
                st.session_state.daily_streak = 1
        else:
            st.session_state.daily_streak = 1
        st.session_state.last_active_date = today_str

    # Check level up (loop to handle multiple level-ups at once)
    current_level = st.session_state.get("level", 1)
    while current_level < 10:
        xp_needed = current_level * 100
        if st.session_state.xp >= xp_needed:
            st.session_state.xp -= xp_needed
            current_level += 1
            st.session_state.level = current_level
            st.toast(f"🎉 Level Up! Sekarang Level {current_level}!", icon="⬆️")
        else:
            break

    if reason:
        st.toast(f"🎯 +{amount} poin! {reason}", icon="✨")

    # Check achievements after every XP award
    check_achievements()


def check_achievements():
    """Check and unlock achievement badges based on session state conditions.

    Inspects various session state keys to determine whether the user has met
    the criteria for each badge defined in ``ACHIEVEMENT_BADGES``.  When a new
    badge is unlocked it is added to ``st.session_state.unlocked_badges``, a
    toast notification is shown, and the XP reward is granted (without
    re-triggering ``check_achievements`` to avoid infinite recursion).
    """
    # Ensure the unlocked_badges set exists
    if "unlocked_badges" not in st.session_state:
        st.session_state.unlocked_badges = set()

    unlocked: set = st.session_state.unlocked_badges

    for badge in ACHIEVEMENT_BADGES:
        badge_id = badge["id"]
        if badge_id in unlocked:
            continue  # Already unlocked

        condition_key = badge["condition_key"]
        met = False

        # --- Evaluate each condition ---
        if condition_key == "pages_visited_count":
            # Count pages visited (session state keys like "visited_<page>")
            visited = sum(
                1 for k in st.session_state
                if isinstance(k, str) and k.startswith("visited_") and st.session_state[k]
            )
            met = visited >= 5

        elif condition_key == "readiness_completed":
            met = bool(st.session_state.get("readiness_completed"))

        elif condition_key == "budget_set":
            met = bool(st.session_state.get("budget_set"))

        elif condition_key == "arabic_phrases_viewed":
            count = st.session_state.get("arabic_phrases_viewed", 0)
            met = isinstance(count, int) and count >= 10

        elif condition_key == "hotels_compared":
            count = st.session_state.get("hotels_compared", 0)
            met = isinstance(count, int) and count >= 3

        elif condition_key == "whatsapp_shared":
            met = bool(st.session_state.get("whatsapp_shared"))

        elif condition_key == "streak_3_days":
            streak = st.session_state.get("daily_streak", 0)
            met = isinstance(streak, int) and streak >= 3

        elif condition_key == "manasik_completed":
            met = bool(st.session_state.get("manasik_completed"))

        if met:
            unlocked.add(badge_id)
            st.session_state.unlocked_badges = unlocked

            # Award XP directly (avoid recursion by not calling add_xp)
            reward = badge["xp_reward"]
            st.session_state.xp = st.session_state.get("xp", 0) + reward

            # Log the badge XP
            if "xp_log" not in st.session_state:
                st.session_state.xp_log = []
            st.session_state.xp_log.append({
                "amount": reward,
                "reason": f"Badge: {badge['name']}",
                "timestamp": datetime.now().isoformat(),
            })
            if len(st.session_state.xp_log) > 20:
                st.session_state.xp_log = st.session_state.xp_log[-20:]

            st.toast(
                f"{badge['icon']} Badge Unlocked: {badge['name']}! +{reward} XP",
                icon="\U0001F3C5",  # sports medal
            )


def get_current_weekly_challenge() -> dict:
    """Return the weekly challenge for the current week.

    Uses ISO week number to rotate through ``WEEKLY_CHALLENGES`` so each week
    presents a different challenge.
    """
    week_number = datetime.now().isocalendar()[1]  # ISO week 1-53
    index = week_number % len(WEEKLY_CHALLENGES)
    return WEEKLY_CHALLENGES[index]


def render_weekly_challenge():
    """Render the weekly challenge card in the sidebar.

    Shows one challenge per week (based on ISO week number), a progress
    indicator, a 'Mulai Tantangan' button to navigate, and a completed
    state with a checkmark.
    """
    challenge = get_current_weekly_challenge()
    challenge_id = challenge["id"]

    # Track completed challenges in session state
    if "completed_challenges" not in st.session_state:
        st.session_state.completed_challenges = set()

    is_completed = challenge_id in st.session_state.completed_challenges

    # Determine if user is currently on the target page (progress indicator)
    current_page = st.session_state.get("current_page", "home")
    is_on_target = current_page == challenge["target_page"]

    # Build status indicator
    if is_completed:
        status_icon = "&#x2705;"  # green check
        status_text = "Selesai!"
        status_color = "#22c55e"
        bar_width = 100
    elif is_on_target:
        status_icon = "&#x1F3C3;"  # runner
        status_text = "Sedang dikerjakan..."
        status_color = "#f59e0b"
        bar_width = 50
    else:
        status_icon = "&#x1F4CB;"  # clipboard
        status_text = "Belum dimulai"
        status_color = "#8e9fb3"
        bar_width = 0

    st.markdown(f"""
    <div style="background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid rgba(212, 175, 55, 0.2);
                border-radius: 10px; padding: 0.6rem; margin-top: 0.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.3rem;">
            <span style="color: #d4af37; font-size: 0.75rem; font-weight: bold;">
                <span aria-hidden="true">&#x1F3AF;</span> Tantangan Mingguan
            </span>
            <span style="color: {status_color}; font-size: 0.6rem;">{status_text}</span>
        </div>
        <div style="color: #e2e8f0; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.2rem;">
            {challenge['title']}
        </div>
        <div style="color: #8e9fb3; font-size: 0.65rem; margin-bottom: 0.4rem;">
            {challenge['description']}
        </div>
        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.3rem;">
            <div style="flex: 1; height: 4px; background: #1e293b; border-radius: 2px; overflow: hidden;">
                <div style="width: {bar_width}%; height: 100%; background: linear-gradient(90deg, #d4af37, #f5d77a);
                            border-radius: 2px; transition: width 0.4s ease;"></div>
            </div>
            <span style="color: #d4af37; font-size: 0.6rem; font-weight: bold;">+{challenge['xp_reward']} XP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not is_completed:
        if st.button(
            "Mulai Tantangan" if not is_on_target else "Lanjutkan",
            key="weekly_challenge_btn",
            use_container_width=True,
        ):
            st.session_state.current_page = challenge["target_page"]
            st.rerun()


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
# PAGE FEEDBACK WIDGET
# =============================================================================

PAGE_FEEDBACK_CSS = """
<style>
.page-feedback-section {
    margin-top: 40px; padding: 20px;
    background: rgba(255,255,255,0.03);
    border-top: 1px solid rgba(212,175,55,0.2);
    border-radius: 8px;
}
.page-feedback-title {
    color: #d4af37; font-size: 1rem; margin-bottom: 12px;
}
.feedback-stars { font-size: 1.5rem; cursor: pointer; }
.feedback-thanks {
    color: #22c55e; font-size: 0.9rem; margin-top: 8px;
}
</style>
"""


def _get_feedback_summary() -> dict:
    """Return average rating and count across all rated pages.

    Returns:
        dict with keys 'average' (float) and 'count' (int).
    """
    feedbacks = st.session_state.get("page_feedback", {})
    if not feedbacks:
        return {"average": 0.0, "count": 0}
    ratings = [fb["rating"] for fb in feedbacks.values() if "rating" in fb]
    if not ratings:
        return {"average": 0.0, "count": 0}
    return {"average": sum(ratings) / len(ratings), "count": len(ratings)}


def render_page_feedback():
    """Render a lightweight 'Rate this page' widget at the bottom of the current page.

    The widget is shown once per page per session. After the user submits feedback
    it is stored in ``st.session_state.page_feedback`` keyed by page name and the
    user receives +5 XP.
    """
    page = st.session_state.get("current_page", "home")

    # Already rated this page in this session — show a short thank-you instead
    if page in st.session_state.get("page_feedback", {}):
        return

    # Inject CSS on every rerun (Streamlit rebuilds the page each time)
    st.markdown(PAGE_FEEDBACK_CSS, unsafe_allow_html=True)

    # Collapsible container so it stays non-intrusive
    st.markdown(
        '<div class="page-feedback-section">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-feedback-title">Bagaimana pengalaman Anda di halaman ini?</div>',
        unsafe_allow_html=True,
    )

    star_options = ["1", "2", "3", "4", "5"]

    rating = st.select_slider(
        "Rating",
        options=star_options,
        value="3",
        format_func=lambda x: "\u2b50" * int(x),
        key=f"feedback_rating_{page}",
        label_visibility="collapsed",
    )

    comment = st.text_input(
        "Saran perbaikan (opsional)",
        max_chars=200,
        key=f"feedback_comment_{page}",
        placeholder="Tulis saran Anda di sini...",
    )

    if st.button("Kirim Feedback", key=f"feedback_submit_{page}"):
        st.session_state.page_feedback[page] = {
            "rating": int(rating),
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
        }
        add_xp(5, "Memberi feedback halaman")
        st.markdown(
            '<div class="feedback-thanks">Terima kasih atas feedback Anda!</div>',
            unsafe_allow_html=True,
        )
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# GAMIFICATION SIDEBAR
# =============================================================================

GAMIFICATION_SIDEBAR_CSS = """
<style>
.gamification-sidebar {
    background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 12px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
}
.gamification-sidebar .gs-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
}
.gamification-sidebar .gs-header .gs-title {
    color: #d4af37;
    font-size: 0.8rem;
    font-weight: bold;
}
.level-badge {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    border-radius: 10px;
    font-size: 0.65rem;
    font-weight: bold;
    color: #000;
}
.level-badge.tier-0 { background: #9ca3af; }
.level-badge.tier-1 { background: #60a5fa; }
.level-badge.tier-2 { background: #34d399; }
.level-badge.tier-3 { background: #f59e0b; }
.level-badge.tier-4 { background: #f472b6; }
.level-badge.tier-5 { background: linear-gradient(135deg, #d4af37, #f5d77a); }
.xp-progress-bar {
    width: 100%;
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
    overflow: hidden;
    margin: 0.35rem 0;
}
.xp-progress-bar .xp-fill {
    height: 100%;
    background: linear-gradient(90deg, #d4af37, #f5d77a);
    border-radius: 3px;
    transition: width 0.4s ease;
}
.xp-stats-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
}
.xp-stats-row .xp-label {
    color: #b0b0b0;
    font-size: 0.7rem;
}
.xp-stats-row .xp-value {
    color: #d4af37;
    font-size: 0.7rem;
    font-weight: bold;
}
.xp-activity-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.2rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.xp-activity-item:last-child {
    border-bottom: none;
}
.xp-activity-item .act-reason {
    color: #b0b0b0;
    font-size: 0.65rem;
    max-width: 70%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.xp-activity-item .act-amount {
    color: #4ade80;
    font-size: 0.65rem;
    font-weight: bold;
}
.streak-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: rgba(249, 115, 22, 0.15);
    border: 1px solid rgba(249, 115, 22, 0.3);
    border-radius: 8px;
    padding: 0.15rem 0.4rem;
    font-size: 0.65rem;
    color: #fb923c;
    font-weight: bold;
}
</style>
"""


def _get_sidebar_level_title(level: int) -> str:
    """Get gamification level title for sidebar display."""
    titles = {
        0: "Pemula",
        1: "Penjelajah",
        2: "Perencana",
        3: "Ahli",
        4: "Master",
    }
    if level >= 5:
        return "Legend"
    return titles.get(level, "Pemula")


def render_gamification_sidebar():
    """Render compact gamification summary in the sidebar."""
    # Inject CSS on every rerun (Streamlit rebuilds the page each time)
    st.markdown(GAMIFICATION_SIDEBAR_CSS, unsafe_allow_html=True)

    xp = st.session_state.get("xp", 0)
    # Sidebar level uses XP // 100 scheme (different from main level system)
    sidebar_level = xp // 100 if xp >= 0 else 0
    # Use the main level for progress display
    level = st.session_state.get("level", 1)
    xp_for_next = level * 100
    progress_pct = min((xp % 100) / 100.0, 1.0) if xp_for_next > 0 else 0
    progress_width = int(progress_pct * 100)

    title = _get_sidebar_level_title(sidebar_level)
    tier_class = f"tier-{min(sidebar_level, 5)}"

    streak = st.session_state.get("daily_streak", 0)

    # Build recent activities HTML (last 3)
    xp_log = st.session_state.get("xp_log", [])
    recent = xp_log[-3:] if xp_log else []
    recent.reverse()  # Most recent first

    activities_html = ""
    if recent:
        for entry in recent:
            reason = entry.get("reason", "Aktivitas")
            amount = entry.get("amount", 0)
            activities_html += (
                '<div class="xp-activity-item">'
                f'<span class="act-reason">{reason}</span>'
                f'<span class="act-amount">+{amount}</span>'
                '</div>'
            )
    else:
        activities_html = '<div style="color:#8e9fb3;font-size:0.65rem;text-align:center;padding:0.2rem 0;">Belum ada aktivitas</div>'

    # Streak HTML
    streak_html = ""
    if streak > 0:
        streak_html = f'<span class="streak-badge"><span aria-hidden="true">&#x1F525;</span> {streak} hari</span>'

    # Achievement badges (new system)
    unlocked_badges = st.session_state.get("unlocked_badges", set())
    total_badges = len(ACHIEVEMENT_BADGES)
    unlocked_count = len(unlocked_badges)

    # Build unlocked badge icons HTML
    badge_icons_html = ""
    if unlocked_count > 0:
        icons = []
        for b in ACHIEVEMENT_BADGES:
            if b["id"] in unlocked_badges:
                icons.append(f'<span title="{b["name"]}">{b["icon"]}</span>')
        badge_icons_html = (
            '<div style="font-size:0.85rem;margin-top:0.25rem;display:flex;gap:0.3rem;flex-wrap:wrap;">'
            + "".join(icons)
            + "</div>"
        )

    # Legacy achievements (keep backward compat)
    achievements = st.session_state.get("achievements", [])
    legacy_badges_html = ""
    if achievements:
        legacy_badges_html = f'<div style="font-size:0.75rem;margin-top:0.25rem;">{" ".join(achievements[:5])}</div>'

    # Build HTML as continuous block — blank lines from empty variables would
    # break CommonMark HTML block parsing, causing raw HTML to appear as text.
    parts = [
        '<div class="gamification-sidebar">',
        '<div class="gs-header">',
        f'<span class="gs-title"><span aria-hidden="true">&#x1F3C6;</span> Progress Anda</span>',
        f'<span class="level-badge {tier_class}">{title}</span>',
        '</div>',
        '<div class="xp-stats-row">',
        f'<span class="xp-label">Level {level}</span>',
        f'<span class="xp-value">{xp}/{xp_for_next} XP</span>',
        '</div>',
        '<div class="xp-progress-bar">',
        f'<div class="xp-fill" style="width:{progress_width}%"></div>',
        '</div>',
        '<div class="xp-stats-row" style="margin-top:0.35rem;">',
        '<span class="xp-label"><span aria-hidden="true">&#x1F3C5;</span> Badge</span>',
        f'<span class="xp-value">{unlocked_count}/{total_badges}</span>',
        '</div>',
    ]
    if badge_icons_html:
        parts.append(badge_icons_html)
    parts += [
        '<div class="xp-stats-row" style="margin-top:0.35rem;">',
        '<span class="xp-label">Aktivitas Terkini</span>',
    ]
    if streak_html:
        parts.append(streak_html)
    parts.append('</div>')
    parts.append(activities_html)
    if legacy_badges_html:
        parts.append(legacy_badges_html)
    parts.append('</div>')

    st.markdown("\n".join(parts), unsafe_allow_html=True)

    # Weekly Challenge widget
    render_weekly_challenge()


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
            <p style="color: #b0b0b0; font-size: 0.8rem; margin-top: 0.25rem;">{BRAND_TAGLINE_ID}</p>
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
                ("🕌", "Panduan Umrah Lengkap", "umrah_complete", HAS_UMRAH_COMPLETE),
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

            # Group Matching
            if HAS_GROUP_MATCHING:
                is_gm = st.session_state.get("current_page") == "group_matching"
                if st.button("🤝 Group Matching", key="p2_group_matching", use_container_width=True,
                            type="primary" if is_gm else "secondary"):
                    st.session_state.current_page = "group_matching"
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

            # Kalkulator Kurs
            if HAS_KURS:
                is_kurs = st.session_state.get("current_page") == "kurs_calculator"
                if st.button("🏦 Kalkulator Kurs", key="p2_kurs_calculator", use_container_width=True,
                            type="primary" if is_kurs else "secondary"):
                    st.session_state.current_page = "kurs_calculator"
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
                ("🗓️", "Itinerary Builder", "itinerary", HAS_ITINERARY, False),
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

        # Gamification Dashboard (compact sidebar card)
        render_gamification_sidebar()

        # Settings quick access
        is_settings = st.session_state.get("current_page") == "settings"
        if st.button("⚙️ Pengaturan", key="nav_settings", use_container_width=True,
                     type="primary" if is_settings else "secondary"):
            st.session_state.current_page = "settings"
            st.rerun()

        st.markdown("---")

        # Footer
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <p style="color: #666; font-size: 0.75rem;">
                {get_display_version()}<br>
                © 2026 MS Hadianto
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

    # Track page view - fires when page changes
    if HAS_TRACKING_SERVICE and st.session_state.get("_tracked_page") != page:
        try:
            track_page(page)
            st.session_state._tracked_page = page
        except Exception as e:
            logger.debug(f"Page tracking failed for '{page}': {e}")
    
    # Page routing map
    page_map = {
        # Core pages
        "home": render_home_page,
        "chat": render_chat_page,
        "simulator": render_simulator_page,
        "umrah_mandiri": render_umrah_mandiri_page,
        "umrah_bareng": render_umrah_bareng_page,
        "group_matching": render_group_matching_page,
        "booking": render_booking_page,

        # New feature pages
        "itinerary": render_itinerary_builder_page,
        "checklist": render_smart_checklist_page,
        "crowd": render_crowd_prediction_page,
        "sos": render_sos_page,
        "tracking": render_group_tracking_page,
        "manasik": render_manasik_page,
        "umrah_complete": render_umrah_complete_page,
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

        # User Settings
        "settings": render_settings_page,

        # Hasan.VC Demo Features
        "readiness": render_readiness_checker_page,
        "cost_tracker": render_cost_tracker_page,
        "tanya_ustadz": render_tanya_ustadz_page,
        "doc_checker": render_doc_checker_page,
        "peta": render_peta_interaktif_page,
        "kurs_calculator": render_kurs_calculator_page,
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
                "kurs_calculator": "Kalkulator Kurs & Harga",
            }
            render_access_denied(reason, page_names.get(page, page))
            return

    try:
        renderer()
    except Exception as e:
        logger.error(f"Error rendering page '{page}': {e}", exc_info=True)
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
    
    # Global UX CSS (page transitions, smooth scroll)
    st.markdown("""
    <style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    section.main .block-container { animation: fadeIn 0.3s ease-out; }
    #main-content { scroll-margin-top: 1rem; }
    html, section.main { scroll-behavior: smooth; }
    @media (prefers-reduced-motion: reduce) {
        section.main .block-container { animation: none; }
        html, section.main { scroll-behavior: auto; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Skip-to-content link (accessibility)
    st.markdown('<a href="#main-content" class="skip-to-content">Langsung ke konten utama</a>', unsafe_allow_html=True)

    # First-visit welcome banner
    if st.session_state.get("is_first_visit") and not st.session_state.get("first_visit_dismissed"):
        st.markdown("""
        <div role="alert" style="background: linear-gradient(135deg, #1a3a1a 0%, #0d2b0d 100%);
                    border: 1px solid #d4af37; border-radius: 12px; padding: 1.25rem;
                    margin-bottom: 1rem; text-align: center;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;" aria-hidden="true">🕋</div>
            <div style="color: #d4af37; font-size: 1.1rem; font-weight: bold;">
                Assalamu'alaikum! Selamat datang di LABBAIK Smart Planner
            </div>
            <div style="color: #b0b0b0; font-size: 0.9rem; margin-top: 0.5rem;">
                Platform AI pertama untuk perencanaan umrah Anda.
                Mulai dengan Simulasi Biaya atau tanya AI Chat.
            </div>
        </div>
        """, unsafe_allow_html=True)
        wcol1, wcol2, wcol3 = st.columns([1, 1, 1])
        with wcol1:
            if st.button("💰 Simulasi Biaya", key="welcome_sim", use_container_width=True, type="primary"):
                st.session_state.first_visit_dismissed = True
                st.session_state.is_first_visit = False
                st.session_state.current_page = "simulator"
                st.rerun()
        with wcol2:
            if st.button("🤖 Tanya AI", key="welcome_chat", use_container_width=True):
                st.session_state.first_visit_dismissed = True
                st.session_state.is_first_visit = False
                st.session_state.current_page = "chat"
                st.rerun()
        with wcol3:
            if st.button("Tutup", key="welcome_dismiss", use_container_width=True):
                st.session_state.first_visit_dismissed = True
                st.session_state.is_first_visit = False
                st.session_state.onboarding_step = 1
                st.rerun()

    # =========================================================================
    # GUIDED ONBOARDING TOUR
    # =========================================================================
    onboarding_step = st.session_state.get("onboarding_step", 0)

    if 1 <= onboarding_step <= 5:
        # Tour step definitions
        tour_steps = {
            1: {
                "title": "Selamat Datang!",
                "text": "Selamat datang di LABBAIK AI! Mari kami pandu Anda mengenal fitur-fitur utama platform ini.",
                "icon": "&#x1F54B;",  # Kaaba
            },
            2: {
                "title": "Menu Navigasi",
                "text": "Gunakan menu di sidebar (panel kiri) untuk navigasi ke berbagai fitur. Klik panah di kiri atas jika sidebar tertutup.",
                "icon": "&#x2630;",  # Menu
            },
            3: {
                "title": "Simulasi Biaya",
                "text": "Coba Simulasi Biaya untuk menghitung estimasi biaya Umrah Anda. Fitur ini ada di menu Smart Savings.",
                "icon": "&#x1F4B0;",  # Money bag
            },
            4: {
                "title": "AI Assistant",
                "text": "Tanya AI Assistant untuk mendapatkan jawaban seputar Umrah. Tersedia di menu Smart Journey.",
                "icon": "&#x1F916;",  # Robot
            },
            5: {
                "title": "Anda Siap!",
                "text": "Anda siap menjelajahi semua fitur LABBAIK AI. Selamat merencanakan Umrah Anda!",
                "icon": "&#x2705;",  # Check mark
            },
        }

        step = tour_steps[onboarding_step]
        total_steps = 5

        # Build step indicator dots
        dots_html = ""
        for i in range(1, total_steps + 1):
            if i == onboarding_step:
                dots_html += '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#d4af37;margin:0 4px;"></span>'
            else:
                dots_html += '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#555;margin:0 4px;"></span>'

        # Inject onboarding CSS + tooltip HTML
        st.markdown(f"""
        <style>
        @keyframes onboardingFadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .onboarding-overlay {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 999999;
            width: 480px;
            max-width: calc(100vw - 32px);
            animation: onboardingFadeIn 0.4s ease-out;
        }}
        .onboarding-tooltip {{
            background: #1a1a2e;
            border: 2px solid #d4af37;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(212,175,55,0.2);
            text-align: center;
        }}
        .onboarding-tooltip .ob-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        .onboarding-tooltip .ob-step-label {{
            color: #d4af37;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.25rem;
        }}
        .onboarding-tooltip .ob-title {{
            color: #f0f0f0;
            font-size: 1.15rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        .onboarding-tooltip .ob-text {{
            color: #b0b0b0;
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 1rem;
        }}
        .onboarding-tooltip .ob-dots {{
            margin-bottom: 1rem;
        }}
        @media (max-width: 640px) {{
            .onboarding-overlay {{
                width: calc(100vw - 16px);
                bottom: 12px;
            }}
            .onboarding-tooltip {{
                padding: 1rem;
                border-radius: 12px;
            }}
            .onboarding-tooltip .ob-title {{
                font-size: 1rem;
            }}
            .onboarding-tooltip .ob-text {{
                font-size: 0.85rem;
            }}
        }}
        </style>
        <div class="onboarding-overlay">
            <div class="onboarding-tooltip">
                <div class="ob-icon">{step['icon']}</div>
                <div class="ob-step-label">Langkah {onboarding_step} dari {total_steps}</div>
                <div class="ob-title">{step['title']}</div>
                <div class="ob-text">{step['text']}</div>
                <div class="ob-dots">{dots_html}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation buttons for the tour (rendered as Streamlit buttons)
        ob_col1, ob_col2 = st.columns(2)
        with ob_col1:
            if st.button("Lewati Tour", key="onboarding_skip", use_container_width=True):
                st.session_state.onboarding_step = 6
                st.session_state.first_visit_dismissed = True
                add_xp(10, "Menyelesaikan tour")
                st.rerun()
        with ob_col2:
            if onboarding_step < 5:
                if st.button("Selanjutnya →", key="onboarding_next", use_container_width=True, type="primary"):
                    st.session_state.onboarding_step = onboarding_step + 1
                    st.rerun()
            else:
                if st.button("Mulai Jelajahi! →", key="onboarding_finish", use_container_width=True, type="primary"):
                    st.session_state.onboarding_step = 6
                    st.session_state.first_visit_dismissed = True
                    add_xp(25, "Menyelesaikan onboarding tour")
                    st.rerun()

    # Content anchor for skip link
    st.markdown('<div id="main-content"></div>', unsafe_allow_html=True)

    # Render sidebar
    render_sidebar()

    # Render main content
    render_page()

    # Render page feedback widget (after page content, before footer)
    render_page_feedback()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
