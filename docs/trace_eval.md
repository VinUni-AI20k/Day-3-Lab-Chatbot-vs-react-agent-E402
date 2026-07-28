# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Role 5: Observability & Reviewer — Chủ đề: Trợ Lý Đặt Lịch Khám Bệnh & Tư Vấn Chuyên Khoa*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

> **Câu hỏi cốt lõi**: Bài toán này CẦN dùng Agent, hay Chatbot thuần là đủ?

| Tiêu chí | Điểm (1–5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Cần nhiều bước: phân tích triệu chứng → xác định chuyên khoa → tra lịch → đặt lịch. Mỗi bước phụ thuộc kết quả bước trước. |
| 🛠️ **Tool Interaction** | `5/5` | Bắt buộc gọi tool thực tế: `get_symptom_advice`, `check_doctor_schedule`, `book_appointment`. LLM thuần không thể bịa lịch bác sĩ có giá trị. |
| 🔀 **Dynamic Decision** | `5/5` | Triệu chứng khác nhau → chuyên khoa khác nhau. Lịch bác sĩ hôm nay vs ngày mai → quyết định khác nhau. Không có đường đi cố định. |
| ⏳ **Long Horizon** | `4/5` | Quy trình gồm 3–4 bước có điều kiện. Bonus Cấp 4 thêm multi-turn memory kéo dài hơn. |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!** Chatbot thuần sẽ buộc phải bịa lịch hẹn hoặc từ chối hoàn toàn. |

---

## 🔍 2. SO SÁNH PHẢN HỒI — TEST CASE #3 (Multi-step, 1 Tool)

**Câu hỏi**: *"Kiểm tra lịch của bác sĩ khoa Tim mạch vào ngày mai có chỗ trống không?"*

### 🤖 Chatbot Baseline (Cấp 2):

```
💬 [CHATBOT BASELINE]
🤖 Phản hồi: "Xin chào! Tôi là Chatbot tư vấn của VinHealth.
Rất tiếc, tôi không có khả năng tra cứu lịch bác sĩ thời gian thực.
Để biết lịch khám Tim mạch ngày mai, bạn vui lòng:
  - Gọi tổng đài 1800-xxxx
  - Hoặc đến trực tiếp quầy tiếp nhận."
```

| Tiêu chí | Đánh giá | Nhận xét |
|:---|:---:|:---|
| Factual correctness | ❌ 0/2 | Không có thông tin thực tế, chỉ từ chối |
| Grounding | ❌ 0/2 | Không có bằng chứng từ Tool |
| Tool selection | ❌ 0/2 | Tool calls = 0 |
| Termination | ✅ 2/2 | Dừng đúng, trả lời lịch sự |
| **Tổng** | **2/8** | **Safe fallback nhưng không hữu ích** |

### 🧠 ReAct Agent (Cấp 3):

```
🤖 [REACT AGENT] Câu hỏi: Kiểm tra lịch của bác sĩ khoa Tim mạch vào ngày mai có chỗ trống không?

--- 🔄 Bước 1/5 ---
📝 LLM output:
Thought: Người dùng muốn biết lịch bác sĩ Tim mạch ngày mai. Tôi cần gọi tool check_doctor_schedule.
Action: check_doctor_schedule["Tim mạch", "ngày mai"]

👁️ Observation:
📅 Lịch khám Tim mạch vào ngày mai:
  - BS. Trần Thị Mai (bs001): 08:00, 10:30, 14:00
  - BS. Nguyễn Hữu Phúc (bs002): 09:00, 15:30

--- 🔄 Bước 2/5 ---
📝 LLM output:
Thought: Tôi đã có đầy đủ thông tin lịch bác sĩ Tim mạch ngày mai.
Final Answer: Khoa Tim mạch ngày mai có 2 bác sĩ đang nhận lịch:
  • BS. Trần Thị Mai: còn slot lúc 08:00, 10:30, 14:00
  • BS. Nguyễn Hữu Phúc: còn slot lúc 09:00, 15:30
Bạn muốn đặt lịch với bác sĩ nào không?

✅ FINAL ANSWER TÌM THẤY sau 2 bước!
```

| Tiêu chí | Đánh giá | Nhận xét |
|:---|:---:|:---|
| Factual correctness | ✅ 2/2 | Thông tin lịch chính xác từ tool |
| Grounding | ✅ 2/2 | Trích dẫn Observation rõ ràng |
| Tool selection | ✅ 2/2 | Gọi đúng `check_doctor_schedule`, đúng thứ tự |
| Termination | ✅ 2/2 | Dừng sau 2 bước, đúng lúc |
| **Tổng** | **8/8** | **Hoàn thành xuất sắc nhờ Tool + Suy luận** |

---

## 🔍 3. TRACE LOG ĐẦY ĐỦ — TEST CASE #4 (Multi-step, 2 Tools)

**Câu hỏi**: *"Tôi bị đau đầu dữ dội kèm chóng mặt và buồn nôn từ sáng. Hãy tư vấn chuyên khoa và đặt lịch ngay hôm nay cho tôi tên Nguyễn Văn An."*

```
🤖 [REACT AGENT]

--- Bước 1/5 ---
Thought: Người dùng mô tả triệu chứng: đau đầu, chóng mặt, buồn nôn. Cần phân tích để xác định chuyên khoa.
Action: get_symptom_advice["đau đầu, chóng mặt, buồn nôn"]

Observation:
🔍 Phân tích triệu chứng: 'đau đầu, chóng mặt, buồn nôn'
→ Chuyên khoa gợi ý: **Thần kinh** (2/3 triệu chứng khớp: đau đầu, chóng mặt)
💡 Lý do: Đau đầu và chóng mặt thường liên quan đến hệ thần kinh.
📌 Cũng có thể liên quan: Nội tổng quát (1)

--- Bước 2/5 ---
Thought: Chuyên khoa gợi ý là Thần kinh. Giờ tôi cần tra lịch bác sĩ Thần kinh hôm nay để chọn slot.
Action: check_doctor_schedule["Thần kinh", "hôm nay"]

Observation:
📅 Lịch khám Thần kinh vào hôm nay:
  - BS. Lê Minh Khoa (bs003): 14:00, 15:00, 16:30

--- Bước 3/5 ---
Thought: BS. Lê Minh Khoa có slot 14:00 hôm nay. Đặt lịch cho bệnh nhân Nguyễn Văn An.
Action: book_appointment["Nguyễn Văn An", "Thần kinh", "hôm nay", "14:00"]

Observation:
✅ ĐẶT LỊCH THÀNH CÔNG!
📋 Mã lịch hẹn: APT-1000
👤 Bệnh nhân: Nguyễn Văn An
🏥 Chuyên khoa: Thần kinh
👨‍⚕️ Bác sĩ phụ trách: BS. Lê Minh Khoa
📅 Thời gian: hôm nay lúc 14:00
📌 Lưu ý: Vui lòng có mặt trước 15 phút và mang theo CCCD + thẻ BHYT.

--- Bước 4/5 ---
Thought: Tôi đã hoàn thành cả 2 bước: phân tích triệu chứng và đặt lịch thành công.
Final Answer: Dựa trên triệu chứng đau đầu, chóng mặt và buồn nôn, tôi gợi ý bạn khám
Khoa Thần kinh. Tôi đã đặt lịch thành công cho bạn:
  • Bác sĩ: BS. Lê Minh Khoa — Khoa Thần kinh
  • Thời gian: Hôm nay lúc 14:00
  • Mã lịch hẹn: APT-1000
Vui lòng có mặt trước 15 phút, mang theo CCCD và thẻ BHYT. Chúc bạn sức khoẻ!

✅ FINAL ANSWER sau 4 bước (3 Tool calls + 1 Tổng hợp)
```

---

## ⚠️ 4. FAILED TRACE ANALYSIS — TEST CASE #5 (Edge Case)

**Câu hỏi bẫy**: *"Đặt lịch khám ngày 32 tháng 13 năm 2026 với bác sĩ Siêu Nhân tại khoa Vũ Trụ cho bệnh nhân tên ABC."*

### Failed Trace (trước khi có Guardrail):

```
--- Bước 1 ---
Action: book_appointment["ABC", "Vũ Trụ", "32/13/2026", "08:00"]
Observation: LỖI: Ngày '32/13/2026' không hợp lệ...

--- Bước 2 ---
Action: check_doctor_schedule["Vũ Trụ", "ngày mai"]
Observation: LỖI: Không tìm thấy chuyên khoa 'Vũ Trụ'. Các chuyên khoa hợp lệ gồm: Tim mạch, Thần kinh...

--- Bước 3 ---
Action: book_appointment["ABC", "Vũ Trụ", "ngày mai", "08:00"]
Observation: LỖI: Không tìm thấy chuyên khoa 'Vũ Trụ'...

🛡️ GUARDRAIL EARLY STOP: 3 lỗi liên tiếp. Ngắt an toàn!
📢 Fallback: "Xin lỗi, tôi đã thử nhiều cách nhưng chưa thể hoàn thành..."
```

### Root Cause Analysis (RCA):

| Failure Mode | Nguyên nhân | Cách Agent V2 khắc phục |
|:---|:---|:---|
| **Invalid Date** | Ngày 32/13 không tồn tại | Tool bắt regex invalid date → trả chuỗi lỗi |
| **Unknown Specialty** | "Khoa Vũ Trụ" không có trong DB | Tool validate specialty → gợi ý danh sách hợp lệ |
| **Repeated Error** | Agent thử lại cùng loại tham số sai | Guardrail `consecutive_errors >= 3` → ngắt sớm |
| **No crash** | Exception lan ra ngoài | Mọi tool wrap `try/except` → trả string lỗi |

### Agent V2 Enhancement:
- ✅ Guardrail `consecutive_errors >= 3` → dừng sớm thay vì chờ MAX_ITERATIONS
- ✅ Tool validate tất cả inputs trước khi xử lý
- ✅ Final fallback message lịch sự, gợi ý cách liên hệ thay thế

---

## 📈 5. BẢNG TỔNG HỢP 5 TEST CASES

| # | Loại | Câu hỏi (tóm tắt) | Chatbot Score | Agent Score | Ghi chú |
|:---:|:---|:---|:---:|:---:|:---|
| 1 | 🟢 Đơn giản | Khoa Tim mạch khám bệnh gì? | 8/8 | 8/8 | Chatbot đủ dùng cho câu lý thuyết |
| 2 | 🟢 Đơn giản | Chuẩn bị gì trước khi khám? | 8/8 | 8/8 | Chatbot đủ dùng, không cần Agent |
| 3 | 🟡 1 Tool | Lịch bác sĩ Tim mạch ngày mai? | 2/8 | 8/8 | Agent vượt trội nhờ `check_doctor_schedule` |
| 4 | 🟡 2 Tools | Triệu chứng → đặt lịch cho Nguyễn Văn An | 0/8 | 8/8 | Agent cần thiết: 3 tool calls liên tiếp |
| 5 | 🔴 Edge | Ngày 32/13, khoa Vũ Trụ (câu bẫy) | 6/8 | 7/8 | Guardrail hoạt động, không crash |

> **Kết luận**: Với câu hỏi lý thuyết (Test 1, 2) → Chatbot nhanh và rẻ hơn.
> Với câu hỏi cần dữ liệu thực (Test 3, 4, 5) → ReAct Agent là bắt buộc.
> Đây là cơ sở cho **Hybrid Decision Flowchart** ở mốc 4.
