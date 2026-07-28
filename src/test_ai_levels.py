"""
🧪 TEST SUITE 4 CẤP ĐỘ AI SYSTEM (LEVEL 1 -> LEVEL 4) WITH GEMINI PROVIDER
Chạy và kiểm thử bộ 5 Test Cases từ config/test_cases.json qua 4 cấp độ hệ thống AI.
"""

import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from providers import get_llm_provider
from ai_levels.level1_rule_based import rule_based_bot
from ai_levels.level2_llm_chatbot import llm_chatbot
from ai_levels.level3_reactive_agent import reactive_agent_process
from ai_levels.level4_autonomous_agent import AutonomousMatchmakerAgent
from agent import MatchmakingAgent

load_dotenv()


def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_full_ai_levels_evaluation():
    print("=================================================================")
    print("🏫 BÀI LAB 3: ĐÁNH GIÁ 4 CẤP ĐỘ AI SYSTEM & ĐIỂM GÃY (GAP ANALYSIS)")
    print("=================================================================")
    
    provider = get_llm_provider()
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {getattr(provider, 'model_name', 'N/A')})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    agent_l3 = MatchmakingAgent()

    for test in tests:
        test_id = test["id"]
        category = test["category"]
        question = test["question"]
        expected = test["expected_behavior"]
        gap = test.get("gap_analysis", "")

        print(f"\n=================================================================")
        print(f"📌 TEST CASE #{test_id} [{category}]")
        print(f"❓ Câu hỏi  : {question}")
        print(f"🎯 Kỳ vọng  : {expected}")
        print(f"💡 Gap Note : {gap}")
        print("=================================================================")

        # CẤP 1: RULE-BASED BOT
        print("\n--- 🤖 CẤP 1: RULE-BASED BOT ---")
        ans_l1 = rule_based_bot(question)
        print(ans_l1)

        # CẤP 2: LLM CHATBOT BASELINE
        print("\n--- 🤖 CẤP 2: LLM CHATBOT (Gemini 3.5 Flash Lite) ---")
        ans_l2 = llm_chatbot(question, provider)
        print(ans_l2)

        # CẤP 3: REACTIVE AGENT
        print("\n--- 🧠 CẤP 3: REACTIVE AGENT (ReAct Loop + Tools + Guardrails) ---")
        agent_l3.reset_state()
        ans_l3 = reactive_agent_process(question, agent_l3)
        print(ans_l3)

        # CẤP 4: AUTONOMOUS AGENT
        print("\n--- 🚀 CẤP 4: AUTONOMOUS AGENT (Planning + Memory + Multi-Tool) ---")
        agent_l4 = AutonomousMatchmakerAgent(question, provider)
        ans_l4 = agent_l4.execute()
        print(ans_l4)

    print("\n=================================================================")
    print("🎉 HOÀN THÀNH TOÀN BỘ BÀI TEST KIỂM THỬ 4 CẤP ĐỘ HỆ THỐNG AI!")
    print("=================================================================")


if __name__ == "__main__":
    run_full_ai_levels_evaluation()
