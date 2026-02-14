"""
================================================================================
LABBAIK AI - TANYA USTADZ AI
================================================================================
Lokasi: ui/pages/tanya_ustadz.py
Fitur: Community Tanya Ustadz AI - Q&A fiqih umrah dengan dalil & rujukan
================================================================================
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import os
import re

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, EMPTY_STATE_CSS

# =============================================================================
# CONSTANTS & DATA
# =============================================================================

USTADZ_SYSTEM_PROMPT = """Anda adalah AI ustadz yang ahli dalam fiqih umrah dan haji, terutama berdasarkan madzhab Syafi'i (mayoritas Indonesia).

Panduan menjawab:
1. Gunakan Bahasa Indonesia yang jelas dan mudah dipahami
2. Sertakan dalil Al-Quran atau Hadits yang relevan
3. Rujuk kitab fiqih klasik jika memungkinkan (Al-Majmu', Fathul Qarib, dll)
4. Berikan kesimpulan singkat di akhir
5. Jika pertanyaan di luar konteks umrah/ibadah, arahkan kembali ke topik umrah
6. Hindari kontroversi antar madzhab - fokus pada pendapat yang lebih kuat di madzhab Syafi'i

Format jawaban:
**Jawaban:**
[Penjelasan utama 2-3 paragraf]

**Dalil:**
[Ayat Al-Quran atau Hadits jika relevan]

**Rujukan:**
[Nama kitab atau ulama]

**Kesimpulan:**
[Ringkasan singkat 1-2 kalimat]"""

CATEGORIES = {
    "semua": {"icon": "📋", "label": "Semua"},
    "tawaf": {"icon": "🕋", "label": "Tawaf"},
    "sai": {"icon": "🏃", "label": "Sa'i"},
    "ihram": {"icon": "🤍", "label": "Ihram"},
    "doa": {"icon": "🤲", "label": "Doa & Dzikir"},
    "umum": {"icon": "📖", "label": "Umum"},
}

POPULAR_QUESTIONS = [
    {"q": "Apa saja rukun umrah yang wajib dilaksanakan?", "cat": "umum"},
    {"q": "Bolehkah wanita umrah tanpa mahram?", "cat": "umum"},
    {"q": "Apa yang membatalkan umrah?", "cat": "umum"},
    {"q": "Berapa kali putaran tawaf dan bagaimana tata caranya?", "cat": "tawaf"},
    {"q": "Doa apa yang dibaca saat sa'i antara Safa dan Marwah?", "cat": "sai"},
    {"q": "Apa saja larangan saat ihram?", "cat": "ihram"},
    {"q": "Bolehkah memakai parfum saat ihram?", "cat": "ihram"},
    {"q": "Bagaimana tata cara umrah saat haid?", "cat": "umum"},
    {"q": "Doa apa yang dibaca saat melihat Ka'bah pertama kali?", "cat": "doa"},
    {"q": "Apakah boleh umrah berkali-kali dalam satu perjalanan?", "cat": "umum"},
]

# Fallback answers for when AI service is unavailable
FALLBACK_ANSWERS = {
    "rukun umrah": """**Jawaban:**
Rukun umrah ada empat menurut madzhab Syafi'i, yaitu: (1) Ihram, yakni berniat masuk ke dalam ibadah umrah dari miqat; (2) Tawaf mengelilingi Ka'bah sebanyak 7 putaran; (3) Sa'i antara bukit Safa dan Marwah sebanyak 7 kali; (4) Tahallul dengan mencukur atau memotong rambut.

Keempat rukun ini wajib dilakukan secara berurutan. Jika salah satu rukun ditinggalkan, maka umrah tidak sah dan harus diulang.

**Dalil:**
"Dan sempurnakanlah ibadah haji dan umrah karena Allah." (QS. Al-Baqarah: 196)

Hadits Rasulullah SAW tentang tata cara umrah diriwayatkan oleh Jabir bin Abdullah ra. dalam Shahih Muslim.

**Rujukan:**
- Al-Majmu' Syarh al-Muhadzdzab, Imam Nawawi
- Fathul Qarib, Ibnu Qasim al-Ghazi
- Kifayatul Akhyar, Imam Taqiyuddin

**Kesimpulan:**
Rukun umrah ada empat: Ihram, Tawaf, Sa'i, dan Tahallul. Semuanya wajib dilakukan berurutan agar umrah sah.""",

    "default": """**Jawaban:**
Terima kasih atas pertanyaan Anda. Ini adalah pertanyaan yang baik terkait fiqih umrah.

Untuk memberikan jawaban yang akurat dan lengkap dengan dalil yang tepat, layanan AI sedang tidak tersedia saat ini. Silakan coba beberapa saat lagi.

**Dalil:**
"Maka bertanyalah kepada orang yang mempunyai pengetahuan jika kamu tidak mengetahui." (QS. An-Nahl: 43)

**Rujukan:**
Konsultasikan pertanyaan Anda dengan ustadz atau ulama setempat.

**Kesimpulan:**
Pastikan API key sudah dikonfigurasi (GROQ_API_KEY) untuk mengaktifkan layanan Ustadz AI secara penuh.""",
}

