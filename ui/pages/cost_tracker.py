"""
================================================================================
LABBAIK AI - UMRAH COST TRACKER
================================================================================
Lokasi: ui/pages/cost_tracker.py
Fitur: Pencatatan dan pelacakan pengeluaran selama umrah
       - Budget setup per kategori
       - Pencatatan pengeluaran harian
       - Dashboard visual dengan progress bars
       - AI savings insights
       - Export ke format teks
================================================================================
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, List
import uuid
import csv
import io

from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS, PROGRESS_CSS, EMPTY_STATE_CSS
from ui.components import format_idr_short as format_idr, format_idr as format_idr_full

try:
    from ui.pages.kurs_calculator import get_current_rates
    HAS_KURS_SERVICE = True
except ImportError:
    HAS_KURS_SERVICE = False

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# =============================================================================
# CONSTANTS & CATEGORIES
# =============================================================================

EXPENSE_CATEGORIES = {
    "penerbangan": {"icon": "\u2708\ufe0f", "label": "Penerbangan", "color": "#60a5fa"},
    "hotel": {"icon": "\U0001f3e8", "label": "Hotel", "color": "#f472b6"},
    "transportasi": {"icon": "\U0001f696", "label": "Transportasi Lokal", "color": "#fbbf24"},
    "makan": {"icon": "\U0001f37d\ufe0f", "label": "Makan & Minum", "color": "#4ade80"},
    "belanja": {"icon": "\U0001f6cd\ufe0f", "label": "Belanja & Oleh-oleh", "color": "#a78bfa"},
    "lainnya": {"icon": "\U0001f4e6", "label": "Lainnya", "color": "#94a3b8"},
}

DEFAULT_BUDGETS = {
    "penerbangan": 10_000_000,
    "hotel": 8_000_000,
    "transportasi": 2_000_000,
    "makan": 3_000_000,
    "belanja": 3_000_000,
    "lainnya": 2_000_000,
}

# =============================================================================
# STYLING
# =============================================================================

TRACKER_CSS = """
/* Page-specific overrides for cost tracker */
.tracker-hero h1 {
    font-family: 'Amiri', serif;
}

.category-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    border-left: 4px solid #334155;
    transition: transform 0.15s;
}

.category-card:hover {
    transform: translateX(2px);
}

.category-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
}

.category-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.category-amounts {
    text-align: right;
    font-size: 0.85rem;
}

.category-spent {
    font-weight: 700;
    color: #e2e8f0;
}

.category-budget {
    color: #64748b;
    font-size: 0.78rem;
}

.progress-pct {
    color: #64748b;
    font-size: 0.75rem;
    margin-top: 0.25rem;
    text-align: right;
}

.expense-row {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #1e293b;
    transition: border-color 0.2s;
}

.expense-row:hover {
    border-color: #334155;
}

.expense-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.expense-icon {
    font-size: 1.5rem;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: rgba(212, 175, 55, 0.1);
}

.expense-info {
    display: flex;
    flex-direction: column;
}

.expense-notes {
    color: #e2e8f0;
    font-weight: 500;
    font-size: 0.95rem;
}

.expense-meta {
    color: #64748b;
    font-size: 0.78rem;
    margin-top: 0.15rem;
}

.expense-amount {
    font-weight: 700;
    font-size: 1.05rem;
    color: #f87171;
}

.insight-card {
    background: linear-gradient(135deg, #0d2818 0%, #1a4d2e 100%);
    border: 1px solid #22c55e;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    color: #e2e8f0;
    line-height: 1.7;
}

.insight-card h3 {
    color: #4ade80;
    margin-top: 0;
    margin-bottom: 0.75rem;
}

.budget-setup-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid #334155;
}

.remaining-positive {
    color: #4ade80;
}

.remaining-negative {
    color: #f87171;
}

/* --- Savings Tracker Section --- */
.savings-tracker-section {
    margin: 1.5rem 0;
}

