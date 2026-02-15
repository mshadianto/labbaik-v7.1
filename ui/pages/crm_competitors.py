"""
LABBAIK AI - Competitor Price Monitor
=======================================
Monitor and compare competitor prices.
"""

import streamlit as st
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

from ui.components.crm_helpers import format_rupiah


def init_session_state():
    """Initialize session state."""
    if "competitor_view" not in st.session_state:
        st.session_state.competitor_view = "list"


def render_competitor_list():
    """Render list of monitored competitors."""
    st.markdown("### Kompetitor yang Dipantau")

    try:
        from services.crm.config import get_competitors_config

        competitors = get_competitors_config().get("list", [])

        for comp in competitors:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"**{comp['name']}**")
                    st.caption(comp.get('website', '-'))

                with col2:
                    st.caption("Harga terakhir: -")

                with col3:
                    if st.button("📊 Detail", key=f"comp_{comp['name']}"):
                        st.session_state.selected_competitor = comp['name']
                        st.session_state.competitor_view = "detail"
                        st.rerun()

                st.divider()

    except Exception as e:
        logger.error(f"Failed to load competitors: {e}")


def render_add_competitor_price():
    """Add competitor price manually."""
    st.markdown("### Tambah Data Harga Kompetitor")

    with st.form("add_competitor_price"):
        col1, col2 = st.columns(2)

        with col1:
            competitor_name = st.text_input("Nama Kompetitor *", placeholder="Nama travel agent")
            competitor_url = st.text_input("Website/URL", placeholder="https://...")
            package_name = st.text_input("Nama Paket", placeholder="Paket 9 Hari Bintang 4")

        with col2:
            package_type = st.selectbox(
                "Tipe Paket",
                options=["regular", "plus", "vip"],
                format_func=lambda x: {"regular": "Regular", "plus": "Plus", "vip": "VIP"}.get(x, x)
            )
            duration_days = st.number_input("Durasi (hari)", min_value=5, max_value=30, value=9)
            price = st.number_input("Harga", min_value=0, value=25000000, step=500000)

        col1, col2 = st.columns(2)

        with col1:
            hotel_makkah = st.text_input("Hotel Makkah", placeholder="Nama hotel")

        with col2:
            hotel_madinah = st.text_input("Hotel Madinah", placeholder="Nama hotel")

        airline = st.text_input("Maskapai", placeholder="Saudia, Garuda, dll")

        source = st.selectbox(
            "Sumber Data",
            options=["website", "social", "manual"],
            format_func=lambda x: {
                "website": "Website Resmi",
                "social": "Media Sosial",
                "manual": "Input Manual"
            }.get(x, x)
        )

        submitted = st.form_submit_button("Simpan Data Harga", type="primary", use_container_width=True)

        if submitted:
            if not competitor_name or not price:
                st.error("Nama kompetitor dan harga wajib diisi!")
            else:
                try:
                    from services.crm import CRMRepository, CompetitorPrice

                    repo = CRMRepository()

                    comp_price = CompetitorPrice(
                        competitor_name=competitor_name,
                        competitor_url=competitor_url if competitor_url else None,
                        package_name=package_name if package_name else None,
                        package_type=package_type,
                        duration_days=duration_days,
                        hotel_makkah=hotel_makkah if hotel_makkah else None,
                        hotel_madinah=hotel_madinah if hotel_madinah else None,
                        airline=airline if airline else None,
                        price=price,
                        source=source,
                        scraped_at=datetime.now()
                    )

                    price_id = repo.add_competitor_price(comp_price)

                    if price_id:
                        st.success("Data harga berhasil disimpan!")
                        add_xp_safe(10, "Menambahkan data kompetitor")
                        st.rerun()
                    else:
                        st.error("Gagal menyimpan data")

                except Exception as e:
                    logger.error(f"Failed to add competitor price: {e}")
                    st.error(f"Gagal menyimpan: {str(e)}")


