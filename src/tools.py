"""
🛠️ TOOL REGISTRY & SCHEMAS (Role 2: Tool Engineer)

This module contains all tools that the ReAct Agent can call.

Important Guardrails:
- These tools DO NOT diagnose diseases.
- These tools DO NOT prescribe medicine.
- These tools ONLY help recommend the appropriate specialty
  and assist with appointment booking.
"""

from typing import Dict, List
import random

# ==========================================================
# Fake Data
# ==========================================================

SPECIALTY_KEYWORDS: Dict[str, List[str]] = {
    "Tiêu hóa": [
        "đau dạ dày",
        "đau bụng",
        "tiêu chảy",
        "ợ chua",
        "đầy hơi",
        "khó tiêu",
    ],
    "Ngoại tổng quát": [
        "đau bụng dưới bên phải",
        "viêm ruột thừa",
        "vết thương",
        "gãy xương",
        "sưng",
        "chấn thương",
    ],
    "Tai Mũi Họng": [
        "đau họng",
        "viêm họng",
        "ngạt mũi",
        "ho",
        "viêm amidan",
    ],
    "Tim mạch": [
        "tim đập nhanh",
        "cao huyết áp",
        "hồi hộp",
    ],
}


DOCTORS: Dict[str, List[str]] = {
    "Tiêu hóa": [
        "BS. Nguyễn Văn Minh (15 năm kinh nghiệm)",
        "BS. Trần Thu Hà (8 năm kinh nghiệm)",
    ],
    "Ngoại tổng quát": [
        "BS. Lê Hoàng Nam (12 năm kinh nghiệm)",
        "BS. Phạm Hải An (9 năm kinh nghiệm)",
    ],
    "Tai Mũi Họng": [
        "BS. Nguyễn Đức Long (10 năm kinh nghiệm)",
    ],
    "Tim mạch": [
        "BS. Võ Minh Quân (20 năm kinh nghiệm)",
    ],
}


AVAILABLE_SLOTS: Dict[str, Dict[str, List[str]]] = {
    "BS. Nguyễn Văn Minh (15 năm kinh nghiệm)": {
        "2026-08-01": ["08:00", "09:30", "10:30"]
    },
    "BS. Trần Thu Hà (8 năm kinh nghiệm)": {
        "2026-08-01": ["09:00", "13:30", "15:00"]
    },
    "BS. Lê Hoàng Nam (12 năm kinh nghiệm)": {
        "2026-08-01": ["08:30", "10:00"]
    },
    "BS. Phạm Hải An (9 năm kinh nghiệm)": {
        "2026-08-01": ["14:00", "16:00"]
    },
    "BS. Nguyễn Đức Long (10 năm kinh nghiệm)": {
        "2026-08-01": ["09:00", "11:00"]
    },
    "BS. Võ Minh Quân (20 năm kinh nghiệm)": {
        "2026-08-01": ["08:00", "10:00", "14:00"]
    },
}


EMERGENCY_KEYWORDS = [
    "khó thở",
    "bất tỉnh",
    "đau ngực dữ dội",
    "chảy máu nhiều",
    "co giật",
]


# ==========================================================
# Tool 1
# ==========================================================

def suggest_specialty(symptoms: str) -> str:
    """
    Recommend an appropriate medical specialty based on symptoms.

    This tool ONLY recommends a department for appointment booking.
    It DOES NOT diagnose diseases or prescribe medication.

    Args:
        symptoms: Patient's description of symptoms.

    Returns:
        A recommendation for a medical specialty or an appropriate
        error/guardrail message.
    """
    try:
        text = symptoms.lower()

        # Guardrail: emergency symptoms
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in text:
                return (
                    "⚠️ Dấu hiệu có thể là tình huống khẩn cấp. "
                    "Vui lòng đến bệnh viện hoặc cơ sở cấp cứu gần nhất "
                    "hoặc gọi số cấp cứu thay vì đặt lịch trực tuyến."
                )

        # Keyword matching
        for specialty, keywords in SPECIALTY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return (
                        f"Gợi ý chuyên khoa: {specialty}\n"
                        "Lưu ý: Đây chỉ là gợi ý đặt lịch, "
                        "không phải chẩn đoán y khoa."
                    )

        return (
            "Không xác định được chuyên khoa phù hợp. "
            "Vui lòng mô tả triệu chứng chi tiết hơn."
        )

    except Exception as e:
        return f"LỖI TOOL: {e}"


# ==========================================================
# Tool 2
# ==========================================================

def list_doctors(specialty: str, date: str) -> str:
    """
    Retrieve available doctors for a specialty.

    Args:
        specialty: Medical specialty.
        date: Appointment date (YYYY-MM-DD).

    Returns:
        A formatted list of doctors or an error message.
    """
    try:
        if specialty not in DOCTORS:
            return f"Không tìm thấy chuyên khoa '{specialty}'."

        doctors = DOCTORS[specialty]

        result = (
            f"Danh sách bác sĩ khoa {specialty} "
            f"({date}):\n"
        )

        for i, doctor in enumerate(doctors, start=1):
            result += f"{i}. {doctor}\n"

        return result

    except Exception as e:
        return f"LỖI TOOL: {e}"


# ==========================================================
# Tool 3
# ==========================================================

def check_slots(doctor_name: str, date: str) -> str:
    """
    Check available appointment slots for a doctor.

    Args:
        doctor_name: Doctor's full name.
        date: Appointment date.

    Returns:
        Available appointment slots or an error message.
    """
    try:
        doctor_schedule = AVAILABLE_SLOTS.get(doctor_name)

        if doctor_schedule is None:
            return "Không tìm thấy bác sĩ."

        slots = doctor_schedule.get(date)

        if slots is None or len(slots) == 0:
            return "Bác sĩ đã kín lịch vào ngày này."

        return (
            f"Lịch trống của {doctor_name} ({date}):\n"
            + ", ".join(slots)
        )

    except Exception as e:
        return f"LỖI TOOL: {e}"


# ==========================================================
# Tool 4
# ==========================================================

def book_appointment(
    doctor_name: str,
    date: str,
    time: str,
    patient_name: str,
) -> str:
    """
    Book an appointment with a doctor.

    Args:
        doctor_name: Selected doctor.
        date: Appointment date.
        time: Appointment time.
        patient_name: Patient's full name.

    Returns:
        Booking confirmation or an error message.
    """
    try:
        if doctor_name not in AVAILABLE_SLOTS:
            return "Không tìm thấy bác sĩ."

        if date not in AVAILABLE_SLOTS[doctor_name]:
            return "Ngày khám không hợp lệ."

        slots = AVAILABLE_SLOTS[doctor_name][date]

        if time not in slots:
            return (
                "Khung giờ đã được đặt hoặc không tồn tại."
            )

        # Remove booked slot
        slots.remove(time)

        appointment_id = (
            f"APT-{date.replace('-', '')}-"
            f"{random.randint(100,999)}"
        )

        return (
            "✅ Đặt lịch thành công!\n"
            f"Bệnh nhân: {patient_name}\n"
            f"Bác sĩ: {doctor_name}\n"
            f"Ngày: {date}\n"
            f"Giờ: {time}\n"
            f"Mã lịch hẹn: {appointment_id}"
        )

    except Exception as e:
        return f"LỖI TOOL: {e}"


# ==========================================================
# Tool Registry
# ==========================================================

AVAILABLE_TOOLS = {
    "suggest_specialty": suggest_specialty,
    "list_doctors": list_doctors,
    "check_slots": check_slots,
    "book_appointment": book_appointment,
}