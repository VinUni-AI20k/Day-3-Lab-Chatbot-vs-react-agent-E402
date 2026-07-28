def fetch_product_from_url(url: str):
    """
    Lấy thông tin sản phẩm từ URL người dùng cung cấp.
    """
    pass


def calculate_cost_per_serving(
    price_vnd: float,
    servings_per_container: float
):
    """
    Tính chi phí trên mỗi serving.
    """
    pass


def compare_products(products: list):
    """
    So sánh từ 2 đến N sản phẩm.
    """
    pass


TOOLS = [
    fetch_product_from_url,
    calculate_cost_per_serving,
    calculate_cost_per_active_amount,
    compare_products,
]