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
# AMENITY FILTER CSS
# =============================================================================

AMENITY_FILTER_CSS = """
<style>
/* Amenity filter section */
.amenity-filter-section {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin: 0.8rem 0;
}
.amenity-filter-section h4 {
    color: #d4af37;
    font-size: 0.95rem;
    margin: 0 0 0.5rem 0;
}

/* Amenity match badge on hotel cards */
.amenity-match-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 6px 12px;
    margin-top: 6px;
}
.amenity-match-badge .match-text {
    color: #b8c5d4;
    font-size: 0.8rem;
}
.amenity-match-badge .match-text strong {
    color: #d4af37;
}

/* Amenity match progress bar */
.amenity-match-bar {
    height: 6px;
    border-radius: 3px;
    background: #2a2a4a;
    overflow: hidden;
    width: 100%;
    margin-top: 4px;
}
.amenity-match-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
}

/* Match count summary */
.amenity-match-summary {
    background: linear-gradient(90deg, #1a1a2e 0%, #0d1b2a 100%);
    border: 1px solid #d4af37;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin: 0.5rem 0;
    color: #b8c5d4;
    font-size: 0.9rem;
}
.amenity-match-summary strong {
    color: #d4af37;
}
</style>
"""

# =============================================================================
# FAVORITES CSS
# =============================================================================

FAVORITES_CSS = """
<style>
/* Favorite star toggle button */
.favorite-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 1px solid #d4af37;
    background: transparent;
    cursor: pointer;
    transition: all 0.25s ease;
    font-size: 1.1rem;
    line-height: 1;
}
.favorite-btn:hover {
    background: rgba(212, 175, 55, 0.15);
    transform: scale(1.15);
}
.favorite-btn.active {
    background: rgba(212, 175, 55, 0.2);
    border-color: #d4af37;
    animation: fav-pop 0.35s ease;
}

@keyframes fav-pop {
    0%   { transform: scale(1); }
    50%  { transform: scale(1.3); }
    100% { transform: scale(1); }
}

/* Favorites section card */
.favorites-section {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a4a 100%);
    border: 1px solid #d4af37;
    border-radius: 12px;
    padding: 1.2rem;
    margin: 1rem 0;
}
.favorites-section h3 {
    color: #d4af37;
    margin: 0 0 0.8rem 0;
    font-size: 1.1rem;
}

/* Compact favorite card */
.favorites-section .fav-card {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
}
.favorites-section .fav-card .fav-info {
    flex: 1;
    min-width: 0;
}
.favorites-section .fav-card .fav-name {
    color: #e0e0e0;
    font-weight: 600;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.favorites-section .fav-card .fav-meta {
    color: #8e9fb3;
    font-size: 0.75rem;
    margin-top: 2px;
}
.favorites-section .fav-card .fav-price {
    color: #d4af37;
    font-weight: bold;
    font-size: 0.9rem;
    white-space: nowrap;
}
.favorites-section .fav-empty {
    color: #8e9fb3;
    font-size: 0.85rem;
    text-align: center;
    padding: 1.5rem 0.5rem;
}

/* Favorites comparison table */
.favorites-compare-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 10px;
    overflow: hidden;
    margin: 1rem 0;
    font-size: 0.85rem;
}
.favorites-compare-table thead th {
    background: #1a2a4a;
    color: #d4af37;
    padding: 0.6rem 0.8rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #d4af37;
}
.favorites-compare-table tbody td {
    background: #0d1b2a;
    color: #e0e0e0;
    padding: 0.5rem 0.8rem;
    border-bottom: 1px solid #1a2a4a;
}
.favorites-compare-table tbody tr:last-child td {
    border-bottom: none;
}
.favorites-compare-table .best-price {
    color: #66bb6a;
    font-weight: bold;
}

/* Small gold star badge */
.favorite-badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    background: rgba(212, 175, 55, 0.15);
    color: #d4af37;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    border: 1px solid rgba(212, 175, 55, 0.3);
}
</style>
"""

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

def get_star_display(stars: int) -> str:
    """Get star rating display"""
    return "⭐" * stars


def get_default_dates() -> tuple:
    """Get default check-in/check-out dates (30 days from now)"""
    check_in = datetime.now() + timedelta(days=30)
    check_out = check_in + timedelta(days=5)
    return check_in.date(), check_out.date()


# =============================================================================
# AMENITY FILTER DEFINITIONS
# =============================================================================

