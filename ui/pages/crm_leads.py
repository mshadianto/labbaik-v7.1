"""
================================================================================
LABBAIK AI - CRM Lead Management
================================================================================
UI for managing leads and sales pipeline with AI scoring & follow-up suggestions.
================================================================================
"""

import streamlit as st
from datetime import datetime, timedelta
import logging
import html

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

logger = logging.getLogger(__name__)


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

CRM_LEADS_CSS = """
/* CRM Leads page overrides */
:root {
    --hero-bg: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
    --hero-subtitle: #888;
}

.pipeline-card {
    padding: 10px;
    margin: 5px 0;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 8px;
    border-left: 4px solid #334155;
    transition: transform 0.15s;
}

.pipeline-card:hover {
    transform: translateX(2px);
}

.pipeline-card .lead-name {
    font-weight: bold;
    color: #e2e8f0;
    margin-bottom: 2px;
}

.pipeline-card .lead-phone {
    font-size: 0.85rem;
    color: #94a3b8;
}

.pipeline-card .lead-package {
    font-size: 0.82rem;
    color: #64748b;
    margin-top: 2px;
}

.lead-score-badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
}

.score-high {
    background: #1a3a1a;
    color: #4ade80;
}

.score-medium {
    background: #4a3a1a;
    color: #fbbf24;
}

.score-low {
    background: #4a1a1a;
    color: #f87171;
}

.followup-suggestion {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem;
    border-left: 3px solid #60a5fa;
    margin-top: 0.5rem;
}

.followup-suggestion .suggestion-title {
    color: #60a5fa;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

.followup-suggestion .suggestion-text {
    color: #cbd5e1;
    font-size: 0.9rem;
    line-height: 1.6;
}
"""


# =============================================================================
# HELPERS
# =============================================================================

def escape_html(text: str) -> str:
    """Escape HTML to prevent XSS."""
    if text is None:
        return ""
    return html.escape(str(text))


def format_rupiah(amount: int) -> str:
    """Format as Rupiah."""
    if amount is None:
        return "-"
    return f"Rp {amount:,.0f}".replace(",", ".")


def format_date(dt) -> str:
    """Format datetime."""
    if dt is None:
        return "-"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%d %b %Y")


def get_status_color(status: str) -> str:
    """Get status badge color."""
    colors = {
        "new": "blue",
        "contacted": "violet",
        "interested": "orange",
        "negotiating": "orange",
        "won": "green",
        "lost": "red",
    }
    return colors.get(status, "gray")


def get_priority_emoji(priority: str) -> str:
    """Get priority emoji."""
    emojis = {
        "urgent": "\U0001f534",
        "high": "\U0001f7e0",
        "medium": "\U0001f7e1",
        "low": "\U0001f7e2",
    }
    return emojis.get(priority, "\u26aa")


def init_session_state():
    """Initialize session state."""
    if "crm_view" not in st.session_state:
        st.session_state.crm_view = "list"
    if "crm_selected_lead" not in st.session_state:
        st.session_state.crm_selected_lead = None
    if "crm_filter_status" not in st.session_state:
        st.session_state.crm_filter_status = None
    if "crm_lead_add_xp_awarded" not in st.session_state:
        st.session_state.crm_lead_add_xp_awarded = False
    if "crm_lead_ai_xp_awarded" not in st.session_state:
        st.session_state.crm_lead_ai_xp_awarded = False


# =============================================================================
# STATS
# =============================================================================

def render_lead_stats():
    """Render lead statistics."""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        stats = repo.get_crm_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Leads", stats.total_leads)
        with col2:
            st.metric("Lead Baru", stats.new_leads)
        with col3:
            st.metric("Conversion Rate", f"{stats.conversion_rate:.1f}%")
        with col4:
            followups = repo.get_leads_for_followup(days_ahead=1)
            st.metric("Perlu Follow-up", len(followups))

    except Exception as e:
        logger.error(f"Failed to load stats: {e}")
        # Show demo stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Leads", 0)
        with col2:
            st.metric("Lead Baru", 0)
        with col3:
            st.metric("Conversion Rate", "0%")
        with col4:
            st.metric("Perlu Follow-up", 0)


