"""
================================================================================
LABBAIK AI - PACKAGE BUILDER
================================================================================
Lokasi: ui/pages/package_builder.py
Fitur: Tool untuk travel partner merancang paket umrah custom dengan margin
       - Pilih komponen paket (hotel, penerbangan, transport, dll)
       - Tentukan margin keuntungan
       - Lihat breakdown biaya dan harga jual
       - Simpan skenario untuk perbandingan
       - AI pricing recommendation & optimization
       - Gamification: XP rewards for building/analyzing packages
================================================================================
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import logging

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

logger = logging.getLogger(__name__)

# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

PACKAGE_BUILDER_CSS = """
/* Hero override for package builder */
.pkg-hero {
    --hero-bg: linear-gradient(135deg, #1a1a2e 0%, #2d1b4e 50%, #1a2a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
}

/* Section card */
.pkg-section {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #333;
    border-left: 4px solid #d4af37;
}

.pkg-section h3 {
    color: #d4af37;
    margin-top: 0;
    font-size: 1.2rem;
}

/* Summary metric cards */
.pkg-metric {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 1.25rem;
    text-align: center;
    border: 1px solid #334155;
    transition: border-color 0.2s;
}

.pkg-metric:hover {
    border-color: #d4af37;
}

.pkg-metric .value {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0.25rem 0;
}

.pkg-metric .label {
    color: #94a3b8;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.pkg-metric .delta {
    font-size: 0.85rem;
    color: #4ade80;
    margin-top: 0.2rem;
}

/* Scenario comparison card */
.scenario-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid #333;
    transition: transform 0.15s;
}

.scenario-card:hover {
    transform: translateX(2px);
}

.scenario-card .name {
    color: #d4af37;
    font-weight: 600;
    font-size: 1.05rem;
}

.scenario-card .price {
    font-size: 1.3rem;
    font-weight: 700;
    color: #4ade80;
}

