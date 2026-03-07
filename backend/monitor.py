"""Background monitoring thread — checks WD API for product availability."""
import time
from collections import defaultdict
from psycopg2.extras import RealDictCursor
from curl_cffi import requests

from backend.database import get_db_connection, parse_price
from backend.notifications import send_discord_alert

DEFAULT_CHECK_INTERVAL = 90  # seconds


# Maximum SKUs per batch API call (avoid excessively long URLs)
BATCH_SIZE = 20


def parse_product_data(product_data):
    """Extract availability info from a single product entry in the API response."""
    sku = product_data.get('code', '') or product_data.get('sku', '')
    name = product_data.get('name') or sku

    price_data = product_data.get('priceData')
    price = price_data.get('formattedValue', '') if isinstance(price_data, dict) else ''

    stock_obj = product_data.get('stock')
    status_obj = stock_obj.get('stockLevelStatus') if isinstance(stock_obj, dict) else None
    stock_code = status_obj.get('code', '') if isinstance(status_obj, dict) else ''
    purchasable = product_data.get('purchasable', False)
    stock_level = stock_obj.get('stockLevel', 0) if isinstance(stock_obj, dict) else 0

    is_error = False
    if stock_code == 'inStock':
        is_available = True
        if purchasable:
            status_message = "In Stock"
            is_purchasable = True
        else:
            status_message = "Inquiry Only"
            is_purchasable = False
    elif stock_code == 'outOfStock':
        is_available = False
        status_message = "Out of Stock"
        is_purchasable = False
        stock_level = 0
    elif stock_code:
        is_available = False
        status_message = f"Status: {stock_code}"
        is_purchasable = False
        stock_level = 0
    else:
        is_available = False
        status_message = "No stock data"
        is_purchasable = False
        is_error = True
        stock_level = 0

    return {
        'sku': sku,
        'name': name,
        'price': price,
        'is_available': is_available,
        'status_message': status_message,
        'is_error': is_error,
        'is_purchasable': is_purchasable,
        'stock_level': stock_level,
    }


def batch_check_availability(skus, locale):
    """Check availability for multiple SKUs in a single API call.
    Returns dict[sku] -> {is_available, status_message, name, price, is_error, is_purchasable, stock_level}"""
    results = {}

    try:
        sku_query = ','.join(skus)
        api_url = f"https://www.westerndigital.com/{locale}/store/cart/guest/products/priceAndInventory?fields=FULL&productsQuery={sku_query}"
        headers = {"Accept": "application/json"}
        response = requests.get(api_url, impersonate="chrome120", headers=headers, timeout=20)

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                # Mark all as error
                for sku in skus:
                    results[sku] = {
                        'is_available': False, 'status_message': 'API JSON parse error',
                        'name': sku, 'price': '', 'is_error': True,
                        'is_purchasable': False, 'stock_level': 0,
                    }
                return results

            if isinstance(data, list):
                for product_data in data:
                    parsed = parse_product_data(product_data)
                    results[parsed['sku']] = parsed
        else:
            for sku in skus:
                results[sku] = {
                    'is_available': False, 'status_message': f'HTTP {response.status_code}',
                    'name': sku, 'price': '', 'is_error': True,
                    'is_purchasable': False, 'stock_level': 0,
                }
    except Exception as e:
        for sku in skus:
            results[sku] = {
                'is_available': False, 'status_message': f'Error: {str(e)[:80]}',
                'name': sku, 'price': '', 'is_error': True,
                'is_purchasable': False, 'stock_level': 0,
            }

    # For SKUs not in the response, try en-us fallback
    missing = [s for s in skus if s not in results]
    if missing and locale != 'en-us':
        try:
            sku_query = ','.join(missing)
            api_url_en = f"https://www.westerndigital.com/en-us/store/cart/guest/products/priceAndInventory?fields=FULL&productsQuery={sku_query}"
            response_en = requests.get(api_url_en, impersonate="chrome120", headers=headers, timeout=15)
            if response_en.status_code == 200:
                data_en = response_en.json()
                if isinstance(data_en, list):
                    for product_data in data_en:
                        parsed = parse_product_data(product_data)
                        if parsed['sku'] in missing:
                            results[parsed['sku']] = parsed
        except Exception:
            pass

    # Remaining unfound SKUs
    for sku in skus:
        if sku not in results:
            results[sku] = {
                'is_available': False, 'status_message': 'Product unknown in WD API',
                'name': sku, 'price': '', 'is_error': True,
                'is_purchasable': False, 'stock_level': 0,
            }

    return results


