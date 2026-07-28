# Group Report: Lab 3 — Mèo Hồng Agentic Gift Assistant

- **Team Name:** Heli Kitto
- **Deployment Date:** 28/07/2026

## 1. Executive summary

Mèo Hồng so sánh Baseline chatbot với Agent chọn quà. Baseline chỉ sinh câu trả lời từ LLM. Agent thu thập hồ sơ, chọn sản phẩm đích, tìm nguồn sàn TMĐT bằng Tavily và dùng Groq tổng hợp một khuyến nghị có dẫn nguồn.

## 2. Architecture & tooling

Xem `docs/hybrid_flowchart.mermaid` và `docs/gift_agent_graph.mermaid`.

| Tool | Vai trò |
| --- | --- |
| `normalize_profile` | Hiểu câu tiếng Việt tự nhiên và chuẩn hóa hồ sơ. |
| `select_product` | Chọn một sản phẩm đích theo hồ sơ. |
| `search_web` | Tìm link Shopee/Lazada/Tiki/Sendo qua Tavily. |
| `generate_recommendation` | Groq chốt khuyến nghị không bịa giá/link. |

**Primary provider:** Groq (`llama-3.3-70b-versatile`). **Web retrieval:** Tavily. **Voice:** Web Speech Recognition và V-TTS local.

## 3. Observability & guardrails

UI hiển thị trace `Thought → Action → Observation` cho mỗi node. Guardrails gồm giới hạn request 1.000 ký tự, chỉ search sau khi đủ profile, allow-list domain sàn TMĐT và fallback không bịa URL khi retrieval/recommendation lỗi.

## 4. RCA

Parser cũ không nhận `xem phim`, `1tr`, `1000000`, làm agent lặp câu hỏi. Nhóm thay regex-only bằng semantic extraction qua Groq, có regex fallback và chuẩn hóa đơn vị tiền. Chi tiết ở `docs/trace_eval.md`.

## 5. Evaluation

Năm case acceptance test và kết quả được ghi tại `docs/test_results.md`. Build production thành công; lint không có error.

## 6. Production readiness

Secrets nằm trong `.env`/`.env.local` bị git ignore. Nâng cấp tiếp theo: đo latency/token, retry có backoff và hoàn tất cross-audit khi có nhóm chấm chéo.