.savings-table-header {
    display: grid;
    grid-template-columns: 2fr 1.5fr 1.5fr 1.5fr;
    padding: 0.75rem 1.25rem;
    background: rgba(212, 175, 55, 0.08);
    border-radius: 12px 12px 0 0;
    border: 1px solid #334155;
    border-bottom: none;
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.savings-row {
    display: grid;
    grid-template-columns: 2fr 1.5fr 1.5fr 1.5fr;
    padding: 0.85rem 1.25rem;
    border: 1px solid #1e293b;
    border-bottom: none;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    align-items: center;
    transition: background 0.15s;
}

.savings-row:hover {
    background: linear-gradient(145deg, #1e1e34 0%, #222c3d 100%);
}

.savings-row:last-of-type {
    border-bottom: 1px solid #1e293b;
    border-radius: 0 0 12px 12px;
}

.savings-row.total-row {
    background: linear-gradient(145deg, #0f172a 0%, #1a2332 100%);
    border-top: 2px solid #334155;
    border-bottom: 1px solid #334155;
    border-radius: 0 0 12px 12px;
    font-weight: 700;
    padding: 1rem 1.25rem;
}

.savings-cat {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: #e2e8f0;
}

.savings-cat .cat-icon {
    font-size: 1.15rem;
}

.savings-amount {
    text-align: right;
    font-size: 0.9rem;
    color: #e2e8f0;
}

.savings-positive {
    color: #4ade80;
    font-weight: 600;
}

.savings-negative {
    color: #f87171;
    font-weight: 600;
}

.savings-pct-badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}

.savings-pct-badge.positive {
    background: rgba(74, 222, 128, 0.12);
    color: #4ade80;
}

.savings-pct-badge.negative {
    background: rgba(248, 113, 113, 0.12);
    color: #f87171;
}

.overall-savings-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-top: 1rem;
    padding: 1rem 1.5rem;
    border-radius: 14px;
    font-size: 1rem;
    font-weight: 600;
}

.overall-savings-banner.positive {
    background: linear-gradient(135deg, #0d2818 0%, #1a4d2e 100%);
    border: 1px solid #22c55e;
    color: #4ade80;
}

.overall-savings-banner.negative {
    background: linear-gradient(135deg, #2d0a0a 0%, #4d1a1a 100%);
    border: 1px solid #f87171;
    color: #f87171;
}

.overall-savings-banner .big-number {
    font-size: 1.6rem;
    font-weight: 800;
}

/* --- Budget Alert Banners --- */
.budget-alert {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 2.5rem 1rem 1.25rem;
    border-radius: 12px;
    margin-bottom: 0.75rem;
    font-size: 0.9rem;
    font-weight: 500;
    line-height: 1.4;
    animation: slideInAlert 0.3s ease-out;
}

@keyframes slideInAlert {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
    .budget-alert { animation: none; }
}

.budget-alert .alert-icon {
    font-size: 1.3rem;
    flex-shrink: 0;
}

.budget-alert .alert-text {
    flex: 1;
}

.budget-alert .alert-close {
    position: absolute;
    top: 0.5rem;
    right: 0.75rem;
    background: none;
    border: none;
    color: inherit;
    opacity: 0.6;
    cursor: pointer;
    font-size: 1.1rem;
    padding: 0.25rem;
    line-height: 1;
    min-height: 44px;
    min-width: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.budget-alert .alert-close:hover {
    opacity: 1;
}

.budget-alert .alert-close:focus-visible {
    outline: 2px solid #d4af37;
    outline-offset: 2px;
    border-radius: 4px;
}

.budget-alert.alert-warning {
    background: linear-gradient(135deg, #2d1f0a 0%, #3d2b0f 100%);
    border: 1px solid #f59e0b;
    border-left: 4px solid #f59e0b;
    color: #fbbf24;
}

.budget-alert.alert-danger {
    background: linear-gradient(135deg, #2d0a0a 0%, #4d1a1a 100%);
    border: 1px solid #ef4444;
    border-left: 4px solid #ef4444;
    color: #f87171;
}

/* --- Expense Chart Section --- */
.expense-chart-section {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.expense-chart-section h4 {
    color: #e2e8f0;
    margin-top: 0;
    margin-bottom: 1rem;
    font-size: 1rem;
}

.donut-chart {
    width: 200px;
    height: 200px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem auto;
    position: relative;
}

.donut-chart::after {
    content: '';
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: #1a1a2e;
    position: absolute;
}

.donut-center-label {
    position: absolute;
    z-index: 2;
    text-align: center;
    color: #e2e8f0;
    font-size: 0.85rem;
    font-weight: 600;
    line-height: 1.3;
}

.chart-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    justify-content: center;
    margin-top: 0.75rem;
}

.chart-legend-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.8rem;
    color: #b0b0b0;
}

.chart-legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

.daily-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}

.daily-bar-label {
    color: #b0b0b0;
    font-size: 0.78rem;
    min-width: 70px;
    text-align: right;
    flex-shrink: 0;
}

.daily-bar-track {
    flex: 1;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    height: 22px;
    position: relative;
    overflow: hidden;
}

.daily-bar-fill {
    height: 100%;
    border-radius: 6px;
    background: linear-gradient(90deg, #d4af37 0%, #f5d76e 100%);
    transition: width 0.3s ease;
    min-width: 2px;
}

.daily-bar-amount {
    color: #e2e8f0;
    font-size: 0.78rem;
    min-width: 80px;
    font-weight: 500;
}

.budget-vs-actual-row {
    margin-bottom: 0.75rem;
}

.budget-vs-actual-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.3rem;
}

.budget-vs-actual-label span {
    font-size: 0.82rem;
    color: #b0b0b0;
}

.budget-vs-actual-bars {
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.bva-bar-track {
    height: 14px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.bva-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
    min-width: 2px;
}

.bva-bar-fill.budget-bar {
    background: #d4af37;
}

.bva-bar-fill.actual-under {
    background: #4ade80;
}

.bva-bar-fill.actual-over {
    background: #f87171;
}

.bva-legend {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 0.75rem;
    font-size: 0.78rem;
    color: #b0b0b0;
}

.bva-legend span {
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.bva-legend-swatch {
    width: 12px;
    height: 8px;
    border-radius: 2px;
    display: inline-block;
}

@media (max-width: 480px) {
    .donut-chart {
        width: 160px;
        height: 160px;
    }
    .donut-chart::after {
        width: 96px;
        height: 96px;
    }
    .daily-bar-label {
        min-width: 55px;
        font-size: 0.72rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    .daily-bar-fill, .bva-bar-fill {
        transition: none;
    }
}
"""

# =============================================================================
# SESSION STATE
# =============================================================================

def init_cost_tracker_state():
    """Initialize cost tracker session state."""
    defaults = {
        "tracker_budget": {},
        "tracker_expenses": [],
        "tracker_budget_set": False,
        "tracker_currency": "IDR",
        "dismissed_budget_alerts": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# HELPERS
# =============================================================================

def get_total_budget():
    """Get total budget across all categories."""
    return sum(st.session_state.tracker_budget.values())


def get_total_spent():
    """Get total spent across all expenses."""
    return sum(e["amount"] for e in st.session_state.tracker_expenses)


def get_spent_by_category(category: str) -> int:
    """Get total spent for a specific category."""
    return sum(
        e["amount"]
        for e in st.session_state.tracker_expenses
        if e["category"] == category
    )


def get_daily_average() -> float:
    """Calculate daily average spending."""
    expenses = st.session_state.tracker_expenses
    if not expenses:
        return 0.0

    dates = set(e["date"] for e in expenses)
    if not dates:
        return 0.0

    total = get_total_spent()
    return total / len(dates)


def add_xp(amount: int, reason: str = ""):
    """Add XP — delegates to shared helper."""
    add_xp_safe(amount, reason)


def export_to_text() -> str:
    """Export budget and expenses to text format."""
    budget = st.session_state.tracker_budget
    expenses = st.session_state.tracker_expenses
    total_budget = get_total_budget()
    total_spent = get_total_spent()
    remaining = total_budget - total_spent

    lines = []
    lines.append("=" * 50)
    lines.append("LABBAIK AI - COST TRACKER UMRAH")
    lines.append("=" * 50)
    lines.append("")

    lines.append("--- RINGKASAN BUDGET ---")
    lines.append(f"Total Budget   : {format_idr_full(total_budget)}")
    lines.append(f"Total Terpakai : {format_idr_full(total_spent)}")
    lines.append(f"Sisa           : {format_idr_full(remaining)}")
    lines.append("")

    lines.append("--- BUDGET PER KATEGORI ---")
    for cat_id, cat_info in EXPENSE_CATEGORIES.items():
        cat_budget = budget.get(cat_id, 0)
        cat_spent = get_spent_by_category(cat_id)
        pct = (cat_spent / cat_budget * 100) if cat_budget > 0 else 0
        lines.append(
            f"{cat_info['icon']} {cat_info['label']:20s} "
            f"Budget: {format_idr_full(cat_budget):>16s} | "
            f"Terpakai: {format_idr_full(cat_spent):>16s} ({pct:.0f}%)"
        )
    lines.append("")

    if expenses:
        lines.append("--- RIWAYAT PENGELUARAN ---")
        sorted_expenses = sorted(expenses, key=lambda x: x["date"], reverse=True)
        for exp in sorted_expenses:
            cat_info = EXPENSE_CATEGORIES.get(exp["category"], {})
            icon = cat_info.get("icon", "")
            label = cat_info.get("label", exp["category"])
            lines.append(
                f"{exp['date']}  {icon} {label:20s}  "
                f"{format_idr_full(exp['amount']):>16s}  "
                f"{exp.get('notes', '')}"
            )
        lines.append("")

    lines.append("=" * 50)
    lines.append("Generated by LABBAIK AI - app.labbaik.io")
    lines.append("=" * 50)

    return "\n".join(lines)


def export_to_csv() -> str:
    """Export expenses to CSV format."""
    expenses = st.session_state.tracker_expenses
    output = io.StringIO()
    writer = csv.writer(output)

    # Get SAR rate for conversion column
    sar_rate = 4250
    if HAS_KURS_SERVICE:
        try:
            sar_rate = get_current_rates()["SAR_IDR"]
        except Exception:
            pass

    writer.writerow(["Tanggal", "Kategori", "Catatan", "Jumlah (Rp)", "Jumlah (SAR)"])
    sorted_expenses = sorted(expenses, key=lambda x: x["date"], reverse=True)
    for exp in sorted_expenses:
        cat_info = EXPENSE_CATEGORIES.get(exp["category"], {})
        label = cat_info.get("label", exp["category"])
        amount_idr = exp["amount"]
        amount_sar = round(amount_idr / sar_rate, 2)
        writer.writerow([
            exp["date"],
            label,
            exp.get("notes", ""),
            amount_idr,
            amount_sar,
        ])

    return output.getvalue()


# =============================================================================
# UI: HERO
# =============================================================================

def render_hero():
    """Render hero section with branding."""
    inject_css(HERO_CSS, CARD_CSS, PROGRESS_CSS, EMPTY_STATE_CSS, TRACKER_CSS)

    st.markdown("""
    <div class="tracker-hero">
        <h1>\U0001f4b0 Umrah Cost Tracker</h1>
        <p class="subtitle">Pantau pengeluaran umrah Anda secara real-time</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# UI: BUDGET SETUP
# =============================================================================

def render_budget_setup():
    """Render budget setup form with per-category inputs."""
    st.markdown("### \u2699\ufe0f Atur Budget Umrah Anda")
    st.caption(
        "Tentukan anggaran untuk setiap kategori pengeluaran. "
        "Anda bisa mengubahnya nanti kapan saja."
    )

    st.markdown('<div class="budget-setup-card">', unsafe_allow_html=True)

    budget_values = {}
    cols = st.columns(2)

    for idx, (cat_id, cat_info) in enumerate(EXPENSE_CATEGORIES.items()):
        with cols[idx % 2]:
            default_val = DEFAULT_BUDGETS.get(cat_id, 1_000_000)
            current_val = st.session_state.tracker_budget.get(cat_id, default_val)
            budget_values[cat_id] = st.number_input(
                f"{cat_info['icon']} {cat_info['label']}",
                min_value=0,
                max_value=500_000_000,
                value=current_val,
                step=500_000,
                format="%d",
                key=f"budget_input_{cat_id}",
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Total preview
    total = sum(budget_values.values())
    st.markdown(f"**Total Budget: {format_idr_full(total)}**")

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(
            "\U0001f4be Simpan Budget",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.tracker_budget = budget_values
            st.session_state.tracker_budget_set = True
            add_xp(30, "Setup budget umrah")
            st.success("Budget berhasil disimpan!")
            st.rerun()

    with col2:
        if st.button("\U0001f504 Reset Default", use_container_width=True):
            st.session_state.tracker_budget = dict(DEFAULT_BUDGETS)
            st.rerun()


# =============================================================================
# UI: BUDGET ALERTS
# =============================================================================

def render_budget_alerts():
    """Render budget alert banners for categories approaching or exceeding budget.

    - > 80% spent  => orange warning
    - > 100% spent => red danger alert
    Alerts are dismissible via session state tracking.
    """
    budget = st.session_state.tracker_budget
    if not budget:
        return

    dismissed = st.session_state.get("dismissed_budget_alerts", set())
    alerts = []

    for cat_id, cat_info in EXPENSE_CATEGORIES.items():
        cat_budget = budget.get(cat_id, 0)
        if cat_budget <= 0:
            continue

        cat_spent = get_spent_by_category(cat_id)
        pct = cat_spent / cat_budget * 100

        if pct > 100:
            alert_key = f"danger_{cat_id}"
            if alert_key not in dismissed:
                alerts.append({
                    "key": alert_key,
                    "type": "danger",
                    "icon": "\U0001f6a8",
                    "message": (
                        f"Pengeluaran {cat_info['label']} sudah {pct:.0f}% dari budget! "
                        f"Melebihi budget sebesar {format_idr(cat_spent - cat_budget)}."
                    ),
                })
        elif pct > 80:
            alert_key = f"warning_{cat_id}"
            if alert_key not in dismissed:
                alerts.append({
                    "key": alert_key,
                    "type": "warning",
                    "icon": "\u26a0\ufe0f",
                    "message": (
                        f"Pengeluaran {cat_info['label']} sudah {pct:.0f}% dari budget!"
                    ),
                })

    if not alerts:
        return

    for alert in alerts:
        st.markdown(
            f'<div class="budget-alert alert-{alert["type"]}">'
            f'<span class="alert-icon" aria-hidden="true">{alert["icon"]}</span>'
            f'<span class="alert-text">{alert["message"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "\u2715 Dismiss",
            key=f"dismiss_{alert['key']}",
            help="Tutup peringatan ini",
        ):
            dismissed.add(alert["key"])
            st.session_state.dismissed_budget_alerts = dismissed
            st.rerun()


# =============================================================================
# UI: DASHBOARD
# =============================================================================

def render_dashboard():
    """Render main dashboard with metrics and category breakdown."""
    budget = st.session_state.tracker_budget
    total_budget = get_total_budget()
    total_spent = get_total_spent()
    remaining = total_budget - total_spent
    daily_avg = get_daily_average()
    expense_count = len(st.session_state.tracker_expenses)

    # --- Top-level metrics ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Budget</div>
            <div class="metric-value" style="color:#d4af37;">{format_idr(total_budget)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Terpakai</div>
            <div class="metric-value" style="color:#f87171;">{format_idr(total_spent)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        remaining_class = "remaining-positive" if remaining >= 0 else "remaining-negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sisa Budget</div>
            <div class="metric-value {remaining_class}">{format_idr(abs(remaining))}</div>
            <div style="font-size:0.75rem;color:#64748b;">
                {'Tersisa' if remaining >= 0 else 'Melebihi budget!'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Rata-rata / Hari</div>
            <div class="metric-value" style="color:#60a5fa;">{format_idr(daily_avg)}</div>
            <div style="font-size:0.75rem;color:#64748b;">{expense_count} transaksi</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Overall progress bar ---
    overall_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0
    bar_color = "#4ade80" if overall_pct <= 75 else "#fbbf24" if overall_pct <= 100 else "#f87171"

    st.markdown(f"""
    <div style="margin:1.25rem 0 0.5rem 0;">
        <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
            <span style="color:#94a3b8;font-size:0.85rem;">Penggunaan Budget Keseluruhan</span>
            <span style="color:#e2e8f0;font-size:0.85rem;font-weight:600;">{overall_pct:.1f}%</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{min(overall_pct, 100):.1f}%;background:{bar_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- Per-category breakdown ---
    st.markdown("### \U0001f4ca Breakdown per Kategori")

    for cat_id, cat_info in EXPENSE_CATEGORIES.items():
        cat_budget = budget.get(cat_id, 0)
        cat_spent = get_spent_by_category(cat_id)
        cat_remaining = cat_budget - cat_spent
        pct = (cat_spent / cat_budget * 100) if cat_budget > 0 else 0
        bar_col = cat_info["color"]

        if pct > 100:
            bar_col = "#f87171"

        st.markdown(f"""
        <div class="category-card" style="border-left-color:{cat_info['color']};">
            <div class="category-header">
                <div class="category-title">
                    <span>{cat_info['icon']}</span>
                    <span>{cat_info['label']}</span>
                </div>
                <div class="category-amounts">
                    <div class="category-spent">{format_idr(cat_spent)}</div>
                    <div class="category-budget">dari {format_idr(cat_budget)}</div>
                </div>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{min(pct, 100):.1f}%;background:{bar_col};"></div>
            </div>
            <div class="progress-pct">
                {pct:.0f}% &mdash;
                {'Sisa ' + format_idr(cat_remaining) if cat_remaining >= 0 else 'Lebih ' + format_idr(abs(cat_remaining))}
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# UI: SAVINGS TRACKER
# =============================================================================

def render_savings_tracker():
    """Render savings comparison table: Budget vs Spent vs Savings per category."""
    budget = st.session_state.tracker_budget
    total_budget = get_total_budget()
    total_spent = get_total_spent()
    total_savings = total_budget - total_spent

    st.markdown("### \U0001f4ca Savings Tracker")
    st.caption(
        "Perbandingan budget vs pengeluaran aktual per kategori. "
        "Hijau = hemat, Merah = melebihi budget."
    )

    st.markdown('<div class="savings-tracker-section">', unsafe_allow_html=True)

    # Table header
    st.markdown("""
    <div class="savings-table-header">
        <div>Kategori</div>
        <div style="text-align:right;">Budget</div>
        <div style="text-align:right;">Terpakai</div>
        <div style="text-align:right;">Selisih</div>
    </div>
    """, unsafe_allow_html=True)

    # Category rows
    for cat_id, cat_info in EXPENSE_CATEGORIES.items():
        cat_budget = budget.get(cat_id, 0)
        cat_spent = get_spent_by_category(cat_id)
        cat_savings = cat_budget - cat_spent
        is_positive = cat_savings >= 0

        savings_class = "savings-positive" if is_positive else "savings-negative"
        savings_label = format_idr(abs(cat_savings))
        if not is_positive:
            savings_label = f"-{savings_label}"

        # Percentage badge
        if cat_budget > 0:
            pct_saved = (cat_savings / cat_budget) * 100
            pct_class = "positive" if is_positive else "negative"
            if is_positive:
                pct_text = f"Hemat {abs(pct_saved):.0f}%"
            else:
                pct_text = f"Lebih {abs(pct_saved):.0f}%"
            pct_badge = (
                f'<span class="savings-pct-badge {pct_class}">{pct_text}</span>'
            )
        else:
            pct_badge = ""

        st.markdown(f"""
        <div class="savings-row">
            <div class="savings-cat">
                <span class="cat-icon">{cat_info['icon']}</span>
                <span>{cat_info['label']}</span>
            </div>
            <div class="savings-amount">{format_idr(cat_budget)}</div>
            <div class="savings-amount">{format_idr(cat_spent)}</div>
            <div class="savings-amount {savings_class}">
                {savings_label} {pct_badge}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Total row
    is_total_positive = total_savings >= 0
    total_savings_class = "savings-positive" if is_total_positive else "savings-negative"
    total_savings_label = format_idr(abs(total_savings))
    if not is_total_positive:
        total_savings_label = f"-{total_savings_label}"

    st.markdown(f"""
    <div class="savings-row total-row">
        <div class="savings-cat">
            <span class="cat-icon">\U0001f4b0</span>
            <span>TOTAL</span>
        </div>
        <div class="savings-amount">{format_idr(total_budget)}</div>
        <div class="savings-amount">{format_idr(total_spent)}</div>
        <div class="savings-amount {total_savings_class}">{total_savings_label}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Overall savings percentage banner
    if total_budget > 0:
        overall_pct = (total_savings / total_budget) * 100
        banner_class = "positive" if is_total_positive else "negative"

        if is_total_positive:
            banner_icon = "\u2705"
            banner_text = "Total Penghematan"
            pct_display = f"{overall_pct:.1f}%"
        else:
            banner_icon = "\U0001f6a8"
            banner_text = "Budget Terlampaui"
            pct_display = f"{abs(overall_pct):.1f}%"

        st.markdown(f"""
        <div class="overall-savings-banner {banner_class}">
            <span>{banner_icon}</span>
            <span>{banner_text}:</span>
            <span class="big-number">{pct_display}</span>
            <span>({format_idr_full(abs(total_savings))})</span>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# UI: ADD EXPENSE
# =============================================================================

def render_add_expense():
    """Render add expense form."""
    st.markdown("### \u2795 Tambah Pengeluaran")

    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            currency = st.radio(
                "Mata uang",
                ["IDR", "SAR"],
                horizontal=True,
                key="expense_currency",
            )

            if currency == "SAR":
                amount_input = st.number_input(
                    "Jumlah (SAR)",
                    min_value=0.0,
                    max_value=100_000.0,
                    value=0.0,
                    step=5.0,
                    format="%.2f",
                )
            else:
                amount_input = st.number_input(
                    "Jumlah (Rp)",
                    min_value=0,
                    max_value=500_000_000,
                    value=0,
                    step=10_000,
                    format="%d",
                )

            category = st.selectbox(
                "Kategori",
                options=list(EXPENSE_CATEGORIES.keys()),
                format_func=lambda x: (
                    f"{EXPENSE_CATEGORIES[x]['icon']} {EXPENSE_CATEGORIES[x]['label']}"
                ),
            )

        with col2:
            expense_date = st.date_input(
                "Tanggal",
                value=date.today(),
                max_value=date.today(),
            )

            notes = st.text_input(
                "Catatan",
                placeholder="Contoh: Tiket Garuda PP Jakarta-Jeddah",
                max_chars=100,
            )

        submitted = st.form_submit_button(
            "\U0001f4be Simpan Pengeluaran",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if amount_input <= 0:
                st.warning("Jumlah harus lebih dari 0.")
            else:
                # Convert SAR to IDR if needed
                if currency == "SAR":
                    sar_rate = 4250
                    if HAS_KURS_SERVICE:
                        try:
                            sar_rate = get_current_rates()["SAR_IDR"]
                        except Exception:
                            pass
                    amount = int(amount_input * sar_rate)
                    original_sar = amount_input
                else:
                    amount = int(amount_input)
                    original_sar = None

                new_expense = {
                    "id": str(uuid.uuid4()),
                    "date": expense_date.isoformat(),
                    "category": category,
                    "amount": amount,
                    "notes": notes if notes else f"{EXPENSE_CATEGORIES[category]['label']}",
                }
                if original_sar:
                    new_expense["original_sar"] = original_sar
                st.session_state.tracker_expenses.append(new_expense)
                add_xp(10, "Mencatat pengeluaran")
                sar_info = f" (SAR {original_sar:.2f})" if original_sar else ""
                st.success(
                    f"Pengeluaran {format_idr_full(amount)}{sar_info} berhasil dicatat!"
                )
                st.rerun()


# =============================================================================
# UI: EXPENSE LIST
# =============================================================================

def render_expense_list():
    """Render expense history with delete functionality."""
    expenses = st.session_state.tracker_expenses

    st.markdown("### \U0001f4cb Riwayat Pengeluaran")

    if not expenses:
        st.markdown("""
        <div class="empty-state-card" style="background:linear-gradient(145deg,#1a1a2e 0%,#1e293b 100%);border-radius:16px;padding:2.5rem 1.5rem;text-align:center;border:1px solid #334155;margin:1rem 0;">
            <div class="empty-state-icon" style="font-size:3rem;margin-bottom:0.75rem;opacity:0.7;" aria-hidden="true">\U0001f4dd</div>
            <h3 style="color:#e2e8f0;margin:0 0 0.5rem 0;font-size:1.1rem;">Belum ada pengeluaran</h3>
            <p style="color:#8e9fb3;font-size:0.9rem;margin:0;">Tambahkan pengeluaran pertama Anda!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(
            "\u2795 Tambah Pengeluaran Sekarang",
            key="btn_empty_add_expense",
            use_container_width=True,
            type="primary",
        ):
            st.info("Gunakan tab 'Tambah Pengeluaran' untuk mencatat pengeluaran.")
        return

    # Sort by date descending
    sorted_expenses = sorted(expenses, key=lambda x: x["date"], reverse=True)

    # Filter
    filter_cat = st.selectbox(
        "Filter kategori",
        options=["semua"] + list(EXPENSE_CATEGORIES.keys()),
        format_func=lambda x: (
            "Semua Kategori" if x == "semua"
            else f"{EXPENSE_CATEGORIES[x]['icon']} {EXPENSE_CATEGORIES[x]['label']}"
        ),
        key="expense_filter",
    )

    if filter_cat != "semua":
        sorted_expenses = [e for e in sorted_expenses if e["category"] == filter_cat]

    if not sorted_expenses:
        st.info("Tidak ada pengeluaran di kategori ini.")
        return

    # Render each expense
    for exp in sorted_expenses:
        cat_info = EXPENSE_CATEGORIES.get(exp["category"], {})
        icon = cat_info.get("icon", "\U0001f4e6")
        label = cat_info.get("label", exp["category"])
        color = cat_info.get("color", "#94a3b8")

        col1, col2 = st.columns([5, 1])

        with col1:
            st.markdown(f"""
            <div class="expense-row">
                <div class="expense-left">
                    <div class="expense-icon" style="background:rgba({_hex_to_rgb_str(color)}, 0.15);">
                        {icon}
                    </div>
                    <div class="expense-info">
                        <div class="expense-notes">{exp.get('notes', label)}</div>
                        <div class="expense-meta">{label} &bull; {exp['date']}</div>
                    </div>
                </div>
                <div class="expense-amount">-{format_idr(exp['amount'])}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button(
                "\U0001f5d1\ufe0f",
                key=f"del_{exp['id']}",
                help="Hapus pengeluaran ini",
            ):
                st.session_state.tracker_expenses = [
                    e for e in st.session_state.tracker_expenses
                    if e["id"] != exp["id"]
                ]
                st.toast("Pengeluaran dihapus.")
                st.rerun()

    # Summary at bottom
    filtered_total = sum(e["amount"] for e in sorted_expenses)
    st.caption(
        f"Menampilkan {len(sorted_expenses)} transaksi "
        f"&mdash; Total: {format_idr_full(filtered_total)}"
    )


def _hex_to_rgb_str(hex_color: str) -> str:
    """Convert hex color to comma-separated RGB string for CSS rgba()."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"{r},{g},{b}"


# =============================================================================
# UI: EXPENSE CHARTS
# =============================================================================

def _build_daily_breakdown(expenses: List[Dict]) -> List[Dict]:
    """Group expenses by date and return sorted daily totals.

    Returns:
        Sorted list of dicts: [{date, total, categories: {cat: amount}}]
    """
    from collections import defaultdict

    daily: Dict[str, Dict] = {}
    for exp in expenses:
        d = exp["date"]
        if d not in daily:
            daily[d] = {"date": d, "total": 0, "categories": defaultdict(int)}
        daily[d]["total"] += exp["amount"]
        daily[d]["categories"][exp["category"]] += exp["amount"]

    result = sorted(daily.values(), key=lambda x: x["date"])
    # Convert defaultdicts to plain dicts for safety
    for item in result:
        item["categories"] = dict(item["categories"])
    return result


def _build_category_donut_html(category_data: Dict[str, int]) -> str:
    """Build a pure CSS conic-gradient donut chart as HTML fallback.

    Args:
        category_data: {category_id: amount} mapping
    """
    total = sum(category_data.values())
    if total <= 0:
        return ""

    # Build conic-gradient stops
    gradient_stops = []
    legend_items = []
    cumulative_pct = 0.0

    for cat_id, cat_info in EXPENSE_CATEGORIES.items():
        amount = category_data.get(cat_id, 0)
        if amount <= 0:
            continue
        pct = (amount / total) * 100
        start = cumulative_pct
        end = cumulative_pct + pct
        color = cat_info["color"]
        gradient_stops.append(f"{color} {start:.1f}% {end:.1f}%")
        legend_items.append(
            f'<div class="chart-legend-item">'
            f'<span class="chart-legend-dot" style="background:{color};"></span>'
            f'{cat_info["label"]} ({pct:.0f}%)'
            f'</div>'
        )
        cumulative_pct = end

    gradient = ", ".join(gradient_stops)

    html = (
        f'<div class="donut-chart" style="background:conic-gradient({gradient});">'
        f'<div class="donut-center-label">{len(category_data)} kategori</div>'
        f'</div>'
        f'<div class="chart-legend">{"".join(legend_items)}</div>'
    )
    return html


def render_expense_charts():
    """Render expense visualization charts: pie, daily bars, budget vs actual.

    Uses Plotly if available, falls back to pure HTML/CSS charts.
    Awards +10 XP on first view.
    """
    expenses = st.session_state.tracker_expenses
    budget = st.session_state.tracker_budget

    # Edge case: no expenses means no charts
    if not expenses:
        return

    # XP for first-time chart view
    if not st.session_state.get("xp_charts_viewed"):
        add_xp(10, "Melihat grafik pengeluaran")
        st.session_state.xp_charts_viewed = True

    st.markdown("### <span aria-hidden='true'>\U0001f4ca</span> Visualisasi Pengeluaran", unsafe_allow_html=True)

    # --- Gather category data ---
    category_data = {}
    for cat_id in EXPENSE_CATEGORIES:
        spent = get_spent_by_category(cat_id)
        if spent > 0:
            category_data[cat_id] = spent

    # --- Gather daily data ---
    daily_data = _build_daily_breakdown(expenses)

    # =====================================================================
    # Chart 1: Category Pie / Donut Chart
    # =====================================================================
    col_pie, col_daily = st.columns(2)

    with col_pie:
        st.markdown(
            '<div class="expense-chart-section">'
            '<h4><span aria-hidden="true">\U0001f4c0</span> Pengeluaran per Kategori</h4>',
            unsafe_allow_html=True,
        )

        if HAS_PLOTLY and category_data:
            labels = []
            values = []
            colors = []
            for cat_id, amount in category_data.items():
                cat_info = EXPENSE_CATEGORIES[cat_id]
                labels.append(cat_info["label"])
                values.append(amount)
                colors.append(cat_info["color"])

            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors),
                textinfo="percent",
                textfont=dict(size=12, color="#e2e8f0"),
                hovertemplate="%{label}<br>Rp %{value:,.0f}<br>%{percent}<extra></extra>",
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                legend=dict(
                    font=dict(color="#b0b0b0", size=11),
                    bgcolor="rgba(0,0,0,0)",
                ),
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_category_pie")
        elif category_data:
            # HTML/CSS donut fallback
            st.markdown(
                _build_category_donut_html(category_data),
                unsafe_allow_html=True,
            )
        else:
            st.caption("Belum ada data pengeluaran per kategori.")

        st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================================
    # Chart 2: Daily Spending Bar Chart
    # =====================================================================
    with col_daily:
        st.markdown(
            '<div class="expense-chart-section">'
            '<h4><span aria-hidden="true">\U0001f4c5</span> Pengeluaran Harian</h4>',
            unsafe_allow_html=True,
        )

        if HAS_PLOTLY and daily_data:
            dates = [d["date"] for d in daily_data]
            totals = [d["total"] for d in daily_data]

            fig = go.Figure(data=[go.Bar(
                x=dates,
                y=totals,
                marker_color="#d4af37",
                hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f}<extra></extra>",
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis=dict(
                    showgrid=False,
                    color="#64748b",
                    tickfont=dict(size=10),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    color="#64748b",
                    tickfont=dict(size=10),
                ),
                margin=dict(t=10, b=40, l=60, r=10),
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_daily_bar")
        elif daily_data:
            # HTML fallback bars
            max_total = max(d["total"] for d in daily_data) if daily_data else 1
            for day in daily_data:
                pct = (day["total"] / max_total * 100) if max_total > 0 else 0
                st.markdown(
                    f'<div class="daily-bar">'
                    f'<div class="daily-bar-label">{day["date"][-5:]}</div>'
                    f'<div class="daily-bar-track">'
                    f'<div class="daily-bar-fill" style="width:{pct:.1f}%;"></div>'
                    f'</div>'
                    f'<div class="daily-bar-amount">{format_idr(day["total"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Belum ada data pengeluaran harian.")

        st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================================
    # Chart 3: Budget vs Actual Comparison
    # =====================================================================
    st.markdown(
        '<div class="expense-chart-section">'
        '<h4><span aria-hidden="true">\U0001f4ca</span> Budget vs Aktual per Kategori</h4>',
        unsafe_allow_html=True,
    )

    if HAS_PLOTLY:
        labels = []
        budget_vals = []
        actual_vals = []
        actual_colors = []

        for cat_id, cat_info in EXPENSE_CATEGORIES.items():
            cat_budget = budget.get(cat_id, 0)
            cat_spent = get_spent_by_category(cat_id)
            if cat_budget <= 0 and cat_spent <= 0:
                continue
            labels.append(cat_info["label"])
            budget_vals.append(cat_budget)
            actual_vals.append(cat_spent)
            actual_colors.append("#f87171" if cat_spent > cat_budget else "#4ade80")

        if labels:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=labels,
                x=budget_vals,
                name="Budget",
                orientation="h",
                marker_color="#d4af37",
                hovertemplate="%{y}<br>Budget: Rp %{x:,.0f}<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                y=labels,
                x=actual_vals,
                name="Aktual",
                orientation="h",
                marker_color=actual_colors,
                hovertemplate="%{y}<br>Aktual: Rp %{x:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                legend=dict(
                    font=dict(color="#b0b0b0", size=11),
                    bgcolor="rgba(0,0,0,0)",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    color="#64748b",
                    tickfont=dict(size=10),
                ),
                yaxis=dict(
                    showgrid=False,
                    color="#e2e8f0",
                    tickfont=dict(size=11),
                    autorange="reversed",
                ),
                margin=dict(t=30, b=20, l=120, r=20),
                height=max(200, len(labels) * 60 + 60),
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_budget_vs_actual")
        else:
            st.caption("Belum ada data budget atau pengeluaran.")
    else:
        # HTML fallback: horizontal grouped bars
        max_val = 1
        for cat_id in EXPENSE_CATEGORIES:
            cat_budget = budget.get(cat_id, 0)
            cat_spent = get_spent_by_category(cat_id)
            max_val = max(max_val, cat_budget, cat_spent)

        has_data = False
        for cat_id, cat_info in EXPENSE_CATEGORIES.items():
            cat_budget = budget.get(cat_id, 0)
            cat_spent = get_spent_by_category(cat_id)
            if cat_budget <= 0 and cat_spent <= 0:
                continue
            has_data = True
            budget_pct = (cat_budget / max_val * 100) if max_val > 0 else 0
            actual_pct = (cat_spent / max_val * 100) if max_val > 0 else 0
            actual_class = "actual-over" if cat_spent > cat_budget else "actual-under"

            st.markdown(
                f'<div class="budget-vs-actual-row">'
                f'<div class="budget-vs-actual-label">'
                f'<span>{cat_info["icon"]} {cat_info["label"]}</span>'
                f'<span>{format_idr(cat_spent)} / {format_idr(cat_budget)}</span>'
                f'</div>'
                f'<div class="budget-vs-actual-bars">'
                f'<div class="bva-bar-track">'
                f'<div class="bva-bar-fill budget-bar" style="width:{budget_pct:.1f}%;"></div>'
                f'</div>'
                f'<div class="bva-bar-track">'
                f'<div class="bva-bar-fill {actual_class}" style="width:{actual_pct:.1f}%;"></div>'
                f'</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if has_data:
            st.markdown(
                '<div class="bva-legend">'
                '<span><span class="bva-legend-swatch" style="background:#d4af37;"></span> Budget</span>'
                '<span><span class="bva-legend-swatch" style="background:#4ade80;"></span> Aktual (di bawah)</span>'
                '<span><span class="bva-legend-swatch" style="background:#f87171;"></span> Aktual (melebihi)</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Belum ada data budget atau pengeluaran.")

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# UI: AI SAVINGS INSIGHTS
# =============================================================================

def render_savings_insights():
    """Render AI-powered savings insights button and results."""
    expenses = st.session_state.tracker_expenses
    budget = st.session_state.tracker_budget

    st.markdown("### \U0001f4a1 AI Savings Insights")
    st.caption(
        "Analisis pola pengeluaran Anda dan dapatkan saran penghematan dari AI."
    )

    if not expenses:
        st.info("Catat beberapa pengeluaran terlebih dahulu untuk mendapatkan insights.")
        return

    if st.button(
        "\U0001f9e0 Analisis Pengeluaran Saya",
        use_container_width=True,
        type="primary",
        key="btn_ai_insights",
    ):
        with st.spinner("AI sedang menganalisis pola pengeluaran Anda..."):
            # Build analysis data
            total_budget = get_total_budget()
            total_spent = get_total_spent()
            remaining = total_budget - total_spent

            category_summary = []
            for cat_id, cat_info in EXPENSE_CATEGORIES.items():
                cat_budget = budget.get(cat_id, 0)
                cat_spent = get_spent_by_category(cat_id)
                pct = (cat_spent / cat_budget * 100) if cat_budget > 0 else 0
                category_summary.append(
                    f"- {cat_info['label']}: Budget {format_idr_full(cat_budget)}, "
                    f"Terpakai {format_idr_full(cat_spent)} ({pct:.0f}%)"
                )

            daily_avg = get_daily_average()
            num_days = len(set(e["date"] for e in expenses))

            prompt_text = (
                f"Analisis pengeluaran umrah berikut dan berikan 3-5 saran penghematan:\n\n"
                f"Total Budget: {format_idr_full(total_budget)}\n"
                f"Total Terpakai: {format_idr_full(total_spent)}\n"
                f"Sisa: {format_idr_full(remaining)}\n"
                f"Rata-rata harian: {format_idr_full(int(daily_avg))}\n"
                f"Jumlah hari pencatatan: {num_days}\n\n"
                f"Breakdown per kategori:\n"
                + "\n".join(category_summary)
                + "\n\nBerikan analisis singkat dan 3-5 tips penghematan praktis "
                "untuk jamaah umrah. Jawab dalam bahasa Indonesia."
            )

            system_prompt = (
                "Kamu adalah konsultan keuangan travel umrah berpengalaman. "
                "Berikan analisis singkat dan saran penghematan yang praktis "
                "untuk jamaah umrah Indonesia. Fokus pada tips yang bisa "
                "langsung diterapkan. Gunakan bahasa Indonesia yang sopan."
            )

            response = ai_complete(prompt_text, system_prompt=system_prompt, max_tokens=1024)

            if response:
                st.markdown(f"""
                <div class="insight-card" role="status" aria-live="polite">
                    <h3>\U0001f4a1 Hasil Analisis AI</h3>
                    {_markdown_to_html_simple(response)}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback insights when AI is unavailable
                _render_fallback_insights(budget, total_spent, total_budget, remaining)


def _markdown_to_html_simple(text: str) -> str:
    """Simple markdown to HTML conversion for display in custom styled div."""
    import re

    lines = text.split("\n")
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append("<br/>")
            continue
        # Bold
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        # Bullet points
        if line.startswith("- ") or line.startswith("* "):
            line = f"&bull; {line[2:]}"
        # Numbered lists
        match = re.match(r"^(\d+)\.\s+", line)
        if match:
            line = f"<strong>{match.group(1)}.</strong> {line[match.end():]}"
        html_lines.append(f"<div style='margin-bottom:0.3rem;'>{line}</div>")

    return "\n".join(html_lines)


def _render_fallback_insights(
    budget: Dict, total_spent: int, total_budget: int, remaining: int
):
    """Render fallback insights when AI is unavailable."""
    tips = []

    # Check overspending categories
    for cat_id, cat_info in EXPENSE_CATEGORIES.items():
        cat_budget = budget.get(cat_id, 0)
        cat_spent = get_spent_by_category(cat_id)
        if cat_budget > 0 and cat_spent > cat_budget:
            over = cat_spent - cat_budget
            tips.append(
                f"\u26a0\ufe0f **{cat_info['label']}** melebihi budget sebesar "
                f"{format_idr(over)}. Pertimbangkan untuk mengurangi pengeluaran "
                f"di kategori ini."
            )

    # Check underutilized categories
    for cat_id, cat_info in EXPENSE_CATEGORIES.items():
        cat_budget = budget.get(cat_id, 0)
        cat_spent = get_spent_by_category(cat_id)
        if cat_budget > 0 and cat_spent < cat_budget * 0.2 and cat_spent > 0:
            tips.append(
                f"\u2705 **{cat_info['label']}** baru terpakai {format_idr(cat_spent)} "
                f"dari {format_idr(cat_budget)}. Budget tersisa masih banyak."
            )

    # General tips
    if remaining < 0:
        tips.append(
            "\U0001f6a8 **Total pengeluaran melebihi budget!** "
            "Segera evaluasi pengeluaran dan kurangi belanja non-esensial."
        )
    elif remaining < total_budget * 0.1:
        tips.append(
            "\u26a0\ufe0f Sisa budget tinggal kurang dari 10%. "
            "Prioritaskan pengeluaran penting saja."
        )
    else:
        tips.append(
            "\U0001f44d Budget masih terkendali. Tetap catat setiap pengeluaran "
            "agar tidak ada yang terlewat."
        )

    tips.append(
        "\U0001f4a1 **Tips:** Bandingkan harga di beberapa toko sebelum membeli "
        "oleh-oleh. Area sekitar Masjidil Haram biasanya lebih mahal."
    )
    tips.append(
        "\U0001f4a1 **Tips:** Makan di restoran lokal yang agak jauh dari "
        "Haram bisa menghemat hingga 50% dibanding area dekat masjid."
    )

    st.markdown("""
    <div class="insight-card" role="status" aria-live="polite">
        <h3>\U0001f4a1 Saran Penghematan</h3>
    </div>
    """, unsafe_allow_html=True)

    for tip in tips:
        st.markdown(tip)


# =============================================================================
# UI: EDIT BUDGET
# =============================================================================

def render_edit_budget():
    """Render edit budget section (accessible after budget is set)."""
    with st.expander("\u2699\ufe0f Ubah Budget", expanded=False):
        budget_values = {}
        cols = st.columns(3)

        for idx, (cat_id, cat_info) in enumerate(EXPENSE_CATEGORIES.items()):
            with cols[idx % 3]:
                current_val = st.session_state.tracker_budget.get(cat_id, 0)
                budget_values[cat_id] = st.number_input(
                    f"{cat_info['icon']} {cat_info['label']}",
                    min_value=0,
                    max_value=500_000_000,
                    value=current_val,
                    step=500_000,
                    format="%d",
                    key=f"edit_budget_{cat_id}",
                )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("\U0001f4be Update Budget", use_container_width=True):
                st.session_state.tracker_budget = budget_values
                st.success("Budget berhasil diupdate!")
                st.rerun()

        with col2:
            if st.button(
                "\U0001f5d1\ufe0f Reset Semua Data",
                use_container_width=True,
            ):
                st.session_state.tracker_budget = {}
                st.session_state.tracker_expenses = []
                st.session_state.tracker_budget_set = False
                st.toast("Semua data cost tracker direset.")
                st.rerun()


# =============================================================================
# UI: EXPORT
# =============================================================================

def render_export_section():
    """Render export options."""
    st.markdown("### \U0001f4e4 Export Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        text_data = export_to_text()
        st.download_button(
            "\U0001f4c4 Download TXT",
            data=text_data,
            file_name=f"cost_tracker_umrah_{date.today().isoformat()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:
        csv_data = export_to_csv()
        st.download_button(
            "\U0001f4ca Download CSV",
            data=csv_data,
            file_name=f"cost_tracker_umrah_{date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col3:
        if st.button(
            "\U0001f4cb Salin ke Clipboard",
            use_container_width=True,
            key="btn_copy_export",
        ):
            text_data = export_to_text()
            st.code(text_data, language=None)
            st.caption("Salin teks di atas secara manual.")


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

.sync-banner {
    background: linear-gradient(135deg, #1a2a1a 0%, #1e3a1e 100%);
    border: 1px solid #4ade80;
    border-left: 4px solid #4ade80;
    border-radius: 14px;
    padding: 1.25rem;
    margin: 1rem 0;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.sync-banner .sync-text {
    flex: 1;
    min-width: 200px;
}

.sync-banner .sync-title {
    color: #4ade80;
    font-weight: 700;
    font-size: 0.95rem;
}

.sync-banner .sync-detail {
    color: #b0b0b0;
    font-size: 0.82rem;
    margin-top: 0.2rem;
}

@media (max-width: 480px) {
    .sync-banner {
        flex-direction: column;
        align-items: stretch;
        text-align: center;
    }
}
"""


# =============================================================================
# CROSS-PAGE NAVIGATION
# =============================================================================

def render_cross_nav():
    """Render cross-page navigation buttons and booking sync banner."""
    st.markdown(CROSS_NAV_CSS, unsafe_allow_html=True)

    # --- Booking data sync banner ---
    booking_costs = st.session_state.get("booking_costs")
    if booking_costs and isinstance(booking_costs, dict):
        total_amount = booking_costs.get("total", 0)
        pkg_name = booking_costs.get("package_name", "Umrah")
        dep_date = booking_costs.get("departure_date", "")
        breakdown = booking_costs.get("breakdown", {})

        st.markdown(
            f'<div class="sync-banner">'
            f'<div style="font-size:1.5rem;" aria-hidden="true">\U0001f504</div>'
            f'<div class="sync-text">'
            f'<div class="sync-title">Data booking tersedia \u2014 Sinkronkan?</div>'
            f'<div class="sync-detail">'
            f'Paket {pkg_name} | {dep_date} | {format_idr_full(total_amount)}'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "\U0001f504 Sinkronkan Data Booking sebagai Pengeluaran",
            key="btn_sync_booking_to_expenses",
            type="primary",
            use_container_width=True,
        ):
            imported_count = 0
            for item_key, item_data in breakdown.items():
                new_expense = {
                    "id": str(uuid.uuid4()),
                    "date": datetime.now().date().isoformat(),
                    "category": _map_booking_category(item_key),
                    "amount": item_data.get("amount", 0),
                    "notes": item_data.get("label", item_key),
                }
                st.session_state.tracker_expenses.append(new_expense)
                imported_count += 1

            add_xp(15, "Sinkronisasi data booking ke cost tracker")
            st.success(
                f"\u2705 {imported_count} item biaya booking berhasil diimpor sebagai pengeluaran!"
            )
            # Clear booking_costs so banner doesn't show again
            del st.session_state["booking_costs"]
            st.rerun()

    # --- Navigation card ---
    st.markdown(
        '<div class="cross-nav-card">'
        '<h3><span aria-hidden="true">\U0001f9ed</span> Jelajahi Fitur Lainnya</h3>'
        '<div class="cross-nav-subtitle">Lanjutkan perencanaan umrah Anda</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        if st.button(
            "\U0001f54b Buat Booking Baru",
            key="nav_to_booking",
            use_container_width=True,
        ):
            st.session_state.nav = "booking"
            st.rerun()

    with nav_col2:
        if st.button(
            "\u2705 Cek Kesiapan",
            key="nav_to_readiness_from_tracker",
            use_container_width=True,
        ):
            st.session_state.nav = "readiness_checker"
            st.rerun()


def _map_booking_category(item_key: str) -> str:
    """Map booking breakdown keys to cost tracker expense categories."""
    mapping = {
        "paket_dasar": "penerbangan",
        "upgrade_hotel": "hotel",
        "addons": "lainnya",
        "penyesuaian_musiman": "lainnya",
    }
    return mapping.get(item_key, "lainnya")


# =============================================================================
# MAIN PAGE RENDERER
# =============================================================================

def render_cost_tracker_page():
    """Main entry point for the Cost Tracker page."""

    # Track page view
    try:
        from services.analytics import track_page
        track_page("cost_tracker")
    except Exception:
        pass

    # Initialize state
    init_cost_tracker_state()

    # Hero
    render_hero()

    # --- BUDGET NOT SET: Show setup ---
    if not st.session_state.tracker_budget_set:
        render_budget_setup()

        # DYOR footer
        st.divider()
        st.warning("""
        \u26a0\ufe0f **DYOR - Do Your Own Research**

        Fitur Cost Tracker ini membantu mencatat pengeluaran secara manual.
        Data disimpan di sesi browser dan tidak tersinkronisasi ke server.
        Pastikan untuk meng-export data Anda secara berkala.

        **LABBAIK AI tidak bertanggung jawab atas data yang hilang.**
        """)
        return

    # --- BUDGET SET: Show full dashboard ---

    # Budget alerts (warning/danger banners)
    render_budget_alerts()

    # Dashboard metrics and category breakdown
    render_dashboard()

    st.divider()

    # Expense visualization charts (pie, daily bar, budget vs actual)
    render_expense_charts()

    st.divider()

    # Savings comparison: Budget vs Actual per category
    render_savings_tracker()

    st.divider()

    # Two-column layout: Add Expense + Insights side by side
    tab_expense, tab_history, tab_insights, tab_export = st.tabs([
        "\u2795 Tambah Pengeluaran",
        "\U0001f4cb Riwayat",
        "\U0001f4a1 AI Insights",
        "\U0001f4e4 Export",
    ])

    with tab_expense:
        render_add_expense()

    with tab_history:
        render_expense_list()

    with tab_insights:
        render_savings_insights()

    with tab_export:
        render_export_section()

    st.divider()

    # Cross-page navigation and booking sync
    render_cross_nav()

    st.divider()

    # Edit budget section
    render_edit_budget()

    # DYOR footer
    st.divider()
    st.warning("""
    \u26a0\ufe0f **DYOR - Do Your Own Research**

    Fitur Cost Tracker ini membantu mencatat pengeluaran secara manual.
    Data disimpan di sesi browser dan tidak tersinkronisasi ke server.
    Pastikan untuk meng-export data Anda secara berkala.

    **LABBAIK AI tidak bertanggung jawab atas data yang hilang.**
    """)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["render_cost_tracker_page"]
