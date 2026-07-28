"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê

Đọc dữ liệu thật từ data/datamock.json (do Role 1 cung cấp), gồm các tin có
id dạng "PROP-0001", địa chỉ tách ward/district/city, trạng thái
(available/rented/maintenance), và viewing_slots là danh sách datetime ISO
riêng cho từng tin (không cố định giờ như bản demo cũ).

⚠️ Mọi hàm tool KHÔNG được để Exception văng ra ngoài. Lỗi tham số / không
tìm thấy dữ liệu phải trả về chuỗi bắt đầu bằng "LỖI:" để Agent đọc được.
"""

import os
import json
import re
import unicodedata
from datetime import datetime

# ============================================================
# 🗄️ NẠP DỮ LIỆU THẬT TỪ data/datamock.json
# ============================================================

_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "datamock.json",
)


def _load_rentals():
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


_RENTALS = _load_rentals()
_RENTALS_BY_ID = {r["id"]: r for r in _RENTALS}

# Lưu vết các giờ xem nhà đã được đặt: {rental_id: set(iso_datetime_string)}
_BOOKED_SLOTS = {}

# Lưu vết các booking đã tạo: {booking_id: {...thông tin...}}
_BOOKINGS = {}


def _normalize(text: str) -> str:
    return (text or "").lower().strip()


def _normalize_search_text(text: str) -> str:
    """Normalize accents, punctuation and common Vietnamese city aliases."""
    text = unicodedata.normalize("NFD", str(text or "").lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()

    aliases = (
        (r"\b(?:tp\s*hcm|tphcm|hcm|sai gon)\b", "ho chi minh"),
        (r"\b(?:tp\s*hn|hn)\b", "ha noi"),
        (r"\b(?:tp\s*dn)\b", "da nang"),
    )
    for pattern, replacement in aliases:
        text = re.sub(pattern, replacement, text)
    return re.sub(r"\s+", " ", text).strip()


def _is_valid_date(date: str):
    """Kiểm tra & parse ngày DD/MM/YYYY. Trả về (year, month, day) hoặc None."""
    try:
        parsed = datetime.strptime((date or "").strip(), "%d/%m/%Y")
    except (TypeError, ValueError):
        return None
    return parsed.year, parsed.month, parsed.day


def _is_valid_time(time: str) -> bool:
    return bool(re.match(r"^([01]\d|2[0-3]):[0-5]\d$", (time or "").strip()))


def _available_slots(rental: dict, date_tuple=None):
    """Lấy các viewing_slots còn trống của 1 tin, lọc theo ngày nếu có."""
    rental_id = rental["id"]
    booked = _BOOKED_SLOTS.get(rental_id, set())
    slots = [s for s in rental.get("viewing_slots", []) if s not in booked]
    if date_tuple:
        year, month, day = date_tuple
        prefix = f"{year:04d}-{month:02d}-{day:02d}T"
        slots = [s for s in slots if s.startswith(prefix)]
    return slots


# ============================================================
# 🛠️ TOOL 1: TÌM KIẾM NHÀ TRỌ / CĂN HỘ
# ============================================================

def search_rentals(
    location: str = None,
    max_price: float = None,
    room_type: str = None,
    min_price: float = None,
    amenities=None,
) -> str:
    """
    Tìm kiếm các tin đăng phòng trọ / căn hộ đang còn trống (status = available)
    theo khu vực (phường/quận/thành phố), mức giá tối đa và loại phòng.

    Args:
        location (str): Từ khoá khu vực (Ví dụ: 'Cầu Giấy', 'Quận 7', 'Đà Nẵng',
            'Mai Dịch'). So khớp với cả ward, district và city.
        max_price (float, optional): Mức giá thuê tối đa (VNĐ/tháng).
        room_type (str, optional): Loại phòng (Ví dụ: 'phòng trọ', 'căn hộ mini',
            'homestay', 'sleepbox', 'nhà nguyên căn', 'căn hộ chung cư').
        min_price (float, optional): Mức giá thuê tối thiểu (VNĐ/tháng).
        amenities (list[str], optional): Các tiện nghi bắt buộc phải có.

    Returns:
        str: Danh sách tối đa 10 tin phù hợp nhất (kèm `rental_id` để tra cứu
        chi tiết / đặt lịch), hoặc chuỗi "LỖI:" nếu không có kết quả hoặc
        tham số không hợp lệ.
    """
    if not isinstance(location, str) or not location.strip():
        return "LỖI: Thiếu tham số 'location' — vui lòng cung cấp khu vực cần tìm."

    def parse_price(value, name):
        if value is None:
            return None, None
        try:
            value = float(value)
            if value < 0:
                return None, f"LỖI: '{name}' phải là một số không âm."
        except (ValueError, TypeError):
            return None, f"LỖI: '{name}' không hợp lệ ('{value}'). Vui lòng nhập một con số."
        return value, None

    max_price, error = parse_price(max_price, "max_price")
    if error:
        return error
    min_price, error = parse_price(min_price, "min_price")
    if error:
        return error
    if min_price is not None and max_price is not None and min_price > max_price:
        return "LỖI: 'min_price' không được lớn hơn 'max_price'."

    if amenities is None:
        required_amenities = []
    elif isinstance(amenities, str):
        required_amenities = [amenities]
    elif isinstance(amenities, (list, tuple)) and all(isinstance(item, str) for item in amenities):
        required_amenities = list(amenities)
    else:
        return "LỖI: 'amenities' phải là một chuỗi hoặc danh sách chuỗi."

    required_amenities = [
        _normalize_search_text(item) for item in required_amenities if item.strip()
    ]

    if not _RENTALS:
        return "LỖI: Không tải được dữ liệu nhà trọ/căn hộ (data/datamock.json)."

    def parse_loc(text):
        text = _normalize_search_text(text)
        for prefix in ["quan", "huyen", "thanh pho", "tp", "tinh", "phuong", "xa"]:
            text = re.sub(rf"\b{prefix}\b", "", text)
        return [w for w in text.split() if w]

    loc_tokens = parse_loc(location)
    
    results = []
    for r in _RENTALS:
        if r.get("status") != "available":
            continue
            
        addr = r.get("address", {})
        haystack = _normalize_search_text(
            " ".join([addr.get("ward", ""), addr.get("district", ""), addr.get("city", "")])
        )
        
        # Tất cả các token của khu vực phải xuất hiện trong địa chỉ (haystack)
        match_loc = True
        for token in loc_tokens:
            if token not in haystack:
                match_loc = False
                break
                
        if not match_loc:
            continue
            
        if max_price is not None and r.get("price", 0) > max_price:
            continue
        if min_price is not None and r.get("price", 0) < min_price:
            continue
        if room_type is not None and _normalize_search_text(room_type) not in _normalize_search_text(r.get("type", "")):
            continue
        rental_amenities = {
            _normalize_search_text(item) for item in r.get("amenities", [])
        }
        if any(item not in rental_amenities for item in required_amenities):
            continue
        results.append(r)

    if not results:
        return f"LỖI: Không tìm thấy phòng trọ/căn hộ nào còn trống khớp với khu vực '{location}' và điều kiện đã cho."

    results.sort(key=lambda item: (item.get("price", 0), item.get("id", "")))
    shown = results[:10]
    lines = [f"Tìm thấy {len(results)} kết quả phù hợp (hiển thị {len(shown)} đầu tiên):"]
    for r in shown:
        addr = r.get("address", {})
        amenities = ", ".join(r.get("amenities", [])) or "Không có"
        lines.append(
            f"- [{r['id']}] {r.get('title', r.get('type', ''))} | "
            f"{addr.get('ward', '')}, {addr.get('district', '')}, {addr.get('city', '')} | "
            f"{r.get('area', 0)}m² | {r.get('price', 0):,.0f} VNĐ/tháng | Tiện nghi: {amenities}"
        )
    return "\n".join(lines)


# ============================================================
# 🛠️ TOOL 2: XEM CHI TIẾT TIN ĐĂNG
# ============================================================

def get_rental_details(rental_id: str = None) -> str:
    """
    Lấy thông tin chi tiết đầy đủ của một tin đăng theo mã tin.

    Args:
        rental_id (str): Mã tin đăng (Ví dụ: 'PROP-0001'), lấy được từ kết quả
            của tool `search_rentals`.

    Returns:
        str: Thông tin chi tiết của tin đăng, hoặc chuỗi "LỖI:" nếu mã tin
        không tồn tại.
    """
    if not isinstance(rental_id, str) or not rental_id.strip():
        return "LỖI: Thiếu tham số 'rental_id'."

    rental_id = rental_id.strip().upper()
    r = _RENTALS_BY_ID.get(rental_id)
    if not r:
        return f"LỖI: Không tìm thấy tin đăng với mã '{rental_id}'. Vui lòng kiểm tra lại mã tin."

    addr = r.get("address", {})
    contact = r.get("contact", {})
    amenities = ", ".join(r.get("amenities", [])) or "Không có thông tin"

    return (
        f"Chi tiết tin [{rental_id}] - {r.get('title', '')}:\n"
        f"- Địa chỉ: {addr.get('street', '')}, {addr.get('ward', '')}, {addr.get('district', '')}, {addr.get('city', '')}\n"
        f"- Loại phòng: {r.get('type', '')}\n"
        f"- Diện tích: {r.get('area', 0)}m²\n"
        f"- Giá thuê: {r.get('price', 0):,.0f} VNĐ/tháng\n"
        f"- Trạng thái: {r.get('status', '')}\n"
        f"- Có thể ở từ: {r.get('available_from', '')}\n"
        f"- Tiện nghi: {amenities}\n"
        f"- Mô tả: {r.get('description', 'Không có mô tả')}\n"
        f"- Liên hệ: {contact.get('name', '')} - {contact.get('phone', '')}"
    )


# ============================================================
# 🛠️ TOOL 3: KIỂM TRA KHUNG GIỜ TRỐNG ĐỂ XEM NHÀ
# ============================================================

def check_viewing_availability(rental_id: str = None, date: str = None) -> str:
    """
    Kiểm tra các khung giờ còn trống để xem nhà cho một tin vào một ngày cụ thể.

    Args:
        rental_id (str): Mã tin đăng (Ví dụ: 'PROP-0001').
        date (str, optional): Ngày muốn xem nhà, định dạng 'DD/MM/YYYY'
            (Ví dụ: '26/08/2026'). Nếu bỏ trống, trả toàn bộ khung giờ còn trống.

    Returns:
        str: Danh sách giờ còn trống trong ngày đó, hoặc chuỗi "LỖI:" nếu mã
        tin/ngày không hợp lệ hoặc không có giờ trống nào trong ngày đó.
    """
    if not isinstance(rental_id, str) or not rental_id.strip():
        return "LỖI: Thiếu tham số 'rental_id'."
    rental_id = rental_id.strip().upper()
    r = _RENTALS_BY_ID.get(rental_id)
    if not r:
        return f"LỖI: Không tìm thấy tin đăng với mã '{rental_id}'."

    date_tuple = None
    if date:
        date_tuple = _is_valid_date(date)
        if not date_tuple:
            return f"LỖI: Ngày '{date}' không đúng định dạng DD/MM/YYYY hoặc không hợp lệ."

    slots = _available_slots(r, date_tuple)
    if not slots and date:
        return f"LỖI: Tin [{rental_id}] không có khung giờ xem nhà nào trống vào ngày {date}. Vui lòng thử ngày khác."
    if not slots:
        return f"LỖI: Tin [{rental_id}] hiện không có khung giờ xem nhà nào còn trống."

    if date:
        times = [s.split("T")[1][:5] for s in slots]
        return f"Khung giờ còn trống để xem nhà [{rental_id}] vào {date}: {', '.join(times)}."

    formatted_slots = []
    for slot in slots:
        parsed = datetime.fromisoformat(slot)
        formatted_slots.append(parsed.strftime("%H:%M ngày %d/%m/%Y"))
    return f"Các khung giờ còn trống để xem nhà [{rental_id}]: {', '.join(formatted_slots)}."


# ============================================================
# 🛠️ TOOL 4: ĐẶT LỊCH XEM NHÀ
# ============================================================

def book_viewing(rental_id: str = None, date: str = None, time: str = None, customer_name: str = None, phone_number: str = None) -> str:
    """
    Đặt lịch hẹn xem nhà cho một tin vào ngày/giờ cụ thể, thay mặt khách hàng.
    Giờ đặt PHẢI nằm trong danh sách trả về bởi `check_viewing_availability`.

    Args:
        rental_id (str): Mã tin đăng (Ví dụ: 'PROP-0001').
        date (str): Ngày muốn xem nhà, định dạng 'DD/MM/YYYY'.
        time (str): Khung giờ muốn xem, định dạng 'HH:MM' (Ví dụ: '15:30').
        customer_name (str): Tên khách hàng đặt lịch.
        phone_number (str): Số điện thoại liên hệ (Ví dụ: '0912345678').

    Returns:
        str: Xác nhận đặt lịch kèm `booking_id`, hoặc chuỗi "LỖI:" nếu thông
        tin không hợp lệ, tin đã ngừng cho thuê, hoặc giờ đã có người đặt.
    """
    if not isinstance(rental_id, str) or not rental_id.strip():
        return "LỖI: Thiếu tham số 'rental_id'."
    if not isinstance(customer_name, str) or not customer_name.strip():
        return "LỖI: Thiếu tham số 'customer_name'."
    if not isinstance(phone_number, str) or not re.match(r"^0\d{9,10}$", phone_number.strip()):
        return f"LỖI: Số điện thoại '{phone_number}' không hợp lệ (cần bắt đầu bằng 0 và có 10-11 chữ số)."
    if not date:
        return "LỖI: Thiếu tham số 'date'."
    if not isinstance(time, str) or not time.strip():
        return "LỖI: Thiếu tham số 'time'."

    rental_id = rental_id.strip().upper()
    r = _RENTALS_BY_ID.get(rental_id)
    if not r:
        return f"LỖI: Không tìm thấy tin đăng với mã '{rental_id}'."
    if r.get("status") != "available":
        return f"LỖI: Tin [{rental_id}] hiện đang ở trạng thái '{r.get('status')}', không thể đặt lịch xem."

    date_tuple = _is_valid_date(date)
    if not date_tuple:
        return f"LỖI: Ngày '{date}' không đúng định dạng DD/MM/YYYY hoặc không hợp lệ."

    time = time.strip()
    if not _is_valid_time(time):
        return f"LỖI: Giờ '{time}' không đúng định dạng HH:MM."

    year, month, day = date_tuple
    target_iso = f"{year:04d}-{month:02d}-{day:02d}T{time}:00"

    booked = _BOOKED_SLOTS.setdefault(rental_id, set())
    if target_iso not in r.get("viewing_slots", []):
        return f"LỖI: Khung giờ {time} ngày {date} không nằm trong lịch xem nhà của tin [{rental_id}]. Hãy kiểm tra lại bằng check_viewing_availability."
    if target_iso in booked:
        return f"LỖI: Khung giờ {time} ngày {date} cho tin [{rental_id}] đã có người đặt. Vui lòng chọn khung giờ khác."

    booked.add(target_iso)
    
    # Overwrite the datamock.json file to persist booking
    if target_iso in r.get("viewing_slots", []):
        r["viewing_slots"].remove(target_iso)
    try:
        with open(_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(_RENTALS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass # Handle gracefully if file can't be written

    booking_id = f"BK-{len(_BOOKINGS) + 1000}"
    _BOOKINGS[booking_id] = {
        "rental_id": rental_id,
        "slot": target_iso,
        "customer_name": customer_name.strip(),
        "phone_number": phone_number.strip(),
    }

    return (
        f"Đặt lịch thành công! Mã lịch hẹn: {booking_id}.\n"
        f"Khách hàng {customer_name.strip()} sẽ xem nhà [{rental_id}] ({r.get('title', '')}) "
        f"vào lúc {time} ngày {date}. Nhân viên sẽ liên hệ qua số {phone_number.strip()} để xác nhận."
    )


# ============================================================
# 🛠️ TOOL 5: HUỶ LỊCH HẸN XEM NHÀ
# ============================================================

def cancel_viewing(booking_id: str = None) -> str:
    """
    Huỷ một lịch hẹn xem nhà đã đặt trước đó, trả lại khung giờ vào danh sách
    còn trống.

    Args:
        booking_id (str): Mã lịch hẹn cần huỷ (Ví dụ: 'BK-1000'), lấy được từ
            kết quả của tool `book_viewing`.

    Returns:
        str: Thông báo huỷ thành công, hoặc chuỗi "LỖI:" nếu mã lịch hẹn
        không tồn tại.
    """
    if not isinstance(booking_id, str) or not booking_id.strip():
        return "LỖI: Thiếu tham số 'booking_id'."

    booking_id = booking_id.strip().upper()
    booking = _BOOKINGS.pop(booking_id, None)
    if not booking:
        return f"LỖI: Không tìm thấy lịch hẹn với mã '{booking_id}'."

    rental_id = booking["rental_id"]
    slot = booking["slot"]
    _BOOKED_SLOTS.get(rental_id, set()).discard(slot)
    
    # Also put the slot back to the file
    r = _RENTALS_BY_ID.get(rental_id)
    if r:
        if slot not in r.get("viewing_slots", []):
            r.setdefault("viewing_slots", []).append(slot)
            r["viewing_slots"].sort()
        try:
            with open(_DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(_RENTALS, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    date_part, time_part = slot.split("T")
    time_part = time_part[:5]
    y, m, d = date_part.split("-")

    return f"Đã huỷ lịch hẹn [{booking_id}] (xem nhà [{rental_id}] lúc {time_part} ngày {d}/{m}/{y}) thành công."


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_rentals": search_rentals,
    "get_rental_details": get_rental_details,
    "check_viewing_availability": check_viewing_availability,
    "book_viewing": book_viewing,
    "cancel_viewing": cancel_viewing,
}