# =============================================================================
# STYLING
# =============================================================================

TANYA_USTADZ_CSS = """
/* Page-specific styles for Tanya Ustadz */
.ustadz-hero {
    background: linear-gradient(135deg, #0d1b0d 0%, #1a3a1a 50%, #0d2b0d 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(74, 222, 128, 0.3);
    position: relative;
    overflow: hidden;
}

.ustadz-hero::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 50% 0%, rgba(74, 222, 128, 0.08) 0%, transparent 60%);
    pointer-events: none;
}

.ustadz-hero h1 {
    color: #4ade80;
    margin: 0 0 0.3rem 0;
    font-size: 2.2rem;
    font-family: 'Amiri', serif;
    position: relative;
}

.ustadz-hero .subtitle {
    color: #94a3b8;
    font-size: 1rem;
    margin-bottom: 1rem;
    position: relative;
}

.ustadz-hero .bismillah {
    color: #4ade80;
    font-family: 'Amiri', serif;
    font-size: 1.6rem;
    margin-bottom: 0.5rem;
    opacity: 0.85;
    position: relative;
}

.ustadz-hero .disclaimer {
    background: rgba(74, 222, 128, 0.08);
    border: 1px solid rgba(74, 222, 128, 0.2);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    color: #94a3b8;
    font-size: 0.82rem;
    margin-top: 1rem;
    position: relative;
}

.category-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: center;
    margin: 1rem 0;
}

.category-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #333;
    background: #1a1a2e;
    color: #94a3b8;
}

.category-pill.active {
    background: linear-gradient(135deg, #166534 0%, #15803d 100%);
    border-color: #4ade80;
    color: #fff;
    box-shadow: 0 0 12px rgba(74, 222, 128, 0.2);
}

.category-pill:hover {
    border-color: #4ade80;
    color: #4ade80;
}

.qa-card {
    background: linear-gradient(145deg, #111827 0%, #1a1a2e 100%);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #4ade80;
    transition: transform 0.2s;
}

.qa-card:hover {
    transform: translateY(-1px);
}

.qa-card .qa-question {
    color: #e2e8f0;
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
}

.qa-card .qa-question .q-icon {
    color: #4ade80;
    font-size: 1.1rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
}

.qa-card .qa-answer {
    color: #cbd5e1;
    font-size: 0.93rem;
    line-height: 1.7;
    padding-left: 0.5rem;
}

.qa-card .qa-answer strong {
    color: #4ade80;
}

.qa-card .qa-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 0.8rem;
    padding-top: 0.6rem;
    border-top: 1px solid rgba(74, 222, 128, 0.1);
}

.qa-card .qa-meta .qa-category {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.75rem;
    background: rgba(74, 222, 128, 0.1);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.2);
}

.qa-card .qa-meta .qa-time {
    color: #64748b;
    font-size: 0.78rem;
}

.popular-card {
    background: linear-gradient(145deg, #111827 0%, #1e1e36 100%);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
    border: 1px solid #2d2d4a;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.popular-card:hover {
    border-color: #4ade80;
    background: linear-gradient(145deg, #162016 0%, #1a2a1a 100%);
    transform: translateX(4px);
}

.popular-card .pop-icon {
    font-size: 1.1rem;
    flex-shrink: 0;
}

.popular-card .pop-text {
    color: #e2e8f0;
    font-size: 0.88rem;
}

.popular-card .pop-cat {
    margin-left: auto;
    flex-shrink: 0;
    padding: 0.15rem 0.5rem;
    border-radius: 10px;
    font-size: 0.7rem;
    background: rgba(74, 222, 128, 0.1);
    color: #4ade80;
}

.stats-row {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 1rem 0;
}

.stat-item {
    text-align: center;
}

.stat-item .stat-num {
    color: #4ade80;
    font-size: 1.6rem;
    font-weight: 700;
}

.stat-item .stat-label {
    color: #64748b;
    font-size: 0.78rem;
}

.section-title {
    color: #e2e8f0;
    font-size: 1.15rem;
    font-weight: 600;
    margin: 1.5rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #64748b;
}

.empty-state .empty-icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.empty-state .empty-text {
    font-size: 0.95rem;
    color: #94a3b8;
}

.spinner-text {
    text-align: center;
    padding: 1.5rem;
    color: #4ade80;
    font-size: 0.95rem;
}
"""

