import re
import unicodedata
from typing import Dict, List


def _normalize(text: str) -> str:
    """Chuyen van ban ve dang chu thuong, bo dau, doi d gach ngang thanh d."""
    if not isinstance(text, str):
        return ""
    t = text.lower().replace("đ", "d")
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip()


def _contains(normalized_text: str, phrase: str) -> bool:
    """Kiem tra cum tu co xuat hien trong van ban theo bien tu."""
    p = _normalize(phrase)
    if not p:
        return False
    pattern = r"(?<![0-9a-z])" + re.escape(p) + r"(?![0-9a-z])"
    return re.search(pattern, normalized_text) is not None


TRAIT_LEXICON: Dict[str, List[str]] = {
    "huong_ngoai": ["đông người", "đi tiệc", "tiệc tùng", "bạn bè", "nói chuyện",
                    "sôi nổi", "kết bạn", "thuyết trình", "ồn ào", "rủ rê"],
    "huong_noi": ["một mình", "yên tĩnh", "im lặng", "ở nhà", "ngại giao tiếp",
                  "né tránh", "riêng tư", "trầm tính", "ít nói"],
    "ky_tinh": ["kế hoạch", "danh sách", "gọn gàng", "đúng giờ", "chi tiết",
                "kiểm tra lại", "hoàn hảo", "ngăn nắp", "kỷ luật"],
    "phieu_luu": ["phiêu lưu", "thử điều mới", "sáng tạo", "tưởng tượng",
                  "du lịch", "mạo hiểm", "tự do", "bất ngờ"],
    "dong_cam": ["giúp đỡ", "quan tâm", "lắng nghe", "yêu thương", "chia sẻ",
                 "nhường", "cảm thông"],
    "canh_tranh": ["chiến thắng", "giỏi nhất", "giỏi hơn", "thành tích",
                   "mục tiêu", "vượt qua", "đứng đầu"],
    "nhay_cam": ["lo lắng", "áp lực", "suy nghĩ nhiều", "sợ hãi", "căng thẳng",
                 "bất an", "dễ tổn thương", "mệt mỏi"],
}

OPPOSITE_PAIRS = {
    "huong_ngoai": "huong_noi",
    "huong_noi": "huong_ngoai",
    "ky_tinh": "phieu_luu",
    "phieu_luu": "ky_tinh",
    "dong_cam": "canh_tranh",
    "canh_tranh": "dong_cam",
}

TRAIT_LABELS = {
    "huong_ngoai": "Hướng ngoại",
    "huong_noi": "Hướng nội",
    "ky_tinh": "Kỷ luật - Ngăn nắp",
    "phieu_luu": "Phiêu lưu - Sáng tạo",
    "dong_cam": "Đồng cảm - Vị tha",
    "canh_tranh": "Cạnh tranh - Thành tựu",
    "nhay_cam": "Nhạy cảm cảm xúc",
}

SHADOW_PROFILES = {
    "huong_noi": "Nhu cầu được ở yên và nạp lại năng lượng mà bạn ít nói ra.",
    "huong_ngoai": "Mong muốn được kết nối, được nhìn thấy mà bạn thường giấu đi.",
    "phieu_luu": "Phần muốn phá vỡ khuôn mẫu, thử điều chưa chắc thắng.",
    "ky_tinh": "Phần khao khát trật tự và sự chắc chắn giữa lúc bạn bay bổng.",
    "canh_tranh": "Tham vọng cá nhân mà bạn hay gạt xuống vì ưu tiên người khác.",
    "dong_cam": "Sự mềm mại và nhu cầu được nương tựa sau lớp vỏ mạnh mẽ.",
}

HIGH_RISK_SIGNALS = [
    "tự tử", "muốn chết", "không muốn sống", "kết thúc cuộc sống", "tự hại",
    "tự làm đau", "biến mất khỏi thế giới", "không còn lý do gì",
    "muốn kết thúc tất cả", "kết thúc tất cả", "kết thúc mọi thứ",
    "làm hại người khác", "bị đánh đập", "bị bạo hành", "bị xâm hại",
    "bị lạm dụng", "bị hành hạ",
]

MEDIUM_RISK_SIGNALS = [
    "trầm cảm", "mất ngủ nhiều", "khóc suốt", "vô vọng", "kiệt sức",
    "hoảng loạn", "lo âu nặng", "không thiết ăn", "cô độc hoàn toàn",
    "rối loạn ăn uống", "nghe thấy giọng nói", "vô dụng",
]

