# 🎬 TRỢ LÝ ĐẶT VÉ XEM PHIM & KIỂM TRA SUẤT CHIẾU

> 📌 Đề tài nhóm chọn cho Bài Lab 3 (không nằm trong danh sách gợi ý `DANH_SACH_DE_TAI.md`). File này đóng vai trò README + Kế hoạch triển khai riêng cho đề tài, dùng song song với `PHAN_CONG_CONG_VIEC.md`.

---

## 1. 💡 Giới thiệu bài toán

**Đối tượng người dùng**: Khách muốn xem phim tại rạp, cần tra cứu suất chiếu, kiểm tra ghế trống và đặt vé nhanh qua chat thay vì mở app rạp phim.

**Vấn đề của Chatbot thường**: LLM không biết lịch chiếu thực tế (thay đổi theo ngày/rạp), không biết ghế nào còn trống, và không thể "thực hiện" hành động đặt vé — chỉ có thể trả lời chung chung hoặc bịa thông tin (ảo giác).

**Giải pháp**: ReAct Agent tra cứu dữ liệu suất chiếu/ghế trống qua Tool, suy luận nhiều bước, rồi thực hiện hành động đặt vé thay người dùng.

---

## 2. 🎯 Đánh giá Agentic Fit (nháp cho `docs/trace_eval.md`)

| Tiêu chí | Điểm (1-5) | Lý do |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Phải suy luận: tìm suất chiếu → kiểm tra ghế trống → chọn ghế → xác nhận đặt. |
| 🛠️ **Tool Interaction** | `5/5` | Bắt buộc tra cứu dữ liệu suất chiếu/ghế trống thời gian thực, không có sẵn trong LLM. |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả tool bước trước (VD: hết suất 19h) quyết định hành động bước sau (gợi ý suất khác). |
| ⏳ **Long Horizon** | `4/5` | Quy trình 3 bước tool + 1 bước xác nhận hành động, dài hơn use-case thời tiết mẫu. |
| **TỔNG ĐIỂM FIT** | **18/20** | **KẾT LUẬN: RẤT NÊN DÙNG REACT AGENT.** |

---

## 3. 🕷️ Nguồn dữ liệu: Crawl từ rạp CGV

**Nguồn**: CGV (`cgv.vn`).

**Chiến lược Pre-crawl (khuyến nghị đã chốt)**: Không crawl trực tiếp mỗi lần Agent trả lời (rủi ro chậm/site sập/đổi cấu trúc HTML giữa buổi demo). Thay vào đó:

1. Chạy script crawl **một lần trước buổi Lab** → lưu kết quả đã chuẩn hóa vào `config/movies_cache.json`.
2. Toàn bộ Tools trong `src/tools.py` chỉ **đọc từ file cache này**, không gọi mạng khi Agent đang chạy → nhanh, ổn định khi demo/chấm điểm.
3. Nếu muốn dữ liệu mới hơn, chạy lại script crawl và ghi đè cache — tách biệt hoàn toàn với vòng lặp ReAct.

**Chuẩn hóa dữ liệu**:

Vì các site rạp thật không lộ sơ đồ ghế chi tiết qua trang public (cần đăng nhập/session để thấy sơ đồ chọn ghế), phần `seat_map` bên dưới là **dữ liệu mô phỏng do nhóm tự soạn** dựa theo cách chia khu vực phổ biến ở rạp Việt Nam (Thường / VIP / Cạnh loa / Sweetbox), gắn vào mỗi suất chiếu đã crawl được. Phần `film_name/genre/duration_min/rating/synopsis/showtimes` (giờ chiếu, tổng ghế trống) là dữ liệu crawl thật.

```json
{
  "film_name": "Avatar 3",
  "genre": "Khoa học viễn tưởng",
  "duration_min": 150,
  "rating": "C13",
  "synopsis": "...",
  "showtimes": [
    {
      "cinema": "CGV Vincom Bà Triệu",
      "date": "2026-07-28",
      "time": "19:00",
      "seats_available": 42,
      "seat_map": {
        "rows": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "cols_per_row": 12,
        "zones": [
          {"zone": "Thường - Gần màn hình", "rows": ["A", "B", "C"], "price": 60000, "note": "Ngồi gần, phải ngước nhìn màn hình"},
          {"zone": "VIP - Trung tâm", "rows": ["D", "E", "F"], "cols": "3-10", "price": 95000, "note": "Vị trí đẹp nhất, hình & âm thanh cân bằng"},
          {"zone": "Thường - Cạnh loa", "rows": ["D", "E", "F", "G"], "cols": "1-2,11-12", "price": 70000, "note": "Gần loa surround hai bên, âm thanh to hơn"},
          {"zone": "Sweetbox - Ghế đôi", "rows": ["H"], "price": 150000, "note": "Ghế đôi liền kề, không tay vịn giữa, số lượng giới hạn"}
        ],
        "booked_seats": ["D5", "D6"]
      }
    },
    {"cinema": "CGV Landmark 81", "date": "2026-07-28", "time": "20:15", "seats_available": 0, "seat_map": null}
  ]
}
```

