"""Tool registry và hợp đồng công cụ cho Gift Recommendation ReAct Agent.

Module này thuộc phạm vi của **Role 2: Tool & Spec Engineer**. Nó định nghĩa
bốn công cụ theo đúng pipeline:

    Câu mô tả người dùng
        → extract_recipient_profile
        → analyze_recipient_profile
        → generate_gift_candidates
        → explain_recommendations

Mỗi công cụ chỉ đảm nhiệm một trách nhiệm chính. Các giá trị trả về phải là
đối tượng Python có thể tuần tự hóa sang JSON để Role 4 đưa vào Observation
của ReAct loop.

Lưu ý:
    Đây là bộ khung Mốc 2 tập trung vào chữ ký hàm, docstring và hợp đồng dữ
    liệu. Phần thân hàm vẫn dùng ``...`` để nhóm triển khai thuật toán sau.
"""

from typing import Any, Callable, Dict, List


RecipientProfile = Dict[str, Any]
ProfileAnalysis = Dict[str, Any]
GiftCandidate = Dict[str, Any]
ToolFunction = Callable[..., Any]


def extract_recipient_profile(user_description: str) -> RecipientProfile:
    """Trích xuất câu mô tả tự do thành hồ sơ người nhận có cấu trúc.

    Đây là tool đầu tiên trong pipeline. Hàm chỉ thu thập những dữ kiện xuất
    hiện trực tiếp trong mô tả của người dùng, chẳng hạn tính cách, sở thích,
    điều cần tránh, mối quan hệ, dịp tặng và ngân sách. Hàm không phân tích
    tâm lý, không suy ra chiến lược chọn quà và không truy cập catalog.

    Args:
        user_description: Câu mô tả người nhận do người dùng cung cấp.
            Chuỗi có thể chứa nhiều thông tin chưa được chuẩn hóa.

    Returns:
        Một dictionary có thể chuyển sang JSON, dự kiến gồm các trường:

        - ``traits``: Danh sách đặc điểm được nhắc trực tiếp.
        - ``interests``: Danh sách sở thích.
        - ``preferences``: Phong cách quà được ưu tiên.
        - ``exclusions``: Điều kiện cần tránh hoặc loại trừ.
        - ``relationship``: Mối quan hệ với người tặng, nếu có.
        - ``occasion``: Dịp tặng quà, nếu có.
        - ``age``: Tuổi người nhận, nếu có.
        - ``budget_vnd``: Ngân sách đã chuẩn hóa sang VND, nếu có.
        - ``missing_fields``: Các thông tin quan trọng còn thiếu.

        Nếu đầu vào không hợp lệ, nên trả về dictionary chứa trường
        ``error`` thay vì làm toàn bộ ứng dụng bị dừng.

    Notes:
        - Không tự bổ sung dữ kiện không có trong câu mô tả.
        - Điều kiện phủ định phải được ưu tiên hơn sở thích cùng loại.
        - Kết quả của hàm là đầu vào cho ``analyze_recipient_profile``.
        - Hàm không có side effect.

    Example:
        >>> profile = extract_recipient_profile(
        ...     "Bạn thân 21 tuổi, thích đọc sách, ngân sách 800.000 VND."
        ... )
        >>> profile["interests"]
        ['đọc sách']
        >>> profile["budget_vnd"]
        800000
    """
    ...


