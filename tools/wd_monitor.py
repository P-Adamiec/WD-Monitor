import time
import winsound
import sys
from bs4 import BeautifulSoup
from curl_cffi import requests
from plyer import notification

# Konfiguracja
# URL docelowego produktu (WD Red Pro 8TB)
URL_TARGET = "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-red-pro-sata-hdd?sku=WD8005FFBX"

# URL produktu testowego, który na pewno jest dostępny (WD Purple Pro)
# Odkomentuj go i przypisz do poniższej zmiennej, aby przetestować działanie alertu
# URL_TARGET = "https://www.westerndigital.com/pl-pl/products/internal-drives/wd-purple-pro-sata-hdd?sku=WD221PURP"

# Interwał sprawdzania w sekundach
CHECK_INTERVAL_SECONDS = 60 

from urllib.parse import urlparse, parse_qs

def check_availability(url):
    try:
        # Western Digital blokuje standardowe zapytania biblioteki "requests" błędem 403.
        # Używamy biblioteki curl_cffi, żeby udawać prawdziwą przeglądarkę.
        
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        locale = path_parts[0] if len(path_parts) > 0 and '-' in path_parts[0] else 'en-us'
        
        qs = parse_qs(parsed_url.query)
        skus = qs.get("sku", [])
        if not skus:
            return False, "Błąd: Brak parametru '?sku=' w linku. Dodaj odpowiednie SKU do URL."
            
        sku = skus[0]
        api_url = f"https://www.westerndigital.com/{locale}/store/cart/guest/products/priceAndInventory?fields=FULL&productsQuery={sku}"
        
        response = requests.get(api_url, impersonate="chrome120", timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                return False, "Błąd: Nie udało się odczytać odpowiedzi JSON z API"
                
            if isinstance(data, list) and len(data) > 0:
                product_data = data[0]
                stock_code = product_data.get('stock', {}).get('stockLevelStatus', {}).get('code', '')
                
                if stock_code == 'inStock':
                    return True, "Produkt jest dostępny (Status: inStock)!"
                elif stock_code == 'outOfStock':
                    return False, "Produkt nadal niedostępny (Brak w magazynie)."
                else:
                    return False, f"Produkt niedostępny (Status: {stock_code})"
            else:
                return False, "Błąd: Otrzymano puste dane z serwera WD."
        else:
            return False, f"Błąd połączenia z API: Otrzymano kod {response.status_code}"
            
    except Exception as e:
        return False, f"Wystąpił błąd podczas sprawdzania API: {e}"

def trigger_alert(title, message):
    print(f"\n[ALARM] {title}: {message}")
    
    # Wywołujemy dźwięk z głośnika systemowego w systemie Windows (częstotliwość 1000Hz, 1500 milisekund)
    try:
        winsound.Beep(1000, 1500)
    except Exception:
        pass
    
    # Wywołujemy systemowe powiadomienie (Toast w prawym dolnym rogu Windows)
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Monitor WD Red",
            timeout=10 # sekundy na ekranie
        )
    except Exception as e:
        print(f"Nie udało się wyświetlić powiadomienia systemowego: {e}")

def main():
    print("=====================================================")
    print(" Monitor dostępności dysku Western Digital")
    print(f" Sprawdzany adres: {URL_TARGET}")
    print(f" Interwał sprawdzań: co {CHECK_INTERVAL_SECONDS} sekund")
    print(" Wciśnij CTRL+C aby zakończyć działanie programu.")
    print("=====================================================\n")
    
    while True:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Sprawdzanie...", end=" ", flush=True)
        
        is_available, status_message = check_availability(URL_TARGET)
        print(status_message)
        
        if is_available:
            trigger_alert(
                title="Dysk WD Red Pro Dostępny!", 
                message="Dysk jest teraz dostępny w sklepie Western Digital. Sprawdź klikając w link."
            )
            # Jeśli produkt zostanie znaleziony, czekamy jeszcze raz (aby nie spamować powiadomieniami)
            # Możesz tutaj dodać np. `break` jeśli program ma się wyłączyć po znalezieniu.
            time.sleep(300) # Czeka dodatkowe 5 minut przed kolejnym alertem  
            
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram zakończony przez użytkownika (CTRL+C).")
        sys.exit(0)
