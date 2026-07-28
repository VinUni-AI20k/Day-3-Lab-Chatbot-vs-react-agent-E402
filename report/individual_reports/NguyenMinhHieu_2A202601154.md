# 📝 BÁO CÁO CÁ NHÂN — NGUYỄN MINH HIẾU (2A202601154)

> **Vai trò:** Role 3 — Prompt Engineer  
> **File phụ trách:** `src/prompts.py`  
> **Dự án:** Mèo Hồng — Trợ lý nắm bắt tính cách & chọn quà tặng phù hợp

---

## 📍 Mốc 1: Xác định các trường hợp Tool có thể bị lỗi (Failure Modes)

### Nhiệm vụ
Xác định các trường hợp tool có thể bị lỗi (Failure Modes) để chuẩn bị cho việc viết Guardrails ở Mốc 3.

### Công việc đã thực hiện
Phân tích 2 tools chính mà nhóm dự định sử dụng và liệt kê các failure modes có thể xảy ra:

#### Tool 1: Profile Extraction/Completeness Tool (trích xuất & kiểm tra hồ sơ người nhận quà)

| # | Failure Mode | Ví dụ | Hậu quả | Giải pháp/Fallback |
|---|---|---|---|---|
| 1 | **Thông tin mâu thuẫn** | "Ngân sách 0 đồng" hoặc "thích công nghệ nhưng muốn quà cổ điển" | Tool không xác định được giá trị hợp lệ để lưu vào state | Agent nhận diện mâu thuẫn và hỏi lại lịch sự |
| 2 | **Dữ liệu quá mơ hồ** | "Tìm quà cho nó", "gì cũng được", "rẻ rẻ thôi" | Không map được vào danh mục cụ thể | Tool trả trạng thái "thiếu thông tin" → Agent hỏi làm rõ |
| 3 | **Trích xuất sai trường** | "Tặng sách cho bạn" → tool nhầm "sách" thành dịp tặng | Truy vấn tìm quà bị sai lệch | Dùng schema ràng buộc kiểu dữ liệu đầu ra |
| 4 | **Vượt quá số lần hỏi** | Người dùng liên tục nói không liên quan → agent kẹt loop | Agent không bao giờ đủ thông tin để tìm quà | Guardrail `MAX_ITERATIONS` → ngắt và fallback |

#### Tool 2: Web Search Tool (tìm kiếm quà tặng trả về đường link)

| # | Failure Mode | Ví dụ | Hậu quả | Giải pháp/Fallback |
|---|---|---|---|---|
| 1 | **Không có kết quả** | Điều kiện lọc quá khắt khe: "quà cho sếp, dưới 50k, đồ Apple" | Tool trả danh sách rỗng | Agent đề xuất nới lỏng **một** điều kiện |
| 2 | **Lỗi API/Timeout** | Search API bị sập hoặc hết quota | Tool ném Exception/Error | Try/catch bắt lỗi → trả chuỗi lỗi an toàn → Agent dùng kiến thức chung |
| 3 | **Kết quả không liên quan** | Tìm "chuột máy tính" → trả về bài về "loài chuột đồng" | Agent gợi ý quà sai lệch | Thêm bước rank/verify kết quả sau khi search |
| 4 | **Đường link hỏng/Hết hàng** | Link trả về bị 404 hoặc sản phẩm đã hết | Người dùng click vào không mua được | Agent cảnh báo kiểm tra tình trạng thực tế khi gợi ý |

---

## 📍 Mốc 2: Soạn Chatbot Baseline Prompt

### Nhiệm vụ
Soạn `CHATBOT_BASELINE_PROMPT` trong file `src/prompts.py` — prompt cho Chatbot Cấp 2 (chỉ LLM, không có Tool).

### Công việc đã thực hiện
Viết prompt định nghĩa nhân vật **Mèo Hồng** ở chế độ Chatbot Baseline với các quy tắc:

