# DỰ ÁN AI MATCHMAKING AGENT - MASTER PROMPT & SYSTEM ARCHITECTURE
> Document Version: 1.0  
> Target Environment: AntiGravity IDE / Cursor / AI Code Assistant  
> Stack: Python 3.10+ | LangChain / OpenAI SDK / Pydantic | SentenceTransformers / OpenAI Embeddings

---

## 1. KHÁI QUÁT HỆ THỐNG & YÊU CẦU KIẾN TRÚC

Hệ thống **AI Matchmaking Agent** bao gồm:
1. **LLM Orchestrator (Agent Core)**: Quản lý hội thoại, kiểm tra thiếu/đủ thông tin (**Interactive Information Gathering Loop**), gọi Tool (Tool Calling) và sinh câu trả lời tự nhiên.
2. **Guardrail Framework**: Ngăn ngừa lặp vô hạn (Infinite Loop Protection), giới hạn số lần retry/tool call (Execution Limits), kiểm tra an toàn dữ liệu riêng tư (PII Redaction) và kiểm soát lỗi đầu vào/đầu ra.
3. **Tool 1: `calculate_compatibility`**: Đánh giá độ tương thích giữa 2 hồ sơ cụ thể dựa trên ma trận điểm số đa tiêu chí (Weighted Scoring + Vector Embedding cho sở thích).
4. **Tool 2: `search_candidates`**: Tìm kiếm danh sách đối tượng phù hợp dựa trên tiêu chí tìm kiếm bằng cơ chế **Hybrid Search** (Hard Filter + Semantic Vector Search).

---

## 2. MASTER SYSTEM PROMPT (Dán vào `.cursorrules` hoặc Prompt Tổng Của Agent)

```markdown
Bạn là một Senior AI System Architect & Lead Engineer. Nhiệm vụ của bạn là xây dựng hệ thống **"AI Agent Ghép Đôi & Đánh Giá Tương Thích"** hoàn chỉnh, hoạt động theo chuẩn Production-grade.

### A. QUY TRÌNH XỬ LÝ VÀ VÒNG LẶP HỎI THÔNG TIN (INFORMATION GATHERING LOOP)
1. **Phân tích Ý định (Intent Analysis)**:
   - Ý định 1: Tìm gợi ý ghép đôi (`SEARCH`).
   - Ý định 2: Đánh giá độ tương thích giữa 2 người (`COMPATIBILITY`).
2. **Kiểm tra Thông tin Thiếu (Missing Parameter Check)**:
   - Trước khi gọi bất kỳ Tool nào, kiểm tra xem người dùng đã cung cấp đủ thông tin bắt buộc chưa.
   - Nếu **THIẾU** thông tin bắt buộc:
     * **KHÔNG ĐƯỢC GỌI TOOL**.
     * Giữ nguyên context, đặt câu hỏi làm rõ (Slot-filling) một cách lịch sự, tự nhiên. Mỗi lượt chỉ hỏi tối đa 1-2 thông tin còn thiếu quan trọng nhất để tránh làm phiền người dùng.
     * Tiếp tục lặp lại quá trình hỏi cho đến khi thu thập đủ thông tin cần thiết.
   - Các tham số bắt buộc:
     * Khi `SEARCH`: Giới tính mong muốn, Độ tuổi (hoặc khoảng tuổi), Vị trí (Tỉnh/Thành), Sở thích/Mong muốn tiêu biểu.
     * Khi `COMPATIBILITY`: Định danh/Thông tin đầy đủ của cả 2 đối tượng (Tên/ID, Giới tính, Độ tuổi, Vị trí, Học vấn, Nghề nghiệp, Sở thích).

### B. SYSTEM GUARDRAILS & CHỐNG LẶP (SAFETY & EXECUTION CONTROLS)
1. **Max Iterations / Loop Limits**:
   - Tối đa **5 lượt tương tác (turns)** cho quá trình thu thập thông tin còn thiếu. Nếu sau 5 lượt vẫn chưa đủ thông tin, Agent phải đưa ra gợi ý mặc định hoặc yêu cầu nhập lại từ đầu.
   - Tối đa **3 lần gọi Tool (Tool Call Limit)** trong 1 lượt xử lý đơn. Nếu Tool trả về lỗi quá 3 lần, fallback về thông báo lỗi thân thiện.
2. **Tool Repetition Prevention**:
   - Nghiêm cấm gọi lại cùng một Tool với chính xác bộ tham số (arguments) cũ hơn 1 lần trong cùng một phiên xử lý.
3. **Guardrail An toàn & Quyền riêng tư (PII & Content Safety)**:
   - Masking toàn bộ Số điện thoại (ví dụ: `0912***678`) và Họ của tên đầy đủ khi trả về danh sách gợi ý.
   - Không xử lý hoặc đưa ra đánh giá phân biệt đối xử, xúc phạm hoặc nội dung độc hại.

### C. DỮ LIỆU ĐẦU VÀO (User Profile Data Schema)
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class UserProfile(BaseModel):
    id: str = Field(..., description="Mã định danh duy nhất")
    name: str = Field(..., description="Tên người dùng")
    phone: str = Field(..., description="Số điện thoại")
    gender: str = Field(..., description="Nam / Nữ / Khác")
    age: int = Field(..., description="Tuổi")
    location: str = Field(..., description="Tỉnh / Thành phố")
    height_cm: int = Field(..., description="Chiều cao tính theo cm")
    education: str = Field(..., description="Trình độ học vấn (VD: Đại học, Thạc sĩ...)")
    occupation: str = Field(..., description="Nghề nghiệp hiện tại")
    interests: str = Field(..., description="Mô tả chi tiết sở thích, lối sống")
```


