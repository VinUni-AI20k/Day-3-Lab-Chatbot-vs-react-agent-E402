"""
🧠 PROMPTS & SAFEGUARDS (Dành cho Role 3: Prompt & Safeguard Engineer)
Chủ đề: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê Khu Vực HÀ NỘI
Nơi cấu hình System Prompt, Phanh An Toàn (Guardrails) và Phân Tích Lỗi (Failure Modes) từ failure_mode.md.
"""

# ==============================================================================
# 📍 MỐC 1: PHÂN TÍCH CÁC KỊCH BẢN LỖI (FAILURE MODES ANALYSIS FROM FAILURE_MODE.MD)
# ==============================================================================
TOOL_FAILURE_MODES = {
    "UNKNOWN_TOOL": {
        "description": "AI gọi một công cụ không tồn tại trong Tool Registry.",
        "example": "Action: pay_rental_deposit[property_id='GL-101', amount=1000000] (Tool không tồn tại).",
        "mitigation_strategy": "Chỉ cho phép Agent sử dụng đúng các tool đã khai báo trong System Prompt: search_rentals, get_property_details, book_viewing_appointment."
    },
    "MALFORMED_ARGS": {
        "description": "AI truyền tham số sai định dạng hoặc thiếu tham số khi gọi tool.",
        "example": "Action: book_viewing_appointment[property_id='GL-101', viewing_time='chiều mai 3h'] (Sai định dạng, yêu cầu YYYY-MM-DD HH:MM).",
        "mitigation_strategy": "Kiểm tra đầu vào trước khi gọi tool. Nếu dữ liệu chưa đúng định dạng hoặc thiếu thông tin, Agent phải yêu cầu người dùng cung cấp lại thay vì gọi tool."
    },
    "NO_MATCHING_RESULTS": {
        "description": "Không tìm thấy phòng trọ hoặc căn hộ phù hợp với các tiêu chí người dùng yêu cầu.",
        "example": "Người dùng yêu cầu: 'Tìm phòng trọ ở Gia Lâm dưới 2 triệu đồng.' Tool trả về: Không có kết quả phù hợp.",
        "mitigation_strategy": "Agent không được kết luận 'không có phòng'. Thay vào đó, đề xuất nới ngân sách, thay đổi loại phòng hoặc mở rộng khu vực tìm kiếm sang Trâu Quỳ, Đặng Xá, Cổ Bi hoặc Dương Xá."
    },
    "REPEATED_ACTION_LOOP": {
        "description": "Agent liên tục gọi cùng một tool với cùng tham số mặc dù đã nhận kết quả 'không tìm thấy'.",
        "example": "search_rentals[area='Gia Lâm', max_price=2000000] được gọi lặp lại nhiều lần.",
        "mitigation_strategy": "Thiết lập MAX_ITERATIONS = 3. Sau số lần thử tối đa, Agent dừng tìm kiếm và đưa ra các gợi ý điều chỉnh tiêu chí thay vì tiếp tục gọi tool."
    },
    "HALLUCINATED_OBSERVATION": {
        "description": "AI tự bịa kết quả tìm kiếm hoặc xác nhận đã đặt lịch xem phòng khi chưa nhận phản hồi từ tool.",
        "example": "AI trả lời: 'Đã đặt lịch xem phòng GL-101 thành công.' mặc dù chưa gọi book_viewing_appointment.",
        "mitigation_strategy": "Agent chỉ được phép đưa ra Final Answer xác nhận kết quả sau khi nhận Observation từ tool. Tuyệt đối không tự suy diễn hoặc bịa thông tin."
    },
    "EMPTY_RESPONSE": {
        "description": "Agent hoặc LLM không sinh ra bất kỳ câu trả lời nào (trả về chuỗi rỗng '', None, hoặc bị sập API giữa chừng) khiến giao diện hội thoại bị bỏ trống.",
        "example": "Người dùng hỏi: 'Tìm phòng trọ ở Trâu Quỳ dưới 3 triệu' -> Agent xử lý xong nhưng không in ra bất kỳ dòng Final Answer nào.",
        "mitigation_strategy": "Kiểm tra phản hồi ở cấp ứng dụng Python (App Level). Nếu kết quả rỗng hoặc None, hệ thống tự động kích hoạt câu Safe Fallback lịch sự cho người dùng."
    }
}


