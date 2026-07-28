# Báo Cáo Cá Nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và tên sinh viên**: Nguyễn Trương Ngọc Mai
- **Mã số sinh viên**: 2A202601652
- **Ngày**: 28/07/2026
- **Nhiệm vụ phụ trách**: Lập bảng Scoring Matrix (Agentic Fit) & Soi nhật ký Trace Log (Role 5).

---

## I. Đóng Góp Kỹ Thuật (15 Điểm)

- **Các module/tài liệu đã triển khai**:
  - [`docs/scoring_matrix_trace_log.md`](../docs/scoring_matrix_trace_log.md) — Bảng chấm điểm Agentic Fit + 5 trace log thực thi với API key thật (`LLM_PROVIDER=gemini`).
  - Xác minh pipeline tool (`search_candidates`, `calculate_compatibility`) bằng cách gọi trực tiếp hàm Python để phân tách kết quả xác định (deterministic) và văn phong LLM.

- **Điểm nổi bật trong công việc**:
  1. **Cập nhật Scoring Matrix**: Tổng điểm tăng **18/20 → 19/20**; *Dynamic Decision* đạt **5/5** do LLM ReAct truyền đúng JSON format, bỏ qua hoàn toàn whitelist địa danh cứng.
  2. **Giải quyết gap Trace Log cũ**: TC#1 và TC#5 hoạt động chuẩn xác trên đường đi JSON của ReAct thật.
  3. **Phát hiện bug F9**: Khi dùng API key thật, danh sách lọc lỗi ở `agent.py:353` bỏ sót các lỗi REST/Exception thực tế từ `GeminiProvider` (`"[Gemini REST API Error 429]"`, `"[Gemini Exception]"`), khiến agent chuyển thẳng lỗi thô ra người dùng và đánh dấu hoàn thành nhiệm vụ.
  4. **Độc lập với LLM**: Đo độ tương thích C001/C002 vẫn là **59.0/100** do thiếu package `sentence-transformers` (rơi vào Bag-of-Words fallback), khẳng định API key chỉ giải quyết tầng suy luận, không giải quyết nội hàm tool.

- **Tương tác với vòng lặp ReAct**: API key thật chuyển dạng lỗi từ "rule-based guardrail quá cứng" sang "bỏ sót quản lý lỗi/trạng thái Provider" (F9).

---

## II. Nghiên Cứu Tình Huống Debug (10 Điểm)

- **Mô tả vấn đề (Bug F9)**: Trong `agent.py:process_message()`, điều kiện `if llm_response:` chỉ kiểm tra chuỗi phi rỗng, không phân biệt output thành công hay chuỗi lỗi API từ Provider.

- **Nguồn bằng chứng**:
  ```python
  >>> fake_err = '[Gemini REST API Error 429]: {"error": {"message": "Resource exhausted"}}'
  >>> checked = ['[Groq Error]', '[Gemini Error]', '[OpenAI Error]', '[Anthropic Error]', '[OpenRouter Error]', '🤖 [Mock Provider]']
  >>> any(e in fake_err for e in checked)
  False  # Lỗi REST thật lọt qua lọc lỗi ở agent.py:353

  >>> re.search(r'Action:\s*`?([a-zA-Z0-9_]+)`?\s*\[(.*Wait/json...)\]', fake_err) # matching action format
  None   # Agent coi lỗi này là Final Answer, set is_task_complete=True
  ```

- **Chẩn đoán**: Lỗi tầng điều phối (`process_message()`).
  1. `agent.py:353` chỉ liệt kê câu lỗi "chưa cấu hình API key", không chứa pattern lỗi runtime dạng `f"[X Exception]"` hay `f"[X API Error {code}]"`.
  2. `if llm_response:` đẩy chuỗi lỗi ra cho người dùng và set `is_task_complete=True`. Bug chỉ xuất hiện khi chạy API key thật (Mock Provider không sinh lỗi này).

- **Giải pháp**:
  1. **Ngắn hạn**: Bắt lỗi qua regex tổng quát `re.match(r'^\[\w+ (Error|Exception)', llm_out)`.
  2. **Dài hạn**: Đổi Provider sang `raise Exception` hoặc trả về status rõ ràng; chỉ set `is_task_complete=True` khi `execution_trace` có bước `Observation` hợp lệ.

---

## III. Nhận Định Cá Nhân: Chatbot vs ReAct (10 Điểm)

1. **Suy luận (Reasoning)**: Với API key thật, chuỗi `Thought → Action → Observation → Final Answer` thực thi trọn vẹn trong 1 lượt gọi, thể hiện rõ năng lực hành động thực tế vượt trội hơn Chatbot Cấp 2.
2. **Độ tin cậy (Reliability)**: Rủi ro chuyển từ "rule-based quá cứng" sang "im lặng nuốt lỗi hệ thống" (F9). Trạng thái quản lý lỗi kém làm giảm độ tin cậy dù suy luận của LLM đúng.
3. **Quan sát (Observation)**: Thiếu lớp Observation về **trạng thái hoạt động của Provider** để loop ReAct đưa ra quyết định xử lý sự cố (retry/fallback).

---

## IV. Cải Tiến Trong Tương Lai (5 Điểm)

- **Khả năng mở rộng (Scalability)**: Hạ ưu tiên đồng bộ whitelist địa danh xuống mức dự phòng guardrail.
- **An toàn (Safety)**: Phân loại tường minh output từ Provider (Hợp lệ / Lỗi hệ thống / Retry) thay vì so khớp chuỗi cứng.
- **Hiệu năng (Performance)**: Ghi log có cấu trúc (structured JSON log với `provider_status`, `is_error`, `latency`) để phát hiện tự động các bug như F9.