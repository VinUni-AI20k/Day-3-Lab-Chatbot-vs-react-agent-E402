"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import re
import ast
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
from tools import AVAILABLE_TOOLS, get_weather, search_flights
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
<<<<<<< Updated upstream
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
=======
    Chạy đúng một lượt sinh phản hồi bằng LLM, không gọi công cụ (Mốc 2).
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
>>>>>>> Stashed changes
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def parse_action(text: str):
    """Trích xuất tên tool và tham số từ dòng Action: tool_name[arg1, arg2] hoặc Action: tool_name(arg1, arg2)"""
    match = re.search(r"Action:\s*(\w+)\s*[\[\(](.*?)[\]\)]", text, re.DOTALL)
    if not match:
        return None, []
    
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    
    if not raw_args:
        return tool_name, []
        
    try:
        parsed = ast.literal_eval(f"({raw_args})")
        if isinstance(parsed, tuple):
            return tool_name, list(parsed)
        else:
            return tool_name, [parsed]
    except Exception:
        # Fallback: tách theo dấu phẩy và làm sạch dấu ngoặc kép / đơn
        args = [arg.strip().strip("'\"`") for arg in raw_args.split(",")]
        return tool_name, args


def execute_tool(tool_name: str, args: list) -> str:
    """Thực thi tool an toàn từ AVAILABLE_TOOLS và trả về chuỗi kết quả (Observation)."""
    if tool_name not in AVAILABLE_TOOLS:
        return f"LỖI: Công cụ '{tool_name}' không tồn tại trong hệ thống. Vui lòng kiểm tra lại."
    
    tool_func = AVAILABLE_TOOLS[tool_name]
    try:
        result = tool_func(*args)
        return str(result)
    except TypeError as e:
        return f"LỖI: Truyền tham số không đúng cho công cụ '{tool_name}' ({str(e)})."
    except Exception as e:
        return f"LỖI THỰC THI TOOL [{tool_name}]: {str(e)}"


def run_react_agent(user_query: str, provider):
    """
<<<<<<< Updated upstream
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        if step == 1:
            print("🧠 Thought: Câu hỏi này cần tra cứu thời tiết thời gian thực.")
            print("🛠️ Action: get_weather['Hà Nội']")
            
            # Thực thi tool
            obs = get_weather("Hà Nội")
            print(f"👁️ Observation: {obs}")
            
        elif step == 2:
            print("🧠 Thought: Tôi đã có thông tin thời tiết Hà Nội, giờ tôi có thể tư vấn trang phục.")
            print("🏁 Final Answer: Thời tiết Hà Nội hôm nay 28°C, nắng nhẹ. Bạn nên mặc áo phông thoáng mát!")
            break
            
    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
=======
    Chạy vòng lặp ReAct Agent (Mốc 3):
    Suy luận (Thought) -> Gọi công cụ (Action) -> Quan sát (Observation) -> Trả lời (Final Answer).
    Bao gồm Phanh An Toàn Guardrail (MAX_ITERATIONS).
    """
    print(f"\n🧠 [REACT AGENT] Câu hỏi: {user_query}")
    
    conversation_history = f"User Question: {user_query}\n"
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n🔄 --- Vòng lặp ReAct #{iteration}/{MAX_ITERATIONS} ---")
        
        prompt = conversation_history
        response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"🤖 Agent:\n{response}")
        
        # Kiểm tra xem Agent đã đưa ra Final Answer chưa
        if "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
            print(f"\n🎯 [FINAL ANSWER]: {final_answer}")
            return response
            
        # Trích xuất Action từ phản hồi của Agent
        tool_name, args = parse_action(response)
        if tool_name:
            print(f"🛠️ [ACTION DETECTED]: Gọi tool '{tool_name}' với tham số: {args}")
            observation = execute_tool(tool_name, args)
            print(f"👁️ [OBSERVATION]:\n{observation}")
            
            conversation_history += f"\n{response}\nObservation: {observation}\n"
        else:
            print("⚠️ [WARNING]: Agent không đưa ra Action hợp lệ hay Final Answer. Yêu cầu định dạng lại...")
            conversation_history += f"\n{response}\nObservation: LỖI: Vui lòng đưa ra Action đúng định dạng 'Action: tool_name[args]' hoặc 'Final Answer: câu_trả_lời'.\n"
            
    # 🛡️ GUARDRAIL TRIGGERED
    print(f"\n🛡️ [GUARDRAIL TRIGGERED]: Đã vượt quá số lần thử tối đa (MAX_ITERATIONS={MAX_ITERATIONS}). Ngắt vòng lặp.")
    fallback_msg = (
        "Xin lỗi, tôi đã thử tra cứu nhiều lần nhưng không thể hoàn thành yêu cầu do dữ liệu không hợp lệ "
        "hoặc gặp sự cố hệ thống. Vui lòng cung cấp lại mã đơn hàng/thông tin chính xác hoặc liên hệ bộ phận hỗ trợ."
    )
    print(f"🤖 Agent (Fallback Response):\nFinal Answer: {fallback_msg}")
    return f"Final Answer: {fallback_msg}"
>>>>>>> Stashed changes


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
<<<<<<< Updated upstream
    # Chạy thử câu test số 3
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
=======
    print("==================================================")
    print("--- MỐC 2: CHẠY CHATBOT BASELINE TRÊN 5 TEST CASES ---")
    print("==================================================")
    for test_case in tests:
        print(
            f"\n{'-' * 50}\n"
            f"Test #{test_case['id']} — {test_case['category']}\n"
            f"Kỳ vọng: {test_case['expected_behavior']}"
        )
        run_baseline_chatbot(test_case["question"], provider)

    print("\n==================================================")
    print("--- MỐC 3: CHẠY REACT AGENT TRÊN 5 TEST CASES ---")
    print("==================================================")
    react_results = []
    for test_case in tests:
        print(
            f"\n{'-' * 50}\n"
            f"Test #{test_case['id']} — {test_case['category']}\n"
            f"Kỳ vọng: {test_case['expected_behavior']}"
        )
        res = run_react_agent(test_case["question"], provider)
        react_results.append(res)

    print("\n✅ HOÀN THÀNH TOÀN BỘ 5 TEST CASES TRÊN CẢ CHATBOT BASELINE VÀ REACT AGENT!")
>>>>>>> Stashed changes
