"""
LABBAIK AI - Authentication Page
=================================
User registration and login UI.
"""

import re
import streamlit as st
from typing import Optional
from services.user import (
    UserService, UserRole, User,
    get_user_service
)
from services.user.user_service import (
    get_current_user, set_current_user, is_logged_in
)
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS
try:
    from services.ai.helpers import add_xp_safe
except ImportError:
    def add_xp_safe(*a, **kw): pass


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_email(email: str):
    """Validate email format. Returns (is_valid, error_message)."""
    if not email:
        return False, "Email wajib diisi"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Format email tidak valid (contoh: nama@email.com)"
    return True, ""


def get_password_strength(password: str):
    """Return (score 0-4, label, color) for password strength."""
    if not password:
        return 0, "", "#333"
    score = 0
    if len(password) >= 6:
        score += 1
    if len(password) >= 8:
        score += 1
    if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[0-9!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    labels = {0: "Terlalu pendek", 1: "Sangat lemah", 2: "Lemah", 3: "Sedang", 4: "Kuat"}
    colors = {0: "#b0b0b0", 1: "#ef4444", 2: "#f97316", 3: "#eab308", 4: "#22c55e"}
    return score, labels[score], colors[score]

# Indonesian provinces for dropdown
PROVINCES = [
    "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi",
    "Sumatera Selatan", "Bengkulu", "Lampung", "Kepulauan Bangka Belitung",
    "Kepulauan Riau", "DKI Jakarta", "Jawa Barat", "Jawa Tengah",
    "DI Yogyakarta", "Jawa Timur", "Banten", "Bali", "Nusa Tenggara Barat",
    "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah",
    "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara",
    "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan",
    "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku",
    "Maluku Utara", "Papua", "Papua Barat", "Papua Selatan",
    "Papua Tengah", "Papua Pegunungan"
]

DEPARTURE_CITIES = [
    "Jakarta (CGK)", "Surabaya (SUB)", "Medan (KNO)", "Makassar (UPG)",
    "Bandung (BDO)", "Semarang (SRG)", "Yogyakarta (JOG)", "Denpasar (DPS)",
    "Balikpapan (BPN)", "Pekanbaru (PKU)", "Palembang (PLM)", "Padang (PDG)",
    "Manado (MDC)", "Banjarmasin (BDJ)", "Solo (SOC)", "Aceh (BTJ)"
]

BUDGET_RANGES = [
    ("low", "Hemat (< 25 Juta)"),
    ("medium", "Standar (25-35 Juta)"),
    ("high", "Nyaman (35-50 Juta)"),
    ("premium", "Premium (> 50 Juta)")
]

TRAVEL_STYLES = [
    ("backpacker", "Backpacker - Mandiri & Hemat"),
    ("standard", "Standar - Rombongan Travel"),
    ("comfort", "Comfort - Fasilitas Lengkap"),
    ("luxury", "Luxury - VIP Experience")
]


def render_login_form():
    """Render login form"""
    st.markdown("### Masuk ke Akun")

    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="contoh@email.com")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Masuk", use_container_width=True, type="primary")

        if submit:
            if not email or not password:
                st.error("Email dan password wajib diisi")
                return
            email_valid, email_err = validate_email(email)
            if not email_valid:
                st.error(email_err)
                return

            service = get_user_service()
            success, message, user = service.login(email, password)

            if success and user:
                set_current_user(user)
                if not st.session_state.get("login_xp_awarded"):
                    add_xp_safe(10, "Login berhasil")
                    st.session_state.login_xp_awarded = True
                st.success(message)
                st.balloons()
                st.rerun()
            else:
                st.error(message)

    st.markdown("---")
    st.markdown("Belum punya akun?")
    if st.button("Daftar Sekarang", use_container_width=True):
        st.session_state.auth_mode = "register"
        st.rerun()


