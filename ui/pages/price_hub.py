"""
LABBAIK Smart Planner - Pusat Perbandingan Harga
=================================================
Unified price comparison hub combining:
- Hotel comparison from 200+ OTAs (Makcorps)
- Multi-source aggregation for flights & packages
"""

import streamlit as st
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# IMPORTS - Services
# =============================================================================

# Makcorps Hotel API
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

# Price Aggregation
try:
    from services.price_aggregation import (
        get_price_aggregator,
        AggregatedOffer,
        SourceType,
        OfferType,
    )
    HAS_AGGREGATOR = True
except ImportError:
    HAS_AGGREGATOR = False
    logger.warning("Price aggregator not available")

# Data Manager
try:
    from services.umrah import get_umrah_data_manager
    HAS_DATA_MANAGER = True
except ImportError:
    HAS_DATA_MANAGER = False

# Access Control
try:
    from services.user.access_control import Feature, has_feature_access
    from services.user.user_service import get_current_user
    HAS_ACCESS_CONTROL = True
except ImportError:
    HAS_ACCESS_CONTROL = False

# Analytics
try:
    from services.analytics import track_page
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False
    def track_page(page): pass


# =============================================================================
# CONSTANTS
# =============================================================================

SAR_TO_IDR = 4200

SOURCE_BADGES = {
    "amadeus": ("🌐 API", "#4CAF50"),
    "xotelo": ("🌐 API", "#4CAF50"),
    "makcorps": ("🏨 Makcorps", "#2196F3"),
    "booking": ("🏨 n8n", "#673AB7"),
    "aviationstack": ("✈️ n8n", "#673AB7"),
    "cheria-travel": ("🤝 Travel", "#FF9800"),
    "alhijaz": ("🤝 Travel", "#FF9800"),
    "patuna": ("🤝 Travel", "#FF9800"),
    "maktour": ("🤝 Travel", "#FF9800"),
    "arminareka": ("🤝 Travel", "#FF9800"),
    "traveloka": ("🛒 OTA", "#2196F3"),
    "tiket": ("🛒 OTA", "#2196F3"),
    "partner": ("🤝 Partner", "#FF9800"),
    "demo": ("📋 Demo", "#9E9E9E"),
    "n8n": ("⚡ n8n", "#673AB7"),
}

CITIES = ["Makkah", "Madinah", "Jeddah"]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_price_sar(price: float) -> str:
    """Format price in SAR."""
    return f"SAR {price:,.0f}"


def format_price_idr(price: float) -> str:
    """Format price in IDR."""
    return f"Rp {price:,.0f}"


def get_star_display(stars: int) -> str:
    """Get star rating display."""
    if not stars:
        return ""
    return "⭐" * min(stars, 5)


def get_source_badge(source_name: str) -> tuple:
    """Get badge label and color for source."""
    return SOURCE_BADGES.get(source_name.lower(), ("❓ Unknown", "#757575"))


def get_default_dates() -> tuple:
    """Get default check-in/check-out dates (30 days from now)."""
    check_in = datetime.now() + timedelta(days=30)
    check_out = check_in + timedelta(days=5)
    return check_in.date(), check_out.date()


def init_session_state():
    """Initialize price hub session state."""
    if "price_hub_hotel_result" not in st.session_state:
        st.session_state.price_hub_hotel_result = None
    if "price_hub_search_params" not in st.session_state:
        st.session_state.price_hub_search_params = {}


# =============================================================================
# HOTEL TAB COMPONENTS
# =============================================================================

