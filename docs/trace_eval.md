# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)


| Tiêu chí | Điểm (1–5) | Lý do đánh giá |
|---|:---:|---|
| 🧠 **Multi-step Reasoning** | **4/5** | Hệ thống phải phân tích nhiều thông tin đầu vào như trình độ hiện tại, mục tiêu học tập, thời gian có thể học mỗi tuần, ngân sách, kỹ năng đã có và các khóa đã hoàn thành. Sau đó, hệ thống mới có thể tìm và đề xuất khóa học phù hợp. |
| 🛠️ **Tool Interaction** | **4/5** | Agent cần gọi các công cụ như `search_courses` để tìm khóa học, `get_course_details` để lấy thông tin chi tiết và `check_prerequisites` để kiểm tra điều kiện tiên quyết. Nếu chỉ sử dụng kiến thức của LLM, hệ thống có thể đưa ra thông tin không đúng với course catalog. |
| 🔀 **Dynamic Decision** | **4/5** | Kết quả tư vấn thay đổi tùy theo hồ sơ của từng sinh viên. Kết quả từ bước tìm kiếm sẽ quyết định Agent cần kiểm tra khóa học nào, điều kiện nào và có cần đề xuất khóa học nền tảng trước hay không. |
| ⏳ **Long Horizon** | **3/5** | Quy trình thường gồm khoảng 2–4 bước: phân tích hồ sơ, tìm khóa học, kiểm tra chi tiết, kiểm tra điều kiện và đưa ra tư vấn. Quy trình không quá dài nhưng cần duy trì thông tin qua nhiều bước. |
| **TỔNG ĐIỂM FIT** | **15/20** | **KẾT LUẬN: BÀI TOÁN RẤT PHÙ HỢP ĐỂ SỬ DỤNG REACT AGENT.** |

### Kết luận đánh giá

Bài toán tư vấn khóa học không nên chỉ sử dụng Chatbot Baseline vì câu trả lời cần dựa trên dữ liệu cụ thể trong course catalog. ReAct Agent phù hợp hơn vì có thể suy luận từ hồ sơ sinh viên, gọi các công cụ tra cứu, kiểm tra điều kiện tiên quyết và đưa ra đề xuất có căn cứ.



---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Mình chưa biết gì, muốn học nền tảng, thời gian rảnh ít, ngân sách thấp?"*
### ⚙️ System Prompt: Bạn là Chatbot baseline tư vấn khóa học và lộ trình học Python/AI cho sinh viên.

### 🤖 Chatbot Baseline:

* **Phản hồi**: *"Hướng học đề xuất là Python nền tảng. Bạn đang ở trình độ beginner, muốn học kiến thức nền tảng, có ít thời gian rảnh và ngân sách thấp nên hướng học Python cơ bản sẽ phù hợp. Bạn nên học cú pháp, biến, kiểu dữ liệu, điều kiện, vòng lặp, hàm cơ bản và thực hiện một project nhỏ."*
**Giới hạn**: *“Chưa thể xác nhận khóa học, thời lượng, số giờ học, ngân sách và project cụ thể vì Chatbot Baseline không trugiy cập course catalog.”*

* **Nhận xét**: *" Chatbot đưa ra định hướng học hợp lý và an toàn nhưng chỉ tư vấn dựa trên kiến thức chung. Chatbot chưa tra cứu được khóa học thực tế và chưa kiểm tra chính xác các ràng buộc của người dùng."*

### 🧠 ReAct Agent:

**Thought 1:** Cần tìm khóa học dành cho người mới bắt đầu, có mục tiêu học nền tảng, thời gian học thấp và ngân sách thấp.
**Action 1:**  `search_courses[foundation, beginner, low, low, ""]`
**Observation 1:** `Tìm thấy PY101 – Python nhập môn. Khóa học yêu cầu 4 giờ/tuần, có mức ngân sách low, mức thực hành high và có project.`

**Thought 2:** PY101 phù hợp với các ràng buộc chính. Cần xem thông tin chi tiết để xác minh điều kiện tiên quyết, nội dung và project.
**Action 2:**  `get_course_details[PY101]`
**Observation 2:**  `PY101 không yêu cầu khóa tiên quyết hoặc kỹ năng đầu vào. Khóa học kéo dài 6 tuần, học 4 giờ/tuần và có project chương trình quản lý danh sách sinh viên.`

**Thought 3:** Đã có đủ thông tin để đưa ra đề xuất phù hợp cho sinh viên.

- **Final Answer:**  
  *“Khóa học phù hợp nhất với bạn là PY101 – Python nhập môn. Khóa học dành cho người chưa có kiến thức Python, không yêu cầu điều kiện tiên quyết, chỉ cần khoảng 4 giờ học mỗi tuần và thuộc mức ngân sách thấp. Bạn sẽ được học biến và kiểu dữ liệu, câu lệnh điều kiện, vòng lặp, list, dictionary và hàm cơ bản. Cuối khóa, bạn sẽ thực hiện project chương trình quản lý danh sách sinh viên.”*

- **Nhận xét:**  
  Agent hoàn thành tốt nhiệm vụ nhờ kết hợp suy luận với công cụ. Đề xuất được xác minh từ course catalog, phù hợp với trình độ, mục tiêu, thời gian và ngân sách của người dùng.