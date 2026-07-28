"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
Cập nhật Mốc 3: Gia cố phanh an toàn (Safeguards) - Đảm bảo tất cả các tool
khi gặp lỗi hoặc đầu vào bất thường đều trả về chuỗi JSON thông báo lỗi,
tuyệt đối không crash ứng dụng.
"""

import json
from datetime import date, datetime


MOCK_ORDERS = {
    "ORD1001": {
        "order_id": "ORD1001",
        "status": "delivered",
        "delivered_date": "2026-07-24",
        "customer": "Minh Anh",
        "items": [
            {
                "item_id": "ITEM-AO-HOODIE",
                "name": "Áo hoodie xanh navy",
                "price": 450000,
                "returnable": True,
            },
            {
                "item_id": "ITEM-TAT-SET",
                "name": "Set tất thể thao",
                "price": 90000,
                "returnable": False,
            },
        ],
    },
    "ORD1002": {
        "order_id": "ORD1002",
        "status": "shipping",
        "delivered_date": None,
        "customer": "Quang Huy",
        "items": [
            {
                "item_id": "ITEM-BALO",
                "name": "Balo laptop 15 inch",
                "price": 620000,
                "returnable": True,
            }
        ],
    },
    "ORD1003": {
        "order_id": "ORD1003",
        "status": "delivered",
        "delivered_date": "2026-06-10",
        "customer": "Lan Chi",
        "items": [
            {
                "item_id": "ITEM-GIAY",
                "name": "Giày chạy bộ",
                "price": 890000,
                "returnable": True,
            }
        ],
    },
}

RETURN_WINDOW_DAYS = 14


def _json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _find_order(order_id: str) -> dict | None:
    if not order_id or not isinstance(order_id, str):
        return None
    return MOCK_ORDERS.get(order_id.strip().upper())


def _find_item(order: dict, item_id: str) -> dict | None:
    if not order or not isinstance(order, dict) or "items" not in order:
        return None
    if not item_id or not isinstance(item_id, str):
        return None
    wanted = item_id.strip().upper()
    for item in order.get("items", []):
        if str(item.get("item_id", "")).upper() == wanted:
            return item
    return None


def lookup_order(order_id: str) -> str:
    """
    Tra cứu trạng thái và chi tiết của một đơn hàng.

    Args:
        order_id (str): Mã đơn hàng, ví dụ "ORD1001".

    Returns:
        str: Chuỗi JSON chứa status, delivered_date, customer và danh sách items.
        Nếu mã đơn không tồn tại hoặc lỗi đầu vào, trả về JSON có status="error" và message rõ ràng.

    Side effect:
        Read-only, không thay đổi dữ liệu.
    """
    try:
        if not order_id or not isinstance(order_id, str) or not order_id.strip():
            return _json({
                "status": "error",
                "message": "LỖI: Thiếu hoặc sai định dạng mã đơn hàng. Vui lòng cung cấp order_id dưới dạng chuỗi hợp lệ.",
            })

        order = _find_order(order_id)
        if not order:
            return _json({
                "status": "error",
                "message": f"LỖI: Không tìm thấy đơn hàng '{order_id}'.",
            })

        return _json({
            "status": "success",
            "order": order,
        })
    except Exception as e:
        return _json({
            "status": "error",
            "message": f"LỖI HỆ THỐNG TRONG TOOL (lookup_order): {str(e)}",
        })


def check_return_policy(order_id: str, item_id: str, reason: str = "") -> str:
    """
    Kiểm tra một sản phẩm trong đơn hàng có đủ điều kiện đổi/trả hay không.

    Args:
        order_id (str): Mã đơn hàng, ví dụ "ORD1001".
        item_id (str): Mã sản phẩm trong đơn, ví dụ "ITEM-AO-HOODIE".
        reason (str): Lý do đổi/trả do khách hàng cung cấp.

    Returns:
        str: Chuỗi JSON gồm eligible, reason, deadline và next_step.
        Với lỗi nghiệp vụ như đơn không tồn tại, đơn chưa giao, quá hạn hoặc sản phẩm
        không hỗ trợ đổi/trả, tool trả JSON giải thích thay vì raise exception.

    Side effect:
        Read-only, không tạo yêu cầu đổi/trả.
    """
    try:
        if not order_id or not isinstance(order_id, str) or not order_id.strip():
            return _json({
                "status": "error",
                "eligible": False,
                "reason": "LỖI: Thiếu hoặc sai định dạng mã đơn hàng (order_id).",
            })

        if not item_id or not isinstance(item_id, str) or not item_id.strip():
            return _json({
                "status": "error",
                "eligible": False,
                "reason": "LỖI: Thiếu hoặc sai định dạng mã sản phẩm (item_id).",
            })

        order = _find_order(order_id)
        if not order:
            return _json({
                "status": "error",
                "eligible": False,
                "reason": f"Không tìm thấy đơn hàng '{order_id}'.",
            })

        item = _find_item(order, item_id)
        if not item:
            return _json({
                "status": "error",
                "eligible": False,
                "reason": f"Không tìm thấy sản phẩm '{item_id}' trong đơn {order['order_id']}.",
            })

        if order.get("status") != "delivered":
            return _json({
                "status": "success",
                "eligible": False,
                "reason": "Đơn hàng chưa được giao nên chưa đủ điều kiện đổi/trả.",
                "next_step": "Theo dõi vận chuyển hoặc liên hệ hỗ trợ nếu muốn hủy đơn.",
            })

        if not item.get("returnable", False):
            return _json({
                "status": "success",
                "eligible": False,
                "reason": f"Sản phẩm '{item.get('name')}' thuộc nhóm không hỗ trợ đổi/trả.",
            })

        delivered_date_str = order.get("delivered_date")
        if not delivered_date_str:
            return _json({
                "status": "success",
                "eligible": False,
                "reason": "Đơn hàng chưa có thông tin ngày giao hàng.",
            })

        try:
            delivered_date = datetime.strptime(delivered_date_str, "%Y-%m-%d").date()
        except ValueError:
            return _json({
                "status": "error",
                "eligible": False,
                "reason": f"Định dạng ngày giao hàng '{delivered_date_str}' không hợp lệ (cần YYYY-MM-DD).",
            })

        days_since_delivery = (date.today() - delivered_date).days
        deadline = delivered_date.toordinal() + RETURN_WINDOW_DAYS
        deadline_text = date.fromordinal(deadline).isoformat()

        if days_since_delivery > RETURN_WINDOW_DAYS:
            return _json({
                "status": "success",
                "eligible": False,
                "reason": f"Đơn đã quá hạn {RETURN_WINDOW_DAYS} ngày đổi trả.",
                "deadline": deadline_text,
            })

        safe_reason = reason.strip() if reason and isinstance(reason, str) else "Khách hàng yêu cầu đổi trả"

        return _json({
            "status": "success",
            "eligible": True,
            "reason": f"Đủ điều kiện đổi/trả với lý do: {safe_reason}.",
            "deadline": deadline_text,
            "next_step": "Có thể tạo yêu cầu đổi/trả bằng create_return_request.",
        })
    except Exception as e:
        return _json({
            "status": "error",
            "eligible": False,
            "reason": f"LỖI HỆ THỐNG TRONG TOOL (check_return_policy): {str(e)}",
        })


def estimate_refund(order_id: str, item_id: str) -> str:
    """
    Ước tính số tiền hoàn lại cho một sản phẩm trong đơn hàng.

    Args:
        order_id (str): Mã đơn hàng.
        item_id (str): Mã sản phẩm cần hoàn tiền.

    Returns:
        str: Chuỗi JSON gồm refund_amount, deduction_fee và currency.
        Nếu đơn hoặc sản phẩm không tồn tại, trả về JSON lỗi an toàn.

    Side effect:
        Read-only, không thực hiện hoàn tiền thật.
    """
    try:
        if not order_id or not isinstance(order_id, str) or not order_id.strip():
            return _json({
                "status": "error",
                "message": "LỖI: Thiếu hoặc sai định dạng mã đơn hàng (order_id).",
            })

        if not item_id or not isinstance(item_id, str) or not item_id.strip():
            return _json({
                "status": "error",
                "message": "LỖI: Thiếu hoặc sai định dạng mã sản phẩm (item_id).",
            })

        order = _find_order(order_id)
        if not order:
            return _json({
                "status": "error",
                "message": f"LỖI: Không tìm thấy đơn hàng '{order_id}'.",
            })

        item = _find_item(order, item_id)
        if not item:
            return _json({
                "status": "error",
                "message": f"LỖI: Không tìm thấy sản phẩm '{item_id}' trong đơn {order['order_id']}.",
            })

        deduction_fee = 30000
        price = item.get("price", 0)
        refund_amount = max(price - deduction_fee, 0)
        return _json({
            "status": "success",
            "item_id": item.get("item_id"),
            "item_name": item.get("name"),
            "refund_amount": refund_amount,
            "deduction_fee": deduction_fee,
            "currency": "VND",
        })
    except Exception as e:
        return _json({
            "status": "error",
            "message": f"LỖI HỆ THỐNG TRONG TOOL (estimate_refund): {str(e)}",
        })


def create_return_request(order_id: str, item_id: str, reason: str = "") -> str:
    """
    Tạo yêu cầu đổi/trả giả lập sau khi kiểm tra điều kiện hợp lệ.

    Args:
        order_id (str): Mã đơn hàng.
        item_id (str): Mã sản phẩm cần đổi/trả.
        reason (str): Lý do đổi/trả.

    Returns:
        str: Chuỗi JSON chứa return_request_id và next_step nếu hợp lệ.
        Nếu chưa đủ điều kiện, trả về JSON lỗi nghiệp vụ và không tạo request.

    Side effect:
        Trong lab này chỉ giả lập tạo ticket, không ghi database thật.
    """
    try:
        if not order_id or not isinstance(order_id, str) or not order_id.strip():
            return _json({
                "status": "error",
                "message": "LỖI: Thiếu hoặc sai định dạng mã đơn hàng (order_id).",
            })

        if not item_id or not isinstance(item_id, str) or not item_id.strip():
            return _json({
                "status": "error",
                "message": "LỖI: Thiếu hoặc sai định dạng mã sản phẩm (item_id).",
            })

        policy_text = check_return_policy(order_id, item_id, reason)
        try:
            policy = json.loads(policy_text)
        except Exception:
            return _json({
                "status": "error",
                "message": "LỖI: Không thể đọc kết quả kiểm tra điều kiện đổi/trả.",
            })

        if not policy.get("eligible"):
            return _json({
                "status": "error",
                "message": "Không thể tạo yêu cầu đổi/trả vì chưa đủ điều kiện.",
                "policy_result": policy,
            })

        request_id = f"RET-{order_id.strip().upper()}-{item_id.strip().upper()}"
        return _json({
            "status": "success",
            "return_request_id": request_id,
            "message": "Đã tạo yêu cầu đổi/trả giả lập.",
            "next_step": "Khách hàng đóng gói sản phẩm và chờ email hướng dẫn gửi hàng.",
        })
    except Exception as e:
        return _json({
            "status": "error",
            "message": f"LỖI HỆ THỐNG TRONG TOOL (create_return_request): {str(e)}",
        })


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_return_policy": check_return_policy,
    "estimate_refund": estimate_refund,
    "create_return_request": create_return_request,
}
