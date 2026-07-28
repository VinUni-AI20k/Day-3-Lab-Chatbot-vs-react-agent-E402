/* -----------------------------------------------------------------------------
 * CUPID AGENT WEB CLIENT LOGIC (SPA Navigation, Auto-Next & Collapsible Agent Thinking)
 * ----------------------------------------------------------------------------- */

let userData = {
    name: "Minh",
    age: "21",
    gender: "Nam",
    goal: "Mối quan hệ nghiêm túc",
    interests: "đọc sách, cà phê yên tĩnh, công nghệ",
    answers: {}
};

let questionsList = [];
let currentQuestionIndex = 0;
let maxQuestionLimit = 15;

// STEP NAVIGATION
function goToStep(stepId) {
    document.querySelectorAll('.step-section').forEach(sec => sec.classList.remove('active'));
    const target = document.getElementById(stepId);
    if (target) {
        target.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function updateQuestionCount(countVal) {
    maxQuestionLimit = parseInt(countVal) || 15;
    const label = document.getElementById('prompt-count-label');
    if (label) label.textContent = maxQuestionLimit;
}

// TOGGLE AGENT THINKING DRAWER
function toggleThinkingDrawer() {
    const drawer = document.getElementById('thinking-drawer');
    if (drawer) {
        drawer.classList.toggle('collapsed');
    }
}

// BASIC FORM SUBMIT
function handleBasicFormSubmit(event) {
    event.preventDefault();
    userData.name = document.getElementById('input-name').value || "Minh";
    userData.age = document.getElementById('input-age').value || "21";
    userData.gender = document.getElementById('input-gender').value || "Nam";
    userData.goal = document.getElementById('input-goal').value || "Mối quan hệ nghiêm túc";
    userData.interests = document.getElementById('input-interests').value || "đọc sách, cà phê yên tĩnh";

    goToStep('step-questionnaire-prompt');
}

// START QUESTIONNAIRE
async function startQuestionnaire() {
    try {
        const res = await fetch('/api/questions');
        if (res.ok) {
            const data = await res.json();
            questionsList = (data.questions || []).slice(0, maxQuestionLimit);
        }
    } catch (e) {
        console.warn("Using fallback questions list", e);
    }

    if (!questionsList || questionsList.length === 0) {
        questionsList = getFallbackQuestions().slice(0, maxQuestionLimit);
    }

    currentQuestionIndex = 0;
    renderQuestion(currentQuestionIndex);
    goToStep('step-questionnaire-modal');
}

// RENDER QUESTION ITEM
function renderQuestion(index) {
    if (index < 0 || index >= questionsList.length) return;

    const q = questionsList[index];
    document.getElementById('q-category').textContent = formatCategory(q.category);
    document.getElementById('q-progress-text').textContent = `Câu ${index + 1} / ${questionsList.length}`;
    
    const pct = ((index + 1) / questionsList.length) * 100;
    document.getElementById('q-progress-fill').style.width = `${pct}%`;

    document.getElementById('q-prompt').textContent = q.prompt;
    document.getElementById('q-desc').textContent = q.description || "";

    const optionsContainer = document.getElementById('q-options');
    optionsContainer.innerHTML = "";

    if (q.answer_type === 'single_choice' && q.options) {
        q.options.forEach(opt => {
            const div = document.createElement('div');
            div.className = `q-option-item ${userData.answers[q.id] === opt.value ? 'selected' : ''}`;
            div.innerHTML = `<span>${opt.label}</span> <span class="opt-check">✓</span>`;
            div.onclick = () => {
                userData.answers[q.id] = opt.value;
                div.classList.add('selected');
                // Auto-next after 250ms delay for smooth feedback
                setTimeout(() => {
                    nextQuestion();
                }, 250);
            };
            optionsContainer.appendChild(div);
        });
    } else if (q.answer_type === 'scale') {
        const scaleObj = q.scale || { min: 1, max: 5 };
        const labels = scaleObj.labels || {};
        for (let v = scaleObj.min; v <= scaleObj.max; v++) {
            const div = document.createElement('div');
            div.className = `q-option-item ${userData.answers[q.id] === v ? 'selected' : ''}`;
            div.innerHTML = `<span>Mức ${v}: ${labels[v] || ''}</span> <span class="opt-check">✓</span>`;
            div.onclick = () => {
                userData.answers[q.id] = v;
                div.classList.add('selected');
                // Auto-next after 250ms delay for smooth feedback
                setTimeout(() => {
                    nextQuestion();
                }, 250);
            };
            optionsContainer.appendChild(div);
        }
    }

    document.getElementById('btn-prev-q').disabled = (index === 0);
}

function prevQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        renderQuestion(currentQuestionIndex);
    }
}

