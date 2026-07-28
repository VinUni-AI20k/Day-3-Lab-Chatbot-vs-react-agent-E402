"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Đề bài 9: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn

Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

from datetime import datetime
import re


# ============================================================
# 📦 MOCK DATABASE (giả lập dữ liệu ứng viên & yêu cầu vị trí)
# ============================================================

CANDIDATE_DB = {
    "CV-1042": {
        "name": "Nguyễn Văn A",
        "position_applied": "Backend Developer",
        "skills": ["Python", "SQL", "Django", "Git"],
        "experience_years": 3,
        "education": "Cử nhân Khoa học Máy tính",
    },
    "CV-2078": {
        "name": "Trần Thị B",
        "position_applied": "Data Analyst",
        "skills": ["SQL", "Excel", "Power BI", "Python"],
        "experience_years": 2,
        "education": "Cử nhân Thống kê",
    },
}

JOB_REQUIREMENTS_DB = {
    "Backend Developer": {
        "required_skills": ["Python", "SQL", "Django"],
        "min_experience_years": 2,
    },
    "Data Analyst": {
        "required_skills": ["SQL", "Excel", "Power BI"],
        "min_experience_years": 1,
    },
    "Frontend Developer": {
        "required_skills": ["JavaScript", "React", "CSS"],
        "min_experience_years": 1,
    },
}

# Lưu các lịch phỏng vấn đã đặt (giả lập)
SCHEDULED_INTERVIEWS = []


# ============================================================
# 🔧 TOOLS
# ============================================================

def get_candidate_profile(candidate_id: str) -> str:
    """
    Tra cứu hồ sơ ứng viên theo mã CV trong hệ thống.

    Args:
        candidate_id (str): Mã hồ sơ ứng viên (Ví dụ: 'CV-1042').

    Returns:
        str: Thông tin chi tiết ứng viên (tên, vị trí ứng tuyển, kỹ năng,
             số năm kinh nghiệm, học vấn), hoặc thông báo lỗi nếu không
             tìm thấy mã ứng viên trong hệ thống.
    """
    if not candidate_id or not candidate_id.strip():
        return "LỖI: Vui lòng cung cấp mã ứng viên."

    candidate_id = candidate_id.strip().upper()
    profile = CANDIDATE_DB.get(candidate_id)

    if not profile:
        return f"LỖI: Không tìm thấy ứng viên với mã '{candidate_id}' trong hệ thống."

    return (
        f"Hồ sơ ứng viên {candidate_id}:\n"
        f"- Họ tên: {profile['name']}\n"
        f"- Vị trí ứng tuyển: {profile['position_applied']}\n"
        f"- Kỹ năng: {', '.join(profile['skills'])}\n"
        f"- Kinh nghiệm: {profile['experience_years']} năm\n"
        f"- Học vấn: {profile['education']}"
    )


def check_job_requirements(job_title: str) -> str:
    """
    Tra cứu yêu cầu tuyển dụng (kỹ năng bắt buộc, số năm kinh nghiệm tối thiểu)
    cho một vị trí công việc cụ thể.

    Args:
        job_title (str): Tên vị trí tuyển dụng (Ví dụ: 'Data Analyst').

    Returns:
        str: Danh sách yêu cầu của vị trí, hoặc lỗi nếu vị trí không tồn tại
             trong hệ thống.
    """
    if not job_title or not job_title.strip():
        return "LỖI: Vui lòng cung cấp tên vị trí tuyển dụng."

    job_title_clean = job_title.strip()
    req = JOB_REQUIREMENTS_DB.get(job_title_clean)

    if not req:
        available = ", ".join(JOB_REQUIREMENTS_DB.keys())
        return (
            f"LỖI: Không tìm thấy yêu cầu tuyển dụng cho vị trí '{job_title}'. "
            f"Các vị trí hiện có: {available}."
        )

    return (
        f"Yêu cầu tuyển dụng cho vị trí {job_title_clean}:\n"
        f"- Kỹ năng bắt buộc: {', '.join(req['required_skills'])}\n"
        f"- Kinh nghiệm tối thiểu: {req['min_experience_years']} năm"
    )


