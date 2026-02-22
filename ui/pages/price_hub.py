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
import random
import math

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SKELETON_CSS, render_skeleton
from ui.components import format_sar as format_price_sar, format_idr as format_price_idr

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

# Price Repository
try:
    from services.price_aggregation.repository import get_aggregated_price_repository
    HAS_PRICE_REPO = True
except ImportError:
    HAS_PRICE_REPO = False
    logger.warning("Price repository not available")

# n8n Adapter
try:
    from services.price_aggregation.n8n_adapter import get_n8n_adapter
    HAS_N8N_ADAPTER = True
except ImportError:
    HAS_N8N_ADAPTER = False
    logger.warning("n8n adapter not available")

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

# Risk Score Intelligence
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

# Geo Cluster & Deduplication
try:
    from services.intelligence.geo_cluster import deduplicate_hotels, merge_hotel_data
    HAS_GEO_CLUSTER = True
except ImportError:
    HAS_GEO_CLUSTER = False
    logger.warning("Geo cluster service not available")

# Plotly (optional, for enhanced charts)
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Pandas (optional, for st.line_chart DataFrame)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


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
    color: #b0b0b0;
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
    color: #b0b0b0;
}

/* AI analysis section */
.ai-analysis-section {
    margin-top: 1.5rem;
}

/* Price trend indicators */
.trend-up {
    color: #f87171;
    font-weight: bold;
    font-size: 0.85rem;
}

.trend-down {
    color: #4ade80;
    font-weight: bold;
    font-size: 0.85rem;
}

.trend-stable {
    color: #94a3b8;
    font-weight: bold;
    font-size: 0.85rem;
}

/* Best price tag */
.best-price-tag {
    display: inline-block;
    background: linear-gradient(135deg, #065f46 0%, #059669 100%);
    color: #ecfdf5;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: bold;
    margin-top: 4px;
}

/* Flight route display */
.flight-route {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.4rem 0;
}

.flight-route .city {
    color: #d4af37;
    font-weight: bold;
    font-size: 0.95rem;
}

.flight-route .arrow {
    color: #64748b;
    font-size: 1.1rem;
}

.flight-route .time {
    color: #94a3b8;
    font-size: 0.8rem;
}

/* Inclusion chip */
.inclusion-chip {
    display: inline-block;
    background: #1e293b;
    color: #94a3b8;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    margin: 2px 3px 2px 0;
    border: 1px solid #334155;
}

/* Freshness bar */
.freshness-bar {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0;
    font-size: 0.78rem;
    color: #94a3b8;
}

.freshness-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.freshness-dot.live {
    background: #4ade80;
    box-shadow: 0 0 4px #4ade80;
}

.freshness-dot.recent {
    background: #fbbf24;
}

.freshness-dot.stale {
    background: #f87171;
}

/* Risk score badge */
.risk-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: bold;
    margin-top: 4px;
    border: 1px solid;
}

.risk-badge.risk-low {
    background: rgba(76, 175, 80, 0.15);
    color: #4CAF50;
    border-color: #4CAF50;
}

.risk-badge.risk-medium {
    background: rgba(255, 193, 7, 0.15);
    color: #FFC107;
    border-color: #FFC107;
}

.risk-badge.risk-high {
    background: rgba(255, 152, 0, 0.15);
    color: #FF9800;
    border-color: #FF9800;
}

.risk-badge.risk-critical {
    background: rgba(244, 67, 54, 0.15);
    color: #F44336;
    border-color: #F44336;
}

.risk-tooltip {
    font-size: 0.72rem;
    color: #b0b0b0;
    margin-top: 2px;
    font-style: italic;
}

/* Merged hotel indicator */
.merge-indicator {
    display: inline-block;
    background: #1e293b;
    color: #b8c5d4;
    padding: 2px 8px;
    border-radius: 8px;
    font-size: 0.72rem;
    margin-top: 4px;
    border: 1px solid #334155;
}

/* Risk legend section */
.risk-legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.3rem 0;
}

.risk-legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

.risk-legend-label {
    color: #e2e8f0;
    font-size: 0.82rem;
    font-weight: 600;
}

.risk-legend-desc {
    color: #b0b0b0;
    font-size: 0.78rem;
}

/* Source stat card */
.source-stat-card {
    background: #1e293b;
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    border: 1px solid #334155;
    margin-bottom: 0.3rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.source-stat-card .source-label {
    color: #e2e8f0;
    font-size: 0.8rem;
    font-weight: 600;
}

.source-stat-card .source-count {
    color: #d4af37;
    font-weight: bold;
    font-size: 0.9rem;
}

/* Price History Section */
.price-history-section {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 15px;
    padding: 1.5rem;
    margin-top: 1.5rem;
}

.price-history-section h3 {
    color: #d4af37;
    margin-bottom: 0.5rem;
}

.price-history-section .section-subtitle {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}

/* Price stat cards (min/max/avg) */
.price-stat-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    text-align: center;
}

.price-stat-card .stat-label {
    color: #b0b0b0;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.price-stat-card .stat-value {
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: bold;
    margin-top: 0.25rem;
}

.price-stat-card.stat-min .stat-value {
    color: #4ade80;
}

.price-stat-card.stat-max .stat-value {
    color: #f87171;
}

.price-stat-card.stat-avg .stat-value {
    color: #d4af37;
}

/* Price trend indicators */
.price-trend-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: bold;
}

.price-trend-indicator.trend-indicator-up {
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.3);
}

.price-trend-indicator.trend-indicator-down {
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.3);
}

.price-trend-indicator.trend-indicator-stable {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.3);
}

