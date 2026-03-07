// ========== PRICE HISTORY CHART MODAL ==========

let priceChart = null;
let currentHistorySku = '';
let currentHistoryMonths = 3;

async function openHistoryModal(sku, name) {
    currentHistorySku = sku;
    currentHistoryMonths = 3;
    document.getElementById('modal-sku-subtitle').innerText = sku;
    document.getElementById('modal-product-name').innerText = name;

    const modal = document.getElementById('price-history-modal');
    modal.classList.add('active');

    updateRangeButtons(3);
    await loadHistory(sku, 3);
}

function closeHistoryModal() {
    const modal = document.getElementById('price-history-modal');
    modal.classList.remove('active');
    if (priceChart) {
        priceChart.destroy();
        priceChart = null;
    }
}

async function changeHistoryRange(months) {
    currentHistoryMonths = months;
    updateRangeButtons(months);
    await loadHistory(currentHistorySku, months);
}

function updateRangeButtons(activeMonths) {
    document.querySelectorAll('.range-btn').forEach(btn => {
        const m = parseInt(btn.dataset.months);
        btn.classList.toggle('active', m === activeMonths);
    });
}

async function loadHistory(sku, months) {
    try {
        const res = await fetch(`/api/targets/${sku}/history?months=${months}`);
        const result = await res.json();
        if (result.success) {
            renderChart(result.history, sku);
        }
    } catch (err) {
        console.error('Failed to load price history:', err);
    }
}

function parsePlnPrice(priceStr) {
    if (!priceStr) return null;
    let cleaned = priceStr.replace(/zł/ig, '').trim();
    cleaned = cleaned.replace(/\s+/g, '').replace(/,/g, '.');
    return parseFloat(cleaned);
}

function renderChart(historyData, sku) {
    const ctx = document.getElementById('priceHistoryChart').getContext('2d');

    if (priceChart) {
        priceChart.destroy();
    }

    if (historyData.length === 0) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.font = '20px Outfit';
        ctx.fillStyle = '#9aa0a6';
        ctx.textAlign = 'center';
        ctx.fillText('No price data in this time range.', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }

    const labels = [];
    const dataPoints = [];
    const availabilityFlags = [];

    historyData.forEach(entry => {
        const localLabel = toLocalDateTime(entry.logged_at);
        labels.push(localLabel);
        const p = parsePlnPrice(entry.price);
        dataPoints.push(p !== null ? p : 0);
        availabilityFlags.push(entry.is_available !== false);
    });

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price',
                data: dataPoints,
                borderWidth: 3,
                pointRadius: 4,
                pointHoverRadius: 7,
                fill: true,
                tension: 0.3,
                segment: {
                    borderColor: ctx2 => {
                        const prevIdx = ctx2.p0DataIndex;
                        const nextIdx = ctx2.p1DataIndex;
                        const prevAvail = availabilityFlags[prevIdx];
                        const nextAvail = availabilityFlags[nextIdx];
                        if (prevAvail && nextAvail) return '#10b981';
                        if (!prevAvail && !nextAvail) return '#ef4444';
                        return '#f59e0b';
                    },
                    backgroundColor: ctx2 => {
                        const prevAvail = availabilityFlags[ctx2.p0DataIndex];
                        const nextAvail = availabilityFlags[ctx2.p1DataIndex];
                        if (prevAvail && nextAvail) return 'rgba(16, 185, 129, 0.15)';
                        if (!prevAvail && !nextAvail) return 'rgba(239, 68, 68, 0.15)';
                        return 'rgba(245, 158, 11, 0.1)';
                    }
                },
                pointBackgroundColor: (ctx2) => {
                    const idx = ctx2.dataIndex;
                    return availabilityFlags[idx] ? '#10b981' : '#ef4444';
                },
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const idx = context.dataIndex;
                            const status = availabilityFlags[idx] ? '🟢 In Stock' : '🔴 Out of Stock';
                            return context.parsed.y + ' PLN  ·  ' + status;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { color: '#9aa0a6', maxRotation: 45, maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { color: '#9aa0a6', callback: v => v + ' PLN' }
                }
            }
        }
    });
}
