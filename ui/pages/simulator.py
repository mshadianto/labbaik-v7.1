"""
LABBAIK AI v7.1 - Cost Simulator with Scenario Planning
========================================================
Advanced cost calculator with scenario planning:
- Multiple scenarios (Optimis, Realistis, Pesimistis)
- Sensitivity analysis
- Risk factor assessment
- Monte Carlo confidence ranges
- Interactive scenario comparison
- AI-powered financial analysis
- Gamification (XP rewards)
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import random
import re

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

try:
    from ui.pages.kurs_calculator import get_current_rates, format_idr as kurs_format_idr
    HAS_KURS_SERVICE = True
except ImportError:
    HAS_KURS_SERVICE = False

try:
    from services.intelligence.season_calendar import SeasonCalendar, get_season_calendar
    HAS_SEASON_CALENDAR = True
except ImportError:
    HAS_SEASON_CALENDAR = False

# =============================================================================
# SIMULATOR PAGE CSS
# =============================================================================

SIMULATOR_CSS = """
/* Simulator page-specific overrides */
:root {
    --hero-bg: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    --hero-border: #d4af37;
    --hero-title: #d4af37;
    --hero-subtitle: #b0b0b0;
}

.sim-confidence-bar {
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    margin: 0.5rem 0;
}

.sim-confidence-bar small {
    color: #fff;
}

.sim-range-bar {
    background: #333;
    border-radius: 5px;
    height: 25px;
    margin-bottom: 10px;
    overflow: hidden;
}

.sim-range-fill {
    height: 100%;
    border-radius: 5px;
}

.sim-percentile {
    text-align: center;
    padding: 1rem;
    background: #1a1a2e;
    border-radius: 10px;
}

.sim-percentile .label {
    font-size: 0.8rem;
    color: #b0b0b0;
}

.sim-percentile .value {
    font-size: 1.1rem;
    font-weight: bold;
    color: white;
}

.sim-tornado-bar {
    display: flex;
    align-items: center;
    margin: 5px 0 15px 0;
}

.sim-tornado-left {
    width: 50%;
    display: flex;
    justify-content: flex-end;
}

.sim-tornado-center {
    width: 2px;
    height: 30px;
    background: #fff;
}

.sim-tornado-right {
    width: 50%;
}

.sim-tornado-fill-green {
    background: #28a745;
    height: 20px;
    border-radius: 3px 0 0 3px;
}

.sim-tornado-fill-red {
    background: #dc3545;
    height: 20px;
    border-radius: 0 3px 3px 0;
}

.sim-discount-tier {
    background: #1a1a2e;
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
}

.sim-discount-tier .inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.sim-discount-tier .tier-name {
    color: white;
    font-weight: bold;
}

.sim-discount-tier .tier-count {
    color: #b0b0b0;
}

.sim-discount-tier .tier-pct {
    color: #28a745;
    font-weight: bold;
}

.sim-discount-tier .tier-price {
    color: white;
}

.sim-group-banner {
    background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
}

.sim-group-banner h3 {
    color: #d4af37;
    margin: 0;
}

.sim-group-banner p {
    color: #ccc;
    margin: 0.5rem 0 0 0;
    font-size: 0.9rem;
}

.sim-save-cta {
    background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    border: 1px solid #d4af37;
    margin: 1rem 0;
}

.sim-save-cta h3 {
    color: #d4af37;
    margin-bottom: 0.5rem;
}

.sim-save-cta p {
    color: #ccc;
    font-size: 0.9rem;
}

.budget-template-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #333;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    transition: border-color 0.2s ease;
    min-height: 180px;
}

.budget-template-card:hover {
    border-color: #d4af37;
}

.budget-template-card .template-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.budget-template-card .template-name {
    color: #d4af37;
    font-weight: bold;
    font-size: 1rem;
    margin-bottom: 0.3rem;
}

.budget-template-card .template-desc {
    color: #b0b0b0;
    font-size: 0.8rem;
    margin-bottom: 0.5rem;
}

.budget-template-card .template-price {
    color: #28a745;
    font-weight: bold;
    font-size: 1.1rem;
}

@media (max-width: 768px) {
    .budget-template-card {
        min-height: 140px;
        padding: 0.75rem;
    }
}

.season-impact-card {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a4a 100%);
    border: 1px solid #d4af37;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 0.75rem 0;
}

.season-impact-card h4 {
    color: #d4af37;
    margin: 0 0 0.75rem 0;
    font-size: 1.05rem;
}

.season-impact-card .season-label {
    color: #e0e0e0;
    font-size: 0.95rem;
    margin-bottom: 0.4rem;
}

.season-impact-card .season-detail {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin-bottom: 0.3rem;
}

.season-multiplier-badge {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
    margin: 0.4rem 0;
}

.season-multiplier-green {
    background: rgba(40, 167, 69, 0.2);
    color: #28a745;
    border: 1px solid #28a745;
}

.season-multiplier-yellow {
    background: rgba(255, 193, 7, 0.2);
    color: #ffc107;
    border: 1px solid #ffc107;
}

.season-multiplier-orange {
    background: rgba(253, 126, 20, 0.2);
    color: #fd7e14;
    border: 1px solid #fd7e14;
}

.season-multiplier-red {
    background: rgba(220, 53, 69, 0.2);
    color: #dc3545;
    border: 1px solid #dc3545;
}

.season-recommendation {
    background: linear-gradient(135deg, #1a2a1a 0%, #1a3a2a 100%);
    border: 1px solid #28a745;
    border-radius: 10px;
    padding: 1rem;
    margin-top: 0.5rem;
}

.season-recommendation .reco-urgency {
    font-weight: bold;
    font-size: 0.9rem;
    margin-bottom: 0.3rem;
}

.season-recommendation .reco-text {
    color: #b0b0b0;
    font-size: 0.85rem;
}

.season-low-tip {
    background: linear-gradient(135deg, #0d2818 0%, #1a3a2a 100%);
    border: 1px solid #28a745;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-top: 0.5rem;
}

.season-low-tip .tip-title {
    color: #28a745;
    font-weight: bold;
    font-size: 0.9rem;
    margin-bottom: 0.3rem;
}

.season-low-tip .tip-text {
    color: #b0b0b0;
    font-size: 0.85rem;
}

@media (max-width: 768px) {
    .season-impact-card {
        padding: 1rem;
    }
    .season-multiplier-badge {
        font-size: 0.8rem;
    }
}

/* Saved Scenario Cards */
.saved-scenario-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #333;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s ease;
}

.saved-scenario-card:hover {
    border-color: #d4af37;
}

.saved-scenario-card .scenario-name {
    color: #d4af37;
    font-weight: bold;
    font-size: 1rem;
    margin-bottom: 0.25rem;
}

.saved-scenario-card .scenario-cost {
    color: #28a745;
    font-weight: bold;
    font-size: 1.15rem;
    margin-bottom: 0.25rem;
}

.saved-scenario-card .scenario-meta {
    color: #b0b0b0;
    font-size: 0.8rem;
}

/* Scenario Comparison Table */
.scenario-compare-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 10px;
    overflow: hidden;
    margin: 1rem 0;
}

.scenario-compare-table th {
    background: #1a1a2e;
    color: #d4af37;
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.9rem;
    border-bottom: 2px solid #d4af37;
}

.scenario-compare-table td {
    background: #0d1b2a;
    color: #e0e0e0;
    padding: 0.65rem 1rem;
    font-size: 0.9rem;
    border-bottom: 1px solid #222;
}

.scenario-compare-table tr:last-child td {
    border-bottom: none;
}

.scenario-compare-table .cheapest {
    color: #28a745;
    font-weight: bold;
}

.scenario-compare-table .diff-cell {
    color: #b0b0b0;
    font-size: 0.8rem;
}

.scenario-compare-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a4a 100%);
    border: 1px solid #d4af37;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    text-align: center;
}

.scenario-compare-header h3 {
    color: #d4af37;
    margin: 0 0 0.3rem 0;
}

.scenario-compare-header p {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin: 0;
}

