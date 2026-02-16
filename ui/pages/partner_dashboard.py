"""
================================================================================
LABBAIK AI v6.0 - Partner Dashboard Page
================================================================================
Dashboard for travel agent and hotel partners.
Tracks bookings, revenue, commission, and provides AI business insights.
================================================================================
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import random

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS


# =============================================================================
# STYLING
# =============================================================================

PARTNER_CSS = """
/* Partner dashboard hero */
.partner-hero {
    --hero-bg: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
    --hero-subtitle: #b0b0b0;
}

/* Status badges */
.status-pending {
    display: inline-block;
    background: #4a3a1a;
    color: #fbbf24;
    padding: 0.2rem 0.7rem;
    border-radius: 10px;
    font-size: 0.78rem;
    font-weight: bold;
}

.status-confirmed {
    display: inline-block;
    background: #1a3a1a;
    color: #4ade80;
    padding: 0.2rem 0.7rem;
    border-radius: 10px;
    font-size: 0.78rem;
    font-weight: bold;
}

.status-completed {
    display: inline-block;
    background: #1a2a3a;
    color: #60a5fa;
    padding: 0.2rem 0.7rem;
    border-radius: 10px;
    font-size: 0.78rem;
    font-weight: bold;
}

.status-cancelled {
    display: inline-block;
    background: #4a1a1a;
    color: #f87171;
    padding: 0.2rem 0.7rem;
    border-radius: 10px;
    font-size: 0.78rem;
    font-weight: bold;
}

