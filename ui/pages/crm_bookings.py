"""
================================================================================
LABBAIK AI - Booking & Payment Tracker
================================================================================
Lokasi: ui/pages/crm_bookings.py
Fitur: Manajemen booking dan pelacakan pembayaran
       - Daftar booking dengan filter status & pembayaran
       - Detail booking dengan update status
       - Riwayat pembayaran & konfirmasi
       - Kalkulator cicilan
       - AI booking insights & trend analysis
       - Gamification (XP rewards)
================================================================================
"""

import streamlit as st
from datetime import datetime, date, timedelta
import logging
import re

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import (
    inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

BOOKINGS_CSS = """
/* Hero overrides for bookings page */
.bookings-hero {
    --hero-bg: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
    --hero-subtitle: #94a3b8;
}

/* Booking stat cards */
.booking-stat-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    text-align: center;
    border: 1px solid #334155;
    transition: border-color 0.2s, transform 0.2s;
}

.booking-stat-card:hover {
    border-color: #d4af37;
    transform: translateY(-2px);
}

.booking-stat-card .stat-icon {
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
}

.booking-stat-card .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0.25rem 0;
}

.booking-stat-card .stat-label {
    color: #94a3b8;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Booking list card */
.booking-row {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid #1e293b;
    transition: border-color 0.2s;
}

.booking-row:hover {
    border-color: #334155;
}

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.status-draft { background: #374151; color: #9ca3af; }
.status-confirmed { background: #1e3a5f; color: #60a5fa; }
.status-processing { background: #4a3a1a; color: #fbbf24; }
.status-completed { background: #1a3a1a; color: #4ade80; }
.status-cancelled { background: #4a1a1a; color: #f87171; }

.payment-pending { background: #4a1a1a; color: #f87171; }
.payment-dp_paid { background: #4a3a1a; color: #fbbf24; }
.payment-partial { background: #1e3a5f; color: #60a5fa; }
.payment-paid { background: #1a3a1a; color: #4ade80; }
.payment-refunded { background: #374151; color: #9ca3af; }

/* Payment progress bar */
.payment-progress-track {
    width: 100%;
    height: 8px;
    background: #1e293b;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 0.5rem;
}

.payment-progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
    background: linear-gradient(90deg, #d4af37, #f5d76e);
}

/* Detail card */
.detail-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    border: 1px solid #334155;
    margin-bottom: 0.75rem;
}

.detail-card .detail-label {
    color: #94a3b8;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 0.15rem;
}

.detail-card .detail-value {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 500;
}

/* Payment history row */
.payment-row {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    border-left: 3px solid #334155;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.payment-row.confirmed { border-left-color: #4ade80; }
.payment-row.pending { border-left-color: #fbbf24; }
.payment-row.failed { border-left-color: #f87171; }

/* Reminder cards */
.reminder-overdue {
    background: linear-gradient(145deg, #2a1a1a 0%, #3a1e1e 100%);
    border: 1px solid #f87171;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    color: #fca5a5;
}

.reminder-pending {
    background: linear-gradient(145deg, #2a2a1a 0%, #3a3a1e 100%);
    border: 1px solid #fbbf24;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    color: #fde68a;
}

/* Installment schedule table */
.schedule-header {
    color: #94a3b8;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}
"""


# =============================================================================
# HELPERS
# =============================================================================

from ui.components.crm_helpers import format_rupiah, format_date


def get_status_color(status: str) -> str:
    """Get status badge color."""
    colors = {
        "draft": "gray",
        "confirmed": "blue",
        "processing": "orange",
        "completed": "green",
        "cancelled": "red",
    }
    return colors.get(status, "gray")


def get_payment_status_color(status: str) -> str:
    """Get payment status color."""
    colors = {
        "pending": "red",
        "dp_paid": "orange",
        "partial": "blue",
        "paid": "green",
        "refunded": "gray",
    }
    return colors.get(status, "gray")


def _markdown_to_html_simple(text: str) -> str:
    """Simple markdown to HTML conversion for display in custom styled div."""
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br/>")
            continue
        # Bold
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        # Bullet points
        if line.startswith("- ") or line.startswith("* "):
            line = "&bull; " + line[2:]
        # Numbered lists
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            num = match.group(1)
            rest = line[match.end():]
            line = "<strong>" + num + ".</strong> " + rest
        html_lines.append("<div style='margin-bottom:0.3rem;'>" + line + "</div>")
    return "\n".join(html_lines)


# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    """Initialize session state."""
    if "booking_view" not in st.session_state:
        st.session_state.booking_view = "list"
    if "selected_booking" not in st.session_state:
        st.session_state.selected_booking = None
    if "crm_booking_manage_xp_awarded" not in st.session_state:
        st.session_state.crm_booking_manage_xp_awarded = False
    if "crm_booking_ai_xp_awarded" not in st.session_state:
        st.session_state.crm_booking_ai_xp_awarded = False


# =============================================================================
# UI: HERO
# =============================================================================

def render_hero():
    """Render hero banner."""
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, BOOKINGS_CSS)

    hero_html = (
        '<div class="page-hero bookings-hero">'
        '<h1>Booking &amp; Pembayaran</h1>'
        '<p class="subtitle">Kelola booking umrah dan lacak pembayaran jamaah</p>'
        '<p class="bismillah">Bismillahirrahmanirrahim</p>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)


# =============================================================================
# UI: STATS
# =============================================================================

def render_booking_stats():
    """Render booking statistics."""
    total_bookings = 0
    total_revenue_val = 0
    total_paid_val = 0
    total_pending_val = 0

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        stats = repo.get_crm_stats()
        total_bookings = stats.total_bookings
        total_revenue_val = stats.total_revenue or 0
        total_paid_val = stats.total_paid or 0
        total_pending_val = stats.total_pending or 0
    except Exception as e:
        logger.error(f"Failed to load stats: {e}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        card1 = (
            '<div class="booking-stat-card">'
            '<div class="stat-icon">&#128203;</div>'
            '<div class="stat-value">' + str(total_bookings) + '</div>'
            '<div class="stat-label">Total Booking</div>'
            '</div>'
        )
        st.markdown(card1, unsafe_allow_html=True)

    with col2:
        card2 = (
            '<div class="booking-stat-card">'
            '<div class="stat-icon">&#128176;</div>'
            '<div class="stat-value">' + format_rupiah(total_revenue_val) + '</div>'
            '<div class="stat-label">Total Revenue</div>'
            '</div>'
        )
        st.markdown(card2, unsafe_allow_html=True)

    with col3:
        card3 = (
            '<div class="booking-stat-card">'
            '<div class="stat-icon">&#9989;</div>'
            '<div class="stat-value">' + format_rupiah(total_paid_val) + '</div>'
            '<div class="stat-label">Sudah Dibayar</div>'
            '</div>'
        )
        st.markdown(card3, unsafe_allow_html=True)

    with col4:
        card4 = (
            '<div class="booking-stat-card">'
            '<div class="stat-icon">&#9203;</div>'
            '<div class="stat-value">' + format_rupiah(total_pending_val) + '</div>'
            '<div class="stat-label">Belum Dibayar</div>'
            '</div>'
        )
        st.markdown(card4, unsafe_allow_html=True)


# =============================================================================
# UI: BOOKING LIST
# =============================================================================

def render_booking_list():
    """Render booking list."""
    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Status Booking",
            options=["Semua", "draft", "confirmed", "processing", "completed", "cancelled"],
            format_func=lambda x: {
                "Semua": "Semua",
                "draft": "Draft",
                "confirmed": "Dikonfirmasi",
                "processing": "Diproses",
                "completed": "Selesai",
                "cancelled": "Dibatalkan"
            }.get(x, x)
        )

    with col2:
        payment_filter = st.selectbox(
            "Status Pembayaran",
            options=["Semua", "pending", "dp_paid", "partial", "paid"],
            format_func=lambda x: {
                "Semua": "Semua",
                "pending": "Belum Bayar",
                "dp_paid": "DP Lunas",
                "partial": "Cicilan",
                "paid": "Lunas"
            }.get(x, x)
        )

    with col3:
        departure_month = st.date_input("Keberangkatan", value=None)

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        bookings = repo.get_bookings(
            status=status_filter if status_filter != "Semua" else None,
            payment_status=payment_filter if payment_filter != "Semua" else None,
            limit=50
        )

        if bookings:
            # Award XP for managing bookings (first time)
            if not st.session_state.get("crm_booking_manage_xp_awarded", False):
                st.session_state.crm_booking_manage_xp_awarded = True
                add_xp_safe(20, "Mengelola booking umrah")

            for booking in bookings:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

                    with col1:
                        st.markdown(f"**{booking.booking_code}**")
                        st.caption(booking.package_name)

                    with col2:
                        st.markdown(f":{get_status_color(booking.status)}[{booking.status.upper()}]")
                        st.caption(f"Berangkat: {format_date(booking.departure_date)}")

                    with col3:
                        st.markdown(f":{get_payment_status_color(booking.payment_status)}[{booking.payment_status.upper()}]")
                        progress = (booking.amount_paid / booking.total_price * 100) if booking.total_price > 0 else 0
                        st.progress(progress / 100, text=f"{progress:.0f}%")

                    with col4:
                        st.caption("Dibayar:")
                        st.markdown(f"**{format_rupiah(booking.amount_paid)}** / {format_rupiah(booking.total_price)}")

                    with col5:
                        if st.button("Detail", key=f"booking_{booking.id}", help="Lihat detail booking"):
                            st.session_state.selected_booking = booking.id
                            st.session_state.booking_view = "detail"
                            st.rerun()

                    st.divider()
        else:
            st.info("Belum ada booking. Klik 'Tambah Booking' untuk membuat booking baru.")

    except Exception as e:
        logger.error(f"Failed to load bookings: {e}")
        st.info("Belum ada data booking atau database belum terhubung.")


