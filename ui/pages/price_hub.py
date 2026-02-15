"""
================================================================================
LABBAIK AI - PUSAT PERBANDINGAN HARGA (Price Hub)
================================================================================
Lokasi: ui/pages/price_hub.py
Fitur: Unified price comparison hub combining:
       - Hotel comparison from 200+ OTAs (Makcorps)
       - Multi-source aggregation for flights & packages
       - AI price analysis & recommendations
       - Gamification XP rewards
================================================================================
"""

import streamlit as st
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any
import logging
import re

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

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
# PAGE-SPECIFIC CSS
# =============================================================================

PRICE_HUB_CSS = """
/* Price Hub hero overrides */
.price-hub-hero {
    --hero-bg: linear-gradient(135deg, #1a1a2e 0%, #2d1a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
}

/* Vendor comparison chip */
.vendor-chip {
    background: #1a1a1a;
    padding: 0.5rem;
    border-radius: 8px;
    text-align: center;
}

.vendor-chip .vendor-name {
    color: #888;
    font-size: 0.75rem;
}

.vendor-chip .vendor-price {
    color: #d4af37;
    font-weight: bold;
}

/* Source badge */
.source-badge {
    display: inline-block;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
}

/* Empty state placeholder for tabs */
.tab-empty {
    background: #1a1a1a;
    border: 1px dashed #333;
    border-radius: 15px;
    padding: 3rem;
    text-align: center;
}

.tab-empty .tab-empty-icon {
    font-size: 3rem;
}

.tab-empty h3 {
    color: #d4af37;
}

.tab-empty p {
    color: #888;
}

/* AI analysis section */
.ai-analysis-section {
    margin-top: 1.5rem;
}
"""


# =============================================================================
# CONSTANTS
# =============================================================================

SAR_TO_IDR = 4200