# Maps filter key -> (label for UI, signal attribute name on AmenitySignals)
AMENITY_FILTER_OPTIONS = [
    ("shuttle", "Shuttle ke Haram", "shuttle"),
    ("wifi", "Free WiFi", "wifi"),
    ("breakfast", "Sarapan Gratis", "breakfast"),
    ("prayer_room", "Ruang Sholat", "prayer_room"),
    ("wheelchair", "Akses Kursi Roda", "wheelchair_access"),
    ("family_room", "Kamar Keluarga", "family_room"),
]


def _get_amenities_text(hotel: Dict) -> str:
    """Extract amenities text from hotel dict, handling both str and list formats."""
    amenities = hotel.get('amenities', '')
    if isinstance(amenities, list):
        return ', '.join(str(a) for a in amenities)
    return str(amenities) if amenities else ''


def _compute_amenity_match(hotel: Dict, active_filters: List[str]) -> tuple:
    """
    Compute amenity match for a hotel against active filters.

    Returns:
        (matched_count, total_filters, matched_names, signals)
    """
    if not HAS_AMENITIES or not active_filters:
        return (0, 0, [], None)

    amenities_text = _get_amenities_text(hotel)
    if not amenities_text:
        return (0, len(active_filters), [], None)

    try:
        signals = extract_signals(amenities_text)
    except Exception:
        return (0, len(active_filters), [], None)

    # Map filter keys to signal attribute names
    filter_to_attr = {f[0]: f[2] for f in AMENITY_FILTER_OPTIONS}

    matched = []
    for fkey in active_filters:
        attr_name = filter_to_attr.get(fkey, fkey)
        if getattr(signals, attr_name, False):
            matched.append(fkey)

    return (len(matched), len(active_filters), matched, signals)


# =============================================================================
# FAVORITES HELPERS
# =============================================================================

MAX_FAVORITES = 10


def _init_favorites():
    """Ensure hotel_favorites list exists in session state."""
    if 'hotel_favorites' not in st.session_state:
        st.session_state.hotel_favorites = []


def _get_hotel_key(hotel: Dict) -> str:
    """Return a stable key for a hotel dict (name + city/address)."""
    name = hotel.get('hotel_name') or hotel.get('name', '')
    city = hotel.get('city') or hotel.get('address', '')
    return f"{name}||{city}"


def _is_favorited(hotel: Dict) -> bool:
    """Check whether a hotel is in the favorites list."""
    _init_favorites()
    key = _get_hotel_key(hotel)
    return any(_get_hotel_key(f) == key for f in st.session_state.hotel_favorites)


def _add_favorite(hotel: Dict):
    """Add a hotel to favorites (max MAX_FAVORITES)."""
    _init_favorites()
    if len(st.session_state.hotel_favorites) >= MAX_FAVORITES:
        return  # Silently cap at max
    if _is_favorited(hotel):
        return
    st.session_state.hotel_favorites.append(dict(hotel))

    # Award XP for the first favorite ever added
    if not st.session_state.get('hotel_fav_xp_awarded'):
        add_xp_safe(5, "Menyimpan hotel favorit pertama")
        st.session_state.hotel_fav_xp_awarded = True


def _remove_favorite(hotel: Dict):
    """Remove a hotel from favorites."""
    _init_favorites()
    key = _get_hotel_key(hotel)
    st.session_state.hotel_favorites = [
        f for f in st.session_state.hotel_favorites
        if _get_hotel_key(f) != key
    ]


def _extract_price_number(price_value) -> float:
    """Extract numeric price from various formats (str, int, float)."""
    if isinstance(price_value, (int, float)):
        return float(price_value)
    if isinstance(price_value, str):
        # Remove currency codes, commas, spaces
        cleaned = price_value.replace(',', '').replace(' ', '')
        for prefix in ('SAR', 'USD', 'IDR', 'Rp'):
            cleaned = cleaned.replace(prefix, '')
        try:
            return float(cleaned.strip())
        except (ValueError, TypeError):
            return 0.0
    return 0.0


# =============================================================================
# FAVORITES UI COMPONENTS
# =============================================================================

def render_favorite_toggle(hotel: Dict, key_suffix: str = ""):
    """Render a star toggle button for adding/removing a hotel from favorites.

    Args:
        hotel: Hotel dict (API result or demo hotel)
        key_suffix: Unique suffix to avoid duplicate widget keys
    """
    _init_favorites()
    is_fav = _is_favorited(hotel)
    hotel_name = hotel.get('hotel_name') or hotel.get('name', 'Hotel')

    label = "Hapus dari Favorit" if is_fav else "Tambah ke Favorit"
    icon = "⭐" if is_fav else "☆"

    at_max = len(st.session_state.hotel_favorites) >= MAX_FAVORITES and not is_fav
    disabled = at_max

    btn_key = f"fav_toggle_{_get_hotel_key(hotel)}_{key_suffix}"

    if st.button(
        f"{icon} {label}",
        key=btn_key,
        disabled=disabled,
        help=f"Maksimal {MAX_FAVORITES} favorit" if at_max else None,
    ):
        if is_fav:
            _remove_favorite(hotel)
        else:
            _add_favorite(hotel)
        st.rerun()

    if is_fav:
        st.markdown(
            '<span class="favorite-badge">⭐ Favorit</span>',
            unsafe_allow_html=True,
        )


