# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

_Dành cho Role 5: Observability & Reviewer — Đề tài: **Cupid Agent: Trợ Lý Ghép Đôi & Phân Tích Độ Tương Thích**_

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Cần suy luận, phân tích hồ sơ, lọc ứng viên và đánh giá độ tương thích theo nhiều bước. |
| 🛠️ **Tool Interaction** | `5/5` | Cần sử dụng nhiều Tool: lấy hồ sơ người dùng, tìm Top 3 ứng viên phù hợp, tính toán độ tương thích và tạo lời mở đầu dựa trên điểm chung. |
| 🔀 **Dynamic Decision** | `5/5` | Kết quả bước trước quyết định hành động bước sau. |
| ⏳ **Long Horizon** | `4/5` | Quy trình xử lý gồm nhiều bước liên tiếp (lấy hồ sơ → lọc ứng viên → tính điểm → phân tích kết quả → tạo lời mở đầu) trước khi tạo Final Answer. |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!** |

---

## 2. KẾT QUẢ ĐÁNH GIÁ MỐC 2

### 2.1. Mục tiêu đánh giá

Quan sát phản hồi của Chatbot Baseline khi được cung cấp dữ liệu hồ sơ mô phỏng; kiểm tra khả năng bám sát dữ liệu, nguy cơ ảo giác, quyền riêng tư và những hạn chế so với ReAct Agent.

### 2.2. Cấu hình kiểm thử

| Hạng mục | Giá trị |
| :--- | :--- |
| Provider | OpenAI |
| Model | `gpt-4o-mini` |
| Dữ liệu | 12 hồ sơ mô phỏng trong `cupid_data/cupid_profiles.json` |
| Test case | Test case số 3 |
| Tool calls | Không sử dụng — đúng thiết kế Chatbot Baseline |

### 2.3. Đầu vào kiểm thử

> Tôi là người dùng U001. Hãy tìm 3 hồ sơ phù hợp nhất với tôi.

### 2.4. Kết quả quan sát

Chatbot đọc dữ liệu mock được đưa trực tiếp vào context và đề xuất ba hồ sơ theo thứ tự:

1. **U002 — Bình**
2. **U003 — Cường**
3. **U004 — Dũng**

Chatbot giải thích kết quả dựa trên các thông tin có trong dữ liệu mock như sở thích, giá trị sống, mục tiêu mối quan hệ, địa điểm và thói quen. Chatbot cũng nêu rõ kết quả chỉ mang tính tham khảo, không phải kết luận khoa học.

### 2.5. Bảng đánh giá

| Tiêu chí | Kết quả | Nhận xét |
| :--- | :---: | :--- |
| Sử dụng đúng mock data | **Đạt** | Không tạo thêm ID hoặc hồ sơ ngoài dữ liệu được cung cấp. |
| Top 3 ứng viên | **Đạt** | Trả đúng U002, U003, U004 và đúng thứ tự mong đợi. |
| Mức độ bám sát dữ liệu | **Đạt** | Các lý do chính đều xuất phát từ trường dữ liệu của hồ sơ. |
| Ảo giác | **Không phát hiện nghiêm trọng** | Không bịa ứng viên hoặc thuộc tính quan trọng không tồn tại. Tuy nhiên, cách diễn giải vẫn do LLM tạo ra. |
| Quyền riêng tư | **Đạt** | Không đưa ra số điện thoại, email, địa chỉ chính xác hoặc tọa độ. |
| Sử dụng tool | **Không sử dụng** | Đúng với baseline nhưng không tạo được trace `Action → Observation`. |
| Điểm tương thích | **Chưa đạt** | Không tính và kiểm chứng deterministic các điểm kỳ vọng 90.0, 75.0 và 69.0. |
| Khả năng lặp lại | **Chưa bảo đảm** | Cách diễn đạt và kết quả suy luận có thể thay đổi giữa các lần gọi LLM. |

### 2.6. Hạn chế của Chatbot Baseline

