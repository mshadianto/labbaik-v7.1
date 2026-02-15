"""
================================================================================
LABBAIK AI - AI UMRAH READINESS SCORE
================================================================================
Lokasi: ui/pages/readiness_checker.py
Fitur: Kuesioner kesiapan Umrah dengan skor AI dan rekomendasi personal
================================================================================
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import json

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS

# =============================================================================
# STYLING
# =============================================================================

READINESS_CSS = """
/* Page-specific overrides for readiness checker */
.readiness-hero {
    --hero-bg: linear-gradient(135deg, #1a2a1a 0%, #2d4a2d 100%);
    --hero-border: #4ade80;
    --hero-title: #4ade80;
}

.dimension-card {
    background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #333;
    border-left: 4px solid #4ade80;
}

.dimension-card h3 {
    color: #4ade80;
    margin-top: 0;
    font-size: 1.2rem;
}

.gauge-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem 1rem;
    background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 20px;
    border: 1px solid #333;
    margin-bottom: 1.5rem;
}

.gauge-outer {
    width: 220px;
    height: 110px;
    border-radius: 110px 110px 0 0;
    background: conic-gradient(
        from 180deg at 50% 100%,
        #ef4444 0deg,
        #f59e0b 60deg,
        #eab308 90deg,
        #22c55e 150deg,
        #4ade80 180deg
    );
    position: relative;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.gauge-inner {
    position: absolute;
    width: 170px;
    height: 85px;
    border-radius: 85px 85px 0 0;
    background: #1a1a1a;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: flex-end;
    justify-content: center;
    padding-bottom: 5px;
}

.gauge-needle {
    position: absolute;
    width: 4px;
    height: 80px;
    background: linear-gradient(to top, #d4af37, #f4d03f);
    bottom: 0;
    left: 50%;
    transform-origin: bottom center;
    border-radius: 2px;
    box-shadow: 0 0 8px rgba(212, 175, 55, 0.6);
    z-index: 2;
}

.gauge-center-dot {
    position: absolute;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #d4af37;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 3;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.8);
}

.gauge-score {
    font-size: 3rem;
    font-weight: bold;
    margin-top: 0.5rem;
}

.gauge-label {
    font-size: 1.1rem;
    font-weight: 600;
    margin-top: 0.25rem;
}

.gauge-sublabel {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin-top: 0.25rem;
}

.dim-progress-card {
    background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 15px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    border: 1px solid #333;
}

.dim-progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.dim-progress-title {
    color: white;
    font-weight: 600;
    font-size: 1rem;
}

.dim-progress-score {
    font-weight: bold;
    font-size: 1rem;
}

.dim-progress-bar-bg {
    width: 100%;
    height: 10px;
    background: #333;
    border-radius: 5px;
    overflow: hidden;
}

.dim-progress-bar-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.8s ease;
}

.rec-card {
    background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 0.75rem;
    border: 1px solid #333;
    border-left: 4px solid #d4af37;
}

.rec-card h4 {
    color: #d4af37;
    margin-top: 0;
    margin-bottom: 0.75rem;
}

.rec-card p {
    color: #ccc;
    line-height: 1.6;
    margin: 0;
}

.export-box {
    background: linear-gradient(135deg, #1a3a1a 0%, #2d4a2d 100%);
    border: 1px solid #4ade80;
    border-radius: 15px;
    padding: 1.5rem;
    text-align: center;
    margin-top: 1rem;
}

.stats-card .number {
    color: #4ade80;
}
"""

# =============================================================================
# QUESTIONNAIRE DATA
# =============================================================================

DIMENSIONS = {
    "dokumen": {
        "title": "Dokumen",
        "icon": "📄",
        "color": "#60a5fa",
        "max_score": 25,
        "questions": [
            {
                "id": "paspor",
                "text": "Status paspor Anda saat ini",
                "type": "selectbox",
                "options": [
                    "Belum ada",
                    "Ada tapi masa berlaku <6 bulan",
                    "Siap (>6 bulan)",
                ],
                "scores": [0, 4, 8],
            },
            {
                "id": "visa",
                "text": "Pemahaman proses visa umrah",
                "type": "selectbox",
                "options": [
                    "Belum tahu",
                    "Sedikit paham",
                    "Sangat paham",
                ],
                "scores": [0, 4, 8],
            },
            {
                "id": "vaksin",
                "text": "Status vaksin meningitis",
                "type": "selectbox",
                "options": [
                    "Belum",
                    "Dalam proses",
                    "Sudah lengkap",
                ],
                "scores": [0, 5, 9],
            },
        ],
    },
    "budget": {
        "title": "Budget",
        "icon": "💰",
        "color": "#fbbf24",
        "max_score": 25,
        "questions": [
            {
                "id": "dana_persen",
                "text": "Persentase dana umrah yang sudah terkumpul",
                "type": "slider",
                "min": 0,
                "max": 100,
                "default": 30,
                "suffix": "%",
                "max_points": 10,
            },
            {
                "id": "estimasi_biaya",
                "text": "Estimasi rincian biaya umrah",
                "type": "selectbox",
                "options": [
                    "Belum ada",
                    "Estimasi kasar",
                    "Perhitungan detail",
                ],
                "scores": [0, 4, 8],
            },
            {
                "id": "dana_darurat",
                "text": "Dana darurat selama di Tanah Suci",
                "type": "selectbox",
                "options": [
                    "Tidak ada",
                    "< Rp 5 juta",
                    "Rp 5-10 juta",
                    "> Rp 10 juta",
                ],
                "scores": [0, 2, 5, 7],
            },
        ],
    },
    "kesehatan": {
        "title": "Kesehatan",
        "icon": "🏥",
        "color": "#f87171",
        "max_score": 25,
        "questions": [
            {
                "id": "fisik",
                "text": "Kesiapan fisik berjalan 5-10 km/hari",
                "type": "slider",
                "min": 1,
                "max": 10,
                "default": 5,
                "suffix": "/10",
                "max_points": 10,
            },
            {
                "id": "penyakit_kronis",
                "text": "Kondisi penyakit kronis",
                "type": "selectbox",
                "options": [
                    "Tidak ada",
                    "Ada tapi terkontrol",
                    "Ada dan perlu perhatian",
                ],
                "scores": [8, 5, 2],
            },
            {
                "id": "vaksinasi_umum",
                "text": "Status vaksinasi umum (COVID, Influenza, dll)",
                "type": "selectbox",
                "options": [
                    "Belum",
                    "Sebagian",
                    "Lengkap",
                ],
                "scores": [0, 4, 7],
            },
        ],
    },
    "manasik": {
        "title": "Pengetahuan Manasik",
        "icon": "📿",
        "color": "#c084fc",
        "max_score": 25,
        "questions": [
            {
                "id": "rukun_umrah",
                "text": "Pemahaman rukun umrah (ihram, thawaf, sa'i, tahallul)",
                "type": "slider",
                "min": 1,
                "max": 10,
                "default": 5,
                "suffix": "/10",
                "max_points": 7,
            },
            {
                "id": "hafal_doa",
                "text": "Hafalan doa-doa umrah",
                "type": "selectbox",
                "options": [
                    "Belum",
                    "Sebagian kecil",
                    "Sebagian besar",
                    "Semua",
                ],
                "scores": [0, 2, 5, 7],
            },
            {
                "id": "bimbingan",
                "text": "Pengalaman bimbingan manasik",
                "type": "selectbox",
                "options": [
                    "Belum",
                    "Online saja",
                    "Tatap muka",
                ],
                "scores": [0, 3, 5],
            },
            {
                "id": "bahasa_arab",
                "text": "Kemampuan bahasa Arab dasar",
                "type": "slider",
                "min": 1,
                "max": 10,
                "default": 3,
                "suffix": "/10",
                "max_points": 6,
            },
        ],
    },
}

# Score level definitions
SCORE_LEVELS = [
    {"min": 0, "max": 25, "label": "Perlu Persiapan Intensif", "color": "#ef4444", "emoji": "🔴"},
    {"min": 26, "max": 50, "label": "Persiapan Awal", "color": "#f59e0b", "emoji": "🟡"},
    {"min": 51, "max": 75, "label": "Cukup Siap", "color": "#22c55e", "emoji": "🟢"},
    {"min": 76, "max": 100, "label": "Sangat Siap", "color": "#4ade80", "emoji": "✅"},
]

# System prompt for AI recommendations
AI_SYSTEM_PROMPT = (
    "Anda adalah AI advisor untuk persiapan Umrah. "
    "Berdasarkan jawaban kuesioner, berikan 5-8 rekomendasi personal yang spesifik, "
    "actionable, dan prioritas jelas. "
    "Format setiap rekomendasi sebagai: **[PRIORITAS] Judul** - deskripsi. "
    "Gunakan prioritas: TINGGI, SEDANG, RENDAH. "
    "Jawab dalam Bahasa Indonesia."
)


# =============================================================================
# SESSION STATE
# =============================================================================

def init_readiness_state():
    """Initialize readiness checker session state."""
    if "readiness_answers" not in st.session_state:
        st.session_state.readiness_answers = {}
    if "readiness_score" not in st.session_state:
        st.session_state.readiness_score = None
    if "readiness_recommendations" not in st.session_state:
        st.session_state.readiness_recommendations = None
    if "readiness_completed" not in st.session_state:
        st.session_state.readiness_completed = False
    if "readiness_timestamp" not in st.session_state:
        st.session_state.readiness_timestamp = None


# =============================================================================
# SCORE CALCULATION
# =============================================================================

def calculate_readiness_score(answers: Dict) -> Dict:
    """
    Calculate readiness score from questionnaire answers.

    Returns a dict with:
        - total: int (0-100)
        - dimensions: dict of dimension scores
        - level: dict with label, color, emoji
        - answers_summary: dict mapping question id to answer text
    """
    dimensions = {}
    answers_summary = {}
    total = 0

    for dim_key, dim_data in DIMENSIONS.items():
        dim_score = 0

        for question in dim_data["questions"]:
            qid = question["id"]
            answer = answers.get(qid)

            if answer is None:
                continue

            if question["type"] == "selectbox":
                idx = answer if isinstance(answer, int) else 0
                idx = max(0, min(idx, len(question["scores"]) - 1))
                points = question["scores"][idx]
                dim_score += points
                answers_summary[qid] = question["options"][idx]

            elif question["type"] == "slider":
                value = answer if isinstance(answer, (int, float)) else question["default"]
                slider_range = question["max"] - question["min"]
                if slider_range > 0:
                    normalized = (value - question["min"]) / slider_range
                else:
                    normalized = 0
                points = round(normalized * question["max_points"])
                dim_score += points
                answers_summary[qid] = f"{value}{question.get('suffix', '')}"

        # Cap dimension score at max
        dim_score = min(dim_score, dim_data["max_score"])

        dimensions[dim_key] = {
            "title": dim_data["title"],
            "icon": dim_data["icon"],
            "color": dim_data["color"],
            "score": dim_score,
            "max": dim_data["max_score"],
            "percentage": round(dim_score / dim_data["max_score"] * 100) if dim_data["max_score"] > 0 else 0,
        }

        total += dim_score

    # Determine level
    level = SCORE_LEVELS[0]
    for sl in SCORE_LEVELS:
        if sl["min"] <= total <= sl["max"]:
            level = sl
            break

    return {
        "total": total,
        "dimensions": dimensions,
        "level": level,
        "answers_summary": answers_summary,
    }


# =============================================================================
# AI RECOMMENDATIONS
# =============================================================================

def generate_ai_recommendations(score: Dict, answers: Dict) -> str:
    """
    Generate AI-powered recommendations based on score and answers.

    Uses the Groq service with the standard LABBAIK AI pattern.
    Returns recommendation text or None on failure.
    """
    # Build the prompt with context
    dims = score.get("dimensions", {})
    summary = score.get("answers_summary", {})

    prompt_lines = [
        f"Skor Kesiapan Umrah: {score['total']}/100",
        f"Level: {score['level']['label']}",
        "",
        "Skor per dimensi:",
    ]

    for dim_key, dim_info in dims.items():
        prompt_lines.append(
            f"- {dim_info['icon']} {dim_info['title']}: {dim_info['score']}/{dim_info['max']} "
            f"({dim_info['percentage']}%)"
        )

    prompt_lines.append("")
    prompt_lines.append("Detail jawaban:")

    for dim_key, dim_data in DIMENSIONS.items():
        for question in dim_data["questions"]:
            qid = question["id"]
            answer_text = summary.get(qid, "Tidak dijawab")
            prompt_lines.append(f"- {question['text']}: {answer_text}")

    prompt_lines.append("")
    prompt_lines.append(
        "Berikan rekomendasi personal berdasarkan data di atas. "
        "Fokus pada area yang skornya rendah. "
        "Sertakan timeline persiapan jika memungkinkan."
    )

    prompt_text = "\n".join(prompt_lines)

    return ai_complete(prompt_text, system_prompt=AI_SYSTEM_PROMPT, max_tokens=1024)


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_hero():
    """Render hero section with CSS."""
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, READINESS_CSS)

    st.markdown("""
    <div class="readiness-hero">
        <div class="ayat">وَأَتِمُّوا الْحَجَّ وَالْعُمْرَةَ لِلَّهِ</div>
        <h1>Umrah Readiness Score</h1>
        <p class="subtitle">Ukur kesiapan Anda untuk menunaikan ibadah Umrah</p>
    </div>
    """, unsafe_allow_html=True)


def render_questionnaire():
    """
    Render the interactive questionnaire across 4 dimensions.

    Populates st.session_state.readiness_answers with raw answer values.
    Returns True if the user clicks the calculate button, False otherwise.
    """
    answers = st.session_state.readiness_answers

    st.markdown("### Kuesioner Kesiapan Umrah")
    st.caption(
        "Jawab seluruh pertanyaan di bawah ini untuk menghitung skor kesiapan Anda. "
        "Semua data hanya tersimpan di sesi browser Anda."
    )

    for dim_key, dim_data in DIMENSIONS.items():
        st.markdown(
            f'<div class="dimension-card">'
            f'<h3>{dim_data["icon"]} {dim_data["title"]}</h3>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for question in dim_data["questions"]:
            qid = question["id"]

            if question["type"] == "selectbox":
                current = answers.get(qid, 0)
                if not isinstance(current, int):
                    current = 0
                current = max(0, min(current, len(question["options"]) - 1))

                selected = st.selectbox(
                    question["text"],
                    options=list(range(len(question["options"]))),
                    format_func=lambda idx, opts=question["options"]: opts[idx],
                    index=current,
                    key=f"rq_{qid}",
                )
                answers[qid] = selected

            elif question["type"] == "slider":
                current = answers.get(qid, question["default"])
                if not isinstance(current, (int, float)):
                    current = question["default"]

                value = st.slider(
                    question["text"],
                    min_value=question["min"],
                    max_value=question["max"],
                    value=current,
                    key=f"rq_{qid}",
                )
                answers[qid] = value

        st.markdown("")  # spacing

    st.session_state.readiness_answers = answers

    # Calculate button
    st.markdown("---")
    calculate_clicked = st.button(
        "Hitung Skor Kesiapan Saya",
        use_container_width=True,
        type="primary",
        key="btn_calculate_readiness",
    )

    return calculate_clicked


def render_score_display(score: Dict):
    """
    Render the visual score gauge and dimension breakdown.

    Uses CSS-based gauge (no Plotly).
    """
    total = score["total"]
    level = score["level"]
    dimensions = score["dimensions"]

    # --- Gauge ---
    # Needle rotation: 0 = far left (-90deg), 100 = far right (90deg)
    needle_deg = -90 + (total / 100) * 180

    st.markdown(
        f"""
        <div class="gauge-container">
            <div class="gauge-outer">
                <div class="gauge-inner"></div>
                <div class="gauge-needle" style="transform: translateX(-50%) rotate({needle_deg}deg);"></div>
                <div class="gauge-center-dot"></div>
            </div>
            <div class="gauge-score" style="color: {level['color']};">{total}</div>
            <div class="gauge-label" style="color: {level['color']};">{level['emoji']} {level['label']}</div>
            <div class="gauge-sublabel">dari 100 poin maksimal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Stats Row ---
    cols = st.columns(4)
    for i, (dim_key, dim_info) in enumerate(dimensions.items()):
        with cols[i]:
            st.markdown(
                f"""
                <div class="stats-card">
                    <div class="number" style="color: {dim_info['color']};">{dim_info['score']}</div>
                    <div class="label">{dim_info['icon']} {dim_info['title']} (/{dim_info['max']})</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")

    # --- Dimension Breakdown with Progress Bars ---
    st.markdown("### Breakdown per Dimensi")

    for dim_key, dim_info in dimensions.items():
        pct = dim_info["percentage"]

        # Color coding based on percentage
        if pct >= 75:
            bar_color = "#4ade80"
            score_color = "#4ade80"
        elif pct >= 50:
            bar_color = "#22c55e"
            score_color = "#22c55e"
        elif pct >= 25:
            bar_color = "#f59e0b"
            score_color = "#f59e0b"
        else:
            bar_color = "#ef4444"
            score_color = "#ef4444"

        st.markdown(
            f"""
            <div class="dim-progress-card">
                <div class="dim-progress-header">
                    <span class="dim-progress-title">{dim_info['icon']} {dim_info['title']}</span>
                    <span class="dim-progress-score" style="color: {score_color};">{dim_info['score']}/{dim_info['max']} ({pct}%)</span>
                </div>
                <div class="dim-progress-bar-bg">
                    <div class="dim-progress-bar-fill" style="width: {pct}%; background: linear-gradient(90deg, {bar_color}, {dim_info['color']});"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_recommendations(recs: str):
    """Render AI-generated recommendations."""
    st.markdown("### Rekomendasi AI untuk Anda")

    if recs:
        st.markdown(
            f"""
            <div class="rec-card">
                <h4>Rekomendasi Personal dari AI</h4>
                <p>{recs.replace(chr(10), '<br>')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "Rekomendasi AI tidak tersedia saat ini. "
            "Berikut panduan umum berdasarkan skor Anda:"
        )
        _render_fallback_recommendations()


def _render_fallback_recommendations():
    """Render static fallback recommendations when AI is unavailable."""
    score = st.session_state.readiness_score
    if not score:
        return

    dims = score.get("dimensions", {})
    tips = []

    # Dokumen
    dok = dims.get("dokumen", {})
    if dok.get("percentage", 0) < 50:
        tips.append(
            "**[TINGGI] Persiapkan Dokumen Segera** - "
            "Urus paspor (pastikan masa berlaku >6 bulan), pahami proses visa umrah, "
            "dan selesaikan vaksinasi meningitis di klinik kesehatan pelabuhan."
        )

    # Budget
    bud = dims.get("budget", {})
    if bud.get("percentage", 0) < 50:
        tips.append(
            "**[TINGGI] Perkuat Perencanaan Keuangan** - "
            "Buat rincian biaya detail (tiket, hotel, transport, makan, oleh-oleh). "
            "Siapkan dana darurat minimal Rp 5 juta untuk kebutuhan tak terduga."
        )

    # Kesehatan
    kes = dims.get("kesehatan", {})
    if kes.get("percentage", 0) < 50:
        tips.append(
            "**[TINGGI] Tingkatkan Kebugaran Fisik** - "
            "Mulai latihan jalan kaki 5 km/hari secara bertahap. "
            "Konsultasikan kondisi kesehatan ke dokter dan lengkapi vaksinasi."
        )

    # Manasik
    man = dims.get("manasik", {})
    if man.get("percentage", 0) < 50:
        tips.append(
            "**[TINGGI] Pelajari Manasik Umrah** - "
            "Ikuti bimbingan manasik tatap muka, hafalkan doa thawaf dan sa'i, "
            "dan pelajari bahasa Arab dasar untuk percakapan sederhana."
        )

    if not tips:
        tips.append(
            "**[RENDAH] Pertahankan Persiapan** - "
            "Persiapan Anda sudah baik. Terus perkuat hafalan doa "
            "dan jaga kebugaran fisik menjelang keberangkatan."
        )

    for tip in tips:
        st.markdown(f"- {tip}")


def render_export_section(score: Dict):
    """Render export results as text download."""
    total = score["total"]
    level = score["level"]
    dims = score["dimensions"]
    summary = score.get("answers_summary", {})
    recs = st.session_state.readiness_recommendations

    # Build text
    lines = []
    lines.append("=" * 55)
    lines.append("   UMRAH READINESS SCORE - LABBAIK AI")
    lines.append("=" * 55)
    lines.append(f"Tanggal      : {datetime.now().strftime('%d %B %Y, %H:%M')}")
    lines.append(f"Skor Total   : {total}/100")
    lines.append(f"Level        : {level['label']}")
    lines.append("")
    lines.append("-" * 55)
    lines.append("SKOR PER DIMENSI:")
    lines.append("-" * 55)

    for dim_key, dim_info in dims.items():
        bar_filled = round(dim_info["percentage"] / 5)
        bar = "#" * bar_filled + "." * (20 - bar_filled)
        lines.append(
            f"  {dim_info['icon']} {dim_info['title']:20s} "
            f"{dim_info['score']:2d}/{dim_info['max']:2d}  "
            f"[{bar}] {dim_info['percentage']}%"
        )

    lines.append("")
    lines.append("-" * 55)
    lines.append("JAWABAN:")
    lines.append("-" * 55)

    for dim_key, dim_data in DIMENSIONS.items():
        lines.append(f"\n  {dim_data['icon']} {dim_data['title']}:")
        for question in dim_data["questions"]:
            qid = question["id"]
            ans = summary.get(qid, "-")
            lines.append(f"    - {question['text']}: {ans}")

    if recs:
        lines.append("")
        lines.append("-" * 55)
        lines.append("REKOMENDASI AI:")
        lines.append("-" * 55)
        lines.append(recs)

    lines.append("")
    lines.append("=" * 55)
    lines.append("Generated by LABBAIK AI - https://app.labbaik.io")
    lines.append("=" * 55)

    export_text = "\n".join(lines)

    st.markdown(
        """
        <div class="export-box">
            <h3 style="color:#4ade80;margin-top:0;">Simpan Hasil Anda</h3>
            <p style="color:#b0b0b0;">Download hasil readiness check untuk referensi pribadi</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "Download Hasil (TXT)",
            data=export_text,
            file_name=f"readiness_umrah_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:
        json_data = json.dumps(
            {
                "score": total,
                "level": level["label"],
                "dimensions": {
                    k: {"score": v["score"], "max": v["max"], "percentage": v["percentage"]}
                    for k, v in dims.items()
                },
                "answers": summary,
                "recommendations": recs,
                "timestamp": datetime.now().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        )
        st.download_button(
            "Download Hasil (JSON)",
            data=json_data,
            file_name=f"readiness_umrah_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )


# =============================================================================
# MAIN PAGE FUNCTION
# =============================================================================

def render_readiness_checker_page():
    """Main entry point for the Umrah Readiness Checker page."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("readiness_checker")
    except Exception:
        pass

    # Initialize state
    init_readiness_state()

    # Hero
    render_hero()

    # If already completed, show results with option to retake
    if st.session_state.readiness_completed and st.session_state.readiness_score:
        score = st.session_state.readiness_score

        # Score display
        render_score_display(score)

        st.divider()

        # Recommendations
        render_recommendations(st.session_state.readiness_recommendations)

        st.divider()

        # Export
        render_export_section(score)

        st.divider()

        # Timestamp
        ts = st.session_state.readiness_timestamp
        if ts:
            st.caption(f"Terakhir dihitung: {ts}")

        # Retake button
        st.markdown("")
        if st.button("Ulangi Kuesioner", use_container_width=True, key="btn_retake"):
            st.session_state.readiness_completed = False
            st.session_state.readiness_score = None
            st.session_state.readiness_recommendations = None
            st.session_state.readiness_answers = {}
            st.session_state.readiness_timestamp = None
            st.rerun()

        # Disclaimer
        st.divider()
        st.warning(
            "**DYOR - Do Your Own Research**\n\n"
            "Skor ini bersifat panduan umum dan bukan merupakan fatwa atau nasihat resmi. "
            "Konsultasikan persiapan Umrah Anda dengan ustadz, travel agent terpercaya, "
            "dan tenaga medis profesional.\n\n"
            "**LABBAIK AI tidak bertanggung jawab atas keputusan berdasarkan skor ini.**"
        )
        return

    # --- Questionnaire Flow ---
    calculate_clicked = render_questionnaire()

    if calculate_clicked:
        answers = st.session_state.readiness_answers

        # Validate: check that at least some answers exist
        answered_count = sum(1 for q_id in answers if answers[q_id] is not None)
        total_questions = sum(len(d["questions"]) for d in DIMENSIONS.values())

        if answered_count < total_questions:
            # Still proceed -- unanswered questions default to lowest score
            pass

        # Calculate score
        score = calculate_readiness_score(answers)
        st.session_state.readiness_score = score
        st.session_state.readiness_timestamp = datetime.now().strftime("%d %B %Y, %H:%M WIB")

        # Generate AI recommendations
        with st.spinner("AI sedang menganalisis dan menyiapkan rekomendasi personal..."):
            recs = generate_ai_recommendations(score, answers)
            st.session_state.readiness_recommendations = recs

        # Gamification: award XP
        add_xp_safe(50, "Menyelesaikan Readiness Check")

        # Mark as completed and rerun to show results
        st.session_state.readiness_completed = True
        st.rerun()


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_readiness_checker_page"]
