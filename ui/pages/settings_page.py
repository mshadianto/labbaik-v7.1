"""
================================================================================
LABBAIK AI - User Settings / Preferences Page
================================================================================
Minimal user preferences page. All settings are stored in session state
(no database required).
================================================================================
"""

import streamlit as st
from datetime import datetime

try:
    from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS
except ImportError:
    def inject_css(*args): pass
    HERO_CSS = ""
    CARD_CSS = ""

try:
    from core.version import get_display_version, APP_VERSION
except ImportError:
    def get_display_version():
        return "v7.8.0"
    APP_VERSION = "7.8.0"


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

SETTINGS_CSS = """
.settings-section {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border: 1px solid #333;
    border-radius: 15px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}
.settings-section h3 {
    color: #d4af37;
    font-size: 1rem;
    margin-top: 0;
    margin-bottom: 0.75rem;
}
.settings-section p {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin: 0;
}
.settings-about {
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(145deg, #0d1b2a 0%, #1b2a4a 100%);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 15px;
}
.settings-about .version {
    color: #d4af37;
    font-size: 1.1rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.settings-about .links {
    margin-top: 0.75rem;
}
.settings-about .links a {
    color: #60a5fa;
    text-decoration: none;
    font-size: 0.85rem;
    margin: 0 0.5rem;
}
.settings-about .links a:hover {
    text-decoration: underline;
}
.danger-zone {
    background: linear-gradient(145deg, #2a1a1a 0%, #1e1010 100%);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 15px;
    padding: 1.25rem;
    margin-top: 1rem;
}
.danger-zone h3 {
    color: #f87171;
    font-size: 1rem;
    margin-top: 0;
    margin-bottom: 0.5rem;
}
.danger-zone p {
    color: #b0b0b0;
    font-size: 0.8rem;
    margin-bottom: 0.75rem;
}
"""


def _init_settings_state():
    """Ensure all settings keys exist in session state."""
    defaults = {
        "pref_notif_email": True,
        "pref_notif_whatsapp": False,
        "pref_notif_inapp": True,
        "pref_display_compact": False,
        "_settings_confirm_clear": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_settings_page():
    """Render the user settings/preferences page."""
    _init_settings_state()

    inject_css(HERO_CSS, CARD_CSS, SETTINGS_CSS)

    # Page Hero
    st.markdown("""
    <div class="page-hero" style="--hero-bg: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);">
        <div style="font-size: 2rem;" aria-hidden="true">&#x2699;&#xFE0F;</div>
        <h1>Pengaturan</h1>
        <div class="subtitle">Sesuaikan preferensi aplikasi Anda</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # NOTIFICATION PREFERENCES
    # =========================================================================
    st.markdown("""
    <div class="settings-section">
        <h3><span aria-hidden="true">&#x1F514;</span> Preferensi Notifikasi</h3>
        <p>Pilih cara Anda ingin menerima pemberitahuan.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        email_notif = st.toggle(
            "Email",
            value=st.session_state.get("pref_notif_email", True),
            key="toggle_notif_email",
            help="Terima notifikasi via email",
        )
        if email_notif != st.session_state.get("pref_notif_email"):
            st.session_state.pref_notif_email = email_notif

    with col2:
        wa_notif = st.toggle(
            "WhatsApp",
            value=st.session_state.get("pref_notif_whatsapp", False),
            key="toggle_notif_wa",
            help="Terima notifikasi via WhatsApp",
        )
        if wa_notif != st.session_state.get("pref_notif_whatsapp"):
            st.session_state.pref_notif_whatsapp = wa_notif

    with col3:
        inapp_notif = st.toggle(
            "Dalam Aplikasi",
            value=st.session_state.get("pref_notif_inapp", True),
            key="toggle_notif_inapp",
            help="Terima notifikasi dalam aplikasi",
        )
        if inapp_notif != st.session_state.get("pref_notif_inapp"):
            st.session_state.pref_notif_inapp = inapp_notif

    st.markdown("")

    # =========================================================================
    # DISPLAY PREFERENCES
    # =========================================================================
    st.markdown("""
    <div class="settings-section">
        <h3><span aria-hidden="true">&#x1F3A8;</span> Preferensi Tampilan</h3>
        <p>Atur tampilan aplikasi sesuai kenyamanan Anda.</p>
    </div>
    """, unsafe_allow_html=True)

    compact_mode = st.toggle(
        "Mode Kompak",
        value=st.session_state.get("pref_display_compact", False),
        key="toggle_compact_mode",
        help="Tampilan ringkas dengan elemen yang lebih kecil",
    )
    if compact_mode != st.session_state.get("pref_display_compact"):
        st.session_state.pref_display_compact = compact_mode

    if compact_mode:
        st.caption("Mode kompak aktif - tampilan lebih ringkas.")
    else:
        st.caption("Mode penuh - tampilan lengkap dengan detail.")

    st.markdown("")

    # =========================================================================
    # DATA / SESSION MANAGEMENT
    # =========================================================================
    st.markdown("""
    <div class="danger-zone">
        <h3><span aria-hidden="true">&#x26A0;&#xFE0F;</span> Manajemen Data</h3>
        <p>Hapus semua data sesi Anda. Tindakan ini tidak dapat dibatalkan.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("_settings_confirm_clear", False):
        if st.button("Hapus Semua Data Sesi", key="btn_clear_session", type="secondary"):
            st.session_state._settings_confirm_clear = True
            st.rerun()
    else:
        st.warning("Apakah Anda yakin? Semua data sesi (chat, XP, checklist, dll.) akan dihapus.")
        ccol1, ccol2 = st.columns(2)
        with ccol1:
            if st.button("Ya, Hapus Semua", key="btn_confirm_clear", type="primary"):
                # Preserve only essential keys
                preserved = {
                    "current_page": "settings",
                    "visitor_counted": True,
                    "_meta_injected": True,
                }
                for key in list(st.session_state.keys()):
                    if key not in preserved:
                        del st.session_state[key]
                for k, v in preserved.items():
                    st.session_state[k] = v
                st.success("Data sesi berhasil dihapus.")
                st.rerun()
        with ccol2:
            if st.button("Batal", key="btn_cancel_clear"):
                st.session_state._settings_confirm_clear = False
                st.rerun()

    st.markdown("")

    # =========================================================================
    # ABOUT SECTION
    # =========================================================================
    st.markdown(f"""
    <div class="settings-about">
        <div style="font-size: 2rem;" aria-hidden="true">&#x1F54B;</div>
        <div class="version">LABBAIK Smart Planner {get_display_version()}</div>
        <div style="color: #b0b0b0; font-size: 0.85rem;">
            Satu-satunya AI Companion untuk Umrah Anda
        </div>
        <div style="color: #8e9fb3; font-size: 0.75rem; margin-top: 0.5rem;">
            &copy; 2026 MS Hadianto. Platform Umrah Cerdas Indonesia.
        </div>
        <div class="links">
            <a href="https://labbaik.io" target="_blank">Website</a>
            <a href="https://labbaik.io/support" target="_blank">Bantuan</a>
            <a href="https://labbaik.io/feedback" target="_blank">Feedback</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
