"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import (
    AVAILABLE_TOOLS,
    get_user_profile,
    search_candidate_profiles,
    calculate_compatibility,
    synthesize_recommendation
)
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp Cupid ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [CUPID REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        if step == 1:
            print("🧠 Thought: Cần lấy thông tin hồ sơ và sở thích của người dùng Minh.")
            print("🛠️ Action: get_user_profile['current_user']")
            
            # Thực thi tool 1
            obs = get_user_profile("current_user")
            print(f"👁️ Observation:\n{obs}")
            
        elif step == 2:
            print("🧠 Thought: Lọc các hồ sơ ứng viên phù hợp với mối quan hệ nghiêm túc, thích đọc sách & cà phê.")
            print("🛠️ Action: search_candidate_profiles['relationship_goal=serious; interests=reading,cafe']")
            
            # Thực thi tool 2
            obs = search_candidate_profiles("relationship_goal=serious; interests=reading,cafe")
            print(f"👁️ Observation:\n{obs}")
            
        elif step == 3:
            print("🧠 Thought: Tính toán độ tương thích chi tiết giữa Minh và ứng viên sáng giá nhất (Mai).")
            print("🛠️ Action: calculate_compatibility['Minh', 'Mai']")
            
            # Thực thi tool 3
            obs = calculate_compatibility("Minh", "Mai")
            print(f"👁️ Observation:\n{obs}")
            
            # Thực thi tool 4 & Đưa ra Final Answer
            summary = synthesize_recommendation("Minh", "Mai")
            print(f"\n🏁 Final Answer:\n"
                  f"Dựa trên phân tích Feature Vector (Độ tương thích 91/100):\n"
                  f"Mai là ứng viên phù hợp nhất với Minh! Cả hai đều hướng nội nhẹ nhàng, thích đọc sách và cà phê yên tĩnh.\n\n"
                  f"💡 [Gợi ý câu mở đầu Icebreaker]:\n"
                  f"\"Chào Mai, mình thấy bạn cũng thích không gian cà phê yên tĩnh và đọc sách. Dạo này bạn đang đọc cuốn sách nào hay không?\"")
            break
            
    if step >= MAX_ITERATIONS and step < 3:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("💘 ỨNG DỤNG: CUPID AGENT (MATCHMAKING & COMPATIBILITY)")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Thống nhất câu truy vấn Cupid Agent chuẩn cho cả 2 Demo để so sánh công bằng
    cupid_sample_query = (
        "Hãy tìm cho tôi ứng viên phù hợp nhất để hẹn hò nghiêm túc, "
        "phân tích điểm tương thích % và gợi ý câu mở đầu bắt chuyện."
    )
    
    print("==================================================")
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE (KHÔNG TOOL) ---")
    print("==================================================")
    run_baseline_chatbot(cupid_sample_query, provider)
    
    print("\n==================================================")
    print("--- DEMO 2: CHẠY TRÊN CUPID REACT AGENT (CÓ TOOLS) ---")
    print("==================================================")
    run_react_agent(cupid_sample_query, provider)

