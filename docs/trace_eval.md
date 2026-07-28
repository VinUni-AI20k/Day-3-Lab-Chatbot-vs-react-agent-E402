# SCORING MATRIX & TRACE LOG — AI MATCHMAKING AGENT ("Bà Mối AI")

## 1. Bảng chấm điểm Agentic Fit (Scoring Matrix)

| Tiêu chí | Điểm (1-5) | Bằng chứng trong code | Lý do đánh giá |
| :--- | :---: | :--- | :--- |
| **Multi-step Reasoning** | 5/5 | `process_message_llm_react()` (agent.py:333-399), `MAX_ITERATIONS=5` | Thực thi chuỗi `Thought → Action → Observation → Final Answer` trong cùng một lượt gọi. |
| **Tool Interaction** | 5/5 | `src/tools.py: AVAILABLE_TOOLS`, `parse_and_execute_tool()` | Định dạng đầu vào/đầu ra Pydantic. LLM truyền JSON trực tiếp, bỏ qua whitelist rule-based. |
| **Dynamic Decision** | **5/5** ⬆(trước: 4/5) | `parse_and_execute_tool()` (agent.py:38-43) | **Nâng điểm**: LLM trích xuất vị trí tự do ("Cà Mau") dạng JSON, kích hoạt Relaxed Search thành công. *Residual risk*: Whitelist cũ vẫn tồn tại làm nhánh dự phòng nếu model trả sai định dạng. |
| **Long Horizon** | 4/5 | `conversation_history` (agent.py:340-342), `is_task_complete` (agent.py:408) | Duy trì ngữ cảnh tốt nhưng `is_task_complete=True` bị set vội ngay khi có `llm_response`, kể cả khi LLM mới chỉ hỏi lại thông tin (xem F9). |
| **TỔNG ĐIỂM FIT** | **19/20** ⬆(trước: 18/20) | — | **Rất phù hợp với ReAct Agent**. Rủi ro chuyển từ "guardrail rule-based cứng" sang "quản lý trạng thái/lỗi API" (F9). |

---

## 2. Bộ Test Case (theo `config/test_cases.json`)

| # | Category | Câu hỏi | Kỳ vọng |
| :---: | :--- | :--- | :--- |
| 1 | Đơn giản | *"Tiêu chuẩn cho một mối quan hệ lành mạnh và bền vững là gì?"* | Trả lời trực tiếp, không cần tool |
| 2 | Search | *"Tìm bạn gái 22-28 tuổi Hà Nội, thích nhạc indie, vẽ tranh, cà phê"* | Gọi `search_candidates`, có PII masking |
| 3 | Compatibility | *"Đánh giá tương thích C001 & C002"* | Gọi `calculate_compatibility`, ra điểm + breakdown |
| 4 | Slot Filling | *"Tôi muốn tìm bạn gái để tìm hiểu hẹn hò."* | Thiếu slot → hỏi lại, KHÔNG gọi tool |
| 5 | Edge Case | *"18-20 tuổi, Cà Mau, thích leo núi tuyết"* | Kỳ vọng: Relaxed Search khi 0 kết quả |

---

## 3. Trace Log (nhánh `process_message_llm_react()` thật, có API key)

### 3.5. TEST CASE #1 — Câu hỏi đơn giản
- **LLM**: Chọn trả lời trực tiếp về kiến thức chung, không phát lệnh `Action:`.
- **Phát hiện**: Không còn bị gán nhầm `intent=SEARCH` hay bắt buộc gọi tool như nhánh Rule-based.
- **Rủi ro (F9)**: `is_task_complete=True` tự động được set bất kể nội dung trả lời.

### 3.6. TEST CASE #2 — Search đầy đủ tham số
- **Action**: `search_candidates[{"target_gender": "Nữ", "min_age": 22, "max_age": 28, "location": "Hà Nội", "query_interests": "thích nghe nhạc indie, vẽ tranh và đi cà phê"}]`
- **TOOL output**: Tìm thấy 3 ứng viên (C002: 50.5, C006: 34.3, C010: 22.0), `is_relaxed_search=false`.
- **Phát hiện**: Tool deterministic hoạt động chính xác, PII được che giữa (ví dụ: `0987***321`).

