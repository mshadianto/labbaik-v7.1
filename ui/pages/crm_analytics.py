"""
LABBAIK AI - CRM Analytics Dashboard
======================================
Analytics and reporting for travel CRM.
"""

import streamlit as st
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

from ui.components import format_idr as format_rupiah


def format_number(num: int) -> str:
    """Format large numbers."""
    if num >= 1000000000:
        return f"{num/1000000000:.1f}M"
    elif num >= 1000000:
        return f"{num/1000000:.1f}jt"
    elif num >= 1000:
        return f"{num/1000:.1f}rb"
    return str(num)


def render_kpi_cards():
    """Render main KPI cards."""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        stats = repo.get_crm_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 14px; opacity: 0.9;">Total Leads</h3>
                <h1 style="margin: 10px 0 0 0; font-size: 32px;">{}</h1>
            </div>
            """.format(stats.total_leads), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 14px; opacity: 0.9;">Conversion Rate</h3>
                <h1 style="margin: 10px 0 0 0; font-size: 32px;">{:.1f}%</h1>
            </div>
            """.format(stats.conversion_rate), unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 14px; opacity: 0.9;">Total Booking</h3>
                <h1 style="margin: 10px 0 0 0; font-size: 32px;">{}</h1>
            </div>
            """.format(stats.total_bookings), unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 14px; opacity: 0.9;">Total Revenue</h3>
                <h1 style="margin: 10px 0 0 0; font-size: 28px;">{}</h1>
            </div>
            """.format(format_number(stats.total_revenue)), unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Failed to load KPIs: {e}")
        # Show placeholder cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Leads", 0)
        with col2:
            st.metric("Conversion Rate", "0%")
        with col3:
            st.metric("Total Booking", 0)
        with col4:
            st.metric("Total Revenue", "Rp 0")


def render_secondary_kpis():
    """Render secondary KPI metrics."""
    try:
        from services.crm import CRMRepository
        repo = CRMRepository()
        stats = repo.get_crm_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Jamaah",
                stats.total_jamaah,
                help="Total jamaah dalam database"
            )

        with col2:
            st.metric(
                "Sudah Dibayar",
                format_rupiah(stats.total_paid),
                help="Total pembayaran yang sudah diterima"
            )

        with col3:
            st.metric(
                "Belum Dibayar",
                format_rupiah(stats.total_pending),
                help="Total pembayaran yang masih pending"
            )

        with col4:
            # Calculate average booking value
            avg_value = stats.total_revenue // stats.total_bookings if stats.total_bookings > 0 else 0
            st.metric(
                "Rata-rata Booking",
                format_rupiah(avg_value),
                help="Nilai rata-rata per booking"
            )

    except Exception as e:
        logger.error(f"Failed to load secondary KPIs: {e}")


def render_lead_funnel():
    """Render lead funnel chart."""
    st.markdown("### Lead Funnel")

    try:
        from services.crm import CRMRepository
        repo = CRMRepository()

        leads_by_status = repo.count_leads_by_status()

        # Order for funnel
        funnel_order = ["new", "contacted", "interested", "negotiating", "won"]
        funnel_labels = {
            "new": "Baru",
            "contacted": "Dihubungi",
            "interested": "Tertarik",
            "negotiating": "Negosiasi",
            "won": "Deal"
        }

        funnel_data = []
        for status in funnel_order:
            count = leads_by_status.get(status, 0)
            funnel_data.append({
                "stage": funnel_labels.get(status, status),
                "count": count
            })

        # Display as horizontal bars
        max_count = max([d["count"] for d in funnel_data]) if funnel_data else 1

        for data in funnel_data:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"**{data['stage']}**")
            with col2:
                progress = data["count"] / max_count if max_count > 0 else 0
                st.progress(progress, text=f"{data['count']}")

        # Lost leads
        lost_count = leads_by_status.get("lost", 0)
        if lost_count > 0:
            st.caption(f"❌ Tidak Jadi: {lost_count}")

    except Exception as e:
        logger.error(f"Failed to render funnel: {e}")
        st.info("Belum ada data lead")


def render_revenue_chart():
    """Render revenue trend chart."""
    st.markdown("### Trend Revenue")

    period = st.selectbox(
        "Periode",
        options=["7 Hari", "30 Hari", "90 Hari"],
        index=1,
        key="revenue_period"
    )

    days = {"7 Hari": 7, "30 Hari": 30, "90 Hari": 90}.get(period, 30)

    try:
        from services.crm import CRMRepository
        import pandas as pd

        repo = CRMRepository()
        trend_data = repo.get_revenue_trend(days)

        if trend_data:
            df = pd.DataFrame(trend_data)
            df['date'] = pd.to_datetime(df['date'])

            st.line_chart(df.set_index('date')['revenue'])

            # Summary
            total = df['revenue'].sum()
            avg = df['revenue'].mean()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Periode", format_rupiah(int(total)))
            with col2:
                st.metric("Rata-rata/Hari", format_rupiah(int(avg)))
        else:
            st.info("Belum ada data revenue")

    except Exception as e:
        logger.error(f"Failed to render revenue chart: {e}")
        st.info("Tidak dapat memuat data revenue")


def render_lead_sources():
    """Render lead sources breakdown."""
    st.markdown("### Sumber Lead")

    try:
        from services.crm import CRMRepository

        repo = CRMRepository()

        # Get leads and count by source
        leads = repo.get_leads(limit=1000)

        if leads:
            source_counts = {}
            for lead in leads:
                source = lead.source or "unknown"
                source_counts[source] = source_counts.get(source, 0) + 1

            source_labels = {
                "direct": "Langsung",
                "referral": "Referensi",
                "social": "Media Sosial",
                "ads": "Iklan",
                "website": "Website",
                "whatsapp": "WhatsApp",
                "event": "Event",
                "unknown": "Lainnya"
            }

            import pandas as pd

            data = [{"Sumber": source_labels.get(k, k), "Jumlah": v} for k, v in source_counts.items()]
            df = pd.DataFrame(data)

            st.bar_chart(df.set_index('Sumber'))
        else:
            st.info("Belum ada data lead")

    except Exception as e:
        logger.error(f"Failed to render lead sources: {e}")
        st.info("Tidak dapat memuat data sumber lead")