def render_register_form():
    """Render registration form"""
    st.markdown("### Daftar Akun Baru")
    st.markdown("Daftar untuk menyimpan simulasi, chat AI unlimited, dan fitur premium lainnya.")

    with st.form("register_form"):
        # Basic info
        st.markdown("#### Informasi Dasar")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nama Lengkap *", placeholder="Nama Anda")
            email = st.text_input("Email *", placeholder="contoh@email.com")
        with col2:
            phone = st.text_input("No. WhatsApp", placeholder="08123456789")
            password = st.text_input("Password *", type="password", help="Minimal 6 karakter")

        st.markdown("---")
        st.markdown("#### Lokasi")
        col1, col2 = st.columns(2)
        with col1:
            province = st.selectbox("Provinsi", [""] + PROVINCES)
        with col2:
            city = st.text_input("Kota/Kabupaten", placeholder="Nama kota")

        st.markdown("---")
        st.markdown("#### Preferensi Umrah (Opsional)")
        st.caption("Bantu kami memberikan rekomendasi yang lebih tepat untuk Anda")

        col1, col2 = st.columns(2)
        with col1:
            departure_city = st.selectbox("Kota Keberangkatan Pilihan", [""] + DEPARTURE_CITIES)
            budget_range = st.selectbox(
                "Range Budget",
                [""] + [f"{v[1]}" for v in BUDGET_RANGES],
                help="Perkiraan budget untuk Umrah"
            )
        with col2:
            travel_style = st.selectbox(
                "Gaya Travel",
                [""] + [f"{v[1]}" for v in TRAVEL_STYLES],
                help="Preferensi gaya perjalanan Anda"
            )

        st.markdown("---")

        # Terms
        agree = st.checkbox("Saya setuju dengan syarat dan ketentuan LABBAIK AI")

        submit = st.form_submit_button("Daftar", use_container_width=True, type="primary")

        if submit:
            if not agree:
                st.error("Anda harus menyetujui syarat dan ketentuan")
                return

            if not name or not email or not password:
                st.error("Nama, email, dan password wajib diisi")
                return

            email_valid, email_err = validate_email(email)
            if not email_valid:
                st.error(email_err)
                return

            if len(password) < 6:
                st.error("Password minimal 6 karakter")
                return

            score, label, color = get_password_strength(password)
            if score < 2:
                st.warning(f"Password Anda '{label}'. Disarankan kombinasi huruf besar, kecil, dan angka.")

            # Map selection back to values
            budget_val = None
            for val, label in BUDGET_RANGES:
                if label == budget_range:
                    budget_val = val
                    break

            style_val = None
            for val, label in TRAVEL_STYLES:
                if label == travel_style:
                    style_val = val
                    break

            service = get_user_service()
            success, message, user = service.register(
                email=email,
                password=password,
                name=name,
                phone=phone if phone else None,
                city=city if city else None,
                province=province if province else None,
                preferred_departure_city=departure_city if departure_city else None,
                budget_range=budget_val,
                travel_style=style_val,
                source="web"
            )

            if success and user:
                set_current_user(user)
                add_xp_safe(50, "Berhasil mendaftar akun")
                st.success(f"Selamat datang, {user.name}! Akun Anda telah dibuat.")
                st.balloons()
                st.rerun()
            else:
                st.error(message)

    # Password tip
    st.markdown("""
    <div style="background: #1a1a2e; border: 1px solid #333; border-radius: 8px;
                padding: 0.75rem; margin-top: 0.5rem;">
        <div style="color: #b0b0b0; font-size: 0.8rem;">
            <strong style="color: #d4af37;">Tips password kuat:</strong>
            Minimal 6 karakter, kombinasi huruf besar + kecil + angka/simbol
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("Sudah punya akun?")
    if st.button("Masuk", use_container_width=True):
        st.session_state.auth_mode = "login"
        st.rerun()


def render_user_profile():
    """Render user profile for logged in users"""
    user = get_current_user()
    if not user:
        return

    st.markdown(f"### Profil: {user.name}")

    # User info card
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Role", user.role.display_name)
    with col2:
        st.metric("Login", f"{user.login_count}x")
    with col3:
        if user.last_login:
            st.metric("Login Terakhir", user.last_login.strftime("%d %b %Y"))

    st.markdown("---")

    # Edit profile
    with st.expander("Edit Profil", expanded=False):
        with st.form("edit_profile"):
            name = st.text_input("Nama", value=user.name)
            phone = st.text_input("No. WhatsApp", value=user.phone or "")

            col1, col2 = st.columns(2)
            with col1:
                province_idx = PROVINCES.index(user.province) + 1 if user.province in PROVINCES else 0
                province = st.selectbox("Provinsi", [""] + PROVINCES, index=province_idx)
            with col2:
                city = st.text_input("Kota", value=user.city or "")

            col1, col2 = st.columns(2)
            with col1:
                dep_idx = DEPARTURE_CITIES.index(user.preferred_departure_city) + 1 if user.preferred_departure_city in DEPARTURE_CITIES else 0
                departure = st.selectbox("Kota Keberangkatan", [""] + DEPARTURE_CITIES, index=dep_idx)

            if st.form_submit_button("Simpan Perubahan", type="primary"):
                service = get_user_service()
                service.update_profile(
                    user,
                    name=name,
                    phone=phone if phone else None,
                    province=province if province else None,
                    city=city if city else None,
                    preferred_departure_city=departure if departure else None
                )
                add_xp_safe(5, "Memperbarui profil")
                st.success("Profil berhasil diperbarui!")
                st.rerun()

    # Role benefits
    st.markdown("---")
    st.markdown("#### Manfaat Akun Anda")

    if user.role == UserRole.FREE:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Fitur Gratis:**
            - Lihat semua paket Umrah
            - Simulasi biaya
            - Chat AI (5x/hari)
            - Lihat prediksi keramaian
            - Panduan Umrah dasar
            """)
        with col2:
            st.markdown("""
            **Upgrade ke Premium:**
            - Chat AI unlimited
            - Notifikasi harga
            - Group tracking
            - Download laporan
            - Prioritas support
            """)
            if st.button("Upgrade ke Premium", type="primary", use_container_width=True):
                st.info("Fitur pembayaran akan segera hadir!")

    elif user.role == UserRole.PREMIUM:
        st.success("Anda adalah pengguna Premium dengan akses penuh!")

    # Logout button
    st.markdown("---")
    if st.button("Keluar", use_container_width=True):
        set_current_user(None)
        st.success("Anda telah keluar")
        st.rerun()


