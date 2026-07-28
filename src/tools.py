"""
🛠️ TOOL REGISTRY, CONTRACTS & SCHEMAS (Dành cho Role 2: Tool Engineer)

Chủ đề hệ thống:
    Trợ lý nắm bắt tính cách, sở thích và chọn quà tặng phù hợp.

Quy trình xử lý (Pipeline 4 bước):
    Câu mô tả người dùng
            ↓
    1. extract_recipient_profile
            ↓
    Hồ sơ người nhận có cấu trúc (recipient_profile)
            ↓
    2. analyze_recipient_profile
            ↓
    Insight và chiến lược chọn quà (profile_analysis)
            ↓
    3. generate_gift_candidates
       Lọc + chấm điểm + xếp hạng + gán rank (ranked_candidates)
            ↓
    4. explain_recommendations
            ↓
    Giải thích kết quả cuối (recommendations)
"""

from __future__ import annotations

from typing import Any

# ==============================================================================
# TYPE ALIASES & STRUCTURES
# ==============================================================================

RecipientProfile = dict[str, Any]
"""Dictionary chứa hồ sơ dữ kiện người nhận quà trích xuất từ Tool 1."""

ProfileAnalysis = dict[str, Any]
"""Dictionary chứa insight phân tích và chiến lược chọn quà từ Tool 2."""

GiftCandidate = dict[str, Any]
"""Dictionary đại diện cho một ứng viên quà tặng đã được chấm điểm từ Tool 3."""

Recommendation = dict[str, Any]
"""Dictionary chứa nội dung giải thích đề xuất quà tặng từ Tool 4."""


# ==============================================================================
# TOOL 1: EXTRACT_RECIPIENT_PROFILE
# ==============================================================================

def extract_recipient_profile(user_description: str) -> dict[str, Any]:
    """
    Trích xuất các dữ kiện thô do người dùng trực tiếp cung cấp trong văn bản mô tả.

    Vai trò trong pipeline:
        Tool 1/4. Công cụ khởi đầu quy trình xử lý.

    Args:
        user_description (str): Chuỗi văn bản tự nhiên mô tả người nhận quà từ người dùng.

    Returns:
        dict[str, Any]: Dữ liệu JSON có cấu trúc gồm:
            - recipient_profile (dict): Chứa các trường traits, interests, preferences,
              exclusions, relationship, occasion, age, budget_vnd.
            - missing_fields (list[str]): Danh sách các trường dữ liệu quan trọng còn thiếu.

    Error semantics:
        Trả về dictionary chứa cấu trúc mặc định cùng danh sách missing_fields đầy đủ
        khi dữ liệu đầu vào rỗng hoặc không hợp lệ, không gây crash chương trình.

    Use when:
        Khi bắt đầu quy trình tư vấn quà tặng và cần chuyển câu văn mô tả thô của người dùng
        thành hồ sơ dữ liệu có cấu trúc.

    Do not use when:
        - Khi cần phân tích tâm lý sâu hoặc chẩn đoán hành vi.
        - Khi cần phỏng đoán các thông tin mà người dùng chưa trực tiếp cung cấp.
        - Khi cần tra cứu danh mục quà tặng hoặc tự gợi ý sản phẩm.

    Side effects:
        Không có (Hàm thuần túy, read-only).

    Safety:
        An toàn tuyệt đối, không thay đổi trạng thái hệ thống, không gọi API ngoài.

    Example:
        >>> profile_data = extract_recipient_profile(
        ...     "Tặng quà sinh nhật cho bạn thân 21t thích đọc sách, trà nhưng không thích mùi hương, ngân sách 800k"
        ... )
        >>> print(profile_data["recipient_profile"]["budget_vnd"])
        800000
    """
    return {
        "recipient_profile": {
            "traits": [],
            "interests": [],
            "preferences": [],
            "exclusions": [],
            "relationship": None,
            "occasion": None,
            "age": None,
            "budget_vnd": None,
        },
        "missing_fields": [],
    }


# ==============================================================================
# TOOL 2: ANALYZE_RECIPIENT_PROFILE
# ==============================================================================

