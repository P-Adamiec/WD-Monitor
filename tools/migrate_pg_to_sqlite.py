"""Migrate data from PostgreSQL to SQLite.

Run this BEFORE switching to the SQLite branch, while both containers are still running:
    docker exec wd-monitor-dev python tools/migrate_pg_to_sqlite.py

Or from host (if psycopg2 is installed):
    DATABASE_URL=postgresql://monitor_user:monitor_password@localhost:5432/monitor_db python tools/migrate_pg_to_sqlite.py

The script exports all data from PostgreSQL and creates /data/monitor.db with identical content.
"""
import os
import sys
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed. Run this inside the OLD container (before migration).")
    print("       docker exec wd-monitor-dev python tools/migrate_pg_to_sqlite.py")
    sys.exit(1)


PG_URL = os.environ.get("DATABASE_URL", "postgresql://monitor_user:monitor_password@db:5432/monitor_db")
SQLITE_PATH = os.environ.get("DB_PATH", "/data/monitor.db")


def migrate():
    print(f"Connecting to PostgreSQL: {PG_URL}")
    pg = psycopg2.connect(PG_URL)

    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    print(f"Creating SQLite database: {SQLITE_PATH}")
    sq = sqlite3.connect(SQLITE_PATH)
    sq_cur = sq.cursor()

    # Create tables
    sq_cur.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT
    )''')

    sq_cur.execute('''CREATE TABLE IF NOT EXISTS targets (
        sku TEXT NOT NULL, locale TEXT NOT NULL DEFAULT 'pl-pl',
        url TEXT NOT NULL, name TEXT, status TEXT,
        is_available INTEGER DEFAULT 0, last_check TIMESTAMP,
        price TEXT, notify INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        stock_level INTEGER DEFAULT 0,
        last_state_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (sku, locale)
    )''')

    sq_cur.execute('''CREATE TABLE IF NOT EXISTS history_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_sku TEXT, target_locale TEXT DEFAULT 'pl-pl',
        status_msg TEXT, is_available INTEGER,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        log_type TEXT DEFAULT 'status_change'
    )''')

    sq_cur.execute('''CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT, locale TEXT DEFAULT 'pl-pl',
        price TEXT, is_available INTEGER DEFAULT 1,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Migrate settings
    with pg.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT key, value FROM settings")
        rows = cur.fetchall()
        for r in rows:
            sq_cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                           (r['key'], r['value']))
    print(f"  settings: {len(rows)} rows")

    # Migrate targets
    with pg.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM targets")
        rows = cur.fetchall()
        for r in rows:
            sq_cur.execute('''INSERT OR REPLACE INTO targets
                (sku, locale, url, name, status, is_available, last_check, price, notify, created_at, stock_level, last_state_change)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (r['sku'], r.get('locale', 'pl-pl'), r['url'], r.get('name'),
                 r.get('status'), int(bool(r.get('is_available', False))),
                 str(r['last_check']) if r.get('last_check') else None,
                 r.get('price'), int(bool(r.get('notify', True))),
                 str(r['created_at']) if r.get('created_at') else None,
                 r.get('stock_level', 0),
                 str(r['last_state_change']) if r.get('last_state_change') else None))
    print(f"  targets: {len(rows)} rows")

    # Migrate history_logs
    with pg.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM history_logs ORDER BY id")
        rows = cur.fetchall()
        for r in rows:
            sq_cur.execute('''INSERT INTO history_logs
                (target_sku, target_locale, status_msg, is_available, logged_at, log_type)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (r.get('target_sku'), r.get('target_locale', 'pl-pl'),
                 r.get('status_msg'), int(bool(r.get('is_available', False))),
                 str(r['logged_at']) if r.get('logged_at') else None,
                 r.get('log_type', 'status_change')))
    print(f"  history_logs: {len(rows)} rows")

    # Migrate price_history
    with pg.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM price_history ORDER BY id")
        rows = cur.fetchall()
        for r in rows:
            sq_cur.execute('''INSERT INTO price_history
                (sku, locale, price, is_available, logged_at)
                VALUES (?, ?, ?, ?, ?)''',
                (r.get('sku'), r.get('locale', 'pl-pl'),
                 r.get('price'), int(bool(r.get('is_available', True))),
                 str(r['logged_at']) if r.get('logged_at') else None))
    print(f"  price_history: {len(rows)} rows")

    sq.commit()
    sq.close()
    pg.close()
    print(f"\nMigration complete! SQLite DB saved to: {SQLITE_PATH}")


if __name__ == "__main__":
    migrate()
