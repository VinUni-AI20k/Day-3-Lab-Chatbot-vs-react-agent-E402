"""
🛠️ TOOL REGISTRY & SCHEMAS — Chủ đề: Trợ Lý Tư Vấn Khóa Học Sinh Viên
Dành cho Role 2: Tool & Spec Engineer

Mốc 1 — Danh sách tool đã xác định (stub + docstring đầy đủ):
  1. search_courses          — Tìm khóa học theo từ khóa / ngành học
  2. check_prerequisites     — Kiểm tra điều kiện tiên quyết của môn học
  3. estimate_workload       — Ước tính tổng tín chỉ & mức độ nặng
  4. get_course_detail       — Xem chi tiết một môn học (mô tả, giảng viên, lịch)
  5. check_schedule_conflict — Kiểm tra xung đột lịch học giữa các môn
"""

# =============================================================================
# 📚 DỮ LIỆU MẪU (Mock Data) — Dùng thay thế database thực tế
# =============================================================================

COURSE_DATABASE = {
    "CS101": {
        "name": "Nhập môn Lập trình",
        "credits": 3,
        "difficulty": "Dễ",
        "prerequisites": [],
        "schedule": "Thứ 2 (7:30 - 9:30)",
        "instructor": "TS. Nguyễn Văn An",
        "description": "Giới thiệu tư duy lập trình và ngôn ngữ Python cơ bản.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "CS201": {
        "name": "Cấu trúc Dữ liệu & Giải thuật",
        "credits": 4,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 3 (9:30 - 11:30)",
        "instructor": "PGS. Trần Thị Bình",
        "description": "Stack, Queue, Tree, Graph và các thuật toán sắp xếp, tìm kiếm.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "CS301": {
        "name": "Trí tuệ Nhân tạo",
        "credits": 3,
        "difficulty": "Khó",
        "prerequisites": ["CS201", "MATH201"],
        "schedule": "Thứ 4 (13:30 - 15:30)",
        "instructor": "GS. Lê Quốc Cường",
        "description": "Các thuật toán AI cổ điển, học máy cơ bản và ứng dụng thực tế.",
        "majors": ["AI", "CNTT"],
    },
    "CS302": {
        "name": "Học Máy (Machine Learning)",
        "credits": 4,
        "difficulty": "Khó",
        "prerequisites": ["CS301", "MATH202"],
        "schedule": "Thứ 5 (7:30 - 9:30)",
        "instructor": "TS. Phạm Minh Đức",
        "description": "Supervised, Unsupervised Learning, Neural Networks.",
        "majors": ["AI"],
    },
    "MATH101": {
        "name": "Giải tích 1",
        "credits": 4,
        "difficulty": "Trung bình",
        "prerequisites": [],
        "schedule": "Thứ 2 (13:30 - 15:30)",
        "instructor": "TS. Hoàng Thị Lan",
        "description": "Giới hạn, đạo hàm, tích phân và ứng dụng.",
        "majors": ["CNTT", "KHMT", "AI", "KT"],
    },
    "MATH201": {
        "name": "Đại số Tuyến tính",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["MATH101"],
        "schedule": "Thứ 6 (9:30 - 11:30)",
        "instructor": "PGS. Vũ Thanh Hà",
        "description": "Ma trận, không gian vector, trị riêng, vector riêng.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "MATH202": {
        "name": "Xác suất & Thống kê",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["MATH101"],
        "schedule": "Thứ 3 (13:30 - 15:30)",
        "instructor": "TS. Ngô Thị Mai",
        "description": "Lý thuyết xác suất, phân phối xác suất, kiểm định thống kê.",
        "majors": ["AI", "CNTT", "KT"],
    },
    "SE201": {
        "name": "Kỹ nghệ Phần mềm",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 4 (9:30 - 11:30)",
        "instructor": "TS. Đinh Văn Khoa",
        "description": "Quy trình phát triển phần mềm, UML, Agile, kiểm thử.",
        "majors": ["CNTT", "KHMT"],
    },
    "DB201": {
        "name": "Cơ sở Dữ liệu",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 5 (13:30 - 15:30)",
        "instructor": "TS. Chu Thị Hương",
        "description": "Mô hình quan hệ, SQL, thiết kế và tối ưu cơ sở dữ liệu.",
        "majors": ["CNTT", "KHMT", "AI"],
    },
    "NET201": {
        "name": "Mạng Máy tính",
        "credits": 3,
        "difficulty": "Trung bình",
        "prerequisites": ["CS101"],
        "schedule": "Thứ 6 (13:30 - 15:30)",
        "instructor": "PGS. Bùi Văn Dũng",
        "description": "Mô hình OSI, TCP/IP, các giao thức mạng phổ biến.",
        "majors": ["CNTT", "KHMT"],
    },
}

