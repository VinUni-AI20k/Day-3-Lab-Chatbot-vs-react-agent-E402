Các tools sử dụng trong AI Agent:
search_theater()          # Tìm rạp CGV
search_movie()            # Tìm phim đang chiếu
search_showtime()         # Tìm suất chiếu
get_available_seats()     # Lấy danh sách ghế trống
book_seats()              # Đặt/giữ ghế
generate_ticket()         # Sinh vé điện tử

> Quy ước chung: mọi tool trả về lỗi dưới dạng **chuỗi bắt đầu bằng `"LỖI: ..."`** (không raise exception), để Agent luôn có Observation để suy luận tiếp thay vì crash.

## search_theater()
Tìm rạp CGV
Mục đích:
    Tìm danh sách rạp CGV phù hợp với yêu cầu của người dùng.
Sử dụng để:
    Xác định rạp người dùng muốn xem.
    Lấy theater_id để tìm suất chiếu.

**Input:**

- `keyword` (str, optional): Tên rạp hoặc khu vực (VD: `"Vincom"`, `"Quận 1"`, `"Hà Nội"`). Bỏ trống → trả về toàn bộ danh sách rạp.

**Output (thành công):**

```json
[
  {"theater_id": "CGV_VCBT", "name": "CGV Vincom Bà Triệu", "address": "191 Bà Triệu, Hai Bà Trưng, Hà Nội"},
  {"theater_id": "CGV_LM81", "name": "CGV Landmark 81", "address": "720A Điện Biên Phủ, Bình Thạnh, TP.HCM"}
]
```

**Output (lỗi):** `"LỖI: Không tìm thấy rạp CGV nào phù hợp với '<keyword>'."`

## search_movie()
Tìm phim đang chiếu / sắp chiếu
Mục đích:
    Tìm thông tin phim theo tên.
Sử dụng để:
    Kiểm tra phim có tồn tại không.
    Lấy ID phim.
    Biết trạng thái:
    Đang chiếu
    Sắp chiếu
    Đã hết suất

**Input:**

- `keyword` (str, required): Tên phim hoặc một phần tên (VD: `"Avatar 3"`, `"Conan"`).

**Output (thành công):**

```json
[
  {"movie_id": "AVT3", "film_name": "Avatar 3", "genre": "Khoa học viễn tưởng", "status": "Đang chiếu"}
]
```

**Output (lỗi):** `"LỖI: Không tìm thấy phim nào khớp với '<keyword>' đang/sắp chiếu tại CGV."`

## search_showtime()
Tìm suất chiếu
Mục đích:
    Tìm thời gian chiếu của phim tại một rạp cụ thể.
Sử dụng để:
    Trả lời:
    "Phim Conan có suất nào?"
    hoặc:
    "Tối nay có chiếu lúc mấy giờ?"

**Input:**

- `film_name` (str, required): Tên phim (VD: `"Avatar 3"`).
- `cinema` (str, optional): Tên rạp cụ thể (VD: `"CGV Vincom Bà Triệu"`). Bỏ trống → tìm ở mọi rạp.
- `date` (str, optional, `YYYY-MM-DD`): Ngày chiếu. Bỏ trống → mặc định ngày hôm nay.

**Output (thành công):**

```json
[
  {"cinema": "CGV Vincom Bà Triệu", "date": "2026-07-28", "time": "19:00", "seats_available": 42},
  {"cinema": "CGV Landmark 81", "date": "2026-07-28", "time": "20:15", "seats_available": 0}
]
```

**Output (lỗi):** `"LỖI: Không tìm thấy suất chiếu nào cho phim '<film_name>' tại '<cinema>' ngày '<date>'."`

## get_available_seats()
Lấy danh sách ghế trống
Mục đích:
    Kiểm tra những ghế nào còn có thể đặt.

**Input:**

- `film_name` (str, required): Tên phim.
- `cinema` (str, required): Tên rạp.
- `time` (str, required, `HH:MM`): Giờ chiếu của suất cần kiểm tra.

**Output (thành công):** Sơ đồ ghế theo khu vực (zone), kèm giá và số ghế trống — ghế đã đặt (kể cả qua `book_seats`) đã được loại trừ.

```json
{
  "rows": ["A", "B", "C", "D", "E", "F", "G", "H"],
  "cols_per_row": 12,
  "zones": [
    {"zone": "Thường - Gần màn hình", "price": 60000, "seats_available": 30},
    {"zone": "VIP - Trung tâm", "price": 95000, "seats_available": 20},
    {"zone": "Thường - Cạnh loa", "price": 70000, "seats_available": 22},
    {"zone": "Sweetbox - Ghế đôi", "price": 150000, "seats_available": 3}
  ]
}
```

**Output (lỗi):** `"LỖI: Suất chiếu '<film_name>' tại '<cinema>' lúc '<time>' đã hết ghế hoặc không có sơ đồ ghế."`

## book_seats()
Đặt hoặc giữ ghế
Mục đích:
    Thực hiện hành động đặt vé.
Sử dụng để:
    Khóa ghế tránh người khác đặt.
    Tạo mã booking.

**Input:**

- `film_name` (str, required): Tên phim.
- `cinema` (str, required): Tên rạp.
- `time` (str, required, `HH:MM`): Giờ chiếu.
- `zone` (str, required): Loại ghế, phải khớp đúng tên trong `get_available_seats()` (VD: `"VIP - Trung tâm"`).
- `quantity` (int, required, `1 ≤ quantity ≤ 10`): Số vé muốn đặt.

**Output (thành công):** Xác nhận đặt vé mô phỏng (DEMO, không phải giao dịch thật) kèm mã ghế cụ thể + tổng tiền.

```json
{
  "booking_id": "BK20260728-193045",
  "film_name": "Avatar 3",
  "cinema": "CGV Vincom Bà Triệu",
  "time": "19:00",
  "zone": "VIP - Trung tâm",
  "seat_ids": ["D3", "D4"],
  "quantity": 2,
  "total_price": 190000,
  "status": "CONFIRMED (DEMO)"
}
```

**Output (lỗi), một trong các trường hợp:**

- `"LỖI: Không có loại ghế '<zone>'. Các loại hợp lệ: [...]."`
- `"LỖI: Số vé không hợp lệ (chỉ được đặt 1-10 vé/lần)."`
- `"LỖI: Zone '<zone>' chỉ còn <n> ghế trống, không đủ cho <quantity> vé."`

## generate_ticket()
Sinh vé điện tử
Mục đích:
    Tạo vé sau khi đặt thành công.
Sử dụng để:
    Hiển thị vé.

**Input:**

- `booking_id` (str, required): Mã đặt vé trả về từ `book_seats()` (VD: `"BK20260728-193045"`).

**Output (thành công):**

```json
{
  "ticket_id": "TCK-BK20260728-193045",
  "film_name": "Avatar 3",
  "cinema": "CGV Vincom Bà Triệu",
  "time": "2026-07-28 19:00",
  "seat_ids": ["D3", "D4"],
  "total_price": 190000,
  "qr_code": "<base64-encoded-QR-placeholder>",
  "note": "[DEMO] Vé mô phỏng, không có giá trị sử dụng thực tế."
}
```

**Output (lỗi):** `"LỖI: Không tìm thấy đơn đặt vé với booking_id '<booking_id>'."`
