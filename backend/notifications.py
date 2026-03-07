"""Discord notification service."""
import time
import json
import urllib.request
from backend.database import get_db_connection
import backend.catalog as catalog


# Locale-to-language mapping for Discord messages
LOCALE_LANG = {
    'pl-pl': 'pl',
    'de-de': 'de',
    'en-us': 'en',
    'en-gb': 'en',
    'fr-fr': 'en',
    'it-it': 'en',
    'es-es': 'en',
    'nl-nl': 'en',
}

DISCORD_TRANSLATIONS = {
    'en': {
        'title': '🟢 Back In Stock!',
        'description': '**{name}** is now available for purchase.',
        'price': '💰 Price',
        'sku': '📦 SKU',
        'capacity': '💾 Capacity',
        'store_link': '🔗 Store Link',
        'open_store': 'Open in WD Store',
        'footer': 'WD Monitor • Availability Alert',
    },
    'pl': {
        'title': '🟢 Ponownie dostępny!',
        'description': '**{name}** jest teraz dostępny do zakupu.',
        'price': '💰 Cena',
        'sku': '📦 SKU',
        'capacity': '💾 Pojemność',
        'store_link': '🔗 Link do sklepu',
        'open_store': 'Otwórz w sklepie WD',
        'footer': 'WD Monitor • Alert dostępności',
    },
    'de': {
        'title': '🟢 Wieder auf Lager!',
        'description': '**{name}** ist jetzt zum Kauf verfügbar.',
        'price': '💰 Preis',
        'sku': '📦 SKU',
        'capacity': '💾 Kapazität',
        'store_link': '🔗 Shop-Link',
        'open_store': 'Im WD Store öffnen',
        'footer': 'WD Monitor • Verfügbarkeitsalarm',
    },
}


def send_discord_alert(webhook_url, target, price):
    if not webhook_url:
        return

    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM settings WHERE key = 'notify_discord'")
                res = cur.fetchone()
                if res and str(res[0]).lower() == 'false':
                    conn.close()
                    return
            conn.close()

    except Exception as e:
        print("Discord settings check error:", e)

    try:
        # Lookup capacity from catalog
        capacity = ""
        for p in catalog.CATALOG_PRODUCTS:
            if p.get("sku") == target.get("sku", ""):
                capacity = p.get("capacity", "")
                break

        sku = target.get('sku', 'N/A')
        name = target.get('name', 'Unknown Product')
        url = target.get('url', '').replace(' ', '')
        locale = target.get('locale', 'en-us')

        # Get localized strings
        lang = LOCALE_LANG.get(locale, 'en')
        dt = DISCORD_TRANSLATIONS.get(lang, DISCORD_TRANSLATIONS['en'])

        fields = [
            {"name": dt['price'], "value": price if price else "—", "inline": True},
            {"name": dt['sku'], "value": f"`{sku}`", "inline": True},
        ]
        if capacity:
            fields.append({"name": dt['capacity'], "value": capacity, "inline": True})
        fields.append({"name": dt['store_link'], "value": f"[{dt['open_store']}]({url})", "inline": False})

        # Title includes product name for quick identification
        embed_title = f"{dt['title']} — {name}"

        payload = json.dumps({
            "username": "WD Monitor",
            "avatar_url": "https://www.westerndigital.com/content/dam/store/en-us/assets/favicon/favicon.ico",
            "embeds": [
                {
                    "title": embed_title,
                    "description": dt['description'].format(name=name),
                    "url": url,
                    "color": 3066993,
                    "fields": fields,
                    "footer": {
                        "text": dt['footer']
                    },
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            ]
        }).encode('utf-8')

        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={'Content-Type': 'application/json', 'User-Agent': 'WD-Monitor-Bot/1.0'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 204):
                print(f"Discord webhook error: {resp.status}")
    except Exception as e:
        print("Discord send error:", e)