# =============================================================================
# UI: ADD BOOKING FORM
# =============================================================================

def render_add_booking_form():
    """Render add booking form."""
    st.markdown("### Tambah Booking Baru")

    with st.form("add_booking_form"):
        # Package info
        st.markdown("**Informasi Paket**")
        col1, col2 = st.columns(2)

        with col1:
            package_name = st.text_input("Nama Paket *", placeholder="Contoh: Paket 9 Hari Bintang 4")
            package_type = st.selectbox(
                "Tipe Paket",
                options=["regular", "plus", "vip"],
                format_func=lambda x: {"regular": "Regular", "plus": "Plus", "vip": "VIP"}.get(x, x)
            )
            duration_days = st.number_input("Durasi (hari)", min_value=5, max_value=30, value=9)

        with col2:
            departure_date = st.date_input("Tanggal Berangkat", value=date.today() + timedelta(days=30))
            return_date = st.date_input("Tanggal Pulang", value=date.today() + timedelta(days=39))
            room_type = st.selectbox(
                "Tipe Kamar",
                options=["quad", "triple", "double", "single"],
                format_func=lambda x: {
                    "quad": "Quad (4 orang)",
                    "triple": "Triple (3 orang)",
                    "double": "Double (2 orang)",
                    "single": "Single"
                }.get(x, x)
            )

        st.markdown("---")
        st.markdown("**Jamaah**")
        col1, col2 = st.columns(2)

        with col1:
            jamaah_name = st.text_input("Nama Jamaah *", placeholder="Nama lengkap")
            jamaah_phone = st.text_input("No. Telepon *", placeholder="08xxxxxxxxxx")

        with col2:
            group_code = st.text_input("Kode Grup", placeholder="Opsional")
            roommate_preference = st.text_input("Preferensi Teman Sekamar", placeholder="Opsional")

        st.markdown("---")
        st.markdown("**Harga**")
        col1, col2, col3 = st.columns(3)

        with col1:
            package_price = st.number_input("Harga Paket", min_value=0, value=25000000, step=500000)

        with col2:
            discount_amount = st.number_input("Diskon", min_value=0, value=0, step=100000)

        with col3:
            total_price = package_price - discount_amount
            st.metric("Total Harga", format_rupiah(total_price))

        discount_reason = st.text_input("Alasan Diskon", placeholder="Opsional")

        st.markdown("---")
        st.markdown("**Catatan**")
        notes = st.text_area("Catatan", placeholder="Catatan untuk jamaah...")
        internal_notes = st.text_area("Catatan Internal", placeholder="Catatan internal (tidak terlihat jamaah)...")

        submitted = st.form_submit_button("Simpan Booking", type="primary", use_container_width=True)

        if submitted:
            if not package_name or not jamaah_name or not jamaah_phone:
                st.error("Nama paket, nama jamaah, dan nomor telepon wajib diisi!")
            else:
                try:
                    from services.crm import CRMRepository, Booking, Jamaah
                    from services.crm.security import (
                        validate_phone, check_rate_limit, audit_log, AuditAction
                    )

                    # Rate limiting: max 5 bookings per minute per session
                    session_key = st.session_state.get("session_id", "anonymous")
                    if not check_rate_limit(f"create_booking:{session_key}", max_requests=5, window_seconds=60):
                        st.error("Terlalu banyak permintaan. Silakan tunggu sebentar.")
                        st.stop()

                    repo = CRMRepository()

                    # Input validation
                    validated_phone = validate_phone(jamaah_phone)
                    if not validated_phone:
                        st.error("Format nomor telepon tidak valid! Gunakan format 08xx atau +628xx")
                        st.stop()

                    # Check or create jamaah
                    jamaah = repo.find_jamaah_by_phone(validated_phone)
                    if not jamaah:
                        jamaah = Jamaah(full_name=jamaah_name.strip(), phone=validated_phone)
                        jamaah_id = repo.create_jamaah(jamaah)
                    else:
                        jamaah_id = jamaah.id

                    # Create booking
                    booking = Booking(
                        jamaah_id=jamaah_id,
                        package_name=package_name,
                        package_type=package_type,
                        departure_date=departure_date,
                        return_date=return_date,
                        duration_days=duration_days,
                        package_price=package_price,
                        discount_amount=discount_amount,
                        discount_reason=discount_reason if discount_reason else None,
                        total_price=total_price,
                        room_type=room_type,
                        group_code=group_code if group_code else None,
                        roommate_preference=roommate_preference if roommate_preference else None,
                        notes=notes if notes else None,
                        internal_notes=internal_notes if internal_notes else None,
                        status="draft",
                        payment_status="pending"
                    )

                    booking_id = repo.create_booking(booking)
                    if booking_id:
                        # Audit log
                        user = st.session_state.get("user", {})
                        audit_log(
                            action=AuditAction.CREATE,
                            entity_type="booking",
                            entity_id=booking_id,
                            user_id=user.get("id"),
                            user_email=user.get("email"),
                            details={
                                "package_name": package_name,
                                "total_price": total_price,
                                "jamaah_name": jamaah_name.strip()
                            }
                        )
                        st.success("Booking berhasil dibuat!")
                        st.session_state.booking_view = "list"
                        st.rerun()
                    else:
                        st.error("Gagal membuat booking. Silakan coba lagi.")

                except Exception as e:
                    logger.error(f"Failed to create booking: {e}")
                    st.error(f"Gagal membuat booking: {str(e)}")


