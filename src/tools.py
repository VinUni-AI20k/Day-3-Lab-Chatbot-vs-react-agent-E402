"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
📌 Đề tài 3: Trợ Lý Nắm Bắt Tính Cách & Chọn Quà Tặng Phù Hợp

Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi:
  1. get_personality_profile     -> tra cứu tính cách một người (theo tên)
  2. tra_cuu_quy_tac_dip         -> tra cứu điều nên tránh/nên tặng theo dịp lễ + văn hóa
  3. search_gift_catalog         -> tìm quà theo sở thích + ngân sách (+ loại trừ)
  4. suggest_gift_by_personality -> gợi ý nhanh quà theo nhóm tính cách + ngân sách
  5. check_gift_availability     -> kiểm tra tồn kho/khuyến mãi theo mã quà
  6. tinh_ngan_sach_gop          -> chia đều tiền quà cho nhiều người góp chung

Nguyên tắc chung của MỌI tool trong file này: KHÔNG BAO GIỜ raise Exception ra
ngoài — mọi lỗi (không tìm thấy, tham số sai, ngân sách âm...) đều trả về một
chuỗi bắt đầu bằng "LỖI:" để Agent (src/app.py) đưa vào Observation và tự phục
hồi theo Guardrails ở src/prompts.py, thay vì làm crash cả chương trình.
"""

import unicodedata


# =============================================================================
# 🧰 HÀM TIỆN ÍCH NỘI BỘ
# =============================================================================

def _normalize(text) -> str:
    """Chuẩn hoá chuỗi tiếng Việt để so khớp: bỏ dấu, hạ chữ thường, nối bằng "_".

    Đây là bản vá cho lỗi đã ghi chú trong prompts.py: trước đây
    get_personality_profile so khớp CHÍNH XÁC key có dấu gạch dưới không dấu
    (vd "hoang_long"), nên input có dấu như "Hoàng Long" sẽ KHÔNG khớp. Hàm
    này chuẩn hoá cả input người dùng lẫn key trong DB về cùng 1 dạng trước khi
    so sánh, nên "Hoàng Long", "hoàng long", "hoang_long", "Hoang Long" đều ra
    cùng 1 kết quả.
    """
    text = str(text).strip().lower()
    text = text.replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("-", " ").replace("_", " ")
    text = "_".join(text.split())
    return text


def _to_number(value, field_name: str) -> float:
    """Ép kiểu số an toàn (Action do LLM sinh ra có thể lỡ để số trong chuỗi)."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} phải là số, không phải boolean.")
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    is_thousand_separated = "," in text or text.count(".") > 1
    if is_thousand_separated:
        text = text.replace(",", "").replace(".", "")
    try:
        return float(text)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} = '{value}' không phải là số hợp lệ.")


