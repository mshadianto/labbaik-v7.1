"""
LABBAIK AI - Access Control Middleware
=======================================
Centralized access control for pages and features.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Callable, List
from functools import wraps
from enum import Enum

from services.user.user_service import (
    User, UserRole, UserStatus,
    get_current_user, is_logged_in, set_current_user
)


class Feature(str, Enum):
    """Feature flags for access control"""
    # Free features
    VIEW_PACKAGES = "view_packages"
    USE_SIMULATOR = "use_simulator"
    VIEW_CROWD = "view_crowd"
    BASIC_CHAT = "basic_chat"
    VIEW_GUIDES = "view_guides"
    SOS_EMERGENCY = "sos_emergency"

    # Premium features
    UNLIMITED_CHAT = "unlimited_chat"
    PRICE_ALERTS = "price_alerts"
    GROUP_TRACKING = "group_tracking"
    DOWNLOAD_REPORTS = "download_reports"
    PRIORITY_SUPPORT = "priority_support"
    SMART_CHECKLIST = "smart_checklist"
    AI_ITINERARY = "ai_itinerary"

    # Expert AI Features (Premium-locked)
    PERSONALIZED_AI_ADVICE = "personalized_ai_advice"
    DETAILED_PRICE_COMPARISON = "detailed_price_comparison"
    FINANCIAL_ANALYSIS = "financial_analysis"

    # Partner features
    MANAGE_PACKAGES = "manage_packages"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_BOOKINGS = "manage_bookings"
    PARTNER_DASHBOARD = "partner_dashboard"

    # Admin features
    USER_MANAGEMENT = "user_management"
    SYSTEM_SETTINGS = "system_settings"


# Feature to minimum role mapping
FEATURE_ROLES = {
    # Public (Guest)
    Feature.VIEW_PACKAGES: UserRole.GUEST,
    Feature.USE_SIMULATOR: UserRole.GUEST,
    Feature.VIEW_CROWD: UserRole.GUEST,
    Feature.SOS_EMERGENCY: UserRole.GUEST,

    # Free user
    Feature.BASIC_CHAT: UserRole.FREE,
    Feature.VIEW_GUIDES: UserRole.FREE,
    Feature.SMART_CHECKLIST: UserRole.FREE,

    # Premium
    Feature.UNLIMITED_CHAT: UserRole.PREMIUM,
    Feature.PRICE_ALERTS: UserRole.PREMIUM,
    Feature.GROUP_TRACKING: UserRole.PREMIUM,
    Feature.DOWNLOAD_REPORTS: UserRole.PREMIUM,
    Feature.PRIORITY_SUPPORT: UserRole.PREMIUM,
    Feature.AI_ITINERARY: UserRole.PREMIUM,

    # Expert AI (Premium-locked)
    Feature.PERSONALIZED_AI_ADVICE: UserRole.PREMIUM,
    Feature.DETAILED_PRICE_COMPARISON: UserRole.PREMIUM,
    Feature.FINANCIAL_ANALYSIS: UserRole.PREMIUM,

    # Partner
    Feature.MANAGE_PACKAGES: UserRole.PARTNER,
    Feature.VIEW_ANALYTICS: UserRole.PARTNER,
    Feature.MANAGE_BOOKINGS: UserRole.PARTNER,
    Feature.PARTNER_DASHBOARD: UserRole.PARTNER,

    # Admin
    Feature.USER_MANAGEMENT: UserRole.ADMIN,
    Feature.SYSTEM_SETTINGS: UserRole.ADMIN,
}

# Role hierarchy for comparison
ROLE_HIERARCHY = {
    UserRole.GUEST: 0,
    UserRole.FREE: 1,
    UserRole.PREMIUM: 2,
    UserRole.PARTNER: 3,
    UserRole.ADMIN: 4,
}


def get_user_role_level(user: Optional[User]) -> int:
    """Get numeric role level for comparison"""
    if not user:
        return ROLE_HIERARCHY[UserRole.GUEST]
    return ROLE_HIERARCHY.get(user.role, 0)


def has_role_access(user: Optional[User], required_role: UserRole) -> bool:
    """Check if user has at least the required role level"""
    user_level = get_user_role_level(user)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def has_feature_access(user: Optional[User], feature: Feature) -> bool:
    """Check if user can access a feature"""
    required_role = FEATURE_ROLES.get(feature, UserRole.ADMIN)
    return has_role_access(user, required_role)


def check_access(required_role: UserRole = None, feature: Feature = None) -> tuple[bool, str]:
    """
    Check access and return (has_access, message)
    """
    user = get_current_user()

    # Check feature access
    if feature:
        required_role = FEATURE_ROLES.get(feature, UserRole.ADMIN)

    if not required_role:
        return True, ""

    # Guest access - always allowed
    if required_role == UserRole.GUEST:
        return True, ""

    # Must be logged in for non-guest features
    if not user:
        return False, "login_required"

    # Check role level
    if not has_role_access(user, required_role):
        if required_role == UserRole.PREMIUM:
            return False, "premium_required"
        elif required_role == UserRole.PARTNER:
            return False, "partner_required"
        elif required_role == UserRole.ADMIN:
            return False, "admin_required"
        else:
            return False, "access_denied"

    return True, ""


def render_access_denied(reason: str, feature_name: str = ""):
    """Render access denied message with appropriate CTA"""

    if reason == "login_required":
        st.warning("### Silakan Login Terlebih Dahulu")
        st.markdown(f"""
        Untuk mengakses **{feature_name or 'fitur ini'}**, Anda perlu login atau daftar akun.

        **Keuntungan mendaftar:**
        - Simpan simulasi biaya
        - Chat dengan AI Assistant
        - Akses panduan lengkap
        - Dan masih banyak lagi!
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Masuk", use_container_width=True, type="primary"):
                st.session_state.current_page = "auth"
                st.session_state.auth_mode = "login"
                st.rerun()
        with col2:
            if st.button("Daftar Gratis", use_container_width=True):
                st.session_state.current_page = "auth"
                st.session_state.auth_mode = "register"
                st.rerun()

    elif reason == "premium_required":
        st.warning("### Fitur Premium")
        st.markdown(f"""
        **{feature_name or 'Fitur ini'}** tersedia untuk pengguna Premium.

        **Keuntungan Premium:**
        - Chat AI tanpa batas
        - Notifikasi harga real-time
        - Group tracking untuk rombongan
        - Download laporan PDF
        - Prioritas support
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Upgrade ke Premium", use_container_width=True, type="primary"):
                st.session_state.current_page = "subscription"
                st.rerun()
        with col2:
            st.markdown("**Mulai dari Rp 99.000/bulan**")

    elif reason == "partner_required":
        st.warning("### Khusus Mitra Travel")
        st.markdown(f"""
        **{feature_name or 'Fitur ini'}** hanya tersedia untuk Mitra Travel LABBAIK.

        **Keuntungan Menjadi Mitra:**
        - Jual paket Umrah di platform
        - Komisi menarik per booking
        - Dashboard analytics lengkap
        - Support prioritas
        """)

        if st.button("Daftar Jadi Mitra", use_container_width=True, type="primary"):
            st.session_state.current_page = "partner"
            st.rerun()

    elif reason == "admin_required":
        st.error("### Akses Terbatas")
        st.markdown("Halaman ini hanya dapat diakses oleh Administrator.")

        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()

    else:
        st.error("Anda tidak memiliki akses ke fitur ini.")


def require_access(required_role: UserRole = None, feature: Feature = None, feature_name: str = ""):
    """
    Decorator for page functions that require access control.
    Returns True if access granted, renders access denied if not.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            has_access, reason = check_access(required_role, feature)

            if has_access:
                return func(*args, **kwargs)
            else:
                render_access_denied(reason, feature_name)
                return None

        return wrapper
    return decorator


def gate_feature(feature: Feature, feature_name: str = ""):
    """
    Check feature access inline (not as decorator).
    Returns True if access granted.
    """
    has_access, reason = check_access(feature=feature)

    if not has_access:
        render_access_denied(reason, feature_name)

    return has_access


# =============================================================================
# RATE LIMITING
# =============================================================================

def get_daily_usage(feature_key: str) -> int:
    """Get daily usage count for a feature"""
    today = datetime.now().date().isoformat()
    usage_key = f"usage_{feature_key}_{today}"

    return st.session_state.get(usage_key, 0)


def increment_usage(feature_key: str) -> int:
    """Increment and return daily usage count"""
    today = datetime.now().date().isoformat()
    usage_key = f"usage_{feature_key}_{today}"

    current = st.session_state.get(usage_key, 0)
    st.session_state[usage_key] = current + 1

    return current + 1


def check_rate_limit(feature_key: str, limit: int) -> tuple[bool, int]:
    """
    Check if user is within rate limit.
    Returns (within_limit, remaining)
    """
    current = get_daily_usage(feature_key)
    remaining = max(0, limit - current)

    return current < limit, remaining


def get_chat_limit() -> int:
    """Get chat message limit based on user role"""
    user = get_current_user()

    if not user:
        return 3  # Guest: 3 messages

    if user.role == UserRole.FREE:
        return 10  # Free: 10 messages/day

    if user.role in [UserRole.PREMIUM, UserRole.PARTNER, UserRole.ADMIN]:
        return 999999  # Unlimited

    return 5


def check_chat_limit() -> tuple[bool, int]:
    """Check if user can send more chat messages"""
    limit = get_chat_limit()
    return check_rate_limit("chat_messages", limit)


def render_chat_limit_reached():
    """Render chat limit reached message"""
    user = get_current_user()

    if not user:
        st.warning("### Batas Chat Tercapai")
        st.markdown("""
        Anda telah mencapai batas chat harian untuk tamu (3 pesan).

        **Daftar gratis** untuk mendapatkan 10 pesan/hari!
        """)
        if st.button("Daftar Gratis", type="primary"):
            st.session_state.current_page = "auth"
            st.session_state.auth_mode = "register"
            st.rerun()

    elif user.role == UserRole.FREE:
        st.warning("### Batas Chat Harian Tercapai")
        st.markdown("""
        Anda telah menggunakan 10 pesan chat hari ini.

        **Upgrade ke Premium** untuk chat tanpa batas!
        """)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Upgrade Premium", type="primary", use_container_width=True):
                st.session_state.current_page = "subscription"
                st.rerun()
        with col2:
            st.caption("Reset besok pukul 00:00")


# =============================================================================
# PAGE ACCESS CONTROL MAPPING
# =============================================================================

PAGE_ACCESS = {
    # Public pages
    "home": UserRole.GUEST,
    "simulator": UserRole.GUEST,
    "crowd": UserRole.GUEST,
    "sos": UserRole.GUEST,
    "compare": UserRole.GUEST,

    # Free user pages
    "chat": UserRole.FREE,
    "umrah_mandiri": UserRole.FREE,
    "umrah_bareng": UserRole.FREE,
    "booking": UserRole.FREE,
    "manasik": UserRole.FREE,
    "doa": UserRole.FREE,
    "checklist": UserRole.FREE,
    "auth": UserRole.GUEST,  # Auth page is always accessible

    # Premium pages
    "tracking": UserRole.PREMIUM,
    "itinerary": UserRole.PREMIUM,

    # Partner pages
    "partner_dashboard": UserRole.PARTNER,
    "whatsapp": UserRole.PARTNER,

    # Admin pages
    "user_analytics": UserRole.ADMIN,
    "analytics": UserRole.ADMIN,
}


def check_page_access(page: str) -> tuple[bool, str]:
    """Check if current user can access a page"""
    required_role = PAGE_ACCESS.get(page, UserRole.GUEST)
    return check_access(required_role=required_role)


def get_page_access_role(page: str) -> UserRole:
    """Get required role for a page"""
    return PAGE_ACCESS.get(page, UserRole.GUEST)


# =============================================================================
# PREMIUM FEATURE PAYWALL UI
# =============================================================================

def render_expert_feature_paywall(feature_name: str = "Expert AI", benefit_text: str = None):
    """
    Render a clean paywall UI for premium/expert features.
    Used for gating personalized AI advice, detailed price comparison, etc.
    """
    if benefit_text is None:
        benefit_text = "analisis mendalam untuk mengoptimalkan dana tabungan Anda"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid #d4af37; border-radius: 15px;
                padding: 1.5rem; text-align: center; margin: 1rem 0;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔐</div>
        <h3 style="color: #d4af37; margin-bottom: 0.5rem;">Fitur {feature_name}</h3>
        <p style="color: #ccc; font-size: 0.9rem; margin-bottom: 1rem;">
            Dapatkan {benefit_text} agar berangkat lebih cepat.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨ Upgrade ke Premium", type="primary", use_container_width=True, key=f"upgrade_{feature_name}"):
            st.session_state.current_page = "subscription"
            st.rerun()

    st.caption("Mulai dari Rp 99.000/bulan")


def check_expert_feature(feature: Feature, feature_name: str = "Expert AI") -> bool:
    """
    Check if user can access an expert feature.
    If not, renders paywall and returns False.
    """
    has_access, reason = check_access(feature=feature)

    if not has_access:
        if reason == "login_required":
            render_access_denied(reason, feature_name)
        else:
            render_expert_feature_paywall(feature_name)
        return False

    return True
