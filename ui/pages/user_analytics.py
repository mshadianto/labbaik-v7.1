"""
LABBAIK AI - User Analytics Dashboard
======================================
Admin dashboard for tracking user registrations and potential customers.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List
from services.user import (
    UserService, UserRepository, UserRole, UserStatus, User,
    get_user_service, get_user_repository
)
from services.user.user_service import get_current_user, is_logged_in, require_role
from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS


def render_user_analytics_page():
    """Main user analytics dashboard"""
    try:
        from services.analytics import track_page
        track_page("user_analytics")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    if not st.session_state.get("user_analytics_xp_awarded"):
        add_xp_safe(10, "Mengakses analitik pengguna")
        st.session_state.user_analytics_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1>📊 Dashboard Pengguna</h1>
            <div class="subtitle">Analitik pengguna terdaftar dan potensi konversi</div>
        </div>
    """, unsafe_allow_html=True)

    # Check admin access
    user = get_current_user()
    if not user or user.role != UserRole.ADMIN:
        st.warning("Halaman ini hanya dapat diakses oleh Admin")
        st.info("Untuk demo, data statistik tetap ditampilkan")

    # Get stats
    repo = get_user_repository()
    stats = repo.get_stats()

    # Quick stats
    st.markdown("### Ringkasan")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Pengguna",
            stats.get("total_users", 0),
            delta=f"+{stats.get('new_today', 0)} hari ini"
        )
    with col2:
        st.metric(
            "Aktif (7 Hari)",
            stats.get("active_7d", 0),
            help="Login dalam 7 hari terakhir"
        )
    with col3:
        premium_count = stats.get("by_role", {}).get("premium", 0)
        st.metric(
            "Premium",
            premium_count,
            help="Pengguna dengan akun premium"
        )
    with col4:
        active_pct = 0
        if stats.get("total_users", 0) > 0:
            active_pct = round(stats.get("active_7d", 0) / stats["total_users"] * 100, 1)
        st.metric(
            "Retention Rate",
            f"{active_pct}%",
            help="% pengguna aktif dalam 7 hari"
        )

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Tren Registrasi",
        "Demografi",
        "Preferensi Umrah",
        "Daftar Pengguna"
    ])

    with tab1:
        render_registration_trends(stats)

    with tab2:
        render_demographics(stats)

    with tab3:
        render_umrah_preferences(stats)

    with tab4:
        render_user_list()

    st.markdown("---")
    if st.button("🤖 Insight AI", key="user_analytics_ai"):
        with st.spinner("Menganalisis data pengguna..."):
            insight = ai_complete(
                "Berikan 3 rekomendasi untuk meningkatkan konversi pengguna gratis menjadi premium "
                "pada platform perencanaan umrah. Bahasa Indonesia.",
                system_prompt="Kamu adalah growth hacking consultant.",
                max_tokens=400,
            )
            if insight:
                st.markdown(f'''
                    <div class="ai-card">
                        <h4>🤖 Insight AI</h4>
                        <p>{insight}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


def render_registration_trends(stats: Dict[str, Any]):
    """Render registration trend charts"""
    st.markdown("### Tren Registrasi (30 Hari)")

    daily_data = stats.get("daily_registrations", [])

    if daily_data:
        # Create chart data
        import pandas as pd
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])

        st.line_chart(df.set_index('date')['count'], use_container_width=True)

        # Summary stats
        total_30d = sum(d['count'] for d in daily_data)
        avg_daily = total_30d / max(len(daily_data), 1)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total 30 Hari", total_30d)
        with col2:
            st.metric("Rata-rata/Hari", f"{avg_daily:.1f}")
        with col3:
            # Trend
            if len(daily_data) >= 14:
                first_half = sum(d['count'] for d in daily_data[:14])
                second_half = sum(d['count'] for d in daily_data[14:])
                trend = "Naik" if second_half > first_half else "Turun"
                st.metric("Tren", trend)
    else:
        st.info("Belum ada data registrasi")


def render_demographics(stats: Dict[str, Any]):
    """Render demographic charts"""
    st.markdown("### Demografi Pengguna")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Berdasarkan Role")
        by_role = stats.get("by_role", {})
        if by_role:
            role_labels = {
                "guest": "Tamu",
                "free": "Gratis",
                "premium": "Premium",
                "partner": "Mitra",
                "admin": "Admin"
            }
            for role, count in by_role.items():
                label = role_labels.get(role, role)
                pct = count / stats.get("total_users", 1) * 100
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.5rem;
                                background: rgba(255,255,255,0.05); border-radius: 8px; margin: 0.25rem 0;">
                        <span>{label}</span>
                        <span><strong>{count}</strong> ({pct:.1f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada data")

    with col2:
        st.markdown("#### Status Akun")
        by_status = stats.get("by_status", {})
        if by_status:
            status_labels = {
                "active": "Aktif",
                "inactive": "Nonaktif",
                "suspended": "Dibekukan",
                "pending": "Menunggu Verifikasi"
            }
            status_colors = {
                "active": "#4CAF50",
                "inactive": "#9E9E9E",
                "suspended": "#F44336",
                "pending": "#FF9800"
            }
            for status, count in by_status.items():
                label = status_labels.get(status, status)
                color = status_colors.get(status, "#2196F3")
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.5rem;
                                background: rgba(255,255,255,0.05); border-radius: 8px; margin: 0.25rem 0;">
                        <span style="color: {color};">● {label}</span>
                        <span><strong>{count}</strong></span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada data")

    st.markdown("---")
    st.markdown("#### Top 10 Provinsi")

    by_province = stats.get("by_province", {})
    if by_province:
        max_count = max(by_province.values()) if by_province else 1
        for province, count in by_province.items():
            pct = count / max_count * 100
            st.markdown(f"""
                <div style="margin: 0.5rem 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{province}</span>
                        <span>{count}</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 8px;">
                        <div style="background: #2196F3; width: {pct}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Tidak ada data provinsi")

    st.markdown("---")
    st.markdown("#### Sumber Traffic")

    by_source = stats.get("by_source", {})
    if by_source:
        source_labels = {
            "web": "Website",
            "organic": "Organik",
            "referral": "Referral",
            "ads": "Iklan",
            "social": "Media Sosial",
            "whatsapp": "WhatsApp"
        }
        for source, count in by_source.items():
            label = source_labels.get(source, source)
            st.markdown(f"- **{label}**: {count} pengguna")
    else:
        st.info("Tidak ada data sumber")


def render_umrah_preferences(stats: Dict[str, Any]):
    """Render Umrah preferences analysis"""
    st.markdown("### Preferensi Umrah Pengguna")
    st.markdown("Data ini membantu memahami paket apa yang paling diminati")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Budget Range")
        by_budget = stats.get("by_budget", {})
        if by_budget:
            budget_labels = {
                "low": "Hemat (< 25 Juta)",
                "medium": "Standar (25-35 Juta)",
                "high": "Nyaman (35-50 Juta)",
                "premium": "Premium (> 50 Juta)"
            }
            budget_colors = {
                "low": "#4CAF50",
                "medium": "#2196F3",
                "high": "#FF9800",
                "premium": "#9C27B0"
            }
            for budget, count in by_budget.items():
                label = budget_labels.get(budget, budget)
                color = budget_colors.get(budget, "#2196F3")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 8px; padding: 0.5rem;
                                background: rgba(255,255,255,0.05); border-radius: 8px; margin: 0.25rem 0;">
                        <span style="color: {color}; font-size: 1.5rem;">●</span>
                        <span style="flex: 1;">{label}</span>
                        <span><strong>{count}</strong></span>
                    </div>
                """, unsafe_allow_html=True)

            # Insights
            st.markdown("---")
            st.markdown("**Insight:**")
            total = sum(by_budget.values())
            if total > 0:
                mid_high = by_budget.get("medium", 0) + by_budget.get("high", 0)
                mid_high_pct = mid_high / total * 100
                st.info(f"{mid_high_pct:.0f}% pengguna memilih budget Standar-Nyaman (25-50 Juta)")
        else:
            st.info("Tidak ada data budget")

    with col2:
        st.markdown("#### Gaya Travel")
        # Would need to add travel style tracking
        st.info("Data gaya travel akan tersedia setelah lebih banyak registrasi")


def render_user_list():
    """Render user list table"""
    st.markdown("### Daftar Pengguna Terdaftar")

    repo = get_user_repository()

    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("Cari nama/email", placeholder="Ketik untuk mencari...")
    with col2:
        role_filter = st.selectbox("Role", ["Semua", "Free", "Premium", "Partner", "Admin"])
    with col3:
        sort_by = st.selectbox("Urutkan", ["Terbaru", "Terlama", "Nama A-Z"])

    # Get users
    if search:
        users = repo.search(search)
    else:
        users = repo.get_all(limit=100)

    # Apply filters
    if role_filter != "Semua":
        role_map = {"Free": "free", "Premium": "premium", "Partner": "partner", "Admin": "admin"}
        users = [u for u in users if u.role.value == role_map.get(role_filter)]

    # Sort
    if sort_by == "Terlama":
        users = sorted(users, key=lambda u: u.created_at)
    elif sort_by == "Nama A-Z":
        users = sorted(users, key=lambda u: u.name.lower())

    # Display count
    st.markdown(f"**Menampilkan {len(users)} pengguna**")

    if users:
        # Table header
        st.markdown("""
            <div style="display: grid; grid-template-columns: 2fr 2fr 1fr 1fr 1.5fr;
                        padding: 0.75rem; background: rgba(255,255,255,0.1);
                        border-radius: 8px; font-weight: bold; font-size: 0.85rem;">
                <div>Nama</div>
                <div>Email</div>
                <div>Role</div>
                <div>Status</div>
                <div>Bergabung</div>
            </div>
        """, unsafe_allow_html=True)

        # Table rows
        for user in users:
            role_colors = {
                UserRole.FREE: "#2196F3",
                UserRole.PREMIUM: "#FFD700",
                UserRole.PARTNER: "#9C27B0",
                UserRole.ADMIN: "#F44336"
            }
            status_colors = {
                UserStatus.ACTIVE: "#4CAF50",
                UserStatus.INACTIVE: "#9E9E9E",
                UserStatus.SUSPENDED: "#F44336",
                UserStatus.PENDING: "#FF9800"
            }

            role_color = role_colors.get(user.role, "#2196F3")
            status_color = status_colors.get(user.status, "#9E9E9E")
            join_date = user.created_at.strftime("%d %b %Y") if user.created_at else "-"

            st.markdown(f"""
                <div style="display: grid; grid-template-columns: 2fr 2fr 1fr 1fr 1.5fr;
                            padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1);
                            font-size: 0.85rem;">
                    <div>{user.name}</div>
                    <div style="color: #aaa;">{user.email}</div>
                    <div style="color: {role_color};">{user.role.display_name}</div>
                    <div style="color: {status_color};">●</div>
                    <div style="color: #b0b0b0;">{join_date}</div>
                </div>
            """, unsafe_allow_html=True)

        # Export option
        st.markdown("---")
        if st.button("Export ke CSV"):
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Nama", "Email", "Phone", "Role", "Status", "Provinsi", "Kota", "Budget", "Bergabung"])

            for user in users:
                writer.writerow([
                    user.name, user.email, user.phone or "-",
                    user.role.display_name, user.status.value,
                    user.province or "-", user.city or "-",
                    user.budget_range or "-",
                    user.created_at.strftime("%Y-%m-%d") if user.created_at else "-"
                ])

            st.download_button(
                "Download CSV",
                output.getvalue(),
                file_name=f"labbaik_users_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("Tidak ada pengguna yang ditemukan")


def render_conversion_funnel():
    """Render conversion funnel analysis"""
    st.markdown("### Funnel Konversi")

    repo = get_user_repository()
    stats = repo.get_stats()

    total = stats.get("total_users", 0)
    if total == 0:
        st.info("Belum ada data untuk funnel")
        return

    # Funnel stages
    stages = [
        ("Visitor", total * 10, "#9E9E9E"),  # Estimated visitors
        ("Registered", total, "#2196F3"),
        ("Active (7d)", stats.get("active_7d", 0), "#4CAF50"),
        ("Premium", stats.get("by_role", {}).get("premium", 0), "#FFD700")
    ]

    for i, (label, count, color) in enumerate(stages):
        width = count / stages[0][1] * 100 if stages[0][1] > 0 else 0
        conversion = count / stages[i-1][1] * 100 if i > 0 and stages[i-1][1] > 0 else 100

        st.markdown(f"""
            <div style="margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span>{label}</span>
                    <span>{count:,} ({conversion:.1f}%)</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 24px;">
                    <div style="background: {color}; width: {max(width, 5)}%;
                                height: 100%; border-radius: 8px;
                                display: flex; align-items: center; justify-content: center;">
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


__all__ = ["render_user_analytics_page"]
