"""
LABBAIK AI - Group Matching with In-App Group Chat
====================================================
Group matching page that helps users find compatible Umrah travel groups,
with an integrated group chat feature for real-time communication.

Features:
- Group discovery and smart matching
- In-app group chat (session-state based)
- XP gamification for chat participation
- WCAG-compliant dark theme
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from services.ai.helpers import add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, EMPTY_STATE_CSS


# =============================================================================
# PAGE-SPECIFIC CSS
# =============================================================================

GROUP_CHAT_CSS = """
/* Group Chat Container */
.group-chat-container {
    background: linear-gradient(145deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 0;
    overflow: hidden;
    margin-top: 1rem;
}

.group-chat-header {
    background: linear-gradient(135deg, #1a2332 0%, #1e293b 100%);
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #30363d;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.group-chat-header h3 {
    color: #d4af37;
    margin: 0;
    font-size: 1.1rem;
}

.group-chat-header .member-count {
    color: #8b949e;
    font-size: 0.8rem;
}

/* Chat messages area */
.chat-messages-area {
    max-height: 420px;
    overflow-y: auto;
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    scrollbar-width: thin;
    scrollbar-color: #30363d #0d1117;
}

.chat-messages-area::-webkit-scrollbar {
    width: 6px;
}

.chat-messages-area::-webkit-scrollbar-track {
    background: #0d1117;
}

.chat-messages-area::-webkit-scrollbar-thumb {
    background: #30363d;
    border-radius: 3px;
}

/* Chat message - other users (left aligned) */
.chat-message {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    max-width: 80%;
}

.chat-message.own-message {
    margin-left: auto;
    flex-direction: row-reverse;
}

/* User avatar circle */
.chat-avatar {
    width: 36px;
    height: 36px;
    min-width: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.85rem;
    color: #fff;
    flex-shrink: 0;
}

/* Message bubble */
.chat-bubble {
    background: #1c2333;
    border: 1px solid #2d3748;
    border-radius: 12px 12px 12px 4px;
    padding: 0.6rem 0.9rem;
    position: relative;
}

.chat-message.own-message .chat-bubble {
    background: linear-gradient(145deg, #1a3a2a 0%, #1a4a2a 100%);
    border-color: #2d6b3f;
    border-radius: 12px 12px 4px 12px;
}

.chat-bubble .chat-user-name {
    color: #d4af37;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.2rem;
}

.chat-message.own-message .chat-bubble .chat-user-name {
    color: #4ade80;
    text-align: right;
}

.chat-bubble .chat-text {
    color: #e6edf3;
    font-size: 0.9rem;
    line-height: 1.5;
    word-wrap: break-word;
}

.chat-bubble .chat-timestamp {
    color: #6e7681;
    font-size: 0.68rem;
    margin-top: 0.25rem;
    text-align: right;
}

/* Chat input area */
.chat-input-area {
    background: #161b22;
    border-top: 1px solid #30363d;
    padding: 0.75rem 1.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Empty state */
.chat-empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #8b949e;
}

.chat-empty-state .empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    opacity: 0.5;
}

.chat-empty-state .empty-text {
    font-size: 0.95rem;
    color: #b0b8c4;
}

/* XP toast for chat */
.chat-xp-toast {
    background: linear-gradient(135deg, #1a3a1a, #2a4a2a);
    border: 1px solid #4ade80;
    border-radius: 10px;
    padding: 0.5rem 0.75rem;
    color: #4ade80;
    font-weight: bold;
    text-align: center;
    font-size: 0.85rem;
    margin: 0.5rem 0;
}

/* Group list cards for matching */
.group-match-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    padding: 1.25rem;
    border: 1px solid #333;
    margin-bottom: 0.75rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.group-match-card:hover {
    transform: translateY(-1px);
    border-color: #d4af37;
}

.group-match-card .group-name {
    color: #d4af37;
    font-size: 1.05rem;
    font-weight: bold;
    margin-bottom: 0.3rem;
}

.group-match-card .group-info {
    color: #b0b0b0;
    font-size: 0.85rem;
}

.group-match-card .member-avatars {
    display: flex;
    gap: 0.25rem;
    margin-top: 0.5rem;
}

/* Compatibility Badge */
.compatibility-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    vertical-align: middle;
    margin-left: 0.4rem;
}

.compatibility-badge.compat-excellent {
    background: #1a3a1a;
    color: #4ade80;
    border: 1px solid #2d6b3f;
}

.compatibility-badge.compat-good {
    background: #3a3520;
    color: #d4af37;
    border: 1px solid #b8962e;
}

.compatibility-badge.compat-fair {
    background: #3a3520;
    color: #fbbf24;
    border: 1px solid #d97706;
}

.compatibility-badge.compat-low {
    background: #2a2a2a;
    color: #8b949e;
    border: 1px solid #484f58;
}

.compatibility-score-bar {
    height: 4px;
    border-radius: 2px;
    background: #21262d;
    margin-top: 0.5rem;
    overflow: hidden;
}

.compatibility-score-bar .bar-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
}

/* Responsive overrides for chat */
@media (max-width: 768px) {
    .chat-messages-area {
        max-height: 320px;
        padding: 0.75rem;
    }
    .chat-message {
        max-width: 90%;
    }
    .chat-avatar {
        width: 30px;
        height: 30px;
        min-width: 30px;
        font-size: 0.75rem;
    }
    .chat-bubble .chat-text {
        font-size: 0.85rem;
    }
}

@media (max-width: 480px) {
    .chat-messages-area {
        max-height: 280px;
    }
    .chat-message {
        max-width: 95%;
    }
}
"""


# =============================================================================
# AVATAR COLOR PALETTE (deterministic based on username)
# =============================================================================

AVATAR_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12",
    "#1abc9c", "#e67e22", "#2980b9", "#8e44ad", "#27ae60",
    "#d35400", "#16a085", "#c0392b", "#7f8c8d", "#2c3e50",
]


def _get_avatar_color(username: str) -> str:
    """Get a deterministic color for a username."""
    hash_val = sum(ord(c) for c in username)
    return AVATAR_COLORS[hash_val % len(AVATAR_COLORS)]


def _get_initial(username: str) -> str:
    """Get the initial letter(s) of a username."""
    parts = username.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return username[0].upper() if username else "?"


# =============================================================================
# MOCK GROUP DATA FOR MATCHING
# =============================================================================

def _get_mock_groups() -> List[Dict]:
    """Return mock group data for the matching view."""
    if "gm_groups" not in st.session_state:
        st.session_state.gm_groups = [
            {
                "id": "grp_001",
                "name": "Umrah Ramadan Barokah",
                "description": "Perjalanan umrah saat Ramadan dengan fokus ibadah.",
                "leader": "Ahmad Fauzi",
                "city": "Jakarta",
                "departure": "2026-03-15",
                "members": ["Ahmad Fauzi", "Siti Nurhaliza", "Budi Santoso", "Dewi Kartika"],
                "max_members": 15,
                "budget": "25-35 Juta",
                "style": "Fokus Ibadah",
                "status": "open",
            },
            {
                "id": "grp_002",
                "name": "Umrah Keluarga Sejahtera",
                "description": "Trip keluarga dengan fasilitas premium dan pendampingan khusus.",
                "leader": "Hasan Abdullah",
                "city": "Surabaya",
                "departure": "2026-04-20",
                "members": ["Hasan Abdullah", "Aisyah Putri", "Umar Faruq"],
                "max_members": 20,
                "budget": "35-50 Juta",
                "style": "Keluarga",
                "status": "open",
            },
            {
                "id": "grp_003",
                "name": "Umrah Muda Bersemangat",
                "description": "Komunitas anak muda yang ingin umrah bersama.",
                "leader": "Muhammad Rizki",
                "city": "Bandung",
                "departure": "2026-05-10",
                "members": ["Muhammad Rizki", "Fatimah Zahra", "Yusuf Mansur",
                            "Aminah Salsabila", "Ibrahim Hakim", "Zahra Aulia"],
                "max_members": 25,
                "budget": "20-25 Juta",
                "style": "Seimbang",
                "status": "open",
            },
            {
                "id": "grp_004",
                "name": "Umrah VIP Eksekutif",
                "description": "Perjalanan umrah premium untuk kalangan profesional.",
                "leader": "Ali Rahman",
                "city": "Jakarta",
                "departure": "2026-06-01",
                "members": ["Ali Rahman", "Nurul Hidayah"],
                "max_members": 10,
                "budget": "50-75 Juta",
                "style": "Premium",
                "status": "open",
            },
            {
                "id": "grp_005",
                "name": "Umrah Hemat Backpacker",
                "description": "Umrah dengan budget terjangkau, fokus ibadah.",
                "leader": "Hamzah Wijaya",
                "city": "Yogyakarta",
                "departure": "2026-04-05",
                "members": ["Hamzah Wijaya", "Maryam Azzahra", "Ismail Pratama",
                            "Halimah Kusuma", "Khadijah Sari"],
                "max_members": 30,
                "budget": "< 20 Juta",
                "style": "Hemat",
                "status": "open",
            },
        ]
    return st.session_state.gm_groups


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def _init_group_matching_state():
    """Initialize session state for group matching and chat."""
    if "group_chat_messages" not in st.session_state:
        st.session_state.group_chat_messages = []

    if "gm_joined_groups" not in st.session_state:
        st.session_state.gm_joined_groups = []

    if "gm_chat_xp_count" not in st.session_state:
        st.session_state.gm_chat_xp_count = 0

    if "gm_selected_chat_group" not in st.session_state:
        st.session_state.gm_selected_chat_group = None

    # Ensure mock groups exist
    _get_mock_groups()


def _get_current_username() -> str:
    """Get the current user's display name."""
    user = st.session_state.get("user")
    if user:
        if isinstance(user, dict):
            return user.get("name", user.get("email", "Pengguna"))
        if hasattr(user, "name"):
            return user.name
        if hasattr(user, "email"):
            return user.email
    return "Pengguna"


def _is_logged_in() -> bool:
    """Check if user is logged in."""
    user = st.session_state.get("user")
    return user is not None


# =============================================================================
# COMPATIBILITY SCORING
# =============================================================================

def _parse_budget_range(budget_str: str) -> Optional[tuple]:
    """Parse a budget string like '25-35 Juta' or '< 20 Juta' into (min, max) in millions.

    Returns None if parsing fails.
    """
    import re
    budget_str = budget_str.strip().lower().replace("juta", "").strip()

    # Handle "< 20" style
    match_lt = re.match(r'^<\s*(\d+)', budget_str)
    if match_lt:
        return (0, int(match_lt.group(1)))

    # Handle "> 50" style
    match_gt = re.match(r'^>\s*(\d+)', budget_str)
    if match_gt:
        return (int(match_gt.group(1)), 999)

    # Handle "25-35" or "25 - 35" style
    match_range = re.match(r'^(\d+)\s*[-–]\s*(\d+)', budget_str)
    if match_range:
        return (int(match_range.group(1)), int(match_range.group(2)))

    return None


def _calculate_compatibility(user_profile: Dict, group: Dict) -> int:
    """Calculate compatibility score between a user profile and a group.

    Scoring weights:
      - Budget range match: 30%
      - Travel dates match: 25%
      - Departure city: 20%
      - Language: 15%
      - Gender preference: 10%

    Args:
        user_profile: Dict with keys like 'budget_min', 'budget_max' (in millions),
                      'travel_date', 'city', 'language', 'gender_preference'.
        group: Dict from mock group data.

    Returns:
        Integer score 0-100.
    """
    score = 0.0

    # --- Budget match (30 points) ---
    user_budget_min = user_profile.get("budget_min", 0)
    user_budget_max = user_profile.get("budget_max", 0)
    group_budget = _parse_budget_range(group.get("budget", ""))

    if group_budget and user_budget_min and user_budget_max:
        g_min, g_max = group_budget
        # Calculate overlap between user budget and group budget
        overlap_min = max(user_budget_min, g_min)
        overlap_max = min(user_budget_max, g_max)
        if overlap_min <= overlap_max:
            # Full or partial overlap
            user_range = max(user_budget_max - user_budget_min, 1)
            overlap_size = overlap_max - overlap_min
            overlap_ratio = min(overlap_size / user_range, 1.0)
            score += 30 * overlap_ratio
        # else: no overlap, 0 points
    elif not user_budget_min and not user_budget_max:
        # No user budget data, give neutral score
        score += 15

    # --- Travel dates match (25 points) ---
    user_travel_date = user_profile.get("travel_date")
    group_departure = group.get("departure", "")

    if user_travel_date and group_departure:
        try:
            if isinstance(user_travel_date, str):
                user_dt = datetime.strptime(user_travel_date, "%Y-%m-%d")
            else:
                user_dt = user_travel_date
            group_dt = datetime.strptime(group_departure, "%Y-%m-%d")
            diff_days = abs((user_dt - group_dt).days)

            if diff_days == 0:
                score += 25
            elif diff_days <= 7:
                score += 20
            elif diff_days <= 14:
                score += 15
            elif diff_days <= 30:
                score += 10
            elif diff_days <= 60:
                score += 5
        except (ValueError, TypeError):
            score += 12  # neutral
    else:
        score += 12  # neutral when no date preference

    # --- Departure city (20 points) ---
    user_city = user_profile.get("city", "").strip().lower()
    group_city = group.get("city", "").strip().lower()

    if user_city and group_city:
        if user_city == group_city:
            score += 20
        elif user_city in group_city or group_city in user_city:
            score += 10
        # else: different cities, 0 points
    else:
        score += 10  # neutral

    # --- Language (15 points) ---
    user_lang = user_profile.get("language", "").strip().lower()
    group_lang = group.get("language", "indonesia").strip().lower()

    if user_lang and group_lang:
        if user_lang == group_lang:
            score += 15
        else:
            score += 5
    else:
        score += 15  # default: Indonesian, assume match

    # --- Gender preference (10 points) ---
    user_gender_pref = user_profile.get("gender_preference", "").strip().lower()
    group_gender_pref = group.get("gender_preference", "campuran").strip().lower()

    if user_gender_pref and group_gender_pref:
        if user_gender_pref == group_gender_pref or group_gender_pref == "campuran":
            score += 10
        else:
            score += 3
    else:
        score += 10  # neutral

    return min(int(round(score)), 100)


def _get_user_profile_from_session() -> Optional[Dict]:
    """Extract user profile data from session state for compatibility scoring.

    Looks at common session state keys that may be set by other pages
    (cost simulator, profile, onboarding, etc.).

    Returns:
        Dict with profile fields, or None if no meaningful data available.
    """
    user = st.session_state.get("user")
    profile = {}

    # Try to extract from user object
    if user:
        if isinstance(user, dict):
            profile["city"] = user.get("city", user.get("departure_city", ""))
            profile["language"] = user.get("language", "indonesia")
            profile["gender_preference"] = user.get("gender_preference", "")
        elif hasattr(user, "city"):
            profile["city"] = getattr(user, "city", "")
            profile["language"] = getattr(user, "language", "indonesia")
            profile["gender_preference"] = getattr(user, "gender_preference", "")

    # Try cost simulator session data
    sim = st.session_state.get("sim_budget_max") or st.session_state.get("budget_max")
    if sim:
        try:
            # Convert from Rupiah to millions
            profile["budget_max"] = int(sim) // 1_000_000
        except (ValueError, TypeError):
            pass

    sim_min = st.session_state.get("sim_budget_min") or st.session_state.get("budget_min")
    if sim_min:
        try:
            profile["budget_min"] = int(sim_min) // 1_000_000
        except (ValueError, TypeError):
            pass

    # Travel date
    travel_date = st.session_state.get("travel_date") or st.session_state.get("sim_travel_date")
    if travel_date:
        profile["travel_date"] = travel_date

    # Departure city from various sources
    if not profile.get("city"):
        profile["city"] = (
            st.session_state.get("departure_city", "")
            or st.session_state.get("sim_departure_city", "")
        )

    # Only return if we have at least one meaningful field
    has_data = any([
        profile.get("budget_min"),
        profile.get("budget_max"),
        profile.get("travel_date"),
        profile.get("city"),
    ])

    return profile if has_data else None


def _get_compatibility_badge_html(score: int) -> str:
    """Return an HTML badge string for the given compatibility score.

    Args:
        score: Integer 0-100.

    Returns:
        HTML string for the badge.
    """
    if score >= 90:
        css_class = "compat-excellent"
        label = "Sangat Cocok"
    elif score >= 70:
        css_class = "compat-good"
        label = "Cocok"
    elif score >= 50:
        css_class = "compat-fair"
        label = "Cukup Cocok"
    else:
        css_class = "compat-low"
        label = "Kurang Cocok"

    return (
        '<span class="compatibility-badge ' + css_class + '" '
        'aria-label="Skor kecocokan: ' + str(score) + '%">'
        + label + ' (' + str(score) + '%)'
        '</span>'
    )


def _get_compatibility_bar_html(score: int) -> str:
    """Return an HTML progress bar for the compatibility score.

    Args:
        score: Integer 0-100.

    Returns:
        HTML string for the score bar.
    """
    if score >= 90:
        color = "#4ade80"
    elif score >= 70:
        color = "#d4af37"
    elif score >= 50:
        color = "#fbbf24"
    else:
        color = "#8b949e"

    return (
        '<div class="compatibility-score-bar" aria-hidden="true">'
        '<div class="bar-fill" style="width:' + str(score) + '%;background:' + color + ';"></div>'
        '</div>'
    )


# =============================================================================
# GROUP CHAT FUNCTIONS
# =============================================================================

def _add_chat_message(group_id: str, user: str, message: str):
    """Add a message to the group chat store in session state."""
    msg = {
        "user": user,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "group_id": group_id,
    }
    st.session_state.group_chat_messages.append(msg)

    # Enforce max 100 messages per group
    group_messages = [
        m for m in st.session_state.group_chat_messages
        if m["group_id"] == group_id
    ]
    if len(group_messages) > 100:
        # Find and remove the oldest message for this group
        for i, m in enumerate(st.session_state.group_chat_messages):
            if m["group_id"] == group_id:
                st.session_state.group_chat_messages.pop(i)
                break


def _get_group_messages(group_id: str) -> List[Dict]:
    """Get all messages for a specific group."""
    return [
        m for m in st.session_state.group_chat_messages
        if m["group_id"] == group_id
    ]


def _format_chat_timestamp(iso_str: str) -> str:
    """Format an ISO timestamp into a readable string."""
    try:
        dt = datetime.fromisoformat(iso_str)
        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return dt.strftime("%d %b, %H:%M")
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} jam lalu"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} menit lalu"
        else:
            return "Baru saja"
    except (ValueError, TypeError):
        return ""