def render_price_comparison():
    """Render price comparison chart."""
    st.markdown("### Perbandingan Harga")

    duration_filter = st.selectbox(
        "Durasi Paket",
        options=[9, 12, 14],
        format_func=lambda x: f"{x} Hari"
    )

    try:
        from services.crm import CRMRepository
        import pandas as pd

        repo = CRMRepository()
        comparison = repo.get_price_comparison(duration_filter)

        if comparison:
            df = pd.DataFrame(comparison)
            df.columns = ["Kompetitor", "Rata-rata", "Minimum", "Maksimum"]

            # Format prices
            for col in ["Rata-rata", "Minimum", "Maksimum"]:
                df[col] = df[col].apply(lambda x: format_rupiah(int(x)))

            st.dataframe(df, use_container_width=True, hide_index=True)

            # Chart
            chart_df = pd.DataFrame(comparison)
            chart_df.columns = ["Kompetitor", "Rata-rata", "Minimum", "Maksimum"]
            st.bar_chart(chart_df.set_index("Kompetitor")["Rata-rata"])

        else:
            st.info("Belum ada data perbandingan harga")

            # Show sample data
            st.markdown("**Contoh Data Kompetitor (Demo):**")

            sample_data = [
                {"Kompetitor": "Al Hijaz", "Harga 9D": format_rupiah(28500000), "Harga 12D": format_rupiah(35000000)},
                {"Kompetitor": "Patuna", "Harga 9D": format_rupiah(27000000), "Harga 12D": format_rupiah(33500000)},
                {"Kompetitor": "Al Azhar", "Harga 9D": format_rupiah(29000000), "Harga 12D": format_rupiah(36000000)},
                {"Kompetitor": "Arminareka", "Harga 9D": format_rupiah(26500000), "Harga 12D": format_rupiah(32000000)},
            ]

            import pandas as pd
            st.dataframe(pd.DataFrame(sample_data), use_container_width=True, hide_index=True)

    except Exception as e:
        logger.error(f"Failed to load comparison: {e}")
        st.info("Tidak dapat memuat perbandingan harga")


def render_price_history():
    """Render price history."""
    st.markdown("### Riwayat Harga")

    try:
        from services.crm import CRMRepository
        import pandas as pd

        repo = CRMRepository()
        prices = repo.get_competitor_prices(limit=50)

        if prices:
            data = []
            for p in prices:
                data.append({
                    "Kompetitor": p.competitor_name,
                    "Paket": p.package_name or "-",
                    "Durasi": f"{p.duration_days}D" if p.duration_days else "-",
                    "Harga": format_rupiah(p.price),
                    "Tanggal": p.scraped_at.strftime("%d %b %Y") if p.scraped_at else "-"
                })

            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada riwayat harga. Tambahkan data harga kompetitor untuk memulai.")

    except Exception as e:
        logger.error(f"Failed to load price history: {e}")
        st.info("Tidak dapat memuat riwayat harga")


def render_market_insights():
    """Render market insights."""
    st.markdown("### Insight Pasar")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Posisi Harga Anda**")

        your_price = st.number_input("Harga Paket Anda (9D)", value=27000000, step=500000)

        # Compare with market
        market_avg = 28000000  # Demo value

        diff = your_price - market_avg
        diff_percent = (diff / market_avg) * 100

        if diff < 0:
            st.success(f"Harga Anda **{abs(diff_percent):.1f}% lebih murah** dari rata-rata pasar")
        elif diff > 0:
            st.warning(f"Harga Anda **{diff_percent:.1f}% lebih mahal** dari rata-rata pasar")
        else:
            st.info("Harga Anda sesuai rata-rata pasar")

    with col2:
        st.markdown("**Rekomendasi**")

        insight = ai_complete(
            "Berikan 4 rekomendasi singkat strategi harga untuk travel umrah "
            "berdasarkan analisis kompetitor. Format: bullet points. Bahasa Indonesia.",
            system_prompt="Kamu adalah business strategist untuk industri travel umrah.",
            max_tokens=300,
        )
        if insight:
            st.markdown(f"""
                <div class="ai-card">
                    <h4>🤖 Rekomendasi AI</h4>
                    <p>{insight}</p>
                </div>
            """, unsafe_allow_html=True)
            if not st.session_state.get("crm_competitor_ai_xp"):
                st.session_state.crm_competitor_ai_xp = True
                add_xp_safe(10, "Menggunakan AI analisis kompetitor")
        else:
            st.markdown("""
            - Pantau harga kompetitor secara berkala
            - Sesuaikan harga saat low/high season
            - Tawarkan value lebih, bukan hanya harga murah
            - Gunakan data untuk negosiasi dengan supplier
            """)


def render_crm_competitors_page():
    """Main competitor monitor page."""
    try:
        from services.analytics import track_page
        track_page("crm_competitors")
    except:
        pass

    init_session_state()

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    st.markdown("""
        <div class="page-hero">
            <h1>📈 Monitor Harga Kompetitor</h1>
            <div class="subtitle">Pantau dan bandingkan harga paket umrah kompetitor</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Perbandingan", "➕ Tambah Data", "📋 Riwayat", "💡 Insight"])

    with tab1:
        render_price_comparison()

    with tab2:
        render_add_competitor_price()

    with tab3:
        render_price_history()

    with tab4:
        render_market_insights()


__all__ = ["render_crm_competitors_page"]