- Toàn bộ mock data phải được đưa vào context, làm tăng kích thước prompt.
- Chatbot không tự gọi tool để lấy đúng dữ liệu cần thiết.
- Không có trace để biết Agent đã thực hiện hành động nào.
- Không bảo đảm công thức tính điểm và thứ tự xếp hạng luôn chính xác.
- Khó xử lý ổn định các lỗi như ID không tồn tại hoặc hồ sơ không có ứng viên phù hợp.

### 2.7. Kết luận Mốc 2

Chatbot Baseline đã sử dụng đúng dữ liệu mock và tìm đúng ba ứng viên U002, U003, U004. Tuy nhiên, baseline chưa bảo đảm tính điểm deterministic, không có tool trace và kết quả vẫn phụ thuộc vào suy luận của LLM. Đây là cơ sở để chuyển sang ReAct Agent ở Mốc 3, nơi các thao tác lọc và tính điểm phải được thực hiện bằng tool.

---

## 3. KẾT QUẢ GIÁM SÁT REACT AGENT — MỐC 3

### 3.1. Mục tiêu đánh giá

Kiểm tra ReAct Agent có lựa chọn đúng tool, truyền đúng JSON input, sử dụng Observation thật để quyết định bước tiếp theo, dừng đúng lúc và xử lý lỗi mà không bịa dữ liệu hay không.

> **Lưu ý về trace:** Báo cáo chỉ ghi tóm tắt quyết định ở mức cao cùng `Action`, `Action Input` và `Observation`; không lưu chain-of-thought nội bộ chi tiết của mô hình.

### 3.2. Cấu hình kiểm thử

| Hạng mục | Giá trị |
| :--- | :--- |
| Provider | OpenAI |
| Model | `gpt-4o-mini` |
| System prompt | `REACT_SYSTEM_PROMPT` |
| Tool registry | `AVAILABLE_TOOLS` |
| Giới hạn vòng lặp | `MAX_ITERATIONS = 8` |
| Dữ liệu | `cupid_data/cupid_profiles.json` |

### 3.3. Happy trace — Test case số 4

**Đầu vào:**

> Tôi là người dùng U001. Hãy tìm người phù hợp nhất, phân tích độ tương thích và gợi ý lời mở đầu.

#### Bước 1 — Tìm ứng viên

- **Thought/Tóm tắt quyết định:** Yêu cầu cần dữ liệu hồ sơ và xếp hạng ứng viên, vì vậy phải gọi tool thay vì tự suy đoán.
- **Action:** `find_candidate_matches`
- **Action Input:**

```json
{"user_id": "U001", "limit": 3}
```

- **Observation:** Tool trả về ba ứng viên hợp lệ theo thứ tự:

| Hạng | Candidate | Tên | Điểm | Lý do nổi bật |
| :---: | :---: | :--- | ---: | :--- |
| 1 | U002 | Bình | 90.0 | Cùng giá trị, sở thích và mục tiêu quan hệ |
| 2 | U003 | Cường | 75.0 | Cùng giá trị, sở thích và mục tiêu quan hệ |
| 3 | U004 | Dũng | 69.0 | Cùng giá trị, sở thích và mục tiêu quan hệ |

#### Bước 2 — Phân tích ứng viên đứng đầu

- **Thought/Tóm tắt quyết định:** U002 đứng đầu Observation trước, nên Agent dùng đúng ID này để phân tích chi tiết.
- **Action:** `calculate_compatibility`
- **Action Input:**

```json
{"user_id": "U001", "candidate_id": "U002"}
```

- **Observation:**

```json
{
  "eligible": true,
  "total_score": 90.0,
  "breakdown": {
    "relationship_goal": 100.0,
    "values": 100.0,
    "interests": 50.0,
    "location": 100.0
  },
  "shared_interests": ["du lịch", "nhiếp ảnh"],
  "shared_values": ["gia đình", "phát triển bản thân", "trung thực"]
}
```

#### Bước 3 — Tạo lời mở đầu

