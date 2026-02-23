"""
LABBAIK AI - Partnership Portal
================================
Halaman khusus untuk program kemitraan travel umrah.
Menampilkan tier pricing dari config/pricing.yaml.
Data mitra disimpan ke DB (PostgreSQL) dengan fallback ke session state.
"""

import streamlit as st
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

# =============================================================================
# DATABASE AVAILABILITY
# =============================================================================

HAS_DB = False
try:
    from services.database.repository import get_db
    HAS_DB = True
except ImportError:
    HAS_DB = False


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def _init_partner_session_state():
    """Initialize session state keys for partnership data."""
    if "partner_registrations" not in st.session_state:
        st.session_state.partner_registrations = []
    if "show_registration" not in st.session_state:
        st.session_state.show_registration = False
    if "selected_batch" not in st.session_state:
        st.session_state.selected_batch = None


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def _validate_email(email: str):
    """Validate email format. Returns (is_valid, error_message)."""
    if not email:
        return False, "Email wajib diisi"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Format email tidak valid"
    return True, ""


def _validate_phone(phone: str):
    """Validate phone number. Returns (is_valid, error_message)."""
    if not phone:
        return False, "Nomor telepon wajib diisi"
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    if len(cleaned) < 8 or not cleaned.isdigit():
        return False, "Format nomor telepon tidak valid (minimal 8 digit)"
    return True, ""


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def _load_partner_counts_from_db():
    """Load partner counts per batch from database.

    Returns dict of {batch_id: count} or None if DB unavailable.
    """
    if not HAS_DB:
        return None
    try:
        db = get_db()
        rows = db.fetch_all("""
            SELECT tier_batch_id, COUNT(*) as cnt
            FROM partners
            WHERE registration_status IN ('pending', 'approved')
            GROUP BY tier_batch_id
        """)
        if rows is not None:
            return {row["tier_batch_id"]: int(row["cnt"]) for row in rows}
    except Exception as e:
        logger.debug(f"Could not load partner counts from DB: {e}")
    return None


@st.cache_data(ttl=300, show_spinner=False)
def _cached_partner_counts():
    """Cached wrapper for partner tier counts."""
    return _load_partner_counts_from_db()


def _load_partner_stats_from_db():
    """Load aggregate partner statistics from database.

    Returns dict with total_partners, active_partners, pending_partners
    or None if DB unavailable.
    """
    if not HAS_DB:
        return None
    try:
        db = get_db()
        result = db.fetch_one("""
            SELECT
                COUNT(*) as total_partners,
                COUNT(*) FILTER (WHERE registration_status = 'approved') as active_partners,
                COUNT(*) FILTER (WHERE registration_status = 'pending') as pending_partners
            FROM partners
        """)
        if result:
            return {
                "total_partners": int(result.get("total_partners", 0)),
                "active_partners": int(result.get("active_partners", 0)),
                "pending_partners": int(result.get("pending_partners", 0)),
            }
    except Exception as e:
        logger.debug(f"Could not load partner stats from DB: {e}")
    return None


@st.cache_data(ttl=300, show_spinner=False)
def _cached_partner_stats():
    """Cached wrapper for partner statistics."""
    return _load_partner_stats_from_db()


def _save_registration_to_db(registration_data: dict) -> bool:
    """Save partner registration to database.

    Returns True on success, False on failure.
    """
    if not HAS_DB:
        return False
    try:
        db = get_db()
        db.execute("""
            INSERT INTO partners (
                tier_batch_id, tier_name, commission_rate_locked,
                setup_fee_paid, status_granted,
                company_name, company_email, company_phone, company_address,
                pic_name, pic_phone, pic_position,
                experience_years, packages_per_year, motivation,
                registration_status
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                'pending'
            )
        """, (
            registration_data["batch_id"],
            registration_data["batch_name"],
            registration_data["commission_rate"],
            registration_data["setup_fee"],
            registration_data["status"],
            registration_data["company_name"],
            registration_data["company_email"],
            registration_data["company_phone"],
            registration_data.get("company_address", ""),
            registration_data["pic_name"],
            registration_data["pic_phone"],
            registration_data.get("pic_position", ""),
            registration_data.get("experience", ""),
            registration_data.get("packages_per_year", 0),
            registration_data.get("motivation", ""),
        ))
        logger.info(f"Partner registration saved to DB: {registration_data['company_name']}")
        return True
    except Exception as e:
        logger.warning(f"Could not save registration to DB: {e}")
        return False


