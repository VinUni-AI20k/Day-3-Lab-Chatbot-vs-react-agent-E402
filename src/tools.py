"""
🛠️ TOOL REGISTRY & SCHEMAS
(Dành cho Role 2: Tool & Spec Engineer)

Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

Gift Recommendation Pipeline:

Câu mô tả người dùng
        ↓
1. extract_recipient_profile
        ↓
2. analyze_recipient_profile
        ↓
3. generate_gift_candidates
        ↓
4. explain_recommendations
"""

from typing import Any, Dict, List, Optional


def extract_recipient_profile(
    user_description: str
) -> Dict[str, Any]:
    """
    Trích xuất thông tin người nhận quà từ câu mô tả tự nhiên
    của người dùng và chuyển thành hồ sơ JSON có cấu trúc.

    Tool này chỉ có nhiệm vụ trích xuất thông tin được nhắc đến.
    Không suy luận quá sâu và không đề xuất quà tặng.

    Args:
        user_description (str):
            Câu mô tả về người nhận quà.

            Ví dụ:
            "Bạn gái tôi 22 tuổi, thích chụp ảnh, mèo và những
            món đồ dễ thương. Ngân sách khoảng 1 triệu đồng."

    Returns:
        Dict[str, Any]:
            Hồ sơ người nhận quà có cấu trúc.

            Output schema dự kiến:

            {
                "recipient": {
                    "relationship": "bạn gái",
                    "age": 22,
                    "gender": "nữ"
                },

                "occasion": None,

                "interests": [
                    "chụp ảnh",
                    "mèo",
                    "đồ dễ thương"
                ],

                "personality_traits": [],

                "preferences": {
                    "liked_styles": ["dễ thương"],
                    "disliked_items": [],
                    "favorite_colors": [],
                    "favorite_brands": []
                },

                "constraints": {
                    "budget_min": None,
                    "budget_max": 1000000,
                    "currency": "VND",
                    "location": None,
                    "delivery_deadline": None
                },

                "additional_context": [],

                "missing_information": [
                    "occasion",
                    "delivery_deadline"
                ]
            }
    """
    ...


