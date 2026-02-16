"""
LABBAIK AI v6.0 - Premium Booking Flow
======================================
Complete booking experience with real-time pricing,
package comparison, and interactive UI.
"""

import streamlit as st
from datetime import date, timedelta, datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random
import json

from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS
from services.ai.helpers import ai_complete, add_xp_safe

# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

BOOKING_CSS = """
/* Booking page hero */
.booking-hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a3a 50%, #1b2a4a 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid #d4af37;
    position: relative;
    overflow: hidden;
}

.booking-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.06) 0%, transparent 70%);
    animation: booking-pulse 4s ease-in-out infinite;
    pointer-events: none;
}

@keyframes booking-pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}

.booking-hero h1 {
    color: #d4af37;
    margin: 0;
    font-size: 2.2rem;
    position: relative;
    z-index: 1;
}

.booking-hero .subtitle {
    color: #b0b0b0;
    font-size: 1rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

.booking-hero .bismillah {
    font-family: 'Amiri', serif;
    color: #d4af37;
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

/* Step progress indicator cards */
.step-active {
    background: linear-gradient(145deg, #1a2e1a 0%, #1a3a1a 100%);
    border: 1px solid #4ade80;
    border-radius: 10px;
    padding: 0.5rem;
    text-align: center;
}

.step-done {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border: 1px solid #333;
    border-radius: 10px;
    padding: 0.5rem;
    text-align: center;
    opacity: 0.7;
}

.step-pending {
    background: #111;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 0.5rem;
    text-align: center;
    opacity: 0.4;
}
"""

# =============================================================================
# DATA CLASSES & ENUMS
# =============================================================================

class BookingStep(str, Enum):
    PACKAGE = "package"
    SCHEDULE = "schedule"
    TRAVELERS = "travelers"
    ADDONS = "addons"
    REVIEW = "review"
    PAYMENT = "payment"
    CONFIRMATION = "confirmation"


class PackageType(str, Enum):
    BACKPACKER = "backpacker"
    REGULER = "reguler"
    PLUS = "plus"
    VIP = "vip"
    MANDIRI = "mandiri"


class HotelCategory(str, Enum):
    BUDGET = "budget"       # Bintang 2-3
    STANDARD = "standard"   # Bintang 3
    SUPERIOR = "superior"   # Bintang 4
    PREMIUM = "premium"     # Bintang 5
    DELUXE = "deluxe"      # Bintang 5+


@dataclass
class Package:
    """Package definition."""
    type: PackageType
    name: str
    icon: str
    description: str
    base_price: int
    hotel_makkah: str
    hotel_madinah: str
    distance_haram: str
    meals: str
    transport: str
    mutawif: str
    features: List[str]
    popular: bool = False
    best_value: bool = False


@dataclass
class Traveler:
    """Traveler information."""
    name: str
    passport_number: str
    passport_expiry: date
    birth_date: date
    gender: str
    nationality: str
    phone: str
    email: str
    is_primary: bool = False
    special_needs: str = ""
    room_preference: str = "double"


@dataclass
class AddOn:
    """Add-on service."""
    id: str
    name: str
    icon: str
    description: str
    price: int
    category: str
    popular: bool = False


# =============================================================================
# PACKAGE DEFINITIONS
# =============================================================================

PACKAGES = [
    Package(
        type=PackageType.BACKPACKER,
        name="Backpacker",
        icon="🎒",
        description="Paket ekonomis untuk jamaah mandiri yang ingin pengalaman autentik",
        base_price=18_000_000,
        hotel_makkah="Hotel Bintang 2-3",
        hotel_madinah="Hotel Bintang 2-3",
        distance_haram="800m - 1.5km",
        meals="Tidak termasuk",
        transport="Bus sharing",
        mutawif="Sharing group (1:30)",
        features=[
            "✈️ Tiket pesawat PP",
            "🏨 Hotel 9 malam",
            "📋 Visa umrah",
            "🚌 Transport bandara",
            "📚 Panduan digital",
            "💬 Support 24/7",
        ],
    ),
    Package(
        type=PackageType.REGULER,
        name="Reguler",
        icon="⭐",
        description="Paket standar dengan keseimbangan harga dan kenyamanan",
        base_price=25_000_000,
        hotel_makkah="Hotel Bintang 3-4",
        hotel_madinah="Hotel Bintang 3-4",
        distance_haram="400m - 800m",
        meals="3x sehari (prasmanan)",
        transport="Bus AC group",
        mutawif="Sharing (1:20)",
        features=[
            "✈️ Tiket pesawat PP",
            "🏨 Hotel 9 malam",
            "📋 Visa umrah",
            "🍽️ Makan 3x sehari",
            "🚌 Transport full",
            "👨\u200d🏫 Mutawif berpengalaman",
            "🎁 Perlengkapan umrah",
            "📸 Dokumentasi",
        ],
        popular=True,
    ),
    Package(
        type=PackageType.PLUS,
        name="Plus",
        icon="🌟",
        description="Paket premium dengan fasilitas lebih dan kenyamanan ekstra",
        base_price=35_000_000,
        hotel_makkah="Hotel Bintang 4-5",
        hotel_madinah="Hotel Bintang 4-5",
        distance_haram="200m - 400m",
        meals="3x sehari + snack",
        transport="Bus VIP / Hiace",
        mutawif="Dedicated (1:15)",
        features=[
            "✈️ Tiket pesawat PP (bagasi 30kg)",
            "🏨 Hotel premium 9 malam",
            "📋 Visa umrah + handling VIP",
            "🍽️ Makan premium",
            "🚌 Transport VIP",
            "👨\u200d🏫 Mutawif senior",
            "🎁 Perlengkapan premium",
            "🕌 Ziarah tambahan",
            "📸 Album foto profesional",
        ],
        best_value=True,
    ),
    Package(
        type=PackageType.VIP,
        name="VIP Executive",
        icon="👑",
        description="Pengalaman umrah mewah dengan pelayanan terbaik",
        base_price=55_000_000,
        hotel_makkah="Hotel Bintang 5 (Fairmont/Pullman)",
        hotel_madinah="Hotel Bintang 5 (Oberoi/Crowne)",
        distance_haram="< 100m (view Ka'bah)",
        meals="Fine dining + room service",
        transport="Private car / Limousine",
        mutawif="Personal (1:5)",
        features=[
            "✈️ Business class flight",
            "🏨 Suite room 9 malam",
            "📋 Fast track visa & handling",
            "🍽️ Fine dining experience",
            "🚗 Private transport",
            "👨\u200d🏫 Personal mutawif",
            "🎁 Luxury amenities",
            "🕌 Private ziarah tour",
            "📸 Professional videography",
            "🎖️ Lounge access",
            "💆 Spa & wellness",
        ],
    ),
    Package(
        type=PackageType.MANDIRI,
        name="Mandiri",
        icon="🧭",
        description="Fleksibilitas penuh untuk umrah mandiri berpengalaman",
        base_price=15_000_000,
        hotel_makkah="Pilihan sendiri",
        hotel_madinah="Pilihan sendiri",
        distance_haram="Sesuai pilihan",
        meals="Tidak termasuk",
        transport="Tidak termasuk",
        mutawif="Panduan digital + hotline",
        features=[
            "📋 Visa umrah",
            "📚 Panduan digital lengkap",
            "💬 24/7 hotline support",
            "🗺️ Rekomendasi hotel",
            "📍 GPS guided tour",
            "🎓 Video tutorial ibadah",
        ],
    ),
]


