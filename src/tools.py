"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

from datetime import datetime


def _error(message: str) -> str:
    """Chuẩn hóa lỗi nghiệp vụ để Agent nhận Observation thay vì bị crash."""
    return f"LỖI: {message}"


def _required_text(value: object, field_name: str) -> str | None:
    """Kiểm tra một tham số text bắt buộc và trả về giá trị đã chuẩn hóa."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _valid_date(value: str) -> bool:
    """Kiểm tra ngày theo định dạng YYYY-MM-DD và ngày lịch hợp lệ."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _valid_time(value: str) -> bool:
    """Kiểm tra giờ theo định dạng 24 giờ HH:MM."""
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Các tool theo chủ đề trong docs/trace_eval.md: sàng lọc CV và đặt lịch
# phỏng vấn. Dữ liệu mock giúp nhóm test ReAct deterministically, không cần
# API bên ngoài ở Mốc 1.
# ---------------------------------------------------------------------------

_CV_DATABASE = {
    "candidate_001": {
        "name": "Nguyễn Văn An",
        "skills": ["Python", "SQL", "REST API"],
        "experience_years": 3,
    },
    "candidate_002": {
        "name": "Trần Thị Bình",
        "skills": ["Marketing", "Content", "SEO"],
        "experience_years": 2,
    },
}

_JD_DATABASE = {
    "python_backend": {
        "title": "Python Backend Developer",
        "required_skills": ["Python", "SQL", "REST API"],
        "minimum_experience_years": 2,
    },
    "marketing_executive": {
        "title": "Marketing Executive",
        "required_skills": ["Marketing", "Content", "SEO"],
        "minimum_experience_years": 1,
    },
}

_CALENDAR_DATABASE = {
    "interviewer_001": {
        "2026-08-01": ["09:00", "14:00"],
        "2026-08-02": ["10:00", "15:00"],
    },
    "interviewer_002": {
        "2026-08-01": ["10:00", "16:00"],
        "2026-08-02": ["09:00", "13:00"],
    },
}


def parse_cv(candidate_id: str) -> str:
    """Tra cứu và trích xuất thông tin CV của ứng viên.

    Args:
        candidate_id: Mã ứng viên, ví dụ ``"candidate_001"``.

    Returns:
        Chuỗi thông tin CV gồm tên, kỹ năng và số năm kinh nghiệm; nếu mã
        không tồn tại hoặc tham số không hợp lệ thì trả về chuỗi ``LỖI:``.
    Side effects:
        Read-only, không thay đổi dữ liệu.
    """
    candidate_id = _required_text(candidate_id, "candidate_id")
    if candidate_id is None:
        return _error("candidate_id phải là chuỗi không rỗng.")

    candidate = _CV_DATABASE.get(candidate_id.lower())
    if candidate is None:
        return _error(f"Không tìm thấy CV cho ứng viên '{candidate_id}'.")

    skills = ", ".join(candidate["skills"])
    return (
        f"CV {candidate_id}: {candidate['name']}; "
        f"Kỹ năng: {skills}; "
        f"Kinh nghiệm: {candidate['experience_years']} năm."
    )


def get_jd(job_id: str) -> str:
    """Lấy yêu cầu của một vị trí tuyển dụng.

    Args:
        job_id: Mã vị trí, ví dụ ``"python_backend"``.

    Returns:
        Chuỗi mô tả chức danh, kỹ năng bắt buộc và kinh nghiệm tối thiểu.
        Mã không hợp lệ được trả về dưới dạng lỗi, không phát sinh exception.
    Side effects:
        Read-only, không thay đổi dữ liệu.
    """
    job_id = _required_text(job_id, "job_id")
    if job_id is None:
        return _error("job_id phải là chuỗi không rỗng.")

    job = _JD_DATABASE.get(job_id.lower())
    if job is None:
        return _error(f"Không tìm thấy JD cho vị trí '{job_id}'.")

    skills = ", ".join(job["required_skills"])
    return (
        f"JD {job_id}: {job['title']}; "
        f"Kỹ năng bắt buộc: {skills}; "
        f"Kinh nghiệm tối thiểu: {job['minimum_experience_years']} năm."
    )