def analyze_recipient_profile(
    recipient_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Phân tích hồ sơ người nhận để tạo ra các insight phục vụ
    việc lựa chọn quà tặng.

    Tool này nhận hồ sơ có cấu trúc từ extract_recipient_profile
    và suy luận:

    - Phong cách quà phù hợp
    - Ý nghĩa cảm xúc nên ưu tiên
    - Nhóm quà nên cân nhắc
    - Nhóm quà nên tránh
    - Tiêu chí chấm điểm quà
    - Mức độ chắc chắn của từng insight

    Tool này chưa tạo ra sản phẩm quà tặng cụ thể.

    Args:
        recipient_profile (Dict[str, Any]):
            Hồ sơ JSON được tạo bởi extract_recipient_profile.

    Returns:
        Dict[str, Any]:
            Các insight lựa chọn quà.

            Output schema dự kiến:

            {
                "recipient_summary":
                    "Nữ 22 tuổi, thích nhiếp ảnh, mèo và đồ dễ thương.",

                "gift_strategy": {
                    "primary_direction":
                        "Quà mang tính cá nhân hóa và thẩm mỹ",

                    "secondary_direction":
                        "Quà hỗ trợ sở thích chụp ảnh",

                    "emotional_goal":
                        "Thể hiện sự quan tâm và hiểu sở thích"
                },

                "recommended_gift_categories": [
                    {
                        "category": "phụ kiện chụp ảnh",
                        "reason":
                            "Phù hợp với sở thích nhiếp ảnh",
                        "priority": "high"
                    },
                    {
                        "category": "đồ trang trí chủ đề mèo",
                        "reason":
                            "Kết hợp sở thích mèo và phong cách dễ thương",
                        "priority": "high"
                    }
                ],

                "avoid_categories": [
                    {
                        "category": "đồ gia dụng phổ thông",
                        "reason":
                            "Ít liên quan đến sở thích cá nhân"
                    }
                ],

                "ranking_criteria": {
                    "interest_match": 0.30,
                    "personality_match": 0.20,
                    "occasion_match": 0.15,
                    "budget_fit": 0.15,
                    "emotional_value": 0.15,
                    "practicality": 0.05
                },

                "uncertainties": [
                    "Chưa biết dịp tặng quà",
                    "Chưa biết người nhận đã sở hữu thiết bị nhiếp ảnh nào"
                ],

                "confidence_score": 0.85
            }
    """
    ...


def generate_gift_candidates(
    recipient_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
    max_candidates: int = 10
) -> List[Dict[str, Any]]:
    """
    Sinh danh sách quà tặng tiềm năng dựa trên hồ sơ người nhận
    và kết quả phân tích.

    Tool này đồng thời:

    - Tạo các ứng viên quà tặng
    - Chấm điểm từng ứng viên
    - Xếp hạng ứng viên
    - Kiểm tra mức độ phù hợp với ngân sách
    - Gắn các ưu điểm, hạn chế và rủi ro

    Tool này chỉ tạo danh sách ứng viên có cấu trúc.
    Phần giải thích tự nhiên cho người dùng sẽ do
    explain_recommendations đảm nhiệm.

    Args:
        recipient_profile (Dict[str, Any]):
            Hồ sơ người nhận từ extract_recipient_profile.

        profile_analysis (Dict[str, Any]):
            Insight lựa chọn quà từ analyze_recipient_profile.

        max_candidates (int):
            Số lượng ứng viên tối đa cần tạo.

    Returns:
        List[Dict[str, Any]]:
            Danh sách quà tặng đã được chấm điểm và xếp hạng.

            Output schema dự kiến:

            [
                {
                    "candidate_id": "gift_001",

                    "gift_name":
                        "Album ảnh cá nhân hóa chủ đề mèo",

                    "category":
                        "quà cá nhân hóa",

                    "description":
                        "Album ảnh được thiết kế theo phong cách dễ thương.",

                    "estimated_price": {
                        "min": 400000,
                        "max": 700000,
                        "currency": "VND"
                    },

                    "matching_attributes": [
                        "chụp ảnh",
                        "mèo",
                        "đồ dễ thương",
                        "cá nhân hóa"
                    ],

                    "score_breakdown": {
                        "interest_match": 9.5,
                        "personality_match": 9.0,
                        "occasion_match": 7.0,
                        "budget_fit": 9.0,
                        "emotional_value": 9.5,
                        "practicality": 7.5
                    },

                    "total_score": 9.0,

                    "rank": 1,

                    "advantages": [
                        "Mang tính cá nhân hóa cao",
                        "Liên quan trực tiếp đến sở thích chụp ảnh"
                    ],

                    "limitations": [
                        "Cần thời gian chuẩn bị ảnh và thiết kế"
                    ],

                    "risk_flags": [
                        "Có thể không kịp nếu thời gian giao hàng ngắn"
                    ],

                    "confidence_score": 0.91
                }
            ]
    """
    ...


def explain_recommendations(
    recipient_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
    gift_candidates: List[Dict[str, Any]],
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Tạo phần giải thích cuối cùng cho các quà tặng được xếp hạng cao.

    Tool này chuyển dữ liệu có cấu trúc thành nội dung dễ hiểu,
    giúp người dùng biết:

    - Vì sao món quà phù hợp
    - Món quà liên quan thế nào đến người nhận
    - Ưu điểm và hạn chế
    - Món nào phù hợp nhất trong từng trường hợp
    - Thông tin nào cần kiểm tra trước khi mua

    Tool này không thay đổi điểm số hoặc thứ hạng được tạo bởi
    generate_gift_candidates.

    Args:
        recipient_profile (Dict[str, Any]):
            Hồ sơ người nhận quà.

        profile_analysis (Dict[str, Any]):
            Insight lựa chọn quà.

        gift_candidates (List[Dict[str, Any]]):
            Danh sách quà đã được chấm điểm và xếp hạng.

        top_k (int):
            Số lượng quà đứng đầu cần giải thích.

    Returns:
        Dict[str, Any]:
            Kết quả giải thích đề xuất quà tặng.

            Output schema dự kiến:

            {
                "summary":
                    "Các đề xuất ưu tiên quà mang tính cá nhân hóa,
                    liên quan đến nhiếp ảnh và phong cách dễ thương.",

                "recommendations": [
                    {
                        "candidate_id": "gift_001",

                        "rank": 1,

                        "gift_name":
                            "Album ảnh cá nhân hóa chủ đề mèo",

                        "short_reason":
                            "Phù hợp đồng thời với sở thích chụp ảnh,
                            mèo và đồ dễ thương.",

                        "detailed_reason":
                            "Album ảnh thể hiện sự đầu tư về mặt cảm xúc
                            và cho thấy người tặng hiểu sở thích của
                            người nhận.",

                        "best_for":
                            "Khi muốn tặng một món quà tình cảm và
                            có tính kỷ niệm.",

                        "considerations": [
                            "Cần chuẩn bị ảnh trước",
                            "Kiểm tra thời gian sản xuất và giao hàng"
                        ]
                    }
                ],

                "best_overall_candidate_id": "gift_001",

                "alternative_choices": {
                    "most_practical": "gift_002",
                    "most_emotional": "gift_001",
                    "most_budget_friendly": "gift_004"
                },

                "questions_before_purchase": [
                    "Người nhận đã có album ảnh tương tự chưa?",
                    "Món quà cần được giao trước ngày nào?"
                ]
            }
    """
    ...


# Danh sách các tool được đăng ký để ReAct Agent sử dụng
AVAILABLE_TOOLS = {
    "extract_recipient_profile": extract_recipient_profile,
    "analyze_recipient_profile": analyze_recipient_profile,
    "generate_gift_candidates": generate_gift_candidates,
    "explain_recommendations": explain_recommendations,
}