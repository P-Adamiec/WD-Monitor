"""Flask routes — all API endpoints via Blueprint."""
import time
import json
import urllib.request
from flask import Blueprint, render_template, jsonify, request

from backend.config import DEFAULT_LOCALE
from backend.database import get_db_connection, get_locale
import backend.catalog as catalog

api = Blueprint('api', __name__)


@api.route("/")
def index():
    import os
    app_env = os.environ.get("APP_ENV", "prod")
    return render_template("index.html", app_env=app_env)


@api.route("/api/status")
def api_status():
    conn = get_db_connection()
    if not conn:
        return jsonify({"targets": [], "history": []})

    try:
        locale = get_locale()
        cur = conn.cursor()
        sort_order = request.args.get('sort', 'desc')
        order_clause = 'ASC' if sort_order == 'asc' else 'DESC'
        # Filter targets by current locale
        cur.execute(
            f"SELECT * FROM targets WHERE locale = ? ORDER BY created_at {order_clause}, sku ASC",
            (locale,)
        )
        targets_rows = cur.fetchall()

        targets = []
        # Build catalog lookup for enrichment
        catalog_by_sku = {}
        for cp in catalog.CATALOG_PRODUCTS:
            catalog_by_sku[cp.get('sku', '')] = cp

        for t in targets_rows:
            d = dict(t)
            d['last_check'] = d['last_check'] if d['last_check'] else 'Never'
            d['stock_level'] = d.get('stock_level', 0) or 0
            # Convert SQLite integer booleans to Python bools
            d['is_available'] = bool(d.get('is_available', 0))
            d['notify'] = bool(d.get('notify', 1))

            # Enrich with catalog metadata
            cat_entry = catalog_by_sku.get(d.get('sku', ''))
            if cat_entry:
                d['category'] = cat_entry.get('category', 'standard')
                d['capacity'] = cat_entry.get('capacity', '')
                # Use catalog name if current name is just the SKU
                if d.get('name') == d.get('sku') and cat_entry.get('name'):
                    d['name'] = cat_entry['name']
            else:
                d['category'] = 'standard'
                d['capacity'] = ''

            targets.append(d)

        cur.execute("SELECT logged_at as time, status_msg as status, is_available as available, log_type FROM history_logs ORDER BY id DESC LIMIT 100")
        history_rows = cur.fetchall()

        history = []
        for h in history_rows:
            dh = dict(h)
            dh['available'] = bool(dh.get('available', 0))
            dh['log_type'] = dh.get('log_type', 'status_change')
            history.append(dh)

        cur.execute("SELECT key, value FROM settings WHERE key IN ('notify_sound', 'notify_discord', 'notify_push', 'monitoring_paused', 'locale', 'check_interval')")
        settings_rows = cur.fetchall()
        settings = {
            "notify_sound": "true",
            "notify_discord": "true",
            "notify_push": "true",
            "monitoring_paused": "false",
            "locale": DEFAULT_LOCALE,
            "check_interval": "90"
        }
        for sr in settings_rows:
            settings[sr['key']] = sr['value']

        return jsonify({"targets": targets, "history": history, "settings": settings})
    except Exception as e:
        print(f"Status API error: {e}")
        return jsonify({"targets": [], "history": []})
    finally:
        conn.close()


@api.route("/api/logs/clear", methods=["POST"])
def api_clear_logs():
    scope = request.args.get('scope', 'all')
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500
    try:
        cur = conn.cursor()
        if scope == 'hour':
            cur.execute("DELETE FROM history_logs WHERE logged_at > datetime('now', '-1 hour')")
        elif scope == 'day':
            cur.execute("DELETE FROM history_logs WHERE logged_at > datetime('now', '-1 day')")
        else:
            cur.execute("DELETE FROM history_logs")
        conn.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


