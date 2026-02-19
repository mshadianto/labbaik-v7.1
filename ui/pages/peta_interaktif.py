"""
================================================================================
LABBAIK AI - PETA INTERAKTIF MAKKAH & MADINAH
================================================================================
Lokasi: ui/pages/peta_interaktif.py
Fitur: Peta interaktif lokasi penting di Makkah & Madinah dengan AI tips
================================================================================
"""

import streamlit as st
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

# Crowd prediction (optional dependency)
try:
    from features.crowd_prediction import CrowdPredictor
    HAS_CROWD_PREDICTION = True
except ImportError:
    HAS_CROWD_PREDICTION = False

# =============================================================================
# STYLING
# =============================================================================

PETA_CSS = """
/* Page-specific styles for peta interaktif */
.peta-hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid #d4af37;
    position: relative;
    overflow: hidden;
}

.peta-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.05) 0%, transparent 70%);
    animation: peta-pulse 4s ease-in-out infinite;
}

@keyframes peta-pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}

.peta-hero h1 {
    color: #d4af37;
    margin: 0;
    font-size: 2.2rem;
    position: relative;
    z-index: 1;
}

.peta-hero .subtitle {
    color: #b0b0b0;
    font-size: 1rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

.peta-hero .ayat {
    font-family: 'Amiri', serif;
    color: #d4af37;
    font-size: 1.4rem;
    margin-top: 1rem;
    position: relative;
    z-index: 1;
}

.peta-stat-row {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-top: 1.5rem;
    position: relative;
    z-index: 1;
    flex-wrap: wrap;
}

.peta-stat-item {
    text-align: center;
    padding: 0.75rem 1.5rem;
    background: rgba(212, 175, 55, 0.1);
    border-radius: 12px;
    border: 1px solid rgba(212, 175, 55, 0.3);
    min-width: 120px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.peta-stat-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.peta-stat-number {
    font-size: 1.8rem;
    font-weight: bold;
    color: #d4af37;
}

.peta-stat-label {
    color: #aaa;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

.peta-city-btn {
    text-align: center;
    padding: 1.25rem 1rem;
    border-radius: 15px;
    border: 2px solid #333;
    background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
    cursor: pointer;
    transition: all 0.3s ease;
}

.peta-city-btn:hover {
    border-color: #d4af37;
    transform: translateY(-2px);
}

.peta-city-btn.active {
    border-color: #d4af37;
    background: linear-gradient(145deg, #1a2a3a 0%, #1b3a5a 100%);
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.2);
}

.peta-city-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

.peta-city-name {
    color: white;
    font-weight: 600;
    font-size: 1.1rem;
}

.peta-city-name-ar {
    color: #d4af37;
    font-family: 'Amiri', serif;
    font-size: 1rem;
    margin-top: 0.25rem;
    direction: rtl;
}

.peta-category-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.25rem;
}

.peta-stats-card {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    border: 1px solid #333;
    transition: transform 0.2s ease;
}

.peta-stats-card:hover {
    transform: translateY(-2px);
}

.peta-stats-card .number {
    font-size: 1.8rem;
    font-weight: bold;
}

.peta-stats-card .label {
    color: #b0b0b0;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

.peta-poi-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 15px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid #333;
    border-left: 4px solid #d4af37;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.peta-poi-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.peta-poi-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
}

.peta-poi-title {
    color: white;
    font-weight: 600;
    font-size: 1.05rem;
    margin: 0;
}

.peta-poi-title-ar {
    color: #b0b0b0;
    font-size: 0.85rem;
    direction: rtl;
    font-family: 'Amiri', serif;
    margin-top: 0.15rem;
}

.peta-poi-desc {
    color: #ccc;
    font-size: 0.9rem;
    line-height: 1.5;
    margin: 0.5rem 0;
}

.peta-poi-meta {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
    margin-top: 0.5rem;
}

.peta-poi-distance {
    color: #aaa;
    font-size: 0.8rem;
}

.peta-ai-card {
    background: linear-gradient(145deg, #1a2e1a 0%, #1a3a1a 100%);
    border: 1px solid #228B22;
    border-radius: 15px;
    padding: 1.5rem;
    margin-top: 1rem;
}

.peta-ai-card h4 {
    color: #4ade80;
    margin-top: 0;
    margin-bottom: 0.75rem;
}

.peta-ai-card p {
    color: #ccc;
    line-height: 1.7;
    margin: 0;
    white-space: pre-wrap;
}

.peta-walk-result {
    background: linear-gradient(145deg, #1a2e1a 0%, #1a3a1a 100%);
    border: 1px solid #228B22;
    border-radius: 15px;
    padding: 1.5rem;
    margin-top: 1rem;
}

.peta-walk-result h4 {
    color: #4ade80;
    margin-top: 0;
    margin-bottom: 0.75rem;
}

.peta-walk-metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.peta-walk-metric:last-child {
    border-bottom: none;
}

.peta-walk-metric .metric-label {
    color: #aaa;
    font-size: 0.9rem;
}

.peta-walk-metric .metric-value {
    color: white;
    font-weight: 600;
    font-size: 1rem;
}

.peta-recommendation {
    padding: 0.75rem 1rem;
    border-radius: 10px;
    margin-top: 0.75rem;
    font-weight: 600;
}

.peta-rec-green {
    background: rgba(34, 139, 34, 0.2);
    color: #4ade80;
    border: 1px solid rgba(34, 139, 34, 0.4);
}

.peta-rec-blue {
    background: rgba(65, 105, 225, 0.2);
    color: #60a5fa;
    border: 1px solid rgba(65, 105, 225, 0.4);
}

.peta-rec-yellow {
    background: rgba(255, 215, 0, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(255, 215, 0, 0.4);
}

.peta-rec-red {
    background: rgba(220, 20, 60, 0.2);
    color: #f87171;
    border: 1px solid rgba(220, 20, 60, 0.4);
}

/* Crowd overlay section */
.crowd-overlay-section {
    background: linear-gradient(145deg, #0d1b2a 0%, #1b2a4a 100%);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(212, 175, 55, 0.3);
}

.crowd-overlay-section h3 {
    color: #d4af37;
    margin-top: 0;
    margin-bottom: 1rem;
}

.crowd-location-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid #333;
    border-left: 5px solid #d4af37;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    display: flex;
    align-items: center;
    gap: 1rem;
}

.crowd-location-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.crowd-location-card.crowd-green { border-left-color: #22c55e; }
.crowd-location-card.crowd-yellow { border-left-color: #eab308; }
.crowd-location-card.crowd-orange { border-left-color: #f97316; }
.crowd-location-card.crowd-red { border-left-color: #ef4444; }

.crowd-level-indicator {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

.crowd-level-indicator.indicator-green { background: #22c55e; }
.crowd-level-indicator.indicator-yellow { background: #eab308; }
.crowd-level-indicator.indicator-orange { background: #f97316; }
.crowd-level-indicator.indicator-red { background: #ef4444; }

.crowd-location-info {
    flex: 1;
    min-width: 0;
}

.crowd-location-name {
    color: white;
    font-weight: 600;
    font-size: 1rem;
    margin: 0;
}

.crowd-location-level {
    font-size: 0.85rem;
    margin-top: 0.15rem;
}

.crowd-location-rec {
    color: #b0b0b0;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

.crowd-location-pct {
    color: white;
    font-weight: bold;
    font-size: 1.3rem;
    flex-shrink: 0;
    text-align: right;
    min-width: 50px;
}

.crowd-legend {
    display: flex;
    gap: 1.25rem;
    margin-top: 1rem;
    justify-content: center;
    flex-wrap: wrap;
    padding: 0.75rem 1rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
}

.crowd-legend-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.8rem;
    color: #b0b0b0;
}

.crowd-legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}

.crowd-time-display {
    background: rgba(212, 175, 55, 0.1);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.crowd-time-display .time-label {
    color: #b0b0b0;
    font-size: 0.8rem;
}

.crowd-time-display .time-value {
    color: #d4af37;
    font-weight: bold;
    font-size: 1.05rem;
}

.crowd-time-display .prayer-badge {
    background: rgba(212, 175, 55, 0.2);
    color: #d4af37;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

@media (max-width: 768px) {
    .crowd-location-card {
        padding: 0.75rem 1rem;
    }
    .crowd-legend {
        gap: 0.75rem;
    }
    .crowd-time-display {
        flex-direction: column;
        text-align: center;
    }
}

@media (max-width: 480px) {
    .crowd-location-card {
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .crowd-location-pct {
        width: 100%;
        text-align: left;
    }
}
"""

