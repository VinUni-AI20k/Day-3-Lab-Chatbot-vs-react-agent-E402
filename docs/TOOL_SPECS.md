# 🛠️ TOOL SPECIFICATIONS — Hệ thống Tuyển dụng Thông minh (JD / CV Matching)

> **File:** `src/tools.py`  
> **Người phụ trách:** Role 2 — Tool Engineer  
> **Tổng số tool:** 8  

---

## 1. `list_jobs`

**Mô tả:** Liệt kê tất cả các vị trí tuyển dụng hiện đang mở.

| | Chi tiết |
|---|---|
| **Input** | *(không có)* |
| **Output** | Danh sách các Job kèm `jd_id`, tên vị trí, phòng ban, hạn nộp hồ sơ, số lượng tuyển |

**Ví dụ output:**
```
📋 DANH SÁCH VỊ TRÍ TUYỂN DỤNG ĐANG MỞ:
  [JD001] Backend Engineer (Python) | Phòng: Engineering | Hạn nộp: 2026-08-15 | Số lượng: 2 người
  [JD002] AI/ML Engineer | Phòng: AI Lab | Hạn nộp: 2026-08-30 | Số lượng: 1 người
```

---

## 2. `get_job_description`

**Mô tả:** Lấy toàn bộ nội dung mô tả công việc (Job Description) theo ID.

| | Chi tiết |
|---|---|
| **Input** | `jd_id` *(str)* — Mã Job Description, ví dụ: `'JD001'` |
| **Output** | Chi tiết JD: tên vị trí, phòng ban, trạng thái, số lượng tuyển, hạn nộp, mức lương, yêu cầu bắt buộc, kỹ năng cộng thêm |

**Ví dụ output:**
```
📄 JD001 — Backend Engineer (Python)
  Phòng ban     : Engineering
  Trạng thái    : Đang tuyển
  Số lượng tuyển: 2 người
  Hạn nộp hồ sơ : 2026-08-15
  Mức lương     : 25 - 40 triệu VNĐ / tháng
  ✅ Yêu cầu bắt buộc:
    - Tối thiểu 2 năm kinh nghiệm Python
    - Thành thạo FastAPI hoặc Django
  ⭐ Kỹ năng cộng thêm:
    - Kinh nghiệm với Kafka
```

---

## 3. `get_pending_candidates`

**Mô tả:** Lấy danh sách ứng viên chưa được xử lý (`status = 'pending'`) cho một vị trí JD cụ thể.

| | Chi tiết |
|---|---|
| **Input** | `jd_id` *(str)* — Mã Job Description, ví dụ: `'JD001'` |
| **Output** | Danh sách ứng viên pending: `candidate_id`, tên, ngày ứng tuyển, tóm tắt hồ sơ |

**Ví dụ output:**
```
👥 Ứng viên đang chờ xử lý cho JD001 (2 người):
  [CV101] Nguyễn Văn An | Nộp: 2026-07-20 | Tóm tắt: 3 năm Python/FastAPI...
  [CV102] Trần Thị Bình | Nộp: 2026-07-21 | Tóm tắt: 1 năm Python...
```

---

## 4. `get_resume_content`

**Mô tả:** Đọc và trả về toàn bộ nội dung CV (hồ sơ) của một ứng viên.

| | Chi tiết |
|---|---|
| **Input** | `candidate_id` *(str)* — Mã ứng viên, ví dụ: `'CV101'` |
| **Output** | Chi tiết CV: họ tên, email, vị trí ứng tuyển, trạng thái hồ sơ, ngày ứng tuyển, số năm kinh nghiệm, kỹ năng, tóm tắt bản thân |

**Ví dụ output:**
```
📝 CV ỨNG VIÊN — CV101
  Họ tên              : Nguyễn Văn An
  Email               : an.nguyen@email.com
  Ứng tuyển vị trí   : JD001
  Trạng thái hồ sơ   : pending
  Ngày ứng tuyển     : 2026-07-20
  Số năm kinh nghiệm : 3 năm
  Kỹ năng            : Python, FastAPI, PostgreSQL, Docker
  Tóm tắt bản thân  : 3 năm kinh nghiệm Python/FastAPI, từng làm tại startup Fintech.
```

---

## 5. `check_availability`

**Mô tả:** Kiểm tra các khung giờ còn trống của người phỏng vấn vào một ngày cụ thể.

| | Chi tiết |
|---|---|
| **Input** | `interviewer_id` *(str)* — Mã người phỏng vấn, ví dụ: `'IV01'` |
| | `date` *(str)* — Ngày cần kiểm tra, định dạng `'YYYY-MM-DD'`, ví dụ: `'2026-08-05'` |
| **Output** | Danh sách các khung giờ còn trống trong ngày đó |

**Ví dụ output:**
```
📅 Lịch trống của Đinh Văn Đức (Engineering Lead) ngày 2026-08-05:
  - 09:00
  - 14:00
```

---

## 6. `book_interview`

**Mô tả:** Đặt lịch phỏng vấn cho ứng viên với người phỏng vấn tại khung giờ cụ thể.  
Sau khi đặt thành công, hệ thống **tự động** gửi email mời phỏng vấn và cập nhật trạng thái ứng viên.