def render_group_chat():
    """Render the in-app group chat interface.

    Requires user to be logged in. Displays a chat for the selected group
    with message history, input field, and XP rewards.
    """
    if not _is_logged_in():
        st.info("Silakan login terlebih dahulu untuk menggunakan fitur chat grup.")
        return

    current_user = _get_current_username()
    joined_groups = st.session_state.gm_joined_groups
    all_groups = _get_mock_groups()

    if not joined_groups:
        st.markdown(
            '<div class="empty-state-card" style="background:linear-gradient(145deg,#1a1a2e 0%,#1e293b 100%);'
            'border-radius:16px;padding:2.5rem 1.5rem;text-align:center;border:1px solid #334155;margin:1rem 0;">'
            '<div class="empty-state-icon" style="font-size:3rem;margin-bottom:0.75rem;opacity:0.7;" '
            'aria-hidden="true">\U0001f465</div>'
            '<h3 style="color:#e2e8f0;margin:0 0 0.5rem 0;font-size:1.1rem;">'
            'Belum bergabung dengan grup</h3>'
            '<p style="color:#8e9fb3;font-size:0.9rem;margin:0;">'
            'Cari grup umrah yang cocok!</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "\U0001f50d Cari Grup Sekarang",
            key="btn_empty_find_group",
            use_container_width=True,
            type="primary",
        ):
            st.info("Gunakan tab 'Cari Grup' untuk menemukan grup umrah yang sesuai.")
        return

    # Group selector if user is in multiple groups
    joined_group_data = [g for g in all_groups if g["id"] in joined_groups]

    if len(joined_group_data) > 1:
        group_options = {g["id"]: g["name"] for g in joined_group_data}
        default_idx = 0
        current_sel = st.session_state.gm_selected_chat_group
        if current_sel and current_sel in group_options:
            keys_list = list(group_options.keys())
            default_idx = keys_list.index(current_sel)

        selected_id = st.selectbox(
            "Pilih Grup Chat",
            options=list(group_options.keys()),
            format_func=lambda x: group_options[x],
            index=default_idx,
            key="gm_chat_group_selector",
        )
        st.session_state.gm_selected_chat_group = selected_id
    elif len(joined_group_data) == 1:
        selected_id = joined_group_data[0]["id"]
        st.session_state.gm_selected_chat_group = selected_id
    else:
        st.warning("Grup yang Anda ikuti tidak ditemukan.")
        return

    # Find the selected group data
    selected_group = next((g for g in joined_group_data if g["id"] == selected_id), None)
    if not selected_group:
        st.error("Grup tidak ditemukan.")
        return

    # Chat header
    member_count = len(selected_group.get("members", []))
    header_html = (
        '<div class="group-chat-header">'
        '<h3><span aria-hidden="true">💬 </span>' + selected_group["name"] + '</h3>'
        '<span class="member-count">' + str(member_count) + ' anggota</span>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Messages area
    messages = _get_group_messages(selected_id)

    if not messages:
        st.markdown(
            '<div class="chat-empty-state">'
            '<div class="empty-icon" aria-hidden="true">🕌</div>'
            '<div class="empty-text">Belum ada pesan. Mulai percakapan!</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        # Build messages HTML
        messages_html_parts = []
        for msg in messages:
            msg_user = msg["user"]
            msg_text = msg["message"]
            msg_time = _format_chat_timestamp(msg["timestamp"])
            is_own = msg_user == current_user

            # Sanitize text for HTML display
            safe_text = (
                msg_text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

            avatar_color = _get_avatar_color(msg_user)
            initial = _get_initial(msg_user)
            own_class = " own-message" if is_own else ""

            msg_html = (
                '<div class="chat-message' + own_class + '">'
                '<div class="chat-avatar" style="background:' + avatar_color + ';"'
                ' aria-hidden="true">' + initial + '</div>'
                '<div class="chat-bubble">'
                '<div class="chat-user-name">' + msg_user + '</div>'
                '<div class="chat-text">' + safe_text + '</div>'
                '<div class="chat-timestamp">' + msg_time + '</div>'
                '</div>'
                '</div>'
            )
            messages_html_parts.append(msg_html)

        all_messages_html = "\n".join(messages_html_parts)
        container_html = (
            '<div class="chat-messages-area" role="log" aria-live="polite" '
            'aria-label="Pesan grup chat">'
            + all_messages_html
            + '</div>'
        )
        st.markdown(container_html, unsafe_allow_html=True)

    # Chat input
    st.markdown("---")
    col_input, col_btn = st.columns([5, 1])

    with col_input:
        chat_input = st.text_input(
            "Tulis pesan",
            placeholder="Ketik pesan Anda...",
            key="gm_chat_input",
            label_visibility="collapsed",
        )

    with col_btn:
        send_pressed = st.button(
            "Kirim",
            key="gm_chat_send_btn",
            type="primary",
            use_container_width=True,
        )

    if send_pressed and chat_input and chat_input.strip():
        cleaned = chat_input.strip()
        _add_chat_message(selected_id, current_user, cleaned)

        # XP award: +5 per message, max 3x per session
        if st.session_state.gm_chat_xp_count < 3:
            st.session_state.gm_chat_xp_count += 1
            add_xp_safe(5, "Mengirim pesan di grup chat")
            st.markdown(
                '<div class="chat-xp-toast">+5 XP - Pesan terkirim!</div>',
                unsafe_allow_html=True,
            )

        st.rerun()


# =============================================================================
# GROUP LIST / MATCHING VIEW
# =============================================================================

def render_group_list():
    """Render the group discovery and matching list with compatibility scoring."""
    groups = _get_mock_groups()
    joined = st.session_state.gm_joined_groups

    # Search filter
    search = st.text_input(
        "Cari grup...",
        placeholder="Nama grup, kota, atau gaya perjalanan...",
        key="gm_search_input",
        label_visibility="collapsed",
    )

    filtered = groups
    if search:
        term = search.lower()
        filtered = [
            g for g in groups
            if term in g["name"].lower()
            or term in g.get("city", "").lower()
            or term in g.get("style", "").lower()
            or term in g.get("description", "").lower()
        ]

    # Calculate compatibility scores
    user_profile = _get_user_profile_from_session()
    scored_groups = []
    for group in filtered:
        if user_profile:
            compat_score = _calculate_compatibility(user_profile, group)
        else:
            compat_score = -1  # No profile data, will show generic label
        scored_groups.append((group, compat_score))

    # Sort by compatibility score (highest first); groups without score go last
    scored_groups.sort(key=lambda x: x[1], reverse=True)

    # Stats
    open_count = len([g for g, _ in scored_groups if g["status"] == "open"])
    st.caption(f"Menampilkan {len(scored_groups)} grup | {open_count} masih open")

    if not scored_groups:
        st.markdown(
            '<div class="chat-empty-state">'
            '<div class="empty-icon" aria-hidden="true">🔍</div>'
            '<div class="empty-text">Tidak ada grup yang cocok dengan pencarian Anda.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    for group, compat_score in scored_groups:
        gid = group["id"]
        members = group.get("members", [])
        is_joined = gid in joined

        with st.container(border=True):
            col_info, col_action = st.columns([4, 1])

            with col_info:
                # Group name with compatibility badge
                if compat_score >= 0:
                    badge_html = _get_compatibility_badge_html(compat_score)
                else:
                    badge_html = (
                        '<span class="compatibility-badge compat-good" '
                        'aria-label="Cocok untuk Anda">'
                        'Cocok untuk Anda</span>'
                    )
                name_html = (
                    '<div style="display:flex;align-items:center;flex-wrap:wrap;">'
                    '<strong>' + group['name'] + '</strong>'
                    + badge_html
                    + '</div>'
                )
                st.markdown(name_html, unsafe_allow_html=True)

                st.caption(
                    f"📍 {group['city']} | 📅 {group['departure']} | "
                    f"💰 {group['budget']} | 🎨 {group['style']}"
                )
                st.caption(group["description"])

                # Compatibility score bar (only if we have a real score)
                if compat_score >= 0:
                    bar_html = _get_compatibility_bar_html(compat_score)
                    st.markdown(bar_html, unsafe_allow_html=True)

                # Member avatars display
                avatar_parts = []
                for member_name in members[:6]:
                    color = _get_avatar_color(member_name)
                    init = _get_initial(member_name)
                    avatar_parts.append(
                        '<span style="display:inline-flex;align-items:center;'
                        'justify-content:center;width:28px;height:28px;'
                        'border-radius:50%;background:' + color + ';'
                        'color:#fff;font-size:0.65rem;font-weight:bold;'
                        'margin-right:2px;" aria-hidden="true">'
                        + init + '</span>'
                    )
                if len(members) > 6:
                    avatar_parts.append(
                        '<span style="color:#8b949e;font-size:0.75rem;'
                        'margin-left:4px;">+' + str(len(members) - 6) + '</span>'
                    )
                avatars_html = (
                    '<div style="display:flex;align-items:center;margin-top:0.4rem;">'
                    + "".join(avatar_parts)
                    + '<span style="color:#8b949e;font-size:0.75rem;margin-left:8px;">'
                    + str(len(members)) + '/' + str(group["max_members"]) + ' anggota'
                    + '</span></div>'
                )
                st.markdown(avatars_html, unsafe_allow_html=True)

            with col_action:
                if is_joined:
                    st.success("Tergabung")
                elif group["status"] == "open":
                    if st.button(
                        "Gabung",
                        key=f"gm_join_{gid}",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state.gm_joined_groups.append(gid)
                        # Add user to mock member list
                        current_user = _get_current_username()
                        if current_user not in group["members"]:
                            group["members"].append(current_user)
                        # Set as selected chat group
                        st.session_state.gm_selected_chat_group = gid
                        add_xp_safe(10, "Bergabung grup matching")
                        st.rerun()
                else:
                    st.button(
                        "Penuh",
                        key=f"gm_full_{gid}",
                        disabled=True,
                        use_container_width=True,
                    )


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_group_matching_page():
    """Main group matching page renderer with integrated group chat."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("group_matching")
    except Exception:
        pass

    # Initialize state
    _init_group_matching_state()

    # Inject shared + page-specific CSS
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, EMPTY_STATE_CSS, GROUP_CHAT_CSS)

    # Hero banner
    hero_html = (
        '<div class="page-hero">'
        '<div class="bismillah">\u0628\u0650\u0633\u0652\u0645\u0650 '
        '\u0627\u0644\u0644\u0651\u064e\u0647\u0650 '
        '\u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0646\u0650 '
        '\u0627\u0644\u0631\u0651\u064e\u062d\u0650\u064a\u0645\u0650</div>'
        '<h1><span aria-hidden="true">👥 </span>Group Matching</h1>'
        '<div class="subtitle">Temukan dan bergabung dengan grup umrah yang sesuai</div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # Tabs: Group list + Group Chat
    tab_groups, tab_chat = st.tabs(["🔍 Cari Grup", "💬 Chat Grup"])

    with tab_groups:
        render_group_list()

    with tab_chat:
        render_group_chat()


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_group_matching_page", "render_group_chat"]