# =============================================================================
# CITY CONFIGURATION
# =============================================================================

CITY_CONFIG = {
    "makkah": {
        "name": "Makkah Al-Mukarramah",
        "name_ar": "مكة المكرمة",
        "icon": "🕋",
        "center": [21.4225, 39.8262],
        "zoom": 14,
        "reference_name": "Masjidil Haram",
        "reference_coords": (21.4225, 39.8262),
    },
    "madinah": {
        "name": "Madinah Al-Munawwarah",
        "name_ar": "المدينة المنورة",
        "icon": "🕌",
        "center": [24.4672, 39.6112],
        "zoom": 14,
        "reference_name": "Masjid Nabawi",
        "reference_coords": (24.4672, 39.6112),
    },
}

# =============================================================================
# AI SYSTEM PROMPT
# =============================================================================

AI_SYSTEM_PROMPT = """Anda adalah pemandu wisata umrah yang berpengalaman.
Berikan tips praktis untuk jamaah umrah Indonesia tentang lokasi yang ditanyakan.
Format jawaban:
1. Waktu terbaik berkunjung
2. Hal yang perlu dibawa/dipersiapkan
3. Etika dan adab yang perlu diperhatikan
4. Estimasi biaya (jika relevan, dalam SAR)
5. Tips keamanan dan kesehatan
Jawab dalam Bahasa Indonesia yang ramah. Maksimal 200 kata."""

# =============================================================================
# FOLIUM COLOR MAPPING
# =============================================================================

