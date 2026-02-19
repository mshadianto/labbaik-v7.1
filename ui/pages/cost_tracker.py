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

try:
    from ui.pages.kurs_calculator import get_current_rates
    HAS_KURS_SERVICE = True
except ImportError:
    HAS_KURS_SERVICE = False

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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# HELPERS
# =============================================================================

def format_idr(amount):
    """Format amount as Indonesian Rupiah with short notation."""
    if amount >= 1_000_000:
        return f"Rp {amount / 1_000_000:.1f} jt"
    elif amount >= 1_000:
        return f"Rp {amount / 1_000:.0f} rb"
    return f"Rp {amount:,.0f}"


def format_idr_full(amount):
    """Format amount as full Indonesian Rupiah."""
    return f"Rp {amount:,.0f}".replace(",", ".")


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
        <div class="empty-state">
            <div class="icon">\U0001f4dd</div>
            <div>Belum ada pengeluaran yang dicatat.</div>
            <div style="margin-top:0.5rem;">Gunakan form di atas untuk menambah pengeluaran pertama Anda.</div>
        </div>
        """, unsafe_allow_html=True)
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

    # Dashboard metrics and category breakdown
    render_dashboard()

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
