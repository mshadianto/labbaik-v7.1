"""
LABBAIK AI v6.0 - AI Chat (Super WOW Edition)
=============================================
Enhanced chat interface with quick actions,
smart suggestions, rich responses, and history.
Supports multiple AI providers: Groq, OpenAI, GLM-4.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
import os

# Shared styles
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, SKELETON_CSS, render_skeleton

# Gamification helper
from services.ai.helpers import add_xp_safe

# AI Service imports
try:
    from services.ai.chat_service import (
        GroqChatService,
        OpenAIChatService,
        GLMChatService,
        UnifiedChatService,
    )
    from services.ai.base import ChatMessage, ChatCompletionRequest
    HAS_AI_SERVICES = True
except ImportError:
    HAS_AI_SERVICES = False

# Live price service for package recommendations in chat
try:
    from services.price.live_prices import LivePriceService, format_price
    HAS_LIVE_PRICES = True
except ImportError:
    HAS_LIVE_PRICES = False

# Available AI providers
AI_PROVIDERS = {
    "groq": {
        "name": "Groq (Llama 3.3)",
        "icon": "🚀",
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
    },
    "glm": {
        "name": "GLM-4 (Zhipu AI)",
        "icon": "🧠",
        "model": "glm-4",
        "env_key": "GLM_API_KEY",
    },
    "openai": {
        "name": "OpenAI (GPT-4o)",
        "icon": "🤖",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
}

# =============================================================================
# CONSTANTS & DATA
# =============================================================================

# Quick question categories
QUICK_CATEGORIES = {
    "📋 Persiapan": [
        "Apa saja syarat umrah?",
        "Dokumen apa yang harus disiapkan?",
        "Berapa lama proses visa umrah?",
        "Vaksin apa yang diperlukan?",
        "Apa yang harus dibawa ke tanah suci?",
    ],
    "🕋 Ibadah": [
        "Bagaimana tata cara umrah?",
        "Apa saja rukun umrah?",
        "Bagaimana cara thawaf yang benar?",
        "Apa doa saat sa'i?",
        "Kapan waktu terbaik untuk umrah?",
    ],
    "💰 Biaya": [
        "Berapa biaya umrah tahun ini?",
        "Apa saja yang termasuk dalam paket?",
        "Bagaimana cara cicilan umrah?",
        "Tips hemat umrah?",
        "Paket umrah paling ekonomis?",
    ],
    "🗣️ Bahasa Arab": [
        "Cara mengucapkan talbiyah?",
        "Frasa penting di Arab Saudi?",
        "Doa masuk Masjidil Haram?",
        "Cara bertanya dalam bahasa Arab?",
        "Angka dalam bahasa Arab?",
    ],
    "🏨 Akomodasi": [
        "Hotel terbaik dekat Masjidil Haram?",
        "Berapa jarak ideal hotel ke Masjid?",
        "Fasilitas hotel umrah apa saja?",
        "Tips memilih hotel di Makkah?",
        "Perbedaan hotel bintang 3, 4, 5?",
    ],
    "👩 Wanita": [
        "Aturan mahram untuk wanita?",
        "Umrah saat haid bagaimana?",
        "Tips pakaian wanita di Arab Saudi?",
        "Apa yang harus diperhatikan wanita?",
        "Perbedaan ihram pria dan wanita?",
    ],
}

# Suggested follow-ups based on context
FOLLOW_UP_SUGGESTIONS = {
    "persiapan": [
        "Lalu apa langkah selanjutnya?",
        "Berapa lama proses ini?",
        "Apa ada tips tambahan?",
    ],
    "ibadah": [
        "Bagaimana doanya?",
        "Apa kesalahan umum yang harus dihindari?",
        "Jelaskan lebih detail",
    ],
    "biaya": [
        "Bisa lebih hemat lagi?",
        "Apa saja yang tidak termasuk?",
        "Bandingkan dengan paket lain",
    ],
    "default": [
        "Jelaskan lebih detail",
        "Ada tips lain?",
        "Apa yang harus saya perhatikan?",
    ],
}

# Sample AI responses (in production, this would come from actual AI)
SAMPLE_RESPONSES = {
    "syarat": """
