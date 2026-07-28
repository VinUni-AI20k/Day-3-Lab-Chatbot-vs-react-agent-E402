"""
TOOL REGISTRY & SCHEMAS
AI Agent: Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
"""

# ============================================================
# MOCK DATABASE
# ============================================================

RENTALS = [

    {
        "id": "CH-1001",
        "title": "Studio Full nội thất",
        "location": "Dịch Vọng, Cầu Giấy",
        "price": 4500000,
        "room_type": "Studio",
        "area": 28,
        "amenities": ["điều hòa", "wifi", "máy giặt"],
        "image": "https://example.com/ch1001.jpg"
    },

    {
        "id": "CH-1002",
        "title": "Phòng trọ gần Đại học Quốc Gia",
        "location": "Dịch Vọng, Cầu Giấy",
        "price": 3900000,
        "room_type": "Phòng trọ",
        "area": 20,
        "amenities": ["wifi", "điều hòa"],
        "image": "https://example.com/ch1002.jpg"
    },

    {
        "id": "CH-1003",
        "title": "Studio có ban công",
        "location": "Mai Dịch, Cầu Giấy",
        "price": 5200000,
        "room_type": "Studio",
        "area": 30,
        "amenities": ["điều hòa", "ban công", "wifi"],
        "image": "https://example.com/ch1003.jpg"
    },

    {
        "id": "CH-1004",
        "title": "Căn hộ 1PN",
        "location": "Mỹ Đình",
        "price": 7200000,
        "room_type": "1PN",
        "area": 42,
        "amenities": ["điều hòa", "máy giặt", "ban công", "thang máy"],
        "image": "https://example.com/ch1004.jpg"
    },

    {
        "id": "CH-1005",
        "title": "Căn hộ 2PN",
        "location": "Mỹ Đình",
        "price": 9500000,
        "room_type": "2PN",
        "area": 68,
        "amenities": ["ban công", "thang máy", "bãi đỗ xe"],
        "image": "https://example.com/ch1005.jpg"
    },

    {
        "id": "CH-1006",
        "title": "Chung cư mini Full nội thất",
        "location": "Nam Từ Liêm",
        "price": 6500000,
        "room_type": "Studio",
        "area": 32,
        "amenities": ["điều hòa", "máy giặt", "wifi", "ban công"],
        "image": "https://example.com/ch1006.jpg"
    },

    {
        "id": "CH-1007",
        "title": "Studio gần Keangnam",
        "location": "Nam Từ Liêm",
        "price": 5800000,
        "room_type": "Studio",
        "area": 30,
        "amenities": ["điều hòa", "wifi"],
        "image": "https://example.com/ch1007.jpg"
    },

    {
        "id": "CH-1008",
        "title": "1PN gần Landmark 81",
        "location": "Bình Thạnh",
        "price": 7800000,
        "room_type": "1PN",
        "area": 45,
        "amenities": ["ban công", "điều hòa", "máy giặt", "wifi"],
        "image": "https://example.com/ch1008.jpg"
    },

    {
        "id": "CH-1009",
        "title": "Studio View Landmark",
        "location": "Bình Thạnh",
        "price": 6900000,
        "room_type": "Studio",
        "area": 33,
        "amenities": ["điều hòa", "ban công"],
        "image": "https://example.com/ch1009.jpg"
    },

    {
        "id": "CH-1010",
        "title": "Căn hộ 1PN Full nội thất",
        "location": "Bình Thạnh",
        "price": 7900000,
        "room_type": "1PN",
        "area": 46,
        "amenities": ["điều hòa", "ban công", "máy giặt", "wifi"],
        "image": "https://example.com/ch1010.jpg"
    },

    {
        "id": "CH-1011",
        "title": "Phòng trọ sinh viên",
        "location": "Thủ Đức",
        "price": 2800000,
        "room_type": "Phòng trọ",
        "area": 18,
        "amenities": ["wifi"],
        "image": "https://example.com/ch1011.jpg"
    },

    {
        "id": "CH-1012",
        "title": "Studio gần Đại học Bách Khoa",
        "location": "Hai Bà Trưng",
        "price": 5100000,
        "room_type": "Studio",
        "area": 27,
        "amenities": ["điều hòa", "wifi", "máy giặt"],
        "image": "https://example.com/ch1012.jpg"
    }

]