def _check_duplicate_email_db(email: str) -> bool:
    """Check if company email already registered in DB.

    Returns True if duplicate found.
    """
    if not HAS_DB:
        return False
    try:
        db = get_db()
        result = db.fetch_one(
            "SELECT id FROM partners WHERE company_email = %s LIMIT 1",
            (email,)
        )
        return result is not None
    except Exception:
        return False


# =============================================================================
# SESSION STATE DATA HELPERS
# =============================================================================

def _get_partner_counts():
    """Get partner counts per batch from DB with session state fallback.

    Returns dict of {batch_id: count}.
    """
    # Try DB first (cached)
    db_counts = _cached_partner_counts()
    if db_counts is not None:
        return db_counts

    # Fallback: calculate from session state registrations
    counts = {}
    registrations = st.session_state.get("partner_registrations", [])
    for reg in registrations:
        bid = reg.get("batch_id", "")
        counts[bid] = counts.get(bid, 0) + 1
    return counts


def _get_partner_stats():
    """Get aggregate partner stats from DB with session state fallback.

    Returns dict with total_partners, active_partners, pending_partners.
    """
    # Try DB first (cached)
    db_stats = _cached_partner_stats()
    if db_stats is not None:
        return db_stats

    # Fallback: derive from session state
    registrations = st.session_state.get("partner_registrations", [])
    total = len(registrations)
    pending = sum(1 for r in registrations if r.get("registration_status") == "pending")
    active = sum(1 for r in registrations if r.get("registration_status") == "approved")
    return {
        "total_partners": total,
        "active_partners": active,
        "pending_partners": pending,
    }


def _check_duplicate_email(email: str) -> bool:
    """Check if email is already registered (DB + session state)."""
    # Check DB
    if _check_duplicate_email_db(email):
        return True
    # Check session state
    registrations = st.session_state.get("partner_registrations", [])
    for reg in registrations:
        if reg.get("company_email", "").lower() == email.lower():
            return True
    return False


# =============================================================================
# PRICING DATA LOADER
# =============================================================================