function nextQuestion() {
    if (currentQuestionIndex < questionsList.length - 1) {
        currentQuestionIndex++;
        renderQuestion(currentQuestionIndex);
    } else {
        // Finish questionnaire
        runCupidAgent();
    }
}

function skipQuestionnaire() {
    runCupidAgent();
}

// RUN AGENT API
async function runCupidAgent() {
    goToStep('step-dashboard');

    try {
        const res = await fetch('/api/run-agent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: userData.name,
                age: userData.age,
                gender: userData.gender,
                goal: userData.goal,
                interests: userData.interests,
                questionnaire_answers: userData.answers
            })
        });

        if (res.ok) {
            const result = await res.json();
            updateDashboard(result);
        } else {
            console.error("API error, fallback offline dashboard");
            updateDashboard(getOfflineResult());
        }
    } catch (e) {
        console.warn("Fetch failed, using offline mock result", e);
        updateDashboard(getOfflineResult());
    }
}

// UPDATE DASHBOARD WITH RESULTS
function updateDashboard(data) {
    const match = data.match;
    document.getElementById('match-cand-name').textContent = `${match.name}, ${match.age}t`;
    document.getElementById('match-cand-mbti').textContent = `${match.mbti} • Hướng nội tinh tế`;
    document.getElementById('match-cand-bio').textContent = `"${match.bio}"`;
    document.getElementById('match-icebreaker').textContent = `"${match.icebreaker}"`;

    // Render Canvas Synastry Radar Chart
    drawRadarChart(data.radar_scores || { values: 95, communication: 92, lifestyle: 89, finance: 91, career: 90, humor: 93 });

    // Update thinking steps badge count
    const countBadge = document.getElementById('thinking-badge');
    if (countBadge && data.react_steps) {
        countBadge.textContent = `${data.react_steps.length} Steps`;
    }

    // Render ReAct Steps Trace inside Collapsible Drawer
    const traceContainer = document.getElementById('trace-steps');
    if (traceContainer && data.react_steps) {
        traceContainer.innerHTML = "";
        data.react_steps.forEach(st => {
            const div = document.createElement('div');
            div.className = "trace-step-item";
            div.innerHTML = `
                <div class="step-tag">Step ${st.step}</div>
                <div class="thought-text">Thought: ${st.thought}</div>
                <div class="action-text">Action: ${st.action}</div>
                <div class="obs-text">Observation: ${st.observation}</div>
            `;
            traceContainer.appendChild(div);
        });
    }
}

// CHATBOT ASSISTANT LOGIC
async function handleChatSubmit(event) {
    event.preventDefault();
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    appendChatMessage("User", msg, "user-msg");
    input.value = "";

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, name: userData.name })
        });
        if (res.ok) {
            const data = await res.json();
            appendChatMessage("Cupid Agent", data.reply, "bot-msg");
        } else {
            appendChatMessage("Cupid Agent", "Đã xảy ra lỗi khi kết nối AI Assistant.", "bot-msg");
        }
    } catch (e) {
        appendChatMessage("Cupid Agent", "Hệ thống đang hoạt động ở chế độ thử nghiệm offline.", "bot-msg");
    }
}

function sendQuickChat(msgText) {
    document.getElementById('chat-input').value = msgText;
    const form = document.querySelector('.chat-input-row-large');
    if (form) form.requestSubmit();
}

function appendChatMessage(author, text, msgClass) {
    const history = document.getElementById('chat-history');
    const div = document.createElement('div');
    div.className = `chat-msg ${msgClass}`;
    div.innerHTML = `<div class="msg-author">${author}</div><div class="msg-text">${text.replace(/\n/g, '<br>')}</div>`;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
}

