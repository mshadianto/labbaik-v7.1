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
    color: var(--hero-subtitle, #888);
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
    color: #888;
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
    color: #94a3b8;
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
    color: #64748b;
}

.empty-state .icon, .empty-state .empty-icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.empty-state .empty-text {
    font-size: 0.95rem;
    color: #94a3b8;
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
# HELPER: inject CSS blocks
# =============================================================================

def inject_css(*css_blocks):
    """Combine and inject CSS blocks via st.markdown.

    Usage:
        inject_css(HERO_CSS, CARD_CSS, MY_PAGE_OVERRIDES)
    """
    combined = FONT_IMPORT + "\n" + "\n".join(css_blocks)
    st.markdown(f"<style>{combined}</style>", unsafe_allow_html=True)


__all__ = [
    "FONT_IMPORT",
    "HERO_CSS",
    "CARD_CSS",
    "AI_CARD_CSS",
    "PROGRESS_CSS",
    "EMPTY_STATE_CSS",
    "BADGE_CSS",
    "inject_css",
]