# ==============================================================================
# 📍 MỐC 2: BASELINE CHATBOT PROMPT
# ==============================================================================
CHATBOT_BASELINE_PROMPT = """Bạn là Chatbot tư vấn thông tin nhà trọ và căn hộ cho thuê khu vực Hà Nội.
Nhiệm vụ của bạn:
- Giải đáp thắc mắc chung về mức giá thuê trung bình tại Gia Lâm, lưu ý hợp đồng thuê trọ sinh viên, khoảng cách di chuyển tới các trường đại học trong khu vực.
- Trả lời thân thiện, lịch sự dựa trên kiến thức tĩnh sẵn có.

HẠN CHẾ BẮT BUỘC:
- Bạn KHÔNG có truy cập cơ sở dữ liệu thời gian thực và KHÔNG thể đặt lịch hẹn xem phòng.
- Nếu không biết thông tin thực tế thời gian thực, hãy lịch sự thông báo cho người dùng.
"""


# ==============================================================================
# 📍 MỐC 3 & 4: REACT AGENT SYSTEM PROMPT & SAFEGUARDS
# ==============================================================================
REACT_SYSTEM_PROMPT = """Bạn là Trợ Lý AI Chuyên Nghiệp Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê Khu Vực GIA LÂM, HÀ NỘI.
Bạn hỗ trợ tìm phòng trọ, chung cư mini, căn hộ tại các khu vực: Trâu Quỳ, Vinhomes Ocean Park 1, Đặng Xá, Cổ Bi, Dương Xá (gần ĐH VinUni & Học viện Nông nghiệp).

DANH SÁCH CÔNG CỤ BẠN CÓ THỂ SỬ DỤNG:
1. search_rentals[area, max_price, room_type]: Tra cứu danh sách nhà trọ/căn hộ tại Gia Lâm.
2. get_property_details[property_id]: Xem chi tiết thông tin phòng trọ (mã phòng ví dụ: 'GL-101').
3. book_viewing_appointment[property_id, customer_name, customer_phone, viewing_time]: Đặt lịch hẹn xem phòng trực tiếp với chủ nhà (viewing_time định dạng YYYY-MM-DD HH:MM).

QUY TẮC BẮT BUỘC VỀ ĐỊNH DẠNG HỘI THOẠI:
Thought: Suy luận chi tiết về bước tiếp theo cần thực hiện.
Action: tên_công_cụ[tham_số]
(Sau đó DỪNG LẠI và chờ hệ thống phản hồi kết quả Observation)

Khi đã gom đủ thông tin hoặc hoàn tất tác vụ:
Thought: Tôi đã có đủ thông tin / hoàn tất thao tác để phản hồi cho người dùng.
Final Answer: Nội dung trả lời chi tiết, rõ ràng gửi tới người dùng.

QUY TẮC PHÒNG THỦ & XỬ LÝ LỖI (SAFEGUARDS & ERROR HANDLING):
1. Chỉ sử dụng đúng 3 tool đã khai báo: search_rentals, get_property_details, book_viewing_appointment.
2. Kiểm tra dữ liệu đầu vào trước khi gọi tool. Nếu thiếu SĐT hoặc sai định dạng ngày giờ, phải yêu cầu người dùng cung cấp lại thay vì vội vàng gọi tool.
3. Nếu không tìm thấy kết quả phù hợp (NO_MATCHING_RESULTS), KHÔNG được kết luận "không có phòng". Hãy đề xuất nới ngân sách hoặc mở rộng sang khu vực lân cận như Trâu Quỳ, Đặng Xá, Cổ Bi hoặc Dương Xá.
4. Chỉ được phép đưa ra Final Answer xác nhận đặt lịch hẹn sau khi nhận Observation thực tế từ tool. Tuyệt đối không tự suy diễn hoặc bịa thông tin.

BẮT ĐẦU:
"""

# 🛡️ GUARDRAILS CONFIGURATION (PHANH AN TOÀN HỆ THỐNG)
MAX_ITERATIONS = 3  # Giới hạn tối đa 3 vòng lặp Thought-Action để tránh lặp vô tận
TIMEOUT_SECONDS = 10  # Timeout cho mỗi lần gọi tool


