"""
================================================================================
LABBAIK AI - SMART VISA & DOC CHECKER
================================================================================
Lokasi: ui/pages/doc_checker.py
Fitur: Checklist dokumen Umrah, cek validitas paspor, timeline, AI tips
================================================================================
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict, List

# =============================================================================
# CONSTANTS & DOCUMENT DATABASE
# =============================================================================

REQUIRED_DOCUMENTS = [
    {"id": "paspor", "name": "Paspor", "icon": "\U0001f4d8", "priority": "wajib",
     "processing_time": "14-30 hari kerja", "tips_short": "Berlaku min 7 bulan dari keberangkatan",
     "days_before": 120},
    {"id": "visa", "name": "Visa Umrah", "icon": "\U0001f4c4", "priority": "wajib",
     "processing_time": "7-14 hari", "tips_short": "Via travel agent atau mandiri via Nusuk app",
     "days_before": 30},
    {"id": "vaksin_meningitis", "name": "Vaksin Meningitis (ICV)", "icon": "\U0001f489", "priority": "wajib",
     "processing_time": "1 hari (min 10 hari sebelum berangkat)", "tips_short": "Wajib untuk masuk Saudi Arabia",
     "days_before": 14},
    {"id": "vaksin_covid", "name": "Vaksin COVID-19", "icon": "\U0001f489", "priority": "disarankan",
     "processing_time": "1 hari", "tips_short": "Minimal 2 dosis, booster disarankan",
     "days_before": 14},
    {"id": "foto", "name": "Pas Foto 4x6 (latar putih)", "icon": "\U0001f4f8", "priority": "wajib",
     "processing_time": "1 hari", "tips_short": "Background putih, tanpa kacamata",
     "days_before": 60},
    {"id": "ktp", "name": "KTP / E-KTP", "icon": "\U0001faaa", "priority": "wajib",
     "processing_time": "Sudah ada", "tips_short": "Pastikan masih berlaku",
     "days_before": 90},
    {"id": "kk", "name": "Kartu Keluarga", "icon": "\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466", "priority": "wajib",
     "processing_time": "Sudah ada", "tips_short": "Fotokopi yang masih berlaku",
     "days_before": 90},
    {"id": "buku_nikah", "name": "Buku Nikah / Akta Lahir", "icon": "\U0001f4cb", "priority": "wajib",
     "processing_time": "Sudah ada", "tips_short": "Untuk bukti hubungan mahram",
     "days_before": 90},
    {"id": "surat_mahram", "name": "Surat Izin Mahram (Wanita)", "icon": "\U0001f4dd", "priority": "kondisional",
     "processing_time": "1-3 hari", "tips_short": "Wajib untuk wanita <45 tahun tanpa mahram",
     "days_before": 30},
    {"id": "asuransi", "name": "Asuransi Perjalanan", "icon": "\U0001f6e1\ufe0f", "priority": "disarankan",
     "processing_time": "1 hari", "tips_short": "Cover kesehatan & kehilangan bagasi",
     "days_before": 14},
    {"id": "tiket", "name": "Tiket Pesawat", "icon": "\u2708\ufe0f", "priority": "wajib",
     "processing_time": "Bervariasi", "tips_short": "Booking jauh hari untuk harga terbaik",
     "days_before": 60},
]

STATUS_OPTIONS = ["belum", "proses", "selesai"]

STATUS_CONFIG = {
    "belum": {"label": "Belum", "color": "#ef4444", "bg": "#4a1a1a", "icon": "\u2b1c"},
    "proses": {"label": "Proses", "color": "#eab308", "bg": "#4a3a1a", "icon": "\U0001f504"},
    "selesai": {"label": "Selesai", "color": "#22c55e", "bg": "#1a4a1a", "icon": "\u2705"},
}

PRIORITY_CONFIG = {
    "wajib": {"label": "WAJIB", "color": "#fff", "bg": "#dc2626"},
    "disarankan": {"label": "Disarankan", "color": "#fff", "bg": "#2563eb"},
    "kondisional": {"label": "Kondisional", "color": "#000", "bg": "#eab308"},
}

DOC_TIPS_SYSTEM_PROMPT = """Anda adalah advisor persiapan dokumen umrah untuk WNI (Warga Negara Indonesia).
Berikan tips praktis untuk dokumen yang ditanyakan:
1. Langkah-langkah mendapatkan dokumen
2. Persyaratan yang dibutuhkan
3. Estimasi biaya (dalam Rupiah)
4. Lokasi pengurusan
5. Kesalahan umum yang harus dihindari
Jawab singkat (max 200 kata), praktis, dalam Bahasa Indonesia."""

# =============================================================================
# STYLING
# =============================================================================

DOC_CHECKER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');

.doc-hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid #d4af37;
    position: relative;
    overflow: hidden;
}

.doc-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at center, rgba(212,175,55,0.08) 0%, transparent 70%);
    animation: doc-hero-glow 6s ease-in-out infinite alternate;
}

@keyframes doc-hero-glow {
    0% { transform: translate(0, 0); }
    100% { transform: translate(10%, 10%); }
}

.doc-hero h1 {
    color: #d4af37;
    margin: 0 0 0.25rem 0;
    font-size: 2rem;
    position: relative;
    z-index: 1;
}

.doc-hero .arabic {
    font-size: 1.8rem;
    font-family: 'Amiri', serif;
    color: #d4af37;
    position: relative;
    z-index: 1;
}

.doc-hero .subtitle {
    color: #94a3b8;
    font-size: 1rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

/* Progress Section */
.doc-progress-container {
    background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid #334155;
    margin-bottom: 1rem;
}

.doc-progress-bar-outer {
    background: #1e293b;
    border-radius: 12px;
    height: 28px;
    overflow: hidden;
    position: relative;
    border: 1px solid #334155;
    margin: 0.75rem 0;
}

.doc-progress-bar-fill {
    height: 100%;
    border-radius: 12px;
    transition: width 0.6s ease;
    background: linear-gradient(90deg, #d4af37, #f4d03f, #d4af37);
    background-size: 200% 100%;
    animation: doc-progress-shimmer 2s linear infinite;
}

@keyframes doc-progress-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.doc-progress-text {
    position: absolute;
    width: 100%;
    text-align: center;
    line-height: 28px;
    color: #fff;
    font-weight: 700;
    font-size: 0.85rem;
    top: 0;
    left: 0;
    text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

/* Stat Cards */
.doc-stat-card {
    background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    text-align: center;
    border: 1px solid #334155;
}

.doc-stat-value {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
}

.doc-stat-label {
    color: #94a3b8;
    font-size: 0.8rem;
    margin: 0;
}

/* Document Cards */
.doc-card {
    background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    border-left: 5px solid #475569;
    transition: all 0.3s ease;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}

.doc-card:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.doc-card.status-belum { border-left-color: #ef4444; }
.doc-card.status-proses { border-left-color: #eab308; }
.doc-card.status-selesai { border-left-color: #22c55e; }

.doc-card-icon {
    font-size: 2rem;
    min-width: 40px;
    text-align: center;
}

.doc-card-body { flex: 1; }

.doc-card-title {
    color: #e2e8f0;
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0 0 0.3rem 0;
}

.doc-card-meta {
    color: #64748b;
    font-size: 0.8rem;
    margin: 0;
}

.doc-card-tip {
    color: #94a3b8;
    font-size: 0.82rem;
    margin-top: 0.25rem;
    font-style: italic;
}

/* Priority Badge */
.doc-priority-badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-left: 0.5rem;
    vertical-align: middle;
}

/* Status Badge */
.doc-status-badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Validity Warning Cards */
.doc-validity-ok {
    background: linear-gradient(135deg, #052e16 0%, #14532d 100%);
    border: 1px solid #22c55e;
    border-radius: 14px;
    padding: 1.25rem;
    color: #bbf7d0;
}

.doc-validity-warn {
    background: linear-gradient(135deg, #431407 0%, #7c2d12 100%);
    border: 1px solid #ef4444;
    border-radius: 14px;
    padding: 1.25rem;
    color: #fecaca;
}

.doc-validity-info {
    background: linear-gradient(135deg, #0c1a3a 0%, #1e3a5f 100%);
    border: 1px solid #3b82f6;
    border-radius: 14px;
    padding: 1.25rem;
    color: #bfdbfe;
}

/* Timeline */
.doc-timeline-item {
    background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    border-left: 4px solid #334155;
    display: flex;
    align-items: center;
    gap: 1rem;
}

.doc-timeline-item.urgent { border-left-color: #ef4444; }
.doc-timeline-item.soon { border-left-color: #eab308; }
.doc-timeline-item.ok { border-left-color: #22c55e; }
.doc-timeline-item.done { border-left-color: #6b7280; opacity: 0.6; }

.doc-timeline-days {
    min-width: 70px;
    text-align: center;
    font-weight: 700;
    font-size: 0.9rem;
    color: #d4af37;
}

.doc-timeline-name {
    color: #e2e8f0;
    font-size: 0.95rem;
    flex: 1;
}

.doc-timeline-processing {
    color: #64748b;
    font-size: 0.78rem;
}

/* AI Tips Section */
.doc-ai-tips {
    background: linear-gradient(135deg, #1a1a0d 0%, #2d2d19 100%);
    border: 1px solid #d4af37;
    border-radius: 14px;
    padding: 1.25rem;
    margin-top: 0.75rem;
    color: #e2e8f0;
    font-size: 0.9rem;
    line-height: 1.6;
}

.doc-ai-tips-header {
    color: #d4af37;
    font-weight: 700;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

/* Countdown */
.doc-countdown-box {
    background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
    color: #d4af37;
    font-size: 2.2rem;
    font-weight: 700;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    display: inline-block;
    border: 1px solid #d4af37;
    min-width: 65px;
    text-align: center;
}

.doc-countdown-label {
    color: #64748b;
    font-size: 0.75rem;
    text-align: center;
    margin-top: 0.25rem;
}

/* Disclaimer */
.doc-disclaimer {
    background: linear-gradient(145deg, #1c1917 0%, #292524 100%);
    border: 1px solid #78716c;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    color: #a8a29e;
    font-size: 0.82rem;
    line-height: 1.5;
}
</style>
"""

