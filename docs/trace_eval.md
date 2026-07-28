# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí                       |  Điểm (1-5)  | Lý do đánh giá                                                                                                                                                                                                                 |
| :------------------------------- | :-------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧠**Multi-step Reasoning** |     `5/5`     | Cupid Agent phải phân tích nhiều lớp: profile người dùng, sở thích, tính cách, mục tiêu hẹn hò, điểm chung, điểm khác biệt và rủi ro không phù hợp.                                                     |
| 🛠️**Tool Interaction**   |     `4/5`     | Cần dùng tool để truy xuất profile đã lưu, tìm ứng viên phù hợp, tính điểm tương thích và lọc các tiêu chí quan trọng. Một phần tư vấn vẫn có thể do LLM xử lý nên chưa cần 5/5.              |
| 🔀**Dynamic Decision**     |     `5/5`     | Kết quả từng bước quyết định hành động tiếp theo: nếu thiếu profile thì hỏi thêm, nếu có nhiều ứng viên thì xếp hạng, nếu phát hiện deal-breaker thì cảnh báo hoặc loại khỏi danh sách.         |
| ⏳**Long Horizon**         |     `4/5`     | Quy trình gồm nhiều bước liên tiếp từ đọc profile, lọc ứng viên, chấm điểm, giải thích lý do và gợi ý cách bắt chuyện. Tuy nhiên chưa phải nhiệm vụ theo dõi dài ngày nên không chấm tối đa. |
| **TỔNG ĐIỂM FIT**       | **18/20** | **KẾT LUẬN: BÀI TOÁN RẤT PHÙ HỢP ĐỂ DÙNG REACT AGENT!**                                                                                                                                                            |

---

## 🔍 2. KẾT QUẢ CHATBOT BASELINE - MỐC 2

**Môi trường chạy**: `MockProvider` offline

**Giao thức**: Mỗi test case gọi LLM đúng 1 lần và không gọi tool.

| Test | Phân loại | LLM calls | Tool calls | Nhận xét |
| :---: | :--- | :---: | :---: | :--- |
| #1 | `correct` | 1 | 0 | Trả lời được câu hỏi tư vấn chung bằng kiến thức sẵn có. |
| #2 | `correct` | 1 | 0 | Nêu được các yếu tố cơ bản của một mối quan hệ nghiêm túc. |
| #3 | `safe fallback` | 1 | 0 | Không bịa người phù hợp nhất khi không truy cập được hồ sơ. |
| #4 | `safe fallback` | 1 | 0 | Không tự tạo điểm số khi không có công cụ tính tương thích. |
| #5 | `safe fallback` | 1 | 0 | Không bịa ứng viên không tồn tại trong dữ liệu. |

### Raw answers

**Test case #1**

> Bạn có thể: (1) chào hỏi và giới thiệu ngắn gọn, (2) hỏi một câu mở dựa trên hoàn cảnh chung, (3) lắng nghe và phản hồi chân thành. Hãy giữ thái độ tự nhiên và tôn trọng ranh giới của đối phương.

**Test case #2**

> Một mối quan hệ nghiêm túc thường cần sự tôn trọng, giao tiếp trung thực, tin cậy, đồng thuận về kỳ vọng và khả năng cùng giải quyết bất đồng.

**Test case #3**

> Tôi chưa thể đưa ra kết luận vì chatbot thông thường không có quyền truy cập hồ sơ đã lưu hoặc công cụ tính độ tương thích. Bạn có thể cung cấp thông tin của từng người để tôi nhận xét sơ bộ.

**Test case #4**

> Tôi chưa thể đưa ra kết luận vì chatbot thông thường không có quyền truy cập hồ sơ đã lưu hoặc công cụ tính độ tương thích. Bạn có thể cung cấp thông tin của từng người để tôi nhận xét sơ bộ.

**Test case #5**

> Tôi không thể kiểm tra danh sách ứng viên vì không có quyền truy cập cơ sở dữ liệu. Tôi sẽ không tự tạo hồ sơ không có căn cứ.

**Tổng kết**: `5 test cases | LLM calls = 5 | Tool calls = 0`. Chatbot
Baseline xử lý tốt câu hỏi kiến thức chung và từ chối an toàn khi câu hỏi cần dữ
liệu hệ thống. Đây là giới hạn mà ReAct Agent sẽ giải quyết ở Mốc 3.

---

## 🧪 3. TRACE REACT CHO MỐC 3

**Môi trường chạy**: `MockProvider` offline

**Cấu hình**: `MAX_ITERATIONS=6`, timeout mỗi tool `10 giây`

### Test case #3 - Multi-step thành công

**Question**: *"Tìm cho tôi 3 người phù hợp nhất để hẹn hò với tôi, dựa trên hồ
sơ và sở thích của tôi."*

1. **Thought**: Cần lấy hồ sơ hiện tại trước khi tìm người phù hợp.
   **Action**: `get_user_profile["current_user"]`
   **Observation**: Minh, 21 tuổi, hướng nội; thích đọc sách, cà phê yên tĩnh,
   công nghệ; mục tiêu là mối quan hệ nghiêm túc.

