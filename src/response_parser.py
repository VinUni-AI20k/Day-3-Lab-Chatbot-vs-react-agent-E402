"""
🔬 REACT PARSER — parse output của LLM thành Thought / Action / Final Answer.
- Hỗ trợ SQL có dấu phẩy trong execute_select_query (không split sai)
- Hỗ trợ multi-line Thought
- Robust với text có ký tự lạ
"""

import re
import ast

ACTION_RE = re.compile(
    r"Action:\s*(\w+)\s*\[(.*)\]\s*$",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
THOUGHT_RE = re.compile(r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)", re.IGNORECASE | re.DOTALL)
FINAL_RE = re.compile(r"Final Answer:\s*(.*)$", re.IGNORECASE | re.DOTALL)

SQL_TOOLS = {"execute_select_query", "validate_sql", "dry_run_query"}


def parse_response(text: str) -> dict:
    """Parse output LLM thành dict {thought, action, args, final_answer, raw}."""
    result = {"thought": "", "action": None, "args": [], "final_answer": None, "raw": text}

    final_m = FINAL_RE.search(text)
    if final_m:
        result["final_answer"] = final_m.group(1).strip()

    thought_m = THOUGHT_RE.search(text)
    if thought_m:
        result["thought"] = thought_m.group(1).strip()

    action_m = ACTION_RE.search(text)
    if action_m:
        result["action"] = action_m.group(1)
        args_str = action_m.group(2).strip()
        result["args"] = _parse_args(args_str, result["action"])

    return result


def _parse_args(args_str: str, tool_name: str = "") -> list:
    if not args_str:
        return []
    if tool_name in SQL_TOOLS:
        # SQL có dấu phẩy → không split; tách optional limit cuối nếu là số
        depth = 0
        in_q = None
        last_comma = -1
        for i, ch in enumerate(args_str):
            if in_q:
                if ch == in_q: in_q = None
                continue
            if ch in "'\"":
                in_q = ch; continue
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                last_comma = i
        if last_comma != -1:
            right = args_str[last_comma + 1:].strip()
            if right.lstrip("-").isdigit():
                sql = args_str[:last_comma].strip()
                return [_strip_quotes(sql), int(right)]
        return [_strip_quotes(args_str)]
    # Tool khác: split theo comma ở depth 0
    parts = _split_args(args_str)
    out = []
    for p in parts:
        p = p.strip()
        try:
            out.append(ast.literal_eval(p))
        except Exception:
            out.append(_strip_quotes(p))
    return out


def _split_args(s: str) -> list:
    parts = []
    depth = 0
    cur = []
    in_q = None
    for ch in s:
        if in_q:
            cur.append(ch)
            if ch == in_q: in_q = None
            continue
        if ch in "'\"":
            in_q = ch; cur.append(ch); continue
        if ch in "([{":
            depth += 1; cur.append(ch); continue
        if ch in ")]}":
            depth -= 1; cur.append(ch); continue
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []; continue
        cur.append(ch)
    if cur:
        parts.append("".join(cur))
    return parts


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    return s


if __name__ == "__main__":
    tests = [
        "Thought: Cần xem schema.\nAction: describe_table[books]",
        "Thought: Top 5.\nAction: execute_select_query[SELECT title, avg_rating FROM books WHERE num_ratings >= 1000 ORDER BY avg_rating DESC LIMIT 5]",
        "Thought: Đã có.\nFinal Answer: Top 5: Harry Potter...",
        "Action: execute_select_query[SELECT COUNT(*) FROM books]",
    ]
    for t in tests:
        print("---")
        print(t)
        print("=>", parse_response(t))