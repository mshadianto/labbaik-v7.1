"""
LABBAIK AI - Subscription Page
===============================
Premium subscription upgrade UI with self-service subscription management.
Includes plan comparison, billing history, upgrade flow, and cancellation.
"""

import os
import streamlit as st
from datetime import datetime, timedelta
from services.subscription import (
    SubscriptionPlan, SubscriptionStatus, Subscription,
    SubscriptionService, get_subscription_service
)
from services.user import get_current_user, is_logged_in, UserRole
from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS
from ui.components import format_idr as format_price


def _get_admin_whatsapp() -> str:
    """Get admin WhatsApp number from env/secrets, fallback to default."""
    number = os.getenv("ADMIN_WHATSAPP")
    if number:
        return number.strip().lstrip("+")
    try:
        number = st.secrets.get("ADMIN_WHATSAPP")
        if number:
            return str(number).strip().lstrip("+")
    except Exception:
        pass
    return "6281200000000"


# =============================================================================
# SUBSCRIPTION PAGE CSS
# =============================================================================

SUBSCRIPTION_CSS = """
/* Plan comparison cards */
.plan-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 1.5rem 1.25rem;
    border: 2px solid #333;
    text-align: center;
    position: relative;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    min-height: 480px;
    display: flex;
    flex-direction: column;
}

.plan-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.plan-card.current {
    border-color: #4ade80;
    box-shadow: 0 0 16px rgba(74, 222, 128, 0.15);
}

.plan-card.popular {
    border-color: #FFD700;
    box-shadow: 0 0 16px rgba(255, 215, 0, 0.15);
}

.plan-badge {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: #FFD700;
    color: #000;
    padding: 3px 14px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.plan-badge.current-badge {
    background: #4ade80;
}

.plan-name {
    font-size: 1.3rem;
    font-weight: 700;
    color: #fff;
    margin: 0.75rem 0 0.25rem;
}

.plan-price {
    font-size: 2rem;
    font-weight: 800;
    color: #d4af37;
    margin: 0.5rem 0;
    line-height: 1.2;
}

.plan-price .period {
    font-size: 0.85rem;
    font-weight: 400;
    color: #b0b0b0;
}

.plan-price.free-price {
    color: #4ade80;
}

/* Feature comparison table */
.comparison-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin-top: 1.5rem;
}

.comparison-table th {
    background: #1a1a2e;
    color: #d4af37;
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.85rem;
    font-weight: 600;
    border-bottom: 2px solid #333;
}

.comparison-table th:not(:first-child) {
    text-align: center;
}

.comparison-table td {
    padding: 0.65rem 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    color: #ccc;
    font-size: 0.85rem;
}

.comparison-table td:not(:first-child) {
    text-align: center;
}

.comparison-table tr:hover td {
    background: rgba(212, 175, 55, 0.04);
}

.comparison-table .feature-name {
    color: #e0e0e0;
    font-weight: 500;
}

.check-yes {
    color: #4ade80;
    font-weight: bold;
    font-size: 1rem;
}

.check-no {
    color: #f87171;
    font-size: 0.9rem;
}

.check-text {
    color: #b8c5d4;
    font-size: 0.8rem;
}

/* Billing history table */
.billing-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin-top: 1rem;
}

.billing-table th {
    background: #1a1a2e;
    color: #d4af37;
    padding: 0.7rem 1rem;
    text-align: left;
    font-size: 0.82rem;
    font-weight: 600;
    border-bottom: 2px solid #333;
}

.billing-table td {
    padding: 0.65rem 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    color: #ccc;
    font-size: 0.85rem;
    vertical-align: middle;
}

.billing-table tr:hover td {
    background: rgba(212, 175, 55, 0.04);
}

.billing-status-paid {
    display: inline-block;
    background: #1a3a1a;
    color: #4ade80;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}

.billing-status-pending {
    display: inline-block;
    background: #4a3a1a;
    color: #fbbf24;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}

/* Upgrade flow steps */
.upgrade-step {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    border: 1px solid #333;
    margin-bottom: 1rem;
}

.upgrade-step.active {
    border-color: #d4af37;
    box-shadow: 0 0 12px rgba(212, 175, 55, 0.1);
}

.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #333;
    color: #b0b0b0;
    font-size: 0.8rem;
    font-weight: 700;
    margin-right: 0.5rem;
}

.step-number.active {
    background: #d4af37;
    color: #000;
}

.step-number.done {
    background: #4ade80;
    color: #000;
}

/* Cancel flow */
.cancel-warning {
    background: linear-gradient(145deg, #2e1a1a 0%, #3b1e1e 100%);
    border: 1px solid #f87171;
    border-radius: 14px;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
}

.cancel-warning h3 {
    color: #f87171;
    margin-top: 0;
}

.feature-loss-item {
    display: flex;
    align-items: center;
    padding: 0.4rem 0;
    color: #ccc;
    font-size: 0.88rem;
}

.feature-loss-item .loss-icon {
    color: #f87171;
    margin-right: 0.5rem;
    font-weight: bold;
}

/* Retention offer */
.retention-offer {
    background: linear-gradient(145deg, #1a2e1a 0%, #1e3b1e 100%);
    border: 1px solid #4ade80;
    border-radius: 14px;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
}

.retention-offer h3 {
    color: #4ade80;
    margin-top: 0;
}

/* Plan feature list in cards */
.plan-features {
    text-align: left;
    margin: 1rem 0;
    flex-grow: 1;
}

.plan-feature-item {
    display: flex;
    align-items: flex-start;
    padding: 0.3rem 0;
    font-size: 0.82rem;
    color: #ccc;
    gap: 0.4rem;
}

.plan-feature-item .feat-icon {
    flex-shrink: 0;
    margin-top: 1px;
}

.plan-feature-item .feat-icon.yes { color: #4ade80; }
.plan-feature-item .feat-icon.no { color: #555; }
.plan-feature-item .feat-icon.limited { color: #fbbf24; }

/* Responsive adjustments for plan cards */
@media (max-width: 768px) {
    .plan-card { min-height: auto; padding: 1rem; }
    .plan-name { font-size: 1.1rem; }
    .plan-price { font-size: 1.5rem; }
    .comparison-table th, .comparison-table td { padding: 0.5rem 0.5rem; font-size: 0.78rem; }
    .billing-table th, .billing-table td { padding: 0.5rem; font-size: 0.78rem; }
}

@media (max-width: 480px) {
    .plan-card { min-height: auto; padding: 0.8rem; }
    .plan-name { font-size: 1rem; }
    .plan-price { font-size: 1.3rem; }
}
"""


