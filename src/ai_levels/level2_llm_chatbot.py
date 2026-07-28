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
    if provider is None:
        provider = get_llm_provider()
    
    response = provider.generate(user_input, system_prompt=CHATBOT_BASELINE_PROMPT)
    return f"🤖 [Cấp 2 - LLM Chatbot ({provider.__class__.__name__})]:\n{response}"

if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 2: LLM CHATBOT BASELINE ===")
    provider = get_llm_provider()
    q = "Hãy tìm cho tôi bạn gái ở Hà Nội khoảng 24 tuổi thích nghe nhạc indie."
    print(f"User: {q}")
    print(llm_chatbot(q, provider))