/* Best time recommendation */
.best-time-box {
    background: linear-gradient(135deg, #065f46 0%, #064e3b 100%);
    border: 1px solid #059669;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-top: 0.75rem;
}

.best-time-box .best-time-label {
    color: #6ee7b7;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: bold;
}

.best-time-box .best-time-value {
    color: #ecfdf5;
    font-size: 0.9rem;
    margin-top: 0.25rem;
}

.price-history-note {
    color: #8e9fb3;
    font-size: 0.75rem;
    font-style: italic;
    margin-top: 0.75rem;
    padding-top: 0.5rem;
    border-top: 1px solid #334155;
}
"""


# =============================================================================
# CONSTANTS
# =============================================================================

from core.constants import CostConstants
SAR_TO_IDR = CostConstants.SAR_TO_IDR

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

ORIGIN_CITIES = [
    "Jakarta", "Surabaya", "Medan", "Makassar",
    "Bandung", "Yogyakarta", "Semarang", "Denpasar",
]

TRAVEL_AGENTS = [
    "cheria-travel", "alhijaz", "patuna", "maktour", "arminareka",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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
    if "price_hub_flight_result" not in st.session_state:
        st.session_state.price_hub_flight_result = None
    if "price_hub_flight_params" not in st.session_state:
        st.session_state.price_hub_flight_params = {}
    if "price_hub_package_result" not in st.session_state:
        st.session_state.price_hub_package_result = None
    if "price_hub_package_params" not in st.session_state:
        st.session_state.price_hub_package_params = {}
    if "price_hub_source_stats" not in st.session_state:
        st.session_state.price_hub_source_stats = None
    if "price_hub_source_stats_time" not in st.session_state:
        st.session_state.price_hub_source_stats_time = None
    if "price_history_data" not in st.session_state:
        st.session_state.price_history_data = {}
    if "price_hub_history_xp_awarded" not in st.session_state:
        st.session_state.price_hub_history_xp_awarded = False


# =============================================================================
# CACHED SOURCE STATS & HELPERS
# =============================================================================

def get_source_stats_cached() -> Dict[str, Any]:
    """Get n8n source stats with 10-minute session cache."""
    now = datetime.now()
    cached_time = st.session_state.get("price_hub_source_stats_time")
    cached_stats = st.session_state.get("price_hub_source_stats")

    if cached_stats and cached_time:
        elapsed = (now - cached_time).total_seconds()
        if elapsed < 600:
            return cached_stats

    if not HAS_N8N_ADAPTER:
        return {"hotels": {"count": 0, "last_update": None},
                "flights": {"count": 0, "last_update": None},
                "packages": {"count": 0, "last_update": None}}

    try:
        adapter = get_n8n_adapter()
        stats = adapter.get_source_stats()
        st.session_state.price_hub_source_stats = stats
        st.session_state.price_hub_source_stats_time = now
        return stats
    except Exception as e:
        logger.error(f"Failed to get source stats: {e}")
        return {"hotels": {"count": 0, "last_update": None},
                "flights": {"count": 0, "last_update": None},
                "packages": {"count": 0, "last_update": None}}


def render_freshness_bar(source_type: str, stats: Dict[str, Any]):
    """Render data freshness indicator."""
    info = stats.get(source_type, {})
    last_update_str = info.get("last_update")

    if not last_update_str:
        dot_cls = "stale"
        label = "Belum ada data"
    else:
        try:
            last_dt = datetime.fromisoformat(last_update_str)
            diff = datetime.now() - last_dt
            hours_ago = diff.total_seconds() / 3600

            if hours_ago < 1:
                dot_cls = "live"
                minutes = int(diff.total_seconds() / 60)
                label = f"Diperbarui {minutes} menit lalu"
            elif hours_ago < 12:
                dot_cls = "recent"
                label = f"Diperbarui {int(hours_ago)} jam lalu"
            else:
                dot_cls = "stale"
                label = f"Diperbarui {int(hours_ago)} jam lalu"
        except Exception:
            dot_cls = "stale"
            label = "Waktu tidak diketahui"

    freshness_html = (
        '<div class="freshness-bar">'
        '<span class="freshness-dot ' + dot_cls + '"></span>'
        '<span>' + label + '</span>'
        '</div>'
    )
    st.markdown(freshness_html, unsafe_allow_html=True)


def render_trend_indicator(offer_id: Optional[str]):
    """Render price trend arrow from price history."""
    if not offer_id or not HAS_PRICE_REPO:
        return

    try:
        repo = get_aggregated_price_repository()
        trend = repo.get_price_trend(offer_id)
        if not trend:
            return

        direction = trend.direction
        pct = abs(trend.change_percent)

        if hasattr(direction, 'value'):
            direction_val = direction.value
        else:
            direction_val = str(direction)

        if direction_val == "up":
            css_class = "trend-up"
            arrow = "&#9650;"
            sign = "+"
        elif direction_val == "down":
            css_class = "trend-down"
            arrow = "&#9660;"
            sign = "-"
        else:
            css_class = "trend-stable"
            arrow = "&#9644;"
            sign = ""

        trend_html = (
            '<span class="' + css_class + '">'
            + arrow + ' ' + sign + f'{pct:.1f}%</span>'
        )
        st.markdown(trend_html, unsafe_allow_html=True)
    except Exception:
        pass


def _build_source_badge_html(source_name: str) -> str:
    """Build an HTML source badge."""
    badge_label, badge_color = get_source_badge(source_name)
    return (
        '<span class="source-badge" style="background-color:'
        + badge_color + ';">' + badge_label + '</span>'
    )


def _compute_risk_for_dates(check_in_str: str, check_out_str: str) -> Optional[Dict]:
    """
    Compute risk level based on search dates using seasonal + urgency scores.

    Returns dict with level, score, color, badge_text, tooltip or None.
    """
    if not HAS_RISK_SCORE:
        return None

    try:
        calculator = get_risk_calculator()

        # Parse dates
        if isinstance(check_in_str, str):
            checkin_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        elif isinstance(check_in_str, date):
            checkin_date = check_in_str
        else:
            return None

        # Calculate seasonal and urgency scores
        seasonal_score, seasonal_reasons = calculator.calculate_seasonal_score(checkin_date)
        urgency_score, urgency_reasons = calculator.calculate_urgency_score(checkin_date)

        # Composite: 60% seasonal + 40% urgency
        composite = int(seasonal_score * 0.6 + urgency_score * 0.4)
        composite = min(100, max(0, composite))

        # Map to risk level
        if composite >= 81:
            level = RiskLevel.CRITICAL
        elif composite >= 61:
            level = RiskLevel.HIGH
        elif composite >= 31:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        color = format_risk_color(level)

        # Indonesian badge text and tooltips
        badge_texts = {
            RiskLevel.LOW: "Risiko Rendah",
            RiskLevel.MEDIUM: "Risiko Sedang",
            RiskLevel.HIGH: "Risiko Tinggi",
            RiskLevel.CRITICAL: "Risiko Kritis",
        }
        tooltips = {
            RiskLevel.LOW: "Harga stabil, ketersediaan tinggi. Aman untuk membandingkan.",
            RiskLevel.MEDIUM: "Permintaan mulai naik. Pertimbangkan untuk booking segera.",
            RiskLevel.HIGH: "Harga kemungkinan naik. Segera booking untuk harga terbaik.",
            RiskLevel.CRITICAL: "Peak season, harga tertinggi. Booking sekarang sebelum habis!",
        }

        reasons = seasonal_reasons + urgency_reasons

        return {
            "level": level,
            "score": composite,
            "color": color,
            "badge_text": badge_texts.get(level, "Tidak Diketahui"),
            "tooltip": tooltips.get(level, ""),
            "reasons": reasons,
        }

    except Exception as e:
        logger.error(f"Risk score computation failed: {e}")
        return None


def _render_risk_badge_html(risk_info: Dict) -> str:
    """Build HTML for a risk badge with tooltip."""
    level = risk_info["level"]
    css_class = f"risk-{level.value}"
    badge_text = risk_info["badge_text"]
    tooltip = risk_info["tooltip"]
    score = risk_info["score"]

    html = (
        '<div>'
        '<span class="risk-badge ' + css_class + '" '
        'title="' + tooltip + '">'
        + badge_text + ' (' + str(score) + ')'
        '</span>'
        '<div class="risk-tooltip">' + tooltip + '</div>'
        '</div>'
    )
    return html


def _render_risk_legend():
    """Render the Skor Risiko legend/explainer as an expandable section."""
    with st.expander("Skor Risiko — Panduan Level", expanded=False):
        levels = [
            ("#4CAF50", "Rendah", "Harga stabil, ketersediaan tinggi"),
            ("#FFC107", "Sedang", "Pertimbangkan untuk booking segera"),
            ("#FF9800", "Tinggi", "Harga kemungkinan naik, segera booking"),
            ("#F44336", "Kritis", "Peak season, harga tertinggi"),
        ]
        emojis = [
            "\U0001f7e2",  # green circle
            "\U0001f7e1",  # yellow circle
            "\U0001f7e0",  # orange circle
            "\U0001f534",  # red circle
        ]

        for i, (color, label, desc) in enumerate(levels):
            emoji = emojis[i]
            item_html = (
                '<div class="risk-legend-item">'
                '<span class="risk-legend-dot" style="background:' + color + ';" '
                'aria-hidden="true"></span>'
                '<span class="risk-legend-label">'
                '<span aria-hidden="true">' + emoji + '</span> ' + label + '</span>'
                '<span class="risk-legend-desc">— ' + desc + '</span>'
                '</div>'
            )
            st.markdown(item_html, unsafe_allow_html=True)

        st.caption(
            "Skor dihitung berdasarkan musim (60%) dan urgensi waktu check-in (40%). "
            "Semakin tinggi skor, semakin disarankan untuk segera booking."
        )


def _deduplicate_hotel_list(hotels: List[Dict], city: str) -> tuple:
    """
    Run geo-cluster deduplication on hotel list.

    Returns (deduplicated_hotels, clusters) or (hotels, []) if unavailable.
    """
    if not HAS_GEO_CLUSTER:
        return hotels, []

    try:
        deduped, clusters = deduplicate_hotels(hotels, city, auto_merge=True)
        return deduped, clusters
    except Exception as e:
        logger.error(f"Hotel deduplication failed: {e}")
        return hotels, []


def _get_alternate_names(hotel: Dict, clusters: list) -> List[str]:
    """Get alternate names for a hotel from cluster data."""
    if not clusters:
        return []

    hotel_id = hotel.get("hotel_id") or hotel.get("id")
    if not hotel_id:
        return []

    for cluster in clusters:
        member_ids = [
            m.get("hotel_id") or m.get("id") for m in cluster.members
        ]
        if hotel_id in member_ids:
            # Return names of other members (not this hotel)
            hotel_name = hotel.get("hotel_name") or hotel.get("name", "")
            alt_names = []
            for m in cluster.members:
                m_id = m.get("hotel_id") or m.get("id")
                m_name = m.get("hotel_name") or m.get("name", "")
                if m_id != hotel_id and m_name and m_name != hotel_name:
                    alt_names.append(m_name)
            return alt_names

    return []


def _get_connected_aggregator():
    """
    Get price aggregator AND connect HybridUmrahDataManager
    so Amadeus/Xotelo APIs are also queried alongside n8n tables.
    """
    if not HAS_AGGREGATOR:
        return None

    try:
        aggregator = get_price_aggregator()

        if HAS_DATA_MANAGER and aggregator._data_manager is None:
            try:
                dm = get_umrah_data_manager()
                aggregator.set_data_manager(dm)
                logger.info("Connected HybridUmrahDataManager to aggregator")
            except Exception as e:
                logger.warning(f"Could not connect data manager: {e}")

        return aggregator
    except Exception as e:
        logger.error(f"Failed to get connected aggregator: {e}")
        return None


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
                    '<div class="ai-card" role="status" aria-live="polite">'
                    '<h4>Rekomendasi AI</h4>'
                    '<p>' + ai_html + '</p>'
                    '</div>'
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
                "<strong>Range harga di " + city + ":</strong> "
                + currency + " " + f"{min_price:,.0f}" + " - "
                + currency + " " + f"{max_price:,.0f}"
                + " (rata-rata " + currency + " " + f"{avg_price:,.0f}" + ")/malam"
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
        '<div style="margin-bottom:0.5rem;">&bull; ' + t + '</div>' for t in tips
    )
    fallback_html = (
        '<div class="ai-card" role="status" aria-live="polite">'
        '<h4>Tips Harga Umrah</h4>'
        '<p>' + tip_items + '</p>'
        '</div>'
    )
    st.markdown(fallback_html, unsafe_allow_html=True)


# =============================================================================
# FLIGHT AI ANALYSIS
# =============================================================================

def _build_flight_summary(result: Dict) -> str:
    """Build a text summary of flight results for AI analysis."""
    flights = result.get("offers", [])
    if not flights:
        return ""

    lines = [
        f"Jumlah penerbangan ditemukan: {len(flights)}",
        "",
    ]
    for i, f in enumerate(flights[:10]):
        name = f.name if hasattr(f, 'name') else str(f)
        price = f.price_idr if hasattr(f, 'price_idr') else 0
        origin = f.departure_city if hasattr(f, 'departure_city') else ""
        dest = f.city if hasattr(f, 'city') else ""
        airline_name = f.airline if hasattr(f, 'airline') else ""
        lines.append(
            f"{i+1}. {name} - {airline_name} - "
            f"{origin} ke {dest} - Rp {price:,.0f}"
        )
    return "\n".join(lines)


def render_flight_ai_analysis(result: Dict):
    """Render AI analysis for flight results."""
    st.markdown("---")
    st.markdown("### Analisis Penerbangan AI")

    summary = _build_flight_summary(result)
    if not summary:
        st.info("Tidak ada data penerbangan untuk dianalisis.")
        return

    if st.button("Analisis Penerbangan dengan AI", type="secondary", key="btn_flight_ai"):
        with st.spinner("AI sedang menganalisis penerbangan..."):
            prompt_text = (
                "Analisis data penerbangan umrah berikut dan berikan "
                "rekomendasi penerbangan terbaik:\n\n"
                + summary + "\n\n"
                "Berikan:\n"
                "1. Rekomendasi penerbangan terbaik (value for money)\n"
                "2. Tips mendapatkan tiket murah\n"
                "3. Perbandingan maskapai\n"
                "4. Waktu terbaik untuk membeli tiket\n"
                "Jawab dalam bahasa Indonesia, singkat dan praktis."
            )

            system_prompt = (
                "Kamu adalah konsultan perjalanan Umrah berpengalaman yang membantu "
                "jamaah mendapatkan penerbangan terbaik."
            )

            response = ai_complete(
                prompt_text,
                system_prompt=system_prompt,
                max_tokens=800,
            )

            if response:
                ai_html = _markdown_to_html_simple(response)
                card_html = (
                    '<div class="ai-card" role="status" aria-live="polite">'
                    '<h4>Rekomendasi AI - Penerbangan</h4>'
                    '<p>' + ai_html + '</p>'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                if not st.session_state.get("price_hub_ai_xp_awarded", False):
                    st.session_state.price_hub_ai_xp_awarded = True
                    add_xp_safe(20, "Menggunakan AI analisis penerbangan umrah")
            else:
                st.info("AI tidak tersedia saat ini. Silakan coba lagi nanti.")
    else:
        st.caption(
            "Klik tombol di atas untuk mendapatkan analisis dan rekomendasi "
            "penerbangan dari AI."
        )


# =============================================================================
# PACKAGE AI ANALYSIS
# =============================================================================

def _build_package_summary(result: Dict) -> str:
    """Build a text summary of package results for AI analysis."""
    packages = result.get("offers", [])
    if not packages:
        return ""

    lines = [
        f"Jumlah paket ditemukan: {len(packages)}",
        "",
    ]
    for i, p in enumerate(packages[:10]):
        name = p.name if hasattr(p, 'name') else str(p)
        price = p.price_idr if hasattr(p, 'price_idr') else 0
        dur = p.duration_days if hasattr(p, 'duration_days') else 0
        dep = p.departure_city if hasattr(p, 'departure_city') else ""
        src = p.source_name if hasattr(p, 'source_name') else ""
        dur_str = f"{dur} hari" if dur else ""
        lines.append(
            f"{i+1}. {name} - {src} - {dep} - {dur_str} - Rp {price:,.0f}"
        )
    return "\n".join(lines)


def render_package_ai_analysis(result: Dict):
    """Render AI analysis for package results."""
    st.markdown("---")
    st.markdown("### Analisis Paket AI")

    summary = _build_package_summary(result)
    if not summary:
        st.info("Tidak ada data paket untuk dianalisis.")
        return

    if st.button("Analisis Paket dengan AI", type="secondary", key="btn_pkg_ai"):
        with st.spinner("AI sedang menganalisis paket..."):
            prompt_text = (
                "Analisis data paket umrah berikut dan berikan "
                "rekomendasi paket terbaik:\n\n"
                + summary + "\n\n"
                "Berikan:\n"
                "1. Rekomendasi paket terbaik (value for money)\n"
                "2. Perbandingan travel agent\n"
                "3. Tips memilih paket yang tepat\n"
                "4. Hal-hal yang perlu diperhatikan sebelum booking\n"
                "Jawab dalam bahasa Indonesia, singkat dan praktis."
            )

            system_prompt = (
                "Kamu adalah konsultan perjalanan Umrah berpengalaman yang membantu "
                "jamaah memilih paket umrah terbaik."
            )

            response = ai_complete(
                prompt_text,
                system_prompt=system_prompt,
                max_tokens=800,
            )

            if response:
                ai_html = _markdown_to_html_simple(response)
                card_html = (
                    '<div class="ai-card" role="status" aria-live="polite">'
                    '<h4>Rekomendasi AI - Paket Umrah</h4>'
                    '<p>' + ai_html + '</p>'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                if not st.session_state.get("price_hub_ai_xp_awarded", False):
                    st.session_state.price_hub_ai_xp_awarded = True
                    add_xp_safe(20, "Menggunakan AI analisis paket umrah")
            else:
                st.info("AI tidak tersedia saat ini. Silakan coba lagi nanti.")
    else:
        st.caption(
            "Klik tombol di atas untuk mendapatkan analisis dan rekomendasi "
            "paket dari AI."
        )


# =============================================================================
# PRICE HISTORY / TREND CHART
# =============================================================================

def _generate_price_history(base_price: float, days: int = 30) -> List[Dict]:
    """
    Generate simulated 30-day price trend data.

    Returns a list of dicts: {date, price, source}.
    Uses sin wave + random noise for realistic variation.
    Weekend prices are slightly higher (+3-5%).
    """
    random.seed(42)
    history = []
    today = datetime.now().date()
    sources = ["Booking.com", "Agoda", "Expedia", "Hotels.com", "Traveloka"]

    for i in range(days):
        day_date = today - timedelta(days=(days - 1 - i))

        # Base variation: sin wave for cyclical pattern (period ~10 days)
        sin_component = math.sin(2 * math.pi * i / 10) * 0.05

        # Slight upward trend (simulating peak season approach): +0.15% per day
        trend_component = i * 0.0015

        # Random daily noise: +/- 5-15%
        noise = random.uniform(-0.08, 0.10)

        # Weekend surcharge: Saturday=5 (Sat), Sunday=6 (Sun)
        weekend_factor = 0.0
        if day_date.weekday() == 5:  # Saturday
            weekend_factor = random.uniform(0.03, 0.05)
        elif day_date.weekday() == 6:  # Sunday
            weekend_factor = random.uniform(0.03, 0.04)

        # Combine all factors
        multiplier = 1.0 + sin_component + trend_component + noise + weekend_factor
        price = round(base_price * multiplier, 0)

        # Pick a random source for this data point
        source = sources[i % len(sources)]

        history.append({
            "date": day_date,
            "price": price,
            "source": source,
        })

    return history


def render_price_history_chart(city: str):
    """
    Render a 30-day price history/trend chart for a city.

    Uses session state cache to avoid regenerating data on every rerun.
    Shows min/max/average stats, trend indicator, and booking recommendation.
    """
    # Determine base price per city (SAR per night, typical 4-star)
    base_prices = {
        "Makkah": 450,
        "Madinah": 350,
        "Jeddah": 300,
    }
    base_price = base_prices.get(city, 400)

    # Cache key per city
    cache_key = f"history_{city}"
    cached = st.session_state.get("price_history_data", {})

    if cache_key not in cached:
        history = _generate_price_history(base_price, days=30)
        cached[cache_key] = history
        st.session_state.price_history_data = cached
    else:
        history = cached[cache_key]

    if not history:
        return

    # Gamification: +10 XP for viewing price history (first time)
    if not st.session_state.get("price_hub_history_xp_awarded", False):
        st.session_state.price_hub_history_xp_awarded = True
        add_xp_safe(10, "Melihat tren harga hotel umrah")

    # --- Section container ---
    st.markdown(
        '<div class="price-history-section">'
        '<h3><span aria-hidden="true">&#128200;</span> Tren Harga 30 Hari - ' + city + '</h3>'
        '<p class="section-subtitle">Estimasi pergerakan harga hotel per malam (SAR)</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # --- Compute stats ---
    prices = [h["price"] for h in history]
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)

    # Find date of min price
    min_entry = min(history, key=lambda h: h["price"])
    min_date = min_entry["date"]

    # Trend direction: compare average of last 7 days vs first 7 days
    first_week = history[:7]
    last_week = history[-7:]
    first_week_avg = sum(h["price"] for h in first_week) / len(first_week) if first_week else 0
    last_week_avg = sum(h["price"] for h in last_week) / len(last_week) if last_week else 0
    trend_pct = ((last_week_avg - first_week_avg) / first_week_avg) * 100 if first_week_avg else 0.0

    if trend_pct > 2:
        trend_dir = "up"
        trend_arrow = "&#9650;"
        trend_label = f"+{trend_pct:.1f}%"
        trend_css = "trend-indicator-up"
        trend_text = "Harga cenderung naik"
    elif trend_pct < -2:
        trend_dir = "down"
        trend_arrow = "&#9660;"
        trend_label = f"{trend_pct:.1f}%"
        trend_css = "trend-indicator-down"
        trend_text = "Harga cenderung turun"
    else:
        trend_dir = "stable"
        trend_arrow = "&#9644;"
        trend_label = f"{trend_pct:+.1f}%"
        trend_css = "trend-indicator-stable"
        trend_text = "Harga relatif stabil"

    # --- Stat cards: Min / Max / Avg ---
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    with stat_col1:
        st.markdown(
            '<div class="price-stat-card stat-min">'
            '<div class="stat-label">Terendah</div>'
            '<div class="stat-value">SAR ' + f'{min_price:,.0f}' + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with stat_col2:
        st.markdown(
            '<div class="price-stat-card stat-max">'
            '<div class="stat-label">Tertinggi</div>'
            '<div class="stat-value">SAR ' + f'{max_price:,.0f}' + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with stat_col3:
        st.markdown(
            '<div class="price-stat-card stat-avg">'
            '<div class="stat-label">Rata-rata</div>'
            '<div class="stat-value">SAR ' + f'{avg_price:,.0f}' + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with stat_col4:
        st.markdown(
            '<div class="price-stat-card">'
            '<div class="stat-label">Tren 30 Hari</div>'
            '<div class="stat-value">'
            '<span class="price-trend-indicator ' + trend_css + '">'
            + trend_arrow + ' ' + trend_label
            + '</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # --- Chart ---
    dates = [h["date"] for h in history]

    if HAS_PLOTLY:
        # Enhanced Plotly chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines+markers',
            name='Harga/Malam',
            line=dict(color='#d4af37', width=2),
            marker=dict(size=4, color='#d4af37'),
            fill='tozeroy',
            fillcolor='rgba(212, 175, 55, 0.1)',
        ))

        # Add min price marker
        fig.add_trace(go.Scatter(
            x=[min_date],
            y=[min_price],
            mode='markers+text',
            name='Harga Terendah',
            marker=dict(size=12, color='#4ade80', symbol='star'),
            text=[f'SAR {min_price:,.0f}'],
            textposition='top center',
            textfont=dict(color='#4ade80', size=11),
        ))

        # Average line
        fig.add_hline(
            y=avg_price,
            line_dash="dash",
            line_color="#94a3b8",
            annotation_text=f"Rata-rata: SAR {avg_price:,.0f}",
            annotation_position="top left",
            annotation_font_color="#94a3b8",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Tanggal",
            yaxis_title="Harga (SAR)",
            height=350,
            margin=dict(l=50, r=20, t=30, b=50),
            showlegend=False,
            xaxis=dict(gridcolor='#334155'),
            yaxis=dict(gridcolor='#334155'),
        )

        st.plotly_chart(fig, use_container_width=True)

    elif HAS_PANDAS:
        # Fallback: Streamlit built-in line chart with pandas DataFrame
        df = pd.DataFrame({
            "Tanggal": dates,
            "Harga (SAR)": prices,
        })
        st.line_chart(df.set_index("Tanggal")["Harga (SAR)"])

    else:
        # Minimal fallback: show data as metrics
        st.caption("Grafik tidak tersedia (pandas/plotly tidak terinstal)")
        recent_prices = prices[-7:]
        cols = st.columns(min(len(recent_prices), 7))
        for idx, p in enumerate(recent_prices):
            day_label = dates[-(7 - idx)].strftime("%d/%m")
            with cols[idx]:
                st.metric(day_label, f"SAR {p:,.0f}")

    # --- Best time to book recommendation ---
    # Find the day-of-week with lowest average price
    weekday_prices = {}
    for h in history:
        wd = h["date"].weekday()
        if wd not in weekday_prices:
            weekday_prices[wd] = []
        weekday_prices[wd].append(h["price"])

    weekday_avgs = {wd: sum(ps) / len(ps) for wd, ps in weekday_prices.items()}
    best_weekday = min(weekday_avgs, key=weekday_avgs.get)
    weekday_names = {
        0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
        4: "Jumat", 5: "Sabtu", 6: "Minggu",
    }
    best_day_name = weekday_names.get(best_weekday, "")
    best_day_avg = weekday_avgs[best_weekday]

    recommendation = (
        f"Berdasarkan tren 30 hari, hari <strong>{best_day_name}</strong> "
        f"cenderung memiliki harga terendah "
        f"(rata-rata SAR {best_day_avg:,.0f}/malam). "
    )

    if trend_dir == "up":
        recommendation += "Harga sedang naik — pertimbangkan untuk booking secepatnya."
    elif trend_dir == "down":
        recommendation += "Harga sedang turun — Anda bisa menunggu beberapa hari untuk harga lebih baik."
    else:
        recommendation += "Harga relatif stabil — waktu yang baik untuk membandingkan dan booking."

    st.markdown(
        '<div class="best-time-box">'
        '<div class="best-time-label">'
        '<span aria-hidden="true">&#128161;</span> Waktu Terbaik untuk Booking</div>'
        '<div class="best-time-value">' + recommendation + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # --- Disclaimer note ---
    st.markdown(
        '<p class="price-history-note">'
        'Data berdasarkan estimasi tren harga. '
        'Gunakan fitur Price Alert untuk notifikasi harga aktual.'
        '</p>',
        unsafe_allow_html=True,
    )


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


def render_hotel_card(
    hotel: Dict,
    nights: int = 1,
    show_vendors: bool = True,
    risk_info: Optional[Dict] = None,
    alt_names: Optional[List[str]] = None,
):
    """Render a single hotel card with vendor comparison, risk badge, and merge indicator."""

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

            # Merge indicator — show alternate names from deduplication
            try:
                if alt_names:
                    names_str = ", ".join(alt_names[:3])
                    merge_html = (
                        '<span class="merge-indicator">'
                        '<span aria-hidden="true">&#128279;</span> '
                        'Juga dikenal sebagai: ' + names_str
                        + '</span>'
                    )
                    st.markdown(merge_html, unsafe_allow_html=True)

                # Show merged count if hotel was merged from multiple providers
                if hotel.get("is_merged") and hotel.get("merged_count", 0) > 1:
                    count = hotel["merged_count"]
                    merged_html = (
                        '<span class="merge-indicator">'
                        '<span aria-hidden="true">&#128200;</span> '
                        'Data digabung dari ' + str(count) + ' sumber'
                        '</span>'
                    )
                    st.markdown(merged_html, unsafe_allow_html=True)
            except Exception:
                pass

        with col2:
            price = hotel.get('price_per_night', 0)
            currency = hotel.get('currency', 'SAR')

            st.markdown(f"### {currency} {price:,.0f}")
            st.caption("per malam")

            total = price * nights
            st.markdown(f"**Total: {currency} {total:,.0f}**")
            st.caption(f"untuk {nights} malam")

            # Risk score badge next to price
            try:
                if risk_info:
                    badge_html = _render_risk_badge_html(risk_info)
                    st.markdown(badge_html, unsafe_allow_html=True)
            except Exception:
                pass

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
                except Exception:
                    has_vendor_access = True  # Default to show

            if has_vendor_access:
                st.markdown(f"**Perbandingan dari {len(vendors)} OTA:**")

                vendor_cols = st.columns(min(len(vendors), 4))
                for i, vendor in enumerate(vendors[:4]):
                    with vendor_cols[i]:
                        v_name = vendor.get('name', 'OTA')
                        v_price = vendor.get('price', 0)
                        chip_html = (
                            '<div class="vendor-chip">'
                            '<div class="vendor-name">' + v_name + '</div>'
                            '<div class="vendor-price">' + currency + ' ' + f'{v_price:,.0f}' + '</div>'
                            '</div>'
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
    """Render hotel search results with risk scores and deduplication."""

    hotels = result.get('hotels', [])
    nights = 1

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

    # --- Geo-cluster deduplication ---
    city_name = result.get('city', 'Unknown')
    clusters = []
    dedup_count = 0
    try:
        original_count = len(hotels)
        hotels, clusters = _deduplicate_hotel_list(hotels, city_name)
        dedup_count = original_count - len(hotels)
    except Exception:
        pass

    # --- Compute risk score for these search dates ---
    risk_info = None
    try:
        ci_str = result.get('check_in')
        co_str = result.get('check_out')
        if ci_str:
            risk_info = _compute_risk_for_dates(ci_str, co_str)
    except Exception:
        pass

    # Header
    hotel_count = len(hotels)
    st.markdown(f"### {hotel_count} Hotel di {city_name}")

    source = result.get('source', 'unknown')
    if source == 'makcorps':
        st.success("Data real-time dari 200+ OTA")
    else:
        st.info("Data dari aggregator")

    ci = result.get('check_in')
    co = result.get('check_out')
    st.caption(f"Check-in: {ci} | Check-out: {co} | {nights} malam")

    # Show dedup info if duplicates were merged
    if dedup_count > 0:
        st.info(
            f"Ditemukan {dedup_count} duplikat hotel yang telah digabungkan secara otomatis."
        )

    # Risk score legend
    try:
        if risk_info:
            _render_risk_legend()
    except Exception:
        pass

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
        # Get alternate names from clusters
        alt_names = []
        try:
            alt_names = _get_alternate_names(hotel, clusters)
        except Exception:
            pass

        render_hotel_card(
            hotel,
            nights,
            risk_info=risk_info,
            alt_names=alt_names,
        )

    # Gamification: +25 XP for comparing prices (first time)
    if not st.session_state.get("price_hub_compare_xp_awarded", False):
        st.session_state.price_hub_compare_xp_awarded = True
        add_xp_safe(25, "Membandingkan harga hotel umrah")

    # Price History / Trend Chart
    render_price_history_chart(city_name)

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
            render_skeleton("cards", count=3)
            st.caption("Pilih kota dan tanggal untuk melihat perbandingan harga")


# =============================================================================
# FLIGHT TAB COMPONENTS
# =============================================================================

def render_flight_search_form() -> Optional[Dict]:
    """Render flight search form with full filter options."""

    col1, col2 = st.columns(2)

    with col1:
        origin = st.selectbox(
            "Kota Asal",
            options=ORIGIN_CITIES,
            index=0,
            key="flight_origin_v2"
        )

    with col2:
        destination = st.selectbox(
            "Tujuan",
            options=["Jeddah", "Madinah"],
            key="flight_dest_v2"
        )

    col1, col2 = st.columns(2)

    with col1:
        default_dep = (datetime.now() + timedelta(days=30)).date()
        departure_date = st.date_input(
            "Tanggal Berangkat",
            value=default_dep,
            min_value=datetime.now().date(),
            key="flight_date_v2"
        )

    with col2:
        ticket_class = st.selectbox(
            "Kelas",
            options=["Semua", "Economy", "Business"],
            index=0,
            key="flight_class_v2"
        )

    col1, col2 = st.columns(2)

    with col1:
        direct_only = st.checkbox("Hanya penerbangan langsung", key="flight_direct_v2")

    with col2:
        sort_option = st.selectbox(
            "Urutkan",
            options=["Harga Terendah", "Harga Tertinggi", "Terbaru"],
            index=0,
            key="flight_sort_v2"
        )

    if st.button("Cari Penerbangan", type="primary", use_container_width=True, key="search_flight_v2"):
        sort_map = {
            "Harga Terendah": "price",
            "Harga Tertinggi": "price_desc",
            "Terbaru": "updated",
        }
        return {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date.strftime("%Y-%m-%d"),
            "ticket_class": ticket_class,
            "direct_only": direct_only,
            "sort_by": sort_map.get(sort_option, "price"),
        }

    return None


def render_flight_card(flight: Any, best_price: float = 0):
    """Render enhanced flight offer card with route visualization."""

    is_best = False
    flight_price = flight.price_idr if hasattr(flight, 'price_idr') else 0
    if flight_price == best_price and best_price > 0:
        is_best = True

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            airline_name = flight.airline if hasattr(flight, 'airline') and flight.airline else ""
            flight_name = flight.name if hasattr(flight, 'name') else ""
            st.markdown(f"**{flight_name}**")

            # Route visualization
            origin_city = flight.departure_city if hasattr(flight, 'departure_city') and flight.departure_city else ""
            dest_city = flight.city if hasattr(flight, 'city') and flight.city else ""

            if origin_city or dest_city:
                route_html = (
                    '<div class="flight-route">'
                    '<span class="city">' + origin_city + '</span>'
                    '<span class="arrow">&#10230;</span>'
                    '<span class="city">' + dest_city + '</span>'
                    '</div>'
                )
                st.markdown(route_html, unsafe_allow_html=True)

            details = []
            if airline_name:
                details.append(airline_name)
            check_in_date = flight.check_in_date if hasattr(flight, 'check_in_date') else None
            if check_in_date:
                details.append(str(check_in_date))

            if details:
                st.caption(" | ".join(details))

        with col2:
            source_name = flight.source_name if hasattr(flight, 'source_name') else "unknown"
            badge_html = _build_source_badge_html(source_name)
            st.markdown(badge_html, unsafe_allow_html=True)

            # Ticket class badge
            inclusions = flight.inclusions if hasattr(flight, 'inclusions') and flight.inclusions else []
            if inclusions:
                chips_parts = []
                for inc in inclusions[:3]:
                    chips_parts.append('<span class="inclusion-chip">' + str(inc) + '</span>')
                chips_html = "".join(chips_parts)
                st.markdown(chips_html, unsafe_allow_html=True)

            # Trend indicator
            offer_id = flight.id if hasattr(flight, 'id') else None
            render_trend_indicator(offer_id)

        with col3:
            if is_best:
                st.markdown(f"### {format_price_idr(flight_price)}")
                best_tag_html = '<span class="best-price-tag">Harga Terbaik</span>'
                st.markdown(best_tag_html, unsafe_allow_html=True)
            else:
                st.markdown(f"### {format_price_idr(flight_price)}")

            is_available = flight.is_available if hasattr(flight, 'is_available') else True
            if not is_available:
                st.error("Sold Out")


def render_flight_results(result: Dict):
    """Render flight search results with stats and freshness."""
    flights = result.get("offers", [])

    if not flights:
        st.info("Tidak ada penerbangan ditemukan dengan kriteria tersebut.")
        return

    flight_count = len(flights)
    st.markdown(f"### {flight_count} Penerbangan Ditemukan")

    # Stats bar
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    with stats_col1:
        st.metric("Total", str(flight_count))
    with stats_col2:
        prices = [f.price_idr for f in flights if hasattr(f, 'price_idr') and f.price_idr > 0]
        min_p = min(prices) if prices else 0
        st.metric("Termurah", format_price_idr(min_p) if min_p > 0 else "-")
    with stats_col3:
        source_stats = result.get("source_stats", {})
        total_sources = len(source_stats)
        st.metric("Sumber Data", str(total_sources))

    # Source breakdown expander
    source_stats = result.get("source_stats", {})
    if source_stats:
        with st.expander("Sumber Data"):
            for src, count in source_stats.items():
                badge_html = _build_source_badge_html(src)
                stat_html = (
                    '<div class="source-stat-card">'
                    '<span class="source-label">' + badge_html + ' ' + src + '</span>'
                    '<span class="source-count">' + str(count) + ' data</span>'
                    '</div>'
                )
                st.markdown(stat_html, unsafe_allow_html=True)

    # Freshness bar
    stats_data = get_source_stats_cached()
    render_freshness_bar("flights", stats_data)

    st.markdown("---")

    # Best price
    valid_prices = [f.price_idr for f in flights if hasattr(f, 'price_idr') and f.price_idr > 0]
    best_price = min(valid_prices) if valid_prices else 0

    for flight in flights:
        render_flight_card(flight, best_price)

    # Gamification
    if not st.session_state.get("price_hub_compare_xp_awarded", False):
        st.session_state.price_hub_compare_xp_awarded = True
        add_xp_safe(25, "Membandingkan harga penerbangan umrah")

    # AI analysis
    render_flight_ai_analysis(result)


def render_flight_tab():
    """Render enhanced flight comparison tab."""

    st.markdown("### Penerbangan ke Tanah Suci")
    st.caption("Data dari berbagai sumber: API, n8n, dan Travel Agent")

    if not HAS_AGGREGATOR:
        st.warning("Price aggregator tidak tersedia")
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        search_params = render_flight_search_form()

    with col2:
        if search_params:
            with st.spinner("Mengambil data penerbangan..."):
                try:
                    aggregator = _get_connected_aggregator()
                    if not aggregator:
                        st.error("Aggregator tidak tersedia")
                    else:
                        result = aggregator.aggregate(
                            city=search_params["destination"],
                            offer_type="flight",
                            sort_by=search_params["sort_by"],
                            limit=30
                        )

                        flights = result.get("offers", [])

                        # Post-filter by origin city
                        origin = search_params["origin"]
                        flights = [
                            f for f in flights
                            if not hasattr(f, 'departure_city')
                            or not f.departure_city
                            or origin.lower() in (f.departure_city or "").lower()
                        ]

                        # Post-filter by direct only
                        if search_params["direct_only"]:
                            filtered_direct = []
                            for f in flights:
                                inclusions = f.inclusions if hasattr(f, 'inclusions') and f.inclusions else []
                                is_direct = any("direct" in str(inc).lower() for inc in inclusions)
                                if is_direct:
                                    filtered_direct.append(f)
                            if filtered_direct:
                                flights = filtered_direct

                        # Post-filter by ticket class
                        tc = search_params["ticket_class"]
                        if tc != "Semua":
                            filtered_class = []
                            for f in flights:
                                inclusions = f.inclusions if hasattr(f, 'inclusions') and f.inclusions else []
                                class_match = any(tc.lower() in str(inc).lower() for inc in inclusions)
                                if class_match:
                                    filtered_class.append(f)
                            if filtered_class:
                                flights = filtered_class

                        result["offers"] = flights
                        st.session_state.price_hub_flight_result = result
                        st.session_state.price_hub_flight_params = search_params

                except Exception as e:
                    logger.error(f"Flight search error: {e}")
                    st.error(f"Error: {e}")

        if st.session_state.get("price_hub_flight_result"):
            render_flight_results(st.session_state.price_hub_flight_result)
        else:
            render_skeleton("cards", count=3)
            st.caption("Pilih kota asal dan tujuan untuk melihat harga penerbangan")


# =============================================================================
# PACKAGE TAB COMPONENTS
# =============================================================================

def render_package_search_form() -> Optional[Dict]:
    """Render package search form with full filter options."""

    col1, col2 = st.columns(2)

    with col1:
        departure = st.selectbox(
            "Berangkat dari",
            options=["Semua"] + ORIGIN_CITIES,
            index=0,
            key="pkg_departure_v2"
        )

    with col2:
        min_stars = st.slider("Min Bintang Hotel", 3, 5, 4, key="pkg_stars_v2")

    col1, col2 = st.columns(2)

    with col1:
        price_range = st.selectbox(
            "Range Harga",
            options=["Semua", "< 30 Juta", "30-50 Juta", "> 50 Juta"],
            key="pkg_price_v2"
        )

    with col2:
        duration = st.selectbox(
            "Durasi",
            options=["Semua", "9 Hari", "12 Hari", "14 Hari", "> 14 Hari"],
            key="pkg_duration_v2"
        )

    # Travel agent multiselect
    agent_options = ["Cheria Travel", "Alhijaz", "Patuna", "Maktour", "Arminareka"]
    selected_agents = st.multiselect(
        "Travel Agent (opsional)",
        options=agent_options,
        default=[],
        key="pkg_agents_v2"
    )

    sort_option = st.selectbox(
        "Urutkan",
        options=["Harga Terendah", "Harga Tertinggi", "Terbaru"],
        index=0,
        key="pkg_sort_v2"
    )

    if st.button("Cari Paket", type="primary", use_container_width=True, key="search_pkg_v2"):
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

        sort_map = {
            "Harga Terendah": "price",
            "Harga Tertinggi": "price_desc",
            "Terbaru": "updated",
        }

        return {
            "departure": departure,
            "min_stars": min_stars,
            "min_price": min_price,
            "max_price": max_price,
            "duration": duration,
            "selected_agents": selected_agents,
            "sort_by": sort_map.get(sort_option, "price"),
        }

    return None


def render_package_card(pkg: Any, best_price: float = 0):
    """Render enhanced package offer card with inclusion chips."""

    is_best = False
    pkg_price = pkg.price_idr if hasattr(pkg, 'price_idr') else 0
    if pkg_price == best_price and best_price > 0:
        is_best = True

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            pkg_name = pkg.name if hasattr(pkg, 'name') else "Paket Umrah"
            st.markdown(f"**{pkg_name}**")

            details = []
            dur = pkg.duration_days if hasattr(pkg, 'duration_days') and pkg.duration_days else None
            dep = pkg.departure_city if hasattr(pkg, 'departure_city') and pkg.departure_city else None
            airline_name = pkg.airline if hasattr(pkg, 'airline') and pkg.airline else None
            if dur:
                details.append(f"{dur} Hari")
            if dep:
                details.append(f"dari {dep}")
            if airline_name:
                details.append(airline_name)

            if details:
                st.caption(" | ".join(details))

            # Hotels with stars
            hotel_info = []
            h_makkah = pkg.hotel_makkah if hasattr(pkg, 'hotel_makkah') and pkg.hotel_makkah else None
            h_madinah = pkg.hotel_madinah if hasattr(pkg, 'hotel_madinah') and pkg.hotel_madinah else None
            h_makkah_stars = pkg.hotel_makkah_stars if hasattr(pkg, 'hotel_makkah_stars') else None
            h_madinah_stars = pkg.hotel_madinah_stars if hasattr(pkg, 'hotel_madinah_stars') else None

            if h_makkah:
                stars_display = get_star_display(h_makkah_stars or 4)
                hotel_info.append("Makkah: " + h_makkah + " " + stars_display)
            if h_madinah:
                stars_display = get_star_display(h_madinah_stars or 4)
                hotel_info.append("Madinah: " + h_madinah + " " + stars_display)

            if hotel_info:
                st.caption(" | ".join(hotel_info))

        with col2:
            source_name = pkg.source_name if hasattr(pkg, 'source_name') else "unknown"
            badge_html = _build_source_badge_html(source_name)
            st.markdown(badge_html, unsafe_allow_html=True)

            # Inclusion chips
            inclusions = pkg.inclusions if hasattr(pkg, 'inclusions') and pkg.inclusions else []
            if inclusions:
                chips_parts = []
                display_count = min(len(inclusions), 4)
                for inc in inclusions[:display_count]:
                    chips_parts.append('<span class="inclusion-chip">' + str(inc) + '</span>')
                remaining = len(inclusions) - display_count
                if remaining > 0:
                    chips_parts.append('<span class="inclusion-chip">+' + str(remaining) + ' lagi</span>')
                chips_html = "".join(chips_parts)
                st.markdown(chips_html, unsafe_allow_html=True)

            # Trend indicator
            offer_id = pkg.id if hasattr(pkg, 'id') else None
            render_trend_indicator(offer_id)

        with col3:
            if is_best:
                st.markdown(f"### {format_price_idr(pkg_price)}")
                best_tag_html = '<span class="best-price-tag">Harga Terbaik</span>'
                st.markdown(best_tag_html, unsafe_allow_html=True)
            else:
                st.markdown(f"### {format_price_idr(pkg_price)}")

            is_available = pkg.is_available if hasattr(pkg, 'is_available') else True
            quota = pkg.quota if hasattr(pkg, 'quota') else None

            if not is_available:
                st.error("Sold Out")
            elif quota and quota < 10:
                st.warning(f"Sisa {quota} seat!")


def render_package_results(result: Dict):
    """Render package search results with stats and freshness."""
    packages = result.get("offers", [])

    if not packages:
        st.info("Tidak ada paket ditemukan dengan kriteria tersebut.")
        return

    pkg_count = len(packages)
    st.markdown(f"### {pkg_count} Paket Ditemukan")

    # Stats bar
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    with stats_col1:
        st.metric("Total", str(pkg_count))
    with stats_col2:
        prices = [p.price_idr for p in packages if hasattr(p, 'price_idr') and p.price_idr > 0]
        min_p = min(prices) if prices else 0
        st.metric("Termurah", format_price_idr(min_p) if min_p > 0 else "-")
    with stats_col3:
        source_stats = result.get("source_stats", {})
        total_sources = len(source_stats)
        st.metric("Sumber Data", str(total_sources))

    # Source breakdown expander
    if source_stats:
        with st.expander("Sumber Data"):
            for src, count in source_stats.items():
                badge_html = _build_source_badge_html(src)
                stat_html = (
                    '<div class="source-stat-card">'
                    '<span class="source-label">' + badge_html + ' ' + src + '</span>'
                    '<span class="source-count">' + str(count) + ' paket</span>'
                    '</div>'
                )
                st.markdown(stat_html, unsafe_allow_html=True)

    # Freshness bar
    stats_data = get_source_stats_cached()
    render_freshness_bar("packages", stats_data)

    st.markdown("---")

    # Best price
    valid_prices = [p.price_idr for p in packages if hasattr(p, 'price_idr') and p.price_idr > 0]
    best_price = min(valid_prices) if valid_prices else 0

    for pkg in packages:
        render_package_card(pkg, best_price)

    # Gamification
    if not st.session_state.get("price_hub_compare_xp_awarded", False):
        st.session_state.price_hub_compare_xp_awarded = True
        add_xp_safe(25, "Membandingkan harga paket umrah")

    # AI analysis
    render_package_ai_analysis(result)


def render_package_tab():
    """Render enhanced package comparison tab."""

    st.markdown("### Paket Umrah")
    st.caption("Paket lengkap dari berbagai Travel Agent terpercaya")

    if not HAS_AGGREGATOR:
        st.warning("Price aggregator tidak tersedia")
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        search_params = render_package_search_form()

    with col2:
        if search_params:
            with st.spinner("Mengambil data paket..."):
                try:
                    aggregator = _get_connected_aggregator()
                    if not aggregator:
                        st.error("Aggregator tidak tersedia")
                    else:
                        result = aggregator.aggregate(
                            offer_type="package",
                            min_price=search_params["min_price"],
                            max_price=search_params["max_price"],
                            min_stars=search_params["min_stars"],
                            sort_by=search_params["sort_by"],
                            limit=30
                        )

                        packages = result.get("offers", [])

                        # Post-filter by departure
                        departure = search_params["departure"]
                        if departure != "Semua":
                            packages = [
                                p for p in packages
                                if not hasattr(p, 'departure_city')
                                or not p.departure_city
                                or departure.lower() in (p.departure_city or "").lower()
                            ]

                        # Post-filter by duration
                        duration_filter = search_params["duration"]
                        if duration_filter != "Semua":
                            filtered_dur = []
                            for p in packages:
                                dur = p.duration_days if hasattr(p, 'duration_days') else None
                                if dur is None:
                                    filtered_dur.append(p)
                                    continue
                                if duration_filter == "9 Hari" and dur == 9:
                                    filtered_dur.append(p)
                                elif duration_filter == "12 Hari" and dur == 12:
                                    filtered_dur.append(p)
                                elif duration_filter == "14 Hari" and dur == 14:
                                    filtered_dur.append(p)
                                elif duration_filter == "> 14 Hari" and dur > 14:
                                    filtered_dur.append(p)
                            if filtered_dur:
                                packages = filtered_dur

                        # Post-filter by travel agent
                        selected_agents = search_params["selected_agents"]
                        if selected_agents:
                            agent_map = {
                                "Cheria Travel": "cheria-travel",
                                "Alhijaz": "alhijaz",
                                "Patuna": "patuna",
                                "Maktour": "maktour",
                                "Arminareka": "arminareka",
                            }
                            agent_keys = [agent_map.get(a, a.lower()) for a in selected_agents]
                            filtered_agents = [
                                p for p in packages
                                if hasattr(p, 'source_name') and p.source_name in agent_keys
                            ]
                            if filtered_agents:
                                packages = filtered_agents

                        result["offers"] = packages
                        st.session_state.price_hub_package_result = result
                        st.session_state.price_hub_package_params = search_params

                except Exception as e:
                    logger.error(f"Package search error: {e}")
                    st.error(f"Error: {e}")

        if st.session_state.get("price_hub_package_result"):
            render_package_results(st.session_state.price_hub_package_result)
        else:
            render_skeleton("cards", count=3)
            st.caption("Pilih kriteria untuk melihat paket dari berbagai travel agent")


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
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SKELETON_CSS, PRICE_HUB_CSS)

    # Header
    hero_html = (
        '<div class="page-hero price-hub-hero">'
        '<h1>Pusat Perbandingan Harga</h1>'
        '<p class="subtitle">Bandingkan harga hotel, penerbangan &amp; paket dari berbagai sumber</p>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # Dynamic quick stats from source stats
    source_stats = get_source_stats_cached()
    hotel_count = source_stats.get("hotels", {}).get("count", 0)
    flight_count = source_stats.get("flights", {}).get("count", 0)
    package_count = source_stats.get("packages", {}).get("count", 0)

    hotel_label = f"{hotel_count} data" if hotel_count > 0 else "200+ OTA"
    flight_label = f"{flight_count} rute" if flight_count > 0 else "Multi-source"
    package_label = f"{package_count} paket" if package_count > 0 else "5+ Travel Agent"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hotel", hotel_label, help="Via Makcorps API + n8n")
    with col2:
        st.metric("Penerbangan", flight_label, help="API, n8n, Partner")
    with col3:
        st.metric("Paket", package_label, help="Cheria, Alhijaz, dll")

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
