// ========== CATALOG ==========

let catalogData = [];
let selectedModels = new Set();
let selectedCategories = new Set();
let selectedCapacities = new Set();
let lastCatalogClickedIndex = -1;
let currentFilteredProducts = [];

const CATEGORY_LABELS = {
    'standard': '🟢 Standard',
    'clearance': '🔴 Clearance'
};

async function fetchCatalog() {
    try {
        const res = await fetch('/api/catalog');
        catalogData = await res.json();
        renderCategoryFilters();
        renderModelFilters();
        renderCapacityFilters();
        renderCatalogGrid();
    } catch (err) {
        console.error("Failed to load catalog", err);
    }
}

let availableSkusToDraft = [];

function renderCategoryFilters() {
    const container = document.getElementById('category-filters');
    container.innerHTML = '';
    const catCounts = {};
    catalogData.forEach(p => {
        const cat = p.category || 'standard';
        catCounts[cat] = (catCounts[cat] || 0) + 1;
    });

    Object.keys(CATEGORY_LABELS).forEach(cat => {
        if (!catCounts[cat]) return;
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.value = cat;
        cb.className = 'custom-checkbox';
        cb.onchange = (e) => {
            if (e.target.checked) selectedCategories.add(cat);
            else selectedCategories.delete(cat);
            renderModelFilters();
            renderCapacityFilters();
            renderCatalogGrid();
        };
        const customBox = document.createElement('span');
        customBox.className = 'checkmark';
        const textNode = document.createElement('span');
        textNode.className = 'checkbox-text';
        textNode.innerText = CATEGORY_LABELS[cat];
        const countSpan = document.createElement('span');
        countSpan.className = 'item-count';
        countSpan.innerText = `(${catCounts[cat]})`;
        label.appendChild(cb);
        label.appendChild(customBox);
        label.appendChild(textNode);
        label.appendChild(countSpan);
        container.appendChild(label);
    });
}

function renderModelFilters() {
    const container = document.getElementById('model-filters');
    container.innerHTML = '';

    const seriesCounts = {};
    catalogData.forEach(p => {
        if (selectedCategories.size > 0 && !selectedCategories.has(p.category || 'standard')) return;
        if (selectedCapacities.size > 0 && !selectedCapacities.has(p.capacity || '')) return;
        const s = p.series;
        seriesCounts[s] = (seriesCounts[s] || 0) + 1;
    });

    const seriesKeys = Object.keys(seriesCounts).sort((a, b) => a.localeCompare(b));

    for (const model of seriesKeys) {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.value = model;
        cb.className = 'custom-checkbox';
        cb.checked = selectedModels.has(model);
        cb.onchange = (e) => {
            if (e.target.checked) selectedModels.add(model);
            else selectedModels.delete(model);
            renderCapacityFilters();
            renderCatalogGrid();
        };
        const customBox = document.createElement('span');
        customBox.className = 'checkmark';
        const textNode = document.createElement('span');
        textNode.className = 'checkbox-text';
        textNode.innerText = model;
        const countSpan = document.createElement('span');
        countSpan.className = 'item-count';
        countSpan.innerText = `(${seriesCounts[model]})`;
        label.appendChild(cb);
        label.appendChild(customBox);
        label.appendChild(textNode);
        label.appendChild(countSpan);
        container.appendChild(label);
    }
}

function renderCapacityFilters() {
    const container = document.getElementById('capacity-filters');
    container.innerHTML = '';

    const capCounts = {};
    catalogData.forEach(p => {
        if (selectedCategories.size > 0 && !selectedCategories.has(p.category || 'standard')) return;
        if (selectedModels.size > 0 && !selectedModels.has(p.series)) return;
        const cap = p.capacity || '';
        if (!cap) return;
        capCounts[cap] = (capCounts[cap] || 0) + 1;
    });

    const parseCapValue = (c) => {
        const m = c.match(/[\d.]+/);
        if (!m) return 0;
        let val = parseFloat(m[0]);
        if (c.includes('GB')) val /= 1000;
        return val;
    };
    const sortedCaps = Object.keys(capCounts).sort((a, b) => parseCapValue(a) - parseCapValue(b));

    sortedCaps.forEach(cap => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.value = cap;
        cb.className = 'custom-checkbox';
        cb.checked = selectedCapacities.has(cap);
        cb.onchange = (e) => {
            if (e.target.checked) selectedCapacities.add(cap);
            else selectedCapacities.delete(cap);
            renderModelFilters();
            renderCatalogGrid();
        };
        const customBox = document.createElement('span');
        customBox.className = 'checkmark';
        const textNode = document.createElement('span');
        textNode.className = 'checkbox-text';
        textNode.innerText = cap;
        const countSpan = document.createElement('span');
        countSpan.className = 'item-count';
        countSpan.innerText = `(${capCounts[cap]})`;
        label.appendChild(cb);
        label.appendChild(customBox);
        label.appendChild(textNode);
        label.appendChild(countSpan);
        container.appendChild(label);
    });
}