def _as_list(value) -> list:
    """Cho phép tham số dạng danh sách được truyền như list hoặc 1 chuỗi đơn."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return [str(value)]


def _format_vnd(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", ".") + " VNĐ"


# =============================================================================
# 🗄️ DỮ LIỆU GIẢ LẬP (MOCK DATABASE)
# =============================================================================

# --- Hồ sơ tính cách (mô phỏng kết quả trắc nghiệm tính cách vui) ---
PERSONALITY_DB = {
    "minh_anh": {
        "display_name": "Minh Anh",
        "personality_type": "Người Sáng Tạo",
        "so_thich": ["sang_tao", "sach", "am_nhac"],
        "mo_ta": "Thích trải nghiệm mới lạ, yêu nghệ thuật và thể hiện bản thân.",
    },
    "anh_tu": {
        "display_name": "Anh Tú",
        "personality_type": "Người Chuyên Nghiệp",
        "so_thich": ["van_phong_pham_cao_cap", "tra_cafe"],
        "mo_ta": "Điềm đạm, coi trọng sự tinh tế, lịch sự và chỉn chu trong công việc.",
    },
    "hoang_long": {
        "display_name": "Hoàng Long",
        "personality_type": "Người Phiêu Lưu",
        "so_thich": ["outdoor", "the_thao"],
        "mo_ta": "Năng động, thích khám phá, ưa vận động ngoài trời.",
    },
    "lan_anh": {
        "display_name": "Lan Anh",
        "personality_type": "Người Điềm Tĩnh",
        "so_thich": ["tra_cafe", "sach"],
        "mo_ta": "Trầm tính, thích không gian yên bình, thư giãn với sách và trà.",
    },
}

# Ánh xạ NHÓM TÍNH CÁCH (dùng cho suggest_gift_by_personality khi chưa có hồ sơ
# chi tiết từng người, chỉ có personality_type chung).
PERSONALITY_TAG_MAP = {
    "nguoi_sang_tao": ["sang_tao", "sach", "am_nhac"],
    "nguoi_phieu_luu": ["outdoor", "the_thao"],
    "nguoi_chuyen_nghiep": ["van_phong_pham_cao_cap", "tra_cafe"],
    "nguoi_thuc_te": ["van_phong_pham_cao_cap", "cong_nghe"],
    "nguoi_diem_tinh": ["tra_cafe", "sach"],
    "nguoi_cong_nghe": ["cong_nghe", "am_nhac"],
}

# --- Danh mục quà (giá tính bằng VNĐ) ---
GIFT_CATALOG = {
    "GIFT_001": {
        "ten": "Bút ký cao cấp khắc tên",
        "gia": 350_000,
        "tags": ["van_phong_pham_cao_cap"],
        "ton_kho": 5,
        "khuyen_mai": None,
    },
    "GIFT_002": {
        "ten": "Bộ trà cao cấp hộp gỗ",
        "gia": 890_000,
        "tags": ["tra_cafe", "van_phong_pham_cao_cap"],
        "ton_kho": 3,
        "khuyen_mai": "Giảm 5% - Mã TRA5",
    },
    "GIFT_003": {
        "ten": "Sổ tay da thủ công phong cách sáng tạo",
        "gia": 320_000,
        "tags": ["sang_tao"],
        "ton_kho": 10,
        "khuyen_mai": None,
    },
    "GIFT_004": {
        "ten": "Bình giữ nhiệt Stanley 500ml",
        "gia": 450_000,
        "tags": ["outdoor"],
        "ton_kho": 7,
        "khuyen_mai": "Giảm 10% - Mã OUTDOOR10",
    },
    "GIFT_005": {
        "ten": "Đồng hồ để bàn cao cấp",
        "gia": 1_200_000,
        # Đồng hồ bị kiêng kỵ khi tặng dịp Tết cho đối tác Nhật/Hoa (gợi liên
        # tưởng "hết giờ" / tang lễ) -> gắn tag kieng_ky để search_gift_catalog
        # có thể loại trừ đúng theo kết quả tra_cuu_quy_tac_dip.
        "tags": ["van_phong_pham_cao_cap", "dong_ho"],
        "ton_kho": 4,
        "khuyen_mai": None,
    },
    "GIFT_006": {
        "ten": "Bộ dao kéo nhà bếp inox cao cấp",
        "gia": 680_000,
        # Dao/kéo tượng trưng cho "cắt đứt" quan hệ -> kiêng kỵ dịp Tết.
        "tags": ["gia_dung", "dao_keo"],
        "ton_kho": 6,
        "khuyen_mai": None,
    },
    "GIFT_007": {
        "ten": "Tai nghe không dây chống ồn",
        "gia": 650_000,
        "tags": ["cong_nghe", "am_nhac"],
        "ton_kho": 8,
        "khuyen_mai": None,
    },
    "GIFT_008": {
        "ten": "Combo sách kỹ năng bán chạy",
        "gia": 150_000,
        "tags": ["sach"],
        "ton_kho": 20,
        "khuyen_mai": None,
    },
    "GIFT_009": {
        "ten": "Bộ dụng cụ cắm trại mini",
        "gia": 780_000,
        "tags": ["outdoor", "the_thao"],
        "ton_kho": 4,
        "khuyen_mai": None,
    },
    "GIFT_010": {
        "ten": "Loa bluetooth mini",
        "gia": 590_000,
        "tags": ["am_nhac", "cong_nghe"],
        "ton_kho": 0,
        "khuyen_mai": None,
    },
}

# --- Quy tắc kiêng kỵ / nên tặng theo DỊP LỄ, có thể lồng thêm theo VĂN HÓA ---
OCCASION_RULES = {
    "tet": {
        "chung": {
            "nen_tang": ["bánh mứt", "lì xì", "trà", "văn phòng phẩm cao cấp"],
            "kieng_ky": ["dao_keo"],
            "kieng_ky_ghi_chu": ["Không tặng dao/kéo (ngụ ý cắt đứt quan hệ)."],
        },
        "nhat_ban": {
            "nen_tang": ["trà", "văn phòng phẩm cao cấp", "bánh kẹo đóng hộp trang nhã"],
            "kieng_ky": ["dong_ho", "dao_keo"],
            "kieng_ky_ghi_chu": [
                "Không tặng đồng hồ (âm gần với 'kết thúc/tang lễ').",
                "Không tặng dao/kéo (ngụ ý cắt đứt quan hệ).",
                "Tránh gói quà toàn màu trắng hoặc đen thuần (liên tưởng tang lễ).",
                "Tránh set 4 món (số 4 đọc gần âm 'tử' - cái chết).",
            ],
        },
        "trung_quoc": {
            "nen_tang": ["trà", "bánh kẹo đóng hộp trang nhã"],
            "kieng_ky": ["dong_ho", "dao_keo"],
            "kieng_ky_ghi_chu": [
                "Không tặng đồng hồ (âm gần 'tống chung' - đưa đám).",
                "Không tặng dao/kéo (ngụ ý cắt đứt quan hệ).",
            ],
        },
    },
    "giang_sinh": {
        "chung": {
            "nen_tang": ["đồ ấm", "đồ trang trí", "bánh kẹo"],
            "kieng_ky": [],
            "kieng_ky_ghi_chu": [],
        },
    },
    "trung_thu": {
        "chung": {
            "nen_tang": ["bánh trung thu", "trà", "đèn lồng"],
            "kieng_ky": [],
            "kieng_ky_ghi_chu": [],
        },
    },
}


# =============================================================================
# 🛠️ 1. TRA CỨU TÍNH CÁCH
# =============================================================================

def get_personality_profile(person_name: str) -> str:
    """
    Tra cứu hồ sơ tính cách (từ trắc nghiệm tính cách vui) của một người theo tên.

    Args:
        person_name (str): Tên người cần tra cứu (có dấu hoặc không dấu đều được,
            vd 'Minh Anh', 'minh_anh', 'minh anh').

    Returns:
        str: Mô tả nhóm tính cách + sở thích, hoặc chuỗi "LỖI: ..." nếu không
            tìm thấy hồ sơ.
    """
    if not person_name or not str(person_name).strip():
        return "LỖI: Thiếu tên người cần tra cứu tính cách (person_name trống)."

    key = _normalize(person_name)
    profile = PERSONALITY_DB.get(key)
    if not profile:
        return (
            f"LỖI: Không tìm thấy hồ sơ tính cách cho '{person_name}'. "
            "Người này có thể chưa làm trắc nghiệm tính cách trong hệ thống."
        )

    return (
        f"{profile['display_name']} thuộc nhóm tính cách '{profile['personality_type']}'. "
        f"Sở thích nổi bật: {', '.join(profile['so_thich'])}. {profile['mo_ta']}"
    )


# =============================================================================
# 🛠️ 2. TRA CỨU QUY TẮC THEO DỊP LỄ / VĂN HÓA
# =============================================================================

def tra_cuu_quy_tac_dip(dip: str, van_hoa: str = None) -> str:
    """
    Tra cứu điều nên tặng / nên tránh khi tặng quà theo một dịp lễ, có thể lọc
    thêm theo văn hóa/quốc gia của người nhận.

    Args:
        dip (str): Tên dịp lễ, vd 'Tết', 'Giáng Sinh', 'Trung Thu'.
        van_hoa (str, optional): Văn hóa/quốc gia người nhận, vd 'Nhật Bản',
            'Trung Quốc'. Bỏ trống để lấy quy tắc chung.

    Returns:
        str: Danh sách nên tặng/nên tránh, hoặc chuỗi "LỖI: ..." nếu không có
            dữ liệu cho dịp lễ đó.
    """
    if not dip or not str(dip).strip():
        return "LỖI: Thiếu tên dịp lễ cần tra cứu (dip trống)."

    dip_key = _normalize(dip)
    rules = OCCASION_RULES.get(dip_key)
    if not rules:
        return f"LỖI: Không có dữ liệu quy tắc kiêng kỵ cho dịp '{dip}' trong hệ thống."

    van_hoa_key = _normalize(van_hoa) if van_hoa else "chung"
    entry = rules.get(van_hoa_key)
    note = ""
    if not entry:
        entry = rules["chung"]
        if van_hoa:
            note = f" (Chưa có dữ liệu riêng cho văn hóa '{van_hoa}', dùng quy tắc chung.)"

    nen_tang = ", ".join(entry["nen_tang"]) if entry["nen_tang"] else "không có gợi ý cụ thể"
    kieng_ky = "; ".join(entry["kieng_ky_ghi_chu"]) if entry["kieng_ky_ghi_chu"] else "không có điều đặc biệt cần tránh"

    return (
        f"Dịp '{dip}'{f' (văn hóa {van_hoa})' if van_hoa else ''}: "
        f"Nên tặng: {nen_tang}. Nên tránh: {kieng_ky}. "
        f"Các nhãn loại_trừ gợi ý dùng cho search_gift_catalog: {entry['kieng_ky']}.{note}"
    )


# =============================================================================
# 🛠️ 3 & 4. TÌM QUÀ THEO SỞ THÍCH / THEO TÍNH CÁCH
# =============================================================================

def _search_catalog_by_tags(tags: list, budget: float, loai_tru: list) -> str:
    tags_norm = {_normalize(t) for t in tags if str(t).strip()}
    exclude_norm = {_normalize(t) for t in loai_tru if str(t).strip()}

    candidates = []
    for gift_id, item in GIFT_CATALOG.items():
        item_tags = set(item["tags"])
        if item["gia"] > budget:
            continue
        if exclude_norm and item_tags & exclude_norm:
            continue
        if tags_norm and not (item_tags & tags_norm):
            continue
        candidates.append((gift_id, item))

    if not candidates:
        return (
            f"Không tìm thấy quà nào phù hợp trong ngân sách {_format_vnd(budget)} "
            f"với sở thích {sorted(tags_norm) or 'bất kỳ'} (đã loại trừ {sorted(exclude_norm) or 'không có'})."
        )

    candidates.sort(key=lambda pair: pair[1]["gia"], reverse=True)
    lines = [
        f"- {gid}: {it['ten']} - {_format_vnd(it['gia'])}"
        f"{' (còn ' + str(it['ton_kho']) + ' sp)' if it['ton_kho'] > 0 else ' (HẾT HÀNG)'}"
        for gid, it in candidates[:3]
    ]
    return "Gợi ý quà phù hợp:\n" + "\n".join(lines)


def search_gift_catalog(so_thich, budget, loai_tru=None) -> str:
    """
    Tìm quà trong danh mục theo danh sách sở thích cụ thể + ngân sách tối đa.

    Args:
        so_thich (list[str] | str): Một hoặc nhiều sở thích/nhãn quan tâm,
            vd ['sang_tao', 'sach'] hoặc 'outdoor'.
        budget (number): Ngân sách tối đa (VNĐ), phải là số dương.
        loai_tru (list[str] | str, optional): Các nhãn cần loại trừ (vd lấy từ
            kết quả tra_cuu_quy_tac_dip), vd ['dong_ho', 'dao_keo'].

    Returns:
        str: Danh sách tối đa 3 quà phù hợp nhất, hoặc thông báo không tìm thấy
            / "LỖI: ..." nếu ngân sách không hợp lệ.
    """
    try:
        budget_value = _to_number(budget, "budget")
    except ValueError as e:
        return f"LỖI: {e}"
    if budget_value <= 0:
        return f"LỖI: Ngân sách phải là số dương, nhận được {budget}."

    return _search_catalog_by_tags(_as_list(so_thich), budget_value, _as_list(loai_tru))


def suggest_gift_by_personality(personality_type: str, budget, loai_tru=None) -> str:
    """
    Gợi ý nhanh quà dựa trên NHÓM TÍNH CÁCH chung (không cần biết chi tiết sở
    thích), phù hợp khi đã có personality_type từ get_personality_profile hoặc
    do người dùng tự mô tả.

    Args:
        personality_type (str): Tên nhóm tính cách, vd 'Người Sáng Tạo',
            'Người Phiêu Lưu'.
        budget (number): Ngân sách tối đa (VNĐ), phải là số dương.
        loai_tru (list[str] | str, optional): Các nhãn cần loại trừ (thường lấy
            từ tra_cuu_quy_tac_dip khi câu hỏi có nhắc dịp lễ/văn hóa cụ thể).
            QUAN TRỌNG: nếu đã tra_cuu_quy_tac_dip, LUÔN truyền loai_tru vào đây
            — nếu không, tool này có thể gợi ý nhầm quà bị kiêng kỵ (vd đồng hồ)
            vì bản thân nó không tự biết về quy tắc dịp lễ.

    Returns:
        str: Danh sách quà phù hợp, hoặc "LỖI: ..." nếu không nhận diện được
            nhóm tính cách hoặc ngân sách không hợp lệ.
    """
    if not personality_type or not str(personality_type).strip():
        return "LỖI: Thiếu personality_type cần gợi ý quà."

    try:
        budget_value = _to_number(budget, "budget")
    except ValueError as e:
        return f"LỖI: {e}"
    if budget_value <= 0:
        return f"LỖI: Ngân sách phải là số dương, nhận được {budget}."

    key = _normalize(personality_type)
    tags = PERSONALITY_TAG_MAP.get(key)
    if not tags:
        valid = ", ".join(sorted(PERSONALITY_TAG_MAP.keys()))
        return (
            f"LỖI: Không nhận diện được nhóm tính cách '{personality_type}'. "
            f"Các nhóm hợp lệ: {valid}."
        )

    return _search_catalog_by_tags(tags, budget_value, _as_list(loai_tru))


# =============================================================================
# 🛠️ 5. KIỂM TRA TỒN KHO / KHUYẾN MÃI
# =============================================================================

def check_gift_availability(gift_id: str) -> str:
    """
    Kiểm tra tồn kho và khuyến mãi hiện tại của một món quà theo mã.

    Args:
        gift_id (str): Mã quà, vd 'GIFT_004'.

    Returns:
        str: Thông tin tồn kho + khuyến mãi, hoặc "LỖI: ..." nếu mã không tồn tại.
    """
    if not gift_id or not str(gift_id).strip():
        return "LỖI: Thiếu gift_id cần kiểm tra tồn kho."

    key = str(gift_id).strip().upper()
    item = GIFT_CATALOG.get(key)
    if not item:
        return f"LỖI: Mã quà '{gift_id}' không tồn tại trong hệ thống."

    if item["ton_kho"] <= 0:
        return f"{key} - {item['ten']}: HẾT HÀNG, vui lòng chọn quà khác."

    promo = f", đang có khuyến mãi: {item['khuyen_mai']}" if item["khuyen_mai"] else ""
    return (
        f"{key} - {item['ten']}: còn hàng ({item['ton_kho']} sản phẩm), "
        f"giá {_format_vnd(item['gia'])}{promo}."
    )


# =============================================================================
# 🛠️ 6. CHIA NGÂN SÁCH GÓP CHUNG
# =============================================================================

def tinh_ngan_sach_gop(gia_tien, so_nguoi_gop) -> str:
    """
    Chia đều số tiền một món quà cho nhiều người cùng góp mua.

    Args:
        gia_tien (number): Tổng giá tiền món quà (VNĐ), phải là số dương.
        so_nguoi_gop (number): Số người cùng góp tiền, phải là số nguyên >= 1.

    Returns:
        str: Số tiền mỗi người cần góp, hoặc "LỖI: ..." nếu tham số không hợp lệ.
    """
    try:
        gia_tien_value = _to_number(gia_tien, "gia_tien")
    except ValueError as e:
        return f"LỖI: {e}"
    if gia_tien_value <= 0:
        return f"LỖI: gia_tien phải là số dương, nhận được {gia_tien}."

    try:
        so_nguoi_value = _to_number(so_nguoi_gop, "so_nguoi_gop")
    except ValueError as e:
        return f"LỖI: {e}"
    if so_nguoi_value < 1 or int(so_nguoi_value) != so_nguoi_value:
        return f"LỖI: so_nguoi_gop phải là số nguyên >= 1, nhận được {so_nguoi_gop}."

    per_person = gia_tien_value / so_nguoi_value
    return (
        f"Tổng {_format_vnd(gia_tien_value)} chia đều cho {int(so_nguoi_value)} người "
        f"= mỗi người góp {_format_vnd(per_person)}."
    )


# =============================================================================
# 📋 TOOL SPECS (dùng để lắp REACT_SYSTEM_PROMPT trong src/prompts.py)
# =============================================================================

TOOL_SPECS = [
    {
        "name": "get_personality_profile",
        "description": "Tra cứu hồ sơ tính cách (nhóm tính cách + sở thích) của một người theo tên.",
        "input_schema": {
            "type": "object",
            "properties": {
                "person_name": {
                    "type": "string",
                    "description": "Tên người cần tra cứu, vd 'Minh Anh'.",
                },
            },
            "required": ["person_name"],
        },
    },
    {
        "name": "tra_cuu_quy_tac_dip",
        "description": "Tra cứu điều nên tặng/nên tránh khi tặng quà theo một dịp lễ, có thể lọc theo văn hóa người nhận.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dip": {
                    "type": "string",
                    "description": "Tên dịp lễ, vd 'Tết', 'Giáng Sinh'.",
                },
                "van_hoa": {
                    "type": "string",
                    "description": "Văn hóa/quốc gia người nhận, vd 'Nhật Bản'. Bỏ trống nếu không rõ.",
                },
            },
            "required": ["dip"],
        },
    },
    {
        "name": "search_gift_catalog",
        "description": "Tìm quà trong danh mục theo danh sách sở thích cụ thể + ngân sách tối đa, có thể loại trừ một số nhãn kiêng kỵ.",
        "input_schema": {
            "type": "object",
            "properties": {
                "so_thich": {
                    "type": "array",
                    "description": "Danh sách sở thích/nhãn quan tâm, vd ['sang_tao', 'sach'].",
                },
                "budget": {
                    "type": "number",
                    "description": "Ngân sách tối đa (VNĐ), phải là số dương.",
                },
                "loai_tru": {
                    "type": "array",
                    "description": "Danh sách nhãn cần loại trừ (thường lấy từ tra_cuu_quy_tac_dip).",
                },
            },
            "required": ["so_thich", "budget"],
        },
    },
    {
        "name": "suggest_gift_by_personality",
        "description": "Gợi ý nhanh quà theo nhóm tính cách chung + ngân sách, dùng khi chỉ có personality_type mà chưa có danh sách sở thích cụ thể. Nếu trước đó đã gọi tra_cuu_quy_tac_dip, PHẢI truyền kết quả loại trừ vào loai_tru để không gợi ý nhầm quà kiêng kỵ.",
        "input_schema": {
            "type": "object",
            "properties": {
                "personality_type": {
                    "type": "string",
                    "description": "Tên nhóm tính cách, vd 'Người Sáng Tạo'.",
                },
                "budget": {
                    "type": "number",
                    "description": "Ngân sách tối đa (VNĐ), phải là số dương.",
                },
                "loai_tru": {
                    "type": "array",
                    "description": "Danh sách nhãn cần loại trừ (thường lấy từ tra_cuu_quy_tac_dip).",
                },
            },
            "required": ["personality_type", "budget"],
        },
    },
    {
        "name": "check_gift_availability",
        "description": "Kiểm tra tồn kho và khuyến mãi hiện tại của một món quà theo mã quà.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gift_id": {
                    "type": "string",
                    "description": "Mã quà cần kiểm tra, vd 'GIFT_004'.",
                },
            },
            "required": ["gift_id"],
        },
    },
    {
        "name": "tinh_ngan_sach_gop",
        "description": "Chia đều số tiền một món quà cho nhiều người cùng góp mua.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gia_tien": {
                    "type": "number",
                    "description": "Tổng giá tiền món quà (VNĐ), phải là số dương.",
                },
                "so_nguoi_gop": {
                    "type": "number",
                    "description": "Số người cùng góp tiền, số nguyên >= 1.",
                },
            },
            "required": ["gia_tien", "so_nguoi_gop"],
        },
    },
]


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_personality_profile": get_personality_profile,
    "tra_cuu_quy_tac_dip": tra_cuu_quy_tac_dip,
    "search_gift_catalog": search_gift_catalog,
    "suggest_gift_by_personality": suggest_gift_by_personality,
    "check_gift_availability": check_gift_availability,
    "tinh_ngan_sach_gop": tinh_ngan_sach_gop,
}


# =============================================================================
# 🧪 QUICK SELF-TEST (chạy: python src/tools.py)
# =============================================================================

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("🧪 SELF-TEST: tools.py")
    print("=" * 60)

    print("\n[1] get_personality_profile('Minh Anh') (có dấu, có khoảng trắng):")
    print(get_personality_profile("Minh Anh"))

    print("\n[2] get_personality_profile('Người Vô Hình') (không tồn tại):")
    print(get_personality_profile("Người Vô Hình"))

    print("\n[3] tra_cuu_quy_tac_dip('Tết', 'Nhật Bản'):")
    print(tra_cuu_quy_tac_dip("Tết", "Nhật Bản"))

    print("\n[4] tra_cuu_quy_tac_dip('Halloween') (không có dữ liệu):")
    print(tra_cuu_quy_tac_dip("Halloween"))

    print("\n[5] search_gift_catalog(['sang_tao'], 400000):")
    print(search_gift_catalog(["sang_tao"], 400000))

    print("\n[6] search_gift_catalog(['van_phong_pham_cao_cap'], 1500000, ['dong_ho', 'dao_keo']):")
    print(search_gift_catalog(["van_phong_pham_cao_cap", "tra_cafe"], 1500000, ["dong_ho", "dao_keo"]))

    print("\n[7] search_gift_catalog([], -500) (ngân sách âm - bẫy guardrail):")
    print(search_gift_catalog([], -500))

    print("\n[8] check_gift_availability('GIFT_004'):")
    print(check_gift_availability("GIFT_004"))

    print("\n[9] check_gift_availability('GIFT_999') (mã không tồn tại - bẫy guardrail):")
    print(check_gift_availability("GIFT_999"))

    print("\n[10] tinh_ngan_sach_gop(890000, 4):")
    print(tinh_ngan_sach_gop(890000, 4))

    print(f"\n✅ TOOL_SPECS có {len(TOOL_SPECS)} tool, AVAILABLE_TOOLS có {len(AVAILABLE_TOOLS)} tool.")
    assert len(TOOL_SPECS) == len(AVAILABLE_TOOLS)
    assert {spec['name'] for spec in TOOL_SPECS} == set(AVAILABLE_TOOLS.keys())

    print("\n" + "=" * 60)
    print("✅ Tất cả self-test PASS.")
    print("=" * 60)