def _get_current_plan_key(current_sub) -> str:
    """Determine the current plan key for highlighting."""
    if current_sub and current_sub.is_active:
        plan_val = current_sub.plan.value
        if plan_val in ("monthly", "quarterly", "yearly", "lifetime"):
            return "premium"
        return plan_val
    return "free"


def _get_demo_billing_history():
    """Generate demo billing history entries."""
    now = datetime.now()
    return [
        {
            "tanggal": (now - timedelta(days=60)).strftime("%d %b %Y"),
            "paket": "Premium (Bulanan)",
            "jumlah": 99000,
            "status": "paid",
            "invoice": "INV-2026-001",
        },
        {
            "tanggal": (now - timedelta(days=30)).strftime("%d %b %Y"),
            "paket": "Premium (Bulanan)",
            "jumlah": 99000,
            "status": "paid",
            "invoice": "INV-2026-002",
        },
        {
            "tanggal": now.strftime("%d %b %Y"),
            "paket": "Premium (Bulanan)",
            "jumlah": 99000,
            "status": "paid",
            "invoice": "INV-2026-003",
        },
    ]


def _generate_invoice_text(entry: dict) -> str:
    """Generate a simple text invoice for download."""
    return (
        "=" * 48 + "\n"
        "               LABBAIK AI - INVOICE\n"
        "=" * 48 + "\n"
        f"Invoice No  : {entry['invoice']}\n"
        f"Tanggal     : {entry['tanggal']}\n"
        f"Paket       : {entry['paket']}\n"
        "------------------------------------------------\n"
        f"Jumlah      : {format_price(entry['jumlah'])}\n"
        f"Status      : {'Lunas' if entry['status'] == 'paid' else 'Pending'}\n"
        "------------------------------------------------\n"
        "PT LABBAIK TECHNOLOGY\n"
        "Email: admin@labbaik.io\n"
        "=" * 48 + "\n"
        "Terima kasih atas kepercayaan Anda.\n"
    )


