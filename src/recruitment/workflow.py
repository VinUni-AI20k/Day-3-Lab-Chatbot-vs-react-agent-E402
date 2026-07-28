"""
🔄 RECRUITMENT WORKFLOW ENGINE — State Machine (LangGraph-style, thuần Python)

Quy trình nghiệp vụ:
    validate_input → parse_cv → get_jd → normalize_data → score_match
        ├─ [PASS]   → check_calendar → select_slot → book_interview → generate_confirmation
        └─ [REJECT] → generate_rejection_email

Mỗi step là hàm thuần: ``(AgentState, WorkflowTracer) → AgentState``
Chạy deterministic với MockProvider — không cần LLM để test.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from .models import (
    AgentState,
    BookingResult,
    CandidateProfile,
    Decision,
    Evidence,
    InterviewSlot,
    JobDescription,
    MatchingResult,
    RecruitmentRunRequest,
    RunError,
    RunStatus,
    utc_now,
)
from .tracing import WorkflowTracer

# We import tools at module level — they are pure functions with mock data.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import (
    parse_cv as _tool_parse_cv,
    get_jd as _tool_get_jd,
    score_candidate as _tool_score_candidate,
    check_calendar as _tool_check_calendar,
    book_interview_slot as _tool_book_interview_slot,
)


# ---------------------------------------------------------------------------
# Helper: call a tool with timing and tracing
# ---------------------------------------------------------------------------

def _call_tool(
    tracer: WorkflowTracer,
    tool_name: str,
    tool_fn: Any,
    arguments: dict[str, Any],
    *,
    attempt: int = 1,
) -> str:
    """Invoke a tool function, record the call in the tracer, and return the raw string result."""
    t0 = time.perf_counter()
    try:
        result: str = tool_fn(**arguments)
    except Exception as exc:
        duration_ms = (time.perf_counter() - t0) * 1000
        tracer.record_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            error=str(exc),
            duration_ms=duration_ms,
            attempt=attempt,
        )
        raise
    duration_ms = (time.perf_counter() - t0) * 1000
    is_error = result.startswith("LỖI:")
    tracer.record_tool_call(
        tool_name=tool_name,
        arguments=arguments,
        output_summary=result[:200],
        error=result if is_error else None,
        duration_ms=duration_ms,
        attempt=attempt,
    )
    return result


def _is_tool_error(result: str) -> bool:
    return result.startswith("LỖI:")


# ---------------------------------------------------------------------------
# Step functions
# ---------------------------------------------------------------------------

def step_validate_input(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Validate the initial request parameters."""
    with tracer.step("validate_input"):
        # Pydantic already validated in RecruitmentRunRequest; do light sanity check
        if not state.candidate_id or not state.job_id:
            state.error = RunError(
                code="INVALID_INPUT",
                message="candidate_id và job_id không được rỗng.",
                retryable=False,
                step="validate_input",
            )
            state.final_status = RunStatus.FAILED
            return state
        state.current_step = "parse_cv"
    return state


