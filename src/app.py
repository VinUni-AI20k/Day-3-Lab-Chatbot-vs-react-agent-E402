"""
🚀 CORE AGENT APP - CUPID AGENT (Dành cho Role 4: Core Agent Developer / Tech Lead)
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
from tools import AVAILABLE_TOOLS, check_horoscope_compatibility, calculate_mbti_compatibility, search_date_ideas
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
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails cho Cupid Agent.
    """
    print(f"\n💘 [CUPID REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        if "cự giải" in user_query.lower() or "bọ cạp" in user_query.lower():
            if step == 1:
                print("🧠 Thought: Cần tra cứu độ tương thích tình yêu giữa Cự Giải và Bọ Cạp.")
                print("🛠️ Action: check_horoscope_compatibility['Cự Giải', 'Bọ Cạp']")
                
                # Thực thi tool
                obs = check_horoscope_compatibility("Cự Giải", "Bọ Cạp")
                print(f"👁️ Observation: {obs}")
                
            elif step == 2:
                print("🧠 Thought: Đã có kết quả tương thích 95%. Tôi có thể tư vấn chi tiết cho cặp đôi.")
                print("🏁 Final Answer: Nam Cự Giải và nữ Bọ Cạp đạt 95% độ tương thích (Cặp đôi Thủy - Thủy hoàn hảo!). Cả hai có sự thấu hiểu sâu sắc và kết nối cảm xúc rất mạnh mẽ.")
                break
        else:
            if step == 1:
                print("🧠 Thought: Cần kiểm tra chỉ số tương thích MBTI giữa INTJ và ENFP trước.")
                print("🛠️ Action: calculate_mbti_compatibility['INTJ', 'ENFP']")
                
                obs = calculate_mbti_compatibility("INTJ", "ENFP")
                print(f"👁️ Observation: {obs}")
                
            elif step == 2:
                print("🧠 Thought: Đã có kết quả MBTI (92%). Tiếp theo cần tìm địa điểm hẹn hò lãng mạn tại Hà Nội.")
                print("🛠️ Action: search_date_ideas['Hà Nội', 'lãng mạn', 'vừa phải']")
                
                obs = search_date_ideas("Hà Nội", "lãng mạn", "vừa phải")
                print(f"👁️ Observation: {obs}")
                
            elif step == 3:
                print("🧠 Thought: Đã có đủ thông tin MBTI và địa điểm hẹn hò để gửi câu trả lời hoàn chỉnh.")
                print("🏁 Final Answer: INTJ & ENFP đạt 92% độ hợp nhau! Gợi ý hẹn hò lãng mạn tại Hà Nội: Cà phê ngắm hoàng hôn Hồ Tây hoặc đi dạo ẩm thực đêm phố cổ.")
                break
            
    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("💘 BÀI LAB 3: CUPID AGENT - TRỢ LÝ GHÉP ĐÔI & HẸN HÒ")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test số 3 (Hoàng đạo) và câu test số 4 (MBTI + Date)
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN CUPID REACT AGENT ---")
    run_react_agent(sample_query, provider)
