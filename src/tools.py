"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)

Các công cụ mô phỏng nghiệp vụ tìm và đặt lịch xem nhà trọ/căn hộ.
Mọi tool đều trả về chuỗi để ReAct Agent có thể dùng trực tiếp làm Observation.
Khi dữ liệu đầu vào không hợp lệ, tool trả về chuỗi bắt đầu bằng ``LỖI:``
thay vì ném exception làm dừng Agent.
"""

from itertools import count

# Dữ liệu giả lập dùng chung cho bài lab, giúp kết quả test có tính lặp lại.
PROPERTIES = {
    "CH001": {
        "name": "Căn hộ Sunrise City",
        "district": "Quận 7",
        "address": "Nguyễn Hữu Thọ, Quận 7",
        "price": 7_500_000,
        "property_type": "căn hộ",
        "amenities": ["máy lạnh", "ban công", "bảo vệ 24/7"],
    },
    "CH002": {
        "name": "Căn hộ mini Linh Trung",
        "district": "Thủ Đức",
        "address": "Linh Trung, Thủ Đức",
        "price": 6_500_000,
        "property_type": "căn hộ",
        "amenities": ["máy lạnh", "máy giặt", "wifi"],
    },
    "PT003": {
        "name": "Phòng trọ Bách Khoa",
        "district": "Quận 10",
        "address": "Tô Hiến Thành, gần Đại học Bách Khoa",
        "price": 4_200_000,
        "property_type": "phòng trọ",
        "amenities": ["wifi", "gác lửng", "giữ xe"],
    },
    "PT004": {
        "name": "Phòng trọ Tân Phú",
        "district": "Tân Phú",
        "address": "Lũy Bán Bích, Tân Phú",
        "price": 3_800_000,
        "property_type": "phòng trọ",
        "amenities": ["máy lạnh", "wifi", "giữ xe"],
    },
}

VIEWING_SLOTS = {
    "CH001": ["2026-08-01 09:00", "2026-08-01 14:00", "2026-08-02 10:00"],
    "CH002": ["2026-08-01 13:30", "2026-08-01 15:30", "2026-08-02 09:00"],
    "PT003": ["2026-07-29 09:00", "2026-07-29 15:00", "2026-08-01 08:00"],
    "PT004": ["2026-07-29 10:00", "2026-08-01 16:00"],
}

# Lưu booking trong bộ nhớ trong thời gian chương trình đang chạy.
BOOKINGS = {}
_booking_sequence = count(1)


def _normalize(value: str) -> str:
    """Chuẩn hóa chuỗi để so khớp không phân biệt hoa/thường."""
    return str(value).strip().casefold()


def _format_property(property_id: str, property_data: dict) -> str:
    """Định dạng ngắn gọn một căn nhà cho Observation."""
    amenities = ", ".join(property_data["amenities"])
    return (
        f"{property_id} | {property_data['name']} | "
        f"{property_data['district']} | {property_data['price']:,} VNĐ/tháng | "
        f"Tiện nghi: {amenities}"
    )


def search_properties(
    location: str = "",
    max_price: int | None = None,
    property_type: str = "",
    amenity: str = "",
) -> str:
    """
    Tìm nhà theo khu vực, giá tối đa, loại hình và một tiện nghi.

    Args:
        location: Quận, khu vực, địa chỉ hoặc địa danh gần căn nhà.
        max_price: Giá thuê tối đa mỗi tháng (VNĐ), phải là số không âm.
        property_type: Loại nơi ở, ví dụ ``căn hộ`` hoặc ``phòng trọ``.
        amenity: Tiện nghi bắt buộc, ví dụ ``máy lạnh`` hoặc ``wifi``.

    Returns:
        Danh sách căn phù hợp; ``KHÔNG TÌM THẤY`` nếu không có kết quả;
        hoặc ``LỖI:`` nếu tham số không hợp lệ.
    """
    if max_price is not None:
        try:
            max_price = int(max_price)
        except (TypeError, ValueError):
            return "LỖI: max_price phải là một số nguyên tính bằng VNĐ."
        if max_price < 0:
            return "LỖI: max_price không được là số âm."

    location_key = _normalize(location)
    type_key = _normalize(property_type)
    amenity_key = _normalize(amenity)
    matches = []

    for property_id, data in PROPERTIES.items():
        searchable_location = _normalize(f"{data['district']} {data['address']}")
        amenities = [_normalize(item) for item in data["amenities"]]
        if location_key and location_key not in searchable_location:
            continue
        if max_price is not None and data["price"] > max_price:
            continue
        if type_key and type_key not in _normalize(data["property_type"]):
            continue
        if amenity_key and not any(amenity_key in item for item in amenities):
            continue
        matches.append(_format_property(property_id, data))

    if not matches:
        return "KHÔNG TÌM THẤY: Không có căn nào phù hợp với các tiêu chí đã chọn."
    return f"Tìm thấy {len(matches)} căn:\n" + "\n".join(matches)


def get_property_details(property_id: str) -> str:
    """
    Tra cứu thông tin chi tiết của một căn theo mã.

    Args:
        property_id: Mã căn, ví dụ ``CH001``.

    Returns:
        Thông tin căn; hoặc ``LỖI:`` nếu mã trống/không tồn tại.
    """
    property_key = str(property_id).strip().upper()
    if not property_key:
        return "LỖI: Cần cung cấp mã căn."

    data = PROPERTIES.get(property_key)
    if data is None:
        return f"LỖI: Không tìm thấy căn có mã '{property_key}'."

    return (
        f"Mã căn: {property_key}\n"
        f"Tên: {data['name']}\n"
        f"Loại hình: {data['property_type']}\n"
        f"Địa chỉ: {data['address']}\n"
        f"Giá: {data['price']:,} VNĐ/tháng\n"
        f"Tiện nghi: {', '.join(data['amenities'])}"
    )


def get_available_slots(property_id: str, date: str = "") -> str:
    """
    Lấy các khung giờ xem nhà còn trống của một căn.

    Args:
        property_id: Mã căn cần xem.
        date: Ngày theo định dạng ``YYYY-MM-DD``; bỏ trống để lấy mọi ngày.

    Returns:
        Các khung giờ trống; hoặc thông báo lỗi/không còn lịch.
    """
    property_key = str(property_id).strip().upper()
    if property_key not in PROPERTIES:
        return f"LỖI: Không tìm thấy căn có mã '{property_key}'."

    date = str(date).strip()
    if date and (len(date) != 10 or date[4] != "-" or date[7] != "-"):
        return "LỖI: date phải có định dạng YYYY-MM-DD."

    slots = [
        slot
        for slot in VIEWING_SLOTS.get(property_key, [])
        if not date or slot.startswith(date)
    ]
    if not slots:
        return f"KHÔNG CÒN LỊCH: Căn {property_key} không có khung giờ trống phù hợp."
    return f"Lịch trống của {property_key}:\n" + "\n".join(f"- {slot}" for slot in slots)


def create_booking(
    property_id: str,
    viewing_time: str,
    customer_name: str,
    confirmed: bool = False,
) -> str:
    """
    Tạo lịch xem nhà sau khi người dùng đã xác nhận rõ ràng.

    Args:
        property_id: Mã căn cần đặt lịch.
        viewing_time: Thời điểm chính xác theo ``YYYY-MM-DD HH:MM``.
        customer_name: Tên người đi xem nhà.
        confirmed: Chỉ truyền ``True`` khi người dùng đã xác nhận đặt lịch.

    Returns:
        Mã booking khi thành công; hoặc ``LỖI:`` nếu chưa xác nhận, căn/khung
        giờ không tồn tại, lịch bị trùng hay thiếu tên khách hàng.

    Safety:
        Tool kiểm tra lại slot ngay lúc tạo booking và loại slot đã đặt để
        ngăn hai người đặt cùng một căn vào cùng thời điểm.
    """
    property_key = str(property_id).strip().upper()
    viewing_time = str(viewing_time).strip()
    customer_name = str(customer_name).strip()

    if confirmed is not True:
        return "LỖI: Chưa có xác nhận rõ ràng của người dùng; không tạo lịch."
    if property_key not in PROPERTIES:
        return f"LỖI: Không tìm thấy căn có mã '{property_key}'."
    if not customer_name:
        return "LỖI: Cần có tên người đặt lịch."
    if viewing_time not in VIEWING_SLOTS.get(property_key, []):
        return (
            f"LỖI: Khung giờ '{viewing_time}' không tồn tại hoặc đã được đặt "
            f"cho căn {property_key}."
        )

    booking_id = f"BK{next(_booking_sequence):03d}"
    BOOKINGS[booking_id] = {
        "property_id": property_key,
        "viewing_time": viewing_time,
        "customer_name": customer_name,
        "status": "confirmed",
    }
    VIEWING_SLOTS[property_key].remove(viewing_time)
    return (
        f"THÀNH CÔNG: Đã tạo lịch {booking_id} cho {customer_name}, "
        f"xem căn {property_key} lúc {viewing_time}."
    )


def cancel_booking(booking_id: str) -> str:
    """
    Hủy một lịch xem nhà và hoàn trả khung giờ vào danh sách lịch trống.

    Args:
        booking_id: Mã lịch hẹn được trả về từ ``create_booking``.

    Returns:
        Xác nhận hủy; hoặc ``LỖI:`` nếu mã lịch không tồn tại/đã bị hủy.
    """
    booking_key = str(booking_id).strip().upper()
    booking = BOOKINGS.get(booking_key)
    if booking is None:
        return f"LỖI: Không tìm thấy lịch hẹn '{booking_key}'."
    if booking["status"] == "cancelled":
        return f"LỖI: Lịch hẹn '{booking_key}' đã được hủy trước đó."

    booking["status"] = "cancelled"
    property_id = booking["property_id"]
    VIEWING_SLOTS[property_id].append(booking["viewing_time"])
    VIEWING_SLOTS[property_id].sort()
    return f"THÀNH CÔNG: Đã hủy lịch hẹn {booking_key}."


# Danh sách tool duy nhất mà Agent được phép gọi.
AVAILABLE_TOOLS = {
    "search_properties": search_properties,
    "get_property_details": get_property_details,
    "get_available_slots": get_available_slots,
    "create_booking": create_booking,
    "cancel_booking": cancel_booking,
}
