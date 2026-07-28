"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

Đề tài: Trợ lý Tra cứu Đơn hàng & Xử lý Đổi trả
"""

import json

# ============================================================
# DỮ LIỆU MẪU (Mô phỏng database đơn hàng & yêu cầu đổi trả)
# ============================================================

_ORDERS_DB = {
    "ORD-001": {
        "trang_thai": "Đã giao",
        "ngay_mua": "2026-07-20",
        "san_pham": "Áo thun nam Cotton",
        "so_luong": 2,
        "gia": 350000,
        "dia_chi": "Số 1, Đại lộ Vinhomes, Hà Nội",
    },
    "ORD-002": {
        "trang_thai": "Đang vận chuyển",
        "ngay_mua": "2026-07-25",
        "san_pham": "Điện thoại Xiaomi Redmi Note 14",
        "so_luong": 1,
        "gia": 6500000,
        "dia_chi": "123 Nguyễn Huệ, Quận 1, TP.HCM",
    },
    "ORD-003": {
        "trang_thai": "Chờ xác nhận",
        "ngay_mua": "2026-07-27",
        "san_pham": "Tai nghe Bluetooth Sony WH-1000XM5",
        "so_luong": 1,
        "gia": 4500000,
        "dia_chi": "456 Lê Lợi, Đà Nẵng",
    },
    "ORD-004": {
        "trang_thai": "Đã giao",
        "ngay_mua": "2026-07-15",
        "san_pham": "Sách 'AI Agent căn bản'",
        "so_luong": 1,
        "gia": 185000,
        "dia_chi": "789 Trần Hưng Đạo, Hà Nội",
    },
}

_RETURNS_DB = {
    "RET-001": {
        "ma_don_hang": "ORD-004",
        "ly_do": "Sách bị rách bìa",
        "trang_thai": "Đang xử lý",
        "ngay_tao": "2026-07-22",
        "phuong_thuc": "Hoàn tiền",
    },
}

_RETURN_ID_COUNTER = 1

_PRODUCTS_DB = [
    {"ma": "P001", "ten": "Áo thun nam Cotton", "gia": 175000, "ton_kho": 50},
    {"ma": "P002", "ten": "Điện thoại Xiaomi Redmi Note 14", "gia": 6500000, "ton_kho": 20},
    {"ma": "P003", "ten": "Tai nghe Bluetooth Sony WH-1000XM5", "gia": 4500000, "ton_kho": 10},
    {"ma": "P004", "ten": "Sách 'AI Agent căn bản'", "gia": 185000, "ton_kho": 100},
    {"ma": "P005", "ten": "Laptop Dell XPS 15", "gia": 35000000, "ton_kho": 5},
    {"ma": "P006", "ten": "Chuột không dây Logitech MX Master 3S", "gia": 1500000, "ton_kho": 30},
]


# ============================================================
# ĐỊNH NGHĨA CÁC TOOL
# ============================================================

def lookup_order(order_id: str) -> str:
    """
    Tra cứu thông tin chi tiết của một đơn hàng theo mã đơn.

    Name: lookup_order
    Purpose: Dùng khi người dùng muốn kiểm tra trạng thái, sản phẩm,
             ngày mua hoặc thông tin giao hàng của một đơn hàng.
             KHÔNG dùng để tạo đơn hàng mới hay xử lý đổi trả.
    Input:  order_id (str) - Mã đơn hàng (VD: 'ORD-001', 'ORD-002')
    Output: Chuỗi JSON chứa thông tin đơn hàng: trạng thái, sản phẩm,
            số lượng, giá, ngày mua, địa chỉ giao hàng.
    Error:  Trả về chuỗi lỗi nếu không tìm thấy đơn hàng hoặc mã rỗng.
    Side effect: Read-only (không thay đổi dữ liệu).
    Example:
        lookup_order("ORD-001")
        -> '{"ma_don": "ORD-001", "trang_thai": "Đã giao", ...}'
    Safety: Được bọc trong try/except, không crash khi nhập sai.
    """
    try:
        if not order_id or not order_id.strip():
            return "LỖI: Mã đơn hàng không được để trống."

        order_id = order_id.strip().upper()
        if order_id not in _ORDERS_DB:
            return (
                f"LỖI: Không tìm thấy đơn hàng với mã '{order_id}'. "
                f"Vui lòng kiểm tra lại mã đơn hàng."
            )

        order = _ORDERS_DB[order_id]
        info = {
            "ma_don": order_id,
            "trang_thai": order["trang_thai"],
            "san_pham": order["san_pham"],
            "so_luong": order["so_luong"],
            "gia": f"{order['gia']:,} VNĐ",
            "ngay_mua": order["ngay_mua"],
            "dia_chi": order["dia_chi"],
        }
        return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể tra cứu đơn hàng. Chi tiết: {str(e)}"


def check_return_eligibility(order_id: str) -> str:
    """
    Kiểm tra đơn hàng có đủ điều kiện đổi/trả hay không.

    Name: check_return_eligibility
    Purpose: Dùng khi người dùng hỏi "có thể đổi trả đơn này không?"
             hoặc muốn biết chính sách đổi trả. Tool này CHỈ kiểm tra,
             không tạo yêu cầu đổi trả.
    Input:  order_id (str) - Mã đơn hàng cần kiểm tra.
    Output: Chuỗi thông báo cho biết đơn hàng có đủ điều kiện đổi trả
            hay không kèm lý do và thời hạn.
    Error:  Trả về lỗi nếu mã đơn hàng không tồn tại.
    Side effect: Read-only.
    Example:
        check_return_eligibility("ORD-001")
        -> "Đơn hàng ORD-001: Đủ điều kiện đổi trả (còn 23 ngày)."
    Safety: try/except bao quanh, không crash.
    """
    try:
        if not order_id or not order_id.strip():
            return "LỖI: Mã đơn hàng không được để trống."

        order_id = order_id.strip().upper()
        if order_id not in _ORDERS_DB:
            return (
                f"LỖI: Không tìm thấy đơn hàng với mã '{order_id}'."
            )

        order = _ORDERS_DB[order_id]

        if order["trang_thai"] != "Đã giao":
            return (
                f"Đơn hàng {order_id} hiện đang ở trạng thái '{order['trang_thai']}'. "
                "Chỉ có thể yêu cầu đổi trả sau khi đơn hàng đã được giao."
            )

        days_since_purchase = 26 - int(order["ngay_mua"].split("-")[2])
        if days_since_purchase > 30:
            return (
                f"Đơn hàng {order_id} đã mua {days_since_purchase} ngày trước. "
                "Đã quá thời hạn đổi trả 30 ngày kể từ ngày mua."
            )

        remaining = 30 - days_since_purchase
        return (
            f"Đơn hàng {order_id}: Đủ điều kiện đổi trả. "
            f"Sản phẩm: {order['san_pham']}. "
            f"Còn {remaining} ngày để yêu cầu đổi trả (trong vòng 30 ngày kể từ ngày mua). "
            "Chính sách: Sản phẩm còn nguyên tem, chưa qua sử dụng, có hóa đơn mua hàng."
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể kiểm tra điều kiện đổi trả. Chi tiết: {str(e)}"


def initiate_return(order_id: str, reason: str) -> str:
    """
    Tạo một yêu cầu đổi/trả hàng cho đơn hàng đã giao.

    Name: initiate_return
    Purpose: Dùng khi người dùng muốn tạo yêu cầu đổi trả hàng.
             Chỉ hoạt động với đơn hàng đã giao và còn hạn đổi trả.
             KHÔNG dùng để tra cứu thông tin.
    Input:  order_id (str) - Mã đơn hàng cần đổi trả.
            reason (str) - Lý do đổi trả (VD: 'Sản phẩm bị lỗi', 'Không đúng mẫu').
    Output: Chuỗi thông báo kết quả kèm mã yêu cầu đổi trả nếu thành công.
    Error:  Trả về lỗi nếu đơn hàng không hợp lệ, chưa giao, quá hạn,
            hoặc đã có yêu cầu đổi trả trước đó.
    Side effect: CÓ THAY ĐỔI TRẠNG THÁI (tạo bản ghi yêu cầu đổi trả mới).
    Example:
        initiate_return("ORD-001", "Sản phẩm bị lỗi")
        -> "Đã tạo yêu cầu đổi trả RET-002 cho đơn hàng ORD-001."
    Safety: try/except bao quanh.
    """
    global _RETURN_ID_COUNTER

    try:
        if not order_id or not order_id.strip():
            return "LỖI: Mã đơn hàng không được để trống."
        if not reason or not reason.strip():
            return "LỖI: Vui lòng cung cấp lý do đổi trả."

        order_id = order_id.strip().upper()
        reason = reason.strip()

        if order_id not in _ORDERS_DB:
            return f"LỖI: Không tìm thấy đơn hàng với mã '{order_id}'."

        order = _ORDERS_DB[order_id]

        if order["trang_thai"] != "Đã giao":
            return (
                f"LỖI: Đơn hàng {order_id} chưa được giao "
                f"(trạng thái hiện tại: '{order['trang_thai']}'). "
                "Chỉ có thể đổi trả sau khi nhận được hàng."
            )

        for ret_id, ret in _RETURNS_DB.items():
            if ret["ma_don_hang"] == order_id:
                return (
                    f"LỖI: Đơn hàng {order_id} đã có yêu cầu đổi trả "
                    f"(mã: {ret_id}, trạng thái: '{ret['trang_thai']}'). "
                    "Vui lòng theo dõi yêu cầu hiện tại."
                )

        _RETURN_ID_COUNTER += 1
        return_id = f"RET-{_RETURN_ID_COUNTER:03d}"

        _RETURNS_DB[return_id] = {
            "ma_don_hang": order_id,
            "ly_do": reason,
            "trang_thai": "Chờ xử lý",
            "ngay_tao": "2026-07-28",
            "phuong_thuc": "Hoàn tiền",
        }

        return (
            f"✅ Đã tạo yêu cầu đổi trả thành công!\n"
            f"Mã yêu cầu: {return_id}\n"
            f"Đơn hàng: {order_id}\n"
            f"Sản phẩm: {order['san_pham']}\n"
            f"Lý do: {reason}\n"
            f"Trạng thái: Chờ xử lý\n"
            f"Phương thức: Hoàn tiền về tài khoản gốc (3-5 ngày làm việc)."
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể tạo yêu cầu đổi trả. Chi tiết: {str(e)}"


def track_return_status(return_id: str) -> str:
    """
    Theo dõi tiến trình xử lý yêu cầu đổi/trả hàng.

    Name: track_return_status
    Purpose: Dùng khi người dùng hỏi "yêu cầu đổi trả đến đâu rồi?"
             hoặc muốn kiểm tra trạng thái xử lý. Chỉ tra cứu, không thay đổi.
    Input:  return_id (str) - Mã yêu cầu đổi trả (VD: 'RET-001').
    Output: Chuỗi thông tin chi tiết về trạng thái xử lý yêu cầu đổi trả.
    Error:  Trả về lỗi nếu mã yêu cầu không tồn tại.
    Side effect: Read-only.
    Example:
        track_return_status("RET-001")
        -> "Yêu cầu RET-001 (Đơn hàng ORD-004): Đang xử lý..."
    Safety: try/except bao quanh.
    """
    try:
        if not return_id or not return_id.strip():
            return "LỖI: Mã yêu cầu đổi trả không được để trống."

        return_id = return_id.strip().upper()
        if return_id not in _RETURNS_DB:
            return (
                f"LỖI: Không tìm thấy yêu cầu đổi trả với mã '{return_id}'."
            )

        ret = _RETURNS_DB[return_id]
        order_id = ret["ma_don_hang"]
        order = _ORDERS_DB.get(order_id, {})

        status_icons = {
            "Chờ xử lý": "⏳ Chờ xử lý",
            "Đang xử lý": "🔄 Đang xử lý",
            "Đã duyệt": "✅ Đã duyệt",
            "Từ chối": "❌ Từ chối",
            "Đã hoàn tiền": "💰 Đã hoàn tiền",
        }
        status_display = status_icons.get(ret["trang_thai"], ret["trang_thai"])

        info = {
            "ma_yeu_cau": return_id,
            "ma_don_hang": order_id,
            "san_pham": order.get("san_pham", "N/A"),
            "ly_do": ret["ly_do"],
            "trang_thai": status_display,
            "ngay_tao": ret["ngay_tao"],
            "phuong_thuc": ret["phuong_thuc"],
        }
        return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể theo dõi yêu cầu đổi trả. Chi tiết: {str(e)}"


def cancel_return(return_id: str) -> str:
    """
    Hủy yêu cầu đổi/trả hàng nếu chưa được xử lý.

    Name: cancel_return
    Purpose: Dùng khi người dùng muốn hủy yêu cầu đổi trả đã tạo trước đó.
             Chỉ hủy được nếu yêu cầu ở trạng thái 'Chờ xử lý' hoặc 'Đang xử lý'.
    Input:  return_id (str) - Mã yêu cầu đổi trả cần hủy.
    Output: Chuỗi thông báo xác nhận hủy thành công hoặc thất bại.
    Error:  Trả về lỗi nếu mã không tồn tại hoặc đã xử lý xong.
    Side effect: CÓ THAY ĐỔI TRẠNG THÁI (cập nhật trạng thái yêu cầu).
    Example:
        cancel_return("RET-001")
        -> "Đã hủy yêu cầu đổi trả RET-001."
    Safety: try/except bao quanh.
    """
    try:
        if not return_id or not return_id.strip():
            return "LỖI: Mã yêu cầu đổi trả không được để trống."

        return_id = return_id.strip().upper()
        if return_id not in _RETURNS_DB:
            return (
                f"LỖI: Không tìm thấy yêu cầu đổi trả với mã '{return_id}'."
            )

        ret = _RETURNS_DB[return_id]
        non_cancellable = {"Đã duyệt", "Đã hoàn tiền", "Từ chối", "Đã hủy"}
        if ret["trang_thai"] in non_cancellable:
            return (
                f"LỖI: Không thể hủy yêu cầu {return_id} vì đã ở trạng thái "
                f"'{ret['trang_thai']}'."
            )

        ret["trang_thai"] = "Đã hủy"
        return (
            f"✅ Đã hủy yêu cầu đổi trả {return_id} thành công.\n"
            f"Đơn hàng: {ret['ma_don_hang']}"
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể hủy yêu cầu đổi trả. Chi tiết: {str(e)}"


def search_products(query: str) -> str:
    """
    Tìm kiếm sản phẩm trong danh mục cửa hàng.

    Name: search_products
    Purpose: Dùng khi người dùng muốn tìm sản phẩm để mua hoặc đổi.
             Hỗ trợ tìm kiếm theo tên sản phẩm (không phân biệt hoa thường).
             KHÔNG dùng để kiểm tra đơn hàng hay tạo yêu cầu đổi trả.
    Input:  query (str) - Từ khóa tìm kiếm (VD: 'áo thun', 'tai nghe', 'laptop').
    Output: Chuỗi danh sách các sản phẩm phù hợp kèm giá và tồn kho.
    Error:  Trả về thông báo nếu không tìm thấy sản phẩm phù hợp.
    Side effect: Read-only.
    Example:
        search_products("tai nghe")
        -> "Tìm thấy 2 sản phẩm: 1. Tai nghe Bluetooth Sony..."
    Safety: try/except bao quanh.
    """
    try:
        if not query or not query.strip():
            return "LỖI: Vui lòng nhập từ khóa tìm kiếm sản phẩm."

        query = query.strip().lower()
        results = []
        for p in _PRODUCTS_DB:
            if query in p["ten"].lower():
                results.append(p)

        if not results:
            return (
                f"Không tìm thấy sản phẩm nào phù hợp với từ khóa '{query}'."
            )

        lines = [f"Tìm thấy {len(results)} sản phẩm:"]
        for i, p in enumerate(results, 1):
            stock_status = "Còn hàng" if p["ton_kho"] > 0 else "Hết hàng"
            lines.append(
                f"{i}. {p['ten']} - {p['gia']:,} VNĐ "
                f"(Mã: {p['ma']}, {stock_status}, SL: {p['ton_kho']})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể tìm kiếm sản phẩm. Chi tiết: {str(e)}"


# ============================================================
# DANH SÁCH TOOL ĐĂNG KÝ CHO AGENT
# ============================================================

AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_return_eligibility": check_return_eligibility,
    "initiate_return": initiate_return,
    "track_return_status": track_return_status,
    "cancel_return": cancel_return,
    "search_products": search_products,
}