PSYCHOLOGY_GLOSSARY = {
    "da nhan cach": (
        "Rối loạn Nhân dạng Phân ly (DID) là một chẩn đoán lâm sàng thật nhưng rất "
        "hiếm, chỉ được xác định bởi bác sĩ tâm thần hoặc nhà tâm lý lâm sàng qua "
        "thăm khám kéo dài. Không một chatbot hay bài test online nào có thể xác "
        "nhận nó. Phim ảnh thường mô tả sai lệch."
    ),
    "did": (
        "Viết tắt của Dissociative Identity Disorder, tức Rối loạn Nhân dạng Phân "
        "ly. Xem thêm mục da nhan cach."
    ),
    "shadow self": (
        "Khái niệm phổ thông gắn với Carl Jung: những phần trong tính cách mà ta ít "
        "thừa nhận hoặc ít thể hiện ra ngoài. Đây là công cụ tự phản tư, không phải "
        "thang đo đã được chuẩn hóa khoa học."
    ),
    "nhan cach thu hai": (
        "Trong ứng dụng này, cụm từ được dùng theo nghĩa shadow self. Cần phân biệt "
        "rõ với Rối loạn Nhân dạng Phân ly. Xem mục shadow self và da nhan cach."
    ),
    "mbti": (
        "Trắc nghiệm phân loại 16 kiểu tính cách, rất phổ biến nhưng bị giới học "
        "thuật phê bình vì độ tin cậy lặp lại thấp và cách phân loại nhị phân. Dùng "
        "để gợi mở trò chuyện thì được, dùng để tuyển dụng hay chẩn đoán thì không."
    ),
    "big five": (
        "Mô hình 5 nhân tố gồm Cởi mở, Tận tâm, Hướng ngoại, Dễ chịu và Bất ổn cảm "
        "xúc, có cơ sở thực nghiệm tốt hơn MBTI. Vẫn là thang đo đặc điểm, không "
        "phải công cụ chẩn đoán bệnh."
    ),
    "tram cam": (
        "Trầm cảm là tình trạng y khoa có thể điều trị, khác với cảm giác buồn thông "
        "thường ở mức độ và thời gian kéo dài. Việc xác định phải do chuyên gia thực "
        "hiện, không tự kết luận qua trò chuyện."
    ),
}

REFLECTION_BANK = {
    "cam_xuc": [
        "Viết ra 3 tình huống tuần này khiến bạn phản ứng mạnh hơn bình thường.",
        "Đặt tên cho cảm xúc bạn đang có, càng cụ thể càng tốt.",
    ],
    "quan_he": [
        "Trong nhóm bạn bè, bạn thường đóng vai người hòa giải, người dẫn dắt hay "
        "người quan sát?",
        "Có điều gì bạn muốn nói với ai đó nhưng chưa nói được?",
    ],
    "muc_tieu": [
        "Nếu không ai đánh giá bạn, bạn sẽ dành cuối tuần để làm gì?",
        "Điều bạn giỏi mà ít người biết là gì?",
    ],
}


def screen_risk_signals(user_text: str) -> str:
    """
    Sang loc dau hieu khung hoang tam ly trong loi nguoi dung.

    Args:
        user_text (str): Toan bo noi dung nguoi dung vua gui.

    Returns:
        str: RISK_LEVEL=HIGH, MEDIUM hoac LOW kem huong xu ly.
    """
    if not user_text or not isinstance(user_text, str):
        return "RISK_LEVEL=LOW | Không có nội dung để sàng lọc."

    norm = _normalize(user_text)

    hits = [s for s in HIGH_RISK_SIGNALS if _contains(norm, s)]
    if hits:
        return (
            "RISK_LEVEL=HIGH\n"
            f"Tín hiệu phát hiện: {', '.join(hits)}\n"
            "HÀNH ĐỘNG BẮT BUỘC: Dừng mọi phân tích tính cách. Không suy đoán, "
            "không chẩn đoán, không tiếp tục trắc nghiệm. Thừa nhận cảm xúc của "
            "người dùng một cách bình tĩnh và gọi ngay "
            "get_support_resources['vietnam']."
        )

    hits = [s for s in MEDIUM_RISK_SIGNALS if _contains(norm, s)]
    if hits:
        return (
            "RISK_LEVEL=MEDIUM\n"
            f"Tín hiệu phát hiện: {', '.join(hits)}\n"
            "HÀNH ĐỘNG: Bỏ giọng điệu giải trí. Ưu tiên lắng nghe, không gán nhãn "
            "bệnh, và nhắc rằng chuyên gia tâm lý là nơi đánh giá chính xác. Có thể "
            "gợi ý get_support_resources."
        )

    return "RISK_LEVEL=LOW | Có thể tiếp tục luồng khám phá tính cách bình thường."