# =============================================================================
# PIPELINE VIEW
# =============================================================================

def render_pipeline_view():
    """Render kanban-style pipeline view."""
    st.markdown("### Pipeline View")

    try:
        from services.crm import CRMRepository
        from services.crm.config import get_lead_statuses
        repo = CRMRepository()
        statuses = get_lead_statuses()

        # Create columns for each status
        cols = st.columns(len(statuses))

        for i, status in enumerate(statuses):
            with cols[i]:
                st.markdown(f"**{status['label']}**")
                leads = repo.get_leads(status=status['code'], limit=10)

                for lead in leads:
                    with st.container():
                        safe_name = escape_html(lead.name)
                        safe_phone = escape_html(lead.phone)
                        safe_package = escape_html(lead.interested_package) if lead.interested_package else 'Belum ada paket'
                        priority_emoji = get_priority_emoji(lead.priority)
                        border_color = status['color']
                        card_html = (
                            '<div class="pipeline-card" style="border-left-color: '
                            + border_color
                            + ';">'
                            + '<div class="lead-name">'
                            + priority_emoji + " " + safe_name
                            + '</div>'
                            + '<div class="lead-phone">'
                            + safe_phone
                            + '</div>'
                            + '<div class="lead-package">'
                            + safe_package
                            + '</div>'
                            + '</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)

                        if st.button("Detail", key=f"lead_{lead.id}", use_container_width=True):
                            st.session_state.crm_selected_lead = lead.id
                            st.session_state.crm_view = "detail"
                            st.rerun()

                if not leads:
                    st.caption("Tidak ada lead")

    except Exception as e:
        logger.error(f"Pipeline view error: {e}")
        st.info("Belum ada data lead")


# =============================================================================
# LEAD LIST
# =============================================================================

def render_lead_list():
    """Render lead list view."""
    st.markdown("### Daftar Lead")

    # Filters
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search = st.text_input("Cari nama/nomor", placeholder="Ketik untuk mencari...")

    with col2:
        status_filter = st.selectbox(
            "Status",
            options=["Semua", "new", "contacted", "interested", "negotiating", "won", "lost"],
            format_func=lambda x: {
                "Semua": "Semua Status",
                "new": "Baru",
                "contacted": "Sudah Dihubungi",
                "interested": "Tertarik",
                "negotiating": "Negosiasi",
                "won": "Deal",
                "lost": "Tidak Jadi"
            }.get(x, x)
        )

    with col3:
        source_filter = st.selectbox(
            "Sumber",
            options=["Semua", "direct", "referral", "social", "ads", "website", "whatsapp"],
            format_func=lambda x: {
                "Semua": "Semua Sumber",
                "direct": "Langsung",
                "referral": "Referensi",
                "social": "Media Sosial",
                "ads": "Iklan",
                "website": "Website",
                "whatsapp": "WhatsApp"
            }.get(x, x)
        )

    with col4:
        priority_filter = st.selectbox(
            "Prioritas",
            options=["Semua", "urgent", "high", "medium", "low"],
            format_func=lambda x: {
                "Semua": "Semua",
                "urgent": "\U0001f534 Urgent",
                "high": "\U0001f7e0 Tinggi",
                "medium": "\U0001f7e1 Sedang",
                "low": "\U0001f7e2 Rendah"
            }.get(x, x)
        )

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        leads = repo.get_leads(
            status=status_filter if status_filter != "Semua" else None,
            source=source_filter if source_filter != "Semua" else None,
            priority=priority_filter if priority_filter != "Semua" else None,
            search=search if search else None,
            limit=50
        )

        if leads:
            for lead in leads:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

                    with col1:
                        st.markdown(f"**{get_priority_emoji(lead.priority)} {lead.name}**")
                        st.caption(lead.phone)

                    with col2:
                        st.markdown(f":{get_status_color(lead.status)}[{lead.status.upper()}]")

                    with col3:
                        st.caption(lead.interested_package or "-")
                        if lead.budget_max:
                            st.caption(format_rupiah(lead.budget_max))

                    with col4:
                        if lead.next_followup_date:
                            followup_date = lead.next_followup_date
                            if isinstance(followup_date, str):
                                st.caption(f"Follow-up: {followup_date[:10]}")
                            else:
                                st.caption(f"Follow-up: {followup_date.strftime('%d %b')}")

                    with col5:
                        if st.button("\U0001f4dd", key=f"edit_{lead.id}", help="Detail"):
                            st.session_state.crm_selected_lead = lead.id
                            st.session_state.crm_view = "detail"
                            st.rerun()

                    st.divider()
        else:
            st.info("Belum ada lead. Klik 'Tambah Lead' untuk menambahkan lead baru.")

    except Exception as e:
        logger.error(f"Failed to load leads: {e}")
        st.info("Belum ada data lead atau database belum terhubung.")


# =============================================================================
# ADD LEAD FORM
# =============================================================================

def render_add_lead_form():
    """Render add lead form."""
    st.markdown("### Tambah Lead Baru")

    with st.form("add_lead_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Nama Lengkap *", placeholder="Nama calon jamaah")
            phone = st.text_input("No. Telepon *", placeholder="08xxxxxxxxxx")
            email = st.text_input("Email", placeholder="email@example.com")
            whatsapp = st.text_input("WhatsApp", placeholder="Sama dengan telepon jika kosong")

        with col2:
            source = st.selectbox(
                "Sumber Lead",
                options=["direct", "referral", "social", "ads", "website", "whatsapp", "event"],
                format_func=lambda x: {
                    "direct": "Langsung",
                    "referral": "Referensi",
                    "social": "Media Sosial",
                    "ads": "Iklan",
                    "website": "Website",
                    "whatsapp": "WhatsApp",
                    "event": "Event/Pameran"
                }.get(x, x)
            )

            priority = st.selectbox(
                "Prioritas",
                options=["medium", "low", "high", "urgent"],
                format_func=lambda x: {
                    "low": "\U0001f7e2 Rendah",
                    "medium": "\U0001f7e1 Sedang",
                    "high": "\U0001f7e0 Tinggi",
                    "urgent": "\U0001f534 Urgent"
                }.get(x, x)
            )

            interested_package = st.text_input("Paket yang Diminati", placeholder="Contoh: Paket 9 Hari Bintang 4")

            group_size = st.number_input("Jumlah Jamaah", min_value=1, max_value=50, value=1)

        st.markdown("**Budget**")
        col1, col2 = st.columns(2)
        with col1:
            budget_min = st.number_input("Budget Minimum", min_value=0, value=20000000, step=1000000)
        with col2:
            budget_max = st.number_input("Budget Maximum", min_value=0, value=35000000, step=1000000)

        preferred_month = st.text_input("Bulan Keberangkatan yang Diinginkan", placeholder="Contoh: Maret 2025")

        notes = st.text_area("Catatan", placeholder="Catatan tambahan tentang lead ini...")

        next_followup = st.date_input("Jadwal Follow-up Berikutnya", value=datetime.now().date() + timedelta(days=1))

        submitted = st.form_submit_button("Simpan Lead", type="primary", use_container_width=True)

        if submitted:
            if not name or not phone:
                st.error("Nama dan nomor telepon wajib diisi!")
            else:
                try:
                    from services.crm import CRMRepository, Lead
                    from services.crm.security import (
                        validate_phone, validate_email, check_rate_limit,
                        audit_log, AuditAction
                    )

                    # Rate limiting: max 10 leads per minute per session
                    session_key = st.session_state.get("session_id", "anonymous")
                    if not check_rate_limit(f"create_lead:{session_key}", max_requests=10, window_seconds=60):
                        st.error("Terlalu banyak permintaan. Silakan tunggu sebentar.")
                        st.stop()

                    repo = CRMRepository()

                    # Input validation
                    validated_phone = validate_phone(phone)
                    if not validated_phone:
                        st.error("Format nomor telepon tidak valid! Gunakan format 08xx atau +628xx")
                        st.stop()

                    validated_email = None
                    if email:
                        validated_email = validate_email(email)
                        if not validated_email:
                            st.error("Format email tidak valid!")
                            st.stop()

                    lead = Lead(
                        name=name.strip(),
                        phone=validated_phone,
                        email=validated_email,
                        whatsapp=whatsapp.strip() if whatsapp else validated_phone,
                        source=source,
                        priority=priority,
                        interested_package=interested_package if interested_package else None,
                        group_size=group_size,
                        budget_min=budget_min,
                        budget_max=budget_max,
                        preferred_month=preferred_month if preferred_month else None,
                        notes=notes if notes else None,
                        next_followup_date=datetime.combine(next_followup, datetime.min.time())
                    )

                    lead_id = repo.create_lead(lead)
                    if lead_id:
                        # Audit log
                        user = st.session_state.get("user", {})
                        audit_log(
                            action=AuditAction.CREATE,
                            entity_type="lead",
                            entity_id=lead_id,
                            user_id=user.get("id"),
                            user_email=user.get("email"),
                            details={"name": name.strip(), "phone": validated_phone, "source": source}
                        )

                        # Gamification: +20 XP for first lead added
                        if not st.session_state.crm_lead_add_xp_awarded:
                            add_xp_safe(20, "Menambahkan lead pertama di CRM")
                            st.session_state.crm_lead_add_xp_awarded = True

                        st.success("Lead berhasil ditambahkan!")
                        st.session_state.crm_view = "list"
                        st.rerun()
                    else:
                        st.error("Gagal menyimpan lead. Silakan coba lagi.")

                except Exception as e:
                    logger.error(f"Failed to create lead: {e}")
                    st.error(f"Gagal menyimpan lead: {str(e)}")


# =============================================================================
# AI LEAD SCORING & FOLLOW-UP SUGGESTIONS
# =============================================================================

def render_ai_lead_analysis(lead):
    """Render AI-powered lead scoring and follow-up suggestions."""
    st.markdown("### \U0001f916 Analisis AI")

    if st.button("\U0001f4a1 Analisis Lead dengan AI", use_container_width=True, key="ai_analyze_lead"):
        safe_name = escape_html(lead.name)
        package_info = lead.interested_package or "Belum ditentukan"
        budget_info = ""
        if lead.budget_min or lead.budget_max:
            budget_info = f"{format_rupiah(lead.budget_min or 0)} - {format_rupiah(lead.budget_max or 0)}"
        else:
            budget_info = "Belum ditentukan"
        preferred_month_info = lead.preferred_month or "Belum ditentukan"
        group_size_info = str(lead.group_size) if lead.group_size else "1"
        source_info = lead.source or "Tidak diketahui"
        priority_info = lead.priority or "medium"
        status_info = lead.status or "new"
        notes_info = lead.notes or "Tidak ada catatan"

        prompt = (
            "Kamu adalah konsultan CRM travel umrah berpengalaman. "
            "Analisis lead berikut dan berikan:\n"
            "1. SKOR LEAD (1-100) berdasarkan potensi konversi\n"
            "2. ALASAN skor tersebut (2-3 poin singkat)\n"
            "3. REKOMENDASI FOLLOW-UP: strategi dan pesan yang tepat\n"
            "4. WAKTU TERBAIK untuk menghubungi\n\n"
            "Data Lead:\n"
            "- Nama: " + safe_name + "\n"
            "- Status: " + status_info + "\n"
            "- Prioritas: " + priority_info + "\n"
            "- Sumber: " + source_info + "\n"
            "- Paket Diminati: " + package_info + "\n"
            "- Budget: " + budget_info + "\n"
            "- Bulan Preferensi: " + preferred_month_info + "\n"
            "- Jumlah Jamaah: " + group_size_info + "\n"
            "- Catatan: " + notes_info + "\n\n"
            "Jawab dalam Bahasa Indonesia, singkat dan actionable."
        )

        with st.spinner("Menganalisis lead..."):
            result = ai_complete(
                prompt=prompt,
                system_prompt="Kamu adalah AI CRM assistant untuk travel umrah. Berikan analisis singkat, praktis, dan actionable.",
                max_tokens=600
            )

        if result:
            ai_html = (
                '<div class="ai-card">'
                '<h4>\U0001f4ca Hasil Analisis AI</h4>'
                '<p>' + escape_html(result) + '</p>'
                '</div>'
            )
            st.markdown(ai_html, unsafe_allow_html=True)

            # Gamification: +15 XP for first AI analysis
            if not st.session_state.crm_lead_ai_xp_awarded:
                add_xp_safe(15, "Analisis AI lead CRM")
                st.session_state.crm_lead_ai_xp_awarded = True
        else:
            st.warning("Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")


# =============================================================================
# LEAD DETAIL
# =============================================================================

def render_lead_detail(lead_id: str):
    """Render lead detail view."""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        lead = repo.get_lead(lead_id)

        if not lead:
            st.error("Lead tidak ditemukan")
            return

        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## {get_priority_emoji(lead.priority)} {lead.name}")
            st.caption(f"\U0001f4de {lead.phone} | \U0001f4e7 {lead.email or '-'}")

        with col2:
            if st.button("\u2190 Kembali"):
                st.session_state.crm_view = "list"
                st.session_state.crm_selected_lead = None
                st.rerun()

        # Status update
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            new_status = st.selectbox(
                "Status",
                options=["new", "contacted", "interested", "negotiating", "won", "lost"],
                index=["new", "contacted", "interested", "negotiating", "won", "lost"].index(lead.status),
                format_func=lambda x: {
                    "new": "Baru",
                    "contacted": "Sudah Dihubungi",
                    "interested": "Tertarik",
                    "negotiating": "Negosiasi",
                    "won": "Deal",
                    "lost": "Tidak Jadi"
                }.get(x, x)
            )

            if new_status != lead.status:
                if st.button("Update Status"):
                    repo.update_lead_status(lead_id, new_status)
                    st.success("Status diupdate!")
                    st.rerun()

        with col2:
            st.markdown("**Paket Diminati**")
            st.write(lead.interested_package or "-")

        with col3:
            st.markdown("**Budget**")
            if lead.budget_min or lead.budget_max:
                st.write(f"{format_rupiah(lead.budget_min or 0)} - {format_rupiah(lead.budget_max or 0)}")
            else:
                st.write("-")

        # Details
        st.markdown("### Detail")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Sumber:** {lead.source}")
            st.markdown(f"**Jumlah Jamaah:** {lead.group_size}")
            st.markdown(f"**Bulan Preferensi:** {lead.preferred_month or '-'}")

        with col2:
            st.markdown(f"**Dibuat:** {format_date(lead.created_at)}")
            st.markdown(f"**Kontak Terakhir:** {format_date(lead.last_contact_date)}")
            st.markdown(f"**Follow-up:** {format_date(lead.next_followup_date)}")

        if lead.notes:
            st.markdown("**Catatan:**")
            st.write(lead.notes)

        # AI Analysis section
        render_ai_lead_analysis(lead)

        # Activities
        st.markdown("### Riwayat Aktivitas")

        # Add activity form
        with st.expander("Tambah Aktivitas"):
            with st.form("add_activity"):
                activity_type = st.selectbox(
                    "Tipe",
                    options=["call", "whatsapp", "email", "meeting", "note"],
                    format_func=lambda x: {
                        "call": "\U0001f4de Telepon",
                        "whatsapp": "\U0001f4ac WhatsApp",
                        "email": "\U0001f4e7 Email",
                        "meeting": "\U0001f91d Meeting",
                        "note": "\U0001f4dd Catatan"
                    }.get(x, x)
                )

                description = st.text_area("Deskripsi", placeholder="Apa yang terjadi?")

                outcome = st.selectbox(
                    "Hasil",
                    options=["", "answered", "no_answer", "callback", "interested", "not_interested", "need_time"],
                    format_func=lambda x: {
                        "": "- Pilih -",
                        "answered": "Dijawab",
                        "no_answer": "Tidak Diangkat",
                        "callback": "Minta Dihubungi Lagi",
                        "interested": "Tertarik",
                        "not_interested": "Tidak Tertarik",
                        "need_time": "Butuh Waktu"
                    }.get(x, x)
                )

                if st.form_submit_button("Simpan Aktivitas", type="primary"):
                    from services.crm import LeadActivity
                    activity = LeadActivity(
                        lead_id=lead_id,
                        activity_type=activity_type,
                        description=description,
                        outcome=outcome if outcome else None
                    )
                    repo.create_activity(activity)
                    st.success("Aktivitas ditambahkan!")
                    st.rerun()

        # Activity history
        activities = repo.get_lead_activities(lead_id)
        if activities:
            for act in activities:
                icon = {
                    "call": "\U0001f4de",
                    "whatsapp": "\U0001f4ac",
                    "email": "\U0001f4e7",
                    "meeting": "\U0001f91d",
                    "note": "\U0001f4dd"
                }.get(act.activity_type, "\U0001f4cc")

                with st.container():
                    st.markdown(f"**{icon} {act.activity_type.title()}** - {format_date(act.created_at)}")
                    st.write(act.description or "-")
                    if act.outcome:
                        st.caption(f"Hasil: {act.outcome}")
                    st.divider()
        else:
            st.info("Belum ada riwayat aktivitas")

        # Actions
        st.markdown("### Aksi")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("\U0001f4cb Buat Quote", use_container_width=True):
                st.session_state.quote_lead_id = lead_id
                st.session_state.current_page = "quotes"
                st.rerun()

        with col2:
            if st.button("\U0001f4c5 Buat Booking", use_container_width=True):
                st.session_state.booking_lead_id = lead_id
                st.session_state.current_page = "bookings"
                st.rerun()

        with col3:
            if lead.whatsapp or lead.phone:
                wa_number = (lead.whatsapp or lead.phone).replace("+", "").replace(" ", "")
                if wa_number.startswith("0"):
                    wa_number = "62" + wa_number[1:]
                st.link_button("\U0001f4ac WhatsApp", f"https://wa.me/{wa_number}", use_container_width=True)

    except Exception as e:
        logger.error(f"Failed to load lead detail: {e}")
        st.error("Gagal memuat detail lead")


# =============================================================================
# MAIN RENDER
# =============================================================================

def render_crm_leads_page():
    """Main CRM leads page."""
    try:
        from services.analytics import track_page
        track_page("crm_leads")
    except Exception:
        pass

    init_session_state()

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, CRM_LEADS_CSS)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# \U0001f465 CRM - Manajemen Lead")
    with col2:
        if st.button("\u2795 Tambah Lead", type="primary", use_container_width=True):
            st.session_state.crm_view = "add"
            st.rerun()

    st.markdown("---")

    # Stats
    render_lead_stats()

    st.markdown("---")

    # View switcher
    if st.session_state.crm_view == "add":
        render_add_lead_form()
    elif st.session_state.crm_view == "detail" and st.session_state.crm_selected_lead:
        render_lead_detail(st.session_state.crm_selected_lead)
    else:
        # View tabs
        tab1, tab2 = st.tabs(["\U0001f4cb List View", "\U0001f4ca Pipeline"])

        with tab1:
            render_lead_list()

        with tab2:
            render_pipeline_view()


__all__ = ["render_crm_leads_page"]
