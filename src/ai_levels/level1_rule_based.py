"""
🤖 CẤP ĐỘ 1: RULE-BASED BOT (Chatbot dựa trên luật if/else cố định)
Khớp từ khóa (keyword matching) với câu trả lời sẵn có. Không sử dụng LLM.
"""

def rule_based_bot(user_input: str) -> str:
    text = user_input.lower()
    if "chào" in text or "hi" in text or "hello" in text:
        return "🤖 [Cấp 1 - Rule-Based Bot]: Xin chào! Tôi là Bot luật cố định Cấp 1. Tôi chỉ trả lời theo từ khóa khớp sẵn."
    elif "tìm bạn gái" in text or "tìm nam" in text or "ghép đôi" in text:
        return "🤖 [Cấp 1 - Rule-Based Bot]: Vui lòng cung cấp chính xác từ khóa 'tim_kiem_ho_so'."
    elif "tương thích" in text or "điểm" in text:
        return "🤖 [Cấp 1 - Rule-Based Bot]: Tôi không có thuật toán tính toán ma trận điểm số hay so sánh hồ sơ!"
    elif "thời tiết" in text:
        return "🤖 [Cấp 1 - Rule-Based Bot]: Tôi là bot luật cố định, tôi không thể tra cứu dữ liệu thời tiết!"
    else:
        return "🤖 [Cấp 1 - Rule-Based Bot]: Xin lỗi, câu hỏi của bạn nằm ngoài tập luật (keywords) được cài đặt sẵn!"

if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 1: RULE-BASED BOT ===")
    test_queries = ["Chào bạn", "Tôi muốn tìm bạn gái", "Đánh giá tương thích giữa A và B"]
    for q in test_queries:
        print(f"User: {q}")
        print(f"Bot : {rule_based_bot(q)}\n")