function toggleCatalogSelection(sku, event, index) {
    // Shift-click range selection
    if (event && event.shiftKey && lastCatalogClickedIndex >= 0 && typeof index === 'number') {
        const start = Math.min(lastCatalogClickedIndex, index);
        const end = Math.max(lastCatalogClickedIndex, index);
        for (let i = start; i <= end; i++) {
            const p = currentFilteredProducts[i];
            if (p && !globalTrackedSkus.has(p.sku)) {
                selectedCatalogSkus.add(p.sku);
            }
        }
    } else {
        if (selectedCatalogSkus.has(sku)) {
            selectedCatalogSkus.delete(sku);
        } else {
            selectedCatalogSkus.add(sku);
        }
    }
    lastCatalogClickedIndex = index;
    updateAddButton();
    updateCatalogCardVisuals();
    updateCatalogSelectAllCheckbox();
}

function toggleCatalogSelectAll() {
    const selectableSkus = currentFilteredProducts
        .filter(p => !globalTrackedSkus.has(p.sku))
        .map(p => p.sku);

    const allSelected = selectableSkus.length > 0 && selectableSkus.every(s => selectedCatalogSkus.has(s));

    if (allSelected) {
        selectableSkus.forEach(s => selectedCatalogSkus.delete(s));
    } else {
        selectableSkus.forEach(s => selectedCatalogSkus.add(s));
    }

    updateAddButton();
    updateCatalogCardVisuals();
    updateCatalogSelectAllCheckbox();
}

function updateCatalogCardVisuals() {
    document.querySelectorAll('.catalog-checkbox').forEach(cb => {
        const isSelected = selectedCatalogSkus.has(cb.dataset.sku);
        cb.checked = isSelected;
        const card = cb.closest('.store-card');
        if (card) card.classList.toggle('catalog-selected', isSelected);
    });
}


function updateCatalogSelectAllCheckbox() {
    const selectAll = document.getElementById('catalog-select-all');
    if (!selectAll) return;

    const selectableSkus = currentFilteredProducts
        .filter(p => !globalTrackedSkus.has(p.sku))
        .map(p => p.sku);

    if (selectableSkus.length === 0) {
        selectAll.checked = false;
        selectAll.indeterminate = false;
    } else if (selectableSkus.every(s => selectedCatalogSkus.has(s))) {
        selectAll.checked = true;
        selectAll.indeterminate = false;
    } else if (selectableSkus.some(s => selectedCatalogSkus.has(s))) {
        selectAll.checked = false;
        selectAll.indeterminate = true;
    } else {
        selectAll.checked = false;
        selectAll.indeterminate = false;
    }
}

function updateAddButton() {
    const btn = document.getElementById('add-target-btn');
    const count = selectedCatalogSkus.size;
    btn.innerText = `${t('track_selected')} (${count})`;
    btn.disabled = count === 0;
}

function getDriveImage(series) {
    const s = series.toLowerCase();
    if (s.includes("red pro")) return "/static/images/wd_red_pro.png";
    if (s.includes("red plus")) return "/static/images/wd_red_plus.png";
    if (s.includes("red")) return "/static/images/wd_wd_red.png";
    if (s.includes("purple pro")) return "/static/images/wd_purple_pro.png";
    if (s.includes("purple")) return "/static/images/wd_wd_purple.png";
    if (s.includes("gold")) return "/static/images/wd_gold.png";
    if (s.includes("black")) return "/static/images/wd_wd_black.png";
    if (s.includes("blue")) return "/static/images/wd_wd_blue.png";
    if (s.includes("ultrastar")) return "/static/images/wd_ultrastar.png";
    if (s.includes("my passport ultra for mac")) return "/static/images/wd_my_passport_ultra_for_mac.png";
    if (s.includes("my passport for mac")) return "/static/images/wd_my_passport_for_mac.png";
    if (s.includes("my passport ultra")) return "/static/images/wd_my_passport_ultra.png";
    if (s.includes("my passport")) return "/static/images/wd_my_passport.png";
    if (s.includes("elements se")) return "/static/images/wd_wd_elements_portable.png";
    if (s.includes("elements portable")) return "/static/images/wd_wd_elements_portable.png";
    if (s.includes("elements desktop")) return "/static/images/wd_wd_elements_desktop.png";
    if (s.includes("my book duo")) return "/static/images/wd_my_book_duo.png";
    if (s.includes("my book")) return "/static/images/wd_my_book.png";
    if (s.includes("gaming drive")) return "/static/images/wd_wd_black.png";
    if (s.includes("chromebook")) return "/static/images/wd_my_passport.png";
    return "/static/images/wd_red_plus.png";
}

