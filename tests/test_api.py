"""FastAPI integration tests for the AI Recruitment Agent API."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.api import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


async def test_screen_candidate_pass(client):
    payload = {
        "candidate_id": "candidate_001",
        "job_id": "python_backend",
        "interviewer_id": "interviewer_001",
        "interview_date": "2026-08-01",
    }
    response = await client.post("/api/v1/screen", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["decision"] == "PASS"
    assert data["total_score"] == 100
    assert data["email_draft"] is not None
    assert "run_id" in data


async def test_screen_candidate_reject(client):
    payload = {
        "candidate_id": "candidate_002",
        "job_id": "python_backend",
        "interviewer_id": "interviewer_001",
        "interview_date": "2026-08-01",
    }
    response = await client.post("/api/v1/screen", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["decision"] == "REJECT"
    assert data["email_draft"] is not None


async def test_screen_invalid_candidate(client):
    payload = {
        "candidate_id": "candidate_999",
        "job_id": "python_backend",
        "interviewer_id": "interviewer_001",
        "interview_date": "2026-08-01",
    }
    response = await client.post("/api/v1/screen", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["error"] is not None


async def test_screen_validation_error(client):
    payload = {
        "candidate_id": "",  # empty
        "job_id": "python_backend",
        "interviewer_id": "interviewer_001",
        "interview_date": "2026-08-01",
    }
    response = await client.post("/api/v1/screen", json=payload)
    assert response.status_code == 422  # Pydantic validation error


async def test_screen_invalid_date_format(client):
    payload = {
        "candidate_id": "candidate_001",
        "job_id": "python_backend",
        "interviewer_id": "interviewer_001",
        "interview_date": "08-01-2026",  # wrong format
    }
    response = await client.post("/api/v1/screen", json=payload)
    assert response.status_code == 422


async def test_get_run_not_found(client):
    response = await client.get("/api/v1/runs/nonexistent-id")
    assert response.status_code == 404


async def test_get_run_after_screen(client):
    # First, create a run
    payload = {
        "candidate_id": "candidate_001",
        "job_id": "python_backend",
        "interviewer_id": "interviewer_001",
        "interview_date": "2026-08-01",
    }
    screen_response = await client.post("/api/v1/screen", json=payload)
    run_id = screen_response.json()["run_id"]

    # Then retrieve it
    response = await client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["run_id"] == run_id


async def test_idempotency_key(client):
    payload = {
        "candidate_id": "candidate_001",
        "job_id": "python_backend",
        "interviewer_id": "interviewer_001",
        "interview_date": "2026-08-01",
        "idempotency_key": "test-key-123",
    }
    resp1 = await client.post("/api/v1/screen", json=payload)
    resp2 = await client.post("/api/v1/screen", json=payload)

    assert resp1.json()["run_id"] == resp2.json()["run_id"]


async def test_get_candidate(client):
    response = await client.get("/api/v1/candidates/candidate_001")
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_id"] == "candidate_001"
    assert "Nguyễn Văn An" in data["info"]


async def test_get_candidate_not_found(client):
    response = await client.get("/api/v1/candidates/unknown")
    assert response.status_code == 404


async def test_get_job(client):
    response = await client.get("/api/v1/jobs/python_backend")
    assert response.status_code == 200
    data = response.json()
    assert "Python Backend Developer" in data["info"]


async def test_get_job_not_found(client):
    response = await client.get("/api/v1/jobs/unknown_job")
    assert response.status_code == 404
