"""Tests for Pydantic recruitment models — field constraints, validators, enums."""

import pytest
from src.recruitment.models import (
    AgentState,
    CandidateProfile,
    Decision,
    Evidence,
    InterviewSlot,
    JobDescription,
    MatchingResult,
    RecruitmentRunRequest,
    RunStatus,
    ToolCallStatus,
)
from pydantic import ValidationError


class TestDecisionEnum:
    def test_values(self):
        assert Decision.PASS == "PASS"
        assert Decision.REJECT == "REJECT"

    def test_str_conversion(self):
        assert str(Decision.PASS) == "PASS"


class TestRunStatus:
    def test_all_statuses(self):
        assert RunStatus.RUNNING == "RUNNING"
        assert RunStatus.COMPLETED == "COMPLETED"
        assert RunStatus.FAILED == "FAILED"


class TestToolCallStatus:
    def test_all_statuses(self):
        assert ToolCallStatus.SUCCESS == "SUCCESS"
        assert ToolCallStatus.ERROR == "ERROR"
        assert ToolCallStatus.TIMEOUT == "TIMEOUT"


class TestRecruitmentRunRequest:
    def test_valid_request(self):
        req = RecruitmentRunRequest(
            candidate_id="candidate_001",
            job_id="python_backend",
            interviewer_id="interviewer_001",
            interview_date="2026-08-01",
        )
        assert req.candidate_id == "candidate_001"
        assert req.timezone == "Asia/Ho_Chi_Minh"
        assert req.threshold is None

    def test_whitespace_stripping(self):
        req = RecruitmentRunRequest(
            candidate_id="  candidate_001  ",
            job_id="  python_backend  ",
            interviewer_id="interviewer_001",
            interview_date="2026-08-01",
        )
        assert req.candidate_id == "candidate_001"
        assert req.job_id == "python_backend"

    def test_empty_candidate_id_rejected(self):
        with pytest.raises(ValidationError):
            RecruitmentRunRequest(
                candidate_id="",
                job_id="python_backend",
                interviewer_id="interviewer_001",
                interview_date="2026-08-01",
            )

    def test_invalid_date_format_rejected(self):
        with pytest.raises(ValidationError):
            RecruitmentRunRequest(
                candidate_id="candidate_001",
                job_id="python_backend",
                interviewer_id="interviewer_001",
                interview_date="01-08-2026",  # wrong format
            )

    def test_unsafe_path_in_id_rejected(self):
        with pytest.raises(ValidationError):
            RecruitmentRunRequest(
                candidate_id="../etc/passwd",
                job_id="python_backend",
                interviewer_id="interviewer_001",
                interview_date="2026-08-01",
            )

    def test_threshold_bounds(self):
        req = RecruitmentRunRequest(
            candidate_id="c1",
            job_id="j1",
            interviewer_id="i1",
            interview_date="2026-08-01",
            threshold=85.5,
        )
        assert req.threshold == 85.5

        with pytest.raises(ValidationError):
            RecruitmentRunRequest(
                candidate_id="c1",
                job_id="j1",
                interviewer_id="i1",
                interview_date="2026-08-01",
                threshold=150,  # > 100
            )


class TestCandidateProfile:
    def test_defaults(self):
        cp = CandidateProfile(candidate_id="c1")
        assert cp.name is None
        assert cp.skills == []
        assert cp.experience_years is None

    def test_with_data(self):
        cp = CandidateProfile(
            candidate_id="c1",
            name="Test",
            skills=["Python", "SQL"],
            experience_years=3.0,
        )
        assert len(cp.skills) == 2


class TestMatchingResult:
    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            MatchingResult(
                candidate_id="c1",
                job_id="j1",
                decision=Decision.PASS,
                total_score=150,  # > 100
                threshold=70,
                must_have_passed=True,
                decision_summary="test",
            )

    def test_valid_result(self):
        mr = MatchingResult(
            candidate_id="c1",
            job_id="j1",
            decision=Decision.PASS,
            total_score=85,
            threshold=70,
            must_have_passed=True,
            matched_skills=["Python"],
            decision_summary="ĐẠT",
        )
        assert mr.decision == Decision.PASS
        assert mr.total_score == 85


class TestAgentState:
    def test_default_state(self):
        state = AgentState(
            request_id="r1",
            idempotency_key="k1",
            candidate_id="c1",
            job_id="j1",
            interviewer_id="i1",
            interview_date="2026-08-01",
            timezone="UTC",
            threshold=70,
        )
        assert state.current_step == "validate_input"
        assert state.final_status == RunStatus.RUNNING
        assert state.cv is None
        assert state.jd is None
        assert state.decision is None
        assert len(state.tool_calls) == 0
        assert len(state.trace) == 0
