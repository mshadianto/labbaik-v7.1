"""
LABBAIK AI - Crowd Prediction Widget
====================================
Predicts crowd levels at Masjidil Haram & Masjid Nabawi
based on prayer times, day of week, and seasonal patterns.
"""

import streamlit as st
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Tuple
import math
from services.ai.helpers import ai_complete, add_xp_safe
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS, AI_CARD_CSS

try:
    from hijri_converter import Gregorian
    HAS_HIJRI = True
except ImportError:
    HAS_HIJRI = False

# =============================================================================
# CROWD PREDICTION ENGINE
# =============================================================================

class CrowdPredictor:
    """
    Predicts crowd levels based on multiple factors:
    - Prayer times (5 daily prayers)
    - Day of week (Friday = highest)
    - Season (Ramadan, Hajj = peak)
    - Time of day
    """
    
    # Base crowd levels by hour (0-23) - normalized 0-100
    HOURLY_BASE = {
        0: 20, 1: 15, 2: 10, 3: 8, 4: 25,   # After midnight, before Fajr
        5: 70, 6: 50, 7: 35, 8: 40, 9: 45,   # Fajr peak, morning
        10: 50, 11: 55, 12: 85, 13: 75, 14: 60,  # Dhuhr peak
        15: 70, 16: 80, 17: 90, 18: 95, 19: 85,  # Asr-Maghrib peak
        20: 80, 21: 70, 22: 55, 23: 35  # Isha, evening
    }
    
    # Day multipliers (Friday highest)
    DAY_MULTIPLIERS = {
        0: 1.0,   # Monday
        1: 1.0,   # Tuesday
        2: 1.0,   # Wednesday
        3: 1.1,   # Thursday (pre-Friday)
        4: 1.5,   # Friday (Jumu'ah)
        5: 1.2,   # Saturday
        6: 1.1,   # Sunday
    }
    
    # Season multipliers
    SEASON_MULTIPLIERS = {
        "regular": 1.0,
        "high": 1.2,      # School holidays
        "ramadan": 1.6,   # Ramadan
        "hajj": 2.0,      # Hajj season
    }
    
    # Prayer time windows (approximate for Makkah)
    PRAYER_TIMES = {
        "fajr": (4, 6),
        "dhuhr": (12, 14),
        "asr": (15, 17),
        "maghrib": (18, 19),
        "isha": (19, 21),
    }
    
    def __init__(self):
        self.current_season = self._detect_season()
    
    def _detect_season(self, target_date: date = None) -> str:
        """Detect current season using Hijri calendar (with Gregorian fallback)."""
        today = target_date or date.today()

        if HAS_HIJRI:
            hijri = Gregorian(today.year, today.month, today.day).to_hijri()
            self._hijri_date = str(hijri)
            h_month = hijri.month
            h_day = hijri.day

            if h_month == 9:  # Ramadan
                return "ramadan"
            if h_month == 12 and h_day <= 13:  # Dhul Hijjah (Hajj period)
                return "hajj"
            if h_month in [11, 12]:  # Dhul Qa'dah + rest of Dhul Hijjah
                return "high"
            if h_month == 10 and h_day <= 6:  # Shawwal (Eid al-Fitr)
                return "high"
        else:
            self._hijri_date = None
            # Gregorian fallback (approximate)
            month = today.month
            if month in [3, 4]:
                return "ramadan"
            elif month in [6, 7]:
                return "hajj"

        # School holidays (Gregorian)
        if today.month in [12, 1, 6, 7]:
            return "high"
        return "regular"
    
    def predict(self, location: str = "makkah", target_time: datetime = None) -> Dict[str, Any]:
        """
        Predict crowd level for a specific time.
        Returns level (0-100), description, and recommendation.
        """
        if target_time is None:
            target_time = datetime.now()
        
        hour = target_time.hour
        day = target_time.weekday()
        
        # Base level from hour
        base = self.HOURLY_BASE.get(hour, 50)
        
        # Apply multipliers
        day_mult = self.DAY_MULTIPLIERS.get(day, 1.0)
        season_mult = self.SEASON_MULTIPLIERS.get(self.current_season, 1.0)
        
        # Location adjustment (Madinah slightly less crowded)
        location_mult = 1.0 if location == "makkah" else 0.85
        
        # Calculate final level (cap at 100)
        level = min(int(base * day_mult * season_mult * location_mult), 100)
        
        # Get description and recommendation
        description, color, emoji = self._get_description(level)
        recommendation = self._get_recommendation(level, hour)
        current_prayer = self._get_current_prayer(hour)
        
        return {
            "level": level,
            "description": description,
            "color": color,
            "emoji": emoji,
            "recommendation": recommendation,
            "current_prayer": current_prayer,
            "location": location,
            "time": target_time.strftime("%H:%M"),
            "season": self.current_season,
            "hijri_date": getattr(self, "_hijri_date", None),
        }
    
    def _get_description(self, level: int) -> Tuple[str, str, str]:
        """Get crowd description based on level."""
        if level < 30:
            return "Sangat Sepi", "#22c55e", "🟢"
        elif level < 50:
            return "Sepi", "#84cc16", "🟡"
        elif level < 70:
            return "Sedang", "#eab308", "🟠"
        elif level < 85:
            return "Ramai", "#f97316", "🔴"
        else:
            return "Sangat Ramai", "#ef4444", "⚫"
    
    def _get_recommendation(self, level: int, hour: int) -> str:
        """Get recommendation based on crowd level."""
        if level < 30:
            return "✅ Waktu ideal untuk ibadah dengan khusyuk"
        elif level < 50:
            return "👍 Waktu baik, keramaian masih nyaman"
        elif level < 70:
            return "⏰ Pertimbangkan waktu lain jika ingin lebih tenang"
        elif level < 85:
            return "⚠️ Sangat ramai, siapkan kesabaran ekstra"
        else:
            return "🚨 Puncak keramaian, waspadai keselamatan"
    
    def _get_current_prayer(self, hour: int) -> str:
        """Get current/next prayer based on hour."""
        for prayer, (start, end) in self.PRAYER_TIMES.items():
            if start <= hour < end:
                return prayer.title()
        
        # Find next prayer
        for prayer, (start, end) in self.PRAYER_TIMES.items():
            if hour < start:
                return f"Menuju {prayer.title()}"
        
        return "Setelah Isha"
    
    def get_24h_forecast(self, location: str = "makkah") -> List[Dict]:
        """Get 24-hour crowd forecast."""
        now = datetime.now()
        forecast = []
        
        for h in range(24):
            target = now.replace(hour=h, minute=0, second=0)
            pred = self.predict(location, target)
            forecast.append({
                "hour": h,
                "hour_label": f"{h:02d}:00",
                "level": pred["level"],
                "description": pred["description"],
                "emoji": pred["emoji"],
            })
        
        return forecast
    
    def get_best_times(self, location: str = "makkah", top_n: int = 5) -> List[Dict]:
        """Get the best (least crowded) times to visit."""
        forecast = self.get_24h_forecast(location)
        sorted_times = sorted(forecast, key=lambda x: x["level"])
        return sorted_times[:top_n]
    
    def get_weekly_heatmap(self, location: str = "makkah") -> List[List[int]]:
        """Get weekly heatmap data (7 days x 24 hours)."""
        heatmap = []
        now = datetime.now()
        
        for day in range(7):
            day_data = []
            for hour in range(24):
                # Create datetime for this day/hour
                target = now.replace(hour=hour, minute=0)
                # Adjust weekday
                days_diff = day - now.weekday()
                target = target + timedelta(days=days_diff)
                
                pred = self.predict(location, target)
                day_data.append(pred["level"])
            heatmap.append(day_data)
        
        return heatmap


