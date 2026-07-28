# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Dương Đức Minh
- **Student ID**: 2A202601306
- **Role**: Role 2 - Tool & Spec Engineer
- **Date**: 2026-07-28

---

## I. Technical Contribution (15 Points)

Tôi phụ trách vai trò **Role 2 - Tool & Spec Engineer**. Nhiệm vụ chính của tôi là thiết kế, xây dựng và chuẩn hóa toàn bộ các công cụ (Tools) cho hệ thống **AI Matchmaking Agent ("Bà Mối AI")**, định nghĩa các Pydantic Schemas đầu vào/đầu ra, cài đặt phanh an toàn (Guardrails) ở mức Tool, và đảm bảo tương tác mượt mà với vòng lặp ReAct Agent (`Thought -> Action -> Observation`).

- **Modules implemented**: `tools/compatibility.py`, `tools/search.py`, `src/tools.py`
- **Modules collaborated/tested**: `agent.py`, `src/app.py`, `src/ai_levels/level3_reactive_agent.py`, `config/test_cases.json`, `docs/trace_eval.md`

### Code Highlights & Chi tiết Đóng góp Kỹ thuật

#### 1. Tool 1: `calculate_compatibility` (`tools/compatibility.py`)
Thiết kế thuật toán đánh giá độ tương thích toàn diện giữa 2 đối tượng dựa trên Ma trận trọng số (Thang điểm 100):

- **Hard Filter (Bộ lọc cứng)**: Kiểm tra tương thích về giới tính và định hướng ghép đôi. Nếu không phù hợp (ví dụ: cùng giới tính nhưng không phải mối quan hệ đồng giới mong muốn), trả về `total_score = 0` ngay lập tức kèm giải thích rõ ràng.
- **Vị trí địa lý (Trọng số 20%)**: Sử dụng hàm phân vùng `get_region()`:
  - Cùng Tỉnh/Thành phố: **20 điểm**.
  - Cùng Vùng miền (Miền Bắc / Miền Trung / Miền Nam): **10 điểm**.
  - Khác vùng miền địa lý xa: **0 điểm**.
- **Độ tuổi & Chiều cao (Trọng số 20%)**:
  - *Độ tuổi*: Lệch 0-3 tuổi (**10đ**), 4-6 tuổi (**6đ**), >6 tuổi (**2đ**).
  - *Chiều cao*: Nam cao hơn Nữ từ 5cm - 20cm (**10đ**), bằng/thấp hơn hoặc lệch quá xa (**3đ**).
- **Sở thích (Trọng số 40% - Vector Similarity)**: Xây dựng hàm `calculate_text_similarity()` tính Cosine Similarity giữa 2 văn bản sở thích bằng `sentence-transformers` (`all-MiniLM-L6-v2`), kết hợp cơ chế Fallback sang TF/Bag-of-Words Cosine Similarity với keyword matching boost khi chưa cài thư viện vector.
- **Học vấn & Nghề nghiệp (Trọng số 20%)**: Đánh giá độ tương đồng hoặc bổ trợ giữa các ngành nghề (ví dụ: Software Engineer & UI/UX Designer bổ trợ nhau nhận **20đ**).
- **Structured Output**: Chuẩn hóa đầu ra bằng Pydantic model `CompatibilityResult` gồm các trường `total_score`, `breakdown`, `strengths`, `weaknesses`, và `summary`.

#### 2. Tool 2: `search_candidates` (`tools/search.py`)
Xây dựng công cụ tìm kiếm ứng viên thông minh dựa trên cơ chế **Hybrid Search** (Hard Filter + Semantic Vector Ranking):

- **Mock Candidate Database (`MOCK_CANDIDATE_DB`)**: Thiết lập cơ sở dữ liệu gồm 18 hồ sơ ứng viên đa dạng về khu vực (Hà Nội, TP.HCM, Đà Nẵng), độ tuổi, nghề nghiệp và mô tả sở thích chi tiết.
- **Hard Filtering**: Lọc tiên quyết theo Giới tính (`gender`), Khoảng tuổi (`min_age`, `max_age`), và Tỉnh/Thành phố (`location`) trước khi tính điểm vector.
- **Privacy Masking Guardrail**: Tự động ẩn Số điện thoại (`0912345678` -> `0912***678`) và Họ tên ứng viên ("Nguyễn Văn Tuấn" -> "Nguyễn Văn T***" / "Nguyễn V.T.") nhằm bảo vệ an toàn PII.
- **Relaxed Search Guardrail**: Nếu Hard Filter trả về 0 ứng viên thỏa mãn, tool không trả về mảng rỗng (tránh gãy luồng ReAct) mà tự động nới lỏng bán kính vị trí / khoảng tuổi và gắn nhãn `is_relaxed_search = True` kèm thông báo hướng dẫn.
- **Structured Output**: Trả về Pydantic model `SearchResponse` chứa danh sách `CandidateMatch`.

#### 3. Module tích hợp Tool Registry (`src/tools.py`)
- Bổ sung công cụ tra cứu thời tiết phụ trợ `get_weather(location)` để kiểm thử khả năng chọn đúng tool của Agent.
- Đóng gói danh sách công cụ trong dict `AVAILABLE_TOOLS` (`calculate_compatibility`, `search_candidates`, `get_weather`).
- Xuất toàn bộ các Pydantic Schemas (`UserProfile`, `CompatibilityResult`, `CandidateMatch`, `SearchResponse`, `MOCK_CANDIDATE_DB`) bằng cơ chế `importlib.util` động để tránh lỗi circular import.
- Áp dụng bọc `try-except` phòng thủ ở cấp Tool, đảm bảo mọi lỗi thực thi đều trả về thông điệp chuỗi thông báo lỗi thay vì quăng Exception làm crash app.

