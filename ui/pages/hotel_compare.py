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

# Demo hotel data for when API is unavailable
DEMO_HOTELS = [
    {"name": "Hilton Suites Makkah", "stars": 5, "distance": "350m dari Haram", "prices": {"Booking.com": "SAR 890", "Agoda": "SAR 920", "Expedia": "SAR 950"}, "amenities": "Free WiFi, free shuttle to Haram, breakfast included, air conditioning, elevator, family room, restaurant, room service, laundry, prayer room"},
    {"name": "Elaf Ajyad Hotel", "stars": 4, "distance": "500m dari Haram", "prices": {"Booking.com": "SAR 450", "Agoda": "SAR 470", "Traveloka": "SAR 440"}, "amenities": "Free WiFi, air conditioning, elevator, restaurant, 24-hour reception desk, parking available, wheelchair accessible"},
    {"name": "Al Marwa Rayhaan", "stars": 5, "distance": "200m dari Haram", "prices": {"Booking.com": "SAR 1,200", "Hotels.com": "SAR 1,250", "Expedia": "SAR 1,180"}, "amenities": "Free WiFi, free shuttle to Masjidil Haram, complimentary breakfast, family room, connecting rooms, spa, gym, pool, concierge, room service, Quran in room"},
    {"name": "Dar Al Tawhid Intercontinental", "stars": 5, "distance": "100m dari Haram", "prices": {"Booking.com": "SAR 1,800", "Agoda": "SAR 1,850"}, "amenities": "Free WiFi, free breakfast, suite available, wheelchair accessible, elevator, prayer room, minibar, safe, room service, laundry, concierge, air conditioning"},
]

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

# Amenity intelligence imports
try:
    from services.intelligence.amenities import extract_signals, get_highlight_amenities
    HAS_AMENITIES = True
except ImportError:
    HAS_AMENITIES = False
    logger.warning("Amenity intelligence not available")

# Risk score imports
try:
    from services.intelligence.risk_score import (
        get_risk_calculator,
        RiskLevel,
        format_risk_badge,
        format_risk_color,
    )
    HAS_RISK_SCORE = True
except ImportError:
    HAS_RISK_SCORE = False
    logger.warning("Risk score service not available")


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

            # Amenity highlight badges
            if HAS_AMENITIES:
                amenities_text = hotel.get('amenities', '')
                if amenities_text:
                    try:
                        signals = extract_signals(amenities_text)
                        highlights = get_highlight_amenities(signals)
                        if highlights:
                            badge_colors = {
                                "Shuttle ke Haram": "#2e7d32",
                                "Free Shuttle": "#2e7d32",
                                "Shuttle Available": "#1b5e20",
                                "Wheelchair Access": "#1565c0",
                                "Free Breakfast": "#e65100",
                                "Breakfast Available": "#bf360c",
                                "Family Room": "#6a1b9a",
                                "Free WiFi": "#00838f",
                                "Prayer Room": "#4a148c",
                            }
                            badges_html = " ".join(
                                f'<span style="display:inline-block;background:{badge_colors.get(h, "#37474f")}; '
                                f'color:#ffffff;font-size:0.7rem;padding:2px 8px;border-radius:12px; '
                                f'margin:2px 2px 2px 0;white-space:nowrap;">{h}</span>'
                                for h in highlights
                            )
                            st.markdown(
                                f'<div style="margin-top:4px;">{badges_html}</div>',
                                unsafe_allow_html=True,
                            )
                    except Exception:
                        pass  # Graceful fallback if amenity extraction fails

        with col2:
            # Price
            price = hotel.get('price_per_night', 0)
            currency = hotel.get('currency', 'SAR')

            st.markdown(f"### {currency} {price:,.0f}")
            st.caption("per malam")

            # Risk score badge (based on seasonal/urgency factors)
            if HAS_RISK_SCORE:
                search_params = st.session_state.get('hotel_search_params', {})
                check_in_str = search_params.get('check_in', '')
                if check_in_str:
                    try:
                        from datetime import date as _date_type
                        checkin_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
                        calculator = get_risk_calculator()
                        seasonal_score, seasonal_reasons = calculator.calculate_seasonal_score(checkin_date)
                        urgency_score, urgency_reasons = calculator.calculate_urgency_score(checkin_date)
                        # Combine seasonal (60%) and urgency (40%) for a simple composite
                        combined_score = int(seasonal_score * 0.6 + urgency_score * 0.4)
                        combined_score = min(100, max(0, combined_score))
                        # Determine risk level from combined score
                        if combined_score >= 81:
                            risk_level = RiskLevel.CRITICAL
                        elif combined_score >= 61:
                            risk_level = RiskLevel.HIGH
                        elif combined_score >= 31:
                            risk_level = RiskLevel.MEDIUM
                        else:
                            risk_level = RiskLevel.LOW
                        risk_color = format_risk_color(risk_level)
                        risk_text = format_risk_badge(risk_level)
                        st.markdown(
                            f'<div style="display:inline-block;background:{risk_color}; '
                            f'color:#ffffff;font-size:0.7rem;font-weight:bold;padding:3px 10px; '
                            f'border-radius:12px;margin-top:4px;">{risk_text}</div>',
                            unsafe_allow_html=True,
                        )
                    except Exception:
                        pass  # Graceful fallback if risk calculation fails

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
            if not HAS_MAKCORPS:
                # Demo data fallback
                st.markdown('''
                    <div style="background:linear-gradient(90deg,#2d1a0d,#4d3319);
                                border:2px dashed #fbbf24;border-radius:12px;
                                padding:0.75rem 1rem;margin-bottom:1rem;text-align:center;">
                        <strong style="color:#fbbf24;">DATA DEMO</strong>
                        <span style="color:#b0b0b0;font-size:0.85rem;"> — Hubungkan Makcorps API untuk harga real-time dari 200+ OTA</span>
                    </div>
                ''', unsafe_allow_html=True)
                for h in DEMO_HOTELS:
                    with st.container(border=True):
                        st.markdown(f"**{'⭐' * h['stars']} {h['name']}** — {h['distance']}")
                        price_text = " | ".join(f"{k}: **{v}**" for k, v in h["prices"].items())
                        st.markdown(price_text)
                        # Amenity badges for demo hotels
                        if HAS_AMENITIES and h.get('amenities'):
                            try:
                                demo_signals = extract_signals(h['amenities'])
                                demo_highlights = get_highlight_amenities(demo_signals)
                                if demo_highlights:
                                    demo_badge_colors = {
                                        "Shuttle ke Haram": "#2e7d32",
                                        "Free Shuttle": "#2e7d32",
                                        "Shuttle Available": "#1b5e20",
                                        "Wheelchair Access": "#1565c0",
                                        "Free Breakfast": "#e65100",
                                        "Breakfast Available": "#bf360c",
                                        "Family Room": "#6a1b9a",
                                        "Free WiFi": "#00838f",
                                        "Prayer Room": "#4a148c",
                                    }
                                    demo_badges_html = " ".join(
                                        f'<span style="display:inline-block;background:{demo_badge_colors.get(hl, "#37474f")}; '
                                        f'color:#ffffff;font-size:0.7rem;padding:2px 8px;border-radius:12px; '
                                        f'margin:2px 2px 2px 0;white-space:nowrap;">{hl}</span>'
                                        for hl in demo_highlights
                                    )
                                    st.markdown(
                                        f'<div style="margin-top:4px;">{demo_badges_html}</div>',
                                        unsafe_allow_html=True,
                                    )
                            except Exception:
                                pass
            else:
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