# =============================================================================
# SESSION STATE
# =============================================================================

def init_doc_checker_state():
    """Initialize all session state keys for doc checker."""
    if "doc_checklist" not in st.session_state:
        st.session_state.doc_checklist = {doc["id"]: "belum" for doc in REQUIRED_DOCUMENTS}
    if "doc_details" not in st.session_state:
        st.session_state.doc_details = {"paspor_expiry": None, "departure_date": None}
    if "doc_tips_cache" not in st.session_state:
        st.session_state.doc_tips_cache = {}


# =============================================================================
# AI TIPS
# =============================================================================

def get_ai_tips(doc_name: str) -> str:
    """Get AI-powered tips for a specific document.

    Uses Groq LLM via the standard service pattern. Results are cached
    in session state to avoid repeated API calls.
    """
    # Return cached result if available
    if doc_name in st.session_state.doc_tips_cache:
        return st.session_state.doc_tips_cache[doc_name]

    prompt_text = (
        f"Berikan tips lengkap untuk mengurus dokumen Umrah berikut: {doc_name}. "
        f"Sertakan langkah-langkah, persyaratan, estimasi biaya dalam Rupiah, "
        f"lokasi pengurusan, dan kesalahan umum yang harus dihindari."
    )
    system_prompt = DOC_TIPS_SYSTEM_PROMPT
    response = None

    try:
        from services.ai.chat_service import GroqChatService
        import os
        api_key = ""
        try:
            api_key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass
        if not api_key:
            api_key = os.getenv("GROQ_API_KEY", "")
        if api_key:
            service = GroqChatService(api_key=api_key)
            service.initialize()
            response = service.simple_complete(
                prompt=prompt_text,
                system_prompt=system_prompt,
                max_tokens=800
            )
    except Exception:
        response = None

    if response:
        st.session_state.doc_tips_cache[doc_name] = response
        return response

    return None


