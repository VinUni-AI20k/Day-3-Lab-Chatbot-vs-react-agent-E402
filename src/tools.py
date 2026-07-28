"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Trợ lý đặt vé xem phim CGV — đọc dữ liệu suất chiếu/ghế từ config/movies_cache.json
(read-only, do Role 2 crawl/soạn tay) và ghi đơn đặt vé mô phỏng vào config/bookings_local.json.
Xem sơ đồ dữ liệu & luồng thực thi đầy đủ tại docs/PROJECT_PLAN.md (mục 3-5).
"""

import json
import os
import re
import uuid
from datetime import datetime
from langchain_core.tools import tool

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(_BASE_DIR, "config", "movies_cache.json")

def load_movies():
    return _load_cache()

def save_movies(data):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

BOOKINGS_PATH = os.path.join(_BASE_DIR, "config", "bookings_local.json")

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
_STOPWORDS = {"phim", "va", "và", "the", "a", "an"}


# --------------------------------------------------------------------------
# Helpers nội bộ (không expose cho Agent)
# --------------------------------------------------------------------------

def _load_cache() -> list:
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _load_bookings() -> list:
    if not os.path.exists(BOOKINGS_PATH):
        os.makedirs(os.path.dirname(BOOKINGS_PATH), exist_ok=True)
        with open(BOOKINGS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(BOOKINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def _append_booking(record: dict) -> None:
    bookings = _load_bookings()
    bookings.append(record)
    with open(BOOKINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(bookings, f, ensure_ascii=False, indent=2)


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _tokenize(text: str) -> set:
    normalized = _normalize(text).replace("&", " ")
    tokens = re.findall(r"[^\W\d_]+", normalized, flags=re.UNICODE)
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 1}


def _find_film(films: list, film_name: str):
    """Khớp phim theo tên: chính xác -> chứa chuỗi con -> trùng phần lớn từ khóa
    (giúp nhận diện tên series/thương hiệu viết tắt, VD 'Conan' hoặc khác biệt
    dấu nối như 'và' so với '&')."""
    query_norm = _normalize(film_name)
    for f in films:
        if _normalize(f.get("film_name", "")) == query_norm:
            return f
    for f in films:
        name_norm = _normalize(f.get("film_name", ""))
        if query_norm and (query_norm in name_norm or name_norm in query_norm):
            return f
    query_tokens = _tokenize(film_name)
    if query_tokens:
        best, best_score = None, 0.0
        for f in films:
            name_tokens = _tokenize(f.get("film_name", ""))
            if not name_tokens:
                continue
            score = len(query_tokens & name_tokens) / len(query_tokens)
            if score > best_score:
                best, best_score = f, score
        if best_score >= 0.6:
            return best
    return None


def _valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _find_showtimes(film: dict, cinema: str = None, date: str = None, time: str = None) -> list:
    cinema_norm = _normalize(cinema) if cinema else None
    results = []
    for st in film.get("showtimes", []):
        if cinema_norm and cinema_norm not in _normalize(st.get("cinema", "")):
            continue
        if date and st.get("date") != date:
            continue
        if time and st.get("time") != time:
            continue
        results.append(st)
    return results


def _parse_cols(cols_spec, cols_per_row: int) -> list:
    if not cols_spec:
        return list(range(1, cols_per_row + 1))
    cols = []
    for part in str(cols_spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-")
            cols.extend(range(int(start), int(end) + 1))
        else:
            cols.append(int(part))
    return cols


def _expand_zone_seats(zone: dict, cols_per_row: int) -> list:
    cols = _parse_cols(zone.get("cols"), cols_per_row)
    return [f"{row}{col}" for row in zone.get("rows", []) for col in cols]


def _zone_available_seats(film_name: str, showtime: dict, zone: dict) -> list:
    """Ghế trống thực tế = ghế trong zone trừ booked_seats gốc (từ cache) trừ
    tiếp các ghế đã đặt qua book_ticket ghi trong bookings_local.json — tính động,
    không sửa file cache (xem docs/PROJECT_PLAN.md mục 5)."""
    seat_map = showtime["seat_map"]
    all_seats = _expand_zone_seats(zone, seat_map.get("cols_per_row", 12))
    taken = set(seat_map.get("booked_seats", []))
    combined_time = f"{showtime.get('date', '')} {showtime.get('time', '')}".strip()
    for booking in _load_bookings():
        if (
            _normalize(booking.get("film_name")) == _normalize(film_name)
            and _normalize(booking.get("cinema")) == _normalize(showtime.get("cinema"))
            and booking.get("time") == combined_time
            and _normalize(booking.get("zone")) == _normalize(zone.get("zone"))
        ):
            taken.update(booking.get("seat_ids", []))
    return [s for s in all_seats if s not in taken]


# --------------------------------------------------------------------------
# Tools expose cho ReAct Agent
# --------------------------------------------------------------------------

def search_now_showing_films(keyword: str = None) -> str:
    """
    Liệt kê phim đang chiếu tại CGV (đọc từ movies_cache.json), lọc theo tên
    phim hoặc thể loại nếu có từ khóa.

    Args:
        keyword (str, optional): Tên phim hoặc thể loại cần tìm (VD: 'Conan', 'hành động').

    Returns:
        str: Danh sách phim khớp (tên + thể loại), hoặc chuỗi lỗi bắt đầu bằng 'LỖI:'.
    """
    films = _load_cache()
    if not films:
        return "LỖI: Không có dữ liệu phim trong movies_cache.json (cache rỗng hoặc chưa crawl)."

    if not keyword or not keyword.strip():
        matched = films
    else:
        kw_norm = _normalize(keyword)
        kw_tokens = _tokenize(keyword)
        matched = []
        for f in films:
            name_norm = _normalize(f.get("film_name", ""))
            genre_norm = _normalize(f.get("genre", ""))
            if kw_norm in name_norm or kw_norm in genre_norm:
                matched.append(f)
            elif kw_tokens and (kw_tokens & _tokenize(f.get("film_name", "")) or kw_tokens & _tokenize(f.get("genre", ""))):
                matched.append(f)

    if not matched:
        return f"LỖI: Không tìm thấy phim nào khớp với từ khóa '{keyword}' đang chiếu tại CGV."

    lines = [f"- {f['film_name']} ({f.get('genre', 'Chưa rõ thể loại')})" for f in matched]
    return "🎬 Phim đang chiếu tại CGV:\n" + "\n".join(lines)


def get_film_details(film_name: str) -> str:
    """
    Lấy mô tả nội dung, thời lượng và nhãn độ tuổi của một phim.

    Args:
        film_name (str): Tên phim cần tra cứu (VD: 'Odyssey').

    Returns:
        str: Chi tiết phim, hoặc chuỗi lỗi bắt đầu bằng 'LỖI:'.
    """
    films = _load_cache()
    if not films:
        return "LỖI: Không có dữ liệu phim trong movies_cache.json (cache rỗng hoặc chưa crawl)."

    film = _find_film(films, film_name)
    if not film:
        return f"LỖI: Không tìm thấy phim '{film_name}' đang chiếu tại CGV."

    lines = [
        f"🎬 {film['film_name']}",
        f"Thể loại: {film.get('genre', 'Chưa rõ')}",
        f"Thời lượng: {film.get('duration_min', '?')} phút",
        f"Nhãn độ tuổi: {film.get('rating_description') or film.get('rating', 'Chưa rõ')}",
    ]
    if film.get("director"):
        lines.append(f"Đạo diễn: {film['director']}")
    if film.get("cast"):
        lines.append(f"Diễn viên: {film['cast']}")
    lines.append(f"Nội dung: {film.get('synopsis', 'Chưa có mô tả.')}")
    return "\n".join(lines)

@tool
def search_movie(movie_name: str):
    """
    Tìm thông tin phim.
    """
    movies = load_movies()
    for movie in movies:
        if movie_name.lower() in movie["film_name"].lower():
            return {
                "film_name": movie["film_name"],
                "genre": movie["genre"],
                "duration": movie["duration_min"],
                "rating": movie["rating"],
                "poster": movie["poster_path"],
                "synopsis": movie["synopsis"]
            }
    return "Không tìm thấy phim."

def get_showtimes(film_name: str, cinema: str = None, date: str = None) -> str:
    """
    Tra cứu suất chiếu của một phim, có thể lọc theo rạp và/hoặc ngày.

    Args:
        film_name (str): Tên phim.
        cinema (str, optional): Tên rạp (khớp gần đúng, VD 'CGV' khớp mọi chi nhánh).
        date (str, optional): Ngày chiếu định dạng 'YYYY-MM-DD'.

    Returns:
        str: Danh sách suất chiếu (rạp, ngày, giờ, số ghế trống), hoặc chuỗi lỗi bắt đầu bằng 'LỖI:'.
    """
    films = _load_cache()
    if not films:
        return "LỖI: Không có dữ liệu phim trong movies_cache.json (cache rỗng hoặc chưa crawl)."

    film = _find_film(films, film_name)
    if not film:
        return f"LỖI: Không tìm thấy phim '{film_name}' đang chiếu tại CGV."

    if date and not _valid_date(date):
        return f"LỖI: Ngày '{date}' không hợp lệ. Định dạng đúng là YYYY-MM-DD và phải là ngày có thật trên lịch."

    showtimes = _find_showtimes(film, cinema=cinema, date=date)
    if not showtimes:
        scope = ""
        if cinema:
            scope += f" tại '{cinema}'"
        if date:
            scope += f" ngày '{date}'"
        return f"LỖI: Không tìm thấy suất chiếu nào cho phim '{film['film_name']}'{scope}."

    lines = []
    for st in showtimes:
        seats = st.get("seats_available", 0)
        status = f"{seats} ghế trống" if seats > 0 else "đã hết vé"
        lines.append(f"- {st['cinema']} | {st['date']} {st['time']} | {status}")
    return f"🎬 Suất chiếu phim '{film['film_name']}':\n" + "\n".join(lines)


def get_seat_map(film_name: str, cinema: str, time: str) -> str:
    """
    Tra cứu sơ đồ khu vực ghế (zone) của một suất chiếu cụ thể, kèm giá và số
    ghế trống thực tế theo từng zone (đã trừ ghế đã đặt qua book_ticket).

    Args:
        film_name (str): Tên phim.
        cinema (str): Tên rạp (khớp gần đúng).
        time (str): Giờ chiếu định dạng 'HH:MM'.

    Returns:
        str: Danh sách zone kèm giá + số ghế trống, hoặc chuỗi lỗi bắt đầu bằng 'LỖI:'.
    """
    films = _load_cache()
    if not films:
        return "LỖI: Không có dữ liệu phim trong movies_cache.json (cache rỗng hoặc chưa crawl)."

    film = _find_film(films, film_name)
    if not film:
        return f"LỖI: Không tìm thấy phim '{film_name}' đang chiếu tại CGV."

    if not time or not _TIME_RE.match(time.strip()):
        return f"LỖI: Giờ chiếu '{time}' không hợp lệ. Định dạng đúng là HH:MM (00:00-23:59)."

    showtimes = _find_showtimes(film, cinema=cinema, time=time.strip())
    if not showtimes:
        available_times = sorted({st["time"] for st in _find_showtimes(film, cinema=cinema)})
        hint = f" Các giờ chiếu thực tế: {', '.join(available_times)}." if available_times else ""
        return f"LỖI: Không tìm thấy suất chiếu phim '{film['film_name']}' tại '{cinema}' lúc '{time}'.{hint}"

    showtime = showtimes[0]
    seat_map = showtime.get("seat_map")
    if not seat_map:
        return f"LỖI: Suất chiếu '{film['film_name']}' tại '{showtime['cinema']}' lúc '{time}' đã hết vé hoặc không có sơ đồ ghế."

    lines = []
    for zone in seat_map.get("zones", []):
        available = _zone_available_seats(film["film_name"], showtime, zone)
        lines.append(f"- {zone['zone']}: {len(available)} ghế trống, giá {zone.get('price', 0):,}đ")
    return f"🎬 Sơ đồ ghế '{film['film_name']}' tại {showtime['cinema']} lúc {time}:\n" + "\n".join(lines)


def book_ticket(film_name: str, cinema: str, time: str, zone: str, quantity: int) -> str:
    """
    Đặt vé mô phỏng (DEMO, không phải giao dịch thật): tự gán `quantity` ghế
    trống đầu tiên trong `zone` yêu cầu, ghi vào bookings_local.json.

    Args:
        film_name (str): Tên phim.
        cinema (str): Tên rạp (khớp gần đúng).
        time (str): Giờ chiếu định dạng 'HH:MM'.
        zone (str): Loại ghế, phải khớp đúng tên trong seat_map.zones.
        quantity (int): Số vé muốn đặt, 1-10.

    Returns:
        str: Xác nhận đặt vé kèm mã ghế + tổng tiền + mã đặt vé, hoặc chuỗi lỗi bắt đầu bằng 'LỖI:'.
    """
    films = _load_cache()
    if not films:
        return "LỖI: Không có dữ liệu phim trong movies_cache.json (cache rỗng hoặc chưa crawl)."

    film = _find_film(films, film_name)
    if not film:
        return f"LỖI: Không tìm thấy phim '{film_name}' đang chiếu tại CGV."

    if not time or not _TIME_RE.match(time.strip()):
        return f"LỖI: Giờ chiếu '{time}' không hợp lệ. Định dạng đúng là HH:MM (00:00-23:59)."

    showtimes = _find_showtimes(film, cinema=cinema, time=time.strip())
    if not showtimes:
        return f"LỖI: Không tìm thấy suất chiếu phim '{film['film_name']}' tại '{cinema}' lúc '{time}'."

    showtime = showtimes[0]
    seat_map = showtime.get("seat_map")
    if not seat_map:
        return f"LỖI: Suất chiếu '{film['film_name']}' tại '{showtime['cinema']}' lúc '{time}' đã hết vé hoặc không có sơ đồ ghế để đặt."

    zone_info = next(
        (z for z in seat_map.get("zones", []) if _normalize(z.get("zone")) == _normalize(zone)), None
    )
    if not zone_info:
        valid_zones = [z["zone"] for z in seat_map.get("zones", [])]
        return f"LỖI: Không có loại ghế '{zone}'. Các loại hợp lệ: {valid_zones}."

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return f"LỖI: Số vé '{quantity}' không hợp lệ (phải là số nguyên từ 1-10)."
    if quantity <= 0 or quantity > 10:
        return "LỖI: Số vé không hợp lệ (chỉ được đặt 1-10 vé/lần)."

    available = _zone_available_seats(film["film_name"], showtime, zone_info)
    if quantity > len(available):
        return f"LỖI: Zone '{zone_info['zone']}' chỉ còn {len(available)} ghế trống, không đủ cho {quantity} vé."

    assigned = available[:quantity]
    total_price = quantity * zone_info.get("price", 0)
    booking_id = f"BK{datetime.now():%Y%m%d-%H%M%S}"
    combined_time = f"{showtime.get('date', '')} {showtime.get('time', '')}".strip()

    _append_booking({
        "booking_id": booking_id,
        "film_name": film["film_name"],
        "cinema": showtime["cinema"],
        "time": combined_time,
        "zone": zone_info["zone"],
        "seat_ids": assigned,
        "quantity": quantity,
        "total_price": total_price,
        "booked_at": datetime.now().isoformat(),
        "status": "CONFIRMED (DEMO)",
    })

    return (
        f"✅ [DEMO] Đặt thành công {quantity} vé '{zone_info['zone']}' ({', '.join(assigned)}) "
        f"phim '{film['film_name']}' suất {time} tại {showtime['cinema']}. "
        f"Tổng tiền: {total_price:,}đ. Mã đặt vé: {booking_id}."
    )

@tool
def search_theater(location: str = ""):
    """
    Tìm rạp CGV theo tên hoặc khu vực.
    """
    films = _load_cache()
    cinemas = set()
    kw = _normalize(location)
    for f in films:
        for st in f.get("showtimes", []):
            name = st.get("cinema", "")
            if not kw or kw in _normalize(name):
                cinemas.add(name)
    return sorted(list(cinemas))

@tool
def search_movie(movie_name: str):
    """
    Tìm phim theo tên hoặc một phần tên.
    """
    films = _load_cache()
    
    # If query is empty or generic, return all movies in cache
    q = _normalize(movie_name)
    if not q or q in ["", "phim", "all", "các phim", "đang chiếu", "cgv"]:
        return [
            {
                "film_name": f["film_name"],
                "genre": f.get("genre", "Chưa rõ"),
                "duration_min": f.get("duration_min", 0),
                "rating": f.get("rating", "P"),
                "poster_path": f.get("poster_path", ""),
                "status": "Đang chiếu"
            }
            for f in films
        ]
        
    film = _find_film(films, movie_name)
    if not film:
        # Check partial match on all movies
        matched = [f for f in films if q in _normalize(f.get("film_name", ""))]
        if len(matched) > 0:
            if len(matched) == 1:
                film = matched[0]
            else:
                return [
                    {
                        "film_name": f["film_name"],
                        "genre": f.get("genre", "Chưa rõ"),
                        "duration_min": f.get("duration_min", 0),
                        "rating": f.get("rating", "P"),
                        "poster_path": f.get("poster_path", ""),
                        "status": "Đang chiếu"
                    }
                    for f in matched
                ]

    if not film:
        return "LỖI: Không tìm thấy phim."
        
    return {
        "film_name": film["film_name"],
        "genre": film.get("genre", "Chưa rõ"),
        "duration_min": film.get("duration_min", 0),
        "rating": film.get("rating", "P"),
        "poster_path": film.get("poster_path", ""),
        "synopsis": film.get("synopsis", "Chưa có mô tả."),
        "status": "Đang chiếu"
    }

@tool
def search_showtime(movie_name: str, cinema: str = "", date: str = ""):
    """
    Tìm suất chiếu của phim.
    """
    films = _load_cache()
    film = _find_film(films, movie_name)
    if not film:
        return f"LỖI: Không tìm thấy phim '{movie_name}'."
    
    if not date:
        date = "2026-07-28"  # Default cache date
        
    showtimes = _find_showtimes(film, cinema=cinema, date=date)
    return [
        {
            "cinema": st["cinema"],
            "date": st["date"],
            "time": st["time"],
            "seats_available": st["seats_available"]
        }
        for st in showtimes
    ]

@tool
def get_available_seats(movie_name: str, cinema: str, time: str):
    """
    Lấy sơ đồ khu vực ghế còn trống và giá của một suất chiếu.
    """
    films = _load_cache()
    film = _find_film(films, movie_name)
    if not film:
        return f"LỖI: Không tìm thấy phim '{movie_name}'."
        
    showtimes = _find_showtimes(film, cinema=cinema, time=time)
    if not showtimes:
        return f"LỖI: Không tìm thấy suất chiếu lúc {time} tại {cinema}."
        
    showtime = showtimes[0]
    seat_map = showtime.get("seat_map")
    if not seat_map:
        return "LỖI: Không có sơ đồ ghế cho suất chiếu này."
        
    zones_info = []
    for zone in seat_map.get("zones", []):
        avail = _zone_available_seats(film["film_name"], showtime, zone)
        zones_info.append({
            "zone": zone["zone"],
            "price": zone["price"],
            "seats_available": len(avail)
        })
        
    return {
        "rows": seat_map.get("rows", []),
        "cols_per_row": seat_map.get("cols_per_row", 12),
        "zones": zones_info
    }

@tool
def book_seats(movie_name: str, cinema: str, time: str, zone: str, quantity: int):
    """
    Đặt/giữ ghế MÔ PHỎNG cho một suất chiếu.
    """
    films = _load_cache()
    film = _find_film(films, movie_name)
    if not film:
        return {"status": "FAILED", "message": f"LỖI: Không tìm thấy phim '{movie_name}'."}
        
    showtimes = _find_showtimes(film, cinema=cinema, time=time)
    if not showtimes:
        return {"status": "FAILED", "message": f"LỖI: Không tìm thấy suất chiếu lúc {time} tại {cinema}."}
        
    showtime = showtimes[0]
    seat_map = showtime.get("seat_map")
    if not seat_map:
        return {"status": "FAILED", "message": "LỖI: Không có sơ đồ ghế."}
        
    zone_info = next(
        (z for z in seat_map.get("zones", []) if _normalize(z.get("zone")) == _normalize(zone)), None
    )
    if not zone_info:
        valid_zones = [z["zone"] for z in seat_map.get("zones", [])]
        return {"status": "FAILED", "message": f"LỖI: Không có loại ghế '{zone}'. Các loại hợp lệ: {valid_zones}."}
        
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"status": "FAILED", "message": "LỖI: Số vé không hợp lệ."}
        
    if quantity <= 0 or quantity > 10:
        return {"status": "FAILED", "message": "LỖI: Số vé không hợp lệ (chỉ được đặt 1-10 vé/lần)."}
        
    available = _zone_available_seats(film["film_name"], showtime, zone_info)
    if quantity > len(available):
        return {"status": "FAILED", "message": f"LỖI: Zone '{zone_info['zone']}' chỉ còn {len(available)} ghế trống."}
        
    assigned = available[:quantity]
    total_price = quantity * zone_info.get("price", 0)
    booking_id = f"BK{datetime.now():%Y%m%d-%H%M%S}"
    combined_time = f"{showtime.get('date', '')} {showtime.get('time', '')}".strip()
    
    _append_booking({
        "booking_id": booking_id,
        "film_name": film["film_name"],
        "cinema": showtime["cinema"],
        "time": combined_time,
        "zone": zone_info["zone"],
        "seat_ids": assigned,
        "quantity": quantity,
        "total_price": total_price,
        "booked_at": datetime.now().isoformat(),
        "status": "CONFIRMED (DEMO)"
    })
    
    return {
        "status": "SUCCESS",
        "booking_id": booking_id,
        "movie": film["film_name"],
        "cinema": showtime["cinema"],
        "date": showtime.get("date", "2026-07-28"),
        "time": showtime.get("time", ""),
        "zone": zone_info["zone"],
        "seats": assigned,
        "customer": "Khách hàng",
        "total_price": total_price
    }

@tool
def generate_ticket(booking_id: str):
    """
    Sinh vé điện tử MÔ PHỎNG sau khi book_seats thành công.
    """
    bookings = _load_bookings()
    booking = next((b for b in bookings if b.get("booking_id") == booking_id), None)
    if not booking:
        return f"LỖI: Không tìm thấy giao dịch đặt vé với mã '{booking_id}'."
        
    ticket_id = f"CGV-{uuid.uuid4().hex[:8].upper()}"
    time_str = booking.get("time", "")
    parts = time_str.split(" ")
    date = parts[0] if len(parts) > 0 else "2026-07-28"
    time = parts[1] if len(parts) > 1 else ""
    
    return {
        "ticket_id": ticket_id,
        "booking_id": booking_id,
        "customer": booking.get("customer", "Khách hàng"),
        "movie": booking.get("film_name", ""),
        "cinema": booking.get("cinema", ""),
        "date": date,
        "time": time,
        "seats": booking.get("seat_ids", []),
        "status": "CONFIRMED",
        "qr_code": f"QR-{ticket_id}"
    }

AVAILABLE_TOOLS = [
    search_theater,
    search_movie,
    search_showtime,
    get_available_seats,
    book_seats,
    generate_ticket
]
