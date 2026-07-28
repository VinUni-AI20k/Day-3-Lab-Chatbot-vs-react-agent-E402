"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả (Dữ liệu động, không dùng Mock DB cứng)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

def get_order_info(order_id: str) -> str:
    """
    Tra cứu thông tin chi tiết của một đơn hàng theo Mã đơn hàng (order_id).
    
    Args:
        order_id (str): Mã đơn hàng cần tra cứu (Ví dụ: 'ORD-123', 'HD98765')
        
    Returns:
        str: Thông tin chi tiết hệ thống trả về cho mã đơn hàng tương ứng.
    """
    order_clean = order_id.strip().upper()
    if not order_clean:
        return "LỖI: Mã đơn hàng không được để trống."
        
    return (
        f"📦 THÔNG TIN ĐƠN HÀNG [{order_clean}]:\n"
        f"- Trạng thái: Đã giao hàng thành công\n"
        f"- Ngày nhận hàng: 3 ngày trước\n"
        f"- Ngành hàng: Thiết bị điện tử / Thời trang\n"
        f"- Tình trạng đổi trả: Trong thời hạn hỗ trợ đổi trả (dưới 7 ngày)"
    )


def check_return_policy(category: str, days_since_purchase: int) -> str:
    """
    Tra cứu quy định và điều kiện đổi trả theo Ngành hàng và Số ngày kể từ khi nhận hàng.
    
    Args:
        category (str): Ngành hàng của sản phẩm (Ví dụ: 'Điện tử', 'Thời trang', 'Thực phẩm tươi sống', 'Mỹ phẩm')
        days_since_purchase (int): Số ngày tính từ khi khách nhận hàng đến thời điểm hiện tại.
        
    Returns:
        str: Kết quả kiểm tra quy định đổi trả chi tiết.
    """
    cat_lower = category.lower()
    
    if any(k in cat_lower for k in ["thực phẩm", "tươi sống", "đông lạnh", "đồ ăn"]):
        return f"❌ KHÔNG ÁP DỤNG: Sản phẩm thuộc ngành '{category}' là hàng tiêu dùng/tươi sống, KHÔNG hỗ trợ đổi trả theo chính sách."
        
    elif any(k in cat_lower for k in ["điện tử", "công nghệ", "thiết bị", "gia dụng"]):
        max_days = 7
        if days_since_purchase <= max_days:
            return f"✅ ĐỦ ĐIỀU KIỆN: Ngành '{category}' cho phép đổi trả trong {max_days} ngày. Đơn hàng ({days_since_purchase} ngày) ĐỦ ĐIỀU KIỆN (Yêu cầu nguyên tem, vỏ hộp)."
        return f"❌ QUÁ THỜI HẠN: Ngành '{category}' chỉ hỗ trợ đổi trả trong {max_days} ngày. Đơn hàng ({days_since_purchase} ngày) đã quá hạn."
        
    elif any(k in cat_lower for k in ["thời trang", "quần áo", "giày dép", "phụ kiện"]):
        max_days = 14
        if days_since_purchase <= max_days:
            return f"✅ ĐỦ ĐIỀU KIỆN: Ngành '{category}' cho phép đổi trả trong {max_days} ngày. Đơn hàng ({days_since_purchase} ngày) ĐỦ ĐIỀU KIỆN (Yêu cầu nguyên mác, chưa qua sử dụng)."
        return f"❌ QUÁ THỜI HẠN: Ngành '{category}' chỉ hỗ trợ đổi trả trong {max_days} ngày. Đơn hàng ({days_since_purchase} ngày) đã quá hạn."
        
    else:
        max_days = 7
        if days_since_purchase <= max_days:
            return f"✅ ĐỦ ĐIỀU KIỆN: Sản phẩm ngành '{category}' được hỗ trợ đổi trả trong {max_days} ngày."
        return f"❌ QUÁ THỜI HẠN: Sản phẩm ngành '{category}' đã quá thời hạn đổi trả ({days_since_purchase}/{max_days} ngày)."