---

## 3. PROMPT THIẾT KẾ TOOL 1: `calculate_compatibility`

```markdown
Hãy khởi tạo file `tools/compatibility.py` triển khai Tool 1 cho hệ thống.

### MỤC TIÊU
Tính toán điểm số tương thích toàn diện giữa 2 đối tượng `Person A` và `Person B` dựa trên ma trận trọng số (Thang điểm 100).

### YÊU CẦU THUẬT TOÁN & BẢO VỆ
1. **Hard Filter (Giới tính & Định hướng)**:
   - Nếu giới tính/định hướng không phù hợp (VD: Cả 2 cùng là Nam/Nữ và không phải mối quan hệ đồng giới mong muốn) -> Trả về `total_score = 0` ngay lập tức kèm giải thích.
2. **Vị trí địa lý (Trọng số 20%)**:
   - Cùng Tỉnh/Thành: 20 điểm.
   - Cùng vùng miền (VD: Hà Nội - Bắc Ninh): 10 điểm.
   - Khác vùng miền xa: 0 điểm.
3. **Độ tuổi & Chiều cao (Trọng số 20%)**:
   - Tuổi: Độ lệch 0-3 tuổi (10đ), 4-6 tuổi (6đ), >6 tuổi (2đ).
   - Chiều cao: Nam cao hơn Nữ từ 5cm - 20cm (10đ), bằng/thấp hơn hoặc lệch quá xa (3đ).
4. **Sở thích (Trọng số 40% - Vector Embedding)**:
   - Sử dụng model Text Embedding (`sentence-transformers/all-MiniLM-L6-v2` hoặc `text-embedding-3-small`).
   - Tính Cosine Similarity giữa `interests` của Person A và Person B.
   - Điểm sở thích = `Cosine_Similarity * 40`.
5. **Học vấn & Nghề nghiệp (Trọng số 20%)**:
   - Cùng trình độ học vấn hoặc ngành nghề bổ trợ cho nhau: 20đ; khác biệt vừa phải: 10đ.

### STRUCTURED OUTPUT (Pydantic Model)
```python
class CompatibilityResult(BaseModel):
    total_score: float = Field(..., description="Tổng điểm tương thích từ 0 - 100")
    breakdown: dict = Field(..., description="Chi tiết điểm số từng tiêu chí")
    strengths: List[str] = Field(..., description="Các điểm hợp nhau nhất")
    weaknesses: List[str] = Field(..., description="Các điểm chưa đồng điệu")
    summary: str = Field(..., description="Đánh giá ngắn gọn 2-3 câu từ AI Matchmaker")
```

Hãy viết mã nguồn Python hoàn chỉnh, xử lý đầy đủ Try-Except, bao gồm unit test với mock data.


---

## 4. PROMPT THIẾT KẾ TOOL 2: `search_candidates`

```markdown
Hãy khởi tạo file `tools/search.py` triển khai Tool 2 cho hệ thống.

