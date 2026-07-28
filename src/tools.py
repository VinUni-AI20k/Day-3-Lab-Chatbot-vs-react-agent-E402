import json
import uuid

# ===============================================================
# MỐC 1: DATABASE GIẢ LẬP DANH SÁCH PHÒNG TRỌ (MOCK DATA)
# ===============================================================
MOCK_ROOMS = [
    {"id": "R01", "location": "Quan 1", "price": 5000000, "status": "available", "address": "123 Nguyen Hue", "contact": "0901234567"},
    {"id": "R02", "location": "Binh Thanh", "price": 3000000, "status": "available", "address": "45 Xo Viet Nghe Tinh", "contact": "0912345678"},
    {"id": "R03", "location": "Quan 7", "price": 4000000, "status": "rented", "address": "789 Nguyen Van Linh", "contact": "0923456789"}
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
            {"id": r["id"], "location": r["location"], "price": r["price"]}
            for r in MOCK_ROOMS 
            if r["location"].lower() == location.lower() and r["price"] <= max_price and r["status"] == "available"
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
        room_exists = any(r["id"] == room_id and r["status"] == "available" for r in MOCK_ROOMS)
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