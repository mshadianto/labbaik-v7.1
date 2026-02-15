"""
LABBAIK AI v6.0 - Price Intelligence UI Components
===================================================
Komponen UI untuk menampilkan data harga.
Dapat digunakan di berbagai halaman.
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime

from services.price.repository import (
    get_cached_packages,
    get_cached_hotels,
    get_cached_flights,
    get_cached_price_summary,
    get_cached_price_ranges,
    format_price_idr
)


# =============================================================================
# PRICE CARDS
# =============================================================================

def render_package_card(package: Dict):
    """Render card untuk paket umrah."""
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {package.get('package_name', 'Paket Umrah')}")
            st.caption(f"🏢 {package.get('source_name', 'Travel Agent')}")
            
            # Details
            details = []
            if package.get('duration_days'):
                details.append(f"📅 {package['duration_days']} Hari")
            if package.get('departure_city'):
                details.append(f"🛫 {package['departure_city']}")
            if package.get('airline'):
                details.append(f"✈️ {package['airline']}")
            
            st.write(" • ".join(details))
            
            # Hotels
            hotel_info = []
            if package.get('hotel_makkah'):
                stars = "⭐" * (package.get('hotel_makkah_stars') or 0)
                hotel_info.append(f"🏨 Makkah: {package['hotel_makkah']} {stars}")
            if package.get('hotel_madinah'):
                stars = "⭐" * (package.get('hotel_madinah_stars') or 0)
                hotel_info.append(f"🏨 Madinah: {package['hotel_madinah']} {stars}")
            
            if hotel_info:
                st.caption(" | ".join(hotel_info))
        
        with col2:
            price = float(package.get('price_idr', 0))
            st.markdown(f"### {format_price_idr(price)}")
            st.caption("per orang")
        
        st.divider()


def render_hotel_card(hotel: Dict):
    """Render card untuk hotel."""
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            stars = "⭐" * hotel.get('star_rating', 0)
            st.markdown(f"**{hotel.get('hotel_name', 'Hotel')}** {stars}")
            st.caption(f"📍 {hotel.get('city', '')} - {hotel.get('distance_to_haram', '')}")
        
        with col2:
            features = []
            if hotel.get('includes_breakfast'):
                features.append("🍳 Sarapan")
            if hotel.get('view_type') == 'haram_view':
                features.append("🕌 Haram View")
            elif hotel.get('view_type') == 'mosque_view':
                features.append("🕌 Mosque View")
            st.write(" • ".join(features) if features else "Standard")
        
        with col3:
            price = float(hotel.get('price_per_night_idr', 0))
            st.markdown(f"**{format_price_idr(price)}**")
            st.caption("/malam")


def render_flight_card(flight: Dict):
    """Render card untuk penerbangan."""
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"**{flight.get('airline', 'Airline')}**")
            st.caption(f"✈️ {flight.get('flight_code', '')}")
        
        with col2:
            route = f"{flight.get('origin_airport', '')} → {flight.get('destination_airport', '')}"
            dep_date = flight.get('departure_date', '')
            if isinstance(dep_date, datetime):
                dep_date = dep_date.strftime('%d %b %Y')
            elif hasattr(dep_date, 'strftime'):
                dep_date = dep_date.strftime('%d %b %Y')
            
            direct = "🟢 Langsung" if flight.get('is_direct') else f"🟡 Transit"
            st.write(f"{route} | {dep_date}")
            st.caption(direct)
        
        with col3:
            price = float(flight.get('price_idr', 0))
            st.markdown(f"**{format_price_idr(price)}**")


# =============================================================================
# SIDEBAR WIDGETS
# =============================================================================

def render_price_sidebar_widget():
    """Widget sidebar untuk quick price info."""
    with st.sidebar:
        st.markdown("### 💰 Harga Terkini")
        
        try:
            packages = get_cached_packages(limit=3)
            if packages:
                st.markdown("**Paket Termurah:**")
                for pkg in packages[:3]:
                    price = format_price_idr(float(pkg.get('price_idr', 0)))
                    name = pkg.get('package_name', '')[:20]
                    st.caption(f"• {name}... - {price}")
            else:
                st.caption("Data harga belum tersedia")
        except Exception as e:
            st.caption("📊 Mode offline")
        
        st.markdown("---")


def render_price_stats_widget():
    """Widget untuk menampilkan statistik harga."""
    try:
        summary = get_cached_price_summary()
        
        if summary.get('packages'):
            pkg = summary['packages']
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Paket Termurah",
                    format_price_idr(float(pkg.get('min_price', 0) or 0))
                )
            with col2:
                st.metric(
                    "Paket Termahal", 
                    format_price_idr(float(pkg.get('max_price', 0) or 0))
                )
        
        # Last update
        if summary.get('last_update'):
            last_update = summary['last_update']
            if isinstance(last_update, datetime):
                st.caption(f"🕐 Update: {last_update.strftime('%d %b %Y, %H:%M')}")
    except Exception:
        st.caption("📊 Statistik tidak tersedia")


# =============================================================================
# FULL PAGE COMPONENTS
# =============================================================================

def render_price_comparison_section():
    """Section perbandingan harga untuk halaman utama."""
    st.markdown("## 💰 Perbandingan Harga Terkini")
    st.caption("Data diupdate otomatis setiap 6 jam")
    
    tab1, tab2, tab3 = st.tabs(["📦 Paket", "🏨 Hotel", "✈️ Penerbangan"])
    
    with tab1:
        try:
            packages = get_cached_packages(limit=8)
            if packages:
                for pkg in packages:
                    render_package_card(pkg)
            else:
                st.info("Belum ada data paket. Menunggu update dari sistem.")
        except Exception as e:
            st.warning(f"Tidak dapat memuat data paket: {e}")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🕋 Makkah")
            try:
                hotels_makkah = get_cached_hotels(city='Makkah', limit=5)
                if hotels_makkah:
                    for hotel in hotels_makkah:
                        render_hotel_card(hotel)
                        st.divider()
                else:
                    st.info("Belum ada data hotel Makkah")
            except Exception:
                st.warning("Data hotel tidak tersedia")

        with col2:
            st.markdown("### 🕌 Madinah")
            try:
                hotels_madinah = get_cached_hotels(city='Madinah', limit=5)
                if hotels_madinah:
                    for hotel in hotels_madinah:
                        render_hotel_card(hotel)
                        st.divider()
                else:
                    st.info("Belum ada data hotel Madinah")
            except Exception:
                st.warning("Data hotel tidak tersedia")
    
    with tab3:
        try:
            flights = get_cached_flights(limit=10)
            if flights:
                for flight in flights[:10]:
                    render_flight_card(flight)
                    st.divider()
            else:
                st.info("Belum ada data penerbangan")
        except Exception:
            st.warning("Data penerbangan tidak tersedia")


# =============================================================================
# SIMULATOR INTEGRATION
# =============================================================================

def get_real_price_defaults() -> Dict:
    """
    Ambil default harga dari database untuk Cost Simulator.
    Fallback ke nilai statis jika database tidak tersedia.
    
    Returns:
        Dictionary dengan default prices
    """
    defaults = {
        'package_min': 23000000,
        'package_max': 55000000,
        'package_avg': 35000000,
        'hotel_makkah_min': 500000,
        'hotel_makkah_max': 5000000,
        'hotel_makkah_avg': 1500000,
        'hotel_madinah_min': 400000,
        'hotel_madinah_max': 3000000,
        'hotel_madinah_avg': 1200000,
        'flight_min': 10000000,
        'flight_max': 20000000,
        'flight_avg': 15000000,
    }
    
    try:
        ranges = get_cached_price_ranges()
        
        if ranges.get('package'):
            defaults['package_min'] = float(ranges['package'].get('min') or defaults['package_min'])
            defaults['package_max'] = float(ranges['package'].get('max') or defaults['package_max'])
            defaults['package_avg'] = float(ranges['package'].get('avg') or defaults['package_avg'])
        
        if ranges.get('hotel_makkah'):
            defaults['hotel_makkah_min'] = float(ranges['hotel_makkah'].get('min') or defaults['hotel_makkah_min'])
            defaults['hotel_makkah_max'] = float(ranges['hotel_makkah'].get('max') or defaults['hotel_makkah_max'])
            defaults['hotel_makkah_avg'] = float(ranges['hotel_makkah'].get('avg') or defaults['hotel_makkah_avg'])
        
        if ranges.get('hotel_madinah'):
            defaults['hotel_madinah_min'] = float(ranges['hotel_madinah'].get('min') or defaults['hotel_madinah_min'])
            defaults['hotel_madinah_max'] = float(ranges['hotel_madinah'].get('max') or defaults['hotel_madinah_max'])
            defaults['hotel_madinah_avg'] = float(ranges['hotel_madinah'].get('avg') or defaults['hotel_madinah_avg'])
        
        if ranges.get('flight'):
            defaults['flight_min'] = float(ranges['flight'].get('min') or defaults['flight_min'])
            defaults['flight_max'] = float(ranges['flight'].get('max') or defaults['flight_max'])
            defaults['flight_avg'] = float(ranges['flight'].get('avg') or defaults['flight_avg'])
    
    except Exception as e:
        # Fallback to static defaults
        pass
    
    return defaults


def render_live_price_indicator():
    """Render indikator harga live di halaman simulator."""
    try:
        summary = get_cached_price_summary()
        last_update = summary.get('last_update')
        
        if last_update:
            if isinstance(last_update, datetime):
                time_str = last_update.strftime('%H:%M')
            else:
                time_str = str(last_update)[:5]
            
            st.success(f"🟢 Harga Live - Terakhir update: {time_str}")
        else:
            st.warning("🟡 Menggunakan harga estimasi")
    except Exception:
        st.info("📊 Mode offline - menggunakan harga estimasi")
