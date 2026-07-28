"""
Tool specs cho trợ lý tra cứu đơn hàng và xử lý đổi/trả.

Phạm vi Mốc 2:
- Khai báo đúng tên và chữ ký của các tool.
- Mô tả rõ input, output và side effect bằng docstring/schema.
- Cung cấp dữ liệu và kết quả giả lập tối thiểu cho luồng thành công.

Việc validate toàn bộ input, bắt exception và xử lý các failure mode sẽ được
bổ sung ở Mốc 3.
"""


# Dữ liệu giả lập tối thiểu để Agent có Observation khi demo.
MOCK_ORDERS = [
    {
        "order_id": "DH001",
        "customer_id": "KH001",
        "status": "Đã giao",
        "items": [
            {
                "item_sku": "SP-AO-001",
                "name": "Áo thun VinAI",
                "variant": "Xanh, size M",
            }
        ],
    },
    {
        "order_id": "DH002",
        "customer_id": "KH001",
        "status": "Đang giao",
        "items": [
            {
                "item_sku": "SP-TAINGHE-001",
                "name": "Tai nghe không dây",
                "variant": "Trắng",
            }
        ],
    },
]


def search_orders(query: str) -> str:
    """Tra cứu đơn hàng bằng mã đơn hoặc mã khách hàng.

    Agent nên gọi tool này trước khi tạo yêu cầu đổi/trả để lấy đúng mã đơn,
    SKU sản phẩm và trạng thái giao hàng.

    Args:
        query (str): Mã đơn hàng, ví dụ ``"DH001"``, hoặc mã khách hàng,
            ví dụ ``"KH001"``.

    Returns:
        str: Danh sách đơn hàng khớp với mã tra cứu, bao gồm mã đơn, trạng
        thái và các sản phẩm trong đơn. Nếu không có kết quả, trả về thông báo
        không tìm thấy.

    Side effects:
        Không có; đây là tool chỉ đọc.

    Example:
        ``search_orders("KH001")``
    """
    normalized_query = query.strip().upper()
    matched_orders = [
        order
        for order in MOCK_ORDERS
        if normalized_query in {order["order_id"], order["customer_id"]}
    ]

    if not matched_orders:
        return f"Không tìm thấy đơn hàng cho mã '{normalized_query}'."

    order_lines = []
    for order in matched_orders:
        items = ", ".join(
            f"{item['item_sku']} - {item['name']} ({item['variant']})"
            for item in order["items"]
        )
        order_lines.append(
            f"Đơn {order['order_id']} | Trạng thái: {order['status']} | "
            f"Sản phẩm: {items}"
        )

    return "\n".join(order_lines)


def create_return_request(order_id: str, item_sku: str, reason: str) -> str:
    """Tạo yêu cầu trả một sản phẩm thuộc đơn hàng.

    Chỉ gọi tool sau khi đã dùng ``search_orders`` và người dùng xác nhận rõ
    sản phẩm muốn trả. Tool chỉ ghi nhận yêu cầu, không tự động hoàn tiền.

    Args:
        order_id (str): Mã đơn hàng, ví dụ ``"DH001"``.
        item_sku (str): SKU sản phẩm cần trả, ví dụ ``"SP-AO-001"``.
        reason (str): Lý do trả hàng do người dùng cung cấp.

    Returns:
        str: Xác nhận đã tạo yêu cầu, gồm mã yêu cầu, mã đơn, SKU, lý do và
        trạng thái chờ duyệt.

    Side effects:
        Tạo một yêu cầu trả hàng giả lập. Không thực hiện hoàn tiền.

    Example:
        ``create_return_request("DH001", "SP-AO-001", "Sản phẩm bị lỗi")``
    """
    request_id = f"YCT-{order_id.strip().upper()}-{item_sku.strip().upper()}"
    return (
        f"Đã tạo yêu cầu trả hàng {request_id}. "
        f"Đơn: {order_id}; SKU: {item_sku}; Lý do: {reason}; "
        "Trạng thái: Chờ duyệt."
    )


def create_exchange_request(
    order_id: str,
    item_sku: str,
    new_variant: str,
    reason: str,
) -> str:
    """Tạo yêu cầu đổi biến thể cho một sản phẩm thuộc đơn hàng.

    Chỉ gọi tool sau khi đã dùng ``search_orders`` và người dùng xác nhận rõ
    sản phẩm cùng biến thể muốn đổi sang. Tool chỉ ghi nhận yêu cầu; tồn kho
    của biến thể mới chưa được đảm bảo ở Mốc 2.

    Args:
        order_id (str): Mã đơn hàng, ví dụ ``"DH001"``.
        item_sku (str): SKU sản phẩm cần đổi, ví dụ ``"SP-AO-001"``.
        new_variant (str): Biến thể muốn nhận, ví dụ ``"Trắng, size L"``.
        reason (str): Lý do đổi hàng do người dùng cung cấp.

    Returns:
        str: Xác nhận đã tạo yêu cầu, gồm mã yêu cầu, mã đơn, SKU, biến thể
        mới, lý do và trạng thái chờ duyệt.

    Side effects:
        Tạo một yêu cầu đổi hàng giả lập. Không tự động giữ tồn kho.

    Example:
        ``create_exchange_request("DH001", "SP-AO-001", "Trắng, size L", "Muốn đổi size")``
    """
    request_id = f"YCD-{order_id.strip().upper()}-{item_sku.strip().upper()}"
    return (
        f"Đã tạo yêu cầu đổi hàng {request_id}. "
        f"Đơn: {order_id}; SKU: {item_sku}; Biến thể mới: {new_variant}; "
        f"Lý do: {reason}; Trạng thái: Chờ duyệt."
    )


# Tool Specs dùng để Role 3 đưa đúng mô tả vào prompt và Role 4 tích hợp Agent.
TOOL_SPECS = {
    "search_orders": {
        "description": (
            "Tra cứu đơn hàng bằng mã đơn hoặc mã khách hàng để lấy trạng thái "
            "và SKU trước khi xử lý đổi/trả."
        ),
        "parameters": {
            "query": "Mã đơn hàng (DH...) hoặc mã khách hàng (KH...).",
        },
        "side_effect": "read_only",
    },
    "create_return_request": {
        "description": (
            "Tạo yêu cầu trả hàng sau khi người dùng xác nhận; không tự động "
            "hoàn tiền."
        ),
        "parameters": {
            "order_id": "Mã đơn hàng.",
            "item_sku": "SKU sản phẩm cần trả.",
            "reason": "Lý do trả hàng.",
        },
        "side_effect": "create_return_request",
    },
    "create_exchange_request": {
        "description": (
            "Tạo yêu cầu đổi biến thể sau khi người dùng xác nhận; không đảm "
            "bảo tồn kho ngay lập tức."
        ),
        "parameters": {
            "order_id": "Mã đơn hàng.",
            "item_sku": "SKU sản phẩm cần đổi.",
            "new_variant": "Biến thể muốn đổi sang.",
            "reason": "Lý do đổi hàng.",
        },
        "side_effect": "create_exchange_request",
    },
}


# Registry để Agent tìm tool theo tên Action.
AVAILABLE_TOOLS = {
    "search_orders": search_orders,
    "create_return_request": create_return_request,
    "create_exchange_request": create_exchange_request,
}
