# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

# Bảng chấm điểm Agentic Fit cho đề: Trợ lý đặt vé xem phim

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Yêu cầu tổng hợp nhiều bước: tìm suất chiếu → kiểm tra ghế trống → chọn ghế -> xác nhận đặt vé. |
| 🛠️ **Tool Interaction** | `5/5` | Cần gọi API rạp, tra lịch chiếu, trạng thái ghế, giá vé thời gian thực, không có trong LLM. |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả tool bước trước (VD: hết suất 19h) quyết định hành động bước sau (gợi ý suất khác). |
| ⏳ **Long Horizon** | `4/5` | Quy trình 3 bước tool + 1 bước xác nhận hành động, dài hơn use-case mẫu |
| **TỔNG ĐIỂM FIT** | **18/20** | **KẾT LUẬN: RẤT PHÙ HỢP — NÊN DÙNG REACT AGENT VỚI TOOLING CHUẨN (BOOKING, PAYMENT, INVENTORY)** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Phim Obsession tối nay chiếu lúc mấy giờ ở CGV?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Xin lỗi, mình không thể kiểm tra suất chiếu cụ thể của phim "Obsession" tại rạp CGV vào tối nay. Bạn nên truy cập trang web hoặc ứng dụng của CGV để xem lịch chiếu chi tiết nhé!"*
* **Nhận xét**: An toàn, không bịa giờ chiếu và đã hướng dẫn người dùng kiểm tra qua kênh chính thức của CGV. Tuy nhiên, Chatbot Baseline không có dữ liệu thời gian thực nên chưa giải quyết được nhu cầu tra cứu suất chiếu cụ thể.
