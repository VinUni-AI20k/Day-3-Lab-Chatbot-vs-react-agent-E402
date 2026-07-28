"""Shared pytest fixtures for the AI Recruitment Agent test suite."""

import pytest


@pytest.fixture
def pass_request():
    """A screening request that should result in PASS (candidate_001 → python_backend)."""
    from src.recruitment.models import RecruitmentRunRequest
    return RecruitmentRunRequest(
        candidate_id="candidate_001",
        job_id="python_backend",
        interviewer_id="interviewer_001",
        interview_date="2026-08-01",
    )


@pytest.fixture
def reject_request():
    """A screening request that should result in REJECT (candidate_002 → python_backend)."""
    from src.recruitment.models import RecruitmentRunRequest
    return RecruitmentRunRequest(
        candidate_id="candidate_002",
        job_id="python_backend",
        interviewer_id="interviewer_001",
        interview_date="2026-08-01",
    )


@pytest.fixture
def invalid_candidate_request():
    """A screening request with a non-existent candidate."""
    from src.recruitment.models import RecruitmentRunRequest
    return RecruitmentRunRequest(
        candidate_id="candidate_999",
        job_id="python_backend",
        interviewer_id="interviewer_001",
        interview_date="2026-08-01",
    )
