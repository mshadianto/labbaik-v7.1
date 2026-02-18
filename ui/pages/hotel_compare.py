"""
LABBAIK Smart Planner - Hotel Price Comparison
===============================================
Compare hotel prices from 200+ OTAs for Makkah & Madinah.
Powered by Makcorps API.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, SKELETON_CSS, render_skeleton

# =============================================================================
# IMPORTS
# =============================================================================

try:
    from services.hotel.makcorps import (
        get_makcorps_client,
        search_umrah_hotels,
        CITY_IDS,
    )
    HAS_MAKCORPS = True
except ImportError:
    HAS_MAKCORPS = False
    logger.warning("Makcorps API not available")

# Access control imports
try:
    from services.user.access_control import Feature, has_feature_access
    from services.user.user_service import get_current_user
    HAS_ACCESS_CONTROL = True
except ImportError:
    HAS_ACCESS_CONTROL = False
    logger.warning("Access control not available")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_price_sar(price: float) -> str:
    """Format price in SAR"""
    return f"SAR {price:,.0f}"


def format_price_idr(price: float) -> str:
    """Format price in IDR"""
    return f"Rp {price:,.0f}"


def get_star_display(stars: int) -> str:
    """Get star rating display"""
    return "⭐" * stars


def get_default_dates() -> tuple:
    """Get default check-in/check-out dates (30 days from now)"""
    check_in = datetime.now() + timedelta(days=30)
    check_out = check_in + timedelta(days=5)
    return check_in.date(), check_out.date()


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_search_form() -> Optional[Dict]:
    """Render hotel search form"""

    st.markdown("### 🔍 Cari Hotel")

    col1, col2 = st.columns(2)

    with col1:
        city = st.selectbox(
            "Kota",
            options=["Makkah", "Madinah", "Jeddah"],
            index=0,
            help="Pilih kota tujuan"
        )

    with col2:
        rooms = st.number_input(
            "Jumlah Kamar",
            min_value=1,
            max_value=10,
            value=1,
            help="Jumlah kamar yang dibutuhkan"
        )

    col1, col2 = st.columns(2)

    default_checkin, default_checkout = get_default_dates()

    with col1:
        check_in = st.date_input(
            "Check-in",
            value=default_checkin,
            min_value=datetime.now().date(),
            help="Tanggal check-in"
        )

    with col2:
        check_out = st.date_input(
            "Check-out",
            value=default_checkout,
            min_value=check_in + timedelta(days=1) if check_in else default_checkout,
            help="Tanggal check-out"
        )

    col1, col2 = st.columns(2)

    with col1:
        adults = st.number_input(
            "Jumlah Dewasa",
            min_value=1,
            max_value=10,
            value=2,
            help="Jumlah tamu dewasa"
        )

    with col2:
        currency = st.selectbox(
            "Mata Uang",
            options=["SAR", "USD"],
            index=0,
            help="Mata uang harga"
        )

    # Calculate nights
    nights = (check_out - check_in).days if check_out > check_in else 1

    st.caption(f"📅 Durasi: **{nights} malam**")

    # Search button
    if st.button("🔍 Cari Hotel", type="primary", use_container_width=True):
        return {
            'city': city,
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'rooms': rooms,
            'adults': adults,
            'currency': currency,
            'nights': nights,
        }

    return None


def render_hotel_card(hotel: Dict, nights: int = 1):
    """Render a single hotel card"""

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            # Hotel name & rating
            stars = hotel.get('stars', 3)
            st.markdown(f"### {hotel.get('hotel_name', 'Unknown Hotel')}")
            st.caption(f"{get_star_display(stars)} • Rating: {hotel.get('rating', 0):.1f}/5")

            # Address
            address = hotel.get('address', '')
            if address:
                st.caption(f"📍 {address}")

        with col2:
            # Price
            price = hotel.get('price_per_night', 0)
            currency = hotel.get('currency', 'SAR')

            st.markdown(f"### {currency} {price:,.0f}")
            st.caption("per malam")

            # Total price
            total = price * nights
            st.markdown(f"**Total: {currency} {total:,.0f}**")
            st.caption(f"untuk {nights} malam")

        # Vendor comparison (PREMIUM FEATURE)
        vendors = hotel.get('vendors', [])
        if vendors:
            st.markdown("---")

            # Check if user has premium access for detailed vendor breakdown
            has_vendor_access = False
            if HAS_ACCESS_CONTROL:
                try:
                    user = get_current_user()
                    has_vendor_access = has_feature_access(user, Feature.DETAILED_PRICE_COMPARISON)
                except Exception:
                    has_vendor_access = False

            if has_vendor_access:
                # === PREMIUM USER: Full vendor comparison ===
                st.markdown("**💰 Perbandingan Harga dari 200+ OTA:**")

                vendor_cols = st.columns(min(len(vendors), 4))
                for i, vendor in enumerate(vendors[:4]):
                    with vendor_cols[i]:
                        st.markdown(f"""
                        <div style="background: #1a1a1a; padding: 0.5rem; border-radius: 8px; text-align: center;">
                            <div style="color: #b0b0b0; font-size: 0.75rem;">{vendor.get('name', 'OTA')}</div>
                            <div style="color: #d4af37; font-weight: bold;">{currency} {vendor.get('price', 0):,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # Show if more vendors available
                if len(vendors) > 4:
                    st.caption(f"+ {len(vendors) - 4} OTA lainnya tersedia")
            else:
                # === FREE USER: Show paywall for vendor comparison ===
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                            border: 1px solid #d4af37; border-radius: 10px;
                            padding: 1rem; text-align: center; margin: 0.5rem 0;">
                    <div style="color: #d4af37; font-weight: bold; margin-bottom: 0.3rem;">
                        🔐 Perbandingan Harga {len(vendors)} OTA
                    </div>
                    <div style="color: #b0b0b0; font-size: 0.8rem; margin-bottom: 0.5rem;">
                        Lihat harga dari Booking.com, Agoda, Expedia & lainnya
                    </div>
                    <div style="color: #666; font-size: 0.75rem;">
                        Upgrade ke Premium untuk akses lengkap
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Best deal indicator
        if hotel.get('vendor_name'):
            st.success(f"✅ Harga terbaik dari **{hotel.get('vendor_name')}**")


def render_hotel_list(result: Dict):
    """Render list of hotels"""

    hotels = result.get('hotels', [])
    nights = 1  # Calculate from dates

    if result.get('check_in') and result.get('check_out'):
        try:
            check_in = datetime.strptime(result['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(result['check_out'], '%Y-%m-%d')
            nights = (check_out - check_in).days
        except Exception:
            pass

    if not hotels:
        st.warning("Tidak ada hotel ditemukan untuk pencarian ini.")
        return

    # Header
    st.markdown(f"### 🏨 {len(hotels)} Hotel di {result.get('city', 'Unknown')}")

    source = result.get('source', 'unknown')
    if source == 'makcorps':
        st.success("🟢 Data real-time dari 200+ OTA")
    else:
        st.info("📊 Data demo - Hubungkan API untuk harga live")

    # Check premium access and show upgrade CTA if needed
    has_premium = False
    if HAS_ACCESS_CONTROL:
        try:
            user = get_current_user()
            has_premium = has_feature_access(user, Feature.DETAILED_PRICE_COMPARISON)
        except Exception:
            pass

    if not has_premium:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1a1a2e 0%, #0d1b2a 100%);
                    border: 1px solid #d4af37; border-radius: 8px;
                    padding: 0.8rem; margin: 0.5rem 0;">
            <span style="color: #d4af37;">✨ <strong>Tip Premium:</strong></span>
            <span style="color: #ccc; font-size: 0.9rem;">
                Upgrade untuk melihat perbandingan harga lengkap dari 200+ OTA dan temukan deal terbaik.
            </span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔓 Upgrade ke Premium", key="hotel_upgrade_cta"):
            st.session_state.current_page = "subscription"
            st.rerun()

    st.caption(f"Check-in: {result.get('check_in')} | Check-out: {result.get('check_out')} | {nights} malam")

    st.markdown("---")

    # Sort options
    col1, col2 = st.columns([2, 1])

    with col1:
        sort_by = st.selectbox(
            "Urutkan berdasarkan",
            options=["Harga Terendah", "Rating Tertinggi", "Bintang Tertinggi"],
            index=0,
            label_visibility="collapsed"
        )

    # Sort hotels
    if sort_by == "Harga Terendah":
        hotels = sorted(hotels, key=lambda x: x.get('price_per_night', 0))
    elif sort_by == "Rating Tertinggi":
        hotels = sorted(hotels, key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_by == "Bintang Tertinggi":
        hotels = sorted(hotels, key=lambda x: x.get('stars', 0), reverse=True)

    # Render hotels
    for hotel in hotels:
        render_hotel_card(hotel, nights)
        st.markdown("")


def render_api_status():
    """Render API configuration status"""

    with st.expander("⚙️ Status API", expanded=False):
        if HAS_MAKCORPS:
            client = get_makcorps_client()

            if client.is_configured:
                st.success("✅ Makcorps API terhubung")
                stats = client.get_usage_stats()
                st.caption(f"Request count: {stats['requests_made']}")
            else:
                st.warning("⚠️ API Key belum dikonfigurasi")
                st.markdown("""
                Untuk mengaktifkan data hotel real-time:
                1. Daftar di [makcorps.com](https://makcorps.com)
                2. Dapatkan API key
                3. Tambahkan ke environment variable:
                   ```
                   MAKCORPS_API_KEY=your_api_key
                   ```
                """)
        else:
            st.error("❌ Modul Makcorps tidak tersedia")


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_hotel_compare_page():
    """Main hotel comparison page"""
    try:
        from services.analytics import track_page
        track_page("hotel_compare")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, SKELETON_CSS)

    # Page header
    st.markdown("""
        <div class="page-hero">
            <h1><span aria-hidden="true">🏨 </span>Perbandingan Harga Hotel</h1>
            <div class="subtitle">Bandingkan harga hotel dari 200+ OTA untuk Makkah & Madinah</div>
        </div>
    """, unsafe_allow_html=True)

    # API Status
    render_api_status()

    st.markdown("---")

    # Search form
    col1, col2 = st.columns([1, 2])

    with col1:
        search_params = render_search_form()

    with col2:
        # Show results or placeholder
        if search_params:
            with st.spinner("Mencari hotel..."):
                result = search_umrah_hotels(
                    city=search_params['city'],
                    check_in=search_params['check_in'],
                    check_out=search_params['check_out'],
                    rooms=search_params['rooms'],
                    adults=search_params['adults'],
                    currency=search_params['currency'],
                )

                if result:
                    # Store in session for persistence
                    st.session_state['hotel_search_result'] = result
                    st.session_state['hotel_search_params'] = search_params

                    if not st.session_state.get("hotel_compare_xp_awarded"):
                        add_xp_safe(10, "Mencari perbandingan hotel")
                        st.session_state.hotel_compare_xp_awarded = True

        # Show stored results
        if 'hotel_search_result' in st.session_state:
            render_hotel_list(st.session_state['hotel_search_result'])
        else:
            # Skeleton placeholder
            render_skeleton("cards", count=3)
            st.caption("Pilih kota dan tanggal untuk melihat harga hotel")

    # Footer info
    st.markdown("---")
    st.caption("""
    💡 **Tips:** Harga dapat berubah sewaktu-waktu. Booking langsung di website hotel/OTA
    untuk harga terkini dan konfirmasi ketersediaan.
    """)

    st.markdown("---")
    if st.button("🤖 Tips Memilih Hotel Umrah", key="hotel_ai_tips"):
        with st.spinner("Menganalisis..."):
            tips = ai_complete(
                "Berikan 4 tips singkat memilih hotel untuk umrah di Makkah dan Madinah. "
                "Pertimbangkan jarak ke masjid, fasilitas, dan harga. Bahasa Indonesia.",
                system_prompt="Kamu adalah travel consultant umrah berpengalaman.",
                max_tokens=400,
            )
            if tips:
                st.markdown(f'''
                    <div class="ai-card" role="status" aria-live="polite">
                        <h4>🤖 Tips AI Memilih Hotel</h4>
                        <p>{tips}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['render_hotel_compare_page']