# =============================================================================
# PLAN COMPARISON
# =============================================================================

def render_plan_comparison(current_sub=None):
    """Show 3 plans side by side: Free, Premium, VIP with feature comparison."""
    current_key = _get_current_plan_key(current_sub)

    # Award XP for viewing comparison
    if not st.session_state.get("subscription_comparison_xp_awarded"):
        add_xp_safe(5, "Melihat perbandingan paket")
        st.session_state.subscription_comparison_xp_awarded = True

    st.markdown("### Pilih Paket Terbaik untuk Anda")

    # --- Plan cards side by side ---
    col_free, col_premium, col_vip = st.columns(3)

    plans_info = [
        {
            "key": "free",
            "name": "Free",
            "price_label": "Gratis",
            "price_sub": "Selamanya",
            "col": col_free,
            "popular": False,
            "features": [
                ("yes", "Chat AI 5x/hari"),
                ("limited", "Hotel Compare 3 hasil"),
                ("limited", "Cost Tracker Basic"),
                ("limited", "Manasik 3D Demo"),
                ("no", "CRM"),
                ("limited", "Support Community"),
            ],
        },
        {
            "key": "premium",
            "name": "Premium",
            "price_label": "Rp 99.000",
            "price_sub": "/bulan",
            "col": col_premium,
            "popular": True,
            "features": [
                ("yes", "Chat AI Unlimited"),
                ("yes", "Hotel Compare Semua"),
                ("yes", "Cost Tracker Full+CSV"),
                ("yes", "Manasik 3D Full"),
                ("limited", "CRM Basic"),
                ("yes", "Support Email"),
            ],
        },
        {
            "key": "vip",
            "name": "VIP",
            "price_label": "Rp 199.000",
            "price_sub": "/bulan",
            "col": col_vip,
            "popular": False,
            "features": [
                ("yes", "Chat AI Unlimited+Priority"),
                ("yes", "Hotel Compare Semua+Alert"),
                ("yes", "Cost Tracker Full+CSV+AI"),
                ("yes", "Manasik 3D Full+Audio"),
                ("yes", "CRM Full"),
                ("yes", "Support WhatsApp+Priority"),
            ],
        },
    ]

    for plan in plans_info:
        with plan["col"]:
            is_current = plan["key"] == current_key
            card_class = "plan-card"
            if is_current:
                card_class += " current"
            elif plan["popular"]:
                card_class += " popular"

            badge_html = ""
            if is_current:
                badge_html = '<div class="plan-badge current-badge">PAKET ANDA</div>'
            elif plan["popular"]:
                badge_html = '<div class="plan-badge">POPULER</div>'

            price_class = "plan-price free-price" if plan["key"] == "free" else "plan-price"

            features_html = ""
            for icon_type, text in plan["features"]:
                if icon_type == "yes":
                    icon_html = '<span class="feat-icon yes" aria-hidden="true">&#10003;</span>'
                elif icon_type == "no":
                    icon_html = '<span class="feat-icon no" aria-hidden="true">&#10007;</span>'
                else:
                    icon_html = '<span class="feat-icon limited" aria-hidden="true">~</span>'
                features_html += f'<div class="plan-feature-item">{icon_html}<span>{text}</span></div>'

            st.markdown(f"""
                <div class="{card_class}">
                    {badge_html}
                    <div class="plan-name">{plan["name"]}</div>
                    <div class="{price_class}">
                        {plan["price_label"]}
                        <span class="period">{plan["price_sub"]}</span>
                    </div>
                    <div class="plan-features">
                        {features_html}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if is_current:
                st.button(
                    "Paket Saat Ini",
                    key=f"comp_current_{plan['key']}",
                    use_container_width=True,
                    disabled=True,
                )
            elif plan["key"] == "free":
                # No CTA for free when user is on a higher plan
                if current_key != "free":
                    if st.button("Downgrade", key="comp_downgrade_free", use_container_width=True):
                        st.session_state.sub_manage_action = "cancel"
                        st.rerun()
                else:
                    st.button(
                        "Paket Saat Ini",
                        key="comp_current_free_btn",
                        use_container_width=True,
                        disabled=True,
                    )
            else:
                btn_type = "primary" if plan["popular"] else "secondary"
                if st.button(
                    f"Pilih {plan['name']}",
                    key=f"comp_select_{plan['key']}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    st.session_state.upgrade_target_plan = plan["key"]
                    st.session_state.upgrade_step = 1
                    st.session_state.sub_manage_action = "upgrade"
                    st.rerun()

    # --- Detailed comparison table ---
    st.markdown("")
    with st.expander("Lihat perbandingan fitur lengkap", expanded=False):
        comparison_rows = [
            ("Chat AI", "5x/hari", "Unlimited", "Unlimited+Priority"),
            ("Hotel Compare", "3 hasil", "Semua", "Semua+Alert"),
            ("Cost Tracker", "Basic", "Full+CSV", "Full+CSV+AI"),
            ("Manasik 3D", "Demo", "Full", "Full+Audio"),
            ("CRM", '<span class="check-no" aria-hidden="true">&#10007;</span>', "Basic", "Full"),
            ("Support", "Community", "Email", "WhatsApp+Priority"),
            ("Itinerary AI", '<span class="check-no" aria-hidden="true">&#10007;</span>', '<span class="check-yes" aria-hidden="true">&#10003;</span>', '<span class="check-yes" aria-hidden="true">&#10003;</span>'),
            ("Notifikasi Harga", '<span class="check-no" aria-hidden="true">&#10007;</span>', '<span class="check-yes" aria-hidden="true">&#10003;</span>', '<span class="check-yes" aria-hidden="true">&#10003;</span>'),
            ("Download PDF", '<span class="check-no" aria-hidden="true">&#10007;</span>', '<span class="check-yes" aria-hidden="true">&#10003;</span>', '<span class="check-yes" aria-hidden="true">&#10003;</span>'),
            ("Early Access", '<span class="check-no" aria-hidden="true">&#10007;</span>', '<span class="check-no" aria-hidden="true">&#10007;</span>', '<span class="check-yes" aria-hidden="true">&#10003;</span>'),
        ]

        rows_html = ""
        for feature, free_val, prem_val, vip_val in comparison_rows:
            rows_html += f"""
                <tr>
                    <td class="feature-name">{feature}</td>
                    <td><span class="check-text">{free_val}</span></td>
                    <td><span class="check-text">{prem_val}</span></td>
                    <td><span class="check-text">{vip_val}</span></td>
                </tr>
            """

        st.markdown(f"""
            <div style="overflow-x: auto;">
            <table class="comparison-table" role="table" aria-label="Perbandingan fitur paket">
                <thead>
                    <tr>
                        <th>Fitur</th>
                        <th>Free</th>
                        <th>Premium</th>
                        <th>VIP</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            </div>
        """, unsafe_allow_html=True)


# =============================================================================
# BILLING HISTORY
# =============================================================================

def render_billing_history():
    """Show billing history from session state or demo data."""
    st.markdown("### Riwayat Pembayaran")

    billing_history = st.session_state.get("billing_history", None)
    if not billing_history:
        billing_history = _get_demo_billing_history()
        st.info("Menampilkan data demo. Riwayat pembayaran asli akan muncul setelah transaksi pertama.")

    if not billing_history:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-icon" aria-hidden="true">&#128203;</div>
                <div class="empty-text">Belum ada riwayat pembayaran</div>
            </div>
        """, unsafe_allow_html=True)
        return

    # Build the billing table
    rows_html = ""
    for entry in billing_history:
        status_class = "billing-status-paid" if entry["status"] == "paid" else "billing-status-pending"
        status_label = "Lunas" if entry["status"] == "paid" else "Pending"
        rows_html += f"""
            <tr>
                <td>{entry['tanggal']}</td>
                <td>{entry['paket']}</td>
                <td>{format_price(entry['jumlah'])}</td>
                <td><span class="{status_class}">{status_label}</span></td>
                <td>{entry['invoice']}</td>
            </tr>
        """

    st.markdown(f"""
        <div style="overflow-x: auto;">
        <table class="billing-table" role="table" aria-label="Riwayat pembayaran">
            <thead>
                <tr>
                    <th>Tanggal</th>
                    <th>Paket</th>
                    <th>Jumlah</th>
                    <th>Status</th>
                    <th>Invoice</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        </div>
    """, unsafe_allow_html=True)

    # Download invoice buttons
    st.markdown("")
    st.markdown("**Download Invoice:**")
    inv_cols = st.columns(min(len(billing_history), 3))
    for i, entry in enumerate(billing_history):
        col_idx = i % len(inv_cols)
        with inv_cols[col_idx]:
            invoice_text = _generate_invoice_text(entry)
            st.download_button(
                label=f"{entry['invoice']}",
                data=invoice_text,
                file_name=f"{entry['invoice']}.txt",
                mime="text/plain",
                key=f"dl_invoice_{i}",
                use_container_width=True,
            )


