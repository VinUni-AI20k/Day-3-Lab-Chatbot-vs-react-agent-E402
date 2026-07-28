"""
🌐 WEB DEMO (localhost) — Giao diện web đơn giản để demo Chatbot Baseline vs ReAct Agent.

Chạy:  python src/web_demo.py
Mở:    http://127.0.0.1:5000

Đây chỉ là lớp UI mỏng gọi lại đúng các hàm run_baseline_chatbot() / run_react_agent()
trong src/app.py — không có logic nghiệp vụ riêng, để tránh lệch với bản CLI.
"""

import json
import os
import sys

from flask import Flask, render_template_string, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import load_test_cases, run_baseline_chatbot, run_react_agent
from prompts import REACT_SYSTEM_PROMPT_V1, REACT_SYSTEM_PROMPT_V2
from providers import get_llm_provider

app = Flask(__name__)

PAGE_TEMPLATE = """
<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>🎁 Demo: Chatbot vs ReAct Agent</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: "Segoe UI", system-ui, sans-serif; max-width: 900px; margin: 24px auto; padding: 0 16px; line-height: 1.5; }
  h1 { font-size: 1.4rem; }
  form { border: 1px solid #8884; border-radius: 10px; padding: 16px; margin-bottom: 24px; }
  textarea { width: 100%; box-sizing: border-box; padding: 8px; font-size: 1rem; border-radius: 6px; border: 1px solid #8886; }
  select, button { padding: 6px 10px; border-radius: 6px; border: 1px solid #8886; font-size: 0.95rem; }
  .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-top: 10px; }
  .row label { font-size: 0.85rem; opacity: 0.8; display: block; margin-bottom: 2px; }
  button[type=submit] { background: #2563eb; color: white; border: none; padding: 8px 18px; cursor: pointer; font-weight: 600; }
  button[type=submit]:hover { background: #1d4ed8; }
  .card { border: 1px solid #8884; border-radius: 10px; padding: 14px 16px; margin-bottom: 16px; }
  .step { border-left: 3px solid #2563eb; padding: 6px 0 6px 12px; margin: 10px 0; }
  .step .thought { opacity: 0.85; font-style: italic; }
  .step .action { font-family: monospace; background: #8881; padding: 2px 6px; border-radius: 4px; display: inline-block; margin: 4px 0; }
  .step .obs { white-space: pre-wrap; }
  .obs.error { color: #dc2626; }
  .final { border-left: 3px solid #16a34a; padding: 6px 0 6px 12px; font-weight: 600; }
  .guardrail { color: #d97706; font-weight: 600; }
  .badge { font-size: 0.75rem; padding: 2px 8px; border-radius: 999px; background: #8882; margin-left: 6px; }
  .error-msg { color: #dc2626; }
</style>
</head>
<body>
  <h1>🎁 Demo: Trợ Lý Chọn Quà Tặng — Chatbot Baseline vs ReAct Agent</h1>

  <form method="post" action="/run">
    <label for="quick">📋 Chọn nhanh 1 test case có sẵn (tuỳ chọn):</label>
    <select id="quick" onchange="document.getElementById('question').value = this.value">
      <option value="">-- tự nhập câu hỏi bên dưới --</option>
      {% for t in tests %}
      <option value="{{ t.question }}">#{{ t.id }} [{{ t.category }}] {{ t.question }}</option>
      {% endfor %}
    </select>

    <div style="margin-top:10px;">
      <label for="question">❓ Câu hỏi:</label>
      <textarea id="question" name="question" rows="3" placeholder="Nhập câu hỏi...">{{ result.question if result else '' }}</textarea>
    </div>

    <div class="row">
      <div>
        <label>Chạy</label>
        <select name="mode">
          <option value="both" {{ 'selected' if result and result.mode == 'both' else '' }}>Baseline + ReAct Agent</option>
          <option value="baseline" {{ 'selected' if result and result.mode == 'baseline' else '' }}>Chỉ Chatbot Baseline</option>
          <option value="react" {{ 'selected' if result and result.mode == 'react' else '' }}>Chỉ ReAct Agent</option>
        </select>
      </div>
      <div>
        <label>Phiên bản Prompt ReAct</label>
        <select name="version">
          <option value="v2" {{ 'selected' if result and result.version == 'v2' else '' }}>V2 (đã có Recovery Guardrails)</option>
          <option value="v1" {{ 'selected' if result and result.version == 'v1' else '' }}>V1 (chưa có Recovery — Before)</option>
        </select>
      </div>
      <div>
        <label>LLM Provider</label>
        <select name="provider">
          <option value="mock" {{ 'selected' if not result or result.provider == 'mock' else '' }}>mock (offline, miễn phí)</option>
          <option value="openai" {{ 'selected' if result and result.provider == 'openai' else '' }}>openai (API thật)</option>
          <option value="gemini" {{ 'selected' if result and result.provider == 'gemini' else '' }}>gemini (API thật)</option>
          <option value="anthropic" {{ 'selected' if result and result.provider == 'anthropic' else '' }}>anthropic (API thật)</option>
          <option value="openrouter" {{ 'selected' if result and result.provider == 'openrouter' else '' }}>openrouter (API thật)</option>
        </select>
      </div>
      <div style="align-self:flex-end;">
        <button type="submit">▶️ Chạy Demo</button>
      </div>
    </div>
  </form>

  {% if result %}
    {% if result.error %}
      <p class="error-msg">⚠️ {{ result.error }}</p>
    {% else %}
      <p>🔌 Provider: <strong>{{ result.provider_label }}</strong></p>

      {% if 'baseline_answer' in result %}
      <div class="card">
        <h3>💬 Chatbot Baseline</h3>
        <p>{{ result.baseline_answer }}</p>
      </div>
      {% endif %}

      {% if 'react_trace' in result %}
      <div class="card">
        <h3>🧠 ReAct Agent {% if result.guardrail %}<span class="badge guardrail">🛡️ Guardrail: {{ result.guardrail }}</span>{% endif %}</h3>

        {% for step in result.react_trace %}
          {% if step.type == 'action' %}
          <div class="step">
            <div><strong>Bước {{ step.step }}</strong></div>
            <div class="thought">🧠 {{ step.thought }}</div>
            <div class="action">🛠️ {{ step.tool }}[{{ step.args }}]</div>
            <div class="obs {{ 'error' if 'LỖI' in step.observation else '' }}">👁️ {{ step.observation }}</div>
          </div>
          {% elif step.type == 'parse_error' %}
          <div class="step">
            <div><strong>Bước {{ step.step }}</strong> (lỗi định dạng phản hồi)</div>
            <div class="obs error">👁️ Không phân tích được Thought/Action/Final Answer hợp lệ.</div>
          </div>
          {% elif step.type == 'final_answer' %}
          <div class="final">🏁 Final Answer: {{ step.content }}</div>
          {% elif step.type == 'guardrail_max_iterations' %}
          <div class="guardrail">🛡️ Đã chạm giới hạn số bước tối đa mà chưa có Final Answer.</div>
          {% endif %}
        {% endfor %}
      </div>
      {% endif %}
    {% endif %}
  {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(PAGE_TEMPLATE, tests=load_test_cases(), result=None)


@app.route("/run", methods=["POST"])
def run():
    tests = load_test_cases()
    question = request.form.get("question", "").strip()
    mode = request.form.get("mode", "both")
    version = request.form.get("version", "v2")
    provider_name = request.form.get("provider", "mock")

    result = {"question": question, "mode": mode, "version": version, "provider": provider_name}

    if not question:
        result["error"] = "Vui lòng nhập câu hỏi."
        return render_template_string(PAGE_TEMPLATE, tests=tests, result=result)

    provider = get_llm_provider(provider_name)
    result["provider_label"] = f"{provider.__class__.__name__} ({getattr(provider, 'model_name', 'Offline Mock')})"

    if mode in ("baseline", "both"):
        result["baseline_answer"] = run_baseline_chatbot(question, provider, verbose=False)

    if mode in ("react", "both"):
        system_prompt = REACT_SYSTEM_PROMPT_V1 if version == "v1" else REACT_SYSTEM_PROMPT_V2
        react_result = run_react_agent(question, provider, system_prompt=system_prompt, verbose=False)
        result["react_trace"] = react_result["trace"]
        result["guardrail"] = react_result["guardrail"]

    return render_template_string(PAGE_TEMPLATE, tests=tests, result=result)


if __name__ == "__main__":
    print("🌐 Đang chạy demo tại: http://127.0.0.1:5000  (Ctrl+C để dừng)")
    print("⚠️ Mặc định provider = mock (miễn phí). Đổi sang openai/gemini/... trên form nếu muốn dùng API thật.")
    app.run(debug=True, port=5000)