/* Commission card */
.commission-card {
    background: linear-gradient(145deg, #1a2e1a 0%, #1e3b1e 100%);
    border-radius: 15px;
    padding: 1.5rem;
    border: 1px solid #228B22;
    text-align: center;
    margin-bottom: 1rem;
}

.commission-card .amount {
    font-size: 2rem;
    font-weight: 700;
    color: #4ade80;
    margin: 0.5rem 0;
}

.commission-card .label {
    color: #94a3b8;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Withdrawal history row */
.withdrawal-row {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #1e293b;
    transition: border-color 0.2s;
}

.withdrawal-row:hover {
    border-color: #334155;
}

.withdrawal-date {
    color: #e2e8f0;
    font-weight: 500;
}

.withdrawal-amount {
    color: #4ade80;
    font-weight: 700;
}

.withdrawal-status {
    color: #60a5fa;
    font-size: 0.85rem;
}

/* Package / city progress item */
.ranking-item {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.5rem;
    border: 1px solid #1e293b;
}

.ranking-item .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}

.ranking-item .item-name {
    color: #e2e8f0;
    font-weight: 600;
    font-size: 0.92rem;
}

.ranking-item .item-count {
    color: #d4af37;
    font-weight: 700;
    font-size: 0.92rem;
}

.ranking-bar-bg {
    width: 100%;
    height: 6px;
    background: #334155;
    border-radius: 3px;
    overflow: hidden;
}

.ranking-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.6s ease;
}
"""


# =============================================================================
# SAMPLE DATA
# =============================================================================

def generate_sample_bookings() -> List[Dict]:
    """Generate sample bookings for demo."""
    statuses = ["pending", "confirmed", "completed", "cancelled"]
    cities = ["Jakarta", "Surabaya", "Bandung", "Medan"]
    packages = ["Backpacker", "Reguler", "Plus", "VIP"]

    bookings = []
    for i in range(15):
        dep_date = date.today() + timedelta(days=random.randint(10, 90))
        bookings.append({
            "id": f"LBK-{random.randint(100000, 999999)}",
            "customer_name": f"Customer {i+1}",
            "customer_phone": f"+628{random.randint(1000000000, 9999999999)}",
            "departure_city": random.choice(cities),
            "departure_date": dep_date.strftime("%d %b %Y"),
            "return_date": (dep_date + timedelta(days=random.randint(9, 15))).strftime("%d %b %Y"),
            "package_type": random.choice(packages),
            "travelers": random.randint(1, 5),
            "total_price": random.randint(25, 75) * 1_000_000,
            "commission": random.randint(25, 75) * 100_000,
            "status": random.choice(statuses),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%d %b %Y"),
        })
    return bookings


def generate_sample_stats() -> Dict:
    """Generate sample statistics."""
    return {
        "total_bookings": 156,
        "confirmed_bookings": 98,
        "pending_bookings": 23,
        "total_revenue": 4_250_000_000,
        "total_commission": 425_000_000,
        "pending_commission": 45_000_000,
        "total_travelers": 412,
        "avg_booking_value": 27_250_000,
        "conversion_rate": 0.68,
        "monthly_growth": 0.12,
    }


def generate_monthly_data() -> List[Dict]:
    """Generate monthly performance data."""
    months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return [
        {"month": m, "bookings": random.randint(15, 35), "revenue": random.randint(400, 800) * 1_000_000}
        for m in months
    ]


# =============================================================================
# AI BUSINESS INSIGHTS
# =============================================================================

AI_SYSTEM_PROMPT = (
    "Kamu adalah konsultan bisnis travel umrah berpengalaman di Indonesia. "
    "Berikan analisis bisnis yang tajam dan saran optimasi revenue yang praktis "
    "untuk travel agent partner. Fokus pada tren booking, strategi penjualan, "
    "dan peluang peningkatan komisi. Gunakan bahasa Indonesia yang profesional."
)


def generate_ai_business_insights(stats: Dict, bookings: List[Dict], monthly_data: List[Dict]) -> Optional[str]:
    """Generate AI-powered business insights for partner dashboard."""
    status_counts = {}
    city_counts = {}
    package_counts = {}
    for b in bookings:
        s = b["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
        c = b["departure_city"]
        city_counts[c] = city_counts.get(c, 0) + 1
        p = b["package_type"]
        package_counts[p] = package_counts.get(p, 0) + 1

    monthly_summary_parts = []
    for m in monthly_data:
        monthly_summary_parts.append(
            f"  - {m['month']}: {m['bookings']} bookings, revenue Rp {m['revenue']/1_000_000:.0f}jt"
        )
    monthly_summary = "\n".join(monthly_summary_parts)

    status_parts = []
    for s, c in status_counts.items():
        status_parts.append(f"  - {s}: {c}")
    status_summary = "\n".join(status_parts)

    city_parts = []
    for c, n in sorted(city_counts.items(), key=lambda x: x[1], reverse=True):
        city_parts.append(f"  - {c}: {n}")
    city_summary = "\n".join(city_parts)

    package_parts = []
    for p, n in sorted(package_counts.items(), key=lambda x: x[1], reverse=True):
        package_parts.append(f"  - {p}: {n}")
    package_summary = "\n".join(package_parts)

    prompt_text = (
        f"Analisis performa bisnis travel umrah partner berikut dan berikan insights:\n\n"
        f"STATISTIK UTAMA:\n"
        f"- Total Booking: {stats['total_bookings']}\n"
        f"- Booking Confirmed: {stats['confirmed_bookings']}\n"
        f"- Booking Pending: {stats['pending_bookings']}\n"
        f"- Total Revenue: Rp {stats['total_revenue']/1_000_000_000:.1f}M\n"
        f"- Total Komisi: Rp {stats['total_commission']/1_000_000:.0f}jt\n"
        f"- Conversion Rate: {stats['conversion_rate']*100:.0f}%\n"
        f"- Pertumbuhan Bulanan: {stats['monthly_growth']*100:.0f}%\n"
        f"- Rata-rata Value per Booking: Rp {stats['avg_booking_value']/1_000_000:.0f}jt\n\n"
        f"DISTRIBUSI STATUS:\n{status_summary}\n\n"
        f"KOTA KEBERANGKATAN:\n{city_summary}\n\n"
        f"PAKET POPULER:\n{package_summary}\n\n"
        f"PERFORMA BULANAN:\n{monthly_summary}\n\n"
        f"Berikan:\n"
        f"1. Ringkasan performa bisnis (2-3 kalimat)\n"
        f"2. 3 insights utama dari data\n"
        f"3. 3 rekomendasi strategi untuk meningkatkan revenue dan konversi\n"
        f"Jawab dalam bahasa Indonesia."
    )

    return ai_complete(prompt_text, system_prompt=AI_SYSTEM_PROMPT, max_tokens=1024)


def _markdown_to_html(text: str) -> str:
    """Convert simple markdown to HTML for rendering inside styled divs."""
    import re

    lines = text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br/>")
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        if line.startswith("- ") or line.startswith("* "):
            line = "&bull; " + line[2:]
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            num = match.group(1)
            rest = line[match.end():]
            line = "<strong>" + num + ".</strong> " + rest
        html_lines.append("<div style='margin-bottom:0.3rem;'>" + line + "</div>")

    return "\n".join(html_lines)


def _render_fallback_insights(stats: Dict) -> None:
    """Render fallback business insights when AI is unavailable."""
    conversion_pct = stats["conversion_rate"] * 100
    growth_pct = stats["monthly_growth"] * 100
    avg_val = stats["avg_booking_value"] / 1_000_000

    tips = []
    if conversion_pct < 70:
        tips.append(
            "Conversion rate " + str(int(conversion_pct)) + "% masih bisa ditingkatkan. "
            "Pertimbangkan follow-up otomatis untuk booking pending."
        )
    if growth_pct > 0:
        tips.append(
            "Pertumbuhan bulanan +" + str(int(growth_pct)) + "% positif. "
            "Tingkatkan momentum dengan promo paket musiman."
        )
    if avg_val < 30:
        tips.append(
            "Rata-rata nilai booking Rp " + str(int(avg_val)) + "jt. "
            "Coba upsell ke paket Plus/VIP untuk meningkatkan revenue per booking."
        )
    tips.append(
        "Fokus pada kota dengan konversi tertinggi dan alokasikan lebih banyak "
        "budget marketing di sana."
    )

    tips_html_parts = []
    for i, tip in enumerate(tips, 1):
        tips_html_parts.append(
            "<div style='margin-bottom:0.5rem;'><strong>"
            + str(i) + ".</strong> " + tip + "</div>"
        )
    tips_html = "\n".join(tips_html_parts)

    html = (
        '<div class="ai-card" role="status" aria-live="polite">'
        '<h4>Rekomendasi Bisnis</h4>'
        '<p>' + tips_html + '</p>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Render a metric card."""
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)


