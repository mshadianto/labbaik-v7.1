"""
================================================================================
LABBAIK AI - SHARED CSS STYLES
================================================================================
Reusable CSS constants for feature pages. Each page imports what it needs
and adds only page-specific overrides.
================================================================================
"""

import streamlit as st


# =============================================================================
# FONT IMPORT
# =============================================================================

FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');"


# =============================================================================
# HERO BANNER (shared structure, pages override colors via variables)
# =============================================================================

HERO_CSS = """
/* Hero banner — override --hero-bg, --hero-border, --hero-title, --hero-subtitle */
.page-hero {
    background: var(--hero-bg, linear-gradient(135deg, #0d1b2a 0%, #1b2a4a 100%));
    padding: 2.5rem 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    border: 1px solid var(--hero-border, #d4af37);
    position: relative;
    overflow: hidden;
}

.page-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.05) 0%, transparent 70%);
    animation: hero-pulse 4s ease-in-out infinite;
    pointer-events: none;
}

@keyframes hero-pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}

.page-hero h1 {
    color: var(--hero-title, #d4af37);
    margin: 0;
    font-size: 2.2rem;
    position: relative;
    z-index: 1;
}

.page-hero .subtitle {
    color: var(--hero-subtitle, #b0b0b0);
    font-size: 1rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

.page-hero .ayat, .page-hero .arabic, .page-hero .bismillah {
    font-family: 'Amiri', serif;
    color: #d4af37;
    font-size: 1.3rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}
"""


# =============================================================================
# DARK CARD BASE (used by stat cards, category cards, POI cards, etc.)
# =============================================================================

CARD_CSS = """
/* Dark card base — reused across pages */
.dark-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    padding: 1.25rem;
    border: 1px solid #333;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.dark-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Stat / metric card */
.stat-card {
    text-align: center;
    padding: 1.25rem;
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 15px;
    border: 1px solid #333;
    transition: transform 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
}

.stat-card .number {
    font-size: 1.8rem;
    font-weight: bold;
}

.stat-card .label {
    color: #b0b0b0;
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

/* Metric card (cost tracker style) */
.metric-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 1.25rem;
    text-align: center;
    border: 1px solid #334155;
    transition: border-color 0.2s;
}

.metric-card:hover {
    border-color: #d4af37;
}

.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    margin: 0.25rem 0;
}

.metric-label {
    color: #b8c5d4;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
"""


# =============================================================================
# AI TIPS CARD (shared green gradient card for AI-generated content)
# =============================================================================

AI_CARD_CSS = """
/* AI insight / tips card */
.ai-card {
    background: linear-gradient(145deg, #1a2e1a 0%, #1a3a1a 100%);
    border: 1px solid #228B22;
    border-radius: 15px;
    padding: 1.5rem;
    margin-top: 1rem;
}

.ai-card h3, .ai-card h4 {
    color: #4ade80;
    margin-top: 0;
    margin-bottom: 0.75rem;
}

.ai-card p {
    color: #ccc;
    line-height: 1.7;
    margin: 0;
    white-space: pre-wrap;
}
"""


# =============================================================================
# PROGRESS BAR
# =============================================================================

PROGRESS_CSS = """
/* Progress bar */
.progress-track {
    width: 100%;
    height: 8px;
    background: #1e293b;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
}
"""


# =============================================================================
# EMPTY STATE
# =============================================================================

EMPTY_STATE_CSS = """
/* Empty state placeholder */
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #8e9fb3;
}

.empty-state .icon, .empty-state .empty-icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.empty-state .empty-text {
    font-size: 0.95rem;
    color: #b8c5d4;
}
"""


# =============================================================================
# SKELETON / LOADING PLACEHOLDERS (opt-in, not auto-included by inject_css)
# =============================================================================

SKELETON_CSS = """
/* Skeleton loading animation */
@keyframes skeleton-pulse {
    0% { opacity: 0.6; }
    50% { opacity: 0.3; }
    100% { opacity: 0.6; }
}

.skeleton {
    background: linear-gradient(90deg, #1a1a2e 25%, #2a2a3e 50%, #1a1a2e 75%);
    background-size: 200% 100%;
    animation: skeleton-pulse 1.5s ease-in-out infinite;
    border-radius: 8px;
}

.skeleton-text {
    height: 1rem;
    margin-bottom: 0.5rem;
    border-radius: 4px;
}

.skeleton-text.short { width: 40%; }
.skeleton-text.medium { width: 70%; }
.skeleton-text.long { width: 100%; }

.skeleton-card {
    height: 120px;
    border-radius: 15px;
    margin-bottom: 1rem;
}

.skeleton-stat {
    height: 80px;
    border-radius: 15px;
}

.skeleton-hero {
    height: 180px;
    border-radius: 20px;
    margin-bottom: 1.5rem;
}
"""


