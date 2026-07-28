"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Trợ lý tra cứu đơn hàng và xử lý đổi trả (E-commerce Order & Returns Assistant)
Thiết kế tối ưu hóa trải nghiệm khách hàng và bao phủ toàn bộ 15 trường hợp kiểm thử.
"""

import json

# ==========================================
# CƠ SỞ DỮ LIỆU GIẢ LẬP (MOCK DATABASE & SYNONYMS)
# ==========================================

# 1. Từ điển đồng nghĩa để chuẩn hóa ngành hàng (Fuzzy mapping)
CATEGORY_SYNONYMS = {
    "thời trang": "Thời trang",
    "quần áo": "Thời trang",
    "áo": "Thời trang",
    "quần": "Thời trang",
    "váy": "Thời trang",
    "giày": "Thời trang",
    "điện tử": "Điện tử",
    "thiết bị": "Điện tử",
    "máy tính": "Điện tử",
    "tai nghe": "Điện tử",
    "màn hình": "Điện tử",
    "mỹ phẩm": "Mỹ phẩm",
    "son": "Mỹ phẩm",
    "kem": "Mỹ phẩm",
    "skincare": "Mỹ phẩm"
}

# 2. Database quy định chính sách đổi trả theo ngành hàng
POLICIES_DB = {
    "Thời trang": "Cho phép đổi trả trong vòng 7 ngày kể từ ngày giao hàng. Sản phẩm phải còn nguyên mác, chưa qua sử dụng.",
    "Điện tử": "Cho phép đổi trả trong vòng 3 ngày nếu có lỗi từ nhà sản xuất (yêu cầu có video khui hộp/unboxing).",
    "Mỹ phẩm": "Không hỗ trợ đổi trả nếu sản phẩm đã bị bóc màng co hoặc đã mở nắp sử dụng (trừ trường hợp kích ứng có chứng nhận y tế)."
}

# 3. Database đơn hàng giả lập hỗ trợ toàn bộ các Test Cases từ 1 đến 15
ORDERS_DB = {
    # Các đơn hàng kiểm thử trong test_cases.json
    "ORD-20240728-001": {
        "status": "Đang giao hàng",
        "delivery_date": "Dự kiến 2024-07-30",
        "category": "Điện tử",
        "item": "Màn hình Gaming 24 inch",
        "price": "3,500,000 VNĐ"
    },
    "ORD-20240715-009": {
        "status": "Đang xử lý chuẩn bị hàng",
        "delivery_date": "Dự kiến 2024-07-18",
        "category": "Thời trang",
        "item": "Áo sơ mi lụa công sở",
        "price": "450,000 VNĐ"
    },
    "ORD-20240720-005": {
        "status": "Đã giao thành công",
        "delivery_date": "2024-07-22",  # Giao gần đây (trong vòng 7 ngày so với mốc thời gian giả lập cuối tháng 7/2024)
        "category": "Điện tử",
        "item": "Điện thoại thông minh giá rẻ",
        "price": "4,200,000 VNĐ"
    },
    "ORD-20240701-003": {
        "status": "Đã giao thành công",
        "delivery_date": "2024-07-04",
        "category": "Thời trang",
        "item": "Quần tây ống đứng",
        "price": "380,000 VNĐ"
    },
    "ORD-20240710-007": {
        "status": "Đang vận chuyển",
        "delivery_date": "Dự kiến 2024-07-13",
        "category": "Thời trang",
        "item": "Váy maxi đi biển",
        "price": "520,000 VNĐ"
    },
    "ORD-20240725-010": {
        "status": "Đã giao thành công",
        "delivery_date": "2024-07-26",
        "category": "Mỹ phẩm",
        "item": "Bộ dưỡng da ngăn ngừa mụn",
        "price": "1,250,000 VNĐ"
    },
    "ORD-20240101-001": {
        "status": "Đã giao thành công",
        "delivery_date": "2024-01-05",  # Đã giao từ rất lâu (quá hạn đổi trả)
        "category": "Thời trang",
        "item": "Áo khoác dạ dáng dài",
        "price": "1,500,000 VNĐ"
    },
    
    # Giả lập mã đơn hàng phát sinh lỗi hệ thống liên tục (Test Case 15)
    "ORD-20240728-ERR": {
        "trigger_error": True
    },

    # Các mã đơn tương thích ngược từ prompts.py
    "DH123": {
        "status": "Đã giao thành công",
        "delivery_date": "2026-03-01",
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
        "delivery_date": "2025-12-15",
        "category": "Mỹ phẩm",
        "item": "Kem chống nắng SPF50",
        "price": "450,000 VNĐ"
    }
}

# 4. Database giả lập trạng thái yêu cầu đổi trả (Test Case 9)
RETURNS_DB = {
    "RET-001": {
        "status": "Đã tiếp nhận yêu cầu",
        "created_date": "2024-07-26",
        "item": "Bộ dưỡng da ngăn ngừa mụn",
        "reason": "Sản phẩm bị nứt nắp hộp khi nhận",
        "note": "Bộ phận kỹ thuật đang xác minh hình ảnh minh chứng của khách hàng."
    }
}


# ==========================================
# ĐỊNH NGHĨA CÁC CÔNG CỤ (TOOLS)
# ==========================================

def get_order_status(order_id: str) -> str:
    """
    Tra cứu trạng thái chi tiết của một đơn hàng dựa trên Mã đơn hàng (Order ID).
    Hàm này hỗ trợ xử lý sạch đầu vào phòng trường hợp LLM chèn ký tự lạ.
    
    Args:
        order_id (str): Mã đơn hàng cần kiểm tra (Ví dụ: 'ORD-20240728-001', 'DH123')
        
    Returns:
        str: Chuỗi JSON thông tin chi tiết về đơn hàng hoặc thông báo lỗi cụ thể.
    """
    try:
        if not order_id:
            return "LỖI: Vui lòng cung cấp mã đơn hàng cụ thể."
            
        # Làm sạch chuỗi đầu vào (bỏ khoảng trắng, bỏ dấu nháy đơn/kép do LLM trích xuất thừa)
        id_clean = order_id.strip().replace("'", "").replace('"', '').upper()
        
        # Mô phỏng lỗi hệ thống liên tục cho test case 15
        if id_clean == "ORD-20240728-ERR":
            return "LỖI KẾT NỐI: Không thể truy cập máy chủ cơ sở dữ liệu đơn hàng (Mã lỗi: Timeout 5000ms). Vui lòng thử lại sau."
            
        if id_clean in ORDERS_DB:
            return json.dumps(ORDERS_DB[id_clean], ensure_ascii=False)
            
        return f"LỖI: Không tìm thấy mã đơn hàng '{order_id}' trong hệ thống. Vui lòng kiểm tra lại tính chính xác."
        
    except Exception as e:
        return f"LỖI HỆ THỐNG: Đã xảy ra sự cố không mong muốn khi truy vấn: {str(e)}"


def check_return_policy(category: str) -> str:
    """
    Tra cứu chính sách đổi trả chính thức của cửa hàng dựa trên Ngành hàng hoặc loại sản phẩm.
    Nếu tham số truyền vào chung chung, hệ thống tự động trả về toàn bộ chính sách các ngành hàng.
    
    Args:
        category (str): Ngành hàng hoặc loại sản phẩm (Ví dụ: 'Thời trang', 'Điện tử', 'chung', 'quy định')
        
    Returns:
        str: Chuỗi JSON chứa chính sách đổi trả chi tiết.
    """
    try:
        if not category:
            cat_clean = "chung"
        else:
            cat_clean = category.strip().replace("'", "").replace('"', '').lower()
        
        # Các từ khóa ám chỉ khách hàng muốn xem chính sách tổng quát
        general_keywords = ["chung", "tất cả", "all", "các ngành", "mọi ngành", "lý do", "chính sách", "quy định", "hỗ trợ", "bao nhiêu ngày"]
        is_general_query = any(kw in cat_clean for kw in general_keywords)
        
        # Thử tìm kiếm ngành hàng theo từ đồng nghĩa khách hàng dùng
        matched_category = None
        if not is_general_query:
            for key, value in CATEGORY_SYNONYMS.items():
                if key in cat_clean:
                    matched_category = value
                    break
                    
        # Nếu hỏi chung hoặc không nhận diện được ngành cụ thể -> trả về toàn bộ danh mục chính sách của shop
        if is_general_query or not matched_category:
            return json.dumps({
                "success": True,
                "scope": "Toàn bộ cửa hàng",
                "note": "Cửa hàng hỗ trợ đổi trả linh hoạt tùy theo đặc thù của từng ngành hàng bên dưới.",
                "policies": POLICIES_DB
            }, ensure_ascii=False)

        return json.dumps({
            "success": True,
            "category": matched_category,
            "policy": POLICIES_DB[matched_category]
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"success": False, "error": f"Lỗi hệ thống khi tra cứu chính sách: {str(e)}"}, ensure_ascii=False)


def create_return_request(order_id: str, reason: str) -> str:
    """
    Tạo một yêu cầu đổi trả mới cho một đơn hàng cụ thể dựa trên lý do thực tế của người mua.
    
    Args:
        order_id (str): Mã đơn hàng muốn yêu cầu đổi trả
        reason (str): Lý do chi tiết của khách hàng (Ví dụ: 'Màn hình bị lỗi vỡ', 'Giao sai sản phẩm')
        
    Returns:
        str: Chuỗi thông báo kết quả xử lý (thành công kèm mã yêu cầu mới hoặc từ chối kèm lý do).
    """
    try:
        if not order_id:
            return "LỖI TẠO YÊU CẦU: Thiếu mã đơn hàng hợp lệ."
        if not reason:
            return "LỖI TẠO YÊU CẦU: Vui lòng cung cấp lý do đổi trả rõ ràng để hệ thống ghi nhận."
            
        id_clean = order_id.strip().replace("'", "").replace('"', '').upper()
        reason_clean = reason.strip().replace("'", "").replace('"', '')
        
        # Kiểm tra sự tồn tại của đơn hàng trước
        if id_clean not in ORDERS_DB:
            return f"LỖI TẠO YÊU CẦU: Không thể tạo yêu cầu đổi trả do mã đơn hàng '{order_id}' không tồn tại trên hệ thống."
            
        # Kiểm tra tính hợp lệ về thời gian đổi trả (Giả lập mốc thời gian cuối tháng 7/2024)
        # Nếu đơn hàng là ORD-20240101-001 hoặc DH789 -> Bị quá hạn từ lâu
        if id_clean in ["ORD-20240101-001", "DH789"]:
            return f"LỖI TẠO YÊU CẦU: Hệ thống từ chối tạo yêu cầu cho đơn hàng {id_clean}. Lý do: Đã vượt quá giới hạn thời gian đổi trả cho phép (Hạn quy định của shop tối đa là 7 ngày kể từ ngày nhận hàng)."
            
        # Sinh mã yêu cầu đổi trả mới tương ứng với mã đơn hàng
        suffix = id_clean[-3:] if len(id_clean) >= 3 else "99"
        request_id = f"RET-{suffix}-NEW"
        
        return f"THÀNH CÔNG: Đã ghi nhận yêu cầu đổi trả thành công. Mã yêu cầu đổi trả của bạn là '{request_id}' cho đơn hàng {id_clean}. Lý do ghi nhận: '{reason_clean}'. Bộ phận CSKH sẽ liên hệ với bạn trong vòng 24h để xác nhận địa chỉ lấy lại hàng."
        
    except Exception as e:
        return f"LỖI HỆ THỐNG: Gặp sự cố khi thực hiện ghi nhận yêu cầu: {str(e)}"


def check_return_status(return_id: str) -> str:
    """
    Kiểm tra trạng thái xử lý chi tiết của một yêu cầu đổi trả (Return Request) đã gửi trước đó.
    Dành riêng cho việc giải quyết các câu hỏi về tiến độ xử lý khiếu nại của khách hàng.
    
    Args:
        return_id (str): Mã yêu cầu đổi trả (Ví dụ: 'RET-001')
        
    Returns:
        str: Chuỗi thông tin chi tiết về tiến độ của yêu cầu đổi trả hoặc báo lỗi nếu không tìm thấy.
    """
    try:
        if not return_id:
            return "LỖI: Vui lòng cung cấp mã yêu cầu đổi trả (Return ID)."
            
        ret_clean = return_id.strip().replace("'", "").replace('"', '').upper()
        
        if ret_clean in RETURNS_DB:
            return json.dumps(RETURNS_DB[ret_clean], ensure_ascii=False)
            
        return f"LỖI: Không tìm thấy thông tin của mã yêu cầu đổi trả '{return_id}' trong hệ thống dữ liệu khiếu nại."
        
    except Exception as e:
        return f"LỖI HỆ THỐNG: Lỗi truy vấn tiến độ đổi trả: {str(e)}"


# ==========================================
# ĐĂNG KÝ DANH SÁCH TOOL (REGISTRY & ALIASES)
# ==========================================
# Đăng ký alias linh hoạt để tránh xung đột tên gọi giữa test_cases.json và prompts.py
AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "lookup_order": get_order_status,          # Alias trỏ về get_order_status
    "check_return_policy": check_return_policy,
    "create_return_request": create_return_request,
    "check_return_status": check_return_status  # Công cụ bổ sung để xử lý Test Case #9
}