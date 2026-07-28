"""
🛠️ TOOL REGISTRY — AI LEARNING PATH ADVISOR
Role 2: Tool & Spec Engineer | Mốc 3

Mục tiêu:
- Đọc dữ liệu từ config/course_catalog.json (single source of truth).
- Hỗ trợ prompt ngắn hoặc dài bằng retrieval + relevance scoring.
- Tool chỉ trả FACTS; LLM chịu trách nhiệm đưa ra JUDGMENT.
- Giữ nguyên API của 5 public tools để không phá tích hợp Role 3/Role 4.

Biến môi trường hỗ trợ:
- COURSE_CATALOG_PATH: ghi đè đường dẫn catalog, hữu ích khi test.
- TOOLS_DEBUG=1: in chi tiết lỗi ra stderr, không lộ trong Observation.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable


# =====================================================================
# ERROR CONTRACT
# =====================================================================

SYSTEM_LOAD_ERROR = "LỖI HỆ THỐNG: Không thể tải database khóa học."
SYSTEM_PROCESS_ERROR = "LỖI HỆ THỐNG: Không thể xử lý yêu cầu."

_VALID_LEVELS = ("beginner", "basic", "intermediate")
_VALID_BUDGETS = ("low", "medium", "high")
_VALID_TIME_LEVELS = ("low", "medium", "high")
_VALID_PRACTICE_LEVELS = ("low", "medium", "high")
_MIN_ALIAS_TOKEN_LENGTH = 3
_DEFAULT_TOP_K = 5

_TOOL_DEBUG = os.getenv("TOOLS_DEBUG", "").strip() == "1"


# =====================================================================
# NORMALIZATION
# =====================================================================

def _normalize_text(value: Any) -> str:
    """Chuẩn hóa chuỗi: lowercase, bỏ nháy ngoài và gọn khoảng trắng."""
    if value is None:
        return ""
    text = str(value).strip().strip("'\"`").strip().casefold()
    return " ".join(text.split())


def _tokenize(value: Any) -> list[str]:
    """
    Tách token an toàn để alias ngắn như ai/ml/dl chỉ match từ độc lập.

    Ví dụ:
        "Tôi muốn học AI/ML" -> ["tôi", "muốn", "học", "ai", "ml"]
        "html" -> ["html"], không chứa token "ml".
    """
    text = _normalize_text(value)
    return re.findall(r"[0-9a-zA-ZÀ-ỹ]+", text, flags=re.UNICODE)


def _normalize_code(value: Any) -> str:
    """Chuẩn hóa mã khóa học về chữ hoa."""
    return _normalize_text(value).upper()


def _normalize_string_list(values: Iterable[Any]) -> list[str]:
    """Chuẩn hóa list chuỗi, bỏ rỗng và trùng, giữ thứ tự."""
    result: list[str] = []
    for value in values:
        normalized = _normalize_text(value)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _is_phrase_match(query: str, candidate: str) -> bool:
    """
    Match query/candidate an toàn.

    Alias <= 2 ký tự như ML, DL, AI chỉ match theo token độc lập.
    Các cụm dài hơn hỗ trợ exact và substring hai chiều.
    """
    q = _normalize_text(query)
    c = _normalize_text(candidate)
    if not q or not c:
        return False
    if q == c:
        return True

    if len(q) < _MIN_ALIAS_TOKEN_LENGTH:
        return q in set(_tokenize(c))
    if len(c) < _MIN_ALIAS_TOKEN_LENGTH:
        return c in set(_tokenize(q))

    return q in c or c in q


def _contains_query_tokens(query: str, candidate: str) -> bool:
    """True khi toàn bộ token có ý nghĩa của query xuất hiện trong candidate."""
    query_tokens = set(_tokenize(query))
    candidate_tokens = set(_tokenize(candidate))
    if not query_tokens:
        return False
    return query_tokens.issubset(candidate_tokens)


# =====================================================================
# DATABASE LOADING & VALIDATION
# =====================================================================

def _get_catalog_path() -> Path:
    """
    Trả đường dẫn catalog.

    Ưu tiên COURSE_CATALOG_PATH khi test. Mặc định:
    <project_root>/config/course_catalog.json
    với project_root là thư mục cha của src/.
    """
    override = os.getenv("COURSE_CATALOG_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / "config" / "course_catalog.json"


def _debug(message: str) -> None:
    """Log debug ra stderr khi TOOLS_DEBUG=1."""
    if _TOOL_DEBUG:
        print(f"[tools.py] {message}", file=sys.stderr)


def _validate_string_list(
    obj: dict[str, Any],
    field: str,
    context: str,
    *,
    required: bool = True,
) -> None:
    """Validate field list[str]."""
    if field not in obj:
        if required:
            raise ValueError(f"{context} thiếu field '{field}'")
        return
    value = obj[field]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{context}.{field} phải là list[str]")


def _validate_catalog_schema(catalog: Any) -> None:
    """Validate cấu trúc catalog, reference và cycle prerequisite."""
    if not isinstance(catalog, dict):
        raise ValueError("Root JSON phải là object")

    for section in ("time_rules", "budget_rank", "courses"):
        if section not in catalog:
            raise ValueError(f"Thiếu section '{section}'")

    time_rules = catalog["time_rules"]
    budget_rank = catalog["budget_rank"]
    courses = catalog["courses"]
    tracks = catalog.get("learning_tracks", {})

    if not isinstance(time_rules, dict):
        raise ValueError("time_rules phải là object")
    if not isinstance(budget_rank, dict):
        raise ValueError("budget_rank phải là object")
    if not isinstance(courses, dict) or not courses:
        raise ValueError("courses phải là object không rỗng")
    if not isinstance(tracks, dict):
        raise ValueError("learning_tracks phải là object")

    for level in _VALID_TIME_LEVELS:
        rule = time_rules.get(level)
        if not isinstance(rule, dict):
            raise ValueError(f"time_rules thiếu '{level}'")
        hours = rule.get("max_hours_per_week")
        if isinstance(hours, bool) or not isinstance(hours, int) or hours <= 0:
            raise ValueError(
                f"time_rules.{level}.max_hours_per_week phải là int dương"
            )

    for level in _VALID_BUDGETS:
        rank = budget_rank.get(level)
        if isinstance(rank, bool) or not isinstance(rank, int) or rank <= 0:
            raise ValueError(f"budget_rank.{level} phải là int dương")

    required_course_fields = {
        "title": str,
        "category": str,
        "minimum_profile_level": str,
        "duration_weeks": int,
        "hours_per_week": int,
        "time_level": str,
        "budget_level": str,
        "practice_level": str,
        "has_projects": bool,
        "description": str,
    }

    for raw_code, course in courses.items():
        context = f"courses.{raw_code}"
        if not isinstance(raw_code, str) or not raw_code.strip():
            raise ValueError("Mã khóa học phải là chuỗi không rỗng")
        if not isinstance(course, dict):
            raise ValueError(f"{context} phải là object")

        for field, expected_type in required_course_fields.items():
            if field not in course:
                raise ValueError(f"{context} thiếu field '{field}'")
            value = course[field]
            if expected_type is int and isinstance(value, bool):
                raise ValueError(f"{context}.{field} phải là int")
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"{context}.{field} phải là {expected_type.__name__}"
                )

        for field in (
            "goals",
            "specializations",
            "prerequisites",
            "required_skills",
            "skills_gained",
        ):
            _validate_string_list(course, field, context)

        # aliases/keywords được khuyến nghị nhưng optional để tương thích JSON Mốc 2.
        _validate_string_list(course, "aliases", context, required=False)
        _validate_string_list(course, "keywords", context, required=False)

        if course["minimum_profile_level"] not in _VALID_LEVELS:
            raise ValueError(f"{context}.minimum_profile_level không hợp lệ")
        if course["time_level"] not in _VALID_TIME_LEVELS:
            raise ValueError(f"{context}.time_level không hợp lệ")
        if course["budget_level"] not in _VALID_BUDGETS:
            raise ValueError(f"{context}.budget_level không hợp lệ")
        if course["practice_level"] not in _VALID_PRACTICE_LEVELS:
            raise ValueError(f"{context}.practice_level không hợp lệ")
        if course["duration_weeks"] <= 0 or course["hours_per_week"] <= 0:
            raise ValueError(f"{context} có duration/hours không hợp lệ")

        project_type = course.get("project_type")
        if project_type is not None and not isinstance(project_type, str):
            raise ValueError(f"{context}.project_type phải là str hoặc null")

    valid_codes = set(courses)
    for code, course in courses.items():
        for prereq in course["prerequisites"]:
            if prereq not in valid_codes:
                raise ValueError(
                    f"Course '{code}' tham chiếu prerequisite không tồn tại '{prereq}'"
                )

    for key, track in tracks.items():
        context = f"learning_tracks.{key}"
        if not isinstance(track, dict):
            raise ValueError(f"{context} phải là object")
        for field in ("title", "description"):
            if not isinstance(track.get(field), str) or not track[field].strip():
                raise ValueError(f"{context}.{field} phải là str không rỗng")
        _validate_string_list(track, "aliases", context)
        _validate_string_list(track, "keywords", context, required=False)

        targets = track.get("targets")
        sequence = track.get("course_sequence")
        if targets is None and sequence is None:
            raise ValueError(
                f"{context} cần 'targets' hoặc 'course_sequence'"
            )
        if targets is not None:
            _validate_string_list(track, "targets", context)
            for target in targets:
                if target not in valid_codes:
                    raise ValueError(
                        f"{context} tham chiếu target không tồn tại '{target}'"
                    )
        if sequence is not None:
            _validate_string_list(track, "course_sequence", context)
            for target in sequence:
                if target not in valid_codes:
                    raise ValueError(
                        f"{context} tham chiếu course không tồn tại '{target}'"
                    )

    _validate_prerequisite_graph(courses)


def _validate_prerequisite_graph(courses: dict[str, dict[str, Any]]) -> None:
    """Phát hiện cycle trong đồ thị prerequisite bằng DFS."""
    state: dict[str, int] = {code: 0 for code in courses}  # 0=new, 1=visiting, 2=done

    def visit(code: str, path: list[str]) -> None:
        if state[code] == 1:
            cycle = " -> ".join([*path, code])
            raise ValueError(f"Phát hiện cycle prerequisite: {cycle}")
        if state[code] == 2:
            return

        state[code] = 1
        for prereq in courses[code]["prerequisites"]:
            visit(prereq, [*path, code])
        state[code] = 2

    for code in courses:
        if state[code] == 0:
            visit(code, [])


def _load_catalog() -> dict[str, Any]:
    """Đọc và validate catalog JSON."""
    path = _get_catalog_path()
    try:
        with path.open("r", encoding="utf-8") as file:
            catalog = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError("Không tìm thấy course catalog") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Course catalog không phải JSON hợp lệ") from exc
    except OSError as exc:
        raise RuntimeError("Không thể đọc course catalog") from exc

    _validate_catalog_schema(catalog)
    return catalog


def _initialize_catalog() -> tuple[dict[str, Any], str | None]:
    """Load catalog nhưng không để import module bị crash."""
    try:
        return _load_catalog(), None
    except Exception as exc:  # outer boundary của loader
        _debug(f"Catalog load error: {type(exc).__name__}: {exc}")
        return {}, str(exc)


_CATALOG, _CATALOG_LOAD_ERROR = _initialize_catalog()
AI_COURSES: dict[str, dict[str, Any]] = _CATALOG.get("courses", {})
LEARNING_TRACKS: dict[str, dict[str, Any]] = _CATALOG.get("learning_tracks", {})
TIME_RULES: dict[str, dict[str, int]] = _CATALOG.get("time_rules", {})
BUDGET_RANK: dict[str, int] = _CATALOG.get(
    "budget_rank",
    {"low": 1, "medium": 2, "high": 3},
)


def _get_catalog_error() -> str | None:
    """Trả lỗi an toàn nếu catalog không load thành công."""
    if _CATALOG_LOAD_ERROR is not None:
        return SYSTEM_LOAD_ERROR
    return None


def _system_error(tool_name: str, exc: Exception) -> str:
    """Ẩn lỗi khỏi Observation, log stderr khi debug."""
    _debug(f"{tool_name}: {type(exc).__name__}: {exc}")
    return SYSTEM_PROCESS_ERROR


# =====================================================================
# RETRIEVAL HELPERS
# =====================================================================

def _course_aliases(code: str, course: dict[str, Any]) -> list[str]:
    """Tập alias runtime, có fallback để JSON cũ vẫn dùng được."""
    aliases = list(course.get("aliases", []))
    aliases.extend(
        [
            code,
            course.get("title", ""),
            course.get("category", "").replace("_", " "),
        ]
    )
    return _normalize_string_list(aliases)


def _course_keywords(course: dict[str, Any]) -> list[str]:
    """Tập keyword runtime từ field explicit và metadata khóa học."""
    values: list[str] = list(course.get("keywords", []))
    values.extend(course.get("goals", []))
    values.extend(course.get("specializations", []))
    values.extend(course.get("skills_gained", []))
    return _normalize_string_list(values)


def _field_best_match(
    query: str,
    values: Iterable[Any],
    exact_score: int,
    contain_score: int,
    label: str,
) -> tuple[int, str | None]:
    """Tìm match tốt nhất trong một field."""
    best = 0
    evidence: str | None = None
    q = _normalize_text(query)
    query_tokens = set(_tokenize(q))

    for raw in values:
        value = _normalize_text(raw)
        if not value:
            continue

        if q == value:
            score = exact_score
        elif len(value) < _MIN_ALIAS_TOKEN_LENGTH:
            score = contain_score if value in query_tokens else 0
        elif len(q) < _MIN_ALIAS_TOKEN_LENGTH:
            score = contain_score if q in set(_tokenize(value)) else 0
        elif q in value or value in q:
            score = contain_score
        elif _contains_query_tokens(q, value):
            score = max(contain_score - 5, 1)
        else:
            score = 0

        if score > best:
            best = score
            evidence = f'{label} "{raw}"'

    return best, evidence


def _score_course_match(
    query: str,
    code: str,
    course: dict[str, Any],
) -> tuple[int, list[str]]:
    """Tính relevance score và bằng chứng match của một course."""
    q = _normalize_text(query)
    if not q:
        return 1, ["truy vấn rỗng: trả catalog"]

    score = 0
    evidence: list[str] = []

    code_score, code_ev = _field_best_match(q, [code], 120, 100, "mã")
    title_score, title_ev = _field_best_match(
        q, [course.get("title", "")], 110, 85, "tiêu đề"
    )
    alias_score, alias_ev = _field_best_match(
        q, _course_aliases(code, course), 100, 90, "alias"
    )
    category_score, category_ev = _field_best_match(
        q, [course.get("category", "").replace("_", " ")], 75, 70, "category"
    )
    specialization_score, specialization_ev = _field_best_match(
        q, course.get("specializations", []), 70, 65, "specialization"
    )
    goal_score, goal_ev = _field_best_match(
        q, course.get("goals", []), 65, 60, "goal"
    )
    keyword_score, keyword_ev = _field_best_match(
        q, _course_keywords(course), 60, 55, "keyword"
    )
    project_score, project_ev = _field_best_match(
        q, [course.get("project_type") or ""], 50, 45, "project"
    )
    description_score, description_ev = _field_best_match(
        q, [course.get("description", "")], 35, 30, "mô tả"
    )
    required_score, required_ev = _field_best_match(
        q, course.get("required_skills", []), 25, 20, "kỹ năng cần"
    )
    gained_score, gained_ev = _field_best_match(
        q, course.get("skills_gained", []), 25, 20, "kỹ năng đạt"
    )

    # Chỉ lấy match mạnh nhất trong nhóm identity và cộng có kiểm soát.
    identity_candidates = [
        (code_score, code_ev),
        (title_score, title_ev),
        (alias_score, alias_ev),
    ]
    identity_score, identity_ev = max(identity_candidates, key=lambda item: item[0])
    if identity_score:
        score += identity_score
        if identity_ev:
            evidence.append(identity_ev)

    for field_score, field_ev in (
        (category_score, category_ev),
        (specialization_score, specialization_ev),
        (goal_score, goal_ev),
        (keyword_score, keyword_ev),
        (project_score, project_ev),
        (description_score, description_ev),
        (required_score, required_ev),
        (gained_score, gained_ev),
    ):
        if field_score:
            score += field_score
            if field_ev and field_ev not in evidence:
                evidence.append(field_ev)

    # Token overlap nhỏ giúp prompt dài vẫn retrieve được.
    query_tokens = set(_tokenize(q))
    haystack_tokens = set(
        _tokenize(
            " ".join(
                [
                    code,
                    course.get("title", ""),
                    course.get("category", ""),
                    course.get("description", ""),
                    " ".join(_course_aliases(code, course)),
                    " ".join(_course_keywords(course)),
                    " ".join(course.get("required_skills", [])),
                    " ".join(course.get("skills_gained", [])),
                ]
            )
        )
    )
    stopwords = {
        "tôi", "toi", "em", "mình", "minh", "muốn", "muon", "học", "hoc",
        "làm", "lam", "và", "va", "nhưng", "nhung", "hiện", "hien", "tại",
        "tai", "mới", "moi", "chỉ", "chi", "biết", "biet", "được", "duoc",
        "cho", "với", "voi", "có", "co", "một", "mot", "the", "a", "an",
        "to", "want", "learn", "course",
    }
    meaningful = {token for token in query_tokens if token not in stopwords}
    overlap = meaningful & haystack_tokens
    if overlap:
        bonus = min(len(overlap) * 8, 32)
        score += bonus
        evidence.append("token: " + ", ".join(sorted(overlap)))

    return score, evidence[:4]


def _retrieve_courses(
    query: str,
    *,
    level: str = "",
    budget_level: str = "",
    top_k: int = _DEFAULT_TOP_K,
) -> list[tuple[str, dict[str, Any], int, list[str]]]:
    """Retrieve, filter và rank course."""
    results: list[tuple[str, dict[str, Any], int, list[str]]] = []
    for code, course in AI_COURSES.items():
        if level and course["minimum_profile_level"] != level:
            continue
        if budget_level and (
            BUDGET_RANK[course["budget_level"]] > BUDGET_RANK[budget_level]
        ):
            continue

        score, evidence = _score_course_match(query, code, course)
        threshold = 1 if not _normalize_text(query) else 20
        if score >= threshold:
            results.append((code, course, score, evidence))

    results.sort(key=lambda item: (-item[2], item[0]))
    return results[:top_k]


def _track_targets(track: dict[str, Any]) -> list[str]:
    """Lấy target của track, hỗ trợ cả schema targets và course_sequence."""
    if isinstance(track.get("targets"), list):
        return list(track["targets"])
    sequence = track.get("course_sequence", [])
    return list(sequence[-1:]) if sequence else []


def _score_track_match(
    query: str,
    key: str,
    track: dict[str, Any],
) -> tuple[int, list[str]]:
    """Tính relevance score cho learning track."""
    q = _normalize_text(query)
    score = 0
    evidence: list[str] = []

    key_score, key_ev = _field_best_match(
        q, [key.replace("_", " ")], 120, 90, "track key"
    )
    title_score, title_ev = _field_best_match(
        q, [track.get("title", "")], 110, 85, "track title"
    )
    alias_score, alias_ev = _field_best_match(
        q, track.get("aliases", []), 100, 90, "track alias"
    )
    keyword_score, keyword_ev = _field_best_match(
        q, track.get("keywords", []), 80, 75, "track keyword"
    )
    description_score, description_ev = _field_best_match(
        q, [track.get("description", "")], 45, 40, "track description"
    )

    identity_score, identity_ev = max(
        [(key_score, key_ev), (title_score, title_ev), (alias_score, alias_ev)],
        key=lambda item: item[0],
    )
    if identity_score:
        score += identity_score
        if identity_ev:
            evidence.append(identity_ev)

    for field_score, field_ev in (
        (keyword_score, keyword_ev),
        (description_score, description_ev),
    ):
        if field_score:
            score += field_score
            if field_ev:
                evidence.append(field_ev)

    # Match qua target course giúp query "RAG" tìm được track GenAI.
    for target_code in _track_targets(track):
        course = AI_COURSES.get(target_code)
        if not course:
            continue
        target_score, target_evidence = _score_course_match(q, target_code, course)
        if target_score >= 80:
            score += min(target_score // 3, 50)
            evidence.append(f"target {target_code}: {', '.join(target_evidence[:1])}")

    career_phrases = (
        "thực tập",
        "intern",
        "ai engineer",
        "muốn làm",
        "muốn trở thành",
        "bắt đầu từ đâu",
        "học từ đầu",
        "roadmap",
        "lộ trình",
    )
    if any(phrase in q for phrase in career_phrases):
        score += 20
        evidence.append("câu hỏi mang ý định lộ trình/nghề nghiệp")

    return score, evidence[:4]


def _retrieve_tracks(
    query: str,
    *,
    top_k: int = 3,
) -> list[tuple[str, dict[str, Any], int, list[str]]]:
    """Retrieve và rank learning track."""
    results: list[tuple[str, dict[str, Any], int, list[str]]] = []
    for key, track in LEARNING_TRACKS.items():
        score, evidence = _score_track_match(query, key, track)
        if score >= 25:
            results.append((key, track, score, evidence))
    results.sort(key=lambda item: (-item[2], item[0]))
    return results[:top_k]


def _detect_query_intent(query: str) -> str:
    """Phát hiện intent đơn giản bằng rule-based keywords."""
    q = _normalize_text(query)
    intents: set[str] = set()

    rules = {
        "learning_track": (
            "lộ trình", "roadmap", "học từ đầu", "bắt đầu từ đâu",
            "muốn làm", "trở thành", "thực tập", "ai engineer",
            "xây ai agent", "muốn học",
        ),
        "course_detail": (
            "chi tiết", "nội dung", "học gì", "môn này", "khóa này",
            "course detail", "tiên quyết", "prerequisite",
        ),
        "readiness": (
            "học được chưa", "đủ điều kiện", "sẵn sàng chưa",
            "còn thiếu gì", "cần biết gì trước",
        ),
        "constraint_filter": (
            "giờ mỗi tuần", "thời gian", "ngân sách", "budget",
            "ít thời gian", "chi phí", "rẻ",
        ),
        "course_search": ("khóa", "course", "môn", "tìm"),
    }

    for intent, phrases in rules.items():
        if any(phrase in q for phrase in phrases):
            intents.add(intent)

    if len(intents) > 1:
        return "mixed"
    if len(intents) == 1:
        return next(iter(intents))

    # Query ngắn là alias/course search.
    if len(_tokenize(q)) <= 3:
        return "course_search"
    return "unknown"


# =====================================================================
# GRAPH & FORMAT HELPERS
# =====================================================================

def _resolve_prerequisite_chain(targets: list[str]) -> list[str]:
    """Suy ra thứ tự prerequisite ổn định, prerequisite luôn trước target."""
    ordered: list[str] = []
    permanent: set[str] = set()
    temporary: set[str] = set()

    def visit(code: str) -> None:
        if code in permanent:
            return
        if code in temporary:
            raise ValueError(f"Cycle prerequisite tại '{code}'")
        if code not in AI_COURSES:
            raise ValueError(f"Course không tồn tại '{code}'")

        temporary.add(code)
        for prereq in AI_COURSES[code]["prerequisites"]:
            visit(prereq)
        temporary.remove(code)
        permanent.add(code)
        ordered.append(code)

    for target in targets:
        visit(target)
    return ordered


def _format_course_summary(
    code: str,
    course: dict[str, Any],
    *,
    score: int | None = None,
    evidence: list[str] | None = None,
) -> str:
    """Format một course retrieval result."""
    base = (
        f"{code} — {course['title']} | "
        f"level={course['minimum_profile_level']} | "
        f"{course['hours_per_week']}h/tuần | "
        f"budget={course['budget_level']}"
    )
    if score is not None:
        base += f" | score={score}"
    if evidence:
        base += "\n   Khớp vì: " + "; ".join(evidence)
    return base


def _format_course_detail(code: str, course: dict[str, Any]) -> str:
    """Format chi tiết đầy đủ của course."""
    def join(field: str, empty: str = "(không có)") -> str:
        values = course.get(field, [])
        return ", ".join(values) if values else empty

    project = course.get("project_type") or "(không có project)"
    aliases = join("aliases")
    keywords = join("keywords")

    return (
        f"Mã khóa học      : {code}\n"
        f"Tên khóa         : {course['title']}\n"
        f"Aliases          : {aliases}\n"
        f"Keywords         : {keywords}\n"
        f"Lĩnh vực         : {course['category']}\n"
        f"Trình độ tối thiểu: {course['minimum_profile_level']}\n"
        f"Mục tiêu         : {join('goals')}\n"
        f"Chuyên ngành     : {join('specializations')}\n"
        f"Tiên quyết       : {join('prerequisites')}\n"
        f"Kỹ năng cần      : {join('required_skills', '(không yêu cầu)')}\n"
        f"Kỹ năng đạt      : {join('skills_gained')}\n"
        f"Thời lượng       : {course['duration_weeks']} tuần\n"
        f"Cường độ         : {course['hours_per_week']} giờ/tuần "
        f"(mức {course['time_level']})\n"
        f"Ngân sách        : {course['budget_level']}\n"
        f"Thực hành        : {course['practice_level']}\n"
        f"Project          : {project}\n"
        f"Mô tả            : {course['description']}"
    )


def _validate_optional_choice(
    value: Any,
    allowed: tuple[str, ...],
    field_name: str,
) -> tuple[str, str | None]:
    """Validate optional enum; trả (normalized, error)."""
    if value is None:
        return "", None
    if not isinstance(value, str):
        return "", f"LỖI THAM SỐ: {field_name} phải là chuỗi hoặc None."
    normalized = _normalize_text(value)
    if not normalized:
        return "", None
    if normalized not in allowed:
        return (
            "",
            f"LỖI THAM SỐ: {field_name} '{value}' không hợp lệ. "
            f"Chỉ nhận: {', '.join(allowed)}.",
        )
    return normalized, None


def _resolve_hours(value: Any) -> int | None:
    """Quy đổi int, numeric string hoặc ít/vừa/nhiều thành giờ."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if not isinstance(value, str):
        return None

    normalized = _normalize_text(value)
    if normalized.isdigit():
        hours = int(normalized)
        return hours if hours > 0 else None

    aliases = {
        "ít": "low", "it": "low", "low": "low", "thấp": "low", "thap": "low",
        "vừa": "medium", "vua": "medium", "medium": "medium",
        "trung bình": "medium", "trung binh": "medium",
        "nhiều": "high", "nhieu": "high", "high": "high", "cao": "high",
    }
    level = aliases.get(normalized)
    if level is None or level not in TIME_RULES:
        return None
    return TIME_RULES[level]["max_hours_per_week"]