def render_booking_table(bookings: List[Dict], show_actions: bool = True):
    """Render bookings table."""
    status_badges = {
        "pending": "🟡",
        "confirmed": "🟢",
        "completed": "✅",
        "cancelled": "🔴",
    }

    for booking in bookings:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

            with col1:
                st.markdown(f"**{booking['id']}**")
                st.caption(f"{booking['customer_name']}")

            with col2:
                st.markdown(f"📍 {booking['departure_city']}")
                st.caption(f"{booking['departure_date']} - {booking['return_date']}")

            with col3:
                st.markdown(f"👥 {booking['travelers']}")
                st.caption(booking['package_type'])

            with col4:
                st.markdown(f"Rp {booking['total_price']/1_000_000:.0f}jt")
                st.caption(f"Komisi: Rp {booking['commission']/1_000_000:.1f}jt")

            with col5:
                badge = status_badges.get(booking['status'], '⚪')
                st.markdown(f"{badge} {booking['status'].title()}")
                if show_actions and booking['status'] == 'pending':
                    if st.button("✅", key=f"confirm_{booking['id']}", help="Konfirmasi"):
                        st.success(f"Booking {booking['id']} dikonfirmasi!")

            st.divider()


def render_commission_summary(stats: Dict):
    """Render commission summary."""
    st.markdown("### 💰 Ringkasan Komisi")

    col1, col2, col3 = st.columns(3)

    with col1:
        growth_text = "+" + str(int(stats['monthly_growth'] * 100)) + "% bulan ini"
        st.metric(
            "Total Komisi",
            f"Rp {stats['total_commission']/1_000_000:.0f}jt",
            growth_text
        )

    with col2:
        st.metric(
            "Komisi Pending",
            f"Rp {stats['pending_commission']/1_000_000:.0f}jt"
        )

    with col3:
        avg_commission = stats['total_commission'] / stats['total_bookings'] / 1_000
        st.metric(
            "Rata-rata per Booking",
            f"Rp {avg_commission:.0f}rb"
        )


def render_performance_chart(monthly_data: List[Dict]):
    """Render performance chart."""
    import pandas as pd

    df = pd.DataFrame(monthly_data)

    st.markdown("### 📊 Performa Bulanan")

    tab1, tab2 = st.tabs(["Bookings", "Revenue"])

    with tab1:
        st.bar_chart(df.set_index("month")["bookings"])

    with tab2:
        st.line_chart(df.set_index("month")["revenue"])


def render_quick_actions():
    """Render quick action buttons."""
    st.markdown("### ⚡ Aksi Cepat")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Input Booking Baru", use_container_width=True):
            st.session_state.partner_action = "new_booking"

    with col2:
        if st.button("📤 Export Laporan", use_container_width=True):
            st.info("Generating report...")

    with col3:
        if st.button("💳 Tarik Komisi", use_container_width=True):
            st.session_state.partner_action = "withdraw"

    with col4:
        if st.button("📞 Hubungi Support", use_container_width=True):
            st.info("WhatsApp: +62 812 3456 7890")