# =============================================================================
# PRIORITY / STATUS BADGES
# =============================================================================

BADGE_CSS = """
/* Priority badges */
.priority-tinggi {
    display: inline-block;
    background: #4a1a1a;
    color: #f87171;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}

.priority-sedang {
    display: inline-block;
    background: #4a3a1a;
    color: #fbbf24;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}

.priority-rendah {
    display: inline-block;
    background: #1a3a1a;
    color: #4ade80;
    padding: 0.15rem 0.6rem;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: bold;
}
"""


# =============================================================================
# RESPONSIVE: Mobile breakpoints
# =============================================================================

RESPONSIVE_CSS = """
/* ================================================================
   TABLET (max-width: 768px)
   - 3-col and 4-col layouts wrap to 2 columns
   - Touch-friendly sizing for buttons and form elements
   - Tabs: smaller text, horizontal scroll
   - Expander: full-width, larger tap target
   - Metric: scaled-down font sizes
   - Dataframe / table: horizontal scroll wrapper
   - Sidebar mobile refinements
   ================================================================ */
@media (max-width: 768px) {
    /* --- Hero --- */
    .page-hero { padding: 1.5rem 1rem; border-radius: 12px; margin-bottom: 1rem; }
    .page-hero h1 { font-size: 1.5rem; }
    .page-hero .subtitle { font-size: 0.85rem; }
    .page-hero .ayat, .page-hero .arabic, .page-hero .bismillah { font-size: 1rem; }

    /* --- Cards --- */
    .dark-card { padding: 1rem; border-radius: 10px; }
    .stat-card { padding: 0.8rem; }
    .stat-card .number { font-size: 1.3rem; }
    .metric-card { padding: 0.8rem; }
    .metric-value { font-size: 1.2rem; }
    .metric-label { font-size: 0.72rem; }
    .ai-card { padding: 1rem; }
    .empty-state { padding: 1.5rem 0.5rem; }
    .empty-state .icon, .empty-state .empty-icon { font-size: 2rem; }

    /* --- Skeleton placeholders --- */
    .skeleton-hero { height: 120px; border-radius: 12px; margin-bottom: 1rem; }
    .skeleton-card { height: 90px; border-radius: 10px; }
    .skeleton-stat { height: 60px; border-radius: 10px; }

    /* --- Column wrapping: 3-col and 4-col layouts → 2 columns --- */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 48% !important;
        min-width: 46%;
        padding: 0 0.25rem;
    }

    /* --- Touch-friendly buttons --- */
    .stButton > button {
        min-height: 44px;
        font-size: 0.9rem;
        padding: 0.5rem 0.75rem;
    }

    /* --- Form elements: larger tap targets and spacing --- */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {
        min-height: 44px;
        font-size: 0.95rem;
    }
    .stRadio > div, .stCheckbox > label {
        padding: 0.35rem 0;
    }
    div[data-testid="stForm"] > div {
        gap: 0.75rem;
    }

    /* --- Tabs: smaller text, horizontal scroll --- */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        gap: 0;
        flex-wrap: nowrap;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
        height: 3px;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
        background: #555;
        border-radius: 3px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.8rem;
        padding: 0.5rem 0.75rem;
        white-space: nowrap;
        flex-shrink: 0;
    }

    /* --- Expander: full width, larger tap target --- */
    .streamlit-expanderHeader {
        font-size: 0.95rem;
        padding: 0.75rem 1rem !important;
        min-height: 48px;
        display: flex;
        align-items: center;
    }
    details[data-testid="stExpander"] {
        width: 100%;
    }

    /* --- Metric widget: scaled fonts --- */
    [data-testid="stMetric"] {
        padding: 0.5rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.7rem !important;
    }

    /* --- Dataframe / table: horizontal scroll --- */
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    .stDataFrame, .stTable {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        max-width: 100%;
    }
    [data-testid="stDataFrame"] > div,
    [data-testid="stTable"] > div {
        min-width: 100%;
    }

    /* --- Sidebar mobile: tighter spacing under hamburger --- */
    section[data-testid="stSidebar"] {
        min-width: 260px;
        max-width: 300px;
    }
    section[data-testid="stSidebar"] .stButton > button {
        min-height: 42px;
        font-size: 0.85rem;
    }
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        font-size: 0.9rem;
        min-height: 44px;
    }
}

/* ================================================================
   SMALL PHONE (max-width: 480px)
   - All columns stack to single column (100% width)
   - Further font size reductions
   - Extra touch padding
   ================================================================ */
@media (max-width: 480px) {
    /* --- Hero --- */
    .page-hero h1 { font-size: 1.3rem; }
    .page-hero .subtitle { font-size: 0.78rem; }

    /* --- Cards --- */
    .stat-card .number { font-size: 1.1rem; }
    .metric-value { font-size: 1rem; }
    .metric-label { font-size: 0.68rem; }

    /* --- Skeleton placeholders --- */
    .skeleton-hero { height: 100px; border-radius: 10px; }
    .skeleton-card { height: 70px; }
    .skeleton-stat { height: 50px; }

    /* --- Single-column stacking --- */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }

    /* --- Touch-friendly buttons: even larger --- */
    .stButton > button {
        min-height: 48px;
        font-size: 0.9rem;
        padding: 0.6rem 0.75rem;
    }

    /* --- Tabs: even smaller to fit --- */
    .stTabs [data-baseweb="tab"] {
        font-size: 0.72rem;
        padding: 0.4rem 0.55rem;
    }

    /* --- Metric widget: compact --- */
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.68rem !important;
    }

    /* --- Expander: bigger tap target on small screen --- */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
        padding: 0.8rem 1rem !important;
        min-height: 52px;
    }

    /* --- Sidebar: compact overlay on phone --- */
    section[data-testid="stSidebar"] {
        min-width: 260px;
        max-width: 85vw;
    }
}
"""


