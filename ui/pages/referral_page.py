"""
LABBAIK AI - Referral Page
===========================
Referral program UI for viral growth.
Includes milestone celebrations and global leaderboard.
"""

import streamlit as st
from services.referral import get_referral_service, ReferralReward
from services.user import get_current_user, is_logged_in
from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, BADGE_CSS, PROGRESS_CSS, AI_CARD_CSS


# =============================================================================
# MILESTONE DEFINITIONS
# =============================================================================

REFERRAL_MILESTONES = [
    {"count": 3, "title": "Pemula", "icon": "\U0001f331", "reward": "Badge Pemula", "xp": 25},
    {"count": 5, "title": "Aktif", "icon": "\u2b50", "reward": "Badge Bintang", "xp": 50},
    {"count": 10, "title": "Ambassador", "icon": "\U0001f3c6", "reward": "Badge Ambassador", "xp": 100},
    {"count": 25, "title": "Legend", "icon": "\U0001f451", "reward": "Badge Legend + Premium 1 Bulan", "xp": 250},
]


# =============================================================================
# MILESTONE & LEADERBOARD CSS
# =============================================================================

MILESTONE_LEADERBOARD_CSS = """
/* Milestone card base */
.milestone-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    padding: 1.25rem;
    border: 1px solid #333;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
}

.milestone-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Unlocked milestone */
.milestone-unlocked {
    border-color: #d4af37;
    background: linear-gradient(145deg, #1a1a2e 0%, #2a2a1e 100%);
}

.milestone-unlocked::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    border-radius: 15px;
    border: 2px solid #d4af37;
    animation: milestone-glow 2s ease-in-out infinite;
    pointer-events: none;
}

@keyframes milestone-glow {
    0%, 100% { box-shadow: 0 0 5px rgba(212, 175, 55, 0.3); }
    50% { box-shadow: 0 0 20px rgba(212, 175, 55, 0.6); }
}

/* Locked milestone */
.milestone-locked {
    border-color: #2a2a3e;
    opacity: 0.6;
}

.milestone-locked .milestone-icon {
    filter: grayscale(80%);
}

/* Milestone icon */
.milestone-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

/* Milestone title */
.milestone-title {
    font-size: 1rem;
    font-weight: bold;
    color: #e0e0e0;
    margin-bottom: 0.25rem;
}

.milestone-unlocked .milestone-title {
    color: #d4af37;
}

/* Milestone reward text */
.milestone-reward {
    font-size: 0.8rem;
    color: #b0b0b0;
}

.milestone-unlocked .milestone-reward {
    color: #b8c5d4;
}

/* Milestone count */
.milestone-count {
    font-size: 0.75rem;
    color: #8e9fb3;
    margin-top: 0.5rem;
}

/* Milestone progress section */
.milestone-progress {
    margin: 1.5rem 0;
    padding: 1.5rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    border: 1px solid #333;
}

.milestone-progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.milestone-progress-label {
    font-size: 0.9rem;
    color: #b8c5d4;
}

.milestone-progress-value {
    font-size: 0.9rem;
    font-weight: bold;
    color: #d4af37;
}

/* Current tier badge */
.current-tier-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: linear-gradient(135deg, #2a2a1e 0%, #1a1a2e 100%);
    border: 2px solid #d4af37;
    border-radius: 12px;
    margin-bottom: 1rem;
}

.current-tier-icon {
    font-size: 1.5rem;
}

.current-tier-info {
    text-align: left;
}

.current-tier-label {
    font-size: 0.7rem;
    color: #8e9fb3;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.current-tier-name {
    font-size: 1.1rem;
    font-weight: bold;
    color: #d4af37;
}

/* Celebration pulse for active milestone */
.milestone-celebration {
    animation: celebration-pulse 1.5s ease-in-out infinite;
}

@keyframes celebration-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

/* Leaderboard styles */
.leaderboard-container {
    margin-top: 1rem;
}

.leaderboard-row {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 10px;
    margin-bottom: 0.5rem;
    border: 1px solid #2a2a3e;
    transition: border-color 0.2s ease;
}

.leaderboard-row:hover {
    border-color: #444;
}

/* Highlight current user */
.leaderboard-highlight {
    border-color: #d4af37;
    background: linear-gradient(145deg, #2a2a1e 0%, #1e293b 100%);
}

.leaderboard-rank {
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-weight: bold;
    font-size: 0.9rem;
    flex-shrink: 0;
    margin-right: 0.75rem;
}

.rank-gold {
    background: linear-gradient(135deg, #d4af37, #f0d060);
    color: #1a1a2e;
}

.rank-silver {
    background: linear-gradient(135deg, #a0a0b0, #c0c0d0);
    color: #1a1a2e;
}

.rank-bronze {
    background: linear-gradient(135deg, #cd7f32, #e0a050);
    color: #1a1a2e;
}

.rank-default {
    background: #2a2a3e;
    color: #b0b0b0;
}

.leaderboard-avatar {
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 50%;
    background: linear-gradient(135deg, #334155, #475569);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    margin-right: 0.75rem;
    color: #b8c5d4;
}

.leaderboard-name {
    flex: 1;
    font-size: 0.9rem;
    color: #e0e0e0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.leaderboard-highlight .leaderboard-name {
    color: #d4af37;
    font-weight: bold;
}

.leaderboard-score {
    font-size: 0.85rem;
    font-weight: bold;
    color: #d4af37;
    flex-shrink: 0;
    margin-left: 0.5rem;
}

.leaderboard-community {
    text-align: center;
    padding: 1.25rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    border: 1px solid #333;
    margin-top: 1rem;
}

.leaderboard-community-number {
    font-size: 2rem;
    font-weight: bold;
    color: #d4af37;
}

.leaderboard-community-label {
    font-size: 0.85rem;
    color: #b0b0b0;
    margin-top: 0.25rem;
}

/* Responsive adjustments for milestones & leaderboard */
@media (max-width: 768px) {
    .milestone-card { padding: 1rem; }
    .milestone-icon { font-size: 2rem; }
    .milestone-title { font-size: 0.9rem; }
    .current-tier-badge { padding: 0.5rem 1rem; }
    .current-tier-name { font-size: 1rem; }
    .leaderboard-row { padding: 0.6rem 0.75rem; }
    .leaderboard-rank { width: 2rem; height: 2rem; font-size: 0.8rem; }
    .leaderboard-avatar { width: 2rem; height: 2rem; font-size: 0.85rem; }
    .leaderboard-name { font-size: 0.82rem; }
    .leaderboard-score { font-size: 0.8rem; }
}

@media (max-width: 480px) {
    .milestone-icon { font-size: 1.6rem; }
    .milestone-title { font-size: 0.82rem; }
    .milestone-reward { font-size: 0.72rem; }
    .current-tier-badge { flex-direction: column; text-align: center; }
    .current-tier-info { text-align: center; }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    .milestone-unlocked::after { animation: none; }
    .milestone-celebration { animation: none; }
    @keyframes milestone-glow { 0%, 100% { box-shadow: none; } }
}
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_current_milestone(total_referrals: int) -> dict:
    """Get the highest achieved milestone for the given referral count."""
    current = None
    for m in REFERRAL_MILESTONES:
        if total_referrals >= m["count"]:
            current = m
    return current


def _get_next_milestone(total_referrals: int) -> dict:
    """Get the next milestone to achieve."""
    for m in REFERRAL_MILESTONES:
        if total_referrals < m["count"]:
            return m
    return None


def _mask_name(name: str) -> str:
    """Mask a leaderboard name for partial privacy (show first name + initial)."""
    if not name:
        return "Anonim"
    parts = name.strip().split()
    if len(parts) == 1:
        if len(parts[0]) <= 3:
            return parts[0]
        return parts[0][:3] + "***"
    return parts[0] + " " + parts[1][0] + "."


def _get_rank_class(rank: int) -> str:
    """CSS class for rank badge."""
    if rank == 1:
        return "rank-gold"
    elif rank == 2:
        return "rank-silver"
    elif rank == 3:
        return "rank-bronze"
    return "rank-default"


def _get_avatar_initial(name: str) -> str:
    """Get initial letter for avatar placeholder."""
    if not name:
        return "?"
    return name.strip()[0].upper()


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_referral_page():
    """Main referral page"""
    try:
        from services.analytics import track_page
        track_page("referral")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS, BADGE_CSS, PROGRESS_CSS, AI_CARD_CSS, MILESTONE_LEADERBOARD_CSS)

    st.markdown("""
        <div class="page-hero">
            <h1><span aria-hidden="true">\U0001f381</span> Program Referral</h1>
            <div class="subtitle">Ajak teman, dapatkan Premium gratis!</div>
        </div>
    """, unsafe_allow_html=True)

    user = get_current_user()

    if not user:
        render_guest_view()
        return

    service = get_referral_service()
    stats = service.get_referral_stats(user.id)

    # Referral code card
    render_referral_code(stats["code"])

    st.markdown("---")

    # Stats
    render_stats(stats)

    st.markdown("---")

    # Milestone progress & celebration
    render_milestone_progress(stats["total_referrals"])

    st.markdown("---")

    # Global leaderboard
    try:
        global_stats = service.get_global_stats()
        render_leaderboard(global_stats, user)
    except Exception:
        st.info("Papan peringkat belum tersedia saat ini.")

    st.markdown("---")

    # How it works
    render_how_it_works()

    st.markdown("---")

    # Referral history
    if stats["referrals"]:
        render_referral_history(stats["referrals"])


def render_guest_view():
    """View for non-logged in users"""
    st.info("Login untuk mendapatkan kode referral Anda")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Masuk", type="primary", use_container_width=True):
            st.session_state.current_page = "auth"
            st.session_state.auth_mode = "login"
            st.rerun()
    with col2:
        if st.button("Daftar", use_container_width=True):
            st.session_state.current_page = "auth"
            st.session_state.auth_mode = "register"
            st.rerun()

    st.markdown("---")
    render_how_it_works()


def render_referral_code(code: str):
    """Display referral code with share options"""
    st.markdown("### Kode Referral Anda")

    # Code display
    st.markdown(f"""
        <div class="dark-card" style="text-align: center; border: 1px solid #d4af37;">
            <div style="font-size: 0.9rem; color: #b0b0b0;">Kode Referral</div>
            <div style="font-size: 2.5rem; font-weight: bold; color: #d4af37;
                        letter-spacing: 4px; margin: 0.5rem 0;">
                {code}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Share link
    share_link = f"https://app.labbaik.io/register?ref={code}"

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Link Referral", value=share_link, key="ref_link", disabled=True)

    with col2:
        st.markdown("")
        if st.button("Copy Link", use_container_width=True, type="primary"):
            st.toast("Link berhasil disalin!")
            # Note: Actual clipboard copy requires JavaScript
            if not st.session_state.get("referral_share_xp_awarded"):
                add_xp_safe(10, "Membagikan kode referral")
                st.session_state.referral_share_xp_awarded = True

    # Share buttons
    st.markdown("**Bagikan via:**")

    wa_text = f"Halo! Yuk pakai LABBAIK AI untuk perencanaan Umrah. Daftar gratis dengan kode saya: {code}\n\n{share_link}"
    newline = "\n"
    wa_url = f"https://wa.me/?text={wa_text.replace(' ', '%20').replace(newline, '%0A')}"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("WhatsApp", wa_url, use_container_width=True)
    with col2:
        st.link_button("Telegram", f"https://t.me/share/url?url={share_link}", use_container_width=True)
    with col3:
        st.link_button("Twitter", f"https://twitter.com/intent/tweet?text={wa_text}", use_container_width=True)

    # AI Tips
    if not st.session_state.get("referral_tips_xp_awarded"):
        add_xp_safe(5, "Melihat tips referral")
        st.session_state.referral_tips_xp_awarded = True

    with st.spinner("Memuat data referral..."):
        tips = ai_complete(
            "Berikan 3 tips singkat dan praktis untuk mengajak teman mendaftar program referral umrah. "
            "Format: nomor dan tips (tanpa markdown). Bahasa Indonesia.",
            system_prompt="Kamu adalah ahli marketing digital untuk travel umrah.",
            max_tokens=300,
        )
    if tips:
        st.markdown(f"""
            <div class="ai-card" role="status" aria-live="polite">
                <h4><span aria-hidden="true">\U0001f916</span> Tips AI: Cara Efektif Mengajak Teman</h4>
                <p>{tips}</p>
            </div>
        """, unsafe_allow_html=True)