def load_pricing_data():
    """Load pricing data from config."""
    try:
        from utils.pricing_loader import (
            get_pioneer_config,
            get_all_batches,
            get_current_batch,
            get_faq,
            get_contact_info,
            get_current_day,
            get_batch_countdown,
            is_batch_available,
        )
        return {
            "config": get_pioneer_config(),
            "batches": get_all_batches(),
            "current_batch": get_current_batch(),
            "faq": get_faq(),
            "contact": get_contact_info(),
            "current_day": get_current_day(),
            "get_countdown": get_batch_countdown,
            "is_available": is_batch_available,
        }
    except Exception as e:
        logger.error(f"Failed to load pricing data: {e}")
        return None


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_hero_section(config: dict):
    """Render hero section with program info."""
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">
            {config.get('program_name', 'Labbaik Pioneer 2026')}
        </h1>
        <p style="font-size: 1.2rem; color: #b0b0b0; max-width: 600px; margin: 0 auto;">
            {config.get('program_description', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_partner_stats_banner():
    """Render a summary banner with dynamic partner statistics."""
    stats = _get_partner_stats()
    total = stats["total_partners"]
    active = stats["active_partners"]
    pending = stats["pending_partners"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pendaftar", total)
    with col2:
        st.metric("Mitra Aktif", active)
    with col3:
        st.metric("Menunggu Verifikasi", pending)


def render_current_batch_banner(data: dict):
    """Render banner for current active batch."""
    current = data["current_batch"]
    if not current:
        return

    countdown = data["get_countdown"](current)

    if current.highlight:
        st.success(f"""
        **{current.name}** sedang berlangsung!
        {current.tagline}
        {"Tersisa " + str(countdown) + " hari lagi" if countdown else "Daftar sekarang!"}
        """, icon="🎉")
    else:
        st.info(f"""
        **{current.name}** - {current.tagline}
        {"Tersisa " + str(countdown) + " hari" if countdown else "Pendaftaran terbuka"}
        """)


def render_pricing_card(batch, is_current: bool, partner_count: int = 0):
    """Render a single pricing card."""

    # Card styling based on highlight
    if batch.highlight:
        border_color = batch.badge_color
        bg_color = "#FFF9E6"
        badge = "TERBATAS"
    elif is_current:
        border_color = "#4CAF50"
        bg_color = "#F0FFF0"
        badge = "AKTIF"
    else:
        border_color = "#E0E0E0"
        bg_color = "#FAFAFA"
        badge = None

    # Container
    with st.container():
        # Header with badge
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {batch.name}")
            st.caption(batch.tagline)
        with col2:
            if badge:
                if batch.highlight:
                    st.markdown(f"<span style='background: {batch.badge_color}; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8rem;'>{badge}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='background: #4CAF50; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;'>{badge}</span>", unsafe_allow_html=True)

        # Price
        if batch.is_free:
            st.markdown("<h2 style='color: #4CAF50; margin: 0.5rem 0;'>GRATIS</h2>", unsafe_allow_html=True)
            st.caption("Setup Fee")
        else:
            st.markdown(f"<h2 style='margin: 0.5rem 0;'>{batch.setup_fee_display}</h2>", unsafe_allow_html=True)
            st.caption("Setup Fee (sekali bayar)")

        st.divider()

        # Key Info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", batch.status)
        with col2:
            commission_label = f"{batch.commission_display}"
            if batch.commission_locked:
                commission_label += " (Locked)"
            st.metric("Komisi", commission_label)

        # Setup Type
        st.markdown(f"**Setup:** {batch.setup_type_display}")

        # Benefits
        st.markdown("**Benefit:**")
        for benefit in batch.benefits:
            st.markdown(f"- {benefit}")

        # Slot info with dynamic count
        if batch.max_partners:
            remaining = batch.max_partners - partner_count
            if remaining > 0:
                st.warning(f"Sisa {remaining} slot dari {batch.max_partners} (terisi {partner_count})")
            else:
                st.error("Slot penuh!")
        else:
            if partner_count > 0:
                st.caption(f"{partner_count} mitra terdaftar")

        # CTA Button
        if is_current and (batch.max_partners is None or partner_count < batch.max_partners):
            if st.button(f"Daftar {batch.name}", key=f"cta_{batch.id}", type="primary", use_container_width=True):
                st.session_state.selected_batch = batch.id
                st.session_state.show_registration = True
                st.rerun()


def render_pricing_cards(data: dict):
    """Render all pricing cards in columns."""
    batches = data["batches"]
    current = data["current_batch"]

    st.markdown("## Pilih Paket Kemitraan")
    st.markdown("---")

    # Get partner counts dynamically from DB / session state
    partner_counts = _get_partner_counts()

    # Display in columns
    cols = st.columns(len(batches))

    for idx, batch in enumerate(batches):
        with cols[idx]:
            is_current = current and batch.id == current.id
            count = partner_counts.get(batch.id, 0)
            render_pricing_card(batch, is_current, count)


def render_comparison_table(data: dict):
    """Render feature comparison table using native Streamlit."""
    import pandas as pd

    batches = data["batches"]

    st.markdown("### Perbandingan Lengkap Antar Paket")

    # Build comparison data
    comparison_data = {
        "Fitur": [
            "Setup Fee",
            "Status Member",
            "Durasi Status",
            "Komisi Bagi Hasil",
            "Komisi Terlindungi",
            "Tipe Onboarding",
            "Kuota Partner",
            "Support Level",
            "Training",
            "Akses Fitur Beta",
        ]
    }

    for idx, b in enumerate(batches):
        comparison_data[b.name] = [
            "GRATIS" if b.setup_fee == 0 else b.setup_fee_display,
            b.status,
            "Selamanya" if not b.status_duration_months else f"{b.status_duration_months} bulan",
            f"Locked {b.commission_display}" if b.commission_locked else b.commission_display,
            "Ya, Locked!" if b.commission_locked else "Tidak",
            b.setup_type_display,
            f"{b.max_partners} partner" if b.max_partners else "Unlimited",
            "Priority 24/7" if b.setup_type == "white_glove" else ("Jam Kerja" if idx < 2 else "Email"),
            "1-on-1 Konsultasi" if b.setup_type == "white_glove" else ("2 Sesi Online" if idx == 1 else "Video Tutorial"),
            "Ya" if b.setup_type == "white_glove" else "Tidak",
        ]

    df = pd.DataFrame(comparison_data)

    # Display with styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fitur": st.column_config.TextColumn("Fitur", width="medium"),
            batches[0].name: st.column_config.TextColumn(f"{batches[0].name}", width="medium"),
        }
    )

    # Legend
    st.info("Locked = Komisi terlindungi selamanya | Selamanya = Lifetime status")


def render_faq_section(faq_list: list):
    """Render FAQ accordion."""
    if not faq_list:
        return

    st.markdown("## Pertanyaan Umum")

    for idx, faq in enumerate(faq_list):
        with st.expander(faq.get("question", ""), expanded=False):
            st.markdown(faq.get("answer", ""))


def render_contact_section(contact: dict):
    """Render contact/CTA section using native Streamlit components."""

    wa = contact.get("whatsapp", "")
    wa_display = contact.get("whatsapp_display", wa)
    email = contact.get("email", "")
    calendly = contact.get("calendly", "")
    wa_link = f"https://wa.me/{wa.replace('+', '').replace('-', '')}" if wa else "#"

    # Header
    st.markdown("---")
    st.markdown("## Siap Bergabung?")
    st.caption("Hubungi kami untuk konsultasi gratis dan mulai perjalanan digital Anda")

    # Contact cards using columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #25D366, #128C7E); padding: 1.5rem; border-radius: 12px; text-align: center;">
            <div style="font-size: 2rem;"><span aria-hidden="true">📱</span></div>
            <div style="color: white; font-weight: 600; margin: 0.5rem 0;">WhatsApp</div>
            <div style="color: rgba(255,255,255,0.9);">""" + wa_display + """</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Chat Sekarang", wa_link, use_container_width=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #EA4335, #C5221F); padding: 1.5rem; border-radius: 12px; text-align: center;">
            <div style="font-size: 2rem;"><span aria-hidden="true">📧</span></div>
            <div style="color: white; font-weight: 600; margin: 0.5rem 0;">Email</div>
            <div style="color: rgba(255,255,255,0.9);">""" + email + """</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Kirim Email", f"mailto:{email}", use_container_width=True)

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #006BFF, #0052CC); padding: 1.5rem; border-radius: 12px; text-align: center;">
            <div style="font-size: 2rem;"><span aria-hidden="true">📅</span></div>
            <div style="color: white; font-weight: 600; margin: 0.5rem 0;">Meeting</div>
            <div style="color: rgba(255,255,255,0.9);">Pilih waktu</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Jadwalkan", calendly, use_container_width=True)

    st.caption("Respon cepat dalam waktu 1x24 jam kerja")


def render_registration_form(data: dict):
    """Render partner registration form with validation, DB save, and XP reward."""
    batch_id = st.session_state.get("selected_batch")
    batch = None

    for b in data["batches"]:
        if b.id == batch_id:
            batch = b
            break

    if not batch:
        st.error("Batch tidak ditemukan")
        return

    st.markdown(f"## Daftar: {batch.name}")
    st.info(f"Setup Fee: {batch.setup_fee_display} | Komisi: {batch.commission_display}")

    with st.form("registration_form"):
        st.markdown("### Data Travel")
        company_name = st.text_input("Nama Travel *", placeholder="PT. Travel Umrah Indonesia")
        company_email = st.text_input("Email Bisnis *", placeholder="info@travel.com")
        company_phone = st.text_input("Telepon *", placeholder="021-12345678")
        company_address = st.text_area("Alamat Kantor", placeholder="Jl. Contoh No. 123, Jakarta")

        st.markdown("### Data PIC")
        pic_name = st.text_input("Nama PIC *", placeholder="Ahmad Subari")
        pic_phone = st.text_input("WhatsApp PIC *", placeholder="08123456789")
        pic_position = st.text_input("Jabatan", placeholder="Direktur / Owner")

        st.markdown("### Informasi Tambahan")
        experience = st.selectbox("Pengalaman di Industri Umrah", [
            "< 1 tahun",
            "1-3 tahun",
            "3-5 tahun",
            "> 5 tahun"
        ])
        packages_per_year = st.number_input("Estimasi Paket Umrah per Tahun", min_value=1, value=10)
        motivation = st.text_area("Mengapa tertarik bergabung Labbaik?", placeholder="Ceritakan motivasi Anda...")

        agree_tos = st.checkbox("Saya setuju dengan Syarat & Ketentuan Kemitraan Labbaik")

        submitted = st.form_submit_button("Kirim Pendaftaran", type="primary", use_container_width=True)

        if submitted:
            # --- Validation ---
            errors = []

            if not all([company_name, company_email, company_phone, pic_name, pic_phone]):
                errors.append("Mohon lengkapi semua field yang wajib (*)")

            if company_email:
                email_valid, email_err = _validate_email(company_email)
                if not email_valid:
                    errors.append(email_err)

            if company_phone:
                phone_valid, phone_err = _validate_phone(company_phone)
                if not phone_valid:
                    errors.append(phone_err)

            if pic_phone:
                pic_phone_valid, pic_phone_err = _validate_phone(pic_phone)
                if not pic_phone_valid:
                    errors.append(f"WhatsApp PIC: {pic_phone_err}")

            if not agree_tos:
                errors.append("Anda harus menyetujui Syarat & Ketentuan")

            # Check duplicate email
            if company_email and not errors:
                if _check_duplicate_email(company_email):
                    errors.append(f"Email {company_email} sudah terdaftar. Gunakan email lain atau hubungi tim kami.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                # --- Build registration data ---
                registration_data = {
                    "batch_id": batch.id,
                    "batch_name": batch.name,
                    "commission_rate": batch.commission_rate,
                    "setup_fee": batch.setup_fee,
                    "status": batch.status,
                    "company_name": company_name,
                    "company_email": company_email,
                    "company_phone": company_phone,
                    "company_address": company_address,
                    "pic_name": pic_name,
                    "pic_phone": pic_phone,
                    "pic_position": pic_position,
                    "experience": experience,
                    "packages_per_year": packages_per_year,
                    "motivation": motivation,
                    "registered_at": datetime.now().isoformat(),
                    "registration_status": "pending",
                }

                # --- Save to DB ---
                saved_to_db = _save_registration_to_db(registration_data)

                # --- Always save to session state ---
                st.session_state.partner_registrations.append(registration_data)

                # --- Success feedback ---
                if saved_to_db:
                    st.success(
                        "Pendaftaran berhasil disimpan! Tim kami akan menghubungi Anda "
                        "dalam 1x24 jam kerja untuk verifikasi."
                    )
                else:
                    st.success(
                        "Pendaftaran berhasil dikirim! Tim kami akan menghubungi Anda "
                        "dalam 1x24 jam."
                    )
                    st.caption("Data tersimpan secara lokal. Pastikan koneksi internet untuk sinkronisasi.")

                # --- Award XP for completing registration ---
                xp_key = f"partner_reg_xp_{company_email}"
                if not st.session_state.get(xp_key):
                    add_xp_safe(25, "Menyelesaikan pendaftaran mitra")
                    st.session_state[xp_key] = True

                # --- Show summary ---
                st.markdown("#### Ringkasan Pendaftaran")
                summary_col1, summary_col2 = st.columns(2)
                with summary_col1:
                    st.markdown(f"**Paket:** {batch.name}")
                    st.markdown(f"**Travel:** {company_name}")
                    st.markdown(f"**Email:** {company_email}")
                with summary_col2:
                    st.markdown(f"**PIC:** {pic_name}")
                    st.markdown(f"**Status:** Menunggu verifikasi")
                    st.markdown(f"**Tanggal:** {datetime.now().strftime('%d %B %Y')}")

                # Clear form state
                st.session_state.show_registration = False
                st.session_state.selected_batch = None

    if st.button("Kembali ke Daftar Harga"):
        st.session_state.show_registration = False
        st.session_state.selected_batch = None
        st.rerun()


def render_partner_list():
    """Render list of registered partners from session state / DB."""
    registrations = st.session_state.get("partner_registrations", [])

    if not registrations:
        return

    st.markdown("## Pendaftaran Anda")
    st.caption(f"{len(registrations)} pendaftaran tercatat")

    for idx, reg in enumerate(registrations):
        status = reg.get("registration_status", "pending")
        status_labels = {
            "pending": ("Menunggu Verifikasi", "warning"),
            "approved": ("Disetujui", "success"),
            "rejected": ("Ditolak", "error"),
            "suspended": ("Ditangguhkan", "error"),
        }
        label, level = status_labels.get(status, ("Tidak Diketahui", "info"))

        with st.expander(
            f"{reg.get('company_name', 'N/A')} - {reg.get('batch_name', '')} ({label})",
            expanded=False,
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Travel:** {reg.get('company_name', '-')}")
                st.markdown(f"**Email:** {reg.get('company_email', '-')}")
                st.markdown(f"**Telepon:** {reg.get('company_phone', '-')}")
            with col2:
                st.markdown(f"**PIC:** {reg.get('pic_name', '-')}")
                st.markdown(f"**Paket:** {reg.get('batch_name', '-')}")
                st.markdown(f"**Tanggal:** {reg.get('registered_at', '-')[:10]}")

            if level == "warning":
                st.warning(f"Status: {label}")
            elif level == "success":
                st.success(f"Status: {label}")
            elif level == "error":
                st.error(f"Status: {label}")
            else:
                st.info(f"Status: {label}")


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_partnership_page():
    """Main partnership page renderer."""

    # Initialize session state
    _init_partner_session_state()

    # Track page view
    try:
        from services.analytics import track_page
        track_page("partnership")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS)

    if not st.session_state.get("partnership_view_xp_awarded"):
        add_xp_safe(10, "Melihat program kemitraan")
        st.session_state.partnership_view_xp_awarded = True

    # Page header
    st.markdown("""
        <div class="page-hero">
            <h1><span aria-hidden="true">🤝</span> Program Kemitraan</h1>
            <div class="subtitle">Jadilah mitra travel umrah LABBAIK AI</div>
        </div>
    """, unsafe_allow_html=True)

    # Load pricing data
    data = load_pricing_data()

    if not data:
        st.error("Gagal memuat data pricing. Silakan coba lagi.")
        return

    # Check if showing registration form
    if st.session_state.get("show_registration"):
        render_registration_form(data)
        return

    # Hero Section
    render_hero_section(data["config"])

    # Partner Statistics Banner
    render_partner_stats_banner()

    # Current Batch Banner
    render_current_batch_banner(data)

    st.divider()

    # Pricing Cards
    render_pricing_cards(data)

    st.divider()

    # Comparison Table
    with st.expander("Lihat Perbandingan Lengkap", expanded=False):
        render_comparison_table(data)

    st.divider()

    # Partner Registrations List (user's own registrations)
    render_partner_list()

    # FAQ
    render_faq_section(data["faq"])

    st.divider()

    # Contact
    render_contact_section(data["contact"])

    # AI Tips
    st.markdown("---")
    if st.button("Tips Menjadi Mitra Sukses", key="partner_ai_tips"):
        with st.spinner("Menganalisis..."):
            tips = ai_complete(
                "Berikan 3 tips singkat untuk sukses menjadi mitra/agen travel umrah. "
                "Termasuk strategi pemasaran dan pelayanan jamaah. Bahasa Indonesia.",
                system_prompt="Kamu adalah business consultant untuk industri travel umrah.",
                max_tokens=300,
            )
            if tips:
                escaped = tips.replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f'''
                    <div class="ai-card" role="status" aria-live="polite">
                        <h4>Tips AI untuk Mitra</h4>
                        <p>{escaped}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")

    # Footer
    st.divider()
    st.caption("Labbaik Pioneer 2026 - Program kemitraan terbatas untuk travel umrah terpilih.")


# Export
__all__ = ["render_partnership_page"]
