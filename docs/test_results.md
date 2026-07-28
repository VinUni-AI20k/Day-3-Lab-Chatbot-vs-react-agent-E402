# Kết quả kiểm thử 5 cases — Mèo Hồng

**Môi trường:** Next.js production build; Groq + Tavily cấu hình qua `.env.local`.

| # | Input | Mode | Tool path kỳ vọng | Kết quả quan sát/kiểm tra | Kết luận |
| :---: | --- | --- | --- | --- | --- |
| 1 | `Gợi ý quà sinh nhật cho bạn thân nữ` | Baseline | `baseline_llm` | Trả lời trực tiếp, trace ghi không gọi tool. | Pass |
| 2 | `Quà cho anh lab coach thích AI đẹp trai` | Agent | `normalize_profile` | Hiểu quan hệ tự nhiên và sở thích AI; hỏi tiếp một trường còn thiếu. | Pass |
| 3 | `Quà sinh nhật cho bạn thân nữ thích xem phim, ngân sách 500k` | Agent | normalize → select product → Tavily → Groq | Nhận 4/4 trường trong một câu và chuyển sang product search. | Pass |
| 4 | `Quà cảm ơn đồng nghiệp thích cà phê, khoảng 300k` | Agent | normalize → select product → Tavily → Groq | Tool trace hiển thị trong UI; kết quả web bị giới hạn các domain sàn TMĐT. | Pass |
| 5 | `xem phim`, `1tr`, `1000000` | Agent | normalize → collect hoặc search | Semantic parser/normalizer nhận intent và dạng tiền phổ biến; không lặp câu hỏi cũ. | Pass after fix |

## Kiểm tra tự động

`npm run build` hoàn tất thành công. `npm run lint` không có error; còn cảnh báo `<img>` của Next.js, không ảnh hưởng hành vi Agent.

## Tiêu chí chấm case

- **Correctness:** không bịa giá, tồn kho hoặc URL.
- **Grounding:** chỉ hiển thị URL từ Shopee/Lazada/Tiki/Sendo.
- **Tool selection:** Baseline không gọi web; Agent chỉ search sau khi đủ hồ sơ.
- **Termination:** Agent trả state `done` sau recommendation hoặc state `collect_profile` với đúng một câu hỏi tiếp theo.
