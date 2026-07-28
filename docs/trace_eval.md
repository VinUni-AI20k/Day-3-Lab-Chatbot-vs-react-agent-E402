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

Chưa nghiệm thu. Phần này sẽ được bổ sung bằng output thực tế sau khi hoàn thiện
ReAct loop, parser và guardrail ở Mốc 3.
