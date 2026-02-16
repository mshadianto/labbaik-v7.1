"""
LABBAIK AI v6.0 - Smart Package AI Comparison
==============================================
Intelligent Umrah package comparison:
- Multi-factor scoring algorithm
- Personalized recommendations
- Value analysis
- Side-by-side comparison

Inspired by Nusuk and travel aggregator platforms.
"""

import streamlit as st
from datetime import date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class PackageTier(str, Enum):
    BUDGET = "budget"
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"


class HotelDistance(str, Enum):
    VERY_CLOSE = "very_close"    # < 100m
    CLOSE = "close"              # 100-300m
    MODERATE = "moderate"        # 300-500m
    FAR = "far"                  # > 500m


@dataclass
class PackageDetails:
    """Detailed package information."""
    id: str
    name: str
    provider: str
    tier: PackageTier
    price: int
    duration_days: int
    
    # Hotels
    hotel_makkah: str
    hotel_makkah_stars: int
    hotel_makkah_distance: HotelDistance
    hotel_makkah_distance_m: int
    nights_makkah: int
    
    hotel_madinah: str
    hotel_madinah_stars: int
    hotel_madinah_distance: HotelDistance
    hotel_madinah_distance_m: int
    nights_madinah: int
    
    # Flight
    airline: str
    flight_class: str
    is_direct: bool
    
    # Inclusions
    includes_visa: bool = True
    includes_meals: str = "breakfast"  # none, breakfast, half_board, full_board
    includes_transport: bool = True
    includes_mutawif: bool = True
    includes_ziarah: bool = True
    includes_insurance: bool = True
    
    # Extras
    extras: List[str] = field(default_factory=list)
    
    # Ratings (1-5)
    rating_overall: float = 0.0
    rating_hotel: float = 0.0
    rating_service: float = 0.0
    review_count: int = 0
    
    # Scoring (calculated)
    value_score: float = 0.0
    location_score: float = 0.0
    comfort_score: float = 0.0
    total_score: float = 0.0


@dataclass
class UserPreferences:
    """User preferences for package matching."""
    budget_min: int = 20_000_000
    budget_max: int = 50_000_000
    priority: str = "balanced"  # budget, location, comfort, balanced
    hotel_stars_min: int = 3
    prefer_direct_flight: bool = False
    need_wheelchair: bool = False
    traveling_with_elderly: bool = False
    traveling_with_kids: bool = False
    prefer_meals_included: bool = True


# =============================================================================
# SAMPLE PACKAGES DATA
# =============================================================================

