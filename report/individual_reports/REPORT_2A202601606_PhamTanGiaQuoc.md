# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phạm Tấn Gia Quốc
- **Student ID**: 2A202601606
- **Date**: 2026-07-28

---

## I. Technical Contribution (15 Points)

Tôi phụ trách **Prompt & Safeguard Engineer (Role 3)**. Phần việc của tôi là viết và điều chỉnh system prompt cho hai chế độ (Baseline Chatbot và ReAct Agent), quy định Tool Contract cho ReAct, và đặt các ràng buộc (guardrails) để Agent không tự tạo dữ liệu khi chưa có Observation.

- **Modules Implementated**: `src/prompts.py`
- **Code Highlights**:
  - `CHATBOT_BASELINE_PROMPT`: Giới hạn Chatbot chỉ trả lời bằng kiến thức có sẵn, không gọi tool.
  - `REACT_SYSTEM_PROMPT`: Định nghĩa Tool Contract (`Action: tên_công_cụ[các_tham_số_json_hoặc_dạng_chuỗi]`), phân tích ý định (SEARCH / COMPATIBILITY), và quy trình Information Gathering Loop.
  - Guardrails config: `MAX_ITERATIONS = 5`, `MAX_INFO_GATHERING_TURNS = 5`, `MAX_TOOL_CALLS_PER_TURN = 3`.
- **Documentation**: Prompt của tôi được `agent.py` sử dụng trong `process_message_llm_react` và `process_message`. Regex `Action:` trích xuất tool name và args từ LLM output. Guardrails đảm bảo Agent không gọi tool khi thiếu tham số và không bị lặp vô hạn.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: LLM trả về Action với tham số JSON bên trong dấu ngoặc vuông, `parse_and_execute_tool` trong `agent.py` không giải mã JSON chính xác. Cụ thể, khi LLM output: `Action: search_candidates[{"city":"Hà Nội","age":22,"interest":"âm nhạc"}]`, parser không nhận diện JSON hợp lệ ở bước 1 mà rơi xuống bước 3 (`split(",")`), làm tách sai tham số.
- **Log Source**: `agent.py` dòng 67: `raw_tokens = [t.strip().strip('"\'') for t in clean_str.split(",") if t.strip()]`. Log trace cho thấy args bị tách thành `['{"city":"Hà Nội', 'age":22', 'interest":"âm nhạc"}']`.
- **Diagnosis**: Nguyên nhân là parser ưu tiên JSON decode chỉ khi toàn bộ `args_str` là JSON hợp lệ. Khi LLM output JSON có ký tự đặc biệt (Tiếng Việt có dấu) hoặc format không chuẩn, JSON decode thất bại và parser tự động fallback sang CSV split, gây lỗi tách tham số.
- **Solution**: Cải tiến parser bằng cách dùng regex để trích JSON block trong args trước khi split CSV, hoặc chuyển sang structured output / function calling của LLM provider (Groq/Gemini) thay vì text-based Tool Contract.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: `Thought` block giúp Agent giải thích lý do tại sao chọn tool đó. Ở case 3 (compatibility), trace cho thấy `Thought` xác định ý định COMPATIBILITY, `Action: calculate_compatibility[...]` được gọi, Observation trả về `total_score: 87.5` với breakdown. Baseline chỉ trả lời chung chung "không có truy cập dữ liệu". `Thought` làm Agent có khả năng giải trình (explainability) mà Chatbot không có.

2. **Reliability**: Agent perform *worse* khi provider không có API key (Mock fallback) hoặc bị rate limit. Trong những case đó, `process_message_llm_react` trả về `None`, rồi agent.py tương tác xuống rule-based path. Baseline vẫn trả lời được vì không cần tool. Agent còn kém khi LLM output không đúng Tool Contract (sai format Action), khiến parser thất bại hoặc gọi sai tham số.

3. **Observation**: Observation là ranh giới giữa thông tin có bằng chứng và suy đoán. Ở case 3, Observation cung cấp `total_score`, `breakdown`, `strengths`, `weaknesses` -- Agent dựa nguyên vào đó để tổng hợp Final Answer. Ở case 4, Observation báo lỗi "THIẾU DỮ LIỆU" giúp Agent không tự đoán mà quay lại hỏi người dùng. Observation là cơ chế đảm bảo tính grounded của Agent.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Dùng asynchronous queue cho tool calls để xử lý nhiều yêu cầu đồng thời, tránh blocking.
- **Safety**: Thêm Supervisor LLM để kiểm tra Action của Agent trước khi thực thi tool (audit layer), phòng tránh prompt injection.
- **Performance**: Chuyển Action parser sang structured output / function calling thay vì text regex, đảm bảo parse chính xác 100% tham số phức tạp.