FOLIUM_COLORS = {
    "#228B22": "green",
    "#4169E1": "blue",
    "#FF6347": "red",
    "#FFD700": "orange",
    "#DC143C": "darkred",
    "#008080": "cadetblue",
    "#8B4513": "darkgreen",
    "#DAA520": "beige",
}


# =============================================================================
# SESSION STATE
# =============================================================================

def init_peta_state():
    """Initialize peta interaktif session state."""
    if "peta_selected_city" not in st.session_state:
        st.session_state.peta_selected_city = "makkah"
    if "peta_selected_categories" not in st.session_state:
        st.session_state.peta_selected_categories = [
            "masjid", "hotel", "kuliner", "belanja", "sejarah", "transportasi"
        ]
    if "peta_selected_poi" not in st.session_state:
        st.session_state.peta_selected_poi = None
    if "peta_ai_tips_cache" not in st.session_state:
        st.session_state.peta_ai_tips_cache = {}
    if "peta_visited_cities" not in st.session_state:
        st.session_state.peta_visited_cities = set()


# =============================================================================
# GAMIFICATION HELPER
# =============================================================================

def _add_xp(amount, reason):
    """Add XP — delegates to shared helper."""
    add_xp_safe(amount, reason)


# =============================================================================
# DISTANCE CALCULATION (Haversine)
# =============================================================================

def calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate distance between two coordinates using the Haversine formula.

    Returns dict with distance_m, distance_km, and walk_minutes.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_m = R * c
    distance_km = distance_m / 1000
    walk_minutes = int(distance_m / 83.3)  # ~5 km/h walking speed
    return {
        "distance_m": distance_m,
        "distance_km": distance_km,
        "walk_minutes": walk_minutes,
    }


# =============================================================================
# FOLIUM COLOR HELPER
# =============================================================================