# =============================================================================
# ADD-ONS DEFINITIONS
# =============================================================================

ADDONS = [
    AddOn(
        id="travel_insurance",
        name="Asuransi Perjalanan Premium",
        icon="🛡️",
        description="Perlindungan medis hingga $100,000 + evakuasi",
        price=500_000,
        category="protection",
        popular=True,
    ),
    AddOn(
        id="extra_baggage",
        name="Extra Bagasi 10kg",
        icon="🧳",
        description="Tambahan bagasi untuk oleh-oleh",
        price=350_000,
        category="comfort",
    ),
    AddOn(
        id="airport_lounge",
        name="Airport Lounge Access",
        icon="✨",
        description="Akses lounge premium di bandara",
        price=450_000,
        category="comfort",
    ),
    AddOn(
        id="ziarah_makkah",
        name="Ziarah Plus Makkah",
        icon="🕋",
        description="Jabal Rahmah, Gua Hira, Muzdalifah, Mina",
        price=350_000,
        category="experience",
        popular=True,
    ),
    AddOn(
        id="ziarah_madinah",
        name="Ziarah Plus Madinah",
        icon="🕌",
        description="Uhud, Quba, Qiblatain, Khandaq",
        price=300_000,
        category="experience",
    ),
    AddOn(
        id="simcard",
        name="SIM Card Saudi (10GB)",
        icon="📱",
        description="Internet + telepon lokal",
        price=150_000,
        category="utility",
    ),
    AddOn(
        id="zamzam_5l",
        name="Air Zamzam 5 Liter",
        icon="💧",
        description="Kemasan khusus untuk dibawa pulang",
        price=100_000,
        category="souvenir",
    ),
    AddOn(
        id="prayer_set",
        name="Set Perlengkapan Sholat Premium",
        icon="📿",
        description="Sajadah + tasbih + mukena/sarung",
        price=250_000,
        category="utility",
    ),
    AddOn(
        id="photography",
        name="Foto Profesional",
        icon="📸",
        description="50+ foto edited + album digital",
        price=500_000,
        category="experience",
    ),
    AddOn(
        id="wheelchair",
        name="Layanan Kursi Roda",
        icon="♿",
        description="Kursi roda + pendamping saat thawaf/sa'i",
        price=400_000,
        category="special",
    ),
]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_currency(amount: int) -> str:
    """Format number as Indonesian Rupiah."""
    return f"Rp {amount:,.0f}".replace(",", ".")


def calculate_total_price(data: Dict) -> Dict[str, int]:
    """Calculate total booking price."""
    package = next((p for p in PACKAGES if p.type.value == data.get("package_type")), None)
    if not package:
        return {"base": 0, "addons": 0, "seasonal": 0, "total": 0}

    travelers = data.get("travelers", [])
    traveler_count = max(len(travelers), 1)

    # Base price
    base_price = package.base_price * traveler_count

    # Hotel upgrade
    hotel_upgrade = 0
    hotel_star = data.get("hotel_star", 3)
    if hotel_star == 4:
        hotel_upgrade = 3_000_000 * traveler_count
    elif hotel_star == 5:
        hotel_upgrade = 8_000_000 * traveler_count

    # Add-ons
    selected_addons = data.get("addons", [])
    addons_price = 0
    for addon_id in selected_addons:
        addon = next((a for a in ADDONS if a.id == addon_id), None)
        if addon:
            addons_price += addon.price * traveler_count

    # Seasonal adjustment
    dep_date = data.get("departure_date")
    seasonal = 0
    if dep_date:
        month = dep_date.month
        if month in [3, 4]:  # Ramadan
            seasonal = int(base_price * 0.25)
        elif month in [6, 7, 12]:  # Peak season
            seasonal = int(base_price * 0.15)

    total = base_price + hotel_upgrade + addons_price + seasonal

    return {
        "base": base_price,
        "hotel_upgrade": hotel_upgrade,
        "addons": addons_price,
        "seasonal": seasonal,
        "total": total,
        "per_person": total // traveler_count if traveler_count > 0 else total,
    }