def get_sample_packages() -> List[PackageDetails]:
    """Get sample package data."""
    
    packages = [
        PackageDetails(
            id="pkg_001",
            name="Umrah Hemat Barokah",
            provider="PT. Barokah Travel",
            tier=PackageTier.BUDGET,
            price=22_500_000,
            duration_days=9,
            hotel_makkah="Grand Zamzam Hotel",
            hotel_makkah_stars=3,
            hotel_makkah_distance=HotelDistance.MODERATE,
            hotel_makkah_distance_m=450,
            nights_makkah=4,
            hotel_madinah="Dallah Taibah Hotel",
            hotel_madinah_stars=3,
            hotel_madinah_distance=HotelDistance.MODERATE,
            hotel_madinah_distance_m=400,
            nights_madinah=3,
            airline="Saudi Airlines",
            flight_class="economy",
            is_direct=False,
            includes_meals="breakfast",
            rating_overall=4.2,
            rating_hotel=3.8,
            rating_service=4.5,
            review_count=156,
            extras=["Air Zamzam 5L", "Tas Umrah"]
        ),
        PackageDetails(
            id="pkg_002",
            name="Umrah Plus Nyaman",
            provider="PT. Alhijaz Indowisata",
            tier=PackageTier.STANDARD,
            price=32_000_000,
            duration_days=12,
            hotel_makkah="Pullman Zamzam Makkah",
            hotel_makkah_stars=5,
            hotel_makkah_distance=HotelDistance.VERY_CLOSE,
            hotel_makkah_distance_m=50,
            nights_makkah=5,
            hotel_madinah="Pullman Zamzam Madinah",
            hotel_madinah_stars=4,
            hotel_madinah_distance=HotelDistance.CLOSE,
            hotel_madinah_distance_m=200,
            nights_madinah=4,
            airline="Garuda Indonesia",
            flight_class="economy",
            is_direct=True,
            includes_meals="half_board",
            rating_overall=4.6,
            rating_hotel=4.7,
            rating_service=4.5,
            review_count=324,
            extras=["Air Zamzam 10L", "Tas Koper", "City Tour Makkah"]
        ),
        PackageDetails(
            id="pkg_003",
            name="Umrah Premium Experience",
            provider="PT. Arminareka Perdana",
            tier=PackageTier.PREMIUM,
            price=45_000_000,
            duration_days=14,
            hotel_makkah="Swissotel Al Maqam",
            hotel_makkah_stars=5,
            hotel_makkah_distance=HotelDistance.VERY_CLOSE,
            hotel_makkah_distance_m=100,
            nights_makkah=6,
            hotel_madinah="Dar Al Taqwa Hotel",
            hotel_madinah_stars=5,
            hotel_madinah_distance=HotelDistance.VERY_CLOSE,
            hotel_madinah_distance_m=100,
            nights_madinah=5,
            airline="Garuda Indonesia",
            flight_class="economy",
            is_direct=True,
            includes_meals="full_board",
            rating_overall=4.8,
            rating_hotel=4.9,
            rating_service=4.7,
            review_count=89,
            extras=["Air Zamzam 10L", "Tas Koper Premium", "City Tour Full", "Laundry 5kg", "Portable WiFi"]
        ),
        PackageDetails(
            id="pkg_004",
            name="Umrah VIP Executive",
            provider="PT. Patuna Tour & Travel",
            tier=PackageTier.VIP,
            price=75_000_000,
            duration_days=14,
            hotel_makkah="Fairmont Clock Tower",
            hotel_makkah_stars=5,
            hotel_makkah_distance=HotelDistance.VERY_CLOSE,
            hotel_makkah_distance_m=30,
            nights_makkah=6,
            hotel_madinah="The Oberoi Madinah",
            hotel_madinah_stars=5,
            hotel_madinah_distance=HotelDistance.VERY_CLOSE,
            hotel_madinah_distance_m=50,
            nights_madinah=5,
            airline="Garuda Indonesia",
            flight_class="business",
            is_direct=True,
            includes_meals="full_board",
            rating_overall=4.9,
            rating_hotel=5.0,
            rating_service=4.9,
            review_count=45,
            extras=["Air Zamzam 20L", "Koper Premium", "Private Tour", "Butler Service", "Airport Lounge", "Spa Treatment"]
        ),
        PackageDetails(
            id="pkg_005",
            name="Umrah Ramadhan Special",
            provider="PT. Ebad Alrahman",
            tier=PackageTier.STANDARD,
            price=38_000_000,
            duration_days=10,
            hotel_makkah="Hilton Suites Makkah",
            hotel_makkah_stars=4,
            hotel_makkah_distance=HotelDistance.CLOSE,
            hotel_makkah_distance_m=150,
            nights_makkah=5,
            hotel_madinah="Millennium Al Aqeeq",
            hotel_madinah_stars=4,
            hotel_madinah_distance=HotelDistance.CLOSE,
            hotel_madinah_distance_m=180,
            nights_madinah=3,
            airline="Saudi Airlines",
            flight_class="economy",
            is_direct=True,
            includes_meals="full_board",
            rating_overall=4.4,
            rating_hotel=4.3,
            rating_service=4.5,
            review_count=201,
            extras=["Air Zamzam 10L", "Sahur & Iftar Special", "Itikaf Package"]
        ),
    ]
    
    # Calculate scores for each package
    for pkg in packages:
        calculate_scores(pkg)
    
    return packages


# =============================================================================
# SCORING ALGORITHM
# =============================================================================

