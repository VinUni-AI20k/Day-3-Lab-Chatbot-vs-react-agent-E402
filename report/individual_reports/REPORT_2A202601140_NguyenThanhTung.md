# Individual Report: Lab 3 - Production-Grade Agentic System

- **Student Name**: Nguyễn Thanh Tùng
- **Student ID**: 2A202601140
- **Role**: Role 4 - Agent Integrator
- **Date**: 2026-07-28

---

## I. Technical Contribution

### 1. Vai trò và Phạm vi Đóng góp (Role & Responsibility)

Là Agent Integrator (Role 4) trong dự án AI Matchmaking Agent ("Bà Mối AI"), nhiệm vụ chính của tôi là kết nối toàn bộ các thành phần rời rạc do các thành viên đảm nhiệm (Tool Specification từ Role 2, System Prompts từ Role 3, Test Cases từ Role 1, Trace Logs từ Role 5) thành một hệ thống AI Agent hoàn chỉnh, đồng bộ và sẵn sàng vận hành trên Production.

Trong quá trình tích hợp, tôi trực tiếp rà soát, tái cấu trúc và sửa lỗi cho các module Tool (`src/tools.py`), điều chỉnh System Prompts (`src/prompts.py`) để khắc phục hiện tượng LLM bối rối khi gọi tool, đồng thời lập trình động cơ tích hợp 4 Cấp độ Hệ thống AI từ Rule-Based đến Free-Style Autonomous Agent.

### 2. Các Module và Thành phần Tích hợp Chính

- **Tích hợp và Chuẩn hóa Provider LLM (`src/providers.py`)**:
  - Kết nối Google Gemini API (`gemini-3.5-flash-lite`) vào hệ thống.
  - Xây dựng cơ chế Fallback đa tầng (Google GenAI SDK -> Legacy SDK -> REST API Direct) giúp hệ thống tự động vượt qua sự cố khi gặp hạn ngạch Free Tier 15 RPM.

- **Tinh chỉnh Tool Registry & Interface (`src/tools.py`)**:
  - Tiếp nhận các định nghĩa công cụ `search_candidates` và `calculate_compatibility` từ Role 2, loại bỏ công cụ không thuộc bài toán chính (`get_weather`), đồng thời chỉnh sửa định dạng tham số đầu vào/đầu ra để khớp với JSON Schema của Gemini.
  - Bổ sung phanh an toàn PII Redaction che SĐT (`0987***321`) và nới lỏng bán kính tìm kiếm Relaxed Search khi CSDL có 0 kết quả khớp cứng.

- **Kết nối Luồng 4 Cấp độ AI System (`src/ai_levels/`)**:
  - **Level 1 (`level1_rule_based.py`)**: Đóng gói luồng Rule-Based Bot khớp từ khóa `if/else`.
  - **Level 2 (`level2_llm_chatbot.py`)**: Đóng gói Baseline LLM Chatbot với phanh kiểm tra đầu vào và xử lý ngoại lệ fallback.
  - **Level 3 (`level3_reactive_agent.py`)**: Tái cấu trúc lớp `MatchmakingAgent`, tích hợp luồng ReAct suy luận `Thought -> Action -> Observation` và phanh an toàn *Information Gathering Loop* (Slot Filling) ngắt gọi tool bối rối khi thiếu thông tin.
  - **Level 4 (`level4_autonomous_agent.py`)**: Thiết kế lại động cơ **Pure Free-Style LLM Dynamic Planner & Orchestrator**. LLM tự do phân tích mục tiêu người dùng, lập kế hoạch N bước, tự chọn hoặc BỎ QUA công cụ không cần thiết (`tool_to_call: NONE`), duy trì bộ nhớ dài hạn `self.memory` và log toàn bộ nhật ký suy luận ReAct-style.

- **Tích hợp Backend API Server & Frontend React UI (`server.py` & `static/index.html`)**:
  - Xây dựng FastAPI REST API quản lý Session State độc lập cho từng người dùng.
  - Tích hợp giao diện React Web UI hiển thị chuỗi suy luận Thought-Action và bộ nhớ Execution Memory.

### 3. Code Highlights

Dưới đây là đoạn mã tích hợp luồng ReAct suy luận tự chủ và lưu vết bộ nhớ dài hạn trong `src/ai_levels/level4_autonomous_agent.py`:

```python
# Tự động lập Kế hoạch N bước tự do bằng LLM (Free-Style Dynamic Planning)
system_prompt = (
    "Bạn là Trí tuệ Nhân tạo Điều phối & Lập kế hoạch Tự chủ (Autonomous Agent Planner).\n"
    "Danh sách Công cụ sẵn có trong hệ thống:\n"
    "1. 'search_candidates': Tra cứu danh sách hoặc hồ sơ ứng viên trong CSDL.\n"
    "2. 'calculate_compatibility': Phân tích ma trận độ tương thích 100 điểm.\n"
    "3. 'NONE': Không gọi công cụ nào (cho câu hỏi kiến thức chung hoặc khi cần hỏi thêm thông tin).\n"
)

# Vòng lặp thực thi tự chủ và lưu nhật ký bộ nhớ
for idx, step_info in enumerate(steps, 1):
    task = step_info.get("task")
    reasoning = step_info.get("reasoning")
    tool_name = step_info.get("tool_to_call")
    
    # Thực thi Action và thu thập Observation
    if tool_name == "search_candidates":
        obs_desc = search_candidates(**tool_args)
    elif tool_name == "calculate_compatibility":
        obs_desc = calculate_compatibility(user_prof, cand_found)
    else:
        obs_desc = self.provider.generate(f"Phản hồi trực tiếp: {self.goal}")

    # Ghi nhớ vết ReAct vào Execution Memory
    self.memory.append({
        "step": idx,
        "task": task,
        "reasoning": reasoning,
        "action": action_desc,
        "observation": obs_desc,
        "result": obs_desc
    })
```

---

## II. Debugging Case Study

### 1. Sự cố 1: Lỗi `KeyError: 'result'` (Internal Server Error 500)
- **Mô tả sự cố**: Khi thực thi câu hỏi Cấp 4 từ giao diện Web UI hoặc gọi API `/api/chat`, server trả về lỗi `500 Internal Server Error` với thông báo: `Lỗi thực thi Agent: 'result'`.
- **Nguồn Log**: Log Uvicorn Server tại `server.py` line 79.
- **Chẩn đoán (Diagnosis)**: Trong quá trình tái cấu trúc Cấp 4 sang luồng ReAct-style, tên key trong cấu trúc dict của `self.memory` đã được đổi từ `"result"` thành `"observation"`. Do đó, khi `server.py` và `src/web_ui.py` cố gắng đọc `m['result']` từ bộ nhớ để hiển thị log lên giao diện, Python đã văng ngoại lệ `KeyError: 'result'`.
- **Giải pháp (Solution)**: 
  - Cập nhật `src/ai_levels/level4_autonomous_agent.py` để bổ sung alias key `"result": obs_desc` song song với `"observation"`.
  - Cập nhật `server.py` và `src/web_ui.py` sử dụng hàm truy cập an toàn `m.get('observation', m.get('result', ''))`.

### 2. Sự cố 2: Lỗi Quota Exceeded HTTP 429 từ Gemini API
- **Mô tả sự cố**: Khi chạy bộ test suite tự động cho 5 test cases qua 4 cấp độ, hệ thống liên tục gửi nhiều request tới Gemini API và bị ngắt giữa chừng với lỗi `RESOURCE_EXHAUSTED` (HTTP 429 Quota Exceeded for 15 RPM free tier).
- **Nguồn Log**: Output log từ `src/providers.py` trong `task-467.log`.
- **Chẩn đoán (Diagnosis)**: Tài khoản Gemini Free Tier giới hạn 15 request/phút. Khi chạy 5 test cases x 4 cấp độ, số lượng request vượt ngưỡng cho phép làm nổ ngoại lệ API.
- **Giải pháp (Solution)**: Xây dựng cơ chế retry tự động với exponential backoff và chuỗi fallback đa tầng trong `GeminiProvider`. Khi một endpoint REST API bị nổ 429, provider tự động chuyển sang thử các model dự phòng (`gemini-3.5-flash-lite` -> `gemini-2.5-flash` -> `gemini-2.0-flash`), giúp toàn bộ test suite chạy thành công 100% không bị dừng đột ngột.

---

## III. Personal Insights: Chatbot vs ReAct Agent