# =============================================================================
# UPGRADE FLOW
# =============================================================================

def render_upgrade_flow(current_sub=None):
    """Multi-step upgrade flow: select plan, review, contact."""
    st.markdown("### Upgrade Paket")

    upgrade_step = st.session_state.get("upgrade_step", 1)
    target_plan = st.session_state.get("upgrade_target_plan", None)

    plan_details = {
        "premium": {
            "name": "Premium",
            "price": "Rp 99.000/bulan",
            "price_int": 99000,
            "new_features": [
                "Chat AI Unlimited (dari 5x/hari)",
                "Hotel Compare semua hasil",
                "Cost Tracker Full + Export CSV",
                "Manasik 3D Full access",
                "CRM Basic",
                "Email Support",
            ],
        },
        "vip": {
            "name": "VIP",
            "price": "Rp 199.000/bulan",
            "price_int": 199000,
            "new_features": [
                "Chat AI Unlimited + Priority Response",
                "Hotel Compare semua + Price Alert",
                "Cost Tracker Full + CSV + AI Insights",
                "Manasik 3D Full + Audio Guide",
                "CRM Full access",
                "WhatsApp Support + Priority",
                "Early Access fitur baru",
            ],
        },
    }

    # Step indicators
    steps = [
        (1, "Pilih Paket"),
        (2, "Review"),
        (3, "Konfirmasi"),
    ]
    steps_html = ""
    for num, label in steps:
        if num < upgrade_step:
            cls = "done"
        elif num == upgrade_step:
            cls = "active"
        else:
            cls = ""
        steps_html += f'<span class="step-number {cls}">{num}</span> {label}  &nbsp;&nbsp;'

    st.markdown(f"<div style='margin-bottom: 1.5rem; color: #b0b0b0;'>{steps_html}</div>", unsafe_allow_html=True)

    # --- Step 1: Select Plan ---
    if upgrade_step == 1:
        st.markdown("""
            <div class="upgrade-step active">
                <p style="color: #b0b0b0; margin: 0;">Pilih paket yang ingin Anda gunakan:</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
                <div class="dark-card" style="text-align: center;">
                    <h3 style="color: #d4af37; margin: 0;">Premium</h3>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #d4af37; margin: 0.5rem 0;">
                        Rp 99.000<span style="font-size: 0.8rem; color: #b0b0b0;">/bulan</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Pilih Premium", key="upgrade_select_premium", use_container_width=True, type="primary"):
                st.session_state.upgrade_target_plan = "premium"
                st.session_state.upgrade_step = 2
                st.rerun()

        with col2:
            st.markdown("""
                <div class="dark-card" style="text-align: center;">
                    <h3 style="color: #d4af37; margin: 0;">VIP</h3>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #d4af37; margin: 0.5rem 0;">
                        Rp 199.000<span style="font-size: 0.8rem; color: #b0b0b0;">/bulan</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Pilih VIP", key="upgrade_select_vip", use_container_width=True):
                st.session_state.upgrade_target_plan = "vip"
                st.session_state.upgrade_step = 2
                st.rerun()

    # --- Step 2: Review Changes ---
    elif upgrade_step == 2 and target_plan and target_plan in plan_details:
        details = plan_details[target_plan]
        current_plan_label = "Free"
        current_price = 0
        if current_sub and current_sub.is_active:
            current_plan_label = current_sub.plan.display_name
            current_price = current_sub.amount_paid

        price_diff = details["price_int"] - current_price

        st.markdown(f"""
            <div class="upgrade-step active">
                <h4 style="color: #d4af37; margin-top: 0;">Review Perubahan</h4>
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <div style="color: #b0b0b0; font-size: 0.82rem;">Paket Saat Ini</div>
                        <div style="color: #fff; font-size: 1.1rem; font-weight: 600;">{current_plan_label}</div>
                        <div style="color: #b0b0b0;">{format_price(current_price)}/bulan</div>
                    </div>
                    <div style="color: #d4af37; font-size: 1.5rem; align-self: center;" aria-hidden="true">&#10132;</div>
                    <div>
                        <div style="color: #b0b0b0; font-size: 0.82rem;">Paket Baru</div>
                        <div style="color: #4ade80; font-size: 1.1rem; font-weight: 600;">{details['name']}</div>
                        <div style="color: #b0b0b0;">{details['price']}</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid #333;">
                    <div style="color: #b0b0b0; font-size: 0.82rem;">Selisih Harga</div>
                    <div style="color: #d4af37; font-size: 1.1rem; font-weight: 600;">+{format_price(price_diff)}/bulan</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("**Fitur baru yang Anda dapatkan:**")
        for feat in details["new_features"]:
            st.markdown(f"- {feat}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Lanjutkan", key="upgrade_to_step3", use_container_width=True, type="primary"):
                st.session_state.upgrade_step = 3
                st.rerun()
        with col2:
            if st.button("Kembali", key="upgrade_back_to_1", use_container_width=True):
                st.session_state.upgrade_step = 1
                st.session_state.upgrade_target_plan = None
                st.rerun()

    # --- Step 3: Contact CTA ---
    elif upgrade_step == 3 and target_plan and target_plan in plan_details:
        details = plan_details[target_plan]

        st.markdown(f"""
            <div class="upgrade-step active" style="text-align: center;">
                <h4 style="color: #4ade80; margin-top: 0;">Hubungi Kami untuk Upgrade ke {details['name']}</h4>
                <p style="color: #b0b0b0; margin-bottom: 1rem;">
                    Pembayaran diproses manual oleh tim kami untuk memastikan keamanan transaksi.
                </p>
                <p style="color: #b0b0b0; font-size: 0.85rem;">
                    Klik tombol di bawah untuk menghubungi admin via WhatsApp.
                    Tim kami akan membantu proses upgrade dalam waktu 1x24 jam.
                </p>
            </div>
        """, unsafe_allow_html=True)

        wa_message = f"Halo admin LABBAIK, saya ingin upgrade ke paket {details['name']} ({details['price']}). Mohon bantuannya."
        admin_wa = _get_admin_whatsapp()
        wa_url = f"https://wa.me/{admin_wa}?text={wa_message.replace(' ', '%20')}"

        st.link_button(
            f"Hubungi Admin via WhatsApp - Upgrade {details['name']}",
            url=wa_url,
            use_container_width=True,
            type="primary",
        )

        st.markdown("")
        st.info("Pembayaran diproses manual oleh tim kami. Anda akan menerima konfirmasi setelah pembayaran diverifikasi.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Kembali ke Review", key="upgrade_back_to_2", use_container_width=True):
                st.session_state.upgrade_step = 2
                st.rerun()
        with col2:
            if st.button("Selesai", key="upgrade_done", use_container_width=True):
                st.session_state.upgrade_step = 1
                st.session_state.upgrade_target_plan = None
                st.session_state.sub_manage_action = None
                st.rerun()

    else:
        # Fallback: reset to step 1
        st.session_state.upgrade_step = 1
        st.session_state.upgrade_target_plan = None
        st.rerun()


# =============================================================================
# CANCEL / DOWNGRADE FLOW
# =============================================================================

def render_cancel_flow(current_sub=None):
    """Cancellation / downgrade flow with retention offer."""
    cancel_step = st.session_state.get("cancel_step", 1)

    # --- Step 1: Retention offer ---
    if cancel_step == 1:
        st.markdown("""
            <div class="cancel-warning">
                <h3><span aria-hidden="true">&#128546; </span>Kami akan merindukan Anda!</h3>
                <p style="color: #ccc;">
                    Sebelum Anda pergi, kami ingin memastikan Anda mendapatkan pengalaman terbaik.
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="retention-offer">
                <h3><span aria-hidden="true">&#127873; </span>Penawaran Spesial untuk Anda</h3>
                <p style="color: #ccc; font-size: 1.1rem;">
                    Dapatkan <strong style="color: #FFD700;">diskon 30%</strong> untuk 3 bulan ke depan!
                </p>
                <p style="color: #b0b0b0; font-size: 0.85rem;">
                    Gunakan kode <strong style="color: #d4af37;">STAYWITHLABBAIK</strong> saat perpanjang.
                </p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Terima Diskon & Tetap", key="cancel_accept_offer", use_container_width=True, type="primary"):
                st.session_state.cancel_step = 1
                st.session_state.sub_manage_action = None
                st.success("Terima kasih! Gunakan kode STAYWITHLABBAIK saat perpanjang.")
                st.rerun()
        with col2:
            if st.button("Tetap Ingin Berhenti", key="cancel_continue", use_container_width=True):
                st.session_state.cancel_step = 2
                st.rerun()

    # --- Step 2: Reason selection ---
    elif cancel_step == 2:
        st.markdown("### Alasan Pembatalan")
        st.markdown('<p style="color: #b0b0b0;">Bantu kami memahami alasan Anda agar kami bisa meningkatkan layanan.</p>', unsafe_allow_html=True)

        reasons = [
            "Terlalu mahal",
            "Tidak membutuhkan fitur Premium",
            "Pindah ke layanan lain",
            "Perjalanan umrah sudah selesai",
            "Lainnya",
        ]

        cancel_reason = st.radio(
            "Pilih alasan:",
            reasons,
            key="cancel_reason_radio",
            index=None,
        )

        if cancel_reason == "Lainnya":
            st.text_area(
                "Ceritakan alasan Anda (opsional):",
                key="cancel_reason_text",
                placeholder="Tuliskan alasan Anda di sini...",
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Lanjut", key="cancel_to_step3", use_container_width=True, type="primary", disabled=cancel_reason is None):
                st.session_state.cancel_step = 3
                st.session_state.cancel_reason = cancel_reason
                st.rerun()
        with col2:
            if st.button("Kembali", key="cancel_back_to_1", use_container_width=True):
                st.session_state.cancel_step = 1
                st.rerun()

    # --- Step 3: Confirmation - show what they'll lose ---
    elif cancel_step == 3:
        st.markdown("### Konfirmasi Pembatalan")

        lost_features = [
            "Chat AI Unlimited",
            "Hotel Compare semua hasil",
            "Cost Tracker Full + Export CSV",
            "Manasik 3D Full access",
            "CRM access",
            "Email / WhatsApp Support prioritas",
            "Notifikasi harga turun",
            "Download laporan PDF",
        ]

        features_html = ""
        for feat in lost_features:
            features_html += f'<div class="feature-loss-item"><span class="loss-icon" aria-hidden="true">&#10007;</span>{feat}</div>'

        st.markdown(f"""
            <div class="cancel-warning">
                <h3>Fitur yang akan hilang:</h3>
                {features_html}
                <p style="color: #b0b0b0; margin-top: 1rem; font-size: 0.85rem;">
                    Akun Anda akan kembali ke paket Free. Data Anda tetap tersimpan.
                </p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Downgrade ke Free", key="cancel_confirm", use_container_width=True, type="primary"):
                # Perform cancellation
                if current_sub and current_sub.id:
                    service = get_subscription_service()
                    service.cancel_subscription(current_sub.id)

                st.session_state.cancel_step = 4
                st.rerun()

        with col2:
            if st.button("Batal, Tetap Premium", key="cancel_abort", use_container_width=True):
                st.session_state.cancel_step = 1
                st.session_state.sub_manage_action = None
                st.rerun()

    # --- Step 4: Post-cancel confirmation ---
    elif cancel_step == 4:
        st.success("Paket Anda telah di-downgrade ke Free.")
        st.markdown("""
            <div class="dark-card" style="text-align: center;">
                <h4 style="color: #b0b0b0; margin-top: 0;">Akun dikembalikan ke paket Free</h4>
                <p style="color: #b0b0b0; font-size: 0.88rem;">
                    Data Anda tetap tersimpan. Anda bisa upgrade kembali kapan saja.
                </p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Kembali ke Beranda", key="cancel_go_home", use_container_width=True):
            st.session_state.cancel_step = 1
            st.session_state.sub_manage_action = None
            st.session_state.current_page = "home"
            st.rerun()


# =============================================================================
# MANAGE TAB (wires upgrade + cancel together)
# =============================================================================

def render_manage_tab(user, current_sub):
    """Manage subscription tab - upgrade or cancel."""
    action = st.session_state.get("sub_manage_action", None)

    if action == "upgrade":
        render_upgrade_flow(current_sub)
    elif action == "cancel":
        render_cancel_flow(current_sub)
    else:
        # Default manage view
        st.markdown("### Kelola Langganan")

        if current_sub and current_sub.is_active:
            render_current_subscription(current_sub)
            st.markdown("")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Upgrade Paket", key="manage_upgrade_btn", use_container_width=True, type="primary"):
                    st.session_state.sub_manage_action = "upgrade"
                    st.session_state.upgrade_step = 1
                    st.rerun()
            with col2:
                if st.button("Batalkan Langganan", key="manage_cancel_btn", use_container_width=True):
                    st.session_state.sub_manage_action = "cancel"
                    st.session_state.cancel_step = 1
                    st.rerun()
        else:
            st.markdown("""
                <div class="dark-card" style="text-align: center;">
                    <h4 style="color: #b0b0b0; margin-top: 0;">Anda menggunakan paket Free</h4>
                    <p style="color: #b0b0b0; font-size: 0.88rem;">
                        Upgrade untuk mendapatkan akses penuh ke semua fitur LABBAIK AI.
                    </p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Upgrade Sekarang", key="manage_upgrade_free_btn", use_container_width=True, type="primary"):
                st.session_state.sub_manage_action = "upgrade"
                st.session_state.upgrade_step = 1
                st.rerun()


# =============================================================================
# EXISTING FUNCTIONS (preserved from original)
# =============================================================================

def render_subscription_page():
    """Main subscription page with tabs."""
    try:
        from services.analytics import track_page
        track_page("subscription")
    except Exception:
        pass
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS, BADGE_CSS, SUBSCRIPTION_CSS)

    if not st.session_state.get("subscription_view_xp_awarded"):
        add_xp_safe(5, "Melihat paket Premium")
        st.session_state.subscription_view_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1><span aria-hidden="true">&#11088; </span>Langganan LABBAIK AI</h1>
            <div class="subtitle">Kelola paket Anda dan akses penuh fitur untuk perjalanan umrah terbaik</div>
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

    # --- Tabs ---
    tab_paket, tab_comparison, tab_history, tab_manage = st.tabs([
        "Paket Saya",
        "Perbandingan",
        "Riwayat",
        "Kelola",
    ])

    with tab_paket:
        _render_paket_saya_tab(user, current_sub)

    with tab_comparison:
        render_plan_comparison(current_sub)

    with tab_history:
        render_billing_history()

    with tab_manage:
        render_manage_tab(user, current_sub)


def _render_paket_saya_tab(user, current_sub):
    """Content for the 'Paket Saya' tab - preserves original subscription display."""
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
    st.success("### Status Premium Anda: Aktif")

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

    with st.spinner("Memproses..."):
        recommendation = ai_complete(
            "Berikan rekomendasi singkat (3-4 kalimat) mengapa jamaah umrah sebaiknya menggunakan "
            "fitur Premium untuk perencanaan umrah mereka. Bahasa Indonesia, persuasif tapi jujur.",
            system_prompt="Kamu adalah advisor perjalanan umrah yang berpengalaman.",
            max_tokens=200,
        )
    if recommendation:
        st.markdown(f"""
            <div class="ai-card" role="status" aria-live="polite">
                <h4><span aria-hidden="true">&#129302;</span> Rekomendasi AI</h4>
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
                    <div style="color: #b0b0b0; font-size: 0.85rem;">
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
        ("Bagaimana cara downgrade?", "Buka tab 'Kelola', pilih 'Batalkan Langganan', dan konfirmasi downgrade ke paket Free."),
        ("Apa perbedaan Premium dan VIP?", "VIP mendapatkan semua fitur Premium plus priority support via WhatsApp, AI insights di Cost Tracker, Audio Guide untuk Manasik 3D, dan akses CRM penuh."),
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


__all__ = ["render_subscription_page", "render_subscription_widget"]
