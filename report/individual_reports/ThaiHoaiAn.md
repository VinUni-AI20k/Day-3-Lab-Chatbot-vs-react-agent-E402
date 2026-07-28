# Individual Report: Lab 3 — Mèo Hồng

- **Student Name:** Thái Hoài An
- **Student ID:** 2A202601862
- **Date:** 28/07/2026

## I. Technical contribution

Tôi triển khai Agent graph cho Mèo Hồng tại `frontend-next/src/lib/gift-agent.ts`, API route `api/gift-agent`, cùng UI chuyển Baseline/Agent. Graph có các tool `normalize_profile`, `select_product`, `search_web` (Tavily) và `generate_recommendation` (Groq). UI hiển thị trace Thought–Action–Observation và chỉ giữ nguồn từ sàn TMĐT allow-list.

## II. Debugging case study

**Sự cố:** `xem phim`, `1tr`, `1000000` không được parser regex nhận diện; Agent lặp câu hỏi nên không gọi web search.

**Nguyên nhân:** regex thiếu intent và định dạng ngân sách phổ biến; điều kiện profile đủ không bao giờ đạt.

**Cách xử lý:** thêm semantic extraction qua Groq, regex fallback, intent AI/phim và chuẩn hóa đơn vị tiền. Trace và RCA chi tiết ở `docs/trace_eval.md`.

## III. Insight: Baseline vs ReAct

Baseline cho phản hồi mượt nhưng không có bằng chứng giá/link thời gian thực. Agent chậm hơn do nhiều tool calls, đổi lại có thể chọn sản phẩm đích, kiểm tra nguồn sàn TMĐT và dừng an toàn khi dữ liệu chưa đủ. Observation từ từng tool quyết định bước kế tiếp, đặc biệt search chỉ diễn ra sau khi profile hoàn chỉnh.

## IV. Future improvements

- Ghi latency, token và chi phí cho từng node graph.
- Thêm retry/backoff, cache kết quả tìm kiếm và đánh giá chất lượng URL sản phẩm.
- Hoàn tất cross-audit với nhóm khác theo `docs/cross_audit.md`.