**Lưu ý tuân thủ khi crawl**: kiểm tra `robots.txt` của từng site, đặt `User-Agent` rõ ràng, giới hạn tần suất request (delay giữa các request), chỉ dùng cho mục đích học tập trong phạm vi Lab — không phát tán lại dữ liệu.

⚠️ **`book_ticket` sẽ là hành động MÔ PHỎNG (simulated), không phải giao dịch thật**: site CGV yêu cầu đăng nhập + thanh toán thật để đặt vé — tự động hóa việc này vượt phạm vi Lab (rủi ro pháp lý/vi phạm điều khoản dịch vụ). Tool `book_ticket` sẽ ghi nhận "đơn đặt vé" vào một file cục bộ (VD: `config/bookings_local.json`) và trả về xác nhận giả lập, có ghi chú rõ đây là demo.

## 4. 🛠️ Danh sách Tools (`src/tools.py`)

| Tool | Tham số | Mô tả | Trả về |
| :--- | :--- | :--- | :--- |
| `search_now_showing_films` | `keyword: str = None` | Liệt kê phim đang chiếu (đọc từ `movies_cache.json`), lọc theo tên nếu có | Danh sách phim + thể loại |
| `get_film_details` | `film_name: str` | Lấy mô tả, thời lượng, nhãn độ tuổi của phim | Chi tiết phim |
| `get_showtimes` | `film_name: str, cinema: str = None, date: str = None` | Tra cứu suất chiếu theo phim/rạp/ngày | Danh sách giờ chiếu + tổng số ghế trống |
| `get_seat_map` | `film_name: str, cinema: str, time: str` | Tra cứu sơ đồ khu vực ghế của 1 suất cụ thể | Danh sách zone (Thường/VIP/Cạnh loa/Sweetbox) kèm giá + số ghế trống theo từng zone |
| `book_ticket` | `film_name: str, cinema: str, time: str, zone: str, quantity: int` | Đặt vé mô phỏng: tự chọn `quantity` ghế trống trong `zone` yêu cầu, ghi vào `bookings_local.json` | Xác nhận đặt vé kèm mã ghế cụ thể + tổng tiền (demo) |

**Failure modes cần xử lý (Role 3)**:

- Phim không có trong cache (không đang chiếu / crawl chưa cập nhật).
- Suất chiếu đã hết ghế → tool trả về lỗi, Agent phải gợi ý suất khác thay vì crash.
- Tên `zone` không tồn tại (VD gõ sai "Ghế Vip" thay vì "VIP - Trung tâm") → tool trả lỗi kèm danh sách zone hợp lệ.
- Zone cụ thể hết ghế (VD Sweetbox chỉ có 3 cặp, khách xin 5 vé) dù suất phim nhìn chung vẫn còn ghế zone khác.
- Cache rỗng/thiếu file hoặc suất không có `seat_map` (VD suất đã hết vé từ khi crawl) → tool trả lỗi rõ ràng thay vì crash toàn bộ app.

---

## 5. 🎟️ Cơ chế thực thi Đặt Vé (Booking Execution Mechanism)

Không thể (và không nên) tự động đăng nhập + thanh toán thật trên CGV thay người dùng — vượt phạm vi Lab và có rủi ro pháp lý/vi phạm điều khoản dịch vụ. `book_ticket` mô phỏng một hệ thống đặt vé nội bộ, tách biệt hoàn toàn khỏi dữ liệu crawl gốc.

**Nguyên tắc thiết kế**:

- `config/movies_cache.json` (dữ liệu crawl + `seat_map` mô phỏng) luôn **read-only** trong lúc Agent chạy — không bị ghi đè bởi hành động đặt vé, để giữ tính tái lập khi test/chấm điểm.
- Ghế trống **thực tế theo từng zone** = ghế trong `zone.rows`/`zone.cols` của `seat_map`, trừ đi `booked_seats` gốc (từ cache) và trừ tiếp các ghế đã đặt qua `book_ticket` được ghi trong `config/bookings_local.json` (tính động lúc gọi tool, không sửa file cache).
- Người dùng chọn theo **loại chỗ ngồi** (`zone`: *Thường - Gần màn hình* / *VIP - Trung tâm* / *Thường - Cạnh loa* / *Sweetbox - Ghế đôi*) thay vì phải tự chọn mã ghế cụ thể — tool tự gán ghế trống đầu tiên còn trống trong zone đó. Việc này giúp câu lệnh chat tự nhiên hơn (VD: *"đặt 2 vé gần màn hình"*) và tránh Agent phải suy luận toạ độ ghế.