LANDLORD_SCHEDULE = {

    "CH-1001": {
        "chiều mai": ["14:00", "15:00", "16:00"],
        "thứ bảy": ["09:00", "10:00", "15:00"]
    },

    "CH-1002": {
        "chiều mai": ["15:30", "17:00"],
        "thứ bảy": ["09:30", "13:30"]
    },

    "CH-1003": {
        "chiều mai": ["14:30"],
        "thứ bảy": ["10:00", "16:00"]
    },

    "CH-1004": {
        "thứ bảy": ["10:00", "11:00", "14:00"]
    },

    "CH-1005": {
        "thứ bảy": ["09:00", "15:00"]
    },

    "CH-1006": {
        "chiều mai": ["14:00", "15:00"],
        "thứ bảy": ["10:00", "16:00"]
    },

    "CH-1007": {
        "chiều mai": ["16:30"],
        "thứ bảy": ["09:00"]
    },

    "CH-1008": {
        "thứ bảy": ["10:00", "14:00", "16:00"]
    },

    "CH-1009": {
        "chiều mai": ["15:00"],
        "thứ bảy": ["09:30", "13:30"]
    },

    "CH-1010": {
        "thứ bảy": ["10:00", "11:30", "15:30"]
    },

    "CH-1011": {
        "chiều mai": ["14:00"]
    },

    "CH-1012": {
        "thứ bảy": ["09:00", "10:00"]
    }

}


BOOKINGS = []

# TOOL 1

def search_rentals(
    location: str,
    price_min: int = 0,
    price_max: int = 999999999,
    room_type: str = "",
    amenities=None
):
    """
    Tìm kiếm nhà theo tiêu chí.
    """

    if amenities is None:
        amenities = []

    results = []

    for room in RENTALS:

        if location.lower() not in room["location"].lower():
            continue

        if room["price"] < price_min:
            continue

        if room["price"] > price_max:
            continue

        if room_type and room["room_type"] != room_type:
            continue

        if not all(a in room["amenities"] for a in amenities):
            continue

        results.append(room)

    return results


# TOOL 2

def get_rental_detail(rental_id: str):
    """
    Lấy thông tin chi tiết căn hộ.
    """

    for room in RENTALS:

        if room["id"] == rental_id:
            return room

    return {
        "error": "Không tìm thấy căn hộ."
    }


# TOOL 3

def check_landlord_calendar(
    rental_id: str,
    date: str
):
    """
    Kiểm tra lịch rảnh của chủ nhà.
    """

    if rental_id not in LANDLORD_SCHEDULE:

        return {
            "error": "Không tìm thấy lịch chủ nhà."
        }

    slots = LANDLORD_SCHEDULE[rental_id].get(date)

    if slots is None:

        return {
            "available": False,
            "message": "Không có lịch trong ngày này."
        }

    return {

        "available": True,
        "slots": slots

    }


# TOOL 4

def book_viewing_appointment(
    rental_id,
    user_name,
    phone,
    datetime
):
    """
    Đặt lịch xem nhà.
    """

    booking = {

        "booking_id": f"BK{len(BOOKINGS)+1:03d}",

        "rental_id": rental_id,

        "user_name": user_name,

        "phone": phone,

        "datetime": datetime,

        "status": "Confirmed"

    }

    BOOKINGS.append(booking)

    return booking


# TOOL 5

def send_confirmation_notification(
    phone,
    booking_details
):
    """
    Mô phỏng gửi SMS.
    """

    return (

        f"Đã gửi SMS xác nhận tới {phone}\n"

        f"Mã đặt lịch: {booking_details['booking_id']}\n"

        f"Thời gian: {booking_details['datetime']}"

    )


# TOOL REGISTRY

AVAILABLE_TOOLS = {

    "search_rentals": search_rentals,

    "get_rental_detail": get_rental_detail,

    "check_landlord_calendar": check_landlord_calendar,

    "book_viewing_appointment": book_viewing_appointment,

    "send_confirmation_notification": send_confirmation_notification

}