def analyze_recipient_profile(
    recipient_profile: RecipientProfile,
) -> ProfileAnalysis:
    """Phân tích hồ sơ người nhận để tạo insight phục vụ chọn quà.

    Đây là tool thứ hai trong pipeline. Hàm nhận hồ sơ có cấu trúc từ
    ``extract_recipient_profile`` và chuyển các dữ kiện đó thành tiêu chí lựa
    chọn quà, ví dụ tag ưu tiên, phong cách quà phù hợp, điều kiện phải tránh
    và chiến lược sử dụng ngân sách.

    Args:
        recipient_profile: Hồ sơ người nhận đã được chuẩn hóa. Dictionary nên
            chứa các trường như ``traits``, ``interests``, ``preferences``,
            ``exclusions``, ``relationship``, ``occasion``, ``age`` và
            ``budget_vnd``.

    Returns:
        Một dictionary có thể chuyển sang JSON, dự kiến gồm:

        - ``priority_tags``: Tín hiệu quan trọng dùng để chấm điểm quà.
        - ``preferred_gift_styles``: Phong cách quà nên ưu tiên.
        - ``avoid_tags``: Tag sản phẩm phải loại bỏ.
        - ``gift_goal``: Mục tiêu tổng quát của món quà.
        - ``ranking_weights``: Trọng số hoặc nguyên tắc chấm điểm.
        - ``budget_strategy``: Cách sử dụng ngân sách.
        - ``missing_information``: Dữ liệu còn thiếu.
        - ``confidence``: Mức độ tin cậy của insight, nếu hệ thống sử dụng.

        Nếu hồ sơ sai schema, nên trả về dictionary chứa ``error``.

    Notes:
        - Chỉ suy luận từ dữ kiện đã có trong ``recipient_profile``.
        - Không chẩn đoán tâm lý và không khẳng định insight là sự thật tuyệt đối.
        - Không tìm sản phẩm và không tạo candidate ở bước này.
        - Kết quả của hàm là đầu vào cho ``generate_gift_candidates``.
        - Hàm không có side effect.

    Example:
        >>> analysis = analyze_recipient_profile({
        ...     "traits": ["hướng nội"],
        ...     "interests": ["đọc sách", "trà"],
        ...     "preferences": ["ý nghĩa"],
        ...     "exclusions": ["mùi hương"],
        ...     "budget_vnd": 800000,
        ... })
        >>> "đọc sách" in analysis["priority_tags"]
        True
    """
    ...


def generate_gift_candidates(
    recipient_profile: RecipientProfile,
    profile_analysis: ProfileAnalysis,
    max_candidates: int = 10,
) -> Dict[str, Any]:
    """Sinh, chấm điểm và xếp hạng các ứng viên quà tặng.

    Đây là tool thứ ba trong pipeline. Hàm sử dụng hồ sơ người nhận và kết quả
    phân tích để lọc catalog, loại các sản phẩm vi phạm ràng buộc, tính điểm và
    gán ``rank`` ngay trong từng candidate. Không cần một tool ranking riêng.

    Args:
        recipient_profile: Hồ sơ có cấu trúc do
            ``extract_recipient_profile`` tạo ra.
        profile_analysis: Insight chọn quà do
            ``analyze_recipient_profile`` tạo ra.
        max_candidates: Số ứng viên tối đa cần trả về. Giá trị phải là số
            nguyên dương và nên được giới hạn ở mức hợp lý, ví dụ từ 1 đến 20.

    Returns:
        Dictionary có thể chuyển sang JSON với hai trường chính:

        - ``ranked_candidates``: Danh sách candidate đã được sắp xếp từ phù
          hợp nhất đến ít phù hợp hơn. Mỗi candidate dự kiến gồm ``rank``,
          ``id``, ``name``, ``price_vnd``, ``score``, ``score_breakdown``,
          ``matched_signals`` và ``tradeoffs``.
        - ``generation_summary``: Thống kê số sản phẩm trong catalog, số món
          đủ điều kiện, số món bị loại và số candidate được trả về.

        Nếu thiếu ngân sách, input sai schema hoặc không còn ứng viên hợp lệ,
        trả dictionary chứa trường ``error``. Việc luôn trả dictionary giúp
        contract của bốn public tool nhất quán và dễ đưa vào Observation.

    Notes:
        - Exclusion và ``avoid_tags`` luôn thắng điểm sở thích.
        - Chỉ sử dụng sản phẩm có thật trong catalog nội bộ.
        - Kết quả phải deterministic với cùng một input và catalog.
        - Sắp xếp nên có tie-break rõ ràng, ví dụ score giảm dần, giá tăng dần,
          sau đó ID tăng dần.
        - Hàm này chịu trách nhiệm ranking; tool sau không được đổi thứ tự.
        - Hàm không có side effect.

    Example:
        >>> result = generate_gift_candidates(
        ...     recipient_profile={"budget_vnd": 800000},
        ...     profile_analysis={
        ...         "priority_tags": ["đọc sách", "trà"],
        ...         "avoid_tags": ["mùi hương"],
        ...     },
        ...     max_candidates=5,
        ... )
        >>> result["ranked_candidates"][0]["rank"]
        1
    """
    ...