# =====================================================================
# PUBLIC TOOLS
# =====================================================================

def search_ai_courses(
    keyword: str | None = None,
    level: str | None = None,
    budget_level: str | None = None,
) -> str:
    """
    Retrieve khóa học liên quan từ keyword hoặc câu tự nhiên dài.

    Tool trả intent, track liên quan, top course và bằng chứng match.
    Tool không tự đưa ra lời khuyên cuối cùng.
    """
    try:
        catalog_error = _get_catalog_error()
        if catalog_error:
            return catalog_error

        if keyword is not None and not isinstance(keyword, str):
            return "LỖI THAM SỐ: keyword phải là chuỗi hoặc None."

        clean_level, error = _validate_optional_choice(
            level, _VALID_LEVELS, "level"
        )
        if error:
            return error
        clean_budget, error = _validate_optional_choice(
            budget_level, _VALID_BUDGETS, "budget_level"
        )
        if error:
            return error

        query = _normalize_text(keyword)
        courses = _retrieve_courses(
            query,
            level=clean_level,
            budget_level=clean_budget,
            top_k=_DEFAULT_TOP_K,
        )

        if not courses:
            return (
                "KHÔNG CÓ KẾT QUẢ: Không tìm thấy khóa học phù hợp. "
                "Có thể thử: Python, Machine Learning, Deep Learning, NLP, "
                "Generative AI hoặc AI Agent."
            )

        intent = _detect_query_intent(query)
        tracks = _retrieve_tracks(query, top_k=3) if query else []

        lines = [
            "KẾT QUẢ: Đã retrieve dữ liệu khóa học.",
            f"INTENT PHÁT HIỆN: {intent}",
            f"QUERY ĐÃ CHUẨN HÓA: {query or '(không có — trả catalog)'}",
        ]

        if tracks:
            lines.append("TRACK LIÊN QUAN:")
            for key, track, score, evidence in tracks:
                lines.append(
                    f"- {key} — {track['title']} | score={score}\n"
                    f"  Khớp vì: {'; '.join(evidence) or '(không có)'}"
                )

        lines.append("KHÓA HỌC LIÊN QUAN:")
        for index, (code, course, score, evidence) in enumerate(courses, start=1):
            lines.append(
                f"{index}. "
                + _format_course_summary(
                    code,
                    course,
                    score=score,
                    evidence=evidence,
                )
            )

        return "\n".join(lines)

    except Exception as exc:
        return _system_error("search_ai_courses", exc)