def render_new_booking_form():
    """Render form for new booking input."""
    st.markdown("### 📝 Input Booking Baru")

    with st.form("new_booking_form"):
        col1, col2 = st.columns(2)

        with col1:
            customer_name = st.text_input("Nama Customer *")
            customer_phone = st.text_input("No. WhatsApp *", placeholder="+628...")
            customer_email = st.text_input("Email")
            departure_city = st.selectbox(
                "Kota Keberangkatan",
                ["Jakarta", "Surabaya", "Bandung", "Medan", "Makassar"]
            )

        with col2:
            departure_date = st.date_input("Tanggal Berangkat", min_value=date.today())
            return_date = st.date_input("Tanggal Pulang", min_value=date.today())
            travelers = st.number_input("Jumlah Jamaah", min_value=1, max_value=50, value=1)
            package_type = st.selectbox("Tipe Paket", ["Backpacker", "Reguler", "Plus", "VIP"])

        total_price = st.number_input(
            "Total Harga (Rp)",
            min_value=15_000_000,
            max_value=500_000_000,
            value=30_000_000,
            step=1_000_000
        )

        notes = st.text_area("Catatan")

        submitted = st.form_submit_button("💾 Simpan Booking", type="primary", use_container_width=True)

        if submitted:
            if customer_name and customer_phone:
                st.success("✅ Booking berhasil disimpan!")
                st.session_state.partner_action = None
                st.rerun()
            else:
                st.error("Nama dan nomor WhatsApp wajib diisi!")

    if st.button("⬅️ Kembali"):
        st.session_state.partner_action = None
        st.rerun()


def render_withdraw_form(stats: Dict):
    """Render commission withdrawal form."""
    st.markdown("### 💳 Tarik Komisi")

    pending_formatted = f"Rp {stats['pending_commission']:,.0f}"
    st.info(f"Saldo komisi tersedia: **{pending_formatted}**")

    with st.form("withdraw_form"):
        amount = st.number_input(
            "Jumlah Penarikan (Rp)",
            min_value=100_000,
            max_value=stats['pending_commission'],
            value=stats['pending_commission'],
            step=100_000
        )

        bank = st.selectbox(
            "Bank Tujuan",
            ["BCA", "Mandiri", "BNI", "BRI", "BSI", "CIMB Niaga"]
        )

        account_number = st.text_input("Nomor Rekening")
        account_name = st.text_input("Nama Pemilik Rekening")

        submitted = st.form_submit_button("💸 Ajukan Penarikan", type="primary", use_container_width=True)

        if submitted:
            if account_number and account_name:
                amount_formatted = f"Rp {amount:,.0f}"
                msg = (
                    "✅ Permintaan penarikan berhasil diajukan!\n\n"
                    "Jumlah: " + amount_formatted + "\n"
                    "Bank: " + bank + "\n"
                    "Rekening: " + account_number + "\n\n"
                    "Dana akan ditransfer dalam 1-3 hari kerja."
                )
                st.success(msg)
            else:
                st.error("Lengkapi data rekening!")

    if st.button("⬅️ Kembali"):
        st.session_state.partner_action = None
        st.rerun()


def render_partner_profile():
    """Render partner profile section."""
    st.markdown("### 👤 Profil Partner")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### PT Travel Sejahtera")
        st.caption("Travel Agent Partner")
        st.markdown("⭐⭐⭐⭐⭐ (4.8)")
        st.markdown("📍 Jakarta Selatan")

    with col2:
        with st.expander("📋 Detail Partner"):
            st.markdown(
                "- **ID Partner:** PTR-001234\n"
                "- **Sejak:** 15 Januari 2024\n"
                "- **Lisensi:** PPIU/2024/001234\n"
                "- **Komisi Rate:** 10%\n"
                "- **Status:** ✅ Aktif"
            )

        with st.expander("📞 Kontak"):
            st.markdown(
                "- **Email:** partner@travel.com\n"
                "- **WhatsApp:** +62 812 3456 7890\n"
                "- **Alamat:** Jl. Sudirman No. 123"
            )


