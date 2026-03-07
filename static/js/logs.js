// ========== LOGS MODAL ==========

function openLogsModal() {
    const modal = document.getElementById('logs-modal');
    modal.classList.add('active');
    renderLogsModal();
}

function closeLogsModal() {
    document.getElementById('logs-modal').classList.remove('active');
}

function renderLogsModal() {
    const container = document.getElementById('logs-list');
    container.innerHTML = '';
    if (systemLogsData.length === 0) {
        container.innerHTML = '<li class="history-item" style="color:var(--text-secondary)">No activity logs yet.</li>';
        return;
    }
    systemLogsData.forEach(log => {
        const li = document.createElement('li');
        li.className = 'history-item';
        li.style.display = 'flex';
        li.style.alignItems = 'flex-start';
        li.style.gap = '8px';

        // Color-coded tag by log_type
        const logType = log.log_type || 'status_change';
        let tagText, tagColor;
        switch (logType) {
            case 'available':
                tagText = 'IN STOCK'; tagColor = '#10b981'; break;
            case 'sold_out':
                tagText = 'SOLD'; tagColor = '#ef4444'; break;
            case 'unavailable':
                tagText = 'OUT'; tagColor = '#ef4444'; break;
            case 'tracking_started':
                tagText = 'TRACKING'; tagColor = '#60a5fa'; break;
            case 'error':
                tagText = 'ERROR'; tagColor = '#f59e0b'; break;
            case 'price_drop':
                tagText = '↓ PRICE'; tagColor = '#22c55e'; break;
            case 'price_increase':
                tagText = '↑ PRICE'; tagColor = '#f59e0b'; break;
            default:
                tagText = 'INFO'; tagColor = '#9aa0a6'; break;
        }

        li.innerHTML = `
            <span style="flex-shrink:0;min-width:120px;color:var(--text-secondary);font-size:0.8rem;">${toLocalDateTime(log.time)}</span>
            <span style="flex-shrink:0;display:inline-block;width:70px;text-align:center;background:${tagColor};color:#000;font-size:0.65rem;font-weight:700;padding:2px 0;border-radius:3px;">${tagText}</span>
            <span style="color:${tagColor};font-size:0.85rem;word-break:break-word;">${log.status}</span>
        `;
        container.appendChild(li);
    });
}

async function clearLogs(scope) {
    if (!confirm(`Clear ${scope === 'all' ? 'ALL' : scope === 'day' ? 'last 24h' : 'last hour'} logs?`)) return;
    try {
        const res = await fetch(`/api/logs/clear?scope=${scope}`, { method: 'POST' });
        if (res.ok) {
            await fetchStatus();
            renderLogsModal();
        }
    } catch (e) {
        console.error(e);
    }
}
