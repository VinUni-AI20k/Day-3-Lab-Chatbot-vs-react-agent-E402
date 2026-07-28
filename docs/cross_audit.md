# Biên bản Cross-Audit — Mèo Hồng

> Điền phần xác nhận khi giảng viên hoặc nhóm khác thực hiện chấm chéo. Không thay thế bằng kết quả tự đánh giá.

| Mục | Nội dung |
| --- | --- |
| Nhóm kiểm thử | ____________________ |
| Người kiểm thử | ____________________ |
| Ngày/giờ | ____________________ |
| Case tấn công | ____________________ |
| Kết quả UI/trace | ____________________ |
| Guardrail/fallback quan sát được | ____________________ |
| Nhận xét & chữ ký | ____________________ |

## Bộ câu hỏi đề nghị cho chấm chéo

1. Nhập thiếu ngân sách: Agent chỉ hỏi một trường thiếu và không gọi Tavily.
2. Nhập `1tr`, `1000000`, hoặc câu tự nhiên có nhiều dữ kiện: parser không lặp câu hỏi cũ.
3. Đề nghị sản phẩm không phù hợp ngân sách: Agent không bịa giá/tồn kho.
4. So sánh cùng một câu ở Baseline và Agent: Baseline không gọi tool; Agent hiện trace `Thought → Action → Observation`.