def render_favorites_comparison(favorites: List[Dict]):
    """Render a side-by-side comparison table of favorited hotels (max 4)."""
    if not favorites:
        return

    display = favorites[:4]

    # Collect prices for best-price highlighting
    prices = []
    for h in display:
        p = h.get('price_per_night', 0)
        if not p:
            # Try demo format
            price_dict = h.get('prices', {})
            if price_dict:
                vals = [_extract_price_number(v) for v in price_dict.values()]
                p = min(vals) if vals else 0
        prices.append(float(p) if p else 0)

    best_price = min(prices) if prices and any(p > 0 for p in prices) else None

    # Build table rows
    # Row 1: Name
    # Row 2: Stars
    # Row 3: Price/night
    # Row 4: Amenities (truncated)
    # Row 5: Source/vendor
    header_cells = "".join(
        f'<th>{(h.get("hotel_name") or h.get("name", "Hotel"))}</th>'
        for h in display
    )

    # Stars row
    star_cells = "".join(
        f'<td>{"⭐" * (h.get("stars", 3))}</td>' for h in display
    )

    # Price row
    price_cells = []
    for i, h in enumerate(display):
        p = prices[i]
        currency = h.get('currency', 'SAR')
        css_class = ' class="best-price"' if (best_price and p > 0 and p == best_price) else ''
        if p > 0:
            price_cells.append(f'<td{css_class}>{currency} {p:,.0f}</td>')
        else:
            price_cells.append('<td>-</td>')
    price_row = "".join(price_cells)

    # Amenities row
    amenity_cells = []
    for h in display:
        text = _get_amenities_text(h)
        if text and len(text) > 60:
            text = text[:57] + "..."
        amenity_cells.append(f'<td>{text or "-"}</td>')
    amenity_row = "".join(amenity_cells)

    # Source row
    source_cells = []
    for h in display:
        vendor = h.get('vendor_name', '')
        if not vendor:
            price_dict = h.get('prices', {})
            vendor = ", ".join(price_dict.keys()) if price_dict else "-"
        source_cells.append(f'<td>{vendor}</td>')
    source_row = "".join(source_cells)

    table_html = f"""
    <table class="favorites-compare-table" role="table"
           aria-label="Perbandingan hotel favorit">
        <thead>
            <tr><th>Properti</th>{header_cells}</tr>
        </thead>
        <tbody>
            <tr><td><strong>Bintang</strong></td>{star_cells}</tr>
            <tr><td><strong>Harga/malam</strong></td>{price_row}</tr>
            <tr><td><strong>Fasilitas</strong></td>{amenity_row}</tr>
            <tr><td><strong>Sumber</strong></td>{source_row}</tr>
        </tbody>
    </table>
    """

    st.markdown(table_html, unsafe_allow_html=True)

    if best_price and best_price > 0:
        st.markdown(
            f'<div style="color:#66bb6a;font-size:0.8rem;margin-top:0.3rem;">'
            f'<span aria-hidden="true">✅ </span>Harga terbaik ditandai hijau</div>',
            unsafe_allow_html=True,
        )


