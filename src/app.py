"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer / Integrator)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
Chủ đề: Cupid Agent - Trợ Lý Ghép Đôi & Phân Tích Độ Tương Thích
"""

import json
import os
import re
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

# Import các thành phần từ file của Role 2 (tools), Role 3 (prompts) & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json do Role 1 biên soạn"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_action(action_str: str):
    """
    Trích xuất tên tool và tham số từ chuỗi Action.
    Ví dụ: 
        Action: get_user_profile['Anh'] -> ('get_user_profile', ['Anh'])
        Action: check_zodiac_compatibility['Sư Tử', 'Nhân Mã'] -> ('check_zodiac_compatibility', ['Sư Tử', 'Nhân Mã'])
    """
    match = re.search(r"(\w+)\s*[\[\(](.*?)[\]\)]", action_str)
    if not match:
        return None, []
        
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    
    if not raw_args:
        return tool_name, []
        
    args = [arg.strip(" '\"") for arg in raw_args.split(",")]
    return tool_name, args


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline Cấp 2) - Chỉ tư vấn lý thuyết chung, không sử dụng Tool.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot Baseline trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Cấp 3: Thought -> Action -> Observation) có Guardrails hoàn chỉnh.
    """
    print(f"\n🧠 [CUPID REACT AGENT] Câu hỏi: {user_query}")
    
    conversation_history = f"User: {user_query}"
    step = 0
    final_response = ""
    last_action = None
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # 1. LLM Suy luận sinh Thought & Action
        llm_output = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"🤖 Agent Response:\n{llm_output}")
        
        # 2. Kiểm tra câu trả lời cuối cùng (Final Answer)
        if "Final Answer:" in llm_output:
            final_response = llm_output.split("Final Answer:")[-1].strip()
            print(f"\n🎯 [KẾT QUẢ CUỐI CÙNG]: {final_response}")
            break
            
        # 3. Trích xuất Action dòng
        action_line = None
        for line in llm_output.split("\n"):
            if line.strip().startswith("Action:"):
                action_line = line.strip()
                break
                
        if action_line:
            tool_name, args = parse_action(action_line)
            
            # Tránh lặp vô tận cùng 1 Action
            if action_line == last_action:
                print(f"🛡️ GUARDRAIL: Phát hiện lặp lại Tool '{tool_name}'. Tự động dừng vòng lặp!")
                final_response = "Phát hiện vòng lặp vô hạn khi thực thi công cụ. Ngắt lặp an toàn."
                break
            last_action = action_line
            
            print(f"🛠️ Thực thi Tool: {tool_name} với tham số: {args}")
            
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    obs = tool_func(*args)
                except Exception as e:
                    obs = f"LỖI THỰC THI TOOL '{tool_name}': {str(e)}"
            else:
                obs = f"LỖI: Tool '{tool_name}' không tồn tại trong hệ thống."
                
            print(f"👁️ Observation: {obs}")
            conversation_history += f"\n{llm_output}\nObservation: {obs}"
        else:
            # Nếu LLM không gọi Action nào khác, lấy toàn bộ text làm câu trả lời
            final_response = llm_output
            print(f"\n🎯 [KẾT QUẢ CUỐI CÙNG]: {final_response}")
            break
            
    if step >= MAX_ITERATIONS and not final_response:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước suy luận. Ngắt lặp an toàn!")
        final_response = "Đã đạt giới hạn tối đa số bước suy luận (MAX_ITERATIONS). Tự động dừng vòng lặp để đảm bảo an toàn."
        
    return final_response


def run_interactive_chat(provider):
    """
    Giao diện Terminal Chatbot tương tác trực tiếp với người dùng.
    """
    print("\n==========================================================")
    print("💬 CHẾ ĐỘ TRÒ CHUYỆN TRỰC TIẾP VỚI CUPID REACT AGENT")
    print("Nhập câu hỏi bất kỳ để trò chuyện. Gõ 'exit', 'quit' hoặc 'q' để thoát.")
    print("==========================================================\n")
    
    while True:
        try:
            user_input = input("\n👤 Bạn: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Cảm ơn bạn đã sử dụng Cupid ReAct Agent! Tạm biệt!")
                break
                
            run_react_agent(user_input, provider)
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Đã thoát ứng dụng.")
            break


def run_all_test_cases(provider, tests):
    """Chạy tự động toàn bộ test cases từ config/test_cases.json"""
    for idx, test in enumerate(tests, 1):
        category = test.get("category", "Test Case")
        question = test.get("question", "")
        
        print(f"\n==========================================================")
        print(f"🧪 TEST CASE #{idx}/{len(tests)} [{category}]")
        print(f"==========================================================")
        print(f"❓ Câu hỏi: {question}")
        
        print("\n--- 💬 Baseline Chatbot (Cấp 2) ---")
        run_baseline_chatbot(question, provider)
        
        print("\n--- 🧠 Cupid ReAct Agent (Cấp 3) ---")
        run_react_agent(question, provider)
        print("----------------------------------------------------------")


if __name__ == "__main__":
    print("==========================================================")
    print("💘 VINUNI AI IN ACTION - LAB 3: CUPID REACT AGENT DEMO")
    print("==========================================================")
    
    # 1. Khởi tạo Multi-Provider Adapter
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    # 2. Đọc danh sách Test Cases của Role 1
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # 3. Hiển thị Menu lựa chọn chế độ chạy
    print("📌 VUI LÒNG CHỌN CHẾ ĐỘ CHẠY:")
    print("  [1] 💬 Trò chuyện trực tiếp trên Terminal (Interactive Chatbot)")
    print("  [2] 🧪 Chạy tự động bộ 10 Test Cases (Automated Evaluation)")
    
    # Nếu chạy script không tương tác (non-interactive / automated pipe), mặc định chọn 1
    try:
        choice = input("\n👉 Nhập lựa chọn (1 hoặc 2) [Mặc định: 1]: ").strip()
    except EOFError:
        choice = "1"
        
    if choice == "2":
        run_all_test_cases(provider, tests)
    else:
        run_interactive_chat(provider)