def analyze_recipient_profile(recipient_profile: dict[str, Any]) -> dict[str, Any]:
    """
    Chuyển đổi dữ kiện thô từ recipient_profile thành insight và chiến lược chọn quà.

    Vai trò trong pipeline:
        Tool 2/4. Chỉ được gọi ngay sau khi đã có Observation từ Tool 1 (extract_recipient_profile).

    Args:
        recipient_profile (dict[str, Any]): Dictionary cấu trúc recipient_profile thu được từ Tool 1.

    Returns:
        dict[str, Any]: Dữ liệu JSON chứa profile_analysis gồm:
            - priority_tags (list[str]): Danh sách các tag ưu tiên hàng đầu.
            - preferred_gift_styles (list[str]): Phong cách quà tặng ưu chuộng.
            - avoid_tags (list[str]): Danh sách các tag cần tuyệt đối tránh.
            - gift_goal (str): Mục tiêu tổng quát của món quà.
            - budget_strategy (dict): Chiến lược phân bổ khoảng chi tiêu đề xuất.
            - needs_clarification (bool): Trạng thái cần làm rõ thêm thông tin hay không.
            - clarification_questions (list[str]): Các câu hỏi làm rõ nếu cần thiết.

    Error semantics:
        Trả về profile_analysis chứa cảnh báo hoặc yêu cầu làm rõ nếu recipient_profile
        thiếu các trường quan trọng (như ngân sách hoặc sở thích), không ném exception.

    Use when:
        Khi cần tổng hợp dữ kiện thô từ Tool 1 thành định hướng chiến lược chọn quà, xác định
        khoảng giá hợp lý và tổng hợp danh sách các yếu tố cần tránh.

    Do not use when:
        - Khi chưa có dữ liệu recipient_profile từ Tool 1.
        - Khi muốn sinh danh sách sản phẩm cụ thể hoặc truy cập catalog.
        - Khi muốn kết luận sự thật tâm lý tuyệt đối của người nhận.

    Side effects:
        Không có (Read-only).

    Safety:
        An toàn, không truy cập tài nguyên bên ngoài, kết quả phân tích chỉ mang tính chất
        hỗ trợ ra quyết định cho các bước sau.

    Example:
        >>> analysis = analyze_recipient_profile({"interests": ["đọc sách"], "budget_vnd": 800000})
        >>> print(analysis["profile_analysis"]["gift_goal"])
        "Ưu tiên món quà phản ánh sở thích đọc sách và tạo cảm giác thư giãn."
    """
    return {
        "profile_analysis": {
            "priority_tags": [],
            "preferred_gift_styles": [],
            "avoid_tags": [],
            "gift_goal": "",
            "budget_strategy": {},
            "needs_clarification": False,
            "clarification_questions": [],
        }
    }


# ==============================================================================
# TOOL 3: GENERATE_GIFT_CANDIDATES
# ==============================================================================

def generate_gift_candidates(
    recipient_profile: dict[str, Any],
    profile_analysis: dict[str, Any],
    max_candidates: int = 10,
) -> dict[str, Any]:
    """
    Lọc catalog sản phẩm, áp dụng ngân sách & điều kiện loại trừ, chấm điểm và xếp hạng.

    Vai trò trong pipeline:
        Tool 3/4. Chỉ gọi khi đã có đầy đủ recipient_profile (từ Tool 1) và profile_analysis (từ Tool 2).

    Args:
        recipient_profile (dict[str, Any]): Hồ sơ dữ kiện người nhận từ Tool 1.
        profile_analysis (dict[str, Any]): Phân tích insight và chiến lược từ Tool 2.
        max_candidates (int, optional): Số lượng sản phẩm ứng viên tối đa cần trả về. Mặc định là 10.

    Returns:
        dict[str, Any]: Dữ liệu JSON gồm:
            - ranked_candidates (list[dict]): Danh sách sản phẩm ứng viên đã được gán rank (1, 2, 3...),
              kèm score, score_breakdown, matched_signals, tradeoffs.
            - generation_summary (dict): Báo cáo tóm tắt số lượng sản phẩm đủ điều kiện và lý do loại trừ.

    Error semantics:
        Nếu không có budget_vnd hoặc budget <= 0, hoặc không tìm thấy sản phẩm phù hợp,
        trả về dictionary chứa thông báo lỗi nghiệp vụ rõ ràng, không crash code.

    Use when:
        Khi cần truy vấn catalog quà tặng mẫu, thực hiện lọc cứng theo ngân sách và điều kiện loại trừ,
        tính điểm phù hợp và gán xếp hạng rank cho các sản phẩm ứng viên tốt nhất.

    Do not use when:
        - Khi chưa gọi Tool 1 và Tool 2 để có đầy đủ profile và analysis.
        - Khi muốn tìm kiếm danh mục sản phẩm thời gian thực qua API thương mại điện tử ngoài.
        - Khi định gọi thêm một tool ranking riêng biệt (Tool này đã thực hiện trọn gói việc ranking).

    Side effects:
        Không có (Read-only tra cứu catalog nội bộ).

    Safety:
        Catalog là dữ liệu giả lập nội bộ. Điều kiện loại trừ (exclusions/avoid_tags)
        luôn được ưu tiên cao nhất và thắng điểm sở thích.

    Example:
        >>> result = generate_gift_candidates(profile, analysis, max_candidates=5)
        >>> print(result["ranked_candidates"][0]["rank"])
        1
    """
    return {
        "ranked_candidates": [
            {
                "rank": 1,
                "id": "G001",
                "name": "Bộ sổ ký họa và bút chì cao cấp",
                "price_vnd": 280000,
                "score": 0,
                "score_breakdown": {},
                "matched_signals": [],
                "tradeoffs": [],
            }
        ],
        "generation_summary": {},
    }


