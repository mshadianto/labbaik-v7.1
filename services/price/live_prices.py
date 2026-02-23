"""
LABBAIK AI - Live Price Updates Service
=======================================
Real-time Umrah package price fetching and display.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import random

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LivePackage:
    """Live Umrah package data."""
    id: str
    name: str
    travel_agent: str
    price: int
    original_price: int
    discount_percent: float
    duration_days: int
    hotel_makkah: str
    hotel_makkah_stars: int
    hotel_madinah: str
    hotel_madinah_stars: int
    departure_city: str
    departure_dates: List[str]
    includes: List[str]
    rating: float
    reviews_count: int
    is_featured: bool
    is_promo: bool
    seats_available: int
    last_updated: datetime


@dataclass
class PriceAlert:
    """Price change alert."""
    package_id: str
    package_name: str
    old_price: int
    new_price: int
    change_percent: float
    change_type: str  # "increase" or "decrease"
    timestamp: datetime


# =============================================================================
# SAMPLE DATA (In production, this comes from database/API)
# =============================================================================

SAMPLE_PACKAGES: List[Dict] = [
    {
        "id": "PKG-001",
        "name": "Umrah Hemat Barokah",
        "travel_agent": "PT Berkah Travel",
        "price": 22_500_000,
        "original_price": 25_000_000,
        "discount_percent": 10,
        "duration_days": 9,
        "hotel_makkah": "Elaf Ajyad Hotel",
        "hotel_makkah_stars": 3,
        "hotel_madinah": "Dallah Taibah Hotel",
        "hotel_madinah_stars": 3,
        "departure_city": "Jakarta",
        "departure_dates": ["2025-02-15", "2025-02-28", "2025-03-10"],
        "includes": ["Tiket PP", "Hotel", "Visa", "Makan 3x", "Guide"],
        "rating": 4.5,
        "reviews_count": 128,
        "is_featured": False,
        "is_promo": True,
        "seats_available": 12,
    },
    {
        "id": "PKG-002",
        "name": "Umrah Plus Nyaman",
        "travel_agent": "Andalusia Tour",
        "price": 32_000_000,
        "original_price": 35_000_000,
        "discount_percent": 8.5,
        "duration_days": 12,
        "hotel_makkah": "Pullman Zamzam",
        "hotel_makkah_stars": 5,
        "hotel_madinah": "Dar Al Taqwa",
        "hotel_madinah_stars": 4,
        "departure_city": "Jakarta",
        "departure_dates": ["2025-02-20", "2025-03-05", "2025-03-15"],
        "includes": ["Tiket PP", "Hotel Bintang 5", "Visa", "Makan 3x", "Mutawif", "City Tour"],
        "rating": 4.8,
        "reviews_count": 256,
        "is_featured": True,
        "is_promo": True,
        "seats_available": 8,
    },
    {
        "id": "PKG-003",
        "name": "Umrah Ramadhan Special",
        "travel_agent": "Hajar Aswad Travel",
        "price": 38_000_000,
        "original_price": 42_000_000,
        "discount_percent": 9.5,
        "duration_days": 14,
        "hotel_makkah": "Swissotel Makkah",
        "hotel_makkah_stars": 5,
        "hotel_madinah": "Pullman Madinah",
        "hotel_madinah_stars": 5,
        "departure_city": "Jakarta",
        "departure_dates": ["2025-03-01", "2025-03-10", "2025-03-15"],
        "includes": ["Tiket PP", "Hotel Bintang 5", "Visa", "Makan 3x", "Mutawif", "Ziarah"],
        "rating": 4.9,
        "reviews_count": 89,
        "is_featured": True,
        "is_promo": True,
        "seats_available": 5,
    },
    {
        "id": "PKG-004",
        "name": "Umrah VIP Executive",
        "travel_agent": "Royal Haji Tour",
        "price": 75_000_000,
        "original_price": 80_000_000,
        "discount_percent": 6.25,
        "duration_days": 12,
        "hotel_makkah": "Raffles Makkah Palace",
        "hotel_makkah_stars": 5,
        "hotel_madinah": "The Oberoi Madinah",
        "hotel_madinah_stars": 5,
        "departure_city": "Jakarta",
        "departure_dates": ["2025-02-25", "2025-03-08"],
        "includes": ["Tiket Business Class", "Hotel View Haram", "Visa", "Full Board", "Private Guide", "Ziarah Lengkap"],
        "rating": 5.0,
        "reviews_count": 34,
        "is_featured": True,
        "is_promo": False,
        "seats_available": 2,
    },
    {
        "id": "PKG-005",
        "name": "Umrah Keluarga Sakinah",
        "travel_agent": "Sakinah Tour",
        "price": 28_500_000,
        "original_price": 30_000_000,
        "discount_percent": 5,
        "duration_days": 10,
        "hotel_makkah": "Le Meridien Makkah",
        "hotel_makkah_stars": 4,
        "hotel_madinah": "Anwar Al Madinah",
        "hotel_madinah_stars": 4,
        "departure_city": "Surabaya",
        "departure_dates": ["2025-02-18", "2025-03-01", "2025-03-12"],
        "includes": ["Tiket PP", "Hotel Bintang 4", "Visa", "Makan 3x", "Guide", "Kids Program"],
        "rating": 4.7,
        "reviews_count": 156,
        "is_featured": False,
        "is_promo": True,
        "seats_available": 15,
    },
    {
        "id": "PKG-006",
        "name": "Umrah Backpacker Muslim",
        "travel_agent": "Hijrah Tours",
        "price": 18_900_000,
        "original_price": 20_000_000,
        "discount_percent": 5.5,
        "duration_days": 9,
        "hotel_makkah": "Makkah Hotel",
        "hotel_makkah_stars": 2,
        "hotel_madinah": "Madinah Hilton",
        "hotel_madinah_stars": 2,
        "departure_city": "Jakarta",
        "departure_dates": ["2025-02-10", "2025-02-24", "2025-03-07"],
        "includes": ["Tiket PP", "Hotel Budget", "Visa", "Transport"],
        "rating": 4.3,
        "reviews_count": 89,
        "is_featured": False,
        "is_promo": True,
        "seats_available": 20,
    },
]


# =============================================================================
# LIVE PRICE SERVICE
# =============================================================================

class LivePriceService:
    """Service for fetching and managing live prices."""

    def __init__(self):
        self.last_fetch = None
        self.cache_ttl = timedelta(minutes=5)
        self._cached_packages = None

    def get_live_packages(
        self,
        min_price: int = 0,
        max_price: int = 100_000_000,
        departure_city: str = None,
        min_stars: int = 0,
        featured_only: bool = False,
        promo_only: bool = False,
    ) -> List[LivePackage]:
        """Get live packages with filters."""
        # Simulate fetching from API/database
        packages = self._fetch_packages()

        # Apply filters
        filtered = []
        for pkg in packages:
            if pkg.price < min_price or pkg.price > max_price:
                continue
            if departure_city and pkg.departure_city != departure_city:
                continue
            if min_stars and min(pkg.hotel_makkah_stars, pkg.hotel_madinah_stars) < min_stars:
                continue
            if featured_only and not pkg.is_featured:
                continue
            if promo_only and not pkg.is_promo:
                continue
            filtered.append(pkg)

        return filtered

    def get_featured_packages(self, limit: int = 3) -> List[LivePackage]:
        """Get featured packages."""
        packages = self.get_live_packages(featured_only=True)
        return packages[:limit]

    def get_promo_packages(self, limit: int = 5) -> List[LivePackage]:
        """Get packages on promo."""
        packages = self.get_live_packages(promo_only=True)
        # Sort by discount
        packages.sort(key=lambda x: x.discount_percent, reverse=True)
        return packages[:limit]

    def get_cheapest_packages(self, limit: int = 5) -> List[LivePackage]:
        """Get cheapest packages."""
        packages = self.get_live_packages()
        packages.sort(key=lambda x: x.price)
        return packages[:limit]

    def get_package_by_id(self, package_id: str) -> Optional[LivePackage]:
        """Get specific package by ID."""
        packages = self._fetch_packages()
        for pkg in packages:
            if pkg.id == package_id:
                return pkg
        return None

    def get_price_stats(self) -> Dict[str, Any]:
        """Get price statistics."""
        packages = self.get_live_packages()
        if not packages:
            return {}

        prices = [p.price for p in packages]
        return {
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) // len(prices),
            "total_packages": len(packages),
            "promo_count": len([p for p in packages if p.is_promo]),
            "featured_count": len([p for p in packages if p.is_featured]),
            "last_updated": datetime.now(),
        }

    def _fetch_packages(self) -> List[LivePackage]:
        """Fetch packages from source (cached)."""
        now = datetime.now()

        # Check cache
        if self._cached_packages and self.last_fetch:
            if now - self.last_fetch < self.cache_ttl:
                return self._cached_packages

        # Simulate API call - add small random price variations
        packages = []
        for data in SAMPLE_PACKAGES:
            # Add small random variation to simulate live prices
            price_variation = random.randint(-500_000, 500_000)
            price = data["price"] + price_variation
            price = max(price, 15_000_000)  # Minimum price

            packages.append(LivePackage(
                id=data["id"],
                name=data["name"],
                travel_agent=data["travel_agent"],
                price=price,
                original_price=data["original_price"],
                discount_percent=round((1 - price / data["original_price"]) * 100, 1),
                duration_days=data["duration_days"],
                hotel_makkah=data["hotel_makkah"],
                hotel_makkah_stars=data["hotel_makkah_stars"],
                hotel_madinah=data["hotel_madinah"],
                hotel_madinah_stars=data["hotel_madinah_stars"],
                departure_city=data["departure_city"],
                departure_dates=data["departure_dates"],
                includes=data["includes"],
                rating=data["rating"],
                reviews_count=data["reviews_count"],
                is_featured=data["is_featured"],
                is_promo=data["is_promo"],
                seats_available=max(0, data["seats_available"] - random.randint(0, 2)),
                last_updated=now,
            ))

        self._cached_packages = packages
        self.last_fetch = now
        return packages


# =============================================================================
# CACHED WRAPPERS (survive Streamlit reruns unlike instance-level cache)
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_live_packages(limit: int = 5) -> list:
    """Cached wrapper for cheapest packages. Returns list of dicts."""
    service = LivePriceService()
    packages = service.get_cheapest_packages(limit)
    return [
        {
            "id": p.id, "name": p.name, "travel_agent": p.travel_agent,
            "price": p.price, "original_price": p.original_price,
            "discount_percent": p.discount_percent,
            "duration_days": p.duration_days,
            "hotel_makkah": p.hotel_makkah, "hotel_makkah_stars": p.hotel_makkah_stars,
            "hotel_madinah": p.hotel_madinah, "hotel_madinah_stars": p.hotel_madinah_stars,
            "departure_city": p.departure_city, "rating": p.rating,
            "is_promo": p.is_promo, "is_featured": p.is_featured,
            "seats_available": p.seats_available,
        }
        for p in packages
    ]


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_price_stats() -> dict:
    """Cached wrapper for price statistics."""
    service = LivePriceService()
    stats = service.get_price_stats()
    if stats and "last_updated" in stats:
        stats["last_updated"] = str(stats["last_updated"])
    return stats


# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================

def format_price(amount: int) -> str:
    """Format price as IDR."""
    return f"Rp {amount:,.0f}".replace(",", ".")


def render_live_price_badge():
    """Render live price indicator."""
    st.markdown("""
    <div style="display: inline-flex; align-items: center; gap: 5px; background: #1a1a2e;
                padding: 5px 10px; border-radius: 20px; border: 1px solid #28a745;">
        <span style="width: 8px; height: 8px; background: #28a745; border-radius: 50%;
                     animation: pulse 1.5s infinite;"></span>
        <span style="color: #28a745; font-size: 0.8rem; font-weight: bold;">LIVE</span>
    </div>
    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_package_card_live(pkg: LivePackage):
    """Render a live package card."""
    with st.container(border=True):
        # Header row
        col1, col2 = st.columns([3, 1])

        with col1:
            # Badges
            badges = []
            if pkg.is_featured:
                badges.append('<span style="background:#d4af37;color:#000;padding:2px 8px;border-radius:10px;font-size:0.7rem;">FEATURED</span>')
            if pkg.is_promo:
                badges.append(f'<span style="background:#dc3545;color:#fff;padding:2px 8px;border-radius:10px;font-size:0.7rem;">-{pkg.discount_percent:.0f}%</span>')
            if pkg.seats_available <= 5:
                badges.append(f'<span style="background:#f0ad4e;color:#000;padding:2px 8px;border-radius:10px;font-size:0.7rem;">Sisa {pkg.seats_available} kursi</span>')

            badge_html = " ".join(badges)
            st.markdown(f"**{pkg.name}** {badge_html}", unsafe_allow_html=True)
            st.caption(f"oleh {pkg.travel_agent}")

        with col2:
            render_live_price_badge()

        # Price section
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if pkg.discount_percent > 0:
                st.markdown(f"~~{format_price(pkg.original_price)}~~")
            st.markdown(f"### {format_price(pkg.price)}")
            st.caption("per orang")

        with col2:
            st.markdown(f"**{pkg.duration_days} hari**")
            st.caption(f"dari {pkg.departure_city}")

        with col3:
            st.markdown(f"**{'⭐' * int(pkg.rating)}**")
            st.caption(f"{pkg.reviews_count} ulasan")

        # Hotels
        st.markdown(f"""
        🕋 **Makkah:** {pkg.hotel_makkah} ({'⭐' * pkg.hotel_makkah_stars})
        🕌 **Madinah:** {pkg.hotel_madinah} ({'⭐' * pkg.hotel_madinah_stars})
        """)

        # Includes (collapsible)
        with st.expander("Termasuk dalam paket"):
            for item in pkg.includes:
                st.markdown(f"✅ {item}")

        # Departure dates
        st.caption(f"📅 Keberangkatan: {', '.join(pkg.departure_dates[:3])}")

        # Last updated
        st.caption(f"🔄 Update: {pkg.last_updated.strftime('%H:%M:%S')}")


