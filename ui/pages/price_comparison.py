"""
LABBAIK AI v7.5 - Price Comparison Page
========================================
Real-time price comparison from multiple sources.

Features:
- Multi-source price comparison table
- Source badges (API/OTA/Partner)
- Price trend indicators
- Best price highlighting
- Filtering by city, stars, price range, source
- AI price trend analysis
- Gamification XP rewards
"""

from __future__ import annotations

import re
import streamlit as st
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

# Type checking imports (not executed at runtime)
if TYPE_CHECKING:
    from services.price_aggregation import AggregatedOffer

# Try to import price aggregation services
try:
    from services.price_aggregation import (
        get_price_aggregator,
        create_price_aggregator,
        AggregatedOffer,
        SourceType,
        OfferType,
    )
    HAS_PRICE_AGGREGATION = True
except ImportError:
    HAS_PRICE_AGGREGATION = False
    AggregatedOffer = None
    SourceType = None
    OfferType = None

# Try to import data manager for API integration
try:
    from services.umrah import get_umrah_data_manager
    HAS_DATA_MANAGER = True
except ImportError:
    HAS_DATA_MANAGER = False


# =============================================================================
# CONSTANTS
# =============================================================================

SOURCE_BADGES = {
    # API Sources
    "amadeus": ("🌐 API", "#4CAF50"),
    "xotelo": ("🌐 API", "#4CAF50"),
    "makcorps": ("🌐 API", "#4CAF50"),
    # n8n Price Intelligence Sources
    "booking": ("🏨 n8n", "#673AB7"),
    "aviationstack": ("✈️ n8n", "#673AB7"),
    "cheria-travel": ("🤝 Travel", "#FF9800"),
    "alhijaz": ("🤝 Travel", "#FF9800"),
    "patuna": ("🤝 Travel", "#FF9800"),
    "maktour": ("🤝 Travel", "#FF9800"),
    "arminareka": ("🤝 Travel", "#FF9800"),
    # OTA Sources
    "traveloka": ("🛒 OTA", "#2196F3"),
    "tiket": ("🛒 OTA", "#2196F3"),
    "pegipegi": ("🛒 OTA", "#2196F3"),
    # Partner & Demo
    "partner": ("🤝 Partner", "#FF9800"),
    "demo": ("📋 Demo", "#9E9E9E"),
    "n8n": ("⚡ n8n", "#673AB7"),
}

CITIES = ["Semua Kota", "Makkah", "Madinah"]
OFFER_TYPES = {
    "Semua": None,
    "Hotel": "hotel",
    "Penerbangan": "flight",
    "Paket Umrah": "package",
}
SORT_OPTIONS = {
    "Harga Terendah": "price",
    "Harga Tertinggi": "price_desc",
    "Bintang Tertinggi": "stars",
    "Jarak Terdekat": "distance",
    "Terbaru": "updated",
}


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