def render_stats(stats: dict):
    """Display referral statistics"""
    st.markdown("### Statistik Anda")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Referral",
            stats["total_referrals"],
            help="Jumlah orang yang mendaftar dengan kode Anda"
        )

    with col2:
        st.metric(
            "Upgrade Premium",
            stats["total_premium_referrals"],
            help="Referral yang upgrade ke Premium"
        )

    with col3:
        st.metric(
            "Hari Premium Didapat",
            f"{stats['total_reward_days']} hari",
            help="Total hari Premium yang Anda dapatkan"
        )


# =============================================================================
# MILESTONE PROGRESS & CELEBRATION
# =============================================================================

def render_milestone_progress(total_referrals: int):
    """Show milestone progress with celebration and tier display."""
    try:
        st.markdown("### <span aria-hidden=\"true\">\U0001f3af</span> Milestone Referral", unsafe_allow_html=True)

        current = _get_current_milestone(total_referrals)
        next_ms = _get_next_milestone(total_referrals)

        # --- Current tier badge ---
        if current:
            celebration_class = "milestone-celebration" if total_referrals == current["count"] else ""
            st.markdown(f"""
                <div class="current-tier-badge {celebration_class}" role="status" aria-live="polite">
                    <div class="current-tier-icon"><span aria-hidden="true">{current['icon']}</span></div>
                    <div class="current-tier-info">
                        <div class="current-tier-label">Tier Saat Ini</div>
                        <div class="current-tier-name">{current['title']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Award XP for reaching a milestone (one-time per session)
            session_key = f"milestone_xp_{current['count']}"
            if not st.session_state.get(session_key):
                add_xp_safe(current["xp"], f"Mencapai milestone {current['title']}")
                st.session_state[session_key] = True
        else:
            st.markdown("""
                <div class="current-tier-badge">
                    <div class="current-tier-icon"><span aria-hidden="true">\U0001f331</span></div>
                    <div class="current-tier-info">
                        <div class="current-tier-label">Tier Saat Ini</div>
                        <div class="current-tier-name">Belum Ada Tier</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # --- Progress bar to next milestone ---
        if next_ms:
            # Calculate progress from current milestone (or 0) to next
            prev_count = current["count"] if current else 0
            range_size = next_ms["count"] - prev_count
            progress_in_range = total_referrals - prev_count
            progress_pct = min(100, (progress_in_range / range_size) * 100) if range_size > 0 else 0

            st.markdown(f"""
                <div class="milestone-progress">
                    <div class="milestone-progress-header">
                        <div class="milestone-progress-label">
                            Menuju <span aria-hidden="true">{next_ms['icon']}</span> {next_ms['title']}
                        </div>
                        <div class="milestone-progress-value">{total_referrals}/{next_ms['count']} referral</div>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="background: linear-gradient(90deg, #d4af37, #f0d060); width: {progress_pct:.1f}%;"></div>
                    </div>
                    <div style="font-size: 0.8rem; color: #8e9fb3; margin-top: 0.5rem;">
                        {next_ms['count'] - total_referrals} referral lagi untuk membuka {next_ms['title']}
                        &mdash; Reward: {next_ms['reward']} (+{next_ms['xp']} XP)
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # All milestones achieved
            st.markdown("""
                <div class="milestone-progress" style="text-align: center; border-color: #d4af37;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">
                        <span aria-hidden="true">\U0001f389</span>
                    </div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #d4af37;">
                        Semua Milestone Tercapai!
                    </div>
                    <div style="font-size: 0.85rem; color: #b8c5d4; margin-top: 0.25rem;">
                        Anda telah mencapai level tertinggi. Terima kasih atas kontribusi Anda!
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # --- All milestones grid ---
        st.markdown("")
        cols = st.columns(len(REFERRAL_MILESTONES))

        for idx, milestone in enumerate(REFERRAL_MILESTONES):
            with cols[idx]:
                achieved = total_referrals >= milestone["count"]
                status_class = "milestone-unlocked" if achieved else "milestone-locked"
                check_mark = '<div style="color: #4CAF50; font-size: 0.8rem; margin-top: 0.25rem;">Tercapai</div>' if achieved else ""

                st.markdown(f"""
                    <div class="milestone-card {status_class}">
                        <div class="milestone-icon"><span aria-hidden="true">{milestone['icon']}</span></div>
                        <div class="milestone-title">{milestone['title']}</div>
                        <div class="milestone-reward">{milestone['reward']}</div>
                        <div class="milestone-count">{milestone['count']} referral &middot; +{milestone['xp']} XP</div>
                        {check_mark}
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.warning("Tidak dapat memuat milestone saat ini.")


# =============================================================================
# GLOBAL LEADERBOARD
# =============================================================================

def render_leaderboard(global_stats: dict, user):
    """Show global referral leaderboard."""
    try:
        st.markdown("### <span aria-hidden=\"true\">\U0001f3c5</span> Papan Peringkat", unsafe_allow_html=True)

        top_referrers = global_stats.get("top_referrers", [])

        if not top_referrers:
            st.markdown("""
                <div style="text-align: center; padding: 2rem; color: #8e9fb3;">
                    <div style="font-size: 2rem; opacity: 0.5;"><span aria-hidden="true">\U0001f3c6</span></div>
                    <div style="margin-top: 0.5rem;">Belum ada data peringkat. Jadilah yang pertama!</div>
                </div>
            """, unsafe_allow_html=True)
            return

        # Determine current user name for highlighting
        current_user_name = getattr(user, "name", "") if user else ""

        st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)

        user_found_in_top = False

        for rank, referrer in enumerate(top_referrers, start=1):
            name = referrer.get("name", "Anonim")
            referral_count = referrer.get("referrals", 0)
            reward_days = referrer.get("reward_days", 0)

            # Highlight if this is the current user
            is_current = (name == current_user_name) if current_user_name else False
            if is_current:
                user_found_in_top = True
            row_class = "leaderboard-row leaderboard-highlight" if is_current else "leaderboard-row"
            rank_class = _get_rank_class(rank)
            display_name = _mask_name(name) if not is_current else name
            initial = _get_avatar_initial(name)

            # Rank display: medal emoji for top 3
            if rank == 1:
                rank_display = '<span aria-hidden="true">\U0001f947</span>'
            elif rank == 2:
                rank_display = '<span aria-hidden="true">\U0001f948</span>'
            elif rank == 3:
                rank_display = '<span aria-hidden="true">\U0001f949</span>'
            else:
                rank_display = str(rank)

            you_label = ' <span style="font-size: 0.7rem; color: #d4af37;">(Anda)</span>' if is_current else ""

            st.markdown(f"""
                <div class="{row_class}">
                    <div class="leaderboard-rank {rank_class}">{rank_display}</div>
                    <div class="leaderboard-avatar">{initial}</div>
                    <div class="leaderboard-name">{display_name}{you_label}</div>
                    <div class="leaderboard-score">{referral_count} referral</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # If current user is not in top 10, show their position hint
        if not user_found_in_top and current_user_name:
            st.markdown(f"""
                <div style="text-align: center; padding: 0.75rem; margin-top: 0.5rem;
                            background: rgba(212, 175, 55, 0.08); border-radius: 10px;
                            font-size: 0.85rem; color: #b8c5d4;">
                    <span aria-hidden="true">\U0001f4aa</span> Terus ajak teman untuk masuk papan peringkat!
                </div>
            """, unsafe_allow_html=True)

        # Community total
        total_community = global_stats.get("total_referrals", 0)
        total_reward_days = global_stats.get("total_reward_days_given", 0)

        st.markdown(f"""
            <div class="leaderboard-community">
                <div class="leaderboard-community-number">{total_community}</div>
                <div class="leaderboard-community-label">Total Referral Komunitas</div>
                <div style="font-size: 0.8rem; color: #8e9fb3; margin-top: 0.5rem;">
                    {total_reward_days} hari Premium telah diberikan kepada komunitas
                </div>
            </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.info("Papan peringkat belum tersedia saat ini.")


def render_how_it_works():
    """Explain how referral works"""
    st.markdown("### Cara Kerja")

    st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0;">
            <div class="dark-card" style="text-align: center;">
                <div style="font-size: 2rem;"><span aria-hidden="true">1\ufe0f\u20e3</span></div>
                <div style="font-weight: bold; margin: 0.5rem 0;">Bagikan Kode</div>
                <div style="font-size: 0.85rem; color: #b0b0b0;">Kirim kode referral ke teman via WhatsApp, sosmed, dll</div>
            </div>
            <div class="dark-card" style="text-align: center;">
                <div style="font-size: 2rem;"><span aria-hidden="true">2\ufe0f\u20e3</span></div>
                <div style="font-weight: bold; margin: 0.5rem 0;">Teman Daftar</div>
                <div style="font-size: 0.85rem; color: #b0b0b0;">Teman memasukkan kode saat registrasi</div>
            </div>
            <div class="dark-card" style="text-align: center;">
                <div style="font-size: 2rem;"><span aria-hidden="true">3\ufe0f\u20e3</span></div>
                <div style="font-weight: bold; margin: 0.5rem 0;">Dapat Reward</div>
                <div style="font-size: 0.85rem; color: #b0b0b0;">Anda dapat Premium gratis!</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Rewards")

    rewards = [
        ("Teman mendaftar", f"+{ReferralReward.SIGNUP_BONUS.reward_days} hari Premium", "Setiap teman yang daftar dengan kode Anda"),
        ("Teman upgrade Premium", f"+{ReferralReward.PREMIUM_BONUS.reward_days} hari Premium", "Saat referral Anda upgrade"),
        ("5 referral", f"+{ReferralReward.MILESTONE_5.reward_days} hari Premium", "Bonus milestone"),
        ("10 referral", f"+{ReferralReward.MILESTONE_10.reward_days} hari Premium", "Bonus milestone"),
        ("25 referral", f"+{ReferralReward.MILESTONE_25.reward_days} hari Premium", "Bonus milestone"),
    ]

    for action, reward, desc in rewards:
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;
                        padding: 0.75rem; background: rgba(255,255,255,0.05);
                        border-radius: 8px; margin: 0.5rem 0;">
                <div>
                    <div style="font-weight: bold;">{action}</div>
                    <div style="font-size: 0.8rem; color: #b0b0b0;">{desc}</div>
                </div>
                <div style="color: #FFD700; font-weight: bold;">{reward}</div>
            </div>
        """, unsafe_allow_html=True)


def render_referral_history(referrals: list):
    """Show referral history"""
    st.markdown("### Riwayat Referral")

    for ref in referrals:
        status_icons = []
        if ref["signup_rewarded"]:
            status_icons.append('<span aria-hidden="true">\u2705</span> Signup')
        if ref["premium_rewarded"]:
            status_icons.append('<span aria-hidden="true">\u2b50</span> Premium')

        status = " | ".join(status_icons) if status_icons else "Pending"

        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;
                        padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div>
                    <div>{ref['name']}</div>
                    <div style="font-size: 0.8rem; color: #b0b0b0;">{ref['email']}</div>
                </div>
                <div style="font-size: 0.85rem; color: #4CAF50;">{status}</div>
            </div>
        """, unsafe_allow_html=True)


def render_referral_widget():
    """Mini widget for sidebar"""
    user = get_current_user()

    if not user:
        return

    service = get_referral_service()
    stats = service.get_referral_stats(user.id)

    st.markdown(f"""
        <div style="padding: 0.5rem; background: rgba(255,215,0,0.1);
                    border-radius: 8px; text-align: center;">
            <div style="font-size: 0.75rem; color: #FFD700;">Kode Referral</div>
            <div style="font-weight: bold;">{stats['code']}</div>
            <div style="font-size: 0.7rem; color: #b0b0b0;">{stats['total_referrals']} referral</div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Lihat Detail", key="ref_widget_btn", use_container_width=True):
        st.session_state.current_page = "referral"
        st.rerun()


__all__ = ["render_referral_page", "render_referral_widget"]