## ✅ Syarat Umrah

Untuk melaksanakan ibadah umrah, berikut syarat yang harus dipenuhi:

### Syarat Wajib
1. **Islam** - Muslim yang beriman
2. **Baligh** - Sudah dewasa (pubertas)
3. **Berakal** - Sehat secara mental
4. **Merdeka** - Bukan budak (sudah tidak relevan di zaman modern)
5. **Mampu** - Secara fisik dan finansial

### Dokumen yang Diperlukan
- 📘 **Paspor** - Minimal berlaku 7 bulan dari tanggal keberangkatan
- 📷 **Pas foto** - Ukuran 4x6, background putih
- 💉 **Kartu vaksin** - Meningitis dan COVID-19
- 📋 **KTP** - Untuk verifikasi identitas

### Untuk Wanita di Bawah 45 Tahun
- Harus ditemani mahram (suami, ayah, saudara laki-laki, dll)
- Atau dengan rombongan wanita minimal 4 orang dengan izin tertulis mahram

---
💡 **Tips:** Siapkan dokumen minimal 2 bulan sebelum keberangkatan!
""",
    "tata_cara": """
## 🕋 Tata Cara Umrah

Umrah memiliki 4 rukun yang harus dilakukan secara berurutan:

### 1. Ihram 📿
- Niat umrah dari miqat
- Memakai pakaian ihram (pria: 2 lembar kain putih tanpa jahitan)
- Membaca talbiyah: *"Labbaikallahumma labbaik..."*

### 2. Thawaf 🔄
- Mengelilingi Ka'bah 7 kali
- Dimulai dari Hajar Aswad
- Berakhir di Hajar Aswad
- Membaca doa dan dzikir

### 3. Sa'i 🚶
- Berjalan antara Shafa dan Marwah
- 7 kali perjalanan (dimulai dari Shafa)
- Mengingat perjuangan Siti Hajar

### 4. Tahallul ✂️
- Mencukur atau memotong rambut
- Pria: minimal 3 helai rambut
- Wanita: memotong ujung rambut seujung jari

---
🤲 Setelah selesai, Anda telah resmi menyelesaikan ibadah umrah!
""",
    "biaya": """
## 💰 Estimasi Biaya Umrah 2025

Biaya umrah bervariasi tergantung beberapa faktor:

### Range Harga per Paket
| Paket | Harga | Hotel |
|-------|-------|-------|
| 🎒 Backpacker | Rp 18-22 Juta | Bintang 2-3 |
| ⭐ Reguler | Rp 25-30 Juta | Bintang 3-4 |
| 🌟 Plus | Rp 35-45 Juta | Bintang 4-5 |
| 👑 VIP | Rp 55-80 Juta | Bintang 5+ |

### Yang Mempengaruhi Harga
1. **Musim** - Ramadan & liburan lebih mahal
2. **Hotel** - Jarak ke Masjid & bintang
3. **Durasi** - 9-21 hari
4. **Airline** - Garuda vs budget airline

### Tips Hemat 💡
- Pilih musim reguler (Mei, Sep, Oct)
- Berangkat rombongan untuk diskon grup
- Booking minimal 3 bulan sebelumnya