```python
CHATBOT_BASELINE_PROMPT = """Bạn là Mèo Hồng — trợ lý tư vấn quà tặng thân thiện (Chatbot Baseline, KHÔNG có Tool).

NHIỆM VỤ:
Đưa ra 3-5 ý tưởng quà tặng chung chung dựa trên thông tin người dùng cung cấp trong cuộc trò chuyện.

GIỚI HẠN — BẮT BUỘC TUÂN THỦ:
1. Bạn KHÔNG có khả năng tra cứu catalog, giá cả, tồn kho hay đường link mua hàng thực tế.
2. Tuyệt đối KHÔNG tự bịa ra đường link, tên cửa hàng, mức giá cụ thể hay trạng thái còn hàng.
3. Luôn nêu rõ cho người dùng rằng đây chỉ là ý tưởng gợi ý chung, chưa được kiểm chứng thực tế.
4. Nếu người dùng hỏi ngoài phạm vi tư vấn quà (ví dụ: y tế, tài chính, pháp luật), lịch sự từ chối.

PHONG CÁCH:
- Trả lời bằng tiếng Việt, thân thiện, ngắn gọn.
- Không biến cuộc trò chuyện thành bảng khảo sát; chỉ trả lời một lần rồi chờ phản hồi.
"""
```

### Giải thích thiết kế
- **Nêu rõ giới hạn "KHÔNG có Tool"**: Đảm bảo LLM không ảo giác bịa ra link/giá/tồn kho, vì ở Cấp 2 chatbot chỉ có kiến thức tĩnh.
- **Giới hạn 3-5 ý tưởng**: Đúng yêu cầu project context — đưa gợi ý chung chung, không tra cứu thực tế.
- **Quy tắc từ chối ngoài phạm vi**: Bảo vệ chatbot khỏi bị lạc đề sang y tế, pháp luật, tài chính.
- **Phong cách thân thiện tiếng Việt**: Phù hợp ngữ cảnh dự án hướng đến người dùng Việt Nam.

---

## 📍 Mốc 3: Soạn ReAct System Prompt & Guardrails

### Nhiệm vụ
- Soạn `REACT_SYSTEM_PROMPT` ép AI sinh `Thought → Action → Observation`.
- Đặt `MAX_ITERATIONS` (giới hạn số lần lặp) trong `src/prompts.py`.

### Công việc đã thực hiện

#### 3.1. REACT_SYSTEM_PROMPT

Viết prompt hệ thống cho ReAct Agent (Cấp 3) với các phần chính:

**a) Danh sách Tools:**
Liệt kê 5 tools với cú pháp gọi rõ ràng để LLM biết đúng tên và cách truyền tham số:
1. `extract_gift_profile[prompt]` — Trích xuất hồ sơ người nhận
2. `get_profile_completeness[profile]` — Kiểm tra đủ thông tin chưa
3. `search_gifts[profile]` — Lọc catalog quà theo hồ sơ
4. `rank_gifts[profile, gifts]` — Xếp hạng quà và tạo lý do
5. `search_gift_api[gift_description]` — Tra cứu cửa hàng/link (mock)

**b) Định dạng bắt buộc (ReAct Format):**
Ép LLM tuân theo đúng 2 mẫu output:
- **Khi cần gọi Tool:** `Thought: ... → Action: tên_tool[tham_số]` rồi **DỪNG NGAY** (chờ Observation từ hệ thống).
- **Khi trả lời người dùng:** `Thought: ... → Final Answer: ...`

**c) Điều kiện gọi Tool tìm quà:**
Agent CHỈ ĐƯỢC gọi `search_gifts` / `search_gift_api` khi hồ sơ đã đủ 4 yếu tố bắt buộc:
- ✅ Dịp lễ / mục đích tặng quà
- ✅ Đối tượng / mối quan hệ
- ✅ Ngân sách
- ✅ Ít nhất 1 sở thích hoặc điều cần tránh

Nếu thiếu → dùng `Final Answer` hỏi người dùng, mỗi lượt chỉ hỏi 1 câu ưu tiên nhất.

**d) Quy tắc an toàn (Guardrails trong prompt):**

| # | Quy tắc | Mục đích |
|---|---|---|
| 1 | Không suy diễn giới tính, thu nhập, sức khỏe, quan hệ khi chưa có dữ liệu | Tránh bias và giả định sai |
| 2 | Không bịa link, tên cửa hàng, giá ngoài kết quả Tool | Chống hallucination |
| 3 | Tool trả lỗi hoặc rỗng → thông báo lịch sự, đề xuất nới 1 điều kiện | Fallback an toàn |
| 4 | Tôn trọng điều cần tránh (dị ứng, kiêng kỵ) | An toàn cho người nhận quà |
| 5 | Người dùng đổi yêu cầu giữa chừng → cập nhật hồ sơ, không dùng dữ liệu cũ | State consistency |
| 6 | Hỏi ngoài phạm vi → từ chối lịch sự | Giữ agent đúng domain |
| 7 | Không yêu cầu/lưu PII (SĐT, địa chỉ, CCCD) | Bảo vệ quyền riêng tư |

