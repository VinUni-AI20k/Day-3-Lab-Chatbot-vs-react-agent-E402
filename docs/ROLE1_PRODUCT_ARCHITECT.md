# Role 1: Product Architect — Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê

> **Đề tài:** #10 — Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê  
> **File đảm nhận:** `config/test_cases.json`  
> **Người đảm nhận:** Tran Gia The (Role 1)

---

## 1. Định hướng bài toán (Product Brief)

### Tên agent

**Rental Viewing Assistant** — Trợ lý tìm và đặt lịch xem nhà trọ / căn hộ cho thuê.

### Mục tiêu

Giúp người dùng:

1. Tìm phòng trọ hoặc căn hộ phù hợp **ngân sách** và **khu vực**
2. Xem **chi tiết tin đăng** (mã phòng, giá, địa chỉ, tiện ích)
3. **Đặt lịch xem phòng** với thông tin liên hệ

Tất cả dữ liệu tin đăng và lịch hẹn phải lấy từ **hệ thống tra cứu thực** (tool), không được bịa.

### Câu hỏi cốt lõi của bài toán

> Người dùng cần thông tin **cập nhật và có thể hành động** (tìm phòng, đặt lịch) — Chatbot thuần không đủ, cần ReAct Agent gọi tool.

### So sánh Chatbot vs ReAct Agent

| Tình huống | Chatbot (Cấp 2) | ReAct Agent (Cấp 3) |
| :--- | :--- | :--- |
| "Cần giấy tờ gì khi thuê trọ?" | Trả lời từ kiến thức LLM | Cũng OK — **không cần tool** |
| "Tìm phòng dưới 4 triệu ở Gia Lâm" | Dễ bịa danh sách phòng | Gọi `search_rentals` → có mã phòng, giá thật |
| "Tìm căn hộ rồi đặt lịch xem CH002" | Có thể giả vờ đặt lịch thành công | `search_rentals` → `book_viewing` → xác nhận lịch hẹn |
| Mã phòng / địa điểm / ngày giờ vô lý | Có thể bịa "đã đặt thành công" | Tool báo lỗi → Guardrail dừng an toàn |

---

## 2. Bảng chấm Agentic Fit (Scoring Matrix)

*Gửi Role 5A điền vào `docs/trace_eval.md`.*

| Tiêu chí | Điểm (1–5) | Lý do đánh giá |
| :--- | :---: | :--- |
| Multi-step Reasoning | **4/5** | Quy trình: tìm phòng → chọn mã → đặt lịch xem |
| Tool Interaction | **5/5** | Cần tra cứu DB tin đăng và hệ thống lịch hẹn thực |
| Dynamic Decision | **4/5** | Kết quả search quyết định có đặt lịch được hay không |
| Long Horizon | **3/5** | Quy trình 2–3 bước, chưa cần memory dài hạn |
| **TỔNG ĐIỂM FIT** | **16/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT** |

---

## 3. Tool Specs (gửi Role 2)

Role 2 triển khai trong `src/tools.py` với 3 tool sau:

### 3.1. `search_rentals`

```text
search_rentals(location: str, max_price: int, property_type: str = None) -> str
```

| Field | Mô tả |
| :--- | :--- |
| **Mục đích** | Tìm danh sách phòng trọ / căn hộ theo khu vực và ngân sách |
| **Input** | `location` (quận/huyện), `max_price` (VNĐ/tháng), `property_type` (`phòng trọ` / `căn hộ`) |
| **Output** | Danh sách mã phòng, giá, địa chỉ, loại BĐS |
| **Lỗi** | `"LỖI: Không tìm thấy tin đăng nào tại '{location}'."` |

**Mock data gợi ý:**

| Mã | Khu vực | Loại | Giá |
| :--- | :--- | :--- | :--- |
| PT001 | Gia Lâm | Phòng trọ | 3.200.000 VNĐ/tháng |
| PT002 | Gia Lâm | Phòng trọ | 3.800.000 VNĐ/tháng |
| CH001 | Gia Lâm | Căn hộ | 7.500.000 VNĐ/tháng |
| CH002 | Gia Lâm | Căn hộ | 6.800.000 VNĐ/tháng |

### 3.2. `get_rental_details`

```text
get_rental_details(listing_id: str) -> str
```

| Field | Mô tả |
| :--- | :--- |
| **Mục đích** | Xem chi tiết một tin đăng theo mã phòng |
| **Input** | `listing_id` (VD: `PT001`, `CH002`) |
| **Output** | Diện tích, tiện ích, địa chỉ, chủ nhà, trạng thái |
| **Lỗi** | `"LỖI: Không tìm thấy tin đăng mã '{listing_id}'."` |

### 3.3. `book_viewing`

```text
book_viewing(listing_id: str, date: str, time: str, contact_name: str) -> str
```

| Field | Mô tả |
| :--- | :--- |
| **Mục đích** | Đặt lịch xem phòng |
| **Input** | Mã phòng, ngày, giờ, tên người liên hệ |
| **Output** | Xác nhận đặt lịch thành công (mã lịch hẹn, thời gian) |
| **Lỗi** | Mã không tồn tại, ngày/giờ sai định dạng → trả chuỗi `LỖI:`, không crash |

**Đăng ký registry:**

```python
AVAILABLE_TOOLS = {
    "search_rentals": search_rentals,
    "get_rental_details": get_rental_details,
    "book_viewing": book_viewing,
}
```

---

## 4. Failure Modes (gửi Role 3)