def render_hotel_search_form() -> Optional[Dict]:
    """Render hotel search form."""

    col1, col2 = st.columns(2)

    with col1:
        city = st.selectbox(
            "Kota",
            options=CITIES,
            index=0,
            help="Pilih kota tujuan",
            key="hotel_city"
        )

    with col2:
        rooms = st.number_input(
            "Jumlah Kamar",
            min_value=1,
            max_value=10,
            value=1,
            help="Jumlah kamar",
            key="hotel_rooms"
        )

    col1, col2 = st.columns(2)
    default_checkin, default_checkout = get_default_dates()

    with col1:
        check_in = st.date_input(
            "Check-in",
            value=default_checkin,
            min_value=datetime.now().date(),
            key="hotel_checkin"
        )

    with col2:
        check_out = st.date_input(
            "Check-out",
            value=default_checkout,
            min_value=check_in + timedelta(days=1) if check_in else default_checkout,
            key="hotel_checkout"
        )

    col1, col2 = st.columns(2)

    with col1:
        adults = st.number_input(
            "Tamu Dewasa",
            min_value=1,
            max_value=10,
            value=2,
            key="hotel_adults"
        )

    with col2:
        currency = st.selectbox(
            "Mata Uang",
            options=["SAR", "USD"],
            index=0,
            key="hotel_currency"
        )

    nights = (check_out - check_in).days if check_out > check_in else 1
    st.caption(f"📅 Durasi: **{nights} malam**")

    if st.button("🔍 Cari Hotel", type="primary", use_container_width=True, key="search_hotel"):
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


