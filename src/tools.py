"""
🛠️ TOOL REGISTRY & SCHEMAS
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

Nguyên tắc thiết kế (Tool Design Principles):
  1. Mỗi tool làm ĐÚNG MỘT việc, tên hàm là động từ rõ nghĩa.
  2. Docstring viết cho LLM đọc: nói rõ DÙNG KHI NÀO, tham số định dạng gì.
  3. KHÔNG BAO GIỜ raise Exception ra ngoài -> luôn trả về chuỗi "LỖI: ..."
     để vòng lặp ReAct đọc được Observation và tự sửa sai ở bước sau.
  4. Dữ liệu: config/data.json (base) + HuggingFace dataset từ config/dataset.txt.
"""

import copy
import hashlib
import json
import os
import re
from datetime import datetime

# ==========================================================
# 📦 LOAD DATABASE: data.json + HF dataset (dataset.txt)
# ==========================================================

# Từ điển kỹ năng dùng để trích xuất từ resume/JD text (deterministic)
_SKILL_VOCAB = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node", "nodejs", "fastapi", "django", "flask", "spring", "sql", "mysql",
    "postgresql", "mongodb", "nosql", "aws", "azure", "gcp", "docker",
    "kubernetes", "k8s", "git", "linux", "excel", "power bi", "tableau",
    "statistics", "machine learning", "deep learning", "nlp", "pandas",
    "numpy", "tensorflow", "pytorch", "spark", "hadoop", "airflow", "kafka",
    "rest", "api", "graphql", "microservices", "ci/cd", "jenkins", "terraform",
    "ansible", "salesforce", "jira", "agile", "scrum", "communication",
    "english", "accounting", "finance", "basel", "risk", "excel",
    "c++", "c#", ".net", "php", "ruby", "go", "golang", "rust", "scala",
    "html", "css", "nextjs", "figma", "selenium", "pytest", "junit",
]

_HF_LABELS = ("Good Fit", "Potential Fit", "No Fit")


def _config_path(*parts: str) -> str:
    """Trả về đường dẫn file trong thư mục config/ (ổn định dù cwd khác nhau)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "config", *parts)
    if os.path.exists(path) or len(parts) == 0:
        return path
    return os.path.join("config", *parts)


def _parse_dataset_config(path: str) -> dict:
    """
    Đọc config/dataset.txt.
    Hỗ trợ:
      - KEY = value
      - DATASET = "https://huggingface.co/datasets/..."
      - JSON object thuần
    """
    defaults = {
        "DATASET": "",
        "SPLIT": "train",
        "LIMIT_PER_LABEL": 8,
        "SEED": 42,
        "CACHE_FILE": "hf_data_cache.json",
    }
    if not os.path.exists(path):
        return defaults

    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return defaults

    # JSON thuần (nếu teammate dump object)
    try:
        data = json.loads(text)
        if isinstance(data, dict) and ("DATASET" in data or "dataset" in data):
            cfg = defaults.copy()
            for k, v in data.items():
                cfg[str(k).upper()] = v
            return cfg
    except json.JSONDecodeError:
        pass

    cfg = defaults.copy()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', line)
        if not m:
            # Dòng chỉ chứa URL HF
            if "huggingface.co/datasets/" in line:
                cfg["DATASET"] = line.strip().strip('"').strip("'")
            continue
        key, val = m.group(1).upper(), m.group(2).strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        if key in ("LIMIT_PER_LABEL", "SEED"):
            try:
                cfg[key] = int(val)
            except ValueError:
                pass
        else:
            cfg[key] = val
    return cfg


def _hf_repo_id(dataset_url: str) -> str:
    """https://huggingface.co/datasets/owner/name -> owner/name"""
    s = (dataset_url or "").strip().rstrip("/")
    m = re.search(r"huggingface\.co/datasets/([^/\s]+/[^/\s]+)", s)
    if m:
        return m.group(1)
    # Cho phép ghi thẳng owner/name
    if re.match(r"^[^/\s]+/[^/\s]+$", s):
        return s
    return s


def _extract_title(jd_text: str) -> str:
    """Lấy job title từ JD text."""
    patterns = [
        r"(?:Role|Position|Job\s*Title|Title)\s*[:\-]\s*(.+)",
        r"(?:Hiring\s+for)\s*[:\-]?\s*(.+)",
    ]
    for pat in patterns:
        m = re.search(pat, jd_text, re.I)
        if m:
            title = m.group(1).split("\n")[0]
            # Cắt phần Location/Type dính liền
            title = re.split(
                r"\b(?:Location|Job\s*Type|Type|Work\s*Mode|Hire\s*Type|Reports?\s+to)\b",
                title,
                maxsplit=1,
                flags=re.I,
            )[0]
            title = re.sub(r"\s+", " ", title).strip(" -:|")
            if 3 <= len(title) <= 80:
                return title
    # Fallback: dòng đầu ngắn
    first = re.sub(r"\s+", " ", jd_text.strip().split("\n")[0]).strip()
    return (first[:70] + "…") if len(first) > 70 else (first or "Unknown Role")