TEST_TRANSLATIONS = {
    'en': {
        'title': '🧪 Test Message',
        'description': 'If you see this message, your Discord webhook is working correctly!',
        'footer': 'WD Monitor • Webhook Test',
    },
    'pl': {
        'title': '🧪 Wiadomość testowa',
        'description': 'Jeśli widzisz tę wiadomość, Twój webhook Discord działa poprawnie!',
        'footer': 'WD Monitor • Test webhooka',
    },
    'de': {
        'title': '🧪 Testnachricht',
        'description': 'Wenn Sie diese Nachricht sehen, funktioniert Ihr Discord-Webhook korrekt!',
        'footer': 'WD Monitor • Webhook-Test',
    },
}


@api.route("/api/discord/test", methods=["POST"])
def test_discord_webhook():
    """Send a test message to the configured Discord webhook."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings WHERE key IN ('discord_webhook', 'ui_language')")
        rows = cur.fetchall()
        webhook_url = None
        ui_lang = 'en'
        for r in rows:
            if r[0] == 'discord_webhook':
                webhook_url = r[1]
            elif r[0] == 'ui_language':
                ui_lang = r[1] if r[1] in TEST_TRANSLATIONS else 'en'

        if not webhook_url:
            return jsonify({"error": "No webhook configured"}), 400

        tt = TEST_TRANSLATIONS.get(ui_lang, TEST_TRANSLATIONS['en'])
        payload = json.dumps({
            "username": "WD Monitor",
            "avatar_url": "https://www.westerndigital.com/content/dam/store/en-us/assets/favicon/favicon.ico",
            "embeds": [{
                "title": tt['title'],
                "description": tt['description'],
                "color": 3447003,
                "footer": {"text": tt['footer']},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }]
        }).encode('utf-8')

        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={'Content-Type': 'application/json', 'User-Agent': 'WD-Monitor-Bot/1.0'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 204):
                return jsonify({"success": True, "message": "Test message sent!"})
            return jsonify({"error": f"Discord returned {resp.status}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api.route("/api/targets/bulk-delete", methods=["POST"])
def bulk_delete_targets():
    """Delete multiple tracked targets at once — scoped to current locale."""
    data = request.json
    skus = data.get("skus", [])
    if not skus or not isinstance(skus, list):
        return jsonify({"error": "Missing SKU list"}), 400

    locale = get_locale()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500
    try:
        cur = conn.cursor()
        placeholders = ','.join('?' for _ in skus)
        cur.execute(f"DELETE FROM targets WHERE sku IN ({placeholders}) AND locale = ?", skus + [locale])
        deleted = cur.rowcount
        conn.commit()
        return jsonify({"success": True, "deleted": deleted})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api.route("/api/catalog")
def api_catalog():
    """Returns full product catalog as a flat list."""
    result = []
    for p in catalog.CATALOG_PRODUCTS:
        result.append({
            "series": p.get("series", "Unknown"),
            "sku": p.get("sku", ""),
            "name": p.get("name", ""),
            "category": p.get("category", "standard"),
            "capacity": p.get("capacity", ""),
            "url_path": p.get("url_path", "")
        })
    return jsonify(result)


@api.route("/api/catalog/refresh", methods=["POST"])
def api_catalog_refresh():
    """Manual catalog refresh from JSON file."""
    success = catalog.load_catalog()
    if success:
        return jsonify({"status": "ok", "count": len(catalog.CATALOG_PRODUCTS)})
    return jsonify({"error": "Catalog refresh error"}), 500


@api.route("/api/targets/batch", methods=["POST"])
def add_targets_batch():
    data = request.json
    skus = data.get("skus", [])

    if not skus or not isinstance(skus, list):
        return jsonify({"error": "Missing SKU list"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    locale = get_locale()
    added_count = 0
    try:
        cur = conn.cursor()
        for sku in skus:
            sku = sku.strip()
            if not sku:
                continue

            url = catalog.get_url_for_sku(sku)

            cur.execute('''
                INSERT INTO targets (sku, locale, url, name, status, is_available, notify, price)
                VALUES (?, ?, ?, ?, ?, 0, 1, '')
                ON CONFLICT (sku, locale) DO NOTHING
            ''', (sku, locale, url, sku, "Oczekiwanie..."))

            if cur.rowcount > 0:
                added_count += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"success": True, "added": added_count})


@api.route("/api/targets", methods=["POST"])
def add_target():
    data = request.json
    sku = data.get("sku")

    if not sku:
        return jsonify({"error": "Missing SKU code"}), 400

    sku = sku.strip()

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    url = catalog.get_url_for_sku(sku)
    locale = get_locale()

    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO targets (sku, locale, url, name, status, is_available, notify, price)
            VALUES (?, ?, ?, ?, ?, 0, 1, '')
            ON CONFLICT (sku, locale) DO NOTHING
        ''', (sku, locale, url, sku, "Oczekiwanie..."))

        if cur.rowcount == 0:
            return jsonify({"error": "Product already tracked in this region"}), 400
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"success": True})


@api.route("/api/targets/<sku>", methods=["DELETE"])
def delete_target(sku):
    locale = get_locale()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM targets WHERE sku = ? AND locale = ?", (sku, locale))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api.route("/api/targets/<sku>/toggle_notify", methods=["POST"])
def toggle_notify(sku):
    locale = get_locale()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    try:
        cur = conn.cursor()
        cur.execute("SELECT notify FROM targets WHERE sku = ? AND locale = ?", (sku, locale))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Product not found"}), 404

        new_notify = 0 if row["notify"] else 1

        cur.execute("UPDATE targets SET notify = ? WHERE sku = ? AND locale = ?", (new_notify, sku, locale))
        conn.commit()

        return jsonify({"success": True, "notify": bool(new_notify)})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api.route("/api/targets/<sku>/history", methods=["GET"])
def target_price_history(sku):
    locale = get_locale()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    try:
        months = int(request.args.get('months', 3))
        if months not in (1, 3, 6, 12):
            months = 3

        cur = conn.cursor()
        cur.execute('''
            SELECT price, logged_at, is_available
            FROM price_history
            WHERE sku = ? AND locale = ? AND logged_at > datetime('now', ? || ' months')
            ORDER BY logged_at ASC
        ''', (sku, locale, f'-{months}'))
        rows = cur.fetchall()

        history = []
        for r in rows:
            d = dict(r)
            d['is_available'] = bool(d.get('is_available', 1))
            history.append(d)

        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api.route("/api/settings/discord", methods=["GET", "POST"])
def discord_settings():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    try:
        cur = conn.cursor()
        if request.method == "POST":
            data = request.json
            webhook = data.get("webhook", "").strip()
            cur.execute('''
                INSERT INTO settings (key, value)
                VALUES ('discord_webhook', ?)
                ON CONFLICT (key) DO UPDATE SET value = excluded.value
            ''', (webhook,))
            conn.commit()
            return jsonify({"success": True})
        else:
            cur.execute("SELECT value FROM settings WHERE key = 'discord_webhook'")
            row = cur.fetchone()
            return jsonify({"webhook": row["value"] if row else ""})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api.route("/api/settings", methods=["POST"])
def update_settings():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        cur = conn.cursor()
        for key, value in data.items():
            if key == 'locale':
                continue  # locale changes go through /api/settings/locale
            val_str = str(value).lower() if isinstance(value, bool) else str(value)
            cur.execute('''
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT (key) DO UPDATE SET value = excluded.value
            ''', (key, val_str))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@api.route("/api/settings/locale", methods=["POST"])
def change_locale():
    """Change store locale — just saves the setting. Each region has independent data."""
    data = request.json
    new_locale = data.get("locale", "").strip()
    if not new_locale:
        return jsonify({"error": "Missing locale"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    try:
        cur = conn.cursor()
        # Save locale setting
        cur.execute('''
            INSERT INTO settings (key, value)
            VALUES ('locale', ?)
            ON CONFLICT (key) DO UPDATE SET value = excluded.value
        ''', (new_locale,))

        # Log the locale change
        cur.execute('''
            INSERT INTO history_logs (target_sku, target_locale, status_msg, is_available, log_type)
            VALUES (?, ?, ?, 0, ?)
        ''', ('system', new_locale,
              f'Store region changed to {new_locale}',
              'locale_change'))

        conn.commit()
        return jsonify({"success": True, "locale": new_locale})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