# =============================================================================
# UI: BOOKING DETAIL
# =============================================================================

def render_booking_detail(booking_id: str):
    """Render booking detail."""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        booking = repo.get_booking(booking_id)

        if not booking:
            st.error("Booking tidak ditemukan")
            return

        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## {booking.booking_code}")
            pkg_type = booking.package_type.upper() if booking.package_type else "REGULAR"
            st.caption(f"{booking.package_name} | {pkg_type}")

        with col2:
            if st.button("Kembali", use_container_width=True):
                st.session_state.booking_view = "list"
                st.session_state.selected_booking = None
                st.rerun()

        st.markdown("---")

        # Status cards
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**Status:** :{get_status_color(booking.status)}[{booking.status.upper()}]")

        with col2:
            st.markdown(f"**Pembayaran:** :{get_payment_status_color(booking.payment_status)}[{booking.payment_status.upper()}]")

        with col3:
            progress = (booking.amount_paid / booking.total_price * 100) if booking.total_price > 0 else 0
            st.progress(progress / 100, text=f"Terbayar: {progress:.0f}%")

        # Details
        st.markdown("### Detail Booking")
        col1, col2 = st.columns(2)

        with col1:
            detail_left = (
                '<div class="detail-card">'
                '<div class="detail-label">Berangkat</div>'
                '<div class="detail-value">' + format_date(booking.departure_date) + '</div>'
                '<br/>'
                '<div class="detail-label">Pulang</div>'
                '<div class="detail-value">' + format_date(booking.return_date) + '</div>'
                '<br/>'
                '<div class="detail-label">Durasi</div>'
                '<div class="detail-value">' + str(booking.duration_days) + ' hari</div>'
                '<br/>'
                '<div class="detail-label">Tipe Kamar</div>'
                '<div class="detail-value">' + str(booking.room_type or "-") + '</div>'
                '</div>'
            )
            st.markdown(detail_left, unsafe_allow_html=True)

        with col2:
            remaining_val = format_rupiah(booking.amount_remaining or 0)
            detail_right = (
                '<div class="detail-card">'
                '<div class="detail-label">Harga Paket</div>'
                '<div class="detail-value">' + format_rupiah(booking.package_price) + '</div>'
                '<br/>'
                '<div class="detail-label">Diskon</div>'
                '<div class="detail-value">' + format_rupiah(booking.discount_amount) + '</div>'
                '<br/>'
                '<div class="detail-label">Total</div>'
                '<div class="detail-value" style="color:#d4af37;font-weight:700;">'
                + format_rupiah(booking.total_price) + '</div>'
                '<br/>'
                '<div class="detail-label">Sisa Bayar</div>'
                '<div class="detail-value">' + remaining_val + '</div>'
                '</div>'
            )
            st.markdown(detail_right, unsafe_allow_html=True)

        # Update status
        st.markdown("---")
        st.markdown("### Update Status")
        col1, col2 = st.columns(2)

        with col1:
            new_status = st.selectbox(
                "Status Booking",
                options=["draft", "confirmed", "processing", "completed", "cancelled"],
                index=["draft", "confirmed", "processing", "completed", "cancelled"].index(booking.status),
                format_func=lambda x: {
                    "draft": "Draft",
                    "confirmed": "Dikonfirmasi",
                    "processing": "Diproses",
                    "completed": "Selesai",
                    "cancelled": "Dibatalkan"
                }.get(x, x)
            )
            if new_status != booking.status:
                if st.button("Update Status"):
                    repo.update_booking(booking_id, {"status": new_status})
                    st.success("Status diupdate!")
                    st.rerun()

        # Payments section
        st.markdown("---")
        st.markdown("### Riwayat Pembayaran")

        payments = repo.get_payments_for_booking(booking_id)

        if payments:
            for payment in payments:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

                    with col1:
                        inst_num = payment.get("installment_number", "")
                        type_label = {
                            "dp": "DP",
                            "installment": "Cicilan #" + str(inst_num),
                            "final": "Pelunasan",
                            "additional": "Tambahan"
                        }.get(payment.get("payment_type", ""), payment.get("payment_type", ""))
                        st.markdown(f"**{type_label}**")
                        st.caption(format_date(payment.get("created_at")))

                    with col2:
                        st.markdown(f"**{format_rupiah(payment.get('amount', 0))}**")
                        st.caption(payment.get("payment_method", "-"))

                    with col3:
                        status = payment.get("status", "pending")
                        color = {"pending": "orange", "confirmed": "green", "failed": "red"}.get(status, "gray")
                        st.markdown(f":{color}[{status.upper()}]")
                        if payment.get("due_date"):
                            st.caption(f"Jatuh tempo: {format_date(payment.get('due_date'))}")

                    with col4:
                        if payment.get("status") == "pending":
                            if st.button("Konfirmasi", key=f"confirm_{payment.get('id')}", help="Konfirmasi pembayaran"):
                                repo.confirm_payment(payment.get("id"))
                                st.success("Pembayaran dikonfirmasi!")
                                st.rerun()

                    st.divider()
        else:
            st.info("Belum ada pembayaran")

        # Add payment form
        with st.expander("Tambah Pembayaran"):
            with st.form("add_payment"):
                col1, col2 = st.columns(2)

                with col1:
                    payment_type = st.selectbox(
                        "Tipe Pembayaran",
                        options=["dp", "installment", "final"],
                        format_func=lambda x: {"dp": "DP", "installment": "Cicilan", "final": "Pelunasan"}.get(x, x)
                    )
                    amount = st.number_input("Jumlah", min_value=0, value=int(booking.total_price * 0.3), step=100000)

                with col2:
                    payment_method = st.selectbox(
                        "Metode",
                        options=["transfer", "cash", "qris"],
                        format_func=lambda x: {"transfer": "Transfer Bank", "cash": "Tunai", "qris": "QRIS"}.get(x, x)
                    )
                    due_date = st.date_input("Jatuh Tempo", value=date.today() + timedelta(days=7))

                if st.form_submit_button("Tambah Pembayaran", type="primary"):
                    from services.crm import Payment
                    payment = Payment(
                        booking_id=booking_id,
                        payment_type=payment_type,
                        amount=amount,
                        payment_method=payment_method,
                        due_date=due_date,
                        status="pending"
                    )
                    repo.create_payment(payment)
                    st.success("Pembayaran ditambahkan!")
                    st.rerun()

        # Installment calculator
        st.markdown("---")
        st.markdown("### Kalkulator Cicilan")

        remaining = booking.amount_remaining or booking.total_price
        if remaining > 0:
            col1, col2 = st.columns(2)

            with col1:
                num_installments = st.selectbox("Jumlah Cicilan", options=[3, 6, 9, 12])

            with col2:
                installment_amount = remaining / num_installments
                st.metric("Cicilan per Bulan", format_rupiah(int(installment_amount)))

            # Show schedule
            st.markdown("**Jadwal Cicilan:**")
            schedule_data = []
            for i in range(num_installments):
                due = date.today() + timedelta(days=30 * (i + 1))
                schedule_data.append({
                    "Cicilan": "#" + str(i + 1),
                    "Jumlah": format_rupiah(int(installment_amount)),
                    "Jatuh Tempo": format_date(due)
                })

            import pandas as pd
            st.dataframe(pd.DataFrame(schedule_data), use_container_width=True, hide_index=True)

        else:
            st.success("Pembayaran sudah lunas!")

        # Notes
        if booking.notes:
            st.markdown("---")
            st.markdown("### Catatan")
            st.write(booking.notes)

    except Exception as e:
        logger.error(f"Failed to load booking detail: {e}")
        st.error("Gagal memuat detail booking")


