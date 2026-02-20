"""
LABBAIK AI v6.0 - UI Components
==============================
Reusable Streamlit UI components.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, date
from functools import wraps
import logging

from core.constants import UIConstants, Messages, APP_NAME, APP_VERSION
from core.config import get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# DECORATORS
# =============================================================================

def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a page."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated"):
            st.warning("🔐 Silakan login untuk mengakses halaman ini.")
            render_login_prompt()
            return None
        return func(*args, **kwargs)
    return wrapper


def require_role(role: str) -> Callable:
    """Decorator to require specific role for a page."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = st.session_state.get("user_role", "guest")
            role_hierarchy = ["guest", "user", "premium", "partner", "admin", "superadmin"]
            
            if role_hierarchy.index(user_role) < role_hierarchy.index(role):
                st.error(f"⛔ Anda memerlukan akses {role} untuk halaman ini.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# HEADER & NAVIGATION
# =============================================================================

def render_header(
    title: str = None,
    subtitle: str = None,
    show_logo: bool = True
):
    """
    Render application header.
    
    Args:
        title: Page title (uses app name if not provided)
        subtitle: Optional subtitle
        show_logo: Whether to show logo
    """
    settings = get_settings()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if show_logo:
            st.markdown(f"# {settings.ui.page_icon} {title or settings.ui.app_name}")
        else:
            st.markdown(f"# {title or settings.ui.app_name}")
        
        if subtitle:
            st.markdown(f"*{subtitle}*")
    
    with col2:
        # User info if logged in
        if st.session_state.get("authenticated"):
            user_name = st.session_state.get("user_name", "User")
            st.markdown(f"👤 **{user_name}**")
            if st.button("Logout", key="header_logout", use_container_width=True):
                logout()


def render_sidebar():
    """Render main navigation sidebar."""
    settings = get_settings()
    
    with st.sidebar:
        # Logo and title
        st.markdown(f"## {settings.ui.page_icon} {settings.ui.app_name}")
        st.caption(f"v{settings.ui.app_version}")
        st.divider()
        
        # Navigation menu
        menu_items = get_menu_items()
        
        for item in menu_items:
            if item.get("divider"):
                st.divider()
                continue
            
            # Check if item requires auth
            if item.get("require_auth") and not st.session_state.get("authenticated"):
                continue
            
            # Check role requirements
            if item.get("require_role"):
                user_role = st.session_state.get("user_role", "guest")
                role_hierarchy = ["guest", "user", "premium", "partner", "admin", "superadmin"]
                if role_hierarchy.index(user_role) < role_hierarchy.index(item["require_role"]):
                    continue
            
            icon = item.get("icon", "")
            label = item.get("label", "Menu")
            key = item.get("key", label.lower())
            
            if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()
        
        st.divider()
        
        # Footer
        st.caption(f"© 2024 {settings.ui.app_name}")
        st.caption("Powered by MS Hadianto")


def get_menu_items() -> List[Dict[str, Any]]:
    """Get navigation menu items based on settings."""
    settings = get_settings()
    
    items = [
        {"key": "home", "label": "Beranda", "icon": "🏠"},
    ]
    
    if settings.ui.enable_chat:
        items.append({"key": "chat", "label": "AI Chat", "icon": "💬"})
    
    if settings.ui.enable_simulator:
        items.append({"key": "simulator", "label": "Simulasi Biaya", "icon": "🧮"})
    
    items.append({"divider": True})
    
    if settings.ui.enable_umrah_mandiri:
        items.append({"key": "mandiri", "label": "Umrah Mandiri", "icon": "📖"})
    
    if settings.ui.enable_umrah_bareng:
        items.append({"key": "bareng", "label": "Umrah Bareng", "icon": "👥"})
    
    if settings.ui.enable_booking:
        items.append({
            "key": "booking", 
            "label": "Booking", 
            "icon": "📝",
            "require_auth": True
        })
    
    items.extend([
        {"divider": True},
        {"key": "profile", "label": "Profil", "icon": "👤", "require_auth": True},
        {
            "key": "admin", 
            "label": "Admin", 
            "icon": "⚙️", 
            "require_auth": True,
            "require_role": "admin"
        },
    ])
    
    return items


# =============================================================================
# AUTHENTICATION UI
# =============================================================================

def render_login_form():
    """Render login form."""
    st.markdown("### 🔐 Login")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="email@example.com")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Login", use_container_width=True)
        with col2:
            if st.form_submit_button("Register", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        
        if submitted:
            if email and password:
                # Authentication logic would go here
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0].title()
                st.session_state.user_role = "user"
                st.success("✅ Login berhasil!")
                st.rerun()
            else:
                st.error("Email dan password harus diisi")
    
    st.divider()
    
    # Google OAuth button
    if st.button("🔵 Login dengan Google", use_container_width=True):
        st.info("Google OAuth akan diimplementasikan")