---
📊 Gunakan **Simulasi Biaya** untuk perhitungan lebih akurat!
""",
}


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

CHAT_PAGE_CSS = """
/* Expert AI paywall card */
.expert-paywall {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #d4af37;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}

.expert-paywall .lock-icon {
    font-size: 1.8rem;
    margin-bottom: 0.3rem;
}

.expert-paywall h4 {
    color: #d4af37;
    margin-bottom: 0.3rem;
}

.expert-paywall p {
    color: #aaa;
    font-size: 0.85rem;
    margin-bottom: 0.8rem;
}

/* Chat package recommendation cards */
.chat-package-cards-section {
    margin-top: 0.8rem;
    padding: 0.8rem;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2a2a4a;
    border-radius: 10px;
}

.chat-package-cards-section h4 {
    color: #d4af37;
    font-size: 0.95rem;
    margin-bottom: 0.6rem;
}

.chat-package-card {
    background: #0e1525;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s ease;
}

.chat-package-card:hover {
    border-color: #d4af37;
}

.chat-package-card .pkg-name {
    color: #e0e0e0;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 0.2rem;
}

.chat-package-card .pkg-price {
    color: #28a745;
    font-weight: 700;
    font-size: 1rem;
}

.chat-package-card .pkg-original-price {
    color: #b0b0b0;
    font-size: 0.75rem;
    text-decoration: line-through;
    margin-left: 0.4rem;
}

.chat-package-card .pkg-details {
    color: #b0b0b0;
    font-size: 0.78rem;
    margin-top: 0.2rem;
}

.chat-package-card .pkg-badge-promo {
    display: inline-block;
    background: #dc3545;
    color: #fff;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 8px;
    margin-left: 0.4rem;
    vertical-align: middle;
}

.chat-package-card .pkg-stars {
    color: #d4af37;
    font-size: 0.78rem;
}

.chat-pkg-cta {
    display: block;
    text-align: center;
    margin-top: 0.6rem;
    padding: 0.45rem;
    background: transparent;
    border: 1px solid #d4af37;
    border-radius: 8px;
    color: #d4af37;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
}

.chat-pkg-cta:hover {
    background: #d4af37;
    color: #000;
}

@media (prefers-reduced-motion: reduce) {
    .chat-package-card {
        transition: none;
    }
}
"""


# =============================================================================
# SESSION STATE
# =============================================================================

def get_api_key(provider: str) -> Optional[str]:
    """Get API key for provider from secrets or environment."""
    env_key = AI_PROVIDERS.get(provider, {}).get("env_key", "")

    # Try Streamlit secrets first
    try:
        if hasattr(st, 'secrets') and env_key in st.secrets:
            return st.secrets[env_key]
    except Exception:
        pass

    # Try environment variable
    return os.environ.get(env_key)


def get_ai_service(provider: str = "groq"):
    """Get AI service instance for the specified provider."""
    if not HAS_AI_SERVICES:
        return None

    api_key = get_api_key(provider)
    if not api_key:
        return None

    try:
        if provider == "groq":
            service = GroqChatService(api_key=api_key)
        elif provider == "glm":
            service = GLMChatService(api_key=api_key)
        elif provider == "openai":
            service = OpenAIChatService(api_key=api_key)
        else:
            return None

        service.initialize()
        return service
    except Exception as e:
        st.error(f"Failed to initialize {provider}: {e}")
        return None


def init_chat_state():
    """Initialize chat session state."""

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Assalamu'alaikum! 👋 Saya asisten AI LABBAIK yang siap membantu Anda merencanakan ibadah umrah. Silakan tanya apa saja tentang persiapan, tata cara, biaya, atau hal lainnya seputar umrah.",
                "timestamp": datetime.now().isoformat(),
            }
        ]

    if "chat_context" not in st.session_state:
        st.session_state.chat_context = "default"

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Default AI provider
    if "ai_provider" not in st.session_state:
        # Auto-detect available provider
        for provider in ["groq", "glm", "openai"]:
            if get_api_key(provider):
                st.session_state.ai_provider = provider
                break
        else:
            st.session_state.ai_provider = "groq"

    # Check for quick question from home page
    if "quick_question" in st.session_state and st.session_state.quick_question:
        question = st.session_state.quick_question
        st.session_state.quick_question = None
        process_user_message(question)

    # Check for voice message from voice input
    if "voice_message" in st.session_state and st.session_state.voice_message:
        voice_text = st.session_state.voice_message
        st.session_state.voice_message = None
        process_user_message(voice_text)


def add_message(role: str, content: str):
    """Add message to chat."""
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })


def get_ai_response(user_message: str) -> str:
    """Get AI response using the selected provider."""

    provider = st.session_state.get("ai_provider", "groq")
    service = get_ai_service(provider)

    # System prompt for Umrah assistant
    system_prompt = """Anda adalah LABBAIK AI, asisten cerdas untuk perencanaan ibadah Umrah.

INSTRUKSI:
1. Jawab dalam Bahasa Indonesia yang baik dan santun
2. Berikan informasi akurat tentang umrah (syarat, tata cara, biaya, tips)
3. Gunakan format markdown untuk response yang rapi
4. Sertakan emoji yang relevan untuk membuat jawaban lebih menarik
5. Jika tidak yakin, sarankan untuk berkonsultasi dengan ustadz/travel agent
6. Dorong sikap DYOR (Do Your Own Research)

KONTEKS: Anda membantu umat Muslim Indonesia merencanakan ibadah umrah."""

    if service:
        try:
            # Build messages from chat history
            messages = [ChatMessage.system(system_prompt)]

            # Add recent chat history (last 6 messages)
            chat_msgs = st.session_state.get("chat_messages", [])
            for msg in chat_msgs[-6:]:
                if msg["role"] == "user":
                    messages.append(ChatMessage.user(msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(ChatMessage.assistant(msg["content"]))

            # Add current question
            messages.append(ChatMessage.user(user_message))

            # Create request
            request = ChatCompletionRequest(
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )

            # Get response
            response = service.complete(request)

            # Update context based on response
            user_lower = user_message.lower()
            if any(word in user_lower for word in ["syarat", "persyaratan", "dokumen", "persiapan"]):
                st.session_state.chat_context = "persiapan"
            elif any(word in user_lower for word in ["tata cara", "rukun", "thawaf", "sai", "ihram"]):
                st.session_state.chat_context = "ibadah"
            elif any(word in user_lower for word in ["biaya", "harga", "cost", "budget"]):
                st.session_state.chat_context = "biaya"
            else:
                st.session_state.chat_context = "default"

            return response.content

        except Exception as e:
            return f"""⚠️ Maaf, terjadi kesalahan saat memproses pertanyaan Anda.

**Error:** {str(e)}

Silakan coba lagi atau gunakan pertanyaan populer di atas."""

    # Fallback to sample responses if no AI service available
    user_lower = user_message.lower()

    if any(word in user_lower for word in ["syarat", "persyaratan", "dokumen", "persiapan"]):
        st.session_state.chat_context = "persiapan"
        return SAMPLE_RESPONSES["syarat"]

    elif any(word in user_lower for word in ["tata cara", "rukun", "cara", "thawaf", "sai", "ihram"]):
        st.session_state.chat_context = "ibadah"
        return SAMPLE_RESPONSES["tata_cara"]

    elif any(word in user_lower for word in ["biaya", "harga", "cost", "budget", "mahal", "murah"]):
        st.session_state.chat_context = "biaya"
        return SAMPLE_RESPONSES["biaya"]

    else:
        st.session_state.chat_context = "default"
        return f"""
Terima kasih atas pertanyaannya! 🤲

Pertanyaan Anda tentang **"{user_message}"** sangat baik.

⚠️ **AI Service tidak tersedia.** Pastikan API key sudah dikonfigurasi.

Silakan pilih kategori di bawah untuk pertanyaan yang lebih spesifik.

---
💡 **Tip:** Konfigurasi `GROQ_API_KEY` atau `GLM_API_KEY` di secrets untuk mengaktifkan AI.
"""


def process_user_message(message: str):
    """Process user message and get response."""

    # --- Gamification XP tracking ---
    # Initialise session-state keys on first use
    if "chat_first_msg_xp_awarded" not in st.session_state:
        st.session_state.chat_first_msg_xp_awarded = False
    if "chat_followup_xp_count" not in st.session_state:
        st.session_state.chat_followup_xp_count = 0

    # Count user messages *before* this one
    user_msg_count = sum(
        1 for m in st.session_state.get("chat_messages", []) if m["role"] == "user"
    )

    # +10 XP for first chat message in this session
    if user_msg_count == 0 and not st.session_state.chat_first_msg_xp_awarded:
        add_xp_safe(10, "Pesan chat pertama")
        st.session_state.chat_first_msg_xp_awarded = True
    # +5 XP for follow-up questions (max 3 times per session)
    elif user_msg_count > 0 and st.session_state.chat_followup_xp_count < 3:
        add_xp_safe(5, "Pertanyaan lanjutan")
        st.session_state.chat_followup_xp_count += 1

    # Add user message
    add_message("user", message)

    # Detect if user is asking about packages/prices
    st.session_state.show_package_recommendations = detect_package_query(message)

    # Get AI response (simulated)
    response = get_ai_response(message)

    # Add AI response
    add_message("assistant", response)


# =============================================================================
# PACKAGE RECOMMENDATION IN CHAT
# =============================================================================

# Keywords that indicate a user is asking about packages/prices
_PACKAGE_KEYWORDS = [
    "paket", "harga", "biaya", "murah", "promo",
    "umrah berapa", "rekomendasi paket", "package",
    "tarif", "ongkos", "budget", "hemat", "diskon",
    "termurah", "terjangkau", "ekonomis",
]


def detect_package_query(message: str) -> bool:
    """Check if the user message is asking about packages or prices.

    Args:
        message: The raw user message text.

    Returns:
        True if any package/price keyword is found.
    """
    if not message:
        return False
    lowered = message.lower()
    return any(kw in lowered for kw in _PACKAGE_KEYWORDS)


def render_package_recommendations():
    """Render compact package recommendation cards below an AI response.

    Fetches the top 3 cheapest packages from LivePriceService and
    displays them as styled HTML cards with a CTA to the full
    price comparison page.  Wrapped entirely in try/except so that
    failures never break the chat flow.
    """
    if not HAS_LIVE_PRICES:
        return

    try:
        service = LivePriceService()
        packages = service.get_cheapest_packages(limit=3)

        if not packages:
            return

        # Build HTML cards
        cards_html = ""
        for pkg in packages:
            # Star display for Makkah hotel
            stars_display = '<span class="pkg-stars">' + ("&#9733;" * pkg.hotel_makkah_stars) + "</span>"

            # Promo badge
            promo_badge = ""
            if pkg.is_promo:
                promo_badge = (
                    f'<span class="pkg-badge-promo">'
                    f'<span aria-hidden="true">&#128293;</span> PROMO -{pkg.discount_percent:.0f}%'
                    f'</span>'
                )

            # Formatted prices
            price_str = format_price(pkg.price)
            original_price_str = ""
            if pkg.is_promo and pkg.original_price > pkg.price:
                original_price_str = (
                    f'<span class="pkg-original-price">{format_price(pkg.original_price)}</span>'
                )

            cards_html += f"""
            <div class="chat-package-card">
                <div class="pkg-name">{pkg.name}{promo_badge}</div>
                <div class="pkg-price">{price_str}{original_price_str}</div>
                <div class="pkg-details">
                    {pkg.duration_days} hari &middot; {stars_display} Hotel Makkah &middot; {pkg.travel_agent}
                </div>
            </div>
            """

        # Full section HTML with accessibility attributes
        section_html = f"""
        <div class="chat-package-cards-section" role="status" aria-live="polite">
            <h4><span aria-hidden="true">&#128161;</span> Rekomendasi Paket Terkait:</h4>
            {cards_html}
        </div>
        """

        st.markdown("---")
        st.markdown(section_html, unsafe_allow_html=True)

        # CTA button to navigate to price comparison page
        if st.button(
            "Lihat Semua Paket \u2192",
            key="chat_pkg_see_all",
            use_container_width=True,
        ):
            st.session_state.current_page = "price_comparison"
            st.rerun()

    except Exception:
        # Graceful fallback -- never break chat
        pass


# =============================================================================
# RENDER COMPONENTS
# =============================================================================

def render_sidebar():
    """Render chat sidebar with quick actions."""

    with st.sidebar:
        # AI Provider Selection
        st.markdown("## 🧠 AI Provider")

        current_provider = st.session_state.get("ai_provider", "groq")

        # Build provider options
        provider_options = []
        provider_labels = {}
        for key, info in AI_PROVIDERS.items():
            has_key = get_api_key(key) is not None
            status = "✓" if has_key else "✗"
            label = f"{info['icon']} {info['name']} [{status}]"
            provider_options.append(key)
            provider_labels[key] = label

        selected_provider = st.selectbox(
            "Pilih AI:",
            options=provider_options,
            index=provider_options.index(current_provider) if current_provider in provider_options else 0,
            format_func=lambda x: provider_labels.get(x, x),
            key="provider_select"
        )

        if selected_provider != current_provider:
            st.session_state.ai_provider = selected_provider
            st.rerun()

        # Show provider status
        if get_api_key(selected_provider):
            st.success(f"✓ {AI_PROVIDERS[selected_provider]['name']} aktif", icon="🟢")
        else:
            st.warning(f"API key belum dikonfigurasi", icon="⚠️")

        st.divider()

        st.markdown("## 🎯 Aksi Cepat")

        # Quick actions
        actions = [
            ("💰 Simulasi Biaya", "simulator"),
            ("📦 Booking", "booking"),
            ("👥 Umrah Bareng", "umrah_bareng"),
            ("📚 Panduan", "guide"),
        ]

        for label, page in actions:
            if st.button(label, use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

        st.divider()

        # Chat history
        st.markdown("## 📜 Riwayat")

        history = st.session_state.get("chat_history", [])
        if history:
            for i, item in enumerate(history[-5:]):
                with st.container(border=True):
                    st.caption(item.get("date", "N/A"))
                    if st.button(f"💬 {item.get('preview', 'Chat')[:20]}...", key=f"hist_{i}", use_container_width=True):
                        st.info("Memuat riwayat chat...")
        else:
            st.caption("Belum ada riwayat")

        st.divider()

        # Chat controls
        st.markdown("## ⚙️ Pengaturan")

        if st.button("🗑️ Hapus Chat", use_container_width=True):
            st.session_state.chat_messages = [st.session_state.chat_messages[0]]
            st.rerun()

        if st.button("📤 Export Chat", use_container_width=True):
            st.info("Fitur export akan segera hadir")


def render_quick_questions():
    """Render quick question buttons."""
    
    with st.expander("💡 Pertanyaan Populer", expanded=False):
        tabs = st.tabs(list(QUICK_CATEGORIES.keys()))
        
        for tab, (category, questions) in zip(tabs, QUICK_CATEGORIES.items()):
            with tab:
                for q in questions:
                    if st.button(q, key=f"quick_{q}", use_container_width=True):
                        process_user_message(q)
                        st.rerun()


def render_chat_messages():
    """Render chat message history."""

    messages = st.session_state.chat_messages
    tts_enabled = st.session_state.get("tts_enabled", False)
    is_last_msg_index = len(messages) - 1

    for idx, msg in enumerate(messages):
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        else:
            with st.chat_message("assistant", avatar="🕋"):
                st.markdown(
                    f'<div role="status" aria-live="polite">{content}</div>',
                    unsafe_allow_html=True,
                ) if idx == is_last_msg_index else st.markdown(content)

                # TTS button for assistant messages (only last message to keep it clean)
                if tts_enabled and idx == is_last_msg_index:
                    render_tts_player(content, idx)

                # Package recommendations after the last assistant response
                if (
                    idx == is_last_msg_index
                    and st.session_state.get("show_package_recommendations", False)
                ):
                    render_package_recommendations()


def render_tts_player(text: str, message_idx: int):
    """Render TTS audio player for a message."""
    try:
        from services.ai.speech_service import text_to_speech, is_tts_available

        if not is_tts_available():
            return

        # Use session state to cache audio
        cache_key = f"tts_audio_{message_idx}"

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔊 Dengar", key=f"tts_btn_{message_idx}", use_container_width=True):
                with st.spinner("Membuat audio..."):
                    audio_bytes = text_to_speech(text)
                    if audio_bytes:
                        st.session_state[cache_key] = audio_bytes

        # Play cached audio if available
        if cache_key in st.session_state and st.session_state[cache_key]:
            st.audio(st.session_state[cache_key], format="audio/mp3")

    except Exception as e:
        pass  # Silently fail for TTS


def render_follow_up_suggestions():
    """Render follow-up question suggestions."""
    
    context = st.session_state.get("chat_context", "default")
    suggestions = FOLLOW_UP_SUGGESTIONS.get(context, FOLLOW_UP_SUGGESTIONS["default"])
    
    if len(st.session_state.chat_messages) > 1:
        st.markdown("**💬 Tanya lebih lanjut:**")
        
        cols = st.columns(len(suggestions))
        
        for col, suggestion in zip(cols, suggestions):
            with col:
                if st.button(suggestion, key=f"followup_{suggestion}", use_container_width=True):
                    process_user_message(suggestion)
                    st.rerun()


def render_chat_input():
    """Render chat input."""
    
    user_input = st.chat_input("Ketik pertanyaan Anda di sini...")
    
    if user_input:
        process_user_message(user_input)
        st.rerun()


def render_chat_features():
    """Render additional chat features with premium gating."""

    # === EXPERT AI FEATURE (Premium-locked) ===
    with st.expander("🧠 Expert AI - Analisis Personal", expanded=False):
        # Check if user has premium access
        try:
            from services.user.access_control import (
                Feature, check_expert_feature, has_feature_access
            )
            from services.user.user_service import get_current_user

            user = get_current_user()
            has_expert_access = has_feature_access(user, Feature.PERSONALIZED_AI_ADVICE)
        except Exception:
            has_expert_access = False

        if has_expert_access:
            # === PREMIUM USER: Full Expert Features ===
            st.success("Expert AI Aktif")

            expert_options = [
                ("📊", "Analisis Rencana Keuangan", "Analisis mendalam tabungan dan target umrah Anda"),
                ("💡", "Rekomendasi Personal", "Saran optimal berdasarkan profil dan preferensi"),
                ("📈", "Proyeksi Tabungan", "Simulasi kapan target tercapai dengan berbagai skenario"),
            ]

            for icon, label, desc in expert_options:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{icon} {label}**")
                        st.caption(desc)
                    with col2:
                        if st.button("Mulai", key=f"expert_{label}", use_container_width=True):
                            # Trigger expert analysis prompt
                            st.session_state.expert_prompt = label
                            st.rerun()
        else:
            # === FREE USER: Show paywall ===
            paywall_html = (
                '<div class="expert-paywall">'
                '<div class="lock-icon">&#128274;</div>'
                '<h4>Fitur Expert AI</h4>'
                '<p>Dapatkan analisis mendalam untuk mengoptimalkan '
                'dana tabungan Anda agar berangkat lebih cepat.</p>'
                '</div>'
            )
            st.markdown(paywall_html, unsafe_allow_html=True)

            if st.button("✨ Upgrade ke Premium", type="primary", use_container_width=True, key="expert_upgrade"):
                st.session_state.current_page = "subscription"
                st.rerun()

            st.caption("Mulai dari Rp 99.000/bulan")

    with st.expander("🛠️ Fitur Tambahan", expanded=False):
        # Voice Input Section
        st.markdown("##### 🎤 Voice Input")
        st.caption("Rekam suara Anda untuk bertanya (Bahasa Indonesia)")

        audio_data = st.audio_input(
            "Tekan untuk merekam",
            key="voice_input",
            label_visibility="collapsed"
        )

        if audio_data is not None:
            # Process voice input
            try:
                from services.ai.speech_service import transcribe_audio

                with st.spinner("🎧 Mengkonversi suara ke teks..."):
                    audio_bytes = audio_data.read()
                    transcribed_text = transcribe_audio(audio_bytes, language="id")

                if transcribed_text:
                    st.success(f"📝 Terdeteksi: **{transcribed_text}**")

                    # Set as pending message to be sent
                    if st.button("📤 Kirim Pertanyaan Ini", use_container_width=True, type="primary"):
                        st.session_state.voice_message = transcribed_text
                        st.rerun()
                else:
                    st.warning("Tidak ada suara terdeteksi. Coba rekam ulang.")

            except Exception as e:
                st.error(f"Gagal memproses audio: {str(e)}")

        st.divider()

        # TTS Toggle Section
        st.markdown("##### 🔊 Voice Response")
        tts_col1, tts_col2 = st.columns([3, 2])

        with tts_col1:
            tts_enabled = st.toggle(
                "Aktifkan respon suara",
                value=st.session_state.get("tts_enabled", False),
                key="tts_toggle",
                help="AI akan membacakan jawaban dengan suara"
            )
            st.session_state.tts_enabled = tts_enabled

        with tts_col2:
            if tts_enabled:
                try:
                    from services.ai.speech_service import is_tts_available
                    if is_tts_available():
                        st.success("✓ TTS Aktif", icon="🔊")
                    else:
                        st.warning("edge-tts belum terinstall")
                except Exception:
                    st.warning("TTS tidak tersedia")

        st.divider()

        # Other features
        col2, col3, col4 = st.columns(3)

        with col2:
            if st.button("📷 Upload Gambar", use_container_width=True):
                st.info("Upload gambar untuk analisis")

        with col3:
            if st.button("📄 Upload Dokumen", use_container_width=True):
                st.info("Upload dokumen untuk review")

        with col4:
            if st.button("🔗 Share Chat", use_container_width=True):
                st.info("Bagikan chat ini")


def render_ai_status():
    """Render AI status indicator."""

    provider = st.session_state.get("ai_provider", "groq")
    provider_info = AI_PROVIDERS.get(provider, {})
    has_key = get_api_key(provider) is not None

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        if has_key:
            st.caption(f"🟢 {provider_info.get('icon', '🤖')} {provider_info.get('name', 'AI')} Aktif")
        else:
            st.caption("🟡 AI Offline (Demo Mode)")

    with col2:
        st.caption(f"💬 {len(st.session_state.chat_messages)} pesan")

    with col3:
        st.caption(f"⚡ {provider.upper()}")


# =============================================================================
# MAIN PAGE RENDERER  
# =============================================================================

def render_chat_page():
    """Main chat page renderer."""

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, SKELETON_CSS, CHAT_PAGE_CSS)

    # Track page view
    try:
        from services.analytics import track_page
        track_page("chat")
    except Exception:
        pass

    # Initialize state
    init_chat_state()
    
    # Header
    st.markdown('<h1><span aria-hidden="true">🤖</span> AI Assistant</h1>', unsafe_allow_html=True)
    st.caption("Asisten cerdas untuk semua pertanyaan seputar umrah")
    
    # AI Status
    render_ai_status()
    
    st.divider()
    
    # Sidebar
    render_sidebar()
    
    # Quick questions
    render_quick_questions()
    
    # Chat container
    chat_container = st.container(height=500)
    
    with chat_container:
        render_chat_messages()
    
    # Follow-up suggestions
    render_follow_up_suggestions()
    
    # Additional features
    render_chat_features()
    
    # Chat input
    render_chat_input()
    
    # Footer
    st.divider()
    st.caption("💡 Tips: Tanya dengan spesifik untuk jawaban yang lebih akurat | 🔒 Percakapan Anda aman dan privat")


# Export
__all__ = ["render_chat_page"]