- **Thought/Tóm tắt quyết định:** Người dùng yêu cầu gợi ý lời mở đầu, nên Agent tiếp tục dùng U001 và U002 từ Observation đã xác minh.
- **Action:** `suggest_first_message`
- **Action Input:**

```json
{"user_id": "U001", "candidate_id": "U002"}
```

- **Observation:**

```json
{
  "message": "Chào Bình, mình thấy chúng ta đều thích du lịch. Bạn thích điều gì nhất ở sở thích này?",
  "based_on": {"type": "interest", "value": "du lịch"}
}
```

#### Final Answer quan sát được

> Chào Bình, mình thấy chúng ta đều thích du lịch. Bạn thích điều gì nhất ở sở thích này?

### 3.4. Đánh giá Test case số 4

| Tiêu chí | Điểm | Nhận xét |
| :--- | :---: | :--- |
| Factual correctness | **1/2** | Tool cho kết quả đúng, nhưng Final Answer mới chỉ hiển thị lời mở đầu, chưa tổng hợp rõ điểm 90.0 và phân tích chi tiết. |
| Grounding | **2/2** | Candidate ID, điểm số và lời mở đầu đều lấy từ Observation. |
| Tool selection | **2/2** | Gọi đúng thứ tự `find_candidate_matches` → `calculate_compatibility` → `suggest_first_message`. |
| Termination | **2/2** | Dừng đúng sau ba lần gọi tool và một Final Answer. |
| **Tổng** | **7/8** | Luồng ReAct đạt; cần cải thiện nội dung Final Answer để tổng hợp đầy đủ kết quả. |

### 3.5. Failed trace — Test case số 5

**Đầu vào:**

> Tôi là người dùng U999. Hãy tìm người phù hợp nhất với tôi.

**Kỳ vọng:**

```text
Action: find_candidate_matches
Action Input: {"user_id": "U999", "limit": 3}
Observation: PROFILE_NOT_FOUND
Final Answer: thông báo lịch sự
```

**Thực tế:** Agent trả `Final Answer` trực tiếp rằng U999 không hợp lệ, không gọi tool để xác minh.

| Tiêu chí | Kết quả | Nhận xét |
| :--- | :---: | :--- |
| An toàn | **Đạt** | Không bịa hồ sơ, không crash và không lặp vô hạn. |
| Tool selection | **Chưa đạt** | Không gọi `find_candidate_matches` như expected behavior. |
| Grounding | **Chưa đạt** | Không có Observation `PROFILE_NOT_FOUND`. |
| Termination | **Đạt** | Dừng ngay bằng câu trả lời lịch sự. |

**Root cause:** Prompt chưa buộc model phải dùng tool để xác minh mọi `user_id`; model tự suy luận U999 không tồn tại từ mẫu ID hoặc ngữ cảnh.

**Đề xuất sửa:** Bổ sung guardrail: khi yêu cầu liên quan đến hồ sơ hoặc `user_id`, Agent không được tự kết luận ID hợp lệ hay không hợp lệ mà phải gọi tool thích hợp để xác minh.

### 3.6. Kết luận Mốc 3

ReAct Agent đã hoàn thành đúng luồng ba tool của Test 4, sử dụng dữ liệu deterministic và tạo trace `Action → Action Input → Observation → Final Answer`. Agent cũng dừng an toàn ở edge case. Tuy nhiên, Test 5 chưa tuân thủ tool path và Final Answer của Test 4 chưa tổng hợp đầy đủ điểm tương thích. Hai vấn đề này cần được khắc phục trước khi đánh dấu toàn bộ Mốc 3 hoàn thành tuyệt đối.

### 3.7. Checklist Role 5 — Mốc 3

- [x] Trích xuất trace ReAct hoàn chỉnh của Test 4.
- [x] Ghi lại Action, JSON Action Input và Observation thật.
- [x] Đối chiếu thứ tự tool với expected behavior.
- [x] Chấm điểm theo rubric correctness, grounding, tool selection và termination.
- [x] Ghi failed trace của Test 5 và phân tích root cause.
- [x] Đề xuất biện pháp cải thiện guardrail.

