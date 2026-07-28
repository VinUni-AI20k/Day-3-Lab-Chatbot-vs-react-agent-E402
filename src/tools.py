import json
import uuid

# ===============================================================
# MỐC 1: DATABASE GIẢ LẬP DANH SÁCH PHÒNG TRỌ (MOCK DATA)
# ===============================================================
MOCK_ROOMS = [
    {
        "id": "NT-CG-101", "type": "phòng trọ", "location": "Cầu Giấy", 
        "price": 3500000, "bedrooms": 1, "address": "12 Dịch Vọng, Cầu Giấy", 
        "contact": "0901234567", "available": True, "amenities": ["Điều hòa", "Nóng lạnh", "Máy giặt chung"]
    },
    {
        "id": "CH-Q1-202", "type": "căn hộ mini", "location": "Quận 1", 
        "price": 8500000, "bedrooms": 1, "address": "123 Nguyễn Huệ, Quận 1", 
        "contact": "0912345678", "available": True, "amenities": ["Full nội thất", "Thang máy", "Bảo vệ 24/7"]
    },
    {
        "id": "NT-BT-303", "type": "phòng trọ", "location": "Bình Thạnh", 
        "price": 2500000, "bedrooms": 1, "address": "45 Xô Viết Nghệ Tĩnh, Bình Thạnh", 
        "contact": "0923456789", "available": False, "amenities": ["Giờ giấc tự do", "Bếp nấu ăn"]
    },
    {
        "id": "CH-Q7-404", "type": "chung cư", "location": "Quận 7", 
        "price": 12000000, "bedrooms": 2, "address": "789 Nguyễn Văn Linh, Quận 7", 
        "contact": "0934567890", "available": True, "amenities": ["Hồ bơi", "Gym", "Ban công", "Nội thất cao cấp"]
    },
    {
        "id": "NT-Q3-505", "type": "phòng trọ", "location": "Quận 3", 
        "price": 4500000, "bedrooms": 1, "address": "12 Võ Văn Tần, Quận 3", 
        "contact": "0945678901", "available": True, "amenities": ["Có gác lửng", "Ban công", "Chỗ để xe rộng"]
    },
    {
        "id": "CH-TB-606", "type": "căn hộ dịch vụ", "location": "Tân Bình", 
        "price": 6000000, "bedrooms": 1, "address": "99 Cộng Hòa, Tân Bình", 
        "contact": "0956789012", "available": True, "amenities": ["Dọn phòng", "Free wifi", "Thang máy"]
    },
    {
        "id": "NT-GV-707", "type": "ký túc xá", "location": "Gò Vấp", 
        "price": 1500000, "bedrooms": 4, "address": "55 Phan Văn Trị, Gò Vấp", 
        "contact": "0967890123", "available": True, "amenities": ["Giường tầng", "Tủ đồ cá nhân", "Bếp chung", "Máy lạnh"]
    },
    {
        "id": "CH-Q10-808", "type": "studio", "location": "Quận 10", 
        "price": 5500000, "bedrooms": 1, "address": "234 Sư Vạn Hạnh, Quận 10", 
        "contact": "0978901234", "available": False, "amenities": ["Máy lạnh", "Giường nệm", "Tủ lạnh mini"]
    },
    {
        "id": "NT-TP-909", "type": "nhà nguyên căn", "location": "Tân Phú", 
        "price": 9000000, "bedrooms": 3, "address": "77 Lũy Bán Bích, Tân Phú", 
        "contact": "0989012345", "available": True, "amenities": ["Sân phơi rộng", "2 Toilet", "Hẻm xe hơi"]
    },
    {
        "id": "CH-Q2-111", "type": "căn hộ cao cấp", "location": "Quận 2", 
        "price": 18000000, "bedrooms": 2, "address": "Thảo Điền, Quận 2", 
        "contact": "0990123456", "available": True, "amenities": ["View sông", "Hồ bơi tràn", "Bảo mật vân tay"]
    }
]

# Lưu trữ danh sách lịch hẹn
APPOINTMENTS = []

# ===============================================================
# MỐC 2 & 3: ĐỊNH NGHĨA TOOLS CÓ DOCSTRING VÀ ĐẶT BẪY LỖI (TRY/EXCEPT)
# ===============================================================

def search_rooms(location: str, max_price: int) -> str:
    """
    Tìm kiếm nhà trọ/căn hộ dựa trên khu vực và mức giá tối đa.
    
    Args:
        location: Khu vực muốn tìm (VD: "Quan 1", "Binh Thanh").
        max_price: Mức giá tối đa có thể trả (số nguyên, VD: 4000000).
        
    Returns:
        Chuỗi JSON chứa danh sách các phòng trọ phù hợp và còn trống.
    """
    try:
        results = [
            {
                "id": r["id"], "type": r["type"], "location": r["location"], 
                "price": r["price"], "bedrooms": r["bedrooms"], "amenities": r["amenities"]
            }
            for r in MOCK_ROOMS 
            if r["location"].lower() == location.lower() and r["price"] <= max_price and r["available"] == True
        ]
        
        if not results:
            return json.dumps({"status": "success", "message": "Không tìm thấy phòng phù hợp.", "data": []}, ensure_ascii=False)
            
        return json.dumps({"status": "success", "data": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Lỗi hệ thống khi tìm kiếm: {str(e)}"}, ensure_ascii=False)

def get_room_details(room_id: str) -> str:
    """
    Lấy thông tin chi tiết của một phòng trọ cụ thể bao gồm địa chỉ và số điện thoại chủ nhà.
    
    Args:
        room_id: Mã ID của phòng trọ (VD: "R01").
        
    Returns:
        Chuỗi JSON chứa thông tin chi tiết của phòng trọ.
    """
    try:
        for r in MOCK_ROOMS:
            if r["id"] == room_id:
                return json.dumps({"status": "success", "data": r}, ensure_ascii=False)
        return json.dumps({"status": "error", "message": f"Không tìm thấy phòng với ID: {room_id}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Lỗi hệ thống khi lấy chi tiết: {str(e)}"}, ensure_ascii=False)

def book_viewing_appointment(room_id: str, customer_name: str, date: str, time: str) -> str:
    """
    Đặt lịch hẹn đi xem nhà trọ.
    
    Args:
        room_id: Mã ID của phòng trọ (VD: "R01").
        customer_name: Tên của khách hàng.
        date: Ngày muốn xem nhà (VD: "20/11/2023").
        time: Thời gian muốn xem nhà (VD: "14:00").
        
    Returns:
        Chuỗi JSON xác nhận đặt lịch thành công hoặc thất bại.
    """
    try:
        # Kiểm tra xem phòng có tồn tại và còn trống không
        room_exists = any(r["id"] == room_id and r["available"] == True for r in MOCK_ROOMS)
        if not room_exists:
            return json.dumps({"status": "error", "message": f"Phòng {room_id} không tồn tại hoặc đã được cho thuê."}, ensure_ascii=False)
            
        appointment_id = str(uuid.uuid4())[:8]
        appointment = {
            "appointment_id": appointment_id,
            "room_id": room_id,
            "customer_name": customer_name,
            "date": date,
            "time": time
        }
        APPOINTMENTS.append(appointment)
        
        return json.dumps({
            "status": "success", 
            "message": f"Đặt lịch thành công cho {customer_name} xem phòng {room_id} lúc {time} ngày {date}.",
            "appointment_id": appointment_id
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Lỗi khi đặt lịch: {str(e)}"}, ensure_ascii=False)

# Xuất danh sách các tools để file app.py có thể import
TOOLS = [search_rooms, get_room_details, book_viewing_appointment]