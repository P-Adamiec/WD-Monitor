"""Product catalog management — loading, URL generation, auto-refresh."""
import time
import json
import threading
from backend.config import CATALOG_PATH, CATALOG_REFRESH_INTERVAL
from backend.database import get_locale

# Module-level catalog state
WD_CATALOG = {}
SERIES_URL_MAP = {}
CATALOG_PRODUCTS = []


def load_catalog():
    """Loads product catalog from JSON file and builds helper structures."""
    global WD_CATALOG, SERIES_URL_MAP, CATALOG_PRODUCTS
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        products = data.get("products", [])

        catalog = {}
        url_map = {}
        all_products = []

        for p in products:
            series = p.get("series", "Unknown")
            sku = p.get("sku", "")
            url_path = p.get("url_path", "")

            if not sku:
                continue

            if series not in url_map and url_path:
                url_map[series] = url_path

            all_products.append(p)

        # Deduplicate by SKU
        seen_skus = set()
        unique_products = []
        for p in all_products:
            if p["sku"] not in seen_skus:
                seen_skus.add(p["sku"])
                unique_products.append(p)

        CATALOG_PRODUCTS = unique_products
        SERIES_URL_MAP = url_map

        # Build legacy WD_CATALOG for backwards compatibility
        catalog = {}
        for p in unique_products:
            series = p.get("series", "Unknown")
            sku = p.get("sku", "")
            if series not in catalog:
                catalog[series] = {}
            catalog[series][sku] = sku

        WD_CATALOG = catalog

        print(f"Catalog loaded: {len(unique_products)} products in {len(catalog)} series")
        return True
    except Exception as e:
        print(f"Catalog load error: {e}")
        return False


def get_url_for_sku(sku):
    """Generates WD store URL for a given SKU based on catalog.json."""
    locale = get_locale()
    for p in CATALOG_PRODUCTS:
        if p.get("sku") == sku:
            url_path = p.get("url_path", "")
            if url_path:
                return f"https://www.westerndigital.com/{locale}/products/{url_path}?sku={sku}"
    return f"https://www.westerndigital.com/{locale}/products/hdd?sku={sku}"


def catalog_refresh_thread():
    """Thread that refreshes catalog every CATALOG_REFRESH_INTERVAL seconds."""
    while True:
        time.sleep(CATALOG_REFRESH_INTERVAL)
        print("Auto-refreshing catalog...")
        load_catalog()


def start_catalog_refresh():
    """Start the catalog auto-refresh daemon thread."""
    t = threading.Thread(target=catalog_refresh_thread, daemon=True)
    t.start()
