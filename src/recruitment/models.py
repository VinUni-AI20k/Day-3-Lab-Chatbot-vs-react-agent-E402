from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Decision(StrEnum):
    PASS = "PASS"
    REJECT = "REJECT"


class RunStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ToolCallStatus(StrEnum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class Evidence(BaseModel):
    category: str
    source: str
    detail: str


class CandidateProfile(BaseModel):
    candidate_id: str
    name: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    projects: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class JobDescription(BaseModel):
    job_id: str
    title: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    minimum_experience_years: float | None = None
    education_requirements: list[str] = Field(default_factory=list)
    certification_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    disqualifiers: list[str] = Field(default_factory=list)
    pass_threshold: float | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class MatchingResult(BaseModel):
    candidate_id: str
    job_id: str
    decision: Decision
    total_score: float = Field(ge=0, le=100)
    threshold: float = Field(ge=0, le=100)
    must_have_passed: bool
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    decision_summary: str


class InterviewSlot(BaseModel):
    interviewer_id: str
    start_at: datetime
    end_at: datetime
    timezone: str


class BookingResult(BaseModel):
    status: str
    booking_id: str | None = None
    interviewer_id: str
    selected_slot: InterviewSlot | None = None
    backup_slot: InterviewSlot | None = None
    confirmation_message: str | None = None
    raw_tool_result: str | None = None


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    status: ToolCallStatus
    attempt: int
    duration_ms: float
    started_at: datetime
    output_summary: str | None = None
    error: str | None = None


class TraceEvent(BaseModel):
    step: str
    status: str
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: float | None = None
    detail: str | None = None


class RunError(BaseModel):
    code: str
    message: str
    retryable: bool = False
    step: str


class RecruitmentRunRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    candidate_id: str = Field(min_length=1, max_length=128)
    job_id: str = Field(min_length=1, max_length=128)
    interviewer_id: str = Field(min_length=1, max_length=128)
    interview_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    timezone: str = Field(default="Asia/Ho_Chi_Minh", min_length=1, max_length=64)
    threshold: float | None = Field(default=None, ge=0, le=100)
    request_id: str | None = Field(default=None, min_length=1, max_length=128)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("candidate_id", "job_id", "interviewer_id")
    @classmethod
    def safe_identifier(cls, value: str) -> str:
        if any(token in value for token in ("..", "/", "\\")):
            raise ValueError("identifier contains an unsafe path sequence")
        return value


class AgentState(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    idempotency_key: str
    candidate_id: str
    job_id: str
    interviewer_id: str
    interview_date: str
    timezone: str
    threshold: float
    cv: CandidateProfile | None = None
    jd: JobDescription | None = None
    matching: MatchingResult | None = None
    decision: Decision | None = None
    calendar_slots: list[InterviewSlot] = Field(default_factory=list)
    selected_slot: InterviewSlot | None = None
    backup_slot: InterviewSlot | None = None
    booking: BookingResult | None = None
    email_draft: str | None = None
    confirmation: str | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    error: RunError | None = None
    retry_count: int = 0
    current_step: str = "validate_input"
    final_status: RunStatus = RunStatus.RUNNING
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)