# =============================================================================
# GAMIFICATION HELPER
# =============================================================================

def add_xp(amount: int, reason: str = ""):
    """Add XP to the user's gamification score."""
    st.session_state.xp = st.session_state.get("xp", 0) + amount

    current_level = st.session_state.get("level", 1)
    xp_per_level = 100
    new_level = (st.session_state.xp // xp_per_level) + 1
    if new_level > current_level:
        st.session_state.level = new_level
        st.toast(f"Level Up! Level {new_level}")

    if reason:
        st.toast(f"+{amount} XP: {reason}")


# =============================================================================
# UI: HERO SECTION
# =============================================================================

def render_hero():
    """Render the hero banner at the top of the page."""
    st.markdown(DOC_CHECKER_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="doc-hero">
        <div class="arabic">\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0670\u0646\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0650\u064a\u0645\u0650</div>
        <h1>Smart Visa & Doc Checker</h1>
        <p class="subtitle">Kelola semua dokumen Umrah Anda di satu tempat. Pastikan semua siap sebelum berangkat.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# UI: PROGRESS SUMMARY
# =============================================================================

def render_progress_summary():
    """Render the progress bar and summary statistics."""
    checklist = st.session_state.doc_checklist
    total = len(REQUIRED_DOCUMENTS)
    selesai = sum(1 for s in checklist.values() if s == "selesai")
    proses = sum(1 for s in checklist.values() if s == "proses")
    belum = sum(1 for s in checklist.values() if s == "belum")
    pct = int((selesai / total) * 100) if total > 0 else 0

    # Wajib subset
    wajib_docs = [d for d in REQUIRED_DOCUMENTS if d["priority"] == "wajib"]
    wajib_selesai = sum(1 for d in wajib_docs if checklist.get(d["id"]) == "selesai")
    wajib_total = len(wajib_docs)

    st.markdown(f"""
    <div class="doc-progress-container">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.25rem;">
            <span style="color:#e2e8f0;font-weight:700;font-size:1.1rem;">Progres Dokumen</span>
            <span style="color:#d4af37;font-weight:700;font-size:1.1rem;">{selesai}/{total} selesai</span>
        </div>
        <div class="doc-progress-bar-outer">
            <div class="doc-progress-bar-fill" style="width:{pct}%;"></div>
            <div class="doc-progress-text">{pct}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stat cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="doc-stat-card">
            <p class="doc-stat-value" style="color:#22c55e;">{selesai}</p>
            <p class="doc-stat-label">Selesai</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="doc-stat-card">
            <p class="doc-stat-value" style="color:#eab308;">{proses}</p>
            <p class="doc-stat-label">Dalam Proses</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="doc-stat-card">
            <p class="doc-stat-value" style="color:#ef4444;">{belum}</p>
            <p class="doc-stat-label">Belum Mulai</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        wajib_color = "#22c55e" if wajib_selesai == wajib_total else "#ef4444"
        st.markdown(f"""
        <div class="doc-stat-card">
            <p class="doc-stat-value" style="color:{wajib_color};">{wajib_selesai}/{wajib_total}</p>
            <p class="doc-stat-label">Wajib Selesai</p>
        </div>
        """, unsafe_allow_html=True)

    if wajib_selesai < wajib_total:
        missing = [d["name"] for d in wajib_docs if checklist.get(d["id"]) != "selesai"]
        st.warning(f"Dokumen wajib belum lengkap: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")


# =============================================================================
# UI: VALIDITY CHECKER
# =============================================================================

def render_validity_checker():
    """Render passport validity check and departure date input."""
    st.markdown("### Tanggal & Validitas")

    col1, col2 = st.columns(2)

    with col1:
        today = date.today()
        default_departure = today + timedelta(days=90)
        departure_date = st.date_input(
            "Tanggal Keberangkatan",
            value=st.session_state.doc_details.get("departure_date") or default_departure,
            min_value=today,
            max_value=today + timedelta(days=730),
            key="input_departure_date",
            help="Pilih perkiraan tanggal keberangkatan Umrah Anda"
        )
        st.session_state.doc_details["departure_date"] = departure_date

    with col2:
        paspor_expiry = st.date_input(
            "Tanggal Kadaluarsa Paspor",
            value=st.session_state.doc_details.get("paspor_expiry") or (today + timedelta(days=365)),
            min_value=today - timedelta(days=365),
            max_value=today + timedelta(days=3650),
            key="input_paspor_expiry",
            help="Masukkan tanggal kadaluarsa paspor Anda"
        )
        st.session_state.doc_details["paspor_expiry"] = paspor_expiry

    # Departure countdown
    if departure_date:
        days_until = (departure_date - today).days
        if days_until > 0:
            months = days_until // 30
            remaining_days = days_until % 30

            st.markdown(f"""
            <div style="text-align:center;margin:1rem 0;">
                <p style="color:#94a3b8;font-size:0.85rem;margin-bottom:0.5rem;">Hitung Mundur Keberangkatan</p>
                <div style="display:flex;justify-content:center;gap:1rem;">
                    <div>
                        <div class="doc-countdown-box">{months}</div>
                        <div class="doc-countdown-label">Bulan</div>
                    </div>
                    <div>
                        <div class="doc-countdown-box">{remaining_days}</div>
                        <div class="doc-countdown-label">Hari</div>
                    </div>
                    <div>
                        <div class="doc-countdown-box">{days_until}</div>
                        <div class="doc-countdown-label">Total Hari</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif days_until == 0:
            st.markdown("""
            <div class="doc-validity-info">
                <strong>Hari ini adalah hari keberangkatan!</strong> Semoga perjalanan Umrah Anda lancar dan penuh berkah.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="doc-validity-warn">
                <strong>Tanggal keberangkatan sudah lewat.</strong> Silakan perbarui tanggal keberangkatan Anda.
            </div>
            """, unsafe_allow_html=True)

    # Passport validity check
    if paspor_expiry and departure_date:
        validity_days = (paspor_expiry - departure_date).days
        validity_months = validity_days / 30.0

        st.markdown("---")
        st.markdown("**Hasil Cek Validitas Paspor:**")

        if validity_months >= 7:
            st.markdown(f"""
            <div class="doc-validity-ok">
                <strong>PASPOR VALID</strong> - Masa berlaku paspor Anda {validity_days} hari
                ({validity_months:.1f} bulan) dari tanggal keberangkatan.
                Memenuhi syarat minimum 6 bulan (disarankan 7 bulan).
            </div>
            """, unsafe_allow_html=True)
        elif validity_months >= 6:
            st.markdown(f"""
            <div class="doc-validity-info">
                <strong>PASPOR VALID (BATAS MINIMUM)</strong> - Masa berlaku paspor Anda {validity_days} hari
                ({validity_months:.1f} bulan) dari tanggal keberangkatan. Ini memenuhi syarat minimum
                tetapi sangat disarankan untuk memperpanjang paspor demi keamanan.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="doc-validity-warn">
                <strong>PASPOR TIDAK VALID</strong> - Masa berlaku paspor Anda hanya {validity_days} hari
                ({validity_months:.1f} bulan) dari tanggal keberangkatan.
                Syarat minimum adalah 6 bulan. Segera perpanjang paspor Anda!
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# UI: DOCUMENT CHECKLIST
# =============================================================================

def render_document_checklist():
    """Render the interactive document checklist with status selectors and AI tips."""
    st.markdown("### Checklist Dokumen")

    checklist = st.session_state.doc_checklist

    for doc in REQUIRED_DOCUMENTS:
        doc_id = doc["id"]
        current_status = checklist.get(doc_id, "belum")
        status_cfg = STATUS_CONFIG[current_status]
        priority_cfg = PRIORITY_CONFIG[doc["priority"]]

        # Card HTML
        st.markdown(f"""
        <div class="doc-card status-{current_status}">
            <div class="doc-card-icon">{doc["icon"]}</div>
            <div class="doc-card-body">
                <p class="doc-card-title">
                    {doc["name"]}
                    <span class="doc-priority-badge" style="background:{priority_cfg['bg']};color:{priority_cfg['color']};">
                        {priority_cfg["label"]}
                    </span>
                </p>
                <p class="doc-card-meta">
                    Waktu proses: {doc["processing_time"]}
                    &nbsp;&bull;&nbsp;
                    <span class="doc-status-badge" style="background:{status_cfg['bg']};color:{status_cfg['color']};">
                        {status_cfg["icon"]} {status_cfg["label"]}
                    </span>
                </p>
                <p class="doc-card-tip">{doc["tips_short"]}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Controls row
        col_status, col_tips = st.columns([3, 1])

        with col_status:
            new_status = st.selectbox(
                f"Status {doc['name']}",
                options=STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current_status),
                format_func=lambda s: STATUS_CONFIG[s]["label"],
                key=f"status_{doc_id}",
                label_visibility="collapsed"
            )

            # Detect status change
            if new_status != current_status:
                old_status = current_status
                st.session_state.doc_checklist[doc_id] = new_status

                # Gamification: award XP when marking as selesai
                if new_status == "selesai" and old_status != "selesai":
                    add_xp(10, f"Dokumen {doc['name']} selesai")

                    # Check if all documents are complete
                    all_done = all(
                        st.session_state.doc_checklist[d["id"]] == "selesai"
                        for d in REQUIRED_DOCUMENTS
                    )
                    if all_done:
                        add_xp(50, "Semua dokumen Umrah lengkap!")
                        st.balloons()

                st.rerun()

        with col_tips:
            if st.button("Tips AI", key=f"tips_{doc_id}", use_container_width=True):
                st.session_state[f"show_tips_{doc_id}"] = True

        # AI Tips display (expanded on demand)
        if st.session_state.get(f"show_tips_{doc_id}", False):
            with st.spinner(f"Memuat tips untuk {doc['name']}..."):
                tips = get_ai_tips(doc["name"])

            if tips:
                st.markdown(f"""
                <div class="doc-ai-tips">
                    <div class="doc-ai-tips-header">Tips AI untuk {doc["name"]}</div>
                    {tips}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback tips when AI is not available
                st.markdown(f"""
                <div class="doc-ai-tips">
                    <div class="doc-ai-tips-header">Tips untuk {doc["name"]}</div>
                    <strong>Waktu proses:</strong> {doc["processing_time"]}<br>
                    <strong>Catatan:</strong> {doc["tips_short"]}<br>
                    <strong>Prioritas:</strong> {priority_cfg["label"]}<br><br>
                    <em>Tips AI tidak tersedia saat ini. Pastikan API key sudah dikonfigurasi.</em>
                </div>
                """, unsafe_allow_html=True)

            if st.button("Tutup Tips", key=f"close_tips_{doc_id}"):
                st.session_state[f"show_tips_{doc_id}"] = False
                st.rerun()

        st.markdown("<div style='margin-bottom:0.25rem;'></div>", unsafe_allow_html=True)


# =============================================================================
# UI: TIMELINE RECOMMENDATION
# =============================================================================

def render_timeline():
    """Render document preparation timeline based on departure date."""
    departure_date = st.session_state.doc_details.get("departure_date")
    if not departure_date:
        st.info("Masukkan tanggal keberangkatan untuk melihat timeline persiapan dokumen.")
        return

    st.markdown("### Timeline Persiapan Dokumen")

    today = date.today()
    days_until_departure = (departure_date - today).days
    checklist = st.session_state.doc_checklist

    # Sort documents by days_before (most lead time first)
    sorted_docs = sorted(REQUIRED_DOCUMENTS, key=lambda d: d["days_before"], reverse=True)

    for doc in sorted_docs:
        doc_id = doc["id"]
        status = checklist.get(doc_id, "belum")
        deadline_date = departure_date - timedelta(days=doc["days_before"])
        days_remaining = (deadline_date - today).days

        # Determine urgency class
        if status == "selesai":
            urgency_class = "done"
            urgency_text = "Selesai"
            urgency_color = "#6b7280"
        elif days_remaining < 0:
            urgency_class = "urgent"
            urgency_text = f"Terlambat {abs(days_remaining)} hari!"
            urgency_color = "#ef4444"
        elif days_remaining <= 14:
            urgency_class = "urgent"
            urgency_text = f"{days_remaining} hari lagi"
            urgency_color = "#ef4444"
        elif days_remaining <= 30:
            urgency_class = "soon"
            urgency_text = f"{days_remaining} hari lagi"
            urgency_color = "#eab308"
        else:
            urgency_class = "ok"
            urgency_text = f"{days_remaining} hari lagi"
            urgency_color = "#22c55e"

        target_date_str = deadline_date.strftime("%d %b %Y")
        status_icon = STATUS_CONFIG[status]["icon"]

        st.markdown(f"""
        <div class="doc-timeline-item {urgency_class}">
            <div class="doc-timeline-days" style="color:{urgency_color};">
                {urgency_text}
            </div>
            <div class="doc-timeline-name">
                {doc["icon"]} {doc["name"]} {status_icon}
            </div>
            <div class="doc-timeline-processing">
                Target: {target_date_str}<br>
                Proses: {doc["processing_time"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Summary advice
    overdue = [
        d for d in sorted_docs
        if checklist.get(d["id"]) != "selesai"
        and (departure_date - timedelta(days=d["days_before"]) - today).days < 0
    ]
    upcoming = [
        d for d in sorted_docs
        if checklist.get(d["id"]) != "selesai"
        and 0 <= (departure_date - timedelta(days=d["days_before"]) - today).days <= 14
    ]

    if overdue:
        names = ", ".join(d["name"] for d in overdue)
        st.error(f"Segera urus dokumen berikut yang sudah melewati tenggat: {names}")

    if upcoming:
        names = ", ".join(d["name"] for d in upcoming)
        st.warning(f"Dokumen berikut harus segera diurus dalam 2 minggu ke depan: {names}")

    if not overdue and not upcoming:
        incomplete = [d for d in sorted_docs if checklist.get(d["id"]) != "selesai"]
        if incomplete:
            st.success("Semua dokumen masih dalam jadwal. Terus pantau timeline Anda!")
        else:
            st.success("Semua dokumen sudah lengkap! Anda siap berangkat Umrah. Alhamdulillah!")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def render_doc_checker_page():
    """Main entry point for the Smart Visa & Doc Checker page."""

    # Initialize state
    init_doc_checker_state()

    # Hero
    render_hero()

    # Date inputs & validity
    render_validity_checker()

    st.divider()

    # Progress summary
    render_progress_summary()

    st.divider()

    # Document checklist
    render_document_checklist()

    st.divider()

    # Timeline
    render_timeline()

    # Disclaimer
    st.divider()
    st.markdown("""
    <div class="doc-disclaimer">
        <strong>Disclaimer:</strong> Informasi dokumen ini bersifat panduan umum berdasarkan
        persyaratan yang berlaku saat ini. Persyaratan dapat berubah sewaktu-waktu sesuai
        kebijakan Pemerintah Indonesia dan Kerajaan Saudi Arabia. Selalu konfirmasi
        persyaratan terbaru ke travel agent, Kedutaan Saudi, atau situs resmi
        <a href="https://www.nusuk.sa" target="_blank" style="color:#d4af37;">Nusuk</a>.
        LABBAIK AI tidak bertanggung jawab atas ketidaklengkapan dokumen.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_doc_checker_page"]
