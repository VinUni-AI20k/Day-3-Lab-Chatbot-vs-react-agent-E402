# 🔗 HỢP ĐỒNG TÍCH HỢP (INTEGRATION CONTRACT)

> Do **Role 4 — Core Developer / Integrator** ban hành.
> Đề tài nhóm: **Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý**
>
> `src/app.py` đã hoàn thiện và **không hardcode tên tool nào**. Mọi người chỉ cần
> giữ đúng giao kèo dưới đây, app sẽ tự động chạy — không ai phải sửa file của người khác.

---

## ⚠️ RÀNG BUỘC ĐẠO ĐỨC CỦA ĐỀ TÀI (cả nhóm đọc trước)

Đây là đề tài tâm lý, nên bài nộp **phải** thể hiện rõ 3 điều sau, nếu không sẽ bị phản biện chết ở Mốc 4:

1. Agent là **trợ lý khám phá bản thân**, KHÔNG chẩn đoán bệnh (không nói "bạn bị trầm cảm/rối loạn đa nhân cách").
2. Kết quả trắc nghiệm là **tham khảo**, luôn kèm khuyến nghị gặp chuyên gia thật.
3. Có **Safety Gate** chặn nội dung tự hại — đã cài sẵn trong `src/app.py`.

---

## 🟢 ROLE 1 — `config/test_cases.json`

Giữ nguyên cấu trúc 4 khóa: `id`, `category`, `question`, `expected_behavior`.
Cần đủ 3 nhóm để chấm điểm mục "Test Design" (20%):

| Loại | Số câu | Ví dụ theo đề tài |
| :--- | :---: | :--- |
| 🟢 Đơn giản (chỉ cần LLM) | 2 | *"Nhân cách hướng nội khác hướng ngoại thế nào?"* |
| 🟡 Multi-step (cần tool) | 2 | *"Tôi hay im lặng nơi đông người nhưng lại rất lì lợm khi làm việc nhóm — con người thứ 2 của tôi là gì và tôi nên làm nghề gì?"* |
| 🔴 Edge case (bẫy guardrail) | 1 | Câu gọi tool không tồn tại, hoặc câu có dấu hiệu khủng hoảng để test Safety Gate |

---

## 🛠️ ROLE 2 — `src/tools.py`

**Giao kèo bắt buộc:**

1. Mỗi tool là một hàm nhận **tham số kiểu `str`** (app truyền vào toàn chuỗi).
2. **Dòng đầu tiên của docstring** sẽ được app tự động đưa vào prompt làm mô tả tool
   ➔ viết dòng đó thật rõ "khi nào nên dùng tool này".
3. Lỗi nghiệp vụ phải `return` chuỗi bắt đầu bằng `"LỖI: ..."`, **tuyệt đối không `raise`**.
4. Đăng ký hàm vào dict `AVAILABLE_TOOLS` ở cuối file, nếu không app sẽ không thấy.

**Gợi ý 4 tool cho đề tài (thay thế `get_weather` / `search_flights`):**

| Tool | Chữ ký | Nhiệm vụ |
| :--- | :--- | :--- |
| `analyze_personality_traits` | `(behaviors: str)` | Nhận mô tả hành vi ➔ trả về nhóm tính trạng MBTI/Big Five |
| `lookup_shadow_archetype` | `(trait: str)` | Tra "nhân cách thứ 2" (Shadow Self theo Jung) ứng với tính trạng |
| `get_coping_strategy` | `(emotion: str)` | Tra kỹ thuật điều hòa cảm xúc theo cảm xúc đầu vào |
| `screening_questionnaire` | `(topic: str)` | Trả về bộ câu hỏi sàng lọc tham khảo (KHÔNG phải chẩn đoán) |

```python
def lookup_shadow_archetype(trait: str) -> str:
    """Tra cứu nguyên mẫu "nhân cách thứ 2" (Shadow Self) ứng với một tính trạng.

    Args:
        trait (str): Tính trạng nổi trội (VD: 'hướng nội', 'cầu toàn')
    Returns:
        str: Mô tả nguyên mẫu bóng, hoặc chuỗi "LỖI: ..." nếu không tra được.
    """
    data = {"hướng nội": "The Sage — bên trong là người quan sát sắc sảo, ..."}
    key = trait.lower().strip()
    for k, v in data.items():
        if k in key:
            return v
    return f"LỖI: Chưa có dữ liệu nguyên mẫu cho tính trạng '{trait}'."


AVAILABLE_TOOLS = {
    "lookup_shadow_archetype": lookup_shadow_archetype,
    # ... đăng ký tiếp các tool khác
}
```

---

## 🧠 ROLE 3 — `src/prompts.py`

**Giao kèo bắt buộc — app import đúng 3 biến này:**
`CHATBOT_BASELINE_PROMPT`, `REACT_SYSTEM_PROMPT`, `MAX_ITERATIONS`.

1. **KHÔNG cần liệt kê tool trong `REACT_SYSTEM_PROMPT` nữa.** App tự sinh danh sách
   tool từ code thật của Role 2 và nối vào cuối prompt ➔ prompt không bao giờ lệch code.
   Phần bạn viết chỉ nên nói về **vai trò, giọng điệu, ranh giới đạo đức và định dạng ReAct**.
2. Nâng `MAX_ITERATIONS` lên **5** nếu nhóm dùng 4 tool (3 bước là quá chật cho câu multi-step).
3. **Tùy chọn (nên làm)** — khai báo thêm 2 biến để ghi đè Safety Gate mặc định của app:

```python
CRISIS_KEYWORDS = ["tự tử", "tự sát", "muốn chết", "tự làm hại", ...]
CRISIS_RESPONSE = "..."   # ⚠️ Nhớ kiểm chứng lại số hotline trước khi nộp bài
```

Nội dung nên có trong `REACT_SYSTEM_PROMPT`: *"Bạn là trợ lý khám phá bản thân, KHÔNG phải bác sĩ. Không chẩn đoán bệnh. Luôn kết thúc bằng khuyến nghị tham khảo chuyên gia."*

---

## 📊 ROLE 5 — `docs/trace_eval.md`

Mỗi lần chạy `python src/app.py`, app tự xuất file trace vào thư mục `logs/`
(đã được gitignore). Mở file mới nhất, copy nguyên khối trace dán vào báo cáo.
Nhớ phân loại từng output: **correct** / **safe fallback** / **hallucinated**.

---

## ✅ LỆNH CHẠY

```bash
python src/app.py                # chạy toàn bộ test case, cả chatbot lẫn agent
python src/app.py --case 3       # chạy riêng 1 test case
python src/app.py --mode agent   # chỉ chạy ReAct Agent
python src/app.py --chat         # hội thoại trực tiếp — dùng khi bị nhóm bạn cross-audit
```