def get_ai_course_detail(course_code: str) -> str:
    """Lấy toàn bộ facts của một khóa học theo mã."""
    try:
        catalog_error = _get_catalog_error()
        if catalog_error:
            return catalog_error

        if not isinstance(course_code, str):
            return "LỖI THAM SỐ: course_code phải là chuỗi."

        code = _normalize_code(course_code)
        if not code:
            return "LỖI: Mã khóa học không được để trống."

        course = AI_COURSES.get(code)
        if course is None:
            valid = ", ".join(AI_COURSES)
            return (
                f"LỖI: Không tìm thấy khóa học '{code}'. "
                f"Các mã hợp lệ: {valid}."
            )

        return f"KẾT QUẢ: Chi tiết khóa học {code}.\n{_format_course_detail(code, course)}"

    except Exception as exc:
        return _system_error("get_ai_course_detail", exc)


def _skill_matches(required: str, owned: str) -> bool:
    """
    Match kỹ năng có kiểm soát.

    Không cho "python" match skill ghép "python và oop".
    JSON nên tách skill ghép thành các skill độc lập.
    """
    r = _normalize_text(required)
    o = _normalize_text(owned)
    if not r or not o:
        return False
    if r == o:
        return True

    # Skill ghép bằng "và"/"and" yêu cầu tất cả thành phần, không fuzzy bằng 1 từ.
    if " và " in r or " and " in r:
        return False

    synonym_groups = [
        {"python", "python cơ bản", "python basic"},
        {"oop", "lập trình hướng đối tượng", "hướng đối tượng"},
        {"thống kê", "xác suất thống kê", "xác suất thống kê cơ bản"},
        {"deep learning", "deep learning căn bản", "học sâu"},
        {"machine learning", "machine learning căn bản", "học máy"},
        {"xử lý dữ liệu", "làm sạch dữ liệu", "phân tích dữ liệu"},
    ]
    for group in synonym_groups:
        normalized_group = {_normalize_text(item) for item in group}
        if r in normalized_group and o in normalized_group:
            return True

    if len(r) >= 4 and len(o) >= 4:
        return r in o or o in r
    return False