/* Tips box */
.pkg-tip {
    background: linear-gradient(145deg, #1a2a1a 0%, #1e3b1e 100%);
    border: 1px solid #2d5a2d;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-top: 0.75rem;
    color: #a3d9a5;
    font-size: 0.9rem;
}

.pkg-tip strong {
    color: #4ade80;
}
"""


# =============================================================================
# CONFIG LOADER
# =============================================================================

def load_config():
    """Load package builder configuration."""
    try:
        from utils.package_calculator import (
            get_config,
            get_hotels,
            get_airlines,
            get_origins,
            get_transport_options,
            get_room_types,
            get_meal_options,
            get_fixed_costs,
            get_margin_presets,
            get_durations,
        )
        return {
            "config": get_config(),
            "hotels_makkah": get_hotels("makkah"),
            "hotels_madinah": get_hotels("madinah"),
            "airlines": get_airlines(),
            "origins": get_origins(),
            "transport": get_transport_options("makkah_madinah"),
            "airport_transfer": get_transport_options("airport_transfer"),
            "room_types": get_room_types(),
            "meals": get_meal_options(),
            "fixed_costs": get_fixed_costs(),
            "margin_presets": get_margin_presets(),
            "durations": get_durations(),
        }
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None


# =============================================================================
# HELPERS
# =============================================================================

def format_rupiah(amount: int) -> str:
    """Format as Rupiah."""
    return f"Rp {amount:,.0f}".replace(",", ".")


def init_session_state():
    """Initialize session state for package builder."""
    if "pkg_scenarios" not in st.session_state:
        st.session_state.pkg_scenarios = []
    if "pkg_current" not in st.session_state:
        st.session_state.pkg_current = {}
    if "pkg_ai_result" not in st.session_state:
        st.session_state.pkg_ai_result = None
    if "pkg_build_xp_awarded" not in st.session_state:
        st.session_state.pkg_build_xp_awarded = False
    if "pkg_ai_xp_awarded" not in st.session_state:
        st.session_state.pkg_ai_xp_awarded = False


# =============================================================================
# HERO
# =============================================================================

def render_hero():
    """Render page hero banner with CSS injection."""
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, PACKAGE_BUILDER_CSS)

    st.markdown(
        '<div class="page-hero pkg-hero">'
        '<div class="bismillah">&#1576;&#1616;&#1587;&#1618;&#1605;&#1616; &#1575;&#1604;&#1604;&#1617;&#1607;&#1616; &#1575;&#1604;&#1585;&#1617;&#1581;&#1618;&#1605;&#1606;&#1616; &#1575;&#1604;&#1585;&#1617;&#1581;&#1610;&#1605;&#1616;</div>'
        '<h1>Package Builder</h1>'
        '<p class="subtitle">Rancang paket umrah dengan berbagai skenario, tentukan margin, dan bandingkan harga jual</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "**Cara Penggunaan:**\n"
        "1. Pilih komponen paket (hotel, penerbangan, transport, dll)\n"
        "2. Tentukan margin keuntungan\n"
        "3. Lihat breakdown biaya dan harga jual\n"
        "4. Gunakan AI untuk analisis & rekomendasi harga\n"
        "5. Simpan skenario untuk perbandingan"
    )


# =============================================================================
# SECTION RENDERERS
# =============================================================================

def render_duration_section(config: dict) -> dict:
    """Render duration selection."""
    st.markdown("### Durasi Perjalanan")

    durations = config.get("durations", [])
    duration_options = {d["label"]: d for d in durations}

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_duration = st.selectbox(
            "Pilih Durasi",
            options=list(duration_options.keys()),
            index=0
        )
        duration_data = duration_options[selected_duration]

    with col2:
        nights_makkah = st.number_input(
            "Malam di Makkah",
            min_value=1,
            max_value=14,
            value=duration_data.get("nights_makkah", 4)
        )

    with col3:
        nights_madinah = st.number_input(
            "Malam di Madinah",
            min_value=1,
            max_value=14,
            value=duration_data.get("nights_madinah", 4)
        )

    return {
        "duration_days": duration_data.get("days", 9),
        "nights_makkah": nights_makkah,
        "nights_madinah": nights_madinah,
    }


def render_hotel_section(config: dict) -> dict:
    """Render hotel selection."""
    st.markdown("### Akomodasi Hotel")

    col1, col2 = st.columns(2)

    # Makkah Hotel
    with col1:
        st.markdown("**Makkah**")
        hotels_makkah = config.get("hotels_makkah", [])
        hotel_makkah_options = {h["label"]: h for h in hotels_makkah}

        selected_makkah = st.selectbox(
            "Kategori Hotel Makkah",
            options=list(hotel_makkah_options.keys()),
            index=1  # Default to bintang 4
        )
        hotel_makkah = hotel_makkah_options[selected_makkah]

        makkah_price = st.slider(
            "Harga per Malam (per kamar)",
            min_value=hotel_makkah["price_min"],
            max_value=hotel_makkah["price_max"],
            value=hotel_makkah["default_price"],
            step=100000,
            format="Rp %d"
        )
        st.caption(f"Jarak ke Haram: {hotel_makkah['distance']}")

    # Madinah Hotel
    with col2:
        st.markdown("**Madinah**")
        hotels_madinah = config.get("hotels_madinah", [])
        hotel_madinah_options = {h["label"]: h for h in hotels_madinah}

        selected_madinah = st.selectbox(
            "Kategori Hotel Madinah",
            options=list(hotel_madinah_options.keys()),
            index=1
        )
        hotel_madinah = hotel_madinah_options[selected_madinah]

        madinah_price = st.slider(
            "Harga per Malam (per kamar)",
            min_value=hotel_madinah["price_min"],
            max_value=hotel_madinah["price_max"],
            value=hotel_madinah["default_price"],
            step=100000,
            format="Rp %d",
            key="madinah_price"
        )
        st.caption(f"Jarak ke Nabawi: {hotel_madinah['distance']}")

    return {
        "hotel_makkah_category": hotel_makkah["category"],
        "hotel_makkah_price": makkah_price,
        "hotel_madinah_category": hotel_madinah["category"],
        "hotel_madinah_price": madinah_price,
    }


def render_flight_section(config: dict) -> dict:
    """Render flight selection."""
    st.markdown("### Penerbangan")

    col1, col2, col3 = st.columns(3)

    # Origin
    with col1:
        origins = config.get("origins", [])
        origin_options = {f"{o['name']}": o for o in origins}

        selected_origin = st.selectbox(
            "Kota Keberangkatan",
            options=list(origin_options.keys()),
            index=0
        )
        origin = origin_options[selected_origin]
        if origin["surcharge"] > 0:
            st.caption(f"Surcharge: +{format_rupiah(origin['surcharge'])}")

    # Airline
    with col2:
        airlines = config.get("airlines", [])
        airline_options = {f"{a['name']} ({a['code']})": a for a in airlines}

        selected_airline = st.selectbox(
            "Maskapai",
            options=list(airline_options.keys()),
            index=0
        )
        airline = airline_options[selected_airline]

    # Class
    with col3:
        flight_class = st.radio(
            "Kelas",
            options=["Economy", "Business"],
            horizontal=True
        )

        if flight_class == "Economy":
            flight_price = airline["price_economy"]
        else:
            if airline.get("price_business"):
                flight_price = airline["price_business"]
            else:
                st.warning("Business class tidak tersedia")
                flight_price = airline["price_economy"]
                flight_class = "Economy"

    st.metric("Harga Tiket PP", format_rupiah(flight_price + origin["surcharge"]))

    return {
        "airline_code": airline["code"],
        "flight_class": flight_class.lower(),
        "flight_price": flight_price,
        "origin_code": origin["code"],
        "origin_surcharge": origin["surcharge"],
    }


def render_transport_section(config: dict) -> dict:
    """Render transport selection."""
    st.markdown("### Transportasi")

    col1, col2 = st.columns(2)

    # Intercity transport
    with col1:
        st.markdown("**Makkah - Madinah**")
        transport = config.get("transport", [])
        transport_options = {t["label"]: t for t in transport}

        selected_transport = st.selectbox(
            "Pilih Transportasi",
            options=list(transport_options.keys()),
            index=0
        )
        trans = transport_options[selected_transport]
        st.caption(f"Durasi: {trans['duration']} | {format_rupiah(trans['price'])}")

    # Airport transfer
    with col2:
        st.markdown("**Airport Transfer**")
        airport_options = {
            "Bus Rombongan (per pax)": {"price": 150000, "per": "person"},
            "Hiace Privat (10 pax)": {"price": 1500000, "per": "group", "pax": 10},
            "Coaster (25 pax)": {"price": 2500000, "per": "group", "pax": 25},
        }

        selected_airport = st.selectbox(
            "Pilih Transfer",
            options=list(airport_options.keys()),
            index=0
        )
        airport = airport_options[selected_airport]

        if airport["per"] == "person":
            airport_price = airport["price"]
        else:
            airport_price = int(airport["price"] / airport["pax"])

        st.caption(f"~{format_rupiah(airport_price)} per orang")

    return {
        "intercity_transport": trans.get("type", "haramain_train"),
        "intercity_price": trans["price"],
        "airport_transfer": selected_airport,
        "airport_transfer_price": airport_price,
    }


def render_room_meal_section(config: dict) -> dict:
    """Render room and meal selection."""
    st.markdown("### Kamar & Makan")

    col1, col2, col3 = st.columns(3)

    # Room type
    with col1:
        room_types = config.get("room_types", [])
        room_options = {r["label"]: r for r in room_types}

        selected_room = st.selectbox(
            "Tipe Kamar",
            options=list(room_options.keys()),
            index=0
        )
        room = room_options[selected_room]

    # Meal type
    with col2:
        meals = config.get("meals", [])
        meal_options = {m["label"]: m for m in meals}

        selected_meal = st.selectbox(
            "Paket Makan",
            options=list(meal_options.keys()),
            index=0
        )
        meal = meal_options[selected_meal]

    # Group size
    with col3:
        group_size = st.number_input(
            "Jumlah Jamaah",
            min_value=1,
            max_value=100,
            value=45
        )

    return {
        "room_type": room["type"],
        "room_occupancy": room["occupancy"],
        "room_multiplier": room["price_multiplier"],
        "meal_type": meal["type"],
        "meal_price_per_day": meal["price_per_day"],
        "group_size": group_size,
    }


def render_additional_costs_section(config: dict) -> dict:
    """Render additional costs."""
    st.markdown("### Biaya Tambahan")

    fixed_costs = config.get("fixed_costs", [])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Biaya Wajib (per orang)**")
        visa_cost = st.number_input("Visa Umrah", value=2500000, step=100000, format="%d")
        insurance_cost = st.number_input("Asuransi", value=350000, step=50000, format="%d")
        handling_cost = st.number_input("Handling & Airport Tax", value=500000, step=50000, format="%d")

    with col2:
        st.markdown("**Biaya Opsional**")
        include_equipment = st.checkbox("Perlengkapan Umrah", value=True)
        equipment_cost = st.number_input("Biaya Perlengkapan", value=300000, step=50000, disabled=not include_equipment)

        include_guide = st.checkbox("Muthawwif/Guide Lokal", value=True)
        guide_cost = st.number_input("Biaya Guide (per grup)", value=3000000, step=500000, disabled=not include_guide)

        include_ziarah = st.checkbox("Ziarah Tambahan", value=True)
        ziarah_cost = st.number_input("Biaya Ziarah", value=500000, step=100000, disabled=not include_ziarah)

    return {
        "visa_cost": visa_cost,
        "insurance_cost": insurance_cost,
        "handling_cost": handling_cost,
        "include_equipment": include_equipment,
        "equipment_cost": equipment_cost if include_equipment else 0,
        "include_guide": include_guide,
        "guide_cost": guide_cost if include_guide else 0,
        "include_ziarah": include_ziarah,
        "ziarah_cost": ziarah_cost if include_ziarah else 0,
    }


def render_margin_section(config: dict) -> dict:
    """Render margin settings."""
    st.markdown("### Margin & Harga Jual")

    presets = config.get("margin_presets", [])

    col1, col2 = st.columns(2)

    with col1:
        margin_type = st.radio(
            "Tipe Margin",
            options=["Persentase", "Nominal Tetap"],
            horizontal=True
        )

        if margin_type == "Persentase":
            # Show presets
            preset_options = {f"{p['name']} ({p['percentage']}%)": p for p in presets}
            selected_preset = st.selectbox(
                "Preset Margin",
                options=["Custom"] + list(preset_options.keys()),
                index=2  # Default to Standar (15%)
            )

            if selected_preset == "Custom":
                margin_percentage = st.slider(
                    "Persentase Margin",
                    min_value=5.0,
                    max_value=40.0,
                    value=15.0,
                    step=1.0,
                    format="%.0f%%"
                )
            else:
                preset = preset_options[selected_preset]
                margin_percentage = preset["percentage"]
                st.info(preset["description"])

            return {
                "margin_type": "percentage",
                "margin_percentage": margin_percentage,
                "margin_fixed": 0,
            }
        else:
            margin_fixed = st.number_input(
                "Margin per Orang (Rp)",
                min_value=0,
                max_value=10000000,
                value=3000000,
                step=500000
            )
            return {
                "margin_type": "fixed",
                "margin_percentage": 0,
                "margin_fixed": margin_fixed,
            }

    with col2:
        season = st.selectbox(
            "Musim/Season",
            options=["Regular Season", "Low Season (-15%)", "High Season (+30%)", "Ramadan (+50%)"],
            index=0
        )

        season_multipliers = {
            "Regular Season": 1.0,
            "Low Season (-15%)": 0.85,
            "High Season (+30%)": 1.3,
            "Ramadan (+50%)": 1.5,
        }

        return {
            "margin_type": "percentage" if margin_type == "Persentase" else "fixed",
            "margin_percentage": margin_percentage if margin_type == "Persentase" else 0,
            "margin_fixed": margin_fixed if margin_type != "Persentase" else 0,
            "season_multiplier": season_multipliers[season],
        }


# =============================================================================
# CALCULATION RESULT
# =============================================================================

def render_calculation_result(params: dict):
    """Render calculation result."""
    from utils.package_calculator import PackageScenario, calculate_package, format_currency

    st.markdown("---")
    st.markdown("## Hasil Kalkulasi")

    # Create scenario from params
    scenario = PackageScenario(**params)
    breakdown = calculate_package(scenario)

    # Summary metric cards
    cost_val = format_currency(breakdown.cost_per_person)
    margin_val = format_currency(breakdown.margin_per_person)
    margin_pct = f"{params.get('margin_percentage', 0):.0f}%"
    sell_val = format_currency(breakdown.selling_price_per_person)
    total_margin_val = format_currency(breakdown.total_margin)
    group_label = f"{params.get('group_size', 45)} jamaah"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            '<div class="pkg-metric">'
            '<div class="label">Modal per Orang</div>'
            '<div class="value" style="color: #60a5fa;">' + cost_val + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            '<div class="pkg-metric">'
            '<div class="label">Margin per Orang</div>'
            '<div class="value" style="color: #fbbf24;">' + margin_val + '</div>'
            '<div class="delta">' + margin_pct + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            '<div class="pkg-metric">'
            '<div class="label">Harga Jual</div>'
            '<div class="value" style="color: #4ade80;">' + sell_val + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            '<div class="pkg-metric">'
            '<div class="label">Total Keuntungan</div>'
            '<div class="value" style="color: #d4af37;">' + total_margin_val + '</div>'
            '<div class="delta">' + group_label + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Detailed breakdown
    st.markdown("### Breakdown Biaya per Orang")

    breakdown_data = {
        "Komponen": [
            "Hotel Makkah",
            "Hotel Madinah",
            "Penerbangan",
            "Transportasi",
            "Makan",
            "Visa",
            "Asuransi",
            "Handling",
            "Perlengkapan",
            "Guide (share)",
            "Ziarah",
            "**TOTAL MODAL**",
            "Margin",
            "**HARGA JUAL**",
        ],
        "Biaya": [
            format_currency(breakdown.hotel_makkah),
            format_currency(breakdown.hotel_madinah),
            format_currency(breakdown.flight),
            format_currency(breakdown.transport),
            format_currency(breakdown.meals),
            format_currency(breakdown.visa),
            format_currency(breakdown.insurance),
            format_currency(breakdown.handling),
            format_currency(breakdown.equipment),
            format_currency(breakdown.guide_share),
            format_currency(breakdown.ziarah),
            f"**{format_currency(breakdown.cost_per_person)}**",
            format_currency(breakdown.margin_per_person),
            f"**{format_currency(breakdown.selling_price_per_person)}**",
        ],
    }

    df = pd.DataFrame(breakdown_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Group summary
    st.markdown("### Ringkasan Grup")

    total_cost_fmt = format_currency(breakdown.total_cost)
    total_rev_fmt = format_currency(breakdown.total_revenue)
    total_margin_fmt = format_currency(breakdown.total_margin)

    gcol1, gcol2, gcol3 = st.columns(3)
    with gcol1:
        st.markdown(
            '<div class="pkg-metric">'
            '<div class="label">Total Modal Grup</div>'
            '<div class="value" style="color: #60a5fa;">' + total_cost_fmt + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with gcol2:
        st.markdown(
            '<div class="pkg-metric">'
            '<div class="label">Total Pendapatan</div>'
            '<div class="value" style="color: #4ade80;">' + total_rev_fmt + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with gcol3:
        st.markdown(
            '<div class="pkg-metric">'
            '<div class="label">Total Keuntungan Bersih</div>'
            '<div class="value" style="color: #d4af37;">' + total_margin_fmt + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Price comparison with different margins
    st.markdown("### Perbandingan Harga dengan Margin Berbeda")

    from utils.package_calculator import generate_price_tiers

    tiers = generate_price_tiers(scenario, [10, 15, 20, 25, 30])

    tier_data = {
        "Margin": [f"{t['margin_percent']}%" for t in tiers],
        "Harga Jual": [format_currency(t["selling_price"]) for t in tiers],
        "Keuntungan/Orang": [format_currency(t["margin"]) for t in tiers],
        "Keuntungan/Grup": [format_currency(t["margin"] * params.get("group_size", 45)) for t in tiers],
    }

    st.dataframe(pd.DataFrame(tier_data), use_container_width=True, hide_index=True)

    # Gamification: first package build
    if not st.session_state.get("pkg_build_xp_awarded"):
        add_xp_safe(30, "Pertama kali merancang paket umrah")
        st.session_state.pkg_build_xp_awarded = True

    return breakdown


# =============================================================================
# AI PRICING RECOMMENDATION
# =============================================================================

AI_SYSTEM_PROMPT = (
    "Kamu adalah konsultan pricing paket umrah berpengalaman. "
    "Berikan analisis singkat dan rekomendasi harga jual yang kompetitif "
    "berdasarkan data paket yang diberikan. Jawab dalam Bahasa Indonesia. "
    "Fokus pada: (1) apakah harga jual kompetitif di pasar, "
    "(2) rekomendasi margin optimal, (3) tips mengoptimalkan biaya, "
    "(4) strategi value-add untuk menarik jamaah. "
    "Gunakan format poin-poin yang ringkas."
)


def build_ai_prompt(params: dict, breakdown) -> str:
    """Build AI prompt from package parameters and breakdown."""
    from utils.package_calculator import format_currency

    hotel_cat_makkah = params.get("hotel_makkah_category", "bintang_4").replace("_", " ").title()
    hotel_cat_madinah = params.get("hotel_madinah_category", "bintang_4").replace("_", " ").title()
    margin_type_label = "persentase" if params.get("margin_type") == "percentage" else "nominal tetap"
    margin_detail = ""
    if params.get("margin_type") == "percentage":
        margin_detail = f"{params.get('margin_percentage', 15)}%"
    else:
        margin_detail = format_currency(params.get("margin_fixed", 0))

    lines = [
        "Analisis paket umrah berikut:",
        "",
        f"- Durasi: {params.get('duration_days', 9)} hari ({params.get('nights_makkah', 4)} malam Makkah, {params.get('nights_madinah', 4)} malam Madinah)",
        f"- Hotel Makkah: {hotel_cat_makkah} @ {format_currency(params.get('hotel_makkah_price', 0))}/malam",
        f"- Hotel Madinah: {hotel_cat_madinah} @ {format_currency(params.get('hotel_madinah_price', 0))}/malam",
        f"- Penerbangan: {params.get('airline_code', 'SV')} kelas {params.get('flight_class', 'economy')} - {format_currency(params.get('flight_price', 0))}",
        f"- Asal: {params.get('origin_code', 'CGK')}",
        f"- Kamar: {params.get('room_type', 'quad')} ({params.get('room_occupancy', 4)} orang/kamar)",
        f"- Jumlah jamaah: {params.get('group_size', 45)}",
        "",
        f"- Modal per orang: {format_currency(breakdown.cost_per_person)}",
        f"- Margin ({margin_type_label} {margin_detail}): {format_currency(breakdown.margin_per_person)}/orang",
        f"- Harga jual: {format_currency(breakdown.selling_price_per_person)}/orang",
        f"- Total keuntungan grup: {format_currency(breakdown.total_margin)}",
        "",
        "Berikan rekomendasi pricing dan tips optimasi biaya.",
    ]
    return "\n".join(lines)


def render_ai_analysis(params: dict, breakdown):
    """Render AI pricing analysis section."""
    st.markdown("---")
    st.markdown("## Analisis AI")

    st.markdown(
        '<div class="pkg-tip">'
        '<strong>AI Pricing Assistant</strong> - '
        'Dapatkan rekomendasi harga jual yang kompetitif dan tips optimasi biaya '
        'dari AI berdasarkan konfigurasi paket Anda.'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("Analisis dengan AI", type="primary", use_container_width=True, key="pkg_ai_btn"):
        with st.spinner("AI sedang menganalisis paket Anda..."):
            prompt = build_ai_prompt(params, breakdown)
            response = ai_complete(prompt, system_prompt=AI_SYSTEM_PROMPT, max_tokens=1024)
            if response:
                st.session_state.pkg_ai_result = response
                # Gamification: first AI analysis
                if not st.session_state.get("pkg_ai_xp_awarded"):
                    add_xp_safe(20, "Pertama kali menggunakan AI analisis paket")
                    st.session_state.pkg_ai_xp_awarded = True
            else:
                st.session_state.pkg_ai_result = None
                st.warning("Layanan AI tidak tersedia saat ini. Silakan coba lagi nanti.")

    # Show cached AI result
    cached = st.session_state.get("pkg_ai_result")
    if cached:
        escaped = cached.replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            '<div class="ai-card">'
            '<h3>Rekomendasi AI untuk Paket Anda</h3>'
            '<p>' + escaped + '</p>'
            '</div>',
            unsafe_allow_html=True,
        )


# =============================================================================
# SAVE & COMPARE SCENARIOS
# =============================================================================

def render_save_scenario(params: dict, breakdown):
    """Render save scenario button."""
    st.markdown("---")

    default_name = params.get("hotel_makkah_category", "bintang_4").replace("_", " ").title()
    default_val = f"Paket {params.get('duration_days', 9)}D - {default_name}"

    col1, col2 = st.columns([3, 1])

    with col1:
        scenario_name = st.text_input(
            "Nama Skenario",
            value=default_val
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Simpan Skenario", type="primary", use_container_width=True):
            if "pkg_scenarios" not in st.session_state:
                st.session_state.pkg_scenarios = []

            st.session_state.pkg_scenarios.append({
                "name": scenario_name,
                "params": params.copy(),
                "cost": breakdown.cost_per_person,
                "selling_price": breakdown.selling_price_per_person,
                "margin": breakdown.margin_per_person,
                "created_at": datetime.now().isoformat(),
            })

            st.success(f"Skenario '{scenario_name}' berhasil disimpan!")
            st.rerun()


def render_saved_scenarios():
    """Render saved scenarios comparison."""
    if not st.session_state.get("pkg_scenarios"):
        return

    st.markdown("---")
    st.markdown("## Perbandingan Skenario Tersimpan")

    scenarios = st.session_state.pkg_scenarios

    # Render scenario cards
    for idx, s in enumerate(scenarios):
        cost_fmt = format_rupiah(s["cost"])
        sell_fmt = format_rupiah(s["selling_price"])
        margin_fmt = format_rupiah(s["margin"])
        st.markdown(
            '<div class="scenario-card">'
            '<div class="name">' + s["name"] + '</div>'
            '<div style="display: flex; gap: 2rem; margin-top: 0.5rem;">'
            '<div><span style="color: #94a3b8;">Modal:</span> ' + cost_fmt + '</div>'
            '<div><span style="color: #94a3b8;">Margin:</span> ' + margin_fmt + '</div>'
            '<div class="price"><span style="color: #94a3b8;">Jual:</span> ' + sell_fmt + '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Also show as table
    comparison_data = {
        "Skenario": [s["name"] for s in scenarios],
        "Modal": [format_rupiah(s["cost"]) for s in scenarios],
        "Margin": [format_rupiah(s["margin"]) for s in scenarios],
        "Harga Jual": [format_rupiah(s["selling_price"]) for s in scenarios],
    }

    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

    if st.button("Hapus Semua Skenario"):
        st.session_state.pkg_scenarios = []
        st.rerun()


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_package_builder_page():
    """Main package builder page."""

    # Track page
    try:
        from services.analytics import track_page
        track_page("package_builder")
    except Exception:
        pass

    # Initialize
    init_session_state()

    # Load config
    config = load_config()
    if not config:
        st.error("Gagal memuat konfigurasi. Silakan coba lagi.")
        return

    # Hero with CSS injection
    render_hero()

    st.markdown("---")

    # Build package parameters
    params = {"name": "Skenario Baru"}

    # Duration
    params.update(render_duration_section(config))

    st.markdown("---")

    # Hotels
    params.update(render_hotel_section(config))

    st.markdown("---")

    # Flight
    params.update(render_flight_section(config))

    st.markdown("---")

    # Transport
    params.update(render_transport_section(config))

    st.markdown("---")

    # Room & Meals
    params.update(render_room_meal_section(config))

    st.markdown("---")

    # Additional costs
    params.update(render_additional_costs_section(config))

    st.markdown("---")

    # Margin
    margin_params = render_margin_section(config)
    params.update(margin_params)

    # Calculation
    breakdown = render_calculation_result(params)

    # AI Analysis
    render_ai_analysis(params, breakdown)

    # Save scenario
    render_save_scenario(params, breakdown)

    # Show saved scenarios
    render_saved_scenarios()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div class="pkg-tip">'
        '<strong>Tips:</strong> Simpan beberapa skenario untuk membandingkan opsi paket yang berbeda. '
        'Gunakan AI untuk mendapatkan rekomendasi harga jual yang kompetitif.'
        '</div>',
        unsafe_allow_html=True,
    )


# Export
__all__ = ["render_package_builder_page"]