PRICE_COMPARISON_CSS = """
/* Price comparison page overrides */
.source-badge {
    display: inline-block;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    vertical-align: middle;
}

.source-badge-large {
    display: inline-block;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    vertical-align: middle;
}

.best-price-tag {
    display: inline-block;
    background: linear-gradient(135deg, #2e7d32 0%, #388e3c 100%);
    color: #fff;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: bold;
    margin-top: 4px;
}

.trend-up {
    color: #f87171;
    font-weight: 600;
}

.trend-down {
    color: #4ade80;
    font-weight: 600;
}

.trend-stable {
    color: #94a3b8;
    font-weight: 600;
}

.price-summary-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    padding: 1.25rem;
    border: 1px solid #333;
    text-align: center;
}

.price-summary-card .number {
    font-size: 1.8rem;
    font-weight: bold;
    color: #d4af37;
}

.price-summary-card .label {
    color: #888;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_price(price: float, currency: str = "IDR") -> str:
    """Format price with thousand separators."""
    if currency == "IDR":
        return f"Rp {price:,.0f}"
    else:
        return f"SAR {price:,.2f}"


def get_source_badge(source_name: str) -> tuple:
    """Get badge label and color for source."""
    return SOURCE_BADGES.get(source_name, ("❓ Unknown", "#757575"))


def get_star_display(stars: int) -> str:
    """Get star display string."""
    if not stars:
        return "-"
    return "⭐" * stars


def get_trend_indicator(trend: str, change_percent: float = 0) -> str:
    """Get price trend indicator."""
    if trend == "down":
        return f"📉 {abs(change_percent):.1f}%"
    elif trend == "up":
        return f"📈 +{change_percent:.1f}%"
    else:
        return "➡️ Stabil"


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
        # Italic
        line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
        # Bullet points
        if line.startswith("- ") or line.startswith("* "):
            line = "&bull; " + line[2:]
        # Numbered lists
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            line = "<strong>" + match.group(1) + ".</strong> " + line[match.end():]
        html_lines.append("<div style='margin-bottom:0.3rem;'>" + line + "</div>")
    return "\n".join(html_lines)


def _build_source_badge_html(source_name: str, size: str = "small") -> str:
    """Build an HTML source badge span. size can be 'small' or 'large'."""
    badge_label, badge_color = get_source_badge(source_name)
    css_class = "source-badge-large" if size == "large" else "source-badge"
    return (
        '<span class="' + css_class + '" '
        'style="background-color:' + badge_color + ';">'
        + badge_label
        + '</span>'
    )


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_price_comparison_page():
    """Render the price comparison page."""

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, PRICE_COMPARISON_CSS)

    st.title("🔍 Perbandingan Harga Real-time")
    st.caption("Bandingkan harga dari berbagai sumber: API, OTA, dan Partner")

    if not HAS_PRICE_AGGREGATION:
        st.error("❌ Module price_aggregation tidak tersedia")
        st.info("Pastikan semua dependencies terinstall dengan benar.")
        return

    # Sidebar filters
    with st.sidebar:
        st.subheader("🎯 Filter")

        # City filter
        city = st.selectbox("Kota", CITIES)
        if city == "Semua Kota":
            city = None

        # Offer type filter
        offer_type_label = st.selectbox("Tipe", list(OFFER_TYPES.keys()))
        offer_type = OFFER_TYPES[offer_type_label]

        # Star filter
        min_stars = st.slider("Minimal Bintang", 1, 5, 3)

        # Price range filter
        st.markdown("**Rentang Harga (Juta IDR)**")
        col1, col2 = st.columns(2)
        with col1:
            min_price_m = st.number_input("Min", value=10, min_value=0, step=5)
        with col2:
            max_price_m = st.number_input("Max", value=100, min_value=0, step=5)

        min_price = min_price_m * 1_000_000
        max_price = max_price_m * 1_000_000 if max_price_m > 0 else None

        # Source filter
        st.markdown("**Sumber Data**")
        use_api = st.checkbox("API (Amadeus, Xotelo)", value=True)
        use_n8n = st.checkbox("n8n Price Intelligence", value=True)
        use_ota = st.checkbox("OTA (Traveloka, Tiket)", value=True)
        use_partner = st.checkbox("Travel Agent & Partner", value=True)

        sources = []
        if use_api:
            sources.extend(["amadeus", "xotelo", "makcorps"])
        if use_n8n:
            sources.extend(["booking", "aviationstack", "n8n"])
        if use_ota:
            sources.extend(["traveloka", "tiket", "pegipegi"])
        if use_partner:
            sources.extend([
                "partner", "cheria-travel", "alhijaz",
                "patuna", "maktour", "arminareka"
            ])

        if not sources:
            sources = None  # Show all

        # Sort option
        sort_label = st.selectbox("Urutkan", list(SORT_OPTIONS.keys()))
        sort_by = SORT_OPTIONS[sort_label]

        # Refresh button
        st.divider()
        force_refresh = st.button("🔄 Refresh Data", use_container_width=True)

    # Main content
    try:
        # Initialize aggregator
        aggregator = get_price_aggregator()

        # Connect to data manager if available
        if HAS_DATA_MANAGER:
            try:
                data_manager = get_umrah_data_manager()
                aggregator.set_data_manager(data_manager)
            except Exception as e:
                st.warning(f"⚠️ Data manager tidak tersedia: {e}")

        # Show loading
        with st.spinner("Mengambil data harga dari berbagai sumber..."):
            result = aggregator.aggregate(
                city=city,
                offer_type=offer_type,
                min_price=min_price,
                max_price=max_price,
                min_stars=min_stars,
                sources=sources,
                sort_by=sort_by,
                limit=50,
                force_refresh=force_refresh
            )

        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ditemukan", result["total_found"])
        with col2:
            st.metric("Ditampilkan", result["total_returned"])
        with col3:
            source_count = len(result.get("source_stats", {}))
            st.metric("Sumber Data", f"{source_count} sumber")
        with col4:
            duration = result.get("duration_ms", 0)
            st.metric("Waktu Proses", f"{duration:.0f} ms")

        # Gamification: +20 XP for first price comparison
        if not st.session_state.get("xp_price_compare_done"):
            add_xp_safe(20, "Pertama kali membandingkan harga")
            st.session_state["xp_price_compare_done"] = True

        # Source stats
        if result.get("source_stats"):
            with st.expander("📊 Detail Sumber Data"):
                for source, count in result["source_stats"].items():
                    badge_html = _build_source_badge_html(source, size="large")
                    source_line = badge_html + " <strong>" + source + "</strong>: " + str(count) + " hasil"
                    st.markdown(source_line, unsafe_allow_html=True)

        # Errors
        if result.get("errors"):
            with st.expander("⚠️ Peringatan"):
                for error in result["errors"]:
                    st.warning(error)

        st.divider()

        # Display offers
        offers = result.get("offers", [])

        if not offers:
            st.info("🔍 Tidak ada hasil yang cocok dengan filter Anda.")
            return

        # Render offers
        render_offers_table(offers, offer_type)

        # AI Price Trend Analysis section
        st.divider()
        _render_ai_price_analysis(offers, result)

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {e}")
        st.info("Coba refresh halaman atau periksa koneksi database.")


def render_offers_table(offers: List[AggregatedOffer], offer_type: str = None):
    """Render offers as a comparison table."""

    # Find best price for highlighting
    best_price = min(o.price_idr for o in offers if o.price_idr > 0) if offers else 0

    # Group by type if showing all
    if offer_type is None:
        # Use string comparison for safety
        hotels = [o for o in offers if getattr(o.offer_type, 'value', o.offer_type) == "hotel"]
        flights = [o for o in offers if getattr(o.offer_type, 'value', o.offer_type) == "flight"]
        packages = [o for o in offers if getattr(o.offer_type, 'value', o.offer_type) == "package"]

        if hotels:
            st.subheader("🏨 Hotel")
            render_hotel_cards(hotels, best_price)

        if flights:
            st.subheader("✈️ Penerbangan")
            render_flight_cards(flights, best_price)

        if packages:
            st.subheader("📦 Paket Umrah")
            render_package_cards(packages, best_price)
    elif offer_type == "hotel":
        render_hotel_cards(offers, best_price)
    elif offer_type == "flight":
        render_flight_cards(offers, best_price)
    else:
        render_package_cards(offers, best_price)


def render_hotel_cards(hotels: List[AggregatedOffer], best_price: float):
    """Render hotel offer cards."""
    for idx, hotel in enumerate(hotels):
        is_best = hotel.price_idr == best_price and best_price > 0

        with st.container():
            # Card styling
            border_color = "#4CAF50" if is_best else "#E0E0E0"

            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                # Hotel name and stars
                stars_display = get_star_display(hotel.stars)
                st.markdown(f"**{hotel.name}** {stars_display}")

                # City and distance
                distance_text = ""
                if hotel.distance_to_haram_m:
                    if hotel.distance_to_haram_m < 1000:
                        distance_text = f"{hotel.distance_to_haram_m}m dari Haram"
                    else:
                        distance_text = f"{hotel.distance_to_haram_m/1000:.1f}km dari Haram"

                st.caption(f"📍 {hotel.city} | {distance_text}")

            with col2:
                # Source badge
                badge_html = _build_source_badge_html(hotel.source_name)
                st.markdown(badge_html, unsafe_allow_html=True)

                # Per night price
                if hotel.price_per_night_idr:
                    st.caption(f"{format_price(hotel.price_per_night_idr)}/malam")

            with col3:
                # Price
                price_display = format_price(hotel.price_idr)
                if is_best:
                    st.markdown(f"### 🏆 {price_display}")
                    st.caption("Harga Terbaik!")
                else:
                    st.markdown(f"### {price_display}")

                # Availability
                if not hotel.is_available:
                    st.error("Sold Out")
                elif hotel.rooms_left and hotel.rooms_left < 5:
                    st.warning(f"Sisa {hotel.rooms_left} kamar!")

            st.divider()


def render_flight_cards(flights: List[AggregatedOffer], best_price: float):
    """Render flight offer cards."""
    for idx, flight in enumerate(flights):
        is_best = flight.price_idr == best_price and best_price > 0

        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                # Flight name (airline + route)
                st.markdown(f"**{flight.name}**")

                # Route details
                details = []
                if flight.departure_city:
                    details.append(f"🛫 dari {flight.departure_city}")
                if flight.city:
                    details.append(f"🛬 ke {flight.city}")
                if flight.airline:
                    details.append(f"✈️ {flight.airline}")

                st.caption(" | ".join(details))

                # Check-in date
                if flight.check_in_date:
                    st.caption(f"📅 {flight.check_in_date}")

            with col2:
                # Source badge
                badge_html = _build_source_badge_html(flight.source_name)
                st.markdown(badge_html, unsafe_allow_html=True)

                # Inclusions (Direct/Transit, Class)
                if flight.inclusions:
                    inclusions_text = ", ".join(flight.inclusions[:3])
                    st.caption(f"✅ {inclusions_text}")

            with col3:
                # Price
                price_display = format_price(flight.price_idr)
                if is_best:
                    st.markdown(f"### 🏆 {price_display}")
                    st.caption("Harga Terbaik!")
                else:
                    st.markdown(f"### {price_display}")

                # Availability
                if not flight.is_available:
                    st.error("Sold Out")

            st.divider()


def render_package_cards(packages: List[AggregatedOffer], best_price: float):
    """Render package offer cards."""
    for idx, pkg in enumerate(packages):
        is_best = pkg.price_idr == best_price and best_price > 0

        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                # Package name
                st.markdown(f"**{pkg.name}**")

                # Duration and departure
                details = []
                if pkg.duration_days:
                    details.append(f"📅 {pkg.duration_days} Hari")
                if pkg.departure_city:
                    details.append(f"✈️ dari {pkg.departure_city}")
                if pkg.airline:
                    details.append(f"🛫 {pkg.airline}")

                st.caption(" | ".join(details))

                # Hotels
                hotel_info = []
                if pkg.hotel_makkah:
                    stars = "⭐" * (pkg.hotel_makkah_stars or 4)
                    hotel_info.append(f"Makkah: {pkg.hotel_makkah} {stars}")
                if pkg.hotel_madinah:
                    stars = "⭐" * (pkg.hotel_madinah_stars or 4)
                    hotel_info.append(f"Madinah: {pkg.hotel_madinah} {stars}")

                if hotel_info:
                    st.caption(" | ".join(hotel_info))

            with col2:
                # Source badge
                badge_html = _build_source_badge_html(pkg.source_name)
                st.markdown(badge_html, unsafe_allow_html=True)

                # Inclusions
                if pkg.inclusions:
                    inclusions_text = ", ".join(pkg.inclusions[:3])
                    extra_count = len(pkg.inclusions) - 3
                    if extra_count > 0:
                        inclusions_text += " +" + str(extra_count) + " lainnya"
                    st.caption(f"✅ {inclusions_text}")

            with col3:
                # Price
                price_display = format_price(pkg.price_idr)
                if is_best:
                    st.markdown(f"### 🏆 {price_display}")
                    st.caption("Harga Terbaik!")
                else:
                    st.markdown(f"### {price_display}")

                # Availability
                if not pkg.is_available:
                    st.error("Sold Out")
                elif pkg.quota:
                    available = pkg.quota - (pkg.quota if hasattr(pkg, 'booked') else 0)
                    if available < 10:
                        st.warning(f"Sisa {available} seat!")

            st.divider()


# =============================================================================
# AI PRICE TREND ANALYSIS
# =============================================================================

def _render_ai_price_analysis(offers: List[AggregatedOffer], result: Dict[str, Any]):
    """Render AI-powered price trend analysis section."""
    st.subheader("🤖 Analisis Tren Harga AI")
    st.caption("Analisis cerdas berdasarkan data harga dari berbagai sumber")

    # Check for cached response
    cached_key = "price_comparison_ai_response"
    cached = st.session_state.get(cached_key)

    if cached:
        html_content = _markdown_to_html_simple(cached)
        ai_html = (
            '<div class="ai-card">'
            '<h4 style="color:#4ade80;margin-top:0;">🧠 Hasil Analisis Tren Harga</h4>'
            '<p>' + html_content + '</p>'
            '</div>'
        )
        st.markdown(ai_html, unsafe_allow_html=True)

    # Button to trigger AI analysis
    if st.button("🧠 Analisis Tren Harga dengan AI", use_container_width=True):
        # Build price context for the AI prompt
        price_context = _build_price_context(offers, result)

        prompt_text = (
            "Analisis data perbandingan harga umrah berikut dan berikan insight:\n\n"
            + price_context
            + "\n\nBerikan:\n"
            "1. Ringkasan tren harga saat ini\n"
            "2. Sumber mana yang paling kompetitif\n"
            "3. Tips waktu terbaik untuk booking\n"
            "4. Rekomendasi pilihan terbaik value-for-money\n"
            "5. Peringatan jika ada harga yang terlalu murah (kemungkinan scam)\n"
            "\nJawab dalam bahasa Indonesia, singkat dan praktis."
        )

        system_prompt = (
            "Kamu adalah konsultan travel umrah berpengalaman yang ahli dalam "
            "analisis harga dan tren pasar. Berikan analisis yang jujur, praktis, "
            "dan membantu jamaah Indonesia mendapatkan harga terbaik untuk umrah. "
            "Gunakan bahasa Indonesia yang sopan dan mudah dipahami."
        )

        with st.spinner("AI sedang menganalisis tren harga..."):
            response = ai_complete(prompt_text, system_prompt=system_prompt, max_tokens=1024)

        if response:
            st.session_state[cached_key] = response
            html_content = _markdown_to_html_simple(response)
            ai_html = (
                '<div class="ai-card">'
                '<h4 style="color:#4ade80;margin-top:0;">🧠 Hasil Analisis Tren Harga</h4>'
                '<p>' + html_content + '</p>'
                '</div>'
            )
            st.markdown(ai_html, unsafe_allow_html=True)

            # Gamification: +15 XP for first AI analysis
            if not st.session_state.get("xp_price_ai_done"):
                add_xp_safe(15, "Analisis harga dengan AI")
                st.session_state["xp_price_ai_done"] = True
        else:
            _render_ai_fallback(offers, result)


def _build_price_context(offers: List[AggregatedOffer], result: Dict[str, Any]) -> str:
    """Build a text summary of price data for the AI prompt."""
    lines = []

    total_found = result.get("total_found", 0)
    total_returned = result.get("total_returned", 0)
    source_stats = result.get("source_stats", {})

    lines.append(f"Total penawaran ditemukan: {total_found}")
    lines.append(f"Ditampilkan: {total_returned}")
    lines.append(f"Jumlah sumber: {len(source_stats)}")
    lines.append("")

    # Source breakdown
    if source_stats:
        lines.append("Sumber data:")
        for source, count in source_stats.items():
            badge_label, _ = get_source_badge(source)
            lines.append(f"  - {source} ({badge_label}): {count} hasil")
        lines.append("")

    # Price statistics
    prices = [o.price_idr for o in offers if o.price_idr > 0]
    if prices:
        min_p = min(prices)
        max_p = max(prices)
        avg_p = sum(prices) / len(prices)
        lines.append("Statistik harga:")
        lines.append(f"  - Terendah: {format_price(min_p)}")
        lines.append(f"  - Tertinggi: {format_price(max_p)}")
        lines.append(f"  - Rata-rata: {format_price(avg_p)}")
        lines.append("")

    # Top 10 offers summary
    top_offers = offers[:10]
    lines.append("Top 10 penawaran:")
    for i, offer in enumerate(top_offers, 1):
        offer_type_val = getattr(offer.offer_type, 'value', offer.offer_type)
        city_str = offer.city if offer.city else "-"
        source_str = offer.source_name if offer.source_name else "-"
        stars_str = str(offer.stars) + " bintang" if offer.stars else ""
        line = (
            f"  {i}. {offer.name} | {offer_type_val} | "
            f"{city_str} | {format_price(offer.price_idr)} | "
            f"sumber: {source_str}"
        )
        if stars_str:
            line += " | " + stars_str
        lines.append(line)

    return "\n".join(lines)


def _render_ai_fallback(offers: List[AggregatedOffer], result: Dict[str, Any]):
    """Render fallback analysis when AI service is unavailable."""
    prices = [o.price_idr for o in offers if o.price_idr > 0]
    if not prices:
        st.info("Tidak cukup data untuk analisis.")
        return

    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    source_stats = result.get("source_stats", {})

    # Find the cheapest source
    source_prices = {}
    for o in offers:
        if o.price_idr > 0 and o.source_name:
            if o.source_name not in source_prices:
                source_prices[o.source_name] = []
            source_prices[o.source_name].append(o.price_idr)

    cheapest_source = ""
    cheapest_avg = float("inf")
    for src, src_prices in source_prices.items():
        src_avg = sum(src_prices) / len(src_prices)
        if src_avg < cheapest_avg:
            cheapest_avg = src_avg
            cheapest_source = src

    tips_items = []
    tips_items.append(
        "<strong>Rentang Harga:</strong> "
        + format_price(min_price) + " - " + format_price(max_price)
        + " (rata-rata " + format_price(avg_price) + ")"
    )

    if cheapest_source:
        tips_items.append(
            "<strong>Sumber Termurah:</strong> "
            + cheapest_source + " dengan rata-rata " + format_price(cheapest_avg)
        )

    tips_items.append(
        "<strong>Jumlah Sumber:</strong> "
        + str(len(source_stats)) + " sumber aktif"
    )

    tips_items.append(
        "<strong>Tips:</strong> Bandingkan minimal 3 sumber sebelum booking. "
        "Harga yang terlalu murah dari rata-rata bisa jadi tidak termasuk biaya tersembunyi."
    )

    tips_html = ""
    for item in tips_items:
        tips_html += "<div style='margin-bottom:0.5rem;'>&bull; " + item + "</div>"

    fallback_html = (
        '<div class="ai-card" style="border-color: #d4af37;">'
        '<h4 style="color: #d4af37; margin-top:0;">💡 Ringkasan Harga</h4>'
        '<p>' + tips_html + '</p>'
        '<p style="color:#888;font-size:0.8rem;margin-top:0.75rem;">'
        'AI tidak tersedia saat ini. Ini adalah analisis otomatis berdasarkan data.</p>'
        '</div>'
    )
    st.markdown(fallback_html, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR WIDGET
# =============================================================================

def render_best_prices_widget():
    """Render best prices widget for sidebar."""
    st.subheader("💰 Harga Terbaik Hari Ini")

    if not HAS_PRICE_AGGREGATION:
        st.caption("Fitur tidak tersedia")
        return

    try:
        aggregator = get_price_aggregator()

        # Get best prices by source
        best_prices = aggregator.get_best_prices(offer_type="hotel")

        if not best_prices:
            st.caption("Belum ada data")
            return

        for offer in best_prices[:5]:
            badge_label, badge_color = get_source_badge(offer.source_name)
            st.markdown(
                f"**{offer.name[:25]}...**\n\n"
                f"{format_price(offer.price_idr)} - {offer.city}",
            )

    except Exception as e:
        st.caption(f"Error: {e}")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "render_price_comparison_page",
    "render_best_prices_widget",
]