# Quy định tối đa tín chỉ mỗi học kỳ
MAX_CREDITS_PER_SEMESTER = 24


# =============================================================================
# 🔧 TOOL 1: search_courses
# =============================================================================

def search_courses(keyword: str) -> str:
    """
    Tìm kiếm các khóa học phù hợp theo từ khóa hoặc ngành học.

    Args:
        keyword (str): Từ khóa tìm kiếm — có thể là tên môn, mã môn,
                       tên ngành (Ví dụ: 'AI', 'lập trình', 'CNTT', 'CS101')

    Returns:
        str: Danh sách các môn học phù hợp (mã, tên, tín chỉ, độ khó).
             Trả về chuỗi "LỖI: ..." nếu không tìm thấy kết quả.

    Ví dụ:
        search_courses("AI")       → Danh sách môn thuộc ngành AI
        search_courses("CS101")    → Thông tin môn Nhập môn Lập trình
        search_courses("toán")     → Các môn toán học khả dụng
    """
    if not keyword or not keyword.strip():
        return "LỖI: Từ khóa tìm kiếm không được để trống."

    kw = keyword.lower().strip()
    matched = []

    for course_id, info in COURSE_DATABASE.items():
        # Tìm theo mã môn, tên môn, ngành, hoặc mô tả
        if (
            kw in course_id.lower()
            or kw in info["name"].lower()
            or kw in info["description"].lower()
            or any(kw in major.lower() for major in info["majors"])
        ):
            matched.append(
                f"  • [{course_id}] {info['name']} — {info['credits']} tín chỉ, "
                f"Độ khó: {info['difficulty']}, Ngành: {', '.join(info['majors'])}"
            )

    if not matched:
        return (
            f"LỖI: Không tìm thấy môn học nào khớp với từ khóa '{keyword}'. "
            f"Hãy thử từ khóa khác (Ví dụ: 'AI', 'CNTT', 'toán', 'CS101')."
        )

    result_lines = [f"📚 Kết quả tìm kiếm cho '{keyword}' ({len(matched)} môn):"]
    result_lines.extend(matched)
    return "\n".join(result_lines)


# =============================================================================
# 🔧 TOOL 2: check_prerequisites
# =============================================================================

def check_prerequisites(course_id: str, completed_courses: str) -> str:
    """
    Kiểm tra sinh viên có đủ điều kiện tiên quyết để đăng ký môn học không.

    Args:
        course_id (str): Mã môn học cần kiểm tra (Ví dụ: 'CS301', 'MATH201').
        completed_courses (str): Danh sách mã môn đã học, cách nhau bởi dấu phẩy
                                 (Ví dụ: 'CS101,MATH101,CS201').

    Returns:
        str: Kết quả kiểm tra — ĐỦ điều kiện hoặc THIẾU môn tiên quyết nào.
             Trả về chuỗi "LỖI: ..." nếu mã môn không hợp lệ.

    Ví dụ:
        check_prerequisites("CS301", "CS101,CS201,MATH101,MATH201")
            → "✅ Đủ điều kiện đăng ký CS301"
        check_prerequisites("CS301", "CS101")
            → "❌ Thiếu môn tiên quyết: CS201, MATH201"
    """
    course_id = course_id.strip().upper()

    if course_id not in COURSE_DATABASE:
        return (
            f"LỖI: Mã môn học '{course_id}' không tồn tại trong hệ thống. "
            f"Hãy dùng search_courses để tìm mã môn chính xác."
        )

    required = COURSE_DATABASE[course_id]["prerequisites"]

    if not required:
        return f"✅ Môn [{course_id}] {COURSE_DATABASE[course_id]['name']} không có môn tiên quyết — Có thể đăng ký ngay!"

    # Chuẩn hóa danh sách môn đã học
    if not completed_courses or not completed_courses.strip():
        done = set()
    else:
        done = {c.strip().upper() for c in completed_courses.split(",") if c.strip()}

    missing = [r for r in required if r not in done]

    course_name = COURSE_DATABASE[course_id]["name"]

    if not missing:
        return (
            f"✅ Đủ điều kiện đăng ký [{course_id}] {course_name}!\n"
            f"   Tiên quyết đã hoàn thành: {', '.join(required)}"
        )
    else:
        missing_detail = []
        for m in missing:
            if m in COURSE_DATABASE:
                missing_detail.append(f"{m} ({COURSE_DATABASE[m]['name']})")
            else:
                missing_detail.append(m)
        return (
            f"❌ Chưa đủ điều kiện đăng ký [{course_id}] {course_name}.\n"
            f"   Thiếu môn tiên quyết: {', '.join(missing_detail)}\n"
            f"   Gợi ý: Hãy hoàn thành các môn trên trước khi đăng ký."
        )


