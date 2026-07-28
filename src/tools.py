"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Trợ Lý Đặt Lịch Khám Bệnh & Tư Vấn Chuyên Khoa

Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
Mỗi hàm tool đều:
  - Có Docstring mô tả đầy đủ: Purpose, Input, Output, Error semantics
  - Bắt lỗi an toàn: trả về chuỗi thông báo lỗi thay vì crash chương trình
  - Là read-only hoặc side-effect nhỏ (không hủy dữ liệu quan trọng)
"""

# ---------------------------------------------------------------------------
# 📅 DỮ LIỆU GIẢ LẬP (Mock Database) - Thay thế cho database/API thực tế
# ---------------------------------------------------------------------------

DOCTOR_SCHEDULE_DB = {
    "tim mạch": {
        "bs001": {
            "name": "BS. Trần Thị Mai",
            "slots": {
                "ngày mai": ["08:00", "10:30", "14:00"],
                "hôm nay":  [],
                "2026-07-29": ["09:00", "11:00"],
            }
        },
        "bs002": {
            "name": "BS. Nguyễn Hữu Phúc",
            "slots": {
                "ngày mai": ["09:00", "15:30"],
                "hôm nay":  ["16:00"],
            }
        },
    },
    "thần kinh": {
        "bs003": {
            "name": "BS. Lê Minh Khoa",
            "slots": {
                "hôm nay":  ["14:00", "15:00", "16:30"],
                "ngày mai": ["08:30", "10:00", "13:00"],
            }
        },
    },
    "nội tổng quát": {
        "bs004": {
            "name": "BS. Phạm Thị Lan",
            "slots": {
                "hôm nay":  ["10:00", "11:00"],
                "ngày mai": ["08:00", "09:30", "14:30"],
            }
        },
    },
    "ngoại": {
        "bs005": {
            "name": "BS. Võ Văn Tuấn",
            "slots": {
                "hôm nay":  [],
                "ngày mai": ["08:00", "13:00"],
            }
        },
    },
}

SYMPTOM_TO_SPECIALTY = {
    "đau đầu":        "Thần kinh",
    "chóng mặt":      "Thần kinh",
    "buồn nôn":       "Nội tổng quát",
    "đau ngực":       "Tim mạch",
    "khó thở":        "Tim mạch",
    "tim đập nhanh":  "Tim mạch",
    "hồi hộp":        "Tim mạch",
    "đau bụng":       "Nội tổng quát",
    "sốt":            "Nội tổng quát",
    "đau lưng":       "Ngoại",
    "đau khớp":       "Ngoại",
    "tê tay":         "Thần kinh",
    "mất ngủ":        "Thần kinh",
}

VALID_SPECIALTIES = set(DOCTOR_SCHEDULE_DB.keys())

# Bộ đếm lịch hẹn (giả lập auto-increment ID)
_appointment_counter = {"value": 1000}


# ---------------------------------------------------------------------------
# 🛠️ TOOL 1: check_doctor_schedule
# ---------------------------------------------------------------------------

def check_doctor_schedule(specialty: str, date: str) -> str:
    """
    Tra cứu lịch khám còn trống của các bác sĩ theo chuyên khoa và ngày.

    Purpose:
        Dùng khi người dùng muốn biết bác sĩ nào còn slot khám trống
        vào một ngày cụ thể. Không dùng để đặt lịch.

    Args:
        specialty (str): Tên chuyên khoa (Ví dụ: 'Tim mạch', 'Thần kinh',
                         'Nội tổng quát', 'Ngoại')
        date (str): Ngày khám (Ví dụ: 'hôm nay', 'ngày mai', '2026-07-29')

    Returns:
        str: Danh sách bác sĩ và giờ trống, hoặc thông báo lỗi.

    Error Semantics:
        - Chuyên khoa không hợp lệ → trả về chuỗi lỗi gợi ý danh sách hợp lệ
        - Ngày không hợp lệ / không có slot → trả về thông báo tương ứng

    Example:
        Input:  check_doctor_schedule("Tim mạch", "ngày mai")
        Output: "Lịch khám Tim mạch vào ngày mai:\\n
                 - BS. Trần Thị Mai (bs001): 08:00, 10:30, 14:00\\n
                 - BS. Nguyễn Hữu Phúc (bs002): 09:00, 15:30"
    """
    try:
        specialty_key = specialty.lower().strip()
        date_key = date.lower().strip()

        # Kiểm tra ngày không hợp lệ (ví dụ: ngày 32, tháng 13)
        import re
        bad_date_pattern = re.search(r'\b(3[2-9]|[4-9]\d)\s*/\s*(1[3-9]|[2-9]\d)', date)
        if bad_date_pattern:
            return (f"LỖI: Ngày '{date}' không hợp lệ (ngày hoặc tháng ngoài phạm vi). "
                    f"Vui lòng nhập ngày hợp lệ như 'hôm nay', 'ngày mai', hoặc 'YYYY-MM-DD'.")

        if specialty_key not in VALID_SPECIALTIES:
            valid_list = ", ".join(s.title() for s in VALID_SPECIALTIES)
            return (f"LỖI: Không tìm thấy chuyên khoa '{specialty}'. "
                    f"Các chuyên khoa hợp lệ gồm: {valid_list}.")

        doctors = DOCTOR_SCHEDULE_DB[specialty_key]
        result_lines = [f"📅 Lịch khám {specialty.title()} vào {date}:"]
        found_any_slot = False

        for doc_id, info in doctors.items():
            slots = info["slots"].get(date_key, [])
            if slots:
                found_any_slot = True
                slot_str = ", ".join(slots)
                result_lines.append(f"  - {info['name']} ({doc_id}): {slot_str}")
            else:
                result_lines.append(f"  - {info['name']} ({doc_id}): Hết slot / không có lịch ngày này")

        if not found_any_slot:
            result_lines.append("  ⚠️ Hiện không có bác sĩ nào còn slot vào ngày này.")

        return "\n".join(result_lines)

    except Exception as e:
        return f"LỖI hệ thống khi tra cứu lịch bác sĩ: {str(e)}"


# ---------------------------------------------------------------------------
# 🛠️ TOOL 2: get_symptom_advice
# ---------------------------------------------------------------------------

def get_symptom_advice(symptoms: str) -> str:
    """
    Phân tích triệu chứng và gợi ý chuyên khoa phù hợp nhất.

    Purpose:
        Dùng khi người dùng mô tả triệu chứng và chưa biết nên gặp
        bác sĩ chuyên khoa nào. Tool này giúp định hướng trước khi
        gọi check_doctor_schedule hoặc book_appointment.

    Args:
        symptoms (str): Mô tả triệu chứng tự do
                        (Ví dụ: 'đau đầu, chóng mặt, buồn nôn')

    Returns:
        str: Gợi ý chuyên khoa kèm giải thích, hoặc thông báo cần khám tổng quát.

    Error Semantics:
        - Symptoms rỗng → gợi ý khám nội tổng quát
        - Không nhận ra triệu chứng nào → gợi ý khám nội tổng quát

    Example:
        Input:  get_symptom_advice("đau đầu, chóng mặt, buồn nôn")
        Output: "Dựa trên triệu chứng: đau đầu, chóng mặt, buồn nôn\\n
                 → Chuyên khoa gợi ý: Thần kinh (2/3 triệu chứng khớp)\\n
                 Lý do: Đau đầu và chóng mặt thường liên quan đến hệ thần kinh."
    """
    try:
        symptoms_lower = symptoms.lower().strip()
        if not symptoms_lower:
            return ("ℹ️ Không có triệu chứng cụ thể. "
                    "Gợi ý: Hãy đến Khoa Nội tổng quát để khám tổng quát.")

        # Đếm triệu chứng khớp theo từng chuyên khoa
        specialty_count = {}
        matched_symptoms = {}

        for symptom_key, specialty in SYMPTOM_TO_SPECIALTY.items():
            if symptom_key in symptoms_lower:
                specialty_count[specialty] = specialty_count.get(specialty, 0) + 1
                if specialty not in matched_symptoms:
                    matched_symptoms[specialty] = []
                matched_symptoms[specialty].append(symptom_key)

        if not specialty_count:
            return (f"ℹ️ Không nhận diện được triệu chứng cụ thể từ mô tả: '{symptoms}'.\n"
                    f"Gợi ý: Hãy đến Khoa Nội tổng quát để được bác sĩ khám và tư vấn ban đầu.")

        # Chọn chuyên khoa có nhiều triệu chứng khớp nhất
        best_specialty = max(specialty_count, key=specialty_count.get)
        count = specialty_count[best_specialty]
        matched = ", ".join(matched_symptoms[best_specialty])
        total = len([s for s in symptoms.split(",") if s.strip()])

        lines = [
            f"🔍 Phân tích triệu chứng: '{symptoms}'",
            f"→ Chuyên khoa gợi ý: **{best_specialty}** ({count} triệu chứng khớp: {matched})",
            f"💡 Lý do: Các triệu chứng {matched} thường liên quan đến khoa {best_specialty}.",
        ]

        if len(specialty_count) > 1:
            others = [f"{sp} ({cnt})" for sp, cnt in specialty_count.items() if sp != best_specialty]
            lines.append(f"📌 Cũng có thể liên quan: {', '.join(others)}")

        return "\n".join(lines)

    except Exception as e:
        return f"LỖI hệ thống khi phân tích triệu chứng: {str(e)}"


# ---------------------------------------------------------------------------
# 🛠️ TOOL 3: book_appointment
# ---------------------------------------------------------------------------

def book_appointment(patient_name: str, specialty: str, date: str, time: str = "08:00") -> str:
    """
    Đặt lịch hẹn khám bệnh cho bệnh nhân với bác sĩ chuyên khoa.

    Purpose:
        Dùng sau khi đã xác định chuyên khoa (qua get_symptom_advice)
        và kiểm tra slot trống (qua check_doctor_schedule). Có side-effect:
        ghi nhận lịch hẹn vào hệ thống và tiêu thụ slot của bác sĩ.

    Args:
        patient_name (str): Họ tên đầy đủ của bệnh nhân
                            (Ví dụ: 'Nguyễn Văn An')
        specialty (str): Chuyên khoa cần khám
                         (Ví dụ: 'Tim mạch', 'Thần kinh')
        date (str): Ngày khám (Ví dụ: 'hôm nay', 'ngày mai')
        time (str): Giờ khám mong muốn (Mặc định: '08:00')
                    (Ví dụ: '14:00', '10:30')

    Returns:
        str: Xác nhận lịch hẹn thành công kèm mã đặt lịch, hoặc thông báo lỗi.

    Error Semantics:
        - Tên bệnh nhân rỗng → lỗi yêu cầu nhập tên
        - Chuyên khoa không tồn tại → lỗi gợi ý danh sách hợp lệ
        - Không còn slot / giờ đã đầy → thông báo và gợi ý giờ khác
        - Ngày không hợp lệ → thông báo lỗi ngày

    Side Effect:
        Ghi nhận lịch hẹn, tiêu thụ slot thời gian của bác sĩ.

    Example:
        Input:  book_appointment("Nguyễn Văn An", "Thần kinh", "hôm nay", "14:00")
        Output: "✅ ĐẶT LỊCH THÀNH CÔNG!\\n
                 📋 Mã lịch hẹn: APT-1001\\n
                 👤 Bệnh nhân: Nguyễn Văn An\\n
                 🏥 Chuyên khoa: Thần kinh\\n
                 👨‍⚕️ Bác sĩ: BS. Lê Minh Khoa\\n
                 📅 Thời gian: hôm nay lúc 14:00"
    """
    try:
        # Kiểm tra tên bệnh nhân
        if not patient_name or not patient_name.strip():
            return "LỖI: Tên bệnh nhân không được để trống. Vui lòng cung cấp họ và tên đầy đủ."

        # Kiểm tra ngày không hợp lệ
        import re
        bad_date_pattern = re.search(r'\b(3[2-9]|[4-9]\d)\s*/\s*(1[3-9]|[2-9]\d)', date)
        if bad_date_pattern:
            return (f"LỖI: Ngày '{date}' không hợp lệ. "
                    f"Vui lòng nhập ngày hợp lệ như 'hôm nay' hoặc 'ngày mai'.")

        specialty_key = specialty.lower().strip()
        date_key = date.lower().strip()

        if specialty_key not in VALID_SPECIALTIES:
            valid_list = ", ".join(s.title() for s in VALID_SPECIALTIES)
            return (f"LỖI: Không tìm thấy chuyên khoa '{specialty}'. "
                    f"Các chuyên khoa hợp lệ gồm: {valid_list}.")

        doctors = DOCTOR_SCHEDULE_DB[specialty_key]

        # Tìm bác sĩ có slot trùng với giờ yêu cầu
        assigned_doctor = None
        assigned_time = None

        for doc_id, info in doctors.items():
            slots = info["slots"].get(date_key, [])
            if time in slots:
                assigned_doctor = info
                assigned_doctor["id"] = doc_id
                assigned_time = time
                # Tiêu thụ slot (xóa khỏi danh sách)
                info["slots"][date_key].remove(time)
                break

        # Nếu giờ yêu cầu không có, tìm slot đầu tiên còn trống
        if not assigned_doctor:
            for doc_id, info in doctors.items():
                slots = info["slots"].get(date_key, [])
                if slots:
                    assigned_doctor = info
                    assigned_doctor["id"] = doc_id
                    assigned_time = slots[0]
                    info["slots"][date_key].pop(0)
                    break

        if not assigned_doctor:
            return (f"LỖI: Không còn slot trống nào tại Khoa {specialty.title()} "
                    f"vào {date}. Vui lòng chọn ngày khác hoặc gọi check_doctor_schedule "
                    f"để xem lịch các ngày khác.")

        # Tạo mã lịch hẹn
        apt_id = f"APT-{_appointment_counter['value']}"
        _appointment_counter["value"] += 1

        return (
            f"✅ ĐẶT LỊCH THÀNH CÔNG!\n"
            f"📋 Mã lịch hẹn: {apt_id}\n"
            f"👤 Bệnh nhân: {patient_name.strip()}\n"
            f"🏥 Chuyên khoa: {specialty.title()}\n"
            f"👨‍⚕️ Bác sĩ phụ trách: {assigned_doctor['name']}\n"
            f"📅 Thời gian: {date} lúc {assigned_time}\n"
            f"📌 Lưu ý: Vui lòng có mặt trước 15 phút và mang theo CCCD + thẻ BHYT."
        )

    except Exception as e:
        return f"LỖI hệ thống khi đặt lịch: {str(e)}"


# ---------------------------------------------------------------------------
# 🛠️ TOOL 4: cancel_appointment
# ---------------------------------------------------------------------------

def cancel_appointment(appointment_id: str) -> str:
    """
    Hủy lịch hẹn khám bệnh đã đặt theo mã lịch hẹn.

    Purpose:
        Dùng khi người dùng muốn hủy một lịch hẹn đã được xác nhận trước đó.
        Có side-effect: giải phóng lại slot thời gian của bác sĩ.

    Args:
        appointment_id (str): Mã lịch hẹn cần hủy
                              (Ví dụ: 'APT-1001', 'APT-1002')

    Returns:
        str: Xác nhận hủy thành công, hoặc thông báo lỗi nếu không tìm thấy mã.

    Error Semantics:
        - Mã lịch hẹn rỗng → lỗi yêu cầu nhập mã
        - Mã không đúng định dạng → thông báo định dạng đúng
        - Mã không tồn tại trong hệ thống → thông báo không tìm thấy

    Side Effect:
        Hủy lịch hẹn và giải phóng slot thời gian bác sĩ (giả lập).

    Example:
        Input:  cancel_appointment("APT-1001")
        Output: "✅ Đã hủy lịch hẹn APT-1001 thành công.\\n
                 Slot thời gian đã được giải phóng."
    """
    try:
        if not appointment_id or not appointment_id.strip():
            return "LỖI: Mã lịch hẹn không được để trống. Ví dụ mã hợp lệ: APT-1001"

        apt_id = appointment_id.strip().upper()

        if not apt_id.startswith("APT-"):
            return (f"LỖI: Mã lịch hẹn '{appointment_id}' không đúng định dạng. "
                    f"Định dạng hợp lệ: APT-XXXX (Ví dụ: APT-1001).")

        # Kiểm tra mã hợp lệ (đơn giản hóa: chỉ kiểm tra range hợp lệ)
        try:
            apt_num = int(apt_id.replace("APT-", ""))
        except ValueError:
            return f"LỖI: Mã lịch hẹn '{appointment_id}' không hợp lệ."

        if apt_num >= _appointment_counter["value"]:
            return (f"LỖI: Không tìm thấy lịch hẹn '{apt_id}' trong hệ thống. "
                    f"Vui lòng kiểm tra lại mã lịch hẹn.")

        return (
            f"✅ Đã hủy lịch hẹn {apt_id} thành công.\n"
            f"🔓 Slot thời gian đã được giải phóng cho bệnh nhân khác.\n"
            f"📩 Thông báo hủy lịch sẽ được gửi qua số điện thoại đã đăng ký."
        )

    except Exception as e:
        return f"LỖI hệ thống khi hủy lịch: {str(e)}"


# ---------------------------------------------------------------------------
# 📋 TOOL REGISTRY - Đăng ký tất cả tools để Agent sử dụng
# ---------------------------------------------------------------------------

AVAILABLE_TOOLS = {
    "check_doctor_schedule": check_doctor_schedule,
    "get_symptom_advice":    get_symptom_advice,
    "book_appointment":      book_appointment,
    "cancel_appointment":    cancel_appointment,
}
