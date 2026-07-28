"""
🧪 TEST TOOL ĐỘC LẬP (Bước 3 — trước khi gắn vào Agent)
Mục đích: loại bỏ hoàn toàn "tool sai" khỏi danh sách nghi phạm khi Agent chạy lỗi.
Chạy: python tests/test_tools.py     (không cần API key, không gọi LLM)
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tools import (
    AVAILABLE_TOOLS,
    INTERVIEW_SLOTS,
    check_calendar_availability,
    reset_calendar,
    schedule_interview,
    screen_resume,
)

_PASSED = 0
_FAILED = []


def check(name: str, condition: bool, detail: str = ""):
    global _PASSED
    if condition:
        _PASSED += 1
        print(f"  ✅ {name}")
    else:
        _FAILED.append(name)
        print(f"  ❌ {name}  {detail}")


def no_crash(name: str, fn, *args, **kwargs):
    """Gọi tool với tham số xấu — yêu cầu KHÔNG raise exception, và trả về chuỗi."""
    try:
        result = fn(*args, **kwargs)
        check(f"{name} (không crash)", isinstance(result, str), f"-> trả về {type(result)}")
        return result
    except Exception as e:
        check(f"{name} (không crash)", False, f"-> RAISE {type(e).__name__}: {e}")
        return ""


# Ngày tính động theo hôm nay để test không bị "hỏng" theo thời gian
FUTURE = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
PAST = (date.today() - timedelta(days=30)).strftime("%d/%m/%Y")

RESUME_FIT = (
    "Nguyễn Văn A - Email: nguyenvana@gmail.com\n"
    "3 năm kinh nghiệm Backend Developer: Python, Django, PostgreSQL, Docker, REST API, Git."
)
JD_BACKEND = (
    "Công ty ABC tuyển Backend Developer - Liên hệ: hr@abc.com\n"
    "Yêu cầu: Python, Django, PostgreSQL, Docker, REST API, Git."
)
RESUME_UNFIT = "Trần Thị B - Email: tranthib@gmail.com\nMới tốt nghiệp ngành Kế toán, thạo Excel và Word."

print("=" * 68)
print("TOOL 1/3 — screen_resume")
print("=" * 68)

reset_calendar()

out = screen_resume(RESUME_FIT, JD_BACKEND)
check("CV khớp JD -> kết luận ĐẠT", "Kết luận: ĐẠT" in out, f"-> {out!r}")
check("trích đúng email ứng viên từ CV", "nguyenvana@gmail.com" in out)
check("trích đúng email HR từ JD", "hr@abc.com" in out)

out = screen_resume(RESUME_UNFIT, JD_BACKEND)
check("CV không liên quan -> kết luận KHÔNG ĐẠT", "Kết luận: KHÔNG ĐẠT" in out, f"-> {out!r}")

out = screen_resume("Nguyễn Văn C - không có email nào ở đây", JD_BACKEND)
check("CV thiếu email -> báo không tìm thấy, không crash", "(không tìm thấy email)" in out)

# --- Error semantics: đầu vào rỗng/thiếu ---
out = no_crash("screen_resume(CV rỗng)", screen_resume, "", JD_BACKEND)
check("CV rỗng -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("screen_resume(JD rỗng)", screen_resume, RESUME_FIT, "   ")
check("JD rỗng -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("screen_resume(None, None)", screen_resume, None, None)
check("CV/JD = None -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")


print()
print("=" * 68)
print("TOOL 2/3 — check_calendar_availability")
print("=" * 68)

reset_calendar()

out = check_calendar_availability(FUTURE)
check("ngày tương lai còn trống -> liệt kê đủ 6 khung giờ", all(s in out for s in INTERVIEW_SLOTS), f"-> {out!r}")

out = no_crash("check_calendar(sai định dạng '32/13/2026')", check_calendar_availability, "32/13/2026")
check("ngày không tồn tại trên dương lịch -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("check_calendar('ngày mai')", check_calendar_availability, "ngày mai")
check("ngày sai định dạng chữ -> LỖI kèm gợi ý dd/mm/yyyy", out.startswith("LỖI:") and "dd/mm/yyyy" in out, f"-> {out!r}")

out = no_crash("check_calendar(rỗng)", check_calendar_availability, "")
check("ngày rỗng -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("check_calendar(None)", check_calendar_availability, None)
check("ngày None -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("check_calendar(ngày quá khứ)", check_calendar_availability, PAST)
check("ngày quá khứ -> LỖI", out.startswith("LỖI:") and "quá khứ" in out, f"-> {out!r}")


print()
print("=" * 68)
print("TOOL 3/3 — schedule_interview")
print("=" * 68)

reset_calendar()

out = schedule_interview("Nguyễn Văn A", FUTURE, "14:00")
check("đặt lịch hợp lệ -> xác nhận thành công", out.startswith("Đã đặt lịch"), f"-> {out!r}")

out = no_crash("schedule(trùng giờ đã đặt)", schedule_interview, "Trần Thị B", FUTURE, "14:00")
check("double-booking bị chặn -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = check_calendar_availability(FUTURE)
check("side effect đúng: 14:00 biến mất khỏi danh sách trống", "14:00" not in out, f"-> {out!r}")

out = no_crash("schedule(giờ không hợp lệ '23:00')", schedule_interview, "Lê Văn C", FUTURE, "23:00")
check("giờ ngoài khung làm việc -> LỖI kèm danh sách giờ hợp lệ", out.startswith("LỖI:") and "09:00" in out, f"-> {out!r}")

out = no_crash("schedule(thiếu tên)", schedule_interview, "", FUTURE, "10:00")
check("thiếu tên ứng viên -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("schedule(ngày sai định dạng)", schedule_interview, "Lê Văn C", "5-8-2026", "10:00")
check("ngày sai định dạng -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("schedule(ngày quá khứ)", schedule_interview, "Lê Văn C", PAST, "10:00")
check("ngày quá khứ -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

out = no_crash("schedule(None, None, None)", schedule_interview, None, None, None)
check("tất cả tham số None -> LỖI", out.startswith("LỖI:"), f"-> {out!r}")

# Kín lịch: đặt hết 6 khung giờ rồi kiểm tra
reset_calendar()
for i, slot in enumerate(INTERVIEW_SLOTS):
    schedule_interview(f"Ứng viên {i}", FUTURE, slot)
out = check_calendar_availability(FUTURE)
check("đặt hết 6 khung giờ -> ngày kín lịch trả LỖI", out.startswith("LỖI:") and "kín lịch" in out, f"-> {out!r}")


print()
print("=" * 68)
print("REGISTRY — AVAILABLE_TOOLS")
print("=" * 68)

check("đăng ký đúng 3 tool", len(AVAILABLE_TOOLS) == 3, f"-> {list(AVAILABLE_TOOLS)}")
for tool_name in ("screen_resume", "check_calendar_availability", "schedule_interview"):
    check(f"'{tool_name}' có trong AVAILABLE_TOOLS", tool_name in AVAILABLE_TOOLS)
check("mọi tool đều callable", all(callable(f) for f in AVAILABLE_TOOLS.values()))
check("mọi tool đều có docstring contract", all((f.__doc__ or "").find("TOOL CONTRACT") != -1 for f in AVAILABLE_TOOLS.values()))

reset_calendar()

print()
print("=" * 68)
if _FAILED:
    print(f"❌ KẾT QUẢ: {_PASSED} pass / {len(_FAILED)} FAIL")
    for name in _FAILED:
        print(f"   - FAIL: {name}")
    sys.exit(1)
else:
    print(f"✅ KẾT QUẢ: {_PASSED}/{_PASSED} test PASS (100%) — tool sẵn sàng gắn vào Agent.")
print("=" * 68)
