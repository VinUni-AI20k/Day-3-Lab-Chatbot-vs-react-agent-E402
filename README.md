# 🤖 AI Recruitment Agent

**Agent sàng lọc CV và điều phối phỏng vấn** — Hệ thống AI Agent tự động hóa quy trình tuyển dụng từ nhận CV đến lên lịch phỏng vấn.

---

## 🏗️ Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────┐
│                    FastAPI REST API                       │
│  POST /api/v1/screen  │  GET /api/v1/runs/{id}           │
│  GET  /api/v1/candidates/{id}  │  GET /api/v1/jobs/{id}  │
└───────────────┬──────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────┐
│              RecruitmentWorkflow                          │
│         (State Machine — LangGraph-style)                │
│                                                          │
│  validate → parse_cv → get_jd → normalize                │
│       → score_match ──┬── [PASS] → check_calendar        │
│                       │       → select_slot               │
│                       │       → book_interview            │
│                       │       → generate_confirmation     │
│                       └── [REJECT] → rejection_email      │
└───────────────┬──────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────┐
│  Tool Layer (tools.py)     │  LLM Adapter (providers.py) │
│  parse_cv, get_jd,        │  Gemini / OpenAI /           │
│  score_candidate,         │  Anthropic / OpenRouter /    │
│  check_calendar,          │  Mock (offline)              │
│  book_interview_slot      │                              │
└──────────────────────────────────────────────────────────┘
```

### Quy trình nghiệp vụ

```
Nhận CV + Job ID
→ Phân tích CV (parse_cv)
→ Lấy JD (get_jd)
→ Chuẩn hóa dữ liệu
→ Đối sánh & chấm điểm (score_candidate)
→ PASS hoặc REJECT

PASS:
→ Kiểm tra lịch (check_calendar)
→ Chọn slot sớm nhất
→ Đặt lịch (book_interview_slot)
→ Tạo email xác nhận phỏng vấn

REJECT:
→ Tạo email từ chối lịch sự
```

---

## 📂 Cấu trúc dự án

```
📁 AI-Recruitment-Agent/
├── 📄 README.md
├── 📄 .env.example               ← Cấu hình API keys & server
├── 📄 requirements.txt           ← Dependencies
├── 📄 Dockerfile                 ← Container image
├── 📄 docker-compose.yml         ← Docker orchestration
│
├── 📁 config/
│   └── 📄 test_cases.json        ← 5 test cases thử thách Agent
│
├── 📁 src/
│   ├── 📄 api.py                 ← FastAPI REST API
│   ├── 📄 app.py                 ← ReAct Agent CLI (Interactive + Batch)
│   ├── 📄 tools.py               ← 5 tool functions (mock data)
│   ├── 📄 prompts.py             ← ReAct System Prompt + Guardrails
│   ├── 📄 providers.py           ← Multi-provider LLM adapter
│   └── 📁 recruitment/
│       ├── 📄 models.py          ← Pydantic models (AgentState, etc.)
│       ├── 📄 workflow.py        ← State machine workflow engine
│       └── 📄 tracing.py         ← Structured logging & observability
│
├── 📁 tests/
│   ├── 📄 conftest.py            ← Shared fixtures
│   ├── 📄 test_tools.py          ← Tool unit tests
│   ├── 📄 test_models.py         ← Pydantic model tests
│   ├── 📄 test_workflow.py       ← Workflow state machine tests
│   └── 📄 test_api.py            ← FastAPI integration tests
│
└── 📁 docs/
    ├── 📄 CODELAB.md
    ├── 📄 trace_eval.md           ← Observability trace logs
    └── 📄 PHAN_CONG_CONG_VIEC.md
```

---

## 🚀 Cài đặt & Chạy

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

```bash
cp .env.example .env
# Sửa file .env: điền API key và chọn LLM_PROVIDER
```

### 3. Chạy API Server

```bash
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

API docs tự động: http://localhost:8000/docs

### 4. Chạy ReAct Agent (CLI)

```bash
# Interactive mode
python -m src.app

# Batch test (chạy tất cả test cases)
python -m src.app --test

# Workflow demo (deterministic, không cần LLM)
python -m src.app --workflow
```

### 5. Chạy với Docker

```bash
docker compose up --build
# API available at http://localhost:8000
```

---

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|:--|:--|:--|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/screen` | Sàng lọc ứng viên (full pipeline) |
| `GET` | `/api/v1/runs/{run_id}` | Lấy kết quả run |
| `GET` | `/api/v1/candidates/{id}` | Tra cứu CV ứng viên |
| `GET` | `/api/v1/jobs/{id}` | Tra cứu JD vị trí |

### Ví dụ gọi API

```bash
# Sàng lọc ứng viên
curl -X POST http://localhost:8000/api/v1/screen \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "candidate_001",
    "job_id": "python_backend",
    "interviewer_id": "interviewer_001",
    "interview_date": "2026-08-01"
  }'
```

Response mẫu:
```json
{
  "run_id": "abc-123",
  "status": "COMPLETED",
  "decision": "PASS",
  "total_score": 100,
  "decision_summary": "Ứng viên candidate_001 ĐẠT với 100/100 điểm...",
  "email_draft": "Kính gửi Nguyễn Văn An, Chúc mừng! ..."
}
```

---

## 🧪 Testing

```bash
# Chạy tất cả tests
pytest tests/ -v

# Chạy với coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Chạy riêng từng test suite
pytest tests/test_tools.py -v       # Tool unit tests
pytest tests/test_models.py -v      # Pydantic model tests
pytest tests/test_workflow.py -v    # Workflow tests
pytest tests/test_api.py -v         # API integration tests
```

---

## 🛡️ Guardrails & Safety

1. **Input Guardrail**: Kiểm duyệt đầu vào chống prompt injection, out-of-scope, bias/discrimination
2. **Output Guardrail**: Lọc thông tin kỹ thuật nội bộ khỏi câu trả lời
3. **Max Iterations**: Giới hạn 8 vòng lặp ReAct (chống infinite loop)
4. **Safe Identifiers**: Chặn path traversal trong candidate_id, job_id
5. **Retry Logic**: Tự động retry cho lỗi tạm thời (calendar, booking)

---

## 🔧 Tech Stack

| Thành phần | Công nghệ |
|:--|:--|
| Language | Python 3.12 |
| API Framework | FastAPI |
| Data Validation | Pydantic v2 |
| LLM Integration | Google Gemini / OpenAI / Anthropic / OpenRouter |
| Agent Pattern | ReAct (Thought → Action → Observation) |
| Workflow Engine | State Machine (LangGraph-style, pure Python) |
| Testing | pytest + httpx |
| Container | Docker |
| Observability | Structured JSON logging + Trace export |

---

## 👥 Nhóm phát triển

| Vai trò | Người đảm nhận |
|:--|:--|
| Product Architect (Role 1) | Vũ Tú Quỳnh 01239 |
| Tool Engineer (Role 2) | Nguyễn Ngọc Nam 01561 |
| Prompt Engineer (Role 3) | Nguyễn Trần Ngọc Thắng 01163 |
| Core Developer (Role 4) | Nguyễn Hoàng Biên 01233 |
| Observability (Role 5) | Vũ Nguyễn Quốc Đạt 01199 |