def render_favorites_section():
    """Render the favorites sidebar/section showing saved hotels."""
    _init_favorites()
    favorites = st.session_state.hotel_favorites

    st.markdown("""
        <div class="favorites-section">
            <h3><span aria-hidden="true">⭐ </span>Hotel Favorit</h3>
        </div>
    """, unsafe_allow_html=True)

    if not favorites:
        st.markdown("""
            <div class="favorites-section">
                <div class="fav-empty">
                    Belum ada hotel favorit. Klik ☆ pada hotel untuk menyimpan.
                </div>
            </div>
        """, unsafe_allow_html=True)
        return

    st.caption(f"{len(favorites)}/{MAX_FAVORITES} hotel tersimpan")

    for i, fav in enumerate(favorites):
        name = fav.get('hotel_name') or fav.get('name', 'Hotel')
        stars = fav.get('stars', 3)
        price = fav.get('price_per_night', 0)
        currency = fav.get('currency', 'SAR')
        city = fav.get('city', '')

        # For demo hotels, extract lowest price
        if not price and fav.get('prices'):
            vals = [_extract_price_number(v) for v in fav['prices'].values()]
            price = min(vals) if vals else 0

        price_str = f"{currency} {price:,.0f}" if price else "-"
        star_str = "⭐" * stars

        st.markdown(f"""
            <div class="favorites-section">
                <div class="fav-card">
                    <div class="fav-info">
                        <div class="fav-name">{name}</div>
                        <div class="fav-meta">{star_str} {(" &bull; " + city) if city else ""}</div>
                    </div>
                    <div class="fav-price">{price_str}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Hapus dari Favorit", key=f"fav_remove_{i}_{name}"):
            _remove_favorite(fav)
            st.rerun()

    st.markdown("---")

    # Compare button (need at least 2 favorites)
    if len(favorites) >= 2:
        if st.button(
            "📊 Bandingkan Favorit",
            key="compare_favorites_btn",
            type="primary",
            use_container_width=True,
        ):
            st.session_state['show_favorites_comparison'] = True
            st.rerun()

        if st.session_state.get('show_favorites_comparison'):
            st.markdown("#### Perbandingan Hotel Favorit")
            if len(favorites) > 4:
                st.caption("Menampilkan 4 hotel pertama")
            render_favorites_comparison(favorites)

            if st.button("Tutup Perbandingan", key="close_fav_compare"):
                st.session_state['show_favorites_comparison'] = False
                st.rerun()
    else:
        st.caption("Tambahkan minimal 2 hotel favorit untuk membandingkan")


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


def render_amenity_filters():
    """Render amenity filter checkboxes. Returns list of active filter keys."""
    if not HAS_AMENITIES:
        return []

    try:
        st.markdown("""
            <div class="amenity-filter-section">
                <h4><span aria-hidden="true">🏷️ </span>Filter Fasilitas</h4>
            </div>
        """, unsafe_allow_html=True)

        # Initialize session state for amenity filters if not present
        if 'amenity_filters' not in st.session_state:
            st.session_state.amenity_filters = {}

        active_filters = []

        for fkey, label, _attr in AMENITY_FILTER_OPTIONS:
            checked = st.checkbox(
                label,
                value=st.session_state.amenity_filters.get(fkey, False),
                key=f"amenity_filter_{fkey}",
            )
            st.session_state.amenity_filters[fkey] = checked
            if checked:
                active_filters.append(fkey)

        if active_filters:
            st.caption(f"{len(active_filters)} filter aktif")

        return active_filters

    except Exception as e:
        logger.warning(f"Amenity filter render error: {e}")
        return []


def render_amenity_match_badge(hotel: Dict, active_filters: List[str]):
    """Render amenity match score badge on a hotel card."""
    if not HAS_AMENITIES or not active_filters:
        return

    try:
        matched, total, matched_names, _signals = _compute_amenity_match(hotel, active_filters)

        if total == 0:
            return

        # Determine color based on match ratio
        ratio = matched / total
        if ratio >= 1.0:
            bar_color = "#2e7d32"  # Green - perfect match
            text_color = "#66bb6a"
        elif ratio >= 0.5:
            bar_color = "#d4af37"  # Gold - partial match
            text_color = "#d4af37"
        else:
            bar_color = "#c62828"  # Red - low match
            text_color = "#ef5350"

        pct = int(ratio * 100)

        st.markdown(f"""
            <div class="amenity-match-badge">
                <div>
                    <div class="match-text">
                        <strong style="color:{text_color};">{matched}/{total}</strong> fasilitas cocok
                    </div>
                    <div class="amenity-match-bar">
                        <div class="amenity-match-bar-fill"
                             style="width:{pct}%;background:{bar_color};"></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except Exception:
        pass  # Graceful fallback


def render_hotel_card(hotel: Dict, nights: int = 1, active_filters: List[str] = None):
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
                amenities_text = _get_amenities_text(hotel)
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

            # Amenity match score badge (when filters are active)
            if active_filters:
                render_amenity_match_badge(hotel, active_filters)

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
                    <div style="color: #8e9fb3; font-size: 0.75rem;">
                        Upgrade ke Premium untuk akses lengkap
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Best deal indicator
        if hotel.get('vendor_name'):
            st.success(f"✅ Harga terbaik dari **{hotel.get('vendor_name')}**")

        # Favorite toggle
        hotel_name = hotel.get('hotel_name', 'Unknown Hotel')
        render_favorite_toggle(hotel, key_suffix=f"card_{hotel_name}")


def render_hotel_list(result: Dict, active_filters: List[str] = None):
    """Render list of hotels with optional amenity filtering/reordering."""

    if active_filters is None:
        active_filters = []

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

    # =========================================================================
    # AMENITY FILTER: Reorder hotels (matching first, then non-matching)
    # =========================================================================
    matching_count = 0
    total_count = len(hotels)

    if active_filters and HAS_AMENITIES:
        try:
            matching_hotels = []
            non_matching_hotels = []

            for hotel in hotels:
                matched, total, _names, _signals = _compute_amenity_match(hotel, active_filters)
                if matched > 0:
                    matching_hotels.append((matched, hotel))
                    matching_count += 1
                else:
                    non_matching_hotels.append(hotel)

            # Sort matching hotels by match count (descending), preserving
            # the original sort order within same match count
            matching_hotels.sort(key=lambda x: x[0], reverse=True)

            # Rebuild hotel list: matching first, then non-matching
            hotels = [h for (_m, h) in matching_hotels] + non_matching_hotels

        except Exception as e:
            logger.warning(f"Amenity filter reorder error: {e}")

    # Show amenity match summary when filters are active
    if active_filters and HAS_AMENITIES:
        if matching_count > 0:
            st.markdown(f"""
                <div class="amenity-match-summary">
                    <span aria-hidden="true">🏷️ </span>
                    <strong>{matching_count}</strong> hotel cocok dari
                    <strong>{total_count}</strong> total
                    ({len(active_filters)} filter fasilitas aktif)
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="amenity-match-summary" style="border-color:#c62828;">
                    <span aria-hidden="true">⚠️ </span>
                    <strong>0</strong> hotel cocok dari
                    <strong>{total_count}</strong> total
                    &mdash; coba kurangi filter fasilitas
                </div>
            """, unsafe_allow_html=True)

    # Render hotels
    for hotel in hotels:
        render_hotel_card(hotel, nights, active_filters=active_filters)
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

    # Inject amenity filter CSS and favorites CSS (combined to reduce DOM nodes)
    st.markdown(AMENITY_FILTER_CSS + FAVORITES_CSS, unsafe_allow_html=True)

    # Initialize favorites in session state
    _init_favorites()

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

    # Search form + amenity filters (left column) | Results (right column)
    col1, col2 = st.columns([1, 2])

    with col1:
        search_params = render_search_form()

        # Amenity filter section (below search form)
        st.markdown("---")
        active_filters = render_amenity_filters()

        # Favorites section (below amenity filters)
        st.markdown("---")
        render_favorites_section()

    with col2:
        # Show results or placeholder
        if search_params and HAS_MAKCORPS:
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
            render_hotel_list(
                st.session_state['hotel_search_result'],
                active_filters=active_filters,
            )
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

                # Apply amenity filtering/reordering to demo hotels too
                demo_display = list(DEMO_HOTELS)
                demo_matching_count = 0

                if active_filters and HAS_AMENITIES:
                    try:
                        matching_demos = []
                        non_matching_demos = []
                        for dh in demo_display:
                            matched, _total, _names, _sig = _compute_amenity_match(dh, active_filters)
                            if matched > 0:
                                matching_demos.append((matched, dh))
                                demo_matching_count += 1
                            else:
                                non_matching_demos.append(dh)
                        matching_demos.sort(key=lambda x: x[0], reverse=True)
                        demo_display = [d for (_m, d) in matching_demos] + non_matching_demos
                    except Exception:
                        pass

                # Show match summary for demo hotels
                if active_filters and HAS_AMENITIES:
                    if demo_matching_count > 0:
                        st.markdown(f"""
                            <div class="amenity-match-summary">
                                <span aria-hidden="true">🏷️ </span>
                                <strong>{demo_matching_count}</strong> hotel cocok dari
                                <strong>{len(DEMO_HOTELS)}</strong> total
                                ({len(active_filters)} filter fasilitas aktif)
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class="amenity-match-summary" style="border-color:#c62828;">
                                <span aria-hidden="true">⚠️ </span>
                                <strong>0</strong> hotel cocok dari
                                <strong>{len(DEMO_HOTELS)}</strong> total
                                &mdash; coba kurangi filter fasilitas
                            </div>
                        """, unsafe_allow_html=True)

                for h in demo_display:
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

                        # Amenity match badge for demo hotels
                        if active_filters:
                            render_amenity_match_badge(h, active_filters)

                        # Favorite toggle for demo hotels
                        render_favorite_toggle(h, key_suffix=f"demo_{h['name']}")
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
                escaped = tips.replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f'''
                    <div class="ai-card" role="status" aria-live="polite">
                        <h4>Tips AI Memilih Hotel</h4>
                        <p>{escaped}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['render_hotel_compare_page', 'render_favorites_section', 'render_favorites_comparison']
