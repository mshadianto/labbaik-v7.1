"""
LABBAIK AI - WhatsApp Broadcast
================================
Broadcast messages to leads and jamaah.
"""

import streamlit as st
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS


def init_session_state():
    """Initialize session state."""
    if "broadcast_view" not in st.session_state:
        st.session_state.broadcast_view = "list"


def render_broadcast_templates():
    """Render message templates."""
    st.markdown("### Template Pesan")

    try:
        from services.crm.config import get_broadcast_templates
        templates = get_broadcast_templates()

        for template in templates:
            with st.expander(f"📝 {template['name']}"):
                st.code(template['template'], language=None)

                if st.button(f"Gunakan Template", key=f"use_{template['code']}"):
                    st.session_state.broadcast_message = template['template']
                    st.session_state.broadcast_view = "create"
                    st.rerun()

    except Exception as e:
        logger.error(f"Failed to load templates: {e}")

    st.markdown("---")
    if st.button("🤖 Generate Template AI", use_container_width=True):
        with st.spinner("Membuat template..."):
            template = ai_complete(
                "Buatkan 1 template pesan WhatsApp broadcast untuk travel umrah. "
                "Tema: promo paket umrah. Gunakan placeholder {name} untuk nama penerima. "
                "Singkat, menarik, dan profesional. Bahasa Indonesia.",
                system_prompt="Kamu adalah copywriter untuk travel umrah.",
                max_tokens=300,
            )
            if template:
                st.markdown(f"""
                    <div class="ai-card">
                        <h4>🤖 Template Hasil AI</h4>
                        <p>{template}</p>
                    </div>
                """, unsafe_allow_html=True)
                if not st.session_state.get("crm_broadcast_ai_xp"):
                    st.session_state.crm_broadcast_ai_xp = True
                    add_xp_safe(10, "Generate template broadcast AI")
            else:
                st.info("AI tidak tersedia saat ini")


def render_create_broadcast():
    """Create new broadcast campaign."""
    st.markdown("### Buat Broadcast Baru")

    with st.form("broadcast_form"):
        campaign_name = st.text_input("Nama Campaign *", placeholder="Contoh: Promo Ramadan 2025")

        # Target selection
        st.markdown("**Target Penerima**")
        target_type = st.selectbox(
            "Target",
            options=["all_leads", "new_leads", "interested", "jamaah", "custom"],
            format_func=lambda x: {
                "all_leads": "Semua Lead",
                "new_leads": "Lead Baru (7 hari terakhir)",
                "interested": "Lead Tertarik",
                "jamaah": "Semua Jamaah",
                "custom": "Custom Filter"
            }.get(x, x)
        )

        if target_type == "custom":
            st.multiselect(
                "Status Lead",
                options=["new", "contacted", "interested", "negotiating"],
                default=["interested"]
            )

        # Message
        st.markdown("**Pesan**")

        default_message = st.session_state.get("broadcast_message", "")

        message = st.text_area(
            "Isi Pesan",
            value=default_message,
            height=200,
            help="Gunakan {name} untuk nama penerima"
        )

        st.caption("Variabel yang tersedia: {name}, {phone}")

        # Preview
        st.markdown("**Preview:**")
        preview = message.replace("{name}", "Ahmad").replace("{phone}", "081234567890")
        st.info(preview)

        # Schedule
        st.markdown("**Jadwal**")
        schedule_type = st.radio("Kirim", options=["Sekarang", "Jadwalkan"], horizontal=True)

        if schedule_type == "Jadwalkan":
            col1, col2 = st.columns(2)
            with col1:
                schedule_date = st.date_input("Tanggal", value=date.today())
            with col2:
                schedule_time = st.time_input("Waktu")

        submitted = st.form_submit_button("Buat Broadcast", type="primary", use_container_width=True)

        if submitted:
            if not campaign_name or not message:
                st.error("Nama campaign dan pesan wajib diisi!")
            else:
                try:
                    from services.crm import CRMRepository, Broadcast

                    repo = CRMRepository()

                    broadcast = Broadcast(
                        name=campaign_name,
                        message_template=message,
                        target_type=target_type,
                        status="draft"
                    )

                    broadcast_id = repo.create_broadcast(broadcast)

                    if broadcast_id:
                        st.success("Broadcast berhasil dibuat!")
                        add_xp_safe(10, "Membuat broadcast baru")

                        # Get recipient count
                        if target_type == "all_leads":
                            leads = repo.get_leads(limit=1000)
                            recipient_count = len(leads)
                        elif target_type == "new_leads":
                            from datetime import timedelta
                            leads = repo.get_leads(limit=1000)
                            recent = [l for l in leads if l.created_at and (datetime.now() - l.created_at).days <= 7]
                            recipient_count = len(recent)
                        elif target_type == "interested":
                            leads = repo.get_leads(status="interested", limit=1000)
                            recipient_count = len(leads)
                        elif target_type == "jamaah":
                            jamaah_list = repo.get_jamaah_list(limit=1000)
                            recipient_count = len(jamaah_list)
                        else:
                            recipient_count = 0

                        st.info(f"Broadcast akan dikirim ke {recipient_count} penerima")

                        st.session_state.broadcast_view = "list"
                        if "broadcast_message" in st.session_state:
                            del st.session_state.broadcast_message
                        st.rerun()
                    else:
                        st.error("Gagal membuat broadcast")

                except Exception as e:
                    logger.error(f"Failed to create broadcast: {e}")
                    st.error(f"Gagal membuat broadcast: {str(e)}")


