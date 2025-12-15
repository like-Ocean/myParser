//  CLIENT IDENTIFICATION
function getClientId() {
    let clientId = localStorage.getItem('ws_client_id');
    if (!clientId) {
        clientId = 'client_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        localStorage.setItem('ws_client_id', clientId);
    }
    return clientId;
}

//  STATE
let ws = null;
let clientId = getClientId();
let messageCount = 0;
let wsCount = 0;
let natsCount = 0;
let createdCount = 0;
let updatedCount = 0;
let parserRunning = false;

//  WEBSOCKET CONNECTION
function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }

    ws = new WebSocket(`ws://localhost:8000/api/ws/items?client_id=${clientId}`);

    ws.onopen = () => {
        document.getElementById('status').textContent = `Connected ✓ (ID: ${clientId.slice(-8)})`;
        document.getElementById('status').className = 'status-connected';
        addMessage(`Connected as ${clientId}`, 'info', 'WebSocket', false);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        messageCount++;

        const isNats = data.type === 'nats_event';
        const source = isNats ? 'NATS' : 'WebSocket';

        if (isNats) {
            natsCount++;
            addMessage(JSON.stringify(data.data, null, 2), 'nats', source, true);
        } else {
            wsCount++;

            if (data.type === 'products_batch_created') {
                createdCount += data.data.count;
                const msg = `Batch Created: ${data.data.count} products\n\nFirst 10:\n${JSON.stringify(data.data.products, null, 2)}`;
                addMessage(msg, 'created', source, false);
            } else if (data.type === 'products_batch_updated') {
                updatedCount += data.data.count;
                const msg = `Batch Updated: ${data.data.count} products\n\nFirst 10:\n${JSON.stringify(data.data.products, null, 2)}`;
                addMessage(msg, 'updated', source, false);
            } else if (data.type === 'product_created') {
                createdCount++;
                addMessage(JSON.stringify(data, null, 2), 'created', source, false);
            } else if (data.type === 'product_updated') {
                updatedCount++;
                addMessage(JSON.stringify(data, null, 2), 'updated', source, false);
            } else if (data.type === 'product_deleted') {
                addMessage(JSON.stringify(data, null, 2), 'deleted', source, false);
            } else if (data.type === 'all_products_deleted') {
                addMessage(
                    `ALL PRODUCTS DELETED\n${data.data.message}`,
                    'deleted',
                    source,
                    false
                );
            } else if (data.type === 'pong') {
                addMessage(
                    `Pong received. Total clients: ${data.total_clients}`,
                    'success',
                    'WebSocket',
                    false
                );
            } else {
                addMessage(JSON.stringify(data, null, 2), 'success', source, false);
            }
        }

        updateStats();
    };


    ws.onerror = (error) => {
        addMessage('WebSocket Error: ' + error, 'error', 'System', false);
    };

    ws.onclose = (event) => {
        document.getElementById('status').textContent = 'Disconnected ✗';
        document.getElementById('status').className = 'status-disconnected';

        if (event.code === 1000 && event.reason === "New connection from same client") {
            addMessage('Reconnected (replaced old connection)', 'info', 'System', false);
        } else {
            addMessage('Disconnected from WebSocket', 'info', 'System', false);
        }
    };
}

function disconnect() {
    if (ws) {
        ws.close();
    }
}

function ping() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
        addMessage('→ Sent: ping', 'info', 'Client', false);
    } else {
        alert('WebSocket is not connected!');
    }
}

//  CLIENT ID MANAGEMENT
function resetClientId() {
    localStorage.removeItem('ws_client_id');
    clientId = getClientId();
    if (ws) {
        ws.close();
    }
    connect();
    addMessage(`New Client ID generated: ${clientId}`, 'info', 'System', false);
}

//  AUTO-RECONNECT
function setupAutoReconnect() {
    setInterval(() => {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
            console.log('Auto-reconnecting...');
            connect();
        }
    }, 5000);
}

