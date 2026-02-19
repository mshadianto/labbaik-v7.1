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
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SKELETON_CSS, render_skeleton

logger = logging.getLogger(__name__)

# =============================================================================
# PARTNER API INTEGRATION (lazy import with feature flag)
# =============================================================================
try:
    from services.partner_api import PartnerAPI, get_partner_api
    HAS_PARTNER_API = True
except ImportError:
    HAS_PARTNER_API = False


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

CRM_LEADS_CSS = """
/* CRM Leads page overrides */
:root {
    --hero-bg: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
    --hero-subtitle: #b0b0b0;
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

.partner-badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 700;
    background: #1e3a5f;
    color: #60a5fa;
    border: 1px solid #3b82f6;
    margin-left: 0.4rem;
    vertical-align: middle;
    letter-spacing: 0.02em;
}

.partner-stats-card {
    background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}

.partner-stats-card .stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #60a5fa;
    margin-bottom: 0.2rem;
}

.partner-stats-card .stat-label {
    font-size: 0.82rem;
    color: #94a3b8;
}

.partner-lead-row {
    padding: 0.75rem;
    margin: 0.5rem 0;
    background: linear-gradient(145deg, #0f172a 0%, #162032 100%);
    border-radius: 10px;
    border-left: 4px solid #3b82f6;
}

.partner-lead-row .partner-lead-name {
    font-weight: 600;
    color: #e2e8f0;
}

.partner-lead-row .partner-lead-detail {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-top: 0.15rem;
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


from ui.components.crm_helpers import format_rupiah, format_date


def _render_partner_badge(partner_name: str) -> str:
    """Render an HTML badge for partner-sourced leads.

    Args:
        partner_name: Name of the partner to display in the badge.

    Returns:
        HTML string for the partner badge, WCAG-compliant (#3b82f6 blue).
    """
    safe_name = escape_html(partner_name)
    return (
        '<span class="partner-badge" aria-label="Lead dari partner '
        + safe_name + '">'
        + safe_name
        + '</span>'
    )


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
    if "crm_partner_import_xp_awarded" not in st.session_state:
        st.session_state.crm_partner_import_xp_awarded = set()


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
            options=["Semua", "direct", "referral", "social", "ads", "website", "whatsapp", "partner"],
            format_func=lambda x: {
                "Semua": "Semua Sumber",
                "direct": "Langsung",
                "referral": "Referensi",
                "social": "Media Sosial",
                "ads": "Iklan",
                "website": "Website",
                "whatsapp": "WhatsApp",
                "partner": "Partner"
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
                        name_display = f"**{get_priority_emoji(lead.priority)} {lead.name}**"
                        if lead.source == "partner":
                            partner_label = lead.notes.split("[partner:")[1].split("]")[0] if lead.notes and "[partner:" in lead.notes else "Partner"
                            name_display += " " + _render_partner_badge(partner_label)
                            st.markdown(name_display, unsafe_allow_html=True)
                        else:
                            st.markdown(name_display)
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
                '<div class="ai-card" role="status" aria-live="polite">'
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
# PARTNER LEADS INTEGRATION
# =============================================================================

def _get_partner_bookings():
    """Fetch partner bookings from the partner API SQLite database.

    Returns a list of dicts with partner booking data suitable for
    display and CRM import, or an empty list on failure.
    """
    if not HAS_PARTNER_API:
        return []

    try:
        api = get_partner_api()
        results = []
        with api._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    b.id,
                    b.booking_code,
                    b.partner_id,
                    b.customer_name,
                    b.customer_email,
                    b.customer_phone,
                    b.num_pax,
                    b.total_price,
                    b.status,
                    b.created_at,
                    b.notes,
                    p.name as package_name,
                    p.departure_city,
                    u.name as partner_name
                FROM partner_bookings b
                LEFT JOIN partner_packages p ON b.package_id = p.id
                LEFT JOIN users u ON b.partner_id = u.id
                ORDER BY b.created_at DESC
                LIMIT 100
            """)
            rows = cursor.fetchall()
            for row in rows:
                results.append(dict(row))
        return results
    except Exception as e:
        logger.warning(f"Failed to fetch partner bookings: {e}")
        # Fallback: try without the users join (table may not exist in SQLite)
        try:
            api = get_partner_api()
            results = []
            with api._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        b.id,
                        b.booking_code,
                        b.partner_id,
                        b.customer_name,
                        b.customer_email,
                        b.customer_phone,
                        b.num_pax,
                        b.total_price,
                        b.status,
                        b.created_at,
                        b.notes,
                        p.name as package_name,
                        p.departure_city
                    FROM partner_bookings b
                    LEFT JOIN partner_packages p ON b.package_id = p.id
                    ORDER BY b.created_at DESC
                    LIMIT 100
                """)
                rows = cursor.fetchall()
                for row in rows:
                    d = dict(row)
                    d["partner_name"] = f"Partner #{d.get('partner_id', '?')}"
                    results.append(d)
            return results
        except Exception as e2:
            logger.error(f"Failed to fetch partner bookings (fallback): {e2}")
            return []


def _import_partner_lead_to_crm(booking: dict) -> bool:
    """Convert a partner booking into a CRM lead.

    Creates a new Lead with source='partner' and embeds the partner
    name in the notes for traceability.

    Args:
        booking: Dict with partner booking data.

    Returns:
        True if lead was created successfully, False otherwise.
    """
    try:
        from services.crm import CRMRepository, Lead

        repo = CRMRepository()

        partner_name = booking.get("partner_name", f"Partner #{booking.get('partner_id', '?')}")
        package_name = booking.get("package_name", "")
        departure_city = booking.get("departure_city", "")
        total_price = booking.get("total_price", 0)

        notes_parts = []
        if booking.get("booking_code"):
            notes_parts.append(f"Kode booking partner: {booking['booking_code']}")
        if booking.get("notes"):
            notes_parts.append(booking["notes"])
        notes_parts.append(f"[partner:{partner_name}]")
        if departure_city:
            notes_parts.append(f"Kota keberangkatan: {departure_city}")
        notes_text = " | ".join(notes_parts)

        lead = Lead(
            name=booking.get("customer_name", "").strip(),
            phone=booking.get("customer_phone", "").strip(),
            email=booking.get("customer_email") or None,
            whatsapp=booking.get("customer_phone", "").strip(),
            source="partner",
            status="new",
            priority="medium",
            interested_package=package_name if package_name else None,
            group_size=booking.get("num_pax", 1) or 1,
            budget_min=int(total_price * 0.8) if total_price else None,
            budget_max=int(total_price * 1.2) if total_price else None,
            notes=notes_text,
            next_followup_date=datetime.now() + timedelta(days=1)
        )

        lead_id = repo.create_lead(lead)
        return lead_id is not None

    except Exception as e:
        logger.error(f"Failed to import partner lead: {e}")
        return False


def render_partner_leads():
    """Render the Partner Leads integration tab.

    Shows partner-sourced bookings from the partner API, allows importing
    them as CRM leads, and displays partner lead statistics.
    """
    if not HAS_PARTNER_API:
        st.info("Modul Partner API belum tersedia. Pastikan services/partner_api terinstal.")
        return

    st.markdown("### Partner Leads")

    # --- Stats cards ---
    partner_bookings = _get_partner_bookings()

    # Also count how many CRM leads have source='partner'
    partner_crm_count = 0
    partner_won_count = 0
    top_partners = {}
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        partner_leads = repo.get_leads(source="partner", limit=500)
        partner_crm_count = len(partner_leads)
        for pl in partner_leads:
            if pl.status == "won":
                partner_won_count += 1
            # Extract partner name from notes
            if pl.notes and "[partner:" in pl.notes:
                try:
                    pname = pl.notes.split("[partner:")[1].split("]")[0]
                    top_partners[pname] = top_partners.get(pname, 0) + 1
                except (IndexError, ValueError):
                    pass
    except Exception:
        pass

    conversion_rate = (partner_won_count / partner_crm_count * 100) if partner_crm_count > 0 else 0.0

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            '<div class="partner-stats-card">'
            '<div class="stat-value">' + str(len(partner_bookings)) + '</div>'
            '<div class="stat-label">Lead dari Partner</div>'
            '</div>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '<div class="partner-stats-card">'
            '<div class="stat-value">' + str(partner_crm_count) + '</div>'
            '<div class="stat-label">Sudah Diimpor ke CRM</div>'
            '</div>',
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            '<div class="partner-stats-card">'
            '<div class="stat-value">' + f"{conversion_rate:.1f}%" + '</div>'
            '<div class="stat-label">Conversion Rate</div>'
            '</div>',
            unsafe_allow_html=True
        )
    with col4:
        top_partner_name = max(top_partners, key=top_partners.get) if top_partners else "-"
        top_partner_count = top_partners.get(top_partner_name, 0) if top_partners else 0
        display_top = escape_html(top_partner_name)
        if top_partner_count > 0:
            display_top += f" ({top_partner_count})"
        st.markdown(
            '<div class="partner-stats-card">'
            '<div class="stat-value" style="font-size:1.1rem;">' + display_top + '</div>'
            '<div class="stat-label">Top Partner</div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- Partner bookings list ---
    if not partner_bookings:
        st.info("Belum ada data booking dari partner. Partner dapat mengirim data melalui Partner API.")
        return

    st.markdown(f"Menampilkan **{len(partner_bookings)}** booking dari partner yang dapat diimpor sebagai lead CRM.")

    for booking in partner_bookings:
        booking_id = booking.get("id", "")
        customer_name = escape_html(booking.get("customer_name", "-"))
        customer_phone = escape_html(booking.get("customer_phone", "-"))
        customer_email = escape_html(booking.get("customer_email", "") or "")
        partner_name = escape_html(booking.get("partner_name", f"Partner #{booking.get('partner_id', '?')}"))
        package_name = escape_html(booking.get("package_name", "-"))
        total_price = booking.get("total_price", 0)
        num_pax = booking.get("num_pax", 1)
        booking_code = escape_html(booking.get("booking_code", "-"))
        booking_status = booking.get("status", "pending")

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                name_html = (
                    '<div class="partner-lead-row">'
                    '<div class="partner-lead-name">'
                    + customer_name + ' ' + _render_partner_badge(partner_name)
                    + '</div>'
                    '<div class="partner-lead-detail">'
                    + customer_phone
                    + (' | ' + customer_email if customer_email else '')
                    + '</div>'
                    '</div>'
                )
                st.markdown(name_html, unsafe_allow_html=True)

            with col2:
                st.caption(f"Paket: {package_name}")
                if total_price:
                    st.caption(f"Harga: {format_rupiah(total_price)}")
                st.caption(f"Jamaah: {num_pax}")

            with col3:
                st.caption(f"Kode: {booking_code}")
                status_color = {
                    "pending": "orange",
                    "confirmed": "green",
                    "completed": "green",
                    "cancelled": "red"
                }.get(booking_status, "gray")
                st.markdown(f":{status_color}[{booking_status.upper()}]")

            with col4:
                btn_key = f"import_partner_{booking_id}"
                if st.button(
                    "Import ke CRM",
                    key=btn_key,
                    use_container_width=True,
                    help="Konversi booking partner ini menjadi lead CRM"
                ):
                    if not booking.get("customer_name") or not booking.get("customer_phone"):
                        st.error("Data customer tidak lengkap (nama/telepon kosong).")
                    else:
                        success = _import_partner_lead_to_crm(booking)
                        if success:
                            st.success(f"Lead '{customer_name}' berhasil diimpor ke CRM!")

                            # Gamification: +10 XP per partner lead import
                            bid_str = str(booking_id)
                            if bid_str not in st.session_state.crm_partner_import_xp_awarded:
                                add_xp_safe(10, "Mengimpor lead partner ke CRM")
                                st.session_state.crm_partner_import_xp_awarded.add(bid_str)

                            st.rerun()
                        else:
                            st.error("Gagal mengimpor lead. Silakan coba lagi.")

            st.divider()


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
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SKELETON_CSS, CRM_LEADS_CSS)

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
        # View tabs (include Partner tab if partner API is available)
        if HAS_PARTNER_API:
            tab1, tab2, tab3 = st.tabs([
                "\U0001f4cb List View",
                "\U0001f4ca Pipeline",
                "\U0001f91d Partner Leads"
            ])
        else:
            tab1, tab2 = st.tabs(["\U0001f4cb List View", "\U0001f4ca Pipeline"])
            tab3 = None

        with tab1:
            render_lead_list()

        with tab2:
            render_pipeline_view()

        if tab3 is not None:
            with tab3:
                render_partner_leads()


__all__ = ["render_crm_leads_page"]