**Luồng thực thi từng bước**:

1. Agent gọi `get_showtimes` để xác nhận suất chiếu tồn tại.
2. Agent gọi `get_seat_map(film_name, cinema, time)` để xem các zone và số ghế trống mỗi zone — dùng khi người dùng hỏi "còn ghế gần màn hình/VIP/cạnh loa/đôi không?" hoặc khi cần gợi ý zone phù hợp.
3. Agent gọi `book_ticket(film_name, cinema, time, zone, quantity)`.
4. Tool tự validate (không dựa vào LLM để kiểm tra logic):
   - Suất chiếu có tồn tại trong `movies_cache.json` và có `seat_map`? Không → trả lỗi.
   - `zone` có khớp đúng tên trong `seat_map.zones`? Không → trả lỗi kèm danh sách zone hợp lệ.
   - `0 < quantity ≤ 10` (chặn case bẫy "đặt 100 vé")? Không → trả lỗi.
   - Số ghế trống thực tế trong đúng zone đó ≥ `quantity`? Không → trả lỗi kèm số ghế còn lại **của zone đó** (không phải tổng suất, vì các zone khác có thể vẫn còn).
5. Nếu hợp lệ: tự gán `quantity` mã ghế trống đầu tiên trong zone (VD `["D3", "D4"]`), tính `total_price = quantity × zone.price`, sinh `booking_id`, append record vào `config/bookings_local.json`, trả về chuỗi xác nhận ghi rõ **"[DEMO]"**.
6. Agent nhận Observation này → sinh `Final Answer` gửi người dùng, liệt kê mã ghế + tổng tiền + ghi chú demo.

**Định dạng `config/bookings_local.json`** (file rỗng `[]` lúc khởi tạo, được tool tự tạo nếu chưa có):

```json
[
  {
    "booking_id": "BK20260728-193045",
    "film_name": "Avatar 3",
    "cinema": "CGV Vincom Bà Triệu",
    "time": "2026-07-28 19:00",
    "zone": "Thường - Gần màn hình",
    "seat_ids": ["A3", "A4"],
    "quantity": 2,
    "total_price": 120000,
    "booked_at": "2026-07-28T19:05:12",
    "status": "CONFIRMED (DEMO)"
  }
]
```

**Pseudocode `book_ticket` (`src/tools.py`)**:

```python
def book_ticket(film_name: str, cinema: str, time: str, zone: str, quantity: int) -> str:
    showtime = find_showtime(movies_cache, film_name, cinema, time)
    if not showtime or not showtime.get("seat_map"):
        return f"LỖI: Không tìm thấy sơ đồ ghế cho suất {film_name} tại {cinema} lúc {time}."

    zone_info = next((z for z in showtime["seat_map"]["zones"] if z["zone"] == zone), None)
    if not zone_info:
        valid_zones = [z["zone"] for z in showtime["seat_map"]["zones"]]
        return f"LỖI: Không có loại ghế '{zone}'. Các loại hợp lệ: {valid_zones}."

    if quantity <= 0 or quantity > 10:
        return "LỖI: Số vé không hợp lệ (chỉ được đặt 1-10 vé/lần)."

    all_seats_in_zone = expand_seats(zone_info)  # VD ["A1".."A12"] theo rows/cols của zone
    taken = set(showtime["seat_map"]["booked_seats"])
    taken |= {s for b in load_bookings() if same_showtime(b, film_name, cinema, time) for s in b["seat_ids"]}
    available = [s for s in all_seats_in_zone if s not in taken]

    if quantity > len(available):
        return f"LỖI: Zone '{zone}' chỉ còn {len(available)} ghế trống, không đủ cho {quantity} vé."

    assigned = available[:quantity]
    total_price = quantity * zone_info["price"]
    booking_id = f"BK{datetime.now():%Y%m%d-%H%M%S}"
    append_booking({"booking_id": booking_id, "film_name": film_name, "cinema": cinema, "time": time,
                     "zone": zone, "seat_ids": assigned, "quantity": quantity, "total_price": total_price,
                     "booked_at": datetime.now().isoformat(), "status": "CONFIRMED (DEMO)"})
    return (f"✅ [DEMO] Đặt thành công {quantity} vé '{zone}' ({', '.join(assigned)}) phim '{film_name}' "
            f"suất {time} tại {cinema}. Tổng tiền: {total_price:,}đ. Mã đặt vé: {booking_id}.")
```

