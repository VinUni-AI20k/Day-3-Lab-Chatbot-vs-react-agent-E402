"""Utilities for parsing the text protocol used by the ReAct agent.

Keep these helpers independent from Streamlit so the UI and headless runner use
exactly the same parsing rules and can be tested without starting the app.
"""

import ast
import json
import re
from typing import Any, Optional, Tuple


_FINAL_ANSWER_RE = re.compile(
    r"^[ \t]*(?:\*\*)?Final[ \t]+Answer(?:\*\*)?[ \t]*:(?:\*\*)?[ \t]*",
    re.IGNORECASE | re.MULTILINE,
)

_ACTION_RE = re.compile(
    r"^[ \t]*(?:\*\*)?Action(?:\*\*)?[ \t]*:(?:\*\*)?[ \t]*"
    r"([A-Za-z_]\w*)[ \t]*\[(.*)\][ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

_THOUGHT_RE = re.compile(
    r"^[ \t]*(?:\*\*)?Thought(?:\*\*)?[ \t]*:(?:\*\*)?[ \t]*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_final_answer(text: str) -> Optional[str]:
    """Return all text after a ``Final Answer:`` marker.

    A final answer commonly spans multiple Markdown lines. Extracting only the
    marker's line silently drops lists and paragraphs that follow it.
    """
    if not isinstance(text, str):
        return None

    match = _FINAL_ANSWER_RE.search(text)
    if not match:
        return None
    return text[match.end():].strip()


def extract_thoughts(text: str) -> list[str]:
    """Extract short Thought lines for observability in the UI."""
    if not isinstance(text, str):
        return []
    return [match.group(1).strip() for match in _THOUGHT_RE.finditer(text)]


def _parse_arguments(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        return []

    # Standard protocol: tool['arg 1', 123, None]. A comma-separated literal
    # parses as a tuple; a single literal parses as that literal.
    try:
        parsed = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        parsed = None
    else:
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, tuple):
            return list(parsed)
        if isinstance(parsed, list):
            return parsed
        return [parsed]

    # Be tolerant of JSON objects/arrays emitted by some models.
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    else:
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return parsed
        return [parsed]

    # Wrapping is needed for JSON literals such as: "location", 2500000, null.
    try:
        parsed = json.loads(f"[{raw}]")
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return parsed


def parse_action(text: str) -> Tuple[Optional[str], Any]:
    """Parse one line in the form ``Action: tool[arg1, arg2, ...]``.

    The regex deliberately stays on one line. The previous DOTALL expression
    was greedy and could absorb later output, including a Final Answer.
    """
    if not isinstance(text, str):
        return None, {}

    match = _ACTION_RE.search(text)
    if not match:
        return None, {}

    params = _parse_arguments(match.group(2))
    if params is None:
        return None, {}
    return match.group(1), params
