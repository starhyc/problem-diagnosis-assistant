"""
Migration script to copy existing SQLite data to PostgreSQL
Run this after creating the PostgreSQL tables
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB = "aiops.db"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://aiops:aiops_password@localhost:5432/aiops")

def migrate_data():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cur = pg_conn.cursor()

    try:
        # Migrate users
        print("Migrating users...")
        sqlite_cur.execute("SELECT * FROM users")
        users = [dict(row) for row in sqlite_cur.fetchall()]
        if users:
            execute_values(
                pg_cur,
                """INSERT INTO users (id, username, email, hashed_password, display_name, role, avatar, is_active, created_at, updated_at)
                   VALUES %s ON CONFLICT (id) DO NOTHING""",
                [(u['id'], u['username'], u['email'], u['hashed_password'], u['display_name'],
                  u['role'], u.get('avatar'), u.get('is_active', True), u.get('created_at'), u.get('updated_at'))
                 for u in users]
            )

        # Migrate cases
        print("Migrating cases...")
        sqlite_cur.execute("SELECT * FROM cases")
        cases = [dict(row) for row in sqlite_cur.fetchall()]
        if cases:
            execute_values(
                pg_cur,
                """INSERT INTO cases (id, case_id, symptom, status, lead_agent, confidence, created_at, updated_at)
                   VALUES %s ON CONFLICT (case_id) DO NOTHING""",
                [(c['id'], c['case_id'], c['symptom'], c['status'], c['lead_agent'],
                  c.get('confidence', 0), c.get('created_at'), c.get('updated_at'))
                 for c in cases]
            )

        # Migrate agents
        print("Migrating agents...")
        sqlite_cur.execute("SELECT * FROM agents")
        agents = [dict(row) for row in sqlite_cur.fetchall()]
        if agents:
            execute_values(
                pg_cur,
                """INSERT INTO agents (id, agent_id, name, role, agent_type, color, description, is_active, created_at)
                   VALUES %s ON CONFLICT (agent_id) DO NOTHING""",
                [(a['id'], a['agent_id'], a['name'], a['role'], a.get('agent_type', 'diagnosis'),
                  a['color'], a['description'], a.get('is_active', True), a.get('created_at'))
                 for a in agents]
            )

        pg_conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        pg_conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        sqlite_cur.close()
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_data()
