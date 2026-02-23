"""
================================================================================
LABBAIK AI - DOA & DZIKIR PLAYER
================================================================================
Lokasi: ui/pages/doa_player.py
Fitur: Audio playback for Umrah duas with:
- Arabic text with proper RTL display
- Latin transliteration
- Indonesian translation
- Audio playback (TTS or pre-recorded)
- Bookmark/favorites system
- Voice chat for doa questions
- AI-powered doa explanations
- Gamification (XP rewards)

Uses Web Speech API for TTS when audio files not available.
================================================================================
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import base64
import io
import os
import tempfile

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

# Try to import TTS libraries
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    import edge_tts
    import asyncio
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

# Arabic voice options (Edge TTS)
VOICE_OPTIONS = {
    "pria": "ar-SA-HamedNeural",      # Male Saudi Arabic
    "wanita": "ar-SA-ZariyahNeural",  # Female Saudi Arabic
}

DEFAULT_VOICE = "wanita"


# =============================================================================
# STYLING
# =============================================================================

DOA_CSS = """
/* Hero override for doa page */
.doa-hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a3a 50%, #1b2a4a 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid #d4af37;
    position: relative;
    overflow: hidden;
}

.doa-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.06) 0%, transparent 70%);
    animation: doa-pulse 4s ease-in-out infinite;
    pointer-events: none;
}

@keyframes doa-pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}

.doa-hero h1 {
    color: #d4af37;
    margin: 0;
    font-size: 2.2rem;
    position: relative;
    z-index: 1;
}

