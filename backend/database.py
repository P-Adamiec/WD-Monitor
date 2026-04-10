"""Database connection and schema initialization — SQLite backend."""
import os
import re
import time
import sqlite3
from backend.config import DB_PATH, DEFAULT_LOCALE


def get_db_connection():
    """Return a sqlite3 connection with Row factory, or None on error."""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    except Exception as e:
        print(f"Cannot open database: {e}")
        return None


def _column_exists(cur, table, column):
    """Check if a column exists in a table."""
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def init_db():
    max_retries = 5
    for attempt in range(max_retries):
        conn = get_db_connection()
        if conn is not None:
            try:
                cur = conn.cursor()

                # ---------- SETTINGS TABLE ----------
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')

                # ---------- TARGETS TABLE ----------
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS targets (
                        sku TEXT NOT NULL,
                        locale TEXT NOT NULL DEFAULT 'pl-pl',
                        url TEXT NOT NULL,
                        name TEXT,
                        status TEXT,
                        is_available INTEGER DEFAULT 0,
                        last_check TIMESTAMP,
                        price TEXT,
                        notify INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        stock_level INTEGER DEFAULT 0,
                        last_state_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (sku, locale)
                    )
                ''')

                # ---------- HISTORY LOGS TABLE ----------
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS history_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_sku TEXT,
                        target_locale TEXT DEFAULT 'pl-pl',
                        status_msg TEXT,
                        is_available INTEGER,
                        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        log_type TEXT DEFAULT 'status_change'
                    )
                ''')

                # ---------- PRICE HISTORY TABLE ----------
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sku TEXT,
                        locale TEXT DEFAULT 'pl-pl',
                        price TEXT,
                        is_available INTEGER DEFAULT 1,
                        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                print("Database ready and initialized!")
                conn.close()
                return
            except Exception as e:
                print(f"Database initialization error: {e}")
                if conn:
                    conn.close()

        print(f"Waiting for database... (attempt {attempt + 1}/{max_retries})")
        time.sleep(3)

    print("Warning: Failed to initialize database on startup.")


def get_locale():
    """Get current locale from settings or env default."""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key = 'locale'")
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
        except Exception:
            pass
        finally:
            conn.close()
    return DEFAULT_LOCALE


def parse_price(price_str):
    """Extract numeric value from price strings like '2 363,99 zł' or '$129.99'."""
    if not price_str:
        return None
    try:
        cleaned = re.sub(r'[^\d,.]', '', price_str)
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
        elif ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None