---

## 6. 🧪 Test Cases nháp (`config/test_cases.json`)

| # | Loại | Câu hỏi | Kỳ vọng |
| :---: | :--- | :--- | :--- |
| 1 | 🟢 Đơn giản | "Rạp CGV có những loại ghế nào?" | Trả lời trực tiếp từ kiến thức, không cần tool. |
| 2 | 🟢 Đơn giản | "Ghế Sweetbox khác gì ghế Thường?" | Trả lời trực tiếp từ kiến thức chung, không cần tool. |
| 3 | 🟡 Multi-step (1 tool) | "Phim Avatar 3 tối nay chiếu lúc mấy giờ ở CGV?" | Gọi `get_showtimes`. |
| 4 | 🟡 Multi-step (2-3 tools) | "Suất 19h phim Avatar 3 ở CGV còn ghế gần màn hình không? Đặt giúp tôi 2 vé loại đó." | Gọi `get_showtimes` → `get_seat_map` → `book_ticket(zone="Thường - Gần màn hình", quantity=2)`. |
| 5 | 🔴 Edge Case (Guardrail) | "Đặt giúp tôi 5 vé Sweetbox suất 19h phim Avatar 3 ở CGV." | Zone Sweetbox chỉ có ít ghế đôi (VD 6 ghế = 3 cặp) → không đủ cho 5 vé dù suất phim nói chung vẫn còn ghế zone khác → Tool báo lỗi rõ ràng, Guardrail ngắt sau `MAX_ITERATIONS` bước nếu Agent cứ thử lại, trả lời lịch sự (có thể gợi ý zone khác). |

---

## 7. 🛡️ Guardrails (`src/prompts.py`)

- `MAX_ITERATIONS = 3`: chặn Agent lặp vô hạn nếu tool liên tục lỗi.
- Tool luôn trả về **chuỗi lỗi** (không raise exception) khi phim/rạp/suất không hợp lệ, để Agent có Observation để suy luận tiếp thay vì crash.
- Prompt cần ép Agent xác nhận lại thông tin trước khi gọi `book_ticket` (tránh đặt nhầm suất/rạp).
- `book_ticket` tự validate số vé (1-10) và ghế trống thực tế trước khi ghi booking (xem mục 5) — không tin tưởng hoàn toàn vào suy luận của LLM cho phần logic nghiệp vụ.

---

## 8. ⏱️ Kế hoạch triển khai theo 4 Mốc

| Mốc | Thời lượng | Việc cần làm cho đề tài này | Role phụ trách |
| :---: | :---: | :--- | :--- |
| **1** | 20 phút | Chốt đề tài (xong ✅) + điền Scoring Matrix mục 2 vào `trace_eval.md` + liệt kê tools mục 4 | Role 1, Role 5, Role 2 |
| **2** | 30 phút | Viết script crawl CGV (mục 3) → sinh `config/movies_cache.json` + viết 5 test cases mục 6 vào `test_cases.json` + viết `CHATBOT_BASELINE_PROMPT` | Role 2, Role 1, Role 3 |
| **3** | 60 phút | Viết `REACT_SYSTEM_PROMPT` liệt kê tools + Guardrails mục 7 + Role 4 lắp ráp vòng lặp ReAct thật trong `app.py` (thay phần hardcode demo hiện tại), cài `book_ticket` theo cơ chế mục 5 | Role 3, Role 4 |
| **4** | 40 phút | Cross-Audit: nhóm bạn thử các câu bẫy (phim ảo, vé âm, quá số ghế) + vẽ `hybrid_flowchart.mermaid` (câu hỏi thông tin chung → Chatbot path; câu hỏi cần tra cứu/đặt vé → ReAct path) | Cả nhóm, Role 5 |

⚠️ Crawl CGV trong 30 phút (Mốc 2) khá gấp — nếu HTML phức tạp/site chặn bot, chuẩn bị sẵn phương án fallback: tự soạn `movies_cache.json` mẫu tay (5-6 phim) để không chặn tiến độ các Mốc sau, rồi crawl thật sau nếu còn thời gian.

---

## 9. 🔀 Hybrid Decision Flowchart (mô tả logic cho `docs/hybrid_flowchart.mermaid`)

- **Chatbot path**: câu hỏi chung chung, không cần dữ liệu thời gian thực (VD: loại ghế, quy định rạp).
- **ReAct Agent path**: câu hỏi cần tra cứu suất chiếu/ghế trống hoặc thực hiện đặt vé.
- **Guardrail fallback**: nếu quá `MAX_ITERATIONS` hoặc tool liên tục lỗi → trả lời an toàn, đề nghị người dùng liên hệ tổng đài.
