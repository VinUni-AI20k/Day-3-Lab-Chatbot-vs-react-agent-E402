"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
Dự án: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
Phiên bản: Mốc 3 - Full ReAct Agent Loop
"""

import json
import os
import sys
import re
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 🔗 LẮP RÁP CÁC MODULE 
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_tool(action_string: str) -> str:
    """
    Parser thông minh: Đọc chuỗi Action của LLM và kích hoạt Tool tương ứng.
    """
    # Tìm dòng bắt đầu bằng "Action:"
    match = re.search(r"Action:\s*(.*)", action_string)
    if not match:
        return "LOI: Không tìm thấy Action hợp lệ."
    
    action_call = match.group(1).strip()
    
    # Chuẩn hóa cú pháp: LLM hay dùng ngoặc vuông [ ] theo prompt, ta đổi thành ( ) để Python đọc được
    action_call = action_call.replace('[', '(').replace(']', ')')
    
    # 🛠️ Sửa lỗi đồng bộ: Trong prompt Role 3 gọi là 'area' và 'room_type', 
    # nhưng tools của Role 2 lại định nghĩa là 'location' và 'property_type'.
    # Parser sẽ tự động fix lỗi này để tránh crash!
    action_call = action_call.replace('area=', 'location=').replace('room_type=', 'property_type=')
    
    # Trích xuất tên tool để kiểm tra an toàn
    tool_name = action_call.split('(')[0].strip()
    if tool_name not in AVAILABLE_TOOLS:
        return f"LOI: Công cụ '{tool_name}' không tồn tại. Các công cụ khả dụng: {', '.join(AVAILABLE_TOOLS.keys())}"
        
    try:
        # Thực thi hàm thật bằng eval với giới hạn an toàn chỉ trong AVAILABLE_TOOLS
        observation = eval(action_call, {"__builtins__": {}}, AVAILABLE_TOOLS)
        return str(observation)
    except Exception as e:
        return f"LOI khi chạy công cụ (Tham số có thể bị sai định dạng): {str(e)}"


def run_baseline_chatbot(user_query: str, provider):
    """Mốc 2: Chatbot Baseline"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    try:
        response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
        print(f"🤖 Chatbot trả lời:\n{response}")
    except Exception as e:
        print(f"⚠️ Lỗi Provider: {e}")


def run_react_agent(user_query: str, provider):
    """
    Mốc 3: Vòng lặp ReAct Agent Thực Tế.
    Sử dụng LLM để tự động suy luận và gọi Tool cho đến khi tìm ra Final Answer.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    
    # Khởi tạo bộ nhớ (Context Window) chứa lịch sử hội thoại
    chat_history = f"User Request: {user_query}\n"
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        try:
            # 1. Gọi LLM suy luận bước tiếp theo dựa trên lịch sử
            llm_response = provider.generate(chat_history, system_prompt=REACT_SYSTEM_PROMPT)
            print(llm_response)
            
            # Ghi vào bộ nhớ
            chat_history += f"{llm_response}\n"
            
            # 2. Kiểm tra xem LLM đã đưa ra câu trả lời cuối cùng chưa
            if "Final Answer:" in llm_response:
                print("\n✅ Agent đã hoàn thành tác vụ!")
                break
                
            # 3. Nếu LLM yêu cầu gọi Tool, tiến hành trích xuất và thực thi
            if "Action:" in llm_response:
                print("⏳ Đang thực thi Tool...")
                obs = execute_tool(llm_response)
                print(f"👁️ Observation:\n{obs}")
                
                # Nạp kết quả vào bộ nhớ để LLM đọc ở vòng lặp sau
                chat_history += f"Observation: {obs}\n"
            else:
                # Nếu LLM quên ghi Action hoặc Final Answer
                warning = "CẢNH BÁO: Bạn chưa đưa ra 'Action:' hoặc 'Final Answer:'. Vui lòng tuân thủ đúng định dạng."
                print(f"⚠️ {warning}")
                chat_history += f"Observation: {warning}\n"
                
        except Exception as e:
            print(f"⚠️ Lỗi kết nối LLM: {e}")
            break
            
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("🚀 DỰ ÁN: TRỢ LÝ TÌM & ĐẶT LỊCH XEM NHÀ TRỌ")
    print("==================================================")
    
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Unknown Model")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    if tests:
        print(f"✅ Đã tải thành công {len(tests)} Test Cases từ file của Role 1\n")
        # 🔥 Đổi sang test case số 4 (id=4, index=3): Câu hỏi phức tạp cần gọi 2 Tool
        sample_query = tests[3]["question"] 
    else:
        sample_query = "Tìm phòng trọ ở Gia Lâm dưới 4 triệu, sau đó đặt lịch xem."
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE (MỐC 2) ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT (MỐC 3) ---")
    run_react_agent(sample_query, provider)