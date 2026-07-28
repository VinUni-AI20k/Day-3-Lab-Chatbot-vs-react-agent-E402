# RentalFlow — Web app LangGraph

Ứng dụng web cho đề tài **Trợ lý tìm & đặt lịch xem nhà trọ / căn hộ cho thuê**.
Luồng được điều phối bằng LangGraph:

```text
parse_request → search_rentals → get_viewing_slots → booking_guard → finalize
```

## Chạy local

```bash
python -m pip install -r requirements.txt
streamlit run web_app.py
```

Mở URL Streamlit được in trong terminal (thường là `http://localhost:8501`).

## Các tính năng

- Lọc theo khu vực, ngân sách, số phòng ngủ và thú cưng.
- Hiển thị listing dạng card với giá, diện tích và tiện ích.
- Chọn listing rồi xem các khung giờ còn trống.
- Booking có checkbox xác nhận rõ ràng ở tầng giao diện.
- Trace LangGraph có thể mở trong phần “Xem trace LangGraph”.
- Dữ liệu demo deterministic trong `src/tools.py`, không phụ thuộc API ngoài.

## Lưu ý

Đây là demo học tập. `book_viewing` tạo mã xác nhận demo, chưa kết nối hệ
thống lịch hoặc thanh toán thật. Không đưa API key vào Git; giữ key trong `.env`.