def render_broadcast_list():
    """Render list of broadcasts."""
    st.markdown("### Riwayat Broadcast")

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        broadcasts = repo.get_broadcasts(limit=20)

        if broadcasts:
            for broadcast in broadcasts:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{broadcast.name}**")
                        st.caption(broadcast.message_template[:50] + "..." if len(broadcast.message_template) > 50 else broadcast.message_template)

                    with col2:
                        status_colors = {
                            "draft": "gray",
                            "scheduled": "blue",
                            "sending": "orange",
                            "completed": "green",
                            "failed": "red"
                        }
                        st.markdown(f":{status_colors.get(broadcast.status, 'gray')}[{broadcast.status.upper()}]")

                    with col3:
                        st.caption(f"Terkirim: {broadcast.sent_count}/{broadcast.total_recipients}")

                    with col4:
                        if broadcast.status == "draft":
                            if st.button("▶️ Kirim", key=f"send_{broadcast.id}"):
                                st.info("Fitur kirim akan segera tersedia")

                    st.divider()
        else:
            st.info("Belum ada riwayat broadcast")

    except Exception as e:
        logger.error(f"Failed to load broadcasts: {e}")
        st.info("Tidak dapat memuat riwayat broadcast")


def render_broadcast_stats():
    """Render broadcast statistics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Broadcast", 0)
    with col2:
        st.metric("Terkirim", 0)
    with col3:
        st.metric("Terbaca", 0)
    with col4:
        st.metric("Response Rate", "0%")


def render_quick_send():
    """Quick send message to single contact."""
    st.markdown("### Kirim Pesan Cepat")

    with st.form("quick_send"):
        phone = st.text_input("Nomor WhatsApp", placeholder="08xxxxxxxxxx")
        message = st.text_area("Pesan", placeholder="Tulis pesan...")

        if st.form_submit_button("Kirim via WhatsApp", type="primary"):
            if phone and message:
                # Format phone number
                wa_number = phone.replace("+", "").replace(" ", "").replace("-", "")
                if wa_number.startswith("0"):
                    wa_number = "62" + wa_number[1:]

                import urllib.parse
                encoded_message = urllib.parse.quote(message)
                wa_url = f"https://wa.me/{wa_number}?text={encoded_message}"

                st.markdown(f"[Buka WhatsApp]({wa_url})")
                st.success("Link WhatsApp siap!")
            else:
                st.error("Nomor dan pesan wajib diisi!")


def render_crm_broadcast_page():
    """Main broadcast page."""
    try:
        from services.analytics import track_page
        track_page("crm_broadcast")
    except Exception:
        pass

    init_session_state()

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    st.markdown("""
        <div class="page-hero">
            <h1>📢 WhatsApp Broadcast</h1>
            <div class="subtitle">Kirim pesan broadcast ke leads dan jamaah</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        pass
    with col2:
        if st.button("➕ Buat Broadcast", type="primary", use_container_width=True):
            st.session_state.broadcast_view = "create"
            st.rerun()

    st.markdown("---")

    # Stats
    render_broadcast_stats()

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Riwayat", "✏️ Buat Baru", "📝 Template", "📱 Kirim Cepat"])

    with tab1:
        render_broadcast_list()

    with tab2:
        render_create_broadcast()

    with tab3:
        render_broadcast_templates()

    with tab4:
        render_quick_send()


__all__ = ["render_crm_broadcast_page"]
