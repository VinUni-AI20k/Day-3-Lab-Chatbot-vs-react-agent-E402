"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider + Matchmaking Agent.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ và root hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Đảm bảo in ra Tiếng Việt không bị lỗi font console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tools import AVAILABLE_TOOLS, calculate_compatibility, search_candidates
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
from agent import MatchmakingAgent

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    if "Error" in response or "Mock" in response:
        response = "🤖 [Baseline Chatbot]: Tôi là Chatbot tư vấn tình cảm thông thường. Tôi không thể tra cứu cơ sở dữ liệu hồ sơ người dùng thực tế hay tính toán ma trận điểm tương thích."
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_matchmaking_agent(user_query: str, agent: MatchmakingAgent):
    """
    Dựng ReAct Matchmaking Agent có Guardrails và Information Gathering Loop.
    """
    print(f"\n💘 [REACT MATCHMAKING AGENT] Câu hỏi: {user_query}")
    response = agent.process_message(user_query)
    print(f"🤖 Bà Mối AI Trả lời:\n{response}")


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("💘 DỰ ÁN AI MATCHMAKING AGENT - BÀ MỐI AI SYSTEM")
    print("==========================================================")
    
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    agent = MatchmakingAgent()

    print("==================================================")
    print("--- DEMO 1: CHẠY CÂU BẮT THỦ (TEST CASE #3 - COMPATIBILITY) ---")
    print("==================================================")
    query_3 = tests[2]["question"]
    print("🔹 CHATBOT BASELINE:")
    run_baseline_chatbot(query_3, provider)
    print("\n🔹 REACT MATCHMAKING AGENT:")
    run_matchmaking_agent(query_3, agent)

    print("\n==================================================")
    print("--- DEMO 2: CHẠY THỬ LUỒNG THIẾU THÔNG TIN (TEST CASE #4) ---")
    print("==================================================")
    agent.reset_state()
    query_4 = tests[3]["question"]
    run_matchmaking_agent(query_4, agent)

    print("\n==================================================")
    print("--- DEMO 3: CHẠY THỬ EDGE CASE RELAXED SEARCH (TEST CASE #5) ---")
    print("==================================================")
    agent.reset_state()
    query_5 = tests[4]["question"]
    run_matchmaking_agent(query_5, agent)