def get_check_interval(conn):
    """Read check interval from DB settings, fallback to default."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = 'check_interval'")
            row = cur.fetchone()
            if row:
                return max(10, int(row[0]))  # minimum 10 seconds
    except Exception:
        pass
    return DEFAULT_CHECK_INTERVAL


def monitor_thread():
    while True:
        conn = get_db_connection()
        if not conn:
            time.sleep(DEFAULT_CHECK_INTERVAL)
            continue

        interval = get_check_interval(conn)

        # Check global pause setting
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT value FROM settings WHERE key = 'monitoring_paused'")
                row = cur.fetchone()
                if row and row['value'].lower() == 'true':
                    conn.close()
                    time.sleep(interval)
                    continue
        except Exception:
            pass

        # Fetch ALL targets across ALL locales
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM targets")
                db_targets = cur.fetchall()
        except Exception as e:
            print(f"DB read error before check: {e}")
            conn.close()
            time.sleep(interval)
            continue

        if not db_targets:
            conn.close()
            time.sleep(interval)
            continue

        # Group targets by locale — all products checked every cycle
        by_locale = defaultdict(list)
        for t in db_targets:
            locale = t.get("locale", "pl-pl")
            by_locale[locale].append(t)

        newly_started = []

        # Process each locale batch
        for locale, targets in by_locale.items():
            # Split into batches of BATCH_SIZE
            for batch_start in range(0, len(targets), BATCH_SIZE):
                batch = targets[batch_start:batch_start + BATCH_SIZE]
                skus = [t["sku"] for t in batch]

                # One API call for multiple SKUs
                api_results = batch_check_availability(skus, locale)

                # Small delay between batches, not between individual SKUs
                if batch_start > 0:
                    time.sleep(2)

                # Process results for each target
                for t in batch:
                    result = api_results.get(t["sku"])
                    if not result:
                        continue

                    is_available = result['is_available']
                    status_message = result['status_message']
                    name = result['name'] if result['name'] != t['sku'] else (t.get('name') or t['sku'])
                    price = result['price'] if result['price'] else ''
                    is_error = result['is_error']
                    stock_level = result['stock_level']

                    if t["status"] == "Oczekiwanie...":
                        newly_started.append(t["sku"])

                    try:
                        with conn.cursor() as cur:
                            prev_available = t["is_available"]
                            prev_status = t["status"]

                            # FALSE POSITIVE PREVENTION
                            if is_error and prev_available:
                                cur.execute('''
                                    INSERT INTO history_logs (target_sku, target_locale, status_msg, is_available, log_type)
                                    VALUES (%s, %s, %s, %s, %s)
                                ''', (t["sku"], locale, f"{t['sku']}: {status_message} (kept previous state)", prev_available, 'error'))
                                cur.execute('UPDATE targets SET last_check = CURRENT_TIMESTAMP WHERE sku = %s AND locale = %s', (t["sku"], locale))
                                conn.commit()
                                continue

                            state_changed = (prev_status != "Oczekiwanie...") and (prev_available != is_available)

                            # PRICE CHANGE DETECTION
                            effective_price = price if price else t["price"]

                            if not is_error and prev_status != "Oczekiwanie..." and effective_price and t["price"]:
                                old_num = parse_price(t["price"])
                                new_num = parse_price(effective_price)
                                if old_num and new_num and abs(old_num - new_num) > 0.01:
                                    pct = ((new_num - old_num) / old_num) * 100
                                    if pct < -0.5:
                                        cur.execute('''
                                            INSERT INTO history_logs (target_sku, target_locale, status_msg, is_available, log_type)
                                            VALUES (%s, %s, %s, %s, %s)
                                        ''', (t["sku"], locale, f"{name} ({t['sku']}): Price dropped {abs(pct):.0f}% → {effective_price}", is_available, 'price_drop'))
                                    elif pct > 0.5:
                                        cur.execute('''
                                            INSERT INTO history_logs (target_sku, target_locale, status_msg, is_available, log_type)
                                            VALUES (%s, %s, %s, %s, %s)
                                        ''', (t["sku"], locale, f"{name} ({t['sku']}): Price increased {pct:.0f}% → {effective_price}", is_available, 'price_increase'))

                            # Log significant state changes
                            if state_changed:
                                if is_available and not prev_available:
                                    cur.execute('''
                                        INSERT INTO history_logs (target_sku, target_locale, status_msg, is_available, log_type)
                                        VALUES (%s, %s, %s, %s, %s)
                                    ''', (t["sku"], locale, f"{name} ({t['sku']}): Back in stock!", True, 'available'))
                                elif not is_available and prev_available:
                                    cur.execute('''
                                        INSERT INTO history_logs (target_sku, target_locale, status_msg, is_available, log_type)
                                        VALUES (%s, %s, %s, %s, %s)
                                    ''', (t["sku"], locale, f"{name} ({t['sku']}): Sold out", False, 'sold_out'))

                                if is_available and not prev_available and t.get("notify", True):
                                    cur.execute("SELECT value FROM settings WHERE key = 'discord_webhook'")
                                    webhook_row = cur.fetchone()
                                    if webhook_row and webhook_row[0]:
                                        alert_target = {**t, 'name': name}
                                        send_discord_alert(webhook_row[0], alert_target, price)
                            elif prev_status == "Oczekiwanie...":
                                if is_available and t.get("notify", True):
                                    cur.execute("SELECT value FROM settings WHERE key = 'discord_webhook'")
                                    webhook_row = cur.fetchone()
                                    if webhook_row and webhook_row[0]:
                                        alert_target = {**t, 'name': name}
                                        send_discord_alert(webhook_row[0], alert_target, price)

                            # PRICE HISTORY — per-locale
                            if state_changed and effective_price:
                                cur.execute('''
                                    INSERT INTO price_history (sku, price, is_available, locale)
                                    VALUES (%s, %s, %s, %s)
                                ''', (t["sku"], effective_price, is_available, locale))
                            elif effective_price:
                                cur.execute('''
                                    SELECT id FROM price_history
                                    WHERE sku = %s AND locale = %s AND logged_at::date = CURRENT_DATE
                                    LIMIT 1
                                ''', (t["sku"], locale))
                                if not cur.fetchone():
                                    cur.execute('''
                                        INSERT INTO price_history (sku, price, is_available, locale)
                                        VALUES (%s, %s, %s, %s)
                                    ''', (t["sku"], effective_price, is_available, locale))

                            # Update target status
                            if state_changed:
                                cur.execute('''
                                    UPDATE targets
                                    SET is_available = %s, status = %s, name = %s, price = %s,
                                        last_check = CURRENT_TIMESTAMP, stock_level = %s,
                                        last_state_change = CURRENT_TIMESTAMP
                                    WHERE sku = %s AND locale = %s
                                ''', (is_available, status_message, name, price if price else t["price"], stock_level, t["sku"], locale))
                            else:
                                cur.execute('''
                                    UPDATE targets
                                    SET is_available = %s, status = %s, name = %s, price = %s,
                                        last_check = CURRENT_TIMESTAMP, stock_level = %s
                                    WHERE sku = %s AND locale = %s
                                ''', (is_available, status_message, name, price if price else t["price"], stock_level, t["sku"], locale))

                        conn.commit()
                    except Exception as e:
                        print(f"Status log error {t['sku']}: {e}")
                        conn.rollback()

            # Small pause between locale groups
            time.sleep(2)

        # Batch log: group newly started trackings
        if newly_started:
            try:
                with conn.cursor() as cur:
                    if len(newly_started) == 1:
                        msg = f"Started tracking {newly_started[0]}"
                    else:
                        msg = f"Started tracking ({len(newly_started)}): {', '.join(newly_started)}"
                    cur.execute('''
                        INSERT INTO history_logs (target_sku, target_locale, status_msg, is_available, log_type)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (newly_started[0], 'system', msg, False, 'tracking_started'))
                conn.commit()
            except Exception as e:
                print(f"Batch log error: {e}")
                conn.rollback()

        conn.close()
        time.sleep(interval)
