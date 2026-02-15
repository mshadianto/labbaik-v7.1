"""
LABBAIK AI - Referral Page
===========================
Referral program UI for viral growth.
"""

import streamlit as st
from services.referral import get_referral_service, ReferralReward
from services.user import get_current_user, is_logged_in
from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, BADGE_CSS, PROGRESS_CSS, AI_CARD_CSS


def render_referral_page():
    """Main referral page"""
    try:
        from services.analytics import track_page
        track_page("referral")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS, BADGE_CSS, PROGRESS_CSS, AI_CARD_CSS)

    st.markdown("""
        <div class="page-hero">
            <h1>🎁 Program Referral</h1>
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

    # How it works
    render_how_it_works()

    st.markdown("---")

    # Referral history
    if stats["referrals"]:
        render_referral_history(stats["referrals"])

    # Milestones
    render_milestones(stats["total_referrals"])


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
            <div style="font-size: 0.9rem; color: #888;">Kode Referral</div>
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

    tips = ai_complete(
        "Berikan 3 tips singkat dan praktis untuk mengajak teman mendaftar program referral umrah. "
        "Format: nomor dan tips (tanpa markdown). Bahasa Indonesia.",
        system_prompt="Kamu adalah ahli marketing digital untuk travel umrah.",
        max_tokens=300,
    )
    if tips:
        st.markdown(f"""
            <div class="ai-card">
                <h4>🤖 Tips AI: Cara Efektif Mengajak Teman</h4>
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


def render_how_it_works():
    """Explain how referral works"""
    st.markdown("### Cara Kerja")

    st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0;">
            <div class="dark-card" style="text-align: center;">
                <div style="font-size: 2rem;">1️⃣</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">Bagikan Kode</div>
                <div style="font-size: 0.85rem; color: #888;">Kirim kode referral ke teman via WhatsApp, sosmed, dll</div>
            </div>
            <div class="dark-card" style="text-align: center;">
                <div style="font-size: 2rem;">2️⃣</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">Teman Daftar</div>
                <div style="font-size: 0.85rem; color: #888;">Teman memasukkan kode saat registrasi</div>
            </div>
            <div class="dark-card" style="text-align: center;">
                <div style="font-size: 2rem;">3️⃣</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">Dapat Reward</div>
                <div style="font-size: 0.85rem; color: #888;">Anda dapat Premium gratis!</div>
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
                    <div style="font-size: 0.8rem; color: #888;">{desc}</div>
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
            status_icons.append("✅ Signup")
        if ref["premium_rewarded"]:
            status_icons.append("⭐ Premium")

        status = " | ".join(status_icons) if status_icons else "Pending"

        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;
                        padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div>
                    <div>{ref['name']}</div>
                    <div style="font-size: 0.8rem; color: #888;">{ref['email']}</div>
                </div>
                <div style="font-size: 0.85rem; color: #4CAF50;">{status}</div>
            </div>
        """, unsafe_allow_html=True)


def render_milestones(total_referrals: int):
    """Show milestone progress"""
    st.markdown("### Milestones")

    milestones = [
        (5, ReferralReward.MILESTONE_5),
        (10, ReferralReward.MILESTONE_10),
        (25, ReferralReward.MILESTONE_25),
    ]

    for target, reward in milestones:
        progress = min(100, (total_referrals / target) * 100)
        achieved = total_referrals >= target
        color = "#4CAF50" if achieved else "#FFD700"
        icon = "✅" if achieved else "🎯"

        st.markdown(f"""
            <div style="margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span>{icon} {target} Referral</span>
                    <span style="color: {color};">+{reward.reward_days} hari</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="background: {color}; width: {progress}%;"></div>
                </div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 0.25rem;">
                    {total_referrals}/{target} referral
                </div>
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
            <div style="font-size: 0.7rem; color: #888;">{stats['total_referrals']} referral</div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Lihat Detail", key="ref_widget_btn", use_container_width=True):
        st.session_state.current_page = "referral"
        st.rerun()


__all__ = ["render_referral_page", "render_referral_widget"]