# =============================================================================
# RENDER FUNCTIONS
# =============================================================================

def render_crowd_widget(location: str = "makkah", compact: bool = False):
    """
    Render crowd prediction widget.
    
    Args:
        location: "makkah" or "madinah"
        compact: If True, render smaller version for sidebar
    """
    predictor = CrowdPredictor()
    current = predictor.predict(location)
    
    location_name = "Masjidil Haram" if location == "makkah" else "Masjid Nabawi"
    location_emoji = "🕋" if location == "makkah" else "🕌"
    
    if compact:
        # Compact version for sidebar
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 15px; border: 1px solid #d4af37;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 1.5rem;">{location_emoji}</span>
                <div style="text-align: right;">
                    <div style="color: #d4af37; font-size: 0.8rem;">{location_name}</div>
                    <div style="color: white; font-size: 1.2rem; font-weight: bold;">{current['emoji']} {current['description']}</div>
                </div>
            </div>
            <div style="margin-top: 0.5rem;">
                <div style="background: #333; border-radius: 10px; height: 8px; overflow: hidden;">
                    <div style="width: {current['level']}%; height: 100%; background: linear-gradient(90deg, #22c55e, #eab308, #ef4444);"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Full version
        st.markdown(f"### {location_emoji} Prediksi Keramaian {location_name}")
        
        # Current status
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1.5rem; border-radius: 20px; border: 1px solid #d4af37;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 4rem;">{current['emoji']}</div>
                    <div>
                        <div style="color: #d4af37; font-size: 0.9rem;">Status Saat Ini ({current['time']} WAS)</div>
                        <div style="color: white; font-size: 2rem; font-weight: bold;">{current['description']}</div>
                        <div style="color: #b0b0b0; font-size: 0.9rem;">Level: {current['level']}% | {current['current_prayer']}</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 0.75rem; background: rgba(212, 175, 55, 0.1); border-radius: 10px; border-left: 3px solid #d4af37;">
                    <div style="color: #d4af37; font-size: 0.85rem;">{current['recommendation']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Season indicator
            season_labels = {
                "regular": ("📅 Musim Reguler", "#22c55e"),
                "high": ("🏖️ Musim Liburan", "#eab308"),
                "ramadan": ("🌙 Ramadan", "#8b5cf6"),
                "hajj": ("🕋 Musim Haji", "#ef4444"),
            }
            season_label, season_color = season_labels.get(current['season'], ("📅 Regular", "#b0b0b0"))
            
            hijri_line = ""
            if current.get("hijri_date"):
                hijri_line = f'<div style="color:#d4af37;font-size:0.75rem;margin-top:0.25rem;">{current["hijri_date"]} H</div>'
            st.markdown(f"""
            <div style="background: #1a1a1a; padding: 1rem; border-radius: 15px; text-align: center; height: 100%;">
                <div style="color: {season_color}; font-size: 2rem;" aria-hidden="true">📊</div>
                <div style="color: white; font-size: 0.9rem; margin-top: 0.5rem;">{season_label}</div>
                {hijri_line}
                <div style="color: #b0b0b0; font-size: 0.75rem; margin-top: 0.25rem;">Multiplier aktif</div>
            </div>
            """, unsafe_allow_html=True)


def render_24h_forecast(location: str = "makkah"):
    """Render 24-hour forecast chart."""
    predictor = CrowdPredictor()
    forecast = predictor.get_24h_forecast(location)
    
    st.markdown("### 📊 Prediksi 24 Jam")
    
    # Convert to dataframe for chart
    import pandas as pd
    df = pd.DataFrame(forecast)
    
    # Create bar chart with color coding
    st.bar_chart(df.set_index('hour_label')['level'], use_container_width=True)
    
    # Best times
    best_times = predictor.get_best_times(location, 3)
    
    st.markdown("#### 🌟 Waktu Terbaik Hari Ini")
    
    cols = st.columns(3)
    for i, time_slot in enumerate(best_times):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a1a, #2d2d2d); padding: 1rem; border-radius: 15px; text-align: center; border: 1px solid #22c55e;">
                <div style="color: #22c55e; font-size: 1.5rem; font-weight: bold;">{time_slot['hour_label']}</div>
                <div style="color: white; font-size: 0.9rem;">{time_slot['description']}</div>
                <div style="color: #b0b0b0; font-size: 0.75rem;">Level: {time_slot['level']}%</div>
            </div>
            """, unsafe_allow_html=True)


def render_weekly_heatmap(location: str = "makkah"):
    """Render weekly crowd heatmap."""
    predictor = CrowdPredictor()
    
    st.markdown("### 🗓️ Peta Keramaian Mingguan")
    st.caption("Warna lebih gelap = lebih ramai")
    
    days = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    heatmap = predictor.get_weekly_heatmap(location)
    
    # Create HTML heatmap
    html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 0.7rem;">'
    
    # Header row (hours)
    html += '<tr><th style="padding: 4px; color: #b0b0b0;"></th>'
    for h in range(0, 24, 2):
        html += f'<th style="padding: 4px; color: #b0b0b0;">{h:02d}</th>'
    html += '</tr>'
    
    # Data rows
    for day_idx, day_data in enumerate(heatmap):
        html += f'<tr><td style="padding: 4px; color: #d4af37; font-weight: bold;">{days[day_idx]}</td>'
        for h in range(0, 24, 2):
            level = day_data[h]
            # Color based on level
            if level < 30:
                bg = "#22c55e"
            elif level < 50:
                bg = "#84cc16"
            elif level < 70:
                bg = "#eab308"
            elif level < 85:
                bg = "#f97316"
            else:
                bg = "#ef4444"
            
            html += f'<td style="padding: 4px; background: {bg}; text-align: center; border-radius: 4px; color: #1a1a1a; font-weight: bold;">{level}</td>'
        html += '</tr>'
    
    html += '</table></div>'
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Legend
    st.markdown("""
    <div style="display: flex; gap: 1rem; margin-top: 1rem; justify-content: center; flex-wrap: wrap;">
        <span style="display: flex; align-items: center; gap: 0.25rem;"><span style="width: 20px; height: 20px; background: #22c55e; border-radius: 4px;"></span> Sepi</span>
        <span style="display: flex; align-items: center; gap: 0.25rem;"><span style="width: 20px; height: 20px; background: #84cc16; border-radius: 4px;"></span> Agak Sepi</span>
        <span style="display: flex; align-items: center; gap: 0.25rem;"><span style="width: 20px; height: 20px; background: #eab308; border-radius: 4px;"></span> Sedang</span>
        <span style="display: flex; align-items: center; gap: 0.25rem;"><span style="width: 20px; height: 20px; background: #f97316; border-radius: 4px;"></span> Ramai</span>
        <span style="display: flex; align-items: center; gap: 0.25rem;"><span style="width: 20px; height: 20px; background: #ef4444; border-radius: 4px;"></span> Sangat Ramai</span>
    </div>
    """, unsafe_allow_html=True)


def render_crowd_prediction_page():
    """Full crowd prediction page."""
    try:
        from services.analytics.tracker import track_page
        track_page("crowd")
    except Exception:
        pass
    inject_css(HERO_CSS, CARD_CSS, AI_CARD_CSS)

    if not st.session_state.get("crowd_prediction_xp_awarded"):
        add_xp_safe(10, "Mengecek prediksi keramaian")
        st.session_state.crowd_prediction_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1>👥 Prediksi Keramaian</h1>
            <div class="subtitle">Prediksi tingkat keramaian Masjidil Haram & Masjid Nabawi</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Location selector
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🕋 Masjidil Haram", use_container_width=True, type="primary"):
            st.session_state.crowd_location = "makkah"
    
    with col2:
        if st.button("🕌 Masjid Nabawi", use_container_width=True):
            st.session_state.crowd_location = "madinah"
    
    location = st.session_state.get("crowd_location", "makkah")
    
    st.divider()
    
    # Current status
    render_crowd_widget(location, compact=False)
    
    st.divider()
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📈 24 Jam", "🗓️ Mingguan"])
    
    with tab1:
        render_24h_forecast(location)
    
    with tab2:
        render_weekly_heatmap(location)
    
    # Tips
    st.divider()
    st.markdown("### 💡 Tips Menghindari Keramaian")
    
    tips = [
        ("🌅 Setelah Subuh", "Waktu paling sepi, ideal untuk thawaf dengan khusyuk"),
        ("🌙 Tengah Malam", "Sepi tapi pastikan stamina cukup"),
        ("📅 Senin-Rabu", "Hari kerja biasanya lebih lengang"),
        ("🚫 Hindari Jumat", "Sholat Jum'at menyebabkan keramaian puncak"),
    ]
    
    cols = st.columns(2)
    for i, (title, desc) in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background: #1a1a1a; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;">
                <div style="color: #d4af37; font-weight: bold;">{title}</div>
                <div style="color: #b0b0b0; font-size: 0.85rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🤖 Tips Menghindari Keramaian", key="crowd_ai_tips"):
        with st.spinner("Menganalisis..."):
            tips = ai_complete(
                "Berikan 4 tips praktis menghindari keramaian saat umrah di Masjidil Haram dan Masjid Nabawi. "
                "Termasuk waktu terbaik untuk tawaf dan sai. Bahasa Indonesia.",
                system_prompt="Kamu adalah pemandu umrah berpengalaman.",
                max_tokens=400,
            )
            if tips:
                st.markdown(f'''
                    <div class="ai-card" role="status" aria-live="polite">
                        <h4>🤖 Tips AI Menghindari Keramaian</h4>
                        <p>{tips}</p>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("AI tidak tersedia saat ini")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "CrowdPredictor",
    "render_crowd_widget",
    "render_24h_forecast",
    "render_weekly_heatmap",
    "render_crowd_prediction_page",
]
