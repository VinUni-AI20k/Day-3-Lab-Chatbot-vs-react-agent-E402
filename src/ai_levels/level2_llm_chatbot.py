"""
🤖 CẤP ĐỘ 2: LLM CHATBOT (Baseline Chatbot không có Tool)
Dùng LLM sinh câu trả lời tự nhiên mượt mà, nhưng không thể truy cập dữ liệu thời gian thực.
"""

CHATBOT_BASELINE_PROMPT = """Bạn là một Chatbot tư vấn thông thường.
Hãy trả lời câu hỏi của người dùng một cách thân thiện dựa trên kiến thức có sẵn.
Nếu không biết thông tin thực tế thời gian thực, hãy thông báo lịch sự cho người dùng.
"""

def llm_chatbot(user_input: str) -> str:
    text = user_input.lower()
    if "thời tiết" in text or "vé máy bay" in text:
        return "🤖 [LLM Chatbot]: Tôi là AI hội thoại nhưng không được cấp công cụ tra cứu dữ liệu thời gian thực, nên tôi không biết chính xác thời tiết/giá vé hôm nay!"
    else:
        return f"🤖 [LLM Chatbot]: Rất vui được hỗ trợ bạn về câu hỏi '{user_input}'!"

if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 2: LLM CHATBOT BASELINE ===")
    q = "Thời tiết Hà Nội hôm nay thế nào?"
    print(f"User: {q}")
    print(f"Bot : {llm_chatbot(q)}")
