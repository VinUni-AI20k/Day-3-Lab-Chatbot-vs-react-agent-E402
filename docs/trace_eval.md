# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Cần suy luận từ hội thoại khai thác tính cách/sở thích đến ánh xạ sang nhóm quà tặng phù hợp. |
| 🛠️ **Tool Interaction** | `4/5` | Cần tra cứu dữ liệu sản phẩm qua API sàn TMĐT, so sánh giá và lọc theo tiêu chí. |
| 🔀 **Dynamic Decision** | `4/5` | Phản hồi của người dùng ở bước trước quyết định hướng tìm kiếm/tinh chỉnh gợi ý ở bước sau. |
| ⏳ **Long Horizon** | `4/5` | Quy trình gồm nhiều lượt: khai thác thông tin, tìm kiếm, tinh chỉnh theo phản hồi, chốt gợi ý. |
| **TỔNG ĐIỂM FIT** | **16/20** | **KẾT LUẬN: BÀI TOÁN NÊN DÙNG REACT AGENT!** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #4)

**Câu hỏi**: *"Sếp nữ của tôi thích làm vườn, sinh nhật tuần sau, ngân sách khoảng 500k. Gợi ý giúp tôi món quà cụ thể và đang bán ở đâu?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Chào bạn, tôi hiểu sếp nữ của bạn thích làm vườn và bạn muốn tìm quà sinh nhật trong ngân sách 500k. Tuy nhiên tôi không có khả năng tra cứu sản phẩm hoặc giá bán thực tế đang có trên thị trường. Tôi có thể gợi ý một số **nhóm quà tham khảo** phù hợp với sở thích làm vườn, ví dụ: bộ dụng cụ làm vườn mini, chậu cây để bàn, hoặc găng tay làm vườn cao cấp — mức giá chỉ mang tính ước tính. Bạn nên kiểm tra thực tế về tình trạng còn hàng, giá và đánh giá sản phẩm trước khi mua."*
* **Nhận xét**: An toàn, tuân thủ đúng giới hạn (không bịa giá/tồn kho), nhưng chỉ dừng ở gợi ý chung chung, không giải quyết được nhu cầu thực tế của người dùng là tìm sản phẩm cụ thể đang bán ở đâu.

### 🧠 ReAct Agent:
* **Thought 1**: Cần trích xuất hồ sơ người nhận từ mô tả người dùng.
* **Action 1**: `extract_recipient_profile["sếp nữ, thích làm vườn, dịp sinh nhật, ngân sách 500k"]`
* **Observation 1**: `{"relationship": "sếp", "gender": "nữ", "interest": "làm vườn", "occasion": "sinh nhật", "budget": 500000}`
* **Thought 2**: Có hồ sơ rồi, cần phân tích để rút ra insight chọn quà.
* **Action 2**: `analyze_recipient_profile[hồ_sơ_JSON]`
* **Observation 2**: `Insight: ưu tiên nhóm quà "làm vườn tại nhà", phong cách tinh tế phù hợp môi trường công sở.`
* **Thought 3**: Đã có insight, tìm các sản phẩm cụ thể phù hợp và trong ngân sách.
* **Action 3**: `generate_gift_candidates[insight, budget=500000]`
* **Observation 3**: `[{"name": "Bộ dụng cụ làm vườn mini cao cấp", "price": 450000, "shop": "Shop A", "rank": 1}, {"name": "Chậu cây gốm để bàn kèm hạt giống", "price": 320000, "shop": "Shop B", "rank": 2}]`
* **Thought 4**: Đã có danh sách xếp hạng, cần giải thích lý do phù hợp cho từng lựa chọn.
* **Action 4**: `explain_recommendations[danh_sách_candidates]`
* **Observation 4**: `Giải thích chi tiết lý do phù hợp cho từng món quà.`
* **Final Answer**: *"Mình gợi ý 2 lựa chọn phù hợp với ngân sách 500k: (1) Bộ dụng cụ làm vườn mini cao cấp – 450.000đ tại Shop A, phù hợp vì tinh tế và đúng sở thích làm vườn; (2) Chậu cây gốm để bàn kèm hạt giống – 320.000đ tại Shop B, phù hợp không gian bàn làm việc. Bạn nên kiểm tra tồn kho và đánh giá sản phẩm trước khi đặt mua nhé."*
* **Nhận xét**: Hoàn thành nhiệm vụ nhờ chuỗi 4 bước (extract → analyze → generate → explain), có tra cứu sản phẩm và ngân sách cụ thể — vượt xa giới hạn của baseline, nhưng lưu ý đây là pipeline tuyến tính cố định, chưa có nhánh rẽ động (xem lại điểm Dynamic Decision ở Scoring Matrix).
