# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer — Nguyễn Thiên Tài*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

**Đề tài: Trợ Lý Nắm Bắt Tính Cách & Chọn Quà Tặng Phù Hợp**

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Chuỗi suy luận dài: tra tính cách → tra quy tắc dịp lễ → loại trừ kiêng kỵ → tìm quà → kiểm tra tồn kho → chia ngân sách. Tối thiểu 3–5 bước nối tiếp, bước sau phụ thuộc kết quả bước trước. |
| 🛠️ **Tool Interaction** | `5/5` | 6 tools chuyên biệt: `get_personality_profile`, `search_gift_catalog`, `check_gift_availability`, `suggest_gift_by_personality`, `tra_cuu_quy_tac_dip`, `tinh_ngan_sach_gop`. Agent phải chọn đúng tool và đúng thứ tự. |
| 🔀 **Dynamic Decision** | `5/5` | Kết quả tính cách quyết định danh mục quà. Dịp lễ + văn hóa thay đổi danh sách kiêng kỵ. Tồn kho hết hàng buộc Agent tìm sản phẩm thay thế. Mỗi tổ hợp (người + dịp + ngân sách) → kết quả hoàn toàn khác nhau. |
| ⏳ **Long Horizon** | `4/5` | Quy trình 4–5 bước xử lý (tra tính cách → tra quy tắc → tìm quà → kiểm tồn kho → chia ngân sách). Đủ phức tạp để thể hiện giá trị của Agent so với Chatbot. |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN CỰC KỲ PHÙ HỢP DÙNG REACT AGENT!** 6 tools tạo thành pipeline hoàn chỉnh từ phân tích → gợi ý → xác nhận → tính tiền. Chatbot thuần không thể làm được. |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Tôi muốn tặng quà sinh nhật cho Minh Anh, ngân sách 400 ngàn. Bạn gợi ý gì?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *(Chờ kết quả chạy thực tế — Role 5 sẽ điền sau Phase 2)*
* **Nhận xét**: Dự kiến Chatbot gợi ý chung chung vì không biết Minh Anh là ai, tính cách gì, thích gì.

### 🧠 ReAct Agent:
* **Thought 1**: Cần tra cứu tính cách Minh Anh trước.
* **Action 1**: `get_personality_profile[minh_anh]`
* **Observation 1**: Minh Anh — Người Sáng Tạo, thích vẽ tranh, nhiếp ảnh, handmade, thời trang vintage. Không thích đồ công nghệ phức tạp.
* **Thought 2**: Minh Anh là người sáng tạo, tìm quà nghệ thuật/handmade trong ngân sách 400k.
* **Action 2**: `search_gift_catalog[vẽ tranh, nhiếp ảnh, handmade, 400000]`
* **Observation 2**: Bộ bút vẽ 48 màu (350k), Sổ tay da vintage (280k), Túi tote canvas (180k)...
* **Thought 3**: Đã có danh sách phù hợp, kiểm tra tồn kho sản phẩm top 1.
* **Action 3**: `check_gift_availability[GIFT_001]`
* **Observation 3**: Còn 15 sản phẩm, không có khuyến mãi.
* **Final Answer**: Gợi ý tặng Minh Anh **Bộ bút vẽ chuyên nghiệp 48 màu** (350,000 VNĐ) — phù hợp tính cách Sáng Tạo, sở thích vẽ tranh, nằm trong ngân sách 400k, còn hàng.
* **Nhận xét**: Agent cá nhân hóa hoàn toàn dựa trên dữ liệu tính cách thực, Chatbot không thể làm được.

---

## 📋 3. BẢNG KẾT QUẢ 5 TEST CASES

| Test # | Category | Chatbot Baseline | ReAct Agent | Tools đã gọi | Nhận xét |
|:---:|:---|:---|:---|:---|:---|
| 1 | 🟢 Đơn giản | *(Chờ điền)* | *(Chờ điền)* | Không cần tool | |
| 2 | 🟢 Đơn giản | *(Chờ điền)* | *(Chờ điền)* | Không cần tool | |
| 3 | 🟡 Multi-step (1-2 Tools) | *(Chờ điền)* | *(Chờ điền)* | `get_personality_profile` → `search_gift_catalog` / `suggest_gift_by_personality` → `check_gift_availability` | |
| 4 | 🟡 Multi-step (3+ Tools) | *(Chờ điền)* | *(Chờ điền)* | `get_personality_profile` → `tra_cuu_quy_tac_dip` → `search_gift_catalog` → `check_gift_availability` → `tinh_ngan_sach_gop` | |
| 5 | 🔴 Edge Case | *(Chờ điền)* | *(Chờ điền)* | Tất cả tools đều báo LỖI → Guardrail ngắt | |

---

## 🔄 4. FAILED TRACE ANALYSIS (Agent V2)

*(Sẽ bổ sung sau khi chạy Edge Case #5 và phát hiện lỗi)*

| Dạng lỗi | Biểu hiện | Root Cause | Cách Agent V2 khắc phục |
|:---|:---|:---|:---|
| Unknown Person | `get_personality_profile('Người Vô Hình')` → LỖI không tìm thấy | Tên không có trong database | Tool trả về danh sách người có sẵn, Agent thông báo lịch sự |
| Invalid Occasion | `tra_cuu_quy_tac_dip('Halloween')` → LỖI không có dữ liệu | Dịp lễ chưa được hỗ trợ | Tool liệt kê các dịp có sẵn, Agent chuyển hướng |
| Negative Budget | `search_gift_catalog('du lịch', -500)` → LỖI ngân sách âm | Tham số không hợp lệ | Tool validate và báo rõ lỗi, Agent yêu cầu nhập lại |
| Invalid Product ID | `check_gift_availability('GIFT_999')` → LỖI mã không tồn tại | Mã sản phẩm không có trong inventory | Tool liệt kê mã hợp lệ, Agent chọn mã khác |
| Out of Stock | `check_gift_availability('GIFT_006')` → HẾT HÀNG | Sản phẩm hết hàng | Agent gọi lại `search_gift_catalog` tìm sản phẩm thay thế |

---

## 📊 5. RUBRIC ĐÁNH GIÁ CHI TIẾT (0–2 điểm mỗi case)

| Tiêu chí | 0 điểm | 1 điểm | 2 điểm |
|:---|:---|:---|:---|
| **Factual correctness** | Sai / Bịa đặt sản phẩm | Đúng một phần (đúng tên nhưng sai giá) | Đúng hoàn toàn theo Observation từ tool |
| **Grounding** | Không có bằng chứng | Có Observation nhưng không trích dẫn | Trích dẫn rõ ràng từ Observation |
| **Tool selection** | Gọi sai tool / Không gọi | Gọi đúng nhưng thiếu bước | Gọi đúng thứ tự, đúng tham số |
| **Termination** | Lặp vô hạn / Crash | Dừng nhưng thừa bước | Dừng đúng lúc (Final Answer / Guardrail) |
