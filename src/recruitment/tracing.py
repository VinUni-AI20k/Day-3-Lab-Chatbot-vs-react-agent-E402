"""
📊 OBSERVABILITY — Structured logging & tracing for the recruitment workflow.

Provides:
- Request-scoped trace context (run_id correlation)
- Step timing with automatic duration calculation
- Tool call recording with attempt/error tracking
- Human-readable trace export for ``docs/trace_eval.md``
- JSON-structured log output (cloud-logging compatible)
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

from .models import (
    AgentState,
    RunStatus,
    ToolCallRecord,
    ToolCallStatus,
    TraceEvent,
    utc_now,
)

# ---------------------------------------------------------------------------
# JSON log formatter
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge extra fields attached by ``WorkflowTracer``
        for key in ("run_id", "step", "tool", "duration_ms", "status", "error"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(*, level: int = logging.INFO, json_output: bool = True) -> None:
    """Configure root logger with optional JSON formatting."""
    root = logging.getLogger("recruitment")
    if root.handlers:
        return  # already configured
    handler = logging.StreamHandler()
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
        )
    root.addHandler(handler)
    root.setLevel(level)


# ---------------------------------------------------------------------------
# Workflow tracer
# ---------------------------------------------------------------------------

logger = logging.getLogger("recruitment.tracing")


class WorkflowTracer:
    """Records trace events and tool calls onto an ``AgentState``."""

    def __init__(self, state: AgentState) -> None:
        self._state = state
        self._step_starts: dict[str, float] = {}

    # -- step lifecycle -----------------------------------------------------

    def begin_step(self, step: str) -> None:
        self._step_starts[step] = time.perf_counter()
        self._state.current_step = step
        self._state.updated_at = utc_now()
        logger.info(
            "Step started: %s",
            step,
            extra={"run_id": self._state.run_id, "step": step},
        )

    def end_step(self, step: str, *, status: str = "ok", detail: str | None = None) -> None:
        start = self._step_starts.pop(step, None)
        duration_ms = round((time.perf_counter() - start) * 1000, 2) if start else None
        event = TraceEvent(
            step=step,
            status=status,
            duration_ms=duration_ms,
            detail=detail,
        )
        self._state.trace.append(event)
        self._state.updated_at = utc_now()
        logger.info(
            "Step finished: %s [%s] %sms",
            step,
            status,
            duration_ms,
            extra={
                "run_id": self._state.run_id,
                "step": step,
                "status": status,
                "duration_ms": duration_ms,
            },
        )

    @contextmanager
    def step(self, name: str) -> Generator[None, None, None]:
        """Context manager that automatically records begin/end of a step."""
        self.begin_step(name)
        status = "ok"
        detail: str | None = None
        try:
            yield
        except Exception as exc:
            status = "error"
            detail = str(exc)
            raise
        finally:
            self.end_step(name, status=status, detail=detail)

    # -- tool call recording ------------------------------------------------

    def record_tool_call(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        output_summary: str | None = None,
        error: str | None = None,
        duration_ms: float = 0,
        attempt: int = 1,
    ) -> None:
        call_status = ToolCallStatus.ERROR if error else ToolCallStatus.SUCCESS
        record = ToolCallRecord(
            tool_name=tool_name,
            arguments=arguments,
            status=call_status,
            attempt=attempt,
            duration_ms=round(duration_ms, 2),
            started_at=utc_now(),
            output_summary=output_summary,
            error=error,
        )
        self._state.tool_calls.append(record)
        log_extra = {
            "run_id": self._state.run_id,
            "tool": tool_name,
            "status": call_status.value,
            "duration_ms": record.duration_ms,
        }
        if error:
            log_extra["error"] = error
            logger.warning("Tool call failed: %s — %s", tool_name, error, extra=log_extra)
        else:
            logger.info("Tool call ok: %s", tool_name, extra=log_extra)

    # -- completion ---------------------------------------------------------

    def mark_completed(self) -> None:
        self._state.final_status = RunStatus.COMPLETED
        self._state.updated_at = utc_now()
        logger.info(
            "Run completed",
            extra={"run_id": self._state.run_id, "status": "COMPLETED"},
        )

    def mark_failed(self, error_msg: str) -> None:
        self._state.final_status = RunStatus.FAILED
        self._state.updated_at = utc_now()
        logger.error(
            "Run failed: %s",
            error_msg,
            extra={"run_id": self._state.run_id, "status": "FAILED", "error": error_msg},
        )


# ---------------------------------------------------------------------------
# Human-readable trace export
# ---------------------------------------------------------------------------

def export_trace_markdown(state: AgentState) -> str:
    """Render the run trace as a Markdown block suitable for ``trace_eval.md``."""
    lines: list[str] = []
    lines.append(f"### 🔍 Trace Log — Run `{state.run_id}`")
    lines.append(f"- **Candidate**: `{state.candidate_id}`")
    lines.append(f"- **Job**: `{state.job_id}`")
    lines.append(f"- **Decision**: `{state.decision or 'N/A'}`")
    lines.append(f"- **Status**: `{state.final_status.value}`")
    lines.append(f"- **Created**: `{state.created_at.isoformat()}`")
    lines.append("")

    if state.trace:
        lines.append("| # | Step | Status | Duration | Detail |")
        lines.append("|:--|:-----|:-------|:---------|:-------|")
        for i, evt in enumerate(state.trace, 1):
            dur = f"{evt.duration_ms:.1f}ms" if evt.duration_ms is not None else "—"
            detail = (evt.detail or "—")[:80]
            lines.append(f"| {i} | `{evt.step}` | {evt.status} | {dur} | {detail} |")
        lines.append("")

    if state.tool_calls:
        lines.append("**Tool Calls:**")
        lines.append("")
        for tc in state.tool_calls:
            emoji = "✅" if tc.status == ToolCallStatus.SUCCESS else "❌"
            args_str = json.dumps(tc.arguments, ensure_ascii=False)
            lines.append(f"- {emoji} `{tc.tool_name}({args_str})` → {tc.output_summary or tc.error or '—'} ({tc.duration_ms}ms)")
        lines.append("")

    return "\n".join(lines)
