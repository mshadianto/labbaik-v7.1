"""
LABBAIK AI - Run Groups Migration
==================================
Run this script to create the simulation_groups and group_members tables.

Usage:
    python scripts/run_groups_migration.py

Or run the SQL directly in Supabase Dashboard:
    1. Go to https://supabase.com/dashboard
    2. Select your project
    3. Go to SQL Editor
    4. Paste contents of sql/simulation_groups_schema.sql
    5. Run the query
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_migration():
    """Run the groups migration."""

    # Read the SQL file
    sql_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'sql',
        'simulation_groups_schema.sql'
    )

    with open(sql_path, 'r') as f:
        sql = f.read()

    print("=" * 60)
    print("LABBAIK AI - Groups Migration")
    print("=" * 60)

    try:
        from services.database.repository import get_db
        db = get_db()

        if not db:
            print("\nERROR: Database connection not available.")
            print("\nAlternative: Run the SQL manually in Supabase Dashboard:")
            print(f"  1. Open {sql_path}")
            print("  2. Copy the contents")
            print("  3. Go to Supabase Dashboard > SQL Editor")
            print("  4. Paste and run")
            return False

        print("\nConnected to database. Running migration...")

        # Execute the full SQL
        db.execute(sql)

        print("\nMigration completed successfully!")

        # Verify tables exist
        result = db.fetch_all("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name IN ('simulation_groups', 'group_members')
            ORDER BY table_name
        """)

        if result:
            print(f"\nTables created: {[r['table_name'] for r in result]}")
        else:
            print("\nWarning: Tables not found in verification query.")

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nAlternative: Run the SQL manually in Supabase Dashboard")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
