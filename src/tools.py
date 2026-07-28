"""Công cụ mô phỏng cho Trợ lý sàng lọc hồ sơ & hẹn phỏng vấn.

Dữ liệu chỉ là dữ liệu mẫu đã ẩn danh, không dùng để ra quyết định tuyển dụng thật.
"""

from __future__ import annotations

from typing import Dict


CANDIDATES: Dict[str, Dict[str, object]] = {
    "UV001": {"skills": ["Python", "SQL", "FastAPI"], "years": 2, "role": "Backend Developer", "status": "new"},
    "UV002": {"skills": ["Figma", "UI/UX", "User Research"], "years": 3, "role": "UI/UX Designer", "status": "new"},
    "UV003": {"skills": ["HTML", "CSS"], "years": 0, "role": "Backend Developer", "status": "new"},
}

ROLE_REQUIREMENTS = {
    "backend developer": {"skills": {"python", "sql"}, "min_years": 1},
    "ui/ux designer": {"skills": {"figma", "ui/ux"}, "min_years": 2},
}

INTERVIEW_SLOTS = {
    "SLOT01": {"role": "Backend Developer", "time": "09:00, 30/07/2026", "available": True},
    "SLOT02": {"role": "Backend Developer", "time": "14:00, 30/07/2026", "available": True},
    "SLOT03": {"role": "UI/UX Designer", "time": "10:00, 31/07/2026", "available": True},
}


def get_candidate_profile(candidate_id: str) -> str:
    """Tra cứu hồ sơ ứng viên đã ẩn danh.

    Input: mã ứng viên, ví dụ ``UV001``. Output: kỹ năng, kinh nghiệm, vị trí ứng tuyển;
    không trả về dữ liệu nhạy cảm. Error: trả chuỗi ``LỖI`` nếu mã không tồn tại.
    Side effect: không có.
    """
    candidate = CANDIDATES.get(candidate_id.upper())
    if not candidate:
        return f"LỖI: Không tìm thấy hồ sơ ứng viên '{candidate_id}'."
    return (f"Hồ sơ {candidate_id.upper()}: vị trí {candidate['role']}; "
            f"kỹ năng {', '.join(candidate['skills'])}; kinh nghiệm {candidate['years']} năm.")


def evaluate_candidate(candidate_id: str, position: str) -> str:
    """Đối chiếu hồ sơ với tiêu chí công việc minh bạch đã định nghĩa.

    Input: mã ứng viên và vị trí. Output: PASS/CHƯA ĐẠT cùng lý do dựa trên kỹ năng,
    kinh nghiệm. Không dùng tuổi, giới tính, ảnh, quê quán hay thuộc tính nhạy cảm.
    Side effect: không có; kết quả chỉ hỗ trợ HR, quyết định cuối cùng do con người.
    """
    candidate = CANDIDATES.get(candidate_id.upper())
    req = ROLE_REQUIREMENTS.get(position.lower())
    if not candidate:
        return f"LỖI: Không tìm thấy hồ sơ ứng viên '{candidate_id}'."
    if not req:
        return f"LỖI: Chưa có bộ tiêu chí cho vị trí '{position}'."
    skills = {skill.lower() for skill in candidate["skills"]}
    missing = sorted(req["skills"] - skills)
    years_ok = candidate["years"] >= req["min_years"]
    if not missing and years_ok:
        return (f"ĐÁNH GIÁ: PASS. {candidate_id.upper()} đáp ứng kỹ năng và tối thiểu "
                f"{req['min_years']} năm kinh nghiệm. Cần HR xác nhận trước khi mời phỏng vấn.")
    reasons = []
    if missing:
        reasons.append("thiếu kỹ năng: " + ", ".join(missing))
    if not years_ok:
        reasons.append(f"kinh nghiệm {candidate['years']} năm, yêu cầu {req['min_years']} năm")
    return "ĐÁNH GIÁ: CHƯA ĐẠT. " + "; ".join(reasons) + "."


def get_interview_slots(position: str) -> str:
    """Tra cứu các khung giờ phỏng vấn còn trống cho một vị trí.

    Input: tên vị trí. Output: mã slot và thời gian; Error: ``LỖI`` khi không có slot.
    Side effect: không có.
    """
    slots = [(slot_id, item) for slot_id, item in INTERVIEW_SLOTS.items()
             if item["role"].lower() == position.lower() and item["available"]]
    if not slots:
        return f"LỖI: Không có lịch phỏng vấn trống cho vị trí '{position}'."
    return "Lịch trống: " + "; ".join(f"{slot_id} - {item['time']}" for slot_id, item in slots) + "."


def schedule_interview(candidate_id: str, slot_id: str) -> str:
    """Đặt lịch phỏng vấn mô phỏng sau khi HR đã xác nhận và ứng viên đồng ý.

    Input: mã ứng viên, mã slot. Output: xác nhận/lỗi. Side effect: đánh dấu slot đã dùng
    trong phiên chạy hiện tại. Tool từ chối nếu slot không tồn tại hoặc đã được đặt.
    """
    if candidate_id.upper() not in CANDIDATES:
        return f"LỖI: Không tìm thấy hồ sơ ứng viên '{candidate_id}'."
    slot = INTERVIEW_SLOTS.get(slot_id.upper())
    if not slot:
        return f"LỖI: Không tìm thấy mã lịch '{slot_id}'."
    if not slot["available"]:
        return f"LỖI: Lịch '{slot_id.upper()}' không còn trống."
    slot["available"] = False
    return f"ĐÃ ĐẶT LỊCH (mô phỏng): {candidate_id.upper()} vào {slot['time']} ({slot['role']})."


AVAILABLE_TOOLS = {
    "get_candidate_profile": get_candidate_profile,
    "evaluate_candidate": evaluate_candidate,
    "get_interview_slots": get_interview_slots,
    "schedule_interview": schedule_interview,
}
