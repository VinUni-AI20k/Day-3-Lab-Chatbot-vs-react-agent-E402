"""
Tool registry cho Cupid Agent.

Các tool trong module này chỉ đọc dữ liệu mock, không thay đổi trạng thái và luôn
trả về chuỗi thông báo thay vì ném exception khi người dùng nhập sai tham số.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent.parent / "config" / "mockdata.json"

with DATA_PATH.open("r", encoding="utf-8") as data_file:
    _MOCK_DATA = json.load(data_file)

USER_DATABASE = _MOCK_DATA["USER_DATABASE"]
CANDIDATES_DATABASE = _MOCK_DATA["CANDIDATES_DATABASE"]


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    without_accents = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", without_accents.replace("đ", "d")).strip()


def _find_user(identifier: str) -> dict | None:
    if not isinstance(identifier, str) or not identifier.strip():
        return None

    key = identifier.strip()
    if key in USER_DATABASE:
        return USER_DATABASE[key]

    normalized_key = _normalize(key)
    for profile in USER_DATABASE.values():
        if (
            _normalize(profile.get("student_id", "")) == normalized_key
            or _normalize(profile.get("name", "")) == normalized_key
        ):
            return profile
    return None


def _find_candidate(identifier: str) -> dict | None:
    if not isinstance(identifier, str) or not identifier.strip():
        return None

    normalized_key = _normalize(identifier)
    for candidate in CANDIDATES_DATABASE:
        identifiers = (
            candidate.get("id", ""),
            candidate.get("student_id", ""),
            candidate.get("name", ""),
        )
        if normalized_key in {_normalize(value) for value in identifiers}:
            return candidate
    return None


def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if len(vector_a) != len(vector_b) or not vector_a:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _profile_text(profile: dict) -> str:
    return _normalize(
        " ".join(
            [
                profile.get("name", ""),
                profile.get("gender", ""),
                profile.get("personality", ""),
                profile.get("goal", ""),
                " ".join(profile.get("interests", [])),
            ]
        )
    )


SEARCH_CONCEPTS = {
    "doc sach": ("doc sach", "reading"),
    "ca phe": ("ca phe", "cafe", "coffee"),
    "cong nghe": ("cong nghe", "technology"),
    "nghe thuat": ("nghe thuat", "art"),
    "phim anh": ("phim anh", "film", "movie"),
    "du lich": ("du lich", "travel"),
    "nhac indie": ("nhac indie", "indie"),
    "moi quan he nghiem tuc": ("moi quan he nghiem tuc", "serious"),
    "huong noi": ("huong noi", "introvert"),
    "nam": (" ban nam", "gender=nam", "gender=male"),
    "nu": (" ban nu", "gender=nu", "gender=female"),
    "piano": ("piano",),
    "nau an": ("nau an", "cooking"),
    "dan len": ("dan len", "knitting"),
}


def get_user_profile(user_id: str = "current_user") -> str:
    """
    Truy xuất hồ sơ người dùng đã lưu.

    Purpose:
        Dùng khi Agent cần dữ liệu có căn cứ về người dùng trước khi tư vấn.
    Input:
        user_id là dict-key, tên hoặc MSSV; mặc định là ``current_user``.
    Output:
        Chuỗi tóm tắt hồ sơ và vector đặc trưng.
    Errors:
        Trả chuỗi bắt đầu bằng ``LỖI:`` nếu đầu vào rỗng hoặc không tồn tại.
    Side effects:
        Không có; tool chỉ đọc dữ liệu mock.
    Example:
        ``get_user_profile("2A202601001")`` trả hồ sơ của Minh.
    """
    if not isinstance(user_id, str) or not user_id.strip():
        return "LỖI: user_id phải là chuỗi không rỗng."

    user = _find_user(user_id)
    if user is None:
        return f"LỖI: Không tìm thấy hồ sơ người dùng '{user_id}'."

    return (
        f"Profile người dùng: {user['name']} (MSSV: {user['student_id']}), "
        f"{user['age']} tuổi, {user['gender']}, {user['personality']}; "
        f"sở thích: {', '.join(user['interests'])}; "
        f"mục tiêu: {user['goal']}; ưu tiên: {user['preference']}.\n"
        f"Vector đặc trưng: {user['vector']}"
    )


def search_candidate_profiles(criteria: str) -> str:
    """
    Tìm ứng viên theo sở thích, tính cách, giới tính hoặc mục tiêu hẹn hò.

    Purpose:
        Dùng để lọc sơ bộ ứng viên; không dùng để kết luận độ tương thích.
    Input:
        criteria là câu tự nhiên hoặc chuỗi key/value, ví dụ ``đọc sách`` hoặc
        ``relationship_goal=serious; interests=reading,cafe``.
    Output:
        Danh sách hồ sơ thỏa tất cả tiêu chí nhận diện được, không kèm điểm số.
    Errors:
        Trả chuỗi bắt đầu bằng ``LỖI:`` nếu criteria không phải chuỗi hoặc rỗng.
        Trả thông báo ``Không tìm thấy`` nếu dữ liệu không có kết quả phù hợp.
    Side effects:
        Không có; tool chỉ đọc dữ liệu mock.
    Example:
        ``search_candidate_profiles("đọc sách")`` trả Mai, An và Phương.
    """
    if not isinstance(criteria, str) or not criteria.strip():
        return "LỖI: criteria phải là chuỗi không rỗng."

    normalized_query = f" {_normalize(criteria)} "
    requested_concepts = [
        concept
        for concept, aliases in SEARCH_CONCEPTS.items()
        if any(alias in normalized_query for alias in aliases)
    ]

    matches = []
    for candidate in CANDIDATES_DATABASE:
        searchable_text = f" {_profile_text(candidate)} "
        if requested_concepts:
            is_match = all(concept in searchable_text for concept in requested_concepts)
        else:
            cleaned_query = re.sub(
                r"\b(thich|so thich|muon|tim|nguoi|ban|cung|co|la|ve)\b",
                " ",
                _normalize(criteria),
            )
            cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()
            is_match = bool(cleaned_query) and cleaned_query in searchable_text

        if is_match:
            matches.append(candidate)

    if not matches:
        return f"Không tìm thấy ứng viên nào phù hợp với tiêu chí '{criteria}'."

    lines = [
        f"Tìm thấy {len(matches)} ứng viên phù hợp với tiêu chí '{criteria}':"
    ]
    for candidate in matches:
        lines.append(
            f"- {candidate['name']} (MSSV: {candidate['student_id']}), "
            f"{candidate['age']} tuổi, {candidate['gender']}, "
            f"{candidate['personality']}; sở thích: "
            f"{', '.join(candidate['interests'])}; mục tiêu: {candidate['goal']}."
        )
    return "\n".join(lines)


def calculate_compatibility(
    user_id: str, candidate_names: str | list[str] | tuple[str, ...]
) -> str:
    """
    Tính và xếp hạng độ tương thích bằng cosine similarity.

    Purpose:
        Dùng sau khi đã có hồ sơ người dùng và danh sách ứng viên cần so sánh.
    Input:
        user_id là tên/MSSV/dict-key; candidate_names là một tên, chuỗi tên
        phân tách bằng dấu phẩy, list hoặc tuple tên/MSSV ứng viên.
    Output:
        Điểm trên thang 100, điểm chung và lưu ý cho từng ứng viên theo thứ tự giảm.
    Errors:
        Trả chuỗi bắt đầu bằng ``LỖI:`` khi sai kiểu, thiếu dữ liệu hoặc không tìm
        thấy người dùng/ứng viên; không ném exception nghiệp vụ.
    Side effects:
        Không có; phép tính hoàn toàn xác định từ dữ liệu mock.
    Example:
        ``calculate_compatibility("current_user", ["Mai", "Lan"])``.
    """
    if not isinstance(user_id, str) or not user_id.strip():
        return "LỖI: user_id phải là chuỗi không rỗng."

    user = _find_user(user_id)
    if user is None:
        return f"LỖI: Không tìm thấy hồ sơ người dùng '{user_id}'."

    if isinstance(candidate_names, str):
        names = [name.strip() for name in candidate_names.split(",") if name.strip()]
    elif isinstance(candidate_names, (list, tuple)):
        if not all(isinstance(name, str) for name in candidate_names):
            return "LỖI: Mỗi ứng viên phải được biểu diễn bằng tên hoặc MSSV dạng chuỗi."
        names = [name.strip() for name in candidate_names if name.strip()]
    else:
        return "LỖI: candidate_names phải là chuỗi, list hoặc tuple."

    if not names:
        return "LỖI: Cần cung cấp ít nhất một ứng viên."

    results = []
    missing_names = []
    for name in names:
        candidate = _find_candidate(name)
        if candidate is None:
            missing_names.append(name)
            continue

        score = round(
            _cosine_similarity(user["vector"], candidate["vector"]) * 100
        )
        user_interests = {_normalize(item): item for item in user["interests"]}
        candidate_interests = {
            _normalize(item): item for item in candidate["interests"]
        }
        shared_keys = set(user_interests) & set(candidate_interests)
        shared_interests = [user_interests[key] for key in sorted(shared_keys)]
        same_goal = _normalize(user["goal"]) == _normalize(candidate["goal"])

        strengths = []
        if same_goal:
            strengths.append(f"cùng mục tiêu {user['goal'].lower()}")
        if shared_interests:
            strengths.append(f"cùng thích {', '.join(shared_interests)}")
        strengths_text = (
            "; ".join(strengths)
            if strengths
            else "chưa có điểm chung nổi bật trong dữ liệu"
        )
        note = (
            "nên trò chuyện thêm để kiểm chứng sự phù hợp ngoài dữ liệu"
            if same_goal
            else "khác mục tiêu mối quan hệ, cần trao đổi rõ kỳ vọng"
        )
        results.append((score, candidate["name"], strengths_text, note))

    if not results:
        return (
            "LỖI: Không tìm thấy ứng viên nào trong danh sách: "
            + ", ".join(missing_names)
            + "."
        )

    results.sort(key=lambda item: item[0], reverse=True)
    lines = [f"Độ tương thích của {user['name']} với {len(results)} ứng viên:"]
    for score, name, strengths, note in results:
        lines.append(
            f"- {name}: {score}/100. Điểm mạnh: {strengths}. "
            f"Điểm cần lưu ý: {note}."
        )
    if missing_names:
        lines.append(f"Không tìm thấy hồ sơ: {', '.join(missing_names)}.")
    return "\n".join(lines)


def synthesize_recommendation(user_id: str, top_candidate: str) -> str:
    """
    Chuẩn hóa gói dữ liệu của cặp ghép để LLM viết tư vấn cuối cùng.

    Purpose:
        Dùng sau khi Agent đã chọn được ứng viên đứng đầu.
    Input:
        user_id và top_candidate là tên, MSSV hoặc định danh tương ứng.
    Output:
        Tên hai hồ sơ, điểm cosine và các điểm chung có căn cứ.
    Errors:
        Trả chuỗi bắt đầu bằng ``LỖI:`` nếu thiếu hoặc không tìm thấy hồ sơ.
    Side effects:
        Không có; tool chỉ đọc và tổng hợp dữ liệu mock.
    Example:
        ``synthesize_recommendation("Minh", "Mai")``.
    """
    if not isinstance(user_id, str) or not isinstance(top_candidate, str):
        return "LỖI: user_id và top_candidate phải là chuỗi."

    user = _find_user(user_id)
    candidate = _find_candidate(top_candidate)
    if user is None:
        return f"LỖI: Không tìm thấy hồ sơ người dùng '{user_id}'."
    if candidate is None:
        return f"LỖI: Không tìm thấy hồ sơ ứng viên '{top_candidate}'."

    score = round(_cosine_similarity(user["vector"], candidate["vector"]) * 100)
    compatibility = calculate_compatibility(user_id, candidate["name"])
    return (
        "[GÓI TỔNG HỢP CHO LLM]\n"
        f"- Người dùng: {user['name']}\n"
        f"- Ứng viên: {candidate['name']}\n"
        f"- Điểm vector: {score}/100\n"
        f"- Bằng chứng:\n{compatibility}\n"
        "- Lưu ý: Điểm số chỉ hỗ trợ tham khảo, không thay thế quyết định cá nhân."
    )


AVAILABLE_TOOLS = {
    "get_user_profile": get_user_profile,
    "search_candidate_profiles": search_candidate_profiles,
    "calculate_compatibility": calculate_compatibility,
    "synthesize_recommendation": synthesize_recommendation,
}
