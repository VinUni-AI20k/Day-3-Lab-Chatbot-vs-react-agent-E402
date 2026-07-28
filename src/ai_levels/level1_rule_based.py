"""
🤖 CẤP ĐỘ 1: RULE-BASED BOT (Chatbot dựa trên luật if/else cố định)
Khớp từ khóa (keyword matching) với câu trả lời sẵn có. Không sử dụng LLM.
"""

def rule_based_bot(user_input: str) -> str:
    text = user_input.lower()
    if "chào" in text or "hi" in text or "hello" in text:
        return "Xin chào! Tôi là Rule-Based Bot (Cấp độ 1). Tôi có thể giúp gì cho bạn?"
    elif "giá" in text or "chi phí" in text or "vé" in text:
        return "Bảng giá dịch vụ: Vé phổ thông từ 1.500.000 VNĐ."
    elif "thời tiết" in text:
        return "Tôi là bot luật cố định (if/else), tôi không biết xem thời tiết hôm nay!"
    elif "liên hệ" in text or "hotline" in text:
        return "Hotline hỗ trợ: 1900-1234, Email: support@vinuni.edu.vn"
    else:
        return "Xin lỗi, câu hỏi của bạn nằm ngoài tập luật (keywords) được cài đặt sẵn!"

if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 1: RULE-BASED BOT ===")
    test_queries = ["Chào bạn", "Giá vé thế nào?", "Thời tiết Hà Nội?"]
    for q in test_queries:
        print(f"User: {q}")
        print(f"Bot : {rule_based_bot(q)}\n")
