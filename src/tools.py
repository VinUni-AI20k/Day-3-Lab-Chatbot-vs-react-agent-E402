"""
🛠️ TOOL REGISTRY & SCHEMAS
(Dành cho Role 2: Tool & Spec Engineer)

Nơi khai báo tất cả các công cụ (tools) mà ReAct Agent
có thể sử dụng để hỗ trợ người dùng tìm kiếm và đặt lịch
xem nhà trọ / căn hộ cho thuê.
"""


def search_properties(location: str, budget: int) -> str:
    """
    Tìm kiếm danh sách nhà trọ hoặc căn hộ phù hợp theo khu vực và ngân sách.

    Args:
        location (str): Khu vực cần tìm
            (Ví dụ: "Cầu Giấy", "Thủ Đức", "Hai Bà Trưng")

        budget (int): Ngân sách tối đa (VNĐ/tháng)

    Returns:
        str: Danh sách nhà phù hợp.
    """

    if location.lower() == "cầu giấy":
        return (
            f"Kết quả tìm kiếm tại {location} (<= {budget:,} VNĐ):\n"
            "1. Phòng trọ Nguyễn Phong Sắc - 4.500.000 VNĐ/tháng\n"
            "2. Chung cư mini Duy Tân - 5.000.000 VNĐ/tháng"
        )

    if location.lower() == "thủ đức":
        return (
            f"Kết quả tìm kiếm tại {location} (<= {budget:,} VNĐ):\n"
            "1. Căn hộ Studio Linh Trung - 5.500.000 VNĐ/tháng\n"
            "2. Phòng trọ Kha Vạn Cân - 3.800.000 VNĐ/tháng"
        )

    return f"Không tìm thấy nhà phù hợp tại {location}."


def check_property_availability(property_name: str) -> str:
    """
    Kiểm tra tình trạng còn trống của nhà trọ hoặc căn hộ.

    Args:
        property_name (str): Tên nhà trọ hoặc căn hộ.

    Returns:
        str: Thông tin còn phòng hay đã hết phòng.
    """

    available = {
        "Phòng trọ Nguyễn Phong Sắc": True,
        "Chung cư mini Duy Tân": False,
        "Căn hộ Studio Linh Trung": True,
    }

    if property_name not in available:
        return f"Không tìm thấy thông tin của '{property_name}'."

    if available[property_name]:
        return f"{property_name} hiện còn phòng."

    return f"{property_name} hiện đã hết phòng."


def schedule_property_viewing(
    property_name: str,
    customer_name: str,
    viewing_time: str,
) -> str:
    """
    Đặt lịch hẹn xem nhà.

    Args:
        property_name (str):
            Tên nhà trọ hoặc căn hộ.

        customer_name (str):
            Tên khách hàng.

        viewing_time (str):
            Thời gian xem nhà.
            Ví dụ: "2026-08-05 14:00"

    Returns:
        str: Kết quả đặt lịch.
    """

    return (
        f"Đã đặt lịch xem '{property_name}' cho khách "
        f"{customer_name} vào lúc {viewing_time}."
    )


def cancel_viewing_schedule(
    customer_name: str,
    property_name: str,
) -> str:
    """
    Hủy lịch xem nhà.

    Args:
        customer_name (str):
            Tên khách hàng.

        property_name (str):
            Nhà trọ hoặc căn hộ đã đặt lịch.

    Returns:
        str: Kết quả hủy lịch.
    """

    return (
        f"Đã hủy lịch xem '{property_name}' "
        f"của khách {customer_name}."
    )


def get_property_details(property_name: str) -> str:
    """
    Xem thông tin chi tiết của một nhà trọ hoặc căn hộ.

    Args:
        property_name (str):
            Tên nhà trọ hoặc căn hộ.

    Returns:
        str: Thông tin chi tiết.
    """

    return (
        f"Thông tin của {property_name}:\n"
        "- Diện tích: 30m²\n"
        "- Nội thất: Đầy đủ\n"
        "- Có chỗ để xe\n"
        "- Có điều hòa\n"
        "- Gần trường đại học và siêu thị"
    )


# =====================================================
# Danh sách các Tool được đăng ký để Agent sử dụng
# =====================================================

AVAILABLE_TOOLS = {
    "search_properties": search_properties,
    "check_property_availability": check_property_availability,
    "schedule_property_viewing": schedule_property_viewing,
    "cancel_viewing_schedule": cancel_viewing_schedule,
    "get_property_details": get_property_details,
}