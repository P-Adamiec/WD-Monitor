// ========== SETTINGS & BULK ACTIONS ==========

let lastBulkClickedIndex = -1;

async function deleteTarget(sku) {
    try {
        const res = await fetch(`/api/targets/${sku}`, { method: 'DELETE' });
        if (res.ok) {
            globalTrackedSkus.delete(sku);
            renderCatalogGrid();
            fetchStatus();
        }
    } catch (e) {
        console.error(e);
    }
}

async function toggleNotify(sku) {
    try {
        const res = await fetch(`/api/targets/${sku}/toggle_notify`, { method: 'POST' });
        if (res.ok) fetchStatus();
    } catch (e) {
        console.error(e);
    }
}

async function loadDiscordWebhook() {
    try {
        const response = await fetch('/api/settings/discord');
        const data = await response.json();
        if (data.webhook) {
            document.getElementById('discord-webhook').value = data.webhook;
        }
    } catch (error) {
        console.error('Failed to load Discord webhook', error);
    }
}

async function saveDiscordWebhook() {
    const webhook = document.getElementById('discord-webhook').value;
    try {
        const response = await fetch('/api/settings/discord', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ webhook })
        });
        if (response.ok) {
            const btn = document.getElementById('save-discord-btn');
            btn.innerText = "Saved!";
            btn.style.background = "var(--success)";
            setTimeout(() => {
                btn.innerText = "Save Token";
                btn.style.background = "";
            }, 2000);
        }
    } catch (error) {
        console.error('Failed to save webhook', error);
    }
}

async function saveGlobalSettings() {
    const isSound = document.getElementById('setting-sound').checked;
    const isPush = document.getElementById('setting-push').checked;
    const isDiscord = document.getElementById('setting-discord').checked;

    globalPlaySound = isSound;
    globalSendPush = isPush;
    globalSendDiscord = isDiscord;

    const locale = document.getElementById('setting-locale');
    const localeVal = locale ? locale.value : null;

    const payload = {
        notify_sound: isSound,
        notify_push: isPush,
        notify_discord: isDiscord
    };
    if (localeVal) payload.locale = localeVal;

    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (error) {
        console.error('Failed to save settings', error);
    }
}

async function changeLocale(locale) {
    if (!locale) return;
    try {
        const res = await fetch('/api/settings/locale', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ locale })
        });
        if (res.ok) {
            currentLocale = locale;

            // Update UI buttons
            document.querySelectorAll('.region-btn').forEach(btn => btn.classList.remove('active'));
            const activeBtn = document.querySelector(`.region-btn[data-locale="${locale}"]`);
            if (activeBtn) activeBtn.classList.add('active');

            // Clear all selections — new region is a clean slate
            selectedCatalogSkus.clear();
            if (typeof clearBulkSelection === 'function') clearBulkSelection();
            updateAddButton();
            // Refresh all data for the new locale — await to avoid race condition
            await fetchStatus();
            renderCatalogGrid();
        }
    } catch (error) {
        console.error('Failed to change locale', error);
    }
}

async function toggleMonitoring() {
    const isActive = document.getElementById('setting-monitoring-active').checked;
    const isPaused = !isActive;

    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ monitoring_paused: isPaused })
        });
    } catch (error) {
        console.error('Failed to toggle monitoring', error);
    }
}

async function saveCheckInterval() {
    const val = parseInt(document.getElementById('setting-check-interval').value);
    if (isNaN(val) || val < 10) return;
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ check_interval: val })
        });
    } catch (error) {
        console.error('Failed to save check interval', error);
    }
}

// ========== NOTIFICATIONS ACCORDION ==========
function toggleNotifAccordion() {
    const header = document.querySelector('.notif-accordion-header');
    const body = document.getElementById('discord-accordion-body');
    header.classList.toggle('open');
    body.classList.toggle('open');
}

