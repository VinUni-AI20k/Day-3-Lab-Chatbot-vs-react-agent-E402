"""Read-only recruitment tools backed by the project's CSV datasets.

These tools support candidate discovery and human review. They must not make
final hiring decisions or contact candidates.
"""

import csv
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
JOBS_CSV = DATA_DIR / "JOB_DATA_FINAL.csv"
CANDIDATES_CSV = DATA_DIR / "USER_DATA_FINAL.csv"
DEFAULT_RESULT_LIMIT = 5
MAX_RESULT_LIMIT = 10
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "va", "la", "cho", "cua", "trong", "voi", "mot", "nhung", "cac",
    "duoc", "theo", "tai", "tu", "den", "nhan", "vien", "cong", "ty",
    "viec", "lam", "kinh", "nghiem", "yeu", "cau", "co", "khong",
}
SKILL_STOP_WORDS = STOP_WORDS | {
    "bao", "biet", "cao", "cap", "chiu", "chuyen", "dai", "dam", "doi",
    "giao", "hang", "hieu", "hien", "hoc", "hoi", "khach", "lam", "ly",
    "nang", "nghiep", "nhanh", "phong", "quan", "thanh", "thao", "thuc",
    "tinh", "tot", "van", "xuat", "yeu", "nguoi", "moi", "nhom",
}


def _normalize(value: object) -> str:
    """Normalize Vietnamese text for accent-insensitive matching."""
    text = unicodedata.normalize("NFD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.replace("đ", "d")


def _shorten(value: object, length: int = 420) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= length else f"{text[:length].rstrip()}..."


def _keywords(value: object) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(_normalize(value))
        if len(token) >= 3 and token not in STOP_WORDS
    }


def _skill_keywords(value: object) -> set[str]:
    """Extract potentially job-specific terms and discard common prose words."""
    return {
        token
        for token in TOKEN_PATTERN.findall(_normalize(value))
        if len(token) >= 3 and token not in SKILL_STOP_WORDS
    }


def _to_limit(limit: int | str) -> int:
    try:
        return max(1, min(int(limit), MAX_RESULT_LIMIT))
    except (TypeError, ValueError):
        return DEFAULT_RESULT_LIMIT


def _experience_years(value: object) -> float | None:
    """Map dataset experience labels to their minimum years of experience."""
    text = _normalize(value)
    if not text:
        return None
    if "khong yeu cau" in text or "chua co kinh nghiem" in text:
        return 0.0
    if "duoi 1" in text:
        return 0.5
    if "tren 10" in text:
        return 10.0

    range_match = re.search(r"(\d+)\s*-\s*(\d+)", text)
    if range_match:
        return float(range_match.group(1))

    number_match = re.search(r"\d+", text)
    return float(number_match.group()) if number_match else None


@lru_cache(maxsize=1)
def _load_jobs() -> list[dict[str, str]]:
    if not JOBS_CSV.exists():
        return []
    with JOBS_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


@lru_cache(maxsize=1)
def _load_candidates() -> list[dict[str, str]]:
    if not CANDIDATES_CSV.exists():
        return []
    with CANDIDATES_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


@lru_cache(maxsize=1)
def _job_requirement_document_frequency() -> Counter[str]:
    """Count in how many job requirements each term occurs."""
    frequencies: Counter[str] = Counter()
    for job in _load_jobs():
        frequencies.update(_skill_keywords(job.get("Job Requirements", "")))
    return frequencies


def _find_by_id(rows: list[dict[str, str]], field: str, record_id: str) -> dict[str, str] | None:
    target = str(record_id).strip()
    return next((row for row in rows if row.get(field, "").strip() == target), None)


def _job_search_text(job: dict[str, str]) -> str:
    fields = ("Job Title", "Name Company", "Industry", "Job Address", "Job Requirements")
    return _normalize(" ".join(job.get(field, "") for field in fields))


def _candidate_search_text(candidate: dict[str, str]) -> str:
    fields = ("User Name", "Industry", "Desired Job", "Workplace Desired", "Skills", "Target")
    return _normalize(" ".join(candidate.get(field, "") for field in fields))