def get_folium_color(hex_color):
    """Map a hex color string to a folium built-in marker color name."""
    return FOLIUM_COLORS.get(hex_color, "blue")


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_hero():
    """Render hero section with CSS injection and statistics."""
    from data.peta_locations import MAKKAH_POIS, MADINAH_POIS, CATEGORY_INFO

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, PETA_CSS)

    total_makkah = len(MAKKAH_POIS)
    total_madinah = len(MADINAH_POIS)
    total_categories = len(CATEGORY_INFO)

    st.markdown(f"""
    <div class="peta-hero">
        <div class="ayat">بسم الله الرحمن الرحيم</div>
        <h1>Peta Interaktif Makkah & Madinah</h1>
        <p class="subtitle">Jelajahi lokasi penting untuk perjalanan umrah Anda</p>
        <div class="peta-stat-row">
            <div class="peta-stat-item">
                <div class="peta-stat-number">{total_makkah}</div>
                <div class="peta-stat-label">Lokasi Makkah</div>
            </div>
            <div class="peta-stat-item">
                <div class="peta-stat-number">{total_madinah}</div>
                <div class="peta-stat-label">Lokasi Madinah</div>
            </div>
            <div class="peta-stat-item">
                <div class="peta-stat-number">{total_categories}</div>
                <div class="peta-stat-label">Kategori</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_city_selector():
    """
    Render city selector buttons for Makkah and Madinah.

    Returns the currently selected city string.
    """
    selected = st.session_state.peta_selected_city

    col1, col2 = st.columns(2)

    with col1:
        makkah_config = CITY_CONFIG["makkah"]
        btn_type = "primary" if selected == "makkah" else "secondary"
        if st.button(
            f"{makkah_config['icon']}  {makkah_config['name']}\n{makkah_config['name_ar']}",
            use_container_width=True,
            type=btn_type,
            key="btn_city_makkah",
        ):
            if selected != "makkah":
                st.session_state.peta_selected_city = "makkah"
                st.session_state.peta_selected_poi = None
                st.rerun()

    with col2:
        madinah_config = CITY_CONFIG["madinah"]
        btn_type = "primary" if selected == "madinah" else "secondary"
        if st.button(
            f"{madinah_config['icon']}  {madinah_config['name']}\n{madinah_config['name_ar']}",
            use_container_width=True,
            type=btn_type,
            key="btn_city_madinah",
        ):
            if selected != "madinah":
                st.session_state.peta_selected_city = "madinah"
                st.session_state.peta_selected_poi = None
                st.rerun()

    return st.session_state.peta_selected_city


def render_category_filters(selected_city):
    """
    Render category filter checkboxes.

    Returns list of active category value strings.
    """
    from data.peta_locations import CATEGORY_INFO

    st.markdown("#### Filter Kategori")

    categories = list(CATEGORY_INFO.keys())
    active_categories = []

    row1_cols = st.columns(3)
    row2_cols = st.columns(3)

    for i, cat_key in enumerate(categories):
        cat_info = CATEGORY_INFO[cat_key]
        col = row1_cols[i] if i < 3 else row2_cols[i - 3]

        with col:
            checked = st.checkbox(
                f"{cat_info['icon']} {cat_info['name']}",
                value=cat_key in st.session_state.peta_selected_categories,
                key=f"cat_{selected_city}_{cat_key}",
            )
            if checked:
                active_categories.append(cat_key)

    st.session_state.peta_selected_categories = active_categories
    return active_categories


def render_statistics(filtered_pois):
    """Show POI count cards grouped by category."""
    from data.peta_locations import CATEGORY_INFO

    # Count per category
    category_counts = {}
    for poi in filtered_pois:
        cat = poi["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Total count
    total = len(filtered_pois)

    # Build stat cards
    active_cats = [c for c in CATEGORY_INFO.keys() if c in category_counts]

    if not active_cats:
        st.info("Tidak ada lokasi yang cocok dengan filter. Coba aktifkan lebih banyak kategori.")
        return

    # Display total prominently
    st.markdown(f"""
    <div class="peta-stats-card" style="margin-bottom: 1rem;">
        <div class="number" style="color: #d4af37;">{total}</div>
        <div class="label">Total Lokasi Ditampilkan</div>
    </div>
    """, unsafe_allow_html=True)

    # Per-category breakdown
    cols = st.columns(min(len(active_cats), 3))
    for i, cat_key in enumerate(active_cats):
        cat_info = CATEGORY_INFO[cat_key]
        count = category_counts[cat_key]
        col_idx = i % min(len(active_cats), 3)
        with cols[col_idx]:
            st.markdown(f"""
            <div class="peta-stats-card">
                <div class="number" style="color: {cat_info['color']};">{count}</div>
                <div class="label">{cat_info['icon']} {cat_info['name']}</div>
            </div>
            """, unsafe_allow_html=True)


def create_map(city, filtered_pois):
    """
    Create a folium.Map with markers for all filtered POIs.

    Returns the folium Map object.
    """
    import folium
    from folium import plugins

    city_config = CITY_CONFIG[city]

    m = folium.Map(
        location=city_config["center"],
        zoom_start=city_config["zoom"],
        tiles="OpenStreetMap",
        control_scale=True,
    )

    ref_coords = city_config["reference_coords"]

    for poi in filtered_pois:
        dist = calculate_distance(
            poi["lat"], poi["lng"], ref_coords[0], ref_coords[1]
        )

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 220px; max-width: 280px;">
            <h4 style="margin: 0 0 4px 0; color: {poi['color']};">{poi['icon']} {poi['name']}</h4>
            <p style="margin: 0 0 8px 0; font-size: 0.8rem; color: #b0b0b0; direction: rtl;">{poi['name_ar']}</p>
            <p style="margin: 0 0 6px 0; font-size: 0.85rem;">{poi['description']}</p>
            <div style="background: #f5f5f5; padding: 8px; border-radius: 6px; margin: 8px 0;">
                <strong>Jarak ke {city_config['reference_name']}:</strong> {dist['distance_km']:.2f} km<br>
                <strong>Jalan kaki:</strong> ~{dist['walk_minutes']} menit
            </div>
            <div style="background: #fff8e1; padding: 8px; border-radius: 6px; margin: 8px 0;">
                <strong>Tips:</strong><br>{poi['tips']}
            </div>
        </div>
        """

        folium.Marker(
            location=[poi["lat"], poi["lng"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{poi['icon']} {poi['name']}",
            icon=folium.Icon(
                color=get_folium_color(poi["color"]),
                icon="info-sign",
                prefix="glyphicon",
            ),
        ).add_to(m)

    # Add reference point marker (Haram/Nabawi) with special star icon
    folium.Marker(
        location=city_config["center"],
        popup=f"<b>{city_config['reference_name']}</b>",
        tooltip=city_config["reference_name"],
        icon=folium.Icon(color="darkgreen", icon="star", prefix="glyphicon"),
    ).add_to(m)

    return m


def render_map(city, filtered_pois):
    """
    Render the folium map using streamlit-folium.

    Handles missing library gracefully with installation instructions.
    """
    try:
        from streamlit_folium import st_folium

        m = create_map(city, filtered_pois)
        map_data = st_folium(
            m,
            width=None,
            height=500,
            key=f"map_{city}_{len(filtered_pois)}",
        )

        # Handle clicks - find nearest POI
        if map_data and map_data.get("last_object_clicked"):
            clicked = map_data["last_object_clicked"]
            clicked_lat = clicked.get("lat")
            clicked_lng = clicked.get("lng")

            if clicked_lat is not None and clicked_lng is not None:
                # Find nearest POI to clicked location
                min_dist = float("inf")
                nearest_poi = None

                for poi in filtered_pois:
                    dist = calculate_distance(
                        clicked_lat, clicked_lng, poi["lat"], poi["lng"]
                    )
                    if dist["distance_m"] < min_dist:
                        min_dist = dist["distance_m"]
                        nearest_poi = poi

                # If click is within 500m of a POI, select it
                if nearest_poi and min_dist < 500:
                    st.session_state.peta_selected_poi = nearest_poi["id"]

    except ImportError:
        st.error("Library peta belum terinstall.")
        st.code("pip install folium streamlit-folium", language="bash")
        st.info("Hubungi admin untuk mengaktifkan fitur ini.")


def render_poi_list(filtered_pois, city):
    """
    Render scrollable POI list below the map.

    Each POI displayed as a styled card with details and action buttons.
    """
    from data.peta_locations import CATEGORY_INFO

    city_config = CITY_CONFIG[city]
    ref_coords = city_config["reference_coords"]

    st.markdown(f"#### Daftar Lokasi di {city_config['name']}")

    if not filtered_pois:
        st.info("Tidak ada lokasi yang ditampilkan. Aktifkan filter kategori di atas.")
        return

    for poi in filtered_pois:
        dist = calculate_distance(
            poi["lat"], poi["lng"], ref_coords[0], ref_coords[1]
        )
        cat_info = CATEGORY_INFO.get(poi["category"], {})
        cat_name = cat_info.get("name", poi["category"])
        cat_color = poi.get("color", "#d4af37")

        # Styled card
        st.markdown(f"""
        <div class="peta-poi-card" style="border-left-color: {cat_color};">
            <div class="peta-poi-header">
                <div>
                    <p class="peta-poi-title">{poi['icon']} {poi['name']}</p>
                    <p class="peta-poi-title-ar">{poi['name_ar']}</p>
                </div>
                <span class="peta-category-badge" style="background: {cat_color}22; color: {cat_color}; border: 1px solid {cat_color}44;">
                    {cat_info.get('icon', '')} {cat_name}
                </span>
            </div>
            <p class="peta-poi-desc">{poi['description']}</p>
            <div class="peta-poi-meta">
                <span class="peta-poi-distance">
                    Jarak: {dist['distance_km']:.2f} km | Jalan kaki: ~{dist['walk_minutes']} menit
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if st.button(
                f"Detail {poi['name']}",
                key=f"detail_{poi['id']}",
                use_container_width=True,
            ):
                st.session_state.peta_selected_poi = poi["id"]
                st.rerun()

        with btn_col2:
            if st.button(
                f"Tanya AI tentang {poi['name']}",
                key=f"ai_{poi['id']}",
                use_container_width=True,
            ):
                st.session_state.peta_selected_poi = poi["id"]
                render_ai_tips(poi)

        # Show detail if this POI is selected
        if st.session_state.peta_selected_poi == poi["id"]:
            with st.container():
                st.markdown(f"""
                <div class="peta-poi-card" style="border-left-color: {cat_color}; background: linear-gradient(145deg, #16213e 0%, #1a2a4a 100%);">
                    <h4 style="color: {cat_color}; margin-top: 0;">{poi['icon']} Detail: {poi['name']}</h4>
                    <p style="color: #d4af37; font-family: 'Amiri', serif; direction: rtl; font-size: 1.1rem;">{poi['name_ar']}</p>
                    <p style="color: #ccc; line-height: 1.6;">{poi['description']}</p>
                    <div style="background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 8px; margin-top: 0.75rem;">
                        <strong style="color: #d4af37;">Tips:</strong>
                        <p style="color: #ccc; margin: 0.25rem 0 0 0;">{poi['tips']}</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 8px; margin-top: 0.5rem;">
                        <strong style="color: #d4af37;">Jarak ke {city_config['reference_name']}:</strong>
                        <span style="color: #ccc;"> {dist['distance_km']:.2f} km (~{dist['walk_minutes']} menit jalan kaki)</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 8px; margin-top: 0.5rem;">
                        <strong style="color: #d4af37;">Koordinat:</strong>
                        <span style="color: #ccc;"> {poi['lat']}, {poi['lng']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # AI tips section
                render_ai_tips(poi)

        st.markdown("")  # spacing


def generate_ai_tips(poi):
    """
    Get AI tips for a POI using Groq service.

    Checks cache first, then calls AI if not cached.
    Returns response string or None.
    """
    # Check cache
    cached = st.session_state.peta_ai_tips_cache.get(poi["id"])
    if cached:
        return cached

    # Build prompt
    prompt = (
        f"Berikan tips lengkap untuk jamaah umrah Indonesia yang akan mengunjungi "
        f"{poi['name']} ({poi['name_ar']}).\n"
        f"Deskripsi lokasi: {poi['description']}\n"
        f"Tips dasar: {poi['tips']}\n\n"
        f"Berikan tips yang lebih detail dan praktis."
    )

    response = ai_complete(prompt, system_prompt=AI_SYSTEM_PROMPT, max_tokens=512)

    # Cache response if successful
    if response:
        st.session_state.peta_ai_tips_cache[poi["id"]] = response

        # Award XP on first AI tips usage
        if len(st.session_state.peta_ai_tips_cache) == 1:
            _add_xp(20, "Pertama kali menggunakan AI Tips Peta")

    return response


def render_ai_tips(poi):
    """
    Render AI tips section for a POI.

    Shows a button to request AI tips, displays cached or new response,
    and falls back to static tips from POI data if AI is unavailable.
    """
    # Check if tips already cached
    cached_tips = st.session_state.peta_ai_tips_cache.get(poi["id"])

    if cached_tips:
        st.markdown(f"""
        <div class="peta-ai-card" role="status" aria-live="polite">
            <h4>AI Tips: {poi['icon']} {poi['name']}</h4>
            <p>{cached_tips}</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if st.button(
        f"Tanya AI tentang lokasi ini",
        key=f"ask_ai_{poi['id']}",
        use_container_width=True,
    ):
        with st.spinner("AI sedang menyiapkan tips untuk Anda..."):
            response = generate_ai_tips(poi)

        if response:
            st.markdown(f"""
            <div class="peta-ai-card" role="status" aria-live="polite">
                <h4>AI Tips: {poi['icon']} {poi['name']}</h4>
                <p>{response}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback to static tips
            st.markdown(f"""
            <div class="peta-ai-card" role="status" aria-live="polite" style="border-color: #d4af37;">
                <h4 style="color: #d4af37;">Tips: {poi['icon']} {poi['name']}</h4>
                <p>{poi['tips']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.caption("AI tips tidak tersedia saat ini. Menampilkan tips bawaan.")


def render_walking_calculator(city):
    """
    Render walking distance calculator from user coordinates to reference point.

    Allows user to input their hotel coordinates and calculates distance
    with color-coded recommendations.
    """
    city_config = CITY_CONFIG[city]
    ref_name = city_config["reference_name"]
    ref_lat, ref_lng = city_config["reference_coords"]

    st.markdown(f"#### Kalkulator Jarak Jalan Kaki ke {ref_name}")

    st.caption(
        "Hitung estimasi jarak dan waktu jalan kaki dari hotel Anda ke "
        f"{ref_name}."
    )

    st.info(
        "**Tip:** Buka Google Maps, tekan lama pada lokasi hotel Anda, "
        "lalu salin koordinat yang muncul."
    )

    col1, col2 = st.columns(2)

    with col1:
        user_lat = st.number_input(
            "Latitude Hotel Anda",
            value=ref_lat,
            format="%.6f",
            step=0.0001,
            key=f"walk_lat_{city}",
        )

    with col2:
        user_lng = st.number_input(
            "Longitude Hotel Anda",
            value=ref_lng,
            format="%.6f",
            step=0.0001,
            key=f"walk_lng_{city}",
        )

    if st.button(
        "Hitung Jarak",
        use_container_width=True,
        type="primary",
        key=f"btn_walk_calc_{city}",
    ):
        dist = calculate_distance(user_lat, user_lng, ref_lat, ref_lng)
        distance_m = dist["distance_m"]
        distance_km = dist["distance_km"]
        walk_min = dist["walk_minutes"]
        taxi_min = max(1, int(distance_m / 333.3))  # ~20 km/h in city traffic

        # Color-coded recommendation
        if distance_m < 500:
            rec_class = "peta-rec-green"
            rec_text = "Sangat dekat! Anda bisa jalan kaki dengan mudah."
            rec_icon = "✅"
        elif distance_m < 1500:
            rec_class = "peta-rec-blue"
            rec_text = "Cukup dekat, bisa jalan kaki dengan nyaman."
            rec_icon = "🚶"
        elif distance_m < 3000:
            rec_class = "peta-rec-yellow"
            rec_text = "Disarankan naik bus atau taksi untuk kenyamanan."
            rec_icon = "🚌"
        else:
            rec_class = "peta-rec-red"
            rec_text = "Gunakan transportasi (bus/taksi). Jarak cukup jauh untuk jalan kaki."
            rec_icon = "🚕"

        st.markdown(f"""
        <div class="peta-walk-result">
            <h4>Hasil Perhitungan Jarak ke {ref_name}</h4>
            <div class="peta-walk-metric">
                <span class="metric-label">Jarak</span>
                <span class="metric-value">{distance_km:.2f} km ({distance_m:.0f} m)</span>
            </div>
            <div class="peta-walk-metric">
                <span class="metric-label">Estimasi Jalan Kaki</span>
                <span class="metric-value">~{walk_min} menit</span>
            </div>
            <div class="peta-walk-metric">
                <span class="metric-label">Estimasi Taksi/Bus</span>
                <span class="metric-value">~{taxi_min} menit</span>
            </div>
            <div class="peta-recommendation {rec_class}">
                {rec_icon} {rec_text}
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# CROWD PREDICTION OVERLAY
# =============================================================================

# Key locations with coordinates for crowd prediction
CROWD_LOCATIONS = [
    {"name": "Masjidil Haram", "name_ar": "المسجد الحرام", "lat": 21.4225, "lon": 39.8262, "city": "makkah", "icon": "🕋"},
    {"name": "Masjid Nabawi", "name_ar": "المسجد النبوي", "lat": 24.4672, "lon": 39.6112, "city": "madinah", "icon": "🕌"},
    {"name": "Jabal Rahmah", "name_ar": "جبل الرحمة", "lat": 21.3549, "lon": 39.9842, "city": "makkah", "icon": "⛰️"},
    {"name": "Mina", "name_ar": "منى", "lat": 21.4133, "lon": 39.8933, "city": "makkah", "icon": "🏕️"},
    {"name": "Arafah", "name_ar": "عرفات", "lat": 21.3547, "lon": 39.9842, "city": "makkah", "icon": "🏔️"},
    {"name": "Muzdalifah", "name_ar": "مزدلفة", "lat": 21.3997, "lon": 39.9000, "city": "makkah", "icon": "🌄"},
]


def _get_crowd_color_class(level: int) -> str:
    """Return CSS class suffix based on crowd level."""
    if level <= 30:
        return "green"
    elif level <= 60:
        return "yellow"
    elif level <= 80:
        return "orange"
    else:
        return "red"


def _get_crowd_label(level: int) -> str:
    """Return Indonesian label based on crowd level."""
    if level <= 30:
        return "Sepi"
    elif level <= 60:
        return "Ramai Sedang"
    elif level <= 80:
        return "Ramai"
    else:
        return "Sangat Padat"


def _get_crowd_hex(level: int) -> str:
    """Return hex color for crowd level (WCAG AA compliant)."""
    if level <= 30:
        return "#22c55e"
    elif level <= 60:
        return "#eab308"
    elif level <= 80:
        return "#f97316"
    else:
        return "#ef4444"


def _get_arabia_time() -> datetime:
    """Get current time in Arabia Standard Time (UTC+3)."""
    utc_now = datetime.now(timezone.utc)
    ast_offset = timedelta(hours=3)
    return utc_now + ast_offset


def _get_wib_to_arabia_label() -> str:
    """Return formatted time string showing WIB and Arabia time."""
    arabia = _get_arabia_time()
    wib = arabia + timedelta(hours=4)  # WIB = UTC+7 = AST+4
    return (
        f"{arabia.strftime('%H:%M')} WAS (Waktu Arab Saudi) | "
        f"{wib.strftime('%H:%M')} WIB"
    )


def _predict_crowd_for_location(loc: Dict, predictor, target_time: datetime = None) -> Dict:
    """
    Get crowd prediction for a location using CrowdPredictor.

    Falls back to a deterministic demo value if predictor is None.
    """
    if predictor is not None:
        city = loc.get("city", "makkah")
        result = predictor.predict(location=city, target_time=target_time)
        return result

    # Demo/static fallback when CrowdPredictor is unavailable
    arabia = target_time or _get_arabia_time()
    hour = arabia.hour
    # Simple sine-based approximation for demo purposes
    base = 40 + int(30 * math.sin(math.pi * (hour - 4) / 12))
    level = max(5, min(95, base))
    label = _get_crowd_label(level)
    color = _get_crowd_hex(level)
    return {
        "level": level,
        "description": label,
        "color": color,
        "emoji": "",
        "recommendation": "Data demo - aktifkan modul crowd_prediction untuk prediksi akurat.",
        "current_prayer": "",
        "time": arabia.strftime("%H:%M") if hasattr(arabia, "strftime") else "--:--",
        "season": "regular",
    }


def render_crowd_legend():
    """Render the color legend for crowd levels."""
    st.markdown("""
    <div class="crowd-legend" role="img" aria-label="Legenda tingkat keramaian">
        <div class="crowd-legend-item">
            <span class="crowd-legend-dot" style="background: #22c55e;"></span>
            Sepi (0-30%)
        </div>
        <div class="crowd-legend-item">
            <span class="crowd-legend-dot" style="background: #eab308;"></span>
            Ramai Sedang (31-60%)
        </div>
        <div class="crowd-legend-item">
            <span class="crowd-legend-dot" style="background: #f97316;"></span>
            Ramai (61-80%)
        </div>
        <div class="crowd-legend-item">
            <span class="crowd-legend-dot" style="background: #ef4444;"></span>
            Sangat Padat (81-100%)
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_crowd_overlay(selected_city: str):
    """
    Render crowd prediction overlay section for the interactive map page.

    Shows crowd levels for key Umrah locations with color-coded cards,
    current Arabia time, prayer time indicator, and a time slider for
    predicting crowd at different hours.
    """
    # Initialize predictor (or None for demo mode)
    predictor = None
    is_demo = True
    if HAS_CROWD_PREDICTION:
        try:
            predictor = CrowdPredictor()
            is_demo = False
        except Exception:
            pass

    arabia_now = _get_arabia_time()

    # --- Current time display ---
    time_label = _get_wib_to_arabia_label()
    prayer_text = ""
    if predictor is not None:
        sample = predictor.predict(location=selected_city, target_time=arabia_now)
        prayer_text = sample.get("current_prayer", "")

    prayer_html = ""
    if prayer_text:
        prayer_html = f'<span class="prayer-badge">{prayer_text}</span>'

    st.markdown(f"""
    <div class="crowd-time-display">
        <div>
            <div class="time-label">Waktu Saat Ini</div>
            <div class="time-value">{time_label}</div>
        </div>
        {prayer_html}
    </div>
    """, unsafe_allow_html=True)

    if is_demo:
        st.caption("Mode demo - instal modul crowd_prediction untuk prediksi akurat.")

    # --- Time slider ---
    slider_hour = st.slider(
        "Prediksi keramaian pada jam (Waktu Arab Saudi):",
        min_value=0,
        max_value=23,
        value=arabia_now.hour,
        format="%02d:00",
        key="crowd_time_slider",
    )

    target_time = arabia_now.replace(hour=slider_hour, minute=0, second=0, microsecond=0)

    # --- Filter locations by selected city ---
    locations = [
        loc for loc in CROWD_LOCATIONS
        if loc["city"] == selected_city
    ]

    if not locations:
        st.info("Tidak ada lokasi prediksi keramaian untuk kota ini.")
        return

    # --- Render cards for each location ---
    for loc in locations:
        prediction = _predict_crowd_for_location(loc, predictor, target_time)
        level = prediction["level"]
        color_class = _get_crowd_color_class(level)
        label = _get_crowd_label(level)
        hex_color = _get_crowd_hex(level)
        recommendation = prediction.get("recommendation", "")

        st.markdown(f"""
        <div class="crowd-location-card crowd-{color_class}" role="status" aria-live="polite"
             aria-label="{loc['name']}: keramaian {level}% - {label}">
            <span class="crowd-level-indicator indicator-{color_class}"
                  aria-hidden="true"></span>
            <div class="crowd-location-info">
                <p class="crowd-location-name">
                    <span aria-hidden="true">{loc['icon']}</span> {loc['name']}
                    <span style="color: #b0b0b0; font-size: 0.8rem; font-family: 'Amiri', serif; direction: rtl; margin-left: 0.5rem;">{loc['name_ar']}</span>
                </p>
                <p class="crowd-location-level" style="color: {hex_color}; font-weight: 600;">
                    {label}
                </p>
                <p class="crowd-location-rec">{recommendation}</p>
            </div>
            <div class="crowd-location-pct" style="color: {hex_color};">
                {level}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Legend ---
    render_crowd_legend()


# =============================================================================
# MAIN PAGE FUNCTION
# =============================================================================

def render_peta_interaktif_page():
    """Main entry point for the Peta Interaktif page."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("peta")
    except Exception:
        pass

    # Initialize state
    init_peta_state()

    # Hero
    render_hero()

    # City selector
    selected_city = render_city_selector()

    st.markdown("")  # spacing

    # Tabs: Peta & Lokasi | Prediksi Keramaian
    tab_peta, tab_crowd = st.tabs(["🗺️ Peta & Lokasi", "📊 Prediksi Keramaian"])

    # ---- Tab 1: Map & POIs (original content) ----
    with tab_peta:
        # Category filters
        active_categories = render_category_filters(selected_city)

        # Get filtered POIs
        from data.peta_locations import get_pois_by_city

        all_pois = get_pois_by_city(selected_city)
        filtered_pois = [
            poi for poi in all_pois if poi["category"] in active_categories
        ]

        # Statistics
        render_statistics(filtered_pois)

        st.markdown("---")

        # Map rendering
        if filtered_pois:
            with st.spinner("Memuat peta..."):
                render_map(selected_city, filtered_pois)
        else:
            st.warning("Tidak ada lokasi untuk ditampilkan. Aktifkan setidaknya satu kategori.")

        st.markdown("")  # spacing

        # POI list below map
        render_poi_list(filtered_pois, selected_city)

        st.markdown("---")

        # Walking calculator in expander
        with st.expander("🚶 Kalkulator Jarak Jalan Kaki", expanded=False):
            render_walking_calculator(selected_city)

    # ---- Tab 2: Crowd Prediction Overlay ----
    with tab_crowd:
        st.markdown("""
        <div class="crowd-overlay-section">
            <h3><span aria-hidden="true">📊</span> Prediksi Keramaian Lokasi Umrah</h3>
            <p style="color: #b0b0b0; margin-top: -0.5rem; margin-bottom: 0;">
                Estimasi tingkat keramaian berdasarkan waktu, hari, dan musim.
            </p>
        </div>
        """, unsafe_allow_html=True)

        render_crowd_overlay(selected_city)

        # XP: +10 for viewing crowd prediction (first time only)
        if not st.session_state.get("peta_crowd_xp_awarded"):
            st.session_state.peta_crowd_xp_awarded = True
            _add_xp(10, "Melihat prediksi keramaian di Peta Interaktif")

    # Gamification: +5 XP first time visiting each city map
    city_key = f"peta_{selected_city}"
    if city_key not in st.session_state.peta_visited_cities:
        st.session_state.peta_visited_cities.add(city_key)
        city_name = CITY_CONFIG[selected_city]["name"]
        _add_xp(5, f"Menjelajahi peta {city_name}")

    # Disclaimer
    st.markdown("---")
    st.warning(
        "**Disclaimer:**\n\n"
        "Koordinat lokasi bersifat perkiraan dan mungkin tidak 100% akurat. "
        "Gunakan aplikasi navigasi seperti Google Maps untuk petunjuk arah yang tepat. "
        "Jarak dan waktu tempuh adalah estimasi dan dapat berbeda tergantung kondisi "
        "cuaca, keramaian, dan rute yang dipilih.\n\n"
        "**LABBAIK AI tidak bertanggung jawab atas ketidakakuratan data lokasi.**"
    )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_peta_interaktif_page"]