# =============================================================================
# UI: PAYMENT REMINDERS
# =============================================================================

def render_payment_reminders():
    """Render payment reminders section."""
    st.markdown("### Pengingat Pembayaran")

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        overdue = repo.get_overdue_payments()
        pending = repo.get_pending_payments()

        if overdue:
            st.error(f"**{len(overdue)} pembayaran sudah jatuh tempo!**")
            for p in overdue[:5]:
                booking_code = p.get("booking_code", "N/A")
                jamaah_name = p.get("jamaah_name", "N/A")
                amount_str = format_rupiah(p.get("amount", 0))
                row_html = (
                    '<div class="reminder-overdue">'
                    '<strong>' + str(booking_code) + '</strong> - '
                    + str(jamaah_name) + ': ' + amount_str
                    + '</div>'
                )
                st.markdown(row_html, unsafe_allow_html=True)

        elif pending:
            st.warning(f"**{len(pending)} pembayaran menunggu konfirmasi**")

        else:
            st.success("Tidak ada pembayaran yang jatuh tempo")

    except Exception as e:
        logger.error(f"Failed to load reminders: {e}")


# =============================================================================
# UI: AI BOOKING INSIGHTS
# =============================================================================

def render_ai_booking_insights():
    """Render AI-powered booking insights and trend analysis."""
    st.markdown("### AI Booking Insights")
    st.caption("Analisis tren booking dan pembayaran menggunakan AI.")

    # Gather booking data for context
    bookings_data = []
    stats_summary = ""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        stats = repo.get_crm_stats()
        bookings = repo.get_bookings(limit=50)

        total_bookings = stats.total_bookings or 0
        total_revenue = stats.total_revenue or 0
        total_paid = stats.total_paid or 0
        total_pending = stats.total_pending or 0

        stats_summary = (
            f"Total Booking: {total_bookings}\n"
            f"Total Revenue: {format_rupiah(total_revenue)}\n"
            f"Sudah Dibayar: {format_rupiah(total_paid)}\n"
            f"Belum Dibayar: {format_rupiah(total_pending)}\n"
        )

        if bookings:
            # Count by status
            status_counts = {}
            payment_counts = {}
            package_types = {}
            for b in bookings:
                s = b.status or "unknown"
                status_counts[s] = status_counts.get(s, 0) + 1
                ps = b.payment_status or "unknown"
                payment_counts[ps] = payment_counts.get(ps, 0) + 1
                pt = b.package_type or "regular"
                package_types[pt] = package_types.get(pt, 0) + 1

            stats_summary += "\nBreakdown Status Booking:\n"
            for s, c in status_counts.items():
                stats_summary += f"- {s}: {c}\n"

            stats_summary += "\nBreakdown Status Pembayaran:\n"
            for ps, c in payment_counts.items():
                stats_summary += f"- {ps}: {c}\n"

            stats_summary += "\nBreakdown Tipe Paket:\n"
            for pt, c in package_types.items():
                stats_summary += f"- {pt}: {c}\n"

            # Collection rate
            if total_revenue > 0:
                collection_pct = (total_paid / total_revenue) * 100
                stats_summary += f"\nTingkat Koleksi Pembayaran: {collection_pct:.1f}%\n"

        bookings_data = bookings or []

    except Exception as e:
        logger.error(f"Failed to load booking data for AI: {e}")
        st.info("Belum ada data booking untuk dianalisis.")
        return

    if not bookings_data:
        st.info("Belum ada data booking untuk dianalisis. Tambahkan booking terlebih dahulu.")
        return

    if st.button("Analisis Booking dengan AI", use_container_width=True, type="primary", key="btn_ai_booking_insights"):
        with st.spinner("AI sedang menganalisis data booking Anda..."):
            prompt_text = (
                "Analisis data booking umrah berikut dan berikan insights:\n\n"
                + stats_summary
                + "\nBerikan:\n"
                "1. Ringkasan kondisi booking saat ini\n"
                "2. Analisis tren pembayaran (apakah collection rate baik?)\n"
                "3. Rekomendasi untuk meningkatkan konversi dan pembayaran\n"
                "4. Tips follow-up untuk jamaah yang belum bayar\n"
                "5. Saran strategi paket yang populer\n"
                "\nJawab dalam bahasa Indonesia, singkat dan praktis."
            )

            system_prompt = (
                "Kamu adalah konsultan bisnis travel umrah berpengalaman. "
                "Berikan analisis data booking yang actionable dan praktis "
                "untuk travel agent umrah di Indonesia. Fokus pada insights "
                "yang bisa langsung diterapkan untuk meningkatkan penjualan "
                "dan collection rate pembayaran. Gunakan bahasa Indonesia yang sopan."
            )

            response = ai_complete(prompt_text, system_prompt=system_prompt, max_tokens=1024)

            if response:
                # Award XP for AI analysis (first time)
                if not st.session_state.get("crm_booking_ai_xp_awarded", False):
                    st.session_state.crm_booking_ai_xp_awarded = True
                    add_xp_safe(15, "Analisis booking dengan AI")

                ai_html = (
                    '<div class="ai-card" role="status" aria-live="polite">'
                    '<h4>Hasil Analisis AI</h4>'
                    '<p>' + _markdown_to_html_simple(response) + '</p>'
                    '</div>'
                )
                st.markdown(ai_html, unsafe_allow_html=True)
            else:
                _render_fallback_insights(stats_summary)