### 3.7. TEST CASE #3 — Compatibility
- **Action**: `calculate_compatibility["C001", "C002"]`
- **TOOL output**: Điểm tổng `59.0/100`.
- **Phát hiện**: Điểm thực đo **59.0/100** do thiếu package `sentence-transformers` (rơi vào Bag-of-Words fallback), độc lập hoàn toàn với việc có API key hay không.

### 3.8. TEST CASE #4 — Slot Filling Loop
- **LLM**: Phát hiện thiếu slot tuổi/vị trí/sở thích → Không gọi tool, hỏi lại người dùng.
- **Phát hiện (F9)**: Tuân thủ prompt tốt, nhưng `is_task_complete` bị set `True` ngay cả khi công việc chưa hoàn thành (bất nhất với nhánh Fallback).

### 3.9. TEST CASE #5 — Edge Case (kỳ vọng Relaxed Search)
- **Action**: `search_candidates[{"target_gender": "Nữ", "min_age": 18, "max_age": 20, "location": "Cà Mau", "query_interests": "thích đi leo núi tuyết"}]`
- **TOOL output**: Tra về 3 gợi ý nới lỏng (`is_relaxed_search=true`).
- **Phát hiện**: Bug F3 (whitelist địa danh) được giải quyết trên đường đi JSON. Tuy nhiên, nếu LLM trả tham số dạng CSV, whitelist cứng ở `agent.py:80` vẫn có nguy cơ gây lỗi.

---

## 4. Tổng hợp phát hiện từ việc soi Trace Log

| # | Phát hiện | Vị trí trong code | Mức độ | Trạng thái | Đề xuất |
| :---: | :--- | :--- | :---: | :---: | :--- |
| F1 | Thiếu API key | `agent.py:352-354` | — | **Đã xử lý** | Đã cấu hình `GEMINI_API_KEY`. |
| F2 | Gán nhầm intent câu hỏi đơn giản | `agent.py: extract_intent_and_slots()` | — | **Đã xử lý** | LLM trả lời trực tiếp không cần Action. |
| F3 | Whitelist địa danh cứng (8 tỉnh/thành) | `agent.py:270`, `agent.py:80` | Trung bình | **Thu hẹp phạm vi** | Mở rộng whitelist lên 63 tỉnh/thành để phòng thủ dự phòng. |
| F4 | Điểm compatibility lệch do thiếu thư viện | `tools/compatibility.py:34-75` | Trung bình | **Chưa xử lý** | Cài đặt `sentence-transformers` hoặc ghi rõ chế độ fallback. |
| F5 | PII Masking sđt/tên | `tools/search.py` | Đạt | **Đạt** | Giữ nguyên. |
| F6 | Guardrail hỏi lại khi thiếu slot | `agent.py: process_message()` | Đạt | **Đạt** | Giữ nguyên. |
| F7 | Từ chối tool khi thiếu tham số | `agent.py:88-100` | Đạt | **Đạt** | Giữ nguyên. |
| F8 | Lọc hallucination sau Action | `agent.py:365-370` | Đạt | **Đạt** | Giữ nguyên. |
| F9 | **Lỗi nuốt exception & set `is_task_complete` sai** | `agent.py:353`, `agent.py:408-412` | **Cao** | **Chưa vá** | 1. Chỉ set `is_task_complete=True` khi có `Observation` thành công.<br>2. Bắt exception/lỗi REST API (`429`, v.v.) bằng `try/except` hoặc regex thay vì so khớp chuỗi cứng. |

---

## 5. Kết luận

- **Scoring Matrix**: Đạt **19/20** điểm nhờ khả năng gọi tool linh hoạt bằng JSON của LLM thật.
- **Trace Log**: Các bug chặn luồng chính (F2, F3) đã được giải quyết qua đường truyền JSON.
- **Phát hiện quan trọng (F9)**: Xảy ra do hệ thống lọt lưới các thông báo lỗi REST API (`429 Resource Exhausted`, v.v.) và set `is_task_complete=True` vô điều kiện.
- **Khuyến nghị**:
  1. Ưu tiên vá bug F9 ở tầng điều phối.
  2. Mở rộng whitelist địa danh phòng ngừa model trả sai format.
  3. Bổ sung `sentence-transformers` để đồng nhất kết quả tính tương thích.