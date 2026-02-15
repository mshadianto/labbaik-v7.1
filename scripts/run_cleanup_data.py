"""
Run database cleanup script to remove old data.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_cleanup():
    """Execute data cleanup SQL."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        return False

    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        try:
            import streamlit as st
            db_url = st.secrets.get("DATABASE_URL")
        except Exception:
            pass

    if not db_url:
        print("ERROR: DATABASE_URL not found in environment or secrets")
        return False

    print("Connecting to database...")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Configuration
        price_retention_days = 30
        log_retention_days = 7

        print(f"Retention policy: prices={price_retention_days} days, logs={log_retention_days} days")
        print("=" * 50)

        # 1. Check current data counts
        print("\n[1/6] Checking current data...")

        tables_to_check = [
            ('prices_packages', 'scraped_at'),
            ('prices_hotels', 'scraped_at'),
            ('prices_flights', 'scraped_at'),
            ('scraping_logs', 'created_at'),
        ]

        for table, date_col in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total = cursor.fetchone()[0]

                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE {date_col} < NOW() - INTERVAL '{price_retention_days} days'
                """)
                old = cursor.fetchone()[0]

                print(f"  {table}: {total} total, {old} old (>{price_retention_days} days)")
            except Exception as e:
                print(f"  {table}: SKIP ({str(e).split(chr(10))[0]})")

        # 2. Delete old packages
        print("\n[2/6] Cleaning old packages...")
        try:
            cursor.execute(f"""
                DELETE FROM prices_packages
                WHERE scraped_at < NOW() - INTERVAL '{price_retention_days} days'
            """)
            deleted = cursor.rowcount
            print(f"  Deleted {deleted} old packages")
        except Exception as e:
            print(f"  SKIP: {str(e).split(chr(10))[0]}")

        # 3. Delete old hotels
        print("\n[3/6] Cleaning old hotels...")
        try:
            cursor.execute(f"""
                DELETE FROM prices_hotels
                WHERE scraped_at < NOW() - INTERVAL '{price_retention_days} days'
            """)
            deleted = cursor.rowcount
            print(f"  Deleted {deleted} old hotels")
        except Exception as e:
            print(f"  SKIP: {str(e).split(chr(10))[0]}")

        # 4. Delete old flights
        print("\n[4/6] Cleaning old flights...")
        try:
            cursor.execute(f"""
                DELETE FROM prices_flights
                WHERE scraped_at < NOW() - INTERVAL '{price_retention_days} days'
            """)
            deleted = cursor.rowcount
            print(f"  Deleted {deleted} old flights")
        except Exception as e:
            print(f"  SKIP: {str(e).split(chr(10))[0]}")

        # 5. Delete old scraping logs
        print("\n[5/6] Cleaning old scraping logs...")
        try:
            cursor.execute(f"""
                DELETE FROM scraping_logs
                WHERE created_at < NOW() - INTERVAL '{log_retention_days} days'
            """)
            deleted = cursor.rowcount
            print(f"  Deleted {deleted} old logs")
        except Exception as e:
            print(f"  SKIP: {str(e).split(chr(10))[0]}")

        # 6. Commit and show final counts
        conn.commit()

        print("\n[6/6] Final data counts...")
        for table, _ in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total = cursor.fetchone()[0]
                print(f"  {table}: {total} records")
            except Exception:
                pass

        # Show table sizes
        print("\n" + "=" * 50)
        print("Table sizes:")
        try:
            cursor.execute("""
                SELECT
                    relname AS table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
                FROM pg_catalog.pg_statio_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 10
            """)
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]}")
        except Exception as e:
            print(f"  Could not get sizes: {e}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 50)
        print("Cleanup completed successfully!")
        return True

    except Exception as e:
        print(f"Database error: {e}")
        return False


if __name__ == "__main__":
    print("LABBAIK AI - Database Cleanup")
    print("=" * 50)
    success = run_cleanup()
    sys.exit(0 if success else 1)