def render_register_form():
    """Render registration form."""
    st.markdown("### 📝 Registrasi")
    
    with st.form("register_form"):
        name = st.text_input("Nama Lengkap", placeholder="Nama Anda")
        email = st.text_input("Email", placeholder="email@example.com")
        phone = st.text_input("No. Telepon", placeholder="+628xxxxxxxxxx")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Konfirmasi Password", type="password")
        
        agree = st.checkbox("Saya menyetujui syarat dan ketentuan")
        
        submitted = st.form_submit_button("Daftar", use_container_width=True)
        
        if submitted:
            if not all([name, email, password, confirm_password]):
                st.error("Semua field harus diisi")
            elif password != confirm_password:
                st.error("Password tidak cocok")
            elif not agree:
                st.error("Anda harus menyetujui syarat dan ketentuan")
            else:
                st.success("✅ Registrasi berhasil! Silakan cek email untuk verifikasi.")
                st.session_state.show_register = False
    
    if st.button("← Kembali ke Login"):
        st.session_state.show_register = False
        st.rerun()


def render_login_prompt():
    """Render login prompt for protected pages."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.info("🔐 Silakan login untuk melanjutkan")
        
        if st.button("Login", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()


def logout():
    """Logout current user."""
    keys_to_clear = [
        "authenticated", "user_email", "user_name", "user_role",
        "user_id", "session_token"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("👋 Berhasil logout")
    st.rerun()


# =============================================================================
# CHAT WIDGET
# =============================================================================

def render_chat_widget(
    messages: List[Dict[str, str]] = None,
    on_send: Callable = None,
    placeholder: str = "Ketik pesan Anda...",
    height: int = 400
):
    """
    Render chat widget.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        on_send: Callback when message is sent
        placeholder: Input placeholder text
        height: Container height
    """
    messages = messages or []
    
    # Chat container
    chat_container = st.container(height=height)
    
    with chat_container:
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                with st.chat_message("user"):
                    st.write(content)
            elif role == "assistant":
                with st.chat_message("assistant", avatar="🕋"):
                    st.write(content)
            elif role == "system":
                st.info(content)
    
    # Input
    user_input = st.chat_input(placeholder)
    
    if user_input and on_send:
        on_send(user_input)
        return user_input
    
    return None


def render_streaming_response(response_generator):
    """
    Render streaming AI response.
    
    Args:
        response_generator: Generator yielding response chunks
    """
    with st.chat_message("assistant", avatar="🕋"):
        response_placeholder = st.empty()
        full_response = ""
        
        for chunk in response_generator:
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    return full_response


# =============================================================================
# COST SIMULATOR WIDGET
# =============================================================================

def render_cost_input_form() -> Optional[Dict[str, Any]]:
    """Render cost simulator input form."""
    from core.constants import INDONESIA_CITIES, CostConstants
    from data.models import HotelStarRating, PackageType
    
    st.markdown("### 🧮 Simulasi Biaya Umrah")
    
    with st.form("cost_simulator_form"):
        # Departure info
        col1, col2 = st.columns(2)
        
        with col1:
            cities = [c["name"] for c in INDONESIA_CITIES]
            departure_city = st.selectbox("Kota Keberangkatan", cities)
        
        with col2:
            package_type = st.selectbox(
                "Tipe Paket",
                [p.value.title() for p in PackageType]
            )
        
        # Dates
        col1, col2 = st.columns(2)
        
        with col1:
            departure_date = st.date_input(
                "Tanggal Berangkat",
                min_value=date.today()
            )
        
        with col2:
            return_date = st.date_input(
                "Tanggal Pulang",
                min_value=date.today()
            )
        
        # Travelers
        traveler_count = st.number_input(
            "Jumlah Jamaah",
            min_value=1,
            max_value=50,
            value=1
        )
        
        # Hotel preferences
        st.markdown("**Hotel**")
        col1, col2 = st.columns(2)
        
        with col1:
            hotel_makkah = st.selectbox(
                "Hotel Makkah",
                [f"{r.value}⭐" for r in HotelStarRating]
            )
            days_makkah = st.number_input("Hari di Makkah", min_value=1, value=5)
        
        with col2:
            hotel_madinah = st.selectbox(
                "Hotel Madinah",
                [f"{r.value}⭐" for r in HotelStarRating]
            )
            days_madinah = st.number_input("Hari di Madinah", min_value=1, value=4)
        
        # Additional options
        st.markdown("**Layanan Tambahan**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_visa = st.checkbox("Visa", value=True)
        with col2:
            include_insurance = st.checkbox("Asuransi", value=True)
        with col3:
            include_mutawif = st.checkbox("Mutawif", value=True)
        
        submitted = st.form_submit_button("💰 Hitung Biaya", use_container_width=True)
        
        if submitted:
            return {
                "departure_city": departure_city,
                "departure_date": departure_date,
                "return_date": return_date,
                "traveler_count": traveler_count,
                "hotel_makkah_star": int(hotel_makkah[0]),
                "hotel_madinah_star": int(hotel_madinah[0]),
                "days_makkah": days_makkah,
                "days_madinah": days_madinah,
                "package_type": package_type.lower(),
                "include_visa": include_visa,
                "include_insurance": include_insurance,
                "include_mutawif": include_mutawif,
            }
    
    return None


def render_cost_result(result: Dict[str, Any]):
    """Render cost simulation result."""
    st.markdown("### 📊 Hasil Simulasi")
    
    breakdown = result.get("breakdown", {})
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total per Orang",
            f"Rp {result.get('total_per_person', 0):,.0f}"
        )
    
    with col2:
        st.metric(
            "Total Semua",
            f"Rp {result.get('total_all', 0):,.0f}"
        )
    
    with col3:
        st.metric(
            "Musim",
            result.get("season_type", "Regular").title()
        )
    
    st.divider()
    
    # Cost breakdown
    st.markdown("**Rincian Biaya:**")
    
    items = [
        ("✈️ Tiket Pesawat", breakdown.get("flight_cost", 0)),
        ("🏨 Hotel Makkah", breakdown.get("hotel_makkah_cost", 0)),
        ("🏨 Hotel Madinah", breakdown.get("hotel_madinah_cost", 0)),
        ("📋 Visa", breakdown.get("visa_cost", 0)),
        ("🛡️ Asuransi", breakdown.get("insurance_cost", 0)),
        ("👨‍🏫 Mutawif", breakdown.get("mutawif_cost", 0)),
        ("📦 Handling", breakdown.get("handling_fee", 0)),
    ]
    
    for label, amount in items:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(label)
        with col2:
            st.write(f"Rp {amount:,.0f}")
    
    # Disclaimer
    st.divider()
    st.warning(Messages.DISCLAIMER)


# =============================================================================
# UTILITY COMPONENTS
# =============================================================================

def render_disclaimer():
    """Render standard disclaimer."""
    with st.expander("⚠️ Disclaimer", expanded=False):
        st.markdown(Messages.DISCLAIMER)


def render_footer():
    """Render page footer."""
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"© 2024 {APP_NAME}")
    
    with col2:
        st.caption(f"Version {APP_VERSION}")
    
    with col3:
        st.caption("Powered by MS Hadianto")


def render_loading(message: str = "Memuat..."):
    """Render loading indicator."""
    with st.spinner(message):
        return st.empty()


def render_success_message(message: str, duration: int = 3):
    """Render success message."""
    st.success(message)


def render_error_message(message: str):
    """Render error message."""
    st.error(message)


def render_info_card(
    title: str,
    content: str,
    icon: str = "ℹ️",
    color: str = "blue"
):
    """Render info card."""
    st.markdown(f"""
    <div style="
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: {'#e3f2fd' if color == 'blue' else '#e8f5e9'};
        border-left: 4px solid {'#1976d2' if color == 'blue' else '#388e3c'};
    ">
        <h4>{icon} {title}</h4>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(
    title: str,
    value: str,
    delta: str = None,
    delta_color: str = "normal"
):
    """Render metric card."""
    st.metric(title, value, delta=delta, delta_color=delta_color)