| | Chi tiết |
|---|---|
| **Input** | `candidate_id` *(str)* — Mã ứng viên, ví dụ: `'CV101'` |
| | `time_slot` *(str)* — Khung giờ, định dạng `'YYYY-MM-DD HH:MM'`, ví dụ: `'2026-08-05 09:00'` |
| | `interviewer_id` *(str)* — Mã người phỏng vấn, ví dụ: `'IV01'` |
| **Output** | Xác nhận lịch đã đặt + thông báo email tự động đã gửi |

**Ví dụ output:**
```
✅ ĐÃ ĐẶT LỊCH PHỎNG VẤN THÀNH CÔNG
  Ứng viên   : Nguyễn Văn An (CV101)
  Người PV   : Đinh Văn Đức (IV01)
  Thời gian  : 2026-08-05 09:00
  📧 [AUTO] Email mời phỏng vấn đã được gửi tới: an.nguyen@email.com
  🔄 [AUTO] Trạng thái ứng viên → 'interview_scheduled'
```

---

## 7. `score_candidate`

**Mô tả:** Chấm điểm mức độ phù hợp của một ứng viên so với yêu cầu của Job Description.  
So sánh kỹ năng, số năm kinh nghiệm của CV với tiêu chí bắt buộc và nice-to-have của JD.

| | Chi tiết |
|---|---|
| **Input** | `jd_id` *(str)* — Mã Job Description dùng làm tiêu chí chấm, ví dụ: `'JD001'` |
| | `candidate_id` *(str)* — Mã ứng viên cần chấm điểm, ví dụ: `'CV101'` |
| **Output** | Báo cáo điểm: điểm tổng /100, điểm từng tiêu chí, kỹ năng match/thiếu, khuyến nghị hành động |

**Khuyến nghị hành động:**

| Điểm | Khuyến nghị |
|---|---|
| >= 80 | Mời phỏng vấn |
| 50 – 79 | Cân nhắc |
| < 50 | Từ chối |

**Ví dụ output:**
```
🎯 KẾT QUẢ CHẤM ĐIỂM CV — CV101 vs JD001
  Ứng viên        : Nguyễn Văn An
  Vị trí          : Backend Engineer (Python)

  📊 Điểm tổng    : 85 / 100
  ├─ Kinh nghiệm  : 30 / 30  (3 năm >= yêu cầu 2 năm)
  ├─ Kỹ năng bắt buộc: 40 / 50  (thiếu: Redis)
  └─ Kỹ năng cộng thêm: 15 / 20  (có: Docker; thiếu: Kafka, Kubernetes)

  Kỹ năng match : Python, FastAPI, PostgreSQL, Docker
  Kỹ năng thiếu : Redis

  Khuyến nghị   : Mời phỏng vấn
```

---

## 8. `notify_candidate_result` — HITL Required

**Mô tả:** Gửi thông báo kết quả tuyển dụng (đỗ hoặc trượt) tới ứng viên sau khi có quyết định cuối cùng.  
Hệ thống **tự động** cập nhật trạng thái ứng viên và gửi email tương ứng.

> **HITL REQUIRED**: Agent **phải xác nhận với HR** trước khi gọi tool này. Tuyệt đối không tự động thực thi mà không có phê duyệt.

| | Chi tiết |
|---|---|
| **Input** | `candidate_id` *(str)* — Mã ứng viên cần thông báo, ví dụ: `'CV101'` |
| | `result` *(str)* — Kết quả: `'passed'` (đỗ) hoặc `'rejected'` (trượt) |
| | `message` *(str)* — Nội dung thông báo kèm trong email, không được để trống |
| **Output** | Xác nhận email đã gửi + trạng thái ứng viên đã cập nhật |

**Ví dụ output (passed):**
```
📬 ĐÃ GỬI THÔNG BÁO KẾT QUẢ (Đã có xác nhận HITL)
  Ứng viên   : Nguyễn Văn An (CV101)
  Kết quả    : ĐỖ
  📧 [AUTO] Email chúc mừng đã được gửi tới: an.nguyen@email.com
  🔄 [AUTO] Trạng thái ứng viên → 'passed'
```

**Ví dụ output (rejected):**
```
📬 ĐÃ GỬI THÔNG BÁO KẾT QUẢ (Đã có xác nhận HITL)
  Ứng viên   : Trần Thị Bình (CV102)
  Kết quả    : TRƯỢT
  📧 [AUTO] Email cảm ơn/từ chối đã được gửi tới: binh.tran@email.com
  🔄 [AUTO] Trạng thái ứng viên → 'rejected'
```

---

## Bảng tóm tắt tất cả Tools

| # | Tên Tool | Input | Output | HITL |
|:-:|---|---|---|:-:|
| 1 | `list_jobs` | *(không có)* | Danh sách JD đang mở | — |
| 2 | `get_job_description` | `jd_id` | Chi tiết JD | — |
| 3 | `get_pending_candidates` | `jd_id` | Danh sách CV chưa xử lý | — |
| 4 | `get_resume_content` | `candidate_id` | Chi tiết CV | — |
| 5 | `check_availability` | `interviewer_id`, `date` | Khung giờ trống | — |
| 6 | `book_interview` | `candidate_id`, `time_slot`, `interviewer_id` | Xác nhận lịch + auto email | — |
| 7 | `score_candidate` | `jd_id`, `candidate_id` | Báo cáo điểm + khuyến nghị | — |
| 8 | `notify_candidate_result` | `candidate_id`, `result`, `message` | Xác nhận thông báo + auto email | HITL |