### MỤC TIÊU
Tìm kiếm top $K$ người phù hợp nhất từ Database dựa trên truy vấn tìm kiếm của người dùng.

### YÊU CẦU XỬ LÝ & GUARDRAILS
1. **Hard Filtering (Tiền lọc)**:
   - Lọc theo Giới tính (`gender`), Khoảng tuổi (`min_age`, `max_age`), Tỉnh/Thành (`location`).
   - Loại bỏ các ứng viên không thỏa điều kiện lọc cứng trước khi tính điểm vector.
2. **Hybrid Semantic Ranking (Xếp hạng lai)**:
   - Tính Cosine Similarity giữa câu mô tả mong muốn của người dùng (`search_query_interests`) với `interests` của từng candidate trong DB.
3. **Privacy Masking Guardrail**:
   - Tự động ẩn Số điện thoại: `0912345678` -> `0912***678`.
   - Tự động ẩn Họ tên: "Nguyễn Văn A" -> "Văn A" hoặc "Anh/Chị V.A".
4. **Empty Results Guardrail**:
   - Nếu không tìm thấy ứng viên thỏa mãn Hard Filter, không trả về mảng rỗng mà tự động nới lỏng bán kính vị trí hoặc khoảng tuổi và gắn nhãn `is_relaxed_search = True`.

### STRUCTURED OUTPUT (Pydantic Model)
```python
class CandidateMatch(BaseModel):
    masked_name: str
    masked_phone: str
    age: int
    location: str
    occupation: str
    interests_highlight: str
    match_score: float

class SearchResponse(BaseModel):
    candidates: List[CandidateMatch]
    total_found: int
    is_relaxed_search: bool
    note: Optional[str] = None
```

Hãy tạo mock Database gồm 15-20 hồ sơ đa dạng sở thích để test và viết hàm `search_candidates` chuẩn hóa.


---

## 5. PROMPT XÂY DỰNG AGENT AGGREGATOR & INTERACTIVE LOOP (`agent.py`)

```markdown
Hãy khởi tạo file `agent.py` tích hợp toàn bộ hệ thống AI Agent ghép đôi.

### YÊU CẦU KIẾN TRÚC & GUARDRAILS TÍCH HỢP

```python
# CẤU HÌNH GUARDRAILS CHÍNH
MAX_INFO_GATHERING_TURNS = 5  # Giới hạn số lượt hỏi bổ sung thông tin
MAX_TOOL_CALLS_PER_TURN = 3   # Tối đa số lần gọi tool mỗi lượt
```

### LUỒNG THI HÀNH (WORKFLOW FLOWCHART LOGIC)
1. **Bước 1**: Nhận `user_input` và `conversation_history`.
2. **Bước 2 (State & Guardrail Check)**:
   - Tăng `turn_count` lên 1.
   - Nếu `turn_count > MAX_INFO_GATHERING_TURNS`: Buộc Agent dừng hỏi, dùng thông tin hiện có để tìm kiếm gần đúng nhất hoặc thông báo yêu cầu làm mới hội thoại.
3. **Bước 3 (Intent & Slot Extraction)**:
   - Dùng LLM trích xuất intent (`SEARCH` / `COMPATIBILITY`) và các tham số hiện có.
   - Kiểm tra các tham số còn thiếu đối với intent tương ứng.
4. **Bước 4 (Conditional Branching)**:
   - **TRƯỜNG HỢP THIẾU PARAMETER**: Trả về câu hỏi slot-filling tinh tế cho người dùng. CHƯA GỌI TOOL.
   - **TRƯỜNG HỢP ĐỦ PARAMETER**:
     * Thực thi Tool tương ứng (`calculate_compatibility` hoặc `search_candidates`).
     * Kiểm tra `tool_call_count`. Nếu gọi thất bại quá `MAX_TOOL_CALLS_PER_TURN` -> Kích hoạt Fallback Response.
5. **Bước 5 (Persona Formatting)**:
   - LLM đóng vai "Bà Mối AI" tinh tế, ấm áp, văn phong tự nhiên có biểu cảm emoji, tổng hợp thông tin trả về từ Tool thành lời khuyên/gợi ý hoàn chỉnh.

Hãy viết trọn vẹn mã nguồn `agent.py` dạng Interactive CLI Loop (`while True:`) để tôi có thể test trực tiếp bằng bàn phím trong terminal!