def render_ai_insights_section(stats: Dict, bookings: List[Dict], monthly_data: List[Dict]):
    """Render AI-powered business insights section."""
    st.markdown("### 🤖 AI Business Insights")

    # Session state key for caching insights
    cache_key = "partner_ai_insights"
    xp_key = "partner_ai_insights_xp_awarded"

    if cache_key in st.session_state and st.session_state[cache_key]:
        # Show cached insights
        cached = st.session_state[cache_key]
        html = (
            '<div class="ai-card" role="status" aria-live="polite">'
            '<h4>🤖 Analisis AI - Performa Bisnis Anda</h4>'
            '<p>' + _markdown_to_html(cached) + '</p>'
            '</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.caption(
            "Dapatkan analisis AI tentang performa bisnis Anda, termasuk tren booking, "
            "optimasi revenue, dan rekomendasi strategi."
        )

    if st.button("🔍 Analisis Bisnis dengan AI", use_container_width=True):
        with st.spinner("AI sedang menganalisis data bisnis Anda..."):
            response = generate_ai_business_insights(stats, bookings, monthly_data)

        if response:
            st.session_state[cache_key] = response
            html = (
                '<div class="ai-card" role="status" aria-live="polite">'
                '<h4>🤖 Analisis AI - Performa Bisnis Anda</h4>'
                '<p>' + _markdown_to_html(response) + '</p>'
                '</div>'
            )
            st.markdown(html, unsafe_allow_html=True)

            # Gamification: +20 XP for AI insights (first time per session)
            if not st.session_state.get(xp_key, False):
                add_xp_safe(20, "Menggunakan AI Business Insights")
                st.session_state[xp_key] = True
        else:
            _render_fallback_insights(stats)


