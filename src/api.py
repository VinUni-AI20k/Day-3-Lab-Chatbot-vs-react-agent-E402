"""
🚀 FASTAPI REST API — AI Recruitment Agent

Endpoints:
    GET  /health                     → Health check
    POST /api/v1/screen              → Submit screening request
    GET  /api/v1/runs/{run_id}       → Get run status & result
    GET  /api/v1/candidates/{id}     → Get candidate info
    GET  /api/v1/jobs/{id}           → Get job description

Usage:
    uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Ensure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from recruitment.models import RecruitmentRunRequest, RunStatus
from recruitment.tracing import export_trace_markdown, setup_logging
from recruitment.workflow import RecruitmentWorkflow
from tools import parse_cv, get_jd

# ---------------------------------------------------------------------------
# In-memory run store (production: replace with Redis / PostgreSQL)
# ---------------------------------------------------------------------------
_RUN_STORE: dict[str, dict[str, Any]] = {}
_IDEMPOTENCY_INDEX: dict[str, str] = {}  # idempotency_key -> run_id

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(json_output=True)
    yield

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Recruitment Agent",
    description="Agent sàng lọc CV và điều phối phỏng vấn — FastAPI Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str
    version: str = "1.0.0"


class ScreenResponse(BaseModel):
    run_id: str
    status: str
    decision: str | None = None
    total_score: float | None = None
    decision_summary: str | None = None
    email_draft: str | None = None
    confirmation: str | None = None
    error: dict[str, Any] | None = None
    trace_markdown: str | None = None


class CandidateResponse(BaseModel):
    candidate_id: str
    info: str


class JobResponse(BaseModel):
    job_id: str
    info: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/screen", response_model=ScreenResponse, tags=["screening"])
async def screen_candidate(request: RecruitmentRunRequest):
    """Submit a candidate screening request.

    Executes the full recruitment pipeline synchronously and returns the result.
    Supports idempotency keys — submitting the same key returns the cached result.
    """
    # Idempotency check
    if request.idempotency_key and request.idempotency_key in _IDEMPOTENCY_INDEX:
        existing_run_id = _IDEMPOTENCY_INDEX[request.idempotency_key]
        if existing_run_id in _RUN_STORE:
            return ScreenResponse(**_RUN_STORE[existing_run_id])

    # Execute workflow
    workflow = RecruitmentWorkflow(max_retries=1)
    state = workflow.run(request)

    # Build response
    response_data: dict[str, Any] = {
        "run_id": state.run_id,
        "status": state.final_status.value,
        "decision": state.decision.value if state.decision else None,
        "total_score": state.matching.total_score if state.matching else None,
        "decision_summary": state.matching.decision_summary if state.matching else None,
        "email_draft": state.email_draft,
        "confirmation": state.confirmation,
        "error": state.error.model_dump() if state.error else None,
        "trace_markdown": export_trace_markdown(state),
    }

    # Store run
    _RUN_STORE[state.run_id] = response_data
    if request.idempotency_key:
        _IDEMPOTENCY_INDEX[request.idempotency_key] = state.run_id

    return ScreenResponse(**response_data)


@app.get("/api/v1/runs/{run_id}", response_model=ScreenResponse, tags=["screening"])
async def get_run(run_id: str):
    """Retrieve a previous screening run result."""
    if run_id not in _RUN_STORE:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return ScreenResponse(**_RUN_STORE[run_id])


@app.get("/api/v1/candidates/{candidate_id}", response_model=CandidateResponse, tags=["data"])
async def get_candidate(candidate_id: str):
    """Look up candidate information."""
    result = parse_cv(candidate_id)
    if result.startswith("LỖI:"):
        raise HTTPException(status_code=404, detail=result)
    return CandidateResponse(candidate_id=candidate_id, info=result)


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse, tags=["data"])
async def get_job(job_id: str):
    """Look up job description information."""
    result = get_jd(job_id)
    if result.startswith("LỖI:"):
        raise HTTPException(status_code=404, detail=result)
    return JobResponse(job_id=job_id, info=result)