# =============================================================================
# 🔧 TOOL 3: estimate_workload
# =============================================================================

def estimate_workload(course_ids: str) -> str:
    """
    Ước tính tổng số tín chỉ và mức độ nặng khi đăng ký một nhóm môn học.

    Args:
        course_ids (str): Danh sách mã môn muốn đăng ký, cách nhau bởi dấu phẩy
                          (Ví dụ: 'CS101,MATH101,SE201').

    Returns:
        str: Tổng tín chỉ, đánh giá mức độ (Nhẹ / Vừa / Nặng / Quá tải),
             và cảnh báo nếu vượt giới hạn.
             Trả về chuỗi "LỖI: ..." nếu danh sách rỗng hoặc mã không hợp lệ.

    Ví dụ:
        estimate_workload("CS101,MATH101")
            → "Tổng: 7 tín chỉ — Mức độ: Nhẹ ✅"
        estimate_workload("CS301,CS302,MATH201,MATH202,DB201")
            → "Tổng: 17 tín chỉ — Mức độ: Nặng ⚠️"
    """
    if not course_ids or not course_ids.strip():
        return "LỖI: Vui lòng cung cấp ít nhất một mã môn học."

    ids = [c.strip().upper() for c in course_ids.split(",") if c.strip()]

    if not ids:
        return "LỖI: Danh sách môn học trống hoặc không hợp lệ."

    total_credits = 0
    hard_count = 0
    valid_courses = []
    invalid_ids = []

    for cid in ids:
        if cid not in COURSE_DATABASE:
            invalid_ids.append(cid)
        else:
            info = COURSE_DATABASE[cid]
            total_credits += info["credits"]
            valid_courses.append(f"  • [{cid}] {info['name']} — {info['credits']} TC, {info['difficulty']}")
            if info["difficulty"] == "Khó":
                hard_count += 1

    lines = ["📊 Ước tính khối lượng học tập:"]
    lines.append(f"Các môn đăng ký ({len(valid_courses)} môn):")
    lines.extend(valid_courses)

    if invalid_ids:
        lines.append(f"\n⚠️  Mã môn không tìm thấy: {', '.join(invalid_ids)} (bỏ qua khi tính).")

    lines.append(f"\nTổng tín chỉ: {total_credits} / {MAX_CREDITS_PER_SEMESTER} TC tối đa.")

    # Đánh giá mức độ
    if total_credits > MAX_CREDITS_PER_SEMESTER:
        level = "🔴 QUÁ TẢI — Vượt giới hạn tín chỉ cho phép!"
        lines.append(f"Mức độ: {level}")
        lines.append(f"💡 Gợi ý: Bỏ bớt {total_credits - MAX_CREDITS_PER_SEMESTER} TC để đảm bảo quy định.")
    elif total_credits >= 18 or hard_count >= 2:
        level = "🟠 Nặng — Cần chuẩn bị kỹ và quản lý thời gian tốt."
        lines.append(f"Mức độ: {level}")
    elif total_credits >= 12:
        level = "🟡 Vừa phải — Phù hợp cho sinh viên có kinh nghiệm."
        lines.append(f"Mức độ: {level}")
    else:
        level = "🟢 Nhẹ — Phù hợp để tập trung học tốt từng môn."
        lines.append(f"Mức độ: {level}")

    return "\n".join(lines)


# =============================================================================
# 🔧 TOOL 4: get_course_detail
# =============================================================================

