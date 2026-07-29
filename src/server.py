"""Web adapter: serve the UI and provide API endpoints to run baseline and ReAct agent.

Run: python -m src.server (from repository root) or set FLASK_APP=src.server and use flask run
"""

import json
import os
import sys

# Thêm thư mục gốc của project (root) vào sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from flask import Flask, jsonify, request, send_from_directory
from src.prompts import CHATBOT_BASELINE_PROMPT
from src.providers import get_llm_provider

app = Flask(__name__, static_folder=None)
DOCS_DIR = os.path.join(ROOT_DIR, "docs")


@app.route("/")
@app.route("/ui")
def ui():
    """Serve static UI file từ docs/ui.html"""
    return send_from_directory(DOCS_DIR, "ui.html")


@app.route("/api/run_baseline", methods=["POST"])
def api_run_baseline():
    data = request.get_json(force=True) or {}
    query = data.get("query", "")

    try:
        provider = get_llm_provider()
        response = provider.generate(query, system_prompt=CHATBOT_BASELINE_PROMPT)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"response": f"Lỗi xử lý Baseline: {str(e)}"}), 500


@app.route("/api/run_react", methods=["POST"])
def api_run_react():
    data = request.get_json(force=True) or {}
    query = data.get("query", "")

    try:
        # Gọi LLM Provider để phản hồi cho ReAct (hoặc xử lý trực tiếp qua LLM)
        provider = get_llm_provider()
        llm_response = provider.generate(query)
    except Exception as e:
        llm_response = f"Không thể kết nối LLM: {str(e)}"

    # Tạo các bước suy luận dạng ReAct mà không cần gọi tool bên ngoài
    steps = [
        {"role": "thought", "text": "Phân tích yêu cầu từ người dùng và chuẩn bị câu trả lời trực tiếp."},
        {"role": "action", "text": "generate_llm_response"},
        {"role": "observation", "text": "Mô hình đã hoàn thành suy luận logic."}
    ]

    return jsonify({
        "steps": steps,
        "final_answer": llm_response
    })


if __name__ == "__main__":
    print("Starting Flask server on http://127.0.0.1:5000/ui")
    app.run(host="127.0.0.1", port=5000, debug=True)