# =============================================================================
# SESSION STATE
# =============================================================================

def init_tanya_ustadz_state():
    """Initialize tanya ustadz session state."""
    if "tanya_history" not in st.session_state:
        st.session_state.tanya_history = []
    if "tanya_category" not in st.session_state:
        st.session_state.tanya_category = "semua"
    if "tanya_pending_question" not in st.session_state:
        st.session_state.tanya_pending_question = ""
    if "tanya_is_loading" not in st.session_state:
        st.session_state.tanya_is_loading = False


# =============================================================================
# AI SERVICE
# =============================================================================

def get_ai_answer(question: str, category: str) -> str:
    """Get AI answer for the given question using Groq service.

    Args:
        question: The user's fiqih question.
        category: The question category (tawaf, sai, ihram, doa, umum).

    Returns:
        The AI-generated answer string, or a fallback if unavailable.
    """
    category_info = CATEGORIES.get(category, CATEGORIES["umum"])
    category_label = category_info["label"]

    prompt_text = f"[Kategori: {category_label}]\n\nPertanyaan:\n{question}"

    response = ai_complete(prompt_text, system_prompt=USTADZ_SYSTEM_PROMPT, max_tokens=1500)

    if response:
        return response

    # Fallback: try to match a known answer
    q_lower = question.lower()
    if "rukun" in q_lower and "umrah" in q_lower:
        return FALLBACK_ANSWERS["rukun umrah"]

    return FALLBACK_ANSWERS["default"]


# =============================================================================
# GAMIFICATION
# =============================================================================

