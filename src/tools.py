"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Trợ Lý Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
"""

import random
import re


MOCK_RENTALS = {
    "R001": {
        "location": "Cầu Giấy, Hà Nội",
        "type": "phòng trọ",
        "price": 3_000_000,
        "area_m2": 20,
        "description": "Phòng trọ khép kín, có gác, gần Đại học Quốc Gia.",
    },
    "R002": {
        "location": "Cầu Giấy, Hà Nội",
        "type": "căn hộ mini",
        "price": 5_500_000,
        "area_m2": 35,
        "description": "Căn hộ mini đầy đủ nội thất, có thang máy, an ninh 24/7.",
    },
    "R003": {
        "location": "Quận 7, TP.HCM",
        "type": "căn hộ",
        "price": 8_000_000,
        "area_m2": 55,
        "description": "Căn hộ chung cư 2 phòng ngủ, view sông, gần Phú Mỹ Hưng.",
    },
    "R004": {
        "location": "Quận 7, TP.HCM",
        "type": "phòng trọ",
        "price": 2_500_000,
        "area_m2": 18,
        "description": "Phòng trọ giá rẻ, gần trường đại học, có chỗ để xe.",
    },
    "R005": {
        "location": "Hải Châu, Đà Nẵng",
        "type": "căn hộ mini",
        "price": 4_000_000,
        "area_m2": 30,
        "description": "Căn hộ mini gần biển Mỹ Khê, ban công thoáng mát.",
    },
}

DEFAULT_SLOTS = ["09:00", "11:00", "14:00", "16:00", "19:00"]
_BOOKED_SLOTS = {}
_BOOKINGS = {}


def _normalize(text: str) -> str:
    return text.lower().strip()


def _is_valid_date(date: str) -> bool:
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", date.strip())
    if not match:
        return False
    day, month, year = (int(x) for x in match.groups())
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False
    return True

def search_rentals(location: str, max_price: float = None, room_type: str = None) -> str:
    """
    Tìm kiếm các tin đăng phòng trọ / căn hộ cho thuê theo khu vực, mức giá tối đa
    và loại phòng.

    Args:
        location (str): Khu vực cần tìm (Ví dụ: 'Cầu Giấy', 'Quận 7', 'Đà Nẵng').
        max_price (float, optional): Mức giá thuê tối đa (VNĐ/tháng). Nếu None,
            không giới hạn giá.
        room_type (str, optional): Loại phòng cần tìm (Ví dụ: 'phòng trọ',
            'căn hộ mini', 'căn hộ'). Nếu None, lấy tất cả loại.

    Returns:
        str: Danh sách các tin đăng phù hợp (kèm mã tin `rental_id` để tra cứu
        chi tiết / đặt lịch xem), hoặc chuỗi "LỖI:" nếu không tìm thấy kết quả
        hoặc tham số không hợp lệ.
    """
    if not location or not location.strip():
        return "LỖI: Thiếu tham số 'location' — vui lòng cung cấp khu vực cần tìm."

    if max_price is not None:
        try:
            max_price = float(max_price)
            if max_price <= 0:
                return "LỖI: 'max_price' phải là một số dương."
        except (ValueError, TypeError):
            return f"LỖI: 'max_price' không hợp lệ ('{max_price}'). Vui lòng nhập một con số."

    loc_query = _normalize(location)
    results = []
    for rental_id, info in MOCK_RENTALS.items():
        if loc_query not in _normalize(info["location"]):
            continue
        if max_price is not None and info["price"] > max_price:
            continue
        if room_type is not None and _normalize(room_type) not in _normalize(info["type"]):
            continue
        results.append((rental_id, info))

    if not results:
        return f"LỖI: Không tìm thấy phòng trọ/căn hộ nào khớp với khu vực '{location}' và điều kiện đã cho."

    lines = [f"Tìm thấy {len(results)} kết quả phù hợp:"]
    for rental_id, info in results:
        lines.append(
            f"- [{rental_id}] {info['type'].capitalize()} tại {info['location']} | "
            f"{info['area_m2']}m² | {info['price']:,.0f} VNĐ/tháng | {info['description']}"
        )
    return "\n".join(lines)

def get_rental_details(rental_id: str) -> str:
    """
    Lấy thông tin chi tiết đầy đủ của một tin đăng phòng trọ / căn hộ theo mã tin.

    Args:
        rental_id (str): Mã tin đăng (Ví dụ: 'R001'), lấy được từ kết quả của
            tool `search_rentals`.

    Returns:
        str: Thông tin chi tiết của tin đăng, hoặc chuỗi "LỖI:" nếu mã tin
        không tồn tại.
    """
    if not rental_id:
        return "LỖI: Thiếu tham số 'rental_id'."

    rental_id = rental_id.strip().upper()
    info = MOCK_RENTALS.get(rental_id)
    if not info:
        return f"LỖI: Không tìm thấy tin đăng với mã '{rental_id}'. Vui lòng kiểm tra lại mã tin."

    return (
        f"Chi tiết tin [{rental_id}]:\n"
        f"- Khu vực: {info['location']}\n"
        f"- Loại phòng: {info['type']}\n"
        f"- Diện tích: {info['area_m2']}m²\n"
        f"- Giá thuê: {info['price']:,.0f} VNĐ/tháng\n"
        f"- Mô tả: {info['description']}"
    )

def check_viewing_availability(rental_id: str, date: str) -> str:
    """
    Kiểm tra các khung giờ còn trống để đặt lịch xem nhà cho một tin đăng vào
    một ngày cụ thể.

    Args:
        rental_id (str): Mã tin đăng (Ví dụ: 'R001').
        date (str): Ngày muốn xem nhà, định dạng 'DD/MM/YYYY' (Ví dụ: '20/08/2026').

    Returns:
        str: Danh sách khung giờ còn trống, hoặc chuỗi "LỖI:" nếu mã tin/ngày
        không hợp lệ hoặc đã kín lịch.
    """
    if not rental_id:
        return "LỖI: Thiếu tham số 'rental_id'."
    if not date:
        return "LỖI: Thiếu tham số 'date'."

    rental_id = rental_id.strip().upper()
    if rental_id not in MOCK_RENTALS:
        return f"LỖI: Không tìm thấy tin đăng với mã '{rental_id}'."

    if not _is_valid_date(date):
        return f"LỖI: Ngày '{date}' không đúng định dạng DD/MM/YYYY hoặc không tồn tại trong lịch."

    booked = _BOOKED_SLOTS.get(rental_id, {}).get(date, set())
    available = [slot for slot in DEFAULT_SLOTS if slot not in booked]

    if not available:
        return f"LỖI: Tin [{rental_id}] đã kín lịch xem nhà vào ngày {date}. Vui lòng chọn ngày khác."

    return f"Khung giờ còn trống để xem nhà [{rental_id}] vào {date}: {', '.join(available)}."

def book_viewing(rental_id: str, date: str, time: str, customer_name: str, phone_number: str) -> str:
    """
    Đặt lịch hẹn xem nhà cho một tin đăng vào ngày/giờ cụ thể, thay mặt khách hàng.

    Args:
        rental_id (str): Mã tin đăng (Ví dụ: 'R001').
        date (str): Ngày muốn xem nhà, định dạng 'DD/MM/YYYY'.
        time (str): Khung giờ muốn xem, phải nằm trong danh sách trả về bởi
            tool `check_viewing_availability` (Ví dụ: '14:00').
        customer_name (str): Tên khách hàng đặt lịch.
        phone_number (str): Số điện thoại liên hệ của khách hàng (Ví dụ:
            '0912345678').

    Returns:
        str: Thông báo xác nhận đặt lịch thành công kèm `booking_id`, hoặc
        chuỗi "LỖI:" nếu thông tin không hợp lệ hoặc khung giờ đã có người đặt.
    """
    if not rental_id:
        return "LỖI: Thiếu tham số 'rental_id'."
    if not customer_name or not customer_name.strip():
        return "LỖI: Thiếu tham số 'customer_name'."
    if not phone_number or not re.match(r"^0\d{9,10}$", phone_number.strip()):
        return f"LỖI: Số điện thoại '{phone_number}' không hợp lệ (cần bắt đầu bằng 0 và có 10-11 chữ số)."

    rental_id = rental_id.strip().upper()
    if rental_id not in MOCK_RENTALS:
        return f"LỖI: Không tìm thấy tin đăng với mã '{rental_id}'."

    if not _is_valid_date(date):
        return f"LỖI: Ngày '{date}' không đúng định dạng DD/MM/YYYY hoặc không tồn tại trong lịch."

    time = time.strip()
    if time not in DEFAULT_SLOTS:
        return f"LỖI: Khung giờ '{time}' không hợp lệ. Các khung giờ khả dụng: {', '.join(DEFAULT_SLOTS)}."

    booked = _BOOKED_SLOTS.setdefault(rental_id, {}).setdefault(date, set())
    if time in booked:
        return f"LỖI: Khung giờ {time} ngày {date} cho tin [{rental_id}] đã có người đặt. Vui lòng chọn khung giờ khác."

    booked.add(time)
    booking_id = f"BK{random.randint(1000, 9999)}"
    _BOOKINGS[booking_id] = {
        "rental_id": rental_id,
        "date": date,
        "time": time,
        "customer_name": customer_name.strip(),
        "phone_number": phone_number.strip(),
    }

    return (
        f"Đặt lịch thành công! Mã lịch hẹn: {booking_id}.\n"
        f"Khách hàng {customer_name.strip()} sẽ xem nhà [{rental_id}] vào lúc {time} ngày {date}. "
        f"Nhân viên sẽ liên hệ qua số {phone_number.strip()} để xác nhận."
    )

def cancel_viewing(booking_id: str) -> str:
    """
    Huỷ một lịch hẹn xem nhà đã đặt trước đó.

    Args:
        booking_id (str): Mã lịch hẹn cần huỷ (Ví dụ: 'BK1234'), lấy được từ
            kết quả của tool `book_viewing`.

    Returns:
        str: Thông báo huỷ lịch thành công, hoặc chuỗi "LỖI:" nếu mã lịch hẹn
        không tồn tại.
    """
    if not booking_id:
        return "LỖI: Thiếu tham số 'booking_id'."

    booking_id = booking_id.strip().upper()
    booking = _BOOKINGS.pop(booking_id, None)
    if not booking:
        return f"LỖI: Không tìm thấy lịch hẹn với mã '{booking_id}'."

    rental_id = booking["rental_id"]
    date = booking["date"]
    time = booking["time"]
    _BOOKED_SLOTS.get(rental_id, {}).get(date, set()).discard(time)

    return f"Đã huỷ lịch hẹn [{booking_id}] (xem nhà [{rental_id}] lúc {time} ngày {date}) thành công."

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_rentals": search_rentals,
    "get_rental_details": get_rental_details,
    "check_viewing_availability": check_viewing_availability,
    "book_viewing": book_viewing,
    "cancel_viewing": cancel_viewing,
}

