# Phân tích các trường hợp lỗi (Failure Modes) của Tools - Role 3 (Mốc 1)

Trong dự án Trợ lý chọn quà tặng, để đảm bảo tính ổn định và khả năng tự phục hồi (resilience) của ReAct Agent, chúng ta cần xác định trước các trường hợp lỗi (failure modes) của các tools được sử dụng. Dưới đây là phân tích cho 2 tools chính mà nhóm dự định sử dụng:

## 1. Tool Xác định thông tin đối tượng (Profile Extraction/Completeness Tool)
**Chức năng:** Trích xuất các thông tin như đối tượng, sở thích, dịp lễ, độ tuổi, ngân sách từ tin nhắn của người dùng để cập nhật hồ sơ người nhận quà.

### Các trường hợp lỗi (Failure Modes) có thể xảy ra:
1. **Thông tin mâu thuẫn (Conflicting Information):**
   - *Ví dụ:* Người dùng nói "tặng bạn gái nhân dịp kỷ niệm, không có tiền đâu, ngân sách 0 đồng" hoặc "thích đồ công nghệ nhưng lại muốn quà cổ điển truyền thống".
   - *Hậu quả:* Tool không thể xác định giá trị hợp lệ, logic để lưu vào state.
   - *Giải pháp/Fallback:* Agent cần nhận diện sự mâu thuẫn này và hỏi lại một cách lịch sự để người dùng làm rõ trước khi lưu.

2. **Dữ liệu quá mơ hồ (Ambiguous Input):**
   - *Ví dụ:* Người dùng nhập "tìm quà cho nó", "gì cũng được", "rẻ rẻ thôi".
   - *Hậu quả:* Tool không thể map vào các danh mục cụ thể (không biết ai là "nó", "rẻ" là mức ngân sách bao nhiêu).
   - *Giải pháp/Fallback:* Tool trả về trạng thái "thiếu thông tin/mơ hồ" và yêu cầu Agent đặt câu hỏi làm rõ (VD: "Để mình gợi ý chuẩn hơn, ngân sách 'rẻ' của bạn nằm trong khoảng dưới 500k hay dưới 200k?").

3. **Lỗi trích xuất sai trường (Misclassification/Hallucination):**
   - *Ví dụ:* Người dùng nói "tặng sách cho bạn", tool lại nhầm "sách" thành "dịp tặng" thay vì "sở thích/loại quà".
   - *Hậu quả:* Truy vấn tìm quà sau đó sẽ bị sai lệch hoàn toàn.
   - *Giải pháp/Fallback:* Cần có schema (ví dụ dùng Pydantic/JSON Schema) rõ ràng để ràng buộc kiểu dữ liệu đầu ra.

4. **Vượt quá số lần hỏi (Looping/Max Iterations):**
   - *Trường hợp:* Người dùng liên tục nói những câu không liên quan, agent kẹt trong vòng lặp liên tục hỏi thông tin còn thiếu.
   - *Giải pháp/Fallback:* Áp dụng Guardrail giới hạn `MAX_ITERATIONS`. Khi đạt ngưỡng, tự động ngắt chuỗi thu thập thông tin và chuyển sang đưa ra các gợi ý chung chung (fallback về Chatbot baseline).

---

## 2. Tool Web Search (Tìm kiếm quà tặng trả ra đường link)
**Chức năng:** Dựa trên hồ sơ người nhận đã thu thập đủ, tìm kiếm các sản phẩm/món quà phù hợp trên internet (hoặc catalog) và trả về danh sách kèm đường link.

### Các trường hợp lỗi (Failure Modes) có thể xảy ra:
1. **Không tìm thấy kết quả (No Results Found / Over-constrained):**
   - *Ví dụ:* Điều kiện lọc quá khắt khe: "Quà sinh nhật cho sếp, ngân sách dưới 50k, thích đồ công nghệ Apple".
   - *Hậu quả:* Tool trả về danh sách rỗng.
   - *Giải pháp/Fallback:* Agent phải phản hồi lịch sự rằng không tìm thấy sản phẩm khớp toàn bộ tiêu chí, và chủ động đề xuất nới lỏng **một** điều kiện (VD: đề xuất tăng ngân sách hoặc bỏ yêu cầu đồ Apple).

2. **Lỗi API / Timeout (Service Unavailable):**
   - *Trường hợp:* Công cụ search (Google Search API, Tavily, v.v.) bị sập, hết quota yêu cầu, hoặc phản hồi quá chậm (timeout).
   - *Hậu quả:* Tool ném ra Exception/Error.
   - *Giải pháp/Fallback:* Tool phải bắt (try/catch) lỗi này và trả về chuỗi thông báo lỗi an toàn (ví dụ: `{"error": "search service unavailable"}`). Agent đọc lỗi này và phản hồi người dùng: "Hệ thống tìm kiếm hiện đang gián đoạn, nhưng với kinh nghiệm của mình, bạn có thể tham khảo..." (Dùng kiến thức chung hoặc catalog fallback mặc định).

3. **Kết quả trả về không liên quan (Irrelevant Results):**
   - *Ví dụ:* Tìm "chuột máy tính" nhưng kết quả từ web search lại trả về bài báo về "loài chuột đồng".
   - *Hậu quả:* Agent gợi ý quà sai lệch hoàn toàn, gây trải nghiệm tệ cho người dùng.
   - *Giải pháp/Fallback:* Thêm bước kiểm tra/chấm điểm (Rank/Verify) sau khi search. Nếu các kết quả trả về không thuộc danh mục quà tặng hoặc không hợp lý, agent tự động thay đổi từ khóa (re-query) hoặc báo cáo lỗi.

4. **Đường link hỏng (Dead Links) hoặc Hết hàng (Out of Stock):**
   - *Trường hợp:* Web search trả về kết quả tốt nhưng khi người dùng click vào thì báo lỗi 404 (do bài viết/sản phẩm đã bị xóa) hoặc trang web báo sản phẩm đã hết hàng.
   - *Giải pháp/Fallback:* Trong thông điệp cuối cùng, agent nên chèn lưu ý cảnh báo (VD: "Bạn hãy kiểm tra tình trạng còn hàng và giá thực tế trên trang web nhé").

### Tổng kết
Việc xác định trước các **Failure Modes** này giúp định hướng cho phần Prompt Engineering (viết hướng dẫn xử lý lỗi) và Core Developer (thiết lập cơ chế try/catch, Guardrails) nhằm đảm bảo Agent không bị crash hay bị "ảo giác" trong quá trình tư vấn.