def calculate_scores(package: PackageDetails) -> None:
    """Calculate various scores for a package."""
    
    # Location Score (0-100)
    # Based on hotel distance to Masjid
    distance_scores = {
        HotelDistance.VERY_CLOSE: 100,
        HotelDistance.CLOSE: 80,
        HotelDistance.MODERATE: 60,
        HotelDistance.FAR: 40,
    }
    
    makkah_loc = distance_scores.get(package.hotel_makkah_distance, 50)
    madinah_loc = distance_scores.get(package.hotel_madinah_distance, 50)
    package.location_score = (makkah_loc * 0.6 + madinah_loc * 0.4)  # Makkah weighted more
    
    # Comfort Score (0-100)
    # Based on hotel stars, meals, flight class
    hotel_score = ((package.hotel_makkah_stars + package.hotel_madinah_stars) / 2) * 20
    
    meal_scores = {"none": 0, "breakfast": 30, "half_board": 60, "full_board": 100}
    meal_score = meal_scores.get(package.includes_meals, 0) * 0.2
    
    flight_score = 100 if package.flight_class == "business" else 50
    flight_score += 20 if package.is_direct else 0
    flight_score = min(flight_score, 100) * 0.2
    
    package.comfort_score = min(100, hotel_score + meal_score + flight_score)
    
    # Value Score (0-100)
    # Price per day per quality point
    price_per_day = package.price / package.duration_days
    quality_factor = (package.location_score + package.comfort_score) / 2
    
    # Normalize: lower price per quality = higher value
    # Baseline: 3M/day with 50 quality = 60k per quality point
    baseline_price_per_quality = 60_000
    actual_price_per_quality = price_per_day / max(quality_factor, 1)
    
    package.value_score = min(100, max(0, 100 - (actual_price_per_quality - baseline_price_per_quality) / 1000))
    
    # Total Score (weighted average) - capped at 100
    package.total_score = min(100, (
        package.location_score * 0.35 +
        package.comfort_score * 0.35 +
        package.value_score * 0.20 +
        package.rating_overall * 20 * 0.10  # Convert 0-5 rating to 0-100
    ))


def match_packages(
    packages: List[PackageDetails],
    preferences: UserPreferences
) -> List[Tuple[PackageDetails, float]]:
    """Match packages to user preferences and return sorted by match score."""
    
    results = []
    
    for pkg in packages:
        # Budget filter
        if pkg.price < preferences.budget_min or pkg.price > preferences.budget_max:
            continue
        
        # Hotel stars filter
        if pkg.hotel_makkah_stars < preferences.hotel_stars_min:
            continue
        
        # Calculate match score based on priority
        if preferences.priority == "budget":
            match_score = pkg.value_score * 0.5 + pkg.total_score * 0.5
        elif preferences.priority == "location":
            match_score = pkg.location_score * 0.5 + pkg.total_score * 0.5
        elif preferences.priority == "comfort":
            match_score = pkg.comfort_score * 0.5 + pkg.total_score * 0.5
        else:  # balanced
            match_score = pkg.total_score
        
        # Bonus for direct flight preference
        if preferences.prefer_direct_flight and pkg.is_direct:
            match_score += 5
        
        # Bonus for meals preference
        if preferences.prefer_meals_included and pkg.includes_meals in ["half_board", "full_board"]:
            match_score += 5
        
        # Cap match_score at 100
        match_score = min(100, match_score)
        
        results.append((pkg, match_score))
    
    # Sort by match score descending
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results


# =============================================================================
# RENDER FUNCTIONS
# =============================================================================