2. **Thought**: Cần lọc ứng viên cùng mục tiêu nghiêm túc.
   **Action**: `search_candidate_profiles["mối quan hệ nghiêm túc"]`
   **Observation**: Tìm thấy ba ứng viên Mai, Lan và Phương.

3. **Thought**: Cần tính và xếp hạng ba ứng viên vừa tìm thấy.
   **Action**:
   `calculate_compatibility["current_user", ["Mai", "Lan", "Phương"]]`
   **Observation**: Mai `98/100`, Phương `94/100`, Lan `88/100`.

4. **Thought**: Mai đứng đầu, cần tổng hợp khuyến nghị cuối.
   **Action**: `synthesize_recommendation["current_user", "Mai"]`
   **Observation**: Gói tổng hợp xác nhận Mai `98/100`, cùng mục tiêu nghiêm túc
   và cùng thích đọc sách; điểm số chỉ mang tính tham khảo.

5. **Thought**: Đã có đủ Observation để trả lời có căn cứ.
   **Final Answer**: *"Ba ứng viên phù hợp nhất là Mai 98/100, Phương 94/100
   và Lan 88/100. Mai đứng đầu vì cùng mục tiêu nghiêm túc và cùng thích đọc
   sách với Minh. Điểm cần lưu ý là dữ liệu chỉ hỗ trợ tham khảo. Gợi ý mở đầu:
   'Chào Mai, gần đây bạn đọc cuốn sách nào khiến bạn ấn tượng nhất?'"*

**Telemetry**: `LLM calls = 5 | Tool calls = 4 | Status = completed`

### Test case #5 - Không có dữ liệu

1. **Thought**: Cần tìm ứng viên theo đầy đủ tiêu chí đã nêu.
   **Action**:
   `search_candidate_profiles["bạn nam chơi piano, biết nấu ăn và đan len"]`
   **Observation**: Không tìm thấy ứng viên phù hợp.

2. **Thought**: Không có ứng viên nên phải dừng an toàn, không bịa hồ sơ.
   **Final Answer**: *"Hiện không tìm thấy ứng viên nào đáp ứng đầy đủ các tiêu
   chí. Bạn có thể mở rộng hoặc ưu tiên lại một vài tiêu chí."*

**Telemetry**: `LLM calls = 2 | Tool calls = 1 | Status = completed`

### Kết quả toàn bộ test cases

| Test | Hành vi | LLM calls | Tool calls | Kết quả |
| :---: | :--- | :---: | :---: | :--- |
| #1 | Tư vấn chung, trả lời trực tiếp | 1 | 0 | Pass |
| #2 | Kiến thức quan hệ, trả lời trực tiếp | 1 | 0 | Pass |
| #3 | Bốn tool, lọc và xếp hạng | 5 | 4 | Pass |
| #4 | So sánh Phương và Lan | 4 | 3 | Pass |
| #5 | Không có ứng viên, dừng an toàn | 2 | 1 | Pass |
| #6 | Từ chối câu hỏi lập trình ngoài phạm vi | 1 | 0 | Pass |
| #7 | Từ chối câu hỏi thời tiết ngoài phạm vi | 1 | 0 | Pass |
| #8 | Yêu cầu bổ sung tên hoặc MSSV | 1 | 0 | Pass |
| **Tổng** | **8/8 pass** | **16** | **8** | **Không crash** |

---

## 🛡️ 4. FAILED TRACE VÀ AGENT V2

### Failure mode: Repeated Action

**Failed response mô phỏng**:

```text
Thought: Tôi thử lấy lại cùng hồ sơ.
Action: get_user_profile["current_user"]
Observation: Profile người dùng Minh...

Thought: Tôi thử lấy lại cùng hồ sơ.
Action: get_user_profile["current_user"]
```

**Root cause**: Nếu ứng dụng không lưu lịch sử Action, LLM có thể gọi lại cùng
tool và tham số, gây lãng phí hoặc lặp vô hạn.

**Agent V2 recovery**:

```text
Observation: LỖI GUARDRAIL: Action này đã được gọi với cùng tham số.
GUARDRAIL TRIGGERED: Phát hiện Action lặp lại với cùng tham số.
Safe Fallback: Xin lỗi, tôi chưa thể hoàn thành yêu cầu một cách có căn cứ.
```

Tool chỉ thực thi ở lần đầu. Lần lặp bị chặn với telemetry:
`LLM calls = 2 | Tool calls = 1 | Status = guardrail`.

### Kiểm tra safeguards

| Failure mode | Cơ chế xử lý | Kết quả |
| :--- | :--- | :--- |
| Malformed Action | Parser trả `LỖI PARSER`, Observation quay lại LLM để sửa cú pháp | Recovered |
| Unknown Tool | Executor trả danh sách tool hợp lệ, LLM gọi lại đúng tên | Recovered |
| Wrong Arguments | Kiểm tra chữ ký hàm trước khi thực thi | Safe error |
| Repeated Action | Lưu canonical action key và chặn lần gọi trùng | Guardrail |
| Endless malformed output | Ngắt tại `MAX_ITERATIONS` và trả Safe Fallback | Guardrail |
| Premature Final Answer | Từ chối kết luận dữ liệu khi chưa có Observation | Recovered |
| Tool exception/timeout | Chuyển exception hoặc timeout thành Observation | Không crash |

Kết quả regression test: `26 tests passed`.
