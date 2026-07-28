# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

_Dành cho Role 5: Observability & Reviewer_

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí                   | Điểm (1-5) | Lý do đánh giá                                                                                                                                                                                                                             |
| :------------------------- | :--------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧠**Multi-step Reasoning** |   `4/5`    | Yêu cầu suy luận qua nhiều bước: Nhận diện mã đơn**$\rightarrow$** Kiểm tra trạng thái **$\rightarrow$** Đối chiếu chính sách đổi trả **$\rightarrow$** Tổng hợp câu trả lời phù hợp với ngữ cảnh hiện tại của đơn hàng.                   |
| 🛠️**Tool Interaction**     |   `5/5`    | Cần tương tác với nhiều hệ thống bên ngoài: 1. API của Đơn vị vận chuyển (GHTK, VNPost...). 2. Truy vấn Database (ví dụ: MySQL) để kiểm tra lịch sử mua hàng. 3. Hệ thống CRM để tạo phiếu khiếu nại/đổi trả.                              |
| 🔀**Dynamic Decision**     |   `5/5`    | Tính rẽ nhánh logic rất cao. Hành động tiếp theo phụ thuộc hoàn toàn vào kết quả của bước trước. Ví dụ: Nếu truy vấn DB thấy đơn*chưa giao* , Agent phải từ chối yêu cầu đổi trả và chuyển hướng sang giải thích lộ trình giao hàng        |
| ⏳**Long Horizon**         |   `4/5`    | Quá trình xử lý đổi trả là một hội thoại kéo dài nhiều lượt (Multi-turn conversation). Agent phải lưu trữ ngữ cảnh (Memory): Nhớ mã đơn hàng từ câu chào, nhớ lý do đổi trả khách vừa nhập, chờ khách tải ảnh lên rồi mới chốt tạo ticket. |
| **TỔNG ĐIỂM FIT**          | **18/20**  | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!**                                                                                                                                                                                           |

---

## 🔍 2. SO SÁNH PHẢN HỒI BASELINE CHATBOT VS REACT AGENT (TOÀN BỘ 5 TEST CASES)

**Chủ đề bài toán**: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả

---

### 📌 Test Case #1: 🟢 Đơn giản (Chỉ cần LLM - Q&A Lý thuyết 1)
**Câu hỏi**: *"Chính sách đổi trả hàng của shop thường kéo dài bao nhiêu ngày là hợp lý?"*

🤖 **Chatbot Baseline**:
- **Phản hồi**: *"Chính sách đổi trả hàng kéo dài bao nhiêu ngày tùy thuộc vào ngành hàng và quy định riêng của shop. Thông thường 7 đến 14 ngày là thời gian phổ biến và hợp lý..."*
- **Nhận xét**: Trả lời thỏa đáng từ kiến thức tổng quát của LLM mà không cần truy vấn công cụ nào.

🧠 **ReAct Agent**:
- **Thought 1**: Đây là câu hỏi tư vấn chính sách chung, không cần tra cứu dữ liệu đơn hàng cụ thể.
- **Final Answer**: *"Chính sách đổi trả thông thường kéo dài từ 7 đến 14 ngày tùy thuộc vào quy định riêng của từng cửa hàng..."*
- **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ, nhận diện đúng không cần dùng Tool (0 tool calls), tiết kiệm thời gian và chi phí.

---

### 📌 Test Case #2: 🟢 Đơn giản (Chỉ cần LLM - Q&A Lý thuyết 2)
**Câu hỏi**: *"Nêu 3 lưu ý khi đóng gói hàng để trả lại cho shop."*

🤖 **Chatbot Baseline**:
- **Phản hồi**: *"1. Sử dụng bao bì gốc của sản phẩm. 2. Bao bọc kỹ lưỡng không để sản phẩm xê dịch. 3. Đính kèm đầy đủ phụ kiện và quà tặng kèm."*
- **Nhận xét**: Trả lời chính xác, đầy đủ dựa trên tri thức sẵn có của LLM.

🧠 **ReAct Agent**:
- **Thought 1**: Câu hỏi hỏi về hướng dẫn đóng gói tổng quát, không cần gọi tool tra cứu.
- **Final Answer**: *"1. Sử dụng bao bì gốc... 2. Bao bọc kỹ lưỡng... 3. Đính kèm đầy đủ phụ kiện..."*
- **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ mà không gọi thừa tool (0 tool calls).

---

### 📌 Test Case #3: 🟡 Multi-step (Cần 1 Tool)
**Câu hỏi**: *"Đơn hàng #DH10234 của tôi đang ở trạng thái nào và bao giờ thì tới nơi?"*