def check_course_readiness(
    course_code: str,
    current_skills: list[str],
) -> str:
    """Đối chiếu skill hiện có với required_skills của course."""
    try:
        catalog_error = _get_catalog_error()
        if catalog_error:
            return catalog_error

        if not isinstance(course_code, str):
            return "LỖI THAM SỐ: course_code phải là chuỗi."
        code = _normalize_code(course_code)
        if not code:
            return "LỖI: Mã khóa học không được để trống."

        course = AI_COURSES.get(code)
        if course is None:
            return f"LỖI: Không tìm thấy khóa học '{code}'."

        if not isinstance(current_skills, list):
            return "LỖI THAM SỐ: current_skills phải là list[str]."
        if any(not isinstance(skill, str) for skill in current_skills):
            return "LỖI THAM SỐ: Mỗi phần tử trong current_skills phải là chuỗi."

        owned = _normalize_string_list(current_skills)
        required = _normalize_string_list(course["required_skills"])

        matched: list[str] = []
        missing: list[str] = []
        for required_skill in required:
            if any(_skill_matches(required_skill, owned_skill) for owned_skill in owned):
                matched.append(required_skill)
            else:
                missing.append(required_skill)

        prerequisites = ", ".join(course["prerequisites"]) or "(không có)"
        body = (
            f"Khóa đang kiểm tra : {code} — {course['title']}\n"
            f"- Trình độ tối thiểu: {course['minimum_profile_level']}\n"
            f"- Môn tiên quyết    : {prerequisites}\n"
            f"- Kỹ năng yêu cầu   : {', '.join(required) or '(không yêu cầu)'}\n"
            f"- Kỹ năng đã khai báo: {', '.join(owned) or '(chưa khai báo)'}\n"
            f"- Kỹ năng đã khớp   : {', '.join(matched) or '(không có)'}\n"
            f"- Kỹ năng còn thiếu : {', '.join(missing) or '(không có)'}"
        )

        if missing:
            return (
                f"CHƯA SẴN SÀNG: Còn thiếu {len(missing)}/{len(required)} "
                f"kỹ năng.\n{body}"
            )
        return f"SẴN SÀNG: Đã đủ kỹ năng bắt buộc.\n{body}"

    except Exception as exc:
        return _system_error("check_course_readiness", exc)


