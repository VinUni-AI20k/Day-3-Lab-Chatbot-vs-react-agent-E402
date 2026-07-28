"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
📌 Đề tài 3: Trợ Lý Nắm Bắt Tính Cách & Chọn Quà Tặng Phù Hợp

Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
Dữ liệu tính cách được lấy từ kết quả bộ trắc nghiệm tính cách (Personality Quiz).

6 tool chính:
  1. get_personality_profile    -> tra cứu kết quả trắc nghiệm tính cách
  2. search_gift_catalog        -> tìm quà theo sở thích / ngân sách / loại trừ kiêng kỵ
  3. check_gift_availability    -> kiểm tra tồn kho & khuyến mãi 1 sản phẩm
  4. suggest_gift_by_personality -> gợi ý quà nhanh theo loại tính cách
  5. tra_cuu_quy_tac_dip        -> tra lưu ý / kiêng kỵ theo dịp lễ & văn hóa
  6. tinh_ngan_sach_gop         -> chia đều ngân sách khi nhiều người góp quà
"""

from typing import Optional


# =============================================================================
# 📦 MOCK DATABASE — Kết quả trắc nghiệm tính cách
# =============================================================================

PERSONALITY_DATABASE = {
    "minh_anh": {
        "name": "Minh Anh",
        "quiz_result": {
            "personality_type": "Người Sáng Tạo (The Creator)",
            "traits": ["sáng tạo", "giàu cảm xúc", "yêu nghệ thuật", "thích sự độc đáo"],
            "interests": ["vẽ tranh", "nhiếp ảnh", "handmade", "thời trang vintage"],
            "lifestyle": "Hướng nội, thích không gian yên tĩnh, hay đi quán cà phê để sáng tạo",
            "dislike": ["đồ công nghệ phức tạp", "quà thực dụng nhàm chán"],
            "score_summary": {
                "sang_tao": 9,
                "huong_ngoai": 3,
                "thuc_dung": 4,
                "cam_xuc": 8,
                "phieu_luu": 5
            }
        }
    },
    "anh_tu": {
        "name": "Anh Tú",
        "quiz_result": {
            "personality_type": "Người Phiêu Lưu (The Adventurer)",
            "traits": ["năng động", "yêu thiên nhiên", "thích khám phá", "hướng ngoại"],
            "interests": ["camping", "leo núi", "chụp ảnh phong cảnh", "cà phê đặc sản"],
            "lifestyle": "Hướng ngoại, cuối tuần luôn đi phượt, thích trải nghiệm mới",
            "dislike": ["đồ trang trí để bàn", "sách lý thuyết dài"],
            "score_summary": {
                "sang_tao": 6,
                "huong_ngoai": 9,
                "thuc_dung": 7,
                "cam_xuc": 5,
                "phieu_luu": 10
            }
        }
    },
    "hoang_long": {
        "name": "Hoàng Long",
        "quiz_result": {
            "personality_type": "Người Phân Tích (The Analyst)",
            "traits": ["logic", "tỉ mỉ", "đam mê công nghệ", "thích tối ưu hóa"],
            "interests": ["lập trình", "đọc sách khoa học", "gaming", "gadget công nghệ"],
            "lifestyle": "Hướng nội, thích ở nhà nghiên cứu, đam mê công nghệ mới",
            "dislike": ["đồ handmade", "quần áo thời trang"],
            "score_summary": {
                "sang_tao": 7,
                "huong_ngoai": 2,
                "thuc_dung": 9,
                "cam_xuc": 3,
                "phieu_luu": 4
            }
        }
    },
    "thu_ha": {
        "name": "Thu Hà",
        "quiz_result": {
            "personality_type": "Người Kết Nối (The Connector)",
            "traits": ["thân thiện", "quan tâm người khác", "thích chia sẻ", "tinh tế"],
            "interests": ["nấu ăn", "làm bánh", "chăm sóc da", "yoga", "đọc sách tâm lý"],
            "lifestyle": "Hướng ngoại nhẹ, thích gặp gỡ bạn bè, chăm sóc bản thân và mọi người",
            "dislike": ["đồ công nghệ khó dùng", "quà không có ý nghĩa cá nhân"],
            "score_summary": {
                "sang_tao": 6,
                "huong_ngoai": 7,
                "thuc_dung": 5,
                "cam_xuc": 9,
                "phieu_luu": 4
            }
        }
    },
}

# =============================================================================
# 📦 MOCK DATABASE — Danh mục quà tặng
# =============================================================================

GIFT_CATALOG = [
    # 🎨 Quà cho người sáng tạo / nghệ thuật
    {"id": "GIFT_001", "name": "Bộ bút vẽ chuyên nghiệp 48 màu", "category": "nghệ thuật", "price": 350000,
     "tags": ["vẽ tranh", "sáng tạo", "handmade", "nghệ thuật"],
     "nhom_tinh_cach": ["sang_tao", "noi_tam"]},
    {"id": "GIFT_002", "name": "Sổ tay da vintage khắc tên", "category": "nghệ thuật", "price": 280000,
     "tags": ["vintage", "sáng tạo", "handmade", "viết lách"],
     "nhom_tinh_cach": ["sang_tao", "noi_tam"]},
    {"id": "GIFT_003", "name": "Máy ảnh chụp lấy liền Instax Mini", "category": "nhiếp ảnh", "price": 1500000,
     "tags": ["nhiếp ảnh", "sáng tạo", "du lịch", "kỷ niệm"],
     "nhom_tinh_cach": ["sang_tao", "huong_ngoai"]},

    # 🏕️ Quà cho người phiêu lưu / outdoor
    {"id": "GIFT_004", "name": "Bình giữ nhiệt Stanley 500ml", "category": "outdoor", "price": 450000,
     "tags": ["camping", "du lịch", "leo núi", "thể thao", "cà phê"],
     "nhom_tinh_cach": ["phieu_luu", "huong_ngoai"]},
    {"id": "GIFT_005", "name": "Đèn pin cắm trại đa năng", "category": "outdoor", "price": 320000,
     "tags": ["camping", "leo núi", "du lịch", "phiêu lưu"],
     "nhom_tinh_cach": ["phieu_luu", "thuc_dung"]},
    {"id": "GIFT_006", "name": "Bộ pha cà phê pour-over du lịch", "category": "outdoor", "price": 480000,
     "tags": ["cà phê", "du lịch", "camping", "cà phê đặc sản"],
     "nhom_tinh_cach": ["phieu_luu", "sang_tao"]},
    {"id": "GIFT_007", "name": "Võng dù gấp gọn siêu nhẹ", "category": "outdoor", "price": 250000,
     "tags": ["camping", "du lịch", "leo núi", "thư giãn"],
     "nhom_tinh_cach": ["phieu_luu", "huong_ngoai"]},

    # 💻 Quà cho người đam mê công nghệ
    {"id": "GIFT_008", "name": "Bàn phím cơ mini Bluetooth", "category": "công nghệ", "price": 890000,
     "tags": ["lập trình", "gaming", "công nghệ", "gadget"],
     "nhom_tinh_cach": ["cong_nghe", "thuc_dung"]},
    {"id": "GIFT_009", "name": "Đế tản nhiệt laptop RGB", "category": "công nghệ", "price": 350000,
     "tags": ["lập trình", "gaming", "công nghệ", "gadget"],
     "nhom_tinh_cach": ["cong_nghe", "thuc_dung"]},
    {"id": "GIFT_010", "name": "Sách 'Clean Code' bản tiếng Việt", "category": "sách", "price": 199000,
     "tags": ["lập trình", "đọc sách", "khoa học", "công nghệ"],
     "nhom_tinh_cach": ["cong_nghe", "noi_tam"]},
    {"id": "GIFT_011", "name": "Chuột không dây ergonomic", "category": "công nghệ", "price": 550000,
     "tags": ["lập trình", "công nghệ", "gadget", "sức khỏe"],
     "nhom_tinh_cach": ["cong_nghe", "thuc_dung"]},

    # 💆 Quà cho người thích chăm sóc bản thân / kết nối
    {"id": "GIFT_012", "name": "Set nến thơm handmade 3 mùi", "category": "chăm sóc", "price": 280000,
     "tags": ["yoga", "thư giãn", "chăm sóc da", "handmade"],
     "nhom_tinh_cach": ["cam_xuc", "noi_tam"]},
    {"id": "GIFT_013", "name": "Bộ dụng cụ làm bánh cơ bản", "category": "nấu ăn", "price": 420000,
     "tags": ["nấu ăn", "làm bánh", "sáng tạo", "chia sẻ"],
     "nhom_tinh_cach": ["cam_xuc", "sang_tao"]},
    {"id": "GIFT_014", "name": "Sách 'Ngôn Ngữ Tình Yêu' - Gary Chapman", "category": "sách", "price": 150000,
     "tags": ["tâm lý", "đọc sách", "cảm xúc", "kết nối"],
     "nhom_tinh_cach": ["cam_xuc", "noi_tam"]},
    {"id": "GIFT_015", "name": "Set mặt nạ dưỡng da cao cấp (10 miếng)", "category": "chăm sóc", "price": 350000,
     "tags": ["chăm sóc da", "làm đẹp", "thư giãn", "tự thưởng"],
     "nhom_tinh_cach": ["cam_xuc", "thuc_dung"]},

    # 🎁 Quà đa năng / phổ biến
    {"id": "GIFT_016", "name": "Túi tote canvas in hình custom", "category": "thời trang", "price": 180000,
     "tags": ["thời trang", "vintage", "handmade", "du lịch"],
     "nhom_tinh_cach": ["sang_tao", "huong_ngoai"]},
    {"id": "GIFT_017", "name": "Gói trải nghiệm Escape Room (2 người)", "category": "trải nghiệm", "price": 300000,
     "tags": ["phiêu lưu", "gaming", "kết nối", "hướng ngoại"],
     "nhom_tinh_cach": ["huong_ngoai", "phieu_luu"]},
    {"id": "GIFT_018", "name": "Hộp chocolate thủ công Maison 12 viên", "category": "ẩm thực", "price": 390000,
     "tags": ["ẩm thực", "chia sẻ", "cảm xúc", "kết nối"],
     "nhom_tinh_cach": ["cam_xuc", "huong_ngoai"]},
]

# =============================================================================
# 📦 MOCK DATABASE — Tồn kho & Khuyến mãi
# =============================================================================

INVENTORY_DATABASE = {
    "GIFT_001": {"stock": 15, "discount": None},
    "GIFT_002": {"stock": 8, "discount": "Giảm 15% — Mã: VINTAGE15"},
    "GIFT_003": {"stock": 3, "discount": "Giảm 5% — Mã: INSTAX5"},
    "GIFT_004": {"stock": 20, "discount": "Giảm 10% — Mã: OUTDOOR10"},
    "GIFT_005": {"stock": 12, "discount": None},
    "GIFT_006": {"stock": 0, "discount": None},  # Hết hàng!
    "GIFT_007": {"stock": 25, "discount": "Giảm 20% — Mã: SUMMER20"},
    "GIFT_008": {"stock": 5, "discount": None},
    "GIFT_009": {"stock": 18, "discount": "Giảm 10% — Mã: TECH10"},
    "GIFT_010": {"stock": 30, "discount": "Giảm 25% — Mã: BOOKWORM25"},
    "GIFT_011": {"stock": 7, "discount": None},
    "GIFT_012": {"stock": 10, "discount": None},
    "GIFT_013": {"stock": 0, "discount": None},  # Hết hàng!
    "GIFT_014": {"stock": 22, "discount": "Giảm 30% — Mã: LOVE30"},
    "GIFT_015": {"stock": 14, "discount": "Giảm 10% — Mã: GLOW10"},
    "GIFT_016": {"stock": 9, "discount": None},
    "GIFT_017": {"stock": 6, "discount": "Giảm 15% — Mã: FUN15"},
    "GIFT_018": {"stock": 11, "discount": None},
}

# =============================================================================
# 📦 MOCK DATABASE — Quy tắc / kiêng kỵ theo dịp lễ & văn hóa
# =============================================================================

QUY_TAC_DIP_LE = {
    ("tết", "nhật bản"): {
        "nen_tranh": ["đồng hồ", "vật sắc nhọn (dao, kéo)", "số lượng 4 hoặc 9"],
        "nen_uu_tien": ["trà", "văn phòng phẩm cao cấp", "đồ trang trí tinh tế"],
        "ghi_chu": "Người Nhật coi đồng hồ tượng trưng cho thời gian cạn dần, tránh tặng cho người lớn tuổi/cấp trên."
    },
    ("tết", "việt nam"): {
        "nen_tranh": ["vật sắc nhọn", "đồ màu đen/trắng toàn bộ"],
        "nen_uu_tien": ["trà", "bánh mứt cao cấp", "quà mang ý nghĩa may mắn"],
        "ghi_chu": "Tránh tặng số lượng lẻ mang ý nghĩa xui rủi tùy vùng miền."
    },
    ("sinh nhật", None): {
        "nen_tranh": [],
        "nen_uu_tien": ["quà cá nhân hóa theo sở thích"],
        "ghi_chu": "Không có kiêng kỵ đặc biệt, ưu tiên cá nhân hóa theo tính cách người nhận."
    },
    ("valentine", None): {
        "nen_tranh": ["quà mang tính công việc/văn phòng thuần túy"],
        "nen_uu_tien": ["quà mang ý nghĩa tình cảm, lãng mạn"],
        "ghi_chu": "Ưu tiên yếu tố cảm xúc hơn giá trị vật chất."
    },
    ("8/3", None): {
        "nen_tranh": ["đồ gia dụng mang tính nghĩa vụ (chổi, nồi cơm...)"],
        "nen_uu_tien": ["hoa, mỹ phẩm, set chăm sóc bản thân, voucher spa"],
        "ghi_chu": "Ngày Quốc tế Phụ nữ — ưu tiên quà giúp người nhận thư giãn và yêu bản thân."
    },
    ("giáng sinh", None): {
        "nen_tranh": [],
        "nen_uu_tien": ["quà đóng gói đẹp, mang tính bất ngờ", "chocolate, nến thơm"],
        "ghi_chu": "Giáng sinh chú trọng sự ấm áp và bất ngờ. Gói quà đẹp rất quan trọng."
    },
}


# =============================================================================
# 🛠️ TOOL 1: Tra cứu kết quả trắc nghiệm tính cách
# =============================================================================

def get_personality_profile(person_name: str) -> str:
    """
    Tra cứu kết quả trắc nghiệm tính cách của một người từ cơ sở dữ liệu.
    Kết quả bao gồm: loại tính cách, đặc điểm, sở thích, phong cách sống,
    điểm số các chiều tính cách, và những thứ người đó KHÔNG thích.

    LUÔN gọi tool này ĐẦU TIÊN khi người dùng muốn chọn quà cho ai đó.

    Args:
        person_name (str): Tên hoặc username của người cần tra cứu.
                           Ví dụ: 'minh_anh', 'anh_tu', 'Hoàng Long'

    Returns:
        str: Thông tin tính cách chi tiết nếu tìm thấy.
             Chuỗi thông báo lỗi nếu không tìm thấy người này.

    Ví dụ:
        >>> get_personality_profile("minh_anh")
        "📋 KẾT QUẢ TRẮC NGHIỆM — Minh Anh ..."
        >>> get_personality_profile("user_la")
        "LỖI: Không tìm thấy kết quả trắc nghiệm ..."
    """
    try:
        # Chuẩn hóa tên: bỏ dấu cách thừa, chuyển lowercase, thay khoảng trắng bằng _
        key = person_name.strip().lower().replace(" ", "_")

        if key not in PERSONALITY_DATABASE:
            available = ", ".join(
                p["name"] for p in PERSONALITY_DATABASE.values()
            )
            return (
                f"LỖI: Không tìm thấy kết quả trắc nghiệm cho '{person_name}'. "
                f"Những người đã làm trắc nghiệm: {available}."
            )

        profile = PERSONALITY_DATABASE[key]
        quiz = profile["quiz_result"]
        scores = quiz["score_summary"]

        result = (
            f"📋 KẾT QUẢ TRẮC NGHIỆM TÍNH CÁCH — {profile['name']}\n"
            f"🏷️ Loại tính cách: {quiz['personality_type']}\n"
            f"✨ Đặc điểm nổi bật: {', '.join(quiz['traits'])}\n"
            f"❤️ Sở thích: {', '.join(quiz['interests'])}\n"
            f"🏠 Phong cách sống: {quiz['lifestyle']}\n"
            f"🚫 Không thích: {', '.join(quiz['dislike'])}\n"
            f"📊 Điểm tính cách (thang 1-10): "
            f"Sáng tạo={scores['sang_tao']}, "
            f"Hướng ngoại={scores['huong_ngoai']}, "
            f"Thực dụng={scores['thuc_dung']}, "
            f"Cảm xúc={scores['cam_xuc']}, "
            f"Phiêu lưu={scores['phieu_luu']}"
        )
        return result

    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi khi tra cứu tính cách — {str(e)}"


# =============================================================================
# 🛠️ TOOL 2: Tìm kiếm quà tặng theo sở thích và ngân sách
# =============================================================================

def search_gift_catalog(
    interests: str,
    budget: float,
    loai_tru: Optional[str] = None,
) -> str:
    """
    Tìm kiếm quà tặng phù hợp trong danh mục dựa trên sở thích và ngân sách.
    Hỗ trợ loại trừ sản phẩm theo từ khóa kiêng kỵ (từ tra_cuu_quy_tac_dip).
    Trả về danh sách quà khớp nhiều tag sở thích nhất, sắp xếp theo độ phù hợp.

    Khi nào nên dùng: Sau khi đã biết sở thích/tính cách người nhận quà.
    Khi nào KHÔNG nên dùng: Khi chưa biết sở thích → gọi get_personality_profile trước.

    Args:
        interests (str): Các sở thích, phân cách bằng dấu phẩy.
                         Ví dụ: 'camping, cà phê, du lịch'
        budget (float):  Ngân sách tối đa (đơn vị VNĐ). Ví dụ: 500000
        loai_tru (str):  Các từ khóa tên sản phẩm cần loại trừ (phân cách bằng dấu phẩy).
                         Dùng khi có quy tắc kiêng kỵ. Ví dụ: 'đồng hồ, dao'. Mặc định None.

    Returns:
        str: Danh sách quà phù hợp (tối đa 5 món) kèm giá và mã sản phẩm.
             Chuỗi thông báo lỗi nếu ngân sách không hợp lệ hoặc không tìm thấy.

    Ví dụ:
        >>> search_gift_catalog("camping, cà phê", 500000)
        "🎁 TÌM THẤY 3 MÓN QUÀ PHÙ HỢP ..."
        >>> search_gift_catalog("du lịch", -100)
        "LỖI: Ngân sách phải là số dương ..."
    """
    try:
        # Validate ngân sách
        budget = float(budget)
        if budget <= 0:
            return f"LỖI: Ngân sách phải là số dương. Bạn đã nhập: {budget} VNĐ."

        # Tách danh sách sở thích
        interest_list = [i.strip().lower() for i in interests.split(",") if i.strip()]
        if not interest_list:
            return "LỖI: Vui lòng cung cấp ít nhất 1 sở thích (phân cách bằng dấu phẩy)."

        # Tách danh sách loại trừ (nếu có)
        exclude_list = []
        if loai_tru:
            exclude_list = [x.strip().lower() for x in loai_tru.split(",") if x.strip()]

        # Tìm quà phù hợp: lọc theo ngân sách, đếm số tag khớp
        matched_gifts = []
        for gift in GIFT_CATALOG:
            if gift["price"] > budget:
                continue

            # Loại trừ theo từ khóa kiêng kỵ
            if any(ex in gift["name"].lower() for ex in exclude_list):
                continue

            # Đếm số tag khớp với sở thích
            match_count = 0
            for interest in interest_list:
                for tag in gift["tags"]:
                    if interest in tag.lower() or tag.lower() in interest:
                        match_count += 1
                        break
            if match_count > 0:
                matched_gifts.append((match_count, gift))

        # Sắp xếp theo số tag khớp (giảm dần), lấy tối đa 5 món
        matched_gifts.sort(key=lambda x: x[0], reverse=True)
        top_gifts = matched_gifts[:5]

        if not top_gifts:
            return (
                f"LỖI: Không tìm thấy quà phù hợp với sở thích '{interests}' "
                f"trong ngân sách {budget:,.0f} VNĐ. "
                f"Hãy thử mở rộng ngân sách hoặc thay đổi từ khóa sở thích."
            )

        # Format kết quả
        lines = [f"🎁 TÌM THẤY {len(top_gifts)} MÓN QUÀ PHÙ HỢP (ngân sách ≤ {budget:,.0f} VNĐ):"]
        for i, (score, gift) in enumerate(top_gifts, 1):
            lines.append(
                f"  {i}. [{gift['id']}] {gift['name']} — "
                f"Giá: {gift['price']:,.0f} VNĐ — "
                f"Danh mục: {gift['category']} — "
                f"Độ khớp: {score} tag"
            )
        return "\n".join(lines)

    except ValueError:
        return f"LỖI: Ngân sách '{budget}' không phải là một số hợp lệ. Vui lòng nhập số (VD: 500000)."
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi khi tìm quà — {str(e)}"


# =============================================================================
# 🛠️ TOOL 3: Kiểm tra tồn kho và khuyến mãi
# =============================================================================

def check_gift_availability(gift_id: str) -> str:
    """
    Kiểm tra tình trạng tồn kho và mã khuyến mãi hiện có của một món quà.
    PHẢI gọi tool này cho sản phẩm được chọn cuối cùng trước khi trả Final Answer.

    Args:
        gift_id (str): Mã sản phẩm duy nhất. Ví dụ: 'GIFT_004'

    Returns:
        str: Thông tin tồn kho (số lượng còn, mã giảm giá nếu có).
             Chuỗi thông báo lỗi nếu mã sản phẩm không tồn tại.

    Ví dụ:
        >>> check_gift_availability("GIFT_004")
        "📦 THÔNG TIN TỒN KHO — GIFT_004 ..."
        >>> check_gift_availability("INVALID")
        "LỖI: Mã sản phẩm 'INVALID' không tồn tại ..."
    """
    try:
        gift_id = gift_id.strip().upper()

        if gift_id not in INVENTORY_DATABASE:
            valid_ids = ", ".join(sorted(INVENTORY_DATABASE.keys()))
            return (
                f"LỖI: Mã sản phẩm '{gift_id}' không tồn tại trong hệ thống. "
                f"Các mã hợp lệ: {valid_ids}."
            )

        inv = INVENTORY_DATABASE[gift_id]

        # Tìm tên sản phẩm từ catalog
        gift_name = "Không rõ"
        gift_price = 0
        for g in GIFT_CATALOG:
            if g["id"] == gift_id:
                gift_name = g["name"]
                gift_price = g["price"]
                break

        stock = inv["stock"]
        discount = inv["discount"]

        if stock == 0:
            return (
                f"📦 THÔNG TIN TỒN KHO — {gift_id}\n"
                f"🏷️ Sản phẩm: {gift_name}\n"
                f"💰 Giá niêm yết: {gift_price:,.0f} VNĐ\n"
                f"❌ Trạng thái: HẾT HÀNG — Không thể mua lúc này.\n"
                f"💡 Gợi ý: Hãy tìm món quà thay thế khác bằng search_gift_catalog."
            )

        status = "Còn hàng" if stock > 5 else f"Sắp hết (chỉ còn {stock} sản phẩm)"
        result = (
            f"📦 THÔNG TIN TỒN KHO — {gift_id}\n"
            f"🏷️ Sản phẩm: {gift_name}\n"
            f"💰 Giá niêm yết: {gift_price:,.0f} VNĐ\n"
            f"✅ Trạng thái: {status} ({stock} sản phẩm)\n"
        )
        if discount:
            result += f"🎉 Khuyến mãi: {discount}\n"
        else:
            result += f"🔖 Khuyến mãi: Không có khuyến mãi hiện tại.\n"

        return result.strip()

    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi khi kiểm tra tồn kho — {str(e)}"


# =============================================================================
# 🛠️ TOOL 4: Gợi ý quà theo loại tính cách
# =============================================================================

def suggest_gift_by_personality(personality_type: str, budget: float) -> str:
    """
    Gợi ý quà tặng dựa trên loại tính cách từ kết quả trắc nghiệm.
    Tool này ánh xạ trực tiếp loại tính cách → danh mục quà phù hợp nhất,
    giúp Agent rút gọn bước suy luận khi đã biết personality_type.

    Khi nào nên dùng: Khi đã biết loại tính cách (từ get_personality_profile)
                      và muốn gợi ý nhanh không cần liệt kê sở thích cụ thể.
    Khi nào KHÔNG nên dùng: Khi muốn tìm kiếm chi tiết theo từng sở thích cụ thể
                            → dùng search_gift_catalog thay thế.

    Args:
        personality_type (str): Loại tính cách. Ví dụ: 'Người Sáng Tạo',
                                'Người Phiêu Lưu', 'Người Phân Tích', 'Người Kết Nối'
        budget (float): Ngân sách tối đa (đơn vị VNĐ). Ví dụ: 500000

    Returns:
        str: Danh sách quà gợi ý (tối đa 3 món) phù hợp loại tính cách.
             Chuỗi thông báo lỗi nếu không nhận diện được loại tính cách.

    Ví dụ:
        >>> suggest_gift_by_personality("Người Phiêu Lưu", 500000)
        "🎯 GỢI Ý QUÀ CHO 'Người Phiêu Lưu' ..."
    """
    try:
        budget = float(budget)
        if budget <= 0:
            return f"LỖI: Ngân sách phải là số dương. Bạn đã nhập: {budget} VNĐ."

        # Ánh xạ loại tính cách → nhom_tinh_cach key trên catalog
        ptype = personality_type.strip().lower()
        mapping = {
            "sáng tạo": ["sang_tao", "noi_tam"],
            "creator": ["sang_tao", "noi_tam"],
            "phiêu lưu": ["phieu_luu", "huong_ngoai"],
            "adventurer": ["phieu_luu", "huong_ngoai"],
            "phân tích": ["cong_nghe", "thuc_dung"],
            "analyst": ["cong_nghe", "thuc_dung"],
            "kết nối": ["cam_xuc", "huong_ngoai"],
            "connector": ["cam_xuc", "huong_ngoai"],
        }

        # Tìm key phù hợp
        matched_groups = None
        for key, groups in mapping.items():
            if key in ptype:
                matched_groups = groups
                break

        if matched_groups is None:
            available_types = "Người Sáng Tạo, Người Phiêu Lưu, Người Phân Tích, Người Kết Nối"
            return (
                f"LỖI: Không nhận diện được loại tính cách '{personality_type}'. "
                f"Các loại hỗ trợ: {available_types}."
            )

        # Lọc quà theo nhom_tinh_cach trên catalog + ngân sách
        matched = []
        for gift in GIFT_CATALOG:
            if gift["price"] > budget:
                continue
            score = sum(1 for g in gift.get("nhom_tinh_cach", []) if g in matched_groups)
            if score > 0:
                matched.append((score, gift))

        matched.sort(key=lambda x: x[0], reverse=True)
        top = matched[:3]

        if not top:
            return (
                f"LỖI: Không tìm thấy quà cho '{personality_type}' "
                f"trong ngân sách {budget:,.0f} VNĐ. Hãy thử tăng ngân sách."
            )

        lines = [
            f"🎯 GỢI Ý QUÀ CHO '{personality_type}' (ngân sách ≤ {budget:,.0f} VNĐ):"
        ]
        for i, (score, gift) in enumerate(top, 1):
            lines.append(
                f"  {i}. [{gift['id']}] {gift['name']} — "
                f"Giá: {gift['price']:,.0f} VNĐ"
            )
        lines.append(
            f"💡 Dùng check_gift_availability[gift_id] để kiểm tra tồn kho trước khi chốt."
        )
        return "\n".join(lines)

    except ValueError:
        return f"LỖI: Ngân sách '{budget}' không phải là một số hợp lệ."
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi khi gợi ý quà — {str(e)}"


# =============================================================================
# 🛠️ TOOL 5: Tra cứu quy tắc / kiêng kỵ theo dịp lễ & văn hóa
# =============================================================================

def tra_cuu_quy_tac_dip(dip_le: str, van_hoa: Optional[str] = None) -> str:
    """
    Tra cứu các lưu ý / điều kiêng kỵ khi tặng quà theo dịp lễ và văn hóa cụ thể.
    PHẢI gọi tool này TRƯỚC search_gift_catalog nếu người dùng đề cập dịp lễ
    có yếu tố văn hóa/nghi thức (Tết, lễ truyền thống, đối tác nước ngoài...).

    Args:
        dip_le (str): Tên dịp lễ. Ví dụ: 'Tết', 'sinh nhật', 'Valentine', '8/3', 'Giáng sinh'
        van_hoa (str): Văn hóa cụ thể (tùy chọn). Ví dụ: 'Nhật Bản', 'Việt Nam'.
                       Để None nếu không rõ hoặc quy tắc chung.

    Returns:
        str: Các điều nên tránh, nên ưu tiên, và ghi chú quan trọng.
             Chuỗi thông báo nếu không tìm thấy dữ liệu cho dịp lễ này.

    Ví dụ:
        >>> tra_cuu_quy_tac_dip("Tết", "Nhật Bản")
        "📜 QUY TẮC TẶNG QUÀ — Dịp: Tết | Văn hóa: Nhật Bản ..."
        >>> tra_cuu_quy_tac_dip("sinh nhật")
        "📜 QUY TẮC TẶNG QUÀ — Dịp: sinh nhật ..."
    """
    try:
        key_dip = dip_le.strip().lower()
        key_vh = van_hoa.strip().lower() if van_hoa else None

        # Ưu tiên khớp đúng cả dịp lễ + văn hóa, sau đó fallback về dịp lễ chung
        quy_tac = None
        for (d, v), qt in QUY_TAC_DIP_LE.items():
            if d == key_dip and v == key_vh:
                quy_tac = qt
                break

        if quy_tac is None:
            for (d, v), qt in QUY_TAC_DIP_LE.items():
                if d == key_dip and v is None:
                    quy_tac = qt
                    break

        if quy_tac is None:
            vh_text = f" / văn hóa '{van_hoa}'" if van_hoa else ""
            return (
                f"LỖI: Chưa có dữ liệu quy tắc cho dịp '{dip_le}'{vh_text}. "
                f"Các dịp có sẵn: Tết (Việt Nam, Nhật Bản), Sinh nhật, Valentine, 8/3, Giáng sinh."
            )

        vh_display = f" | Văn hóa: {van_hoa}" if van_hoa else ""
        tranh = ", ".join(quy_tac["nen_tranh"]) if quy_tac["nen_tranh"] else "Không có kiêng kỵ đặc biệt"
        uu_tien = ", ".join(quy_tac["nen_uu_tien"])

        result = (
            f"📜 QUY TẮC TẶNG QUÀ — Dịp: {dip_le}{vh_display}\n"
            f"🚫 Nên tránh: {tranh}\n"
            f"✅ Nên ưu tiên: {uu_tien}\n"
            f"📝 Ghi chú: {quy_tac['ghi_chu']}"
        )
        return result

    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi khi tra cứu quy tắc dịp lễ — {str(e)}"


# =============================================================================
# 🛠️ TOOL 6: Tính ngân sách góp (chia đều khi nhiều người góp quà)
# =============================================================================

def tinh_ngan_sach_gop(tong_tien: int, so_nguoi_gop: int) -> str:
    """
    Chia đều ngân sách khi nhiều người cùng góp mua một món quà.
    Giúp nhóm bạn bè / đồng nghiệp biết mỗi người cần góp bao nhiêu.

    Args:
        tong_tien (int): Tổng ngân sách dự kiến hoặc giá sản phẩm (đơn vị VNĐ). Ví dụ: 900000
        so_nguoi_gop (int): Số người tham gia góp quà. Ví dụ: 4

    Returns:
        str: Thông tin phân chia ngân sách (tổng tiền, số người, mỗi người góp).
             Chuỗi thông báo lỗi nếu tham số không hợp lệ.

    Ví dụ:
        >>> tinh_ngan_sach_gop(900000, 4)
        "💰 PHÂN CHIA NGÂN SÁCH GÓP QUÀ ..."
        >>> tinh_ngan_sach_gop(500000, 0)
        "LỖI: Số người góp phải lớn hơn 0."
    """
    try:
        tong_tien = int(tong_tien)
        so_nguoi_gop = int(so_nguoi_gop)

        if so_nguoi_gop <= 0:
            return "LỖI: Số người góp phải lớn hơn 0."
        if tong_tien <= 0:
            return "LỖI: Tổng tiền phải là số dương."

        moi_nguoi = round(tong_tien / so_nguoi_gop)
        result = (
            f"💰 PHÂN CHIA NGÂN SÁCH GÓP QUÀ\n"
            f"💵 Tổng tiền: {tong_tien:,.0f} VNĐ\n"
            f"👥 Số người góp: {so_nguoi_gop}\n"
            f"🧮 Mỗi người góp: {moi_nguoi:,.0f} VNĐ"
        )
        return result

    except ValueError:
        return f"LỖI: Tham số không hợp lệ. tong_tien và so_nguoi_gop phải là số nguyên."
    except Exception as e:
        return f"LỖI: Đã xảy ra lỗi khi tính ngân sách — {str(e)}"


# =============================================================================
# 📋 ĐĂNG KÝ DANH SÁCH TOOLS CHO AGENT
# =============================================================================

AVAILABLE_TOOLS = {
    "get_personality_profile": get_personality_profile,
    "search_gift_catalog": search_gift_catalog,
    "check_gift_availability": check_gift_availability,
    "suggest_gift_by_personality": suggest_gift_by_personality,
    "tra_cuu_quy_tac_dip": tra_cuu_quy_tac_dip,
    "tinh_ngan_sach_gop": tinh_ngan_sach_gop,
}


# =============================================================================
# 📋 TOOL SPECS — Schema chuẩn cho LLM function-calling
# =============================================================================

TOOL_SPECS = [
    {
        "name": "get_personality_profile",
        "description": (
            "Tra cứu kết quả trắc nghiệm tính cách của một người (loại tính cách, sở thích, "
            "đặc điểm, phong cách sống, điểm số các chiều tính cách). "
            "LUÔN gọi tool này ĐẦU TIÊN khi người dùng muốn chọn quà cho ai đó."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "person_name": {
                    "type": "string",
                    "description": "Tên hoặc username người cần tra cứu. VD: 'minh_anh', 'Anh Tú'."
                }
            },
            "required": ["person_name"],
        },
    },
    {
        "name": "search_gift_catalog",
        "description": (
            "Tìm kiếm quà tặng theo sở thích và ngân sách. Hỗ trợ loại trừ sản phẩm kiêng kỵ. "
            "Trả về danh sách rỗng nếu không có sản phẩm phù hợp — KHÔNG được tự bịa sản phẩm."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "interests": {
                    "type": "string",
                    "description": "Các sở thích phân cách bằng dấu phẩy. VD: 'camping, cà phê'."
                },
                "budget": {
                    "type": "number",
                    "description": "Ngân sách tối đa (VNĐ). VD: 500000."
                },
                "loai_tru": {
                    "type": "string",
                    "description": "Từ khóa tên sản phẩm cần loại trừ (phân cách bằng dấu phẩy). Dùng khi có quy tắc kiêng kỵ."
                },
            },
            "required": ["interests", "budget"],
        },
    },
    {
        "name": "check_gift_availability",
        "description": (
            "Kiểm tra tồn kho và khuyến mãi của một sản phẩm cụ thể (theo mã sản phẩm). "
            "PHẢI gọi tool này cho sản phẩm được chọn cuối cùng trước khi trả Final Answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "gift_id": {
                    "type": "string",
                    "description": "Mã sản phẩm. VD: 'GIFT_004'."
                }
            },
            "required": ["gift_id"],
        },
    },
    {
        "name": "suggest_gift_by_personality",
        "description": (
            "Gợi ý quà nhanh dựa trên loại tính cách (từ kết quả trắc nghiệm). "
            "Dùng khi muốn gợi ý nhanh mà không cần liệt kê từng sở thích cụ thể."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "personality_type": {
                    "type": "string",
                    "description": "Loại tính cách. VD: 'Người Sáng Tạo', 'Người Phiêu Lưu'."
                },
                "budget": {
                    "type": "number",
                    "description": "Ngân sách tối đa (VNĐ). VD: 500000."
                },
            },
            "required": ["personality_type", "budget"],
        },
    },
    {
        "name": "tra_cuu_quy_tac_dip",
        "description": (
            "Tra cứu điều nên tránh / nên ưu tiên khi tặng quà theo dịp lễ và văn hóa cụ thể. "
            "PHẢI gọi TRƯỚC search_gift_catalog khi người dùng đề cập dịp lễ có yếu tố văn hóa."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dip_le": {
                    "type": "string",
                    "description": "Tên dịp lễ. VD: 'Tết', 'sinh nhật', 'Valentine', '8/3'."
                },
                "van_hoa": {
                    "type": "string",
                    "description": "Văn hóa cụ thể (tùy chọn). VD: 'Nhật Bản', 'Việt Nam'."
                },
            },
            "required": ["dip_le"],
        },
    },
    {
        "name": "tinh_ngan_sach_gop",
        "description": "Chia đều ngân sách khi nhiều người cùng góp mua một món quà.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tong_tien": {
                    "type": "integer",
                    "description": "Tổng ngân sách dự kiến (VNĐ). VD: 900000."
                },
                "so_nguoi_gop": {
                    "type": "integer",
                    "description": "Số người tham gia góp quà. VD: 4."
                },
            },
            "required": ["tong_tien", "so_nguoi_gop"],
        },
    },
]


# =============================================================================
# 🧪 QUICK SELF-TEST (chạy: python src/tools.py)
# =============================================================================

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=" * 60)
    print("🧪 SELF-TEST: Tools cho Trợ Lý Chọn Quà Tặng")
    print("=" * 60)

    print("\n== Test 1: get_personality_profile ==")
    print(get_personality_profile("anh_tu"))

    print("\n== Test 2: get_personality_profile (edge case) ==")
    print(get_personality_profile("user_khong_ton_tai"))

    print("\n== Test 3: search_gift_catalog ==")
    print(search_gift_catalog("camping, cà phê", 500000))

    print("\n== Test 4: search_gift_catalog (với loại trừ) ==")
    print(search_gift_catalog("camping, cà phê", 500000, loai_tru="bình giữ nhiệt"))

    print("\n== Test 5: search_gift_catalog (edge case: ngân sách âm) ==")
    print(search_gift_catalog("du lịch", -100))

    print("\n== Test 6: check_gift_availability (còn hàng + khuyến mãi) ==")
    print(check_gift_availability("GIFT_004"))

    print("\n== Test 7: check_gift_availability (hết hàng) ==")
    print(check_gift_availability("GIFT_006"))

    print("\n== Test 8: check_gift_availability (edge case: mã sai) ==")
    print(check_gift_availability("INVALID"))

    print("\n== Test 9: suggest_gift_by_personality ==")
    print(suggest_gift_by_personality("Người Phiêu Lưu", 500000))

    print("\n== Test 10: tra_cuu_quy_tac_dip (Tết - Nhật Bản) ==")
    print(tra_cuu_quy_tac_dip("Tết", "Nhật Bản"))

    print("\n== Test 11: tra_cuu_quy_tac_dip (sinh nhật) ==")
    print(tra_cuu_quy_tac_dip("sinh nhật"))

    print("\n== Test 12: tra_cuu_quy_tac_dip (edge case: dịp lạ) ==")
    print(tra_cuu_quy_tac_dip("Halloween"))

    print("\n== Test 13: tinh_ngan_sach_gop ==")
    print(tinh_ngan_sach_gop(900000, 4))

    print("\n== Test 14: tinh_ngan_sach_gop (edge case: 0 người) ==")
    print(tinh_ngan_sach_gop(500000, 0))

    print("\n" + "=" * 60)
    print(f"✅ Tổng cộng {len(AVAILABLE_TOOLS)} tools đã đăng ký: {list(AVAILABLE_TOOLS.keys())}")
    print(f"✅ Tổng cộng {len(TOOL_SPECS)} tool specs đã khai báo.")
    print("=" * 60)