def render_hotel_card(hotel: Dict, nights: int = 1, show_vendors: bool = True):
    """Render a single hotel card with vendor comparison."""

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            stars = hotel.get('stars', 3)
            st.markdown(f"### {hotel.get('hotel_name', 'Unknown Hotel')}")
            st.caption(f"{get_star_display(stars)} • Rating: {hotel.get('rating', 0):.1f}/5")

            address = hotel.get('address', '')
            if address:
                st.caption(f"📍 {address[:50]}...")

        with col2:
            price = hotel.get('price_per_night', 0)
            currency = hotel.get('currency', 'SAR')

            st.markdown(f"### {currency} {price:,.0f}")
            st.caption("per malam")

            total = price * nights
            st.markdown(f"**Total: {currency} {total:,.0f}**")
            st.caption(f"untuk {nights} malam")

        # Vendor comparison
        vendors = hotel.get('vendors', [])
        if vendors and show_vendors:
            st.markdown("---")

            # Check premium access
            has_vendor_access = True
            if HAS_ACCESS_CONTROL:
                try:
                    user = get_current_user()
                    has_vendor_access = has_feature_access(user, Feature.DETAILED_PRICE_COMPARISON)
                except:
                    has_vendor_access = True  # Default to show

            if has_vendor_access:
                st.markdown(f"**💰 Perbandingan dari {len(vendors)} OTA:**")

                vendor_cols = st.columns(min(len(vendors), 4))
                for i, vendor in enumerate(vendors[:4]):
                    with vendor_cols[i]:
                        st.markdown(f"""
                        <div style="background: #1a1a1a; padding: 0.5rem; border-radius: 8px; text-align: center;">
                            <div style="color: #888; font-size: 0.75rem;">{vendor.get('name', 'OTA')}</div>
                            <div style="color: #d4af37; font-weight: bold;">{currency} {vendor.get('price', 0):,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                if len(vendors) > 4:
                    st.caption(f"+ {len(vendors) - 4} OTA lainnya")
            else:
                st.info(f"🔐 Upgrade Premium untuk lihat {len(vendors)} OTA")

        if hotel.get('vendor_name'):
            st.success(f"✅ Harga terbaik dari **{hotel.get('vendor_name')}**")


def render_hotel_results(result: Dict):
    """Render hotel search results."""

    hotels = result.get('hotels', [])
    nights = 1

    if result.get('check_in') and result.get('check_out'):
        try:
            check_in = datetime.strptime(result['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(result['check_out'], '%Y-%m-%d')
            nights = (check_out - check_in).days
        except:
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
        st.info("📊 Data dari aggregator")

    st.caption(f"Check-in: {result.get('check_in')} | Check-out: {result.get('check_out')} | {nights} malam")

    # Sort options
    sort_by = st.selectbox(
        "Urutkan",
        options=["Harga Terendah", "Rating Tertinggi", "Bintang Tertinggi"],
        index=0,
        key="hotel_sort",
        label_visibility="collapsed"
    )

    if sort_by == "Harga Terendah":
        hotels = sorted(hotels, key=lambda x: x.get('price_per_night', 0))
    elif sort_by == "Rating Tertinggi":
        hotels = sorted(hotels, key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_by == "Bintang Tertinggi":
        hotels = sorted(hotels, key=lambda x: x.get('stars', 0), reverse=True)

    st.markdown("---")

    for hotel in hotels:
        render_hotel_card(hotel, nights)


def render_hotel_tab():
    """Render hotel comparison tab."""

    st.markdown("### 🔍 Cari Hotel")
    st.caption("Bandingkan harga dari 200+ OTA seperti Booking.com, Agoda, Expedia, dll")

    col1, col2 = st.columns([1, 2])

    with col1:
        search_params = render_hotel_search_form()

    with col2:
        if search_params:
            with st.spinner("Mencari hotel dari 200+ OTA..."):
                if HAS_MAKCORPS:
                    result = search_umrah_hotels(
                        city=search_params['city'],
                        check_in=search_params['check_in'],
                        check_out=search_params['check_out'],
                        rooms=search_params['rooms'],
                        adults=search_params['adults'],
                        currency=search_params['currency'],
                    )
                    if result:
                        st.session_state.price_hub_hotel_result = result
                        st.session_state.price_hub_search_params = search_params
                else:
                    st.warning("⚠️ Makcorps API tidak tersedia")

        if st.session_state.get('price_hub_hotel_result'):
            render_hotel_results(st.session_state.price_hub_hotel_result)
        else:
            st.markdown("""
            <div style="background: #1a1a1a; border: 1px dashed #333; border-radius: 15px;
                        padding: 3rem; text-align: center;">
                <div style="font-size: 3rem;">🏨</div>
                <h3 style="color: #d4af37;">Cari Hotel Terbaik</h3>
                <p style="color: #888;">Pilih kota dan tanggal untuk melihat perbandingan harga</p>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# FLIGHT TAB COMPONENTS
# =============================================================================

def render_flight_card(flight: Any, best_price: float = 0):
    """Render flight offer card."""

    is_best = flight.price_idr == best_price and best_price > 0

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.markdown(f"**{flight.name}**")

            details = []
            if flight.departure_city:
                details.append(f"🛫 {flight.departure_city}")
            if flight.city:
                details.append(f"🛬 {flight.city}")
            if flight.airline:
                details.append(f"✈️ {flight.airline}")

            st.caption(" | ".join(details) if details else "")

            if flight.check_in_date:
                st.caption(f"📅 {flight.check_in_date}")

        with col2:
            badge_label, badge_color = get_source_badge(flight.source_name)
            st.markdown(
                f"<span style='background-color:{badge_color};color:white;"
                f"padding:2px 8px;border-radius:4px;font-size:11px;'>{badge_label}</span>",
                unsafe_allow_html=True
            )

            if flight.inclusions:
                st.caption(f"✅ {', '.join(flight.inclusions[:2])}")

        with col3:
            if is_best:
                st.markdown(f"### 🏆 {format_price_idr(flight.price_idr)}")
                st.caption("Harga Terbaik!")
            else:
                st.markdown(f"### {format_price_idr(flight.price_idr)}")

            if not flight.is_available:
                st.error("Sold Out")


def render_flight_tab():
    """Render flight comparison tab."""

    st.markdown("### ✈️ Penerbangan ke Tanah Suci")
    st.caption("Data dari berbagai sumber: API, n8n, dan Travel Agent")

    if not HAS_AGGREGATOR:
        st.warning("⚠️ Price aggregator tidak tersedia")
        return

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        origin = st.selectbox(
            "Kota Asal",
            options=["Jakarta", "Surabaya", "Medan", "Makassar", "Bandung"],
            key="flight_origin"
        )

    with col2:
        destination = st.selectbox(
            "Tujuan",
            options=["Jeddah", "Madinah"],
            key="flight_dest"
        )

    with col3:
        min_price_m = st.number_input("Min Harga (Juta)", value=10, min_value=0, key="flight_min")

    if st.button("🔍 Cari Penerbangan", type="primary", use_container_width=True, key="search_flight"):
        with st.spinner("Mengambil data penerbangan..."):
            try:
                aggregator = get_price_aggregator()

                result = aggregator.aggregate(
                    city=destination,
                    offer_type="flight",
                    min_price=min_price_m * 1_000_000,
                    sort_by="price",
                    limit=20
                )

                flights = result.get('offers', [])

                if flights:
                    best_price = min(f.price_idr for f in flights if f.price_idr > 0)

                    st.markdown(f"### {len(flights)} Penerbangan Ditemukan")

                    for flight in flights:
                        render_flight_card(flight, best_price)
                else:
                    st.info("Tidak ada penerbangan ditemukan")

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.markdown("""
        <div style="background: #1a1a1a; border: 1px dashed #333; border-radius: 15px;
                    padding: 3rem; text-align: center;">
            <div style="font-size: 3rem;">✈️</div>
            <h3 style="color: #d4af37;">Cari Penerbangan</h3>
            <p style="color: #888;">Pilih kota asal dan tujuan untuk melihat harga</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# PACKAGE TAB COMPONENTS
# =============================================================================

def render_package_card(pkg: Any, best_price: float = 0):
    """Render package offer card."""

    is_best = pkg.price_idr == best_price and best_price > 0

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.markdown(f"**{pkg.name}**")

            details = []
            if pkg.duration_days:
                details.append(f"📅 {pkg.duration_days} Hari")
            if pkg.departure_city:
                details.append(f"✈️ dari {pkg.departure_city}")
            if pkg.airline:
                details.append(f"🛫 {pkg.airline}")

            st.caption(" | ".join(details) if details else "")

            # Hotels
            hotel_info = []
            if pkg.hotel_makkah:
                stars = get_star_display(pkg.hotel_makkah_stars or 4)
                hotel_info.append(f"Makkah: {pkg.hotel_makkah} {stars}")
            if pkg.hotel_madinah:
                stars = get_star_display(pkg.hotel_madinah_stars or 4)
                hotel_info.append(f"Madinah: {pkg.hotel_madinah} {stars}")

            if hotel_info:
                st.caption(" | ".join(hotel_info))

        with col2:
            badge_label, badge_color = get_source_badge(pkg.source_name)
            st.markdown(
                f"<span style='background-color:{badge_color};color:white;"
                f"padding:2px 8px;border-radius:4px;font-size:11px;'>{badge_label}</span>",
                unsafe_allow_html=True
            )

            if pkg.inclusions:
                inc_text = ", ".join(pkg.inclusions[:3])
                if len(pkg.inclusions) > 3:
                    inc_text += f" +{len(pkg.inclusions) - 3}"
                st.caption(f"✅ {inc_text}")

        with col3:
            if is_best:
                st.markdown(f"### 🏆 {format_price_idr(pkg.price_idr)}")
                st.caption("Harga Terbaik!")
            else:
                st.markdown(f"### {format_price_idr(pkg.price_idr)}")

            if not pkg.is_available:
                st.error("Sold Out")
            elif pkg.quota and pkg.quota < 10:
                st.warning(f"Sisa {pkg.quota} seat!")


def render_package_tab():
    """Render package comparison tab."""

    st.markdown("### 📦 Paket Umrah")
    st.caption("Paket lengkap dari berbagai Travel Agent terpercaya")

    if not HAS_AGGREGATOR:
        st.warning("⚠️ Price aggregator tidak tersedia")
        return

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        departure = st.selectbox(
            "Berangkat dari",
            options=["Jakarta", "Surabaya", "Medan", "Makassar", "Bandung", "Semua"],
            key="pkg_departure"
        )

    with col2:
        min_stars = st.slider("Min Bintang Hotel", 3, 5, 4, key="pkg_stars")

    with col3:
        price_range = st.selectbox(
            "Range Harga",
            options=["Semua", "< 30 Juta", "30-50 Juta", "> 50 Juta"],
            key="pkg_price"
        )

    # Parse price range
    min_price = 0
    max_price = None
    if price_range == "< 30 Juta":
        max_price = 30_000_000
    elif price_range == "30-50 Juta":
        min_price = 30_000_000
        max_price = 50_000_000
    elif price_range == "> 50 Juta":
        min_price = 50_000_000

    if st.button("🔍 Cari Paket", type="primary", use_container_width=True, key="search_pkg"):
        with st.spinner("Mengambil data paket..."):
            try:
                aggregator = get_price_aggregator()

                result = aggregator.aggregate(
                    offer_type="package",
                    min_price=min_price,
                    max_price=max_price,
                    min_stars=min_stars,
                    sort_by="price",
                    limit=20
                )

                packages = result.get('offers', [])

                # Filter by departure if specified
                if departure != "Semua":
                    packages = [p for p in packages if departure.lower() in (p.departure_city or "").lower()]

                if packages:
                    best_price = min(p.price_idr for p in packages if p.price_idr > 0)

                    st.markdown(f"### {len(packages)} Paket Ditemukan")

                    # Source stats
                    source_count = {}
                    for p in packages:
                        src = p.source_name
                        source_count[src] = source_count.get(src, 0) + 1

                    with st.expander("📊 Sumber Data"):
                        for src, count in source_count.items():
                            badge_label, badge_color = get_source_badge(src)
                            st.markdown(
                                f"<span style='background-color:{badge_color};color:white;"
                                f"padding:2px 6px;border-radius:4px;font-size:11px;'>{badge_label}</span> "
                                f"**{src}**: {count} paket",
                                unsafe_allow_html=True
                            )

                    st.markdown("---")

                    for pkg in packages:
                        render_package_card(pkg, best_price)
                else:
                    st.info("Tidak ada paket ditemukan dengan kriteria tersebut")

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.markdown("""
        <div style="background: #1a1a1a; border: 1px dashed #333; border-radius: 15px;
                    padding: 3rem; text-align: center;">
            <div style="font-size: 3rem;">📦</div>
            <h3 style="color: #d4af37;">Cari Paket Umrah</h3>
            <p style="color: #888;">Pilih kriteria untuk melihat paket dari berbagai travel agent</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_price_hub_page():
    """Main unified price comparison page."""

    # Track page
    if HAS_ANALYTICS:
        track_page("price_hub")

    # Initialize state
    init_session_state()

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="color: #d4af37;">💰 Pusat Perbandingan Harga</h1>
        <p style="color: #888;">Bandingkan harga hotel, penerbangan & paket dari berbagai sumber</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏨 Hotel", "200+ OTA", help="Via Makcorps API")
    with col2:
        st.metric("✈️ Flight", "Multi-source", help="API, n8n, Partner")
    with col3:
        st.metric("📦 Paket", "5+ Travel Agent", help="Cheria, Alhijaz, dll")

    st.markdown("---")

    # Main tabs
    tabs = st.tabs(["🏨 Hotel", "✈️ Penerbangan", "📦 Paket Umrah"])

    with tabs[0]:
        render_hotel_tab()

    with tabs[1]:
        render_flight_tab()

    with tabs[2]:
        render_package_tab()

    # Footer
    st.markdown("---")
    st.caption("""
    💡 **Catatan:** Harga bersifat estimasi dan dapat berubah sewaktu-waktu.
    Lakukan booking langsung di website resmi untuk konfirmasi harga dan ketersediaan.
    """)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['render_price_hub_page']
