# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

**Đề tài được chọn:** Đề tài 9 — *Trợ lý Sàng lọc Hồ sơ Tuyển dụng & Hẹn Phỏng vấn*.

**Phạm vi bài toán:** Agent tiếp nhận hồ sơ ứng viên, đối chiếu với yêu cầu tuyển dụng, đánh giá mức độ phù hợp, đề xuất danh sách ứng viên cần phỏng vấn và phối hợp lịch rảnh để tạo lịch hẹn. Quyết định tuyển dụng cuối cùng vẫn thuộc về con người.

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Cần trích xuất thông tin từ CV, đối chiếu từng tiêu chí của mô tả công việc, nhận diện điểm thiếu hoặc mâu thuẫn, tổng hợp điểm phù hợp và giải thích lý do đề xuất. |
| 🛠️ **Tool Interaction** | `5/5` | Cần dùng nhiều công cụ như đọc CV/JD, tra cứu dữ liệu ứng viên, kiểm tra lịch rảnh của nhà tuyển dụng và gửi hoặc tạo lời mời phỏng vấn. |
| 🔀 **Dynamic Decision** | `5/5` | Đường xử lý thay đổi theo dữ liệu thực tế: hồ sơ thiếu thông tin thì yêu cầu bổ sung; không đạt ngưỡng thì dừng; đạt ngưỡng thì kiểm tra lịch và đề xuất khung giờ. |
| ⏳ **Long Horizon** | `4/5` | Quy trình trải qua nhiều giai đoạn từ tiếp nhận hồ sơ, sàng lọc, xếp hạng, xin phê duyệt đến hẹn phỏng vấn; tuy nhiên chưa phải tác vụ tự chủ kéo dài nhiều ngày nếu chỉ giới hạn trong một đợt xử lý. |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN CÓ AGENTIC FIT RẤT CAO VÀ PHÙ HỢP VỚI REACT AGENT, NHƯNG CẦN HUMAN-IN-THE-LOOP CHO QUYẾT ĐỊNH TUYỂN DỤNG VÀ HÀNH ĐỘNG GỬI LỊCH.** |

### Kết luận Mốc 1

Chatbot thông thường có thể giải thích yêu cầu công việc hoặc góp ý một CV riêng lẻ, nhưng không phù hợp để điều phối toàn bộ quy trình vì không thể chủ động gọi công cụ và phản ứng theo kết quả từng bước. ReAct Agent phù hợp hơn nhờ khả năng quan sát dữ liệu, lựa chọn hành động tiếp theo và lưu lại trace để người phụ trách tuyển dụng kiểm tra.

Các ràng buộc cần áp dụng ở những mốc sau:

- Không sử dụng các thuộc tính nhạy cảm như giới tính, tuổi, dân tộc, tôn giáo hoặc tình trạng hôn nhân để chấm điểm ứng viên.
- Mỗi đánh giá phải dẫn chiếu tiêu chí chuyên môn trong mô tả công việc và bằng chứng tương ứng từ hồ sơ.
- Không tự động loại ứng viên hoặc gửi lịch phỏng vấn nếu chưa có bước xác nhận của người phụ trách tuyển dụng.
- Dữ liệu hồ sơ và thông tin liên hệ phải được giới hạn quyền truy cập và không xuất hiện trong trace công khai.

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Thời tiết ở Hà Nội hôm nay thế nào và tôi nên mặc gì đi chơi?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Tôi không có truy cập Internet thời gian thực nên không biết thời tiết hôm nay ở Hà Nội."*
* **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế của người dùng.

### 🧠 ReAct Agent:
* **Thought 1**: Cần tra cứu thời tiết Hà Nội.
* **Action 1**: `get_weather['Hà Nội']`
* **Observation 1**: `Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%.`
* **Thought 2**: Đã có thông tin 28°C nắng nhẹ, đưa ra lời khuyên trang phục.
* **Final Answer**: *"Thời tiết Hà Nội hôm nay 28°C, nắng nhẹ. Bạn nên mặc quần áo thoáng mát!"*
* **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ sự kết hợp giữa suy luận và công cụ.