def _extract_skills(text: str, limit: int = 8) -> list:
    """Trích kỹ năng theo vocab (giữ thứ tự xuất hiện)."""
    low = text.lower()
    found = []
    for skill in _SKILL_VOCAB:
        # word-ish match; cho phép # + . /
        pat = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pat, low):
            if skill not in found:
                found.append(skill)
        if len(found) >= limit:
            break
    return found


def _extract_years(text: str, default: int = 1) -> int:
    """Lấy số năm kinh nghiệm gần đúng từ text."""
    patterns = [
        r"(\d+)\s*\+\s*years?",
        r"(\d+)\s*years?\s+of\s+(?:relevant\s+)?experience",
        r"(\d+)\s*years?\s+experience",
        r"experience\s*[:\-]?\s*(\d+)\s*\+?\s*years?",
    ]
    years = []
    head = text[:2500]
    for pat in patterns:
        for m in re.finditer(pat, head, re.I):
            try:
                y = int(m.group(1))
                if 0 <= y <= 40:
                    years.append(y)
            except ValueError:
                continue
    if not years:
        return default
    return max(years)


def _guess_department(title: str, skills: list) -> str:
    t = title.lower()
    joined = " ".join(skills).lower()
    if any(k in t or k in joined for k in ("account", "finance", "basel", "audit")):
        return "Finance"
    if any(k in t or k in joined for k in ("data", "analyst", "bi", "sql", "ml")):
        return "Data"
    if any(k in t or k in joined for k in ("hr", "recruit", "people")):
        return "People Ops"
    if any(k in t or k in joined for k in ("sales", "marketing", "business")):
        return "Business"
    return "Engineering"


def _short_text(text: str, n: int = 280) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    return (s[: n - 1] + "…") if len(s) > n else s


