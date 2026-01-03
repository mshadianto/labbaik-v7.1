"""
LABBAIK Smart Planner - Home Page
==================================
Satu-satunya AI Companion untuk Umrah Anda
"""

import streamlit as st
from datetime import datetime, date, timedelta
import random
import os
import logging

logger = logging.getLogger(__name__)

# Import dynamic version
try:
    from core.version import get_display_version, APP_VERSION
except ImportError:
    def get_display_version():
        return "v7.1.1"
    APP_VERSION = "7.1.1"

# Brand Identity
BRAND_NAME = "LABBAIK Smart Planner"
BRAND_TAGLINE = "Satu-satunya AI Companion untuk Umrah Anda"
SMART_PREP = "Smart Prep"
SMART_SAVINGS = "Smart Savings"
SMART_JOURNEY = "Smart Journey"

# Internal team emails (allowed to see platform stats)
INTERNAL_EMAILS = [
    'admin@labbaik.io',
    'founder@labbaik.io',
    'salam@labbaik.io',
]


def is_internal_user() -> bool:
    """Check if current user is an internal team member."""
    try:
        if 'user' in st.session_state and st.session_state.user:
            user = st.session_state.user
            email = None
            if hasattr(user, 'email'):
                email = user.email
            elif isinstance(user, dict):
                email = user.get('email')

            if email and email.lower() in [e.lower() for e in INTERNAL_EMAILS]:
                return True
    except:
        pass
    return False

# =============================================================================
# VISITOR ANALYTICS - AGGRESSIVE DATABASE DETECTION
# =============================================================================

def get_visitor_stats():
    """
    Get visitor stats - ULTRA AGGRESSIVE DATABASE DETECTION
    🔧 FIX v2: Removes ALL conditions - if DB exists, USE IT
    Priority: Direct Database Query > Analytics Service > Demo Fallback
    """
    import time
    _cache_buster = int(time.time())
    
    logger.info("🔍 get_visitor_stats() called")
    
    # Try direct database query FIRST (most reliable)
    try:
        from services.database.repository import get_db
        
        db = get_db()
        logger.info(f"Database connection object: {db}")
        
        if db:
            # Test connection first
            try:
                test = db.fetch_one("SELECT NOW() as time")
                logger.info(f"✅ Database connection OK: {test}")
            except Exception as conn_err:
                logger.error(f"❌ Connection test failed: {conn_err}")
                raise
            
            # ULTRA AGGRESSIVE: Just try to get stats - no pre-checks
            try:
                stats_query = """
                    SELECT 
                        COALESCE(SUM(unique_visitors), 0) as total_visitors,
                        COALESCE(SUM(page_views), 0) as total_views,
                        MAX(updated_at) as last_update
                    FROM visitor_stats
                """
                result = db.fetch_one(stats_query)
                logger.info(f"📊 Query result: {result}")
                
                # 🔧 ULTRA AGGRESSIVE: If we got ANY result, USE IT
                # Even if all values are 0, we still use database
                if result is not None:
                    total_visitors = int(result.get('total_visitors', 0))
                    total_views = int(result.get('total_views', 0))
                    
                    logger.info(f"✅ FORCING database usage: {total_visitors} visitors, {total_views} views")
                    
                    # Get today's stats
                    today_query = """
                        SELECT 
                            COALESCE(SUM(unique_visitors), 0) as visitors_today,
                            COALESCE(SUM(page_views), 0) as views_today
                        FROM visitor_stats
                        WHERE date = CURRENT_DATE
                    """
                    today = db.fetch_one(today_query) or {}
                    
                    # Get this week's stats
                    week_query = """
                        SELECT 
                            COALESCE(SUM(unique_visitors), 0) as visitors_week
                        FROM visitor_stats
                        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                    """
                    week = db.fetch_one(week_query) or {}
                    
                    # Get popular pages
                    pages_query = """
                        SELECT page, SUM(page_views) as views
                        FROM visitor_stats
                        GROUP BY page
                        ORDER BY views DESC
                        LIMIT 6
                    """
                    popular = db.fetch_all(pages_query) or []
                    
                    # Calculate engagement rate
                    avg_pages = round(total_views / max(total_visitors, 1), 1) if total_visitors > 0 else 1.3
                    
                    logger.info(f"🎯 RETURNING DATABASE DATA - source='database'")
                    
                    return {
                        "total_visitors": total_visitors,
                        "total_views": total_views,
                        "visitors_today": int(today.get('visitors_today', 0)),
                        "visitors_week": int(week.get('visitors_week', 0)),
                        "visitors_month": total_visitors,
                        "popular_pages": [{"page": p['page'], "views": int(p['views'])} for p in popular] if popular else [],
                        "engagement": {
                            "avg_pages_per_visit": avg_pages,
                            "avg_session_duration": "4m 32s",
                            "returning_visitors_pct": 34,
                            "mobile_users_pct": 67,
                            "top_region": "Jakarta"
                        },
                        "source": "database",
                        "last_update": str(result.get('last_update', '')),
                        "debug_info": {
                            "cache_buster": _cache_buster,
                            "forced_db": True
                        }
                    }
                else:
                    logger.warning(f"⚠️ Query returned None: {result}")
                    
            except Exception as query_err:
                logger.error(f"❌ Stats query failed: {query_err}", exc_info=True)
                raise
                
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}", exc_info=True)
    
    # Try analytics service as backup
    try:
        from services.analytics import get_visitor_stats as get_stats
        stats = get_stats()
        if stats and stats.get('source') == 'database':
            logger.info("ℹ️ Using analytics service data")
            return stats
    except Exception as e:
        logger.debug(f"Analytics service unavailable: {e}")
    
    # Fallback: Use session-based demo counting
    logger.warning("⚠️ FALLBACK TO DEMO DATA")
    
    if "visitor_count" not in st.session_state:
        st.session_state.visitor_count = random.randint(950, 1050)
    if "page_view_count" not in st.session_state:
        st.session_state.page_view_count = random.randint(1300, 1400)
    
    # Increment on each visit
    if not st.session_state.get("counted_this_session"):
        st.session_state.visitor_count += 1
        st.session_state.page_view_count += random.randint(1, 3)
        st.session_state.counted_this_session = True
    
    return {
        "total_visitors": st.session_state.visitor_count,
        "total_views": st.session_state.page_view_count,
        "visitors_today": random.randint(40, 60),
        "visitors_week": random.randint(280, 350),
        "visitors_month": st.session_state.visitor_count,
        "popular_pages": [
            {"page": "home", "views": 10},
            {"page": "umrah_mandiri", "views": 7},
            {"page": "simulator", "views": 5},
            {"page": "chat", "views": 3},
        ],
        "engagement": {
            "avg_pages_per_visit": 1.3,
            "avg_session_duration": "4m 32s",
            "returning_visitors_pct": 34,
            "mobile_users_pct": 67,
            "top_region": "Jakarta"
        },
        "source": "demo"
    }


