"""
LABBAIK AI - Subscription Page
===============================
Premium subscription upgrade UI.
"""

import streamlit as st
from datetime import datetime
from services.subscription import (
    SubscriptionPlan, SubscriptionStatus, Subscription,
    SubscriptionService, get_subscription_service
)
from services.user import get_current_user, is_logged_in, UserRole
from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS


def format_price(amount: int) -> str:
    """Format price in IDR"""
    return f"Rp {amount:,.0f}".replace(",", ".")


def render_subscription_page():
    """Main subscription page"""
    try:
        from services.analytics import track_page
        track_page("subscription")
    except Exception:
        pass
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS)

    if not st.session_state.get("subscription_view_xp_awarded"):
        add_xp_safe(5, "Melihat paket Premium")
        st.session_state.subscription_view_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1>⭐ Upgrade ke Premium</h1>
            <div class="subtitle">Akses penuh semua fitur LABBAIK AI untuk perjalanan umrah terbaik</div>
        </div>
    """, unsafe_allow_html=True)

    user = get_current_user()

    # Check if logged in
    if not user:
        st.warning("Silakan login terlebih dahulu untuk upgrade")
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
        return

    # Check current subscription
    service = get_subscription_service()
    current_sub = service.get_user_subscription(user.id)

    if current_sub and current_sub.is_active:
        render_current_subscription(current_sub)
        st.markdown("---")
        st.markdown("### Perpanjang atau Upgrade")

    # Premium benefits
    render_premium_benefits()

    st.markdown("---")

    # Pricing plans
    render_pricing_plans(user, current_sub)

    st.markdown("---")

    # FAQ
    render_faq()


def render_current_subscription(sub: Subscription):
    """Show current subscription status"""
    st.success(f"### Status Premium Anda: Aktif")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Paket", sub.plan.display_name)
    with col2:
        st.metric("Sisa Hari", f"{sub.days_remaining} hari")
    with col3:
        if sub.expires_at:
            st.metric("Berakhir", sub.expires_at.strftime("%d %b %Y"))


def render_premium_benefits():
    """Show premium benefits"""
    st.markdown("### Keuntungan Premium")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Fitur Chat AI**
        - Chat tanpa batas (vs 10/hari)
        - Respons prioritas
        - Riwayat chat tersimpan

        **Fitur Planning**
        - AI Itinerary Generator
        - Group Tracking real-time
        - Download laporan PDF
        """)

    with col2:
        st.markdown("""
        **Fitur Harga**
        - Notifikasi harga turun
        - Akses harga eksklusif
        - Booking prioritas

        **Support**
        - WhatsApp support 24/7
        - Prioritas bantuan
        - Early access fitur baru
        """)

    recommendation = ai_complete(
        "Berikan rekomendasi singkat (3-4 kalimat) mengapa jamaah umrah sebaiknya menggunakan "
        "fitur Premium untuk perencanaan umrah mereka. Bahasa Indonesia, persuasif tapi jujur.",
        system_prompt="Kamu adalah advisor perjalanan umrah yang berpengalaman.",
        max_tokens=200,
    )
    if recommendation:
        st.markdown(f"""
            <div class="ai-card">
                <h4>🤖 Rekomendasi AI</h4>
                <p>{recommendation}</p>
            </div>
        """, unsafe_allow_html=True)