def search_jobs(keyword: str = "", location: str = "", limit: int = DEFAULT_RESULT_LIMIT) -> str:
    """Find jobs by keyword and optional location from JOB_DATA_FINAL.csv.

    Args:
        keyword: Text to match against title, company, industry, or requirements.
        location: Optional city or location text to match against the job address.
        limit: Number of results to return, from 1 to 10.
    """
    jobs = _load_jobs()
    if not jobs:
        return "LỖI: Không tìm thấy file dữ liệu việc làm JOB_DATA_FINAL.csv."

    keyword_query = _normalize(keyword)
    location_query = _normalize(location)
    matches = [
        job
        for job in jobs
        if (not keyword_query or keyword_query in _job_search_text(job))
        and (not location_query or location_query in _normalize(job.get("Job Address", "")))
    ]
    if not matches:
        return "Không tìm thấy việc làm phù hợp với điều kiện tra cứu."

    result_limit = _to_limit(limit)
    lines = [f"Tìm thấy {len(matches)} việc làm, hiển thị {min(len(matches), result_limit)} kết quả:"]
    for job in matches[:result_limit]:
        lines.append(
            f"- [{job['JobID']}] {job.get('Job Title', 'Không rõ vị trí')} | "
            f"{job.get('Name Company', 'Không rõ công ty')} | "
            f"{job.get('Job Address', 'Không rõ địa điểm')} | "
            f"Lương: {job.get('Salary', 'Không rõ')}"
        )
    return "\n".join(lines)


def list_jobs(limit: int = DEFAULT_RESULT_LIMIT) -> str:
    """List a small, prompt-safe sample of jobs in the dataset."""
    return search_jobs(limit=limit)


def get_job_description(job_id: str) -> str:
    """Return a job record by its real JobID from JOB_DATA_FINAL.csv."""
    job = _find_by_id(_load_jobs(), "JobID", job_id)
    if job is None:
        return f"LỖI: Không tìm thấy JobID '{job_id}'."

    return "\n".join(
        [
            f"JOB [{job['JobID']}]: {job.get('Job Title', 'Không rõ')}",
            f"Công ty: {job.get('Name Company', 'Không rõ')}",
            f"Ngành: {job.get('Industry', 'Không rõ')}",
            f"Địa điểm: {job.get('Job Address', 'Không rõ')}",
            f"Loại việc: {job.get('Job Type', 'Không rõ')}",
            f"Kinh nghiệm: {job.get('Years of Experience', 'Không rõ')}",
            f"Lương: {job.get('Salary', 'Không rõ')}",
            f"Hạn nộp: {job.get('Submission Deadline', 'Không rõ')}",
            f"Yêu cầu: {_shorten(job.get('Job Requirements'))}",
            f"Mô tả: {_shorten(job.get('Job Description'), 900)}",
        ]
    )


def search_candidates(keyword: str = "", location: str = "", limit: int = DEFAULT_RESULT_LIMIT) -> str:
    """Find candidate profiles by skills, desired role, industry, or location.

    The result is for HR review only; it is not an automated hiring decision.
    """
    candidates = _load_candidates()
    if not candidates:
        return "LỖI: Không tìm thấy file dữ liệu ứng viên USER_DATA_FINAL.csv."

    keyword_query = _normalize(keyword)
    location_query = _normalize(location)
    matches = [
        candidate
        for candidate in candidates
        if (not keyword_query or keyword_query in _candidate_search_text(candidate))
        and (not location_query or location_query in _normalize(candidate.get("Workplace Desired", "")))
    ]
    if not matches:
        return "Không tìm thấy ứng viên phù hợp với điều kiện tra cứu."

    result_limit = _to_limit(limit)
    lines = [f"Tìm thấy {len(matches)} ứng viên, hiển thị {min(len(matches), result_limit)} kết quả:"]
    for candidate in matches[:result_limit]:
        lines.append(
            f"- [{candidate['UserID']}] {candidate.get('User Name', 'Không rõ')} | "
            f"Mong muốn: {candidate.get('Desired Job', 'Không rõ')} | "
            f"Địa điểm: {candidate.get('Workplace Desired', 'Không rõ')} | "
            f"Kinh nghiệm: {candidate.get('Work Experience', 'Không rõ')}"
        )
    return "\n".join(lines)


def get_candidate_profile(user_id: str) -> str:
    """Return a candidate profile by its real UserID from USER_DATA_FINAL.csv."""
    candidate = _find_by_id(_load_candidates(), "UserID", user_id)
    if candidate is None:
        return f"LỖI: Không tìm thấy UserID '{user_id}'."

    return "\n".join(
        [
            f"ỨNG VIÊN [{candidate['UserID']}]: {candidate.get('User Name', 'Không rõ')}",
            f"Ngành: {candidate.get('Industry', 'Không rõ')}",
            f"Vị trí mong muốn: {candidate.get('Desired Job', 'Không rõ')}",
            f"Nơi làm việc mong muốn: {candidate.get('Workplace Desired', 'Không rõ')}",
            f"Mức lương mong muốn: {candidate.get('Desired Salary', 'Không rõ')}",
            f"Học vấn: {candidate.get('Degree', 'Không rõ')}",
            f"Kinh nghiệm: {candidate.get('Work Experience', 'Không rõ')}",
            f"Kỹ năng: {_shorten(candidate.get('Skills'), 900)}",
            f"Mục tiêu: {_shorten(candidate.get('Target'), 700)}",
        ]
    )