def _render_fallback_insights(stats_summary: str):
    """Render fallback insights when AI is unavailable."""
    fallback_html = (
        '<div class="ai-card" role="status" aria-live="polite">'
        '<h4>Ringkasan Booking</h4>'
        '<p>'
        '<strong>Tips Pengelolaan Booking:</strong><br/>'
        '&bull; Lakukan follow-up jamaah yang belum bayar dalam 3 hari<br/>'
        '&bull; Tawarkan cicilan untuk meningkatkan konversi booking<br/>'
        '&bull; Konfirmasi pembayaran secepat mungkin untuk menjaga kepercayaan<br/>'
        '&bull; Pantau booking yang mendekati tanggal keberangkatan<br/>'
        '&bull; Berikan diskon early bird untuk booking jauh hari<br/>'
        '</p>'
        '</div>'
    )
    st.markdown(fallback_html, unsafe_allow_html=True)


# =============================================================================
# UI: MAIN PAGE
# =============================================================================

def render_crm_bookings_page():
    """Main bookings page."""
    try:
        from services.analytics import track_page
        track_page("crm_bookings")
    except Exception:
        pass

    init_session_state()

    # Hero
    render_hero()

    # Header actions
    col1, col2 = st.columns([3, 1])
    with col1:
        pass
    with col2:
        if st.button("Tambah Booking", type="primary", use_container_width=True):
            st.session_state.booking_view = "add"
            st.rerun()

    # Stats
    render_booking_stats()

    st.markdown("---")

    # View
    if st.session_state.booking_view == "add":
        render_add_booking_form()
    elif st.session_state.booking_view == "detail" and st.session_state.selected_booking:
        render_booking_detail(st.session_state.selected_booking)
    else:
        tab1, tab2, tab3 = st.tabs(["Daftar Booking", "Pengingat", "AI Insights"])

        with tab1:
            render_booking_list()

        with tab2:
            render_payment_reminders()

        with tab3:
            render_ai_booking_insights()


__all__ = ["render_crm_bookings_page"]