def _add_xp(amount: int, reason: str = ""):
    """Add XP — delegates to shared helper."""
    add_xp_safe(amount, reason)


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_hero():
    """Render hero section with disclaimer."""
    inject_css(HERO_CSS, CARD_CSS, EMPTY_STATE_CSS, TANYA_USTADZ_CSS)

    st.markdown("""
    <div class="ustadz-hero">
        <div class="bismillah">بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</div>
        <h1>Tanya Ustadz AI</h1>
        <p class="subtitle">Tanya jawab seputar fiqih umrah berdasarkan madzhab Syafi'i</p>
        <div class="disclaimer">
            <strong>Catatan:</strong> Jawaban AI bersifat referensi edukatif.
            Konsultasikan dengan ustadz/ulama setempat untuk kasus spesifik Anda.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    history = st.session_state.get("tanya_history", [])
    total_q = len(history)
    cats_used = len(set(entry.get("category", "umum") for entry in history)) if history else 0

    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-item">
            <div class="stat-num">{total_q}</div>
            <div class="stat-label">Pertanyaan Dijawab</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{cats_used}</div>
            <div class="stat-label">Kategori Dijelajahi</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">6</div>
            <div class="stat-label">Topik Tersedia</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_ask_form():
    """Render the question form with category selector and textarea."""
    st.markdown('<div class="section-title">💬 Ajukan Pertanyaan</div>', unsafe_allow_html=True)

    with st.container(border=True):
        # Category selector
        cat_options = list(CATEGORIES.keys())
        cat_labels = [f"{CATEGORIES[k]['icon']} {CATEGORIES[k]['label']}" for k in cat_options]

        current_cat = st.session_state.get("tanya_category", "semua")
        current_idx = cat_options.index(current_cat) if current_cat in cat_options else 0

        col_cat, col_spacer = st.columns([3, 1])
        with col_cat:
            selected_label = st.selectbox(
                "Kategori Pertanyaan",
                options=cat_labels,
                index=current_idx,
                label_visibility="collapsed",
                key="tanya_cat_select",
            )
            selected_cat = cat_options[cat_labels.index(selected_label)]
            st.session_state.tanya_category = selected_cat

        # Render category pills display (visual only)
        pills_html = ""
        for key, info in CATEGORIES.items():
            active_cls = "active" if key == selected_cat else ""
            pills_html += f'<span class="category-pill {active_cls}">{info["icon"]} {info["label"]}</span>'

        st.markdown(f'<div class="category-pills">{pills_html}</div>', unsafe_allow_html=True)

        # Question textarea
        pending = st.session_state.get("tanya_pending_question", "")
        question = st.text_area(
            "Tulis pertanyaan Anda",
            value=pending,
            height=100,
            placeholder="Contoh: Bagaimana tata cara tawaf yang benar menurut madzhab Syafi'i?",
            key="tanya_question_input",
        )

        # Submit
        col_submit, col_clear = st.columns([3, 1])

        with col_submit:
            submit = st.button(
                "Tanya Ustadz AI",
                type="primary",
                use_container_width=True,
                key="tanya_submit_btn",
                disabled=st.session_state.get("tanya_is_loading", False),
            )

        with col_clear:
            if st.button("Hapus", use_container_width=True, key="tanya_clear_btn"):
                st.session_state.tanya_pending_question = ""
                st.rerun()

        # Process submission
        if submit and question and question.strip():
            _process_question(question.strip(), selected_cat)


def _process_question(question: str, category: str):
    """Process a submitted question: call AI, store result, award XP."""
    st.session_state.tanya_is_loading = True

    with st.spinner("Ustadz AI sedang menyiapkan jawaban..."):
        answer = get_ai_answer(question, category)

    # Store in history
    entry = {
        "question": question,
        "answer": answer,
        "category": category,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    st.session_state.tanya_history.insert(0, entry)

    # Clear pending question and loading state
    st.session_state.tanya_pending_question = ""
    st.session_state.tanya_is_loading = False

    # Gamification
    _add_xp(5, "Bertanya kepada Ustadz AI")

    # Track analytics
    try:
        from services.analytics import track_page
        track_page("tanya_ustadz_ask")
    except Exception:
        pass

    st.rerun()


def render_popular_questions():
    """Render popular pre-defined questions as clickable cards."""
    st.markdown('<div class="section-title">🔥 Pertanyaan Populer</div>', unsafe_allow_html=True)

    current_cat = st.session_state.get("tanya_category", "semua")

    # Filter by category
    if current_cat == "semua":
        filtered = POPULAR_QUESTIONS
    else:
        filtered = [pq for pq in POPULAR_QUESTIONS if pq["cat"] == current_cat]

    if not filtered:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">Belum ada pertanyaan populer untuk kategori ini.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Render as clickable buttons
    for i, pq in enumerate(filtered):
        cat_info = CATEGORIES.get(pq["cat"], CATEGORIES["umum"])
        cat_label = f'{cat_info["icon"]} {cat_info["label"]}'

        st.markdown(f"""
        <div class="popular-card">
            <span class="pop-icon">💡</span>
            <span class="pop-text">{pq['q']}</span>
            <span class="pop-cat">{cat_label}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            f"Tanyakan: {pq['q'][:50]}...",
            key=f"popular_q_{i}",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.tanya_pending_question = pq["q"]
            st.session_state.tanya_category = pq["cat"]
            st.rerun()


def render_qa_history():
    """Render Q&A history filtered by selected category, newest first."""
    st.markdown('<div class="section-title">📜 Riwayat Tanya Jawab</div>', unsafe_allow_html=True)

    history = st.session_state.get("tanya_history", [])
    current_cat = st.session_state.get("tanya_category", "semua")

    # Filter by category
    if current_cat == "semua":
        filtered = history
    else:
        filtered = [entry for entry in history if entry.get("category") == current_cat]

    if not filtered:
        if history:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <div class="empty-text">Tidak ada pertanyaan untuk kategori ini. Coba pilih "Semua".</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🕌</div>
                <div class="empty-text">Belum ada pertanyaan. Ajukan pertanyaan pertama Anda di atas!</div>
            </div>
            """, unsafe_allow_html=True)
        return

    # Render cards
    for idx, entry in enumerate(filtered):
        question = entry.get("question", "")
        answer = entry.get("answer", "")
        category = entry.get("category", "umum")
        timestamp = entry.get("timestamp", "")
        cat_info = CATEGORIES.get(category, CATEGORIES["umum"])
        cat_label = f'{cat_info["icon"]} {cat_info["label"]}'

        # Format answer for HTML display - escape basic HTML but allow our formatting
        answer_html = answer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Re-apply bold markers for display
        answer_html = answer_html.replace("**Jawaban:**", "<strong>📖 Jawaban:</strong>")
        answer_html = answer_html.replace("**Dalil:**", "<strong>📜 Dalil:</strong>")
        answer_html = answer_html.replace("**Rujukan:**", "<strong>📚 Rujukan:</strong>")
        answer_html = answer_html.replace("**Kesimpulan:**", "<strong>✅ Kesimpulan:</strong>")
        # Generic bold
        answer_html = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            answer_html,
        )
        # Convert newlines for HTML
        answer_html = answer_html.replace("\n\n", "<br><br>").replace("\n", "<br>")

        st.markdown(f"""
        <div class="qa-card">
            <div class="qa-question">
                <span class="q-icon">❓</span>
                <span>{question}</span>
            </div>
            <div class="qa-answer">{answer_html}</div>
            <div class="qa-meta">
                <span class="qa-category">{cat_label}</span>
                <span class="qa-time">🕐 {timestamp}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Also render in native markdown for accessibility via expander
        with st.expander(f"📋 Lihat jawaban lengkap #{idx + 1}", expanded=False):
            st.markdown(f"**Pertanyaan:** {question}")
            st.divider()
            st.markdown(answer)

    # Show count
    total = len(history)
    showing = len(filtered)
    if current_cat != "semua" and showing < total:
        st.caption(f"Menampilkan {showing} dari {total} pertanyaan (filter: {cat_info['label']})")


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_tanya_ustadz_page():
    """Main entry point for Tanya Ustadz AI page."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("tanya_ustadz")
    except Exception:
        pass

    # Initialize state
    init_tanya_ustadz_state()

    # Hero section with disclaimer
    render_hero()

    st.divider()

    # Ask form (category selector + textarea + submit)
    render_ask_form()

    st.divider()

    # Popular questions (clickable, fills textarea)
    render_popular_questions()

    st.divider()

    # Q&A history (filtered by category, newest first)
    render_qa_history()

    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <p style="color: #64748b; font-size: 0.82rem; margin-bottom: 0.3rem;">
            <strong style="color: #94a3b8;">Tanya Ustadz AI</strong> - Powered by LABBAIK AI
        </p>
        <p style="color: #4a5568; font-size: 0.75rem;">
            Jawaban AI bersifat referensi edukatif. Konsultasikan dengan ustadz/ulama setempat untuk kasus spesifik Anda.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_tanya_ustadz_page"]