def render_pricing_plans(user, current_sub):
    """Show pricing plan cards"""
    st.markdown("### Pilih Paket")

    # Promo code input
    promo_code = st.text_input("Punya kode promo?", placeholder="Masukkan kode promo")
    discount = 0
    if promo_code:
        discount = get_subscription_service()._validate_promo(promo_code)
        if discount > 0:
            st.success(f"Kode valid! Diskon {discount}%")
        else:
            st.error("Kode tidak valid")

    st.markdown("")

    # Plan cards
    col1, col2, col3 = st.columns(3)

    plans = [
        (SubscriptionPlan.MONTHLY, col1, False),
        (SubscriptionPlan.QUARTERLY, col2, True),  # Popular
        (SubscriptionPlan.YEARLY, col3, False),
    ]

    for plan, col, is_popular in plans:
        with col:
            price = plan.price_idr
            if discount > 0:
                price = int(price * (100 - discount) / 100)

            # Card styling
            border_color = "#FFD700" if is_popular else "rgba(255,255,255,0.1)"
            badge = '<div style="background: #FFD700; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; margin-bottom: 8px;">POPULER</div>' if is_popular else ""

            st.markdown(f"""
                <div class="dark-card" style="text-align: center; border: 2px solid {border_color};">
                    {badge}
                    <h3 style="margin: 0; color: #fff;">{plan.display_name}</h3>
                    <div style="font-size: 2rem; font-weight: bold; color: #d4af37; margin: 1rem 0;">
                        {format_price(price)}
                    </div>
                    <div style="color: #888; font-size: 0.85rem;">
                        {format_price(plan.price_idr // (plan.duration_days // 30))}/bulan
                    </div>
                    {"<div style='color: #4CAF50; margin-top: 0.5rem;'>Hemat " + str(plan.savings_percent) + "%</div>" if plan.savings_percent > 0 else ""}
                </div>
            """, unsafe_allow_html=True)

            if st.button(
                f"Pilih {plan.display_name}",
                key=f"select_{plan.value}",
                use_container_width=True,
                type="primary" if is_popular else "secondary"
            ):
                st.session_state.selected_plan = plan
                st.session_state.promo_code = promo_code if discount > 0 else None
                st.session_state.show_payment = True
                if not st.session_state.get("subscription_select_xp_awarded"):
                    add_xp_safe(15, "Memilih paket Premium")
                    st.session_state.subscription_select_xp_awarded = True
                st.rerun()

    # Lifetime option
    st.markdown("---")
    st.markdown("### Paket Selamanya")

    lifetime = SubscriptionPlan.LIFETIME
    lifetime_price = lifetime.price_idr
    if discount > 0:
        lifetime_price = int(lifetime_price * (100 - discount) / 100)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        **Akses Premium Selamanya** - {format_price(lifetime_price)}

        Bayar sekali, akses selamanya. Termasuk semua fitur premium
        dan update di masa depan. Hemat {lifetime.savings_percent}% dibanding langganan 2 tahun.
        """)
    with col2:
        if st.button("Pilih Lifetime", key="select_lifetime", use_container_width=True):
            st.session_state.selected_plan = lifetime
            st.session_state.promo_code = promo_code if discount > 0 else None
            st.session_state.show_payment = True
            if not st.session_state.get("subscription_select_xp_awarded"):
                add_xp_safe(15, "Memilih paket Premium")
                st.session_state.subscription_select_xp_awarded = True
            st.rerun()

    # Payment modal
    if st.session_state.get("show_payment"):
        render_payment_modal(user)


def render_payment_modal(user):
    """Show payment options"""
    plan = st.session_state.get("selected_plan")
    promo = st.session_state.get("promo_code")

    if not plan:
        return

    st.markdown("---")
    st.markdown(f"### Pembayaran - {plan.display_name}")

    service = get_subscription_service()
    discount = service._validate_promo(promo) if promo else 0

    price = plan.price_idr
    if discount > 0:
        price = int(price * (100 - discount) / 100)

    st.markdown(f"""
    **Detail Pesanan:**
    - Paket: {plan.display_name}
    - Durasi: {plan.duration_days} hari
    - Harga: {format_price(price)}
    {"- Promo: " + promo + f" (-{discount}%)" if promo else ""}
    """)

    st.markdown("---")
    st.markdown("**Pilih Metode Pembayaran:**")

    payment_methods = [
        ("QRIS", "qris", "Scan QR untuk bayar"),
        ("Transfer Bank", "bank", "BCA, Mandiri, BNI, BRI"),
        ("E-Wallet", "ewallet", "GoPay, OVO, DANA, ShopeePay"),
    ]

    for name, method, desc in payment_methods:
        if st.button(f"{name} - {desc}", key=f"pay_{method}", use_container_width=True):
            # Create pending subscription
            success, msg, sub = service.create_subscription(
                user_id=user.id,
                plan=plan,
                payment_method=method,
                promo_code=promo
            )

            if success:
                st.session_state.pending_subscription = sub.id
                st.success("Pesanan dibuat! Silakan lakukan pembayaran.")

                # Show payment instructions
                render_payment_instructions(method, price, sub.id)
            else:
                st.error(f"Gagal: {msg}")

    col1, col2 = st.columns(2)
    with col2:
        if st.button("Batal", use_container_width=True):
            st.session_state.show_payment = False
            st.session_state.selected_plan = None
            st.rerun()


def render_payment_instructions(method: str, amount: int, order_id: int):
    """Show payment instructions"""

    if method == "qris":
        st.markdown("""
        ### Scan QRIS

        1. Buka aplikasi e-wallet atau mobile banking
        2. Pilih menu Scan/QRIS
        3. Scan QR code di bawah
        4. Konfirmasi pembayaran
        """)
        # Placeholder for QRIS image
        st.info("QR Code akan ditampilkan di sini setelah integrasi dengan Midtrans")

    elif method == "bank":
        st.markdown(f"""
        ### Transfer Bank

        **BCA**
        - No. Rekening: 1234567890
        - Atas Nama: PT LABBAIK TECHNOLOGY

        **Jumlah Transfer:** {format_price(amount)}

        *Harap transfer dengan jumlah tepat untuk verifikasi otomatis*
        """)

    elif method == "ewallet":
        st.markdown("""
        ### E-Wallet

        Pilih e-wallet yang ingin digunakan:
        """)
        ewallets = ["GoPay", "OVO", "DANA", "ShopeePay"]
        for ew in ewallets:
            st.button(f"Bayar dengan {ew}", key=f"ew_{ew}", use_container_width=True)

    st.markdown(f"""
    ---
    **Order ID:** #{order_id}

    Setelah pembayaran, konfirmasi akan diproses dalam 1x24 jam.
    Untuk konfirmasi manual, hubungi WhatsApp: 0812-xxxx-xxxx
    """)


def render_faq():
    """Render FAQ section"""
    st.markdown("### FAQ")

    faqs = [
        ("Bagaimana cara upgrade?", "Pilih paket di atas, lakukan pembayaran, dan akun akan otomatis di-upgrade setelah pembayaran dikonfirmasi."),
        ("Bisa refund?", "Refund tersedia dalam 7 hari pertama jika Anda tidak puas dengan layanan."),
        ("Apa yang terjadi jika langganan habis?", "Akun akan kembali ke versi Gratis. Data Anda tetap tersimpan."),
        ("Bagaimana cara perpanjang?", "Langganan akan otomatis diperpanjang. Anda bisa membatalkan kapan saja."),
    ]

    for q, a in faqs:
        with st.expander(q):
            st.markdown(a)


def render_subscription_widget():
    """Mini widget for sidebar showing subscription status"""
    user = get_current_user()

    if not user:
        return

    service = get_subscription_service()
    sub = service.get_user_subscription(user.id)

    if sub and sub.is_active:
        st.markdown(f"""
            <div style="padding: 0.5rem; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                        border-radius: 8px; text-align: center;">
                <div style="font-size: 0.8rem; color: #000; font-weight: bold;">PREMIUM</div>
                <div style="font-size: 0.7rem; color: #333;">{sub.days_remaining} hari tersisa</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        if st.button("Upgrade Premium", key="sidebar_upgrade", use_container_width=True, type="secondary"):
            st.session_state.current_page = "subscription"
            st.rerun()
