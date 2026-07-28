"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Trợ Lý Duyệt Chi Phí Doanh Nghiệp

Mỗi tool tuân contract: Name | Purpose | Input | Output | Error | Side effect | Example | Safety

Ghi chú kiến trúc:
- Tất cả state (ngân sách đã chi, các request đã nộp) được lưu trong bộ nhớ (in-memory)
  qua các dict module-level bên dưới, để các tool liên kết đúng logic nghiệp vụ với nhau
  (vd: submit_expense_request tạo ra 1 request thì check_approval_status phải tra được
  chính request đó, và check_budget_remaining phải phản ánh đúng số đã chi).
- Không tool nào được phép raise Exception ra ngoài — luôn trả về chuỗi "LỖI: ..." để
  Agent đọc được và tự quyết định bước tiếp theo (không cho crash chương trình).
"""

from __future__ import annotations

from typing import Callable

# ============================================================
# STATE NỘI BỘ (in-memory, dùng chung giữa các tool)
# ============================================================

_VALID_CATEGORIES = {"di_lai", "an_uong", "van_phong_pham", "dao_tao", "phan_mem"}
_VALID_DEPARTMENTS = {"marketing", "it", "hr"}

_CATEGORY_LIMITS = {
    "di_lai": 20_000_000,
    "an_uong": 3_000_000,
    "van_phong_pham": 2_000_000,
    "dao_tao": 30_000_000,
    "phan_mem": 50_000_000,
}

_DEPARTMENT_BUDGET_LIMITS = {
    "marketing": 100_000_000,
    "it": 200_000_000,
    "hr": 80_000_000,
}

# Ngân sách đã chi lũy kế theo phòng ban — sẽ bị trừ dần khi có request approved.
_DEPARTMENT_SPENT: dict[str, int] = {
    "marketing": 50_000_000,
    "it": 80_000_000,
    "hr": 45_000_000,
}

_POLICY_MAP = {
    "di_lai": "Quy định công tác: tối đa 20.000.000 VND/lần, cần hóa đơn và lịch trình.",
    "an_uong": "Quy định tiếp khách: tối đa 3.000.000 VND/bữa, ghi rõ mục đích.",
    "van_phong_pham": "Quy định văn phòng phẩm: tối đa 2.000.000 VND/lần.",
    "dao_tao": "Quy định đào tạo: tối đa 30.000.000 VND/khóa, cần duyệt HR.",
    "phan_mem": "Quy định phần mềm: tối đa 50.000.000 VND/năm/gói.",
}

# Mức hoàn tiền đi lại cá nhân theo km — tách riêng khỏi hạn mức "di_lai" (công tác trọn gói).
_MILEAGE_RATE_PER_KM = 5_000  # VND/km

# Danh sách request — bắt đầu với dữ liệu mẫu có sẵn, sau đó submit_expense_request
# sẽ append thêm và tự sinh mã tăng dần (REQ003, REQ004, ...).
_REQUESTS: dict[str, dict] = {
    "REQ001": {
        "status": "approved",
        "amount": 4_500_000,
        "category": "di_lai",
        "employee_id": "NV001",
        "description": "Công tác HCM",
    },
    "REQ002": {
        "status": "pending",
        "amount": 2_800_000,
        "category": "an_uong",
        "employee_id": "NV001",
        "description": "Tiếp khách quý 3",
    },
}
_REQUEST_COUNTER = 2  # đã có REQ001, REQ002 -> request kế tiếp là REQ003

_AUDIT_TRAIL: list[str] = []
_ESCALATION_COUNTER = 0


def _next_request_id() -> str:
    global _REQUEST_COUNTER
    _REQUEST_COUNTER += 1
    return f"REQ{_REQUEST_COUNTER:03d}"


def _next_escalation_id() -> str:
    global _ESCALATION_COUNTER
    _ESCALATION_COUNTER += 1
    return f"ESC{_ESCALATION_COUNTER:03d}"


def _format_vnd(value: int) -> str:
    return f"{value:,} VND".replace(",", ".")


def _parse_amount(amount: str | int | float) -> int | None:
    """Chuẩn hóa số tiền về int dương; trả None nếu không hợp lệ."""
    if isinstance(amount, bool):
        return None
    if isinstance(amount, (int, float)):
        return int(amount) if amount > 0 else None
    text = (
        str(amount)
        .strip()
        .lower()
        .replace(".", "")
        .replace(",", "")
        .replace("vnđ", "")
        .replace("vnd", "")
    )
    return int(text) if text.isdigit() and int(text) > 0 else None


# ============================================================
# TOOL 1 — Tra cứu chính sách
# ============================================================

def get_expense_policy(category: str = "", department: str = "") -> str:
    """
    Tool: get_expense_policy
    Mô tả: Tra cứu quy định/chính sách chi phí nội bộ theo danh mục hoặc phòng ban.

    Khi nào dùng: Người dùng hỏi hạn mức, quy định trước khi nộp/duyệt chi phí.
    Khi nào KHÔNG dùng: Chỉ cần số dư ngân sách → dùng check_budget_remaining.

    Input:
      category (str, optional) - Danh mục chi phí (di_lai, an_uong, van_phong_pham, dao_tao, phan_mem).
      department (str, optional) - Phòng ban (marketing, it, hr).

    Output: str - Nội dung quy định áp dụng.
    Error semantics: Danh mục/phòng ban không hợp lệ → trả "LỖI: ...", không crash.
    Side effect: Read-only.

    Example:
      Input: get_expense_policy("di_lai", "marketing")
      Output: "Quy định công tác: tối đa 20.000.000 VND/lần, cần hóa đơn..."
    """
    try:
        category = str(category or "").strip().lower()
        department = str(department or "").strip().lower()

        if category and category not in _VALID_CATEGORIES:
            return (
                f"LỖI: Danh mục '{category}' không hợp lệ. "
                f"Danh mục hợp lệ: {', '.join(sorted(_VALID_CATEGORIES))}."
            )

        if department and department not in _VALID_DEPARTMENTS:
            return (
                f"LỖI: Phòng ban '{department}' không hợp lệ. "
                f"Phòng ban hợp lệ: {', '.join(sorted(_VALID_DEPARTMENTS))}."
            )

        if category:
            return _POLICY_MAP[category]
        return (
            "Quy định chung: mọi chi phí phải có mục đích công việc rõ ràng. "
            "Chi phí vượt 50% ngân sách còn lại cần duyệt cấp Giám đốc."
        )
    except Exception as exc:
        return f"LỖI: Không thể tra cứu chính sách — {exc}"


# ============================================================
# TOOL 2 — Ngân sách còn lại
# ============================================================

def check_budget_remaining(department: str = "marketing") -> str:
    """
    Tool: check_budget_remaining
    Mô tả: Kiểm tra số dư ngân sách còn lại của phòng ban (đã trừ các chi phí approved).

    Input: department (str, optional) - Tên phòng ban.
    Output: str - Số dư ngân sách còn lại.
    Error semantics: Phòng ban rỗng hoặc không hợp lệ → "LỖI: ...".
    Side effect: Read-only.

    Example:
      Input: check_budget_remaining("marketing")
      Output: "Số dư ngân sách phòng marketing còn lại: 50.000.000 VND (đã chi 50.000.000/100.000.000 VND)."
    """
    try:
        department = str(department or "").strip().lower()
        if not department:
            return "LỖI: Thiếu tên phòng ban."
        if department not in _DEPARTMENT_BUDGET_LIMITS:
            return f"LỖI: Phòng ban '{department}' không tồn tại."

        limit = _DEPARTMENT_BUDGET_LIMITS[department]
        spent = _DEPARTMENT_SPENT.get(department, 0)
        remaining = max(limit - spent, 0)

        return (
            f"Số dư ngân sách phòng {department} còn lại: {_format_vnd(remaining)} "
            f"(đã chi {_format_vnd(spent)}/{_format_vnd(limit)})."
        )
    except Exception as exc:
        return f"LỖI: Không thể kiểm tra ngân sách — {exc}"


# ============================================================
# TOOL 3 — Hạn mức ngân sách tối đa
# ============================================================

def check_budget_limit(department: str = "marketing") -> str:
    """
    Tool: check_budget_limit
    Mô tả: Kiểm tra hạn mức ngân sách tối đa (tổng, không phải số dư) của phòng ban.

    Input: department (str, optional) - Tên phòng ban.
    Output: str - Hạn mức ngân sách tối đa.
    Error semantics: Phòng ban không hợp lệ → "LỖI: ...".
    Side effect: Read-only.

    Example:
      Input: check_budget_limit("it")
      Output: "Hạn mức ngân sách tối đa phòng it: 200.000.000 VND."
    """
    try:
        department = str(department or "").strip().lower()
        if not department:
            return "LỖI: Thiếu tên phòng ban."
        if department not in _DEPARTMENT_BUDGET_LIMITS:
            return f"LỖI: Phòng ban '{department}' không tồn tại."

        limit = _DEPARTMENT_BUDGET_LIMITS[department]
        return f"Hạn mức ngân sách tối đa phòng {department}: {_format_vnd(limit)}."
    except Exception as exc:
        return f"LỖI: Không thể kiểm tra hạn mức — {exc}"


# ============================================================
# TOOL 4 — Tính hoàn tiền đi lại theo km (bổ sung, còn thiếu trong bản gốc)
# ============================================================

def calculate_mileage_reimbursement(distance_km: str | int | float) -> str:
    """
    Tool: calculate_mileage_reimbursement
    Mô tả: Tính số tiền hoàn trả cho việc dùng phương tiện cá nhân đi công tác,
           theo mức cố định VND/km (khác với hạn mức "di_lai" trọn gói).

    Khi nào dùng: Người dùng khai báo quãng đường đã di chuyển, cần tính tiền hoàn.
    Khi nào KHÔNG dùng: Chi phí công tác trọn gói (vé máy bay, khách sạn) → dùng get_expense_policy.

    Input:
      distance_km (str|int|float, required) - Quãng đường di chuyển, đơn vị km.

    Output: str - Số tiền hoàn trả, kèm mức áp dụng.
    Error semantics: distance_km <= 0 hoặc không phải số → "LỖI: ...".
    Side effect: Read-only.

    Example:
      Input: calculate_mileage_reimbursement(120)
      Output: "Quãng đường 120 km × 5.000 VND/km = 600.000 VND."
    """
    try:
        parsed = _parse_amount(distance_km)
        if parsed is None:
            return f"LỖI: Quãng đường '{distance_km}' không hợp lệ (phải là số dương)."

        total = parsed * _MILEAGE_RATE_PER_KM
        return (
            f"Quãng đường {parsed} km × {_format_vnd(_MILEAGE_RATE_PER_KM)}/km "
            f"= {_format_vnd(total)}."
        )
    except Exception as exc:
        return f"LỖI: Không thể tính hoàn tiền đi lại — {exc}"


# ============================================================
# TOOL 5 — Validate yêu cầu chi phí
# ============================================================

def validate_expense_request(
    amount: str | int | float,
    category: str,
    employee_id: str,
    description: str = "",
) -> str:
    """
    Tool: validate_expense_request
    Mô tả: Kiểm tra yêu cầu chi phí có hợp lệ theo chính sách (không kiểm tra ngân sách phòng ban).

    Khi nào dùng: Bước bắt buộc trước submit_expense_request.

    Input:
      amount (str|int|float, required) - Số tiền yêu cầu.
      category (str, required) - Danh mục chi phí.
      employee_id (str, required) - Mã nhân viên (vd: NV001).
      description (str, optional) - Mô tả/mục đích chi phí.

    Output: str - "HỢP LỆ: ..." hoặc "KHÔNG HỢP LỆ: ...".
    Error semantics: Thiếu tham số, amount <= 0, category sai → KHÔNG HỢP LỆ (không raise).
    Side effect: Read-only.

    Example:
      Input: validate_expense_request(4500000, "di_lai", "NV001", "Công tác HCM")
      Output: "HỢP LỆ: Yêu cầu đáp ứng chính sách. Có thể gọi submit_expense_request."
    """
    try:
        parsed_amount = _parse_amount(amount)
        if parsed_amount is None:
            return f"KHÔNG HỢP LỆ: Số tiền '{amount}' không hợp lệ."

        category = str(category or "").strip().lower()
        employee_id = str(employee_id or "").strip().upper()
        description = str(description or "").strip()

        if not employee_id:
            return "KHÔNG HỢP LỆ: Thiếu mã nhân viên. Dùng request_clarification."
        if not description:
            return "KHÔNG HỢP LỆ: Thiếu mô tả chi phí. Dùng request_clarification."
        if category not in _VALID_CATEGORIES:
            return f"KHÔNG HỢP LỆ: Danh mục '{category}' không hợp lệ."

        if parsed_amount > _CATEGORY_LIMITS[category]:
            return (
                f"KHÔNG HỢP LỆ: Vượt hạn mức danh mục "
                f"(tối đa {_format_vnd(_CATEGORY_LIMITS[category])})."
            )

        return "HỢP LỆ: Yêu cầu đáp ứng chính sách. Có thể gọi submit_expense_request."
    except Exception as exc:
        return f"LỖI: Không thể validate yêu cầu — {exc}"


# ============================================================
# TOOL 6 — Nộp yêu cầu chi phí
# ============================================================

def submit_expense_request(
    amount: str | int | float,
    category: str,
    employee_id: str,
    description: str = "",
    department: str = "",
) -> str:
    """
    Tool: submit_expense_request
    Mô tả: Nộp yêu cầu chi phí vào hệ thống sau khi đã validate. Tự sinh mã request
           tăng dần (REQ003, REQ004, ...), lưu vào hệ thống để check_approval_status
           và check_request_history tra cứu được ngay.

    Input:
      amount (str|int|float, required) - Số tiền yêu cầu.
      category (str, required) - Danh mục chi phí.
      employee_id (str, required) - Mã nhân viên.
      description (str, optional) - Mô tả/mục đích chi phí.
      department (str, optional) - Phòng ban chịu chi phí, dùng để trừ ngân sách nếu auto-approve.

    Output: str - Mã yêu cầu và trạng thái (pending/approved).
    Error semantics: Validate thất bại → không tạo yêu cầu, trả "KHÔNG THỂ NỘP: ...".
    Side effect: Write — tạo yêu cầu mới, có thể trừ ngân sách phòng ban nếu auto-approve.

    Example:
      Input: submit_expense_request(1500000, "van_phong_pham", "NV001", "Mua giấy in", "it")
      Output: "Đã tạo REQ003 | Trạng thái: approved (tự duyệt) | Nhân viên: NV001 | Số tiền: 1.500.000 VND."
    """
    try:
        validation = validate_expense_request(amount, category, employee_id, description)
        if not validation.startswith("HỢP LỆ"):
            return f"KHÔNG THỂ NỘP: {validation}"

        parsed_amount = _parse_amount(amount)
        category = str(category).strip().lower()
        employee_id = str(employee_id).strip().upper()
        description = str(description or "").strip()
        department = str(department or "").strip().lower()

        request_id = _next_request_id()
        auto_approve = parsed_amount is not None and parsed_amount <= 5_000_000
        status = "approved" if auto_approve else "pending"

        _REQUESTS[request_id] = {
            "status": status,
            "amount": parsed_amount,
            "category": category,
            "employee_id": employee_id,
            "description": description,
        }

        if auto_approve:
            if department in _DEPARTMENT_SPENT:
                _DEPARTMENT_SPENT[department] += parsed_amount
            audit_log("Auto-approve expense", f"{employee_id} — {parsed_amount} VND — {request_id}")
            return (
                f"Đã tạo {request_id} | Trạng thái: approved (tự duyệt) | "
                f"Nhân viên: {employee_id} | Số tiền: {_format_vnd(parsed_amount)}."
            )

        audit_log("Submit expense", f"{employee_id} — {request_id} — chờ duyệt")
        return (
            f"Đã tạo {request_id} | Trạng thái: pending | "
            f"Chờ Trưởng phòng duyệt | Nhân viên: {employee_id} | "
            f"Số tiền: {_format_vnd(parsed_amount)}."
        )
    except Exception as exc:
        return f"LỖI: Không thể nộp yêu cầu — {exc}"


# ============================================================
# TOOL 7 — Tra cứu trạng thái duyệt
# ============================================================

def check_approval_status(request_id: str) -> str:
    """
    Tool: check_approval_status
    Mô tả: Tra cứu trạng thái duyệt của một yêu cầu chi phí (bao gồm cả request
           vừa được submit_expense_request tạo ra trong phiên hiện tại).

    Input: request_id (str, required) - Mã yêu cầu (vd: REQ001, REQ002, REQ003...).
    Output: str - Trạng thái pending / approved / rejected kèm chi tiết.
    Error semantics: Mã rỗng hoặc không tồn tại → "LỖI: ...".
    Side effect: Read-only.

    Example:
      Input: check_approval_status("REQ002")
      Output: "REQ002 | pending | 2.800.000 VND | an_uong | NV001"
    """
    try:
        request_id = str(request_id or "").strip().upper()
        if not request_id:
            return "LỖI: Thiếu mã yêu cầu (request_id)."
        if request_id not in _REQUESTS:
            return f"LỖI: Không tìm thấy yêu cầu '{request_id}'."

        r = _REQUESTS[request_id]
        return (
            f"{request_id} | {r['status']} | {_format_vnd(r['amount'])} | "
            f"{r['category']} | {r['employee_id']}"
        )
    except Exception as exc:
        return f"LỖI: Không thể tra cứu trạng thái — {exc}"


# ============================================================
# TOOL 8 — Lịch sử yêu cầu theo nhân viên
# ============================================================

def check_request_history(employee_id: str = "") -> str:
    """
    Tool: check_request_history
    Mô tả: Xem lịch sử các yêu cầu chi phí đã thực hiện (bao gồm request mới nộp
           trong phiên hiện tại).

    Input: employee_id (str, optional) - Lọc theo mã nhân viên. Rỗng = xem toàn bộ.
    Output: str - Danh sách yêu cầu và trạng thái.
    Error semantics: employee_id có nhưng không có request nào → "LỖI: ...".
    Side effect: Read-only.

    Example:
      Input: check_request_history("NV001")
      Output: "Lịch sử NV001: REQ001-approved (4.500.000 VND), REQ002-pending (2.800.000 VND)."
    """
    try:
        employee_id = str(employee_id or "").strip().upper()

        if employee_id:
            matches = {
                rid: r for rid, r in _REQUESTS.items() if r["employee_id"] == employee_id
            }
            if not matches:
                return f"LỖI: Không tìm thấy lịch sử cho nhân viên '{employee_id}'."
            items = ", ".join(
                f"{rid}-{r['status']} ({_format_vnd(r['amount'])})"
                for rid, r in matches.items()
            )
            return f"Lịch sử {employee_id}: {items}."

        items = "; ".join(
            f"{rid} — {r['employee_id']} — {r['status']} — {_format_vnd(r['amount'])}"
            for rid, r in _REQUESTS.items()
        )
        return f"Lịch sử yêu cầu: {items}."
    except Exception as exc:
        return f"LỖI: Không thể tra cứu lịch sử — {exc}"


# ============================================================
# TOOL 9 — Chuyển cho con người xử lý
# ============================================================

def escalate_to_human(query: str, priority: str = "normal") -> str:
    """
    Tool: escalate_to_human
    Mô tả: Chuyển case phức tạp/vượt thẩm quyền cho chuyên gia con người.

    Khi nào dùng: Vượt hạn mức duyệt, tranh chấp chính sách, Guardrail sắp kích hoạt.

    Input:
      query (str, required) - Tóm tắt vấn đề.
      priority (str, optional) - normal | high | urgent.

    Output: str - Xác nhận ticket escalated.
    Error semantics: query rỗng → "LỖI: ...".
    Side effect: Write — tạo ticket (mã tự tăng), ghi audit log.

    Example:
      Input: escalate_to_human("Yêu cầu 80 triệu vượt hạn mức", "high")
      Output: "Ticket ESC001 | Ưu tiên: high | Chuyên gia sẽ phản hồi trong 4 giờ."
    """
    try:
        query = str(query or "").strip()
        if not query:
            return "LỖI: Thiếu nội dung cần chuyển cho chuyên gia."

        priority = str(priority or "normal").strip().lower()
        if priority not in {"normal", "high", "urgent"}:
            priority = "normal"

        sla = {"normal": 24, "high": 4, "urgent": 1}[priority]
        ticket_id = _next_escalation_id()
        audit_log("Escalate to human", f"{ticket_id} — {query}")
        return (
            f"Ticket {ticket_id} | Ưu tiên: {priority} | "
            f"Chuyên gia đã nhận: '{query}' | Phản hồi dự kiến trong {sla} giờ."
        )
    except Exception as exc:
        return f"LỖI: Không thể escalate — {exc}"


# ============================================================
# TOOL 10 — Yêu cầu làm rõ thông tin
# ============================================================

def request_clarification(query: str, missing_fields: str = "") -> str:
    """
    Tool: request_clarification
    Mô tả: Yêu cầu người dùng bổ sung thông tin còn thiếu hoặc mơ hồ.

    Khi nào dùng: Thiếu amount, category, employee_id, hoặc mô tả chi phí.

    Input:
      query (str, required) - Ngữ cảnh cần làm rõ.
      missing_fields (str, optional) - Các trường thiếu, cách nhau bởi dấu phẩy.

    Output: str - Câu hỏi làm rõ gửi cho người dùng.
    Error semantics: query rỗng → "LỖI: ...".
    Side effect: Read-only.

    Example:
      Input: request_clarification("Duyệt chi phí công tác", "amount, category")
      Output: "Vui lòng cung cấp thêm: amount, category — cho yêu cầu 'Duyệt chi phí công tác'."
    """
    try:
        query = str(query or "").strip()
        if not query:
            return "LỖI: Thiếu ngữ cảnh cần làm rõ."

        fields = str(missing_fields or "").strip()
        if fields:
            return f"Vui lòng cung cấp thêm: {fields} — cho yêu cầu '{query}'."
        return f"Xin vui lòng làm rõ thêm thông tin về: '{query}'."
    except Exception as exc:
        return f"LỖI: Không thể tạo yêu cầu làm rõ — {exc}"


# ============================================================
# TOOL 11 — Ghi audit log
# ============================================================

def audit_log(action: str, details: str = "") -> str:
    """
    Tool: audit_log
    Mô tả: Ghi lại hành động/sự kiện quan trọng phục vụ kiểm toán và trace log.

    Input:
      action (str, required) - Tên hành động.
      details (str, optional) - Chi tiết bổ sung.

    Output: str - Xác nhận đã ghi log.
    Error semantics: action rỗng → "LỖI: ...".
    Side effect: Write — ghi vào audit trail nội bộ (in-memory).

    Example:
      Input: audit_log("Submit REQ003", "NV001 — 1.500.000 VND")
      Output: "Hành động 'Submit REQ003' đã được ghi lại trong hệ thống kiểm toán."
    """
    try:
        action = str(action or "").strip()
        if not action:
            return "LỖI: Thiếu tên hành động cần ghi log."

        details = str(details or "").strip()
        entry = f"{action} — {details}" if details else action
        _AUDIT_TRAIL.append(entry)

        if details:
            return f"Hành động '{action}' ({details}) đã được ghi lại trong hệ thống kiểm toán."
        return f"Hành động '{action}' đã được ghi lại trong hệ thống kiểm toán."
    except Exception as exc:
        return f"LỖI: Không thể ghi audit log — {exc}"


# ============================================================
# TOOL 12 — Gửi thông báo
# ============================================================

def send_notification(recipient: str, message: str, channel: str = "email") -> str:
    """
    Tool: send_notification
    Mô tả: Gửi thông báo cho người dùng khi có sự kiện duyệt/từ chối chi phí.

    Input:
      recipient (str, required) - Người nhận (mã NV hoặc email).
      message (str, required) - Nội dung thông báo.
      channel (str, optional) - email | sms | app.

    Output: str - Xác nhận đã gửi.
    Error semantics: Thiếu recipient/message → "LỖI: ...".
    Side effect: Write — gửi thông báo (stub, không gọi dịch vụ ngoài thật).

    Example:
      Input: send_notification("NV001", "Yêu cầu REQ003 đã được duyệt.")
      Output: "Thông báo đã được gửi qua email tới 'NV001': 'Yêu cầu REQ003 đã được duyệt.'."
    """
    try:
        recipient = str(recipient or "").strip()
        message = str(message or "").strip()
        if not recipient:
            return "LỖI: Thiếu người nhận (recipient)."
        if not message:
            return "LỖI: Thiếu nội dung thông báo (message)."

        channel = str(channel or "email").strip().lower()
        if channel not in {"email", "sms", "app"}:
            channel = "email"

        return f"Thông báo đã được gửi qua {channel} tới '{recipient}': '{message}'."
    except Exception as exc:
        return f"LỖI: Không thể gửi thông báo — {exc}"


# ============================================================
# Danh sách tool đăng ký cho ReAct Agent
# ============================================================

AVAILABLE_TOOLS: dict[str, Callable[..., str]] = {
    "get_expense_policy": get_expense_policy,
    "check_budget_remaining": check_budget_remaining,
    "check_budget_limit": check_budget_limit,
    "calculate_mileage_reimbursement": calculate_mileage_reimbursement,
    "validate_expense_request": validate_expense_request,
    "submit_expense_request": submit_expense_request,
    "check_approval_status": check_approval_status,
    "check_request_history": check_request_history,
    "escalate_to_human": escalate_to_human,
    "request_clarification": request_clarification,
    "audit_log": audit_log,
    "send_notification": send_notification,
}


# ============================================================
# Self-test khi chạy trực tiếp: python src/tools.py
# ============================================================

if __name__ == "__main__":
    print("=== TEST get_expense_policy ===")
    print(get_expense_policy("di_lai", "marketing"))
    print(get_expense_policy("khong_ton_tai"))  # case lỗi

    print("\n=== TEST check_budget_remaining ===")
    print(check_budget_remaining("marketing"))
    print(check_budget_remaining("khong_ton_tai"))  # case lỗi

    print("\n=== TEST check_budget_limit ===")
    print(check_budget_limit("it"))

    print("\n=== TEST calculate_mileage_reimbursement ===")
    print(calculate_mileage_reimbursement(120))
    print(calculate_mileage_reimbursement(-5))  # case lỗi
    print(calculate_mileage_reimbursement("abc"))  # case lỗi

    print("\n=== TEST validate_expense_request ===")
    print(validate_expense_request(4_500_000, "di_lai", "NV001", "Công tác HCM"))
    print(validate_expense_request(999_999_999, "di_lai", "NV001", "Vượt hạn mức"))  # case lỗi

    print("\n=== TEST submit_expense_request (đồng bộ với check_approval_status) ===")
    result = submit_expense_request(1_500_000, "van_phong_pham", "NV001", "Mua giấy in", "it")
    print(result)
    # request_id vừa tạo phải tra được ngay bằng check_approval_status
    new_id = result.split("|")[0].replace("Đã tạo", "").strip()
    print(check_approval_status(new_id))

    print("\n=== TEST check_request_history (phải thấy cả request mới) ===")
    print(check_request_history("NV001"))

    print("\n=== TEST escalate_to_human ===")
    print(escalate_to_human("Yêu cầu 80 triệu vượt hạn mức", "high"))
    print(escalate_to_human(""))  # case lỗi

    print("\n=== TEST request_clarification ===")
    print(request_clarification("Duyệt chi phí công tác", "amount, category"))

    print("\n=== TEST audit_log ===")
    print(audit_log("Test log", "chi tiết mẫu"))

    print("\n=== TEST send_notification ===")
    print(send_notification("NV001", "Yêu cầu REQ003 đã được duyệt."))
    print(send_notification("", "thiếu recipient"))  # case lỗi

    print("\n✅ Tất cả tool chạy xong, không có exception nào crash chương trình.")