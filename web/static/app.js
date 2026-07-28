/**
 * 🏹 Cupid Bot Lab - Frontend Application
 * VinUni Lab 3: Chatbot vs ReAct Agent
 */

// === State ===
let currentMode = 'both';
let testCases = [];
let history = [];
let activeTestId = null;

// === Initialize ===
document.addEventListener('DOMContentLoaded', () => {
    loadProviderInfo();
    loadTestCases();
    loadTools();
    setupEventListeners();
});

// === Event Listeners ===
function setupEventListeners() {
    // Mode buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;
        });
    });

    // Enter to send
    document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery();
        }
    });
}

// === API Calls ===
async function loadProviderInfo() {
    try {
        const res = await fetch('/api/provider-info');
        const data = await res.json();
        if (data.success) {
            const info = data.data;
            document.getElementById('providerName').textContent =
                `${info.provider} • ${info.model}`;
        }
    } catch (err) {
        document.getElementById('providerName').textContent = 'Connection Error';
    }
}

async function loadTestCases() {
    try {
        const res = await fetch('/api/test-cases');
        const data = await res.json();
        if (data.success) {
            testCases = data.data;
            renderTestCases(testCases);
            document.getElementById('testCount').textContent = `${testCases.length} cases`;
        }
    } catch (err) {
        console.error('Failed to load test cases:', err);
    }
}

async function loadTools() {
    try {
        const res = await fetch('/api/tools');
        const data = await res.json();
        if (data.success) {
            renderTools(data.data);
        }
    } catch (err) {
        console.error('Failed to load tools:', err);
    }
}