def get_learning_track(goal: str) -> str:
    """Retrieve learning track từ prompt ngắn hoặc câu tự nhiên dài."""
    try:
        catalog_error = _get_catalog_error()
        if catalog_error:
            return catalog_error

        if not isinstance(goal, str):
            return "LỖI THAM SỐ: goal phải là chuỗi."
        query = _normalize_text(goal)
        if not query:
            return "LỖI: Mục tiêu học không được để trống."
        if not LEARNING_TRACKS:
            return (
                "KHÔNG CÓ LỘ TRÌNH: Database chưa khai báo learning_tracks."
            )

        results = _retrieve_tracks(query, top_k=3)
        if not results:
            valid = ", ".join(
                track["title"] for track in LEARNING_TRACKS.values()
            )
            return (
                f"KHÔNG CÓ LỘ TRÌNH: Không tìm thấy lộ trình cho '{query}'. "
                f"Các lựa chọn hiện có: {valid}."
            )

        key, track, score, evidence = results[0]
        if "course_sequence" in track and track["course_sequence"]:
            sequence = list(track["course_sequence"])
        else:
            sequence = _resolve_prerequisite_chain(_track_targets(track))

        total_weeks = sum(AI_COURSES[code]["duration_weeks"] for code in sequence)
        steps = []
        for index, code in enumerate(sequence, start=1):
            course = AI_COURSES[code]
            steps.append(
                f"{index}. {code} — {course['title']} | "
                f"{course['duration_weeks']} tuần | "
                f"{course['hours_per_week']}h/tuần | "
                f"budget={course['budget_level']}"
            )

        related_tracks = [
            f"- {other_key} — {other_track['title']} | score={other_score}"
            for other_key, other_track, other_score, _ in results[1:]
        ]

        lines = [
            "KẾT QUẢ: Đã retrieve lộ trình phù hợp.",
            f"INTENT PHÁT HIỆN: {_detect_query_intent(query)}",
            f"TRACK KEY: {key}",
            f"TÊN LỘ TRÌNH: {track['title']}",
            f"MÔ TẢ: {track['description']}",
            f"ĐỘ LIÊN QUAN: score={score}",
            f"KHỚP VÌ: {'; '.join(evidence) or '(không có)'}",
            f"TARGETS: {', '.join(_track_targets(track))}",
            f"THỨ TỰ HỌC: {' → '.join(sequence)}",
            f"TỔNG THỜI GIAN: {total_weeks} tuần (ước tính nếu học tuần tự)",
            "CHI TIẾT:",
            *steps,
        ]
        if related_tracks:
            lines.extend(["TRACK LIÊN QUAN KHÁC:", *related_tracks])
        return "\n".join(lines)

    except Exception as exc:
        return _system_error("get_learning_track", exc)