//  API CALLS
async function triggerParser() {
    if (parserRunning) {
        addMessage('Parser is already running!', 'info', 'System', false);
        return;
    }

    const button = event.target;
    const originalText = button.textContent;

    button.disabled = true;
    button.innerHTML = '⏳ Running...';
    button.classList.add('btn-loading');
    parserRunning = true;

    const progressDiv = document.getElementById('parserProgress');
    const progressFill = progressDiv.querySelector('.progress-fill');
    const progressText = progressDiv.querySelector('.progress-text');

    progressDiv.style.display = 'block';
    progressFill.style.width = '30%';
    progressText.textContent = 'Starting parser...';

    addMessage('🚀 Parser started! Fetching products from page 1...', 'info', 'System', false);

    try {
        const startTime = Date.now();

        progressFill.style.width = '60%';
        progressText.textContent = 'Fetching products...';

        const response = await fetch('http://localhost:8000/api/tasks/run?start_page=1&end_page=1', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        progressFill.style.width = '90%';
        progressText.textContent = 'Processing results...';

        const result = await response.json();
        const duration = ((Date.now() - startTime) / 1000).toFixed(2);

        progressFill.style.width = '100%';
        progressText.textContent = '✅ Completed!';

        const resultMessage = `Parser completed in ${duration}s\n` +
                            `Parsed: ${result.parsed_count} products\n` +
                            `Created: ${result.created_count}\n` +
                            `Updated: ${result.updated_count}`;

        addMessage(resultMessage, 'success', 'API', false);
        addMessage('Full response:\n' + JSON.stringify(result, null, 2), 'success', 'API', false);

        setTimeout(() => {
            progressDiv.style.display = 'none';
            progressFill.style.width = '0%';
        }, 2000);

    } catch (error) {
        progressFill.style.width = '100%';
        progressFill.style.background = '#e74c3c';
        progressText.textContent = 'Failed!';

        addMessage(`Parser failed: ${error.message}`, 'error', 'API', false);

        setTimeout(() => {
            progressDiv.style.display = 'none';
            progressFill.style.width = '0%';
            progressFill.style.background = 'linear-gradient(90deg, #667eea, #764ba2)';
        }, 3000);
    } finally {
        button.disabled = false;
        button.innerHTML = originalText;
        button.classList.remove('btn-loading');
        parserRunning = false;
    }
}

// UI UPDATES
function clearMessages() {
    document.getElementById('allMessages').innerHTML = '';
    document.getElementById('natsMessages').innerHTML = '';
    messageCount = 0;
    wsCount = 0;
    natsCount = 0;
    createdCount = 0;
    updatedCount = 0;
    updateStats();
}

function updateStats() {
    document.getElementById('totalMessages').textContent = messageCount;
    document.getElementById('wsCount').textContent = wsCount;
    document.getElementById('natsCount').textContent = natsCount;
    document.getElementById('createdCount').textContent = createdCount;
    document.getElementById('updatedCount').textContent = updatedCount;
}

function addMessage(text, type, source, isNats) {
    const allMessagesDiv = document.getElementById('allMessages');
    const natsMessagesDiv = document.getElementById('natsMessages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message msg-' + type;

    const time = new Date().toLocaleTimeString();
    const badgeClass = isNats ? 'badge-nats' : 'badge-ws';

    messageDiv.innerHTML = `
        <div class="time">
            ⏰ ${time}
            <span class="source-badge ${badgeClass}">${source}</span>
        </div>
        <pre>${text}</pre>
    `;

    allMessagesDiv.insertBefore(messageDiv, allMessagesDiv.firstChild);

    if (isNats) {
        const natsMessageDiv = messageDiv.cloneNode(true);
        natsMessagesDiv.insertBefore(natsMessageDiv, natsMessagesDiv.firstChild);

        while (natsMessagesDiv.children.length > 50) {
            natsMessagesDiv.removeChild(natsMessagesDiv.lastChild);
        }
    }

    while (allMessagesDiv.children.length > 100) {
        allMessagesDiv.removeChild(allMessagesDiv.lastChild);
    }
}

// INITIALIZATION
window.onload = () => {
    connect();
    setupAutoReconnect();
};

document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
            connect();
        }
    }
});
