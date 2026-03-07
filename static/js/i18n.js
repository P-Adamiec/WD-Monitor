// ========== INTERNATIONALIZATION (i18n) ==========

const TRANSLATIONS = {
    en: {
        subtitle: 'Live multi-product availability tracker',
        tracked_products: 'Tracked Products',
        product_catalog: 'Product Catalog',
        filter_products: 'Filter Products',
        category: 'Category',
        drive_series: 'Drive Series',
        capacity: 'Capacity',
        discord_notifications: 'Discord Notifications',
        monitoring: 'Monitoring',
        store_region: 'Store Region',
        notification_channels: 'Notification Channels',
        monitor_products: 'Monitor products',
        play_alert_sound: 'Play alert sound',
        browser_notifications: 'Browser notifications',
        send_discord: 'Send Discord messages',
        logs: 'Logs',
        refresh: 'Refresh',
        delete: 'Delete',
        system_logs: 'System Logs',
        clear_last_hour: 'Clear Last Hour',
        clear_last_day: 'Clear Last Day',
        clear_all: 'Clear All',
        price_history: 'Price History',
        in_stock: 'In Stock',
        out_of_stock: 'Out of Stock',
        pending: 'Pending...',
        inquiry: 'Inquiry',
        last_check: 'Last',
        select_all: 'Select all',
        notifications: 'Notifications',
        discord_webhook: 'Discord Webhook',
        standard: 'Standard',
        clearance: 'Clearance',
        track_selected: 'Track Selected',
        newest: 'Newest',
        oldest: 'Oldest',
        no_products: 'No tracked products yet',
        back_in_stock: 'Back in stock!',
        sold_out: 'Sold out',
        price_dropped: 'Price dropped',
        price_increased: 'Price increased',
        started_tracking: 'Started tracking',
        region_changed: 'Store region changed to',
        test_webhook: 'Test',
        save: 'Save',
        check_interval: 'Interval',
        left: 'left'
    },
    pl: {
        subtitle: 'Monitor dostępności produktów w czasie rzeczywistym',
        tracked_products: 'Śledzone produkty',
        product_catalog: 'Katalog produktów',
        filter_products: 'Filtruj produkty',
        category: 'Kategoria',
        drive_series: 'Seria dysków',
        capacity: 'Pojemność',
        discord_notifications: 'Powiadomienia Discord',
        monitoring: 'Monitoring',
        store_region: 'Region sklepu',
        notification_channels: 'Kanały powiadomień',
        monitor_products: 'Monitoruj produkty',
        play_alert_sound: 'Odtwarzaj dźwięk alertu',
        browser_notifications: 'Powiadomienia przeglądarki',
        send_discord: 'Wyślij wiadomości Discord',
        logs: 'Logi',
        refresh: 'Odśwież',
        delete: 'Usuń',
        system_logs: 'Logi systemowe',
        clear_last_hour: 'Wyczyść ostatnią godzinę',
        clear_last_day: 'Wyczyść ostatni dzień',
        clear_all: 'Wyczyść wszystko',
        price_history: 'Historia cen',
        in_stock: 'Dostępny',
        out_of_stock: 'Niedostępny',
        pending: 'Oczekiwanie...',
        inquiry: 'Zapytanie',
        last_check: 'Ost.',
        select_all: 'Zaznacz wszystkie',
        notifications: 'Powiadomienia',
        discord_webhook: 'Webhook Discord',
        standard: 'Standardowe',
        clearance: 'Wyprzedaż',
        track_selected: 'Śledź zaznaczone',
        newest: 'Najnowsze',
        oldest: 'Najstarsze',
        no_products: 'Brak śledzonych produktów',
        back_in_stock: 'Ponownie dostępny!',
        sold_out: 'Wyprzedany',
        price_dropped: 'Cena spadła',
        price_increased: 'Cena wzrosła',
        started_tracking: 'Rozpoczęto śledzenie',
        region_changed: 'Region zmieniony na',
        test_webhook: 'Testuj',
        save: 'Zapisz',
        check_interval: 'Interwał',
        left: 'szt.'
    },
    de: {
        subtitle: 'Live-Verfügbarkeitstracker für mehrere Produkte',
        tracked_products: 'Verfolgte Produkte',
        product_catalog: 'Produktkatalog',
        filter_products: 'Produkte filtern',
        category: 'Kategorie',
        drive_series: 'Festplattenserie',
        capacity: 'Kapazität',
        discord_notifications: 'Discord-Benachrichtigungen',
        monitoring: 'Überwachung',
        store_region: 'Shop-Region',
        notification_channels: 'Benachrichtigungskanäle',
        monitor_products: 'Produkte überwachen',
        play_alert_sound: 'Alarmton abspielen',
        browser_notifications: 'Browser-Benachrichtigungen',
        send_discord: 'Discord-Nachrichten senden',
        logs: 'Protokolle',
        refresh: 'Aktualisieren',
        delete: 'Löschen',
        system_logs: 'Systemprotokolle',
        clear_last_hour: 'Letzte Stunde löschen',
        clear_last_day: 'Letzten Tag löschen',
        clear_all: 'Alle löschen',
        price_history: 'Preisverlauf',
        in_stock: 'Auf Lager',
        out_of_stock: 'Nicht verfügbar',
        pending: 'Ausstehend...',
        inquiry: 'Anfrage',
        last_check: 'Zuletzt',
        select_all: 'Alle auswählen',
        notifications: 'Benachrichtigungen',
        discord_webhook: 'Discord-Webhook',
        standard: 'Standard',
        clearance: 'Ausverkauf',
        track_selected: 'Ausgewählte verfolgen',
        newest: 'Neueste',
        oldest: 'Älteste',
        no_products: 'Noch keine verfolgten Produkte',
        back_in_stock: 'Wieder auf Lager!',
        sold_out: 'Ausverkauft',
        price_dropped: 'Preis gesunken',
        price_increased: 'Preis gestiegen',
        started_tracking: 'Verfolgung gestartet',
        region_changed: 'Shop-Region geändert zu',
        test_webhook: 'Testen',
        save: 'Speichern',
        check_interval: 'Intervall',
        left: 'übrig'
    }
};

let currentLang = localStorage.getItem('wd_monitor_lang') || 'en';

function setLanguage(lang) {
    if (!TRANSLATIONS[lang]) return;
    currentLang = lang;
    localStorage.setItem('wd_monitor_lang', lang);
    applyTranslations();
    // Update active flag button style
    document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
    const flags = document.querySelectorAll('.lang-btn');
    const langIndex = { 'pl': 0, 'en': 1, 'de': 2 };
    if (flags[langIndex[lang]]) flags[langIndex[lang]].classList.add('active');

    // Force re-render of dynamic elements to apply new translations instantly
    if (typeof updateUI === 'function' && typeof currentTargetsList !== 'undefined') {
        updateUI({ targets: currentTargetsList });
    }
    if (typeof renderCatalogGrid === 'function') {
        renderCatalogGrid();
    }
}

function applyTranslations() {
    const t = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            el.textContent = t[key];
        }
    });
}

function t(key) {
    const trans = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    return trans[key] || TRANSLATIONS.en[key] || key;
}

// Apply on load
window.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
    // Highlight active lang button
    const flags = document.querySelectorAll('.lang-btn');
    const langIndex = { 'pl': 0, 'en': 1, 'de': 2 };
    if (flags[langIndex[currentLang]]) flags[langIndex[currentLang]].classList.add('active');
});
