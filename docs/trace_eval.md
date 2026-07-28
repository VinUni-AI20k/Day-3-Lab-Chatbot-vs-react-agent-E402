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

