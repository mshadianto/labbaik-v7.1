"""
Run Analytics Schema Migration to Supabase
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2 import sql

def get_database_url():
    """Get database URL from secrets or environment."""
    # Try streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            return st.secrets['DATABASE_URL']
    except:
        pass

    # Try environment variable
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url

    # Try reading from secrets.toml directly
    try:
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.streamlit', 'secrets.toml')
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL'):
                        # Extract URL from line like: DATABASE_URL = "postgresql://..."
                        url = line.split('=', 1)[1].strip().strip('"').strip("'")
                        return url
    except Exception as e:
        print(f"Could not read secrets.toml: {e}")

    return None

def run_migration():
    """Run the analytics schema migration."""
    print("=" * 60)
    print("LABBAIK Analytics Schema Migration")
    print("=" * 60)

    # Get database URL
    db_url = get_database_url()
    if not db_url:
        print("ERROR: DATABASE_URL not found!")
        print("Set it in .streamlit/secrets.toml or as environment variable")
        return False

    print(f"Connecting to database...")
    print(f"URL: {db_url[:50]}...")

    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        print("Connected successfully!")
        print()

        # Execute each statement individually
        statements = [
            # 0. Visitor Stats Table (required by existing tracker)
            ("visitor_stats table", """
                CREATE TABLE IF NOT EXISTS visitor_stats (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    page VARCHAR(100) NOT NULL,
                    unique_visitors INTEGER DEFAULT 0,
                    page_views INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(date, page)
                )
            """),
            # 0b. Page View Events Table (required by existing tracker)
            ("page_view_events table", """
                CREATE TABLE IF NOT EXISTS page_view_events (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    page VARCHAR(100) NOT NULL,
                    device_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """),
            # 0c. Visitor Sessions Table (required by existing tracker)
            ("visitor_sessions table", """
                CREATE TABLE IF NOT EXISTS visitor_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    first_page VARCHAR(100),
                    last_page VARCHAR(100),
                    page_count INTEGER DEFAULT 0,
                    device_type VARCHAR(50),
                    started_at TIMESTAMP DEFAULT NOW(),
                    last_activity TIMESTAMP DEFAULT NOW(),
                    duration_seconds INTEGER DEFAULT 0,
                    is_returning BOOLEAN DEFAULT FALSE
                )
            """),
            # 1. Analytics Events Table (user_id as INTEGER to match users table)
            ("analytics_events table", """
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
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
                )
            """),
            # 2. Analytics indexes
            ("analytics indexes", """
                CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_events(event_timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_id);
                CREATE INDEX IF NOT EXISTS idx_analytics_session ON analytics_events(session_id);
                CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_analytics_page ON analytics_events(page_name);
                CREATE INDEX IF NOT EXISTS idx_analytics_category ON analytics_events(event_category)
            """),
            # 3. User Sessions Table (user_id as INTEGER to match users table)
            ("user_sessions table", """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
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
                )
            """),
            # 4. Sessions indexes
            ("sessions indexes", """
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_started ON user_sessions(started_at DESC);
                CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id)
            """),
            # 5. Daily Metrics Table
            ("daily_metrics table", """
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
                )
            """),
            # 6. Daily metrics index
            ("daily_metrics index", """
                CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date DESC)
            """),
        ]

        for name, stmt in statements:
            try:
                print(f"Creating {name}...")
                cursor.execute(stmt)
                print(f"  [OK] Success")
            except Exception as e:
                if 'already exists' in str(e).lower():
                    print(f"  [SKIP] Already exists")
                else:
                    print(f"  [ERR] Error: {e}")

        # Verify tables were created
        print()
        print("Verifying tables...")

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('analytics_events', 'user_sessions', 'daily_metrics')
        """)

        tables = [row[0] for row in cursor.fetchall()]

        for table in ['analytics_events', 'user_sessions', 'daily_metrics']:
            if table in tables:
                print(f"  [OK] {table}")
            else:
                print(f"  [MISSING] {table}")

        cursor.close()
        conn.close()

        print()
        print("=" * 60)
        print("Migration completed!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
