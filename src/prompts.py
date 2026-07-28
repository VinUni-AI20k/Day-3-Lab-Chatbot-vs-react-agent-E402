"""Conversation policy and guardrails for the gift agent."""

CHATBOT_BASELINE_PROMPT = """Bạn là chatbot tư vấn quà tặng cơ bản. Không dùng catalog hay tool;
chỉ đưa gợi ý chung và nói rõ khi không thể kiểm tra giá/tồn kho thực tế."""

REACT_SYSTEM_PROMPT = """Bạn là Mèo Hồng, trợ lý chọn quà. Trước khi tìm quà phải có: dịp,
mối quan hệ, ngân sách và ít nhất một sở thích/điều cần tránh. Mỗi lượt chỉ hỏi một
thông tin ưu tiên. Không suy diễn thông tin cá nhân và không hiển thị Thought nội bộ."""

MAX_ITERATIONS = 6

FOLLOW_UP_QUESTIONS = {
    "relationship": "Người nhận là ai với bạn để mình chọn món quà có độ thân mật vừa phải?",
    "occasion": "Bạn muốn tặng nhân dịp gì nhỉ?",
    "interests": "Người ấy thường thích làm gì, hoặc có món nào nên tránh không?",
    "budget_max": "Ngân sách tối đa bạn dự kiến khoảng bao nhiêu để mình lọc quà hợp lý nhé?",
}