def render_live_prices_page():
    """Render the live prices page."""
    st.markdown("## 💰 Harga Paket Umrah Terkini")

    # Live indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Data diupdate real-time dari berbagai travel agent")
    with col2:
        render_live_price_badge()

    # Initialize service
    service = LivePriceService()

    # Stats
    stats = service.get_price_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Termurah", format_price(stats.get("min_price", 0)))
    with col2:
        st.metric("Rata-rata", format_price(stats.get("avg_price", 0)))
    with col3:
        st.metric("Total Paket", stats.get("total_packages", 0))
    with col4:
        st.metric("Promo Aktif", stats.get("promo_count", 0))

    st.divider()

    # Filters
    with st.expander("🔍 Filter Paket", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            price_range = st.slider(
                "Range Harga (Juta)",
                min_value=15,
                max_value=100,
                value=(15, 50),
                step=5
            )

        with col2:
            departure_city = st.selectbox(
                "Kota Keberangkatan",
                ["Semua", "Jakarta", "Surabaya", "Medan", "Bandung"]
            )

        with col3:
            min_stars = st.selectbox(
                "Minimal Bintang Hotel",
                [0, 2, 3, 4, 5],
                format_func=lambda x: "Semua" if x == 0 else f"{x} Bintang"
            )

        col1, col2 = st.columns(2)
        with col1:
            featured_only = st.checkbox("Featured Only")
        with col2:
            promo_only = st.checkbox("Promo Only")

    # Get filtered packages
    packages = service.get_live_packages(
        min_price=price_range[0] * 1_000_000,
        max_price=price_range[1] * 1_000_000,
        departure_city=None if departure_city == "Semua" else departure_city,
        min_stars=min_stars,
        featured_only=featured_only,
        promo_only=promo_only,
    )

    # Sort options
    sort_option = st.radio(
        "Urutkan:",
        ["Harga Terendah", "Harga Tertinggi", "Rating Tertinggi", "Diskon Terbesar"],
        horizontal=True
    )

    if sort_option == "Harga Terendah":
        packages.sort(key=lambda x: x.price)
    elif sort_option == "Harga Tertinggi":
        packages.sort(key=lambda x: x.price, reverse=True)
    elif sort_option == "Rating Tertinggi":
        packages.sort(key=lambda x: x.rating, reverse=True)
    else:
        packages.sort(key=lambda x: x.discount_percent, reverse=True)

    # Display packages
    st.markdown(f"### Menampilkan {len(packages)} paket")

    for pkg in packages:
        render_package_card_live(pkg)

    # Refresh button
    st.divider()
    if st.button("🔄 Refresh Harga", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Last update info
    st.caption(f"Terakhir diupdate: {datetime.now().strftime('%d %b %Y %H:%M:%S WIB')}")


def render_live_prices_widget():
    """Render mini widget for sidebar/home."""
    service = LivePriceService()
    cheapest = service.get_cheapest_packages(limit=3)

    st.markdown("### 💰 Paket Terpopuler")
    render_live_price_badge()

    for pkg in cheapest:
        with st.container(border=True):
            st.markdown(f"**{pkg.name}**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{format_price(pkg.price)}**")
            with col2:
                if pkg.is_promo:
                    st.markdown(f"🔥 -{pkg.discount_percent:.0f}%")
            st.caption(f"{pkg.duration_days} hari | {'⭐' * pkg.hotel_makkah_stars}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LivePackage",
    "PriceAlert",
    "LivePriceService",
    "render_live_price_badge",
    "render_package_card_live",
    "render_live_prices_page",
    "render_live_prices_widget",
    "format_price",
]
