"""
TOOL REGISTRY & SCHEMAS
AI Agent: Tìm & Đặt Lịch Xem Nhà Trọ / Căn Hộ Cho Thuê
"""

# ============================================================
# MOCK DATABASE
# ============================================================

RENTALS = [
    {
        "id": "CH-8802",
        "title": "Căn hộ Studio Full nội thất",
        "location": "Dịch Vọng, Cầu Giấy",
        "price": 4800000,
        "room_type": "Studio",
        "amenities": ["điều hòa", "máy giặt", "wifi"],
        "image": "https://example.com/ch8802.jpg"
    },
    {
        "id": "CH-102",
        "title": "Phòng trọ gần Đại học X",
        "location": "Cầu Giấy",
        "price": 3500000,
        "room_type": "Phòng trọ",
        "amenities": ["điều hòa"],
        "image": "https://example.com/ch102.jpg"
    },
    {
        "id": "CH-5501",
        "title": "Căn hộ 1PN có ban công",
        "location": "Bình Thạnh",
        "price": 7900000,
        "room_type": "1PN",
        "amenities": ["ban công", "máy lạnh", "wifi"],
        "image": "https://example.com/ch5501.jpg"
    }
]


LANDLORD_SCHEDULE = {
    "CH-8802": {
        "chiều mai": [
            "14:00",
            "15:00",
            "16:00"
        ],
        "thứ bảy": [
            "10:00",
            "15:00"
        ]
    },

    "CH-102": {
        "hôm nay": [
            "16:00",
            "17:00"
        ]
    },

    "CH-5501": {
        "thứ bảy": [
            "10:00",
            "14:00"
        ]
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