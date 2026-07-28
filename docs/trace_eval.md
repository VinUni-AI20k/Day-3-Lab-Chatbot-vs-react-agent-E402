# Trace & đánh giá — Mèo Hồng

## Agentic fit

| Tiêu chí | Điểm | Lý do |
| --- | ---: | --- |
| Multi-step reasoning | 5/5 | Trích xuất hồ sơ, kiểm tra điều kiện, tìm và xếp hạng quà. |
| Tool interaction | 5/5 | Bắt buộc gọi completeness, search và rank khi dữ liệu đủ. |
| Dynamic decision | 5/5 | Mỗi lượt chọn một câu hỏi còn thiếu hoặc chuyển sang catalog. |
| Long horizon | 4/5 | State theo phiên, cập nhật dần và có giới hạn 6 lượt. |
| Tổng | 19/20 | Phù hợp cho ReAct/state machine. |

## Trace mẫu: thiếu ngân sách

```text
User: Tìm quà sinh nhật cho đồng nghiệp thích cà phê.
Action: get_profile_completeness(profile)
Observation: missing_fields=[budget_max]
Final (user-visible): Ngân sách tối đa bạn dự kiến khoảng bao nhiêu...?

User: Khoảng 400 nghìn.
Action: get_profile_completeness(profile) -> complete
Action: search_gifts(profile)
Observation: Bộ cà phê drip thủ công, 320.000đ
Action: rank_gifts(profile, candidates)
Final: 1. Bộ cà phê drip thủ công — 320.000đ: hợp sở thích cà phê...
```

`Thought/Action/Observation` là trace nội bộ phục vụ đánh giá; giao diện chỉ hiển thị follow-up hoặc câu trả lời cuối. Catalog là dữ liệu demo offline, không phải giá/tồn kho thời gian thực.