def generate_booking_number() -> str:
    """Generate unique booking number."""
    import random
    import string
    return "LBK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_booking_state():
    """Initialize booking session state."""

    if "booking_step" not in st.session_state:
        st.session_state.booking_step = BookingStep.PACKAGE

    if "booking_data" not in st.session_state:
        st.session_state.booking_data = {
            "package_type": None,
            "departure_city": "Jakarta",
            "departure_date": None,
            "return_date": None,
            "travelers": [],
            "hotel_star": 4,
            "days_makkah": 5,
            "days_madinah": 4,
            "addons": [],
            "notes": "",
            "promo_code": "",
        }

    # Gamification tracking flags
    if "booking_step_xp_awarded" not in st.session_state:
        st.session_state.booking_step_xp_awarded = set()
    if "booking_ai_tips_xp_awarded" not in st.session_state:
        st.session_state.booking_ai_tips_xp_awarded = False


def get_current_step() -> BookingStep:
    """Get current booking step."""
    return st.session_state.get("booking_step", BookingStep.PACKAGE)


def set_step(step: BookingStep):
    """Set current booking step."""
    st.session_state.booking_step = step


def next_step():
    """Move to next step."""
    steps = list(BookingStep)
    current = get_current_step()
    idx = steps.index(current)
    if idx < len(steps) - 1:
        # Award XP for completing a step (first time only)
        step_name = current.value
        awarded = st.session_state.get("booking_step_xp_awarded", set())
        if step_name not in awarded:
            awarded.add(step_name)
            st.session_state.booking_step_xp_awarded = awarded
            add_xp_safe(30, f"Menyelesaikan langkah booking: {step_name}")
        set_step(steps[idx + 1])


def prev_step():
    """Move to previous step."""
    steps = list(BookingStep)
    current = get_current_step()
    idx = steps.index(current)
    if idx > 0:
        set_step(steps[idx - 1])


# =============================================================================
# AI TIPS
# =============================================================================