def render_progress_card(
    title: str,
    current: int,
    total: int,
    unit: str = ""
):
    """Render progress card."""
    progress = current / total if total > 0 else 0
    
    st.markdown(f"**{title}**")
    st.progress(progress)
    st.caption(f"{current}/{total} {unit}")


# =============================================================================
# FORM HELPERS
# =============================================================================

def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    import re
    pattern = r'^\+?[0-9]{10,15}$'
    return bool(re.match(pattern, phone.replace(" ", "").replace("-", "")))


def format_currency(amount: float, currency: str = "IDR") -> str:
    """Format number as currency with Indonesian dot separator."""
    if currency == "IDR":
        return f"Rp {amount:,.0f}".replace(",", ".")
    elif currency == "USD":
        return f"${amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif currency == "SAR":
        return f"SAR {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{amount:,.2f}"


def format_idr(amount: float) -> str:
    """Format amount as Indonesian Rupiah (Rp X.XXX.XXX)."""
    return f"Rp {int(round(amount)):,}".replace(",", ".")


def format_idr_short(amount: float) -> str:
    """Format Rupiah with short notation (jt/rb)."""
    if amount >= 1_000_000:
        return f"Rp {amount / 1_000_000:.1f} jt"
    elif amount >= 1_000:
        return f"Rp {amount / 1_000:.0f} rb"
    return f"Rp {amount:,.0f}"


def format_sar(amount: float) -> str:
    """Format amount as Saudi Riyal."""
    return f"SAR {amount:,.0f}"


def format_date(dt: date, format_str: str = "%d %B %Y") -> str:
    """Format date for display."""
    return dt.strftime(format_str)