def render_auth_page():
    """Main auth page renderer"""
    try:
        from services.analytics import track_page
        track_page("auth")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS)

    st.markdown("""
        <div class="page-hero">
            <h1><span aria-hidden="true">🔐 </span>Selamat Datang</h1>
            <div class="subtitle">Masuk atau daftar untuk mengakses LABBAIK AI</div>
        </div>
    """, unsafe_allow_html=True)

    # Check if already logged in
    if is_logged_in():
        render_user_profile()
        return

    # Auth mode toggle
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    # Render appropriate form
    if st.session_state.auth_mode == "register":
        render_register_form()
    else:
        render_login_form()


def render_login_widget():
    """Compact login widget for sidebar"""
    if is_logged_in():
        user = get_current_user()
        st.markdown(f"""
            <div style="padding: 0.5rem; background: rgba(76,175,80,0.1); border-radius: 8px; text-align: center;">
                <div style="font-size: 0.9rem;">Halo, <strong>{(user.name.split() or [user.name or "User"])[0]}</strong></div>
                <div style="font-size: 0.75rem; color: #4CAF50;">{user.role.display_name}</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Profil", use_container_width=True, key="sidebar_profile"):
            st.session_state.current_page = "auth"
            st.rerun()
    else:
        if st.button("Masuk / Daftar", use_container_width=True, key="sidebar_login"):
            st.session_state.current_page = "auth"
            st.session_state.auth_mode = "login"
            st.rerun()


def render_user_badge():
    """User badge for header"""
    if is_logged_in():
        user = get_current_user()
        role_colors = {
            UserRole.FREE: "#2196F3",
            UserRole.PREMIUM: "#FFD700",
            UserRole.PARTNER: "#9C27B0",
            UserRole.ADMIN: "#F44336"
        }
        color = role_colors.get(user.role, "#2196F3")

        st.markdown(f"""
            <div style="display: inline-flex; align-items: center; gap: 8px;
                        padding: 4px 12px; background: rgba(255,255,255,0.1);
                        border-radius: 20px; font-size: 0.85rem;">
                <span style="color: {color};">●</span>
                <span>{(user.name.split() or [user.name or "User"])[0]}</span>
            </div>
        """, unsafe_allow_html=True)


__all__ = ["render_auth_page", "render_login_widget", "render_user_badge"]