---

## II. Debugging Case Study (10 Points)

### 1. Problem Description
Trong quá trình thử nghiệm integration test với ReAct Agent, LLM đôi khi trích xuất hoặc truyền tham số dạng chuỗi JSON / Dictionary không chuẩn vào các hàm tool (ví dụ: truyền thiếu dict `person_b` hoặc truyền chuỗi JSON chưa unescape quotes vào `search_candidates`). Điều này khiến Pydantic ném ra lỗi `ValidationError` hoặc Python ném `KeyError: 'interests'` khiến luồng ReAct bị văng out dừng đột ngột.

### 2. Log Source
Trích đoạn nhật ký lỗi từ `logs/trace_eval.md` & terminal execution:

```text
[Action]: calculate_compatibility({"person_a": "C001"})
[Tool Error Traceback]: KeyError: 'person_b' in tools/compatibility.py line 98
[Status]: ReAct Loop Crashed - Uncaught Exception in Tool Execution
```

### 3. Diagnosis
Nguyên nhân do LLM khi tự sinh Action có thể không tuân thủ 100% định dạng Pydantic object hoặc thiếu thông tin tham số. Hàm tool ban đầu chưa có cơ chế ép kiểu an toàn (defensive type parsing) và chưa bọc ngoại lệ cẩn thận, dẫn đến việc ngoại lệ Python bị đẩy thẳng lên vòng lặp ReAct chính.

### 4. Solution
Là Tool Engineer, tôi đã nâng cấp defensive programming cho cả 2 tool:
1. Cho phép `calculate_compatibility` tiếp nhận linh hoạt cả `dict` thô lẫn `UserProfile` instance, tự động lookup từ `MOCK_CANDIDATE_DB` nếu LLM chỉ truyền mã ID (ví dụ: `"C001"`, `"C002"`).
2. Xử lý fallback cho các trường thông tin còn thiếu bằng giá trị mặc định hợp lý.
3. Bọc toàn bộ body của tool trong khối `try-except Exception as e`, trả về định dạng thông báo lỗi dạng text rõ ràng: `{"status": "error", "message": "LỖI THAM SỐ: Thiếu thông tin person_b. Vui lòng hỏi thêm người dùng."}`.
4. Sau khi sửa, khi LLM truyền tham số lỗi, Observation nhận được thông báo lỗi chi tiết, giúp Agent suy luận tiếp `Thought` để hỏi làm rõ người dùng thay vì crash ứng dụng.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Khối `Thought` giúp Agent suy luận rõ ràng trước khi quyết định gọi tool. Khi so sánh với Chatbot Baseline (Level 2) - vốn chỉ đưa ra câu trả lời lý thuyết chung chung ("Hãy dùng app hẹn hò"), ReAct Agent (Level 3) có thể tự phân tích intent, chuẩn bị đúng tham số và kích hoạt `calculate_compatibility` để tính ra điểm số thực tế **69.2/100** kèm phân tích chi tiết.
2. **Reliability**: Cơ chế mã nguồn trong Tool giúp đảm bảo tính nhất quán (Deterministic). Chatbot thuần LLM dễ bị ảo giác (hallucination) khi đưa ra con số ngẫu nhiên, trong khi Tool của tôi đảm bảo ma trận điểm số và bộ lọc an toàn (PII Masking, Hard Filter) chạy chính xác 100% theo logic thuật toán đã định.
3. **Observation**: Phản hồi từ môi trường (Observation) chính là căn cứ thực tế (Grounding) duy nhất cho LLM. Khi tool `search_candidates` trả về `is_relaxed_search = True`, Agent dựa vào Observation này để thành thật giải thích với người dùng rằng hệ thống đã mở rộng tiêu chí tìm kiếm, tạo niềm tin và tính minh bạch cho AI.

---

## IV. Future Improvements (5 Points)

- **Production Vector Database**: Chuyển đổi `MOCK_CANDIDATE_DB` từ mảng in-memory sang cơ sở dữ liệu Vector chuyên dụng (Qdrant, Milvus hoặc Pinecone) kết hợp HNSW Indexing để hỗ trợ tìm kiếm ngữ nghĩa hàng triệu hồ sơ với độ trễ < 10ms.
- **Dynamic PII Masking Engine**: Nâng cấp Guardrail bảo mật thông tin cá nhân bằng cách tích hợp Microsoft Presidio hoặc spaCy NER model để tự động nhận diện và che mờ PII phức tạp (địa chỉ nhà, tài khoản mạng xã hội, email) trước khi trả dữ liệu về LLM.
- **Asynchronous Execution & Caching**: Áp dụng `async/await` cho các hàm tính embedding và truy vấn DB, đồng thời dùng Redis Cache lưu kết quả tính tương thích giữa các cặp hồ sơ phổ biến nhằm tối ưu chi phí API và thời gian phản hồi.
- **Native Function Calling**: Phối hợp với Role 3 để chuyển từ regex text-parsing Action sang cơ chế Native Function Calling API của Gemini / OpenAI, giúp loại bỏ hoàn toàn lỗi syntax khi truyền tham số tool.

---