// ========== WEBHOOK TEST ==========
async function testWebhook() {
    try {
        const res = await fetch('/api/discord/test', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            alert('Test message sent to Discord!');
        } else {
            alert('Failed: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// ========== BULK ACTIONS (Tracked Products) ==========
function toggleBulkSelect(sku, event, index) {
    // Shift-click range selection
    if (event && event.shiftKey && lastBulkClickedIndex >= 0 && typeof index === 'number') {
        const start = Math.min(lastBulkClickedIndex, index);
        const end = Math.max(lastBulkClickedIndex, index);
        const allSkus = Array.from(document.querySelectorAll('.bulk-checkbox')).map(cb => cb.dataset.sku);
        for (let i = start; i <= end; i++) {
            if (allSkus[i]) bulkSelectedSkus.add(allSkus[i]);
        }
    } else {
        if (bulkSelectedSkus.has(sku)) {
            bulkSelectedSkus.delete(sku);
        } else {
            bulkSelectedSkus.add(sku);
        }
    }
    lastBulkClickedIndex = index;
    updateBulkUI();
    // Update checkboxes visually without full re-render
    document.querySelectorAll('.bulk-checkbox').forEach(cb => {
        cb.checked = bulkSelectedSkus.has(cb.dataset.sku);
        cb.closest('.status-card')?.classList.toggle('bulk-selected', cb.checked);
    });
    updateSelectAllCheckbox();
}

function toggleBulkSelectAll() {
    const allCheckboxes = document.querySelectorAll('.bulk-checkbox');
    const allSkus = Array.from(allCheckboxes).map(cb => cb.dataset.sku);
    const allSelected = allSkus.length > 0 && allSkus.every(s => bulkSelectedSkus.has(s));

    if (allSelected) {
        // Deselect all
        allSkus.forEach(s => bulkSelectedSkus.delete(s));
    } else {
        // Select all
        allSkus.forEach(s => bulkSelectedSkus.add(s));
    }
    updateBulkUI();
    allCheckboxes.forEach(cb => {
        cb.checked = bulkSelectedSkus.has(cb.dataset.sku);
        cb.closest('.status-card')?.classList.toggle('bulk-selected', cb.checked);
    });
    updateSelectAllCheckbox();
}

function updateSelectAllCheckbox() {
    const selectAll = document.getElementById('bulk-select-all');
    if (!selectAll) return;
    const allCheckboxes = document.querySelectorAll('.bulk-checkbox');
    const allSkus = Array.from(allCheckboxes).map(cb => cb.dataset.sku);
    if (allSkus.length === 0) {
        selectAll.checked = false;
        selectAll.indeterminate = false;
    } else if (allSkus.every(s => bulkSelectedSkus.has(s))) {
        selectAll.checked = true;
        selectAll.indeterminate = false;
    } else if (allSkus.some(s => bulkSelectedSkus.has(s))) {
        selectAll.checked = false;
        selectAll.indeterminate = true;
    } else {
        selectAll.checked = false;
        selectAll.indeterminate = false;
    }
}

function updateBulkUI() {
    const bar = document.getElementById('bulk-actions');
    const count = document.getElementById('bulk-count');
    if (bulkSelectedSkus.size > 0) {
        bar.style.display = 'flex';
        count.textContent = `${bulkSelectedSkus.size} selected`;
    } else {
        bar.style.display = 'none';
    }
}

function clearBulkSelection() {
    bulkSelectedSkus.clear();
    lastBulkClickedIndex = -1;
    updateBulkUI();
    updateSelectAllCheckbox();
    fetchStatus();
}

async function bulkDelete() {
    try {
        const res = await fetch('/api/targets/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skus: [...bulkSelectedSkus] })
        });
        if (res.ok) {
            bulkSelectedSkus.clear();
            fetchStatus();
        }
    } catch (e) {
        console.error('Bulk delete error', e);
    }
}

async function bulkToggleNotify() {
    for (const sku of bulkSelectedSkus) {
        try {
            await fetch(`/api/targets/${sku}/toggle_notify`, { method: 'POST' });
        } catch (e) {
            console.error('Toggle notify error', e);
        }
    }
    bulkSelectedSkus.clear();
    fetchStatus();
}

// Load discord webhook on page ready
window.addEventListener('DOMContentLoaded', () => {
    loadDiscordWebhook();
});
