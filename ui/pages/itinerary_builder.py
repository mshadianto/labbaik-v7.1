"""
================================================================================
LABBAIK AI - AI ITINERARY BUILDER
================================================================================
Lokasi: ui/pages/itinerary_builder.py
Fitur: Generate jadwal harian Umrah otomatis dengan estimasi biaya & tips AI
================================================================================
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import json
import re

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

try:
    from services.intelligence.itinerary import compare_transport
    HAS_TRANSPORT_SERVICE = True
except ImportError:
    HAS_TRANSPORT_SERVICE = False

try:
    from services.intelligence.season_calendar import get_season_calendar, is_peak_season, get_booking_recommendation
    HAS_SEASON_CALENDAR = True
except ImportError:
    HAS_SEASON_CALENDAR = False


# =============================================================================
# STYLING
# =============================================================================

ITINERARY_CSS = """
.itinerary-hero {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid #d4af37;
}

.itinerary-hero h1 {
    color: #d4af37;
    margin: 0;
    font-size: 2rem;
}

.itinerary-hero .subtitle {
    color: #b0b0b0;
    font-size: 1rem;
}

.day-card {
    background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #d4af37;
}

.day-header {
    color: #d4af37;
    font-size: 1.3rem;
    font-weight: bold;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.activity-item {
    display: flex;
    align-items: flex-start;
    padding: 0.75rem 0;
    border-bottom: 1px solid #333;
}

.activity-item:last-child {
    border-bottom: none;
}

.activity-time {
    color: #d4af37;
    font-weight: bold;
    min-width: 60px;
    font-size: 0.9rem;
}

.activity-icon {
    font-size: 1.2rem;
    margin: 0 0.75rem;
}

.activity-content {
    flex: 1;
}

.activity-title {
    color: white;
    font-weight: 500;
}

.activity-desc {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin-top: 0.25rem;
}

.activity-tag {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 10px;
    font-size: 0.7rem;
    margin-top: 0.25rem;
}

.tag-ibadah { background: #1a4d1a; color: #4ade80; }
.tag-transport { background: #1a3d4d; color: #60a5fa; }
.tag-rest { background: #4d3d1a; color: #fbbf24; }
.tag-food { background: #4d1a1a; color: #f87171; }
.tag-explore { background: #3d1a4d; color: #c084fc; }

.summary-box {
    background: linear-gradient(135deg, #0d2818 0%, #1a4d2e 100%);
    border: 1px solid #4ade80;
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.tips-box {
    background: linear-gradient(135deg, #2d1a0d 0%, #4d3319 100%);
    border: 1px solid #d4af37;
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.stat-mini {
    text-align: center;
    padding: 1rem;
    background: #2d2d2d;
    border-radius: 10px;
}

.stat-mini .number {
    font-size: 1.5rem;
    color: #d4af37;
    font-weight: bold;
}

.stat-mini .label {
    color: #b0b0b0;
    font-size: 0.8rem;
}

.transport-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1.25rem;
    border: 1px solid #333;
    margin-bottom: 0.75rem;
}
.transport-card.recommended {
    border-color: #4ade80;
    border-width: 2px;
}
.cost-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #333;
    color: #ccc;
}
.cost-row .cost-label { color: #94a3b8; }
.cost-row .cost-value { color: #d4af37; font-weight: bold; }
.peak-badge {
    display: inline-block;
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
    padding: 0.25rem 0.75rem;
    border-radius: 10px;
    font-size: 0.8rem;
    font-weight: bold;
    border: 1px solid rgba(248, 113, 113, 0.3);
    margin-bottom: 0.5rem;
}
"""


# =============================================================================
# ITINERARY DATA & TEMPLATES
# =============================================================================

# Prayer times template (approximate, will vary by season)
PRAYER_TIMES_MAKKAH = {
    "fajr": "05:00",
    "sunrise": "06:30",
    "dhuhr": "12:15",
    "asr": "15:30",
    "maghrib": "18:00",
    "isha": "19:30"
}

PRAYER_TIMES_MADINAH = {
    "fajr": "05:15",
    "sunrise": "06:45",
    "dhuhr": "12:20",
    "asr": "15:35",
    "maghrib": "18:05",
    "isha": "19:35"
}

# Activity templates
ACTIVITIES = {
    # Makkah Activities
    "arrival_jeddah": {
        "title": "Landing di Jeddah Airport",
        "icon": "✈️",
        "duration": 90,
        "tag": "transport",
        "desc": "Imigrasi, ambil bagasi, tukar uang jika perlu"
    },
    "hhr_to_makkah": {
        "title": "Haramain Train ke Makkah",
        "icon": "🚄",
        "duration": 45,
        "tag": "transport",
        "desc": "Kereta cepat dari Jeddah Airport ke Makkah (SAR 75)"
    },
    "hhr_to_madinah": {
        "title": "Haramain Train ke Madinah",
        "icon": "🚄",
        "duration": 150,
        "tag": "transport",
        "desc": "Kereta cepat Makkah ke Madinah (SAR 250, 2.5 jam)"
    },
    "hhr_madinah_jeddah": {
        "title": "Haramain Train ke Jeddah",
        "icon": "🚄",
        "duration": 110,
        "tag": "transport",
        "desc": "Kereta cepat Madinah ke Jeddah Airport (SAR 200)"
    },
    "checkin_hotel_makkah": {
        "title": "Check-in Hotel Makkah",
        "icon": "🏨",
        "duration": 30,
        "tag": "rest",
        "desc": "Simpan bagasi, istirahat sebentar, persiapan ihram"
    },
    "checkin_hotel_madinah": {
        "title": "Check-in Hotel Madinah",
        "icon": "🏨",
        "duration": 30,
        "tag": "rest",
        "desc": "Simpan bagasi, istirahat, siap-siap ke Masjid Nabawi"
    },
    "umrah_full": {
        "title": "UMRAH: Thawaf + Sa'i + Tahallul",
        "icon": "🕋",
        "duration": 180,
        "tag": "ibadah",
        "desc": "Thawaf 7 putaran → Sholat 2 rakaat → Minum Zamzam → Sa'i 7 kali → Potong rambut"
    },
    "thawaf_sunnah": {
        "title": "Thawaf Sunnah",
        "icon": "🕋",
        "duration": 60,
        "tag": "ibadah",
        "desc": "Thawaf sunnah untuk menambah pahala"
    },
    "sholat_fajr": {
        "title": "Sholat Subuh di Masjidil Haram",
        "icon": "🌙",
        "duration": 45,
        "tag": "ibadah",
        "desc": "Sholat Subuh berjamaah"
    },
    "sholat_dhuhr": {
        "title": "Sholat Dzuhur",
        "icon": "☀️",
        "duration": 30,
        "tag": "ibadah",
        "desc": "Sholat Dzuhur berjamaah"
    },
    "sholat_asr": {
        "title": "Sholat Ashar",
        "icon": "🌤️",
        "duration": 30,
        "tag": "ibadah",
        "desc": "Sholat Ashar berjamaah"
    },
    "sholat_maghrib": {
        "title": "Sholat Maghrib",
        "icon": "🌅",
        "duration": 30,
        "tag": "ibadah",
        "desc": "Sholat Maghrib berjamaah"
    },
    "sholat_isha": {
        "title": "Sholat Isya",
        "icon": "🌙",
        "duration": 30,
        "tag": "ibadah",
        "desc": "Sholat Isya berjamaah"
    },
    "rest_morning": {
        "title": "Istirahat Pagi",
        "icon": "😴",
        "duration": 120,
        "tag": "rest",
        "desc": "Tidur/istirahat setelah Subuh"
    },
    "rest_afternoon": {
        "title": "Istirahat Siang",
        "icon": "😴",
        "duration": 90,
        "tag": "rest",
        "desc": "Qailulah (tidur siang sunnah)"
    },
    "rest_night": {
        "title": "Tidur Malam",
        "icon": "😴",
        "duration": 360,
        "tag": "rest",
        "desc": "Istirahat untuk ibadah esok hari"
    },
    "breakfast": {
        "title": "Sarapan",
        "icon": "🍳",
        "duration": 30,
        "tag": "food",
        "desc": "Sarapan di hotel atau sekitar Haram"
    },
    "lunch": {
        "title": "Makan Siang",
        "icon": "🍽️",
        "duration": 45,
        "tag": "food",
        "desc": "Makan siang"
    },
    "dinner": {
        "title": "Makan Malam",
        "icon": "🍽️",
        "duration": 45,
        "tag": "food",
        "desc": "Makan malam"
    },
    "ziarah_makkah": {
        "title": "Ziarah Tempat Bersejarah Makkah",
        "icon": "🏛️",
        "duration": 180,
        "tag": "explore",
        "desc": "Jabal Nur, Gua Hira, Jabal Tsur, Arafah, Mina, Muzdalifah"
    },
    "shopping_makkah": {
        "title": "Belanja Oleh-oleh",
        "icon": "🛍️",
        "duration": 120,
        "tag": "explore",
        "desc": "Belanja di sekitar Masjidil Haram atau mall"
    },
    # Madinah Activities
    "sholat_masjid_nabawi": {
        "title": "Sholat di Masjid Nabawi",
        "icon": "🕌",
        "duration": 45,
        "tag": "ibadah",
        "desc": "Sholat berjamaah di Masjid Nabawi (1000x lipat pahala)"
    },
    "ziarah_raudhah": {
        "title": "Ziarah Raudhah",
        "icon": "💚",
        "duration": 60,
        "tag": "ibadah",
        "desc": "Sholat & berdoa di Raudhah (taman surga)"
    },
    "ziarah_makam_rasul": {
        "title": "Ziarah Makam Rasulullah \u0635\u0644\u0649 \u0627\u0644\u0644\u0647 \u0639\u0644\u064a\u0647 \u0648\u0633\u0644\u0645",
        "icon": "🌹",
        "duration": 30,
        "tag": "ibadah",
        "desc": "Salam kepada Rasulullah, Abu Bakar, dan Umar"
    },
    "ziarah_baqi": {
        "title": "Ziarah Pemakaman Baqi",
        "icon": "🪦",
        "duration": 45,
        "tag": "ibadah",
        "desc": "Ziarah makam sahabat & keluarga Nabi"
    },
    "ziarah_uhud": {
        "title": "Ziarah Jabal Uhud",
        "icon": "⛰️",
        "duration": 120,
        "tag": "explore",
        "desc": "Makam Hamzah, lokasi Perang Uhud"
    },
    "ziarah_quba": {
        "title": "Sholat di Masjid Quba",
        "icon": "🕌",
        "duration": 90,
        "tag": "ibadah",
        "desc": "Masjid pertama dalam Islam (pahala = umrah)"
    },
    "ziarah_qiblatain": {
        "title": "Sholat di Masjid Qiblatain",
        "icon": "🕌",
        "duration": 60,
        "tag": "ibadah",
        "desc": "Masjid dua kiblat"
    },
    "ziarah_7_masjid": {
        "title": "Ziarah 7 Masjid (Sab'ah Masajid)",
        "icon": "🕌",
        "duration": 90,
        "tag": "explore",
        "desc": "Kompleks 7 masjid bersejarah"
    },
    "departure": {
        "title": "Check-out & Berangkat ke Airport",
        "icon": "✈️",
        "duration": 60,
        "tag": "transport",
        "desc": "Persiapan pulang ke tanah air"
    },
    "free_time": {
        "title": "Waktu Bebas",
        "icon": "🚶",
        "duration": 60,
        "tag": "rest",
        "desc": "Eksplorasi bebas atau istirahat"
    }
}

# Route templates
ROUTE_TEMPLATES = {
    "makkah_first": {
        "name": "Makkah Dulu",
        "desc": "Landing Jeddah \u2192 Makkah \u2192 Madinah \u2192 Pulang via Madinah/Jeddah",
        "flow": ["jeddah", "makkah", "madinah", "departure"]
    },
    "madinah_first": {
        "name": "Madinah Dulu",
        "desc": "Landing Jeddah/Madinah \u2192 Madinah \u2192 Makkah \u2192 Pulang via Jeddah",
        "flow": ["arrival", "madinah", "makkah", "departure"]
    }
}

# Ziarah packages
ZIARAH_MAKKAH = [
    {"name": "Jabal Nur & Gua Hira", "duration": 120, "desc": "Tempat turunnya wahyu pertama"},
    {"name": "Jabal Tsur", "duration": 90, "desc": "Tempat persembunyian Nabi saat hijrah"},
    {"name": "Arafah", "duration": 60, "desc": "Lokasi wukuf haji"},
    {"name": "Mina & Muzdalifah", "duration": 90, "desc": "Lokasi mabit & lempar jumrah"},
    {"name": "Pemakaman Ma'la", "duration": 45, "desc": "Makam Khadijah & keluarga Nabi"},
]

ZIARAH_MADINAH = [
    {"name": "Masjid Quba", "duration": 60, "desc": "Masjid pertama, pahala = umrah"},
    {"name": "Jabal Uhud", "duration": 90, "desc": "Lokasi Perang Uhud, makam Hamzah"},
    {"name": "Masjid Qiblatain", "duration": 45, "desc": "Masjid dua kiblat"},
    {"name": "Pemakaman Baqi", "duration": 30, "desc": "Makam sahabat & keluarga Nabi"},
    {"name": "7 Masjid", "duration": 60, "desc": "Kompleks masjid bersejarah"},
    {"name": "Kebun Kurma", "duration": 45, "desc": "Ajwa, kurma favorit Nabi"},
]

DAILY_COSTS = {
    "hemat": {"label": "\U0001f49a Hemat", "meals": 60, "local_transport": 20, "misc": 20, "total": 100},
    "standar": {"label": "\U0001f49b Standar", "meals": 100, "local_transport": 40, "misc": 50, "total": 190},
    "premium": {"label": "\U0001f48e Premium", "meals": 180, "local_transport": 80, "misc": 100, "total": 360},
}

INTERCITY_TRANSPORT = {
    "train": {"label": "\U0001f684 Haramain Train", "icon": "\U0001f684", "makkah_madinah": 200, "jeddah_makkah": 75, "jeddah_madinah": 200, "duration": "2 jam"},
    "bus": {"label": "\U0001f68c SAPTCO Bus", "icon": "\U0001f68c", "makkah_madinah": 120, "jeddah_makkah": 50, "jeddah_madinah": 100, "duration": "5-6 jam"},
    "private_car": {"label": "\U0001f697 Mobil Pribadi", "icon": "\U0001f697", "makkah_madinah": 600, "jeddah_makkah": 200, "jeddah_madinah": 500, "duration": "5 jam"},
    "uber": {"label": "\U0001f4f1 Uber/Careem", "icon": "\U0001f4f1", "makkah_madinah": 450, "jeddah_makkah": 200, "jeddah_madinah": 400, "duration": "5 jam"},
}


# =============================================================================
# SESSION STATE
# =============================================================================

def init_itinerary_state():
    defaults = {
        "itinerary_generated": False,
        "current_itinerary": None,
        "itinerary_start_date": None,
        "itinerary_preferences": {},
        "itinerary_xp_generate": False,
        "itinerary_xp_ai": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def time_add(time_str: str, minutes: int) -> str:
    """Add minutes to time string."""
    h, m = map(int, time_str.split(":"))
    total = h * 60 + m + minutes
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def generate_day_schedule(
    day_num: int,
    location: str,
    day_type: str,
    prayer_times: dict,
    preferences: dict
) -> List[dict]:
    """Generate schedule for a single day."""
    schedule = []

    if day_type == "arrival_makkah":
        # Arrival day - Makkah
        schedule = [
            {"time": "06:00", **ACTIVITIES["arrival_jeddah"]},
            {"time": "07:30", **ACTIVITIES["hhr_to_makkah"]},
            {"time": "08:30", **ACTIVITIES["checkin_hotel_makkah"]},
            {"time": "09:00", **ACTIVITIES["rest_morning"]},
            {"time": "12:15", **ACTIVITIES["sholat_dhuhr"]},
            {"time": "13:00", **ACTIVITIES["lunch"]},
            {"time": "14:00", **ACTIVITIES["rest_afternoon"]},
            {"time": "15:30", **ACTIVITIES["sholat_asr"]},
            {"time": "16:30", **ACTIVITIES["umrah_full"]},
            {"time": "18:00", **ACTIVITIES["sholat_maghrib"]},
            {"time": "19:00", **ACTIVITIES["dinner"]},
            {"time": "19:30", **ACTIVITIES["sholat_isha"]},
            {"time": "21:00", **ACTIVITIES["rest_night"]},
        ]

    elif day_type == "arrival_madinah":
        # Arrival day - Madinah first
        schedule = [
            {"time": "06:00", **ACTIVITIES["arrival_jeddah"]},
            {"time": "07:30", "title": "Haramain Train ke Madinah", "icon": "\U0001f684", "duration": 110, "tag": "transport", "desc": "Kereta cepat dari Jeddah ke Madinah (SAR 200)"},
            {"time": "10:00", **ACTIVITIES["checkin_hotel_madinah"]},
            {"time": "10:30", **ACTIVITIES["rest_morning"]},
            {"time": "12:20", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "13:00", **ACTIVITIES["lunch"]},
            {"time": "14:00", **ACTIVITIES["rest_afternoon"]},
            {"time": "15:35", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "16:30", **ACTIVITIES["ziarah_makam_rasul"]},
            {"time": "18:05", **ACTIVITIES["sholat_maghrib"]},
            {"time": "19:00", **ACTIVITIES["dinner"]},
            {"time": "19:35", **ACTIVITIES["sholat_isha"]},
            {"time": "21:00", **ACTIVITIES["rest_night"]},
        ]

    elif day_type == "makkah_regular":
        # Regular day in Makkah
        schedule = [
            {"time": "04:30", "title": "Bangun & Persiapan", "icon": "\u23f0", "duration": 30, "tag": "rest", "desc": "Wudhu, persiapan ke Haram"},
            {"time": "05:00", **ACTIVITIES["sholat_fajr"]},
            {"time": "06:00", "title": "Thawaf Sunnah / Dzikir", "icon": "\U0001f54b", "duration": 60, "tag": "ibadah", "desc": "Thawaf sunnah atau dzikir pagi"},
            {"time": "07:00", **ACTIVITIES["breakfast"]},
            {"time": "08:00", **ACTIVITIES["rest_morning"]},
            {"time": "12:15", **ACTIVITIES["sholat_dhuhr"]},
            {"time": "13:00", **ACTIVITIES["lunch"]},
            {"time": "14:00", **ACTIVITIES["rest_afternoon"]},
            {"time": "15:30", **ACTIVITIES["sholat_asr"]},
            {"time": "16:30", **ACTIVITIES["thawaf_sunnah"]},
            {"time": "18:00", **ACTIVITIES["sholat_maghrib"]},
            {"time": "19:00", **ACTIVITIES["dinner"]},
            {"time": "19:30", **ACTIVITIES["sholat_isha"]},
            {"time": "20:30", "title": "Ibadah Malam / Tahajud", "icon": "\U0001f319", "duration": 90, "tag": "ibadah", "desc": "Thawaf, dzikir, atau tahajud"},
            {"time": "22:00", **ACTIVITIES["rest_night"]},
        ]

        # Add ziarah option
        if preferences.get("include_ziarah") and day_num % 2 == 0:
            schedule[7] = {"time": "08:00", **ACTIVITIES["ziarah_makkah"]}

    elif day_type == "madinah_regular":
        # Regular day in Madinah
        schedule = [
            {"time": "04:45", "title": "Bangun & Persiapan", "icon": "\u23f0", "duration": 30, "tag": "rest", "desc": "Wudhu, persiapan ke Masjid Nabawi"},
            {"time": "05:15", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "06:00", "title": "Dzikir Pagi / Raudhah", "icon": "\U0001f49a", "duration": 60, "tag": "ibadah", "desc": "Dzikir atau antri Raudhah"},
            {"time": "07:00", **ACTIVITIES["breakfast"]},
            {"time": "08:00", **ACTIVITIES["rest_morning"]},
            {"time": "12:20", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "13:00", **ACTIVITIES["lunch"]},
            {"time": "14:00", **ACTIVITIES["rest_afternoon"]},
            {"time": "15:35", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "16:30", **ACTIVITIES["ziarah_baqi"]},
            {"time": "18:05", **ACTIVITIES["sholat_maghrib"]},
            {"time": "19:00", **ACTIVITIES["dinner"]},
            {"time": "19:35", **ACTIVITIES["sholat_isha"]},
            {"time": "20:30", "title": "Sholat & Dzikir Malam", "icon": "\U0001f319", "duration": 90, "tag": "ibadah", "desc": "Ibadah malam di Masjid Nabawi"},
            {"time": "22:00", **ACTIVITIES["rest_night"]},
        ]

        # Add ziarah variations
        if preferences.get("include_ziarah"):
            if day_num == 1:
                schedule[9] = {"time": "16:30", **ACTIVITIES["ziarah_quba"]}
            elif day_num == 2:
                schedule[9] = {"time": "16:30", **ACTIVITIES["ziarah_uhud"]}

    elif day_type == "travel_makkah_madinah":
        # Travel day Makkah to Madinah
        schedule = [
            {"time": "04:30", "title": "Bangun & Persiapan", "icon": "\u23f0", "duration": 30, "tag": "rest", "desc": "Wudhu, packing"},
            {"time": "05:00", **ACTIVITIES["sholat_fajr"]},
            {"time": "06:00", "title": "Check-out Hotel", "icon": "\U0001f3e8", "duration": 60, "tag": "transport", "desc": "Check-out dan ke stasiun"},
            {"time": "07:00", **ACTIVITIES["hhr_to_madinah"]},
            {"time": "10:00", **ACTIVITIES["checkin_hotel_madinah"]},
            {"time": "10:30", **ACTIVITIES["rest_morning"]},
            {"time": "12:20", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "13:00", **ACTIVITIES["lunch"]},
            {"time": "14:00", **ACTIVITIES["ziarah_makam_rasul"]},
            {"time": "15:35", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "16:30", **ACTIVITIES["free_time"]},
            {"time": "18:05", **ACTIVITIES["sholat_maghrib"]},
            {"time": "19:00", **ACTIVITIES["dinner"]},
            {"time": "19:35", **ACTIVITIES["sholat_isha"]},
            {"time": "21:00", **ACTIVITIES["rest_night"]},
        ]

    elif day_type == "travel_madinah_makkah":
        # Travel day Madinah to Makkah (need ihram!)
        schedule = [
            {"time": "04:45", "title": "Bangun & Persiapan Ihram", "icon": "\u23f0", "duration": 30, "tag": "rest", "desc": "Mandi, pakai ihram, niat umrah"},
            {"time": "05:15", **ACTIVITIES["sholat_masjid_nabawi"]},
            {"time": "06:00", "title": "Check-out & ke Miqat Bir Ali", "icon": "\U0001f3e8", "duration": 90, "tag": "transport", "desc": "Ke Masjid Dzulhulaifah untuk ihram"},
            {"time": "07:30", "title": "Ihram di Bir Ali", "icon": "\U0001f9d5", "duration": 30, "tag": "ibadah", "desc": "Sholat 2 rakaat, niat umrah, mulai talbiyah"},
            {"time": "08:00", **ACTIVITIES["hhr_to_makkah"]},
            {"time": "10:30", **ACTIVITIES["checkin_hotel_makkah"]},
            {"time": "11:00", **ACTIVITIES["rest_morning"]},
            {"time": "12:15", **ACTIVITIES["sholat_dhuhr"]},
            {"time": "13:00", **ACTIVITIES["lunch"]},
            {"time": "14:00", **ACTIVITIES["umrah_full"]},
            {"time": "18:00", **ACTIVITIES["sholat_maghrib"]},
            {"time": "19:00", **ACTIVITIES["dinner"]},
            {"time": "19:30", **ACTIVITIES["sholat_isha"]},
            {"time": "21:00", **ACTIVITIES["rest_night"]},
        ]

    elif day_type == "departure":
        # Departure day
        schedule = [
            {"time": "04:30", "title": "Bangun & Persiapan", "icon": "\u23f0", "duration": 30, "tag": "rest", "desc": "Wudhu, packing final"},
            {"time": "05:00", "title": "Sholat Subuh Terakhir", "icon": "\U0001f319", "duration": 45, "tag": "ibadah", "desc": "Sholat Subuh terakhir di Tanah Suci \U0001f622"},
            {"time": "06:00", **ACTIVITIES["breakfast"]},
            {"time": "07:00", **ACTIVITIES["departure"]},
            {"time": "08:00", "title": "Ke Bandara", "icon": "\U0001f684", "duration": 120, "tag": "transport", "desc": "Perjalanan ke Jeddah Airport"},
            {"time": "10:00", "title": "Check-in Bandara", "icon": "\u2708\ufe0f", "duration": 180, "tag": "transport", "desc": "Check-in, imigrasi, tunggu boarding"},
            {"time": "13:00", "title": "Boarding & Terbang", "icon": "\u2708\ufe0f", "duration": 0, "tag": "transport", "desc": "Pulang ke Indonesia. Alhamdulillah! \U0001f932"},
        ]

    else:
        # Default fallback
        schedule = [
            {"time": "05:00", **ACTIVITIES["sholat_fajr"]},
            {"time": "12:15", **ACTIVITIES["sholat_dhuhr"]},
            {"time": "15:30", **ACTIVITIES["sholat_asr"]},
            {"time": "18:00", **ACTIVITIES["sholat_maghrib"]},
            {"time": "19:30", **ACTIVITIES["sholat_isha"]},
        ]

    return schedule


def generate_full_itinerary(
    duration: int,
    route: str,
    makkah_days: int,
    madinah_days: int,
    preferences: dict
) -> List[dict]:
    """Generate complete itinerary."""
    itinerary = []
    current_day = 1

    if route == "makkah_first":
        # Day 1: Arrival in Makkah
        itinerary.append({
            "day": current_day,
            "date": None,  # Will be filled later
            "location": "Makkah",
            "title": f"Hari {current_day}: Arrival & Umrah",
            "type": "arrival_makkah",
            "schedule": generate_day_schedule(current_day, "makkah", "arrival_makkah", PRAYER_TIMES_MAKKAH, preferences)
        })
        current_day += 1

        # Makkah days
        for i in range(makkah_days - 1):
            itinerary.append({
                "day": current_day,
                "date": None,
                "location": "Makkah",
                "title": f"Hari {current_day}: Ibadah di Makkah",
                "type": "makkah_regular",
                "schedule": generate_day_schedule(current_day, "makkah", "makkah_regular", PRAYER_TIMES_MAKKAH, preferences)
            })
            current_day += 1

        # Travel to Madinah
        itinerary.append({
            "day": current_day,
            "date": None,
            "location": "Makkah \u2192 Madinah",
            "title": f"Hari {current_day}: Perjalanan ke Madinah",
            "type": "travel_makkah_madinah",
            "schedule": generate_day_schedule(current_day, "travel", "travel_makkah_madinah", PRAYER_TIMES_MADINAH, preferences)
        })
        current_day += 1

        # Madinah days
        for i in range(madinah_days - 1):
            itinerary.append({
                "day": current_day,
                "date": None,
                "location": "Madinah",
                "title": f"Hari {current_day}: Ibadah di Madinah",
                "type": "madinah_regular",
                "schedule": generate_day_schedule(i + 1, "madinah", "madinah_regular", PRAYER_TIMES_MADINAH, preferences)
            })
            current_day += 1

        # Departure
        itinerary.append({
            "day": current_day,
            "date": None,
            "location": "Madinah \u2192 Indonesia",
            "title": f"Hari {current_day}: Pulang ke Tanah Air",
            "type": "departure",
            "schedule": generate_day_schedule(current_day, "departure", "departure", PRAYER_TIMES_MADINAH, preferences)
        })

    else:  # madinah_first
        # Day 1: Arrival in Madinah
        itinerary.append({
            "day": current_day,
            "date": None,
            "location": "Madinah",
            "title": f"Hari {current_day}: Arrival Madinah",
            "type": "arrival_madinah",
            "schedule": generate_day_schedule(current_day, "madinah", "arrival_madinah", PRAYER_TIMES_MADINAH, preferences)
        })
        current_day += 1

        # Madinah days
        for i in range(madinah_days - 1):
            itinerary.append({
                "day": current_day,
                "date": None,
                "location": "Madinah",
                "title": f"Hari {current_day}: Ibadah di Madinah",
                "type": "madinah_regular",
                "schedule": generate_day_schedule(i + 1, "madinah", "madinah_regular", PRAYER_TIMES_MADINAH, preferences)
            })
            current_day += 1

        # Travel to Makkah (with Ihram!)
        itinerary.append({
            "day": current_day,
            "date": None,
            "location": "Madinah \u2192 Makkah",
            "title": f"Hari {current_day}: Ihram & Perjalanan ke Makkah",
            "type": "travel_madinah_makkah",
            "schedule": generate_day_schedule(current_day, "travel", "travel_madinah_makkah", PRAYER_TIMES_MAKKAH, preferences)
        })
        current_day += 1

        # Makkah days
        for i in range(makkah_days - 1):
            itinerary.append({
                "day": current_day,
                "date": None,
                "location": "Makkah",
                "title": f"Hari {current_day}: Ibadah di Makkah",
                "type": "makkah_regular",
                "schedule": generate_day_schedule(current_day, "makkah", "makkah_regular", PRAYER_TIMES_MAKKAH, preferences)
            })
            current_day += 1

        # Departure
        itinerary.append({
            "day": current_day,
            "date": None,
            "location": "Makkah \u2192 Indonesia",
            "title": f"Hari {current_day}: Pulang ke Tanah Air",
            "type": "departure",
            "schedule": generate_day_schedule(current_day, "departure", "departure", PRAYER_TIMES_MAKKAH, preferences)
        })

    return itinerary


def export_to_text(itinerary: List[dict], start_date: date) -> str:
    """Export itinerary to plain text format."""
    output = []
    output.append("=" * 50)
    output.append("\U0001f54b JADWAL UMRAH - Generated by LABBAIK.AI")
    output.append("=" * 50)
    output.append("")

    for day in itinerary:
        day_date = start_date + timedelta(days=day["day"] - 1)
        output.append(f"\U0001f4c5 {day['title']}")
        output.append(f"   {day_date.strftime('%A, %d %B %Y')} | \U0001f4cd {day['location']}")
        output.append("-" * 40)

        for item in day["schedule"]:
            output.append(f"   {item['time']}  {item['icon']} {item['title']}")
            if item.get('desc'):
                output.append(f"          \u2514\u2500 {item['desc']}")

        output.append("")

    output.append("=" * 50)
    output.append("Generated by LABBAIK.AI - labbaik-umrahplanner.streamlit.app")
    output.append("\u26a0\ufe0f Jadwal bersifat estimasi, sesuaikan dengan kondisi aktual")
    output.append("=" * 50)

    return "\n".join(output)


def export_to_whatsapp(itinerary: List[dict], start_date: date) -> str:
    """Export itinerary to WhatsApp-friendly format."""
    output = []
    output.append("\U0001f54b *JADWAL UMRAH*")
    output.append("_Generated by LABBAIK.AI_")
    output.append("")

    for day in itinerary:
        day_date = start_date + timedelta(days=day["day"] - 1)
        output.append(f"*{day['title']}*")
        output.append(f"\U0001f4cd {day['location']} | {day_date.strftime('%d/%m/%Y')}")
        output.append("")

        for item in day["schedule"]:
            output.append(f"\u23f0 {item['time']} {item['icon']} {item['title']}")

        output.append("")
        output.append("\u2500" * 20)
        output.append("")

    output.append("\U0001f517 labbaik-umrahplanner.streamlit.app")

    return "\n".join(output)


def _markdown_to_html_simple(text: str) -> str:
    """Simple markdown to HTML for AI response display."""
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br/>")
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        if line.startswith("- ") or line.startswith("* "):
            line = f"&bull; {line[2:]}"
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            line = f"<strong>{match.group(1)}.</strong> {line[match.end():]}"
        html_lines.append(f"<div style='margin-bottom:0.3rem;'>{line}</div>")
    return "\n".join(html_lines)


def calculate_trip_cost(itinerary, budget_level, transport_mode):
    """Calculate estimated trip cost based on budget level and transport."""
    daily = DAILY_COSTS.get(budget_level, DAILY_COSTS["standar"])
    transport = INTERCITY_TRANSPORT.get(transport_mode, INTERCITY_TRANSPORT["train"])
    total_days = len(itinerary)
    travel_days = sum(1 for d in itinerary if "\u2192" in d.get("location", ""))
    stay_days = total_days - travel_days
    daily_total = stay_days * daily["total"]
    transport_total = 0
    for day in itinerary:
        loc = day.get("location", "")
        if "Makkah \u2192 Madinah" in loc or "Madinah \u2192 Makkah" in loc:
            transport_total += transport["makkah_madinah"]
        elif "Indonesia" in loc:
            transport_total += transport["jeddah_makkah"]
    if not transport_total:
        transport_total = transport["jeddah_makkah"]
    total = daily_total + transport_total
    return {
        "daily_cost": daily["total"],
        "daily_breakdown": {
            "meals": daily["meals"],
            "local_transport": daily["local_transport"],
            "misc": daily["misc"],
        },
        "stay_days": stay_days,
        "travel_days": travel_days,
        "daily_subtotal": daily_total,
        "transport_subtotal": transport_total,
        "total_sar": total,
        "budget_label": daily["label"],
        "transport_label": transport["label"],
    }


def get_season_info(start_date, duration):
    """Get season information for the trip dates."""
    if not HAS_SEASON_CALENDAR:
        return None
    try:
        cal = get_season_calendar()
        end_date = start_date + timedelta(days=duration)
        weight = cal.get_weight_range(start_date, end_date)
        season = cal.get_season(start_date)
        rec = cal.get_booking_recommendation(start_date)
        return {
            "is_peak": weight >= 1.5,
            "weight": weight,
            "season_name": season.name if season else "Regular",
            "recommendation": rec,
        }
    except Exception:
        return None


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_hero():
    """Render hero section."""
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, ITINERARY_CSS)
    st.markdown(
        '<div class="itinerary-hero">'
        '<h1>\U0001f5d3\ufe0f Smart Itinerary Builder</h1>'
        '<p class="subtitle">Generate jadwal Umrah harian dengan estimasi biaya & tips AI</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_day_schedule(day: dict, day_date: date):
    """Render a single day's schedule."""
    st.markdown(
        f'<div class="day-card">'
        f'<div class="day-header">'
        f'\U0001f4c5 {day["title"]} \u2014 {day_date.strftime("%A, %d %b %Y")}'
        f'<span style="margin-left:auto;font-size:0.9rem;color:#b0b0b0;">\U0001f4cd {day["location"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for item in day["schedule"]:
        tag_class = f"tag-{item.get('tag', 'rest')}"
        tag_label = {
            "ibadah": "Ibadah",
            "transport": "Transport",
            "rest": "Istirahat",
            "food": "Makan",
            "explore": "Ziarah"
        }.get(item.get('tag'), '')

        st.markdown(
            f'<div class="activity-item">'
            f'<span class="activity-time">{item["time"]}</span>'
            f'<span class="activity-icon">{item["icon"]}</span>'
            f'<div class="activity-content">'
            f'<div class="activity-title">{item["title"]}</div>'
            f'<div class="activity-desc">{item.get("desc", "")}</div>'
            f'<span class="activity-tag {tag_class}">{tag_label}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_itinerary_summary(itinerary: List[dict], preferences: dict):
    """Render itinerary summary."""
    total_days = len(itinerary)
    makkah_days = sum(1 for d in itinerary if "Makkah" in d["location"] and "\u2192" not in d["location"])
    madinah_days = sum(1 for d in itinerary if "Madinah" in d["location"] and "\u2192" not in d["location"])
    travel_days = sum(1 for d in itinerary if "\u2192" in d["location"])

    st.markdown(
        '<div class="summary-box">'
        '<h3 style="color:#4ade80;margin-top:0;">\U0001f4ca Ringkasan Itinerary</h3>'
        '</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    with cols[0]:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">{total_days}</div>'
            f'<div class="label">Total Hari</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with cols[1]:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">{makkah_days}</div>'
            f'<div class="label">Hari di Makkah</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with cols[2]:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">{madinah_days}</div>'
            f'<div class="label">Hari di Madinah</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with cols[3]:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">{travel_days}</div>'
            f'<div class="label">Hari Perjalanan</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_tips():
    """Render tips section."""
    st.markdown(
        '<div class="tips-box">'
        '<h3 style="color:#d4af37;margin-top:0;">\U0001f4a1 Tips Penting</h3>'
        '</div>',
        unsafe_allow_html=True,
    )

    tips = [
        "\u23f0 **Waktu sholat bersifat estimasi** - cek waktu aktual via aplikasi Muslim Pro atau azan masjid",
        "\U0001f6b6 **Jarak hotel ke Haram** sangat mempengaruhi waktu tempuh, sesuaikan jadwal",
        "\U0001f634 **Jangan skip istirahat** - fisik yang fit = ibadah lebih khusyuk",
        "\U0001f964 **Minum banyak air** - cuaca panas, dehidrasi berbahaya",
        "\U0001f4f1 **Download peta offline** - WiFi tidak selalu tersedia",
        "\U0001f550 **Datang lebih awal** untuk sholat Jumat (minimal 2 jam sebelum)",
    ]

    for tip in tips:
        st.markdown(tip)


def render_season_warning(start_date, duration):
    """Show peak season badge and warning if applicable."""
    info = get_season_info(start_date, duration)
    if info is None:
        return
    if info["is_peak"]:
        st.markdown(
            f'<span class="peak-badge">\U0001f525 Peak Season: {info["season_name"]} (x{info["weight"]:.1f})</span>',
            unsafe_allow_html=True,
        )
        rec = info.get("recommendation")
        if rec and isinstance(rec, dict):
            msg = rec.get("message", "")
            if msg:
                st.warning(f"\u26a0\ufe0f **Peak Season Alert**\n\n{msg}")
        else:
            st.warning(
                "\u26a0\ufe0f **Peak Season Alert**\n\n"
                "Perjalanan Anda jatuh di musim ramai. "
                "Booking hotel & tiket jauh-jauh hari untuk harga terbaik."
            )


def render_cost_estimate(itinerary, preferences):
    """Render cost estimation section with selectors and breakdown."""
    st.markdown("#### \U0001f4b0 Estimasi Biaya Harian")

    col_b, col_t = st.columns(2)
    with col_b:
        budget_level = st.selectbox(
            "Level Budget",
            options=["hemat", "standar", "premium"],
            format_func=lambda x: DAILY_COSTS[x]["label"],
            index=["hemat", "standar", "premium"].index(preferences.get("budget_level", "standar")),
            key="cost_budget_selector",
        )
    with col_t:
        transport_mode = st.selectbox(
            "Transport Antar Kota",
            options=["train", "bus", "private_car", "uber"],
            format_func=lambda x: INTERCITY_TRANSPORT[x]["label"],
            key="cost_transport_selector",
        )

    cost = calculate_trip_cost(itinerary, budget_level, transport_mode)

    # Metric cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">SAR {cost["total_sar"]:,.0f}</div>'
            f'<div class="label">Total Estimasi</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">SAR {cost["daily_cost"]:,.0f}</div>'
            f'<div class="label">Per Hari</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">SAR {cost["transport_subtotal"]:,.0f}</div>'
            f'<div class="label">Transport</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="number">{cost["stay_days"]}+{cost["travel_days"]}</div>'
            f'<div class="label">Menginap + Travel</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Detailed breakdown
    st.markdown("##### Rincian Biaya")
    breakdown_items = [
        ("Makan/hari", f'SAR {cost["daily_breakdown"]["meals"]}'),
        ("Transport lokal/hari", f'SAR {cost["daily_breakdown"]["local_transport"]}'),
        ("Lain-lain/hari", f'SAR {cost["daily_breakdown"]["misc"]}'),
        ("Subtotal harian", f'SAR {cost["daily_cost"]} x {cost["stay_days"]} hari = SAR {cost["daily_subtotal"]:,.0f}'),
        ("Transport antar kota", f'SAR {cost["transport_subtotal"]:,.0f}'),
        ("TOTAL", f'SAR {cost["total_sar"]:,.0f}'),
    ]
    for label, value in breakdown_items:
        st.markdown(
            f'<div class="cost-row">'
            f'<span class="cost-label">{label}</span>'
            f'<span class="cost-value">{value}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.caption(
        "\u26a0\ufe0f Estimasi **belum termasuk**: tiket pesawat, hotel, visa, "
        "asuransi, handling, dan biaya travel agent."
    )


def render_transport_comparison(start_date, route):
    """Render intercity transport comparison."""
    st.markdown("#### \U0001f68c Perbandingan Transport Antar Kota")

    # Determine cities based on route
    if route == "makkah_first":
        from_city = "MAKKAH"
        to_city = "MADINAH"
        route_label = "Makkah \u2192 Madinah"
    else:
        from_city = "MADINAH"
        to_city = "MAKKAH"
        route_label = "Madinah \u2192 Makkah"

    st.markdown(f"**Rute: {route_label}**")

    options = None
    if HAS_TRANSPORT_SERVICE:
        try:
            options = compare_transport(from_city, to_city, start_date)
        except Exception:
            options = None

    if options:
        for opt in options:
            css_class = "transport-card recommended" if opt.get("recommended") else "transport-card"
            rec_badge = ' <span style="color:#4ade80;font-weight:bold;">\u2705 Recommended</span>' if opt.get("recommended") else ""
            duration_h = opt["duration_min"] // 60
            duration_m = opt["duration_min"] % 60
            dur_str = f"{duration_h}j {duration_m}m" if duration_h else f"{duration_m}m"
            total_h = opt["total_time_min"] // 60
            total_m = opt["total_time_min"] % 60
            total_str = f"{total_h}j {total_m}m" if total_h else f"{total_m}m"
            notes_str = ", ".join(opt.get("notes", []))
            notes_html = f'<div style="color:#b0b0b0;font-size:0.8rem;margin-top:0.5rem;">{notes_str}</div>' if notes_str else ""

            st.markdown(
                f'<div class="{css_class}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">'
                f'<strong style="color:#fff;font-size:1.1rem;">{opt["operator"]}</strong>'
                f'{rec_badge}'
                f'</div>'
                f'<div class="cost-row"><span class="cost-label">Mode</span><span class="cost-value">{opt["mode"]}</span></div>'
                f'<div class="cost-row"><span class="cost-label">Durasi perjalanan</span><span class="cost-value">{dur_str}</span></div>'
                f'<div class="cost-row"><span class="cost-label">Buffer waktu</span><span class="cost-value">{opt["buffer_min"]} menit</span></div>'
                f'<div class="cost-row"><span class="cost-label">Total waktu</span><span class="cost-value">{total_str}</span></div>'
                f'<div class="cost-row"><span class="cost-label">Harga</span><span class="cost-value">SAR {opt["price_sar"]:.0f} ({opt["price_range"]})</span></div>'
                f'<div class="cost-row"><span class="cost-label">Frekuensi</span><span class="cost-value">{opt["frequency"]}</span></div>'
                f'<div class="cost-row"><span class="cost-label">Stasiun</span><span class="cost-value">{opt["station_from"]} \u2192 {opt["station_to"]}</span></div>'
                f'{notes_html}'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        # Fallback to static data
        st.info("\U0001f4cb Menggunakan data referensi statis (service transport tidak tersedia)")
        for key, t in INTERCITY_TRANSPORT.items():
            price = t["makkah_madinah"]
            st.markdown(
                f'<div class="transport-card">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">'
                f'<strong style="color:#fff;font-size:1.1rem;">{t["label"]}</strong>'
                f'</div>'
                f'<div class="cost-row"><span class="cost-label">Harga {route_label}</span><span class="cost-value">SAR {price}</span></div>'
                f'<div class="cost-row"><span class="cost-label">Estimasi durasi</span><span class="cost-value">{t["duration"]}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_ai_analysis(itinerary, preferences, start_date):
    """Render AI analysis section with button-triggered analysis."""
    st.markdown("#### \U0001f9e0 Analisis AI untuk Itinerary Anda")

    if st.button("\U0001f9e0 Analisis Itinerary Saya", use_container_width=True):
        total_days = len(itinerary)
        makkah_days = sum(1 for d in itinerary if "Makkah" in d["location"] and "\u2192" not in d["location"])
        madinah_days = sum(1 for d in itinerary if "Madinah" in d["location"] and "\u2192" not in d["location"])
        route = preferences.get("route", "makkah_first")
        pace = preferences.get("pace", "normal")
        route_label = "Makkah dulu" if route == "makkah_first" else "Madinah dulu"

        season_context = ""
        info = get_season_info(start_date, total_days)
        if info and info["is_peak"]:
            season_context = f"\nPerjalanan ini jatuh di musim ramai ({info['season_name']}, bobot {info['weight']:.1f}x). "

        prompt = (
            f"Saya merencanakan Umrah {total_days} hari, "
            f"rute {route_label}, {makkah_days} hari di Makkah dan {madinah_days} hari di Madinah. "
            f"Pace ibadah: {pace}. Tanggal berangkat: {start_date.strftime('%d %B %Y')}."
            f"{season_context}\n\n"
            "Berikan analisis singkat:\n"
            "1. Apakah pembagian hari sudah optimal?\n"
            "2. Tips khusus untuk durasi dan rute ini\n"
            "3. Hal yang perlu diwaspadai\n"
            "4. Rekomendasi ibadah sunnah yang bisa ditambahkan\n\n"
            "Jawab dalam Bahasa Indonesia, singkat dan praktis."
        )

        system_prompt = (
            "Kamu adalah konsultan perjalanan Umrah berpengalaman. "
            "Berikan saran praktis dan actionable untuk jamaah Indonesia. "
            "Gunakan Bahasa Indonesia yang mudah dipahami."
        )

        with st.spinner("AI sedang menganalisis itinerary Anda..."):
            response = ai_complete(prompt, system_prompt=system_prompt, max_tokens=1024)

        if response:
            html_content = _markdown_to_html_simple(response)
            st.markdown(
                f'<div class="ai-card" role="status" aria-live="polite">'
                f'<h4 style="color:#4ade80;margin-top:0;">\U0001f9e0 Analisis AI</h4>'
                f'{html_content}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if not st.session_state.itinerary_xp_ai:
                st.session_state.itinerary_xp_ai = True
                add_xp_safe(20, "AI analisis itinerary Umrah")
        else:
            st.info(
                "\U0001f4a1 **Tips Umum Itinerary Umrah:**\n\n"
                "- Prioritaskan ibadah wajib (sholat 5 waktu berjamaah) di atas semua aktivitas\n"
                "- Jangan terlalu padat di hari pertama \u2014 tubuh perlu adaptasi\n"
                "- Manfaatkan waktu setelah Subuh untuk thawaf (paling sepi)\n"
                "- Siapkan buffer waktu untuk antrian Raudhah di Madinah\n"
                "- Bawa bekal air dan snack untuk perjalanan antar kota"
            )


# =============================================================================
# MAIN PAGE FUNCTION
# =============================================================================

def render_itinerary_builder_page():
    """Main entry point for Itinerary Builder page."""
    try:
        from services.analytics import track_page
        track_page("itinerary")
    except Exception:
        pass

    init_itinerary_state()
    render_hero()

    # CONFIG FORM
    with st.container(border=True):
        st.markdown("### \u2699\ufe0f Konfigurasi Perjalanan")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "\U0001f4c5 Tanggal Keberangkatan",
                value=date.today() + timedelta(days=30),
                min_value=date.today(),
            )
            duration = st.slider(
                "\u23f1\ufe0f Total Durasi (hari)",
                min_value=7,
                max_value=21,
                value=9,
            )
            route = st.selectbox(
                "\U0001f6e4\ufe0f Rute Perjalanan",
                options=["makkah_first", "madinah_first"],
                format_func=lambda x: "Makkah Dulu \u2192 Madinah" if x == "makkah_first" else "Madinah Dulu \u2192 Makkah",
            )
        with col2:
            default_makkah = (duration - 2) * 2 // 3 + 1
            makkah_days = st.slider(
                "\U0001f54b Hari di Makkah",
                min_value=3,
                max_value=duration - 4,
                value=min(default_makkah, duration - 4),
            )
            madinah_days = duration - makkah_days - 1
            st.info(f"\U0001f54c Hari di Madinah: **{madinah_days} hari** (otomatis)")
            include_ziarah = st.checkbox("\U0001f3db\ufe0f Include Ziarah Bersejarah", value=True)

        # New options row
        col3, col4 = st.columns(2)
        with col3:
            pace = st.select_slider(
                "\U0001f6b6 Pace Ibadah",
                options=["santai", "normal", "intensif"],
                value="normal",
            )
        with col4:
            budget_level = st.selectbox(
                "\U0001f4b0 Level Budget",
                options=["hemat", "standar", "premium"],
                format_func=lambda x: DAILY_COSTS[x]["label"],
                index=1,
            )

        render_season_warning(start_date, duration)

        preferences = {
            "include_ziarah": include_ziarah,
            "pace": pace,
            "route": route,
            "budget_level": budget_level,
        }

        if st.button("\U0001f680 Generate Itinerary", use_container_width=True, type="primary"):
            with st.spinner("Menyusun jadwal terbaik untuk Anda..."):
                itinerary = generate_full_itinerary(
                    duration=duration,
                    route=route,
                    makkah_days=makkah_days,
                    madinah_days=madinah_days,
                    preferences=preferences,
                )
                st.session_state.current_itinerary = itinerary
                st.session_state.itinerary_start_date = start_date
                st.session_state.itinerary_preferences = preferences
                st.session_state.itinerary_generated = True
                if not st.session_state.itinerary_xp_generate:
                    st.session_state.itinerary_xp_generate = True
                    add_xp_safe(30, "Generate itinerary Umrah")
                st.rerun()

    # DISPLAY RESULTS
    if st.session_state.itinerary_generated and st.session_state.current_itinerary:
        itinerary = st.session_state.current_itinerary
        start_date = st.session_state.itinerary_start_date
        prefs = st.session_state.itinerary_preferences

        st.divider()
        render_itinerary_summary(itinerary, prefs)
        st.divider()

        tab_jadwal, tab_biaya, tab_ai = st.tabs(
            ["\U0001f4cb Jadwal Harian", "\U0001f4b0 Estimasi Biaya", "\U0001f9e0 Analisis AI"]
        )

        with tab_jadwal:
            # Export
            st.markdown("#### \U0001f4e4 Export Jadwal")
            exp1, exp2, exp3 = st.columns(3)
            with exp1:
                st.download_button(
                    "\U0001f4c4 Download TXT",
                    data=export_to_text(itinerary, start_date),
                    file_name=f"jadwal_umrah_{start_date.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with exp2:
                st.download_button(
                    "\U0001f4f1 Format WhatsApp",
                    data=export_to_whatsapp(itinerary, start_date),
                    file_name=f"jadwal_umrah_wa_{start_date.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with exp3:
                st.download_button(
                    "\U0001f4be Download JSON",
                    data=json.dumps(itinerary, indent=2, default=str),
                    file_name=f"jadwal_umrah_{start_date.strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            if st.button("\U0001f4cb Salin ke Clipboard", key="copy_itinerary", use_container_width=True):
                wa_text = export_to_whatsapp(itinerary, start_date)
                st.code(wa_text, language=None)
                st.caption("Salin teks di atas dan tempel ke WhatsApp atau media lain.")

            st.divider()
            view_mode = st.radio("Tampilan:", ["\U0001f4d1 Semua Hari", "\U0001f50d Per Hari"], horizontal=True)
            if view_mode == "\U0001f4d1 Semua Hari":
                for day in itinerary:
                    day_date = start_date + timedelta(days=day["day"] - 1)
                    render_day_schedule(day, day_date)
            else:
                day_options = [f'Hari {d["day"]}: {d["location"]}' for d in itinerary]
                selected_day = st.selectbox("Pilih Hari:", day_options)
                day_idx = day_options.index(selected_day)
                day = itinerary[day_idx]
                day_date = start_date + timedelta(days=day["day"] - 1)
                render_day_schedule(day, day_date)

            st.divider()
            render_tips()

        with tab_biaya:
            render_cost_estimate(itinerary, prefs)
            st.divider()
            render_transport_comparison(start_date, prefs.get("route", "makkah_first"))

        with tab_ai:
            render_ai_analysis(itinerary, prefs, start_date)

        st.divider()
        if st.button("\U0001f504 Buat Jadwal Baru", use_container_width=True):
            st.session_state.itinerary_generated = False
            st.session_state.current_itinerary = None
            st.rerun()

    # Disclaimer
    st.divider()
    st.warning(
        "\u26a0\ufe0f **DYOR - Do Your Own Research**\n\n"
        "Jadwal ini bersifat **estimasi** dan dibuat otomatis. "
        "Waktu sholat, durasi aktivitas, dan kondisi di lapangan dapat berbeda.\n\n"
        "Selalu sesuaikan dengan kondisi fisik, jarak hotel, musim, dan jadwal penerbangan aktual.\n\n"
        "**LABBAIK AI tidak bertanggung jawab atas perubahan jadwal di lapangan.**"
    )


__all__ = ["render_itinerary_builder_page"]
