# Báo cáo giám sát và đánh giá — Đề tài 10

## 1. Agentic Fit Scoring Matrix

| Tiêu chí | Điểm | Lý do |
|---|---:|---|
| Multi-step Reasoning | 5/5 | Agent có thể tìm nhà, đọc chi tiết, kiểm tra lịch, đặt lịch và gửi xác nhận. |
| Tool Interaction | 5/5 | Hệ thống có 5 tool với dữ liệu nhà, lịch chủ nhà và trạng thái đặt lịch. |
| Dynamic Decision | 5/5 | Observation quyết định có đặt lịch, hỏi thêm thông tin hay đề xuất khung giờ khác. |
| Long Horizon | 4/5 | Full-flow có thể đi qua 4–5 action liên tiếp; vẫn là quy trình ngắn, có giới hạn. |
| **Tổng** | **19/20** | **Rất phù hợp để dùng ReAct Agent.** |

## 2. Contract và tiêu chí đánh giá

- `search_rentals`: không gọi nếu thiếu vị trí; kiểm tra đúng giá, loại phòng và tiện ích.
- `get_rental_detail`: chỉ trả chi tiết của `rental_id` tồn tại.
- `check_landlord_calendar`: luôn gọi trước khi đặt lịch.
- `book_viewing_appointment`: chỉ gọi khi có căn hợp lệ, slot hợp lệ, tên và số điện thoại.
- `send_confirmation_notification`: chỉ gọi sau khi booking thành công.

Các chỉ số chính:

| Chỉ số | Cách kiểm tra |
|---|---|
| Tool Call Accuracy | Agent chọn đúng tool theo ý định người dùng. |
| Parameter Extraction Precision | Vị trí, giá, mã căn, ngày giờ và thông tin liên hệ đúng. |
| Slot Filling Efficiency | Agent hỏi lại khi thiếu vị trí, ngân sách hoặc thông tin đặt lịch. |
| Graceful Fallback / Guardrail | Không crash, không bịa dữ liệu, dừng an toàn khi tool lỗi hoặc yêu cầu ngoài phạm vi. |

## 3. Trace mẫu — Full-flow tìm và đặt lịch

**Input:** Tìm căn hộ 1PN ở Bình Thạnh dưới 8 triệu, có ban công; đặt lịch thứ Bảy 10:00. Tên Nam, SĐT 0901234567.

```text
Step 1
Thought: Cần tìm căn 1PN tại Bình Thạnh, giá tối đa 8 triệu và có ban công.
Action: search_rentals['Bình Thạnh', 0, 8000000, '1PN', ['ban công']]
Observation: CH-5501, 7.900.000 VNĐ, căn hộ 1PN có ban công.

Step 2
Thought: Đã có căn phù hợp, cần kiểm tra lịch thứ Bảy trước khi đặt.
Action: check_landlord_calendar['CH-5501', 'thứ bảy']
Observation: available=True, slots=['10:00', '14:00']

Step 3
Thought: Slot 10:00 còn trống và đã đủ thông tin khách hàng.
Action: book_viewing_appointment['CH-5501', 'Nam', '0901234567', 'thứ bảy 10:00']
Observation: booking_id=BK001, status=Confirmed

Step 4
Thought: Booking đã thành công, có thể gửi xác nhận.
Action: send_confirmation_notification['0901234567', booking_details]
Observation: SMS xác nhận đã được gửi.

Final Answer: Đã đặt lịch xem căn CH-5501 vào thứ Bảy lúc 10:00 và gửi SMS xác nhận.
```

## 4. So sánh Chatbot Baseline và ReAct Agent

| Test case | Chatbot baseline | ReAct Agent | Kết luận |
|---|---|---|---|
| Tư vấn giấy tờ/chi phí | Trả lời trực tiếp | Trả lời trực tiếp | Chatbot đủ dùng, không cần tool. |
| Tìm phòng theo tiêu chí | Không có dữ liệu thực tế | Gọi `search_rentals` | Agent có grounding từ tool. |
| Xem chi tiết căn | Có thể bịa thông tin | Gọi `get_rental_detail` | Agent trả dữ liệu có căn cứ. |
| Đặt lịch xem nhà | Không thể xác nhận lịch | Kiểm tra lịch rồi đặt | Agent thực hiện được workflow. |
| Dữ liệu sai/ngoài phạm vi | Có thể trả lời chung chung | Từ chối hoặc yêu cầu nhập lại | Guardrail an toàn hơn. |

## 5. Checklist kiểm thử Role 4–5

- [ ] Chạy `python src/app.py` không cần API key.
- [ ] Baseline không gọi tool.
- [ ] Agent chỉ gọi tool trong `AVAILABLE_TOOLS`.
- [ ] Có Observation sau mỗi Action.
- [ ] Không đặt lịch trước khi kiểm tra calendar.
- [ ] Tool lỗi được chuyển thành thông báo thân thiện.
- [ ] Agent dừng sau `MAX_ITERATIONS`.
- [ ] Trace có đủ Thought/Action/Observation/Final Answer.