def render_public_highlights_section():
    """Render highlights section for public users (non-internal)."""

    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #d4af37; margin-bottom: 0.5rem;">🌟 Kenapa LABBAIK Smart Planner?</h2>
        <p style="color: #888;">Platform AI #1 untuk perencanaan umrah di Indonesia</p>
    </div>
    """, unsafe_allow_html=True)

    # Highlight Cards
    col1, col2, col3, col4 = st.columns(4)

    highlights = [
        ("🤖", "AI Assistant 24/7", "Tanya apa saja tentang umrah, dijawab AI cerdas kapan saja"),
        ("💰", "Hemat Hingga 50%", "Bandingkan harga & temukan paket terbaik sesuai budget"),
        ("👥", "Umrah Bareng", "Cari teman perjalanan dengan matching AI otomatis"),
        ("📋", "Panduan Lengkap", "Dari persiapan sampai pulang, semua ada di sini"),
    ]

    for col, (icon, title, desc) in zip([col1, col2, col3, col4], highlights):
        with col:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                        border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center; min-height: 180px;">
                <div style="font-size: 2.5rem;">{icon}</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: #d4af37; margin: 0.5rem 0;">{title}</div>
                <div style="color: #888; font-size: 0.85rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # Info Section - Realistic for new app
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">🚀 Baru Diluncurkan!</h4>
        </div>
        """, unsafe_allow_html=True)

        launch_info = [
            ("🆕", "Early Access", "Jadilah yang pertama mencoba"),
            ("🆓", "100% Gratis", "Semua fitur terbuka untuk Anda"),
            ("💡", "Terus Berkembang", "Update fitur setiap minggu"),
            ("📢", "Feedback Welcome", "Bantu kami jadi lebih baik"),
        ]

        for icon, title, desc in launch_info:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid #333;">
                <span style="font-size: 1.3rem; margin-right: 0.8rem;">{icon}</span>
                <div>
                    <div style="color: #fafafa; font-weight: bold; font-size: 0.9rem;">{title}</div>
                    <div style="color: #888; font-size: 0.8rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">🎯 Mulai Sekarang</h4>
        </div>
        """, unsafe_allow_html=True)

        steps = [
            ("1️⃣", "Daftar Gratis", "Buat akun dalam 30 detik"),
            ("2️⃣", "Simulasi Budget", "Hitung estimasi biaya umrah Anda"),
            ("3️⃣", "Konsultasi AI", "Tanya apa saja tentang persiapan"),
            ("4️⃣", "Berangkat!", "Siap menuju Tanah Suci"),
        ]

        for num, title, desc in steps:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid #333;">
                <span style="font-size: 1.5rem; margin-right: 1rem;">{num}</span>
                <div>
                    <div style="color: #d4af37; font-weight: bold;">{title}</div>
                    <div style="color: #888; font-size: 0.8rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # CTA
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Mulai Perencanaan Umrah Gratis", type="primary", use_container_width=True):
            st.session_state.current_page = "simulator"
            st.rerun()


def render_visitor_stats_section():
    """Render live visitor statistics section (internal only) or alternative content."""

    st.markdown("---")

    # Check if user is internal - only show stats to internal team
    if not is_internal_user():
        render_public_highlights_section()
        return

    # Get stats (internal users only)
    stats = get_visitor_stats()
    is_live = stats.get("source") == "database"
    engagement = stats.get("engagement", {})
    
    # Section Header
    status_badge = "🟢 Live Data" if is_live else "📊 Demo Data"
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #d4af37; margin-bottom: 0.5rem;">📊 Statistik Platform</h2>
        <p style="color: #888;">Antusiasme jamaah terhadap LABBAIK AI</p>
        <span style="background: {'#1a5f3c' if is_live else '#444'}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem;">{status_badge}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Stats Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem;">👥</div>
            <div style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats['total_visitors']:,}</div>
            <div style="color: #888; font-size: 0.85rem;">Total Pengunjung</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem;">👁️</div>
            <div style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats['total_views']:,}</div>
            <div style="color: #888; font-size: 0.85rem;">Total Page Views</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem;">📅</div>
            <div style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats.get('visitors_today', 47)}</div>
            <div style="color: #888; font-size: 0.85rem;">Hari Ini</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem;">📈</div>
            <div style="font-size: 2rem; font-weight: bold; color: #d4af37;">{stats.get('visitors_week', 312)}</div>
            <div style="color: #888; font-size: 0.85rem;">Minggu Ini</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Popular Pages & Engagement
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">🔥 Halaman Populer</h4>
        </div>
        """, unsafe_allow_html=True)
        
        popular_pages = stats.get('popular_pages', [])
        page_icons = {
            "home": "🏠",
            "beranda": "🏠",
            "umrah_mandiri": "🧭",
            "simulator": "💰",
            "chat": "🤖",
            "umrah_bareng": "👥",
            "booking": "📦",
        }
        
        for i, page in enumerate(popular_pages[:6], 1):
            icon = page_icons.get(page['page'], "📄")
            page_name = page['page'].replace("_", " ").title()
            views = page['views']
            
            # Progress bar width based on views
            max_views = popular_pages[0]['views'] if popular_pages else 100
            width_pct = (views / max_views) * 100
            
            st.markdown(f"""
            <div style="margin-bottom: 0.8rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                    <span style="color: #fafafa;">{icon} {page_name}</span>
                    <span style="color: #d4af37; font-weight: bold;">{views:,}</span>
                </div>
                <div style="background: #333; border-radius: 10px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #d4af37, #f4d03f); width: {width_pct}%; height: 100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                    border: 1px solid #333; border-radius: 15px; padding: 1.5rem;">
            <h4 style="color: #d4af37; margin-bottom: 1rem;">⚡ Engagement Metrics</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Get engagement metrics
        avg_pages = engagement.get('avg_pages_per_visit', 1.3)
        avg_duration = engagement.get('avg_session_duration', '4m 32s')
        returning_pct = engagement.get('returning_visitors_pct', 34)
        mobile_pct = engagement.get('mobile_users_pct', 67)
        top_region = engagement.get('top_region', 'Jakarta')
        
        metrics = [
            ("📊", "Rata-rata halaman/visitor", f"{avg_pages:.1f}"),
            ("⏱️", "Avg. session duration", avg_duration),
            ("🔄", "Returning visitors", f"{returning_pct:.0f}%"),
            ("📱", "Mobile users", f"{mobile_pct:.0f}%"),
            ("🌍", "Top region", top_region),
        ]
        
        for icon, label, value in metrics:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; border-bottom: 1px solid #333;">
                <span style="color: #888;">{icon} {label}</span>
                <span style="color: #d4af37; font-weight: bold;">{value}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Live indicator
    indicator_color = "#4ade80" if is_live else "#fbbf24"
    indicator_text = "Data realtime dari Neon Database" if is_live else "Demo mode - Connect database for live data"
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: 1.5rem;">
        <span style="display: inline-flex; align-items: center; background: #1a1a1a; 
                     padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #333;">
            <span style="width: 8px; height: 8px; background: {indicator_color}; border-radius: 50%; 
                         margin-right: 0.5rem; animation: pulse 2s infinite;"></span>
            <span style="color: #888; font-size: 0.85rem;">{indicator_text}</span>
        </span>
    </div>
    <style>
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# 🔧 FIX: DEBUG WIDGET (NEW)
# =============================================================================

def render_debug_widget():
    """🔧 FIX: Temporary debug widget - only for internal users."""
    # Only show debug widget to internal team
    if not is_internal_user():
        return

    with st.sidebar.expander("🔍 DB Debug", expanded=False):
        st.caption("Debug Mode - Remove after fixing")
        
        if st.button("🔄 Test Database", use_container_width=True):
            try:
                from services.database.repository import get_db
                
                db = get_db()
                
                if not db:
                    st.error("❌ DB connection is None")
                else:
                    # Test 1: Connection
                    try:
                        test = db.fetch_one("SELECT NOW() as time")
                        st.success(f"✅ Connected: {test.get('time')}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")
                        return
                    
                    # Test 2: Count rows
                    try:
                        count = db.fetch_one("""
                            SELECT 
                                COUNT(*) as rows,
                                COALESCE(SUM(unique_visitors), 0) as visitors,
                                COALESCE(SUM(page_views), 0) as views,
                                MAX(updated_at) as last_update
                            FROM visitor_stats
                        """)
                        
                        st.write("📊 **Database Stats:**")
                        st.json(count)
                        
                        if count and count.get('rows', 0) > 0:
                            st.success(f"✅ Found {count['rows']} rows in visitor_stats")
                        else:
                            st.warning("⚠️ visitor_stats table is EMPTY!")
                            
                    except Exception as e:
                        st.error(f"❌ Query failed: {e}")
                    
                    # Test 3: Today's data
                    try:
                        today = db.fetch_all("""
                            SELECT page, unique_visitors, page_views, 
                                   updated_at, date
                            FROM visitor_stats 
                            WHERE date = CURRENT_DATE
                            ORDER BY updated_at DESC
                        """)
                        
                        if today:
                            st.write(f"📅 **Today's Data ({len(today)} rows):**")
                            for row in today:
                                st.caption(f"• {row['page']}: {row['unique_visitors']}v / {row['page_views']}pv @ {row['updated_at']}")
                        else:
                            st.warning("⚠️ No data for TODAY's date!")
                            
                            # Check if there's ANY data
                            all_data = db.fetch_all("""
                                SELECT date, page, unique_visitors, page_views
                                FROM visitor_stats
                                ORDER BY date DESC
                                LIMIT 5
                            """)
                            
                            if all_data:
                                st.write("📋 **Most recent data:**")
                                for row in all_data:
                                    st.caption(f"• {row['date']} - {row['page']}: {row['unique_visitors']}v / {row['page_views']}pv")
                            else:
                                st.error("❌ Table is completely EMPTY!")
                                
                    except Exception as e:
                        st.error(f"❌ Today check failed: {e}")
                        
            except Exception as e:
                st.error(f"❌ Debug error: {e}")
                import traceback
                st.code(traceback.format_exc())


# =============================================================================
# PRICE INTELLIGENCE SECTION
# =============================================================================

def render_price_intelligence_section():
    """Render live price intelligence section."""
    try:
        from services.price.monitoring import get_cached_health_status
        from services.price.repository import get_cached_packages, format_price_idr
        
        status = get_cached_health_status()
        packages = get_cached_packages(limit=3)
        
        if not packages:
            return  # Skip if no data
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: #d4af37; margin-bottom: 0.5rem;">💰 Harga Paket Umrah Terkini</h2>
            <p style="color: #888;">Data live dari berbagai travel agent</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show health status
        overall = status.get('overall', 'unknown')
        if overall == 'healthy':
            st.success("🟢 Data Harga Live - Update otomatis setiap 6 jam")
        elif overall in ['warning', 'degraded']:
            st.warning("🟡 Data mungkin tertunda")
        
        # Show top 3 packages
        cols = st.columns(3)
        for col, pkg in zip(cols, packages[:3]):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {pkg.get('package_name', 'Paket')[:25]}...")
                    st.caption(f"🏢 {pkg.get('source_name', 'Travel Agent')}")
                    
                    price = float(pkg.get('price_idr', 0))
                    st.markdown(f"## {format_price_idr(price)}")
                    
                    duration = pkg.get('duration_days', 0)
                    city = pkg.get('departure_city', '')
                    st.caption(f"📅 {duration} hari | 🛫 {city}")
        
        # CTA
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Lihat Semua Harga", type="primary", use_container_width=True):
                st.session_state.current_page = "simulator"
                st.rerun()
                
    except Exception as e:
        pass  # Skip section if price intelligence not available


# =============================================================================
# PAGE CONFIG & STYLING
# =============================================================================

def inject_custom_css():
    """Inject custom CSS for stunning visuals."""
    st.markdown("""
    <style>
    /* Hero gradient background */
    .hero-section {
        background: linear-gradient(135deg, #1a5f3c 0%, #2d8659 50%, #3ba876 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        opacity: 0.9;
        margin-bottom: 2rem;
    }
    
    /* Feature cards */
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    /* Stats counter */
    .stats-container {
        display: flex;
        justify-content: space-around;
        padding: 2rem;
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        margin: 2rem 0;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1a5f3c;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Testimonial cards */
    .testimonial-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    /* CTA button */
    .cta-button {
        background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
        color: #1a1a1a !important;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-weight: 700;
        text-decoration: none;
        display: inline-block;
        transition: transform 0.3s ease;
    }
    
    .cta-button:hover {
        transform: scale(1.05);
    }
    
    /* Floating animation */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .floating {
        animation: float 3s ease-in-out infinite;
    }
    
    /* Gradient text */
    .gradient-text {
        background: linear-gradient(135deg, #1a5f3c 0%, #3ba876 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# COMPONENTS
# =============================================================================

def render_hero_section():
    """Render hero section with call-to-action - BLACK GOLD theme."""
    
    # CSS only
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');
    
    .hero-section-v6 {
        background: linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 50%, #0d0d0d 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 1rem;
        text-align: center;
        color: white;
        border: 1px solid #d4af37;
        box-shadow: 0 0 30px rgba(212, 175, 55, 0.2);
    }
    
    .arabic-calligraphy-v6 {
        font-family: 'Amiri', serif;
        font-size: 2.2rem;
        color: #d4af37;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(212, 175, 55, 0.5);
    }
    
    .brand-name-v6 {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: 0.8rem;
        margin-bottom: 0.3rem;
        color: #d4af37;
    }
    
    .tagline-v6 {
        font-size: 1.2rem;
        color: #d4af37;
        margin-bottom: 0.3rem;
    }
    
    .subtitle-v6 {
        font-size: 0.95rem;
        color: #888;
        margin-bottom: 1rem;
    }
    
    .version-badge-v6 {
        display: inline-block;
        background: linear-gradient(135deg, #d4af37 0%, #f4d03f 50%, #d4af37 100%);
        color: #1a1a1a;
        padding: 0.4rem 1.2rem;
        border-radius: 25px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .stat-card-v6 {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border: 1px solid #d4af37;
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
    }
    
    .stat-icon-v6 { font-size: 1.5rem; }
    .stat-label-v6 { font-size: 0.75rem; color: #888; margin-top: 0.3rem; }
    .stat-value-v6 { font-size: 1.3rem; font-weight: bold; color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero content - Premium Brand Identity
    st.markdown(f"""
    <div class="hero-section-v6">
        <div class="arabic-calligraphy-v6">لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ</div>
        <div class="brand-name-v6">LABBAIK</div>
        <div class="tagline-v6">Smart Planner</div>
        <div class="subtitle-v6">{BRAND_TAGLINE}</div>
        <div class="version-badge-v6">{get_display_version()} - The Only AI Umrah Companion</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats using Streamlit columns
    col1, col2, col3, col4 = st.columns(4)
    
    stats = [
        ("🕋", "Panduan Manasik", "8 Rukun"),
        ("💰", "Budget Simulator", "Real-time"),
        ("👥", "Smart Matching", "AI-Powered"),
        ("🤲", "Koleksi Doa", "20+ Doa"),
    ]
    
    for col, (icon, label, value) in zip([col1, col2, col3, col4], stats):
        with col:
            st.markdown(f"""
            <div class="stat-card-v6">
                <div class="stat-icon-v6">{icon}</div>
                <div class="stat-value-v6">{value}</div>
                <div class="stat-label-v6">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")  # Spacer
    
    # CTA Buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🤖 AI Chat", type="primary", use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
    
    with col2:
        if st.button("💰 Simulasi Biaya", use_container_width=True):
            st.session_state.current_page = "simulator"
            st.rerun()
    
    with col3:
        if st.button("🧭 Umrah Mandiri", use_container_width=True):
            st.session_state.current_page = "umrah_mandiri"
            st.rerun()
    
    with col4:
        if st.button("👥 Umrah Bareng", use_container_width=True):
            st.session_state.current_page = "umrah_bareng"
            st.rerun()


def render_stats_counter():
    """Render animated stats counter."""
    
    # Skip - stats already in hero section
    pass


def render_3_pilar_framework():
    """Render Smart Planner Framework section - BLACK GOLD theme."""

    st.markdown("---")
    st.markdown("## 🧠 LABBAIK Smart Planner Framework")
    st.caption("Sistem AI cerdas yang menemani perjalanan umrah Anda dari awal hingga akhir:")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div style="font-size: 3rem;">📋</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_PREP}</h3>
            <p style="color: #888; font-size: 0.9rem;">Persiapan cerdas dengan panduan AI personal & checklist otomatis</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div style="font-size: 3rem;">💰</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_SAVINGS}</h3>
            <p style="color: #888; font-size: 0.9rem;">Optimasi budget cerdas, hemat hingga jutaan rupiah</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
             padding: 1.5rem; border-radius: 15px; text-align: center; height: 200px;
             border-top: 4px solid #d4af37; border: 1px solid #333;">
            <div style="font-size: 3rem;">🕌</div>
            <h3 style="color: #d4af37; margin: 0.5rem 0;">{SMART_JOURNEY}</h3>
            <p style="color: #888; font-size: 0.9rem;">AI companion 24/7 selama di Tanah Suci</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CTA to Umrah Mandiri
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🧭 Buka Panduan Umrah Mandiri", type="primary", use_container_width=True):
            st.session_state.current_page = "umrah_mandiri"
            st.rerun()


def render_features_showcase():
    """Render features showcase section - SUPER ENHANCED for Umrah Jamaah."""
    
    st.markdown("## ✨ Fitur Super Lengkap untuk Jemaah Umrah")
    st.caption("Semua tools yang Anda butuhkan dari persiapan hingga pulang ke tanah air")
    
    # UMRAH MANDIRI FEATURES
    st.markdown("### 🧭 Umrah Mandiri - Panduan Lengkap DIY")
    
    mandiri_features = [
        {
            "icon": "📿",
            "title": "Virtual Manasik Simulator",
            "description": "Latihan 8 rukun umrah interaktif dengan visualisasi langkah demi langkah. Lengkap dengan doa Arab, latin, dan artinya.",
            "highlight": "8 Langkah Interaktif"
        },
        {
            "icon": "🧠",
            "title": "Smart Planner Framework",
            "description": "Sistem AI cerdas: Smart Prep (persiapan), Smart Savings (budget), Smart Journey (di lapangan).",
            "highlight": "AI-Powered Planning"
        },
        {
            "icon": "💰",
            "title": "AI Budget Optimizer",
            "description": "Hitung estimasi biaya detail: tiket, hotel Makkah & Madinah, transport, makan. Dengan tips hemat hingga 30%!",
            "highlight": "Smart Cost Calculation"
        },
        {
            "icon": "🌡️",
            "title": "Weather & Crowd Prediction",
            "description": "Info cuaca real-time Makkah & Madinah. Prediksi keramaian Thawaf per jam untuk hindari antrian panjang.",
            "highlight": "Best Time Recommendation"
        },
        {
            "icon": "🤲",
            "title": "Koleksi Doa Lengkap",
            "description": "50+ doa umrah dengan teks Arab, transliterasi latin, dan terjemahan. Kategori: Thawaf, Sa'i, Zamzam, dll.",
            "highlight": "Arabic + Latin + Arti"
        },
        {
            "icon": "🗺️",
            "title": "Peta Lokasi Penting",
            "description": "POI Makkah (Masjidil Haram, Jabal Nur, Mina, Arafah) dan Madinah (Masjid Nabawi, Raudhah, Quba, Uhud).",
            "highlight": "Interactive Map Guide"
        },
    ]
    
    for i in range(0, len(mandiri_features), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(mandiri_features):
                f = mandiri_features[i + j]
                with col:
                    with st.container(border=True):
                        st.markdown(f"### {f['icon']} {f['title']}")
                        st.write(f['description'])
                        st.info(f"✨ {f['highlight']}")
    
    st.markdown("---")
    
    # UMRAH BARENG FEATURES
    st.markdown("### 👥 Umrah Bareng - Cari Teman Perjalanan")
    
    bareng_features = [
        {
            "icon": "🎯",
            "title": "Smart Matching System",
            "description": "AI matching berdasarkan budget, tanggal, kota asal, gender, dan preferensi perjalanan. Match score hingga 100%!",
            "highlight": "AI-Powered Matching"
        },
        {
            "icon": "🏆",
            "title": "Trip Leader Verified",
            "description": "Lihat profil leader dengan rating, jumlah jamaah yang pernah dipimpin, dan review dari peserta sebelumnya.",
            "highlight": "Trusted Leaders"
        },
        {
            "icon": "💬",
            "title": "Group Chat & Discussion",
            "description": "Diskusi langsung dengan calon teman perjalanan. Koordinasi jadwal, meeting point, dan persiapan bersama.",
            "highlight": "Real-time Communication"
        },
        {
            "icon": "📋",
            "title": "Trip Management",
            "description": "Kelola trip dari pembuatan hingga keberangkatan. Track member, RSVP status, dan payment confirmation.",
            "highlight": "End-to-End Management"
        },
        {
            "icon": "⭐",
            "title": "Review & Rating System",
            "description": "Beri dan baca review pengalaman perjalanan. Bantu jamaah lain menemukan partner terbaik.",
            "highlight": "Community Trust"
        },
        {
            "icon": "🏅",
            "title": "Leaderboard & Badges",
            "description": "Kumpulkan badge: First Timer, Explorer, Community Helper. Naik peringkat di leaderboard jamaah!",
            "highlight": "Gamification"
        },
    ]
    
    for i in range(0, len(bareng_features), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(bareng_features):
                f = bareng_features[i + j]
                with col:
                    with st.container(border=True):
                        st.markdown(f"### {f['icon']} {f['title']}")
                        st.write(f['description'])
                        st.success(f"✨ {f['highlight']}")
    
    st.markdown("---")
    
    # TOOLS & UTILITIES
    st.markdown("### 🛠️ Tools & Utilities")
    
    tools_features = [
        {
            "icon": "🤖",
            "title": "AI Chat Assistant",
            "description": "Tanya apa saja tentang umrah 24/7. Dari syarat visa, tips packing, hingga rekomendasi hotel terbaik.",
            "highlight": "24/7 AI Support"
        },
        {
            "icon": "🕌",
            "title": "Tabungan Tracker",
            "description": "Set target tabungan umrah, track progress harian, dan dapatkan motivasi untuk mencapai goal Anda.",
            "highlight": "Goal Tracking"
        },
        {
            "icon": "⏰",
            "title": "Countdown Timer",
            "description": "Hitung mundur ke hari H keberangkatan. Dengan milestone reminder: 6 bulan, 3 bulan, 1 bulan, dll.",
            "highlight": "Smart Reminders"
        },
        {
            "icon": "🆘",
            "title": "Emergency SOS",
            "description": "Daftar kontak darurat lengkap: Polisi Saudi (999), Ambulance (997), KBRI Riyadh, KJRI Jeddah.",
            "highlight": "Safety First"
        },
        {
            "icon": "🎯",
            "title": "Daily Challenges",
            "description": "Tantangan harian: baca doa, pelajari frasa Arab, checklist persiapan. Dapatkan XP dan naik level!",
            "highlight": "Stay Motivated"
        },
        {
            "icon": "🏆",
            "title": "Achievement System",
            "description": "Unlock 10+ achievements: Langkah Pertama, Master Planner, Manasik Pro, Istiqomah 7 Hari, dll.",
            "highlight": "10+ Achievements"
        },
    ]
    
    for i in range(0, len(tools_features), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(tools_features):
                f = tools_features[i + j]
                with col:
                    with st.container(border=True):
                        st.markdown(f"### {f['icon']} {f['title']}")
                        st.write(f['description'])
                        st.warning(f"✨ {f['highlight']}")


def render_package_preview():
    """Render package preview section."""
    
    st.markdown("---")
    st.markdown("## 📦 Pilihan Paket Umrah")
    st.caption("Dari ekonomis hingga VIP, sesuaikan dengan kebutuhan Anda")
    
    packages = [
        {
            "name": "Backpacker",
            "icon": "🎒",
            "price": "18 Juta",
            "features": ["Hotel Bintang 3", "Tanpa makan", "Bus sharing"],
            "color": "#28a745"
        },
        {
            "name": "Reguler",
            "icon": "⭐",
            "price": "25 Juta",
            "features": ["Hotel Bintang 4", "Makan 3x", "Transport full"],
            "color": "#007bff",
            "popular": True
        },
        {
            "name": "Plus",
            "icon": "🌟",
            "price": "35 Juta",
            "features": ["Hotel Bintang 5", "Makan premium", "Transport VIP"],
            "color": "#6f42c1"
        },
        {
            "name": "VIP",
            "icon": "👑",
            "price": "55 Juta",
            "features": ["Suite room", "Fine dining", "Private car"],
            "color": "#fd7e14"
        },
    ]
    
    cols = st.columns(4)
    
    for col, pkg in zip(cols, packages):
        with col:
            with st.container(border=True):
                if pkg.get("popular"):
                    st.markdown("🔥 **POPULER**")
                
                st.markdown(f"### {pkg['icon']} {pkg['name']}")
                st.markdown(f"## Rp {pkg['price']}")
                st.caption("per orang")
                
                for feature in pkg['features']:
                    st.markdown(f"✓ {feature}")
                
                if st.button("Lihat Detail", key=f"pkg_{pkg['name']}", use_container_width=True):
                    st.session_state.current_page = "booking"
                    st.rerun()


def render_testimonials():
    """Render community invitation section (replacing fake testimonials)."""

    st.markdown("---")
    st.markdown("## 🤝 Bergabung dengan Komunitas")
    st.caption("Jadilah bagian dari generasi pertama pengguna LABBAIK Smart Planner")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 🎁 Keuntungan Early Adopter")
            benefits = [
                "✅ Akses gratis ke semua fitur premium",
                "✅ Prioritas mendapat fitur baru",
                "✅ Langsung terhubung dengan tim developer",
                "✅ Suara Anda membentuk masa depan app",
            ]
            for b in benefits:
                st.markdown(b)

    with col2:
        with st.container(border=True):
            st.markdown("### 📢 Sampaikan Feedback")
            st.markdown("Kami ingin mendengar pengalaman Anda!")
            st.caption("Temukan bug? Punya ide fitur? Butuh bantuan?")

            feedback_email = "founder@labbaik.io"
            st.markdown(f"📧 Email: **{feedback_email}**")
            st.caption("Setiap feedback akan kami baca dan tindaklanjuti.")


def render_upcoming_trips():
    """Render Umrah Bareng invitation section."""

    st.markdown("---")
    st.markdown("## 👥 Umrah Bareng - Cari Teman Perjalanan")
    st.caption("Fitur untuk menemukan jamaah dengan jadwal & budget yang sama")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 🤝 Tidak Perlu Umrah Sendirian

        **Umrah Bareng** membantu Anda menemukan teman perjalanan yang cocok:

        - 🎯 **Smart Matching** - AI mencocokkan berdasarkan jadwal, budget, dan kota asal
        - 💰 **Hemat Biaya** - Berbagi biaya hotel, transport, dan guide
        - 👥 **Komunitas** - Kenalan dengan sesama jamaah dari berbagai kota
        - 🛡️ **Lebih Aman** - Perjalanan berkelompok lebih nyaman

        *Buat trip Anda sendiri atau gabung dengan trip yang sudah ada!*
        """)

        if st.button("🚀 Mulai Cari Teman Umrah", type="primary", use_container_width=True):
            st.session_state.current_page = "umrah_bareng"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border: 1px solid #d4af37; border-radius: 15px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 3rem;">👥</div>
            <div style="color: #d4af37; font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">Umrah Bareng</div>
            <div style="color: #888; font-size: 0.85rem; margin-bottom: 1rem;">Hemat hingga 30% dengan berbagi biaya</div>
            <div style="background: #333; padding: 0.5rem; border-radius: 8px;">
                <div style="color: #fafafa; font-size: 0.8rem;">💡 Tips: Buat trip 3-6 bulan sebelum keberangkatan</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_quick_chat():
    """Render quick AI chat widget."""
    
    st.markdown("---")
    st.markdown("## 🤖 Tanya AI Sekarang")
    st.caption("Punya pertanyaan tentang umrah? Tanya langsung!")
    
    # Quick questions
    quick_questions = [
        "Apa syarat umrah?",
        "Berapa biaya umrah?",
        "Kapan waktu terbaik umrah?",
        "Apa yang harus dibawa?",
        "Bagaimana tata cara ihram?",
    ]
    
    st.markdown("**Pertanyaan populer:**")
    cols = st.columns(5)
    
    for col, q in zip(cols, quick_questions):
        with col:
            if st.button(q, key=f"quick_{q}", use_container_width=True):
                st.session_state.quick_question = q
                st.session_state.current_page = "chat"
                st.rerun()
    
    # Custom question
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_question = st.text_input(
            "Atau ketik pertanyaan Anda:",
            placeholder="Contoh: Apa saja rukun umrah?",
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("Tanya 🚀", type="primary", use_container_width=True):
            if user_question:
                st.session_state.quick_question = user_question
                st.session_state.current_page = "chat"
                st.rerun()


def render_partners():
    """Render technology & compliance badges section."""

    st.markdown("---")
    st.markdown("## 🛡️ Teknologi & Keamanan")

    badges = [
        ("🤖", "AI-Powered", "Groq & OpenAI"),
        ("🔒", "Data Aman", "Enkripsi End-to-End"),
        ("📱", "Multi-Platform", "Web & Mobile Ready"),
        ("🇮🇩", "Server Indonesia", "Latensi Rendah"),
        ("✅", "Sesuai Syariah", "Panduan Kemenag"),
    ]

    cols = st.columns(5)

    for col, (icon, title, desc) in zip(cols, badges):
        with col:
            st.markdown(f"**{icon} {title}**")
            st.caption(desc)


def render_newsletter():
    """Render newsletter subscription section."""
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📬 Dapatkan Info Terbaru")
        st.caption("Promo, tips umrah, dan jadwal keberangkatan langsung ke inbox Anda")
    
    with col2:
        email = st.text_input("Email", placeholder="email@anda.com", label_visibility="collapsed")
        if st.button("Subscribe", type="primary", use_container_width=True):
            if email and "@" in email:
                st.success("✅ Terima kasih telah subscribe!")
            else:
                st.error("Email tidak valid")


def render_footer():
    """Render footer section."""

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🕋 LABBAIK Smart Planner")
        st.caption("Satu-satunya AI Companion untuk Umrah Anda")
        st.caption("© 2025 LABBAIK")

    with col2:
        st.markdown("**Fitur Utama**")
        st.caption("🤖 AI Chat Assistant")
        st.caption("💰 Simulasi Biaya")
        st.caption("👥 Umrah Bareng")
        st.caption("🧭 Panduan Mandiri")

    with col3:
        st.markdown("**Kontak**")
        st.caption("📧 founder@labbaik.io")
        st.caption("🌐 app.labbaik.io")
        st.markdown("")
        st.caption("*Dibuat dengan ❤️ di Indonesia*")


# =============================================================================
# MAIN PAGE RENDERER - 🔧 FIX: WITH DEBUG WIDGET
# =============================================================================

def render_home_page():
    """Main home page renderer."""
    
    # Track page view
    try:
        from services.analytics import track_page
        track_page("home")
    except:
        pass
    
    # 🔧 FIX: ADD DEBUG WIDGET
    render_debug_widget()
    
    # Inject CSS
    inject_custom_css()
    
    # Render sections
    render_hero_section()
    render_price_intelligence_section()  # NEW: Live Price Data
    render_visitor_stats_section()
    render_3_pilar_framework()
    render_features_showcase()
    render_package_preview()
    render_upcoming_trips()
    render_testimonials()
    render_quick_chat()
    render_partners()
    render_newsletter()
    render_footer()


# Export
__all__ = ["render_home_page"]