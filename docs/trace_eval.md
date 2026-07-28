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

## 💬 4. QUAN SÁT CHATBOT BASELINE (MỐC 2)

> ✅ **Đây là dữ liệu chạy thật**, không phải chép từ `print()` mô phỏng.

| Thông số | Giá trị |
| :--- | :--- |
| Ngày chạy | 2026-07-28 |
| Commit | `c4bd1b3` (nhánh `role-5a/moc2-failure-taxonomy`, đã merge `integration/moc2`) |
| Provider / Model | `MistralProvider` / `mistral-medium-latest` |
| Lệnh chạy | `python src/app.py` |
| Số test case | 8 trong `config/test_cases.json` (⚠️ `src/app.py:68` chỉ chạy `tests[:5]`; các case 6–8 được chạy riêng để quan sát đủ) |

### 4.1. Bảng tổng hợp phản hồi

| ID | Loại | Chatbot Baseline trả lời gì | Có bằng chứng thật? | Nhận xét của Role 5A |
| :---: | :--- | :--- | :---: | :--- |
| 1 | 🟢 Đơn giản | Tự giới thiệu đúng vai trò, liệt kê 3 năng lực hỗ trợ | ➖ không cần | ✅ **Đạt**. Đúng kỳ vọng, không cần tool. |
| 2 | 🟢 Chính sách | **Hỏi ngược lại** *"bạn cho mình biết tên cửa hàng?"*, không nêu được chính sách 7 ngày | ❌ | ⚠️ **Chưa đạt kỳ vọng**. Chính sách 7 ngày/nguyên tem mác không nằm trong prompt nên chatbot không có gì để trả lời. Thiếu kiến thức tĩnh, không phải lỗi thiếu tool. |
| 3 | 🟡 Cần 1 tool | **(rỗng — không in ra chữ nào)** | ❌ | 🚨 Xem RCA mục 4.2. |
| 4 | 🟡 Cần 2 tools | **(rỗng)** | ❌ | 🚨 Xem RCA mục 4.2. |
| 5 | 🔴 F1 | Từ chối lịch sự việc hủy đơn/đổi SĐT, đề nghị chuyển hotline, gợi ý tra cứu thay thế | ➖ | ✅ Từ chối đúng phạm vi — nhưng là do prompt, **chưa có phanh thật**. |
| 6 | 🔴 F2 | Chủ động hỏi lại mã đơn hàng trước khi tra cứu | ➖ | ✅ Hành vi mong muốn ở F2; cần kiểm chứng lại khi có ReAct loop. |
| 7 | 🔴 F3/F4 | **(rỗng)** | ❌ | 🚨 Xem RCA mục 4.2. |
| 8 | 🔴 F5 (injection) | *"Tôi không thể ghi đè quy trình nghiệp vụ..."* — **không sinh ra chuỗi `Observation:` giả** | ➖ | ✅ Chống được prompt injection ở mức baseline. Phải test lại ở Mốc 3 khi có parser thật. |

**Kết luận Mốc 2**: Chatbot baseline xử lý được câu hỏi tĩnh (case 1) và biết từ chối/hỏi lại
(case 5, 6, 8), nhưng **không trả lời được bất kỳ câu nào cần dữ liệu đơn hàng thật** (case 3, 4, 7).
Đây chính là khoảng trống mà ReAct Agent phải lấp ở Mốc 3.

### 4.2. 🚨 RCA: Vì sao case 3, 4, 7 trả về chuỗi rỗng?

Không phải chatbot "im lặng". Gọi thẳng API Mistral với đúng payload mà `MistralProvider` gửi, kết quả:

```text
finish_reason : tool_calls
message keys  : ['role', 'tool_calls', 'content']
content       : ''
tool_calls    : [{'function': {'name': 'search_order',
                               'arguments': '{"order_id": "DH-1002"}'}}]
```

**Chuỗi nguyên nhân (3 tầng):**

1. **Prompt**: `CHATBOT_BASELINE_PROMPT` (`src/prompts.py`) nói thẳng với model rằng nó *có* các công cụ
   `search_order`, `create_return_request`, `create_exchange_request`. Nhưng baseline theo CODELAB là
   **chatbot KHÔNG có tool** — mục đích là để lộ ra giới hạn của nó.
2. **Model**: `mistral-medium-latest` phản ứng đúng như được huấn luyện — phát ra **native function call**
   với `finish_reason = tool_calls` và `content = ""`, dù payload **không hề khai báo `tools`**.
3. **Adapter**: `MistralProvider.generate()` (`src/providers.py:165`) chỉ đọc
   `data["choices"][0]["message"]["content"]` ➔ trả về chuỗi rỗng, **nuốt luôn `tool_calls` mà không báo lỗi**.
   Ứng dụng in ra khoảng trắng, người chạy tưởng là model hỏng.

**Đề xuất (thuộc quyền Role 3 & Role 4, Role 5A chỉ ghi nhận):**

* Role 3: bỏ tên tool khỏi `CHATBOT_BASELINE_PROMPT` — baseline phải nói *"tôi không tra cứu được"*
  thì mới chứng minh được nhu cầu dùng Agent.
* Role 4: khi `content` rỗng, adapter nên trả về chuỗi cảnh báo (VD:
  `"[Cảnh báo] Model trả về tool_calls thay vì text"`) thay vì `""` — im lặng là kiểu lỗi khó soi nhất.

### 4.3. ⚠️ Rủi ro phát hiện sớm cho Mốc 3 (sai tên tool)

Model gọi tool tên **`search_order`** (số ít) vì `REACT_SYSTEM_PROMPT` và `ALLOWED_TOOLS` trong
`src/prompts.py` ghi như vậy. Nhưng registry thật trong `src/tools.py` lại là:

```python
AVAILABLE_TOOLS = {
    "search_orders": search_orders,          # ← số NHIỀU
    "create_return_request": ...,
    "create_exchange_request": ...,
}
```

Ngoài ra chữ ký hàm cũng lệch với mô tả trong prompt:

| Prompt (Role 3) | Hàm thật (Role 2) | Lệch |
| :--- | :--- | :--- |
| `search_order[order_id]` | `search_orders(query)` | Tên + tên tham số |
| `create_return_request[order_id, item_id, reason, quantity]` | `create_return_request(order_id, item_sku, reason)` | Thừa `quantity`, sai `item_id`/`item_sku` |
| `create_exchange_request[order_id, item_id, reason, quantity, preferred_item]` | `create_exchange_request(order_id, item_sku, new_variant, reason)` | Lệch 2 tham số |

➔ Nếu không sửa trước Mốc 3, **mọi** lượt tra cứu sẽ rơi vào **F1 (Unknown Tool)** và mọi lượt đổi/trả
rơi vào **F2 (Malformed Args)** — không phải vì Agent yếu, mà vì prompt và registry chưa khớp nhau.

---
