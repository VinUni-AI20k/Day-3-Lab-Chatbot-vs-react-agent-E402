# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Cần suy luận từ tra cứu thời tiết đến chọn trang phục. |
| 🛠️ **Tool Interaction** | `5/5` | Cần tra cứu dữ liệu thời gian thực qua API thời tiết/chuyến bay. |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả bước trước quyết định hành động bước sau. |
| ⏳ **Long Horizon** | `3/5` | Quy trình gồm 2-3 bước xử lý ngắn. |
| **TỔNG ĐIỂM FIT** | **16/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!** |

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

---

## 🧪 3. PHÂN LOẠI LỖI (FAILURE MODE TAXONOMY)

> ⚠️ **Khung phân loại — chưa điền dữ liệu quan sát.** Vòng lặp `run_react_agent()` trong `src/app.py`
> hiện vẫn là bản mô phỏng (in cứng Thought/Action/Observation, chưa gọi `provider.generate()` và chưa
> tra `AVAILABLE_TOOLS`). Chỉ điền các ô `⬜` bên dưới bằng trace **chạy thật**, không chép lại từ
> `print()`. Tên tool là **dự kiến theo đề tài số 5 (Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả)**, chờ
> Role 2 chốt trong `src/tools.py`.

### 3.1. Bảng tổng hợp các dạng lỗi

| Mã | Dạng lỗi (Failure Mode) | Cách kích hoạt (Trap Input) | Biểu hiện kỳ vọng ở Agent V1 | Cơ chế phục hồi ở Agent V2 | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **F1** | **Unknown Tool** | Hỏi việc ngoài bộ tool, VD: *"Hủy đơn hàng #DH1024 giúp tôi"* khi chưa có tool hủy đơn | LLM tự bịa tên tool `huy_don_hang`, app không tìm thấy trong `AVAILABLE_TOOLS` | Observation trả về danh sách tool hợp lệ để LLM chọn lại ở vòng sau | ⬜ |
| **F2** | **Malformed Args** | Câu thiếu tham số bắt buộc, VD: *"Đơn của tôi tới đâu rồi?"* (không có mã đơn) | Parser nhận `tra_cuu_don_hang['']` hoặc sai cú pháp ngoặc | Observation nêu đúng cú pháp / hỏi lại người dùng mã đơn thay vì crash | ⬜ |
| **F3** | **Repeated Action** | Câu bẫy khiến tool luôn trả lỗi giống nhau, VD: mã đơn **không tồn tại** `#DH0000` | Gọi lặp 1 tool với **cùng tham số** qua nhiều vòng, không tiến triển | Phát hiện action trùng ➔ đổi hướng hoặc dừng sớm | ⬜ |
| **F4** | **Budget Exhausted** | Bất kỳ case nào chạm `MAX_ITERATIONS` mà chưa có Final Answer | Vòng lặp bị cắt ngang, không có câu trả lời | Fallback lịch sự, **không crash** (checkpoint CODELAB §5) | ⬜ |
| **F5** | **Hallucinated Observation** | Prompt yếu khiến LLM tự viết luôn dòng `Observation:` | Agent "trả lời có bằng chứng" nhưng bằng chứng do chính nó bịa | App cắt output tại `Action`, chỉ app được ghi Observation từ giá trị tool trả về | ⬜ |

**Ghi chú**: F1–F3 là ba nhánh recovery mà CODELAB §5 chấm điểm; F4 là checkpoint bắt buộc
(*"Agent V2 không bị crash khi gặp câu bẫy"*); F5 kiểm chứng nguyên tắc bất biến số 2 của §4
(*"mỗi Action đúng một Observation, do ứng dụng chèn vào"*) — đây là lỗi khó thấy nhất vì trace vẫn
trông rất đẹp.

### 3.2. Phân tích nguyên nhân gốc (RCA) — Before/After

> Điền **ít nhất 1 failed trace** đầy đủ theo mẫu dưới đây (yêu cầu bắt buộc của checkpoint §5).

#### ⬜ F__ — *(tên dạng lỗi)*

* **Test case**: `#__` — *"..."*
* **Provider / model khi chạy**: `______` (VD: `mock`, `gemini`)

**Trace TRƯỚC (Agent V1 — thất bại):**

```text
Thought 1: ...
Action 1: ...
Observation 1: ...
...
[Kết quả: ...]
```

* **Triệu chứng quan sát được**: ...
* **Nguyên nhân gốc (Root Cause)**: ... *(chỉ rõ nằm ở prompt, ở parser, hay ở tool)*
* **Sửa ở đâu**: `src/prompts.py` / `src/app.py` / `src/tools.py` — *(nêu cụ thể)*

**Trace SAU (Agent V2 — đã phục hồi):**

```text
Thought 1: ...
Action 1: ...
Observation 1: ...
...
Final Answer: ...
```

* **Khác biệt then chốt**: ...
* **Đã dừng đúng cách chưa?**: ⬜ Final Answer ⬜ Guardrail cắt an toàn ⬜ Vẫn lặp/crash

---
