"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

import json
import os

def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "datamock.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def search_properties(city: str = "", district: str = "", type: str = "", max_price: int = 999999999) -> str:
    """
    Tra cứu danh sách các phòng trọ/căn hộ thỏa mãn điều kiện.
    
    Args:
        city (str): Thành phố (vd: 'Hà Nội', 'Hồ Chí Minh'). Bỏ trống nếu không chắc.
        district (str): Quận/Huyện (vd: 'Cầu Giấy', 'Đống Đa'). Bỏ trống nếu không chắc.
        type (str): Loại phòng (vd: 'phòng trọ', 'căn hộ mini', 'nhà nguyên căn'). Bỏ trống để tìm tất cả.
        max_price (int): Mức giá tối đa mong muốn (VNĐ). Mặc định là 999999999.
        
    Returns:
        str: Danh sách tóm tắt các căn thỏa mãn.
    """
    data = load_data()
    results = []
    for item in data:
        if item.get("status") != "available":
            continue
            
        c = item.get("address", {}).get("city", "").lower()
        d = item.get("address", {}).get("district", "").lower()
        t = item.get("type", "").lower()
        p = item.get("price", 999999999)
        
        if city and city.lower() not in c:
            continue
        if district and district.lower() not in d:
            continue
        if type and type.lower() not in t:
            continue
        if p > max_price:
            continue
            
        results.append(item)
    
    if not results:
        return f"Không tìm thấy kết quả nào phù hợp ở {district}, {city} với giá dưới {max_price} VNĐ."
        
    # Chỉ trả về tối đa 5 kết quả đầu tiên để tránh bị quá tải ngữ cảnh LLM
    top_results = results[:5]
    res_str = f"Tìm thấy {len(results)} kết quả. Dưới đây là 5 lựa chọn tốt nhất:\n"
    for r in top_results:
        res_str += f"- ID: {r['id']} | Tên: {r['title']} | Giá: {r['price']} VNĐ | Loại: {r['type']}\n"
    
    res_str += "\n(Gợi ý: Dùng tool check_property_details để xem tiện ích và lịch trống của 1 ID cụ thể)"
    return res_str

def check_property_details(property_id: str) -> str:
    """
    Xem thông tin chi tiết (tiện ích, mô tả, lịch trống) của 1 căn cụ thể.
    
    Args:
        property_id (str): Mã căn (ví dụ: PROP-0012)
        
    Returns:
        str: Thông tin chi tiết của căn nhà.
    """
    data = load_data()
    for item in data:
        if item.get("id") == property_id:
            amens = ", ".join(item.get("amenities", ["Không rõ"]))
            desc = item.get("description", "Không có mô tả.")
            slots = ", ".join(item.get("viewing_slots", []))
            if not slots:
                slots = "Hiện không có lịch trống để xem nhà."
            
            return (
                f"Chi tiết căn {property_id}:\n"
                f"- Tiện ích: {amens}\n"
                f"- Mô tả: {desc}\n"
                f"- Lịch trống có thể xem: {slots}\n"
                f"- Liên hệ chủ nhà: {item.get('contact', {}).get('name')} - {item.get('contact', {}).get('phone')}"
            )
    return f"Lỗi: Không tìm thấy căn nhà nào có mã {property_id}."

def book_viewing(property_id: str, time_slot: str, user_name: str, phone: str) -> str:
    """
    Đặt lịch xem nhà và cập nhật lại file datamock.json.
    
    Args:
        property_id (str): Mã căn (ví dụ: PROP-0012).
        time_slot (str): Thời gian muốn xem (vd: '2026-08-01T10:30:00').
        user_name (str): Tên khách hàng.
        phone (str): Số điện thoại khách hàng.
        
    Returns:
        str: Kết quả đặt lịch (thành công hoặc thất bại).
    """
    data = load_data()
    for item in data:
        if item.get("id") == property_id:
            slots = item.get("viewing_slots", [])
            if time_slot in slots:
                # Xóa slot này khỏi danh sách
                slots.remove(time_slot)
                item["viewing_slots"] = slots
                
                # Ghi đè lại vào datamock.json
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                data_path = os.path.join(base_dir, "data", "datamock.json")
                with open(data_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                return f"ĐẶT LỊCH THÀNH CÔNG! Đã xác nhận lịch xem căn {property_id} lúc {time_slot} cho khách hàng {user_name} ({phone}). Hệ thống đã loại bỏ giờ này khỏi lịch trống."
            else:
                return f"Lỗi: Khung giờ {time_slot} không khả dụng cho căn {property_id}. Vui lòng chọn khung giờ khác từ check_property_details."
                
    return f"Lỗi: Không tìm thấy căn nhà nào có mã {property_id} để đặt lịch."


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_properties": search_properties,
    "check_property_details": check_property_details,
    "book_viewing": book_viewing,
}
