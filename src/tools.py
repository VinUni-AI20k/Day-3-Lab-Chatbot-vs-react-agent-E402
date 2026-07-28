"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo các công cụ hỗ trợ chatbot định hướng sự nghiệp theo mô hình khảo sát.
"""


def _normalize(text: str) -> str:
    """Chuẩn hóa chuỗi đầu vào bằng cách bỏ khoảng trắng thừa và chuyển về chữ thường."""
    return " ".join((text or "").strip().lower().split())


SURVEY = {
    "title": "Khảo sát định hướng nghề nghiệp",
    "questions": [
        {
            "id": 1,
            "question": "Bạn thích làm việc với:",
            "options": ["Con người", "Dữ liệu", "Thiết kế", "Công nghệ kỹ thuật"],
            "profile_key": "interest",
            "profile_values": ["people", "data", "design", "technology"],
        },
        {
            "id": 2,
            "question": "Điểm mạnh của bạn:",
            "options": ["Giao tiếp", "Phân tích", "Sáng tạo", "Kỹ thuật"],
            "profile_key": "strength",
            "profile_values": ["communication", "analysis", "creativity", "technical"],
        },
        {
            "id": 3,
            "question": "Môi trường làm việc yêu thích:",
            "options": ["Chuyên sâu", "Linh hoạt", "Nhiều tương tác"],
            "profile_key": "environment",
            "profile_values": ["focused", "flexible", "interactive"],
        },
        {
            "id": 4,
            "question": "Lĩnh vực muốn học:",
            "options": ["Lập trình", "Phân tích dữ liệu", "Thiết kế sản phẩm", "An toàn thông tin"],
            "profile_key": "learning",
            "profile_values": ["programming", "data_analysis", "product_design", "cybersecurity"],
        },
        {
            "id": 5,
            "question": "Hướng phát triển:",
            "options": ["Chuyên gia kỹ thuật", "Quản lý sản phẩm", "Nhà thiết kế", "Data Analyst"],
            "profile_key": "career_goal",
            "profile_values": ["technical_expert", "product_manager", "designer", "data_analyst"],
        },
    ],
}


def start_career_survey() -> dict:
    """Khởi tạo bộ câu hỏi khảo sát cho người dùng."""
    return {
        "title": SURVEY["title"],
        "questions": [question["question"] for question in SURVEY["questions"]],
    }


def get_question(index: int) -> dict:
    """Lấy thông tin câu hỏi theo chỉ số 1-based."""
    zero_based_index = _to_zero_based_index(index)
    if zero_based_index is None:
        return {"error": f"Invalid question index: {index}"}

    question = SURVEY["questions"][zero_based_index]
    return {
        "index": question["id"],
        "question": question["question"],
        "options": question["options"],
    }


def validate_answer(question_index: int, answer: str) -> dict:
    """Kiểm tra câu trả lời có hợp lệ hay không."""
    zero_based_index = _to_zero_based_index(question_index)
    if zero_based_index is None:
        return {"valid": False, "message": f"Invalid question index: {question_index}"}

    question = SURVEY["questions"][zero_based_index]
    normalized_answer = _normalize(answer)
    valid_options = {_normalize(option) for option in question["options"]}

    if not normalized_answer:
        return {"valid": False, "message": "Answer cannot be empty."}

    if normalized_answer in valid_options:
        return {"valid": True, "normalized_answer": normalized_answer}

    return {
        "valid": False,
        "message": f"Invalid answer. Choose one of: {', '.join(question['options'])}.",
    }


def save_answer(state: dict, question_index: int, answer: str) -> dict:
    """Lưu câu trả lời vào state và trả về state mới."""
    if not isinstance(state, dict):
        state = {}

    answers = dict(state.get("answers") or {})
    zero_based_index = _to_zero_based_index(question_index)
    if zero_based_index is None:
        return {"answers": answers}

    validation = validate_answer(question_index, answer)
    if validation.get("valid"):
        answers[zero_based_index] = validation["normalized_answer"]

    state["answers"] = answers
    return state


def is_survey_completed(state: dict) -> bool:
    """Kiểm tra xem khảo sát đã được trả lời đầy đủ 5 câu hay chưa."""
    if not isinstance(state, dict):
        return False

    answers = state.get("answers") or {}
    if not isinstance(answers, dict):
        return False

    return len(answers) >= len(SURVEY["questions"])


def build_career_profile(state: dict) -> dict:
    """Chuyển kết quả khảo sát thành profile chuẩn hóa không dùng tiếng Việt."""
    if not isinstance(state, dict):
        return {}

    answers = state.get("answers") or {}
    if not isinstance(answers, dict):
        return {}

    profile: dict[str, str] = {}
    for question in SURVEY["questions"]:
        index = question["id"] - 1
        if index in answers:
            option_index = _find_option_index(question["options"], answers[index])
            if option_index is not None:
                profile[question["profile_key"]] = question["profile_values"][option_index]

    return profile


def get_next_question(state: dict) -> dict:
    """Trả về câu hỏi tiếp theo chưa được trả lời."""
    if is_survey_completed(state):
        return {"completed": True}

    answers = (state or {}).get("answers") or {}
    for question in SURVEY["questions"]:
        if question["id"] - 1 not in answers:
            return {
                "index": question["id"],
                "question": question["question"],
                "options": question["options"],
            }

    return {"completed": True}


def reset_survey() -> dict:
    """Reset trạng thái khảo sát về rỗng."""
    return {"answers": {}}


def _to_zero_based_index(index: int) -> int | None:
    """Chuyển đổi chỉ số 1-based thành 0-based."""
    if not isinstance(index, int):
        return None
    if 1 <= index <= len(SURVEY["questions"]):
        return index - 1
    return None


def _find_option_index(options: list[str], answer: str) -> int | None:
    """Tìm chỉ số của một đáp án đã chuẩn hóa."""
    normalized_answer = _normalize(answer)
    for idx, option in enumerate(options):
        if _normalize(option) == normalized_answer:
            return idx
    return None


AVAILABLE_TOOLS = {
    "start_career_survey": start_career_survey,
    "get_question": get_question,
    "validate_answer": validate_answer,
    "save_answer": save_answer,
    "is_survey_completed": is_survey_completed,
    "build_career_profile": build_career_profile,
    "get_next_question": get_next_question,
    "reset_survey": reset_survey,
}