def calculate_refund_amount(order_id: str, product_price: float, reason: str) -> str:
    """
    Tính toán số tiền hoàn lại cho khách hàng dựa trên giá trị sản phẩm và lý do đổi trả.
    
    Args:
        order_id (str): Mã đơn hàng
        product_price (float): Giá trị sản phẩm (VNĐ)
        reason (str): Lý do trả hàng (Ví dụ: 'Lỗi nhà sản xuất', 'Giao sai hàng', 'Đổi ý không thích')
        
    Returns:
        str: Số tiền hoàn lại dự kiến và các khoản phí trừ (nếu có).
    """
    order_clean = order_id.strip().upper()
    reason_lower = reason.lower()
    
    # Nếu lỗi do shop/sản phẩm: Miễn phí thu hồi
    if any(k in reason_lower for k in ["lỗi", "hỏng", "sai", "vỡ", "kém", "tì vết"]):
        shipping_fee = 0.0
        refund = product_price
        note = "Miễn phí vận chuyển thu hồi (Lỗi do nhà bán/sản phẩm)."
    else:
        # Khách đổi ý: Trừ phí ship thu hồi 30,000 VNĐ
        shipping_fee = 30000.0
        refund = max(0.0, product_price - shipping_fee)
        note = f"Trừ {shipping_fee:,.0f} VNĐ phí vận chuyển thu hồi (Do lý do cá nhân từ khách hàng)."
        
    return (
        f"💰 BẢNG TÍNH TIỀN HOÀN DỰ KIẾN [{order_clean}]:\n"
        f"- Giá trị sản phẩm: {product_price:,.0f} VNĐ\n"
        f"- Lý do đổi trả: {reason}\n"
        f"- Chi phí vận chuyển: {note}\n"
        f"👉 TỔNG TIỀN HOÀN LẠI DỰ KIẾN: {refund:,.0f} VNĐ"
    )


def create_return_request(order_id: str, items_to_return: str, reason: str, bank_account: str) -> str:
    """
    Khởi tạo yêu cầu đổi/trả hàng chính thức trên hệ thống và cấp mã vận đơn gửi hàng trả.
    
    Args:
        order_id (str): Mã đơn hàng
        items_to_return (str): Sản phẩm cần đổi/trả
        reason (str): Lý do đổi trả
        bank_account (str): Số tài khoản nhận tiền hoàn (Ví dụ: 'MBBank - 0987654321 - NGUYEN VAN A')
        
    Returns:
        str: Kết quả tạo yêu cầu đổi trả, mã RMA và mã vận đơn gửi trả.
    """
    order_clean = order_id.strip().upper()
    if not order_clean:
        return "LỖI: Mã đơn hàng không hợp lệ."
        
    rma_code = f"RMA-{order_clean}"
    tracking_return = f"RET-GHN-{order_clean}"
    
    return (
        f"🎉 THÀNH CÔNG: Đã khởi tạo yêu cầu đổi trả cho đơn hàng [{order_clean}]!\n"
        f"- Mã Yêu Cầu (RMA): {rma_code}\n"
        f"- Sản phẩm trả: {items_to_return}\n"
        f"- Lý do: {reason}\n"
        f"- Tài khoản nhận hoàn tiền: {bank_account}\n"
        f"- Mã vận đơn thu hồi hàng: {tracking_return}\n"
        f"📌 Hướng dẫn: Đóng gói sản phẩm, dán mã {rma_code} bên ngoài kiện hàng. Shipper sẽ liên hệ lấy hàng trong 24h."
    )


def track_shipping_status(tracking_number: str) -> str:
    """
    Tra cứu tiến trình vận chuyển của một mã vận đơn (kiện giao đi hoặc kiện thu hồi đổi trả).
    
    Args:
        tracking_number (str): Mã vận đơn cần tra cứu (Ví dụ: 'GHN987654', 'RET-GHN-ORD123')
        
    Returns:
        str: Trạng thái chi tiết hành trình vận chuyển.
    """
    tn_clean = tracking_number.strip().upper()
    if not tn_clean:
        return "LỖI: Mã vận đơn không được để trống."
        
    return (
        f"🚚 HÀNH TRÌNH VẬN CHUYỂN [{tn_clean}]:\n"
        f"- Trạng thái: Đang trong tiến trình luân chuyển bưu kiện.\n"
        f"- Cập nhật mới nhất: Bưu kiện đã rời Kho tổng Tân Bình, đang chuyển sang Bưu cục Giao nhận."
    )


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_order_info": get_order_info,
    "check_return_policy": check_return_policy,
    "calculate_refund_amount": calculate_refund_amount,
    "create_return_request": create_return_request,
    "track_shipping_status": track_shipping_status,
}
