"""TOOL REGISTRY & SCHEMAS - CUPID AGENT (Dành cho Role 2: Tool Engineer)
Khai báo các công cụ tra cứu hoàng đạo, MBTI và địa điểm hẹn hò cho Cupid Agent
"""

import unicodedata


VALID_SIGNS = {
    "bach duong": "Bạch Dương",
    "kim nguu": "Kim Ngưu",
    "song tu": "Song Tử",
    "cu giai": "Cự Giải",
    "su tu": "Sư Tử",
    "xu nu": "Xử Nữ",
    "thien binh": "Thiên Bình",
    "bo cap": "Bọ Cạp",
    "than nong": "Bọ Cạp",
    "nhan ma": "Nhân Mã",
    "ma ket": "Ma Kết",
    "bao binh": "Bảo Bình",
    "song ngu": "Song Ngư",
}

VALID_MBTI_TYPES = {
    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP",
}

VALID_VIBES = {"lang man", "soi dong", "nhe nhang", "nghe thuat"}
VALID_BUDGETS = {"tiet kiem", "vua phai", "sang trong"}


def _normalize_text(value: object) -> str | None:
    """Return lower-case Vietnamese text without accents, or None if invalid."""
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = unicodedata.normalize("NFD", value.strip().lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return normalized.replace("đ", "d")


def _invalid_text_error(field: str) -> str:
    return f"LỖI: '{field}' phải là chuỗi không rỗng."


def check_horoscope_compatibility(sign1: str, sign2: str) -> str:
    """Provide a sample compatibility reading for two zodiac signs.

    Args:
        sign1: One of the 12 zodiac signs, e.g. ``'Cự Giải'``.
        sign2: One of the 12 zodiac signs, e.g. ``'Bọ Cạp'``.

    Returns:
        A sample compatibility score and discussion prompt, or a ``LỖI:``
        message when either sign is missing or unsupported.
    """
    normalized_sign1 = _normalize_text(sign1)
    normalized_sign2 = _normalize_text(sign2)
    if normalized_sign1 is None:
        return _invalid_text_error("sign1")
    if normalized_sign2 is None:
        return _invalid_text_error("sign2")
    if normalized_sign1 not in VALID_SIGNS or normalized_sign2 not in VALID_SIGNS:
        return (
            "LỖI: Cung hoàng đạo không hợp lệ. Vui lòng nhập một trong 12 cung "
            "hoàng đạo chuẩn."
        )

    first_sign = VALID_SIGNS[normalized_sign1]
    second_sign = VALID_SIGNS[normalized_sign2]
    pair = frozenset((first_sign, second_sign))
    if pair == frozenset(("Cự Giải", "Bọ Cạp")):
        reading = "95% — cùng hệ Thủy, dễ đồng cảm và gắn kết sâu sắc"
    elif pair == frozenset(("Kim Ngưu", "Xử Nữ")):
        reading = "90% — cùng hệ Đất, thực tế và có thể xây dựng sự tin cậy"
    else:
        reading = "80% — có tiềm năng; nên lắng nghe và trao đổi kỳ vọng rõ ràng"
    return f"💘 Gợi ý tham khảo về {first_sign} & {second_sign}: {reading}."


def calculate_mbti_compatibility(mbti1: str, mbti2: str) -> str:
    """Provide a sample communication-compatibility reading for two MBTI types.

    Args:
        mbti1: One of the 16 valid four-letter MBTI types, e.g. ``'INTJ'``.
        mbti2: One of the 16 valid four-letter MBTI types, e.g. ``'ENFP'``.

    Returns:
        A sample compatibility insight, or a ``LỖI:`` message for invalid input.
    """
    normalized_mbti1 = _normalize_text(mbti1)
    normalized_mbti2 = _normalize_text(mbti2)
    if normalized_mbti1 is None:
        return _invalid_text_error("mbti1")
    if normalized_mbti2 is None:
        return _invalid_text_error("mbti2")

    first_type = normalized_mbti1.upper()
    second_type = normalized_mbti2.upper()
    if first_type not in VALID_MBTI_TYPES or second_type not in VALID_MBTI_TYPES:
        return "LỖI: MBTI không hợp lệ. Vui lòng nhập một trong 16 mã MBTI chuẩn, ví dụ INTJ hoặc ENFP."

    if frozenset((first_type, second_type)) == frozenset(("INTJ", "ENFP")):
        reading = "92% — khác biệt có thể bổ trợ nếu cả hai tôn trọng nhịp giao tiếp"
    else:
        reading = "85% — có thể tạo tiếng nói chung khi chủ động trao đổi nhu cầu"
    return f" Gợi ý tham khảo MBTI {first_type} & {second_type}: {reading}."


def search_date_ideas(location: str, vibe: str, budget: str = "vừa phải") -> str:
    """Suggest deterministic sample date ideas for a supported city.

    Args:
        location: ``'Hà Nội'`` or ``'TP.HCM'`` (common aliases are accepted).
        vibe: One of ``lãng mạn``, ``sôi động``, ``nhẹ nhàng``, ``nghệ thuật``.
        budget: One of ``tiết kiệm``, ``vừa phải``, ``sang trọng``.

    Returns:
        Two sample date ideas, or a ``LỖI:`` message when an argument is invalid.
    """
    normalized_location = _normalize_text(location)
    normalized_vibe = _normalize_text(vibe)
    normalized_budget = _normalize_text(budget)
    if normalized_location is None:
        return _invalid_text_error("location")
    if normalized_vibe is None:
        return _invalid_text_error("vibe")
    if normalized_budget is None:
        return _invalid_text_error("budget")
    if normalized_vibe not in VALID_VIBES:
        return "LỖI: Vibe không hợp lệ. Chọn: lãng mạn, sôi động, nhẹ nhàng hoặc nghệ thuật."
    if normalized_budget not in VALID_BUDGETS:
        return "LỖI: Ngân sách không hợp lệ. Chọn: tiết kiệm, vừa phải hoặc sang trọng."

    if normalized_location in {"ha noi", "hanoi"}:
        return (
            f" Gợi ý mẫu tại Hà Nội (vibe: {vibe.strip()}, ngân sách: {budget.strip()}):\n"
            "1. Cà phê ngắm hoàng hôn Hồ Tây để trò chuyện trong không gian ấm cúng.\n"
            "2. Đi dạo phố cổ và thử ẩm thực đêm để tạo chủ đề trò chuyện tự nhiên."
        )
    if normalized_location in {"ho chi minh", "tp.hcm", "tphcm", "hcm", "sai gon", "saigon"}:
        return (
            f" Gợi ý mẫu tại TP.HCM (vibe: {vibe.strip()}, ngân sách: {budget.strip()}):\n"
            "1. Đi Waterbus Bến Bạch Đằng rồi dùng bữa tối nhẹ.\n"
            "2. Tham gia workshop làm gốm hoặc vẽ tranh cặp đôi để cùng trải nghiệm."
        )
    return "LỖI: Chưa có dữ liệu gợi ý hẹn hò cho địa điểm này. Hỗ trợ: Hà Nội, TP.HCM."


AVAILABLE_TOOLS = {
    "check_horoscope_compatibility": check_horoscope_compatibility,
    "calculate_mbti_compatibility": calculate_mbti_compatibility,
    "search_date_ideas": search_date_ideas,
}
