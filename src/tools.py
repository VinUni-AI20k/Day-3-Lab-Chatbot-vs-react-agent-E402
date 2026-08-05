"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi cho chủ đề Tìm kiếm nhà trọ & Đặt lịch xem nhà.
"""

import re

# Cơ sở dữ liệu phòng trọ/căn hộ giả lập (Mock Rental Database)
RENTAL_DATABASE = [
    {
        "listing_id": "ROOM-101",
        "location": "Cầu Giấy, Hà Nội",
        "price": 4500000,
        "allow_pets": True,
        "description": "Phòng trọ khép kín tại Cầu Giấy, Hà Nội. Giá: 4.5 triệu/tháng. Diện tích 25m2, cho phép nuôi mèo."
    },
    {
        "listing_id": "ROOM-102",
        "location": "Cầu Giấy, Hà Nội",
        "price": 4800000,
        "allow_pets": True,
        "description": "Phòng trọ có ban công rộng rãi tại Cầu Giấy, Hà Nội. Giá: 4.8 triệu/tháng. Diện tích 30m2, cho phép nuôi chó mèo."
    },
    {
        "listing_id": "ROOM-103",
        "location": "Cầu Giấy, Hà Nội",
        "price": 5500000,
        "allow_pets": False,
        "description": "Phòng trọ cao cấp ngõ 105 Cầu Giấy, Hà Nội. Giá: 5.5 triệu/tháng. Diện tích 35m2, KHÔNG cho phép nuôi thú cưng."
    },
    {
        "listing_id": "APT-201",
        "location": "Bình Thạnh, TP.HCM",
        "price": 9000000,
        "allow_pets": True,
        "description": "Căn hộ dịch vụ 1 phòng ngủ tại Bình Thạnh, TP.HCM. Giá: 9 triệu/tháng. Đầy đủ nội thất, cho nuôi thú cưng."
    },
    {
        "listing_id": "APT-202",
        "location": "Bình Thạnh, TP.HCM",
        "price": 10000000,
        "allow_pets": False,
        "description": "Căn hộ chung cư mini tại Bình Thạnh, TP.HCM. Giá: 10 triệu/tháng. Ban công thoáng, KHÔNG cho nuôi thú cưng."
    },
    {
        "listing_id": "APT-203",
        "location": "Bình Thạnh, TP.HCM",
        "price": 12000000,
        "allow_pets": True,
        "description": "Căn hộ cao cấp Vinhomes Bình Thạnh, TP.HCM. Giá: 12 triệu/tháng. View sông Sài Gòn, cho phép nuôi thú cưng."
    }
]

# Cơ sở dữ liệu lịch xem nhà giả lập (Mock Viewing Slots Database)
VIEWING_SLOTS_DATABASE = {
    "ROOM-101": "Thứ Bảy (09:00 - 11:00), Chủ Nhật (14:00 - 16:00)",
    "ROOM-102": "Thứ Bảy (10:00 - 12:00), Chủ Nhật (15:00 - 17:00)",
    "ROOM-103": "Thứ Bảy (08:00 - 10:00)",
    "APT-201": "Thứ Bảy (15:00 - 17:00), Chủ Nhật (09:00 - 11:30)",
    "APT-202": "Chủ Nhật (14:00 - 16:00)",
    "APT-203": "Thứ Bảy (09:00 - 11:00, 14:00 - 16:00)"
}


def search_rentals(location: str, max_price: float = None, allow_pets: bool = None) -> str:
    """
    Tìm kiếm danh sách phòng trọ hoặc căn hộ cho thuê theo khu vực, ngân sách và yêu cầu thú cưng.
    
    Args:
        location (str): Tên khu vực cần tìm kiếm (Ví dụ: 'Cầu Giấy, Hà Nội', 'Bình Thạnh, TP.HCM')
        max_price (float, optional): Ngân sách thuê tối đa mỗi tháng tính bằng VNĐ (Ví dụ: 5000000, 10000000)
        allow_pets (bool, optional): Bộ lọc cho phép nuôi thú cưng hay không (True hoặc False)
        
    Returns:
        str: Chuỗi kết quả danh sách các phòng trọ/căn hộ tìm thấy hoặc thông báo không có kết quả hợp lệ.
    """
    if not location:
        return "LỖI: Khu vực tìm kiếm (location) không được để trống."

    loc_lower = location.lower().strip()
    results = []

    for item in RENTAL_DATABASE:
        # Kiểm tra điều kiện vị trí (chứa từ khóa tìm kiếm)
        item_loc_lower = item["location"].lower()
        if loc_lower not in item_loc_lower and not any(part in item_loc_lower for part in loc_lower.split(",")):
            # Fallback check partial matches
            match = False
            for word in loc_lower.split():
                if word in item_loc_lower:
                    match = True
                    break
            if not match:
                continue

        # Kiểm tra điều kiện giá thuê
        if max_price is not None:
            try:
                # Đề phòng trường hợp max_price truyền vào dưới dạng string từ LLM
                val_price = float(max_price)
                if item["price"] > val_price:
                    continue
            except (ValueError, TypeError):
                return f"LỖI: Giá trị ngân sách tối đa '{max_price}' không hợp lệ. Vui lòng truyền số thực."

        # Kiểm tra điều kiện nuôi thú cưng
        if allow_pets is not None:
            # Chuyển đổi linh hoạt nếu allow_pets được truyền dưới dạng string từ LLM
            if isinstance(allow_pets, str):
                allow_pets_bool = allow_pets.lower() in ("true", "1", "yes", "cho phép")
            else:
                allow_pets_bool = bool(allow_pets)
            
            if item["allow_pets"] != allow_pets_bool:
                continue

        results.append(item)

    if not results:
        # Xử lý fallback trả lỗi nghiệp vụ thay vì crash chương trình
        return f"LỖI: Không tìm thấy phòng trọ/căn hộ nào phù hợp với yêu cầu tại khu vực '{location}'."

    # Định dạng chuỗi kết quả trả về cho Agent
    output = "Danh sách căn hộ/phòng trọ tìm thấy:\n"
    for idx, res in enumerate(results, 1):
        pet_status = "Cho phép nuôi thú cưng" if res["allow_pets"] else "KHÔNG cho phép nuôi thú cưng"
        output += f"{idx}. [Mã căn: {res['listing_id']}] - {res['location']} - Giá: {res['price']:,} VNĐ/tháng - {pet_status}\n   Chi tiết: {res['description']}\n"
    
    return output.strip()


def get_viewing_slots(listing_id: str) -> str:
    """
    Tra cứu các khung giờ xem nhà còn trống vào cuối tuần cho một mã căn hộ/phòng trọ cụ thể.
    
    Args:
        listing_id (str): Mã định danh duy nhất của căn hộ/phòng trọ (Ví dụ: 'ROOM-101', 'APT-201')
        
    Returns:
        str: Các khung giờ còn trống hoặc thông báo lỗi nếu mã căn không tồn tại.
    """
    if not listing_id:
        return "LỖI: Mã căn hộ (listing_id) không được để trống."
        
    id_clean = listing_id.strip().upper()
    if id_clean in VIEWING_SLOTS_DATABASE:
        return f"Khung giờ xem nhà còn trống cuối tuần này cho căn {id_clean}: {VIEWING_SLOTS_DATABASE[id_clean]}"
    else:
        # Trả về thông báo lỗi nghiệp vụ, tránh ném ra Exception làm dừng chương trình
        return f"LỖI: Không tìm thấy listing_id '{listing_id}' trong hệ thống hoặc mã căn hộ không tồn tại."


def book_viewing(listing_id: str, date: str, time: str) -> str:
    """
    Đặt lịch hẹn xem căn hộ/phòng trọ dựa trên mã căn, ngày hẹn và giờ hẹn cụ thể.
    
    Args:
        listing_id (str): Mã định danh duy nhất của căn hộ/phòng trọ (Ví dụ: 'ROOM-101', 'APT-201')
        date (str): Ngày hẹn xem nhà theo định dạng DD/MM/YYYY (Ví dụ: '29/07/2026')
        time (str): Giờ hẹn xem nhà theo định dạng HH:MM (Ví dụ: '15:00')
        
    Returns:
        str: Chuỗi thông báo đặt lịch thành công hoặc chi tiết lỗi nghiệp vụ khi dữ liệu không hợp lệ.
    """
    # 1. Kiểm tra tồn tại của mã căn
    id_clean = listing_id.strip().upper() if listing_id else ""
    if not id_clean or id_clean not in VIEWING_SLOTS_DATABASE:
        return f"LỖI: Không tìm thấy mã căn hộ '{listing_id}' để đặt lịch xem nhà."

    # 2. Kiểm tra định dạng ngày DD/MM/YYYY
    date_pattern = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(date_pattern, date.strip()):
        return f"LỖI: Định dạng ngày '{date}' không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY (Ví dụ: 29/07/2026)."
        
    try:
        day, month, year = map(int, date.strip().split('/'))
        if not (1 <= month <= 12):
            return f"LỖI: Tháng '{month}' không hợp lệ trong ngày hẹn '{date}'."
        if not (1 <= day <= 31):
            return f"LỖI: Ngày '{day}' không hợp lệ trong ngày hẹn '{date}'."
    except Exception:
        return f"LỖI: Ngày hẹn '{date}' không đúng cấu trúc thời gian thực tế."

    # 3. Kiểm tra định dạng giờ HH:MM
    time_pattern = r"^\d{2}:\d{2}$"
    if not re.match(time_pattern, time.strip()):
        return f"LỖI: Định dạng giờ '{time}' không hợp lệ. Vui lòng sử dụng định dạng HH:MM (Ví dụ: 15:30)."
        
    try:
        hour, minute = map(int, time.strip().split(':'))
        if not (0 <= hour <= 23):
            return f"LỖI: Giờ '{hour}' không hợp lệ trong giờ hẹn '{time}'."
        if not (0 <= minute <= 59):
            return f"LỖI: Phút '{minute}' không hợp lệ trong giờ hẹn '{time}'."
    except Exception:
        return f"LỖI: Giờ hẹn '{time}' không đúng cấu trúc thời gian thực tế."

    return f"Thành công: Đã đặt lịch xem nhà cho căn {id_clean} vào ngày {date} lúc {time}."


# Danh sách các tool được đăng ký hoạt động để Agent có thể tra cứu và gọi sử dụng
AVAILABLE_TOOLS = {
    "search_rentals": search_rentals,
    "get_viewing_slots": get_viewing_slots,
    "book_viewing": book_viewing,
}