function renderCatalogGrid() {
    const container = document.getElementById('catalog-container');
    container.innerHTML = '';

    let filtered = catalogData.slice();

    if (selectedCategories.size > 0) {
        filtered = filtered.filter(p => selectedCategories.has(p.category || 'standard'));
    }
    if (selectedModels.size > 0) {
        filtered = filtered.filter(p => selectedModels.has(p.series));
    }
    if (selectedCapacities.size > 0) {
        filtered = filtered.filter(p => selectedCapacities.has(p.capacity || ''));
    }

    const parseCapacity = (cap) => {
        if (!cap) return 0;
        const m = cap.match(/(\d+)\s*(TB|GB)/i);
        if (!m) return 0;
        const val = parseInt(m[1]);
        return m[2].toUpperCase() === 'TB' ? val * 1024 : val;
    };
    filtered.sort((a, b) => {
        if (a.series !== b.series) return a.series.localeCompare(b.series);
        return parseCapacity(a.capacity) - parseCapacity(b.capacity);
    });

    // Store filtered list for select-all
    currentFilteredProducts = filtered;

    filtered.forEach((product, index) => {
        const isTracked = globalTrackedSkus.has(product.sku);
        const card = document.createElement('div');
        card.className = `store-card ${isTracked ? 'tracked-dimmed' : ''}`;

        const catBadge = product.category !== 'standard'
            ? `<span class="store-card-cat-badge cat-${product.category}">${product.category}</span>`
            : '';

        // Use current locale instead of hardcoded pl-pl
        const locale = typeof currentLocale !== 'undefined' ? currentLocale : 'pl-pl';
        const shopUrl = product.url_path
            ? `https://www.westerndigital.com/${locale}/products/${product.url_path}?sku=${product.sku}`
            : `https://www.westerndigital.com/${locale}/search?q=${product.sku}`;

        card.innerHTML = `
            <div class="store-card-image">
                <input type="checkbox" class="catalog-checkbox" data-sku="${product.sku}"
                       onclick="toggleCatalogSelection('${product.sku}', event, ${index})"
                       ${selectedCatalogSkus.has(product.sku) ? 'checked' : ''}
                       ${isTracked ? 'disabled' : ''}>
                <a href="${shopUrl}" target="_blank" class="store-card-shop-link" title="Open in store"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg></a>
                <img src="${getDriveImage(product.series)}" alt="${product.series}">
            </div>
            <div class="store-card-content">
                <div class="store-card-series">${product.series} ${catBadge}</div>
                <div class="store-card-capacity">${product.capacity || ''}</div>
                <div class="store-card-sku">${product.sku}</div>
            </div>
        `;
        container.appendChild(card);
    });

    updateCatalogSelectAllCheckbox();
}

async function refreshCatalog() {
    const btn = document.getElementById('refresh-catalog-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Refreshing...';
    try {
        const res = await fetch('/api/catalog/refresh', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
            const catRes = await fetch('/api/catalog');
            catalogData = await catRes.json();
            renderCategoryFilters();
            renderModelFilters();
            renderCapacityFilters();
            renderCatalogGrid();
            btn.textContent = `✅ Done (${data.count})`;
            setTimeout(() => { btn.textContent = '🔄 Refresh'; btn.disabled = false; }, 2000);
        } else {
            btn.textContent = '❌ Error';
            setTimeout(() => { btn.textContent = '🔄 Refresh'; btn.disabled = false; }, 2000);
        }
    } catch (e) {
        console.error(e);
        btn.textContent = '❌ Error';
        setTimeout(() => { btn.textContent = '🔄 Refresh'; btn.disabled = false; }, 2000);
    }
}

async function addSelectedTargets() {
    if (selectedCatalogSkus.size === 0) return;

    const btn = document.getElementById('add-target-btn');
    btn.disabled = true;
    btn.innerText = 'Adding...';

    const skusToDraft = Array.from(selectedCatalogSkus);

    try {
        const res = await fetch('/api/targets/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skus: skusToDraft })
        });
        const result = await res.json();

        if (result.error) {
            alert(result.error);
        } else {
            selectedCatalogSkus.clear();
            renderCatalogGrid();
            fetchStatus();
        }
    } catch (e) {
        console.error("Batch add failed", e);
        alert("Communication error with the API.");
    } finally {
        updateAddButton();
    }
}

// Load catalog on page load
fetchCatalog();
