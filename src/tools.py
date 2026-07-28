"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

from datetime import datetime
from typing import Any


RENTAL_LISTINGS = [
    {
        "listing_id": "APT-102",
        "title": "Studio ban công sáng — Cầu Giấy",
        "location": "Cầu Giấy, Hà Nội",
        "price": 4_500_000,
        "bedrooms": 0,
        "area_m2": 32,
        "pet_allowed": True,
        "furnished": True,
        "image": "🏡",
        "description": "Gần ga tàu điện, nội thất cơ bản, nhiều ánh sáng tự nhiên.",
    },
    {
        "listing_id": "APT-118",
        "title": "Căn hộ 1PN yên tĩnh — Cầu Giấy",
        "location": "Cầu Giấy, Hà Nội",
        "price": 5_800_000,
        "bedrooms": 1,
        "area_m2": 42,
        "pet_allowed": False,
        "furnished": True,
        "image": "🏠",
        "description": "Tòa nhà có bảo vệ, thang máy, hợp đồng tối thiểu 6 tháng.",
    },
    {
        "listing_id": "APT-205",
        "title": "Căn hộ 1PN ven sông — Bình Thạnh",
        "location": "Bình Thạnh, TP.HCM",
        "price": 9_000_000,
        "bedrooms": 1,
        "area_m2": 50,
        "pet_allowed": True,
        "furnished": True,
        "image": "🌇",
        "description": "View thành phố, bếp riêng, cách Landmark 81 vài phút.",
    },
    {
        "listing_id": "APT-221",
        "title": "Căn hộ 2PN có sân thượng — Bình Thạnh",
        "location": "Bình Thạnh, TP.HCM",
        "price": 12_500_000,
        "bedrooms": 2,
        "area_m2": 68,
        "pet_allowed": True,
        "furnished": True,
        "image": "🌿",
        "description": "Không gian rộng, phù hợp gia đình nhỏ, có chỗ để xe.",
    },
    {
        "listing_id": "APT-305",
        "title": "Phòng ban công — Hải Châu",
        "location": "Hải Châu, Đà Nẵng",
        "price": 4_200_000,
        "bedrooms": 0,
        "area_m2": 30,
        "pet_allowed": False,
        "furnished": True,
        "image": "🌊",
        "description": "Gần sông Hàn, khu dân cư an ninh, vào ở ngay.",
    },
]

VIEWING_SLOTS = {
    "APT-102": ["Thứ Bảy 09:00", "Thứ Bảy 14:00", "Chủ Nhật 10:30"],
    "APT-118": ["Thứ Bảy 16:00", "Chủ Nhật 09:30"],
    "APT-205": ["Thứ Bảy 10:00", "Chủ Nhật 14:00", "Chủ Nhật 16:30"],
    "APT-221": ["Thứ Bảy 11:30"],
    "APT-305": ["Chủ Nhật 08:30", "Chủ Nhật 15:00"],
}

def get_weather(location: str) -> str:
    """
    Tra cứu thời tiết hiện tại của một thành phố.
    
    Args:
        location (str): Tên thành phố (Ví dụ: 'Hà Nội', 'TP.HCM', 'Đà Nẵng')
        
    Returns:
        str: Thông tin thời tiết chi tiết
    """
    loc_lower = location.lower()
    if "hà nội" in loc_lower or "ha noi" in loc_lower:
        return "Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%."
    elif "hồ chí minh" in loc_lower or "tp.hcm" in loc_lower or "hcm" in loc_lower:
        return "Thời tiết TP.HCM: 33°C, Nắng nóng, Có mây."
    elif "đà nẵng" in loc_lower or "da nang" in loc_lower:
        return "Thời tiết Đà Nẵng: 30°C, Gió nhẹ, Mát mẻ."
    else:
        return f"LỖI: Không tìm thấy dữ liệu thời tiết cho địa điểm '{location}'."


def search_flights(origin: str, destination: str) -> str:
    """
    Tra cứu chuyến bay giữa hai địa điểm.
    
    Args:
        origin (str): Nơi đi (Ví dụ: 'TP.HCM')
        destination (str): Nơi đến (Ví dụ: 'Hà Nội')
        
    Returns:
        str: Danh sách chuyến bay khả dụng và giá vé
    """
    return (
        f"Chuyến bay từ {origin} -> {destination} ngày mai:\n"
        f"1. VN123 (08:00) - Giá: 1,500,000 VNĐ (Còn vé)\n"
        f"2. VJ456 (14:30) - Giá: 1,200,000 VNĐ (Còn vé)"
    )


def search_rentals(
    location: str = "",
    max_price: int | None = None,
    bedrooms: int | None = None,
    pet_allowed: bool | None = None,
    furnished: bool | None = None,
) -> list[dict[str, Any]]:
    """Tìm listing theo bộ lọc; chỉ trả dữ liệu trong kho demo deterministic."""
    normalized_location = location.casefold().strip()
    results = []
    for listing in RENTAL_LISTINGS:
        if normalized_location and normalized_location not in listing["location"].casefold():
            continue
        if max_price is not None and listing["price"] > int(max_price):
            continue
        if bedrooms is not None and listing["bedrooms"] != int(bedrooms):
            continue
        if pet_allowed is True and not listing["pet_allowed"]:
            continue
        if furnished is True and not listing["furnished"]:
            continue
        results.append(listing.copy())
    return results


def get_viewing_slots(listing_id: str, date_range: str = "") -> dict[str, Any]:
    """Tra cứu các khung giờ xem nhà đang có trong lịch demo."""
    listing = next(
        (item for item in RENTAL_LISTINGS if item["listing_id"] == listing_id),
        None,
    )
    if listing is None:
        return {"error": f"Không tìm thấy listing_id '{listing_id}'."}
    return {
        "listing_id": listing_id,
        "date_range": date_range or "Các ngày gần nhất",
        "slots": VIEWING_SLOTS.get(listing_id, []),
    }


def book_viewing(
    listing_id: str,
    slot: str,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    """Đặt lịch demo; luôn yêu cầu xác nhận rõ ràng từ ứng dụng."""
    if not user_confirmed:
        return {"error": "Cần xác nhận của người dùng trước khi đặt lịch."}
    schedule = get_viewing_slots(listing_id)
    if schedule.get("error"):
        return schedule
    if slot not in schedule["slots"]:
        return {"error": f"Khung giờ '{slot}' không còn trong lịch khả dụng."}
    confirmation_code = f"VIEW-{listing_id}-{datetime.now().strftime('%H%M%S')}"
    return {
        "status": "confirmed",
        "listing_id": listing_id,
        "slot": slot,
        "confirmation_code": confirmation_code,
    }


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "search_flights": search_flights,
    "search_rentals": search_rentals,
    "get_viewing_slots": get_viewing_slots,
    "book_viewing": book_viewing,
}
