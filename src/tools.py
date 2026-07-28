"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

Chủ đề: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn
"""

# ============================================================
# 📦 MOCK DATA (Giả lập cơ sở dữ liệu tuyển dụng)
# ============================================================

# Hồ sơ ứng viên: kỹ năng & số năm kinh nghiệm
CANDIDATES_DB = {
    "nguyễn văn a": {"skills": ["python", "sql", "machine learning"], "experience_years": 3},
    "trần thị b": {"skills": ["java", "spring boot", "docker"], "experience_years": 5},
    "lê văn c": {"skills": ["react", "javascript", "css"], "experience_years": 1},
}

# Yêu cầu kỹ năng theo vị trí tuyển dụng
POSITIONS_DB = {
    "data engineer": {"required_skills": ["python", "sql"], "min_experience": 2},
    "backend developer": {"required_skills": ["java", "spring boot"], "min_experience": 3},
    "frontend developer": {"required_skills": ["react", "javascript"], "min_experience": 2},
}

# Lịch bận của người phỏng vấn: {tên: {ngày: [khung giờ đã bận]}}
INTERVIEWER_CALENDAR = {
    "chị hương (hr)": {"2026-08-01": ["09:00", "14:00"], "2026-08-02": ["10:00"]},
    "anh minh (tech lead)": {"2026-08-01": ["10:00", "11:00", "15:00"]},
}

# Lịch phỏng vấn đã đặt thành công (được cập nhật khi gọi schedule_interview)
BOOKED_INTERVIEWS = []


# ============================================================
# 🛠️ TOOLS
# ============================================================

def screen_resume(candidate_name: str, position: str) -> str:
    """
    Sàng lọc & chấm điểm mức độ phù hợp giữa hồ sơ ứng viên và vị trí tuyển dụng.

    Args:
        candidate_name (str): Tên ứng viên (Ví dụ: 'Nguyễn Văn A')
        position (str): Tên vị trí tuyển dụng (Ví dụ: 'Data Engineer')

    Returns:
        str: Kết quả sàng lọc gồm điểm phù hợp (%), kỹ năng khớp/thiếu và kết luận Đạt/Không đạt.
             Trả về chuỗi LỖI nếu không tìm thấy ứng viên hoặc vị trí trong hệ thống.
    """
    candidate = CANDIDATES_DB.get(candidate_name.strip().lower())
    if candidate is None:
        return f"LỖI: Không tìm thấy hồ sơ ứng viên '{candidate_name}' trong hệ thống."

    role = POSITIONS_DB.get(position.strip().lower())
    if role is None:
        return f"LỖI: Không tìm thấy vị trí tuyển dụng '{position}' trong danh sách đang mở."

    matched_skills = set(candidate["skills"]) & set(role["required_skills"])
    missing_skills = set(role["required_skills"]) - set(candidate["skills"])
    skill_score = len(matched_skills) / len(role["required_skills"]) * 100
    exp_ok = candidate["experience_years"] >= role["min_experience"]

    verdict = "ĐẠT ✅" if skill_score >= 50 and exp_ok else "KHÔNG ĐẠT ❌"

    return (
        f"Sàng lọc '{candidate_name}' cho vị trí '{position}':\n"
        f"- Độ khớp kỹ năng: {skill_score:.0f}% (Khớp: {sorted(matched_skills) or 'Không có'}, "
        f"Thiếu: {sorted(missing_skills) or 'Không'})\n"
        f"- Kinh nghiệm: {candidate['experience_years']} năm "
        f"(Yêu cầu tối thiểu: {role['min_experience']} năm)\n"
        f"- Kết luận: {verdict}"
    )


def check_interviewer_availability(interviewer: str, date: str) -> str:
    """
    Tra cứu các khung giờ còn trống của người phỏng vấn trong một ngày cụ thể.

    Args:
        interviewer (str): Tên người phỏng vấn (Ví dụ: 'Chị Hương (HR)')
        date (str): Ngày cần kiểm tra, định dạng YYYY-MM-DD (Ví dụ: '2026-08-01')

    Returns:
        str: Danh sách khung giờ trống trong ngày làm việc (09:00 - 17:00, mỗi slot 1 tiếng).
             Trả về chuỗi LỖI nếu không tìm thấy người phỏng vấn hoặc ngày không hợp lệ.
    """
    key = interviewer.strip().lower()
    if key not in INTERVIEWER_CALENDAR:
        return f"LỖI: Không tìm thấy người phỏng vấn '{interviewer}' trong hệ thống."

    try:
        import datetime
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return f"LỖI: Ngày '{date}' không hợp lệ. Vui lòng dùng định dạng YYYY-MM-DD."

    work_hours = [f"{h:02d}:00" for h in range(9, 17)]
    busy_slots = INTERVIEWER_CALENDAR[key].get(date, [])
    free_slots = [slot for slot in work_hours if slot not in busy_slots]

    if not free_slots:
        return f"{interviewer} đã kín lịch vào ngày {date}. Không còn khung giờ trống."

    return f"Khung giờ trống của {interviewer} ngày {date}: {', '.join(free_slots)}."


def schedule_interview(candidate_name: str, interviewer: str, date: str, time: str) -> str:
    """
    Đặt lịch phỏng vấn cho ứng viên với người phỏng vấn, nếu khung giờ còn trống.

    Args:
        candidate_name (str): Tên ứng viên
        interviewer (str): Tên người phỏng vấn
        date (str): Ngày phỏng vấn, định dạng YYYY-MM-DD
        time (str): Giờ phỏng vấn, định dạng HH:MM (Ví dụ: '09:00')

    Returns:
        str: Thông báo đặt lịch thành công, hoặc chuỗi LỖI nếu khung giờ đã bận/không hợp lệ.
    """
    key = interviewer.strip().lower()
    if key not in INTERVIEWER_CALENDAR:
        return f"LỖI: Không tìm thấy người phỏng vấn '{interviewer}' trong hệ thống."

    busy_slots = INTERVIEWER_CALENDAR[key].setdefault(date, [])
    if time in busy_slots:
        return f"LỖI: {interviewer} đã bận vào lúc {time} ngày {date}. Vui lòng chọn khung giờ khác."

    busy_slots.append(time)
    BOOKED_INTERVIEWS.append({
        "candidate": candidate_name,
        "interviewer": interviewer,
        "date": date,
        "time": time,
    })

    return (
        f"✅ Đặt lịch thành công: Ứng viên '{candidate_name}' phỏng vấn với '{interviewer}' "
        f"lúc {time} ngày {date}."
    )


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "screen_resume": screen_resume,
    "check_interviewer_availability": check_interviewer_availability,
    "schedule_interview": schedule_interview,
}
