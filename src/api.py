"""
🌐 FASTAPI BACKEND — cầu nối giữa Frontend (React + Chakra UI) và src/app.py.
Chỉ import và tái sử dụng run_baseline_chatbot()/run_react_agent() của Role 4,
không chỉnh sửa app.py/prompts.py/tools.py/providers.py.

Chạy: python src/api.py   (mặc định http://localhost:8000)
"""

import contextlib
import io
import os
import re
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import run_baseline_chatbot, run_react_agent, load_test_cases  # noqa: E402
from providers import get_llm_provider  # noqa: E402

app = FastAPI(title="CGV Movie Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = get_llm_provider()


class ChatRequest(BaseModel):
    message: str
    mode: str  # "baseline" | "react"


# --------------------------------------------------------------------------
# Bóc tách log console của run_react_agent(verbose=True) thành trace có cấu
# trúc (thought/action/observation theo từng step) để Frontend hiển thị.
# Final Answer luôn lấy từ giá trị trả về của run_react_agent, không parse từ log.
# --------------------------------------------------------------------------
_LABELS = {
    "🧠 Thought:": "thought",
    "🛠️ Action:": "action",
    "👁️ Observation:": "observation",
}
_LABEL_PATTERN = re.compile(
    r"(🧠 Thought:|🛠️ Action:|👁️ Observation:)(.*?)(?=(?:🧠 Thought:|🛠️ Action:|👁️ Observation:|$))",
    re.DOTALL,
)
_STEP_PATTERN = re.compile(r"--- 🔄 Vòng lặp ReAct \(Step (\d+)/(\d+)\) ---")


def _parse_trace(output: str) -> list:
    steps = []
    positions = list(_STEP_PATTERN.finditer(output))
    for i, m in enumerate(positions):
        start = m.end()
        end = positions[i + 1].start() if i + 1 < len(positions) else len(output)
        block = output[start:end]
        entry = {"step": int(m.group(1))}
        for marker, content in _LABEL_PATTERN.findall(block):
            entry[_LABELS[marker]] = content.strip()
        steps.append(entry)
    return steps


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", None),
    }


@app.get("/api/test-cases")
def test_cases():
    return load_test_cases()


@app.post("/api/chat")
def chat(req: ChatRequest):
    if req.mode == "baseline":
        response = run_baseline_chatbot(req.message, provider)
        return {"mode": "baseline", "response": response}

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        final_answer = run_react_agent(req.message, provider, verbose=True)
    output = buf.getvalue()

    return {
        "mode": "react",
        "trace": _parse_trace(output),
        "final_answer": final_answer,
        "guardrail_triggered": "GUARDRAIL TRIGGERED" in output,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