def render_package_card(package: PackageDetails, match_score: float = None, show_details: bool = True):
    """Render a package card using Streamlit components."""
    
    tier_labels = {
        PackageTier.BUDGET: "💚 Budget",
        PackageTier.STANDARD: "💙 Standard",
        PackageTier.PREMIUM: "💜 Premium",
        PackageTier.VIP: "👑 VIP",
    }
    
    tier_label = tier_labels.get(package.tier, "Standard")
    
    # Use Streamlit container
    with st.container():
        # Header row
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown(f"**{tier_label}**")
        
        with col2:
            st.markdown(f"### {package.name}")
            st.caption(package.provider)
        
        with col3:
            if match_score:
                st.metric("Match", f"{min(100, match_score):.0f}%")
            st.markdown(f"**Rp {package.price:,.0f}**")
            st.caption(f"{package.duration_days} hari")
        
        # Hotels row
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"🕋 **MAKKAH** ({package.nights_makkah} malam)")
            st.markdown(f"{package.hotel_makkah}")
            st.caption(f"{'⭐' * package.hotel_makkah_stars} • {package.hotel_makkah_distance_m}m dari Masjid")
        
        with col2:
            st.markdown(f"🕌 **MADINAH** ({package.nights_madinah} malam)")
            st.markdown(f"{package.hotel_madinah}")
            st.caption(f"{'⭐' * package.hotel_madinah_stars} • {package.hotel_madinah_distance_m}m dari Masjid")
        
        # Flight & amenities
        flight_type = "✈️ Direct" if package.is_direct else "✈️ Transit"
        st.markdown(f"{flight_type} {package.airline} | 🍽️ {package.includes_meals} | ⭐ {package.rating_overall} ({package.review_count} review)")
        
        st.divider()


def render_score_breakdown(package: PackageDetails):
    """Render score breakdown for a package."""
    
    st.markdown("#### 📊 Breakdown Skor")
    
    scores = [
        ("📍 Lokasi", package.location_score, "Jarak hotel ke Masjid"),
        ("🛋️ Kenyamanan", package.comfort_score, "Hotel, makanan, penerbangan"),
        ("💰 Nilai", package.value_score, "Harga vs kualitas"),
        ("⭐ Rating", package.rating_overall * 20, "Rating pengguna"),
    ]
    
    for label, score, desc in scores:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{label}**")
            st.caption(desc)
            # Clamp progress between 0 and 1
            progress_value = max(0.0, min(1.0, score / 100))
            st.progress(progress_value)
        with col2:
            st.markdown(f"**{score:.0f}**")


def render_comparison_table(packages: List[PackageDetails]):
    """Render side-by-side comparison table."""
    
    if len(packages) < 2:
        st.warning("Pilih minimal 2 paket untuk dibandingkan")
        return
    
    st.markdown("### 📊 Perbandingan Paket")
    
    # Header
    cols = st.columns(len(packages) + 1)
    cols[0].markdown("**Kriteria**")
    for i, pkg in enumerate(packages):
        cols[i + 1].markdown(f"**{pkg.name[:20]}...**")
    
    # Rows
    comparisons = [
        ("💰 Harga", [f"Rp {p.price:,.0f}" for p in packages]),
        ("📅 Durasi", [f"{p.duration_days} hari" for p in packages]),
        ("🕋 Hotel Makkah", [f"{'⭐' * p.hotel_makkah_stars} ({p.hotel_makkah_distance_m}m)" for p in packages]),
        ("🕌 Hotel Madinah", [f"{'⭐' * p.hotel_madinah_stars} ({p.hotel_madinah_distance_m}m)" for p in packages]),
        ("✈️ Penerbangan", [f"{p.airline} ({'Direct' if p.is_direct else 'Transit'})" for p in packages]),
        ("🍽️ Makanan", [p.includes_meals for p in packages]),
        ("⭐ Rating", [f"{p.rating_overall}/5 ({p.review_count})" for p in packages]),
        ("📍 Skor Lokasi", [f"{p.location_score:.0f}/100" for p in packages]),
        ("🛋️ Skor Kenyamanan", [f"{p.comfort_score:.0f}/100" for p in packages]),
        ("💎 Skor Total", [f"{p.total_score:.0f}/100" for p in packages]),
    ]
    
    for label, values in comparisons:
        cols = st.columns(len(packages) + 1)
        cols[0].markdown(label)
        for i, val in enumerate(values):
            cols[i + 1].markdown(val)