🤖 **Chatbot Baseline**:
- **Phản hồi**: *"Xin lỗi, tôi không thể tra cứu trạng thái đơn hàng cho bạn vì không có quyền truy cập vào hệ thống nội bộ. Bạn vui lòng liên hệ chăm sóc khách hàng..."*
- **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế của người dùng.

🧠 **ReAct Agent**:
- **Thought 1**: Tôi cần tra cứu trạng thái đơn hàng #DH10234 để biết thông tin chi tiết về quá trình vận chuyển.
- **Action 1**: `get_order_status['DH10234']`
- **Observation 1**: `THÔNG TIN TRẠNG THÁI ĐƠN HÀNG [DH10234]: Đã giao hàng thành công 3 ngày trước.`
- **Thought 2**: Đơn hàng đã giao thành công 3 ngày trước, không cần theo dõi thêm.
- **Final Answer**: *"Đơn hàng #DH10234 của bạn đã được giao hàng thành công cách đây 3 ngày. Nếu bạn có nhu cầu đổi trả, đơn hàng vẫn đang trong thời hạn hỗ trợ đổi trả (dưới 7 ngày)."*
- **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ sự kết hợp giữa suy luận và công cụ.

---

### 📌 Test Case #4: 🟡 Multi-step (Cần gọi 2 Tools)
**Câu hỏi**: *"Kiểm tra đơn hàng #DH10234 đã giao chưa, và nếu giao rồi thì tôi có còn đủ điều kiện đổi trả không?"*

🤖 **Chatbot Baseline**:
- **Phản hồi**: *"Xin lỗi, tôi không có quyền truy cập vào hệ thống để kiểm tra trạng thái đơn hàng của bạn. Tuy nhiên thông thường bạn có thể đổi trả sản phẩm trong vòng 7-30 ngày..."*
- **Nhận xét**: Trả lời chung chung theo lý thuyết, không thể tự động đối chiếu ngày giao của đơn hàng `#DH10234`.

🧠 **ReAct Agent**:
- **Thought 1**: Trước tiên, tôi cần tra cứu trạng thái giao hàng của đơn hàng #DH10234.
- **Action 1**: `get_order_status['DH10234']`
- **Observation 1**: `Đã giao hàng thành công 3 ngày trước. Ngành hàng: Thiết bị điện tử.`
- **Thought 2**: Đơn hàng đã giao được 3 ngày thuộc ngành Thiết bị điện tử. Cần kiểm tra điều kiện đổi trả cho sản phẩm Thiết bị điện tử mua 3 ngày trước.
- **Action 2**: `check_return_policy['Thiết bị điện tử', 3]`
- **Observation 2**: `ĐỦ ĐIỀU KIỆN: Ngành 'Thiết bị điện tử' cho phép đổi trả trong 7 ngày. Đơn hàng (3 ngày) ĐỦ ĐIỀU KIỆN.`
- **Thought 3**: Đơn hàng #DH10234 đã giao và đủ điều kiện đổi trả. Tôi đã có đủ thông tin.
- **Final Answer**: *"Đơn hàng #DH10234 đã được giao thành công, và bạn vẫn đủ điều kiện để thực hiện việc đổi trả, vì đơn hàng này thuộc ngành Thiết bị điện tử và mới được nhận 3 ngày trước."*
- **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ sự kết hợp giữa suy luận đa bước và gọi chuỗi công cụ (Tool Chaining).

---

### 📌 Test Case #5: 🔴 Edge Case (Bẫy Guardrail)
**Câu hỏi**: *"Tra cứu đơn hàng #DH99999999999 được đặt ngày 32/13/2026, tôi muốn đổi trả ngay."*

🤖 **Chatbot Baseline**:
- **Phản hồi**: *"Xin lỗi, hiện tại tôi không thể tra cứu đơn hàng do không có quyền truy cập hệ thống. Bạn vui lòng chuẩn bị thông tin mã đơn..."*
- **Nhận xét**: Không phát hiện ra lỗi ngày tháng không hợp lệ (32/13/2026), trả lời rập khuôn.

🧠 **ReAct Agent**:
- **Input Guardrail**: `🛡️ INPUT GUARDRAIL: Ngày '32/13/2026' không hợp lệ. Vui lòng cung cấp ngày theo định dạng DD/MM/YYYY và kiểm tra lại giá trị ngày/tháng.`
- **Final Answer**: *"Ngày bạn cung cấp ('32/13/2026') không hợp lệ trong thực tế. Vui lòng cung cấp ngày theo định dạng DD/MM/YYYY và kiểm tra lại giá trị ngày/tháng."*
- **Nhận xét**: Phanh Guardrail kích hoạt lập tức ngăn chặn xử lý lỗi và cảnh báo người dùng chính xác.