def filter_courses_by_constraints(
    course_codes: list[str],
    available_hours_per_week: int | str,
    budget_level: str,
) -> str:
    """Phân loại course theo thời gian và khả năng chi trả."""
    try:
        catalog_error = _get_catalog_error()
        if catalog_error:
            return catalog_error

        if not isinstance(course_codes, list):
            return "LỖI THAM SỐ: course_codes phải là list[str]."
        if any(not isinstance(code, str) for code in course_codes):
            return "LỖI THAM SỐ: Mỗi phần tử trong course_codes phải là chuỗi."
        if not course_codes:
            return "KHÔNG CÓ KẾT QUẢ: Danh sách course_codes rỗng."

        max_hours = _resolve_hours(available_hours_per_week)
        if max_hours is None:
            return (
                "LỖI THAM SỐ: available_hours_per_week phải là int dương, "
                "chuỗi số hoặc ít/vừa/nhiều."
            )

        clean_budget, error = _validate_optional_choice(
            budget_level, _VALID_BUDGETS, "budget_level"
        )
        if error or not clean_budget:
            return error or "LỖI THAM SỐ: budget_level không được để trống."

        budget_cap = BUDGET_RANK[clean_budget]
        fits: list[str] = []
        unfits: list[str] = []
        invalids: list[str] = []

        for raw_code in course_codes:
            code = _normalize_code(raw_code)
            course = AI_COURSES.get(code)
            if course is None:
                invalids.append(f"- {raw_code}: mã không tồn tại")
                continue

            time_ok = course["hours_per_week"] <= max_hours
            budget_ok = BUDGET_RANK[course["budget_level"]] <= budget_cap
            summary = (
                f"{code} — {course['title']} | "
                f"{course['hours_per_week']}h/tuần | "
                f"budget={course['budget_level']}"
            )

            if time_ok and budget_ok:
                fits.append(f"- {summary}")
                continue

            reasons = []
            if not time_ok:
                reasons.append(
                    f"thiếu thời gian (cần {course['hours_per_week']}h, có {max_hours}h)"
                )
            if not budget_ok:
                reasons.append(
                    f"vượt ngân sách (khóa={course['budget_level']}, "
                    f"người học={clean_budget})"
                )
            unfits.append(f"- {summary}: {'; '.join(reasons)}")

        lines = [
            f"KẾT QUẢ: Đã lọc {len(course_codes)} khóa với "
            f"{max_hours}h/tuần và budget={clean_budget}.",
            "PHÙ HỢP:",
            *(fits or ["- (không có)"]),
            "CHƯA PHÙ HỢP:",
            *(unfits or ["- (không có)"]),
        ]
        if invalids:
            lines.extend(["MÃ KHÔNG HỢP LỆ:", *invalids])
        return "\n".join(lines)

    except Exception as exc:
        return _system_error("filter_courses_by_constraints", exc)


# =====================================================================
# TOOL REGISTRY — GIỮ BACKWARD COMPATIBILITY
# =====================================================================

AVAILABLE_TOOLS = {
    "search_ai_courses": search_ai_courses,
    "get_ai_course_detail": get_ai_course_detail,
    "check_course_readiness": check_course_readiness,
    "get_learning_track": get_learning_track,
    "filter_courses_by_constraints": filter_courses_by_constraints,
}