def get_support_resources(region: str = "vietnam") -> str:
    """
    Tra ve kenh ho tro tam ly do con nguoi phu trach.

    Args:
        region (str): Khu vuc nguoi dung. Hien ho tro: vietnam.

    Returns:
        str: Danh sach kenh ho tro, hoac chuoi bat dau bang "LOI:".
    """
    if _normalize(region) not in ("vietnam", "vn", "viet nam"):
        return (
            f"LOI: Chưa có dữ liệu kênh hỗ trợ cho khu vực '{region}'. Hãy khuyên "
            "người dùng liên hệ cơ sở y tế gần nhất hoặc một người thân mà họ tin "
            "tưởng."
        )

    return (
        "KÊNH HỖ TRỢ TẠI VIỆT NAM:\n"
        "1. Cấp cứu y tế: 115, dùng khi có nguy hiểm tức thời đến tính mạng.\n"
        "2. Tổng đài Quốc gia Bảo vệ Trẻ em: 111, miễn phí, hoạt động 24/7, dành "
        "cho người dưới 18 tuổi hoặc trường hợp bị bạo hành, xâm hại.\n"
        "3. Phòng tư vấn tâm lý của trường, hoặc bệnh viện có khoa Tâm thần - Tâm "
        "lý gần nơi ở.\n"
        "4. Một người thân hoặc bạn bè mà người dùng tin tưởng.\n"
        "CÁCH TRUYỀN ĐẠT: nói ngắn, không phán xét, không hứa bảo mật tuyệt đối, "
        "không mô tả phương thức gây hại."
    )


def analyze_personality_signals(user_text: str) -> str:
    """
    Phan tich doan nguoi dung tu mo ta de rut ra cac tin hieu tinh cach.

    Ket qua chi la thong ke tu khoa, khong phai bai test chuan hoa va khong phai
    chan doan.

    Args:
        user_text (str): Doan nguoi dung tu ke ve ban than, thoi quen, cam xuc.

    Returns:
        str: Danh sach tin hieu kem dong TRAIT_TROI_NHAT, hoac chuoi bat dau
             bang "LOI:".
    """
    if not user_text or not isinstance(user_text, str):
        return "LOI: Thiếu dữ liệu mô tả. Hãy hỏi người dùng tự kể về bản thân trước."

    norm = _normalize(user_text)
    if len(norm) < 15:
        return (
            "LOI: Mô tả quá ngắn, cần ít nhất 15 ký tự. Hãy hỏi thêm về thói quen "
            "hoặc cảm xúc gần đây của người dùng."
        )

    scores = {}
    for trait, keywords in TRAIT_LEXICON.items():
        hit = sum(1 for kw in keywords if _contains(norm, kw))
        if hit:
            scores[trait] = hit

    if not scores:
        return (
            "KHÔNG RÕ TÍN HIỆU: Chưa nhận ra từ khóa tính cách nào trong mô tả. Hãy "
            "hỏi một câu cụ thể hơn, ví dụ cuối tuần bạn thường làm gì một mình."
        )

    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    lines = [f"- {TRAIT_LABELS[t]}: {n} tín hiệu" for t, n in ranked]
    return (
        "KẾT QUẢ QUÉT TÍN HIỆU, không phải chẩn đoán:\n"
        + "\n".join(lines)
        + f"\nTRAIT_TROI_NHAT = {ranked[0][0]}"
    )


