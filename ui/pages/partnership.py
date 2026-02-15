"""
LABBAIK AI - Partnership Portal
================================
Halaman khusus untuk program kemitraan travel umrah.
Menampilkan tier pricing dari config/pricing.yaml.
"""

import streamlit as st
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

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
        <p style="font-size: 1.2rem; color: #666; max-width: 600px; margin: 0 auto;">
            {config.get('program_description', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)


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
            st.markdown(f"<h2 style='color: #4CAF50; margin: 0.5rem 0;'>GRATIS</h2>", unsafe_allow_html=True)
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

        # Slot info
        if batch.max_partners:
            remaining = batch.max_partners - partner_count
            if remaining > 0:
                st.warning(f"Sisa {remaining} slot dari {batch.max_partners}")
            else:
                st.error("Slot penuh!")

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

    # Get partner counts from database (placeholder for now)
    partner_counts = {}  # TODO: Load from database

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
            "💰 Setup Fee",
            "⭐ Status Member",
            "⏱️ Durasi Status",
            "📊 Komisi Bagi Hasil",
            "🔒 Komisi Terlindungi",
            "🛠️ Tipe Onboarding",
            "👥 Kuota Partner",
            "📞 Support Level",
            "🎓 Training",
            "🚀 Akses Fitur Beta",
        ]
    }

    for idx, b in enumerate(batches):
        comparison_data[b.name] = [
            "✅ GRATIS" if b.setup_fee == 0 else b.setup_fee_display,
            b.status,
            "🌟 Selamanya" if not b.status_duration_months else f"{b.status_duration_months} bulan",
            f"🔒 {b.commission_display}" if b.commission_locked else b.commission_display,
            "✅ Ya, Locked!" if b.commission_locked else "❌ Tidak",
            b.setup_type_display,
            f"{b.max_partners} partner" if b.max_partners else "Unlimited",
            "Priority 24/7" if b.setup_type == "white_glove" else ("Jam Kerja" if idx < 2 else "Email"),
            "1-on-1 Konsultasi" if b.setup_type == "white_glove" else ("2 Sesi Online" if idx == 1 else "Video Tutorial"),
            "✅ Ya" if b.setup_type == "white_glove" else "❌ Tidak",
        ]

    df = pd.DataFrame(comparison_data)

    # Display with styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fitur": st.column_config.TextColumn("Fitur", width="medium"),
            batches[0].name: st.column_config.TextColumn(f"⭐ {batches[0].name}", width="medium"),
        }
    )

    # Legend
    st.info("✅ = Tersedia | ❌ = Tidak Tersedia | 🔒 = Terlindungi Selamanya | 🌟 = Lifetime")


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
            <div style="font-size: 2rem;">📱</div>
            <div style="color: white; font-weight: 600; margin: 0.5rem 0;">WhatsApp</div>
            <div style="color: rgba(255,255,255,0.9);">""" + wa_display + """</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Chat Sekarang", wa_link, use_container_width=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #EA4335, #C5221F); padding: 1.5rem; border-radius: 12px; text-align: center;">
            <div style="font-size: 2rem;">📧</div>
            <div style="color: white; font-weight: 600; margin: 0.5rem 0;">Email</div>
            <div style="color: rgba(255,255,255,0.9);">""" + email + """</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Kirim Email", f"mailto:{email}", use_container_width=True)

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #006BFF, #0052CC); padding: 1.5rem; border-radius: 12px; text-align: center;">
            <div style="font-size: 2rem;">📅</div>
            <div style="color: white; font-weight: 600; margin: 0.5rem 0;">Meeting</div>
            <div style="color: rgba(255,255,255,0.9);">Pilih waktu</div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Jadwalkan", calendly, use_container_width=True)

    st.caption("Respon cepat dalam waktu 1x24 jam kerja")


def render_registration_form(data: dict):
    """Render partner registration form."""
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
            if not all([company_name, company_email, company_phone, pic_name, pic_phone]):
                st.error("Mohon lengkapi semua field yang wajib (*)")
            elif not agree_tos:
                st.error("Anda harus menyetujui Syarat & Ketentuan")
            else:
                # TODO: Save to database
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
                }

                st.success("Pendaftaran berhasil dikirim! Tim kami akan menghubungi Anda dalam 1x24 jam.")
                st.json(registration_data)

                # Clear state
                st.session_state.show_registration = False
                st.session_state.selected_batch = None

    if st.button("Kembali ke Daftar Harga"):
        st.session_state.show_registration = False
        st.session_state.selected_batch = None
        st.rerun()


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_partnership_page():
    """Main partnership page renderer."""

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
            <h1>🤝 Program Kemitraan</h1>
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

    # FAQ
    render_faq_section(data["faq"])

    st.divider()

    # Contact
    render_contact_section(data["contact"])

    # AI Tips
    st.markdown("---")
    if st.button("🤖 Tips Menjadi Mitra Sukses", key="partner_ai_tips"):
        with st.spinner("Menganalisis..."):
            tips = ai_complete(
                "Berikan 3 tips singkat untuk sukses menjadi mitra/agen travel umrah. "
                "Termasuk strategi pemasaran dan pelayanan jamaah. Bahasa Indonesia.",
                system_prompt="Kamu adalah business consultant untuk industri travel umrah.",
                max_tokens=300,
            )
            if tips:
                st.markdown(f'''
                    <div class="ai-card">
                        <h4>🤖 Tips AI untuk Mitra</h4>
                        <p>{tips}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")

    # Footer
    st.divider()
    st.caption("Labbaik Pioneer 2026 - Program kemitraan terbatas untuk travel umrah terpilih.")


# Export
__all__ = ["render_partnership_page"]