/* PDF Report Styles */
.sim-pdf-download {
    background: linear-gradient(135deg, #1a2a1a 0%, #1a3a2a 100%);
    border: 1px solid #28a745;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    margin: 0.75rem 0;
}

.sim-pdf-download p {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin: 0.3rem 0 0 0;
}

@media (max-width: 768px) {
    .saved-scenario-card {
        padding: 0.75rem;
    }
    .scenario-compare-table th,
    .scenario-compare-table td {
        padding: 0.5rem 0.6rem;
        font-size: 0.8rem;
    }
}
"""

# =============================================================================
# BUDGET TEMPLATE PRESETS
# =============================================================================

BUDGET_TEMPLATES = {
    "backpacker": {
        "label": "🎒 Backpacker",
        "description": "Umrah hemat, hotel budget, makan sederhana",
        "hotel_stars": 2,
        "meals_budget": "hemat",
        "transport": "bus",
        "duration_days": 9,
        "total_estimate_idr": 18_000_000,
    },
    "standard": {
        "label": "⭐ Standard",
        "description": "Umrah nyaman, hotel bintang 3-4, makan lengkap",
        "hotel_stars": 3,
        "meals_budget": "standar",
        "transport": "mix",
        "duration_days": 9,
        "total_estimate_idr": 28_000_000,
    },
    "premium": {
        "label": "💎 Premium",
        "description": "Hotel bintang 5 dekat Haram, full board",
        "hotel_stars": 5,
        "meals_budget": "premium",
        "transport": "private",
        "duration_days": 12,
        "total_estimate_idr": 45_000_000,
    },
    "vip": {
        "label": "👑 VIP Executive",
        "description": "View Haram, private guide, business class",
        "hotel_stars": 5,
        "meals_budget": "premium",
        "transport": "private",
        "duration_days": 12,
        "total_estimate_idr": 75_000_000,
    },
}


# =============================================================================
# HELPERS
# =============================================================================

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


# =============================================================================
# DATA CLASSES & CONSTANTS
# =============================================================================

class Season(str, Enum):
    REGULAR = "regular"
    HIGH = "high"
    PEAK = "peak"       # Ramadan
    SUPER_PEAK = "super_peak"  # Haji season


class ScenarioType(str, Enum):
    OPTIMISTIC = "optimistic"    # Best case
    REALISTIC = "realistic"       # Most likely
    PESSIMISTIC = "pessimistic"  # Worst case


@dataclass
class CostBreakdown:
    """Cost breakdown structure."""
    flight: int
    visa: int
    hotel_makkah: int
    hotel_madinah: int
    transport: int
    meals: int
    mutawif: int
    insurance: int
    misc: int
    seasonal_adj: int
    total: int


@dataclass
class RiskFactor:
    """Risk factor that affects cost."""
    name: str
    description: str
    probability: float  # 0-1
    impact_min: float   # percentage impact
    impact_max: float
    category: str


@dataclass
class Scenario:
    """Complete scenario with costs and analysis."""
    name: str
    type: ScenarioType
    base_cost: CostBreakdown
    adjusted_cost: int
    confidence_low: int
    confidence_high: int
    risk_factors: List[Dict]
    assumptions: List[str]
    probability: float  # likelihood of this scenario


@dataclass
class SensitivityResult:
    """Result of sensitivity analysis."""
    variable: str
    base_value: Any
    low_value: Any
    high_value: Any
    base_cost: int
    low_cost: int
    high_cost: int
    impact_range: int


# Risk factors database
RISK_FACTORS = [
    RiskFactor(
        name="Fluktuasi Kurs",
        description="Perubahan nilai tukar IDR/SAR",
        probability=0.7,
        impact_min=-5,
        impact_max=15,
        category="ekonomi"
    ),
    RiskFactor(
        name="Kenaikan Harga Tiket",
        description="Harga tiket pesawat naik mendekati keberangkatan",
        probability=0.5,
        impact_min=0,
        impact_max=20,
        category="penerbangan"
    ),
    RiskFactor(
        name="Occupancy Hotel Tinggi",
        description="Hotel penuh, harus upgrade atau hotel lebih jauh",
        probability=0.4,
        impact_min=0,
        impact_max=25,
        category="akomodasi"
    ),
    RiskFactor(
        name="Biaya Tak Terduga",
        description="Pengeluaran tidak terencana (medis, extra bagasi, dll)",
        probability=0.6,
        impact_min=2,
        impact_max=10,
        category="lainnya"
    ),
    RiskFactor(
        name="Inflasi Saudi",
        description="Kenaikan harga umum di Arab Saudi",
        probability=0.5,
        impact_min=0,
        impact_max=8,
        category="ekonomi"
    ),
    RiskFactor(
        name="Perubahan Regulasi Visa",
        description="Biaya visa naik atau persyaratan baru",
        probability=0.2,
        impact_min=0,
        impact_max=30,
        category="regulasi"
    ),
]

# Scenario multipliers
SCENARIO_MULTIPLIERS = {
    ScenarioType.OPTIMISTIC: {
        "flight": 0.90,
        "hotel": 0.85,
        "misc": 0.80,
        "seasonal": 0.90,
    },
    ScenarioType.REALISTIC: {
        "flight": 1.0,
        "hotel": 1.0,
        "misc": 1.0,
        "seasonal": 1.0,
    },
    ScenarioType.PESSIMISTIC: {
        "flight": 1.20,
        "hotel": 1.30,
        "misc": 1.50,
        "seasonal": 1.15,
    },
}


# Pricing data
FLIGHT_PRICES = {
    "Jakarta": {"economy": 8_000_000, "business": 25_000_000},
    "Surabaya": {"economy": 8_500_000, "business": 26_000_000},
    "Bandung": {"economy": 8_200_000, "business": 25_500_000},
    "Medan": {"economy": 9_000_000, "business": 27_000_000},
    "Makassar": {"economy": 9_500_000, "business": 28_000_000},
    "Semarang": {"economy": 8_300_000, "business": 25_800_000},
    "Yogyakarta": {"economy": 8_400_000, "business": 26_000_000},
    "Palembang": {"economy": 8_800_000, "business": 27_000_000},
    "Balikpapan": {"economy": 9_200_000, "business": 28_500_000},
    "Pekanbaru": {"economy": 8_600_000, "business": 26_500_000},
}

HOTEL_PRICES_PER_NIGHT = {
    "makkah": {
        2: 400_000,
        3: 700_000,
        4: 1_500_000,
        5: 3_500_000,
    },
    "madinah": {
        2: 350_000,
        3: 600_000,
        4: 1_200_000,
        5: 2_800_000,
    }
}

SEASONAL_MULTIPLIERS = {
    Season.REGULAR: 1.0,
    Season.HIGH: 1.15,
    Season.PEAK: 1.35,
    Season.SUPER_PEAK: 1.50,
}

VISA_COST = 1_500_000
INSURANCE_BASE = 500_000
MUTAWIF_COST = 2_000_000
TRANSPORT_COST = 1_500_000
MEALS_PER_DAY = {
    "none": 0,
    "basic": 150_000,
    "standard": 250_000,
    "premium": 400_000,
}


# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================

def get_season(departure_date: date) -> Tuple[Season, str]:
    """Determine season based on departure date."""
    month = departure_date.month
    
    if month == 3 or month == 4:
        return Season.PEAK, "🌙 Musim Ramadan - Harga tertinggi"
    elif month == 6 or month == 7:
        return Season.SUPER_PEAK, "🕋 Musim Haji - Harga sangat tinggi"
    elif month == 12 or month == 1:
        return Season.HIGH, "🎄 Musim Liburan - Harga tinggi"
    else:
        return Season.REGULAR, "✅ Musim Reguler - Harga normal"


def calculate_cost(
    departure_city: str,
    departure_date: date,
    duration: int,
    nights_makkah: int,
    nights_madinah: int,
    hotel_star_makkah: int,
    hotel_star_madinah: int,
    flight_class: str,
    meal_type: str,
    num_travelers: int,
    include_mutawif: bool,
    include_insurance: bool,
) -> CostBreakdown:
    """Calculate detailed cost breakdown."""
    
    # Flight
    flight_prices = FLIGHT_PRICES.get(departure_city, FLIGHT_PRICES["Jakarta"])
    flight = flight_prices.get(flight_class, flight_prices["economy"])
    
    # Visa
    visa = VISA_COST
    
    # Hotels
    hotel_makkah = HOTEL_PRICES_PER_NIGHT["makkah"].get(hotel_star_makkah, 700_000) * nights_makkah
    hotel_madinah = HOTEL_PRICES_PER_NIGHT["madinah"].get(hotel_star_madinah, 600_000) * nights_madinah
    
    # Transport
    transport = TRANSPORT_COST
    
    # Meals
    meals = MEALS_PER_DAY.get(meal_type, 0) * duration
    
    # Mutawif
    mutawif = MUTAWIF_COST if include_mutawif else 0
    
    # Insurance
    insurance = INSURANCE_BASE if include_insurance else 0
    
    # Misc (tips, zamzam, souvenirs, etc)
    misc = 2_000_000
    
    # Subtotal
    subtotal = flight + visa + hotel_makkah + hotel_madinah + transport + meals + mutawif + insurance + misc
    
    # Seasonal adjustment
    season, _ = get_season(departure_date)
    multiplier = SEASONAL_MULTIPLIERS.get(season, 1.0)
    seasonal_adj = int(subtotal * (multiplier - 1))
    
    # Total per person
    total = subtotal + seasonal_adj
    
    return CostBreakdown(
        flight=flight,
        visa=visa,
        hotel_makkah=hotel_makkah,
        hotel_madinah=hotel_madinah,
        transport=transport,
        meals=meals,
        mutawif=mutawif,
        insurance=insurance,
        misc=misc,
        seasonal_adj=seasonal_adj,
        total=total,
    )


def format_currency(amount: int) -> str:
    """Format as Indonesian Rupiah."""
    return f"Rp {amount:,.0f}".replace(",", ".")


# =============================================================================
# SCENARIO PLANNING FUNCTIONS
# =============================================================================

def calculate_scenario_cost(
    base_cost: CostBreakdown,
    scenario_type: ScenarioType
) -> CostBreakdown:
    """Calculate cost for a specific scenario."""
    multipliers = SCENARIO_MULTIPLIERS[scenario_type]

    flight = int(base_cost.flight * multipliers["flight"])
    hotel_makkah = int(base_cost.hotel_makkah * multipliers["hotel"])
    hotel_madinah = int(base_cost.hotel_madinah * multipliers["hotel"])
    misc = int(base_cost.misc * multipliers["misc"])
    seasonal_adj = int(base_cost.seasonal_adj * multipliers["seasonal"])

    total = (flight + base_cost.visa + hotel_makkah + hotel_madinah +
             base_cost.transport + base_cost.meals + base_cost.mutawif +
             base_cost.insurance + misc + seasonal_adj)

    return CostBreakdown(
        flight=flight,
        visa=base_cost.visa,
        hotel_makkah=hotel_makkah,
        hotel_madinah=hotel_madinah,
        transport=base_cost.transport,
        meals=base_cost.meals,
        mutawif=base_cost.mutawif,
        insurance=base_cost.insurance,
        misc=misc,
        seasonal_adj=seasonal_adj,
        total=total
    )


def generate_all_scenarios(base_cost: CostBreakdown) -> Dict[ScenarioType, Scenario]:
    """Generate all three scenarios from base cost."""
    scenarios = {}

    # Scenario configurations
    configs = {
        ScenarioType.OPTIMISTIC: {
            "name": "Skenario Optimis",
            "probability": 0.20,
            "assumptions": [
                "Dapat promo early bird tiket pesawat",
                "Hotel tersedia dengan harga normal",
                "Kurs stabil atau menguat",
                "Tidak ada biaya tak terduga",
                "Berangkat di musim reguler"
            ]
        },
        ScenarioType.REALISTIC: {
            "name": "Skenario Realistis",
            "probability": 0.60,
            "assumptions": [
                "Harga tiket sesuai rata-rata pasar",
                "Hotel sesuai bintang yang dipilih",
                "Kurs normal dengan sedikit fluktuasi",
                "Buffer 5-10% untuk tak terduga",
                "Kondisi pasar normal"
            ]
        },
        ScenarioType.PESSIMISTIC: {
            "name": "Skenario Pesimis",
            "probability": 0.20,
            "assumptions": [
                "Tiket dibeli mendekati keberangkatan",
                "Hotel harus upgrade karena penuh",
                "Kurs melemah signifikan",
                "Ada biaya tak terduga (medis, dll)",
                "Peak season atau high demand"
            ]
        }
    }

    for scenario_type, config in configs.items():
        scenario_cost = calculate_scenario_cost(base_cost, scenario_type)

        # Calculate confidence range (Monte Carlo-style)
        if scenario_type == ScenarioType.OPTIMISTIC:
            confidence_low = int(scenario_cost.total * 0.95)
            confidence_high = int(scenario_cost.total * 1.05)
        elif scenario_type == ScenarioType.REALISTIC:
            confidence_low = int(scenario_cost.total * 0.92)
            confidence_high = int(scenario_cost.total * 1.12)
        else:
            confidence_low = int(scenario_cost.total * 0.98)
            confidence_high = int(scenario_cost.total * 1.25)

        # Identify relevant risk factors
        risk_factors = []
        for rf in RISK_FACTORS:
            if scenario_type == ScenarioType.PESSIMISTIC:
                impact = rf.impact_max
            elif scenario_type == ScenarioType.OPTIMISTIC:
                impact = rf.impact_min
            else:
                impact = (rf.impact_min + rf.impact_max) / 2

            risk_factors.append({
                "name": rf.name,
                "description": rf.description,
                "probability": rf.probability,
                "impact": impact,
                "category": rf.category
            })

        scenarios[scenario_type] = Scenario(
            name=config["name"],
            type=scenario_type,
            base_cost=scenario_cost,
            adjusted_cost=scenario_cost.total,
            confidence_low=confidence_low,
            confidence_high=confidence_high,
            risk_factors=risk_factors,
            assumptions=config["assumptions"],
            probability=config["probability"]
        )

    return scenarios


def run_monte_carlo_simulation(
    base_cost: CostBreakdown,
    num_simulations: int = 1000
) -> Dict[str, Any]:
    """Run Monte Carlo simulation for cost estimation."""
    results = []

    for _ in range(num_simulations):
        # Random variations for each component
        flight_var = random.uniform(0.85, 1.25)
        hotel_var = random.uniform(0.90, 1.35)
        misc_var = random.uniform(0.80, 1.50)

        # Apply risk factors randomly
        risk_multiplier = 1.0
        for rf in RISK_FACTORS:
            if random.random() < rf.probability:
                impact = random.uniform(rf.impact_min, rf.impact_max) / 100
                risk_multiplier += impact

        # Calculate simulated total
        sim_total = (
            base_cost.flight * flight_var +
            base_cost.visa +
            (base_cost.hotel_makkah + base_cost.hotel_madinah) * hotel_var +
            base_cost.transport +
            base_cost.meals +
            base_cost.mutawif +
            base_cost.insurance +
            base_cost.misc * misc_var +
            base_cost.seasonal_adj
        ) * risk_multiplier

        results.append(int(sim_total))

    results.sort()

    return {
        "min": results[0],
        "max": results[-1],
        "mean": int(sum(results) / len(results)),
        "median": results[len(results) // 2],
        "p10": results[int(len(results) * 0.10)],  # 10th percentile
        "p25": results[int(len(results) * 0.25)],  # 25th percentile
        "p75": results[int(len(results) * 0.75)],  # 75th percentile
        "p90": results[int(len(results) * 0.90)],  # 90th percentile
        "std_dev": int((sum((x - sum(results)/len(results))**2 for x in results) / len(results)) ** 0.5),
        "distribution": results
    }


def calculate_sensitivity(
    params: Dict,
    base_cost: CostBreakdown
) -> List[SensitivityResult]:
    """Calculate sensitivity analysis for key variables."""
    results = []

    # Test sensitivity for hotel stars
    for city in ["makkah", "madinah"]:
        param_key = f"hotel_star_{city}"
        base_value = params.get(param_key, 4)

        # Low scenario (1 star lower)
        low_params = params.copy()
        low_params[param_key] = max(2, base_value - 1)
        low_cost = calculate_cost(**{k: v for k, v in low_params.items()
                                     if k in calculate_cost.__code__.co_varnames})

        # High scenario (1 star higher)
        high_params = params.copy()
        high_params[param_key] = min(5, base_value + 1)
        high_cost = calculate_cost(**{k: v for k, v in high_params.items()
                                      if k in calculate_cost.__code__.co_varnames})

        results.append(SensitivityResult(
            variable=f"Hotel {city.title()}",
            base_value=f"{base_value} bintang",
            low_value=f"{low_params[param_key]} bintang",
            high_value=f"{high_params[param_key]} bintang",
            base_cost=base_cost.total,
            low_cost=low_cost.total,
            high_cost=high_cost.total,
            impact_range=high_cost.total - low_cost.total
        ))

    # Test sensitivity for flight class
    if params.get("flight_class") == "economy":
        high_cost = calculate_cost(**{**params, "flight_class": "business"})
        results.append(SensitivityResult(
            variable="Kelas Penerbangan",
            base_value="Economy",
            low_value="Economy",
            high_value="Business",
            base_cost=base_cost.total,
            low_cost=base_cost.total,
            high_cost=high_cost.total,
            impact_range=high_cost.total - base_cost.total
        ))

    # Test sensitivity for duration
    base_duration = params.get("duration", 10)
    short_params = {**params, "duration": max(9, base_duration - 2),
                    "nights_makkah": max(3, params.get("nights_makkah", 5) - 1)}
    short_params["nights_madinah"] = short_params["duration"] - 1 - short_params["nights_makkah"]

    long_params = {**params, "duration": min(21, base_duration + 4),
                   "nights_makkah": min(12, params.get("nights_makkah", 5) + 2)}
    long_params["nights_madinah"] = long_params["duration"] - 1 - long_params["nights_makkah"]

    short_cost = calculate_cost(**{k: v for k, v in short_params.items()
                                   if k in calculate_cost.__code__.co_varnames})
    long_cost = calculate_cost(**{k: v for k, v in long_params.items()
                                  if k in calculate_cost.__code__.co_varnames})

    results.append(SensitivityResult(
        variable="Durasi Trip",
        base_value=f"{base_duration} hari",
        low_value=f"{short_params['duration']} hari",
        high_value=f"{long_params['duration']} hari",
        base_cost=base_cost.total,
        low_cost=short_cost.total,
        high_cost=long_cost.total,
        impact_range=long_cost.total - short_cost.total
    ))

    # Test sensitivity for meals
    meal_options = ["none", "basic", "standard", "premium"]
    current_meal = params.get("meal_type", "standard")
    current_idx = meal_options.index(current_meal)

    low_meal = meal_options[max(0, current_idx - 1)]
    high_meal = meal_options[min(3, current_idx + 1)]

    low_cost = calculate_cost(**{**params, "meal_type": low_meal})
    high_cost = calculate_cost(**{**params, "meal_type": high_meal})

    results.append(SensitivityResult(
        variable="Paket Makan",
        base_value=current_meal.title(),
        low_value=low_meal.title(),
        high_value=high_meal.title(),
        base_cost=base_cost.total,
        low_cost=low_cost.total,
        high_cost=high_cost.total,
        impact_range=high_cost.total - low_cost.total
    ))

    # Sort by impact range (highest first)
    results.sort(key=lambda x: x.impact_range, reverse=True)

    return results


def calculate_break_even_analysis(
    base_cost: CostBreakdown,
    num_travelers: int
) -> Dict[str, Any]:
    """Calculate break-even points and group discounts."""
    total_per_person = base_cost.total

    # Group discount tiers
    discount_tiers = [
        {"min_travelers": 1, "discount": 0, "label": "Individual"},
        {"min_travelers": 5, "discount": 0.03, "label": "Keluarga Kecil"},
        {"min_travelers": 10, "discount": 0.05, "label": "Grup Kecil"},
        {"min_travelers": 20, "discount": 0.08, "label": "Grup Sedang"},
        {"min_travelers": 30, "discount": 0.10, "label": "Grup Besar"},
        {"min_travelers": 45, "discount": 0.12, "label": "Satu Bus"},
    ]

    # Find applicable discount
    applicable_discount = 0
    applicable_label = "Individual"
    for tier in discount_tiers:
        if num_travelers >= tier["min_travelers"]:
            applicable_discount = tier["discount"]
            applicable_label = tier["label"]

    discounted_total = int(total_per_person * (1 - applicable_discount))
    total_savings = (total_per_person - discounted_total) * num_travelers

    return {
        "base_per_person": total_per_person,
        "discounted_per_person": discounted_total,
        "discount_percentage": applicable_discount * 100,
        "discount_label": applicable_label,
        "total_group_cost": discounted_total * num_travelers,
        "total_savings": total_savings,
        "discount_tiers": discount_tiers
    }


# =============================================================================
# SESSION STATE
# =============================================================================

def init_simulator_state():
    """Initialize simulator session state."""

    if "sim_history" not in st.session_state:
        st.session_state.sim_history = []

    if "sim_saved" not in st.session_state:
        st.session_state.sim_saved = []

    # Group planning state
    if "sim_group" not in st.session_state:
        st.session_state.sim_group = None  # Current SimulationGroup

    if "sim_group_members" not in st.session_state:
        st.session_state.sim_group_members = []  # List[GroupMember]

    if "sim_group_totals" not in st.session_state:
        st.session_state.sim_group_totals = {}  # Group financial summary

    if "is_group_view" not in st.session_state:
        st.session_state.is_group_view = False  # Flag for group mode

    # Saved scenarios for comparison
    if "saved_scenarios" not in st.session_state:
        st.session_state.saved_scenarios = []

    # Gamification XP tracking (first-time-per-session)
    if "simulator_xp_simulate" not in st.session_state:
        st.session_state.simulator_xp_simulate = False

    if "simulator_xp_ai" not in st.session_state:
        st.session_state.simulator_xp_ai = False

    if "simulator_xp_save_scenario" not in st.session_state:
        st.session_state.simulator_xp_save_scenario = False

    # AI analysis cache
    if "simulator_ai_response" not in st.session_state:
        st.session_state.simulator_ai_response = None


# =============================================================================
# GROUP PLANNING FUNCTIONS
# =============================================================================

def check_group_from_url():
    """
    Check URL query params for group_id and load group data.
    Returns SimulationGroup if found, None otherwise.
    """
    try:
        group_code = st.query_params.get("group_id")
        if not group_code:
            return None

        from utils.group_manager import (
            get_group_by_code, get_group_members, calculate_group_totals,
            add_member_to_group, MemberStatus
        )

        group = get_group_by_code(group_code)
        if group:
            st.session_state.sim_group = group
            st.session_state.sim_group_members = get_group_members(group.id)
            st.session_state.sim_group_totals = calculate_group_totals(group.id)
            st.session_state.is_group_view = True

            # Check if user needs to join the group
            try:
                from services.user.user_service import is_logged_in, get_current_user
                if is_logged_in():
                    user = get_current_user()
                    # Check if user is already a member
                    from utils.group_manager import get_member_by_user_id
                    existing = get_member_by_user_id(group.id, user.id)
                    if not existing:
                        # Auto-add user to group
                        add_member_to_group(
                            group_id=group.id,
                            name=user.name,
                            user_id=user.id,
                            phone=getattr(user, 'phone', None),
                            status=MemberStatus.ACTIVE
                        )
                        st.session_state.sim_group_members = get_group_members(group.id)
                        st.session_state.sim_group_totals = calculate_group_totals(group.id)
                        st.toast(f"Anda bergabung ke grup '{group.name}'!")
                else:
                    # Not logged in - will show login prompt
                    pass
            except ImportError:
                pass

            return group

        return None
    except Exception as e:
        import logging
        logging.error(f"Error loading group from URL: {e}")
        return None


def handle_group_auth_callback():
    """Handle post-authentication actions for groups."""
    auth_action = st.session_state.get("auth_action")

    if auth_action == "create_group":
        # User just logged in to create a group
        pending = st.session_state.get("pending_group_data")
        if pending:
            st.session_state.auth_action = None
            st.info("Grup Anda siap dibuat. Silakan klik tombol 'Buat Grup' lagi.")

    elif auth_action == "join_group":
        # User just logged in to join a group
        group_code = st.query_params.get("group_id")
        if group_code:
            from utils.group_manager import get_group_by_code, add_member_to_group, MemberStatus
            group = get_group_by_code(group_code)
            if group:
                try:
                    from services.user.user_service import get_current_user
                    user = get_current_user()
                    add_member_to_group(
                        group_id=group.id,
                        name=user.name,
                        user_id=user.id,
                        phone=getattr(user, 'phone', None),
                        status=MemberStatus.ACTIVE
                    )
                    st.session_state.auth_action = None
                    st.success(f"Anda bergabung ke grup '{group.name}'!")
                except Exception:
                    pass


def render_group_header(group):
    """Render group info banner at top of simulator."""
    from utils.group_manager import MemberStatus

    with st.container(border=True):
        banner_html = (
            f'<div class="sim-group-banner">'
            f'<h3>Rencana Umrah Grup: {group.name}</h3>'
            f'<p>Kode Grup: <strong>{group.group_code}</strong> | '
            f'Dibuat oleh: {group.leader_name}</p>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

        # Show group totals if we have multiple members
        totals = st.session_state.sim_group_totals
        members = st.session_state.sim_group_members

        if totals.get("total_members", 0) > 0:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Anggota", f"{totals.get('total_members', 0)} orang")
            with col2:
                st.metric("Dana Target", format_currency(totals.get('total_target', 0)))
            with col3:
                st.metric("Terkumpul", format_currency(totals.get('total_collected', 0)))
            with col4:
                st.metric("Kekurangan/Orang", format_currency(totals.get('per_person_remaining', 0)))

            # Progress bar
            progress = totals.get('progress_percentage', 0) / 100
            st.progress(min(progress, 1.0), text=f"Terkumpul: {totals.get('progress_percentage', 0):.1f}%")

        # Show members
        if members:
            with st.expander(f"Anggota Grup ({len(members)} orang)", expanded=False):
                for member in members:
                    status_icon = "✅" if member.status == MemberStatus.ACTIVE else "⏳"
                    role_badge = "👑" if member.role.value == "leader" else ""
                    contrib = format_currency(member.contribution_amount) if member.contribution_amount > 0 else "-"

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"{status_icon} **{member.name}** {role_badge}")
                    with col2:
                        st.caption(contrib)


def render_group_share_section(group):
    """Render group sharing options."""
    from utils.group_manager import generate_share_url, generate_whatsapp_share_link

    st.markdown("### 📤 Bagikan ke Keluarga")

    share_url = generate_share_url(group.group_code)
    wa_link = generate_whatsapp_share_link(group, share_url)

    col1, col2 = st.columns(2)

    with col1:
        st.link_button(
            "📲 Bagikan ke WhatsApp Keluarga",
            wa_link,
            use_container_width=True,
            type="primary"
        )

    with col2:
        st.code(f"Kode: {group.group_code}", language=None)

    st.caption(f"Link: {share_url}")


def render_create_group_form(params: Dict, cost):
    """Render form to create a new group from current simulation."""

    st.markdown("---")
    st.markdown("### 👨‍👩‍👧‍👦 Rencanakan Bersama Keluarga")
    st.caption("Buat grup untuk berbagi rencana dan pantau tabungan bersama")

    with st.form("create_group_form", clear_on_submit=False):
        group_name = st.text_input(
            "Nama Grup",
            placeholder="Contoh: Keluarga Pak Ahmad",
            max_chars=50,
            value=st.session_state.get("pending_group_name", "")
        )

        target_date = st.date_input(
            "Target Keberangkatan",
            value=params.get("departure_date", date.today() + timedelta(days=60))
        )

        submitted = st.form_submit_button(
            "🚀 Buat Grup Umrah",
            use_container_width=True,
            type="primary"
        )

        if submitted and group_name:
            # Check login status
            try:
                from services.user.user_service import is_logged_in, get_current_user

                if not is_logged_in():
                    # Store pending data and redirect to auth
                    st.session_state.pending_group_data = {
                        "params": {k: str(v) if isinstance(v, date) else v for k, v in params.items()},
                        "breakdown": {
                            "flight": cost.flight,
                            "visa": cost.visa,
                            "hotel_makkah": cost.hotel_makkah,
                            "hotel_madinah": cost.hotel_madinah,
                            "transport": cost.transport,
                            "meals": cost.meals,
                            "mutawif": cost.mutawif,
                            "insurance": cost.insurance,
                            "misc": cost.misc,
                            "total": cost.total,
                        },
                        "group_name": group_name,
                        "target_date": str(target_date),
                        "cost_per_person": cost.total
                    }
                    st.session_state.pending_group_name = group_name
                    st.session_state.auth_redirect_to = "simulator"
                    st.session_state.auth_action = "create_group"
                    st.session_state.current_page = "auth"
                    st.session_state.auth_mode = "login"
                    st.rerun()
                    return

                # User is logged in - create the group
                user = get_current_user()

                from utils.group_manager import create_group, generate_share_url, generate_whatsapp_share_link

                simulation_params = {k: str(v) if isinstance(v, date) else v for k, v in params.items()}
                simulation_breakdown = {
                    "flight": cost.flight,
                    "visa": cost.visa,
                    "hotel_makkah": cost.hotel_makkah,
                    "hotel_madinah": cost.hotel_madinah,
                    "transport": cost.transport,
                    "meals": cost.meals,
                    "mutawif": cost.mutawif,
                    "insurance": cost.insurance,
                    "misc": cost.misc,
                    "total": cost.total,
                }

                group = create_group(
                    name=group_name,
                    leader_id=user.id,
                    leader_name=user.name,
                    leader_phone=getattr(user, 'phone', None),
                    target_date=target_date,
                    simulation_params=simulation_params,
                    simulation_breakdown=simulation_breakdown,
                    cost_per_person=cost.total
                )

                if group:
                    st.session_state.sim_group = group
                    st.session_state.is_group_view = True
                    st.session_state.pending_group_name = ""
                    st.session_state.pending_group_data = None

                    # Show success with share options
                    st.success(f"✅ Grup '{group_name}' berhasil dibuat!")
                    st.info(f"**Kode Grup:** {group.group_code}")

                    share_url = generate_share_url(group.group_code)
                    wa_link = generate_whatsapp_share_link(group, share_url)

                    st.link_button(
                        "📲 Bagikan ke WhatsApp Keluarga",
                        wa_link,
                        use_container_width=True,
                        type="primary"
                    )

                    st.rerun()
                else:
                    st.error("Gagal membuat grup. Silakan coba lagi.")

            except ImportError:
                st.warning("Fitur login diperlukan untuk membuat grup")

        elif submitted and not group_name:
            st.warning("Silakan masukkan nama grup")


def render_group_join_prompt(group):
    """Render login prompt for joining a group."""

    st.warning(f"""
    ### Bergabung ke Grup: {group.name}

    Anda perlu login untuk bergabung ke grup ini dan melihat detail rencana Umrah.
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Masuk", use_container_width=True, type="primary"):
            st.session_state.auth_redirect_to = "simulator"
            st.session_state.auth_action = "join_group"
            st.session_state.current_page = "auth"
            st.session_state.auth_mode = "login"
            st.rerun()
    with col2:
        if st.button("Daftar Gratis", use_container_width=True):
            st.session_state.auth_redirect_to = "simulator"
            st.session_state.auth_action = "join_group"
            st.session_state.current_page = "auth"
            st.session_state.auth_mode = "register"
            st.rerun()


# =============================================================================
# RENDER COMPONENTS
# =============================================================================

def render_input_section() -> Dict:
    """Render input form and return parameters."""
    
    st.markdown("## 🎛️ Konfigurasi Trip")
    
    params = {}
    
    # Section 1: Basic info
    with st.expander("✈️ Keberangkatan", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            params["departure_city"] = st.selectbox(
                "Kota Keberangkatan",
                list(FLIGHT_PRICES.keys()),
                index=0
            )
            
            params["departure_date"] = st.date_input(
                "Tanggal Berangkat",
                min_value=date.today() + timedelta(days=30),
                value=date.today() + timedelta(days=60)
            )
        
        with col2:
            params["flight_class"] = st.radio(
                "Kelas Penerbangan",
                ["economy", "business"],
                format_func=lambda x: "✈️ Ekonomi" if x == "economy" else "💺 Business",
                horizontal=True
            )
            
            # Show season
            season, season_desc = get_season(params["departure_date"])
            if season == Season.REGULAR:
                st.success(season_desc)
            elif season == Season.HIGH:
                st.info(season_desc)
            elif season == Season.PEAK:
                st.warning(season_desc)
            else:
                st.error(season_desc)
    
    # Section 2: Duration
    with st.expander("📅 Durasi & Pembagian", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            params["duration"] = st.selectbox(
                "Total Durasi",
                [9, 10, 12, 14, 21],
                format_func=lambda x: f"{x} hari / {x-1} malam",
                index=1
            )
        
        with col2:
            params["num_travelers"] = st.number_input(
                "Jumlah Jamaah",
                min_value=1,
                max_value=50,
                value=1
            )
        
        max_nights = params["duration"] - 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            params["nights_makkah"] = st.slider(
                "🕋 Malam di Makkah",
                min_value=3,
                max_value=max_nights - 2,
                value=min(5, max_nights - 3)
            )
        
        with col2:
            params["nights_madinah"] = max_nights - params["nights_makkah"]
            st.info(f"🕌 {params['nights_madinah']} malam di Madinah")
    
    # Section 3: Accommodation
    with st.expander("🏨 Akomodasi", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            params["hotel_star_makkah"] = st.select_slider(
                "Hotel Makkah",
                options=[2, 3, 4, 5],
                value=4,
                format_func=lambda x: "⭐" * x
            )
            
            # Show hotel info
            price = HOTEL_PRICES_PER_NIGHT["makkah"][params["hotel_star_makkah"]]
            st.caption(f"{format_currency(price)}/malam")
        
        with col2:
            params["hotel_star_madinah"] = st.select_slider(
                "Hotel Madinah",
                options=[2, 3, 4, 5],
                value=4,
                format_func=lambda x: "⭐" * x
            )
            
            price = HOTEL_PRICES_PER_NIGHT["madinah"][params["hotel_star_madinah"]]
            st.caption(f"{format_currency(price)}/malam")
    
    # Section 4: Services
    with st.expander("🍽️ Layanan", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            params["meal_type"] = st.selectbox(
                "Paket Makan",
                ["none", "basic", "standard", "premium"],
                index=2,
                format_func=lambda x: {
                    "none": "❌ Tidak termasuk",
                    "basic": "🍚 Basic (Rp 150k/hari)",
                    "standard": "🍱 Standard (Rp 250k/hari)",
                    "premium": "🍽️ Premium (Rp 400k/hari)",
                }.get(x, x)
            )
        
        with col2:
            params["include_mutawif"] = st.checkbox("👨‍🏫 Mutawif (Rp 2 Juta)", value=True)
            params["include_insurance"] = st.checkbox("🛡️ Asuransi (Rp 500k)", value=True)
    
    return params


def render_cost_breakdown(cost: CostBreakdown, num_travelers: int):
    """Render detailed cost breakdown."""
    
    st.markdown("## 💰 Rincian Biaya")
    
    # Per person breakdown
    with st.container(border=True):
        st.markdown("### Per Orang")
        
        items = [
            ("✈️ Tiket Pesawat", cost.flight),
            ("📋 Visa Umrah", cost.visa),
            ("🕋 Hotel Makkah", cost.hotel_makkah),
            ("🕌 Hotel Madinah", cost.hotel_madinah),
            ("🚌 Transportasi", cost.transport),
            ("🍽️ Makan", cost.meals),
            ("👨‍🏫 Mutawif", cost.mutawif),
            ("🛡️ Asuransi", cost.insurance),
            ("🎁 Lain-lain", cost.misc),
        ]
        
        col1, col2 = st.columns([3, 2])
        
        for item, amount in items:
            if amount > 0:
                with col1:
                    st.markdown(item)
                with col2:
                    st.markdown(format_currency(amount))
        
        # Seasonal adjustment
        if cost.seasonal_adj > 0:
            st.markdown("---")
            with col1:
                st.markdown("📅 **Penyesuaian Musim**")
            with col2:
                st.markdown(f"+{format_currency(cost.seasonal_adj)}")
        
        st.markdown("---")
        
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown("### Total per Orang")
        with col2:
            st.markdown(f"### {format_currency(cost.total)}")
    
    # Group total if multiple travelers
    if num_travelers > 1:
        with st.container(border=True):
            st.markdown("### 👥 Total Grup")
            
            group_total = cost.total * num_travelers
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Jamaah", f"{num_travelers} orang")
            
            with col2:
                st.metric("Total Biaya Grup", format_currency(group_total))


def render_cost_chart(cost: CostBreakdown):
    """Render cost distribution chart."""
    
    st.markdown("## 📊 Distribusi Biaya")
    
    # Prepare data for chart
    data = {
        "Komponen": ["Tiket", "Visa", "Hotel Makkah", "Hotel Madinah", "Transport", "Makan", "Mutawif", "Asuransi", "Lainnya"],
        "Biaya": [cost.flight, cost.visa, cost.hotel_makkah, cost.hotel_madinah, cost.transport, cost.meals, cost.mutawif, cost.insurance, cost.misc]
    }
    
    # Filter out zero values
    filtered_data = [(k, v) for k, v in zip(data["Komponen"], data["Biaya"]) if v > 0]
    
    # Simple bar representation
    total = sum([v for _, v in filtered_data])
    
    for item, amount in filtered_data:
        pct = amount / total * 100
        st.markdown(f"**{item}** ({pct:.1f}%)")
        st.progress(pct / 100)
        st.caption(format_currency(amount))


def render_comparison():
    """Render package comparison section."""
    
    st.markdown("## 🔄 Perbandingan Paket")
    st.caption("Bandingkan berbagai konfigurasi trip")
    
    # Quick comparison presets
    presets = {
        "Backpacker": {"hotel": 3, "meals": "none", "mutawif": False},
        "Reguler": {"hotel": 4, "meals": "standard", "mutawif": True},
        "Premium": {"hotel": 5, "meals": "premium", "mutawif": True},
    }
    
    cols = st.columns(3)
    
    for col, (name, config) in zip(cols, presets.items()):
        with col:
            # Calculate cost for this preset
            cost = calculate_cost(
                departure_city="Jakarta",
                departure_date=date.today() + timedelta(days=60),
                duration=10,
                nights_makkah=5,
                nights_madinah=4,
                hotel_star_makkah=config["hotel"],
                hotel_star_madinah=config["hotel"],
                flight_class="economy",
                meal_type=config["meals"],
                num_travelers=1,
                include_mutawif=config["mutawif"],
                include_insurance=True,
            )
            
            with st.container(border=True):
                st.markdown(f"### {name}")
                st.markdown(f"## {format_currency(cost.total)}")
                st.caption("per orang")
                
                st.markdown(f"🏨 Hotel Bintang {config['hotel']}")
                st.markdown(f"🍽️ Makan: {config['meals'].title()}")
                st.markdown(f"👨‍🏫 Mutawif: {'Ya' if config['mutawif'] else 'Tidak'}")


def render_savings_tips(cost: CostBreakdown):
    """Render money-saving tips."""
    
    st.markdown("## 💡 Tips Hemat")
    
    tips = []
    
    # Flight tips
    if cost.flight > 8_500_000:
        tips.append({
            "icon": "✈️",
            "title": "Pilih Penerbangan Ekonomi",
            "desc": "Hemat hingga Rp 17 Juta dengan memilih kelas ekonomi",
            "savings": "s/d Rp 17.000.000"
        })
    
    # Hotel tips
    if cost.hotel_makkah > 1_500_000 * 5:
        tips.append({
            "icon": "🏨",
            "title": "Downgrade Hotel",
            "desc": "Hotel bintang 3-4 masih nyaman dan lebih hemat",
            "savings": "s/d Rp 10.000.000"
        })
    
    # Season tips
    if cost.seasonal_adj > 0:
        tips.append({
            "icon": "📅",
            "title": "Pilih Musim Reguler",
            "desc": "Berangkat di bulan Mei, Sep, Oct, atau Nov untuk harga normal",
            "savings": f"s/d {format_currency(cost.seasonal_adj)}"
        })
    
    # Meals tips
    if cost.meals > 0:
        tips.append({
            "icon": "🍽️",
            "title": "Makan Mandiri",
            "desc": "Banyak pilihan makanan halal dengan harga terjangkau di sekitar hotel",
            "savings": f"s/d {format_currency(cost.meals)}"
        })
    
    # Group tips
    tips.append({
        "icon": "👥",
        "title": "Berangkat Rombongan",
        "desc": "Dapat diskon grup untuk 10+ jamaah",
        "savings": "5-15%"
    })
    
    if tips:
        for tip in tips:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {tip['icon']} {tip['title']}")
                    st.caption(tip['desc'])
                
                with col2:
                    st.success(f"💰 {tip['savings']}")
    else:
        st.success("✅ Konfigurasi Anda sudah cukup hemat!")


def render_budget_planner(cost: CostBreakdown, num_travelers: int):
    """Render budget/savings planner."""
    
    st.markdown("## 📈 Rencana Tabungan")
    
    total_needed = cost.total * num_travelers
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_savings = st.number_input(
            "💰 Tabungan Saat Ini (Rp)",
            min_value=0,
            max_value=total_needed * 2,
            value=0,
            step=1_000_000,
            format="%d"
        )
    
    with col2:
        target_date = st.date_input(
            "📅 Target Berangkat",
            min_value=date.today() + timedelta(days=30),
            value=date.today() + timedelta(days=180)
        )
    
    # Calculate
    remaining = max(total_needed - current_savings, 0)
    days_left = (target_date - date.today()).days
    months_left = days_left / 30
    
    if remaining > 0 and months_left > 0:
        monthly_saving = int(remaining / months_left)
        weekly_saving = int(remaining / (days_left / 7))
        daily_saving = int(remaining / days_left)
        
        with st.container(border=True):
            st.markdown("### 🎯 Target Tabungan")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Per Bulan", format_currency(monthly_saving))
            
            with col2:
                st.metric("Per Minggu", format_currency(weekly_saving))
            
            with col3:
                st.metric("Per Hari", format_currency(daily_saving))
            
            # Progress bar
            progress = current_savings / total_needed
            st.progress(progress)
            st.caption(f"Terkumpul: {progress * 100:.1f}% ({format_currency(current_savings)} dari {format_currency(total_needed)})")
    
    elif remaining == 0:
        st.success("🎉 Tabungan Anda sudah cukup! Siap berangkat umrah!")
    else:
        st.info("Masukkan tabungan saat ini untuk melihat rencana")


def render_save_simulation(params: Dict, cost: CostBreakdown):
    """Render save/export simulation with WhatsApp gating for anonymous users."""

    st.markdown("---")

    # Check if user is logged in
    try:
        from services.user.user_service import is_logged_in, get_current_user
        user_logged_in = is_logged_in()
        current_user = get_current_user()
    except Exception:
        user_logged_in = False
        current_user = None

    # Store simulation in session for later use (anonymous-first)
    if "pending_simulation" not in st.session_state:
        st.session_state.pending_simulation = None

    # Save current simulation to session
    simulation_data = {
        "timestamp": datetime.now().isoformat(),
        "params": {k: str(v) if isinstance(v, date) else v for k, v in params.items()},
        "total": cost.total,
        "breakdown": {
            "flight": cost.flight,
            "visa": cost.visa,
            "hotel_makkah": cost.hotel_makkah,
            "hotel_madinah": cost.hotel_madinah,
            "transport": cost.transport,
            "meals": cost.meals,
            "mutawif": cost.mutawif,
            "insurance": cost.insurance,
            "misc": cost.misc,
        }
    }
    st.session_state.pending_simulation = simulation_data

    if user_logged_in:
        # === LOGGED IN USER: Full features ===
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Simpan Simulasi", use_container_width=True):
                st.session_state.sim_saved.append(simulation_data)
                st.success("Simulasi disimpan!")

        with col2:
            if st.button("📤 Export PDF", use_container_width=True):
                st.info("Fitur export PDF akan segera hadir")

        with col3:
            if st.button("📱 Kirim ke WhatsApp", use_container_width=True, type="primary"):
                _send_simulation_to_whatsapp(simulation_data, current_user)

    else:
        # === ANONYMOUS USER: WhatsApp Gating ===
        cta_html = (
            '<div class="sim-save-cta">'
            '<h3>Simpan Rencana Umrah Anda</h3>'
            '<p>Dapatkan jadwal rencana lengkap langsung ke WhatsApp Anda</p>'
            '</div>'
        )
        st.markdown(cta_html, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            # HIGH-INTENT CTA BUTTON
            if st.button(
                "📲 Kirim Jadwal Rencana ke WhatsApp Saya",
                use_container_width=True,
                type="primary",
                key="wa_gate_btn"
            ):
                # Track WhatsApp gating click event for funnel analysis
                try:
                    from services.analytics.tracker import track_whatsapp_gating_click
                    track_whatsapp_gating_click(
                        page_name="simulator",
                        simulation_data=simulation_data
                    )
                except Exception:
                    pass  # Don't block UX if tracking fails

                # Store simulation and redirect to auth
                st.session_state.pending_simulation = simulation_data
                st.session_state.auth_redirect_to = "simulator"
                st.session_state.auth_action = "send_wa_simulation"
                st.session_state.current_page = "auth"
                st.session_state.auth_mode = "login"
                st.rerun()

        with col2:
            st.caption("Gratis & tanpa spam")

        # Secondary option
        st.markdown("---")
        st.caption("Atau copy manual:")
        total = format_currency(cost.total)
        msg = f"Simulasi Umrah LABBAIK:\n💰 Total: {total}/orang\n📅 Durasi: {params.get('duration', 10)} hari\n🔗 Hitung sendiri di: labbaik.streamlit.app"
        st.code(msg)


def _send_simulation_to_whatsapp(simulation: Dict, user):
    """Send simulation summary to user's WhatsApp."""
    try:
        from services.whatsapp import send_whatsapp_message

        if not user or not getattr(user, 'phone', None):
            st.warning("Nomor WhatsApp belum terdaftar. Silakan update di profil.")
            return

        # Format message
        total = format_currency(simulation.get('total', 0))
        params = simulation.get('params', {})

        message = f"""
*Rencana Umrah Anda*

📅 *Keberangkatan:* {params.get('departure_city', 'N/A')}
🗓️ *Tanggal:* {params.get('departure_date', 'N/A')}
⏱️ *Durasi:* {params.get('duration', 10)} hari

💰 *Estimasi Biaya:*
{total} per orang

🕋 Makkah: {params.get('nights_makkah', 5)} malam
🕌 Madinah: {params.get('nights_madinah', 4)} malam

---
Simulasi dari LABBAIK Smart Planner
🔗 labbaik.streamlit.app
        """.strip()

        # Send via WAHA
        success = send_whatsapp_message(user.phone, message)

        if success:
            st.success("Jadwal rencana telah dikirim ke WhatsApp Anda!")
        else:
            st.warning("Gagal mengirim. Silakan coba lagi.")

    except ImportError:
        st.info("Layanan WhatsApp belum tersedia. Copy pesan di bawah:")
        total = format_currency(simulation.get('total', 0))
        st.code(f"Rencana Umrah: {total}/orang")


def render_saved_simulations():
    """Render saved simulations."""

    saved = st.session_state.get("sim_saved", [])

    if saved:
        st.markdown("## 📁 Simulasi Tersimpan")

        for i, sim in enumerate(saved[-5:], 1):  # Show last 5
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 2, 1])

                with col1:
                    st.caption(f"#{i}")

                with col2:
                    params = sim["params"]
                    st.caption(f"{params.get('departure_city', 'N/A')} | {params.get('duration', 0)} hari")

                with col3:
                    st.markdown(f"**{format_currency(sim['total'])}**")


# =============================================================================
# SAVED SCENARIOS (Save & Compare)
# =============================================================================

def render_saved_scenarios(params: Dict, cost: CostBreakdown):
    """Render scenario saving and comparison UI.

    Allows users to save the current simulation as a named scenario,
    view saved scenarios as compact cards, delete individual scenarios,
    and compare 2-3 scenarios side-by-side.

    Stores data in ``st.session_state.saved_scenarios`` (max 5).
    Awards +10 XP on the first save per session.
    """

    st.markdown("## 📂 Skenario Tersimpan")
    st.caption("Simpan hingga 5 skenario dan bandingkan")

    saved: list = st.session_state.get("saved_scenarios", [])

    # --- Save current scenario ---
    with st.container(border=True):
        st.markdown("### 💾 Simpan Skenario Saat Ini")

        col_name, col_btn = st.columns([3, 1])

        with col_name:
            scenario_name = st.text_input(
                "Nama Skenario",
                placeholder="Contoh: Umrah Hemat Mei 2026",
                max_chars=50,
                key="save_scenario_name_input",
                label_visibility="collapsed",
            )

        with col_btn:
            save_disabled = len(saved) >= 5
            save_label = "Simpan Skenario" if not save_disabled else "Maks 5"
            if st.button(
                save_label,
                key="btn_save_scenario",
                use_container_width=True,
                type="primary",
                disabled=save_disabled,
            ):
                if not scenario_name.strip():
                    st.warning("Masukkan nama skenario terlebih dahulu.")
                else:
                    # Build scenario dict
                    new_scenario = {
                        "name": scenario_name.strip(),
                        "timestamp": datetime.now().isoformat(),
                        "params": {
                            k: str(v) if isinstance(v, date) else v
                            for k, v in params.items()
                        },
                        "cost": {
                            "flight": cost.flight,
                            "visa": cost.visa,
                            "hotel_makkah": cost.hotel_makkah,
                            "hotel_madinah": cost.hotel_madinah,
                            "transport": cost.transport,
                            "meals": cost.meals,
                            "mutawif": cost.mutawif,
                            "insurance": cost.insurance,
                            "misc": cost.misc,
                            "seasonal_adj": cost.seasonal_adj,
                            "total": cost.total,
                        },
                    }
                    saved.append(new_scenario)
                    st.session_state.saved_scenarios = saved

                    # XP for first save
                    if not st.session_state.get("simulator_xp_save_scenario", False):
                        add_xp_safe(10, "Simpan Skenario Simulator")
                        st.session_state.simulator_xp_save_scenario = True

                    st.success(f"Skenario '{scenario_name}' berhasil disimpan!")
                    st.rerun()

        if save_disabled:
            st.caption("Hapus skenario lama untuk menyimpan yang baru.")

    # --- Display saved scenarios ---
    if not saved:
        st.info("Belum ada skenario tersimpan. Simpan skenario pertama Anda di atas.")
        return

    st.markdown("---")

    # Render each saved scenario as a compact card
    delete_idx: Optional[int] = None

    for idx, sc in enumerate(saved):
        sc_params = sc.get("params", {})
        sc_cost = sc.get("cost", {})
        sc_total = sc_cost.get("total", 0)
        sc_name = sc.get("name", f"Skenario {idx + 1}")
        sc_time = sc.get("timestamp", "")

        # Format date nicely
        try:
            dt = datetime.fromisoformat(sc_time)
            date_str = dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            date_str = sc_time[:10] if len(sc_time) >= 10 else "-"

        duration_val = sc_params.get("duration", "-")
        hotel_star = sc_params.get("hotel_star_makkah", "-")
        num_pax = sc_params.get("num_travelers", 1)
        city = sc_params.get("departure_city", "-")

        card_html = (
            f'<div class="saved-scenario-card">'
            f'<div class="scenario-name">{sc_name}</div>'
            f'<div class="scenario-cost">{format_currency(sc_total)}</div>'
            f'<div class="scenario-meta">'
            f'{city} &middot; {duration_val} hari &middot; Hotel {"&#11088;" * int(hotel_star) if str(hotel_star).isdigit() else hotel_star} &middot; {num_pax} orang'
            f'</div>'
            f'<div class="scenario-meta">{date_str}</div>'
            f'</div>'
        )
        col_card, col_del = st.columns([5, 1])

        with col_card:
            st.markdown(card_html, unsafe_allow_html=True)

        with col_del:
            if st.button("Hapus", key=f"del_scenario_{idx}", use_container_width=True):
                delete_idx = idx

    # Process deletion outside the loop to avoid mutation during iteration
    if delete_idx is not None:
        st.session_state.saved_scenarios.pop(delete_idx)
        st.rerun()

    # --- Compare button ---
    st.markdown("---")
    if len(saved) >= 2:
        if st.button(
            "Bandingkan Skenario",
            key="btn_compare_scenarios",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["show_scenario_comparison"] = True
            st.rerun()

        if st.session_state.get("show_scenario_comparison", False):
            render_scenario_comparison(saved)
    else:
        st.caption("Simpan minimal 2 skenario untuk membandingkan.")


def render_scenario_comparison(scenarios: list):
    """Render a side-by-side comparison table of saved scenarios.

    Compares: Nama, Durasi, Hotel Bintang, Jumlah Orang, Total Biaya.
    Highlights the cheapest scenario in green and shows price differences.
    """

    # Use up to 3 scenarios for comparison
    to_compare = scenarios[:3]

    if len(to_compare) < 2:
        st.info("Minimal 2 skenario diperlukan untuk perbandingan.")
        return

    # Header
    header_html = (
        '<div class="scenario-compare-header" role="status" aria-live="polite">'
        '<h3><span aria-hidden="true">&#128200;</span> Perbandingan Skenario</h3>'
        f'<p>Membandingkan {len(to_compare)} skenario</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Find cheapest
    totals = [sc.get("cost", {}).get("total", 0) for sc in to_compare]
    min_total = min(totals) if totals else 0

    # Build table HTML
    # Header row
    header_cells = '<th>Kriteria</th>'
    for sc in to_compare:
        header_cells += f'<th>{sc.get("name", "Skenario")}</th>'

    # Data rows
    rows_data = [
        ("Durasi", [f'{sc.get("params", {}).get("duration", "-")} hari' for sc in to_compare]),
        ("Hotel Makkah", [f'{"&#11088;" * int(sc.get("params", {}).get("hotel_star_makkah", 0))}' if str(sc.get("params", {}).get("hotel_star_makkah", "")).replace(".", "").isdigit() else "-" for sc in to_compare]),
        ("Hotel Madinah", [f'{"&#11088;" * int(sc.get("params", {}).get("hotel_star_madinah", 0))}' if str(sc.get("params", {}).get("hotel_star_madinah", "")).replace(".", "").isdigit() else "-" for sc in to_compare]),
        ("Jumlah Orang", [str(sc.get("params", {}).get("num_travelers", 1)) for sc in to_compare]),
        ("Kota Berangkat", [sc.get("params", {}).get("departure_city", "-") for sc in to_compare]),
        ("Kelas Penerbangan", [sc.get("params", {}).get("flight_class", "-").title() for sc in to_compare]),
        ("Paket Makan", [sc.get("params", {}).get("meal_type", "-").title() for sc in to_compare]),
    ]

    body_rows = ''
    for label, values in rows_data:
        body_rows += f'<tr><td><strong>{label}</strong></td>'
        for v in values:
            body_rows += f'<td>{v}</td>'
        body_rows += '</tr>'

    # Total cost row with cheapest highlight
    body_rows += '<tr><td><strong>Total Biaya</strong></td>'
    for sc in to_compare:
        t = sc.get("cost", {}).get("total", 0)
        css_class = ' class="cheapest"' if t == min_total else ''
        body_rows += f'<td{css_class}>{format_currency(t)}</td>'
    body_rows += '</tr>'

    # Difference row
    body_rows += '<tr><td><strong>Selisih dari Termurah</strong></td>'
    for sc in to_compare:
        t = sc.get("cost", {}).get("total", 0)
        diff = t - min_total
        if diff == 0:
            body_rows += '<td class="cheapest">Termurah</td>'
        else:
            body_rows += f'<td class="diff-cell">+{format_currency(diff)}</td>'
    body_rows += '</tr>'

    table_html = (
        f'<table class="scenario-compare-table">'
        f'<thead><tr>{header_cells}</tr></thead>'
        f'<tbody>{body_rows}</tbody>'
        f'</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # Summary insight
    cheapest_name = to_compare[totals.index(min_total)].get("name", "Skenario")
    most_expensive_total = max(totals)
    savings = most_expensive_total - min_total

    if savings > 0:
        st.success(
            f"**{cheapest_name}** adalah skenario termurah. "
            f"Anda bisa hemat hingga **{format_currency(savings)}** dibanding skenario termahal."
        )


def _generate_simulator_pdf_html(params: Dict, cost_result: CostBreakdown) -> str:
    """Generate a print-friendly HTML report of the simulation.

    Returns an HTML string with LABBAIK branding, parameter summary,
    and cost breakdown suitable for download/printing.
    """

    # Resolve parameter display values
    departure_city = params.get("departure_city", "Jakarta")
    departure_date_val = params.get("departure_date", "-")
    if isinstance(departure_date_val, date):
        departure_date_str = departure_date_val.strftime("%d/%m/%Y")
    else:
        departure_date_str = str(departure_date_val)

    duration = params.get("duration", 10)
    nights_makkah = params.get("nights_makkah", 5)
    nights_madinah = params.get("nights_madinah", 4)
    hotel_star_makkah = params.get("hotel_star_makkah", 4)
    hotel_star_madinah = params.get("hotel_star_madinah", 4)
    flight_class = params.get("flight_class", "economy").title()
    meal_type = params.get("meal_type", "standard").title()
    num_travelers = params.get("num_travelers", 1)
    include_mutawif = params.get("include_mutawif", False)
    include_insurance = params.get("include_insurance", False)

    season, season_desc = get_season(
        departure_date_val if isinstance(departure_date_val, date) else date.today()
    )

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Build cost breakdown rows
    cost_items = [
        ("Tiket Pesawat", cost_result.flight),
        ("Visa Umrah", cost_result.visa),
        ("Hotel Makkah", cost_result.hotel_makkah),
        ("Hotel Madinah", cost_result.hotel_madinah),
        ("Transportasi", cost_result.transport),
        ("Makan", cost_result.meals),
        ("Mutawif", cost_result.mutawif),
        ("Asuransi", cost_result.insurance),
        ("Lain-lain", cost_result.misc),
    ]

    cost_rows_html = ''
    for label, amount in cost_items:
        if amount > 0:
            cost_rows_html += (
                f'<tr><td style="padding:8px 12px;border-bottom:1px solid #ddd;">{label}</td>'
                f'<td style="padding:8px 12px;border-bottom:1px solid #ddd;text-align:right;">'
                f'{format_currency(amount)}</td></tr>'
            )

    if cost_result.seasonal_adj > 0:
        cost_rows_html += (
            f'<tr><td style="padding:8px 12px;border-bottom:1px solid #ddd;">Penyesuaian Musim</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #ddd;text-align:right;">'
            f'+{format_currency(cost_result.seasonal_adj)}</td></tr>'
        )

    group_total_html = ''
    if num_travelers > 1:
        group_total = cost_result.total * num_travelers
        group_total_html = (
            f'<tr style="background:#e8f5e9;">'
            f'<td style="padding:10px 12px;font-weight:bold;">Total {num_travelers} Orang</td>'
            f'<td style="padding:10px 12px;font-weight:bold;text-align:right;">'
            f'{format_currency(group_total)}</td></tr>'
        )

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Laporan Simulasi Umrah - LABBAIK</title>
<style>
body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0; padding: 20px;
    color: #333; background: #fff;
    max-width: 800px; margin: 0 auto;
}}
.header {{
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    color: white; padding: 24px 30px; border-radius: 12px;
    margin-bottom: 24px; text-align: center;
}}
.header h1 {{
    color: #d4af37; margin: 0 0 4px 0; font-size: 1.6rem;
}}
.header p {{
    color: #b0b0b0; margin: 0; font-size: 0.9rem;
}}
.section {{
    margin-bottom: 20px;
}}
.section h2 {{
    color: #1b2a4a; font-size: 1.15rem;
    border-bottom: 2px solid #d4af37; padding-bottom: 6px;
    margin-bottom: 12px;
}}
table {{
    width: 100%; border-collapse: collapse;
}}
.param-table td {{
    padding: 6px 12px; border-bottom: 1px solid #eee;
}}
.param-table td:first-child {{
    color: #666; width: 45%;
}}
.cost-table {{
    border: 1px solid #ddd; border-radius: 8px; overflow: hidden;
}}
.total-row {{
    background: #1b2a4a; color: white;
}}
.total-row td {{
    padding: 12px; font-size: 1.1rem; font-weight: bold;
    border-bottom: none !important;
}}
.footer {{
    text-align: center; color: #999; font-size: 0.8rem;
    margin-top: 30px; padding-top: 16px;
    border-top: 1px solid #eee;
}}
@media print {{
    body {{ padding: 10px; }}
    .header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .total-row {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
}}
</style>
</head>
<body>
<div class="header">
    <h1>LABBAIK Smart Planner</h1>
    <p>Laporan Simulasi Biaya Umrah</p>
</div>

<div class="section">
    <h2>Parameter Simulasi</h2>
    <table class="param-table">
        <tr><td>Kota Berangkat</td><td><strong>{departure_city}</strong></td></tr>
        <tr><td>Tanggal Berangkat</td><td><strong>{departure_date_str}</strong></td></tr>
        <tr><td>Durasi</td><td><strong>{duration} hari</strong></td></tr>
        <tr><td>Malam di Makkah</td><td><strong>{nights_makkah} malam</strong></td></tr>
        <tr><td>Malam di Madinah</td><td><strong>{nights_madinah} malam</strong></td></tr>
        <tr><td>Hotel Makkah</td><td><strong>{"&#11088;" * hotel_star_makkah} ({hotel_star_makkah} bintang)</strong></td></tr>
        <tr><td>Hotel Madinah</td><td><strong>{"&#11088;" * hotel_star_madinah} ({hotel_star_madinah} bintang)</strong></td></tr>
        <tr><td>Kelas Penerbangan</td><td><strong>{flight_class}</strong></td></tr>
        <tr><td>Paket Makan</td><td><strong>{meal_type}</strong></td></tr>
        <tr><td>Jumlah Jamaah</td><td><strong>{num_travelers} orang</strong></td></tr>
        <tr><td>Mutawif</td><td><strong>{"Ya" if include_mutawif else "Tidak"}</strong></td></tr>
        <tr><td>Asuransi</td><td><strong>{"Ya" if include_insurance else "Tidak"}</strong></td></tr>
        <tr><td>Musim</td><td><strong>{season_desc}</strong></td></tr>
    </table>
</div>

<div class="section">
    <h2>Rincian Biaya (per Orang)</h2>
    <table class="cost-table">
        {cost_rows_html}
        <tr class="total-row">
            <td>TOTAL PER ORANG</td>
            <td style="text-align:right;">{format_currency(cost_result.total)}</td>
        </tr>
        {group_total_html}
    </table>
</div>

<div class="footer">
    <p>Dibuat pada {generated_at} oleh LABBAIK Smart Planner &mdash; app.labbaik.io</p>
    <p>Harga bersifat estimasi dan dapat berubah sewaktu-waktu.</p>
</div>
</body>
</html>"""

    return html


# =============================================================================
# SCENARIO PLANNING UI
# =============================================================================

def render_scenario_planning(cost: CostBreakdown, params: Dict):
    """Render complete scenario planning section."""

    st.markdown("## 🎯 Scenario Planning")
    st.caption("Perencanaan biaya dengan analisis skenario dan risiko")

    # Generate scenarios
    scenarios = generate_all_scenarios(cost)

    # Scenario cards
    st.markdown("### 📊 Perbandingan Skenario")

    cols = st.columns(3)

    scenario_configs = [
        (ScenarioType.OPTIMISTIC, "🌟", "#28a745", "success"),
        (ScenarioType.REALISTIC, "⚖️", "#007bff", "info"),
        (ScenarioType.PESSIMISTIC, "⚠️", "#dc3545", "warning"),
    ]

    for col, (sc_type, icon, color, alert_type) in zip(cols, scenario_configs):
        scenario = scenarios[sc_type]

        with col:
            with st.container(border=True):
                st.markdown(f"### {icon} {scenario.name}")
                st.markdown(f"**Probabilitas: {scenario.probability * 100:.0f}%**")

                # Main cost
                st.markdown(f"## {format_currency(scenario.adjusted_cost)}")
                st.caption("per orang")

                # Confidence range
                bg_style = "background:linear-gradient(90deg,#333 0%," + color + " 50%,#333 100%)"
                conf_html = (
                    f'<div class="sim-confidence-bar" style="{bg_style}">'
                    f'<small>{format_currency(scenario.confidence_low)} - {format_currency(scenario.confidence_high)}</small>'
                    f'</div>'
                )
                st.markdown(conf_html, unsafe_allow_html=True)

                st.caption("Range estimasi (90% confidence)")

                # Assumptions
                with st.expander("📋 Asumsi"):
                    for assumption in scenario.assumptions:
                        st.markdown(f"• {assumption}")

    # Scenario difference analysis
    st.markdown("---")
    st.markdown("### 📈 Analisis Perbedaan Skenario")

    optimistic = scenarios[ScenarioType.OPTIMISTIC]
    realistic = scenarios[ScenarioType.REALISTIC]
    pessimistic = scenarios[ScenarioType.PESSIMISTIC]

    # Calculate differences
    diff_opt_real = realistic.adjusted_cost - optimistic.adjusted_cost
    diff_real_pess = pessimistic.adjusted_cost - realistic.adjusted_cost
    total_range = pessimistic.adjusted_cost - optimistic.adjusted_cost

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Optimis vs Realistis",
            format_currency(diff_opt_real),
            delta=f"+{diff_opt_real / optimistic.adjusted_cost * 100:.1f}%",
            delta_color="inverse"
        )

    with col2:
        st.metric(
            "Realistis vs Pesimis",
            format_currency(diff_real_pess),
            delta=f"+{diff_real_pess / realistic.adjusted_cost * 100:.1f}%",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "Total Range",
            format_currency(total_range),
            delta=f"{total_range / realistic.adjusted_cost * 100:.1f}% variasi"
        )

    # Visual range bar
    st.markdown("#### Range Biaya")

    # Create visual range
    range_data = {
        "Optimis": optimistic.adjusted_cost,
        "Realistis": realistic.adjusted_cost,
        "Pesimis": pessimistic.adjusted_cost,
    }

    max_val = max(range_data.values())
    for label, value in range_data.items():
        pct = value / max_val * 100
        color = "#28a745" if "Optimis" in label else "#007bff" if "Realistis" in label else "#dc3545"
        st.markdown(f"**{label}**: {format_currency(value)}")
        range_bar_html = (
            f'<div class="sim-range-bar">'
            f'<div class="sim-range-fill" style="background:{color};width:{pct}%;"></div>'
            f'</div>'
        )
        st.markdown(range_bar_html, unsafe_allow_html=True)


def render_monte_carlo_analysis(cost: CostBreakdown):
    """Render Monte Carlo simulation results."""

    st.markdown("### 🎲 Simulasi Monte Carlo")
    st.caption("1,000 simulasi untuk estimasi range biaya yang lebih akurat")

    # Run simulation
    with st.spinner("Menjalankan simulasi..."):
        mc_results = run_monte_carlo_simulation(cost)

    # Results display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Rata-rata", format_currency(mc_results["mean"]))
    with col2:
        st.metric("Median", format_currency(mc_results["median"]))
    with col3:
        st.metric("Std Deviasi", format_currency(mc_results["std_dev"]))
    with col4:
        st.metric("Range", format_currency(mc_results["max"] - mc_results["min"]))

    # Percentile breakdown
    st.markdown("#### Distribusi Percentile")

    percentiles = [
        ("P10 (Optimis)", mc_results["p10"], "#28a745"),
        ("P25", mc_results["p25"], "#5cb85c"),
        ("P50 (Median)", mc_results["median"], "#007bff"),
        ("P75", mc_results["p75"], "#f0ad4e"),
        ("P90 (Pesimis)", mc_results["p90"], "#dc3545"),
    ]

    cols = st.columns(5)
    for col, (label, value, color) in zip(cols, percentiles):
        with col:
            pct_html = (
                f'<div class="sim-percentile" style="border-left:4px solid {color};">'
                f'<div class="label">{label}</div>'
                f'<div class="value">{format_currency(value)}</div>'
                f'</div>'
            )
            st.markdown(pct_html, unsafe_allow_html=True)

    # Confidence interval recommendation
    st.markdown("---")
    with st.container(border=True):
        st.markdown("#### 💡 Rekomendasi Budget")
        reco_text = (
            f"Berdasarkan simulasi Monte Carlo dengan 1,000 iterasi:\n\n"
            f"- **Budget Minimal** (P10): {format_currency(mc_results['p10'])}\n"
            f"- **Budget Rekomendasi** (P75): {format_currency(mc_results['p75'])}\n"
            f"- **Budget Aman** (P90): {format_currency(mc_results['p90'])}\n\n"
            f"> Kami rekomendasikan menyiapkan budget sebesar "
            f"**{format_currency(mc_results['p75'])}** "
            f"untuk mengantisipasi 75% kemungkinan skenario."
        )
        st.markdown(reco_text)


def render_sensitivity_analysis(params: Dict, cost: CostBreakdown):
    """Render sensitivity analysis (tornado chart style)."""

    st.markdown("### 🌪️ Analisis Sensitivitas")
    st.caption("Variabel mana yang paling mempengaruhi total biaya?")

    # Calculate sensitivity
    sensitivity_results = calculate_sensitivity(params, cost)

    if not sensitivity_results:
        st.info("Tidak dapat menghitung sensitivitas dengan konfigurasi saat ini")
        return

    # Tornado chart (text-based)
    st.markdown("#### Tornado Chart")

    max_impact = max(s.impact_range for s in sensitivity_results) if sensitivity_results else 1

    for result in sensitivity_results:
        # Calculate bar widths
        low_diff = result.base_cost - result.low_cost
        high_diff = result.high_cost - result.base_cost

        low_pct = abs(low_diff) / max_impact * 50 if max_impact > 0 else 0
        high_pct = abs(high_diff) / max_impact * 50 if max_impact > 0 else 0

        st.markdown(f"**{result.variable}**")
        st.caption(f"{result.low_value} ← {result.base_value} → {result.high_value}")

        # Visual bar
        tornado_html = (
            f'<div class="sim-tornado-bar">'
            f'<div class="sim-tornado-left">'
            f'<div class="sim-tornado-fill-green" style="width:{low_pct}%;"></div>'
            f'</div>'
            f'<div class="sim-tornado-center"></div>'
            f'<div class="sim-tornado-right">'
            f'<div class="sim-tornado-fill-red" style="width:{high_pct}%;"></div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(tornado_html, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            if low_diff != 0:
                st.caption(f"↓ {format_currency(abs(low_diff))}")
        with col2:
            st.caption(f"Base: {format_currency(result.base_cost)}")
        with col3:
            if high_diff != 0:
                st.caption(f"↑ {format_currency(high_diff)}")

    # Summary table
    st.markdown("---")
    st.markdown("#### Ringkasan Sensitivitas")

    for result in sensitivity_results:
        impact_pct = result.impact_range / result.base_cost * 100

        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"**{result.variable}**")

            with col2:
                st.markdown(f"Impact: **{format_currency(result.impact_range)}**")

            with col3:
                if impact_pct > 20:
                    st.error(f"{impact_pct:.1f}% variasi")
                elif impact_pct > 10:
                    st.warning(f"{impact_pct:.1f}% variasi")
                else:
                    st.success(f"{impact_pct:.1f}% variasi")


def render_risk_factors(cost: CostBreakdown):
    """Render risk factors analysis."""

    st.markdown("### ⚠️ Analisis Faktor Risiko")
    st.caption("Faktor-faktor yang dapat mempengaruhi biaya umrah Anda")

    # Group by category
    categories = {}
    for rf in RISK_FACTORS:
        if rf.category not in categories:
            categories[rf.category] = []
        categories[rf.category].append(rf)

    # Display by category
    category_icons = {
        "ekonomi": "💰",
        "penerbangan": "✈️",
        "akomodasi": "🏨",
        "lainnya": "📦",
        "regulasi": "📋"
    }

    for category, risks in categories.items():
        icon = category_icons.get(category, "📌")
        st.markdown(f"#### {icon} {category.title()}")

        for rf in risks:
            # Calculate potential impact
            avg_impact = (rf.impact_min + rf.impact_max) / 2
            potential_cost = int(cost.total * avg_impact / 100)

            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{rf.name}**")
                    st.caption(rf.description)

                with col2:
                    # Probability indicator
                    prob_pct = rf.probability * 100
                    if prob_pct >= 60:
                        st.error(f"📊 {prob_pct:.0f}%")
                    elif prob_pct >= 40:
                        st.warning(f"📊 {prob_pct:.0f}%")
                    else:
                        st.success(f"📊 {prob_pct:.0f}%")
                    st.caption("Probabilitas")

                with col3:
                    st.markdown(f"**+{format_currency(potential_cost)}**")
                    st.caption(f"Impact {rf.impact_min:.0f}-{rf.impact_max:.0f}%")

    # Risk mitigation tips
    st.markdown("---")
    st.markdown("#### 🛡️ Tips Mitigasi Risiko")

    mitigations = [
        ("✈️ Booking tiket 3-6 bulan sebelumnya", "Hindari kenaikan harga last-minute"),
        ("💱 Pantau kurs dan tukar saat menguntungkan", "Manfaatkan kurs bagus untuk pembelian SAR"),
        ("🏨 Reservasi hotel jauh hari", "Dapatkan harga terbaik dan pilihan hotel"),
        ("🛡️ Beli asuransi perjalanan", "Lindungi dari biaya medis tak terduga"),
        ("📅 Pilih waktu di luar peak season", "Hemat 15-35% dari total biaya"),
        ("💰 Siapkan dana darurat 10-15%", "Buffer untuk pengeluaran tak terduga"),
    ]

    cols = st.columns(2)
    for i, (tip, desc) in enumerate(mitigations):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{tip}**")
                st.caption(desc)


def render_group_discount_analysis(cost: CostBreakdown, num_travelers: int):
    """Render group discount and break-even analysis."""

    st.markdown("### 👥 Analisis Grup & Diskon")

    # Calculate break-even
    be_analysis = calculate_break_even_analysis(cost, num_travelers)

    # Current discount status
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### Status Diskon Saat Ini")
            st.markdown(f"**Jumlah Jamaah:** {num_travelers} orang")
            st.markdown(f"**Kategori:** {be_analysis['discount_label']}")
            st.markdown(f"**Diskon:** {be_analysis['discount_percentage']:.0f}%")

            if be_analysis['discount_percentage'] > 0:
                st.success(f"Hemat {format_currency(be_analysis['total_savings'])} total!")
            else:
                st.info("Tambah jamaah untuk dapat diskon grup")

    with col2:
        with st.container(border=True):
            st.markdown("#### Biaya dengan Diskon")

            st.metric(
                "Per Orang",
                format_currency(be_analysis['discounted_per_person']),
                delta=f"-{format_currency(cost.total - be_analysis['discounted_per_person'])}" if be_analysis['discount_percentage'] > 0 else None
            )

            st.metric(
                "Total Grup",
                format_currency(be_analysis['total_group_cost'])
            )

    # Discount tiers visualization
    st.markdown("---")
    st.markdown("#### 📊 Tier Diskon Grup")

    for tier in be_analysis['discount_tiers']:
        is_current = (num_travelers >= tier['min_travelers'] and
                      (tier == be_analysis['discount_tiers'][-1] or
                       num_travelers < be_analysis['discount_tiers'][be_analysis['discount_tiers'].index(tier) + 1]['min_travelers']))

        discount_amount = int(cost.total * tier['discount'])
        final_price = cost.total - discount_amount

        border_color = "#d4af37" if is_current else "#333"
        shadow_style = "box-shadow:0 0 10px rgba(212,175,55,0.3);" if is_current else ""
        discount_pct_str = f"{tier['discount']*100:.0f}"

        tier_html = (
            f'<div class="sim-discount-tier" style="border:2px solid {border_color};{shadow_style}">'
            f'<div class="inner">'
            f'<div>'
            f'<span class="tier-name">{tier["label"]}</span>'
            f'<span class="tier-count"> ({tier["min_travelers"]}+ jamaah)</span>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<span class="tier-pct">{discount_pct_str}% OFF</span><br/>'
            f'<span class="tier-price">{format_currency(final_price)}/orang</span>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(tier_html, unsafe_allow_html=True)

    # Next tier suggestion
    current_tier_idx = 0
    for i, tier in enumerate(be_analysis['discount_tiers']):
        if num_travelers >= tier['min_travelers']:
            current_tier_idx = i

    if current_tier_idx < len(be_analysis['discount_tiers']) - 1:
        next_tier = be_analysis['discount_tiers'][current_tier_idx + 1]
        needed = next_tier['min_travelers'] - num_travelers

        with st.container(border=True):
            next_discount_str = f"{next_tier['discount']*100:.0f}"
            st.markdown(
                f"💡 **Tambah {needed} jamaah** untuk naik ke tier "
                f"**{next_tier['label']}** dan dapat diskon **{next_discount_str}%**!"
            )


# =============================================================================
# SEASON IMPACT (from SeasonCalendar service)
# =============================================================================

def render_season_impact(cost: CostBreakdown, params: Dict):
    """Render season impact analysis using the SeasonCalendar service."""
    if not HAS_SEASON_CALENDAR:
        return

    try:
        calendar = get_season_calendar()
        departure_date = params.get("departure_date", date.today() + timedelta(days=60))

        # Get season info
        season_period = calendar.get_season(departure_date)
        weight = calendar.get_weight(departure_date)
        recommendation = calendar.get_booking_recommendation(departure_date)

        # Determine season display name and description
        if season_period:
            season_name = season_period.name
            season_desc = season_period.description
        else:
            season_name = "Musim Reguler"
            season_desc = "Bukan musim puncak - harga cenderung normal"

        # Determine multiplier badge color
        if weight <= 1.0:
            badge_class = "season-multiplier-green"
        elif weight <= 1.3:
            badge_class = "season-multiplier-yellow"
        elif weight <= 1.5:
            badge_class = "season-multiplier-orange"
        else:
            badge_class = "season-multiplier-red"

        # Calculate adjusted cost estimate
        base_cost_no_season = cost.total - cost.seasonal_adj
        adjusted_by_calendar = int(base_cost_no_season * weight)

        # Urgency color mapping
        urgency = recommendation.get("urgency", "LOW")
        urgency_colors = {
            "CRITICAL": "#dc3545",
            "HIGH": "#fd7e14",
            "MEDIUM": "#ffc107",
            "LOW": "#28a745",
        }
        urgency_color = urgency_colors.get(urgency, "#28a745")

        urgency_labels = {
            "CRITICAL": "KRITIS",
            "HIGH": "TINGGI",
            "MEDIUM": "SEDANG",
            "LOW": "RENDAH",
        }
        urgency_label = urgency_labels.get(urgency, "RENDAH")

        # Build the HTML card
        card_html = (
            '<div class="season-impact-card" role="status" aria-live="polite">'
            '<h4><span aria-hidden="true">📅</span> Dampak Musim</h4>'
            f'<div class="season-label"><strong>Musim:</strong> {season_name}</div>'
            f'<div class="season-detail">{season_desc}</div>'
            f'<div style="margin:0.6rem 0;">'
            f'<span class="season-multiplier-badge {badge_class}">'
            f'Faktor harga musim: {weight}x'
            f'</span>'
            f'</div>'
            f'<div class="season-label">'
            f'<strong>Estimasi biaya setelah faktor musim:</strong> '
            f'{format_currency(adjusted_by_calendar)}'
            f'</div>'
            f'<div class="season-detail">'
            f'Dampak harga: {recommendation.get("expected_price_impact", "Normal")}'
            f'</div>'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        # Booking recommendation
        reco_text = recommendation.get("recommendation", "")
        advance_days = recommendation.get("recommended_advance_booking_days", 14)

        reco_html = (
            '<div class="season-recommendation" role="status" aria-live="polite">'
            f'<div class="reco-urgency" style="color:{urgency_color};">'
            f'<span aria-hidden="true">&#9888;</span> '
            f'Urgensi Booking: {urgency_label}'
            f'</div>'
            f'<div class="reco-text">{reco_text}</div>'
            f'<div class="reco-text" style="margin-top:0.3rem;">'
            f'Disarankan booking minimal <strong>{advance_days} hari</strong> sebelumnya.'
            f'</div>'
            '</div>'
        )
        st.markdown(reco_html, unsafe_allow_html=True)

        # Low season date suggestions
        travel_year = departure_date.year
        low_season_gaps = calendar.get_low_season_dates(year=travel_year, min_gap_days=14)

        if low_season_gaps and weight > 1.0:
            # Build month names for the low season periods
            month_names_id = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }

            low_periods = []
            for gap_start, gap_end in low_season_gaps:
                start_month = month_names_id.get(gap_start.month, str(gap_start.month))
                end_month = month_names_id.get(gap_end.month, str(gap_end.month))
                if gap_start.month == gap_end.month:
                    low_periods.append(f"{start_month} {gap_start.year}")
                else:
                    low_periods.append(f"{start_month} - {end_month} {gap_end.year}")

            low_text = ", ".join(low_periods[:3])
            savings_pct = int((weight - 1.0) * 100)

            tip_html = (
                '<div class="season-low-tip" role="status" aria-live="polite">'
                '<div class="tip-title">'
                '<span aria-hidden="true">&#128161;</span> Tip Hemat Musim'
                '</div>'
                f'<div class="tip-text">'
                f'Periode harga lebih murah di {travel_year}: <strong>{low_text}</strong>. '
                f'Harga bisa lebih murah hingga <strong>{savings_pct}%</strong> '
                f'dibanding musim saat ini.'
                f'</div>'
                '</div>'
            )
            st.markdown(tip_html, unsafe_allow_html=True)

    except Exception:
        # Graceful fallback -- do not break the page
        pass


# =============================================================================
# AI ANALYSIS
# =============================================================================

def render_ai_analysis(cost: CostBreakdown, params: Dict):
    """Render AI-powered financial analysis of the simulation results."""

    st.markdown("## 🤖 Analisis AI")
    st.caption("Konsultasi keuangan Umrah berbasis AI")

    # Build summary for the prompt
    season, season_desc = get_season(params.get("departure_date", date.today()))
    total_str = format_currency(cost.total)
    flight_str = format_currency(cost.flight)
    hotel_m_str = format_currency(cost.hotel_makkah)
    hotel_d_str = format_currency(cost.hotel_madinah)
    meals_str = format_currency(cost.meals)
    seasonal_str = format_currency(cost.seasonal_adj)
    num_travelers = params.get("num_travelers", 1)

    prompt = (
        f"Analisis simulasi biaya Umrah berikut dan berikan saran keuangan:\n\n"
        f"- Kota berangkat: {params.get('departure_city', 'Jakarta')}\n"
        f"- Durasi: {params.get('duration', 10)} hari\n"
        f"- Malam di Makkah: {params.get('nights_makkah', 5)}\n"
        f"- Malam di Madinah: {params.get('nights_madinah', 4)}\n"
        f"- Hotel Makkah: bintang {params.get('hotel_star_makkah', 4)}\n"
        f"- Hotel Madinah: bintang {params.get('hotel_star_madinah', 4)}\n"
        f"- Kelas penerbangan: {params.get('flight_class', 'economy')}\n"
        f"- Paket makan: {params.get('meal_type', 'standard')}\n"
        f"- Jumlah jamaah: {num_travelers}\n"
        f"- Musim: {season_desc}\n\n"
        f"Rincian biaya per orang:\n"
        f"- Tiket pesawat: {flight_str}\n"
        f"- Hotel Makkah: {hotel_m_str}\n"
        f"- Hotel Madinah: {hotel_d_str}\n"
        f"- Makan: {meals_str}\n"
        f"- Penyesuaian musim: {seasonal_str}\n"
        f"- TOTAL: {total_str}\n\n"
        f"Berikan:\n"
        f"1. Evaluasi apakah budget ini wajar\n"
        f"2. 3 tips spesifik untuk menghemat\n"
        f"3. Rekomendasi waktu terbaik untuk booking\n"
        f"4. Saran tabungan bulanan jika berangkat 6 bulan lagi\n"
        f"Jawab dalam Bahasa Indonesia, singkat dan praktis."
    )

    if st.button("🔍 Minta Analisis AI", key="btn_ai_analysis", use_container_width=True):
        with st.spinner("Menganalisis simulasi Anda..."):
            response = ai_complete(
                prompt,
                system_prompt="Kamu adalah konsultan keuangan Umrah berpengalaman.",
                max_tokens=1000,
            )

        if response:
            st.session_state.simulator_ai_response = response

            # Award XP for first AI analysis
            if not st.session_state.get("simulator_xp_ai", False):
                add_xp_safe(20, "Analisis AI Simulator")
                st.session_state.simulator_xp_ai = True
        else:
            st.warning(
                "Layanan AI sedang tidak tersedia. Silakan coba lagi nanti."
            )

    # Show cached response
    cached = st.session_state.get("simulator_ai_response")
    if cached:
        ai_html = (
            '<div class="ai-card" role="status" aria-live="polite">'
            '<h4>🤖 Hasil Analisis AI</h4>'
            '<p>' + _markdown_to_html_simple(cached) + '</p>'
            '</div>'
        )
        st.markdown(ai_html, unsafe_allow_html=True)


# =============================================================================
# LIVE HOTEL PRICES
# =============================================================================

def render_live_hotel_prices(params: Dict):
    """Render live hotel prices from APIs."""

    st.markdown("## 🏨 Harga Hotel Live")
    st.caption("Data real-time dari berbagai sumber (Amadeus, Xotelo, dll)")

    # Try to load live data
    try:
        from services.umrah import get_cost_integration_service

        service = get_cost_integration_service()

        # Format dates
        check_in = params.get("departure_date")
        if check_in:
            check_in_str = check_in.strftime("%Y-%m-%d")
            duration = params.get("duration", 10)
            check_out_str = (check_in + timedelta(days=duration)).strftime("%Y-%m-%d")
        else:
            check_in_str = None
            check_out_str = None

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🕋 Hotel Makkah")

            makkah_price = service.get_hotel_price(
                "Makkah",
                params.get("hotel_star_makkah", 4),
                check_in_str,
                check_out_str
            )

            with st.container(border=True):
                # Data source indicator
                if makkah_price.is_live_data:
                    st.success(f"🟢 Live Data ({makkah_price.source})")
                else:
                    st.warning("🟡 Data Estimasi")

                st.markdown(f"**{makkah_price.hotel_name}**")
                st.markdown(f"{'⭐' * makkah_price.hotel_stars}")

                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Per Malam", format_currency(makkah_price.price_per_night_idr))
                with metric_col2:
                    st.metric("Jarak", f"{makkah_price.distance_to_haram_km:.1f} km")

                st.caption(f"🚶 {makkah_price.walking_time_minutes} menit ke Masjidil Haram")

        with col2:
            st.markdown("### 🕌 Hotel Madinah")

            madinah_price = service.get_hotel_price(
                "Madinah",
                params.get("hotel_star_madinah", 4),
                check_in_str,
                check_out_str
            )

            with st.container(border=True):
                if madinah_price.is_live_data:
                    st.success(f"🟢 Live Data ({madinah_price.source})")
                else:
                    st.warning("🟡 Data Estimasi")

                st.markdown(f"**{madinah_price.hotel_name}**")
                st.markdown(f"{'⭐' * madinah_price.hotel_stars}")

                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Per Malam", format_currency(madinah_price.price_per_night_idr))
                with metric_col2:
                    st.metric("Jarak", f"{madinah_price.distance_to_haram_km:.1f} km")

                st.caption(f"🚶 {madinah_price.walking_time_minutes} menit ke Masjid Nabawi")

        # Transport section
        st.markdown("---")
        st.markdown("### 🚄 Transportasi Makkah - Madinah")

        transport = service.get_transport_price("Makkah", "Madinah", "train")

        transport_cols = st.columns(3)
        with transport_cols[0]:
            with st.container(border=True):
                st.markdown("**🚄 Haramain Train**")
                st.markdown(f"**{format_currency(transport.get('price_idr', 420000))}**")
                st.caption(f"~{transport.get('duration_hours', 2.5)} jam")

        with transport_cols[1]:
            bus = service.get_transport_price("Makkah", "Madinah", "bus")
            with st.container(border=True):
                st.markdown("**🚌 SAPTCO Bus**")
                st.markdown(f"**{format_currency(bus.get('price_idr', 210000))}**")
                st.caption(f"~{bus.get('duration_hours', 5)} jam")

        with transport_cols[2]:
            car = service.get_transport_price("Makkah", "Madinah", "private_car")
            with st.container(border=True):
                st.markdown("**🚗 Private Car**")
                st.markdown(f"**{format_currency(car.get('price_idr', 840000))}**")
                st.caption(f"~{car.get('duration_hours', 4.5)} jam")

        # Show all available hotels
        st.markdown("---")
        with st.expander("📋 Lihat Semua Hotel Tersedia"):
            city_choice = st.radio(
                "Pilih Kota",
                ["Makkah", "Madinah"],
                horizontal=True,
                key="live_hotel_city"
            )

            hotels = service.get_hotels_by_city(city_choice, check_in_str, check_out_str, max_results=10)

            if hotels:
                for hotel in hotels:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(f"**{hotel['hotel_name']}**")
                            st.caption(f"{'⭐' * hotel['stars']} | {hotel['rating']}")
                        with col2:
                            st.markdown(f"**{format_currency(hotel['price_per_night_idr'])}**/malam")
                        with col3:
                            st.caption(f"📍 {hotel['distance_to_haram_km']:.1f} km")
                            st.caption(f"🚶 {hotel['walking_time_minutes']} min")
            else:
                st.info("Tidak ada data hotel tersedia")

    except ImportError:
        st.info("🔧 Modul data live belum tersedia. Gunakan estimasi statis.")
    except Exception as e:
        st.warning(f"⚠️ Gagal memuat data live: {str(e)}")
        st.info("Menggunakan estimasi harga statis")


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_simulator_page():
    """Main cost simulator page renderer."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("simulator")
    except Exception:
        pass

    # Initialize state
    init_simulator_state()

    # Inject shared + page CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SIMULATOR_CSS)

    # Check for group link in URL
    group = check_group_from_url()

    # Handle post-auth callbacks for group actions
    handle_group_auth_callback()

    # If group found but user not logged in, show join prompt
    if group:
        try:
            from services.user.user_service import is_logged_in
            if not is_logged_in():
                render_group_join_prompt(group)
                return
        except ImportError:
            pass

    # Header
    st.markdown("# 💰 Simulasi Biaya Umrah")
    st.caption("Hitung estimasi biaya umrah sesuai preferensi Anda")

    # Show group header if viewing a group
    if st.session_state.is_group_view and st.session_state.sim_group:
        render_group_header(st.session_state.sim_group)
    
    # Quick info
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💚 Mulai Dari", "Rp 15 Juta")
        with col2:
            st.metric("⭐ Paket Populer", "Rp 25 Juta")
        with col3:
            st.metric("👑 VIP", "Rp 55 Juta")
        with col4:
            st.metric("📊 Akurasi", "95%+")
    
    st.divider()

    # Quick Start - Budget Template Presets
    st.markdown("### 🚀 Quick Start — Pilih Template Budget")
    st.caption("Gunakan sebagai referensi untuk mengisi form di bawah")

    tpl_cols = st.columns(4)
    for idx, (key, tpl) in enumerate(BUDGET_TEMPLATES.items()):
        with tpl_cols[idx]:
            icon = tpl["label"].split(" ")[0]
            name = " ".join(tpl["label"].split(" ")[1:])
            price_str = f"Rp {tpl['total_estimate_idr']:,.0f}".replace(",", ".")
            st.markdown(f"""
<div class="budget-template-card">
    <div class="template-icon"><span aria-hidden="true">{icon}</span></div>
    <div class="template-name">{name}</div>
    <div class="template-desc">{tpl['description']}</div>
    <div class="template-price">~{price_str}</div>
    <div class="template-desc">{tpl['duration_days']} hari · Hotel {'⭐' * tpl['hotel_stars']}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # Two column layout
    col_input, col_result = st.columns([1, 1])

    with col_input:
        params = render_input_section()
    
    # Calculate
    cost = calculate_cost(
        departure_city=params["departure_city"],
        departure_date=params["departure_date"],
        duration=params["duration"],
        nights_makkah=params["nights_makkah"],
        nights_madinah=params["nights_madinah"],
        hotel_star_makkah=params["hotel_star_makkah"],
        hotel_star_madinah=params["hotel_star_madinah"],
        flight_class=params["flight_class"],
        meal_type=params["meal_type"],
        num_travelers=params["num_travelers"],
        include_mutawif=params["include_mutawif"],
        include_insurance=params["include_insurance"],
    )
    
    # Award XP for running simulation (first time per session)
    if not st.session_state.get("simulator_xp_simulate", False):
        add_xp_safe(30, "Simulasi Biaya Umrah")
        st.session_state.simulator_xp_simulate = True

    with col_result:
        # Main result
        with st.container(border=True):
            st.markdown("## 🎯 Estimasi Total")
            st.markdown(f"# {format_currency(cost.total)}")
            st.caption("per orang")

            if params["num_travelers"] > 1:
                group_total = cost.total * params["num_travelers"]
                st.info(f"👥 Total {params['num_travelers']} orang: **{format_currency(group_total)}**")

            # Live kurs info
            if HAS_KURS_SERVICE:
                rates = get_current_rates()
                sar_equiv = cost.total / rates["SAR_IDR"]
                source_label = "Live" if rates.get("source") == "live" else "Estimasi"
                st.caption(f"≈ SAR {sar_equiv:,.0f} (kurs {source_label}: 1 SAR = Rp {rates['SAR_IDR']:,.0f})")
                if st.button("🏦 Kalkulator Kurs", key="sim_to_kurs", use_container_width=True):
                    st.session_state.current_page = "kurs_calculator"
                    st.rerun()

            # Smart Nudge untuk Umrah Bareng
            if cost.total > 25_000_000:
                potential_savings = int(cost.total * 0.15)

                # Track nudge display
                try:
                    from services.analytics.tracker import track_smart_nudge_show
                    track_smart_nudge_show(potential_savings)
                except Exception:
                    pass

                st.success(f"""
💡 **Hemat hingga {format_currency(potential_savings)}!**

Dengan **Umrah Bareng**, kamu bisa:
- ✅ Dapat group pricing untuk hotel & transport
- ✅ Match dengan jamaah yang punya jadwal serupa
- ✅ Tidak perlu repot cari 10-15 orang sendiri
                """)

                if st.button("🤝 Coba Umrah Bareng", key="nudge_umrah_bareng", use_container_width=True):
                    # Track nudge click
                    try:
                        from services.analytics.tracker import track_smart_nudge_click
                        track_smart_nudge_click()
                    except Exception:
                        pass
                    st.session_state.current_page = "umrah_bareng"
                    st.rerun()

        # Quick breakdown
        render_cost_breakdown(cost, params["num_travelers"])

        # Season impact analysis (from SeasonCalendar service)
        if HAS_SEASON_CALENDAR:
            render_season_impact(cost, params)

    st.divider()

    # Additional sections with Scenario Planning
    tabs = st.tabs([
        "🎯 Scenario Planning",
        "📊 Grafik",
        "🔄 Perbandingan",
        "💡 Tips Hemat",
        "📈 Rencana Tabungan",
        "🏨 Hotel Live",
        "🤖 Analisis AI",
    ])

    with tabs[0]:
        # Scenario Planning Tab
        scenario_subtabs = st.tabs([
            "📊 Skenario",
            "🎲 Monte Carlo",
            "🌪️ Sensitivitas",
            "⚠️ Risiko",
            "👥 Grup"
        ])

        with scenario_subtabs[0]:
            render_scenario_planning(cost, params)

        with scenario_subtabs[1]:
            render_monte_carlo_analysis(cost)

        with scenario_subtabs[2]:
            render_sensitivity_analysis(params, cost)

        with scenario_subtabs[3]:
            render_risk_factors(cost)

        with scenario_subtabs[4]:
            render_group_discount_analysis(cost, params["num_travelers"])

    with tabs[1]:
        render_cost_chart(cost)

    with tabs[2]:
        render_comparison()

    with tabs[3]:
        render_savings_tips(cost)

    with tabs[4]:
        render_budget_planner(cost, params["num_travelers"])

    with tabs[5]:
        render_live_hotel_prices(params)

    with tabs[6]:
        render_ai_analysis(cost, params)
    
    # Save/export
    render_save_simulation(params, cost)

    # PDF / HTML download report
    st.markdown("---")
    report_html = _generate_simulator_pdf_html(params, cost)
    st.download_button(
        label="Download Laporan (HTML)",
        data=report_html,
        file_name="laporan_simulasi_umrah.html",
        mime="text/html",
        use_container_width=True,
        key="btn_download_report",
    )
    st.caption("Buka file HTML di browser untuk mencetak sebagai PDF.")

    # Saved scenarios (save & compare)
    st.divider()
    render_saved_scenarios(params, cost)

    # Group Planning Section
    if st.session_state.is_group_view and st.session_state.sim_group:
        # Show share section for existing group
        st.divider()
        render_group_share_section(st.session_state.sim_group)
    else:
        # Show create group form for new groups
        render_create_group_form(params, cost)

    # Saved simulations (legacy)
    render_saved_simulations()

    # Footer
    st.divider()
    st.caption("💡 Harga bersifat estimasi berdasarkan data terkini dan dapat berubah sewaktu-waktu.")


# Export
__all__ = ["render_simulator_page"]