def explain_recommendations(
    recipient_profile: RecipientProfile,
    profile_analysis: ProfileAnalysis,
    gift_candidates: List[GiftCandidate],
    top_k: int = 5,
) -> Dict[str, Any]:
    """Giải thích các ứng viên quà tặng đã được xếp hạng.

    Đây là tool cuối cùng trong pipeline. Hàm tạo lý do dễ hiểu cho các
    candidate do ``generate_gift_candidates`` cung cấp, đồng thời có thể thêm
    lưu ý kiểm tra và gợi ý cá nhân hóa. Hàm không được chấm điểm lại, đổi
    thứ tự hoặc tự thêm sản phẩm mới.

    Args:
        recipient_profile: Hồ sơ người nhận dùng làm căn cứ giải thích.
        profile_analysis: Insight chọn quà dùng để liên kết candidate với nhu
            cầu và ưu tiên của người nhận.
        gift_candidates: Danh sách candidate đã có ``rank`` và ``score`` từ
            ``generate_gift_candidates``. Thứ tự hiện tại phải được giữ nguyên.
        top_k: Số candidate đầu tiên cần giải thích. Giá trị phải là số nguyên
            dương và không vượt quá số candidate hiện có.

    Returns:
        Dictionary có thể chuyển sang JSON, dự kiến gồm:

        - ``recommendations``: Danh sách đề xuất theo đúng thứ tự ranking.
        - ``summary``: Tóm tắt chiến lược chọn quà.
        - ``clarification_needed``: Thông tin cần hỏi thêm, nếu có.
        - ``explanation_note``: Ghi chú rằng ranking đến từ tool thứ ba.

        Mỗi recommendation có thể gồm ``rank``, ``id``, ``name``,
        ``price_vnd``, ``reason``, ``matched_signals``,
        ``personalization_tip`` và ``verify_before_buying``.

        Nếu ``gift_candidates`` rỗng hoặc sai schema, nên trả về dictionary
        chứa ``error`` thay vì phát sinh exception nghiệp vụ.

    Notes:
        - Giữ nguyên ``rank``, ``score`` và thứ tự từ tool thứ ba.
        - Không tự thêm sản phẩm ngoài danh sách input.
        - Lý do phải dựa trên hồ sơ, insight và matched signals có sẵn.
        - Hàm không có side effect.

    Example:
        >>> result = explain_recommendations(
        ...     recipient_profile={"interests": ["đọc sách"]},
        ...     profile_analysis={"priority_tags": ["đọc sách"]},
        ...     gift_candidates=[{
        ...         "rank": 1,
        ...         "id": "G003",
        ...         "name": "Sách theo chủ đề yêu thích",
        ...         "price_vnd": 220000,
        ...         "score": 18,
        ...         "matched_signals": ["đọc sách"],
        ...     }],
        ...     top_k=1,
        ... )
        >>> result["recommendations"][0]["rank"]
        1
    """
    ...


# Registry dùng bởi Role 4 để ánh xạ tên Action sang Python function.
AVAILABLE_TOOLS: Dict[str, ToolFunction] = {
    "extract_recipient_profile": extract_recipient_profile,
    "analyze_recipient_profile": analyze_recipient_profile,
    "generate_gift_candidates": generate_gift_candidates,
    "explain_recommendations": explain_recommendations,
}


# Mô tả ngắn dành cho LLM hoặc Prompt Engineer.
TOOL_DESCRIPTIONS: Dict[str, str] = {
    "extract_recipient_profile": (
        "Tool 1/4: trích xuất dữ kiện trực tiếp từ mô tả tự do thành hồ sơ "
        "người nhận có cấu trúc; không phân tích insight và không gợi ý quà."
    ),
    "analyze_recipient_profile": (
        "Tool 2/4: nhận recipient_profile từ Observation của tool 1 để tạo "
        "priority tags, kiểu quà ưu tiên, avoid tags và chiến lược ngân sách."
    ),
    "generate_gift_candidates": (
        "Tool 3/4: nhận recipient_profile và profile_analysis, lọc catalog, "
        "chấm điểm và gán rank ngay trong từng candidate."
    ),
    "explain_recommendations": (
        "Tool 4/4: giải thích các candidate đã được tool 3 xếp hạng; không "
        "được chấm điểm lại, đổi thứ tự hoặc thêm sản phẩm mới."
    ),
}