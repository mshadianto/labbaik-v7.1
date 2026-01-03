-- LABBAIK Smart Planner - Analytics Schema
-- ==========================================
-- Run: psql $DATABASE_URL < sql/analytics_schema.sql

-- Analytics Events Table
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255) NOT NULL,
    event_timestamp TIMESTAMP DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(100),
    event_action VARCHAR(255),
    event_label VARCHAR(255),
    page_name VARCHAR(100),
    referrer VARCHAR(255),
    user_agent TEXT,
    ip_address INET,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_events(event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_session ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_page ON analytics_events(page_name);
CREATE INDEX IF NOT EXISTS idx_analytics_category ON analytics_events(event_category);

-- User Sessions Table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    pages_visited INTEGER DEFAULT 0,
    actions_taken INTEGER DEFAULT 0,
    converted BOOLEAN DEFAULT FALSE,
    conversion_type VARCHAR(100),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    location VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON user_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id);

-- Daily Metrics Aggregation (for faster dashboard queries)
CREATE TABLE IF NOT EXISTS daily_metrics (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    dau INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    avg_session_duration FLOAT,
    total_page_views INTEGER DEFAULT 0,
    smart_prep_views INTEGER DEFAULT 0,
    smart_savings_views INTEGER DEFAULT 0,
    smart_journey_views INTEGER DEFAULT 0,
    smart_budget_uses INTEGER DEFAULT 0,
    umrah_bareng_views INTEGER DEFAULT 0,
    umrah_bareng_conversions INTEGER DEFAULT 0,
    smart_nudge_shows INTEGER DEFAULT 0,
    smart_nudge_clicks INTEGER DEFAULT 0,
    premium_conversions INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date DESC);

-- Function to update daily metrics (run via cron or trigger)
CREATE OR REPLACE FUNCTION update_daily_metrics(target_date DATE DEFAULT CURRENT_DATE)
RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_metrics (
        date, dau, total_sessions, total_page_views,
        smart_prep_views, smart_savings_views, smart_journey_views,
        smart_budget_uses, umrah_bareng_views,
        smart_nudge_shows, smart_nudge_clicks
    )
    SELECT
        target_date,
        COUNT(DISTINCT user_id),
        COUNT(DISTINCT session_id),
        COUNT(*) FILTER (WHERE event_type = 'page_view'),
        COUNT(*) FILTER (WHERE page_name IN ('checklist', 'umrah_mandiri', 'manasik')),
        COUNT(*) FILTER (WHERE page_name IN ('simulator', 'umrah_bareng', 'price_comparison', 'booking')),
        COUNT(*) FILTER (WHERE page_name IN ('chat', 'crowd', 'doa', 'tracking')),
        COUNT(*) FILTER (WHERE page_name = 'simulator'),
        COUNT(*) FILTER (WHERE page_name = 'umrah_bareng'),
        COUNT(*) FILTER (WHERE event_action = 'nudge_displayed'),
        COUNT(*) FILTER (WHERE event_action = 'nudge_clicked')
    FROM analytics_events
    WHERE DATE(event_timestamp) = target_date
    ON CONFLICT (date) DO UPDATE SET
        dau = EXCLUDED.dau,
        total_sessions = EXCLUDED.total_sessions,
        total_page_views = EXCLUDED.total_page_views,
        smart_prep_views = EXCLUDED.smart_prep_views,
        smart_savings_views = EXCLUDED.smart_savings_views,
        smart_journey_views = EXCLUDED.smart_journey_views,
        smart_budget_uses = EXCLUDED.smart_budget_uses,
        umrah_bareng_views = EXCLUDED.umrah_bareng_views,
        smart_nudge_shows = EXCLUDED.smart_nudge_shows,
        smart_nudge_clicks = EXCLUDED.smart_nudge_clicks,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
-- GRANT ALL ON analytics_events TO postgres;
-- GRANT ALL ON user_sessions TO postgres;
-- GRANT ALL ON daily_metrics TO postgres;