def render_preferences_form() -> UserPreferences:
    """Render preferences form and return preferences."""
    
    st.markdown("### 🎯 Preferensi Anda")
    
    col1, col2 = st.columns(2)
    
    with col1:
        budget_range = st.slider(
            "💰 Budget (Juta Rupiah)",
            min_value=15,
            max_value=100,
            value=(20, 50),
            step=5
        )
        
        priority = st.selectbox(
            "🎯 Prioritas Utama",
            ["balanced", "budget", "location", "comfort"],
            format_func=lambda x: {
                "balanced": "⚖️ Seimbang",
                "budget": "💰 Harga Terbaik",
                "location": "📍 Lokasi Dekat",
                "comfort": "🛋️ Kenyamanan"
            }.get(x, x)
        )
    
    with col2:
        hotel_stars = st.selectbox(
            "⭐ Minimal Bintang Hotel",
            [3, 4, 5],
            index=0
        )
        
        direct_flight = st.checkbox("✈️ Prefer penerbangan langsung")
        meals_included = st.checkbox("🍽️ Prefer makan termasuk", value=True)
    
    return UserPreferences(
        budget_min=budget_range[0] * 1_000_000,
        budget_max=budget_range[1] * 1_000_000,
        priority=priority,
        hotel_stars_min=hotel_stars,
        prefer_direct_flight=direct_flight,
        prefer_meals_included=meals_included
    )


def render_smart_comparison_page():
    """Full smart comparison page."""

    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    if not st.session_state.get("smart_comparison_xp_awarded"):
        add_xp_safe(10, "Membandingkan paket umrah")
        st.session_state.smart_comparison_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1>⚖️ Smart Comparison</h1>
            <div class="subtitle">Bandingkan paket umrah secara cerdas dengan AI</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Get preferences
    preferences = render_preferences_form()
    
    st.divider()
    
    # Get and match packages
    packages = get_sample_packages()
    matched = match_packages(packages, preferences)
    
    if not matched:
        st.warning("😕 Tidak ada paket yang cocok dengan kriteria Anda. Coba sesuaikan preferensi.")
        return
    
    # Show results
    st.markdown(f"### 🎯 {len(matched)} Paket Ditemukan")
    
    # Tabs: List vs Compare
    tab1, tab2 = st.tabs(["📋 Daftar Paket", "📊 Bandingkan"])
    
    with tab1:
        for pkg, score in matched:
            render_package_card(pkg, score)
            
            with st.expander("📊 Lihat Detail Skor"):
                render_score_breakdown(pkg)
    
    with tab2:
        st.markdown("Pilih paket untuk dibandingkan:")
        
        selected_ids = []
        cols = st.columns(min(len(matched), 4))
        
        for i, (pkg, score) in enumerate(matched[:4]):
            with cols[i]:
                if st.checkbox(f"{pkg.name[:15]}...", key=f"cmp_{pkg.id}"):
                    selected_ids.append(pkg.id)
        
        if len(selected_ids) >= 2:
            selected_packages = [pkg for pkg, _ in matched if pkg.id in selected_ids]
            render_comparison_table(selected_packages)
        else:
            st.info("Pilih minimal 2 paket untuk membandingkan")
    
    # AI Recommendation
    st.divider()
    if matched:
        best_pkg, best_score = matched[0]
        st.markdown("### 🤖 Rekomendasi AI")
        st.success(f"""
        **{best_pkg.name}** adalah pilihan terbaik untuk Anda!

        ✅ Skor kecocokan: **{best_score:.0f}%**
        ✅ {best_pkg.hotel_makkah} hanya {best_pkg.hotel_makkah_distance_m}m dari Masjidil Haram
        ✅ Rating: {best_pkg.rating_overall}/5 dari {best_pkg.review_count} review
        """)

    st.markdown("---")
    if st.button("🤖 Rekomendasi AI", key="comparison_ai_tips"):
        with st.spinner("Menganalisis paket..."):
            tips = ai_complete(
                "Berikan 3 tips singkat untuk memilih paket umrah terbaik berdasarkan budget, "
                "kenyamanan, dan kualitas pelayanan. Bahasa Indonesia.",
                system_prompt="Kamu adalah konsultan perjalanan umrah berpengalaman.",
                max_tokens=300,
            )
            if tips:
                st.markdown(f'''
                    <div class="ai-card" role="status" aria-live="polite">
                        <h4>🤖 Rekomendasi AI</h4>
                        <p>{tips}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "render_smart_comparison_page",
    "render_package_card",
    "render_comparison_table",
    "get_sample_packages",
    "match_packages",
    "PackageDetails",
    "UserPreferences",
]
