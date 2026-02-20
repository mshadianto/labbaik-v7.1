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
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SKELETON_CSS, render_skeleton

# Try to import doc checker document list for cross-page integration
try:
    from ui.pages.doc_checker import REQUIRED_DOCUMENTS as _DOC_CHECKER_DOCUMENTS
    _DOC_CHECKER_TOTAL = len(_DOC_CHECKER_DOCUMENTS)
except Exception:
    _DOC_CHECKER_DOCUMENTS = None
    _DOC_CHECKER_TOTAL = 11  # fallback count

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

/* Doc completion supplementary card */
.doc-completion-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    margin: 1rem 0;
    border: 1px solid #334155;
    border-left: 4px solid #60a5fa;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.doc-completion-card .doc-icon {
    font-size: 1.5rem;
}

.doc-completion-card .doc-info {
    flex: 1;
    min-width: 180px;
}

.doc-completion-card .doc-title {
    color: #e2e8f0;
    font-weight: 600;
    font-size: 0.95rem;
}

.doc-completion-card .doc-progress {
    color: #60a5fa;
    font-size: 0.85rem;
    margin-top: 0.2rem;
}

.doc-completion-card .doc-warning {
    color: #f59e0b;
    font-size: 0.82rem;
    margin-top: 0.3rem;
}

.doc-completion-bar {
    width: 100%;
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
    overflow: hidden;
    margin-top: 0.5rem;
}

