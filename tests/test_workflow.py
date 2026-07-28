"""Tests for the recruitment workflow state machine."""

import pytest
from src.recruitment.models import (
    Decision,
    RecruitmentRunRequest,
    RunStatus,
)
from src.recruitment.workflow import RecruitmentWorkflow
from src.recruitment.tracing import export_trace_markdown


class TestWorkflowPassPath:
    """candidate_001 + python_backend → PASS → book interview."""

    def test_full_pass_workflow(self, pass_request):
        wf = RecruitmentWorkflow(max_retries=1)
        state = wf.run(pass_request)

        assert state.final_status == RunStatus.COMPLETED
        assert state.decision == Decision.PASS
        assert state.error is None

    def test_cv_parsed(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        assert state.cv is not None
        assert state.cv.candidate_id == "candidate_001"
        assert "Python" in state.cv.skills

    def test_jd_parsed(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        assert state.jd is not None
        assert state.jd.job_id == "python_backend"
        assert "Python" in state.jd.required_skills

    def test_matching_result(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        assert state.matching is not None
        assert state.matching.total_score == 100
        assert state.matching.decision == Decision.PASS
        assert len(state.matching.missing_skills) == 0

    def test_interview_booked(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        assert state.booking is not None
        assert state.booking.status == "confirmed"
        assert state.booking.booking_id is not None
        assert state.selected_slot is not None

    def test_confirmation_email_generated(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        assert state.email_draft is not None
        assert "Chúc mừng" in state.email_draft
        assert state.confirmation is not None

    def test_trace_recorded(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        assert len(state.trace) > 0
        step_names = [e.step for e in state.trace]
        assert "validate_input" in step_names
        assert "parse_cv" in step_names
        assert "score_match" in step_names
        assert "book_interview" in step_names

    def test_tool_calls_recorded(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        assert len(state.tool_calls) > 0
        tool_names = [tc.tool_name for tc in state.tool_calls]
        assert "parse_cv" in tool_names
        assert "get_jd" in tool_names
        assert "score_candidate" in tool_names
        assert "book_interview_slot" in tool_names


class TestWorkflowRejectPath:
    """candidate_002 + python_backend → REJECT → rejection email."""

    def test_full_reject_workflow(self, reject_request):
        wf = RecruitmentWorkflow()
        state = wf.run(reject_request)

        assert state.final_status == RunStatus.COMPLETED
        assert state.decision == Decision.REJECT
        assert state.error is None

    def test_rejection_email(self, reject_request):
        state = RecruitmentWorkflow().run(reject_request)
        assert state.email_draft is not None
        assert "chưa hoàn toàn phù hợp" in state.email_draft or "Cảm ơn" in state.email_draft

    def test_no_booking_on_reject(self, reject_request):
        state = RecruitmentWorkflow().run(reject_request)
        assert state.booking is None
        assert state.confirmation is None

    def test_matching_shows_missing_skills(self, reject_request):
        state = RecruitmentWorkflow().run(reject_request)
        assert state.matching is not None
        assert len(state.matching.missing_skills) > 0


class TestWorkflowErrorHandling:
    """Invalid inputs → graceful failure."""

    def test_invalid_candidate(self, invalid_candidate_request):
        state = RecruitmentWorkflow().run(invalid_candidate_request)
        assert state.final_status == RunStatus.FAILED
        assert state.error is not None
        assert state.error.code == "CV_NOT_FOUND"

    def test_invalid_job_id(self):
        request = RecruitmentRunRequest(
            candidate_id="candidate_001",
            job_id="nonexistent_job",
            interviewer_id="interviewer_001",
            interview_date="2026-08-01",
        )
        state = RecruitmentWorkflow().run(request)
        assert state.final_status == RunStatus.FAILED
        assert state.error is not None
        assert state.error.code == "JD_NOT_FOUND"


class TestTraceExport:
    """Test the markdown trace export."""

    def test_export_contains_run_id(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        md = export_trace_markdown(state)
        assert state.run_id in md
        assert "Trace Log" in md

    def test_export_contains_tool_calls(self, pass_request):
        state = RecruitmentWorkflow().run(pass_request)
        md = export_trace_markdown(state)
        assert "parse_cv" in md
        assert "score_candidate" in md


class TestWorkflowIdempotency:
    """Verify that the workflow produces consistent results."""

    def test_deterministic_results(self, pass_request):
        wf = RecruitmentWorkflow()
        state1 = wf.run(pass_request)
        state2 = wf.run(pass_request)

        assert state1.decision == state2.decision
        assert state1.matching.total_score == state2.matching.total_score
