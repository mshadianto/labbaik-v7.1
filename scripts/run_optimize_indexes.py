"""
Run database index optimization script.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_optimize_indexes():
    """Execute index optimization SQL."""
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

    # Read SQL file
    sql_file = project_root / "sql" / "optimize_indexes.sql"
    if not sql_file.exists():
        print(f"ERROR: SQL file not found: {sql_file}")
        return False

    sql_content = sql_file.read_text(encoding='utf-8')

    # Split into individual statements (skip comments and empty lines)
    statements = []
    current_stmt = []

    for line in sql_content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('--') or not stripped:
            continue
        current_stmt.append(line)
        if stripped.endswith(';'):
            statements.append('\n'.join(current_stmt))
            current_stmt = []

    print(f"Found {len(statements)} SQL statements to execute")
    print("=" * 50)

    # Execute
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        success_count = 0
        error_count = 0

        for i, stmt in enumerate(statements, 1):
            stmt_preview = stmt.replace('\n', ' ')[:60]
            try:
                cursor.execute(stmt)
                print(f"[{i}/{len(statements)}] OK: {stmt_preview}...")
                success_count += 1
            except Exception as e:
                error_msg = str(e).split('\n')[0]
                if 'already exists' in error_msg.lower() or 'does not exist' in error_msg.lower():
                    print(f"[{i}/{len(statements)}] SKIP: {stmt_preview}... ({error_msg})")
                else:
                    print(f"[{i}/{len(statements)}] ERROR: {stmt_preview}... ({error_msg})")
                    error_count += 1

        cursor.close()
        conn.close()

        print("=" * 50)
        print(f"Completed: {success_count} success, {error_count} errors")
        return error_count == 0

    except Exception as e:
        print(f"Database connection error: {e}")
        return False


if __name__ == "__main__":
    print("LABBAIK AI - Database Index Optimization")
    print("=" * 50)
    success = run_optimize_indexes()
    sys.exit(0 if success else 1)