SOURCE_BADGES = {
    "amadeus": ("API", "#4CAF50"),
    "xotelo": ("API", "#4CAF50"),
    "makcorps": ("Makcorps", "#2196F3"),
    "booking": ("n8n", "#673AB7"),
    "aviationstack": ("n8n", "#673AB7"),
    "cheria-travel": ("Travel", "#FF9800"),
    "alhijaz": ("Travel", "#FF9800"),
    "patuna": ("Travel", "#FF9800"),
    "maktour": ("Travel", "#FF9800"),
    "arminareka": ("Travel", "#FF9800"),
    "traveloka": ("OTA", "#2196F3"),
    "tiket": ("OTA", "#2196F3"),
    "partner": ("Partner", "#FF9800"),
    "demo": ("Demo", "#9E9E9E"),
    "n8n": ("n8n", "#673AB7"),
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
    return "* " * min(stars, 5)


def get_source_badge(source_name: str) -> tuple:
    """Get badge label and color for source."""
    return SOURCE_BADGES.get(source_name.lower(), ("Unknown", "#757575"))


def get_default_dates() -> tuple:
    """Get default check-in/check-out dates (30 days from now)."""
    check_in = datetime.now() + timedelta(days=30)
    check_out = check_in + timedelta(days=5)
    return check_in.date(), check_out.date()


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
            line = f"&bull; {line[2:]}"
        # Numbered lists
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            num = match.group(1)
            rest = line[match.end():]
            line = f"<strong>{num}.</strong> {rest}"
        html_lines.append(f"<div style='margin-bottom:0.3rem;'>{line}</div>")

    return "\n".join(html_lines)


def init_session_state():
    """Initialize price hub session state."""
    if "price_hub_hotel_result" not in st.session_state:
        st.session_state.price_hub_hotel_result = None
    if "price_hub_search_params" not in st.session_state:
        st.session_state.price_hub_search_params = {}
    if "price_hub_compare_xp_awarded" not in st.session_state:
        st.session_state.price_hub_compare_xp_awarded = False
    if "price_hub_ai_xp_awarded" not in st.session_state:
        st.session_state.price_hub_ai_xp_awarded = False


# =============================================================================
# AI ANALYSIS SECTION
# =============================================================================

def _build_hotel_summary(result: Dict) -> str:
    """Build a text summary of hotel results for AI analysis."""
    hotels = result.get("hotels", [])
    if not hotels:
        return ""
    city = result.get("city", "Unknown")
    check_in = result.get("check_in", "")
    check_out = result.get("check_out", "")
    currency = hotels[0].get("currency", "SAR") if hotels else "SAR"

    lines = [
        f"Kota: {city}",
        f"Check-in: {check_in}, Check-out: {check_out}",
        f"Jumlah hotel ditemukan: {len(hotels)}",
        "",
    ]
    for i, h in enumerate(hotels[:10]):
        name = h.get("hotel_name", "Unknown")
        price = h.get("price_per_night", 0)
        stars = h.get("stars", 0)
        rating = h.get("rating", 0)
        vendor_count = len(h.get("vendors", []))
        lines.append(
            f"{i+1}. {name} - {stars} bintang - Rating {rating:.1f} - "
            f"{currency} {price:,.0f}/malam - {vendor_count} OTA"
        )
    return "\n".join(lines)


def render_ai_analysis(result: Dict):
    """Render AI price analysis section for hotel results."""
    st.markdown("---")
    st.markdown("### Analisis Harga AI")

    summary = _build_hotel_summary(result)
    if not summary:
        st.info("Tidak ada data hotel untuk dianalisis.")
        return

    if st.button("Analisis dengan AI", type="secondary", key="btn_ai_analysis"):
        with st.spinner("AI sedang menganalisis harga..."):
            prompt_text = (
                f"Analisis data perbandingan harga hotel umrah berikut dan berikan "
                f"rekomendasi hotel terbaik berdasarkan value for money:\n\n"
                f"{summary}\n\n"
                f"Berikan:\n"
                f"1. Rekomendasi hotel terbaik (best value)\n"
                f"2. Tips mendapatkan harga terbaik\n"
                f"3. Waktu terbaik untuk booking\n"
                f"4. Perbandingan singkat hotel teratas\n"
                f"Jawab dalam bahasa Indonesia, singkat dan praktis."
            )

            system_prompt = (
                "Kamu adalah konsultan harga Umrah berpengalaman yang membantu "
                "jamaah mendapatkan harga terbaik."
            )

            response = ai_complete(
                prompt_text,
                system_prompt=system_prompt,
                max_tokens=800,
            )

            if response:
                ai_html = _markdown_to_html_simple(response)
                card_html = (
                    f'<div class="ai-card">'
                    f'<h4>Rekomendasi AI</h4>'
                    f'<p>{ai_html}</p>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                # Gamification: +20 XP for AI analysis (first time)
                if not st.session_state.get("price_hub_ai_xp_awarded", False):
                    st.session_state.price_hub_ai_xp_awarded = True
                    add_xp_safe(20, "Menggunakan AI analisis harga umrah")
            else:
                _render_ai_fallback(result)
    else:
        st.caption(
            "Klik tombol di atas untuk mendapatkan analisis dan rekomendasi "
            "harga dari AI berdasarkan hasil pencarian."
        )


def _render_ai_fallback(result: Dict):
    """Render fallback tips when AI is unavailable."""
    hotels = result.get("hotels", [])
    city = result.get("city", "Unknown")

    tips = []
    if hotels:
        prices = [h.get("price_per_night", 0) for h in hotels if h.get("price_per_night", 0) > 0]
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            currency = hotels[0].get("currency", "SAR")
            tips.append(
                f"<strong>Range harga di {city}:</strong> "
                f"{currency} {min_price:,.0f} - {currency} {max_price:,.0f} "
                f"(rata-rata {currency} {avg_price:,.0f})/malam"
            )

    tips.append(
        "<strong>Tips:</strong> Booking 2-3 bulan sebelum keberangkatan "
        "biasanya mendapatkan harga lebih baik."
    )
    tips.append(
        "<strong>Tips:</strong> Bandingkan harga di beberapa OTA sebelum "
        "booking. Harga bisa berbeda signifikan antar platform."
    )
    tips.append(
        "<strong>Tips:</strong> Hotel bintang 4 yang sedikit lebih jauh dari "
        "Masjidil Haram sering menawarkan value lebih baik daripada hotel "
        "bintang 3 yang sangat dekat."
    )

    tip_items = "".join(
        f'<div style="margin-bottom:0.5rem;">&bull; {t}</div>' for t in tips
    )
    fallback_html = (
        f'<div class="ai-card">'
        f'<h4>Tips Harga Umrah</h4>'
        f'<p>{tip_items}</p>'
        f'</div>'
    )
    st.markdown(fallback_html, unsafe_allow_html=True)


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
    st.caption(f"Durasi: **{nights} malam**")

    if st.button("Cari Hotel", type="primary", use_container_width=True, key="search_hotel"):
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
            star_text = get_star_display(stars)
            rating_val = hotel.get('rating', 0)
            st.caption(f"{star_text} Rating: {rating_val:.1f}/5")

            address = hotel.get('address', '')
            if address:
                truncated = address[:50]
                st.caption(f"{truncated}...")

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
                st.markdown(f"**Perbandingan dari {len(vendors)} OTA:**")

                vendor_cols = st.columns(min(len(vendors), 4))
                for i, vendor in enumerate(vendors[:4]):
                    with vendor_cols[i]:
                        v_name = vendor.get('name', 'OTA')
                        v_price = vendor.get('price', 0)
                        chip_html = (
                            f'<div class="vendor-chip">'
                            f'<div class="vendor-name">{v_name}</div>'
                            f'<div class="vendor-price">{currency} {v_price:,.0f}</div>'
                            f'</div>'
                        )
                        st.markdown(chip_html, unsafe_allow_html=True)

                if len(vendors) > 4:
                    remaining = len(vendors) - 4
                    st.caption(f"+ {remaining} OTA lainnya")
            else:
                st.info(f"Upgrade Premium untuk lihat {len(vendors)} OTA")

        if hotel.get('vendor_name'):
            best_vendor = hotel.get('vendor_name')
            st.success(f"Harga terbaik dari **{best_vendor}**")


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
    hotel_count = len(hotels)
    city_name = result.get('city', 'Unknown')
    st.markdown(f"### {hotel_count} Hotel di {city_name}")

    source = result.get('source', 'unknown')
    if source == 'makcorps':
        st.success("Data real-time dari 200+ OTA")
    else:
        st.info("Data dari aggregator")

    ci = result.get('check_in')
    co = result.get('check_out')
    st.caption(f"Check-in: {ci} | Check-out: {co} | {nights} malam")

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

    # Gamification: +25 XP for comparing prices (first time)
    if not st.session_state.get("price_hub_compare_xp_awarded", False):
        st.session_state.price_hub_compare_xp_awarded = True
        add_xp_safe(25, "Membandingkan harga hotel umrah")

    # AI Analysis section
    render_ai_analysis(result)


def render_hotel_tab():
    """Render hotel comparison tab."""

    st.markdown("### Cari Hotel")
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
                    st.warning("Makcorps API tidak tersedia")

        if st.session_state.get('price_hub_hotel_result'):
            render_hotel_results(st.session_state.price_hub_hotel_result)
        else:
            empty_html = (
                '<div class="tab-empty">'
                '<div class="tab-empty-icon">&#127976;</div>'
                '<h3>Cari Hotel Terbaik</h3>'
                '<p>Pilih kota dan tanggal untuk melihat perbandingan harga</p>'
                '</div>'
            )
            st.markdown(empty_html, unsafe_allow_html=True)


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
                details.append(f"Dari {flight.departure_city}")
            if flight.city:
                details.append(f"Ke {flight.city}")
            if flight.airline:
                details.append(f"{flight.airline}")

            st.caption(" | ".join(details) if details else "")

            if flight.check_in_date:
                st.caption(f"{flight.check_in_date}")

        with col2:
            badge_label, badge_color = get_source_badge(flight.source_name)
            badge_html = (
                f'<span class="source-badge" style="background-color:{badge_color};">'
                f'{badge_label}</span>'
            )
            st.markdown(badge_html, unsafe_allow_html=True)

            if flight.inclusions:
                inc_text = ", ".join(flight.inclusions[:2])
                st.caption(f"{inc_text}")

        with col3:
            if is_best:
                st.markdown(f"### {format_price_idr(flight.price_idr)}")
                st.caption("Harga Terbaik!")
            else:
                st.markdown(f"### {format_price_idr(flight.price_idr)}")

            if not flight.is_available:
                st.error("Sold Out")


def render_flight_tab():
    """Render flight comparison tab."""

    st.markdown("### Penerbangan ke Tanah Suci")
    st.caption("Data dari berbagai sumber: API, n8n, dan Travel Agent")

    if not HAS_AGGREGATOR:
        st.warning("Price aggregator tidak tersedia")
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

    if st.button("Cari Penerbangan", type="primary", use_container_width=True, key="search_flight"):
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

                    # Gamification: +25 XP for comparing prices (first time)
                    if not st.session_state.get("price_hub_compare_xp_awarded", False):
                        st.session_state.price_hub_compare_xp_awarded = True
                        add_xp_safe(25, "Membandingkan harga penerbangan umrah")
                else:
                    st.info("Tidak ada penerbangan ditemukan")

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        empty_html = (
            '<div class="tab-empty">'
            '<div class="tab-empty-icon">&#9992;</div>'
            '<h3>Cari Penerbangan</h3>'
            '<p>Pilih kota asal dan tujuan untuk melihat harga</p>'
            '</div>'
        )
        st.markdown(empty_html, unsafe_allow_html=True)


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
                details.append(f"{pkg.duration_days} Hari")
            if pkg.departure_city:
                details.append(f"dari {pkg.departure_city}")
            if pkg.airline:
                details.append(f"{pkg.airline}")

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
            badge_html = (
                f'<span class="source-badge" style="background-color:{badge_color};">'
                f'{badge_label}</span>'
            )
            st.markdown(badge_html, unsafe_allow_html=True)

            if pkg.inclusions:
                inc_text = ", ".join(pkg.inclusions[:3])
                if len(pkg.inclusions) > 3:
                    extra = len(pkg.inclusions) - 3
                    inc_text += f" +{extra}"
                st.caption(f"{inc_text}")

        with col3:
            if is_best:
                st.markdown(f"### {format_price_idr(pkg.price_idr)}")
                st.caption("Harga Terbaik!")
            else:
                st.markdown(f"### {format_price_idr(pkg.price_idr)}")

            if not pkg.is_available:
                st.error("Sold Out")
            elif pkg.quota and pkg.quota < 10:
                st.warning(f"Sisa {pkg.quota} seat!")


def render_package_tab():
    """Render package comparison tab."""

    st.markdown("### Paket Umrah")
    st.caption("Paket lengkap dari berbagai Travel Agent terpercaya")

    if not HAS_AGGREGATOR:
        st.warning("Price aggregator tidak tersedia")
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

    if st.button("Cari Paket", type="primary", use_container_width=True, key="search_pkg"):
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

                    with st.expander("Sumber Data"):
                        for src, count in source_count.items():
                            badge_label, badge_color = get_source_badge(src)
                            src_badge_html = (
                                f'<span class="source-badge" '
                                f'style="background-color:{badge_color};">'
                                f'{badge_label}</span> '
                                f'<strong>{src}</strong>: {count} paket'
                            )
                            st.markdown(src_badge_html, unsafe_allow_html=True)

                    st.markdown("---")

                    for pkg in packages:
                        render_package_card(pkg, best_price)

                    # Gamification: +25 XP for comparing prices (first time)
                    if not st.session_state.get("price_hub_compare_xp_awarded", False):
                        st.session_state.price_hub_compare_xp_awarded = True
                        add_xp_safe(25, "Membandingkan harga paket umrah")
                else:
                    st.info("Tidak ada paket ditemukan dengan kriteria tersebut")

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        empty_html = (
            '<div class="tab-empty">'
            '<div class="tab-empty-icon">&#128230;</div>'
            '<h3>Cari Paket Umrah</h3>'
            '<p>Pilih kriteria untuk melihat paket dari berbagai travel agent</p>'
            '</div>'
        )
        st.markdown(empty_html, unsafe_allow_html=True)


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

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, PRICE_HUB_CSS)

    # Header
    hero_html = (
        '<div class="page-hero price-hub-hero">'
        '<h1>Pusat Perbandingan Harga</h1>'
        '<p class="subtitle">Bandingkan harga hotel, penerbangan &amp; paket dari berbagai sumber</p>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hotel", "200+ OTA", help="Via Makcorps API")
    with col2:
        st.metric("Flight", "Multi-source", help="API, n8n, Partner")
    with col3:
        st.metric("Paket", "5+ Travel Agent", help="Cheria, Alhijaz, dll")

    st.markdown("---")

    # Main tabs
    tabs = st.tabs(["Hotel", "Penerbangan", "Paket Umrah"])

    with tabs[0]:
        render_hotel_tab()

    with tabs[1]:
        render_flight_tab()

    with tabs[2]:
        render_package_tab()

    # Footer
    st.markdown("---")
    st.caption(
        "**Catatan:** Harga bersifat estimasi dan dapat berubah sewaktu-waktu. "
        "Lakukan booking langsung di website resmi untuk konfirmasi harga dan ketersediaan."
    )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['render_price_hub_page']