// === Render Functions ===
function renderTestCases(cases) {
    const container = document.getElementById('testList');
    let html = '';
    let lastCategory = '';

    cases.forEach(tc => {
        if (tc.category !== lastCategory) {
            html += `<div class="category-separator">${tc.category}</div>`;
            lastCategory = tc.category;
        }

        const difficultyClass = `difficulty-${tc.difficulty}`;
        const badgeClass = `badge-${tc.difficulty}`;
        const difficultyLabels = {
            easy: 'Dễ',
            medium: 'TB',
            hard: 'Khó',
            trap: 'Bẫy'
        };

        html += `
            <div class="test-card ${difficultyClass}" data-id="${tc.id}" onclick="selectTestCase(${tc.id})">
                <div class="test-id">Test #${tc.id}</div>
                <div class="test-question">${escapeHtml(tc.question)}</div>
                <div class="test-meta">
                    <span class="test-badge ${badgeClass}">${difficultyLabels[tc.difficulty] || tc.difficulty}</span>
                    ${tc.tools_expected.length > 0
                        ? `<span class="test-badge badge-tool">🛠️ ${tc.tools_expected.length} tool${tc.tools_expected.length > 1 ? 's' : ''}</span>`
                        : `<span class="test-badge badge-easy">💬 No tool</span>`
                    }
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderTools(tools) {
    const container = document.getElementById('toolsList');
    let html = '';

    tools.forEach(tool => {
        // Get first line of description
        const desc = tool.description.split('\n')[0].trim();
        html += `
            <div class="tool-item">
                <div class="tool-name">${tool.name}</div>
                <div class="tool-desc">${escapeHtml(desc)}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderResults(query, results) {
    const grid = document.getElementById('resultsGrid');
    const isBoth = results.chatbot && results.react;

    let html = `
        <div class="query-display">
            <div class="query-avatar">👤</div>
            <div class="query-text">${escapeHtml(query)}</div>
        </div>
        <div class="comparison-container ${isBoth ? '' : 'single-mode'}">
    `;

    if (results.chatbot) {
        html += renderResultCard(results.chatbot, 'chatbot');
    }
    if (results.react) {
        html += renderResultCard(results.react, 'react');
    }

    html += '</div>';

    // Prepend instead of replace
    grid.innerHTML = html + grid.innerHTML;
}

function renderResultCard(result, type) {
    const isChatbot = type === 'chatbot';
    const icon = isChatbot ? '💬' : '🤖';
    const label = isChatbot ? 'Chatbot Baseline' : 'ReAct Agent';
    const headerClass = isChatbot ? 'chatbot-header' : 'react-header';
    const labelClass = isChatbot ? 'chatbot-label' : 'react-label';

    let stepsHtml = '';
    if (!isChatbot && result.steps && result.steps.length > 0) {
        stepsHtml = `
            <div class="react-steps">
                <div class="react-steps-title">🔄 ReAct Loop Steps (${result.steps.length})</div>
                ${result.steps.map(step => `
                    <div class="step-item">
                        <div class="step-number">Step ${step.step}</div>
                        ${step.thought ? `<div class="step-thought">🧠 Thought: ${escapeHtml(step.thought)}</div>` : ''}
                        ${step.action ? `<div class="step-action">🛠️ Action: ${escapeHtml(step.action)}</div>` : ''}
                        ${step.observation ? `<div class="step-observation">👁️ Observation: ${escapeHtml(step.observation)}</div>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    return `
        <div class="result-card">
            <div class="result-card-header ${headerClass}">
                <div class="result-type">
                    <span class="result-type-icon">${icon}</span>
                    <span class="result-type-label ${labelClass}">${label}</span>
                </div>
                <div class="result-meta">
                    <span class="meta-tag meta-time">⏱️ ${result.elapsed_time}s</span>
                    ${result.tools_called.length > 0
                        ? `<span class="meta-tag meta-tools">🛠️ ${result.tools_called.length}</span>`
                        : ''
                    }
                </div>
            </div>
            <div class="result-card-body">
                <div class="result-response">${escapeHtml(result.response)}</div>
                ${stepsHtml}
            </div>
        </div>
    `;
}

// === Actions ===
function selectTestCase(id) {
    const tc = testCases.find(t => t.id === id);
    if (!tc) return;

    // Update active state
    activeTestId = id;
    document.querySelectorAll('.test-card').forEach(card => {
        card.classList.toggle('active', parseInt(card.dataset.id) === id);
    });

    // Set query text
    document.getElementById('chatInput').value = tc.question;
    document.getElementById('chatInput').focus();
}

function setQuery(text) {
    document.getElementById('chatInput').value = text;
    document.getElementById('chatInput').focus();
}

async function sendQuery() {
    const input = document.getElementById('chatInput');
    const query = input.value.trim();
    if (!query) return;

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    // Show loading, hide welcome
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('loadingOverlay').style.display = 'flex';
    document.getElementById('resultsGrid').style.display = 'flex';

    try {
        const res = await fetch('/api/run-test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, mode: currentMode })
        });

        const data = await res.json();

        if (data.success) {
            renderResults(query, data.data);
            addToHistory(query, data.data);
        } else {
            showError(data.error || 'Unknown error occurred');
        }
    } catch (err) {
        showError(`Connection error: ${err.message}`);
    } finally {
        document.getElementById('loadingOverlay').style.display = 'none';
        sendBtn.disabled = false;
    }
}

function showError(message) {
    const grid = document.getElementById('resultsGrid');
    grid.innerHTML = `<div class="error-message">❌ ${escapeHtml(message)}</div>` + grid.innerHTML;
}

// === History ===
function addToHistory(query, results) {
    const timestamp = new Date().toLocaleTimeString('vi-VN');
    history.unshift({ query, timestamp, results });

    // Limit history
    if (history.length > 20) history = history.slice(0, 20);

    renderHistory();
}

function renderHistory() {
    const container = document.getElementById('historyList');
    if (history.length === 0) {
        container.innerHTML = '<p class="empty-state">Chưa có lịch sử</p>';
        return;
    }

    container.innerHTML = history.map((item, i) => `
        <div class="history-item" onclick="replayHistory(${i})">
            <div class="history-query">${escapeHtml(item.query)}</div>
            <div class="history-time">${item.timestamp}</div>
        </div>
    `).join('');
}

function replayHistory(index) {
    if (history[index]) {
        document.getElementById('chatInput').value = history[index].query;
    }
}

function clearHistory() {
    history = [];
    renderHistory();
}

// === Utils ===
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