def render_withdrawal_history():
    """Render withdrawal history with styled rows."""
    st.markdown("### 📜 Riwayat Penarikan")

    withdrawals = [
        {"date": "01 Dec 2024", "amount": 15_000_000, "status": "completed", "bank": "BCA"},
        {"date": "15 Nov 2024", "amount": 12_500_000, "status": "completed", "bank": "BCA"},
        {"date": "01 Nov 2024", "amount": 18_000_000, "status": "completed", "bank": "BCA"},
    ]

    for w in withdrawals:
        amount_str = f"Rp {w['amount']/1_000_000:.1f}jt"
        status_str = w['status'].title()
        html = (
            '<div class="withdrawal-row">'
            '<span class="withdrawal-date">' + w['date'] + ' - ' + w['bank'] + '</span>'
            '<span class="withdrawal-amount">' + amount_str + '</span>'
            '<span class="withdrawal-status">✅ ' + status_str + '</span>'
            '</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


def render_ranking_section(title: str, data: Dict[str, int], max_val: int, color: str):
    """Render a ranking section with progress bars."""
    st.markdown(f"### {title}")

    for name, count in data.items():
        pct = min(count / max_val * 100, 100)
        count_text = str(count) + " bookings"
        html = (
            '<div class="ranking-item">'
            '<div class="item-header">'
            '<span class="item-name">' + name + '</span>'
            '<span class="item-count">' + count_text + '</span>'
            '</div>'
            '<div class="ranking-bar-bg">'
            '<div class="ranking-bar-fill" style="width: ' + str(pct) + '%; '
            'background: ' + color + ';"></div>'
            '</div>'
            '</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_partner_dashboard():
    """Render the main partner dashboard."""

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, PARTNER_CSS)

    # Track page view
    try:
        from services.analytics import track_page
        track_page("partner_dashboard")
    except Exception:
        pass

    # Hero header
    hero_html = (
        '<div class="page-hero partner-hero">'
        '<h1>🤝 Partner Dashboard</h1>'
        '<p class="subtitle">Kelola booking dan pantau performa bisnis Anda</p>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # Check authentication
    if not st.session_state.get("partner_authenticated", False):
        render_partner_login()
        return

    # Gamification: +25 XP for reviewing dashboard (first time per session)
    xp_key = "partner_dashboard_xp_awarded"
    if not st.session_state.get(xp_key, False):
        add_xp_safe(25, "Membuka Partner Dashboard")
        st.session_state[xp_key] = True

    # Initialize
    if "partner_action" not in st.session_state:
        st.session_state.partner_action = None

    # Handle actions
    if st.session_state.partner_action == "new_booking":
        render_new_booking_form()
        return

    if st.session_state.partner_action == "withdraw":
        render_withdraw_form(generate_sample_stats())
        return

    # Generate data
    stats = generate_sample_stats()
    bookings = generate_sample_bookings()
    monthly_data = generate_monthly_data()

    # Sidebar profile
    with st.sidebar:
        render_partner_profile()
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.partner_authenticated = False
            st.rerun()

    # Quick Actions
    render_quick_actions()

    st.divider()

    # Overview Metrics
    st.markdown("### 📈 Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        growth_count = int(stats['total_bookings'] * stats['monthly_growth'])
        st.metric(
            "Total Booking",
            stats['total_bookings'],
            f"+{growth_count} bulan ini"
        )

    with col2:
        confirm_pct = stats['confirmed_bookings'] / stats['total_bookings'] * 100
        st.metric(
            "Booking Confirmed",
            stats['confirmed_bookings'],
            f"{confirm_pct:.0f}%"
        )

    with col3:
        revenue_b = stats['total_revenue'] / 1_000_000_000
        growth_pct = stats['monthly_growth'] * 100
        st.metric(
            "Total Revenue",
            f"Rp {revenue_b:.1f}M",
            f"+{growth_pct:.0f}%"
        )

    with col4:
        avg_per_booking = stats['total_travelers'] / stats['total_bookings']
        st.metric(
            "Total Jamaah",
            stats['total_travelers'],
            f"avg {avg_per_booking:.1f}/booking"
        )

    st.divider()

    # AI Business Insights Section
    render_ai_insights_section(stats, bookings, monthly_data)

    st.divider()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Bookings",
        "💰 Komisi",
        "📊 Statistik",
        "⚙️ Pengaturan"
    ])

    with tab1:
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["Semua", "Pending", "Confirmed", "Completed", "Cancelled"]
            )
        with col2:
            date_filter = st.date_input(
                "Periode",
                value=(date.today() - timedelta(days=30), date.today())
            )
        with col3:
            search = st.text_input("Cari", placeholder="ID atau nama...")

        # Filter bookings
        filtered_bookings = bookings
        if status_filter != "Semua":
            filtered_bookings = [b for b in bookings if b['status'] == status_filter.lower()]

        st.markdown(f"**{len(filtered_bookings)} bookings**")
        render_booking_table(filtered_bookings)

    with tab2:
        render_commission_summary(stats)

        st.divider()

        render_withdrawal_history()

    with tab3:
        render_performance_chart(monthly_data)

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            packages_data = {
                "Reguler": 45,
                "Plus": 32,
                "VIP": 18,
                "Backpacker": 5
            }
            render_ranking_section("🏆 Top Packages", packages_data, 50, "#d4af37")

        with col2:
            cities_data = {
                "Jakarta": 52,
                "Surabaya": 35,
                "Bandung": 28,
                "Medan": 15,
                "Makassar": 12
            }
            render_ranking_section("🌍 Top Kota", cities_data, 60, "#60a5fa")

    with tab4:
        st.markdown("### ⚙️ Pengaturan")

        with st.expander("🔔 Notifikasi"):
            st.checkbox("Email untuk booking baru", value=True)
            st.checkbox("WhatsApp untuk booking baru", value=True)
            st.checkbox("Laporan mingguan", value=True)
            st.checkbox("Laporan bulanan", value=True)

        with st.expander("💳 Informasi Bank"):
            bank = st.selectbox("Bank", ["BCA", "Mandiri", "BNI", "BRI", "BSI"])
            account = st.text_input("Nomor Rekening", value="1234567890")
            name = st.text_input("Nama Rekening", value="PT Travel Sejahtera")
            if st.button("💾 Simpan"):
                st.success("Informasi bank berhasil disimpan!")

        with st.expander("🔒 Keamanan"):
            if st.button("🔑 Ganti Password"):
                st.info("Link reset password akan dikirim ke email Anda.")
            if st.button("📱 Setup 2FA"):
                st.info("Scan QR code dengan aplikasi authenticator.")


def render_partner_login():
    """Render partner login form."""
    st.markdown("### 🔐 Login Partner")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("partner_login"):
            email = st.text_input("Email Partner")
            password = st.text_input("Password", type="password")

            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

            if submitted:
                if email and password:
                    st.session_state.partner_authenticated = True
                    st.rerun()
                else:
                    st.error("Email dan password wajib diisi!")

        st.divider()
        st.markdown("Belum punya akun partner?")
        if st.button("📝 Daftar Sekarang", use_container_width=True):
            st.info("Hubungi tim LABBAIK AI untuk pendaftaran partner.")


__all__ = ["render_partner_dashboard", "render_partner_login"]


# Run page
if __name__ == "__main__":
    render_partner_dashboard()