def get_course_detail(course_id: str) -> str:
    """
    Lấy thông tin chi tiết đầy đủ của một môn học cụ thể.

    Args:
        course_id (str): Mã môn học (Ví dụ: 'CS201', 'MATH101').

    Returns:
        str: Thông tin đầy đủ: tên, mã, tín chỉ, tiên quyết, lịch học,
             giảng viên và mô tả nội dung môn học.
             Trả về chuỗi "LỖI: ..." nếu mã môn không tồn tại.

    Ví dụ:
        get_course_detail("CS301")
            → Toàn bộ thông tin môn Trí tuệ Nhân tạo
    """
    course_id = course_id.strip().upper()

    if course_id not in COURSE_DATABASE:
        return (
            f"LỖI: Mã môn học '{course_id}' không tồn tại. "
            f"Hãy dùng search_courses để tìm mã môn hợp lệ."
        )

    info = COURSE_DATABASE[course_id]
    prereq_str = (
        ", ".join(info["prerequisites"]) if info["prerequisites"] else "Không có"
    )

    return (
        f"📖 Chi tiết môn học:\n"
        f"  Mã môn   : {course_id}\n"
        f"  Tên môn  : {info['name']}\n"
        f"  Tín chỉ  : {info['credits']} TC\n"
        f"  Độ khó   : {info['difficulty']}\n"
        f"  Tiên quyết: {prereq_str}\n"
        f"  Lịch học : {info['schedule']}\n"
        f"  Giảng viên: {info['instructor']}\n"
        f"  Ngành    : {', '.join(info['majors'])}\n"
        f"  Mô tả    : {info['description']}"
    )


# =============================================================================
# 🔧 TOOL 5: check_schedule_conflict
# =============================================================================

def check_schedule_conflict(course_ids: str) -> str:
    """
    Kiểm tra xem các môn học đăng ký có bị trùng lịch học với nhau không.

    Args:
        course_ids (str): Danh sách mã môn muốn kiểm tra, cách nhau bởi dấu phẩy
                          (Ví dụ: 'CS101,MATH101,CS201').

    Returns:
        str: Báo cáo xung đột lịch học (nếu có), hoặc xác nhận lịch hợp lệ.
             Trả về chuỗi "LỖI: ..." nếu danh sách rỗng hoặc mã không hợp lệ.

    Ví dụ:
        check_schedule_conflict("CS101,MATH101")
            → "✅ Không có xung đột lịch học"
        check_schedule_conflict("CS101,MATH101,CS101_REPEAT")
            → "❌ Xung đột: Thứ 2 (7:30–9:30) — CS101 & ..."
    """
    if not course_ids or not course_ids.strip():
        return "LỖI: Vui lòng cung cấp ít nhất một mã môn học."

    ids = [c.strip().upper() for c in course_ids.split(",") if c.strip()]

    schedule_map: dict[str, list[str]] = {}
    invalid_ids = []

    for cid in ids:
        if cid not in COURSE_DATABASE:
            invalid_ids.append(cid)
            continue
        slot = COURSE_DATABASE[cid]["schedule"]
        if slot not in schedule_map:
            schedule_map[slot] = []
        schedule_map[slot].append(cid)

    lines = ["🗓️  Kiểm tra xung đột lịch học:"]

    conflicts = {slot: cids for slot, cids in schedule_map.items() if len(cids) > 1}

    if invalid_ids:
        lines.append(f"⚠️  Mã môn không tìm thấy: {', '.join(invalid_ids)} (bỏ qua).")

    if not conflicts:
        lines.append("✅ Không có xung đột lịch học — Có thể đăng ký tất cả các môn!")
        for slot, cids in sorted(schedule_map.items()):
            cid = cids[0]
            lines.append(f"   {slot}: [{cid}] {COURSE_DATABASE[cid]['name']}")
    else:
        lines.append("❌ Phát hiện xung đột lịch học:")
        for slot, cids in conflicts.items():
            names = " & ".join(
                f"[{c}] {COURSE_DATABASE[c]['name']}" for c in cids
            )
            lines.append(f"   ⛔ {slot} → {names} bị TRÙNG lịch!")
        lines.append("💡 Gợi ý: Hãy chọn lại để tránh trùng lịch.")

    return "\n".join(lines)


# =============================================================================
# 📋 ĐĂNG KÝ TOOL — Agent sẽ tra bảng này để gọi tool
# =============================================================================

AVAILABLE_TOOLS = {
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "estimate_workload": estimate_workload,
    "get_course_detail": get_course_detail,
    "check_schedule_conflict": check_schedule_conflict,
}