def step_parse_cv(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Call ``parse_cv`` tool and populate ``state.cv``."""
    with tracer.step("parse_cv"):
        result = _call_tool(tracer, "parse_cv", _tool_parse_cv, {"candidate_id": state.candidate_id})
        if _is_tool_error(result):
            state.error = RunError(
                code="CV_NOT_FOUND",
                message=result,
                retryable=False,
                step="parse_cv",
            )
            state.final_status = RunStatus.FAILED
            return state

        # Parse structured info from the tool output
        # Output format: "CV candidate_001: Nguyễn Văn An; Kỹ năng: Python, SQL, REST API; Kinh nghiệm: 3 năm."
        parts = result.split(";")
        name = parts[0].split(":")[-1].strip() if len(parts) > 0 else None
        skills: list[str] = []
        experience_years: float = 0
        for part in parts:
            part_stripped = part.strip()
            if "Kỹ năng:" in part_stripped:
                skills_str = part_stripped.split("Kỹ năng:")[-1].strip()
                skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            elif "Kinh nghiệm:" in part_stripped:
                exp_str = part_stripped.split("Kinh nghiệm:")[-1].strip()
                try:
                    experience_years = float(exp_str.replace("năm.", "").replace("năm", "").strip())
                except ValueError:
                    experience_years = 0

        state.cv = CandidateProfile(
            candidate_id=state.candidate_id,
            name=name,
            skills=skills,
            experience_years=experience_years,
            evidence=[Evidence(category="tool", source="parse_cv", detail=result)],
        )
        state.current_step = "get_jd"
    return state


def step_get_jd(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Call ``get_jd`` tool and populate ``state.jd``."""
    with tracer.step("get_jd"):
        result = _call_tool(tracer, "get_jd", _tool_get_jd, {"job_id": state.job_id})
        if _is_tool_error(result):
            state.error = RunError(
                code="JD_NOT_FOUND",
                message=result,
                retryable=False,
                step="get_jd",
            )
            state.final_status = RunStatus.FAILED
            return state

        # Parse: "JD python_backend: Python Backend Developer; Kỹ năng bắt buộc: Python, SQL, REST API; Kinh nghiệm tối thiểu: 2 năm."
        parts = result.split(";")
        title: str | None = None
        required_skills: list[str] = []
        min_exp: float = 0
        for part in parts:
            p = part.strip()
            if "JD " in p and ":" in p:
                title = p.split(":")[-1].strip()
            elif "Kỹ năng bắt buộc:" in p:
                skills_str = p.split("Kỹ năng bắt buộc:")[-1].strip()
                required_skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            elif "Kinh nghiệm tối thiểu:" in p:
                exp_str = p.split("Kinh nghiệm tối thiểu:")[-1].strip()
                try:
                    min_exp = float(exp_str.replace("năm.", "").replace("năm", "").strip())
                except ValueError:
                    min_exp = 0

        state.jd = JobDescription(
            job_id=state.job_id,
            title=title,
            required_skills=required_skills,
            minimum_experience_years=min_exp,
            pass_threshold=state.threshold,
            evidence=[Evidence(category="tool", source="get_jd", detail=result)],
        )
        state.current_step = "normalize_data"
    return state


def step_normalize_data(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Normalize skill names to lowercase for matching (data cleansing)."""
    with tracer.step("normalize_data"):
        if state.cv:
            state.cv.skills = [s.strip() for s in state.cv.skills]
        if state.jd:
            state.jd.required_skills = [s.strip() for s in state.jd.required_skills]
        state.current_step = "score_match"
    return state


def step_score_match(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Call ``score_candidate`` tool, populate ``state.matching`` and ``state.decision``."""
    with tracer.step("score_match"):
        result = _call_tool(
            tracer,
            "score_candidate",
            _tool_score_candidate,
            {"candidate_id": state.candidate_id, "job_id": state.job_id},
        )
        if _is_tool_error(result):
            state.error = RunError(
                code="SCORING_ERROR",
                message=result,
                retryable=False,
                step="score_match",
            )
            state.final_status = RunStatus.FAILED
            return state

        # Parse scoring output
        matched_skills: list[str] = []
        missing_skills: list[str] = []
        total_score: float = 0
        decision_str = ""
        score_breakdown: dict[str, float] = {}

        for segment in result.split(";"):
            seg = segment.strip()
            if "Kỹ năng khớp:" in seg:
                val = seg.split("Kỹ năng khớp:")[-1].strip()
                matched_skills = [s.strip() for s in val.split(",") if s.strip() and s.strip() != "Không có"]
            elif "Kỹ năng thiếu:" in seg:
                val = seg.split("Kỹ năng thiếu:")[-1].strip()
                missing_skills = [s.strip() for s in val.split(",") if s.strip() and s.strip() != "Không có"]
            elif "Điểm kỹ năng:" in seg:
                try:
                    score_breakdown["skill"] = float(seg.split("Điểm kỹ năng:")[-1].split("/")[0].strip())
                except (ValueError, IndexError):
                    pass
            elif "Điểm kinh nghiệm:" in seg:
                try:
                    score_breakdown["experience"] = float(seg.split("Điểm kinh nghiệm:")[-1].split("/")[0].strip())
                except (ValueError, IndexError):
                    pass
            elif "Tổng điểm:" in seg:
                try:
                    total_score = float(seg.split("Tổng điểm:")[-1].split("/")[0].strip())
                except (ValueError, IndexError):
                    total_score = 0
            elif "Quyết định:" in seg:
                decision_str = seg.split("Quyết định:")[-1].strip().rstrip(".")

        threshold = state.threshold
        must_have_passed = len(missing_skills) == 0
        decision = Decision.PASS if decision_str == "ĐẠT" else Decision.REJECT

        # Determine strengths/concerns
        strengths: list[str] = []
        concerns: list[str] = []
        if must_have_passed:
            strengths.append("Đáp ứng đầy đủ kỹ năng bắt buộc")
        if state.cv and state.jd and state.cv.experience_years and state.jd.minimum_experience_years:
            if state.cv.experience_years >= state.jd.minimum_experience_years:
                strengths.append(f"Kinh nghiệm {state.cv.experience_years} năm ≥ yêu cầu {state.jd.minimum_experience_years} năm")
            else:
                concerns.append(f"Kinh nghiệm {state.cv.experience_years} năm < yêu cầu {state.jd.minimum_experience_years} năm")
        if missing_skills:
            concerns.append(f"Thiếu kỹ năng: {', '.join(missing_skills)}")

        decision_summary = (
            f"Ứng viên {state.candidate_id} {'ĐẠT' if decision == Decision.PASS else 'KHÔNG ĐẠT'} "
            f"với {total_score}/100 điểm cho vị trí {state.jd.title or state.job_id}."
        )

        state.matching = MatchingResult(
            candidate_id=state.candidate_id,
            job_id=state.job_id,
            decision=decision,
            total_score=total_score,
            threshold=threshold,
            must_have_passed=must_have_passed,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            strengths=strengths,
            concerns=concerns,
            evidence=[Evidence(category="tool", source="score_candidate", detail=result)],
            score_breakdown=score_breakdown,
            decision_summary=decision_summary,
        )
        state.decision = decision

        # Route to next step
        if decision == Decision.PASS:
            state.current_step = "check_calendar"
        else:
            state.current_step = "generate_rejection_email"

    return state


def step_check_calendar(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Call ``check_calendar`` tool and populate ``state.calendar_slots``."""
    with tracer.step("check_calendar"):
        result = _call_tool(
            tracer,
            "check_calendar",
            _tool_check_calendar,
            {"interviewer_id": state.interviewer_id, "date": state.interview_date},
        )
        if _is_tool_error(result):
            state.error = RunError(
                code="CALENDAR_ERROR",
                message=result,
                retryable=True,
                step="check_calendar",
            )
            state.final_status = RunStatus.FAILED
            return state

        # Parse slots: "Slot rảnh của interviewer_001 ngày 2026-08-01: 09:00, 14:00."
        # Use regex to extract HH:MM patterns (colon-split breaks because times contain colons)
        import re as _re
        time_strings = _re.findall(r"\b(\d{2}:\d{2})\b", result)

        from datetime import datetime as _dt

        slots: list[InterviewSlot] = []
        for ts in time_strings:
            try:
                start = _dt.strptime(f"{state.interview_date} {ts}", "%Y-%m-%d %H:%M")
                # Assume 1-hour interview
                end = _dt.strptime(f"{state.interview_date} {ts}", "%Y-%m-%d %H:%M")
                end = end.replace(hour=end.hour + 1) if end.hour < 23 else end.replace(hour=23, minute=59)
                from datetime import timezone as _tz
                start = start.replace(tzinfo=_tz.utc)
                end = end.replace(tzinfo=_tz.utc)
                slots.append(InterviewSlot(
                    interviewer_id=state.interviewer_id,
                    start_at=start,
                    end_at=end,
                    timezone=state.timezone,
                ))
            except ValueError:
                continue

        state.calendar_slots = slots
        state.current_step = "select_slot"
    return state


def step_select_slot(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Pick the earliest available slot."""
    with tracer.step("select_slot"):
        if not state.calendar_slots:
            state.error = RunError(
                code="NO_SLOTS",
                message="Không còn slot rảnh để đặt lịch phỏng vấn.",
                retryable=True,
                step="select_slot",
            )
            state.final_status = RunStatus.FAILED
            return state

        sorted_slots = sorted(state.calendar_slots, key=lambda s: s.start_at)
        state.selected_slot = sorted_slots[0]
        state.backup_slot = sorted_slots[1] if len(sorted_slots) > 1 else None
        state.current_step = "book_interview"
    return state


def step_book_interview(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Call ``book_interview_slot`` tool."""
    with tracer.step("book_interview"):
        if not state.selected_slot:
            state.error = RunError(
                code="NO_SLOT_SELECTED",
                message="Chưa chọn slot phỏng vấn.",
                retryable=False,
                step="book_interview",
            )
            state.final_status = RunStatus.FAILED
            return state

        time_str = state.selected_slot.start_at.strftime("%H:%M")
        result = _call_tool(
            tracer,
            "book_interview_slot",
            _tool_book_interview_slot,
            {
                "candidate_id": state.candidate_id,
                "interviewer_id": state.interviewer_id,
                "date": state.interview_date,
                "time": time_str,
            },
        )
        if _is_tool_error(result):
            state.error = RunError(
                code="BOOKING_FAILED",
                message=result,
                retryable=True,
                step="book_interview",
            )
            state.final_status = RunStatus.FAILED
            return state

        state.booking = BookingResult(
            status="confirmed",
            booking_id=str(uuid4()),
            interviewer_id=state.interviewer_id,
            selected_slot=state.selected_slot,
            backup_slot=state.backup_slot,
            confirmation_message=result,
            raw_tool_result=result,
        )
        state.current_step = "generate_confirmation"
    return state


def step_generate_confirmation(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Generate the interview confirmation email/message."""
    with tracer.step("generate_confirmation"):
        if not state.selected_slot or not state.matching:
            state.current_step = "done"
            return state

        candidate_name = state.cv.name if state.cv else state.candidate_id
        job_title = state.jd.title if state.jd else state.job_id
        time_str = state.selected_slot.start_at.strftime("%H:%M")
        date_str = state.interview_date

        confirmation = (
            f"Kính gửi {candidate_name},\n\n"
            f"Chúc mừng! Hồ sơ ứng tuyển vị trí {job_title} của bạn đã được đánh giá ĐẠT "
            f"với tổng điểm {state.matching.total_score}/100.\n\n"
            f"Chúng tôi xin mời bạn tham gia buổi phỏng vấn:\n"
            f"  📅 Ngày: {date_str}\n"
            f"  ⏰ Giờ: {time_str}\n"
            f"  👤 Người phỏng vấn: {state.interviewer_id}\n\n"
            f"Vui lòng xác nhận tham dự bằng cách phản hồi email này.\n\n"
            f"Trân trọng,\n"
            f"Phòng Nhân Sự"
        )
        state.confirmation = confirmation
        state.email_draft = confirmation
        state.current_step = "done"
    return state


def step_generate_rejection_email(state: AgentState, tracer: WorkflowTracer) -> AgentState:
    """Generate a polite rejection email."""
    with tracer.step("generate_rejection_email"):
        candidate_name = state.cv.name if state.cv else state.candidate_id
        job_title = state.jd.title if state.jd else state.job_id

        concerns_text = ""
        if state.matching and state.matching.concerns:
            concerns_text = "\n".join(f"  - {c}" for c in state.matching.concerns)
        score_text = f"{state.matching.total_score}/100" if state.matching else "N/A"

        rejection = (
            f"Kính gửi {candidate_name},\n\n"
            f"Cảm ơn bạn đã quan tâm đến vị trí {job_title} tại công ty chúng tôi.\n\n"
            f"Sau khi xem xét kỹ lưỡng hồ sơ của bạn (điểm đánh giá: {score_text}), "
            f"chúng tôi nhận thấy hồ sơ chưa hoàn toàn phù hợp với yêu cầu hiện tại "
            f"của vị trí này.\n"
        )
        if concerns_text:
            rejection += f"\nCác điểm cần cải thiện:\n{concerns_text}\n"

        rejection += (
            f"\nChúng tôi rất trân trọng sự quan tâm của bạn và khuyến khích bạn "
            f"ứng tuyển lại trong tương lai khi đã bổ sung thêm kinh nghiệm.\n\n"
            f"Trân trọng,\n"
            f"Phòng Nhân Sự"
        )
        state.email_draft = rejection
        state.current_step = "done"
    return state


# ---------------------------------------------------------------------------
# Step registry and router
# ---------------------------------------------------------------------------

_STEP_MAP = {
    "validate_input": step_validate_input,
    "parse_cv": step_parse_cv,
    "get_jd": step_get_jd,
    "normalize_data": step_normalize_data,
    "score_match": step_score_match,
    "check_calendar": step_check_calendar,
    "select_slot": step_select_slot,
    "book_interview": step_book_interview,
    "generate_confirmation": step_generate_confirmation,
    "generate_rejection_email": step_generate_rejection_email,
}


# ---------------------------------------------------------------------------
# Main workflow class
# ---------------------------------------------------------------------------

class RecruitmentWorkflow:
    """Orchestrates the full recruitment screening pipeline.

    Usage::

        wf = RecruitmentWorkflow(max_retries=2)
        state = wf.run(request)
        print(state.decision, state.email_draft)
    """

    def __init__(self, *, max_retries: int = 1) -> None:
        self.max_retries = max_retries

    def run(self, request: RecruitmentRunRequest) -> AgentState:
        """Execute the complete workflow from request to decision + email."""
        state = AgentState(
            request_id=request.request_id or str(uuid4()),
            idempotency_key=request.idempotency_key or str(uuid4()),
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            interviewer_id=request.interviewer_id,
            interview_date=request.interview_date,
            timezone=request.timezone,
            threshold=request.threshold if request.threshold is not None else 70.0,
        )
        tracer = WorkflowTracer(state)

        max_steps = 15  # safety limit
        step_count = 0

        while state.current_step != "done" and state.final_status == RunStatus.RUNNING:
            step_count += 1
            if step_count > max_steps:
                tracer.mark_failed(f"Vượt quá giới hạn {max_steps} bước xử lý.")
                break

            step_fn = _STEP_MAP.get(state.current_step)
            if step_fn is None:
                tracer.mark_failed(f"Không tìm thấy step handler cho '{state.current_step}'.")
                break

            try:
                state = step_fn(state, tracer)
            except Exception as exc:
                state.error = RunError(
                    code="UNEXPECTED_ERROR",
                    message=str(exc),
                    retryable=False,
                    step=state.current_step,
                )
                tracer.mark_failed(str(exc))
                break

            # If failed but retryable, attempt retry
            if state.final_status == RunStatus.FAILED and state.error and state.error.retryable:
                if state.retry_count < self.max_retries:
                    state.retry_count += 1
                    state.final_status = RunStatus.RUNNING
                    state.error = None
                    # retry the same step
                    continue

        if state.final_status == RunStatus.RUNNING:
            tracer.mark_completed()

        return state
