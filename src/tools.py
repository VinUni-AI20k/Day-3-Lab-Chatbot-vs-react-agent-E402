"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Trợ lý tra cứu đơn hàng và xử lý đổi trả (E-commerce Order & Returns Assistant)
"""

import json


def get_order_status(order_id: str) -> str:
    """
    Tra cứu trạng thái chi tiết của một đơn hàng dựa trên Mã đơn hàng (Order ID).
    
    Args:
        order_id (str): Mã đơn hàng cần kiểm tra (Ví dụ: 'DH123', 'DH456', 'DH789')
        
    Returns:
        str: Chuỗi thông tin chi tiết về đơn hàng (JSON hoặc thông báo lỗi)
    """
    try:
        id_clean = order_id.strip().upper()
        
        # Giả lập database đơn hàng
        orders_db = {
            "DH123": {
                "status": "Đã giao thành công",
                "delivery_date": "2026-03-01",  # Đơn hàng mới giao gần đây
                "category": "Thời trang",
                "item": "Áo khoác gió Unisex",
                "price": "350,000 VNĐ"
            },
            "DH456": {
                "status": "Đang vận chuyển",
                "delivery_date": None,
                "category": "Điện tử",
                "item": "Tai nghe Bluetooth",
                "price": "1,200,000 VNĐ"
            },
            "DH789": {
                "status": "Đã giao thành công",
                "delivery_date": "2025-12-15",  # Đơn hàng đã giao quá lâu
                "category": "Mỹ phẩm",
                "item": "Kem chống nắng SPF50",
                "price": "450,000 VNĐ"
            }
        }
        
        if id_clean in orders_db:
            # Trả về chuỗi JSON để Agent dễ phân tích thông số
            return json.dumps(orders_db[id_clean], ensure_ascii=False)
            
        return f"LỖI: Không tìm thấy mã đơn hàng '{order_id}' trong hệ thống."
        
    except Exception as e:
        return f"LỖI: Đã xảy ra sự cố khi truy vấn đơn hàng: {str(e)}"


def check_return_policy(category: str) -> str:
    """
    Tra cứu chính sách đổi trả của cửa hàng dựa trên Ngành hàng.
    
    Args:
        category (str): Ngành hàng của sản phẩm (Ví dụ: 'Thời trang', 'Điện tử', 'Mỹ phẩm')
        
    Returns:
        str: Quy định đổi trả cụ thể cho ngành hàng đó
    """
    try:
        cat_lower = category.strip().lower()
        
        if "thời trang" in cat_lower or "quần áo" in cat_lower:
            return "Chính sách THỜI TRANG: Cho phép đổi trả trong vòng 7 ngày kể từ ngày giao hàng. Sản phẩm phải còn nguyên mác, chưa qua sử dụng."
        elif "điện tử" in cat_lower or "thiết bị" in cat_lower:
            return "Chính sách ĐIỆN TỬ: Cho phép đổi trả trong vòng 3 ngày nếu có lỗi từ nhà sản xuất. Yêu cầu có video khui hộp (unboxing)."
        elif "mỹ phẩm" in cat_lower:
            return "Chính sách MỸ PHẨM: Không hỗ trợ đổi trả nếu sản phẩm đã bị bóc màng co hoặc đã mở nắp sử dụng (trừ trường hợp kích ứng có chứng nhận y tế)."
        else:
            return f"LỖI: Ngành hàng '{category}' không thuộc danh mục hỗ trợ đổi trả tự động hoặc không tồn tại."
            
    except Exception as e:
        return f"LỖI: Đã xảy ra sự cố khi kiểm tra chính sách: {str(e)}"


def create_return_request(order_id: str, reason: str) -> str:
    """
    Tạo một yêu cầu đổi trả mới cho đơn hàng.
    
    Args:
        order_id (str): Mã đơn hàng muốn đổi trả
        reason (str): Lý do đổi trả sản phẩm (Ví dụ: 'Sai kích cỡ', 'Lỗi kỹ thuật')
        
    Returns:
        str: Kết quả xử lý yêu cầu đổi trả (thành công kèm mã yêu cầu hoặc thất bại)
    """
    try:
        id_clean = order_id.strip().upper()
        reason_clean = reason.strip()
        
        if not id_clean:
            return "LỖI: Thiếu mã đơn hàng để tạo yêu cầu đổi trả."
        if not reason_clean:
            return "LỖI: Vui lòng cung cấp lý do đổi trả rõ ràng."
            
        # Giả lập kiểm tra sơ bộ trước khi tạo yêu cầu
        # Ở đây, ta tự động từ chối nếu là đơn hàng DH789 vì đã quá hạn đổi trả
        if id_clean == "DH789":
            return "LỖI TẠO YÊU CẦU: Hệ thống từ chối do đơn hàng DH789 đã vượt quá thời hạn đổi trả quy định."
            
        # Tạo mã yêu cầu ngẫu nhiên/giả lập
        request_id = f"YCDT-{id_clean[-3:]}-99"
        return f"THÀNH CÔNG: Đã tạo yêu cầu đổi trả {request_id} cho đơn hàng {id_clean}. Lý do ghi nhận: '{reason_clean}'. Nhân viên sẽ liên hệ lại trong vòng 24 giờ."
        
    except Exception as e:
        return f"LỖI: Đã xảy ra sự cố khi tạo yêu cầu đổi trả: {str(e)}"


# ==========================================
# ĐĂNG KÝ DANH SÁCH TOOL (REGISTRY)
# ==========================================
AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "check_return_policy": check_return_policy,
    "create_return_request": create_return_request,
}


# ==========================================
# CHẠY THỬ ĐỘC LẬP (TESTING)
# ==========================================
if __name__ == "__main__":
    print("--- BẮT ĐẦU KIỂM THỬ ĐỘC LẬP CÁC TOOL ĐỔI TRẢ ---")
    
    # 1. Test get_order_status
    print("\n[Test 1] Tra cứu đơn hàng tồn tại:")
    print(get_order_status("DH123"))
    print("\n[Test 2] Tra cứu đơn hàng KHÔNG tồn tại:")
    print(get_order_status("DH000"))
    
    # 2. Test check_return_policy
    print("\n[Test 3] Kiểm tra chính sách ngành hàng:")
    print(check_return_policy("Thời trang"))
    
    # 3. Test create_return_request
    print("\n[Test 4] Tạo yêu cầu đổi trả hợp lệ:")
    print(create_return_request("DH123", "Mặc bị chật size"))
    print("\n[Test 5] Tạo yêu cầu đổi trả cho đơn đã quá hạn:")
    print(create_return_request("DH789", "Không thích nữa"))
    
    print("\n--- HOÀN THÀNH KIỂM THỬ ---")