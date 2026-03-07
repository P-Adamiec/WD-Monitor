"""Database connection and schema initialization."""
import time
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.config import DATABASE_URL, DEFAULT_LOCALE


def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Cannot connect to database: {e}")
        return None


def init_db():
    max_retries = 5
    for attempt in range(max_retries):
        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cur:
                    # Settings table (needed early for locale)
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS settings (
                            key VARCHAR(100) PRIMARY KEY,
                            value TEXT
                        )
                    ''')

                    # ---------- TARGETS TABLE ----------
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS targets (
                            sku VARCHAR(50),
                            locale VARCHAR(10) NOT NULL DEFAULT 'pl-pl',
                            url TEXT NOT NULL,
                            name TEXT,
                            status TEXT,
                            is_available BOOLEAN DEFAULT FALSE,
                            last_check TIMESTAMP,
                            price TEXT,
                            notify BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            stock_level INTEGER DEFAULT 0,
                            last_state_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (sku, locale)
                        )
                    ''')

                    # Migration: if old sku-only PK exists, migrate to composite PK
                    cur.execute('''
                        SELECT COUNT(*) FROM information_schema.table_constraints
                        WHERE table_name = 'targets'
                          AND constraint_type = 'PRIMARY KEY'
                          AND constraint_name = 'targets_pkey'
                    ''')
                    has_pk = cur.fetchone()[0] > 0
                    if has_pk:
                        # Check if the PK is sku-only (1 column) vs composite (2 columns)
                        cur.execute('''
                            SELECT COUNT(*) FROM information_schema.key_column_usage
                            WHERE table_name = 'targets' AND constraint_name = 'targets_pkey'
                        ''')
                        pk_col_count = cur.fetchone()[0]
                        if pk_col_count == 1:
                            print("Migrating targets PK from (sku) to (sku, locale)...")
                            # Ensure locale column exists
                            cur.execute("ALTER TABLE targets ADD COLUMN IF NOT EXISTS locale VARCHAR(10) DEFAULT 'pl-pl'")
                            cur.execute("ALTER TABLE targets ADD COLUMN IF NOT EXISTS stock_level INTEGER DEFAULT 0")
                            cur.execute("ALTER TABLE targets ADD COLUMN IF NOT EXISTS last_state_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                            cur.execute("ALTER TABLE targets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                            # Drop all FK constraints referencing targets
                            cur.execute('''
                                SELECT tc.constraint_name, tc.table_name
                                FROM information_schema.table_constraints tc
                                JOIN information_schema.referential_constraints rc
                                    ON tc.constraint_name = rc.constraint_name
                                JOIN information_schema.table_constraints pk
                                    ON rc.unique_constraint_name = pk.constraint_name
                                WHERE pk.table_name = 'targets' AND tc.constraint_type = 'FOREIGN KEY'
                            ''')
                            fk_constraints = cur.fetchall()
                            for fk_name, fk_table in fk_constraints:
                                cur.execute(f"ALTER TABLE {fk_table} DROP CONSTRAINT IF EXISTS {fk_name}")
                                print(f"  Dropped FK {fk_name} on {fk_table}")
                            # Drop old PK, create new composite PK
                            cur.execute("ALTER TABLE targets DROP CONSTRAINT targets_pkey")
                            cur.execute("ALTER TABLE targets ADD PRIMARY KEY (sku, locale)")
                            print("  Migrated targets PK to (sku, locale)")

                    # ---------- HISTORY LOGS TABLE ----------
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS history_logs (
                            id SERIAL PRIMARY KEY,
                            target_sku VARCHAR(50),
                            target_locale VARCHAR(10) DEFAULT 'pl-pl',
                            status_msg TEXT,
                            is_available BOOLEAN,
                            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            log_type VARCHAR(30) DEFAULT 'status_change'
                        )
                    ''')
                    cur.execute("ALTER TABLE history_logs ADD COLUMN IF NOT EXISTS log_type VARCHAR(30) DEFAULT 'status_change'")
                    cur.execute("ALTER TABLE history_logs ADD COLUMN IF NOT EXISTS target_locale VARCHAR(10) DEFAULT 'pl-pl'")

                    # ---------- PRICE HISTORY TABLE ----------
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS price_history (
                            id SERIAL PRIMARY KEY,
                            sku VARCHAR(50),
                            locale VARCHAR(10) DEFAULT 'pl-pl',
                            price TEXT,
                            is_available BOOLEAN DEFAULT TRUE,
                            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    cur.execute("ALTER TABLE price_history ADD COLUMN IF NOT EXISTS is_available BOOLEAN DEFAULT TRUE")
                    cur.execute("ALTER TABLE price_history ADD COLUMN IF NOT EXISTS locale VARCHAR(10) DEFAULT 'pl-pl'")

                conn.commit()
                print("Database ready and initialized!")
                conn.close()
                return
            except Exception as e:
                print(f"Database initialization error: {e}")
                if conn:
                    conn.close()

        print(f"Waiting for database to start... (attempt {attempt + 1}/{max_retries})")
        time.sleep(3)

    print("Warning: Failed to connect and initialize database on startup.")


def get_locale():
    """Get current locale from settings or env default."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
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