# ==============================================================================
# TOOL 4: EXPLAIN_RECOMMENDATIONS
# ==============================================================================

def explain_recommendations(
    recipient_profile: dict[str, Any],
    profile_analysis: dict[str, Any],
    gift_candidates: list[dict[str, Any]],
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Tạo lời giải thích chi tiết và gợi ý cá nhân hóa cho các sản phẩm đã xếp hạng từ Tool 3.

    Vai trò trong pipeline:
        Tool 4/4. Công cụ bước cuối cùng trong quy trình tư vấn quà tặng.

    Args:
        recipient_profile (dict[str, Any]): Hồ sơ dữ kiện người nhận từ Tool 1.
        profile_analysis (dict[str, Any]): Phân tích insight từ Tool 2.
        gift_candidates (list[dict[str, Any]]): Danh sách ứng viên đã xếp hạng từ Tool 3.
        top_k (int, optional): Số lượng đề xuất tối đa cần tạo giải thích. Mặc định là 5.

    Returns:
        dict[str, Any]: Dữ liệu JSON chứa danh sách recommendations gồm:
            - rank (int): Thứ tự xếp hạng (giữ nguyên tuyệt đối từ Tool 3).
            - id (str): Mã sản phẩm.
            - name (str): Tên sản phẩm.
            - price_vnd (int): Giá sản phẩm (không tự sửa đổi).
            - reason (str): Lý do đề xuất thuyết phục dựa trên matched_signals.
            - matched_signals (list[str]): Các tín hiệu phù hợp.
            - personalization_tip (str): Gợi ý tinh tế để tăng tính cá nhân hóa.
            - verify_before_buying (list[str]): Lưu ý kiểm tra trước khi quyết định mua.

    Error semantics:
        Nếu danh sách gift_candidates rỗng hoặc chứa sản phẩm không hợp lệ, trả về
        thông báo lỗi nghiệp vụ dạng JSON, không ném exception.

    Use when:
        Sau khi Tool 3 đã xuất danh sách ứng viên được xếp hạng, cần sinh câu văn giải thích
        lý do lựa chọn, gợi ý thiệp/lời nhắn và các điều khoản kiểm tra trước khi mua.

    Do not use when:
        - Khi muốn thay đổi thứ tự ranking, chấm điểm lại hoặc lọc bớt/thêm sản phẩm mới.
        - Khi muốn bịa thêm ID sản phẩm hoặc điều chỉnh giá niêm yết ngoài catalog.

    Side effects:
        Không có (Read-only).

    Safety:
        Giữ nguyên tuyệt đối thứ tự rank từ Tool 3, đảm bảo tính nhất quán giữa điểm số
        và lời giải thích tư vấn.

    Example:
        >>> recs = explain_recommendations(profile, analysis, candidates, top_k=3)
        >>> print(recs["recommendations"][0]["reason"])
        "Khớp với sở thích đọc sách và phong cách quà thư giãn..."
    """
    return {
        "recommendations": [
            {
                "rank": 1,
                "id": "G001",
                "name": "Bộ sổ ký họa và bút chì cao cấp",
                "price_vnd": 280000,
                "reason": "Khớp với sở thích và phong cách quà tặng.",
                "matched_signals": [],
                "personalization_tip": "Tặng kèm lời nhắn cá nhân.",
                "verify_before_buying": [],
            }
        ]
    }


# ==============================================================================
# TOOL REGISTRY, CONTRACTS & SPECS FOR REACT AGENT
# ==============================================================================

AVAILABLE_TOOLS = {
    "extract_recipient_profile": extract_recipient_profile,
    "analyze_recipient_profile": analyze_recipient_profile,
    "generate_gift_candidates": generate_gift_candidates,
    "explain_recommendations": explain_recommendations,
}

TOOL_CONTRACTS: dict[str, dict[str, Any]] = {
    "extract_recipient_profile": {
        "description": "Trích xuất các dữ kiện trực tiếp được người dùng cung cấp.",
        "input": {"user_description": "str"},
        "output": {"recipient_profile": "dict", "missing_fields": "list"},
    },
    "analyze_recipient_profile": {
        "description": "Chuyển dữ kiện thô thành insight và chiến lược chọn quà.",
        "input": {"recipient_profile": "dict"},
        "output": {"profile_analysis": "dict"},
    },
    "generate_gift_candidates": {
        "description": "Lọc catalog, áp dụng ngân sách/loại trừ, chấm điểm và gán rank.",
        "input": {
            "recipient_profile": "dict",
            "profile_analysis": "dict",
            "max_candidates": "int",
        },
        "output": {"ranked_candidates": "list", "generation_summary": "dict"},
    },
    "explain_recommendations": {
        "description": "Giải thích chi tiết các đề xuất đã được xếp hạng ở tool 3.",
        "input": {
            "recipient_profile": "dict",
            "profile_analysis": "dict",
            "gift_candidates": "list",
            "top_k": "int",
        },
        "output": {"recommendations": "list"},
    },
}

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "extract_recipient_profile",
        "description": (
            "Tool 1/4 trong pipeline. Gọi đầu tiên để trích xuất dữ kiện trực tiếp từ "
            "câu mô tả tự nhiên của người dùng thành hồ sơ JSON cấu trúc (traits, interests, "
            "preferences, exclusions, relationship, occasion, age, budget_vnd). "
            "Tool này không tra catalog, không phỏng đoán thông tin bị thiếu và không tự gợi ý quà."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_description": {
                    "type": "string",
                    "description": "Câu mô tả tự nhiên của người dùng về người nhận quà."
                }
            },
            "required": ["user_description"],
            "additionalProperties": False,
        },
    },
    {
        "name": "analyze_recipient_profile",
        "description": (
            "Tool 2/4 trong pipeline. Chỉ gọi sau khi đã có recipient_profile từ Observation của Tool 1 "
            "(extract_recipient_profile). Phân tích priority_tags, preferred_gift_styles, avoid_tags "
            "và chiến lược ngân sách. Tool này không truy cập catalog và không sinh sản phẩm."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "recipient_profile": {
                    "type": "object",
                    "description": "Hồ sơ JSON recipient_profile thu được từ Observation của Tool 1."
                }
            },
            "required": ["recipient_profile"],
            "additionalProperties": False,
        },
    },
    {
        "name": "generate_gift_candidates",
        "description": (
            "Tool 3/4 trong pipeline. Chỉ gọi khi đã có recipient_profile từ Tool 1 và profile_analysis "
            "từ Observation của Tool 2 (analyze_recipient_profile). Tool này thực hiện trọn gói: "
            "lọc catalog theo ngân sách & loại trừ, chấm điểm, sắp xếp và gán rank trực tiếp. "
            "Không cần gọi thêm bất kỳ tool ranking nào khác."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "recipient_profile": {
                    "type": "object",
                    "description": "Hồ sơ JSON recipient_profile từ Observation của Tool 1."
                },
                "profile_analysis": {
                    "type": "object",
                    "description": "Phân tích profile_analysis từ Observation của Tool 2."
                },
                "max_candidates": {
                    "type": "integer",
                    "description": "Số lượng ứng viên tối đa cần trả về (mặc định 10).",
                    "default": 10,
                },
            },
            "required": ["recipient_profile", "profile_analysis"],
            "additionalProperties": False,
        },
    },
    {
        "name": "explain_recommendations",
        "description": (
            "Tool 4/4 trong pipeline. Chỉ gọi khi đã có danh sách gift_candidates từ Observation "
            "của Tool 3 (generate_gift_candidates). Tool này tạo lý do chi tiết, tip cá nhân hóa và "
            "thông tin cần xác nhận cho từng ứng viên. BẮT BUỘC giữ nguyên thứ tự ranking từ Tool 3; "
            "tuyệt đối không chấm điểm lại, không đổi thứ tự, không thêm hoặc xóa sản phẩm."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "recipient_profile": {
                    "type": "object",
                    "description": "Hồ sơ JSON recipient_profile từ Observation của Tool 1."
                },
                "profile_analysis": {
                    "type": "object",
                    "description": "Phân tích profile_analysis từ Observation của Tool 2."
                },
                "gift_candidates": {
                    "type": "array",
                    "items": {
                        "type": "object"
                    },
                    "description": "Danh sách các ứng viên đã được xếp hạng từ Observation của Tool 3."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Số lượng đề xuất tối đa cần giải thích (mặc định 5).",
                    "default": 5,
                },
            },
            "required": ["recipient_profile", "profile_analysis", "gift_candidates"],
            "additionalProperties": False,
        },
    },
]