.doc-completion-bar-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #60a5fa, #3b82f6);
    transition: width 0.4s ease;
}
"""

# =============================================================================
# COACHING PLAN CSS
# =============================================================================

COACHING_CSS = """
/* Coaching Plan Timeline */
.coaching-section-header {
    background: linear-gradient(135deg, #1a2a3a 0%, #2d3a4a 100%);
    border: 1px solid #d4af37;
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
}

.coaching-section-header h3 {
    color: #d4af37;
    margin: 0 0 0.25rem 0;
    font-size: 1.3rem;
}

.coaching-section-header p {
    color: #b0b0b0;
    margin: 0;
    font-size: 0.9rem;
}

.coaching-track-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding: 0.75rem 1rem;
    background: linear-gradient(135deg, #1a1a2e 0%, #2d2d4a 100%);
    border-radius: 12px;
    border-left: 4px solid var(--track-color, #d4af37);
}

.coaching-track-header .track-icon {
    font-size: 1.5rem;
}

.coaching-track-header .track-title {
    color: white;
    font-weight: 700;
    font-size: 1.1rem;
}

.coaching-track-header .track-score {
    margin-left: auto;
    color: var(--track-color, #d4af37);
    font-weight: 600;
    font-size: 0.9rem;
}

.coaching-timeline {
    position: relative;
    padding-left: 2rem;
    margin-left: 1rem;
    margin-bottom: 1.5rem;
}

.coaching-timeline::before {
    content: '';
    position: absolute;
    left: 0.5rem;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(to bottom, #444, #333);
    border-radius: 2px;
}

.coaching-step {
    position: relative;
    background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    border: 1px solid #333;
    transition: border-color 0.3s ease;
}

.coaching-step:hover {
    border-color: #555;
}

.coaching-step::before {
    content: '';
    position: absolute;
    left: -1.75rem;
    top: 1.5rem;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 3px solid;
    z-index: 1;
}

.coaching-step.step-pending::before {
    background: #333;
    border-color: #666;
}

.coaching-step.step-current::before {
    background: #d4af37;
    border-color: #f4d03f;
    box-shadow: 0 0 8px rgba(212, 175, 55, 0.6);
}

.coaching-step.step-done::before {
    background: #4ade80;
    border-color: #22c55e;
    box-shadow: 0 0 8px rgba(74, 222, 128, 0.4);
}

.coaching-step .step-timeframe {
    display: inline-block;
    background: rgba(212, 175, 55, 0.15);
    color: #d4af37;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.coaching-step .step-title {
    color: white;
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 0.4rem;
}

.coaching-step .step-desc {
    color: #b8c5d4;
    font-size: 0.9rem;
    line-height: 1.5;
    margin-bottom: 0.5rem;
}

.coaching-step .step-meta {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
}

.coaching-step .step-priority {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.coaching-step .priority-tinggi {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
}

.coaching-step .priority-sedang {
    background: rgba(251, 191, 36, 0.2);
    color: #fbbf24;
}

.coaching-step .step-effort {
    color: #8e9fb3;
    font-size: 0.8rem;
}

.coaching-ai-tip {
    background: linear-gradient(135deg, #1a2a1a 0%, #2d4a2d 100%);
    border: 1px solid #4ade80;
    border-radius: 15px;
    padding: 1.5rem;
    margin-top: 1rem;
}

.coaching-ai-tip h4 {
    color: #4ade80;
    margin-top: 0;
    margin-bottom: 0.75rem;
}

.coaching-ai-tip p {
    color: #ccc;
    line-height: 1.6;
    margin: 0;
}

@media (max-width: 768px) {
    .coaching-timeline {
        padding-left: 1.5rem;
        margin-left: 0.5rem;
    }

    .coaching-step {
        padding: 1rem;
    }

    .coaching-step::before {
        left: -1.35rem;
        width: 12px;
        height: 12px;
    }

    .coaching-step .step-meta {
        gap: 0.5rem;
    }

    .coaching-track-header {
        flex-wrap: wrap;
    }

    .coaching-track-header .track-score {
        margin-left: 0;
        width: 100%;
        margin-top: 0.25rem;
    }
}

@media (max-width: 480px) {
    .coaching-step {
        padding: 0.85rem;
    }

    .coaching-section-header {
        padding: 1rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    .coaching-step {
        transition: none;
    }
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

# System prompt for coaching plan AI tip
COACHING_AI_SYSTEM_PROMPT = (
    "Anda adalah coach persiapan Umrah yang berpengalaman. "
    "Berikan 1 tip motivasi dan actionable yang personal berdasarkan area lemah jamaah. "
    "Singkat (2-3 kalimat), hangat, dan mendorong semangat. "
    "Jawab dalam Bahasa Indonesia."
)

# =============================================================================
# COACHING TRACKS DATA
# =============================================================================

COACHING_TRACKS = {
    "dokumen": {
        "title": "Dokumen",
        "icon": "\U0001f4c4",
        "color": "#60a5fa",
        "steps": [
            {
                "title": "Cek paspor",
                "description": (
                    "Periksa masa berlaku paspor Anda. Pastikan masih berlaku minimal "
                    "6 bulan dari tanggal keberangkatan. Jika belum ada atau sudah "
                    "expired, segera urus pembuatan/perpanjangan di kantor imigrasi terdekat."
                ),
                "timeframe": "Minggu 1-2",
                "priority": "tinggi",
                "effort": "2-5 hari kerja",
            },
            {
                "title": "Apply visa umrah",
                "description": (
                    "Pelajari persyaratan visa umrah terbaru. Siapkan dokumen pendukung: "
                    "foto ukuran 4x6 latar putih, bukti vaksin meningitis, dan formulir "
                    "aplikasi. Koordinasikan dengan travel agent untuk proses pengajuan."
                ),
                "timeframe": "Minggu 3-4",
                "priority": "tinggi",
                "effort": "3-7 hari kerja",
            },
            {
                "title": "Vaksinasi meningitis",
                "description": (
                    "Lakukan vaksinasi meningitis di Kantor Kesehatan Pelabuhan (KKP) "
                    "terdekat. Bawa paspor dan foto. Sertifikat ICV (International "
                    "Certificate of Vaccination) berlaku 3 tahun dan wajib untuk masuk "
                    "Arab Saudi."
                ),
                "timeframe": "Minggu 3-6",
                "priority": "tinggi",
                "effort": "1 hari",
            },
            {
                "title": "Kumpulkan dokumen pendukung",
                "description": (
                    "Siapkan semua dokumen pelengkap: KTP, Kartu Keluarga, akta nikah "
                    "(jika berpasangan), surat izin suami/wali (untuk wanita), dan "
                    "dokumen lain yang diminta travel agent. Buat salinan fisik dan "
                    "digital semua dokumen penting."
                ),
                "timeframe": "Minggu 5-8",
                "priority": "sedang",
                "effort": "2-3 hari",
            },
        ],
    },
    "budget": {
        "title": "Budget",
        "icon": "\U0001f4b0",
        "color": "#fbbf24",
        "steps": [
            {
                "title": "Hitung total biaya",
                "description": (
                    "Buat rincian lengkap biaya umrah: tiket pesawat, hotel Makkah & "
                    "Madinah, transportasi lokal, makan, perlengkapan ibadah, oleh-oleh, "
                    "dan biaya tak terduga. Gunakan fitur Simulasi Biaya LABBAIK untuk "
                    "estimasi akurat."
                ),
                "timeframe": "Minggu 1-2",
                "priority": "tinggi",
                "effort": "2-3 jam",
            },
            {
                "title": "Buat rencana tabungan",
                "description": (
                    "Tentukan target menabung bulanan berdasarkan total biaya dan waktu "
                    "keberangkatan. Pertimbangkan tabungan umrah syariah atau deposito "
                    "untuk menjaga konsistensi. Sisihkan minimal 20-30% penghasilan "
                    "bulanan untuk dana umrah."
                ),
                "timeframe": "Minggu 3-4",
                "priority": "tinggi",
                "effort": "1-2 jam + konsisten",
            },
            {
                "title": "Siapkan dana darurat",
                "description": (
                    "Alokasikan dana darurat minimal Rp 5-10 juta di luar biaya paket "
                    "umrah. Dana ini untuk kebutuhan tak terduga selama di Tanah Suci: "
                    "kesehatan, transportasi tambahan, atau perpanjangan penginapan."
                ),
                "timeframe": "Minggu 5-8",
                "priority": "sedang",
                "effort": "Bertahap",
            },
            {
                "title": "Review & optimasi",
                "description": (
                    "Bandingkan harga paket dari beberapa travel agent. Cek promo tiket "
                    "pesawat dan hotel. Gunakan fitur Price Hub LABBAIK untuk "
                    "perbandingan harga. Pastikan semua pembayaran terjadwal dan "
                    "terdokumentasi."
                ),
                "timeframe": "Minggu 9-12",
                "priority": "sedang",
                "effort": "3-5 jam",
            },
        ],
    },
    "kesehatan": {
        "title": "Kesehatan",
        "icon": "\U0001f3e5",
        "color": "#f87171",
        "steps": [
            {
                "title": "Medical checkup",
                "description": (
                    "Lakukan pemeriksaan kesehatan menyeluruh: tekanan darah, gula "
                    "darah, kolesterol, fungsi jantung, dan paru-paru. Konsultasikan "
                    "kemampuan fisik Anda untuk ibadah umrah yang membutuhkan stamina "
                    "tinggi."
                ),
                "timeframe": "Minggu 1-2",
                "priority": "tinggi",
                "effort": "1 hari",
            },
            {
                "title": "Mulai olahraga rutin",
                "description": (
                    "Tingkatkan stamina secara bertahap. Mulai dengan jalan kaki 2-3 "
                    "km/hari, naikkan ke 5-10 km/hari. Latih juga naik-turun tangga "
                    "dan berdiri lama. Thawaf dan Sa'i membutuhkan daya tahan yang baik."
                ),
                "timeframe": "Minggu 1-8",
                "priority": "tinggi",
                "effort": "30-60 menit/hari",
            },
            {
                "title": "Vaksinasi lengkap",
                "description": (
                    "Selain meningitis (wajib), pertimbangkan vaksin influenza, COVID "
                    "booster, dan pneumonia terutama untuk lansia. Konsultasikan dengan "
                    "dokter vaksin apa saja yang direkomendasikan untuk perjalanan ke "
                    "Arab Saudi."
                ),
                "timeframe": "Minggu 3-6",
                "priority": "sedang",
                "effort": "1-2 kunjungan",
            },
            {
                "title": "Persiapan obat pribadi",
                "description": (
                    "Siapkan obat-obatan rutin dalam jumlah cukup plus cadangan. Bawa "
                    "P3K: obat flu, diare, sakit kepala, plester, dan hand sanitizer. "
                    "Minta surat keterangan dokter untuk obat resep yang dibawa."
                ),
                "timeframe": "Minggu 7-8",
                "priority": "sedang",
                "effort": "2-3 jam",
            },
        ],
    },
    "manasik": {
        "title": "Pengetahuan Manasik",
        "icon": "\U0001f4ff",
        "color": "#c084fc",
        "steps": [
            {
                "title": "Pelajari rukun umrah",
                "description": (
                    "Pahami secara mendalam 4 rukun umrah: Ihram (niat & miqat), "
                    "Thawaf (mengelilingi Ka'bah 7 kali), Sa'i (berjalan antara Shafa "
                    "dan Marwah 7 kali), dan Tahallul (mencukur/memotong rambut). "
                    "Pelajari juga wajib dan sunnah umrah."
                ),
                "timeframe": "Minggu 1-4",
                "priority": "tinggi",
                "effort": "1-2 jam/hari",
            },
            {
                "title": "Hafalan doa",
                "description": (
                    "Hafalkan doa-doa utama: niat ihram, doa thawaf setiap putaran, "
                    "doa di Multazam, doa Sa'i, dan doa-doa harian di Tanah Suci. "
                    "Gunakan fitur Doa Player LABBAIK untuk membantu hafalan dengan "
                    "audio."
                ),
                "timeframe": "Minggu 3-8",
                "priority": "tinggi",
                "effort": "30 menit/hari",
            },
            {
                "title": "Ikut bimbingan manasik",
                "description": (
                    "Ikuti bimbingan manasik tatap muka dari travel agent atau masjid. "
                    "Praktik langsung gerakan thawaf, sa'i, dan tahallul. Bimbingan "
                    "tatap muka lebih efektif daripada belajar online saja."
                ),
                "timeframe": "Minggu 5-10",
                "priority": "tinggi",
                "effort": "2-4 sesi",
            },
            {
                "title": "Praktik mandiri",
                "description": (
                    "Lakukan simulasi mandiri: praktikkan urutan ibadah dari awal "
                    "hingga akhir. Latih membaca doa sambil berjalan. Pelajari juga "
                    "bahasa Arab dasar untuk komunikasi sederhana di Tanah Suci."
                ),
                "timeframe": "Minggu 9-12",
                "priority": "sedang",
                "effort": "1 jam/hari",
            },
        ],
    },
}


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


def render_doc_completion_card():
    """Render a supplementary card showing doc checker completion status.

    Reads doc_checklist from session state (populated by doc_checker page).
    Shows X/11 documents completed with a progress bar, and a warning
    if completion is below 50%.
    """
    doc_checklist = st.session_state.get("doc_checklist", {})
    total = _DOC_CHECKER_TOTAL

    if doc_checklist:
        completed = sum(1 for s in doc_checklist.values() if s == "selesai")
    else:
        completed = 0

    pct = round(completed / total * 100) if total > 0 else 0

    warning_html = ""
    if pct < 50:
        warning_html = (
            '<div class="doc-warning">'
            '<span aria-hidden="true">\u26a0\ufe0f</span> '
            'Lengkapi dokumen untuk meningkatkan skor kesiapan'
            '</div>'
        )

    st.markdown(
        f'<div class="doc-completion-card">'
        f'<div class="doc-icon" aria-hidden="true">\U0001f4c4</div>'
        f'<div class="doc-info">'
        f'<div class="doc-title">Dokumen Anda: {completed}/{total} selesai</div>'
        f'<div class="doc-progress">{pct}% kelengkapan dokumen</div>'
        f'{warning_html}'
        f'<div class="doc-completion-bar">'
        f'<div class="doc-completion-bar-fill" style="width: {pct}%;"></div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "\U0001f4c4 Buka Cek Dokumen",
        key="btn_nav_doc_checker_from_readiness",
        use_container_width=False,
    ):
        st.session_state.nav = "doc_checker"
        st.rerun()


def render_recommendations(recs: str):
    """Render AI-generated recommendations."""
    st.markdown("### Rekomendasi AI untuk Anda")

    if recs:
        st.markdown(
            f"""
            <div class="rec-card" role="status" aria-live="polite">
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
# COACHING PLAN
# =============================================================================

def render_coaching_plan(score: Dict, dimension_scores: Dict, answers: Dict):
    """
    Render a personalized coaching plan based on weak dimensions.

    Generates timeline-based coaching tracks for dimensions scoring < 60% of max.
    Includes AI-powered personalized tip with fallback.

    Args:
        score: Full score dict from calculate_readiness_score()
        dimension_scores: The 'dimensions' sub-dict from the score
        answers: Raw answers dict from session state
    """
    # Inject coaching CSS
    inject_css(COACHING_CSS)

    # Identify weak dimensions (< 60% of max)
    weak_dims = []
    for dim_key, dim_info in dimension_scores.items():
        if dim_info["percentage"] < 60:
            weak_dims.append(dim_key)

    # If no weak dimensions, show congratulations instead
    if not weak_dims:
        st.markdown(
            '<div class="coaching-section-header">'
            '<h3><span aria-hidden="true">\U0001f3af</span> Coaching Plan</h3>'
            '<p>Semua dimensi kesiapan Anda sudah baik! Pertahankan persiapan '
            'dan terus tingkatkan menjelang keberangkatan.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # Section header
    weak_count = len(weak_dims)
    st.markdown(
        '<div class="coaching-section-header">'
        '<h3><span aria-hidden="true">\U0001f3af</span> Coaching Plan Personal</h3>'
        f'<p>Rencana persiapan bertahap untuk {weak_count} area yang perlu ditingkatkan</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Render coaching tracks for each weak dimension
    for dim_key in weak_dims:
        track = COACHING_TRACKS.get(dim_key)
        if not track:
            continue

        dim_info = dimension_scores[dim_key]
        pct = dim_info["percentage"]
        track_color = track["color"]

        # Track header
        st.markdown(
            f'<div class="coaching-track-header" style="--track-color: {track_color};">'
            f'<span class="track-icon" aria-hidden="true">{track["icon"]}</span>'
            f'<span class="track-title">{track["title"]}</span>'
            f'<span class="track-score">{dim_info["score"]}/{dim_info["max"]} ({pct}%)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Timeline with steps
        steps_html_parts = []
        for i, step in enumerate(track["steps"]):
            # First step is "current", rest are "pending"
            step_status = "step-current" if i == 0 else "step-pending"

            # Priority badge
            priority_class = f"priority-{step['priority']}"
            priority_label = step["priority"].upper()

            steps_html_parts.append(
                f'<div class="coaching-step {step_status}">'
                f'<div class="step-timeframe">{step["timeframe"]}</div>'
                f'<div class="step-title">{step["title"]}</div>'
                f'<div class="step-desc">{step["description"]}</div>'
                f'<div class="step-meta">'
                f'<span class="step-priority {priority_class}">{priority_label}</span>'
                f'<span class="step-effort">\U0000231b {step["effort"]}</span>'
                f'</div>'
                f'</div>'
            )

        timeline_html = "\n".join(steps_html_parts)
        st.markdown(
            f'<div class="coaching-timeline">{timeline_html}</div>',
            unsafe_allow_html=True,
        )

    # AI-powered personalized tip
    _render_coaching_ai_tip(score, weak_dims, dimension_scores, answers)

    # Gamification: award XP for generating coaching plan
    if "coaching_plan_xp_awarded" not in st.session_state:
        add_xp_safe(20, "Membuat Coaching Plan")
        st.session_state.coaching_plan_xp_awarded = True


def _render_coaching_ai_tip(
    score: Dict,
    weak_dims: List[str],
    dimension_scores: Dict,
    answers: Dict,
):
    """Generate and render an AI-powered coaching tip for weak dimensions."""
    # Build context for AI
    weak_info_lines = []
    for dim_key in weak_dims:
        dim_info = dimension_scores[dim_key]
        weak_info_lines.append(
            f"- {dim_info['title']}: {dim_info['score']}/{dim_info['max']} ({dim_info['percentage']}%)"
        )

    summary = score.get("answers_summary", {})
    answer_lines = []
    for dim_key in weak_dims:
        dim_data = DIMENSIONS.get(dim_key, {})
        for question in dim_data.get("questions", []):
            qid = question["id"]
            ans_text = summary.get(qid, "Tidak dijawab")
            answer_lines.append(f"- {question['text']}: {ans_text}")

    prompt = (
        f"Skor kesiapan umrah: {score['total']}/100.\n"
        f"Area lemah:\n" + "\n".join(weak_info_lines) + "\n\n"
        f"Detail jawaban area lemah:\n" + "\n".join(answer_lines) + "\n\n"
        "Berikan 1 tip coaching personal yang motivatif dan actionable "
        "untuk membantu jamaah ini memulai persiapan."
    )

    skeleton_placeholder = st.empty()
    with skeleton_placeholder:
        st.markdown(SKELETON_CSS, unsafe_allow_html=True)
        render_skeleton(skeleton_type="text")

    with st.spinner("AI menyiapkan tip coaching personal..."):
        ai_tip = ai_complete(
            prompt,
            system_prompt=COACHING_AI_SYSTEM_PROMPT,
            max_tokens=512,
        )

    skeleton_placeholder.empty()

    if ai_tip:
        st.markdown(
            f'<div class="coaching-ai-tip" role="status" aria-live="polite">'
            f'<h4><span aria-hidden="true">\U0001f4a1</span> Tip Coach AI untuk Anda</h4>'
            f'<p>{ai_tip.replace(chr(10), "<br>")}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        # Fallback static tip
        fallback_tips = {
            "dokumen": (
                "Mulailah dari yang paling mendasar: pastikan paspor Anda masih berlaku. "
                "Satu langkah kecil hari ini akan membuka jalan menuju Tanah Suci."
            ),
            "budget": (
                "Mulai sisihkan dana secara rutin, sekecil apapun. Konsistensi menabung "
                "lebih penting daripada jumlah besar di awal."
            ),
            "kesehatan": (
                "Mulai jalan kaki 15-30 menit setiap hari mulai hari ini. Ibadah di "
                "Tanah Suci membutuhkan stamina yang baik, dan tubuh sehat adalah modal utama."
            ),
            "manasik": (
                "Pelajari satu rukun umrah setiap minggu. Dengan memahami makna setiap "
                "ibadah, perjalanan Anda akan jauh lebih bermakna dan khusyuk."
            ),
        }
        # Pick the tip for the first weak dimension
        first_weak = weak_dims[0] if weak_dims else "dokumen"
        tip_text = fallback_tips.get(first_weak, fallback_tips["dokumen"])

        st.markdown(
            f'<div class="coaching-ai-tip" role="status" aria-live="polite">'
            f'<h4><span aria-hidden="true">\U0001f4a1</span> Tip untuk Anda</h4>'
            f'<p>{tip_text}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )


# =============================================================================
# CROSS-PAGE NAVIGATION CSS
# =============================================================================

CROSS_NAV_CSS = """
.cross-nav-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1.5rem 0;
}

.cross-nav-card h3 {
    color: #d4af37;
    margin-top: 0;
    margin-bottom: 0.25rem;
    font-size: 1.1rem;
}

.cross-nav-card .cross-nav-subtitle {
    color: #b0b0b0;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}

.cross-nav-hint {
    background: linear-gradient(135deg, #2d1a0a 0%, #3d2a1a 100%);
    border: 1px solid #f59e0b;
    border-left: 4px solid #f59e0b;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.cross-nav-hint .hint-icon {
    font-size: 1.25rem;
}

.cross-nav-hint .hint-text {
    color: #b8c5d4;
    font-size: 0.85rem;
}

.cross-nav-hint .hint-text strong {
    color: #f59e0b;
}
"""


# =============================================================================
# CROSS-PAGE NAVIGATION
# =============================================================================

def _render_contextual_nav(score: Dict):
    """Render contextual cross-page navigation buttons based on low-scoring dimensions."""
    st.markdown(CROSS_NAV_CSS, unsafe_allow_html=True)

    dims = score.get("dimensions", {})

    # Gather suggestions based on low scores
    suggestions = []

    dokumen_pct = dims.get("dokumen", {}).get("percentage", 100)
    budget_pct = dims.get("budget", {}).get("percentage", 100)
    manasik_pct = dims.get("manasik", {}).get("percentage", 100)

    if dokumen_pct < 60:
        suggestions.append({
            "hint": "Skor <strong>Dokumen</strong> Anda masih rendah. Periksa kelengkapan dokumen umrah.",
            "icon": "\U0001f4c4",
            "label": "\U0001f4c4 Cek Dokumen Anda",
            "key": "nav_to_doc_checker",
            "target": "doc_checker",
        })

    if budget_pct < 60:
        suggestions.append({
            "hint": "Skor <strong>Budget</strong> Anda masih rendah. Hitung dan pantau biaya umrah.",
            "icon": "\U0001f4b0",
            "label": "\U0001f4b0 Hitung Budget",
            "key": "nav_to_cost_tracker",
            "target": "cost_tracker",
        })

    if manasik_pct < 60:
        suggestions.append({
            "hint": "Skor <strong>Manasik</strong> Anda masih rendah. Pelajari tata cara ibadah umrah.",
            "icon": "\U0001f4ff",
            "label": "\U0001f4ff Latihan Manasik",
            "key": "nav_to_manasik",
            "target": "manasik",
        })

    st.markdown(
        '<div class="cross-nav-card">'
        '<h3><span aria-hidden="true">\U0001f9ed</span> Tingkatkan Kesiapan Anda</h3>'
        '<div class="cross-nav-subtitle">Berdasarkan hasil skor, berikut langkah yang disarankan</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Render contextual hints and buttons
    for suggestion in suggestions:
        st.markdown(
            f'<div class="cross-nav-hint">'
            f'<span class="hint-icon" aria-hidden="true">{suggestion["icon"]}</span>'
            f'<div class="hint-text">{suggestion["hint"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Build button columns: contextual suggestions + always-present booking
    button_items = suggestions + [
        {
            "label": "\U0001f54b Mulai Perencanaan",
            "key": "nav_to_booking_from_readiness",
            "target": "booking",
        }
    ]

    cols = st.columns(len(button_items))
    for i, item in enumerate(button_items):
        with cols[i]:
            if st.button(
                item["label"],
                key=item["key"],
                use_container_width=True,
            ):
                st.session_state.nav = item["target"]
                st.rerun()


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

        # Doc checker completion supplementary card
        render_doc_completion_card()

        # Contextual cross-page navigation based on dimension scores
        _render_contextual_nav(score)

        st.divider()

        # Recommendations
        render_recommendations(st.session_state.readiness_recommendations)

        st.divider()

        # Coaching Plan
        render_coaching_plan(score, score["dimensions"], st.session_state.readiness_answers)

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
            st.session_state.coaching_plan_xp_awarded = False
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

        # Generate AI recommendations — show skeleton while loading
        skeleton_placeholder = st.empty()
        with skeleton_placeholder:
            st.markdown(SKELETON_CSS, unsafe_allow_html=True)
            render_skeleton(skeleton_type="text")
            render_skeleton(skeleton_type="cards", count=2)

        with st.spinner("AI sedang menganalisis dan menyiapkan rekomendasi personal..."):
            recs = generate_ai_recommendations(score, answers)
            st.session_state.readiness_recommendations = recs

        skeleton_placeholder.empty()

        # Gamification: award XP
        add_xp_safe(50, "Menyelesaikan Readiness Check")

        # Mark as completed and rerun to show results
        st.session_state.readiness_completed = True
        st.rerun()


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_readiness_checker_page"]
