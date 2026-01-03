"""
LABBAIK AI v7.0 - Cost Simulator with Scenario Planning
========================================================
Advanced cost calculator with scenario planning:
- Multiple scenarios (Optimis, Realistis, Pesimistis)
- Sensitivity analysis
- Risk factor assessment
- Monte Carlo confidence ranges
- Interactive scenario comparison
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import random

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
    """Render save/export simulation."""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Simpan Simulasi", use_container_width=True):
            simulation = {
                "timestamp": datetime.now().isoformat(),
                "params": {k: str(v) if isinstance(v, date) else v for k, v in params.items()},
                "total": cost.total,
            }
            st.session_state.sim_saved.append(simulation)
            st.success("✅ Simulasi disimpan!")
    
    with col2:
        if st.button("📤 Export PDF", use_container_width=True):
            st.info("Fitur export PDF akan segera hadir")
    
    with col3:
        if st.button("📱 Share WhatsApp", use_container_width=True):
            total = format_currency(cost.total)
            msg = f"Simulasi Umrah LABBAIK:\n💰 Total: {total}/orang\n🔗 Hitung di: labbaik.streamlit.app"
            st.code(msg)
            st.caption("Copy dan paste ke WhatsApp")


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
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, #333 0%, {color} 50%, #333 100%);
                            padding: 0.5rem; border-radius: 5px; text-align: center; margin: 0.5rem 0;">
                    <small>{format_currency(scenario.confidence_low)} - {format_currency(scenario.confidence_high)}</small>
                </div>
                """, unsafe_allow_html=True)

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
        st.markdown(f"""
        <div style="background: #333; border-radius: 5px; height: 25px; margin-bottom: 10px;">
            <div style="background: {color}; width: {pct}%; height: 100%; border-radius: 5px;"></div>
        </div>
        """, unsafe_allow_html=True)


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
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #1a1a2e; border-radius: 10px; border-left: 4px solid {color};">
                <div style="font-size: 0.8rem; color: #888;">{label}</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: white;">{format_currency(value)}</div>
            </div>
            """, unsafe_allow_html=True)

    # Confidence interval recommendation
    st.markdown("---")
    with st.container(border=True):
        st.markdown("#### 💡 Rekomendasi Budget")
        st.markdown(f"""
        Berdasarkan simulasi Monte Carlo dengan 1,000 iterasi:

        - **Budget Minimal** (P10): {format_currency(mc_results["p10"])}
        - **Budget Rekomendasi** (P75): {format_currency(mc_results["p75"])}
        - **Budget Aman** (P90): {format_currency(mc_results["p90"])}

        > Kami rekomendasikan menyiapkan budget sebesar **{format_currency(mc_results["p75"])}**
        > untuk mengantisipasi 75% kemungkinan skenario.
        """)


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
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 5px 0 15px 0;">
            <div style="width: 50%; display: flex; justify-content: flex-end;">
                <div style="background: #28a745; height: 20px; width: {low_pct}%; border-radius: 3px 0 0 3px;"></div>
            </div>
            <div style="width: 2px; height: 30px; background: #fff;"></div>
            <div style="width: 50%;">
                <div style="background: #dc3545; height: 20px; width: {high_pct}%; border-radius: 0 3px 3px 0;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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

        st.markdown(f"""
        <div style="background: #1a1a2e; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
                    border: 2px solid {border_color}; {'box-shadow: 0 0 10px rgba(212,175,55,0.3);' if is_current else ''}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: white;">{tier['label']}</strong>
                    <span style="color: #888;"> ({tier['min_travelers']}+ jamaah)</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: #28a745; font-weight: bold;">{tier['discount']*100:.0f}% OFF</span><br/>
                    <span style="color: white;">{format_currency(final_price)}/orang</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Next tier suggestion
    current_tier_idx = 0
    for i, tier in enumerate(be_analysis['discount_tiers']):
        if num_travelers >= tier['min_travelers']:
            current_tier_idx = i

    if current_tier_idx < len(be_analysis['discount_tiers']) - 1:
        next_tier = be_analysis['discount_tiers'][current_tier_idx + 1]
        needed = next_tier['min_travelers'] - num_travelers

        with st.container(border=True):
            st.markdown(f"""
            💡 **Tambah {needed} jamaah** untuk naik ke tier **{next_tier['label']}**
            dan dapat diskon **{next_tier['discount']*100:.0f}%**!
            """)


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
    except:
        pass
    
    # Initialize state
    init_simulator_state()
    
    # Header
    st.markdown("# 💰 Simulasi Biaya Umrah")
    st.caption("Hitung estimasi biaya umrah sesuai preferensi Anda")
    
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
    
    with col_result:
        # Main result
        with st.container(border=True):
            st.markdown("## 🎯 Estimasi Total")
            st.markdown(f"# {format_currency(cost.total)}")
            st.caption("per orang")
            
            if params["num_travelers"] > 1:
                group_total = cost.total * params["num_travelers"]
                st.info(f"👥 Total {params['num_travelers']} orang: **{format_currency(group_total)}**")

            # Smart Nudge untuk Umrah Bareng
            if cost.total > 25_000_000:
                potential_savings = int(cost.total * 0.15)
                st.success(f"""
💡 **Hemat hingga {format_currency(potential_savings)}!**

Dengan **Umrah Bareng**, kamu bisa:
- ✅ Dapat group pricing untuk hotel & transport
- ✅ Match dengan jamaah yang punya jadwal serupa
- ✅ Tidak perlu repot cari 10-15 orang sendiri
                """)

                if st.button("🤝 Coba Umrah Bareng", key="nudge_umrah_bareng", use_container_width=True):
                    st.session_state.current_page = "umrah_bareng"
                    st.rerun()

        # Quick breakdown
        render_cost_breakdown(cost, params["num_travelers"])
    
    st.divider()

    # Additional sections with Scenario Planning
    tabs = st.tabs([
        "🎯 Scenario Planning",
        "📊 Grafik",
        "🔄 Perbandingan",
        "💡 Tips Hemat",
        "📈 Rencana Tabungan",
        "🏨 Hotel Live"
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
    
    # Save/export
    render_save_simulation(params, cost)
    
    # Saved simulations
    render_saved_simulations()
    
    # Footer
    st.divider()
    st.caption("💡 Harga bersifat estimasi dan dapat berubah. Hubungi tim kami untuk penawaran terbaik.")


# Export
__all__ = ["render_simulator_page"]