def render_ai_booking_tips():
    """Render AI-powered booking tips based on current booking data."""

    data = st.session_state.booking_data
    package_type = data.get("package_type")
    if not package_type:
        return

    package = next((p for p in PACKAGES if p.type.value == package_type), None)
    if not package:
        return

    st.markdown("---")
    st.markdown("### \U0001f9e0 Tips AI untuk Booking Anda")

    # Build context for the AI prompt
    traveler_count = max(len(data.get("travelers", [])), 1)
    prices = calculate_total_price(data)
    dep_date = data.get("departure_date")
    dep_date_str = dep_date.strftime("%d %B %Y") if dep_date else "belum dipilih"
    city = data.get("departure_city", "Jakarta")
    hotel_star = data.get("hotel_star", 3)
    addons_list = data.get("addons", [])
    addons_names = []
    for aid in addons_list:
        a = next((x for x in ADDONS if x.id == aid), None)
        if a:
            addons_names.append(a.name)
    addons_str = ", ".join(addons_names) if addons_names else "tidak ada"

    prompt_text = (
        f"Seorang jamaah umrah dari {city} memilih:\n"
        f"- Paket: {package.name} ({format_currency(package.base_price)}/orang)\n"
        f"- Jumlah jamaah: {traveler_count}\n"
        f"- Hotel bintang: {hotel_star}\n"
        f"- Tanggal berangkat: {dep_date_str}\n"
        f"- Add-ons: {addons_str}\n"
        f"- Total estimasi: {format_currency(prices['total'])}\n\n"
        "Berikan 3-4 tips singkat dan praktis untuk memaksimalkan "
        "pengalaman umrah mereka berdasarkan pilihan di atas. "
        "Termasuk tips hemat, persiapan dokumen, dan saran ibadah."
    )

    system_prompt = (
        "Kamu adalah konsultan perjalanan umrah berpengalaman. "
        "Berikan tips yang personal dan relevan berdasarkan pilihan paket jamaah. "
        "Gunakan bahasa Indonesia yang sopan dan Islami. "
        "Format jawaban dalam poin-poin singkat. Jangan lebih dari 200 kata."
    )

    if st.button("\U0001f9e0 Dapatkan Tips AI", key="btn_ai_booking_tips"):
        with st.spinner("Menganalisis pilihan Anda..."):
            response = ai_complete(prompt_text, system_prompt=system_prompt, max_tokens=512)

        if response:
            escaped = response.replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(
                '<div class="ai-card" role="status" aria-live="polite">'
                '<h3>\U0001f9e0 Tips AI untuk Perjalanan Anda</h3>'
                '<p>' + escaped + '</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            if not st.session_state.get("booking_ai_tips_xp_awarded", False):
                st.session_state.booking_ai_tips_xp_awarded = True
                add_xp_safe(15, "Mendapatkan tips AI booking umrah")
        else:
            _render_ai_tips_fallback(package)


def _render_ai_tips_fallback(package):
    """Static fallback tips when AI is unavailable."""
    if package.type == PackageType.BACKPACKER or package.type == PackageType.MANDIRI:
        tips = (
            "1. Pastikan paspor masih berlaku minimal 6 bulan\n"
            "2. Siapkan uang tunai SAR secukupnya untuk makan dan transport\n"
            "3. Download peta offline Makkah dan Madinah\n"
            "4. Bawa obat-obatan pribadi yang cukup"
        )
    elif package.type == PackageType.VIP:
        tips = (
            "1. Manfaatkan fasilitas lounge untuk istirahat sebelum penerbangan\n"
            "2. Koordinasikan jadwal ziarah pribadi dengan mutawif personal Anda\n"
            "3. Hotel dekat Ka'bah memudahkan sholat 5 waktu di Masjidil Haram\n"
            "4. Gunakan layanan room service untuk hemat waktu"
        )
    else:
        tips = (
            "1. Pastikan paspor masih berlaku minimal 6 bulan sebelum keberangkatan\n"
            "2. Siapkan copy dokumen penting secara digital di cloud\n"
            "3. Bawa perlengkapan ibadah cadangan (mukena/sarung)\n"
            "4. Perbanyak doa dan dzikir selama perjalanan"
        )
    st.markdown(
        '<div class="ai-card" role="status" aria-live="polite" style="border-color: #d4af37;">'
        '<h3 style="color: #d4af37;">\U0001f4a1 Tips Booking</h3>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(tips)


# =============================================================================
# RENDER COMPONENTS
# =============================================================================

def render_progress_bar():
    """Render booking progress indicator."""

    steps = [
        (BookingStep.PACKAGE, "\U0001f4e6 Paket"),
        (BookingStep.SCHEDULE, "\U0001f4c5 Jadwal"),
        (BookingStep.TRAVELERS, "\U0001f465 Jamaah"),
        (BookingStep.ADDONS, "\U0001f381 Add-ons"),
        (BookingStep.REVIEW, "\U0001f4cb Review"),
        (BookingStep.PAYMENT, "\U0001f4b3 Bayar"),
        (BookingStep.CONFIRMATION, "\u2705 Selesai"),
    ]

    current = get_current_step()
    current_idx = list(BookingStep).index(current)

    # Progress bar
    progress = (current_idx + 1) / len(steps)
    st.progress(progress)

    # Step indicators
    cols = st.columns(len(steps))
    for i, (step, label) in enumerate(steps):
        with cols[i]:
            if i < current_idx:
                st.markdown(f"\u2705 ~~{label}~~")
            elif i == current_idx:
                st.markdown(f"\U0001f535 **{label}**")
            else:
                st.caption(f"\u26aa {label}")


def render_price_summary():
    """Render real-time price summary in sidebar."""

    with st.sidebar:
        st.markdown("### \U0001f4b0 Ringkasan Biaya")

        data = st.session_state.booking_data
        prices = calculate_total_price(data)

        travelers_count = max(len(data.get("travelers", [])), 1)

        with st.container(border=True):
            st.markdown(f"**\U0001f465 {travelers_count} Jamaah**")

            st.markdown("---")

            # Base
            if data.get("package_type"):
                package = next((p for p in PACKAGES if p.type.value == data["package_type"]), None)
                if package:
                    st.markdown(f"\U0001f4e6 {package.name}")
                    st.caption(f"{format_currency(prices['base'])}")

            # Hotel upgrade
            if prices.get("hotel_upgrade", 0) > 0:
                st.markdown(f"\U0001f3e8 Upgrade Hotel")
                st.caption(f"+{format_currency(prices['hotel_upgrade'])}")

            # Add-ons
            if prices.get("addons", 0) > 0:
                st.markdown(f"\U0001f381 Add-ons")
                st.caption(f"+{format_currency(prices['addons'])}")

            # Seasonal
            if prices.get("seasonal", 0) > 0:
                st.markdown(f"\U0001f4c5 Seasonal")
                st.caption(f"+{format_currency(prices['seasonal'])}")

            st.markdown("---")

            # Total
            st.markdown(f"### Total")
            st.markdown(f"## {format_currency(prices['total'])}")
            st.caption(f"{format_currency(prices['per_person'])} / orang")

        # Promo code
        promo = st.text_input("\U0001f39f\ufe0f Kode Promo", placeholder="Masukkan kode")
        if promo:
            if promo.upper() == "LABBAIK10":
                st.success("\u2705 Diskon 10% applied!")
            else:
                st.error("\u274c Kode tidak valid")


def render_step_package():
    """Render package selection step."""

    st.markdown("## \U0001f4e6 Pilih Paket Umrah")
    st.caption("Pilih paket yang sesuai dengan kebutuhan dan budget Anda")

    # Package comparison
    selected = st.session_state.booking_data.get("package_type")

    # Grid view
    for i in range(0, len(PACKAGES), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(PACKAGES):
                package = PACKAGES[i + j]

                with col:
                    is_selected = selected == package.type.value

                    with st.container(border=True):
                        # Header badges
                        badges = ""
                        if package.popular:
                            badges += "\U0001f525 POPULER "
                        if package.best_value:
                            badges += "\U0001f48e BEST VALUE"

                        if badges:
                            st.markdown(f"**{badges}**")

                        # Package header
                        st.markdown(f"### {package.icon} {package.name}")
                        st.caption(package.description)

                        # Price
                        st.markdown(f"### {format_currency(package.base_price)}")
                        st.caption("per orang")

                        # Key features
                        st.markdown("---")
                        st.markdown(f"\U0001f3e8 **Hotel:** {package.hotel_makkah}")
                        st.markdown(f"\U0001f4cd **Jarak:** {package.distance_haram}")
                        st.markdown(f"\U0001f37d\ufe0f **Makan:** {package.meals}")
                        st.markdown(f"👨\u200d\U0001f3eb **Mutawif:** {package.mutawif}")

                        # Expandable features
                        with st.expander("Lihat semua fitur"):
                            for feature in package.features:
                                st.markdown(f"- {feature}")

                        # Select button
                        btn_type = "primary" if is_selected else "secondary"
                        btn_label = "\u2713 Terpilih" if is_selected else "Pilih Paket"

                        if st.button(btn_label, key=f"pkg_{package.type.value}", type=btn_type, use_container_width=True):
                            st.session_state.booking_data["package_type"] = package.type.value
                            st.rerun()

    # Navigation
    st.divider()
    col1, col2 = st.columns([3, 1])

    with col2:
        if selected:
            if st.button("Lanjut \u2192", type="primary", use_container_width=True):
                next_step()
                st.rerun()
        else:
            st.warning("Pilih paket terlebih dahulu")


def render_step_schedule():
    """Render schedule selection step."""

    st.markdown("## \U0001f4c5 Pilih Jadwal Perjalanan")

    data = st.session_state.booking_data

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### \U0001f6eb Keberangkatan")

        departure_city = st.selectbox(
            "Kota Keberangkatan",
            ["Jakarta", "Surabaya", "Bandung", "Medan", "Makassar", "Semarang", "Yogyakarta", "Palembang", "Balikpapan", "Pekanbaru"],
            index=0
        )
        data["departure_city"] = departure_city

        departure_date = st.date_input(
            "Tanggal Berangkat",
            min_value=date.today() + timedelta(days=30),
            value=date.today() + timedelta(days=60)
        )
        data["departure_date"] = departure_date

        # Calendar highlight
        month = departure_date.month
        if month == 3 or month == 4:
            st.warning("\u26a0\ufe0f **Periode Ramadan** - Harga lebih tinggi, sangat ramai")
        elif month in [6, 7]:
            st.info("\u2139\ufe0f **Peak Season** - Musim liburan sekolah")
        elif month == 12:
            st.info("\u2139\ufe0f **Peak Season** - Liburan akhir tahun")
        else:
            st.success("\u2705 **Regular Season** - Harga normal")

    with col2:
        st.markdown("### \U0001f6ec Kepulangan")

        duration = st.selectbox(
            "Durasi Trip",
            [9, 10, 12, 14, 21],
            format_func=lambda x: f"{x} hari / {x-1} malam",
            index=1
        )

        return_date = departure_date + timedelta(days=duration)
        data["return_date"] = return_date

        st.info(f"\U0001f4c5 **Pulang:** {return_date.strftime('%d %B %Y')}")

        # Duration breakdown
        st.markdown("### \u23f1\ufe0f Pembagian Waktu")

        max_nights = duration - 1

        days_makkah = st.slider(
            "Malam di Makkah",
            min_value=3,
            max_value=max_nights - 2,
            value=min(5, max_nights - 3)
        )
        data["days_makkah"] = days_makkah

        days_madinah = max_nights - days_makkah
        data["days_madinah"] = days_madinah

        st.caption(f"\U0001f54b {days_makkah} malam di Makkah")
        st.caption(f"\U0001f54c {days_madinah} malam di Madinah")

    # Hotel selection
    st.markdown("---")
    st.markdown("### \U0001f3e8 Kategori Hotel")

    package_type = data.get("package_type")

    hotel_cols = st.columns(5)
    hotel_options = [
        (3, "\u2b50\u2b50\u2b50", "Standar", "300-500m dari Masjid"),
        (4, "\u2b50\u2b50\u2b50\u2b50", "Superior", "100-300m dari Masjid"),
        (5, "\u2b50\u2b50\u2b50\u2b50\u2b50", "Premium", "< 100m, view Ka'bah"),
    ]

    current_hotel = data.get("hotel_star", 4)

    for i, (star, icons, name, desc) in enumerate(hotel_options):
        with hotel_cols[i]:
            is_selected = current_hotel == star

            with st.container(border=True):
                st.markdown(f"### {icons}")
                st.markdown(f"**{name}**")
                st.caption(desc)

                upgrade = ""
                if star == 4:
                    upgrade = "+Rp 3 Juta"
                elif star == 5:
                    upgrade = "+Rp 8 Juta"

                if upgrade:
                    st.caption(upgrade)

                if st.button(
                    "\u2713" if is_selected else "Pilih",
                    key=f"hotel_{star}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True
                ):
                    data["hotel_star"] = star
                    st.rerun()

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("\u2190 Kembali", use_container_width=True):
            prev_step()
            st.rerun()

    with col3:
        if st.button("Lanjut \u2192", type="primary", use_container_width=True):
            next_step()
            st.rerun()


def render_step_travelers():
    """Render travelers data step."""

    st.markdown("## \U0001f465 Data Jamaah")
    st.caption("Masukkan data sesuai paspor untuk semua jamaah")

    data = st.session_state.booking_data
    travelers = data.get("travelers", [])

    # Summary
    if travelers:
        st.success(f"\u2705 {len(travelers)} jamaah terdaftar")

    # Add traveler form
    with st.expander("\u2795 Tambah Jamaah Baru", expanded=not travelers):
        with st.form("add_traveler", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Nama Lengkap (sesuai paspor) *")
                passport_number = st.text_input("Nomor Paspor *")
                passport_expiry = st.date_input(
                    "Masa Berlaku Paspor *",
                    min_value=date.today() + timedelta(days=180),
                    value=date.today() + timedelta(days=365 * 2)
                )
                nationality = st.selectbox(
                    "Kewarganegaraan",
                    ["Indonesia", "Malaysia", "Singapura", "Lainnya"]
                )

            with col2:
                birth_date = st.date_input(
                    "Tanggal Lahir *",
                    max_value=date.today() - timedelta(days=365),
                    value=date.today() - timedelta(days=365 * 35)
                )
                gender = st.radio("Jenis Kelamin *", ["Laki-laki", "Perempuan"], horizontal=True)
                phone = st.text_input("Nomor HP (WhatsApp)")
                email = st.text_input("Email")

            # Additional options
            col1, col2 = st.columns(2)
            with col1:
                room_pref = st.selectbox(
                    "Preferensi Kamar",
                    ["Double (2 orang)", "Triple (3 orang)", "Quad (4 orang)"],
                    index=0
                )
            with col2:
                special_needs = st.text_input("Kebutuhan Khusus", placeholder="Kursi roda, vegetarian, dll.")

            is_primary = st.checkbox("Jamaah utama (contact person)")

            if st.form_submit_button("\u2795 Tambah Jamaah", type="primary", use_container_width=True):
                if name and passport_number:
                    new_traveler = {
                        "name": name,
                        "passport_number": passport_number,
                        "passport_expiry": passport_expiry.isoformat(),
                        "birth_date": birth_date.isoformat(),
                        "gender": "male" if gender == "Laki-laki" else "female",
                        "nationality": nationality,
                        "phone": phone,
                        "email": email,
                        "room_preference": room_pref,
                        "special_needs": special_needs,
                        "is_primary": is_primary,
                    }
                    travelers.append(new_traveler)
                    data["travelers"] = travelers
                    st.success(f"\u2705 {name} berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Nama dan nomor paspor wajib diisi")

    # List travelers
    if travelers:
        st.markdown("### \U0001f4cb Daftar Jamaah")

        for i, t in enumerate(travelers):
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

                with col1:
                    st.markdown(f"### {i+1}")
                    if t.get("is_primary"):
                        st.caption("\U0001f451 Utama")

                with col2:
                    st.markdown(f"**{t['name']}**")
                    st.caption(f"\U0001f6c2 {t['passport_number']}")

                with col3:
                    gender_icon = "\U0001f468" if t['gender'] == 'male' else "\U0001f469"
                    st.caption(f"{gender_icon} {t.get('birth_date', 'N/A')}")
                    if t.get("special_needs"):
                        st.caption(f"\u26a0\ufe0f {t['special_needs']}")

                with col4:
                    if st.button("\U0001f5d1\ufe0f", key=f"del_{i}", help="Hapus jamaah"):
                        travelers.pop(i)
                        data["travelers"] = travelers
                        st.rerun()

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("\u2190 Kembali", use_container_width=True):
            prev_step()
            st.rerun()

    with col3:
        if travelers:
            if st.button("Lanjut \u2192", type="primary", use_container_width=True):
                next_step()
                st.rerun()
        else:
            st.warning("Tambahkan minimal 1 jamaah")


def render_step_addons():
    """Render add-ons selection step."""

    st.markdown("## \U0001f381 Pilih Add-ons")
    st.caption("Tambahkan layanan ekstra untuk pengalaman umrah yang lebih lengkap")

    data = st.session_state.booking_data
    selected_addons = data.get("addons", [])

    # Group by category
    categories = {
        "protection": ("\U0001f6e1\ufe0f Perlindungan", [a for a in ADDONS if a.category == "protection"]),
        "comfort": ("\u2728 Kenyamanan", [a for a in ADDONS if a.category == "comfort"]),
        "experience": ("\U0001f31f Pengalaman", [a for a in ADDONS if a.category == "experience"]),
        "utility": ("\U0001f527 Utilitas", [a for a in ADDONS if a.category == "utility"]),
        "souvenir": ("\U0001f381 Oleh-oleh", [a for a in ADDONS if a.category == "souvenir"]),
        "special": ("\u267f Kebutuhan Khusus", [a for a in ADDONS if a.category == "special"]),
    }

    for cat_id, (cat_name, addons) in categories.items():
        if addons:
            st.markdown(f"### {cat_name}")

            cols = st.columns(3)
            for i, addon in enumerate(addons):
                with cols[i % 3]:
                    is_selected = addon.id in selected_addons

                    with st.container(border=True):
                        # Popular badge
                        if addon.popular:
                            st.markdown("\U0001f525 **POPULER**")

                        st.markdown(f"### {addon.icon} {addon.name}")
                        st.caption(addon.description)
                        st.markdown(f"**{format_currency(addon.price)}**")
                        st.caption("per orang")

                        if st.checkbox(
                            "Tambahkan" if not is_selected else "\u2713 Ditambahkan",
                            value=is_selected,
                            key=f"addon_{addon.id}"
                        ):
                            if addon.id not in selected_addons:
                                selected_addons.append(addon.id)
                        else:
                            if addon.id in selected_addons:
                                selected_addons.remove(addon.id)

            st.markdown("")

    data["addons"] = selected_addons

    # Summary
    if selected_addons:
        st.success(f"\u2705 {len(selected_addons)} add-ons dipilih")

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("\u2190 Kembali", use_container_width=True):
            prev_step()
            st.rerun()

    with col3:
        if st.button("Lanjut \u2192", type="primary", use_container_width=True):
            next_step()
            st.rerun()


def render_step_review():
    """Render booking review step."""

    st.markdown("## \U0001f4cb Review Booking")

    data = st.session_state.booking_data
    prices = calculate_total_price(data)

    # Package summary
    package = next((p for p in PACKAGES if p.type.value == data.get("package_type")), None)

    with st.container(border=True):
        st.markdown("### \U0001f4e6 Paket")
        if package:
            st.markdown(f"## {package.icon} {package.name}")
            st.caption(package.description)

    # Schedule
    with st.container(border=True):
        st.markdown("### \U0001f4c5 Jadwal")
        col1, col2, col3 = st.columns(3)

        with col1:
            dep_label = data.get("departure_date", "N/A").strftime("%d %b %Y") if data.get("departure_date") else "N/A"
            st.metric("Berangkat", dep_label)
        with col2:
            ret_label = data.get("return_date", "N/A").strftime("%d %b %Y") if data.get("return_date") else "N/A"
            st.metric("Pulang", ret_label)
        with col3:
            if data.get("departure_date") and data.get("return_date"):
                days = (data["return_date"] - data["departure_date"]).days
                st.metric("Durasi", f"{days} hari")

        st.caption(f"\U0001f4cd Dari: {data.get('departure_city', 'N/A')}")
        st.caption(f"\U0001f54b {data.get('days_makkah', 0)} malam di Makkah | \U0001f54c {data.get('days_madinah', 0)} malam di Madinah")

    # Travelers
    travelers = data.get("travelers", [])
    with st.container(border=True):
        st.markdown("### \U0001f465 Jamaah")
        for i, t in enumerate(travelers, 1):
            primary = " \U0001f451" if t.get("is_primary") else ""
            st.markdown(f"{i}. **{t['name']}**{primary} - {t['passport_number']}")
        st.info(f"Total: {len(travelers)} jamaah")

    # Add-ons
    selected_addons = data.get("addons", [])
    if selected_addons:
        with st.container(border=True):
            st.markdown("### \U0001f381 Add-ons")
            for addon_id in selected_addons:
                addon = next((a for a in ADDONS if a.id == addon_id), None)
                if addon:
                    st.markdown(f"- {addon.icon} {addon.name} ({format_currency(addon.price)}/orang)")

    # Price breakdown
    with st.container(border=True):
        st.markdown("### \U0001f4b0 Rincian Biaya")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"\U0001f4e6 Paket ({len(travelers)} orang)")
            if prices.get("hotel_upgrade", 0) > 0:
                st.markdown("\U0001f3e8 Upgrade Hotel")
            if prices.get("addons", 0) > 0:
                st.markdown("\U0001f381 Add-ons")
            if prices.get("seasonal", 0) > 0:
                st.markdown("\U0001f4c5 Seasonal Adjustment")
            st.markdown("---")
            st.markdown("**TOTAL**")

        with col2:
            st.markdown(f"{format_currency(prices['base'])}")
            if prices.get("hotel_upgrade", 0) > 0:
                st.markdown(f"+{format_currency(prices['hotel_upgrade'])}")
            if prices.get("addons", 0) > 0:
                st.markdown(f"+{format_currency(prices['addons'])}")
            if prices.get("seasonal", 0) > 0:
                st.markdown(f"+{format_currency(prices['seasonal'])}")
            st.markdown("---")
            st.markdown(f"**{format_currency(prices['total'])}**")

    # AI booking tips on review page
    render_ai_booking_tips()

    # Terms
    st.markdown("### \U0001f4dc Syarat & Ketentuan")
    agree = st.checkbox("Saya telah membaca dan menyetujui syarat dan ketentuan yang berlaku")

    # Notes
    notes = st.text_area("\U0001f4dd Catatan Tambahan (opsional)", placeholder="Permintaan khusus, alergi makanan, dll.")
    data["notes"] = notes

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("\u2190 Kembali", use_container_width=True):
            prev_step()
            st.rerun()

    with col3:
        if agree:
            if st.button("Lanjut ke Pembayaran \u2192", type="primary", use_container_width=True):
                next_step()
                st.rerun()
        else:
            st.warning("Setujui syarat dan ketentuan")


def render_step_payment():
    """Render payment step."""

    st.markdown("## \U0001f4b3 Pembayaran")

    data = st.session_state.booking_data
    prices = calculate_total_price(data)
    total = prices["total"]

    # Payment options
    st.markdown("### \U0001f4b5 Pilih Jenis Pembayaran")

    payment_type = st.radio(
        "Opsi pembayaran",
        ["DP 30%", "DP 50%", "Lunas 100%"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if payment_type == "DP 30%":
        amount = int(total * 0.3)
        remaining = total - amount
        st.info(f"Bayar sekarang: **{format_currency(amount)}** | Sisa: {format_currency(remaining)}")
    elif payment_type == "DP 50%":
        amount = int(total * 0.5)
        remaining = total - amount
        st.info(f"Bayar sekarang: **{format_currency(amount)}** | Sisa: {format_currency(remaining)}")
    else:
        amount = total
        remaining = 0
        st.success(f"Bayar lunas: **{format_currency(amount)}** | Hemat Rp 500.000!")

    st.markdown("---")

    # Payment method
    st.markdown("### \U0001f3e6 Metode Pembayaran")

    method = st.radio(
        "Pilih metode",
        ["\U0001f4b3 Transfer Bank", "\U0001f4f1 Virtual Account", "\U0001f4b0 E-Wallet", "\U0001f4b3 Kartu Kredit"],
        label_visibility="collapsed"
    )

    with st.container(border=True):
        if "Transfer" in method:
            st.markdown(
                "**Bank BCA**\n"
                "- No. Rekening: `123-456-7890`\n"
                "- Atas Nama: PT LABBAIK WISATA MANDIRI\n\n"
                "**Bank Mandiri**\n"
                "- No. Rekening: `098-765-4321`\n"
                "- Atas Nama: PT LABBAIK WISATA MANDIRI"
            )
        elif "Virtual" in method:
            st.markdown("Virtual Account akan digenerate setelah konfirmasi booking")
            st.markdown(f"**Total: {format_currency(amount)}**")
        elif "E-Wallet" in method:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.button("GoPay", use_container_width=True)
            with col2:
                st.button("OVO", use_container_width=True)
            with col3:
                st.button("DANA", use_container_width=True)
            with col4:
                st.button("ShopeePay", use_container_width=True)
        else:
            st.markdown("Pembayaran kartu kredit akan diarahkan ke payment gateway")

    # Upload bukti
    st.markdown("### \U0001f4e4 Upload Bukti Pembayaran")
    uploaded = st.file_uploader(
        "Upload screenshot/foto bukti transfer",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Format: JPG, PNG, atau PDF. Max 5MB"
    )

    if uploaded:
        st.success("\u2705 File berhasil diupload")

    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("\u2190 Kembali", use_container_width=True):
            prev_step()
            st.rerun()

    with col3:
        if uploaded or method != "\U0001f4b3 Transfer Bank":
            if st.button("Konfirmasi Pembayaran \u2192", type="primary", use_container_width=True):
                next_step()
                st.rerun()
        else:
            st.warning("Upload bukti pembayaran")


def render_step_confirmation():
    """Render confirmation step."""

    st.balloons()

    booking_number = generate_booking_number()

    st.markdown("## \u2705 Booking Berhasil!")

    with st.container(border=True):
        st.markdown("### \U0001f389 Alhamdulillah!")

        st.markdown(
            "Booking Umrah Anda telah berhasil dibuat.\n\n"
            "### Nomor Booking\n"
            f"## `{booking_number}`\n\n"
            "Simpan nomor ini untuk referensi."
        )

        st.success("\U0001f4e7 Email konfirmasi telah dikirim ke alamat email jamaah utama")
        st.info("\U0001f4f1 WhatsApp konfirmasi akan dikirim dalam 1x24 jam")

    # Next steps
    with st.container(border=True):
        st.markdown("### \U0001f4cb Langkah Selanjutnya")

        steps = [
            ("1\ufe0f\u20e3", "Simpan nomor booking Anda"),
            ("2\ufe0f\u20e3", "Cek email untuk detail lengkap"),
            ("3\ufe0f\u20e3", "Tunggu konfirmasi dari tim kami (1x24 jam)"),
            ("4\ufe0f\u20e3", "Siapkan dokumen yang diperlukan"),
            ("5\ufe0f\u20e3", "Lunasi pembayaran sesuai jadwal"),
            ("6\ufe0f\u20e3", "Ikuti briefing pra-keberangkatan"),
        ]

        for num, text in steps:
            st.markdown(f"{num} {text}")

    # Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("\U0001f3e0 Kembali ke Beranda", use_container_width=True):
            st.session_state.booking_step = BookingStep.PACKAGE
            st.session_state.booking_data = {}
            st.rerun()

    with col2:
        if st.button("\U0001f4e5 Download Konfirmasi", use_container_width=True):
            st.info("PDF konfirmasi akan segera tersedia")

    with col3:
        if st.button("\U0001f4e4 Share", use_container_width=True):
            st.info("Bagikan ke WhatsApp/sosmed")


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_booking_page():
    """Main booking page renderer."""

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, BOOKING_CSS)

    # Track page view
    try:
        from services.analytics import track_page
        track_page("booking")
    except Exception:
        pass

    # Initialize state
    init_booking_state()

    # Header with hero
    st.markdown(
        '<div class="booking-hero">'
        '<div class="bismillah">\u0628\u0633\u0645 \u0627\u0644\u0644\u0647 \u0627\u0644\u0631\u062d\u0645\u0646 \u0627\u0644\u0631\u062d\u064a\u0645</div>'
        '<h1>\U0001f54b Booking Umrah</h1>'
        '<p class="subtitle">Pesan perjalanan umrah Anda dengan mudah dan aman</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Progress bar
    render_progress_bar()

    st.divider()

    # Price summary in sidebar
    if get_current_step() not in [BookingStep.PACKAGE, BookingStep.CONFIRMATION]:
        render_price_summary()

    # Render current step
    current = get_current_step()

    step_renderers = {
        BookingStep.PACKAGE: render_step_package,
        BookingStep.SCHEDULE: render_step_schedule,
        BookingStep.TRAVELERS: render_step_travelers,
        BookingStep.ADDONS: render_step_addons,
        BookingStep.REVIEW: render_step_review,
        BookingStep.PAYMENT: render_step_payment,
        BookingStep.CONFIRMATION: render_step_confirmation,
    }

    renderer = step_renderers.get(current)
    if renderer:
        renderer()

    # Footer
    if current != BookingStep.CONFIRMATION:
        st.divider()
        st.caption("\U0001f512 Data Anda aman dan terenkripsi | \U0001f4ac Butuh bantuan? Chat kami 24/7")


# Export
__all__ = ["render_booking_page"]
