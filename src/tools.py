"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Đề tài: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

NGUYÊN TẮC THIẾT KẾ TOOL (áp dụng cho cả 3 tool bên dưới):
1. Deterministic — tool KHÔNG tự gọi LLM. Việc suy luận "có nên đặt lịch hay không" thuộc
   về Agent; tool chỉ cung cấp dữ kiện (evidence) để Agent suy luận.
2. Error là dữ liệu, không phải crash — mọi lỗi nghiệp vụ trả về chuỗi bắt đầu bằng "LỖI:"
   thay vì raise exception, để Agent đọc Observation và tự chuyển hướng.
3. Mỗi tool có contract 8 field đầy đủ trong docstring (Name / Purpose / Input schema /
   Output schema / Error semantics / Side effect / Example / Safety).
"""

import re
from datetime import date as _date

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+")
_DATE_RE = re.compile(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$")

# Ngưỡng khớp từ khóa CV/JD để coi là ĐẠT yêu cầu vị trí
MATCH_THRESHOLD = 0.35

# Vài từ nối phổ biến (VN + EN) bị loại khi so khớp từ khóa CV/JD, tránh làm nhiễu điểm khớp
_STOPWORDS = {
    "the", "and", "for", "with", "our", "you", "your", "are", "was", "were", "have", "has",
    "this", "that", "from", "will", "who", "role", "work", "team", "years", "year",
    "và", "của", "các", "được", "trong", "cho", "với", "là", "có", "một", "này", "để",
    "kinh", "nghiệm", "công", "việc", "yêu", "cầu", "vị", "trí",
}


def _extract_email(text: str) -> str:
    """Trích email đầu tiên tìm được trong text, hoặc chuỗi báo không tìm thấy."""
    if not text:
        return "(không tìm thấy email)"
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else "(không tìm thấy email)"


def _keywords(text: str) -> set:
    """Tách tập từ khóa (>=3 ký tự, bỏ stopword) để so khớp CV với JD."""
    tokens = re.findall(r"[a-zA-ZÀ-ỹ0-9+#.]{3,}", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


def _parse_date(date_str: str):
    """Parse chuỗi dd/mm/yyyy thành datetime.date. Trả về (date, None) nếu hợp lệ,
    hoặc (None, "chuỗi LỖI") nếu sai định dạng / không phải ngày thật."""
    if not date_str or not date_str.strip():
        return None, "LỖI: Thiếu ngày (bắt buộc, định dạng dd/mm/yyyy)."
    match = _DATE_RE.match(date_str)
    if not match:
        return None, (
            f"LỖI: Ngày '{date_str}' sai định dạng. Định dạng đúng là dd/mm/yyyy "
            "(ví dụ: 05/08/2026)."
        )
    day, month, year = (int(g) for g in match.groups())
    try:
        parsed = _date(year, month, day)
    except ValueError:
        return None, (
            f"LỖI: Ngày '{date_str}' không tồn tại trên dương lịch "
            "(kiểm tra lại ngày/tháng)."
        )
    return parsed, None


def normalize_date(date_str: str):
    """Chuẩn hóa ngày hợp lệ về dạng dd/mm/yyyy để dùng làm calendar key."""
    parsed, error = _parse_date(date_str)
    return parsed.strftime("%d/%m/%Y") if not error else None


def screen_resume(resume_text: str, job_description_text: str) -> str:
    """
    So khớp CV ứng viên với JD của vị trí đang tuyển và trích email hai bên.

    TOOL CONTRACT (8 field):
    - Name: screen_resume — sàng lọc hồ sơ ứng viên theo JD.
    - Purpose: DÙNG KHI cần biết ứng viên có đạt yêu cầu vị trí không (luôn gọi trước
      khi cân nhắc đặt lịch). KHÔNG DÙNG để đặt lịch hay tra cứu lịch trống.
    - Input schema: resume_text (str, required) — toàn văn CV;
      job_description_text (str, required) — toàn văn JD.
    - Output schema: chuỗi nhiều dòng gồm: email ứng viên (từ CV), email HR (từ JD),
      độ khớp từ khóa (%), danh sách từ khóa khớp, từ khóa JD còn thiếu, và dòng
      "Kết luận: ĐẠT/KHÔNG ĐẠT yêu cầu vị trí." (ĐẠT khi độ khớp >= MATCH_THRESHOLD).
    - Error semantics: thiếu CV -> "LỖI: Thiếu nội dung CV..."; thiếu JD -> "LỖI: Thiếu
      nội dung JD..."; JD không trích được từ khóa -> "LỖI: Không trích được từ khóa...".
    - Side effect: READ-ONLY — không ghi/đổi trạng thái nào.
    - Example: screen_resume("Nguyen Van A - a@gmail.com. Python, SQL, Docker.",
      "Tuyen Backend - hr@abc.com. Yeu cau: Python, SQL, Docker.")
      -> "...Độ khớp từ khóa CV/JD: 75%...Kết luận: ĐẠT yêu cầu vị trí."
    - Safety: mọi nhánh lỗi đều trả chuỗi "LỖI: ..." — không raise exception.

    Args:
        resume_text (str): Toàn bộ text CV ứng viên do người dùng dán vào.
        job_description_text (str): Toàn bộ text JD của vị trí đang tuyển.

    Returns:
        str: Kết quả sàng lọc, hoặc chuỗi "LỖI: ..." nếu đầu vào không dùng được.
    """
    if not resume_text or not resume_text.strip():
        return "LỖI: Thiếu nội dung CV — không có gì để sàng lọc."
    if not job_description_text or not job_description_text.strip():
        return "LỖI: Thiếu nội dung JD — không có tiêu chí để so khớp."

    candidate_email = _extract_email(resume_text)
    hr_email = _extract_email(job_description_text)

    resume_kw = _keywords(resume_text)
    jd_kw = _keywords(job_description_text)
    if not jd_kw:
        return "LỖI: Không trích được từ khóa nào từ JD để so khớp."

    matched = sorted(resume_kw & jd_kw)
    missing = sorted(jd_kw - resume_kw)
    score = len(matched) / len(jd_kw)
    verdict = "ĐẠT" if score >= MATCH_THRESHOLD else "KHÔNG ĐẠT"

    return (
        f"Email ứng viên (trích từ CV): {candidate_email}\n"
        f"Email liên hệ nhà tuyển dụng (trích từ JD): {hr_email}\n"
        f"Độ khớp từ khóa CV/JD: {score:.0%}\n"
        f"Từ khóa khớp: {', '.join(matched[:12]) or '(không có)'}\n"
        f"Từ khóa JD còn thiếu trong CV: {', '.join(missing[:12]) or '(không có)'}\n"
        f"Kết luận: {verdict} yêu cầu vị trí."
    )


# Mock lịch làm việc trong bộ nhớ — chỉ để demo, không phải hệ thống lịch thật.
INTERVIEW_SLOTS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
_BOOKED = {}  # date (str) -> set các time đã bị đặt


def reset_calendar() -> None:
    """Xóa toàn bộ lịch đã đặt trong mock calendar (dùng cho test/demo lặp lại)."""
    _BOOKED.clear()


def check_calendar_availability(date: str) -> str:
    """
    Kiểm tra khung giờ phỏng vấn còn trống trong một ngày.

    TOOL CONTRACT (8 field):
    - Name: check_calendar_availability — tra lịch trống của người phỏng vấn.
    - Purpose: DÙNG KHI cần biết ngày đó còn khung giờ nào trống, BẮT BUỘC gọi trước
      schedule_interview. KHÔNG DÙNG để đặt lịch (không thay đổi trạng thái gì).
    - Input schema: date (str, required) — định dạng dd/mm/yyyy.
    - Output schema: "Ngày <date> còn trống các khung giờ: 09:00, 10:00, ...".
    - Error semantics: thiếu ngày / sai định dạng / ngày không tồn tại / ngày trong quá
      khứ / đã kín lịch -> đều trả chuỗi bắt đầu bằng "LỖI:" kèm lý do cụ thể.
    - Side effect: READ-ONLY — chỉ đọc mock calendar, không ghi.
    - Example: check_calendar_availability("05/08/2026")
      -> "Ngày 05/08/2026 còn trống các khung giờ: 09:00, 10:00, 11:00, 14:00, 15:00, 16:00."
    - Safety: validate định dạng bằng regex + datetime.date, mọi lỗi trả chuỗi "LỖI: ...".

    Args:
        date (str): Ngày cần kiểm tra, định dạng dd/mm/yyyy (Ví dụ: '05/08/2026').

    Returns:
        str: Danh sách khung giờ còn trống, hoặc chuỗi "LỖI: ..." nếu không tra được.
    """
    parsed, error = _parse_date(date)
    if error:
        return error
    if parsed < _date.today():
        return f"LỖI: Ngày {date.strip()} đã ở trong quá khứ, không thể xếp lịch phỏng vấn."

    key = parsed.strftime("%d/%m/%Y")
    booked = _BOOKED.get(key, set())
    free = [t for t in INTERVIEW_SLOTS if t not in booked]
    if not free:
        return f"LỖI: Ngày {key} đã kín lịch, không còn khung giờ trống. Hãy thử một ngày khác."
    return f"Ngày {key} còn trống các khung giờ: {', '.join(free)}."


def schedule_interview(candidate_name: str, date: str, time: str) -> str:
    """
    Đặt lịch phỏng vấn cho ứng viên vào một khung giờ cụ thể.

    TOOL CONTRACT (8 field):
    - Name: schedule_interview — chốt lịch phỏng vấn.
    - Purpose: DÙNG KHI ứng viên đã ĐẠT yêu cầu (theo screen_resume) VÀ khung giờ đã được
      xác nhận còn trống (theo check_calendar_availability). KHÔNG DÙNG khi ứng viên chưa
      qua sàng lọc hoặc chưa kiểm tra lịch.
    - Input schema: candidate_name (str, required); date (str, required, dd/mm/yyyy);
      time (str, required, phải thuộc INTERVIEW_SLOTS).
    - Output schema: "Đã đặt lịch phỏng vấn cho <tên> vào <giờ> ngày <ngày>."
    - Error semantics: thiếu tên/giờ, sai định dạng ngày, ngày quá khứ, giờ ngoài danh
      sách hợp lệ, hoặc giờ đã bị đặt -> trả chuỗi "LỖI: ..." kèm gợi ý khắc phục.
    - Side effect: ⚠️ CÓ GHI TRẠNG THÁI — thêm (date, time) vào mock calendar, làm khung
      giờ đó biến mất khỏi kết quả check_calendar_availability lần sau.
    - Example: schedule_interview("Nguyễn Văn A", "05/08/2026", "14:00")
      -> "Đã đặt lịch phỏng vấn cho Nguyễn Văn A vào 14:00 ngày 05/08/2026."
    - Safety: kiểm tra đầy đủ trước khi ghi; double-booking bị chặn và trả chuỗi "LỖI:".

    Args:
        candidate_name (str): Tên ứng viên.
        date (str): Ngày phỏng vấn, định dạng dd/mm/yyyy.
        time (str): Khung giờ, phải là một trong các giờ do check_calendar_availability trả về.

    Returns:
        str: Xác nhận đặt lịch, hoặc chuỗi "LỖI: ..." nếu không đặt được.
    """
    if not candidate_name or not candidate_name.strip():
        return "LỖI: Thiếu tên ứng viên (candidate_name) để đặt lịch."
    if not time or not time.strip():
        return f"LỖI: Thiếu khung giờ (time). Các giờ hợp lệ: {', '.join(INTERVIEW_SLOTS)}."

    parsed, error = _parse_date(date)
    if error:
        return error
    if parsed < _date.today():
        return f"LỖI: Ngày {date.strip()} đã ở trong quá khứ, không thể xếp lịch phỏng vấn."

    key = parsed.strftime("%d/%m/%Y")
    slot = time.strip()
    if slot not in INTERVIEW_SLOTS:
        return f"LỖI: Khung giờ '{slot}' không hợp lệ. Các giờ hợp lệ: {', '.join(INTERVIEW_SLOTS)}."

    booked = _BOOKED.setdefault(key, set())
    if slot in booked:
        return (
            f"LỖI: Khung giờ {slot} ngày {key} đã có người đặt trước. "
            "Hãy gọi lại check_calendar_availability để chọn giờ còn trống khác."
        )
    booked.add(slot)
    return f"Đã đặt lịch phỏng vấn cho {candidate_name.strip()} vào {slot} ngày {key}."


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "screen_resume": screen_resume,
    "check_calendar_availability": check_calendar_availability,
    "schedule_interview": schedule_interview,
}
