import json
import uuid
import os
from datetime import datetime

# ===============================================================
# MỐC 1: DATABASE GIẢ LẬP DANH SÁCH PHÒNG TRỌ (MOCK DATA)
# ===============================================================
MOCK_ROOMS = []
try:
    # Xác định đường dẫn tuyệt đối đến file data/mock.json
    mock_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mock.json")
    with open(mock_file_path, "r", encoding="utf-8") as f:
        mock_data = json.load(f)
        MOCK_ROOMS = mock_data.get("rooms", [])
except Exception as e:
    print(f"⚠️ Cảnh báo: Không thể tải file mock.json - Lỗi: {e}")

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
        # Kiểm tra xem phòng có tồn tại không
        room = next((r for r in MOCK_ROOMS if r["id"] == room_id), None)
        if not room:
            return json.dumps({"status": "error", "message": f"Phòng {room_id} không tồn tại."}, ensure_ascii=False)
            
        if not room.get("available", False):
            return json.dumps({"status": "error", "message": f"Phòng {room_id} đã được cho thuê."}, ensure_ascii=False)
            
        # Kiểm tra ngày nghỉ (days_off) của chủ nhà
        try:
            dt = datetime.strptime(date, "%d/%m/%Y")
            # Chuyển đổi weekday() của Python (0=Thứ 2, 6=Chủ nhật) sang format yêu cầu (0=Chủ nhật, 1=Thứ 2)
            day_index = (dt.weekday() + 1) % 7
            
            viewing_schedule = room.get("viewing_schedule", {})
            days_off = viewing_schedule.get("days_off", [])
            
            if day_index in days_off:
                return json.dumps({"status": "error", "message": f"Chủ nhà không nhận lịch xem phòng vào ngày {date}. Xin vui lòng đổi sang ngày khác."}, ensure_ascii=False)
        except ValueError:
            return json.dumps({"status": "error", "message": "Định dạng ngày không hợp lệ. Vui lòng dùng định dạng dd/mm/yyyy (VD: 20/11/2023)."}, ensure_ascii=False)
            
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