Role 3 cần xử lý trong `src/prompts.py` và guardrails:

| # | Failure Mode | Biểu hiện | Cách xử lý mong đợi |
| :---: | :--- | :--- | :--- |
| 1 | Unknown listing ID | Mã `XYZ999` không có trong DB | Tool trả lỗi, Agent thử lại hoặc hỏi lại user |
| 2 | Invalid location | "Atlantis", quận không tồn tại | Tool trả lỗi, Agent không bịa kết quả |
| 3 | Malformed datetime | `32/13/2026`, `25:99` | Tool trả lỗi định dạng ngày/giờ |
| 4 | Repeated Action | Gọi `book_viewing` cùng tham số lặp lại | `MAX_ITERATIONS` ngắt vòng lặp |
| 5 | Premature Final Answer | Trả "đã đặt lịch" khi chưa gọi tool | Prompt ép: chỉ Final Answer khi có Observation |

---

## 5. Bộ 5 Test Cases

> File chính thức: [`config/test_cases.json`](../config/test_cases.json)

### Test Case #1 — Đơn giản (chỉ LLM)

- **Câu hỏi:** *"Lần đầu thuê phòng trọ, tôi cần chuẩn bị những giấy tờ gì?"*
- **Kỳ vọng:** Chatbot trả lời trực tiếp (CMND/CCCD, hợp đồng, tiền cọc...). **Không gọi tool.**

### Test Case #2 — Đơn giản (chỉ LLM)

- **Câu hỏi:** *"Tiền cọc phòng trọ ở Việt Nam thường bằng bao nhiêu tháng tiền nhà?"*
- **Kỳ vọng:** Chatbot trả lời từ kiến thức chung (1–2 tháng). **Không gọi tool.**

### Test Case #3 — Multi-step (1 tool)

- **Câu hỏi:** *"Tìm giúp tôi phòng trọ dưới 4 triệu/tháng ở Gia Lâm, Hà Nội."*
- **Kỳ vọng:** Agent gọi `search_rentals(location='Gia Lâm', max_price=4000000, property_type='phòng trọ')`, tổng hợp danh sách có mã phòng và giá.

### Test Case #4 — Multi-step (2 tools)

- **Câu hỏi:** *"Tìm căn hộ cho thuê ở Gia Lâm dưới 8 triệu/tháng, sau đó đặt lịch xem phòng mã CH002 vào thứ 7 tuần này lúc 10:00, tên liên hệ Trần Minh Đức."*
- **Kỳ vọng:**
  1. `search_rentals(location='Gia Lâm', max_price=8000000, property_type='căn hộ')`
  2. `book_viewing(listing_id='CH002', date='thứ 7 tuần này', time='10:00', contact_name='Trần Minh Đức')`
  3. Báo kết quả đặt lịch cho người dùng.

### Test Case #5 — Edge Case (bẫy Guardrail)

- **Câu hỏi:** *"Đặt lịch xem phòng trọ mã XYZ999 ở thành phố Atlantis vào ngày 32/13/2026 lúc 25:99."*
- **Kỳ vọng:** Tool báo lỗi (mã không tồn tại / địa điểm không hợp lệ / ngày giờ sai). Agent **không bịa** kết quả đặt lịch thành công. Guardrail ngắt sau `MAX_ITERATIONS` và trả thông báo lịch sự.

---

## 6. Phân luồng Hybrid (gợi ý cho Role 5B)

```text
User query
    │
    ├─ Câu hỏi lý thuyết / tư vấn chung (giấy tờ, quy định, mẹo thuê trọ)
    │       └─► Chatbot path (1 LLM call, 0 tool)
    │
    └─ Câu hỏi cần dữ liệu thực (tìm phòng, xem chi tiết, đặt lịch)
            └─► ReAct Agent path (Thought → Action → Observation)
```

---

## 7. Checklist Role 1 theo mốc

### Mốc 1 — Định hình & Agentic Fit

- [x] Chọn đề tài #10
- [x] Viết Product Brief & Scoring Matrix
- [x] Liệt kê tool specs gửi Role 2
- [x] Liệt kê failure modes gửi Role 3
- [ ] Thống nhất với cả nhóm trước khi sang Mốc 2
- [ ] Push Git: `git add .` → `git commit -m "Moc 1: Dinh hinh de tai 10 - Role 1"` → `git push`

### Mốc 2 — Test Cases

- [x] Viết 5 test cases vào `config/test_cases.json`
- [ ] Push Git: `git commit -m "Moc 2: Test cases de tai 10 - Role 1"`

### Mốc 3 — Kiểm tra Agent

- [ ] Chạy test case #5, xác nhận Guardrail hoạt động với câu bẫy

### Mốc 4 — Cross-Audit

- [ ] Chuẩn bị câu bẫy bổ sung để tấn công Agent nhóm khác (nếu được yêu cầu)

---

## 8. Thông báo nhanh cho các Role khác

| Role | Việc cần làm |
| :--- | :--- |
| **Role 2** | Implement 3 tool trong `src/tools.py` theo mục 3 |
| **Role 3** | Cập nhật prompt cho domain thuê phòng; xử lý failure modes mục 4 |
| **Role 4** | `git pull` → lắp ReAct loop với tool mới vào `src/app.py` |
| **Role 5A** | Copy Scoring Matrix mục 2 vào `docs/trace_eval.md`; ghi trace log khi chạy test |
| **Role 5B** | Vẽ hybrid flowchart theo mục 6 vào `docs/hybrid_flowchart.mermaid` |
