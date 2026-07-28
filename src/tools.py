"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Chủ đề: Hệ thống Tuyển dụng Thông minh (JD / CV Matching)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""


def list_jobs() -> str:
    """
    Liệt kê tất cả các vị trí tuyển dụng hiện đang mở (available).

    Không cần tham số đầu vào.

    Returns:
        str: Danh sách các Job với ID, tên vị trí, phòng ban và hạn nộp hồ sơ.
             Trả về thông báo nếu không có job nào đang mở.

    Ví dụ kết quả:
        📋 DANH SÁCH VỊ TRÍ TUYỂN DỤNG ĐANG MỞ:
          [JD001] Backend Engineer (Python) | Phòng: Engineering | Hạn nộp: 2026-08-15 | Số lượng: 2 người
          [JD002] AI/ML Engineer | Phòng: AI Lab | Hạn nộp: 2026-08-30 | Số lượng: 1 người
    """
    # TODO: Implement logic — truy vấn danh sách job đang mở từ DB / file JSON
    raise NotImplementedError


def get_job_description(jd_id: str) -> str:
    """
    Lấy toàn bộ nội dung mô tả công việc (Job Description) theo ID.

    Args:
        jd_id (str): Mã Job Description (Ví dụ: 'JD001', 'JD002').

    Returns:
        str: Chi tiết JD gồm tên vị trí, phòng ban, trạng thái tuyển dụng,
             số lượng cần tuyển, hạn nộp hồ sơ, mức lương, yêu cầu bắt buộc
             và kỹ năng cộng thêm (nice-to-have).
             Trả về thông báo lỗi nếu không tìm thấy jd_id.

    Ví dụ kết quả:
        📄 JD001 — Backend Engineer (Python)
          Phòng ban     : Engineering
          Trạng thái    : Đang tuyển
          Số lượng tuyển: 2 người
          Hạn nộp hồ sơ : 2026-08-15
          Mức lương     : 25 - 40 triệu VNĐ / tháng
          ✅ Yêu cầu bắt buộc: ...
          ⭐ Kỹ năng cộng thêm: ...
    """
    # TODO: Implement logic — tìm jd_id trong DB / file JSON, trả về thông tin chi tiết
    raise NotImplementedError


def get_pending_candidates(jd_id: str) -> str:
    """
    Lấy danh sách ứng viên chưa được xử lý (status='pending') cho một vị trí JD cụ thể.

    Args:
        jd_id (str): Mã Job Description cần xem ứng viên (Ví dụ: 'JD001').

    Returns:
        str: Danh sách ứng viên pending gồm candidate_id, tên, ngày ứng tuyển
             và tóm tắt hồ sơ.
             Trả về thông báo nếu jd_id không tồn tại hoặc không có ứng viên nào pending.

    Ví dụ kết quả:
        👥 Ứng viên đang chờ xử lý cho JD001 (2 người):
          [CV101] Nguyễn Văn An | Nộp: 2026-07-20 | Tóm tắt: 3 năm Python/FastAPI...
          [CV102] Trần Thị Bình | Nộp: 2026-07-21 | Tóm tắt: 1 năm Python...
    """
    # TODO: Implement logic — lọc candidates theo jd_id và status == 'pending'
    raise NotImplementedError


def get_resume_content(candidate_id: str) -> str:
    """
    Đọc và trả về toàn bộ nội dung CV (hồ sơ) của một ứng viên.

    Args:
        candidate_id (str): Mã định danh ứng viên (Ví dụ: 'CV101', 'CV102').

    Returns:
        str: Thông tin chi tiết CV gồm họ tên, email, vị trí ứng tuyển,
             trạng thái hồ sơ, ngày ứng tuyển, số năm kinh nghiệm,
             danh sách kỹ năng và tóm tắt bản thân.
             Trả về thông báo lỗi nếu không tìm thấy candidate_id.

    Ví dụ kết quả:
        📝 CV ỨNG VIÊN — CV101
          Họ tên              : Nguyễn Văn An
          Email               : an.nguyen@email.com
          Ứng tuyển vị trí   : JD001
          Trạng thái hồ sơ   : pending
          Ngày ứng tuyển     : 2026-07-20
          Số năm kinh nghiệm : 3 năm
          Kỹ năng            : Python, FastAPI, PostgreSQL, Docker
          Tóm tắt bản thân  : 3 năm kinh nghiệm Python/FastAPI...
    """
    # TODO: Implement logic — tìm candidate_id trong DB / file JSON, trả về nội dung CV
    raise NotImplementedError