# =============================================================================
# ACCESSIBILITY: Contrast, focus, skip link, reduced motion
# =============================================================================

ACCESSIBILITY_CSS = """
/* Skip-to-content (hidden until focused) */
.skip-to-content {
    position: absolute; top: -100px; left: 0;
    background: #d4af37; color: #000;
    padding: 0.75rem 1.5rem; z-index: 10000;
    font-weight: bold; font-size: 1rem;
    text-decoration: none; border-radius: 0 0 8px 0;
    transition: top 0.2s ease;
}
.skip-to-content:focus { top: 0; }

/* Focus-visible outlines for keyboard nav */
.stButton > button:focus-visible,
a:focus-visible, input:focus-visible,
select:focus-visible, textarea:focus-visible,
[tabindex]:focus-visible {
    outline: 2px solid #d4af37; outline-offset: 2px;
}

/* Pointer cursor for buttons */
.stButton > button { cursor: pointer; }

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    .page-hero::before { animation: none; }
    .progress-fill { transition: none; }
    .dark-card, .stat-card, .metric-card { transition: none; }
    .skeleton { animation: none; opacity: 0.4; }
}
"""


# =============================================================================
# HELPER: inject CSS blocks
# =============================================================================

def inject_css(*css_blocks):
    """Combine and inject CSS blocks via st.markdown.

    Automatically includes responsive and accessibility CSS.

    Usage:
        inject_css(HERO_CSS, CARD_CSS, MY_PAGE_OVERRIDES)
    """
    combined = FONT_IMPORT + "\n" + "\n".join(css_blocks) + "\n" + RESPONSIVE_CSS + "\n" + ACCESSIBILITY_CSS
    st.markdown(f"<style>{combined}</style>", unsafe_allow_html=True)


def render_skeleton(skeleton_type="card", count=3):
    """Render skeleton loading placeholder.

    Requires SKELETON_CSS to be included via inject_css().

    Args:
        skeleton_type: One of "hero", "stats", "cards", "text".
        count: Number of skeleton elements (used by "stats" and "cards").
    """
    if skeleton_type == "hero":
        st.markdown('<div class="skeleton skeleton-hero"></div>', unsafe_allow_html=True)
    elif skeleton_type == "stats":
        cols_html = ''.join(
            [f'<div style="flex:1"><div class="skeleton skeleton-stat"></div></div>' for _ in range(count)]
        )
        st.markdown(f'<div style="display:flex;gap:1rem">{cols_html}</div>', unsafe_allow_html=True)
    elif skeleton_type == "cards":
        for _ in range(count):
            st.markdown('<div class="skeleton skeleton-card"></div>', unsafe_allow_html=True)
    elif skeleton_type == "text":
        st.markdown('''
            <div class="skeleton skeleton-text long"></div>
            <div class="skeleton skeleton-text medium"></div>
            <div class="skeleton skeleton-text short"></div>
        ''', unsafe_allow_html=True)


__all__ = [
    "FONT_IMPORT",
    "HERO_CSS",
    "CARD_CSS",
    "AI_CARD_CSS",
    "PROGRESS_CSS",
    "EMPTY_STATE_CSS",
    "SKELETON_CSS",
    "BADGE_CSS",
    "RESPONSIVE_CSS",
    "ACCESSIBILITY_CSS",
    "inject_css",
    "render_skeleton",
]
