"""
🌐 WEB SERVER cho ReAct Agent (Lab 3: Chatbot vs ReAct Agent)
FastAPI + SSE streaming, tái sử dụng trực tiếp run_react_agent() từ src/app.py.

Chạy:
    uvicorn server:app --reload --port 8000
Mở:
    http://localhost:8000

Endpoints:
    GET  /            -> index.html (chat UI)
    GET  /api/status  -> thông tin provider/model + trạng thái session
    GET  /api/chat    -> SSE stream các event của ReAct loop (message=<query>)
    POST /api/reset   -> xóa lịch sử hội thoại, bắt đầu session mới
"""

import json
import os
import sys
import threading

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

# ----------------------------------------------------------------------------
# Import agent core từ src/
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

load_dotenv(os.path.join(BASE_DIR, ".env"))

from app import MAX_ITERATIONS, _init_messages, run_react_agent  # noqa: E402
from providers import get_llm_provider  # noqa: E402

app = FastAPI(title="VinUni Course Agent - Lab 3")

# ----------------------------------------------------------------------------
# Session state (single-user demo — giống vòng lặp CLI trong src/app.py)
# ----------------------------------------------------------------------------
_state = {
    "llm": None,
    "messages": None,
    "step_offset": 0,
    "turn": 0,
    "init_error": None,
}
_lock = threading.Lock()


def _get_llm():
    """Khởi tạo LLM lazily (giống __main__ của app.py)."""
    if _state["llm"] is None and _state["init_error"] is None:
        try:
            _state["llm"] = get_llm_provider()
            _state["messages"] = _init_messages()
        except Exception as e:  # thiếu API key, v.v.
            _state["init_error"] = str(e)
    return _state["llm"]


def _sse(payload: dict) -> str:
    """Đóng gói 1 event thành 1 frame Server-Sent Events."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/status")
def status():
    llm = _get_llm()
    if llm is None:
        return {
            "ok": False,
            "error": _state["init_error"],
        }
    return {
        "ok": True,
        "provider": getattr(llm, "_provider_name", "?"),
        "model": getattr(llm, "model_name", None) or getattr(llm, "model", "?"),
        "turn": _state["turn"],
        "history_messages": len(_state["messages"] or []),
        "max_iterations": MAX_ITERATIONS,
    }


@app.post("/api/reset")
def reset():
    with _lock:
        _state["messages"] = _init_messages()
        _state["step_offset"] = 0
        _state["turn"] = 0
    return {"ok": True}


@app.get("/api/chat")
def chat(message: str = Query(..., min_length=1)):
    llm = _get_llm()
    if llm is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": f"Chưa cấu hình LLM provider: {_state['init_error']}. "
                "Thiết lập trong file .env (xem .env.example)."
            },
        )

    if not _lock.acquire(blocking=False):
        return JSONResponse(
            status_code=409,
            content={"error": "Agent đang xử lý một câu hỏi khác. Vui lòng đợi."},
        )

    def event_stream():
        try:
            _state["turn"] += 1
            yield _sse({"type": "turn_start", "turn": _state["turn"]})

            # ReAct loop — yield từng event ngay khi xảy ra (stream thật)
            for event in run_react_agent(
                message, llm, _state["messages"], _state["step_offset"]
            ):
                yield _sse(event)

            # Giữ đánh số step liên tục qua các turn (giống CLI)
            _state["step_offset"] += MAX_ITERATIONS
            yield _sse({"type": "done", "turn": _state["turn"]})
        except Exception as e:
            yield _sse({"type": "error", "step": None, "content": f"Server error: {e}"})
        finally:
            _lock.release()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
