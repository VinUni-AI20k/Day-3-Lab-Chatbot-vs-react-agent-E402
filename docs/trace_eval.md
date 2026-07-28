# 📊 Trace & Đánh giá Agent — Mèo Hồng

> Artifact cho Role 5: Observability & Reviewer. Trace được trả về từ `POST /api/gift-agent` và hiển thị trong UI sau mỗi phản hồi Agent.

## 1. Agentic-fit scoring matrix

| Tiêu chí | Điểm | Lý do |
| --- | :---: | --- |
| Multi-step reasoning | 5/5 | Agent cần thu thập/chuẩn hóa hồ sơ, chọn sản phẩm đích, tìm web rồi tổng hợp. |
| Tool interaction | 5/5 | Tavily cung cấp nguồn sản phẩm; Groq dùng để hiểu ngôn ngữ tự nhiên và tạo khuyến nghị. |
| Dynamic decision | 4/5 | Thiếu trường hồ sơ thì chỉ hỏi một trường; đủ hồ sơ mới chuyển sang web search. |
| Long horizon | 4/5 | Luồng gồm 3–4 tool calls và có fallback khi search/recommendation lỗi. |
| **Tổng** | **18/20** | Bài toán phù hợp ReAct Agent hơn baseline chatbot. |

## 2. Tool inventory

| Tool | Action | Observation trả về |
| --- | --- | --- |
| `normalize_profile` | Trích xuất người nhận, dịp, sở thích, ngân sách từ câu tiếng Việt tự nhiên. | Hồ sơ có bao nhiêu/4 trường; hoặc câu hỏi tiếp theo. |
| `select_product` | Groq chọn một sản phẩm đích theo hồ sơ. | Cụm từ sản phẩm cụ thể dùng làm query. |
| `search_web` | Tavily search, giới hạn domain `shopee.vn`, `lazada.vn`, `tiki.vn`, `sendo.vn`. | Số URL sản phẩm hợp lệ từ sàn TMĐT. |
| `generate_recommendation` | Groq đối chiếu hồ sơ và nguồn. | Một sản phẩm nên mua, lý do, nguồn/link. |
| `baseline_llm` | Groq trả lời trực tiếp ở chế độ Baseline. | Phản hồi không có web search/tool calling. |

## 3. Trace thật — Agent path

**Input:** `Quà sinh nhật cho bạn thân nữ thích xem phim, ngân sách 500k`

**Mode:** `Agent`

| Step | Thought (tóm tắt quyết định) | Action | Observation |
| :---: | --- | --- | --- |
| 1 | Cần hiểu tự nhiên thông tin người dùng vừa cung cấp. | `normalize_profile(message, current_profile)` | Nhận đủ 4/4 trường: bạn thân, sinh nhật, xem phim, 500k. |
| 2 | Hồ sơ đã đủ, cần chọn một sản phẩm đích để tìm chính xác. | `select_product(profile)` | Groq trả về một cụm từ sản phẩm dành cho người thích xem phim trong ngân sách. |
| 3 | Cần kiểm tra các trang bán hàng thực tế. | `search_web(product, marketplaces)` | Tavily chỉ giữ kết quả thuộc Shopee/Lazada/Tiki/Sendo; UI hiển thị số kết quả hợp lệ. |
| 4 | Đã có hồ sơ và nguồn để chốt khuyến nghị. | `generate_recommendation(profile, product, sources)` | Trả về đúng một sản phẩm nên mua, lý do và các link nguồn. |

**Termination:** state `done` sau khi tạo khuyến nghị; không hỏi tiếp.

### Trace partial-profile

**Input:** `Quà cho anh lab coach thích AI đẹp trai`

| Thought | Action | Observation |
| --- | --- | --- |
| Cần hiểu câu nói tự nhiên và quan hệ không chuẩn. | `normalize_profile(...)` | Nhận người nhận `anh lab coach`, sở thích `AI/công nghệ`; chưa có dịp và ngân sách. |
| Hồ sơ chưa đủ để tìm sản phẩm chính xác. | `skip select_product`, `skip search_web`, `skip generate_recommendation` | Agent tạo một câu hỏi tự nhiên cho đúng trường còn thiếu; không phát sinh API search. |

## 4. So sánh Baseline và Agent

| Chế độ | Hành vi | Bằng chứng |
| --- | --- | --- |
| Baseline | Groq trả lời trực tiếp, không khẳng định giá/tồn kho thực tế. | Trace `baseline_llm → generate_text(message) → không gọi tool`. |
| Agent | Chuẩn hóa hồ sơ, search sàn TMĐT và grounded recommendation. | Trace 4 bước ở mục 3; có URL nguồn hiển thị trong UI. |

## 5. RCA — Parser lặp câu hỏi

### Sự cố

Người dùng nhập `xem phim` và sau đó `1tr` hoặc `1000000`, nhưng bot lặp lại câu hỏi về sở thích/ngân sách và không gọi Tavily.

### Root cause

Parser regex cũ không có intent `xem phim`; budget regex yêu cầu 2–4 chữ số kèm hậu tố, nên không nhận `1tr`, số tiền 7 chữ số hoặc câu nói tự nhiên. Điều kiện `Object.values(profile).every(Boolean)` không đạt nên graph bị giữ ở node `collect_profile`.

### Fix

1. Thay parser keyword-only bằng `normalize_profile` semantic extraction qua Groq, vẫn có regex fallback.
2. Bổ sung các intent như `xem phim`, `lười vận động`, `AI/công nghệ`.
3. Chuẩn hóa `1tr`, `1 triệu`, `500k`, `1000000`.
4. Cho phép `không vì dịp gì cả` được hiểu là `Tặng bất ngờ`.

### Kết quả sau fix

Với câu `Quà sinh nhật cho bạn thân nữ thích xem phim, ngân sách 500k`, Agent nhận đủ dữ liệu trong một lượt và đi thẳng đến `select_product → search_web → generate_recommendation`.

## 6. Guardrails & fallback

- Tin nhắn API giới hạn 1.000 ký tự.
- Chỉ giữ URL từ các sàn TMĐT đã allow-list; nguồn từ điển/translate bị loại ở server.
- Không đủ hồ sơ: skip tool tốn phí và hỏi đúng một trường thiếu.
- Tavily lỗi: trace ghi `error`, Agent tiếp tục tạo phản hồi thận trọng thay vì crash.
- Groq lỗi: state `error`, trả thông báo an toàn; không bịa link, giá hoặc tồn kho.
- UI mở/đóng được trace để quan sát `Thought → Action → Observation` cho từng tool call.

## 7. Verification

`npm run build` đã chạy thành công sau khi thêm Agent graph, Baseline/Agent switch, trace UI và semantic profile extraction. Lint chỉ còn cảnh báo tối ưu hóa `<img>`, không có error.
