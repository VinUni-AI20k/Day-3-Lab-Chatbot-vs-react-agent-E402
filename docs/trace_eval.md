# Báo cáo đánh giá — Trợ lý sàng lọc hồ sơ & hẹn phỏng vấn

> Dữ liệu ứng viên trong bài là dữ liệu mô phỏng đã ẩn danh. Agent chỉ hỗ trợ HR; không tự động ra quyết định tuyển dụng.

## 1. Agentic Fit

| Tiêu chí | Điểm | Lý do |
| --- | :---: | --- |
| Multi-step reasoning | 5/5 | Cần đọc hồ sơ, đối chiếu tiêu chí, tra lịch và có thể đặt lịch. |
| Tool interaction | 5/5 | Cần dữ liệu hồ sơ/lịch thực tế thay vì LLM tự suy đoán. |
| Dynamic decision | 5/5 | Chỉ tra lịch khi đánh giá PASS; chỉ đặt lịch khi có đồng ý. |
| Long horizon | 4/5 | Một quy trình ngắn nhưng có thay đổi trạng thái ở bước đặt lịch. |
| **Tổng** | **19/20** | **Rất phù hợp với ReAct Agent.** |

## 2. Trace thành công — Test #4

**Câu hỏi:** “UV001 đã đồng ý. Hãy sàng lọc cho vị trí Backend Developer và đặt lịch phỏng vấn.”

```text
Thought: Cần đọc hồ sơ ẩn danh trước khi đánh giá.
Action: get_candidate_profile["UV001"]
Observation: Hồ sơ UV001: vị trí Backend Developer; kỹ năng Python, SQL, FastAPI; kinh nghiệm 2 năm.

Thought: Cần đối chiếu hồ sơ với tiêu chí vị trí.
Action: evaluate_candidate["UV001", "Backend Developer"]
Observation: ĐÁNH GIÁ: PASS. UV001 đáp ứng kỹ năng và tối thiểu 1 năm kinh nghiệm. Cần HR xác nhận trước khi mời phỏng vấn.

Thought: Ứng viên đạt tiêu chí và đã đồng ý; cần xem lịch trống.
Action: get_interview_slots["Backend Developer"]
Observation: Lịch trống: SLOT01 - 09:00, 30/07/2026; SLOT02 - 14:00, 30/07/2026.

Thought: Chọn khung giờ trống đầu tiên theo yêu cầu.
Action: schedule_interview["UV001", "SLOT01"]
Observation: ĐÃ ĐẶT LỊCH (mô phỏng): UV001 vào 09:00, 30/07/2026 (Backend Developer).

Final Answer: Đã đặt lịch mô phỏng; HR cần gửi xác nhận chính thức cho ứng viên.
```

## 3. Failed trace & Agent V2 recovery — Test #5

**Failure mode:** Người dùng yêu cầu đặt lịch cho `UV999`, là mã không tồn tại.

| Mục | Phân tích |
| --- | --- |
| Root cause | Dữ liệu đầu vào không có hồ sơ ứng viên hợp lệ. |
| Observation | `LỖI: Không tìm thấy hồ sơ ứng viên 'UV999'.` |
| Recovery | Agent không suy đoán dữ liệu, không gọi `schedule_interview`, trả về yêu cầu HR kiểm tra mã. |
| Guardrail | Chặn Action trùng lặp và dừng sau tối đa 5 vòng lặp. |

## 4. So sánh baseline và agent

| Loại câu hỏi | Chatbot baseline | ReAct Agent |
| --- | --- | --- |
| Mẹo phỏng vấn/quy tắc công bằng | Phù hợp, nhanh, không cần tool | Có thể trả lời ngay. |
| Sàng lọc UV001 | Không thể xác minh hồ sơ | Có Observation từ hồ sơ và tiêu chí. |
| Đặt lịch | Không được khẳng định đã đặt | Thực hiện mô phỏng có kiểm tra PASS, sự đồng ý và slot. |