def get_resume_content(user_id: str) -> str:
    """Compatibility alias for get_candidate_profile."""
    return get_candidate_profile(user_id)


def score_candidate(job_id: str, user_id: str) -> str:
    """Provide a transparent, heuristic job-profile similarity score for HR review.

    This is decision support only. A human must review the source profile and
    job description before any interview or hiring decision.
    """
    job = _find_by_id(_load_jobs(), "JobID", job_id)
    candidate = _find_by_id(_load_candidates(), "UserID", user_id)
    if job is None:
        return f"LỖI: Không tìm thấy JobID '{job_id}'."
    if candidate is None:
        return f"LỖI: Không tìm thấy UserID '{user_id}'."

    job_title_terms = _keywords(job.get("Job Title"))
    candidate_role_terms = _keywords(candidate.get("Desired Job"))
    role_matches = sorted(job_title_terms & candidate_role_terms)
    role_score = round(15 * len(role_matches) / max(1, len(job_title_terms)))

    job_requirement_terms = _skill_keywords(job.get("Job Requirements", ""))
    candidate_skill_terms = _skill_keywords(candidate.get("Skills", ""))
    skill_matches = sorted(job_requirement_terms & candidate_skill_terms)
    requirement_frequency = _job_requirement_document_frequency()
    job_count = len(_load_jobs())
    if job_requirement_terms and job_count:
        def term_weight(term: str) -> float:
            return math.log((job_count + 1) / (requirement_frequency[term] + 1)) + 1

        total_weight = sum(term_weight(term) for term in job_requirement_terms)
        matched_weight = sum(term_weight(term) for term in skill_matches)
        skill_score = round(40 * matched_weight / total_weight)
    else:
        skill_score = 0

    required_experience = _experience_years(job.get("Years of Experience"))
    candidate_experience = _experience_years(candidate.get("Work Experience"))
    if required_experience is None or candidate_experience is None:
        experience_score = 0
        experience_note = "Không đủ dữ liệu để quy đổi"
    elif required_experience == 0:
        experience_score = 30
        experience_note = "Job không yêu cầu kinh nghiệm"
    else:
        experience_score = round(30 * min(candidate_experience / required_experience, 1))
        experience_note = (
            f"Ứng viên ~{candidate_experience:g} năm, "
            f"job yêu cầu từ {required_experience:g} năm"
        )

    job_industry = _normalize(job.get("Industry"))
    candidate_industry = _normalize(candidate.get("Industry"))
    industry_score = 10 if job_industry and (job_industry in candidate_industry or candidate_industry in job_industry) else 0

    job_location = _normalize(job.get("Job Address"))
    candidate_location = _normalize(candidate.get("Workplace Desired"))
    location_score = 5 if job_location and candidate_location and (job_location in candidate_location or candidate_location in job_location) else 0

    total_score = role_score + skill_score + experience_score + industry_score + location_score
    recommendation = (
        "Ưu tiên HR xem xét" if total_score >= 60 else "Cần HR xem xét thủ công thêm"
    )
    matched_display = ", ".join(skill_matches[:12]) or "Chưa phát hiện từ khóa trùng rõ ràng"

    return "\n".join(
        [
            f"ĐÁNH GIÁ HỖ TRỢ HR: UserID {user_id} với JobID {job_id}",
            f"Ứng viên: {candidate.get('User Name', 'Không rõ')}",
            f"Vị trí: {job.get('Job Title', 'Không rõ')}",
            f"Điểm heuristic: {total_score}/100",
            f"- Tương đồng vị trí: {role_score}/15 ({', '.join(role_matches) or 'không rõ'})",
            f"- Từ khóa kỹ năng/nhiệm vụ: {skill_score}/40 ({matched_display})",
            f"- Kinh nghiệm làm việc: {experience_score}/30 ({experience_note})",
            f"- Ngành: {industry_score}/10 | Địa điểm: {location_score}/5",
            f"Khuyến nghị: {recommendation}.",
            "Lưu ý: Điểm này chỉ hỗ trợ sàng lọc; HR phải kiểm tra JD và hồ sơ gốc trước quyết định.",
        ]
    )


AVAILABLE_TOOLS = {
    "search_jobs": search_jobs,
    "list_jobs": list_jobs,
    "get_job_description": get_job_description,
    "search_candidates": search_candidates,
    "get_candidate_profile": get_candidate_profile,
    "get_resume_content": get_resume_content,
    "score_candidate": score_candidate,
}