def check_availability(interviewer_id: str, date: str) -> str:
    """
    Kiểm tra lịch trống của người phỏng vấn vào một ngày cụ thể.

    Args:
        interviewer_id (str): Mã người phỏng vấn (Ví dụ: 'IV01', 'IV02').
        date (str): Ngày cần kiểm tra, định dạng 'YYYY-MM-DD' (Ví dụ: '2026-08-05').

    Returns:
        str: Danh sách khung giờ còn trống của người phỏng vấn trong ngày đó.
             Trả về thông báo nếu không có khung giờ nào trống
             hoặc không tìm thấy interviewer_id.

    Ví dụ kết quả:
        📅 Lịch trống của Đinh Văn Đức (Engineering Lead) ngày 2026-08-05:
          - 09:00
          - 14:00
    """
    # TODO: Implement logic — lọc available_slots của interviewer_id theo ngày date
    raise NotImplementedError


def book_interview(candidate_id: str, time_slot: str, interviewer_id: str) -> str:
    """
    Đặt lịch phỏng vấn cho ứng viên với người phỏng vấn tại khung giờ cụ thể.

    ⚠️  HITL REQUIRED (Human-In-The-Loop):
        Hành động này có tác động trực tiếp đến ứng viên (gửi email mời phỏng vấn).
        Agent PHẢI xác nhận với người dùng HR trước khi thực thi.
        Tuyệt đối không được tự động gọi tool này mà không có phê duyệt của HR.

    Sau khi đặt thành công, hệ thống sẽ tự động:
      - Gửi Email mời phỏng vấn tới ứng viên
      - Cập nhật trạng thái ứng viên thành 'interview_scheduled'
      - Xóa khung giờ đó khỏi lịch trống của người phỏng vấn

    Args:
        candidate_id (str): Mã ứng viên cần đặt lịch (Ví dụ: 'CV101').
        time_slot (str): Khung giờ phỏng vấn, định dạng 'YYYY-MM-DD HH:MM'
                         (Ví dụ: '2026-08-05 09:00').
        interviewer_id (str): Mã người phỏng vấn (Ví dụ: 'IV01').

    Returns:
        str: Xác nhận lịch phỏng vấn đã được đặt thành công kèm thông tin tóm tắt.
             Trả về thông báo lỗi nếu ứng viên / người phỏng vấn không tồn tại
             hoặc khung giờ không còn trống.

    Ví dụ kết quả:
        ✅ ĐÃ ĐẶT LỊCH PHỎNG VẤN THÀNH CÔNG
          Ứng viên   : Nguyễn Văn An (CV101)
          Người PV   : Đinh Văn Đức (IV01)
          Thời gian  : 2026-08-05 09:00
          📧 [AUTO] Email mời phỏng vấn đã được gửi tới: an.nguyen@email.com
          🔄 [AUTO] Trạng thái ứng viên → 'interview_scheduled'
    """
    # TODO: Implement logic — validate inputs, đặt lịch, cập nhật status, trigger email
    raise NotImplementedError


