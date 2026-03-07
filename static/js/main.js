// ========== MAIN STATE & CORE FUNCTIONS ==========

let hasAlertedFor = {};
let globalPlaySound = true;
let globalSendPush = true;
let globalSendDiscord = true;
let selectedCatalogSkus = new Set();
let currentSortOrder = 'desc';
let systemLogsData = [];
let bulkSelectedSkus = new Set();
let globalTrackedSkus = new Set();
let currentLocale = 'pl-pl';
let currentTargetsList = [];

// Convert UTC timestamp to local time
function toLocalTime(utcStr) {
    if (!utcStr || utcStr === '--:--') return '--:--';
    try {
        const d = new Date(utcStr + 'Z');
        return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
        return utcStr.split(' ')[1] || utcStr;
    }
}

function toLocalDateTime(utcStr) {
    if (!utcStr) return '';
    try {
        const d = new Date(utcStr + 'Z');
        return d.toLocaleString('en-GB', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
        return utcStr;
    }
}

function toggleSortOrder() {
    currentSortOrder = currentSortOrder === 'desc' ? 'asc' : 'desc';
    document.getElementById('sort-icon').textContent = currentSortOrder === 'desc' ? '↓' : '↑';
    document.getElementById('sort-label').textContent = currentSortOrder === 'desc' ? t('newest') : t('oldest');
    fetchStatus();
}

async function fetchStatus() {
    try {
        const response = await fetch(`/api/status?sort=${currentSortOrder}`);
        const data = await response.json();

        if (data.settings) {
            globalPlaySound = (data.settings.notify_sound || 'true').toLowerCase() === 'true';
            globalSendDiscord = (data.settings.notify_discord || 'true').toLowerCase() === 'true';
            globalSendPush = (data.settings.notify_push || 'true').toLowerCase() === 'true';

            document.getElementById('setting-sound').checked = globalPlaySound;
            document.getElementById('setting-push').checked = globalSendPush;
            document.getElementById('setting-discord').checked = globalSendDiscord;

            const isPaused = data.settings.monitoring_paused === 'true';
            document.getElementById('setting-monitoring-active').checked = !isPaused;

            const intervalInput = document.getElementById('setting-check-interval');
            if (intervalInput && data.settings.check_interval) {
                intervalInput.value = data.settings.check_interval;
            }

            if (data.settings.locale) {
                currentLocale = data.settings.locale;
                document.querySelectorAll('.region-btn').forEach(btn => btn.classList.remove('active'));
                const activeBtn = document.querySelector(`.region-btn[data-locale="${currentLocale}"]`);
                if (activeBtn) activeBtn.classList.add('active');
            }
        }

        systemLogsData = data.history || [];

        updateUI(data);
        checkAlerts(data.targets);

    } catch (error) {
        console.error('Failed to fetch status', error);
    }
}

function updateUI(data) {
    const targetsContainer = document.getElementById('targets-container');
    const statusRing = document.getElementById('status-ring');

    targetsContainer.innerHTML = '';

    let anyAvailable = false;

    globalTrackedSkus.clear();
    currentTargetsList = data.targets || [];

    data.targets.forEach((target, index) => {
        globalTrackedSkus.add(target.sku);
        if (target.is_available) anyAvailable = true;

        const card = document.createElement('div');
        card.className = 'status-card compact';
        if (bulkSelectedSkus.has(target.sku)) card.classList.add('bulk-selected');

        const isInquiry = target.status === 'Inquiry Only';
        const statusClass = target.status === 'Oczekiwanie...' ? 'loading' : (target.is_available && !isInquiry ? 'available' : (isInquiry ? 'inquiry' : 'unavailable'));
        const statusText = isInquiry ? t('inquiry') : (target.is_available ? t('in_stock') : (target.status === 'Oczekiwanie...' ? t('pending') : t('out_of_stock')));
        const statusDot = isInquiry ? '🟠' : (target.is_available ? '🟢' : (target.status === 'Oczekiwanie...' ? '🟡' : '🔴'));

        const isNotifyOn = target.notify !== false;
        const stockLevel = target.stock_level || 0;
        const stockBadge = stockLevel > 0 ? `<span class="stock-badge">${stockLevel} ${t('left')}</span>` : '';

        // Build URL using current locale
        const storeUrl = target.url ? target.url.replace(/\/[a-z]{2}-[a-z]{2}\//, `/${currentLocale}/`) : target.url;

        card.innerHTML = `
            <div class="compact-card-top">
                <div class="compact-card-info" style="display:flex;gap:8px;align-items:flex-start;">
                    <input type="checkbox" class="bulk-checkbox" data-sku="${target.sku}" ${bulkSelectedSkus.has(target.sku) ? 'checked' : ''}
                        onclick="toggleBulkSelect('${target.sku}', event, ${index})" title="Select for bulk action"
                        style="margin-top:3px;cursor:pointer;accent-color:var(--primary);flex-shrink:0;">
                    <div>
                        <div class="compact-card-name">${target.name}</div>
                        <div class="compact-card-meta">
                            <span class="sku-badge-sm">${target.sku}</span>
                            <span class="price-badge-sm">${target.price || '—'}</span>
                            ${stockBadge}
                        </div>
                    </div>
                </div>
                <div class="compact-card-status">
                    <span class="status-dot-text ${statusClass}">${statusDot} ${statusText}</span>
                </div>
            </div>
            <div class="compact-card-bottom">
                <span class="compact-card-time">${t('last_check')} ${toLocalTime(target.last_check)}</span>
                <div class="compact-card-actions">
                    <a href="${storeUrl}" target="_blank" class="action-btn-sm" title="Open in store">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                    </a>
                    <button class="action-btn-sm" onclick="openHistoryModal('${target.sku}', '${target.name.replace(/'/g, "\\'")}')" title="Price history">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                    </button>
                    <button class="action-btn-sm ${isNotifyOn ? '' : 'muted'}" onclick="toggleNotify('${target.sku}')" title="Toggle notifications">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                    </button>
                    <button class="action-btn-sm danger" onclick="deleteTarget('${target.sku}')" title="Remove">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            </div>
        `;
        targetsContainer.appendChild(card);
    });

    statusRing.className = 'pulse-ring';
    if (anyAvailable) {
        statusRing.classList.add('ring-available');
    } else if (data.targets.length > 0 && !data.targets[0].status.includes('Oczekiwanie')) {
        statusRing.classList.add('ring-unavailable');
    }

    updateBulkUI();
    updateSelectAllCheckbox();
}

function checkAlerts(targets) {
    targets.forEach(target => {
        if (target.is_available && target.notify !== false && target.status !== 'Oczekiwanie...') {
            if (!hasAlertedFor[target.sku]) {
                triggerAlert(target.name);
                hasAlertedFor[target.sku] = true;
            }
        } else if (!target.is_available || target.notify === false) {
            hasAlertedFor[target.sku] = false;
        }
    });
}

function triggerAlert(productName) {
    if (globalPlaySound) {
        const audio = document.getElementById('alert-sound');
        audio.play().catch(e => console.log('Autoplay blocked'));
    }

    if (globalSendPush && Notification.permission === 'granted') {
        new Notification('WD Drive In Stock!', {
            body: `${productName} is now available. Click to visit the store.`,
            icon: 'https://www.westerndigital.com/content/dam/store/en-us/assets/favicon/favicon.ico'
        });
    }
}

document.body.addEventListener('click', () => {
    if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
        Notification.requestPermission();
    }
}, { once: true });

// Auto-refresh every 5 seconds
setInterval(fetchStatus, 5000);
fetchStatus();
