"""
🚀 FASTAPI BACKEND SERVER FOR REACT FRONTEND (`server.py`)
Cung cấp REST API cho React Frontend, quản lý session_id độc lập,
kết nối trực tiếp với agent.py, tools.py và các AI levels.
"""

import os
import sys
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.abspath(__file__), "src"))

from src.providers import get_llm_provider
from src.tools import MOCK_CANDIDATE_DB
from agent import MatchmakingAgent
from src.ai_levels.level1_rule_based import rule_based_bot
from src.ai_levels.level2_llm_chatbot import llm_chatbot
from src.ai_levels.level4_autonomous_agent import AutonomousMatchmakerAgent

load_dotenv()

app = FastAPI(title="AI Matchmaking Agent API", version="2.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store Agents per Session ID
SESSION_AGENTS: Dict[str, MatchmakingAgent] = {}
provider = get_llm_provider()


class ChatRequest(BaseModel):
    message: str
    level: str = "level3"  # level1 | level2 | level3 | level4
    session_id: Optional[str] = None


class ResetRequest(BaseModel):
    session_id: str


def get_or_create_agent(session_id: str) -> MatchmakingAgent:
    if session_id not in SESSION_AGENTS:
        SESSION_AGENTS[session_id] = MatchmakingAgent(provider_name="groq")
    return SESSION_AGENTS[session_id]


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống!")

    session_id = req.session_id or "default_session"
    agent = get_or_create_agent(session_id)

    level = req.level.lower().strip()

    try:
        if level == "level3" or "cấp 3" in level or "react" in level:
            response_text = agent.process_message(message)
        elif level == "level4" or "cấp 4" in level or "autonomous" in level:
            auto_agent = AutonomousMatchmakerAgent(goal=message, provider=provider)
            auto_agent.execute()
            memory_logs = [f"• **Step {m['step']}** [{m['task']}]: {m['result']}" for m in auto_agent.memory]
            response_text = (
                f"🚀 **[CẤP 4 - AUTONOMOUS AGENT GOAL COMPLETION]**\n\n"
                f"🎯 **Mục tiêu**: {message}\n\n"
                f"📋 **Nhật ký Bộ nhớ Execution Memory**:\n" + "\n".join(memory_logs) + "\n\n"
                f"✨ **Đề xuất hoàn tất!**"
            )
        elif level == "level2" or "cấp 2" in level or "chatbot" in level:
            response_text = llm_chatbot(message, provider)
        else:
            response_text = rule_based_bot(message)

        return {
            "status": "success",
            "session_id": session_id,
            "level": level,
            "response": response_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thực thi Agent: {str(e)}")


@app.post("/api/reset")
async def api_reset(req: ResetRequest):
    session_id = req.session_id
    if session_id in SESSION_AGENTS:
        SESSION_AGENTS[session_id].reset_state()
        del SESSION_AGENTS[session_id]
    
    # Re-create brand new clean agent
    SESSION_AGENTS[session_id] = MatchmakingAgent(provider_name="groq")
    return {
        "status": "success",
        "message": f"Đã xóa sạch 100% lịch sử và reset phiên {session_id}"
    }


@app.get("/api/candidates")
async def api_candidates():
    return {
        "status": "success",
        "candidates": MOCK_CANDIDATE_DB
    }


# Static files setup for React Web App
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Matchmaking Agent API Server running. Open /static/index.html"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
