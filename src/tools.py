"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

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


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "search_flights": search_flights,
}