def get_shadow_profile(dominant_trait: str) -> str:
    """
    Tra cuu mat tinh cach it boc lo tuong ung voi net troi.

    Args:
        dominant_trait (str): Ma net troi lay tu analyze_personality_signals. Hop
            le: huong_ngoai, huong_noi, ky_tinh, phieu_luu, dong_cam, canh_tranh.

    Returns:
        str: Mo ta mat it boc lo kem cau hoi phan tu, hoac chuoi bat dau bang
             "LOI:".
    """
    key = _normalize(dominant_trait).replace(" ", "_")

    if key == "nhay_cam":
        return (
            "LOI: Mã nhay_cam là tín hiệu cảm xúc, không dùng để suy ra mặt ít bộc "
            "lộ. Hãy dùng screen_risk_signals hoặc "
            "suggest_reflection_exercise['cam_xuc']."
        )

    if key not in OPPOSITE_PAIRS:
        return (
            f"LOI: Mã nét tính cách '{dominant_trait}' không hợp lệ. Chỉ nhận: "
            f"{', '.join(OPPOSITE_PAIRS.keys())}."
        )

    shadow = OPPOSITE_PAIRS[key]
    return (
        f"MẶT ÍT BỘC LỘ: {TRAIT_LABELS[shadow]}\n"
        f"Diễn giải: {SHADOW_PROFILES[shadow]}\n"
        "Câu hỏi phản tư: Lần gần nhất bạn để mặt này xuất hiện là khi nào?\n"
        "LƯU Ý KHI TRẢ LỜI: đây là gợi ý tự khám phá, không phải kết luận tâm lý học."
    )


def lookup_psychology_concept(term: str) -> str:
    """
    Tra cuu dinh nghia mot khai niem tam ly pho thong.

    Agent phai lay dinh nghia tu day thay vi tu sinh ra noi dung.

    Args:
        term (str): Ten khai niem, co dau hay khong dau deu duoc. Ho tro: da nhan
            cach, did, shadow self, nhan cach thu hai, mbti, big five, tram cam.

    Returns:
        str: Dinh nghia, hoac chuoi bat dau bang "LOI:" kem danh sach khai niem
             co san.
    """
    if not term or not isinstance(term, str):
        return "LOI: Chưa truyền tên khái niệm cần tra cứu."

    key = _normalize(term)
    if key in PSYCHOLOGY_GLOSSARY:
        return f"ĐỊNH NGHĨA ({key}): {PSYCHOLOGY_GLOSSARY[key]}"

    for name, definition in PSYCHOLOGY_GLOSSARY.items():
        if name in key or key in name:
            return f"ĐỊNH NGHĨA ({name}): {definition}"

    return (
        f"LOI: Không có dữ liệu cho khái niệm '{term}'. Các khái niệm có sẵn: "
        f"{', '.join(PSYCHOLOGY_GLOSSARY.keys())}. Không được tự tạo định nghĩa mới."
    )


def suggest_reflection_exercise(theme: str) -> str:
    """
    Goi y bai tap viet phan tu nhe nhang.

    Args:
        theme (str): Chu de. Ho tro: cam_xuc, quan_he, muc_tieu.

    Returns:
        str: Cac cau hoi phan tu, hoac chuoi bat dau bang "LOI:".
    """
    key = _normalize(theme).replace(" ", "_")
    if key not in REFLECTION_BANK:
        return (
            f"LOI: Chủ đề '{theme}' không có. Chọn một trong: "
            f"{', '.join(REFLECTION_BANK.keys())}."
        )
    return "BÀI TẬP PHẢN TƯ:\n" + "\n".join(f"- {i}" for i in REFLECTION_BANK[key])


AVAILABLE_TOOLS = {
    "screen_risk_signals": screen_risk_signals,
    "analyze_personality_signals": analyze_personality_signals,
    "get_shadow_profile": get_shadow_profile,
    "lookup_psychology_concept": lookup_psychology_concept,
    "suggest_reflection_exercise": suggest_reflection_exercise,
    "get_support_resources": get_support_resources,
}

TOOL_SPECS = [
    ("screen_risk_signals[user_text]",
     "Bat buoc goi dau tien. Sang loc dau hieu khung hoang tam ly."),
    ("analyze_personality_signals[user_text]",
     "Rut tin hieu tinh cach tu doan nguoi dung tu mo ta."),
    ("get_shadow_profile[dominant_trait]",
     "Suy ra mat tinh cach it boc lo tu ma net troi."),
    ("lookup_psychology_concept[term]",
     "Tra dinh nghia khai niem tam ly tu tu dien co san."),
    ("suggest_reflection_exercise[theme]",
     "Goi y bai tap phan tu: cam_xuc, quan_he hoac muc_tieu."),
    ("get_support_resources[region]",
     "Tra ve kenh ho tro do nguoi that phu trach. Dung khi RISK_LEVEL=HIGH."),
]

TOOL_SPECS_TEXT = "\n".join(
    f"{i}. {sig}: {desc}" for i, (sig, desc) in enumerate(TOOL_SPECS, 1)
)