def schedule_interview(candidate_id: str, interviewer_name: str, interview_datetime: str) -> str:
    """
    Đặt lịch phỏng vấn cho ứng viên. Tool sẽ TỰ VALIDATE:
    - Mã ứng viên phải tồn tại trong hệ thống (kiểm tra qua CANDIDATE_DB).
    - Ngày giờ phỏng vấn phải hợp lệ (đúng định dạng, ngày tháng có thật,
      giờ giấc hợp lý trong khung 07:00 - 20:00).
    Nếu bất kỳ điều kiện nào không thỏa, tool trả về lỗi và KHÔNG tạo lịch hẹn.

    Args:
        candidate_id (str): Mã ứng viên (Ví dụ: 'CV-2078').
        interviewer_name (str): Tên người phỏng vấn (Ví dụ: 'Anh Minh').
        interview_datetime (str): Ngày giờ phỏng vấn theo định dạng
            'DD/MM/YYYY HH:MM' (Ví dụ: '05/11/2025 14:00').

    Returns:
        str: Xác nhận đặt lịch thành công, hoặc thông báo lỗi rõ ràng
             (candidate not found / invalid date / invalid time) nếu
             không thể đặt lịch.
    """
    if not candidate_id or not interviewer_name or not interview_datetime:
        return "LỖI: Thiếu thông tin (mã ứng viên / người phỏng vấn / thời gian)."

    candidate_id = candidate_id.strip().upper()

    # 1. Validate ứng viên có tồn tại không
    if candidate_id not in CANDIDATE_DB:
        return f"LỖI: candidate not found - Không tìm thấy ứng viên với mã '{candidate_id}'. Không thể đặt lịch."

    # 2. Validate định dạng & tính hợp lệ của ngày giờ
    dt_str = interview_datetime.strip()
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})$", dt_str)
    if not match:
        return (
            f"LỖI: invalid date format - '{interview_datetime}' không đúng định dạng "
            f"'DD/MM/YYYY HH:MM'. Không thể đặt lịch."
        )

    day, month, year, hour, minute = map(int, match.groups())

    try:
        parsed_dt = datetime(year=year, month=month, day=day, hour=hour, minute=minute)
    except ValueError:
        return (
            f"LỖI: invalid date - '{interview_datetime}' không phải là ngày giờ có thật "
            f"(ví dụ: ngày/tháng không tồn tại). Không thể đặt lịch."
        )

    # 3. Validate giờ giấc hợp lý (giờ hành chính mở rộng: 07:00 - 20:00)
    if not (7 <= parsed_dt.hour < 20):
        return (
            f"LỖI: invalid time - Giờ phỏng vấn '{parsed_dt.strftime('%H:%M')}' nằm ngoài "
            f"khung giờ làm việc hợp lý (07:00 - 20:00). Không thể đặt lịch."
        )

    # 4. Validate không đặt lịch trong quá khứ
    if parsed_dt < datetime.now():
        return f"LỖI: invalid date - Thời gian '{dt_str}' đã ở trong quá khứ. Không thể đặt lịch."

    # Mọi điều kiện hợp lệ -> tạo lịch hẹn
    candidate_name = CANDIDATE_DB[candidate_id]["name"]
    SCHEDULED_INTERVIEWS.append({
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "interviewer": interviewer_name,
        "datetime": parsed_dt.strftime("%d/%m/%Y %H:%M"),
    })

    return (
        f"Đã đặt lịch phỏng vấn thành công:\n"
        f"- Ứng viên: {candidate_name} ({candidate_id})\n"
        f"- Người phỏng vấn: {interviewer_name}\n"
        f"- Thời gian: {parsed_dt.strftime('%d/%m/%Y %H:%M')}"
    )


# ============================================================
# 🔧 TOOLS PHỤ TRỢ (giữ lại để mở rộng, không nằm trong
# tools_expected của các test case hiện tại nhưng hữu ích cho
# các luồng hội thoại khác)
# ============================================================

def extract_skills(candidate_id: str) -> str:
    """
    Liệt kê kỹ năng chính của ứng viên theo mã hồ sơ.

    Args:
        candidate_id (str): Mã ứng viên (Ví dụ: 'CV-1042').

    Returns:
        str: Danh sách kỹ năng của ứng viên, hoặc lỗi nếu không tìm thấy.
    """
    if not candidate_id or not candidate_id.strip():
        return "LỖI: Vui lòng cung cấp mã ứng viên."

    candidate_id = candidate_id.strip().upper()
    profile = CANDIDATE_DB.get(candidate_id)

    if not profile:
        return f"LỖI: Không tìm thấy ứng viên với mã '{candidate_id}' trong hệ thống."

    return f"Kỹ năng của {profile['name']} ({candidate_id}): {', '.join(profile['skills'])}"


def generate_interview_questions(job_role: str) -> str:
    """
    Sinh bộ câu hỏi phỏng vấn phù hợp với vị trí tuyển dụng.

    Args:
        job_role (str): Tên vị trí tuyển dụng.

    Returns:
        str: Danh sách câu hỏi phỏng vấn đề xuất.
    """
    if not job_role or not job_role.strip():
        return "LỖI: Vui lòng cung cấp tên vị trí tuyển dụng."

    return (
        f"Bộ câu hỏi phỏng vấn cho vị trí {job_role}:\n"
        "1. Hãy mô tả kinh nghiệm liên quan trực tiếp đến vị trí này.\n"
        "2. Bạn đã từng xử lý tình huống khó trong công việc như thế nào?\n"
        "3. Vì sao bạn phù hợp với vị trí và văn hóa công ty?\n"
    )


# ============================================================
# 📋 ĐĂNG KÝ TOOLS ĐỂ AGENT SỬ DỤNG
# ============================================================

AVAILABLE_TOOLS = {
    "get_candidate_profile": get_candidate_profile,
    "check_job_requirements": check_job_requirements,
    "schedule_interview": schedule_interview,
    "extract_skills": extract_skills,
    "generate_interview_questions": generate_interview_questions,
}