**e) Phong cách hội thoại:**
- Tiếng Việt, thân thiện, tự nhiên.
- Không lặp lại thông tin đã có.
- Thought/Action/Observation là trace nội bộ; người dùng chỉ thấy Final Answer.

#### 3.2. Guardrails Configuration

```python
MAX_ITERATIONS = 5       # Tối đa 5 vòng Thought-Action trước khi buộc dừng
TIMEOUT_SECONDS = 15     # Timeout (giây) cho mỗi lần gọi tool
```

- **`MAX_ITERATIONS = 5`**: Giới hạn số vòng lặp ReAct. Nếu sau 5 lượt mà hồ sơ vẫn chưa đủ → agent buộc dừng và đưa fallback message. Giá trị 5 được chọn vì: hồ sơ có 4 trường bắt buộc (relationship, occasion, interests, budget_max), nên 5 vòng là đủ để thu thập kể cả trường hợp xấu nhất + 1 lượt dự phòng.
- **`TIMEOUT_SECONDS = 15`**: Nếu tool không phản hồi trong 15 giây → hủy và chuyển sang fallback.

#### 3.3. Fallback Messages

```python
FALLBACK_MESSAGE = (
    "Mình đã hỏi khá nhiều rồi nhưng vẫn chưa đủ thông tin để tìm quà thật chuẩn. "
    "Bạn có thể cho mình biết thêm một thông tin quan trọng nhất (sở thích hoặc ngân sách) "
    "để mình gợi ý tốt hơn không?"
)

TOOL_ERROR_FALLBACK = (
    "Hệ thống tìm kiếm đang gặp sự cố tạm thời. "
    "Mình sẽ đưa ra một số gợi ý chung dựa trên thông tin bạn đã cung cấp nhé!"
)
```

- **`FALLBACK_MESSAGE`**: Khi đạt `MAX_ITERATIONS` → tin nhắn này được gửi thay vì tiếp tục hỏi, tránh vòng lặp vô hạn.
- **`TOOL_ERROR_FALLBACK`**: Khi tool bị lỗi (API sập, timeout) → thông báo lịch sự và chuyển sang gợi ý chung (fallback về Chatbot baseline).

#### 3.4. Follow-up Questions

```python
FOLLOW_UP_QUESTIONS = {
    "relationship": "Người nhận là ai với bạn (bạn thân, người yêu, đồng nghiệp…) để mình chọn quà có độ thân mật phù hợp?",
    "occasion": "Bạn muốn tặng nhân dịp gì nhỉ (sinh nhật, kỷ niệm, tốt nghiệp…)?",
    "interests": "Người ấy thường thích làm gì, hoặc có món nào nên tránh không?",
    "budget_max": "Ngân sách bạn dự kiến khoảng bao nhiêu để mình lọc quà hợp lý nhé?",
    "age_range": "Người nhận khoảng bao nhiêu tuổi để mình gợi ý đúng phong cách hơn?",
}
```

Dictionary này cung cấp câu hỏi follow-up tự nhiên cho từng trường còn thiếu trong hồ sơ, giúp agent hỏi đúng trọng tâm mà không biến cuộc hội thoại thành bảng khảo sát.

---

## 📊 Tổng kết đóng góp

| Mốc | Deliverable | Trạng thái |
|------|---|---|
| Mốc 1 | Phân tích Failure Modes cho 2 tools chính (8 failure modes) | ✅ Hoàn thành |
| Mốc 2 | Soạn `CHATBOT_BASELINE_PROMPT` trong `src/prompts.py` | ✅ Hoàn thành |
| Mốc 3 | Soạn `REACT_SYSTEM_PROMPT` + `MAX_ITERATIONS` + Guardrails + Fallback Messages + Follow-up Questions trong `src/prompts.py` | ✅ Hoàn thành |
