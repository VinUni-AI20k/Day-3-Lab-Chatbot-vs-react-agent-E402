"""
🤖 CẤP ĐỘ 2: LLM CHATBOT (Baseline Chatbot không có Tool)
Dùng LLM (Gemini) sinh câu trả lời tự nhiên mượt mà, nhưng không thể truy cập dữ liệu thực tế thời gian thực.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from providers import get_llm_provider
from prompts import CHATBOT_BASELINE_PROMPT

def llm_chatbot(user_input: str, provider=None) -> str:
    # Guardrail 1: Input Validation
    if not user_input or not str(user_input).strip():
        return "[Cấp 2 - LLM Chatbot]: Vui lòng nhập câu hỏi hợp lệ!"

    if provider is None:
        provider = get_llm_provider()
    
    # Guardrail 2: Exception Fallback Handling
    try:
        response = provider.generate(str(user_input).strip(), system_prompt=CHATBOT_BASELINE_PROMPT)
        if not response or "[Error]" in response or "[Exception]" in response:
            return f"[Cấp 2 - LLM Chatbot]: Hệ thống tạm thời chưa thể phản hồi. Chi tiết: {response}"
        return f"[Cấp 2 - LLM Chatbot ({provider.__class__.__name__})]:\n{response}"
    except Exception as e:
        return f"[Cấp 2 - LLM Chatbot Error]: Lỗi xử lý phản hồi ({str(e)})"

if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 2: LLM CHATBOT BASELINE ===")
    provider = get_llm_provider()
    q = "Hãy tìm cho tôi bạn gái ở Hà Nội khoảng 24 tuổi thích nghe nhạc indie."
    print(f"User: {q}")
    print(llm_chatbot(q, provider))
