"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

def extract_gift_profile(prompt: str) -> str:
    """
    Phân tích chuỗi prompt của người dùng để xác định đối tượng nhận quà,
    sở thích, dịp lễ và độ tuổi, phục vụ Agent "Trợ lý chọn quà tặng dựa trên tính cách".

    Args:
        prompt (str): Câu mô tả nhu cầu tặng quà (Ví dụ: 'Mình cần quà sinh nhật cho mẹ 50 tuổi thích nấu ăn')

    Returns:
        str: Hồ sơ đã trích xuất gồm đối tượng, độ tuổi, dịp lễ, sở thích
    """
    import re
    text = prompt.lower()

    doi_tuong_map = {
        "mẹ": ["mẹ", "má"],
        "bố": ["bố", "ba", "cha"],
        "bạn gái": ["bạn gái", "người yêu nữ"],
        "bạn trai": ["bạn trai", "người yêu nam"],
        "vợ": ["vợ"],
        "chồng": ["chồng"],
        "sếp": ["sếp"],
        "đồng nghiệp": ["đồng nghiệp"],
        "con": ["con trai", "con gái"],
        "bạn thân": ["bạn thân", "bạn bè", "bạn"],
    }
    doi_tuong = "Không xác định"
    for key, keywords in doi_tuong_map.items():
        if any(kw in text for kw in keywords):
            doi_tuong = key
            break

    dip_le_map = {
        "sinh nhật": ["sinh nhật"],
        "Giáng sinh": ["giáng sinh", "noel"],
        "Valentine": ["valentine", "lễ tình nhân"],
        "Tết": ["tết", "năm mới"],
        "kỷ niệm ngày cưới": ["kỷ niệm ngày cưới", "kỷ niệm"],
        "20/10": ["20/10"],
        "8/3": ["8/3"],
        "tốt nghiệp": ["tốt nghiệp", "ra trường"],
    }
    dip_le = "Không xác định"
    for key, keywords in dip_le_map.items():
        if any(kw in text for kw in keywords):
            dip_le = key
            break

    so_thich_map = {
        "đọc sách": ["đọc sách", "sách"],
        "nấu ăn": ["nấu ăn", "nấu nướng", "ẩm thực"],
        "du lịch": ["du lịch", "phượt"],
        "công nghệ": ["công nghệ", "gadget", "điện tử"],
        "thể thao": ["thể thao", "gym", "bóng đá", "chạy bộ"],
        "âm nhạc": ["âm nhạc", "nghe nhạc", "guitar"],
        "làm đẹp": ["làm đẹp", "skincare", "mỹ phẩm"],
        "thời trang": ["thời trang", "quần áo"],
        "chơi game": ["chơi game", "game thủ"],
    }
    so_thich_list = [key for key, kws in so_thich_map.items() if any(kw in text for kw in kws)]
    so_thich = ", ".join(so_thich_list) if so_thich_list else "Không xác định"

    age_match = re.search(r"(\d{1,3})\s*tuổi", text)
    do_tuoi = f"{age_match.group(1)} tuổi" if age_match else "Không xác định"

    return (
        f"Hồ sơ tặng quà:\n"
        f"- Đối tượng: {doi_tuong}\n"
        f"- Độ tuổi: {do_tuoi}\n"
        f"- Dịp lễ: {dip_le}\n"
        f"- Sở thích: {so_thich}"
    )


def search_gift_api(gift_description: str) -> str:
    """
    Tra cứu cửa hàng bán món quà được mô tả (dữ liệu mock), trả về tên cửa hàng và link mua hàng,
    phục vụ Agent "Trợ lý chọn quà tặng dựa trên tính cách".

    Args:
        gift_description (str): Mô tả món quà cần tìm mua (Ví dụ: 'sách nấu ăn cho người mới bắt đầu')

    Returns:
        str: Tên cửa hàng và link mua món quà tương ứng
    """
    desc_lower = gift_description.lower()

    if "sách" in desc_lower or "sach" in desc_lower:
        return "Cửa hàng: Tiki - Nhà sách trực tuyến. Link: https://tiki.vn/nha-sach-tiki"

    elif "công nghệ" in desc_lower or "gadget" in desc_lower or "điện tử" in desc_lower:
        return "Cửa hàng: FPT Shop - Đồ công nghệ. Link: https://fptshop.com.vn"

    elif "nấu ăn" in desc_lower or "ẩm thực" in desc_lower:
        return "Cửa hàng: Shopee - Đồ dùng nhà bếp. Link: https://shopee.vn"

    elif "làm đẹp" in desc_lower or "skincare" in desc_lower or "mỹ phẩm" in desc_lower:
        return "Cửa hàng: Hasaki - Mỹ phẩm & làm đẹp. Link: https://hasaki.vn"

    elif "thời trang" in desc_lower or "quần áo" in desc_lower:
        return "Cửa hàng: Lazada - Thời trang. Link: https://www.lazada.vn"

    elif "thể thao" in desc_lower or "gym" in desc_lower:
        return "Cửa hàng: Decathlon - Đồ thể thao. Link: https://www.decathlon.vn"

    elif "du lịch" in desc_lower or "phượt" in desc_lower:
        return "Cửa hàng: Travelgear - Phụ kiện du lịch. Link: https://travelgear.vn"

    elif "chơi game" in desc_lower or "game thủ" in desc_lower:
        return "Cửa hàng: GearVN - Gaming Gear. Link: https://gearvn.com"

    elif "âm nhạc" in desc_lower or "guitar" in desc_lower:
        return "Cửa hàng: Việt Thương Music - Nhạc cụ. Link: https://vietthuong.vn"
    
    else:
        return f"LỖI: Không tìm thấy cửa hàng phù hợp cho món quà '{gift_description}'."

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "extract_gift_profile": extract_gift_profile,
    "search_gift_api": search_gift_api,
}