.doa-hero .subtitle {
    color: #b0b0b0;
    font-size: 1rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

.doa-hero .bismillah {
    font-family: 'Amiri', serif;
    color: #d4af37;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

.doa-hero .stat-row {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-top: 1.5rem;
    position: relative;
    z-index: 1;
    flex-wrap: wrap;
}

.doa-hero .stat-item {
    text-align: center;
    padding: 0.75rem 1.5rem;
    background: rgba(212, 175, 55, 0.1);
    border-radius: 12px;
    border: 1px solid rgba(212, 175, 55, 0.3);
    min-width: 110px;
}

.doa-hero .stat-number {
    font-size: 1.6rem;
    font-weight: bold;
    color: #d4af37;
}

.doa-hero .stat-label {
    color: #b0b0b0;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

/* Arabic text display card */
.arabic-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    border: 1px solid #d4af37;
}

.arabic-card .arabic-text {
    direction: rtl;
    text-align: right;
    font-family: 'Amiri', 'Traditional Arabic', serif;
    font-size: 2rem;
    line-height: 2.5;
    color: #d4af37;
}

/* Doa player card */
.doa-player-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid #333;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.doa-player-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.doa-player-card .doa-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.doa-player-card .doa-name {
    color: #d4af37;
    font-size: 1.2rem;
    font-weight: bold;
    margin: 0;
}

.doa-player-card .doa-meta {
    color: #b0b0b0;
    font-size: 0.8rem;
}

.doa-player-card .latin-text {
    color: #b0b0b0;
    font-style: italic;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
}

.doa-player-card .translation-text {
    color: #eee;
    font-size: 1rem;
}

/* Wajib badge */
.wajib-badge {
    display: inline-block;
    background: #4a1a1a;
    color: #f87171;
    padding: 0.2rem 0.75rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
    border: 1px solid rgba(248, 113, 113, 0.3);
}

/* Category stat cards */
.cat-stat-card {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    border: 1px solid #333;
}

.cat-stat-card .number {
    font-size: 1.5rem;
    font-weight: bold;
}

.cat-stat-card .label {
    color: #b0b0b0;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

/* Voice chat container */
.voice-chat-box {
    background: linear-gradient(135deg, #0f3460, #16213e);
    padding: 1rem;
    border-radius: 15px;
    border: 1px solid #00d9ff;
}

/* Quick reference step */
.step-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    border-left: 3px solid #d4af37;
}

.step-card .step-num {
    color: #d4af37;
    font-weight: bold;
    font-size: 1.1rem;
}

.step-card .step-title {
    color: #eee;
    font-weight: bold;
}

.step-card .step-when {
    color: #b0b0b0;
    font-size: 0.85rem;
}

/* Mini widget */
.doa-mini-widget {
    background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
    padding: 1rem;
    border-radius: 15px;
    border: 1px solid #d4af37;
}

.doa-mini-widget .mini-label {
    color: #d4af37;
    font-size: 0.8rem;
}

.doa-mini-widget .mini-value {
    color: white;
    font-weight: bold;
}

.doa-mini-widget .mini-hint {
    color: #b0b0b0;
    font-size: 0.75rem;
}
"""


# =============================================================================
# DOA DATABASE
# =============================================================================

@dataclass
class Doa:
    """Doa/prayer data structure."""
    id: str
    name: str
    arabic: str
    latin: str
    translation: str
    category: str
    when_to_read: str
    audio_url: str = ""  # Optional audio file URL
    is_wajib: bool = False


class DoaCategory(str, Enum):
    PERJALANAN = "perjalanan"
    IHRAM = "ihram"
    TAWAF = "tawaf"
    SAI = "sai"
    MASJID = "masjid"
    HARIAN = "harian"
    ZIARAH = "ziarah"


# Complete Umrah Doa Database
UMRAH_DOAS: List[Doa] = [
    # PERJALANAN
    Doa(
        id="doa_001",
        name="Doa Keluar Rumah",
        arabic="\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0647\u0650 \u062a\u064e\u0648\u064e\u0643\u0651\u064e\u0644\u0652\u062a\u064f \u0639\u064e\u0644\u064e\u0649 \u0627\u0644\u0644\u0647\u0650 \u0648\u064e\u0644\u0627\u064e \u062d\u064e\u0648\u0652\u0644\u064e \u0648\u064e\u0644\u0627\u064e \u0642\u064f\u0648\u0651\u064e\u0629\u064e \u0625\u0650\u0644\u0627\u0651\u064e \u0628\u0650\u0627\u0644\u0644\u0647\u0650",
        latin="Bismillahi tawakkaltu 'alallah, wa laa hawla wa laa quwwata illa billah",
        translation="Dengan nama Allah, aku bertawakal kepada Allah. Tidak ada daya dan kekuatan kecuali dengan pertolongan Allah.",
        category=DoaCategory.PERJALANAN,
        when_to_read="Saat keluar rumah menuju bandara"
    ),
    Doa(
        id="doa_002",
        name="Doa Naik Kendaraan",
        arabic="\u0633\u064f\u0628\u0652\u062d\u064e\u0627\u0646\u064e \u0627\u0644\u0651\u064e\u0630\u0650\u064a \u0633\u064e\u062e\u0651\u064e\u0631\u064e \u0644\u064e\u0646\u064e\u0627 \u0647\u064e\u0630\u064e\u0627 \u0648\u064e\u0645\u064e\u0627 \u0643\u064f\u0646\u0651\u064e\u0627 \u0644\u064e\u0647\u064f \u0645\u064f\u0642\u0652\u0631\u0650\u0646\u0650\u064a\u0646\u064e \u0648\u064e\u0625\u0650\u0646\u0651\u064e\u0627 \u0625\u0650\u0644\u064e\u0649 \u0631\u064e\u0628\u0651\u0650\u0646\u064e\u0627 \u0644\u064e\u0645\u064f\u0646\u0642\u064e\u0644\u0650\u0628\u064f\u0648\u0646\u064e",
        latin="Subhanalladzi sakhkhara lana hadza wa ma kunna lahu muqrinin, wa inna ila rabbina lamunqalibun",
        translation="Maha Suci Allah yang telah menundukkan ini untuk kami, padahal kami tidak mampu menguasainya. Dan sesungguhnya kami akan kembali kepada Tuhan kami.",
        category=DoaCategory.PERJALANAN,
        when_to_read="Saat naik pesawat/kendaraan"
    ),
    Doa(
        id="doa_003",
        name="Doa Safar (Perjalanan)",
        arabic="\u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0625\u0650\u0646\u0651\u064e\u0627 \u0646\u064e\u0633\u0652\u0623\u064e\u0644\u064f\u0643\u064e \u0641\u0650\u064a \u0633\u064e\u0641\u064e\u0631\u0650\u0646\u064e\u0627 \u0647\u064e\u0630\u064e\u0627 \u0627\u0644\u0652\u0628\u0650\u0631\u0651\u064e \u0648\u064e\u0627\u0644\u062a\u0651\u064e\u0642\u0652\u0648\u064e\u0649 \u0648\u064e\u0645\u0650\u0646\u064e \u0627\u0644\u0652\u0639\u064e\u0645\u064e\u0644\u0650 \u0645\u064e\u0627 \u062a\u064e\u0631\u0652\u0636\u064e\u0649",
        latin="Allahumma inna nas'aluka fi safarina hadzal birra wat-taqwa, wa minal 'amali ma tardha",
        translation="Ya Allah, kami memohon kepada-Mu dalam perjalanan kami ini kebaikan dan takwa, serta amal yang Engkau ridhai.",
        category=DoaCategory.PERJALANAN,
        when_to_read="Saat memulai perjalanan"
    ),

    # IHRAM
    Doa(
        id="doa_010",
        name="Niat Ihram Umrah",
        arabic="\u0644\u064e\u0628\u0651\u064e\u064a\u0652\u0643\u064e \u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0639\u064f\u0645\u0652\u0631\u064e\u0629\u064b",
        latin="Labbaika Allahumma 'Umratan",
        translation="Aku penuhi panggilan-Mu ya Allah untuk melaksanakan umrah.",
        category=DoaCategory.IHRAM,
        when_to_read="Saat niat ihram di miqat",
        is_wajib=True
    ),
    Doa(
        id="doa_011",
        name="Talbiyah",
        arabic="\u0644\u064e\u0628\u0651\u064e\u064a\u0652\u0643\u064e \u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0644\u064e\u0628\u0651\u064e\u064a\u0652\u0643\u064e\u060c \u0644\u064e\u0628\u0651\u064e\u064a\u0652\u0643\u064e \u0644\u0627\u064e \u0634\u064e\u0631\u0650\u064a\u0643\u064e \u0644\u064e\u0643\u064e \u0644\u064e\u0628\u0651\u064e\u064a\u0652\u0643\u064e\u060c \u0625\u0650\u0646\u0651\u064e \u0627\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064e \u0648\u064e\u0627\u0644\u0646\u0651\u0650\u0639\u0652\u0645\u064e\u0629\u064e \u0644\u064e\u0643\u064e \u0648\u064e\u0627\u0644\u0652\u0645\u064f\u0644\u0652\u0643\u064e\u060c \u0644\u0627\u064e \u0634\u064e\u0631\u0650\u064a\u0643\u064e \u0644\u064e\u0643\u064e",
        latin="Labbaik Allahumma labbaik, labbaika laa syariika laka labbaik. Innal hamda wan ni'mata laka wal mulk, laa syariika lak",
        translation="Aku memenuhi panggilan-Mu ya Allah, aku memenuhi panggilan-Mu. Aku memenuhi panggilan-Mu, tidak ada sekutu bagi-Mu, aku memenuhi panggilan-Mu. Sesungguhnya segala puji, nikmat, dan kerajaan adalah milik-Mu. Tidak ada sekutu bagi-Mu.",
        category=DoaCategory.IHRAM,
        when_to_read="Sepanjang perjalanan menuju Makkah",
        is_wajib=True
    ),

    # TAWAF
    Doa(
        id="doa_020",
        name="Doa Melihat Ka'bah",
        arabic="\u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0632\u0650\u062f\u0652 \u0647\u064e\u0630\u064e\u0627 \u0627\u0644\u0652\u0628\u064e\u064a\u0652\u062a\u064e \u062a\u064e\u0634\u0652\u0631\u0650\u064a\u0641\u064b\u0627 \u0648\u064e\u062a\u064e\u0639\u0652\u0638\u0650\u064a\u0645\u064b\u0627 \u0648\u064e\u062a\u064e\u0643\u0652\u0631\u0650\u064a\u0645\u064b\u0627 \u0648\u064e\u0645\u064e\u0647\u064e\u0627\u0628\u064e\u0629\u064b",
        latin="Allahumma zid hadzal baita tasyrifan wa ta'zhiman wa takriman wa mahabah",
        translation="Ya Allah, tambahkanlah kemuliaan, keagungan, kehormatan, dan kewibawaan rumah ini.",
        category=DoaCategory.TAWAF,
        when_to_read="Pertama kali melihat Ka'bah"
    ),
    Doa(
        id="doa_021",
        name="Doa di Hajar Aswad (Istilam)",
        arabic="\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0647\u0650 \u0648\u064e\u0627\u0644\u0644\u0647\u064f \u0623\u064e\u0643\u0652\u0628\u064e\u0631\u064f",
        latin="Bismillahi wallahu akbar",
        translation="Dengan nama Allah, Allah Maha Besar.",
        category=DoaCategory.TAWAF,
        when_to_read="Saat menghadap/menyentuh Hajar Aswad",
        is_wajib=True
    ),
    Doa(
        id="doa_022",
        name="Doa Antara Rukun Yamani dan Hajar Aswad",
        arabic="\u0631\u064e\u0628\u0651\u064e\u0646\u064e\u0627 \u0622\u062a\u0650\u0646\u064e\u0627 \u0641\u0650\u064a \u0627\u0644\u062f\u0651\u064f\u0646\u0652\u064a\u064e\u0627 \u062d\u064e\u0633\u064e\u0646\u064e\u0629\u064b \u0648\u064e\u0641\u0650\u064a \u0627\u0644\u0652\u0622\u062e\u0650\u0631\u064e\u0629\u0650 \u062d\u064e\u0633\u064e\u0646\u064e\u0629\u064b \u0648\u064e\u0642\u0650\u0646\u064e\u0627 \u0639\u064e\u0630\u064e\u0627\u0628\u064e \u0627\u0644\u0646\u0651\u064e\u0627\u0631\u0650",
        latin="Rabbana atina fid-dunya hasanah, wa fil akhirati hasanah, wa qina 'adzaban-nar",
        translation="Ya Tuhan kami, berilah kami kebaikan di dunia dan kebaikan di akhirat, dan lindungilah kami dari siksa api neraka.",
        category=DoaCategory.TAWAF,
        when_to_read="Antara Rukun Yamani dan Hajar Aswad (setiap putaran)",
        is_wajib=True
    ),
    Doa(
        id="doa_023",
        name="Doa Setelah Tawaf",
        arabic="\u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0625\u0650\u0646\u0651\u0650\u064a \u0623\u064e\u0633\u0652\u0623\u064e\u0644\u064f\u0643\u064e \u0639\u0650\u0644\u0652\u0645\u064b\u0627 \u0646\u064e\u0627\u0641\u0650\u0639\u064b\u0627 \u0648\u064e\u0631\u0650\u0632\u0652\u0642\u064b\u0627 \u0637\u064e\u064a\u0651\u0650\u0628\u064b\u0627 \u0648\u064e\u0639\u064e\u0645\u064e\u0644\u064b\u0627 \u0645\u064f\u062a\u064e\u0642\u064e\u0628\u0651\u064e\u0644\u064b\u0627",
        latin="Allahumma inni as'aluka 'ilman nafi'an, wa rizqan thayyiban, wa 'amalan mutaqabbalan",
        translation="Ya Allah, aku memohon kepada-Mu ilmu yang bermanfaat, rizki yang halal, dan amal yang diterima.",
        category=DoaCategory.TAWAF,
        when_to_read="Setelah selesai tawaf, saat minum air zamzam"
    ),

    # SAI
    Doa(
        id="doa_030",
        name="Doa di Bukit Shafa",
        arabic="\u0625\u0650\u0646\u0651\u064e \u0627\u0644\u0635\u0651\u064e\u0641\u064e\u0627 \u0648\u064e\u0627\u0644\u0652\u0645\u064e\u0631\u0652\u0648\u064e\u0629\u064e \u0645\u0650\u0646\u0652 \u0634\u064e\u0639\u064e\u0627\u0626\u0650\u0631\u0650 \u0627\u0644\u0644\u0647\u0650",
        latin="Innas-shafa wal marwata min sya'a'irillah",
        translation="Sesungguhnya Shafa dan Marwah adalah sebagian dari syiar-syiar Allah.",
        category=DoaCategory.SAI,
        when_to_read="Saat naik ke bukit Shafa (pertama kali saja)",
        is_wajib=True
    ),
    Doa(
        id="doa_031",
        name="Doa di Shafa dan Marwah",
        arabic="\u0627\u0644\u0644\u0647\u064f \u0623\u064e\u0643\u0652\u0628\u064e\u0631\u064f \u0627\u0644\u0644\u0647\u064f \u0623\u064e\u0643\u0652\u0628\u064e\u0631\u064f \u0627\u0644\u0644\u0647\u064f \u0623\u064e\u0643\u0652\u0628\u064e\u0631\u064f\u060c \u0644\u0627\u064e \u0625\u0650\u0644\u064e\u0647\u064e \u0625\u0650\u0644\u0651\u064e\u0627 \u0627\u0644\u0644\u0647\u064f \u0648\u064e\u062d\u0652\u062f\u064e\u0647\u064f \u0644\u0627\u064e \u0634\u064e\u0631\u0650\u064a\u0643\u064e \u0644\u064e\u0647\u064f\u060c \u0644\u064e\u0647\u064f \u0627\u0644\u0652\u0645\u064f\u0644\u0652\u0643\u064f \u0648\u064e\u0644\u064e\u0647\u064f \u0627\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064f \u0648\u064e\u0647\u064f\u0648\u064e \u0639\u064e\u0644\u064e\u0649 \u0643\u064f\u0644\u0651\u0650 \u0634\u064e\u064a\u0652\u0621\u064d \u0642\u064e\u062f\u0650\u064a\u0631\u064c",
        latin="Allahu akbar, Allahu akbar, Allahu akbar. Laa ilaha illallahu wahdahu laa syarika lah, lahul mulku wa lahul hamdu wa huwa 'ala kulli syai'in qadir",
        translation="Allah Maha Besar (3x). Tidak ada Tuhan selain Allah Yang Maha Esa, tidak ada sekutu bagi-Nya. Milik-Nya kerajaan dan pujian, dan Dia Maha Kuasa atas segala sesuatu.",
        category=DoaCategory.SAI,
        when_to_read="Di atas bukit Shafa dan Marwah"
    ),

    # MASJID
    Doa(
        id="doa_040",
        name="Doa Masuk Masjid",
        arabic="\u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0627\u0641\u0652\u062a\u064e\u062d\u0652 \u0644\u0650\u064a \u0623\u064e\u0628\u0652\u0648\u064e\u0627\u0628\u064e \u0631\u064e\u062d\u0652\u0645\u064e\u062a\u0650\u0643\u064e",
        latin="Allahummaf-tah li abwaba rahmatik",
        translation="Ya Allah, bukakanlah untukku pintu-pintu rahmat-Mu.",
        category=DoaCategory.MASJID,
        when_to_read="Saat masuk Masjidil Haram/Nabawi"
    ),
    Doa(
        id="doa_041",
        name="Doa Keluar Masjid",
        arabic="\u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0625\u0650\u0646\u0651\u0650\u064a \u0623\u064e\u0633\u0652\u0623\u064e\u0644\u064f\u0643\u064e \u0645\u0650\u0646\u0652 \u0641\u064e\u0636\u0652\u0644\u0650\u0643\u064e",
        latin="Allahumma inni as'aluka min fadlik",
        translation="Ya Allah, aku memohon karunia-Mu.",
        category=DoaCategory.MASJID,
        when_to_read="Saat keluar dari masjid"
    ),

    # HARIAN
    Doa(
        id="doa_050",
        name="Doa Sebelum Makan",
        arabic="\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0647\u0650 \u0648\u064e\u0639\u064e\u0644\u064e\u0649 \u0628\u064e\u0631\u064e\u0643\u064e\u0629\u0650 \u0627\u0644\u0644\u0647\u0650",
        latin="Bismillahi wa 'ala barakatillah",
        translation="Dengan nama Allah dan dengan berkah Allah.",
        category=DoaCategory.HARIAN,
        when_to_read="Sebelum makan"
    ),
    Doa(
        id="doa_051",
        name="Doa Setelah Makan",
        arabic="\u0627\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064f \u0644\u0650\u0644\u0647\u0650 \u0627\u0644\u0651\u064e\u0630\u0650\u064a \u0623\u064e\u0637\u0652\u0639\u064e\u0645\u064e\u0646\u064e\u0627 \u0648\u064e\u0633\u064e\u0642\u064e\u0627\u0646\u064e\u0627 \u0648\u064e\u062c\u064e\u0639\u064e\u0644\u064e\u0646\u064e\u0627 \u0645\u064f\u0633\u0652\u0644\u0650\u0645\u0650\u064a\u0646\u064e",
        latin="Alhamdulillahilladzi ath'amana wa saqana wa ja'alana muslimin",
        translation="Segala puji bagi Allah yang telah memberi kami makan dan minum, serta menjadikan kami orang-orang muslim.",
        category=DoaCategory.HARIAN,
        when_to_read="Setelah makan"
    ),
    Doa(
        id="doa_052",
        name="Doa Sebelum Tidur",
        arabic="\u0628\u0650\u0627\u0633\u0652\u0645\u0650\u0643\u064e \u0627\u0644\u0644\u0651\u064e\u0647\u064f\u0645\u0651\u064e \u0623\u064e\u0645\u064f\u0648\u062a\u064f \u0648\u064e\u0623\u064e\u062d\u0652\u064a\u064e\u0627",
        latin="Bismika Allahumma amutu wa ahya",
        translation="Dengan nama-Mu ya Allah, aku mati dan aku hidup.",
        category=DoaCategory.HARIAN,
        when_to_read="Sebelum tidur"
    ),
    Doa(
        id="doa_053",
        name="Doa Bangun Tidur",
        arabic="\u0627\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064f \u0644\u0650\u0644\u0647\u0650 \u0627\u0644\u0651\u064e\u0630\u0650\u064a \u0623\u064e\u062d\u0652\u064a\u064e\u0627\u0646\u064e\u0627 \u0628\u064e\u0639\u0652\u062f\u064e \u0645\u064e\u0627 \u0623\u064e\u0645\u064e\u0627\u062a\u064e\u0646\u064e\u0627 \u0648\u064e\u0625\u0650\u0644\u064e\u064a\u0652\u0647\u0650 \u0627\u0644\u0646\u0651\u064f\u0634\u064f\u0648\u0631\u064f",
        latin="Alhamdulillahilladzi ahyana ba'da ma amatana wa ilaihin-nusyur",
        translation="Segala puji bagi Allah yang telah menghidupkan kami setelah mematikan kami, dan kepada-Nya kami dibangkitkan.",
        category=DoaCategory.HARIAN,
        when_to_read="Setelah bangun tidur"
    ),

    # ZIARAH
    Doa(
        id="doa_060",
        name="Salam di Makam Rasulullah",
        arabic="\u0627\u0644\u0633\u0651\u064e\u0644\u0627\u064e\u0645\u064f \u0639\u064e\u0644\u064e\u064a\u0652\u0643\u064e \u064a\u064e\u0627 \u0631\u064e\u0633\u064f\u0648\u0644\u064e \u0627\u0644\u0644\u0647\u0650\u060c \u0627\u0644\u0633\u0651\u064e\u0644\u0627\u064e\u0645\u064f \u0639\u064e\u0644\u064e\u064a\u0652\u0643\u064e \u064a\u064e\u0627 \u0646\u064e\u0628\u0650\u064a\u0651\u064e \u0627\u0644\u0644\u0647\u0650\u060c \u0627\u0644\u0633\u0651\u064e\u0644\u0627\u064e\u0645\u064f \u0639\u064e\u0644\u064e\u064a\u0652\u0643\u064e \u064a\u064e\u0627 \u062e\u064e\u064a\u0652\u0631\u064e \u062e\u064e\u0644\u0652\u0642\u0650 \u0627\u0644\u0644\u0647\u0650",
        latin="Assalamu 'alaika ya Rasulallah, assalamu 'alaika ya Nabiyyallah, assalamu 'alaika ya khaira khalqillah",
        translation="Salam sejahtera atasmu wahai Rasulullah, salam sejahtera atasmu wahai Nabi Allah, salam sejahtera atasmu wahai sebaik-baik makhluk Allah.",
        category=DoaCategory.ZIARAH,
        when_to_read="Di depan makam Rasulullah SAW"
    ),
    Doa(
        id="doa_061",
        name="Doa Setelah Umrah",
        arabic="\u0627\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064f \u0644\u0650\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0651\u064e\u0630\u0650\u064a \u0628\u0650\u0646\u0650\u0639\u0652\u0645\u064e\u062a\u0650\u0647\u0650 \u062a\u064e\u062a\u0650\u0645\u0651\u064f \u0627\u0644\u0635\u0651\u064e\u0627\u0644\u0650\u062d\u064e\u0627\u062a\u064f",
        latin="Alhamdulillahilladzi bini'matihi tatimmus-shalihat",
        translation="Segala puji bagi Allah yang dengan nikmat-Nya sempurnalah segala amal shalih.",
        category=DoaCategory.ZIARAH,
        when_to_read="Setelah selesai umrah (tahallul)"
    ),
]


# =============================================================================
# ENHANCED AUDIO PLAYER COMPONENT (HTML/JS)
# =============================================================================

def _build_audio_player_html(doa_id, name, category, when_to_read, arabic,
                             latin, translation, is_wajib):
    """Build the HTML for the enhanced in-browser audio player."""
    wajib_html = (
        '<span class="wajib-badge">WAJIB</span>' if is_wajib else ''
    )
    return (
        '<div id="enhanced-player-' + doa_id + '" style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 1.5rem; border-radius: 20px; border: 1px solid #d4af37; margin-bottom: 1.5rem; box-shadow: 0 10px 40px rgba(212, 175, 55, 0.1);">'
        '    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">'
        '        <div>'
        '            <h3 style="color: #d4af37; margin: 0; font-size: 1.2rem;">' + name + '</h3>'
        '            <span style="color: #b0b0b0; font-size: 0.8rem;">' + category + ' &bull; ' + when_to_read + '</span>'
        '        </div>'
        '        ' + wajib_html +
        '    </div>'
        '    <div style="background: rgba(0,0,0,0.3); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">'
        '        <div style="direction: rtl; text-align: right; font-family: \'Amiri\', \'Traditional Arabic\', serif; font-size: 2rem; line-height: 2.2; color: #d4af37;">'
        '            ' + arabic +
        '        </div>'
        '    </div>'
        '    <div style="background: rgba(212, 175, 55, 0.1); padding: 1rem; border-radius: 15px; margin-bottom: 1rem;">'
        '        <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">'
        '            <div style="display: flex; gap: 0.5rem;">'
        '                <button id="play-' + doa_id + '" onclick="playDoa_' + doa_id + '()" aria-label="Putar doa" style="background: #d4af37; border: none; width: 50px; height: 50px; border-radius: 50%; cursor: pointer; font-size: 1.5rem; display: flex; align-items: center; justify-content: center;">&#9654;&#65039;</button>'
        '                <button onclick="pauseDoa_' + doa_id + '()" aria-label="Jeda doa" style="background: #333; border: 1px solid #d4af37; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 1rem;">&#9208;&#65039;</button>'
        '                <button onclick="stopDoa_' + doa_id + '()" aria-label="Berhenti" style="background: #333; border: 1px solid #d4af37; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 1rem;">&#9209;&#65039;</button>'
        '            </div>'
        '            <div style="display: flex; align-items: center; gap: 0.5rem;">'
        '                <span style="color: #b0b0b0; font-size: 0.8rem;">Kecepatan:</span>'
        '                <select id="speed-' + doa_id + '" onchange="updateSpeed_' + doa_id + '()" aria-label="Kecepatan pemutaran" style="background: #333; color: white; border: 1px solid #d4af37; padding: 5px 10px; border-radius: 8px;">'
        '                    <option value="0.5">0.5x (Lambat)</option>'
        '                    <option value="0.7" selected>0.7x (Normal)</option>'
        '                    <option value="0.9">0.9x (Cepat)</option>'
        '                    <option value="1.0">1.0x (Asli)</option>'
        '                </select>'
        '            </div>'
        '            <button id="repeat-' + doa_id + '" onclick="toggleRepeat_' + doa_id + '()" aria-label="Ulangi doa" style="background: #333; border: 1px solid #555; padding: 8px 15px; border-radius: 20px; cursor: pointer; color: #b0b0b0;">&#128257; Ulangi</button>'
        '        </div>'
        '        <div id="status-' + doa_id + '" style="color: #b0b0b0; font-size: 0.8rem; margin-top: 0.5rem;">Siap diputar</div>'
        '    </div>'
        '    <div style="color: #b0b0b0; font-style: italic; margin-bottom: 0.5rem; font-size: 0.95rem;">' + latin + '</div>'
        '    <div style="color: #eee; font-size: 1rem;"><strong>Artinya:</strong> ' + translation + '</div>'
        '</div>'
        '<script>'
        '(function() {'
        '    let currentUtterance_' + doa_id + ' = null;'
        '    let repeatEnabled_' + doa_id + ' = false;'
        '    let playbackSpeed_' + doa_id + ' = 0.7;'
        ''
        '    window.playDoa_' + doa_id + ' = function() {'
        '        window.speechSynthesis.cancel();'
        '        var text = "' + arabic.replace('"', '\\"') + '";'
        '        currentUtterance_' + doa_id + ' = new SpeechSynthesisUtterance(text);'
        '        currentUtterance_' + doa_id + '.lang = "ar-SA";'
        '        currentUtterance_' + doa_id + '.rate = playbackSpeed_' + doa_id + ';'
        '        currentUtterance_' + doa_id + '.pitch = 1.0;'
        '        var voices = window.speechSynthesis.getVoices();'
        '        var arabicVoice = voices.find(function(v){ return v.lang.indexOf("ar") >= 0; });'
        '        if (arabicVoice) currentUtterance_' + doa_id + '.voice = arabicVoice;'
        '        currentUtterance_' + doa_id + '.onstart = function() {'
        '            document.getElementById("status-' + doa_id + '").innerText = "\\ud83d\\udd0a Sedang memutar...";'
        '            document.getElementById("play-' + doa_id + '").innerText = "\\ud83d\\udd0a";'
        '        };'
        '        currentUtterance_' + doa_id + '.onend = function() {'
        '            document.getElementById("status-' + doa_id + '").innerText = repeatEnabled_' + doa_id + ' ? "\\ud83d\\udd01 Mengulang..." : "\\u2705 Selesai";'
        '            document.getElementById("play-' + doa_id + '").innerText = "\\u25b6\\ufe0f";'
        '            if (repeatEnabled_' + doa_id + ') { setTimeout(function(){ playDoa_' + doa_id + '(); }, 1500); }'
        '        };'
        '        currentUtterance_' + doa_id + '.onerror = function() {'
        '            document.getElementById("status-' + doa_id + '").innerText = "\\u274c Error - coba lagi";'
        '        };'
        '        window.speechSynthesis.speak(currentUtterance_' + doa_id + ');'
        '    };'
        ''
        '    window.pauseDoa_' + doa_id + ' = function() {'
        '        if (window.speechSynthesis.speaking) {'
        '            window.speechSynthesis.pause();'
        '            document.getElementById("status-' + doa_id + '").innerText = "\\u23f8\\ufe0f Dijeda";'
        '        } else if (window.speechSynthesis.paused) {'
        '            window.speechSynthesis.resume();'
        '            document.getElementById("status-' + doa_id + '").innerText = "\\ud83d\\udd0a Melanjutkan...";'
        '        }'
        '    };'
        ''
        '    window.stopDoa_' + doa_id + ' = function() {'
        '        window.speechSynthesis.cancel();'
        '        repeatEnabled_' + doa_id + ' = false;'
        '        document.getElementById("repeat-' + doa_id + '").style.borderColor = "#555";'
        '        document.getElementById("repeat-' + doa_id + '").style.color = "#b0b0b0";'
        '        document.getElementById("status-' + doa_id + '").innerText = "Siap diputar";'
        '        document.getElementById("play-' + doa_id + '").innerText = "\\u25b6\\ufe0f";'
        '    };'
        ''
        '    window.updateSpeed_' + doa_id + ' = function() {'
        '        playbackSpeed_' + doa_id + ' = parseFloat(document.getElementById("speed-' + doa_id + '").value);'
        '    };'
        ''
        '    window.toggleRepeat_' + doa_id + ' = function() {'
        '        repeatEnabled_' + doa_id + ' = !repeatEnabled_' + doa_id + ';'
        '        var btn = document.getElementById("repeat-' + doa_id + '");'
        '        btn.style.borderColor = repeatEnabled_' + doa_id + ' ? "#d4af37" : "#555";'
        '        btn.style.color = repeatEnabled_' + doa_id + ' ? "#d4af37" : "#b0b0b0";'
        '        btn.style.background = repeatEnabled_' + doa_id + ' ? "rgba(212,175,55,0.2)" : "#333";'
        '    };'
        ''
        '    if (window.speechSynthesis.onvoiceschanged !== undefined) {'
        '        window.speechSynthesis.onvoiceschanged = function() {};'
        '    }'
        '})();'
        '</script>'
    )


# Legacy reference -- kept for compatibility
AUDIO_PLAYER_HTML = None  # Use _build_audio_player_html() instead


# =============================================================================
# VOICE CHAT COMPONENT
# =============================================================================

VOICE_CHAT_HTML = (
    '<div id="voice-chat-container" style="background: linear-gradient(135deg, #0f3460, #16213e); padding: 1.5rem; border-radius: 20px; border: 1px solid #00d9ff; margin-bottom: 1.5rem;">'
    '    <h3 style="color: #00d9ff; margin-bottom: 1rem;">&#127897;&#65039; Tanya Doa dengan Suara</h3>'
    '    <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">'
    '        <button id="voice-record-btn" onclick="toggleRecording()" aria-label="Rekam suara untuk bertanya" style="background: linear-gradient(135deg, #e94560, #ff6b6b); border: none; width: 70px; height: 70px; border-radius: 50%; cursor: pointer; font-size: 2rem; box-shadow: 0 5px 20px rgba(233, 69, 96, 0.4); transition: all 0.3s;">&#127908;</button>'
    '        <div style="flex: 1; min-width: 200px;">'
    '            <div id="voice-status" style="color: #b0b0b0; margin-bottom: 0.5rem;">Tekan tombol mikrofon untuk bertanya</div>'
    '            <div id="voice-transcript" style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 10px; min-height: 50px; color: white; font-size: 1rem;">'
    '                <span style="color: #8e9fb3;">Pertanyaan Anda akan muncul di sini...</span>'
    '            </div>'
    '        </div>'
    '    </div>'
    '    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0,217,255,0.2);">'
    '        <span style="color: #b0b0b0; font-size: 0.8rem;">Contoh pertanyaan:</span>'
    '        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">'
    '            <span role="button" tabindex="0" aria-label="Tanya doa masuk masjid" onclick="setQuestion(\'Apa doa masuk masjid?\')" style="background: rgba(0,217,255,0.1); color: #00d9ff; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; cursor: pointer; border: 1px solid rgba(0,217,255,0.3);">Doa masuk masjid?</span>'
    '            <span role="button" tabindex="0" aria-label="Tanya bacaan talbiyah lengkap" onclick="setQuestion(\'Bacaan talbiyah lengkap\')" style="background: rgba(0,217,255,0.1); color: #00d9ff; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; cursor: pointer; border: 1px solid rgba(0,217,255,0.3);">Talbiyah lengkap</span>'
    '            <span role="button" tabindex="0" aria-label="Tanya doa saat tawaf" onclick="setQuestion(\'Doa saat tawaf\')" style="background: rgba(0,217,255,0.1); color: #00d9ff; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; cursor: pointer; border: 1px solid rgba(0,217,255,0.3);">Doa saat tawaf</span>'
    '            <span role="button" tabindex="0" aria-label="Tanya doa wajib saat sai" onclick="setQuestion(\'Doa wajib saat sai\')" style="background: rgba(0,217,255,0.1); color: #00d9ff; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; cursor: pointer; border: 1px solid rgba(0,217,255,0.3);">Doa wajib sai</span>'
    '        </div>'
    '    </div>'
    '</div>'
    '<script>'
    '(function() {'
    '    var recognition = null;'
    '    var isRecording = false;'
    '    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {'
    '        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;'
    '        recognition = new SpeechRecognition();'
    '        recognition.continuous = false;'
    '        recognition.interimResults = true;'
    '        recognition.lang = "id-ID";'
    '        recognition.onresult = function(event) {'
    '            var transcript = "";'
    '            for (var i = event.resultIndex; i < event.results.length; i++) {'
    '                transcript += event.results[i][0].transcript;'
    '            }'
    '            document.getElementById("voice-transcript").innerHTML = transcript || \'<span style="color: #8e9fb3;">Mendengarkan...</span>\';'
    '            if (event.results[event.results.length - 1].isFinal) {'
    '                window.parent.postMessage({type: "streamlit:setComponentValue", value: transcript}, "*");'
    '            }'
    '        };'
    '        recognition.onstart = function() {'
    '            document.getElementById("voice-status").innerText = "\\ud83d\\udd34 Mendengarkan... Silakan bicara";'
    '            document.getElementById("voice-record-btn").style.background = "linear-gradient(135deg, #ff0000, #ff4444)";'
    '            document.getElementById("voice-record-btn").style.animation = "pulse 1s infinite";'
    '        };'
    '        recognition.onend = function() {'
    '            isRecording = false;'
    '            document.getElementById("voice-status").innerText = "Tekan tombol mikrofon untuk bertanya lagi";'
    '            document.getElementById("voice-record-btn").style.background = "linear-gradient(135deg, #e94560, #ff6b6b)";'
    '            document.getElementById("voice-record-btn").style.animation = "none";'
    '        };'
    '        recognition.onerror = function(event) {'
    '            document.getElementById("voice-status").innerText = "\\u274c Error: " + event.error;'
    '            isRecording = false;'
    '        };'
    '    }'
    '    window.toggleRecording = function() {'
    '        if (!recognition) { document.getElementById("voice-status").innerText = "\\u274c Browser tidak mendukung voice input"; return; }'
    '        if (isRecording) { recognition.stop(); isRecording = false; }'
    '        else { recognition.start(); isRecording = true; }'
    '    };'
    '    window.setQuestion = function(question) {'
    '        document.getElementById("voice-transcript").innerText = question;'
    '        window.parent.postMessage({type: "streamlit:setComponentValue", value: question}, "*");'
    '    };'
    '})();'
    '</script>'
    '<style>'
    '@keyframes pulse {'
    '    0% { transform: scale(1); box-shadow: 0 5px 20px rgba(255, 0, 0, 0.4); }'
    '    50% { transform: scale(1.1); box-shadow: 0 5px 30px rgba(255, 0, 0, 0.6); }'
    '    100% { transform: scale(1); box-shadow: 0 5px 20px rgba(255, 0, 0, 0.4); }'
    '}'
    '</style>'
)

# Legacy template (kept for compatibility)
TTS_HTML_TEMPLATE = None  # Use _build_audio_player_html() instead


# =============================================================================
# AUDIO GENERATION
# =============================================================================

@st.cache_data(ttl=3600)
def generate_audio_edge(text: str, voice: str = "wanita") -> bytes:
    """Generate audio from text using Edge TTS with voice selection."""
    if not HAS_EDGE_TTS:
        return None

    try:
        voice_id = VOICE_OPTIONS.get(voice, VOICE_OPTIONS["wanita"])

        async def _generate():
            communicate = edge_tts.Communicate(text, voice_id, rate="-20%")
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_buffer.seek(0)
            return audio_buffer.read()

        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_generate())
        loop.close()
        return result
    except Exception:
        return None


@st.cache_data(ttl=3600)
def generate_audio(text: str, lang: str = "ar") -> bytes:
    """Generate audio from text using gTTS (fallback)."""
    if not HAS_GTTS:
        return None

    try:
        tts = gTTS(text=text, lang=lang, slow=True)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception:
        return None


def get_audio_player_html(audio_base64: str, doa_id: str) -> str:
    """Generate HTML for custom audio player."""
    return (
        '<div style="background: rgba(212, 175, 55, 0.1); padding: 1rem; border-radius: 15px; margin: 1rem 0;">'
        '<div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">'
        '<audio id="audio-' + doa_id + '" style="display: none;">'
        '<source src="data:audio/mp3;base64,' + audio_base64 + '" type="audio/mp3">'
        '</audio>'
        '<button onclick="document.getElementById(\'audio-' + doa_id + '\').play()" '
        'aria-label="Putar doa" style="background: #d4af37; border: none; width: 50px; height: 50px; border-radius: 50%; cursor: pointer; font-size: 1.5rem;">&#9654;&#65039;</button>'
        '<button onclick="document.getElementById(\'audio-' + doa_id + '\').pause()" '
        'aria-label="Jeda doa" style="background: #333; border: 1px solid #d4af37; width: 40px; height: 40px; border-radius: 50%; cursor: pointer;">&#9208;&#65039;</button>'
        '<button onclick="var a=document.getElementById(\'audio-' + doa_id + '\'); a.pause(); a.currentTime=0;" '
        'aria-label="Berhenti" style="background: #333; border: 1px solid #d4af37; width: 40px; height: 40px; border-radius: 50%; cursor: pointer;">&#9209;&#65039;</button>'
        '<select onchange="document.getElementById(\'audio-' + doa_id + '\').playbackRate=this.value" '
        'aria-label="Kecepatan pemutaran" style="background: #333; color: white; border: 1px solid #d4af37; padding: 5px 10px; border-radius: 8px;">'
        '<option value="0.5">0.5x Lambat</option>'
        '<option value="0.75" selected>0.75x Normal</option>'
        '<option value="1.0">1.0x Cepat</option>'
        '</select>'
        '<span style="color: #b0b0b0; font-size: 0.8rem;">&#128266; Audio Ready</span>'
        '</div>'
        '</div>'
    )


# =============================================================================
# AI DOA EXPLANATION
# =============================================================================

DOA_SYSTEM_PROMPT = (
    "Kamu adalah seorang ustadz/ustadzah yang ahli dalam doa dan dzikir Islam, "
    "khususnya yang berkaitan dengan ibadah umrah. Jelaskan dengan bahasa Indonesia "
    "yang sopan, mudah dipahami, dan penuh hikmah. Sertakan konteks kapan doa "
    "tersebut dibaca, keutamaannya, dan adab membacanya. Jawab dalam 3-5 paragraf."
)


def render_ai_explanation(doa: Doa):
    """Render an AI-powered explanation section for a specific doa."""
    session_key = "doa_ai_explained_" + doa.id
    result_key = "doa_ai_result_" + doa.id

    if st.button(
        "Jelaskan Makna & Keutamaan",
        key="ai_explain_" + doa.id,
        use_container_width=True,
    ):
        with st.spinner("Meminta penjelasan dari AI..."):
            prompt = (
                "Jelaskan makna, keutamaan, dan adab membaca doa berikut:\n\n"
                "Nama: " + doa.name + "\n"
                "Arab: " + doa.arabic + "\n"
                "Latin: " + doa.latin + "\n"
                "Terjemahan: " + doa.translation + "\n"
                "Kategori: " + doa.category.value.title() + "\n"
                "Kapan dibaca: " + doa.when_to_read + "\n\n"
                "Jelaskan secara mendalam namun ringkas makna dan hikmah doa ini, "
                "serta adab dan waktu terbaik membacanya."
            )

            response = ai_complete(prompt, system_prompt=DOA_SYSTEM_PROMPT, max_tokens=768)

            if response:
                st.session_state[result_key] = response
                # Gamification: +20 XP first time AI explanation per session
                if not st.session_state.get(session_key, False):
                    st.session_state[session_key] = True
                    add_xp_safe(20, "Penjelasan AI doa: " + doa.name)
            else:
                st.session_state[result_key] = None

    # Show cached AI result
    cached = st.session_state.get(result_key)
    if cached:
        escaped_name = doa.name.replace("<", "&lt;").replace(">", "&gt;")
        escaped_cached = cached.replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            '<div class="ai-card" role="status" aria-live="polite">'
            '<h4>Penjelasan AI: ' + escaped_name + '</h4>'
            '<p>' + escaped_cached + '</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif cached is not None and not cached:
        st.info("Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")


def render_ai_contextual_doa():
    """Render AI section for suggesting contextual duas based on a situation."""
    st.markdown("### Saran Doa dari AI")
    st.caption("Ceritakan situasi Anda dan AI akan menyarankan doa yang tepat")

    situation = st.text_area(
        "Situasi Anda:",
        placeholder="Contoh: Saya sedang cemas menjelang keberangkatan umrah...",
        key="doa_ai_situation",
        height=100,
    )

    if st.button("Dapatkan Saran Doa", key="btn_ai_contextual_doa", use_container_width=True):
        if not situation.strip():
            st.warning("Silakan ceritakan situasi Anda terlebih dahulu.")
            return

        with st.spinner("AI sedang mencari doa yang tepat..."):
            prompt = (
                "Seorang jamaah umrah menceritakan situasi berikut:\n\n"
                '"' + situation.strip() + '"\n\n'
                "Berdasarkan situasi tersebut, sarankan 1-3 doa yang tepat beserta "
                "teks Arab, transliterasi latin, artinya, dan keutamaannya. "
                "Jelaskan mengapa doa tersebut cocok untuk situasi ini."
            )

            response = ai_complete(prompt, system_prompt=DOA_SYSTEM_PROMPT, max_tokens=1024)

            if response:
                escaped = response.replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(
                    '<div class="ai-card" role="status" aria-live="polite">'
                    '<h4>Saran Doa untuk Situasi Anda</h4>'
                    '<p>' + escaped + '</p>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                # Gamification: +20 XP first time contextual doa
                if not st.session_state.get("doa_ai_contextual_done", False):
                    st.session_state.doa_ai_contextual_done = True
                    add_xp_safe(20, "Saran doa kontekstual dari AI")
            else:
                st.info("Layanan AI sedang tidak tersedia. Silakan coba lagi nanti.")


# =============================================================================
# RENDER FUNCTIONS
# =============================================================================

def render_doa_card(doa: Doa, show_audio: bool = True, enhanced: bool = True):
    """Render a single doa card with audio player."""

    with st.container():
        # Header with name and badge
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown("### " + doa.name)
            st.caption(doa.category.value.title() + " -- " + doa.when_to_read)

        with col2:
            if doa.is_wajib:
                st.error("WAJIB", icon="\u26a0\ufe0f")

        # Arabic text with beautiful styling
        st.markdown(
            '<div class="arabic-card">'
            '<div class="arabic-text">' + doa.arabic + '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Audio player with voice selection
        if show_audio and (HAS_EDGE_TTS or HAS_GTTS):
            with st.expander("Putar Audio", expanded=False):
                # Voice selection (only for Edge TTS)
                if HAS_EDGE_TTS:
                    col_voice1, col_voice2 = st.columns(2)
                    with col_voice1:
                        voice_choice = st.radio(
                            "Pilih Suara:",
                            ["Pria", "Wanita"],
                            index=1,
                            horizontal=True,
                            key="voice_" + doa.id,
                        )
                    voice = "pria" if "Pria" in voice_choice else "wanita"

                    # Generate audio with selected voice
                    audio_data = generate_audio_edge(doa.arabic, voice=voice)

                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                        voice_label = "Hamed (Pria)" if voice == "pria" else "Zariyah (Wanita)"
                        st.caption("Suara: " + voice_label + " - Arab Saudi")
                    else:
                        # Fallback to gTTS
                        audio_data = generate_audio(doa.arabic, lang="ar")
                        if audio_data:
                            st.audio(audio_data, format="audio/mp3")
                            st.caption("Suara: Google TTS")
                        else:
                            st.warning("Audio tidak tersedia. Pastikan koneksi internet aktif.")
                else:
                    # gTTS only (no voice selection)
                    audio_data = generate_audio(doa.arabic, lang="ar")
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                        st.caption("Klik tombol play untuk mendengarkan bacaan doa")
                    else:
                        st.warning("Audio tidak tersedia. Pastikan koneksi internet aktif.")
        elif show_audio:
            st.info("Install edge-tts untuk audio: pip install edge-tts")

        # Gamification: +15 XP for reading/listening to a doa (first per session)
        listened_key = "doa_listened_" + doa.id
        if not st.session_state.get(listened_key, False):
            st.session_state[listened_key] = True
            add_xp_safe(15, "Membaca doa: " + doa.name)

        # Latin transliteration
        st.markdown("**Latin:** *" + doa.latin + "*")

        # Translation
        st.markdown("**Artinya:** " + doa.translation)

        # AI explanation section
        render_ai_explanation(doa)

        # Bookmark button
        bookmarks = st.session_state.get("doa_bookmarks", set())
        is_bookmarked = doa.id in bookmarks

        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            bookmark_label = "Favorit" if is_bookmarked else "Simpan"
            if st.button(
                bookmark_label,
                key="bookmark_" + doa.id,
                use_container_width=True,
            ):
                if is_bookmarked:
                    bookmarks.discard(doa.id)
                    st.toast("Dihapus dari favorit")
                else:
                    bookmarks.add(doa.id)
                    st.toast("Ditambahkan ke favorit!")
                st.session_state.doa_bookmarks = bookmarks
                st.rerun()

        st.divider()


def render_doa_list(category: DoaCategory = None, wajib_only: bool = False):
    """Render list of duas filtered by category."""

    # Filter doas
    doas = UMRAH_DOAS

    if category:
        doas = [d for d in doas if d.category == category]

    if wajib_only:
        doas = [d for d in doas if d.is_wajib]

    if not doas:
        st.info("Tidak ada doa dalam kategori ini")
        return

    for doa in doas:
        render_doa_card(doa)


def render_voice_chat():
    """Render voice chat component for asking doa questions."""

    # Quick question buttons
    st.markdown("**Pertanyaan Cepat:**")

    col1, col2 = st.columns(2)

    quick_questions = [
        ("Doa Tawaf", "tawaf"),
        ("Doa Sa'i", "sai"),
        ("Doa Masjid", "masjid"),
        ("Doa Perjalanan", "perjalanan"),
        ("Doa Ihram", "ihram"),
        ("Talbiyah", "talbiyah"),
    ]

    with col1:
        for label, keyword in quick_questions[:3]:
            if st.button(label, key="quick_" + keyword, use_container_width=True):
                st.session_state.doa_voice_query = keyword
                st.rerun()

    with col2:
        for label, keyword in quick_questions[3:]:
            if st.button(label, key="quick_" + keyword, use_container_width=True):
                st.session_state.doa_voice_query = keyword
                st.rerun()

    st.divider()

    # Voice input using Web Speech API
    st.markdown("**Atau gunakan suara:**")

    voice_html = (
        '<div class="voice-chat-box">'
        '<div style="display: flex; gap: 1rem; align-items: center;">'
        '<button id="voice-btn" onclick="startRecognition()" '
        'aria-label="Rekam suara untuk bertanya" style="background: linear-gradient(135deg, #e94560, #ff6b6b); border: none; width: 60px; height: 60px; border-radius: 50%; cursor: pointer; font-size: 1.5rem;">&#127908;</button>'
        '<div style="flex: 1;">'
        '<div id="voice-status" style="color: #b0b0b0; font-size: 0.9rem;">Tekan tombol untuk bicara</div>'
        '<div id="voice-result" style="color: #00d9ff; font-size: 1.1rem; margin-top: 0.5rem; min-height: 25px;"></div>'
        '</div>'
        '</div>'
        '</div>'
        '<script>'
        'var recognition = null;'
        'if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {'
        '    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;'
        '    recognition = new SpeechRecognition();'
        '    recognition.lang = "id-ID";'
        '    recognition.continuous = false;'
        '    recognition.interimResults = false;'
        '    recognition.onstart = function() {'
        '        document.getElementById("voice-status").innerText = "\\ud83d\\udd34 Mendengarkan...";'
        '        document.getElementById("voice-btn").style.background = "#ff0000";'
        '    };'
        '    recognition.onresult = function(event) {'
        '        var transcript = event.results[0][0].transcript;'
        '        document.getElementById("voice-result").innerText = "\\ud83d\\udcdd \\"" + transcript + "\\"";'
        '        document.getElementById("voice-status").innerText = "\\u2705 Ketik hasil di kolom pencarian di bawah";'
        '        navigator.clipboard.writeText(transcript).then(function() {'
        '            document.getElementById("voice-status").innerText = "\\u2705 Tersalin! Paste di kolom pencarian";'
        '        });'
        '    };'
        '    recognition.onend = function() {'
        '        document.getElementById("voice-btn").style.background = "linear-gradient(135deg, #e94560, #ff6b6b)";'
        '    };'
        '    recognition.onerror = function(event) {'
        '        document.getElementById("voice-status").innerText = "\\u274c Error: " + event.error;'
        '        document.getElementById("voice-btn").style.background = "linear-gradient(135deg, #e94560, #ff6b6b)";'
        '    };'
        '}'
        'function startRecognition() {'
        '    if (recognition) { recognition.start(); }'
        '    else { document.getElementById("voice-status").innerText = "\\u274c Browser tidak mendukung"; }'
        '}'
        '</script>'
    )

    st.components.v1.html(voice_html, height=120)


def search_doa(query: str) -> List[Doa]:
    """Search doas by keyword."""
    query_lower = query.lower()
    results = []

    for doa in UMRAH_DOAS:
        if (query_lower in doa.name.lower() or
            query_lower in doa.translation.lower() or
            query_lower in doa.when_to_read.lower() or
            query_lower in doa.category.value.lower()):
            results.append(doa)

    return results


def render_doa_answer(query: str):
    """Render AI-style answer for doa question."""
    results = search_doa(query)

    if results:
        st.success("Ditemukan " + str(len(results)) + " doa terkait:")
        for doa in results[:3]:  # Show top 3
            render_doa_card(doa, enhanced=True)
    else:
        st.info(
            "Tidak ditemukan doa yang cocok. Coba kata kunci lain "
            "seperti: tawaf, sai, ihram, masjid"
        )


# =============================================================================
# HERO
# =============================================================================

def _render_hero():
    """Render the hero banner for the doa player page."""
    total_count = len(UMRAH_DOAS)
    wajib_count = sum(1 for d in UMRAH_DOAS if d.is_wajib)
    cat_count = len(set(d.category for d in UMRAH_DOAS))

    st.markdown(
        '<div class="doa-hero">'
        '<div class="bismillah">'
        '\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0646\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0650\u064a\u0645\u0650'
        '</div>'
        '<h1>Doa &amp; Dzikir Umrah</h1>'
        '<p class="subtitle">Kumpulan doa lengkap untuk perjalanan umrah dengan audio player</p>'
        '<div class="stat-row">'
        '<div class="stat-item">'
        '<div class="stat-number">' + str(total_count) + '</div>'
        '<div class="stat-label">Total Doa</div>'
        '</div>'
        '<div class="stat-item">'
        '<div class="stat-number">' + str(wajib_count) + '</div>'
        '<div class="stat-label">Doa Wajib</div>'
        '</div>'
        '<div class="stat-item">'
        '<div class="stat-number">' + str(cat_count) + '</div>'
        '<div class="stat-label">Kategori</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_doa_player_page():
    """Full doa player page."""
    try:
        from services.analytics import track_page
        track_page("doa")
    except Exception:
        pass

    # Inject all CSS via the shared pattern
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, DOA_CSS)

    # Hero banner
    _render_hero()

    # Initialize session state
    if "doa_bookmarks" not in st.session_state:
        st.session_state.doa_bookmarks = set()
    if "doa_voice_query" not in st.session_state:
        st.session_state.doa_voice_query = ""

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Semua Doa",
        "Tanya Suara",
        "Favorit",
        "Quick Reference",
        "Saran AI",
    ])

    # --- Tab 2: Voice search ---
    with tab2:
        st.markdown("### Tanya Doa dengan Suara")
        st.caption("Gunakan tombol cepat atau suara untuk mencari doa")

        # Voice chat component with quick buttons
        render_voice_chat()

        st.divider()

        # Text input for manual search or paste from voice
        query = st.text_input(
            "Cari doa:",
            value=st.session_state.get("doa_voice_query", ""),
            placeholder="Ketik atau paste hasil suara di sini...",
            key="doa_search_input",
        )

        # Show results
        if query:
            st.markdown("---")
            render_doa_answer(query)
        elif st.session_state.get("doa_voice_query"):
            st.markdown("---")
            render_doa_answer(st.session_state.doa_voice_query)
            # Clear after showing
            st.session_state.doa_voice_query = ""

    # --- Tab 1: All doas ---
    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            categories = ["Semua"] + [c.value.title() for c in DoaCategory]
            selected = st.selectbox("Kategori", categories)

        with col2:
            wajib_only = st.checkbox("Hanya Wajib")

        st.divider()

        if selected == "Semua":
            render_doa_list(wajib_only=wajib_only)
        else:
            category_map = {c.value.title(): c for c in DoaCategory}
            category = category_map.get(selected)
            render_doa_list(category=category, wajib_only=wajib_only)

    # --- Tab 3: Favorites ---
    with tab3:
        bookmarks = st.session_state.get("doa_bookmarks", set())

        if bookmarks:
            st.success("Anda memiliki " + str(len(bookmarks)) + " doa favorit")
            bookmarked_doas = [d for d in UMRAH_DOAS if d.id in bookmarks]
            for doa in bookmarked_doas:
                render_doa_card(doa, enhanced=True)
        else:
            st.info(
                "Belum ada doa favorit. Tekan Simpan pada doa "
                "untuk menambahkan ke favorit."
            )

    # --- Tab 4: Quick Reference ---
    with tab4:
        st.markdown("### Ringkasan Doa Wajib Umrah")

        wajib_doas = [d for d in UMRAH_DOAS if d.is_wajib]

        for i, doa in enumerate(wajib_doas, 1):
            with st.expander(
                str(i) + ". " + doa.name + " (" + doa.category.value.title() + ")"
            ):
                st.markdown(
                    "**Arab:** " + doa.arabic + "\n\n"
                    "**Latin:** *" + doa.latin + "*\n\n"
                    "**Artinya:** " + doa.translation + "\n\n"
                    "**Kapan dibaca:** " + doa.when_to_read
                )

        st.divider()

        st.markdown("### Urutan Doa dalam Umrah")

        steps = [
            ("1", "Niat Ihram", "Di Miqat"),
            ("2", "Talbiyah", "Sepanjang perjalanan ke Makkah"),
            ("3", "Doa Melihat Ka'bah", "Pertama kali melihat Ka'bah"),
            ("4", "Doa Istilam", "Di Hajar Aswad (setiap putaran)"),
            ("5", "Doa Tawaf", "Selama 7 putaran"),
            ("6", "Doa Minum Zamzam", "Setelah sholat tawaf"),
            ("7", "Doa Sa'i di Shafa", "Awal sa'i"),
            ("8", "Doa Sa'i", "7 kali Shafa-Marwah"),
            ("9", "Doa Selesai Umrah", "Setelah tahallul"),
        ]

        for num, title, when in steps:
            st.markdown(
                '<div class="step-card">'
                '<span class="step-num">' + num + '.</span> '
                '<span class="step-title">' + title + '</span>'
                '<br><span class="step-when">' + when + '</span>'
                '</div>',
                unsafe_allow_html=True,
            )

    # --- Tab 5: AI Contextual Doa ---
    with tab5:
        render_ai_contextual_doa()


def render_doa_mini_widget():
    """Mini widget showing quick doa access."""

    wajib_count = sum(1 for d in UMRAH_DOAS if d.is_wajib)
    total_count = len(UMRAH_DOAS)

    st.markdown(
        '<div class="doa-mini-widget">'
        '<div class="mini-label">Doa Umrah</div>'
        '<div class="mini-value">' + str(wajib_count) + ' Wajib / ' + str(total_count) + ' Total</div>'
        '<div class="mini-hint">Klik untuk buka player</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "Doa",
    "DoaCategory",
    "UMRAH_DOAS",
    "render_doa_card",
    "render_doa_list",
    "render_doa_player_page",
    "render_doa_mini_widget",
    "render_voice_chat",
    "search_doa",
    "generate_audio",
    "generate_audio_edge",
    "HAS_GTTS",
    "HAS_EDGE_TTS",
    "VOICE_OPTIONS",
]