// DRAW CANVAS RADAR CHART
function drawRadarChart(scores) {
    const canvas = document.getElementById('synastryRadarCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 80;

    ctx.clearRect(0, 0, width, height);

    const labels = ["Giá Trị", "Giao Tiếp", "Lối Sống", "Tài Chính", "Sự Nghiệp", "Hài Hước"];
    const keys = ["values", "communication", "lifestyle", "finance", "career", "humor"];
    const userVals = [80, 85, 82, 80, 85, 88];
    const matchVals = keys.map(k => scores[k] || 90);

    const numAxes = labels.length;

    // Draw background grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1;
    for (let level = 1; level <= 4; level++) {
        const r = (radius / 4) * level;
        ctx.beginPath();
        for (let i = 0; i < numAxes; i++) {
            const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
            const x = centerX + r * Math.cos(angle);
            const y = centerY + r * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();
    }

    // Draw Axis lines & labels
    ctx.font = "11px 'Plus Jakarta Sans', sans-serif";
    ctx.fillStyle = "#A89BB0";
    ctx.textAlign = "center";

    for (let i = 0; i < numAxes; i++) {
        const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.stroke();

        const labelX = centerX + (radius + 18) * Math.cos(angle);
        const labelY = centerY + (radius + 18) * Math.sin(angle);
        ctx.fillText(labels[i], labelX, labelY + 4);
    }

    // Draw Match Data Polygon
    ctx.beginPath();
    for (let i = 0; i < numAxes; i++) {
        const val = matchVals[i] / 100;
        const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
        const x = centerX + radius * val * Math.cos(angle);
        const y = centerY + radius * val * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(229, 56, 85, 0.25)";
    ctx.fill();
    ctx.strokeStyle = "#E53855";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw User Data Polygon
    ctx.beginPath();
    for (let i = 0; i < numAxes; i++) {
        const val = userVals[i] / 100;
        const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
        const x = centerX + radius * val * Math.cos(angle);
        const y = centerY + radius * val * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(192, 132, 252, 0.18)";
    ctx.fill();
    ctx.strokeStyle = "#C084FC";
    ctx.lineWidth = 2;
    ctx.stroke();
}

function copyIcebreaker() {
    const txt = document.getElementById('match-icebreaker').textContent;
    navigator.clipboard.writeText(txt);
    alert("Đã sao chép câu mở đầu!");
}

function formatCategory(cat) {
    const map = {
        relationship_intent: "Mục Tiêu Hẹn Hò",
        family: "Gia Đình & Con Cái",
        values: "Hệ Giá Trị & Tâm Linh",
        lifestyle: "Lối Sống & Thói Quen",
        finance: "Tài Chính",
        life_direction: "Sự Nghiệp & Định Hướng",
        communication: "Phong Cách Giao Tiếp",
        boundaries: "Sự Độc Lập"
    };
    return map[cat] || cat;
}

function getFallbackQuestions() {
    return [
        {
            id: "relationship_goal",
            category: "relationship_intent",
            answer_type: "single_choice",
            prompt: "Hiện tại bạn đang tìm kiếm loại mối quan hệ nào?",
            description: "Chọn mục tiêu phù hợp nhất với mong muốn hiện tại của bạn.",
            options: [
                { value: "short_term", label: "Kết nối ngắn hạn" },
                { value: "exploring", label: "Tìm hiểu, chưa xác định rõ" },
                { value: "long_term", label: "Mối quan hệ độc quyền lâu dài" },
                { value: "marriage_oriented", label: "Mối quan hệ hướng tới kết hôn" }
            ]
        },
        {
            id: "financial_style",
            category: "finance",
            answer_type: "scale",
            prompt: "Phong cách sử dụng tiền của bạn gần với phía nào hơn?",
            scale: {
                min: 1, max: 5,
                labels: { 1: "Chi tiêu hiện tại", 3: "Cân bằng chi tiêu & tiết kiệm", 5: "Ưu tiên tiết kiệm dài hạn" }
            }
        }
    ];
}

function getOfflineResult() {
    return {
        user: userData,
        match: {
            id: "cand_01",
            name: "Mai",
            age: 22,
            match_score: 91,
            mbti: "INFJ",
            bio: "Hướng nội vừa phải, tinh tế, yêu sách & không gian cà phê yên tĩnh.",
            strengths: ["Cùng mục tiêu nghiêm túc", "Cùng thích đọc sách & cà phê", "Phong cách giao tiếp nhẹ nhàng"],
            icebreaker: `Chào Mai, mình thấy bạn cũng thích không gian cà phê yên tĩnh và đọc sách. Dạo này bạn đang đọc cuốn sách nào hay không?`
        },
        radar_scores: { values: 95, communication: 92, lifestyle: 89, finance: 91, career: 90, humor: 93 },
        react_steps: [
            { step: 1, thought: "Đọc thông tin hồ sơ và sở thích của người dùng Minh.", action: "get_user_profile['current_user']", observation: "Minh, 21t, Hướng nội, Vector: [0.2, 0.9, 0.8, 0.95]" },
            { step: 2, thought: "Lọc các hồ sơ ứng viên phù hợp với mối quan hệ nghiêm túc, thích đọc sách & cà phê.", action: "search_candidate_profiles['relationship_goal=serious']", observation: "Lan 82/100, Mai 91/100, An 76/100" },
            { step: 3, thought: "Tính toán độ tương thích chi tiết giữa Minh và Mai.", action: "calculate_compatibility['Minh', 'Mai']", observation: "Điểm tương thích Minh - Mai: 91/100" }
        ]
    };
}