def render_payment_status():
    """Render payment status overview."""
    st.markdown("### Status Pembayaran")

    try:
        from services.crm import CRMRepository

        repo = CRMRepository()
        bookings = repo.get_bookings(limit=100)

        if bookings:
            status_counts = {
                "pending": 0,
                "dp_paid": 0,
                "partial": 0,
                "paid": 0
            }

            for booking in bookings:
                status = booking.payment_status or "pending"
                if status in status_counts:
                    status_counts[status] += 1

            status_labels = {
                "pending": "Belum Bayar",
                "dp_paid": "DP Lunas",
                "partial": "Cicilan",
                "paid": "Lunas"
            }

            status_colors = {
                "pending": "🔴",
                "dp_paid": "🟠",
                "partial": "🟡",
                "paid": "🟢"
            }

            for status, count in status_counts.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"{status_colors.get(status, '⚪')} {status_labels.get(status, status)}")
                with col2:
                    st.markdown(f"**{count}**")

            # Overdue payments
            overdue = repo.get_overdue_payments()
            if overdue:
                st.error(f"⚠️ {len(overdue)} pembayaran jatuh tempo!")

        else:
            st.info("Belum ada data booking")

    except Exception as e:
        logger.error(f"Failed to render payment status: {e}")
        st.info("Tidak dapat memuat status pembayaran")


def render_upcoming_departures():
    """Render upcoming departures."""
    st.markdown("### Keberangkatan Mendatang")

    try:
        from services.crm import CRMRepository

        repo = CRMRepository()

        # Get confirmed bookings with upcoming departure
        bookings = repo.get_bookings(
            status="confirmed",
            departure_from=date.today(),
            departure_to=date.today() + timedelta(days=60),
            limit=10
        )

        if bookings:
            for booking in bookings:
                days_left = (booking.departure_date - date.today()).days if booking.departure_date else 0

                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"**{booking.booking_code}**")
                    st.caption(booking.package_name)

                with col2:
                    if booking.departure_date:
                        st.caption(booking.departure_date.strftime("%d %b %Y"))

                with col3:
                    if days_left <= 7:
                        st.markdown(f"🔴 **{days_left} hari**")
                    elif days_left <= 14:
                        st.markdown(f"🟠 **{days_left} hari**")
                    else:
                        st.markdown(f"🟢 {days_left} hari")

                st.divider()
        else:
            st.info("Tidak ada keberangkatan dalam 60 hari ke depan")

    except Exception as e:
        logger.error(f"Failed to render departures: {e}")
        st.info("Tidak dapat memuat data keberangkatan")


def render_quick_actions():
    """Render quick action buttons."""
    st.markdown("### Aksi Cepat")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("➕ Tambah Lead", use_container_width=True):
            st.session_state.current_page = "crm_leads"
            st.session_state.crm_view = "add"
            st.rerun()

    with col2:
        if st.button("📅 Buat Booking", use_container_width=True):
            st.session_state.current_page = "crm_bookings"
            st.session_state.booking_view = "add"
            st.rerun()

    with col3:
        if st.button("📋 Buat Quote", use_container_width=True):
            st.session_state.current_page = "crm_quotes"
            st.rerun()

    with col4:
        if st.button("📦 Package Builder", use_container_width=True):
            st.session_state.current_page = "package_builder"
            st.rerun()


def render_crm_analytics_page():
    """Main analytics dashboard."""
    try:
        from services.analytics import track_page
        track_page("crm_analytics")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    if not st.session_state.get("crm_analytics_view_xp"):
        st.session_state.crm_analytics_view_xp = True
        add_xp_safe(10, "Mengakses analitik CRM")

    st.markdown("""
        <div class="page-hero">
            <h1>📊 Dashboard Analytics</h1>
            <div class="subtitle">Overview performa CRM dan penjualan</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Main KPIs
    render_kpi_cards()

    st.markdown("---")

    # Secondary KPIs
    render_secondary_kpis()

    st.markdown("---")

    # Quick actions
    render_quick_actions()

    st.markdown("---")

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        render_lead_funnel()

    with col2:
        render_lead_sources()

    st.markdown("---")

    # Charts row 2
    col1, col2 = st.columns(2)

    with col1:
        render_revenue_chart()

    with col2:
        render_payment_status()

    st.markdown("---")

    # Upcoming departures
    render_upcoming_departures()

    # AI Summary
    st.markdown("---")
    if st.button("🤖 Rangkuman AI", use_container_width=True):
        with st.spinner("Menganalisis data CRM..."):
            summary = ai_complete(
                "Berikan 3-4 rekomendasi aksi untuk meningkatkan performa CRM travel umrah. "
                "Fokus pada: konversi lead, retensi jamaah, dan optimasi revenue. "
                "Format: nomor dan rekomendasi singkat. Bahasa Indonesia.",
                system_prompt="Kamu adalah CRM consultant untuk industri travel umrah.",
                max_tokens=400,
            )
            if summary:
                st.markdown(f"""
                    <div class="ai-card" role="status" aria-live="polite">
                        <h4>🤖 Rekomendasi AI untuk Meningkatkan Performa</h4>
                        <p>{summary}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


__all__ = ["render_crm_analytics_page"]