def score_candidate(candidate_id: str, job_id: str) -> str:
    """Đối sánh CV với JD và chấm điểm mức độ phù hợp.

    Args:
        candidate_id: Mã ứng viên, ví dụ ``"candidate_001"``.
        job_id: Mã vị trí tuyển dụng, ví dụ ``"python_backend"``.

    Returns:
        Báo cáo gồm kỹ năng khớp, kỹ năng còn thiếu, điểm kỹ năng (70 điểm),
        điểm kinh nghiệm (30 điểm), tổng điểm và quyết định ``ĐẠT`` hoặc
        ``KHÔNG ĐẠT``. Mã không tồn tại hoặc tham số sai được trả về dạng
        ``LỖI:`` để Agent xử lý an toàn.
    Side effects:
        Read-only, không sửa CV/JD và không tự động đặt lịch phỏng vấn.
    """
    candidate_id = _required_text(candidate_id, "candidate_id")
    job_id = _required_text(job_id, "job_id")
    if candidate_id is None or job_id is None:
        return _error("candidate_id và job_id phải là chuỗi không rỗng.")

    candidate = _CV_DATABASE.get(candidate_id.lower())
    if candidate is None:
        return _error(f"Không thể chấm điểm: không tìm thấy CV '{candidate_id}'.")

    job = _JD_DATABASE.get(job_id.lower())
    if job is None:
        return _error(f"Không thể chấm điểm: không tìm thấy JD '{job_id}'.")

    candidate_skill_map = {
        skill.casefold(): skill for skill in candidate["skills"]
    }
    required_skill_map = {
        skill.casefold(): skill for skill in job["required_skills"]
    }
    matched_keys = candidate_skill_map.keys() & required_skill_map.keys()
    missing_keys = required_skill_map.keys() - candidate_skill_map.keys()
    matched_skills = sorted(candidate_skill_map[key] for key in matched_keys)
    missing_skills = sorted(required_skill_map[key] for key in missing_keys)

    skill_score = round(70 * len(matched_skills) / len(required_skill_map))
    experience = candidate["experience_years"]
    minimum_experience = job["minimum_experience_years"]
    experience_score = 30 if experience >= minimum_experience else round(
        30 * experience / minimum_experience
    )
    total_score = skill_score + experience_score
    decision = "ĐẠT" if not missing_skills and experience >= minimum_experience else "KHÔNG ĐẠT"

    matched_text = ", ".join(matched_skills) or "Không có"
    missing_text = ", ".join(missing_skills) or "Không có"
    return (
        f"Kết quả chấm điểm {candidate_id} cho JD {job_id}: "
        f"Kỹ năng khớp: {matched_text}; Kỹ năng thiếu: {missing_text}; "
        f"Điểm kỹ năng: {skill_score}/70; Điểm kinh nghiệm: {experience_score}/30; "
        f"Tổng điểm: {total_score}/100; Quyết định: {decision}."
    )


def check_calendar(interviewer_id: str, date: str) -> str:
    """Tra cứu các khung giờ rảnh của người phỏng vấn.

    Args:
        interviewer_id: Mã người phỏng vấn, ví dụ ``"interviewer_001"``.
        date: Ngày cần tra theo định dạng ``YYYY-MM-DD``.

    Returns:
        Danh sách slot rảnh. Nếu không có dữ liệu hoặc tham số sai, trả về
        chuỗi ``LỖI:`` để Agent có thể đề xuất ngày/slot khác.
    Side effects:
        Read-only, không đặt lịch.
    """
    interviewer_id = _required_text(interviewer_id, "interviewer_id")
    date = _required_text(date, "date")
    if interviewer_id is None or date is None:
        return _error("interviewer_id và date phải là chuỗi không rỗng.")
    if not _valid_date(date):
        return _error("date phải là ngày hợp lệ theo định dạng YYYY-MM-DD.")

    slots_by_date = _CALENDAR_DATABASE.get(interviewer_id.lower())
    if slots_by_date is None:
        return _error(f"Không tìm thấy lịch của người phỏng vấn '{interviewer_id}'.")

    slots = slots_by_date.get(date)
    if not slots:
        return _error(f"Không còn slot rảnh cho {interviewer_id} vào ngày {date}.")

    return f"Slot rảnh của {interviewer_id} ngày {date}: {', '.join(slots)}."


def book_interview_slot(
    candidate_id: str,
    interviewer_id: str,
    date: str,
    time: str,
) -> str:
    """Đặt slot phỏng vấn và xác nhận gửi email mời phỏng vấn.

    Args:
        candidate_id: Mã ứng viên đã được ``parse_cv`` xác nhận.
        interviewer_id: Mã người phỏng vấn đã được ``check_calendar`` xác nhận.
        date: Ngày phỏng vấn theo định dạng ``YYYY-MM-DD``.
        time: Giờ phỏng vấn, ví dụ ``"09:00"``.

    Returns:
        Thông báo xác nhận khi slot hợp lệ; nếu ứng viên, người phỏng vấn,
        ngày hoặc giờ không hợp lệ thì trả về ``LỖI:``. Đây là mock side
        effect, chỉ mô phỏng đặt lịch/gửi email và không gọi dịch vụ thật.
    """
    candidate_id = _required_text(candidate_id, "candidate_id")
    interviewer_id = _required_text(interviewer_id, "interviewer_id")
    date = _required_text(date, "date")
    time = _required_text(time, "time")
    if None in (candidate_id, interviewer_id, date, time):
        return _error("candidate_id, interviewer_id, date và time đều bắt buộc.")
    if not _valid_date(date):
        return _error("date phải là ngày hợp lệ theo định dạng YYYY-MM-DD.")
    if not _valid_time(time):
        return _error("time phải là giờ hợp lệ theo định dạng HH:MM.")

    if candidate_id.lower() not in _CV_DATABASE:
        return _error(f"Không thể đặt lịch: không tìm thấy ứng viên '{candidate_id}'.")

    slots_by_date = _CALENDAR_DATABASE.get(interviewer_id.lower())
    if slots_by_date is None:
        return _error(f"Không thể đặt lịch: không tìm thấy người phỏng vấn '{interviewer_id}'.")

    if time not in slots_by_date.get(date, []):
        return _error(f"Slot {date} {time} không còn trống hoặc không tồn tại.")

    return (
        f"Đã đặt lịch phỏng vấn cho {candidate_id} với {interviewer_id} "
        f"vào {date} lúc {time}. Email mời phỏng vấn đã được tạo (mock)."
    )

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "parse_cv": parse_cv,
    "get_jd": get_jd,
    "score_candidate": score_candidate,
    "check_calendar": check_calendar,
    "book_interview_slot": book_interview_slot,
}


