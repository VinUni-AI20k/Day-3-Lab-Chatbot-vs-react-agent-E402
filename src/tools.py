"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool Engineer)
Tập hợp 4 Tools phục vụ Cupid Agent dựa trên khớp nối Trace Evaluation Logs.
"""

# Cơ sở dữ liệu giả lập (Mock Database & Feature Vectors)
USER_DATABASE = {
    "current_user": {
        "student_id": "2A202601001",
        "name": "Minh",
        "age": 21,
        "gender": "Nam",
        "personality": "Hướng nội, điềm tĩnh",
        "interests": ["đọc sách", "cà phê yên tĩnh", "công nghệ"],
        "goal": "Mối quan hệ nghiêm túc",
        "preference": "Người biết lắng nghe, có mục tiêu rõ ràng",
        # Feature Vector giả lập [Hướng ngoại, Công nghệ, Đọc sách/Chill, Nghiêm túc]
        "vector": [0.2, 0.9, 0.8, 0.95]
    }
}

CANDIDATES_DATABASE = [
    {
        "id": "cand_01",
        "student_id": "2A202601002",
        "name": "Mai",
        "age": 22,
        "gender": "Nữ",
        "personality": "Hướng nội vừa phải, tinh tế",
        "interests": ["đọc sách", "cà phê", "nghệ thuật"],
        "goal": "Mối quan hệ nghiêm túc",
        "vector": [0.3, 0.6, 0.9, 0.9]
    },
    {
        "id": "cand_02",
        "student_id": "2A202601316",
        "name": "Lan",
        "age": 21,
        "gender": "Nữ",
        "personality": "Cởi mở, năng động",
        "interests": ["du lịch", "công nghệ", "cà phê"],
        "goal": "Mối quan hệ nghiêm túc",
        "vector": [0.8, 0.8, 0.4, 0.85]
    },
    {
        "id": "cand_03",
        "student_id": "2A202601004",
        "name": "An",
        "age": 20,
        "gender": "Nữ",
        "personality": "Hòa đồng, cá tính",
        "interests": ["mèo", "nhạc indie", "đọc sách"],
        "goal": "Tìm bạn đồng hành / Tìm hiểu từ từ",
        "vector": [0.6, 0.3, 0.7, 0.6]
    },
    {
        "id": "cand_04",
        "student_id": "2A202601315",
        "name": "Phương",
        "age": 22,
        "gender": "Nam",
        "personality": "Chu đáo, hài hước",
        "interests": ["đọc sách", "cà phê", "phim ảnh"],
        "goal": "Mối quan hệ nghiêm túc",
        "vector": [0.5, 0.5, 0.85, 0.8]
    }
]


def _find_profile(identifier: str) -> dict | None:
    """Tra cứu một hồ sơ (người dùng hoặc ứng viên) theo dict-key ('current_user'),
    mã số sinh viên (student_id) hoặc tên (không phân biệt hoa/thường)."""
    if not identifier:
        return None

    key = identifier.strip()
    if key in USER_DATABASE:
        return USER_DATABASE[key]

    key_lower = key.lower()
    for profile in list(USER_DATABASE.values()) + CANDIDATES_DATABASE:
        if profile.get("student_id") == key or profile.get("name", "").lower() == key_lower:
            return profile
    return None


def get_user_profile(user_id: str = "current_user") -> str:
    """
    [TOOL 1] Truy xuất hồ sơ cá nhân (người dùng hoặc ứng viên) theo dict-key,
    mã số sinh viên (student_id) hoặc tên, và xuất ra tóm tắt thông tin kèm
    Feature Vector đặc trưng.

    Args:
        user_id (str): Dict-key ('current_user'), mã số sinh viên hoặc tên
            (Mặc định: 'current_user')

    Returns:
        str: Tóm tắt thông tin Profile đã lưu + Vector biểu diễn, hoặc thông báo
            không tìm thấy nếu không khớp hồ sơ nào trong cơ sở dữ liệu.
    """
    user = _find_profile(user_id)
    if user is None:
        return f"Không tìm thấy hồ sơ nào khớp với '{user_id}'. Vui lòng kiểm tra lại tên hoặc mã số sinh viên."

    preference_part = f", ưu tiên {user['preference'].lower()}" if "preference" in user else ""
    return (
        f"Profile: {user['name']} (MSSV: {user.get('student_id', 'N/A')}), {user['age']} tuổi, "
        f"{user['personality']}, thích {', '.join(user['interests'])}, "
        f"muốn tìm {user['goal'].lower()}{preference_part}.\n"
        f"[Vector đặc trưng]: {user['vector']}"
    )


def search_candidate_profiles(criteria: str) -> str:
    """
    [TOOL 2] Tìm kiếm hồ sơ ứng viên (Candidate Profiles) trong cơ sở dữ liệu
    dựa trên từ khóa lọc (sở thích, tính cách, mục tiêu hẹn hò). Đây là bước
    lọc sơ bộ, KHÔNG tính điểm tương thích (điểm số được tính riêng bởi
    tool `calculate_compatibility`).

    Args:
        criteria (str): Từ khóa hoặc cụm từ tìm kiếm (Ví dụ: 'thích cà phê', 'đọc sách')

    Returns:
        str: Danh sách tên các ứng viên có hồ sơ khớp với từ khóa, không kèm điểm số
    """
    # Loại bỏ các từ đệm phổ biến để giữ lại từ khóa cốt lõi
    # (VD: "thích cà phê" -> "cà phê")
    STOPWORDS = {"thích", "sở", "muốn", "tìm", "có", "là", "về", "người", "bạn", "cùng"}
    tokens = [w for w in criteria.strip().lower().split() if w not in STOPWORDS]
    keyword = " ".join(tokens) if tokens else criteria.strip().lower()

    if not keyword:
        return "Vui lòng cung cấp từ khóa tìm kiếm (ví dụ: sở thích, tính cách, mục tiêu)."

    matches = []
    for candidate in CANDIDATES_DATABASE:
        searchable_text = " ".join([
            candidate["name"],
            candidate["personality"],
            candidate["goal"],
            " ".join(candidate["interests"]),
        ]).lower()

        if keyword in searchable_text:
            matches.append(candidate)

    if not matches:
        return f"Không tìm thấy ứng viên nào phù hợp với từ khóa '{criteria}'."

    lines = [f"Tìm thấy {len(matches)} ứng viên phù hợp với từ khóa '{criteria}':"]
    for c in matches:
        lines.append(
            f"- {c['name']} ({c['age']} tuổi, {c['gender']}): {c['personality']}, "
            f"thích {', '.join(c['interests'])}, muốn tìm {c['goal'].lower()}."
        )
    return "\n".join(lines)


def _cosine_similarity(vec_a: list, vec_b: list) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def calculate_compatibility(user_id: str, candidate_names) -> str:
    """
    [TOOL 3] Tính độ tương đồng giữa Vector của người dùng với một hoặc nhiều ứng viên
    (Vector Cosine Similarity), xuất ra điểm tương thích thực tế kèm phân tích điểm mạnh/
    điểm cần lưu ý dựa trên sở thích chung, xếp hạng theo điểm giảm dần.

    Args:
        user_id (str): Tên, MSSV hoặc dict-key của người dùng (Ví dụ: 'Minh', 'current_user')
        candidate_names (list[str] | str): Mảng tên/MSSV các ứng viên cần so sánh
            (Ví dụ: ['Mai', 'Lan']), hoặc một tên/MSSV đơn, hoặc chuỗi nhiều tên
            cách nhau bởi dấu phẩy (Ví dụ: 'Mai, Lan')

    Returns:
        str: Điểm tương thích %, điểm mạnh ghép đôi và điểm cần lưu ý cho từng ứng viên
            (xếp hạng cao -> thấp), hoặc thông báo lỗi nếu không tìm thấy hồ sơ.
    """
    user = _find_profile(user_id)
    if user is None:
        return f"Không thể tính độ tương thích: không tìm thấy hồ sơ người dùng '{user_id}'."

    if isinstance(candidate_names, str):
        names = [n.strip() for n in candidate_names.split(",") if n.strip()]
    else:
        names = list(candidate_names)

    if not names:
        return "Vui lòng cung cấp ít nhất một ứng viên để tính độ tương thích."

    results = []
    not_found = []
    for name in names:
        candidate = _find_profile(name)
        if candidate is None:
            not_found.append(name)
            continue

        score = round(_cosine_similarity(user["vector"], candidate["vector"]) * 100)
        shared_interests = sorted(set(user["interests"]) & set(candidate["interests"]))
        same_goal = user["goal"] == candidate["goal"]

        strengths = []
        if same_goal:
            strengths.append(f"cùng mục tiêu {user['goal'].lower()}")
        if shared_interests:
            strengths.append(f"cùng thích {', '.join(shared_interests)}")
        strengths_text = "; ".join(strengths) if strengths else "chưa tìm thấy điểm chung nổi bật"

        notes_text = (
            "khác biệt về mục tiêu mối quan hệ, nên trao đổi rõ kỳ vọng trước"
            if not same_goal else
            "nên chủ động trò chuyện thêm để hiểu tính cách của nhau"
        )

        results.append((score, candidate["name"], strengths_text, notes_text))

    if not results:
        return f"Không thể tính độ tương thích: không tìm thấy ứng viên nào khớp với {', '.join(not_found)}."

    results.sort(key=lambda r: r[0], reverse=True)

    lines = [f"Độ tương thích của {user['name']} với {len(results)} ứng viên:"]
    for score, name, strengths_text, notes_text in results:
        lines.append(
            f"- {name}: {score}/100. Điểm mạnh: {strengths_text}. Điểm cần lưu ý: {notes_text}."
        )
    if not_found:
        lines.append(f"(Không tìm thấy hồ sơ: {', '.join(not_found)})")

    return "\n".join(lines)


def synthesize_recommendation(user_id: str, top_candidate: str) -> str:
    """
    [TOOL 4] Tổng hợp dữ liệu từ 3 tools trên, chuẩn hóa gói thông tin
    để LLM dễ dàng đưa ra câu trả lời tư vấn cuối cùng kèm câu mở đầu Icebreaker.

    Args:
        user_id (str): Tên, MSSV hoặc dict-key của người dùng
        top_candidate (str): Tên hoặc MSSV của ứng viên phù hợp nhất

    Returns:
        str: Gói dữ liệu tổng hợp đã được xác thực cho LLM, hoặc thông báo lỗi
            nếu không tìm thấy hồ sơ người dùng hoặc ứng viên.
    """
    user = _find_profile(user_id)
    candidate = _find_profile(top_candidate)
    if user is None or candidate is None:
        return f"Không thể tổng hợp: không tìm thấy hồ sơ '{user_id}' hoặc '{top_candidate}'."

    score = round(_cosine_similarity(user["vector"], candidate["vector"]) * 100)
    return (
        f"[GÓI TỔNG HỢP HOÀN CHỈNH CHO LLM]:\n"
        f"- Người dùng: {user['name']}\n"
        f"- Ứng viên xuất sắc nhất: {candidate['name']} (Điểm Vector: {score}/100)\n"
        f"- Trạng thái: Đã có đủ dữ liệu để LLM viết Final Answer tư vấn và tạo câu mở đầu Icebreaker."
    )


# EXPORT CHUẨN ĐỂ ROLE 4 (APP.PY) VÀ ROLE 3 (PROMPTS.PY) SỬ DỤNG
AVAILABLE_TOOLS = {
    "get_user_profile": get_user_profile,
    "user_profile": get_user_profile,  # Alias giúp ReAct gọi linh hoạt
    "search_candidate_profiles": search_candidate_profiles,
    "calculate_compatibility": calculate_compatibility,
    "synthesize_recommendation": synthesize_recommendation,
}