def notify_candidate_result(candidate_id: str, result: str, message: str) -> str:
    """
    Gửi thông báo kết quả tuyển dụng tới ứng viên sau khi có quyết định cuối cùng.

    ⚠️  HITL REQUIRED (Human-In-The-Loop):
        Hành động này gửi email trực tiếp tới ứng viên.
        Agent PHẢI xác nhận với HR trước khi thực thi.
        Tuyệt đối không tự động gọi tool này mà không có phê duyệt của HR.

    Sau khi gửi thành công, hệ thống sẽ tự động:
      - Gửi Email thông báo kết quả (đỗ / trượt) tới ứng viên
      - Cập nhật trạng thái ứng viên tương ứng ('passed' hoặc 'rejected')

    Args:
        candidate_id (str): Mã ứng viên cần gửi thông báo (Ví dụ: 'CV101', 'CV102').
        result (str): Kết quả tuyển dụng, chỉ nhận một trong hai giá trị:
                      - 'passed'   — Ứng viên đỗ, gửi email chúc mừng / mời onboard
                      - 'rejected' — Ứng viên trượt, gửi email cảm ơn / từ chối lịch sự
        message (str): Nội dung thông báo gửi kèm trong email.
                       Không được để trống.
                       (Ví dụ passed  : 'Chúc mừng! Bạn đã vượt qua vòng phỏng vấn.')
                       (Ví dụ rejected: 'Kinh nghiệm chưa đủ 2 năm theo yêu cầu JD.')

    Returns:
        str: Xác nhận email đã được gửi và trạng thái ứng viên đã được cập nhật.
             Trả về thông báo lỗi nếu candidate_id không tồn tại,
             result không hợp lệ, hoặc message bị để trống.

    Ví dụ kết quả (passed):
        📬 ĐÃ GỬI THÔNG BÁO KẾT QUẢ (Đã có xác nhận HITL)
          Ứng viên   : Nguyễn Văn An (CV101)
          Kết quả    : ✅ ĐỖ
          📧 [AUTO] Email chúc mừng đã được gửi tới: an.nguyen@email.com
          🔄 [AUTO] Trạng thái ứng viên → 'passed'

    Ví dụ kết quả (rejected):
        📬 ĐÃ GỬI THÔNG BÁO KẾT QUẢ (Đã có xác nhận HITL)
          Ứng viên   : Trần Thị Bình (CV102)
          Kết quả    : ❌ TRƯỢT
          📧 [AUTO] Email cảm ơn/từ chối đã được gửi tới: binh.tran@email.com
          🔄 [AUTO] Trạng thái ứng viên → 'rejected'
    """
    # TODO: Implement logic — validate result in ['passed', 'rejected'], validate message,
    #       cập nhật trạng thái ứng viên, trigger email thông báo kết quả tương ứng
    raise NotImplementedError


def score_candidate(jd_id: str, candidate_id: str) -> str:
    """
    Chấm điểm mức độ phù hợp của một ứng viên so với yêu cầu của Job Description.

    So sánh nội dung CV (kỹ năng, số năm kinh nghiệm, tóm tắt bản thân)
    với các tiêu chí bắt buộc và kỹ năng cộng thêm trong JD,
    sau đó trả về điểm tổng hợp và nhận xét chi tiết theo từng tiêu chí.

    Args:
        jd_id (str): Mã Job Description dùng làm tiêu chí chấm điểm
                     (Ví dụ: 'JD001').
        candidate_id (str): Mã ứng viên cần được chấm điểm
                            (Ví dụ: 'CV101').

    Returns:
        str: Báo cáo chấm điểm gồm:
               - Điểm tổng (thang 100)
               - Điểm từng tiêu chí: kinh nghiệm, kỹ năng bắt buộc, kỹ năng cộng thêm
               - Danh sách kỹ năng match / thiếu so với JD
               - Khuyến nghị hành động: 'Mời phỏng vấn' / 'Cân nhắc' / 'Từ chối'
             Trả về thông báo lỗi nếu jd_id hoặc candidate_id không tồn tại.

    Ví dụ kết quả:
        🎯 KẾT QUẢ CHẤM ĐIỂM CV — CV101 vs JD001
          Ứng viên        : Nguyễn Văn An
          Vị trí          : Backend Engineer (Python)

          📊 Điểm tổng    : 85 / 100
          ├─ Kinh nghiệm  : 30 / 30  (3 năm >= yêu cầu 2 năm ✅)
          ├─ Kỹ năng bắt buộc: 40 / 50  (thiếu: Redis)
          └─ Kỹ năng cộng thêm: 15 / 20  (có: Docker; thiếu: Kafka, Kubernetes)

          ✅ Kỹ năng match : Python, FastAPI, PostgreSQL, Docker
          ❌ Kỹ năng thiếu : Redis

          💡 Khuyến nghị  : Mời phỏng vấn
    """
    # TODO: Implement logic — so sánh skills/experience của candidate với requirements của JD,
    #       tính điểm từng tiêu chí, tổng hợp điểm và đưa ra khuyến nghị hành động
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 📋 TOOL REGISTRY — Danh sách tool đăng ký cho Agent sử dụng
# ---------------------------------------------------------------------------

AVAILABLE_TOOLS = {
    "list_jobs": list_jobs,
    "get_job_description": get_job_description,
    "get_pending_candidates": get_pending_candidates,
    "get_resume_content": get_resume_content,
    "check_availability": check_availability,
    "book_interview": book_interview, # ⚠️ HITL Required
    "score_candidate": score_candidate,
    "notify_candidate_result": notify_candidate_result,  # ⚠️ HITL Required
}