# Tool Specification: contract input/output để Role 3 và Role 4 dùng khi
# viết prompt, parser và vòng lặp ReAct.
TOOL_SCHEMAS = {
    "parse_cv": {
        "purpose": "Tra cứu thông tin CV của ứng viên.",
        "input": {"candidate_id": "str, bắt buộc"},
        "output": "str: tên, kỹ năng và số năm kinh nghiệm.",
        "error": "str bắt đầu bằng 'LỖI:' nếu mã ứng viên không tồn tại hoặc input rỗng.",
        "example": {
            "input": {"candidate_id": "candidate_001"},
            "output": "CV candidate_001: Nguyễn Văn An; Kỹ năng: Python, SQL, REST API; Kinh nghiệm: 3 năm.",
        },
    },
    "get_jd": {
        "purpose": "Tra cứu yêu cầu của vị trí tuyển dụng.",
        "input": {"job_id": "str, bắt buộc"},
        "output": "str: chức danh, kỹ năng bắt buộc và kinh nghiệm tối thiểu.",
        "error": "str bắt đầu bằng 'LỖI:' nếu mã JD không tồn tại hoặc input rỗng.",
        "example": {
            "input": {"job_id": "python_backend"},
            "output": "JD python_backend: Python Backend Developer; Kỹ năng bắt buộc: Python, SQL, REST API; Kinh nghiệm tối thiểu: 2 năm.",
        },
    },
    "score_candidate": {
        "purpose": "Đối sánh CV với JD và chấm điểm mức độ phù hợp.",
        "input": {
            "candidate_id": "str, bắt buộc",
            "job_id": "str, bắt buộc",
        },
        "output": "str: kỹ năng khớp/thiếu, điểm kỹ năng /70, điểm kinh nghiệm /30, tổng điểm /100 và quyết định.",
        "error": "str bắt đầu bằng 'LỖI:' nếu CV/JD không tồn tại hoặc input không hợp lệ.",
        "example": {
            "input": {"candidate_id": "candidate_001", "job_id": "python_backend"},
            "output": "Tổng điểm: 100/100; Quyết định: ĐẠT.",
        },
    },
    "check_calendar": {
        "purpose": "Tra cứu slot rảnh của người phỏng vấn.",
        "input": {
            "interviewer_id": "str, bắt buộc",
            "date": "str YYYY-MM-DD, bắt buộc",
        },
        "output": "str: danh sách giờ rảnh trong ngày được yêu cầu.",
        "error": "str bắt đầu bằng 'LỖI:' nếu người phỏng vấn/ngày không có dữ liệu hoặc input rỗng.",
        "example": {
            "input": {"interviewer_id": "interviewer_001", "date": "2026-08-01"},
            "output": "Slot rảnh: 09:00, 14:00.",
        },
    },
    "book_interview_slot": {
        "purpose": "Đặt lịch phỏng vấn và mô phỏng tạo email mời.",
        "input": {
            "candidate_id": "str, bắt buộc",
            "interviewer_id": "str, bắt buộc",
            "date": "str YYYY-MM-DD, bắt buộc",
            "time": "str HH:MM, bắt buộc",
        },
        "output": "str: xác nhận ứng viên, người phỏng vấn, ngày/giờ và email mock đã tạo.",
        "error": "str bắt đầu bằng 'LỖI:' nếu ứng viên/người phỏng vấn/slot không hợp lệ.",
        "example": {
            "input": {
                "candidate_id": "candidate_001",
                "interviewer_id": "interviewer_001",
                "date": "2026-08-01",
                "time": "09:00",
            },
            "output": "Đã đặt lịch phỏng vấn; Email mời phỏng vấn đã được tạo (mock).",
        },
    },
}