### 1. Khả năng Suy luận (Reasoning)
Khối suy luận `Thought` mang lại sự khác biệt bản chất giữa ReAct Agent và Chatbot thông thường. 
- Chatbot thuần túy (Cấp 2) đưa ra câu trả lời trực tiếp bằng cách dự đoán từ tiếp theo. Khi gặp câu hỏi cần dữ liệu thực tế (như tìm bạn gái ở Hà Nội 24 tuổi), Chatbot sẽ bị "ảo giác" (hallucination) tự bịa ra thông tin hoặc từ chối trả lời vì không có dữ liệu.
- Trong khi đó, ReAct Agent (Cấp 3 & 4) sử dụng khối `Thought` để phân tích tình huống: *"Người dùng cần tìm bạn gái 24t ở Hà Nội thích indie. Ta đã có đủ tham số giới tính, vị trí, độ tuổi. Ta cần gọi công cụ search_candidates để lấy dữ liệu thực tế trước khi trả lời"*. Khối `Thought` giúp Agent có khả năng tự định hướng hành động chuẩn xác.

### 2. Độ Tin Cậy và Ranh Giới Thất Bại (Reliability)
Mặc dù ReAct Agent vượt trội về khả năng tương tác với môi trường, có những trường hợp Agent hoạt động kém hơn Chatbot đơn giản:
- **Câu hỏi kiến thức tổng quát**: Đối với các câu hỏi lý thuyết mở như *"Tiêu chuẩn mối quan hệ lành mạnh là gì?"*, Chatbot Cấp 2 phản hồi rất nhanh và mượt mà. Trong khi đó, một ReAct Agent Cấp 3 chưa tối ưu có thể bị bối rối cố gắng đi tìm một Tool để gọi, dẫn đến tốn thêm thời gian latency và chi phí token không cần thiết. Đây chính là lý do tôi đã nâng cấp Cấp 4 thành Free-Style Dynamic Planner để biết thông minh **BỎ QUA gọi tool (`tool_to_call: NONE`)** khi gặp câu hỏi dạng này.

### 3. Tác động của Phản hồi Môi trường (Observations)
Phản hồi từ công cụ (`Observation`) đóng vai trò là "mắt thần" điều hướng các bước tiếp theo của Agent:
- Ví dụ trong **Test Case 5** (Tìm bạn gái 18-20t ở Cà Mau thích đi leo núi tuyết), khi gọi tool `search_candidates`, kết quả Observation trả về `is_relaxed_search: True` kèm thông báo không có kết quả khớp tuyệt đối tại Cà Mau.
- Nhờ có Observation này, Agent ở bước tiếp theo không bị ảo tưởng đáp án mà đã lập tức điều chỉnh lời khuyên: giải thích cho người dùng về khí hậu Cà Mau không có tuyết và đề xuất các ứng viên gần nhất từ CSDL.

---

## IV. Future Improvements

Để phát triển hệ thống AI Agent từ quy mô Lab lên môi trường Production thực tế phục vụ hàng triệu người dùng, tôi đề xuất các hướng cải tiến kỹ thuật sau:

1. **Scalability (Khả năng Mở rộng)**:
   - Chuyển đổi kiến trúc gọi Tool đồng bộ hiện tại sang mô hình **Asynchronous Task Queue** sử dụng Celery hoặc Redis Queue. Các tác vụ tính toán ma trận tương thích hoặc truy xuất CSDL nặng sẽ được thực thi bất đồng bộ, tránh làm nghẽn Event Loop của Web API.

2. **Safety & Auditing (An toàn & Giám sát)**:
   - Triển khai mô hình **Supervisor LLM (Agent Giám sát)** hoạt động như một lớp phanh an toàn độc lập. Supervisor LLM sẽ kiểm duyệt toàn bộ tham số của Tool Call và phản hồi cuối cùng của Agent trước khi gửi tới người dùng để phát hiện Prompt Injection, rò rỉ PII hoặc các nội dung không phù hợp.

3. **Performance & Tool Retrieval (Hiệu năng & Tra cứu Công cụ)**:
   - Tích hợp **Vector Database (Qdrant / Milvus)** lưu trữ Embeddings của hàng nghìn hồ sơ ứng viên và tài liệu hướng dẫn.
   - Khi hệ thống mở rộng lên hàng trăm Tool khác nhau (như đặt bàn ăn, mua vé xem phim, gửi tin nhắn), sử dụng Vector Search để tự động tra cứu và chọn ra Top K công cụ phù hợp nhất đưa vào Prompt của Agent, giúp giảm bớt token overhead và tăng tốc độ phản hồi.