def _map_hf_rows_to_db(rows: list) -> dict:
    """
    Map list[{resume_text, job_description_text, label}]
    -> {jobs, candidates} với id HFJD### / HFCV###
    """
    jobs = {}
    candidates = {}

    for i, row in enumerate(rows, start=1):
        jd_text = str(row.get("job_description_text") or "")
        cv_text = str(row.get("resume_text") or "")
        label = str(row.get("label") or "Unknown")

        job_id = f"HFJD{i:03d}"
        cv_id = f"HFCV{i:03d}"

        title = _extract_title(jd_text)
        jd_skills = _extract_skills(jd_text, limit=8)
        cv_skills = _extract_skills(cv_text, limit=10)
        # must_have: ưu tiên giao skills JD∩CV + top JD skills
        must = jd_skills[:3] if jd_skills else (cv_skills[:2] or ["communication"])
        nice = [s for s in jd_skills[3:6] if s not in must]
        min_years = max(0, _extract_years(jd_text, default=2) // 2)  # nới nhẹ cho lab
        # GPA giả lập ổn định theo hash (deterministic)
        digest = int(hashlib.md5(cv_id.encode()).hexdigest()[:4], 16)
        gpa = round(2.6 + (digest % 15) / 10, 1)  # 2.6 .. 4.0
        years = _extract_years(cv_text, default=1)
        # clamp years theo label để tool score có case PASS/FAIL
        if label == "No Fit":
            years = min(years, max(0, min_years - 1))
        elif label == "Good Fit":
            years = max(years, min_years)

        jobs[job_id] = {
            "title": title,
            "department": _guess_department(title, jd_skills),
            "must_have_skills": must,
            "nice_to_have_skills": nice,
            "min_years_exp": min_years,
            "min_gpa": 2.8,
            "headcount": 1,
            "source_label": label,
            "raw_summary": _short_text(jd_text, 320),
        }
        candidates[cv_id] = {
            "name": f"HF Candidate {i:03d}",
            "email": f"hf.candidate{i:03d}@email.com",
            "phone": f"09{i:08d}"[-10:],
            "applied_job": job_id,
            "years_exp": years,
            "gpa": gpa,
            "skills": cv_skills or ["communication"],
            "education": "Imported from HuggingFace resume-job-description-fit",
            "status": "NEW",
            "ground_truth_fit": label,
            "raw_summary": _short_text(cv_text, 320),
        }

    return {"jobs": jobs, "candidates": candidates}


def _sample_hf_dataset(repo_id: str, split: str, limit_per_label: int, seed: int) -> list:
    """Tải HF dataset và lấy mẫu cân bằng theo label."""
    from datasets import load_dataset

    ds = load_dataset(repo_id, split=split)
    # Shuffle deterministic
    ds = ds.shuffle(seed=seed)

    buckets = {lab: [] for lab in _HF_LABELS}
    for row in ds:
        lab = row.get("label")
        if lab in buckets and len(buckets[lab]) < limit_per_label:
            buckets[lab].append({
                "resume_text": row["resume_text"],
                "job_description_text": row["job_description_text"],
                "label": lab,
            })
        if all(len(v) >= limit_per_label for v in buckets.values()):
            break

    rows = []
    for lab in _HF_LABELS:
        rows.extend(buckets[lab])
    return rows


def _load_hf_extra(cfg: dict) -> dict:
    """
    Load subset từ HuggingFace theo config dataset.txt.
    Có cache local config/hf_data_cache.json để import nhanh.
    """
    repo = _hf_repo_id(cfg.get("DATASET", ""))
    if not repo or "/" not in repo:
        return {}

    split = str(cfg.get("SPLIT", "train"))
    limit = int(cfg.get("LIMIT_PER_LABEL", 8))
    seed = int(cfg.get("SEED", 42))
    cache_name = str(cfg.get("CACHE_FILE", "hf_data_cache.json"))
    cache_path = _config_path(cache_name)

    cache_key = {
        "repo": repo,
        "split": split,
        "limit_per_label": limit,
        "seed": seed,
        "version": 1,
    }

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("cache_key") == cache_key and cached.get("jobs") and cached.get("candidates"):
                return {"jobs": cached["jobs"], "candidates": cached["candidates"]}
        except (json.JSONDecodeError, OSError, TypeError):
            pass

    try:
        rows = _sample_hf_dataset(repo, split, limit, seed)
        extra = _map_hf_rows_to_db(rows)
    except Exception as e:
        # Không crash tools nếu offline / thiếu package
        print(f"⚠️ Không tải được HF dataset '{repo}': {type(e).__name__}: {e}")
        return {}

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({
                "cache_key": cache_key,
                "source": f"https://huggingface.co/datasets/{repo}",
                "count_jobs": len(extra["jobs"]),
                "count_candidates": len(extra["candidates"]),
                "jobs": extra["jobs"],
                "candidates": extra["candidates"],
            }, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

    return extra


def _merge_db(base: dict, extra: dict) -> dict:
    """Merge dataset bổ sung vào DB gốc (extra ghi đè key trùng)."""
    merged = copy.deepcopy(base)
    for key in ("jobs", "candidates", "interviewers", "email_templates"):
        if key in extra and isinstance(extra[key], dict):
            merged.setdefault(key, {}).update(extra[key])
    if "pass_score_threshold" in extra:
        merged["pass_score_threshold"] = extra["pass_score_threshold"]
    return merged


def _load_database() -> dict:
    """
    Load mock DB:
      1) config/data.json              (base lab: JD/CV demo + interviewers)
      2) HuggingFace dataset từ dataset.txt (merge HFJD*/HFCV*)
    """
    data_path = _config_path("data.json")
    with open(data_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    dataset_path = _config_path("dataset.txt")
    cfg = _parse_dataset_config(dataset_path)
    extra = _load_hf_extra(cfg)
    if extra:
        db = _merge_db(db, extra)

    return db


_DB = _load_database()

# Deep copy để tool có thể mutate status/lịch trong phiên chạy
# mà không làm hỏng file JSON gốc trên đĩa.
JOB_DATABASE = copy.deepcopy(_DB["jobs"])
CANDIDATE_DATABASE = copy.deepcopy(_DB["candidates"])
INTERVIEWER_CALENDAR = copy.deepcopy(_DB["interviewers"])
PASS_SCORE_THRESHOLD = int(_DB.get("pass_score_threshold", 70))
EMAIL_TEMPLATES = copy.deepcopy(_DB.get("email_templates", {}))

# Danh sách lịch phỏng vấn đã chốt (ghi nhận trong phiên chạy, không lưu file)
SCHEDULED_INTERVIEWS = []


# ==========================================================
# 🧰 HELPER (Hàm phụ trợ nội bộ, không đăng ký làm tool)
# ==========================================================

def _fmt_id_list(keys, limit: int = 12) -> str:
    """Rút gọn danh sách mã khi DB lớn (HF merge)."""
    keys = list(keys)
    if len(keys) <= limit:
        return ", ".join(keys)
    head = ", ".join(keys[:limit])
    return f"{head}, ... (+{len(keys) - limit} mã khác)"


def _validate_date(date_str: str):
    """Kiểm tra chuỗi ngày dạng DD/MM/YYYY. Trả về (datetime, None) hoặc (None, 'LỖI: ...')."""
    try:
        parsed = datetime.strptime(date_str.strip(), "%d/%m/%Y")
    except (ValueError, AttributeError):
        return None, (
            f"LỖI: Ngày '{date_str}' không hợp lệ. "
            f"Vui lòng dùng đúng định dạng DD/MM/YYYY và là ngày thật (VD: 05/08/2026)."
        )
    if parsed.weekday() >= 5:
        return None, (
            f"LỖI: Ngày {date_str} là Thứ {'Bảy' if parsed.weekday() == 5 else 'Chủ Nhật'}. "
            f"Công ty chỉ phỏng vấn từ Thứ 2 đến Thứ 6, hãy chọn ngày khác."
        )
    return parsed, None

# ==========================================================
# 🛠️ TOOL 1: Tra cứu mô tả công việc
# ==========================================================

def get_job_requirements(job_id: str) -> str:
    """
    Tra cứu yêu cầu tuyển dụng (Job Description) của một vị trí.

    DÙNG KHI: cần biết vị trí yêu cầu kỹ năng gì, bao nhiêu năm kinh nghiệm,
    trước khi đánh giá hoặc so sánh ứng viên.

    Args:
        job_id (str): Mã vị trí tuyển dụng. VD: 'JD001', 'HFJD001'.

    Returns:
        str: Chi tiết yêu cầu vị trí, hoặc chuỗi bắt đầu bằng 'LỖI:' nếu mã sai.
    """
    key = str(job_id).strip().upper()
    job = JOB_DATABASE.get(key)
    if not job:
        return (
            f"LỖI: Không tìm thấy vị trí '{job_id}'. "
            f"Các mã hợp lệ: {_fmt_id_list(JOB_DATABASE.keys())}."
        )
    lines = [
        f"[{key}] {job['title']} - Phòng {job['department']}",
        f"- Kỹ năng bắt buộc: {', '.join(job['must_have_skills'])}",
        f"- Kỹ năng ưu tiên: {', '.join(job.get('nice_to_have_skills') or [])}",
        f"- Kinh nghiệm tối thiểu: {job['min_years_exp']} năm",
        f"- GPA tối thiểu: {job['min_gpa']}",
        f"- Số lượng cần tuyển: {job['headcount']} người",
    ]
    if job.get("source_label"):
        lines.append(f"- Nhãn dataset (ground truth): {job['source_label']}")
    if job.get("raw_summary"):
        lines.append(f"- Tóm tắt JD: {job['raw_summary']}")
    return "\n".join(lines)


# ==========================================================
# 🛠️ TOOL 2: Tìm kiếm / lọc ứng viên
# ==========================================================

def search_candidates(job_id: str, min_years_exp: int = 0, required_skill: str = "") -> str:
    """
    Tìm danh sách ứng viên đã ứng tuyển vào một vị trí, có thể lọc thêm.

    DÙNG KHI: cần biết có những ai đang ứng tuyển vị trí nào, hoặc cần lọc nhanh
    theo số năm kinh nghiệm / một kỹ năng cụ thể.

    Args:
        job_id (str): Mã vị trí (VD: 'JD001', 'HFJD001').
        min_years_exp (int): Số năm kinh nghiệm tối thiểu. Mặc định 0 (không lọc).
        required_skill (str): Kỹ năng buộc phải có (VD: 'python'). Mặc định '' (không lọc).

    Returns:
        str: Danh sách mã CV + tên + kinh nghiệm, hoặc 'LỖI:' / thông báo không có kết quả.
    """
    key = str(job_id).strip().upper()
    if key not in JOB_DATABASE:
        return (
            f"LỖI: Không tìm thấy vị trí '{job_id}'. "
            f"Các mã hợp lệ: {_fmt_id_list(JOB_DATABASE.keys())}."
        )

    try:
        min_years = int(min_years_exp)
    except (TypeError, ValueError):
        return f"LỖI: Tham số min_years_exp='{min_years_exp}' phải là số nguyên (VD: 2)."

    skill = str(required_skill).strip().lower()
    rows = []
    for cv_id, c in CANDIDATE_DATABASE.items():
        if c["applied_job"] != key:
            continue
        if c["years_exp"] < min_years:
            continue
        if skill and skill not in [s.lower() for s in c["skills"]]:
            continue
        rows.append(
            f"- {cv_id} | {c['name']} | {c['years_exp']} năm KN | GPA {c['gpa']} | "
            f"Skills: {', '.join(c['skills'])}"
        )

    if not rows:
        return (
            f"Không có ứng viên nào của vị trí {key} thỏa điều kiện "
            f"(min_years_exp={min_years}, required_skill='{required_skill}'). "
            f"Hãy thử nới lỏng tiêu chí."
        )
    return f"Tìm thấy {len(rows)} ứng viên cho {key} ({JOB_DATABASE[key]['title']}):\n" + "\n".join(rows)


# ==========================================================
# 🛠️ TOOL 3: Xem chi tiết hồ sơ ứng viên
# ==========================================================

def get_candidate_profile(candidate_id: str) -> str:
    """
    Lấy chi tiết hồ sơ (CV) của một ứng viên theo mã CV.

    DÙNG KHI: cần thông tin đầy đủ của 1 người (email, học vấn, kỹ năng, trạng thái)
    trước khi chấm điểm hoặc gửi email.

    Args:
        candidate_id (str): Mã hồ sơ ứng viên (VD: 'CV101', 'HFCV001').

    Returns:
        str: Thông tin chi tiết hồ sơ, hoặc chuỗi bắt đầu bằng 'LỖI:' nếu không tồn tại.
    """
    key = str(candidate_id).strip().upper()
    c = CANDIDATE_DATABASE.get(key)
    if not c:
        return (
            f"LỖI: Không tìm thấy hồ sơ '{candidate_id}' trong hệ thống. "
            f"Các mã hợp lệ: {_fmt_id_list(CANDIDATE_DATABASE.keys())}."
        )
    job = JOB_DATABASE.get(c["applied_job"], {})
    lines = [
        f"[{key}] {c['name']}",
        f"- Email: {c['email']} | SĐT: {c['phone']}",
        f"- Ứng tuyển: {c['applied_job']} ({job.get('title', 'N/A')})",
        f"- Kinh nghiệm: {c['years_exp']} năm | GPA: {c['gpa']}",
        f"- Kỹ năng: {', '.join(c['skills'])}",
        f"- Học vấn: {c['education']}",
        f"- Trạng thái hiện tại: {c['status']}",
    ]
    if c.get("ground_truth_fit"):
        lines.append(f"- Nhãn dataset (ground truth): {c['ground_truth_fit']}")
    if c.get("raw_summary"):
        lines.append(f"- Tóm tắt CV: {c['raw_summary']}")
    return "\n".join(lines)


# ==========================================================
# 🛠️ TOOL 4: Chấm điểm độ phù hợp CV vs JD
# ==========================================================

def score_candidate(candidate_id: str, job_id: str) -> str:
    """
    Chấm điểm độ phù hợp (0-100) giữa một hồ sơ và một vị trí tuyển dụng.

    DÙNG KHI: cần quyết định ứng viên PASS hay FAIL vòng sàng lọc CV.
    Công thức: kỹ năng bắt buộc 60đ + kinh nghiệm 25đ + GPA 15đ.
    Điểm >= 70 mới được phép đặt lịch phỏng vấn.

    Args:
        candidate_id (str): Mã hồ sơ ứng viên (VD: 'CV101').
        job_id (str): Mã vị trí cần so khớp (VD: 'JD001').

    Returns:
        str: Bảng điểm chi tiết kèm kết luận PASS/FAIL, hoặc chuỗi 'LỖI:' nếu mã sai.
    """
    cv_key = str(candidate_id).strip().upper()
    job_key = str(job_id).strip().upper()

    c = CANDIDATE_DATABASE.get(cv_key)
    if not c:
        return (
            f"LỖI: Không tìm thấy hồ sơ '{candidate_id}'. "
            f"Các mã hợp lệ: {_fmt_id_list(CANDIDATE_DATABASE.keys())}."
        )
    job = JOB_DATABASE.get(job_key)
    if not job:
        return (
            f"LỖI: Không tìm thấy vị trí '{job_id}'. "
            f"Các mã hợp lệ: {_fmt_id_list(JOB_DATABASE.keys())}."
        )

    cand_skills = [s.lower() for s in c["skills"]]
    must = job["must_have_skills"]
    matched = [s for s in must if s in cand_skills]
    missing = [s for s in must if s not in cand_skills]

    skill_score = 60 * len(matched) / len(must) if must else 60
    exp_score = 25 if c["years_exp"] >= job["min_years_exp"] else 25 * c["years_exp"] / max(job["min_years_exp"], 1)
    gpa_score = 15 if c["gpa"] >= job["min_gpa"] else 15 * c["gpa"] / job["min_gpa"]
    total = round(skill_score + exp_score + gpa_score)

    verdict = "PASS ✅ (đủ điều kiện mời phỏng vấn)" if total >= PASS_SCORE_THRESHOLD else "FAIL ❌ (chưa đạt ngưỡng)"
    # Cập nhật trạng thái để tool schedule_interview kiểm tra lại được
    c["status"] = "SCREEN_PASSED" if total >= PASS_SCORE_THRESHOLD else "SCREEN_FAILED"

    return (
        f"KẾT QUẢ SÀNG LỌC {cv_key} ({c['name']}) cho {job_key} ({job['title']}):\n"
        f"- Kỹ năng khớp: {', '.join(matched) if matched else 'không có'} "
        f"(thiếu: {', '.join(missing) if missing else 'không thiếu gì'}) -> {round(skill_score)}/60\n"
        f"- Kinh nghiệm: {c['years_exp']}/{job['min_years_exp']} năm -> {round(exp_score)}/25\n"
        f"- GPA: {c['gpa']}/{job['min_gpa']} -> {round(gpa_score)}/15\n"
        f"=> TỔNG ĐIỂM: {total}/100 - {verdict}"
    )


# ==========================================================
# 🛠️ TOOL 5: Kiểm tra lịch trống của người phỏng vấn
# ==========================================================

def check_interview_slots(date: str, interviewer: str = "") -> str:
    """
    Kiểm tra các khung giờ còn trống để phỏng vấn trong một ngày.

    DÙNG KHI: trước khi đặt lịch, cần biết ngày đó ai rảnh và rảnh giờ nào.
    Công ty chỉ phỏng vấn Thứ 2 - Thứ 6.

    Args:
        date (str): Ngày cần kiểm tra, định dạng DD/MM/YYYY (VD: '05/08/2026').
        interviewer (str): Tên người phỏng vấn cụ thể. Mặc định '' = xem tất cả.

    Returns:
        str: Danh sách khung giờ trống, hoặc chuỗi bắt đầu bằng 'LỖI:' nếu ngày/tên sai.
    """
    _, err = _validate_date(date)
    if err:
        return err

    name_filter = str(interviewer).strip().lower()
    targets = INTERVIEWER_CALENDAR
    if name_filter:
        targets = {k: v for k, v in INTERVIEWER_CALENDAR.items() if name_filter in k.lower()}
        if not targets:
            return (
                f"LỖI: Không tìm thấy người phỏng vấn '{interviewer}'. "
                f"Danh sách hợp lệ: {', '.join(INTERVIEWER_CALENDAR.keys())}."
            )

    booked = {(i["date"], i["time"], i["interviewer"]) for i in SCHEDULED_INTERVIEWS}
    lines = []
    for person, slots in targets.items():
        free = [s for s in slots if (date.strip(), s, person) not in booked]
        lines.append(f"- {person}: {', '.join(free) if free else 'ĐÃ KÍN LỊCH'}")
    return f"Lịch trống ngày {date.strip()}:\n" + "\n".join(lines)


# ==========================================================
# 🛠️ TOOL 6: Đặt lịch phỏng vấn
# ==========================================================

def schedule_interview(candidate_id: str, date: str, time: str, interviewer: str) -> str:
    """
    Đặt lịch phỏng vấn cho ứng viên ĐÃ PASS vòng sàng lọc CV.

    DÙNG KHI: đã chấm điểm bằng score_candidate và ứng viên đạt >= 70 điểm,
    đồng thời đã kiểm tra khung giờ trống bằng check_interview_slots.

    Args:
        candidate_id (str): Mã hồ sơ ứng viên (VD: 'CV101').
        date (str): Ngày phỏng vấn, định dạng DD/MM/YYYY (VD: '05/08/2026').
        time (str): Khung giờ dạng HH:MM (VD: '10:00').
        interviewer (str): Tên người phỏng vấn (VD: 'Mr. Hùng').

    Returns:
        str: Xác nhận lịch đã chốt kèm mã booking, hoặc chuỗi bắt đầu bằng 'LỖI:'
             nêu rõ lý do (chưa sàng lọc, chưa đạt điểm, trùng lịch, sai định dạng).
    """
    cv_key = str(candidate_id).strip().upper()
    c = CANDIDATE_DATABASE.get(cv_key)
    if not c:
        return (
            f"LỖI: Không tìm thấy hồ sơ '{candidate_id}'. "
            f"Các mã hợp lệ: {_fmt_id_list(CANDIDATE_DATABASE.keys())}."
        )

    # 🛡️ GUARDRAIL NGHIỆP VỤ: bắt buộc sàng lọc trước khi hẹn phỏng vấn
    if c["status"] == "NEW":
        return (
            f"LỖI: Hồ sơ {cv_key} chưa được sàng lọc. "
            f"Hãy gọi score_candidate('{cv_key}', '{c['applied_job']}') trước khi đặt lịch."
        )
    if c["status"] == "SCREEN_FAILED":
        return (
            f"LỖI: Hồ sơ {cv_key} ({c['name']}) KHÔNG đạt ngưỡng {PASS_SCORE_THRESHOLD} điểm "
            f"nên không được phép mời phỏng vấn. Hãy gửi thư từ chối bằng send_candidate_email."
        )

    _, err = _validate_date(date)
    if err:
        return err

    try:
        datetime.strptime(str(time).strip(), "%H:%M")
    except ValueError:
        return f"LỖI: Giờ '{time}' không hợp lệ. Dùng định dạng HH:MM (VD: '10:00')."

    name_filter = str(interviewer).strip().lower()
    person = next((k for k in INTERVIEWER_CALENDAR if name_filter and name_filter in k.lower()), None)
    if not person:
        return (
            f"LỖI: Không tìm thấy người phỏng vấn '{interviewer}'. "
            f"Danh sách hợp lệ: {', '.join(INTERVIEWER_CALENDAR.keys())}."
        )

    slot = str(time).strip()
    d = date.strip()
    if slot not in INTERVIEWER_CALENDAR[person]:
        return (
            f"LỖI: {person} không làm việc khung {slot}. "
            f"Các khung khả dụng: {', '.join(INTERVIEWER_CALENDAR[person])}."
        )
    for booked in SCHEDULED_INTERVIEWS:
        if booked["date"] == d and booked["time"] == slot and booked["interviewer"] == person:
            return (
                f"LỖI: Khung {slot} ngày {d} của {person} đã bị {booked['candidate_id']} đặt trước. "
                f"Hãy gọi check_interview_slots('{d}') để chọn khung khác."
            )

    booking_id = f"ITV{len(SCHEDULED_INTERVIEWS) + 1:03d}"
    SCHEDULED_INTERVIEWS.append({
        "booking_id": booking_id,
        "candidate_id": cv_key,
        "date": d,
        "time": slot,
        "interviewer": person,
    })
    c["status"] = "INTERVIEW_SCHEDULED"
    return (
        f"✅ ĐÃ CHỐT LỊCH [{booking_id}]: {c['name']} ({cv_key}) phỏng vấn vị trí "
        f"{c['applied_job']} lúc {slot} ngày {d} với {person}. "
        f"Đừng quên gửi thư mời bằng send_candidate_email('{cv_key}', 'invite')."
    )


# ==========================================================
# 🛠️ TOOL 7: Gửi email cho ứng viên
# ==========================================================

def send_candidate_email(candidate_id: str, template: str) -> str:
    """
    Gửi email thông báo cho ứng viên theo mẫu có sẵn.

    DÙNG KHI: cần mời phỏng vấn ('invite'), từ chối lịch sự ('reject'),
    hoặc nhắc lịch ('reminder'). Đây là hành động GỬI THẬT, chỉ gọi 1 lần cho mỗi mục đích.

    Args:
        candidate_id (str): Mã hồ sơ ứng viên (VD: 'CV101').
        template (str): Mẫu email. Hợp lệ: 'invite', 'reject', 'reminder'.

    Returns:
        str: Xác nhận đã gửi, hoặc chuỗi bắt đầu bằng 'LỖI:' nếu mã/mẫu sai
             hoặc gửi thư mời khi chưa có lịch phỏng vấn.
    """
    cv_key = str(candidate_id).strip().upper()
    c = CANDIDATE_DATABASE.get(cv_key)
    if not c:
        return (
            f"LỖI: Không tìm thấy hồ sơ '{candidate_id}'. "
            f"Các mã hợp lệ: {_fmt_id_list(CANDIDATE_DATABASE.keys())}."
        )

    tpl = str(template).strip().lower()
    if tpl not in EMAIL_TEMPLATES:
        return (
            f"LỖI: Mẫu email '{template}' không tồn tại. "
            f"Các mẫu hợp lệ: {', '.join(EMAIL_TEMPLATES.keys())}."
        )

    # 🛡️ GUARDRAIL: không mời/nhắc phỏng vấn khi chưa có lịch
    if tpl in ("invite", "reminder") and c["status"] != "INTERVIEW_SCHEDULED":
        return (
            f"LỖI: Chưa có lịch phỏng vấn cho {cv_key}. "
            f"Hãy gọi schedule_interview trước khi gửi mẫu '{tpl}'."
        )

    detail = ""
    if tpl in ("invite", "reminder"):
        itv = next((i for i in reversed(SCHEDULED_INTERVIEWS) if i["candidate_id"] == cv_key), None)
        if itv:
            detail = f" Nội dung: {itv['time']} ngày {itv['date']} với {itv['interviewer']}."

    return (
        f"📧 ĐÃ GỬI '{EMAIL_TEMPLATES[tpl]}' tới {c['name']} <{c['email']}>.{detail}"
    )


# ==========================================================
# 📋 TOOL REGISTRY (Role 4 & Role 3 dùng dict này)
# ==========================================================

AVAILABLE_TOOLS = {
    "get_job_requirements": get_job_requirements,
    "search_candidates": search_candidates,
    "get_candidate_profile": get_candidate_profile,
    "score_candidate": score_candidate,
    "check_interview_slots": check_interview_slots,
    "schedule_interview": schedule_interview,
    "send_candidate_email": send_candidate_email,
}


def get_tools_description() -> str:
    """
    Sinh khối text mô tả toàn bộ tool để Role 3 chèn vào REACT_SYSTEM_PROMPT.

    Returns:
        str: Danh sách 'tên_tool(tham số): mô tả ngắn' của tất cả tool đã đăng ký.
    """
    import inspect

    lines = []
    for name, fn in AVAILABLE_TOOLS.items():
        sig = str(inspect.signature(fn))
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        lines.append(f"- {name}{sig}: {doc}")
    return "\n".join(lines)


# ==========================================================
# 🧪 SELF-TEST: chạy `python src/tools.py` để nghiệm thu tool
# ==========================================================

if __name__ == "__main__":
    import sys

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("🧪 SELF-TEST TOOLS - ĐỀ TÀI 9: SÀNG LỌC CV & HẸN PHỎNG VẤN")
    print("=" * 60)
    print(f"📦 DB: {len(JOB_DATABASE)} jobs | {len(CANDIDATE_DATABASE)} candidates")

    checks = [
        ("Happy path: xem JD", lambda: get_job_requirements("JD001")),
        ("Happy path: lọc ứng viên có python, >=2 năm", lambda: search_candidates("JD001", 2, "python")),
        ("Happy path: xem hồ sơ", lambda: get_candidate_profile("CV101")),
        ("Happy path: chấm điểm PASS", lambda: score_candidate("CV101", "JD001")),
        ("Happy path: xem lịch trống", lambda: check_interview_slots("05/08/2026")),
        ("Happy path: đặt lịch", lambda: schedule_interview("CV101", "05/08/2026", "10:00", "Mr. Hùng")),
        ("Happy path: gửi thư mời", lambda: send_candidate_email("CV101", "invite")),
        ("HF path: xem JD HF", lambda: get_job_requirements("HFJD001") if "HFJD001" in JOB_DATABASE else "SKIP: chưa load HF"),
        ("HF path: xem CV HF", lambda: get_candidate_profile("HFCV001") if "HFCV001" in CANDIDATE_DATABASE else "SKIP: chưa load HF"),
        ("Edge: mã CV không tồn tại", lambda: get_candidate_profile("CV999")),
        ("Edge: ngày 32/13/2026 vô lý", lambda: check_interview_slots("32/13/2026")),
        ("Edge: ngày cuối tuần", lambda: check_interview_slots("08/08/2026")),
        ("Edge: chấm điểm FAIL", lambda: score_candidate("CV104", "JD002")),
        ("Edge: đặt lịch cho người FAIL", lambda: schedule_interview("CV104", "05/08/2026", "10:00", "Ms. Lan")),
        ("Edge: chưa sàng lọc đã đặt lịch", lambda: schedule_interview("CV102", "05/08/2026", "09:00", "Mr. Hùng")),
        ("Edge: trùng slot đã đặt", lambda: schedule_interview("CV103", "05/08/2026", "10:00", "Mr. Hùng")),
        ("Edge: mẫu email không tồn tại", lambda: send_candidate_email("CV101", "khen_thuong")),
    ]

    failed = 0
    for title, fn in checks:
        try:
            print(f"\n▶️ {title}\n{fn()}")
        except Exception as e:  # Tool KHÔNG được phép crash
            failed += 1
            print(f"\n❌ {title} -> CRASH: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print(f"{'✅ TẤT CẢ TOOL AN TOÀN, KHÔNG CRASH.' if failed == 0 else f'❌ Có {failed} tool bị crash!'}")
    print(f"📋 Đã đăng ký {len(AVAILABLE_TOOLS)} tools:")
    print(get_tools_description())
