"""
================================================================================
LABBAIK AI - KALKULATOR KURS & HARGA
================================================================================
Lokasi: ui/pages/kurs_calculator.py
Fitur: Konversi mata uang dan referensi harga di Arab Saudi untuk jamaah umrah
       - Kalkulator konversi SAR/IDR/USD
       - Referensi harga barang & jasa di Makkah/Madinah
       - Tips penukaran uang
       - Budget calculator dengan alokasi kategori
       - Analisis AI untuk budget umrah
================================================================================
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import re

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

# =============================================================================
# STYLING
# =============================================================================

KURS_CSS = """
/* Page-specific overrides for kurs calculator */
.kurs-hero {
    background: linear-gradient(135deg, #1a1a0a 0%, #2a2a1a 50%, #1a1a2e 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid #d4af37;
    position: relative;
    overflow: hidden;
}

.kurs-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.08) 0%, transparent 70%);
    animation: kurs-pulse 4s ease-in-out infinite;
    pointer-events: none;
}

@keyframes kurs-pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}

.kurs-hero h1 {
    color: #d4af37;
    margin: 0;
    font-size: 2.2rem;
    position: relative;
    z-index: 1;
}

.kurs-hero .subtitle {
    color: #b0b0b0;
    font-size: 1rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

.kurs-hero .bismillah {
    font-family: 'Amiri', serif;
    color: #d4af37;
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

.kurs-stat-row {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-top: 1.5rem;
    position: relative;
    z-index: 1;
    flex-wrap: wrap;
}

.kurs-stat-item {
    text-align: center;
    padding: 0.75rem 1.5rem;
    background: rgba(212, 175, 55, 0.1);
    border-radius: 12px;
    border: 1px solid rgba(212, 175, 55, 0.3);
    min-width: 130px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kurs-stat-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.kurs-stat-number {
    font-size: 1.6rem;
    font-weight: bold;
    color: #d4af37;
}

.kurs-stat-label {
    color: #aaa;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

/* Converter result card */
.converter-result {
    background: linear-gradient(145deg, #1a2a1a 0%, #1e3a1e 100%);
    border: 1px solid #228B22;
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    margin-top: 1rem;
    transition: transform 0.2s ease;
}

.converter-result:hover {
    transform: translateY(-1px);
}

.converter-amount {
    font-size: 2rem;
    font-weight: 700;
    color: #4ade80;
    margin: 0.5rem 0;
}

.converter-equals {
    color: #b0b0b0;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
}

.converter-ref {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* Price guide items */
.price-item-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid #333;
    border-left: 4px solid #d4af37;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.price-item-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.price-item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
}

.price-item-name {
    color: #e2e8f0;
    font-weight: 600;
    font-size: 1.05rem;
    margin: 0;
}

.price-item-name-ar {
    color: #d4af37;
    font-family: 'Amiri', serif;
    font-size: 0.95rem;
    direction: rtl;
    margin-top: 0.15rem;
}

.price-item-values {
    display: flex;
    gap: 1rem;
    align-items: center;
    margin-top: 0.5rem;
    flex-wrap: wrap;
}

.price-sar {
    font-size: 1.1rem;
    font-weight: 700;
    color: #d4af37;
}

.price-idr {
    font-size: 0.9rem;
    color: #94a3b8;
}

.price-item-notes {
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 0.4rem;
    font-style: italic;
}

/* Price level badges */
.price-murah {
    display: inline-block;
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
    border: 1px solid rgba(74, 222, 128, 0.3);
}

.price-sedang {
    display: inline-block;
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
    border: 1px solid rgba(251, 191, 36, 0.3);
}

.price-mahal {
    display: inline-block;
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
    border: 1px solid rgba(248, 113, 113, 0.3);
}

/* Category header */
.price-category-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    margin: 1.25rem 0 0.75rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #e2e8f0;
}

/* Tips card */
.tips-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid #334155;
    border-left: 4px solid #d4af37;
    transition: transform 0.15s ease;
}

.tips-card:hover {
    transform: translateX(2px);
}

.tips-card h4 {
    color: #d4af37;
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
}

.tips-card p {
    color: #ccc;
    font-size: 0.9rem;
    line-height: 1.6;
    margin: 0;
}

/* Budget breakdown item */
.budget-breakdown-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 10px;
    margin-bottom: 0.5rem;
    border: 1px solid #1e293b;
    transition: border-color 0.2s;
}

.budget-breakdown-item:hover {
    border-color: #334155;
}

.budget-breakdown-label {
    color: #e2e8f0;
    font-weight: 500;
    font-size: 0.95rem;
}

.budget-breakdown-value {
    text-align: right;
}

.budget-breakdown-pct {
    font-size: 1rem;
    font-weight: 700;
    color: #d4af37;
}

.budget-breakdown-amount {
    color: #94a3b8;
    font-size: 0.8rem;
}
"""

# =============================================================================
# CONSTANTS & DATA
# =============================================================================

BASE_RATES = {
    "SAR_IDR": 4250,
    "USD_IDR": 15938,
    "USD_SAR": 3.75,
}

QUICK_AMOUNTS_SAR = [100, 500, 1000, 5000]

PRICE_CATEGORIES = {
    "makanan": {"icon": "\U0001f37d\ufe0f", "label": "Makanan & Minuman", "color": "#4ade80"},
    "transport": {"icon": "\U0001f695", "label": "Transportasi", "color": "#60a5fa"},
    "belanja": {"icon": "\U0001f6cd\ufe0f", "label": "Belanja & Oleh-oleh", "color": "#f472b6"},
    "layanan": {"icon": "\u2702\ufe0f", "label": "Layanan", "color": "#fbbf24"},
}

SAUDI_PRICES = [
    # Makanan & Minuman
    {
        "name": "Nasi + Lauk",
        "name_ar": "\u0623\u0631\u0632 \u0645\u0639 \u0644\u062d\u0645",
        "category": "makanan",
        "price_min": 15,
        "price_max": 35,
        "unit": "porsi",
        "notes": "Restoran biasa di sekitar Haram, nasi kabsa/mandi",
        "city": "both",
    },
    {
        "name": "Shawarma",
        "name_ar": "\u0634\u0627\u0648\u0631\u0645\u0627",
        "category": "makanan",
        "price_min": 5,
        "price_max": 15,
        "unit": "porsi",
        "notes": "Jajanan populer, tersedia di mana-mana",
        "city": "both",
    },
    {
        "name": "Air Zamzam",
        "name_ar": "\u0645\u0627\u0621 \u0632\u0645\u0632\u0645",
        "category": "makanan",
        "price_min": 0,
        "price_max": 5,
        "unit": "botol",
        "notes": "Gratis di Masjidil Haram, botolan di toko",
        "city": "both",
    },
    {
        "name": "Jus Buah Segar",
        "name_ar": "\u0639\u0635\u064a\u0631 \u0641\u0648\u0627\u0643\u0647",
        "category": "makanan",
        "price_min": 5,
        "price_max": 15,
        "unit": "gelas",
        "notes": "Jus mangga, jeruk, delima populer",
        "city": "both",
    },
    {
        "name": "Kopi Arab (Qahwa)",
        "name_ar": "\u0642\u0647\u0648\u0629 \u0639\u0631\u0628\u064a\u0629",
        "category": "makanan",
        "price_min": 5,
        "price_max": 20,
        "unit": "cangkir",
        "notes": "Kopi tradisional dengan kapulaga dan za'faran",
        "city": "both",
    },
    {
        "name": "Fast Food (Al Baik)",
        "name_ar": "\u0627\u0644\u0628\u064a\u0643",
        "category": "makanan",
        "price_min": 15,
        "price_max": 40,
        "unit": "paket",
        "notes": "Fried chicken favorit, antrian panjang saat ramai",
        "city": "both",
    },
    # Transportasi
    {
        "name": "Taksi Bandara - Hotel",
        "name_ar": "\u062a\u0627\u0643\u0633\u064a \u0645\u0646 \u0627\u0644\u0645\u0637\u0627\u0631",
        "category": "transport",
        "price_min": 50,
        "price_max": 150,
        "unit": "perjalanan",
        "notes": "Tergantung jarak hotel dari bandara",
        "city": "both",
    },
    {
        "name": "Uber / Careem",
        "name_ar": "\u0623\u0648\u0628\u0631 / \u0643\u0631\u064a\u0645",
        "category": "transport",
        "price_min": 10,
        "price_max": 50,
        "unit": "perjalanan",
        "notes": "Lebih murah dari taksi biasa, pakai aplikasi",
        "city": "both",
    },
    {
        "name": "Bus Makkah - Madinah",
        "name_ar": "\u0628\u0627\u0635 \u0645\u0643\u0629 - \u0627\u0644\u0645\u062f\u064a\u0646\u0629",
        "category": "transport",
        "price_min": 50,
        "price_max": 100,
        "unit": "sekali jalan",
        "notes": "SAPTCO bus, perjalanan ~5-6 jam",
        "city": "both",
    },
    # Belanja & Oleh-oleh
    {
        "name": "Kurma (per kg)",
        "name_ar": "\u062a\u0645\u0631",
        "category": "belanja",
        "price_min": 15,
        "price_max": 150,
        "unit": "kg",
        "notes": "Ajwa paling mahal, Sukkari menengah, Safawi murah",
        "city": "both",
    },
    {
        "name": "Minyak Zaitun",
        "name_ar": "\u0632\u064a\u062a \u0632\u064a\u062a\u0648\u0646",
        "category": "belanja",
        "price_min": 20,
        "price_max": 80,
        "unit": "botol",
        "notes": "Pilih yang asli, cek label dan kemasan",
        "city": "both",
    },
    {
        "name": "Sajadah",
        "name_ar": "\u0633\u062c\u0627\u062f\u0629",
        "category": "belanja",
        "price_min": 10,
        "price_max": 100,
        "unit": "lembar",
        "notes": "Harga bervariasi tergantung kualitas dan bahan",
        "city": "both",
    },
    {
        "name": "Kain Ihram",
        "name_ar": "\u0642\u0645\u0627\u0634 \u0625\u062d\u0631\u0627\u0645",
        "category": "belanja",
        "price_min": 15,
        "price_max": 80,
        "unit": "set",
        "notes": "Katun biasa vs microfiber premium",
        "city": "makkah",
    },
    {
        "name": "Parfum / Oud",
        "name_ar": "\u0639\u0637\u0631 / \u0639\u0648\u062f",
        "category": "belanja",
        "price_min": 20,
        "price_max": 500,
        "unit": "botol",
        "notes": "Oud asli sangat mahal, bukhur lebih terjangkau",
        "city": "both",
    },
    # Layanan
    {
        "name": "Laundry (per kg)",
        "name_ar": "\u063a\u0633\u064a\u0644 \u0645\u0644\u0627\u0628\u0633",
        "category": "layanan",
        "price_min": 5,
        "price_max": 15,
        "unit": "kg",
        "notes": "Banyak tersedia di sekitar hotel",
        "city": "both",
    },
    {
        "name": "SIM Card Data",
        "name_ar": "\u0634\u0631\u064a\u062d\u0629 \u0628\u064a\u0627\u0646\u0627\u062a",
        "category": "layanan",
        "price_min": 30,
        "price_max": 100,
        "unit": "paket",
        "notes": "STC, Mobily, Zain; paket 7-30 hari",
        "city": "both",
    },
    {
        "name": "Barbershop / Tahallul",
        "name_ar": "\u062d\u0644\u0627\u0642 / \u062a\u062d\u0644\u0644",
        "category": "layanan",
        "price_min": 5,
        "price_max": 20,
        "unit": "potong",
        "notes": "Cukur rambut setelah umrah, banyak di sekitar Haram",
        "city": "makkah",
    },
]

MONEY_CHANGER_TIPS = [
    {
        "title": "Bank vs Money Changer Kota",
        "desc": "Money changer di kota besar (Jakarta, Surabaya) biasanya memberikan kurs lebih baik dibanding bank. Bandingkan rate di beberapa tempat sebelum menukar.",
    },
    {
        "title": "Hindari Tukar di Bandara",
        "desc": "Kurs di bandara (baik Indonesia maupun Saudi) biasanya lebih mahal 2-5% dibanding money changer kota. Tukarkan sebagian besar uang sebelum berangkat.",
    },
    {
        "title": "Tukar di Indonesia Lebih Aman",
        "desc": "Sebaiknya tukarkan SAR di Indonesia sebelum berangkat. Kurs di Arab Saudi untuk IDR seringkali kurang menguntungkan karena Rupiah bukan mata uang utama.",
    },
    {
        "title": "Gunakan ATM dengan Bijak",
        "desc": "ATM di Arab Saudi menerima kartu Visa/Mastercard internasional. Pilih opsi 'tanpa konversi' agar dikenakan kurs bank Anda, bukan kurs ATM lokal.",
    },
    {
        "title": "Simpan Bukti Penukaran",
        "desc": "Selalu minta dan simpan bukti/struk penukaran uang. Berguna jika ada masalah atau jika ingin menukar kembali sisa SAR setelah pulang.",
    },
    {
        "title": "Waktu Terbaik Menukar",
        "desc": "Pantau kurs 1-2 minggu sebelum keberangkatan. Tukarkan saat kurs sedang menguntungkan. Hindari menukar saat Rupiah sedang melemah drastis.",
    },
]

BUDGET_BREAKDOWN = {
    "makanan": {"label": "\U0001f37d\ufe0f Makanan & Minuman", "pct": 30},
    "transport": {"label": "\U0001f695 Transportasi", "pct": 15},
    "belanja": {"label": "\U0001f6cd\ufe0f Belanja & Oleh-oleh", "pct": 35},
    "darurat": {"label": "\U0001f6a8 Dana Darurat", "pct": 20},
}


# =============================================================================
# SESSION STATE
# =============================================================================

def init_kurs_state():
    """Initialize kurs calculator session state."""
    defaults = {
        "kurs_amount_sar": 100.0,
        "kurs_amount_idr": 425000.0,
        "kurs_direction": "SAR_to_IDR",
        "kurs_first_use": False,
        "kurs_ai_analysis_done": False,
        "kurs_budget_idr": 5000000,
        "kurs_selected_category": "semua",
        "kurs_selected_city": "both",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# HELPERS
# =============================================================================

def sar_to_idr(amount: float) -> float:
    """Convert SAR to IDR."""
    return amount * BASE_RATES["SAR_IDR"]


def idr_to_sar(amount: float) -> float:
    """Convert IDR to SAR."""
    return amount / BASE_RATES["SAR_IDR"]


def sar_to_usd(amount: float) -> float:
    """Convert SAR to USD."""
    return amount / BASE_RATES["USD_SAR"]


def format_idr(amount: float) -> str:
    """Format amount as Indonesian Rupiah with dot separator."""
    rounded = int(round(amount))
    formatted = f"{rounded:,}".replace(",", ".")
    return f"Rp {formatted}"


def format_sar(amount: float) -> str:
    """Format amount as Saudi Riyal with dot separator (Indonesian style)."""
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} SAR"


def format_usd(amount: float) -> str:
    """Format amount as US Dollar with dot separator (Indonesian style)."""
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${formatted}"


def format_num(amount) -> str:
    """Format a number with Indonesian dot separator (e.g. 1.000, 5.000)."""
    return f"{int(amount):,}".replace(",", ".")


def get_price_level(price_avg: float) -> Dict:
    """Determine price level based on average price in SAR."""
    if price_avg <= 20:
        return {"label": "Murah", "class": "price-murah", "color": "#4ade80"}
    elif price_avg <= 60:
        return {"label": "Sedang", "class": "price-sedang", "color": "#fbbf24"}
    else:
        return {"label": "Mahal", "class": "price-mahal", "color": "#f87171"}


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
            line = f"<strong>{match.group(1)}.</strong> {line[match.end():]}"
        html_lines.append(f"<div style='margin-bottom:0.3rem;'>{line}</div>")
    return "\n".join(html_lines)


# =============================================================================
# UI: HERO
# =============================================================================

def render_hero():
    """Render hero section with branding and stats."""
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, KURS_CSS)

    total_items = len(SAUDI_PRICES)

    st.markdown(
        f'<div class="kurs-hero">'
        f'<div class="bismillah">\u0628\u0633\u0645 \u0627\u0644\u0644\u0647 \u0627\u0644\u0631\u062d\u0645\u0646 \u0627\u0644\u0631\u062d\u064a\u0645</div>'
        f'<h1>\U0001f3e6 Kalkulator Kurs & Harga</h1>'
        f'<p class="subtitle">Konversi mata uang dan referensi harga di Arab Saudi untuk jamaah umrah</p>'
        f'<div class="kurs-stat-row">'
        f'<div class="kurs-stat-item">'
        f'<div class="kurs-stat-number">{format_idr(BASE_RATES["SAR_IDR"])}</div>'
        f'<div class="kurs-stat-label">1 SAR = IDR</div>'
        f'</div>'
        f'<div class="kurs-stat-item">'
        f'<div class="kurs-stat-number">3.75</div>'
        f'<div class="kurs-stat-label">1 USD = SAR</div>'
        f'</div>'
        f'<div class="kurs-stat-item">'
        f'<div class="kurs-stat-number">{total_items}</div>'
        f'<div class="kurs-stat-label">Referensi Harga</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "\u26a0\ufe0f Kurs yang ditampilkan adalah estimasi rata-rata dan dapat berbeda "
        "dengan kurs aktual di money changer atau bank. Selalu cek kurs terkini sebelum menukar uang."
    )


# =============================================================================
# UI: CURRENCY CONVERTER
# =============================================================================

def render_currency_converter():
    """Render the currency converter section."""
    st.markdown("### \U0001f4b1 Konversi Mata Uang")

    direction = st.radio(
        "Arah konversi",
        options=["SAR_to_IDR", "IDR_to_SAR"],
        format_func=lambda x: "SAR \u2192 IDR" if x == "SAR_to_IDR" else "IDR \u2192 SAR",
        horizontal=True,
        key="kurs_direction_radio",
    )
    st.session_state.kurs_direction = direction

    if direction == "SAR_to_IDR":
        amount_sar = st.number_input(
            "Jumlah SAR",
            min_value=0.0,
            max_value=1000000.0,
            value=st.session_state.kurs_amount_sar,
            step=10.0,
            format="%.2f",
            key="input_amount_sar",
        )
        st.session_state.kurs_amount_sar = amount_sar

        # Quick amount buttons
        st.caption("Jumlah cepat:")
        qcols = st.columns(4)
        for i, quick_amt in enumerate(QUICK_AMOUNTS_SAR):
            with qcols[i]:
                if st.button(
                    f"{format_num(quick_amt)} SAR",
                    key=f"quick_sar_{quick_amt}",
                    use_container_width=True,
                ):
                    st.session_state.kurs_amount_sar = float(quick_amt)
                    st.rerun()

        # Calculate and display result
        result_idr = sar_to_idr(amount_sar)
        result_usd = sar_to_usd(amount_sar)

        st.markdown(
            f'<div class="converter-result">'
            f'<div class="converter-equals">{format_sar(amount_sar)} =</div>'
            f'<div class="converter-amount">{format_idr(result_idr)}</div>'
            f'<div class="converter-ref">Referensi: {format_usd(result_usd)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    else:
        amount_idr = st.number_input(
            "Jumlah IDR (Rupiah)",
            min_value=0.0,
            max_value=10000000000.0,
            value=st.session_state.kurs_amount_idr,
            step=50000.0,
            format="%.0f",
            key="input_amount_idr",
        )
        st.session_state.kurs_amount_idr = amount_idr

        # Calculate and display result
        result_sar = idr_to_sar(amount_idr)
        result_usd = sar_to_usd(result_sar)

        st.markdown(
            f'<div class="converter-result">'
            f'<div class="converter-equals">{format_idr(amount_idr)} =</div>'
            f'<div class="converter-amount">{format_sar(result_sar)}</div>'
            f'<div class="converter-ref">Referensi: {format_usd(result_usd)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Award XP on first use
    if not st.session_state.kurs_first_use:
        st.session_state.kurs_first_use = True
        add_xp_safe(5, "Menggunakan kalkulator kurs")


# =============================================================================
# UI: PRICE GUIDE
# =============================================================================

def render_price_guide():
    """Render the Saudi Arabia price reference guide."""
    st.markdown("### \U0001f4cb Referensi Harga di Arab Saudi")

    col_cat, col_city = st.columns(2)

    with col_cat:
        category_options = ["semua"] + list(PRICE_CATEGORIES.keys())
        selected_cat = st.selectbox(
            "Filter Kategori",
            options=category_options,
            format_func=lambda x: (
                "Semua Kategori" if x == "semua"
                else f"{PRICE_CATEGORIES[x]['icon']} {PRICE_CATEGORIES[x]['label']}"
            ),
            key="kurs_cat_filter",
        )
        st.session_state.kurs_selected_category = selected_cat

    with col_city:
        city_options = ["both", "makkah", "madinah"]
        selected_city = st.selectbox(
            "Filter Kota",
            options=city_options,
            format_func=lambda x: {
                "both": "Semua Kota",
                "makkah": "\U0001f54b Makkah",
                "madinah": "\U0001f54c Madinah",
            }.get(x, x),
            key="kurs_city_filter",
        )
        st.session_state.kurs_selected_city = selected_city

    # Filter prices
    filtered_prices = SAUDI_PRICES

    if selected_cat != "semua":
        filtered_prices = [p for p in filtered_prices if p["category"] == selected_cat]

    if selected_city != "both":
        filtered_prices = [
            p for p in filtered_prices
            if p["city"] == "both" or p["city"] == selected_city
        ]

    if not filtered_prices:
        st.info("Tidak ada item yang sesuai dengan filter. Coba ubah filter kategori atau kota.")
        return

    # Sort by category for grouping
    sorted_prices = sorted(filtered_prices, key=lambda x: x["category"])

    # Group by category
    from itertools import groupby

    for cat_key, items_iter in groupby(sorted_prices, key=lambda x: x["category"]):
        items = list(items_iter)
        cat_info = PRICE_CATEGORIES.get(cat_key, {})
        cat_icon = cat_info.get("icon", "")
        cat_label = cat_info.get("label", cat_key)
        cat_color = cat_info.get("color", "#d4af37")

        # Category header
        st.markdown(
            f'<div class="price-category-header" style="background: {cat_color}15; border: 1px solid {cat_color}33;">'
            f'<span>{cat_icon}</span>'
            f'<span>{cat_label}</span>'
            f'<span style="color: #64748b; font-size: 0.85rem; font-weight: 400;">({len(items)} item)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Items
        for item in items:
            price_avg = (item["price_min"] + item["price_max"]) / 2
            level = get_price_level(price_avg)
            idr_min = sar_to_idr(item["price_min"])
            idr_max = sar_to_idr(item["price_max"])

            city_badge = ""
            if item["city"] == "makkah":
                city_badge = '<span style="color:#60a5fa;font-size:0.75rem;">\U0001f54b Makkah</span>'
            elif item["city"] == "madinah":
                city_badge = '<span style="color:#60a5fa;font-size:0.75rem;">\U0001f54c Madinah</span>'

            card_html = (
                f'<div class="price-item-card" style="border-left-color: {cat_color};">'
                f'<div class="price-item-header">'
                f'<div>'
                f'<p class="price-item-name">{item["name"]}</p>'
                f'<p class="price-item-name-ar">{item["name_ar"]}</p>'
                f'</div>'
                f'<div style="display:flex;gap:0.5rem;align-items:center;">'
                f'{city_badge}'
                f'<span class="{level["class"]}">{level["label"]}</span>'
                f'</div>'
                f'</div>'
                f'<div class="price-item-values">'
                f'<span class="price-sar">{format_num(item["price_min"])}-{format_num(item["price_max"])} SAR</span>'
                f'<span style="color:#64748b;">|</span>'
                f'<span class="price-idr">{format_idr(idr_min)} - {format_idr(idr_max)}</span>'
                f'<span style="color:#64748b;font-size:0.8rem;">/ {item["unit"]}</span>'
                f'</div>'
                f'<p class="price-item-notes">{item["notes"]}</p>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

    st.caption(f"Menampilkan {len(filtered_prices)} dari {len(SAUDI_PRICES)} item referensi harga.")


# =============================================================================
# UI: TIPS & ANALYSIS
# =============================================================================

def render_tips_and_analysis():
    """Render tips, budget calculator, and AI analysis section."""

    # --- Section 1: Money Changer Tips ---
    st.markdown("### \U0001f4a1 Tips Penukaran Uang")

    for tip in MONEY_CHANGER_TIPS:
        st.markdown(
            f'<div class="tips-card">'
            f'<h4>{tip["title"]}</h4>'
            f'<p>{tip["desc"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # --- Section 2: Budget Quick Calculator ---
    st.markdown("### \U0001f9ee Budget Quick Calculator")

    budget_idr = st.number_input(
        "Total budget belanja harian (IDR)",
        min_value=0,
        max_value=100000000,
        value=st.session_state.kurs_budget_idr,
        step=500000,
        format="%d",
        key="input_budget_idr",
    )
    st.session_state.kurs_budget_idr = budget_idr

    budget_sar = idr_to_sar(float(budget_idr))
    budget_usd = sar_to_usd(budget_sar)

    # Metric cards
    mcol1, mcol2, mcol3 = st.columns(3)

    with mcol1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Budget IDR</div>'
            f'<div class="metric-value" style="color:#d4af37;">{format_idr(float(budget_idr))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with mcol2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Setara SAR</div>'
            f'<div class="metric-value" style="color:#4ade80;">{format_sar(budget_sar)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with mcol3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Setara USD</div>'
            f'<div class="metric-value" style="color:#60a5fa;">{format_usd(budget_usd)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Budget breakdown
    st.markdown("**Rekomendasi Alokasi Budget:**")

    for cat_key, cat_info in BUDGET_BREAKDOWN.items():
        pct = cat_info["pct"]
        alloc_sar = budget_sar * pct / 100
        alloc_idr = sar_to_idr(alloc_sar)

        st.markdown(
            f'<div class="budget-breakdown-item">'
            f'<div class="budget-breakdown-label">{cat_info["label"]}</div>'
            f'<div class="budget-breakdown-value">'
            f'<div class="budget-breakdown-pct">{pct}% &mdash; {format_sar(alloc_sar)}</div>'
            f'<div class="budget-breakdown-amount">{format_idr(alloc_idr)}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # --- Section 3: AI Analysis ---
    st.markdown("### \U0001f9e0 Analisis AI")
    st.caption(
        "Dapatkan saran pengelolaan budget umrah dari AI berdasarkan total budget Anda."
    )

    if st.button(
        "\U0001f9e0 Analisis Budget Saya",
        use_container_width=True,
        type="primary",
        key="btn_ai_budget_analysis",
    ):
        with st.spinner("AI sedang menganalisis budget Anda..."):
            # Build breakdown text
            breakdown_lines = []
            for cat_key, cat_info in BUDGET_BREAKDOWN.items():
                pct = cat_info["pct"]
                alloc_sar = budget_sar * pct / 100
                breakdown_lines.append(
                    f"- {cat_info['label']}: {pct}% = {format_sar(alloc_sar)}"
                )

            prompt_text = (
                f"Analisis budget belanja umrah berikut dan berikan saran pengelolaan:\n\n"
                f"Total Budget: {format_idr(float(budget_idr))} ({format_sar(budget_sar)})\n"
                f"Setara USD: {format_usd(budget_usd)}\n\n"
                f"Rencana alokasi:\n"
                + "\n".join(breakdown_lines)
                + "\n\nBerikan:\n"
                "1. Apakah budget ini cukup untuk umrah standar?\n"
                "2. Tips menghemat di setiap kategori\n"
                "3. Item apa saja yang bisa dibeli dengan budget ini\n"
                "4. Saran prioritas belanja\n"
                "Jawab dalam bahasa Indonesia yang sopan dan praktis."
            )

            system_prompt = (
                "Kamu adalah konsultan keuangan travel umrah berpengalaman. "
                "Berikan analisis singkat dan saran pengelolaan budget yang praktis "
                "untuk jamaah umrah Indonesia. Gunakan referensi harga di Arab Saudi "
                "yang realistis. Fokus pada tips yang bisa langsung diterapkan. "
                "Gunakan bahasa Indonesia yang sopan."
            )

            response = ai_complete(
                prompt_text, system_prompt=system_prompt, max_tokens=1024
            )

            if response:
                st.markdown(
                    f'<div class="ai-card">'
                    f'<h3>\U0001f9e0 Hasil Analisis AI</h3>'
                    f'<p>{_markdown_to_html_simple(response)}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if not st.session_state.kurs_ai_analysis_done:
                    st.session_state.kurs_ai_analysis_done = True
                    add_xp_safe(15, "Analisis AI budget umrah")
            else:
                render_budget_fallback(budget_sar)


# =============================================================================
# UI: BUDGET FALLBACK
# =============================================================================

def render_budget_fallback(budget_sar: float):
    """Render static budget tips when AI is unavailable."""
    st.markdown(
        '<div class="ai-card" style="border-color: #d4af37;">'
        '<h3 style="color: #d4af37;">\U0001f4a1 Saran Budget</h3>'
        '</div>',
        unsafe_allow_html=True,
    )

    if budget_sar < 500:
        st.markdown(
            "\U0001f4b0 **Budget Terbatas (< 500 SAR)**\n\n"
            "- Prioritaskan kebutuhan pokok: makan dan transportasi\n"
            "- Pilih shawarma dan nasi restoran lokal (hemat 50%)\n"
            "- Gunakan bus SAPTCO daripada taksi untuk jarak jauh\n"
            "- Belanja oleh-oleh secukupnya, pilih kurma Safawi yang lebih terjangkau\n"
            "- Bawa bekal snack dari Indonesia untuk camilan"
        )
    elif budget_sar < 1000:
        st.markdown(
            "\U0001f4b0 **Budget Menengah (500-1000 SAR)**\n\n"
            "- Cukup untuk makan teratur dan transportasi nyaman\n"
            "- Bisa beli oleh-oleh standar: kurma, minyak zaitun, sajadah\n"
            "- Gunakan Careem/Uber untuk transportasi harian\n"
            "- Sisihkan 20% untuk dana darurat\n"
            "- Coba Al Baik (fast food favorit) setidaknya sekali"
        )
    else:
        st.markdown(
            "\U0001f4b0 **Budget Cukup (> 1000 SAR)**\n\n"
            "- Budget cukup leluasa untuk semua kebutuhan\n"
            "- Bisa beli oleh-oleh premium: kurma Ajwa, parfum oud\n"
            "- Transportasi bisa lebih fleksibel dengan taksi\n"
            "- Jangan lupa tetap sisihkan dana darurat 20%\n"
            "- Bandingkan harga di beberapa toko sebelum membeli"
        )

    st.markdown(
        "\n**Tips Umum:**\n"
        "- Gunakan Careem/Uber karena lebih murah dari taksi biasa\n"
        "- Beli SIM card data lokal (STC/Mobily) untuk navigasi dan komunikasi\n"
        "- Makan di restoran yang agak jauh dari Haram biasanya lebih murah"
    )

    st.caption("AI tidak tersedia saat ini. Menampilkan saran bawaan.")


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_kurs_calculator_page():
    """Main entry point for the Kalkulator Kurs & Harga page."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("kurs_calculator")
    except Exception:
        pass

    # Initialize state
    init_kurs_state()

    # Hero
    render_hero()

    # Tabs
    tab_konversi, tab_harga, tab_tips = st.tabs([
        "\U0001f4b1 Konversi Kurs",
        "\U0001f4cb Referensi Harga",
        "\U0001f4a1 Tips & Analisis",
    ])

    with tab_konversi:
        render_currency_converter()

    with tab_harga:
        render_price_guide()

    with tab_tips:
        render_tips_and_analysis()

    # Disclaimer footer
    st.divider()
    st.warning(
        "\u26a0\ufe0f **DYOR - Do Your Own Research**\n\n"
        "Kurs dan harga yang ditampilkan adalah **estimasi** berdasarkan data rata-rata "
        "dan dapat berbeda dengan kondisi aktual. Kurs berubah setiap hari dan harga "
        "barang/jasa dapat bervariasi tergantung lokasi, musim, dan negosiasi.\n\n"
        "Selalu cek kurs terkini di money changer atau bank sebelum menukar uang. "
        "Bandingkan harga di beberapa toko sebelum membeli.\n\n"
        "**LABBAIK AI tidak bertanggung jawab atas perbedaan kurs dan harga aktual.**"
    )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_kurs_calculator_page"]
