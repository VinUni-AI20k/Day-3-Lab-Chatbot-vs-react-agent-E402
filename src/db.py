"""
🗄️ DATABASE WRAPPER — books.db (Goodreads Books)
Chỉ cho phép SELECT, tự chèn LIMIT, bắt exception trả string.
"""

import os
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "books.db"

FORBIDDEN = [
    "insert ", "update ", "delete ", "drop ", "alter ", "create ",
    "replace ", "truncate ", "attach ", "detach ", "pragma ",
    "vacuum", "reindex",
]


def get_connection() -> sqlite3.Connection:
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def is_select_only(sql: str) -> bool:
    cleaned = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip().lower()
    if not cleaned or not cleaned.startswith("select"):
        return False
    return not any(tok in cleaned for tok in FORBIDDEN)


def ensure_limit(sql: str, default_limit: int = 100) -> str:
    s = sql.strip().rstrip(";").strip()
    if re.search(r"\blimit\b", s, re.IGNORECASE):
        return s + ";"
    return f"{s} LIMIT {default_limit};"


def safe_execute(sql: str, limit: int = 100) -> dict:
    if not is_select_only(sql):
        return {"error": "GUARDRAIL: Chỉ SELECT. DML/DDL bị chặn."}
    sql_safe = ensure_limit(sql, default_limit=limit)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql_safe)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        conn.close()
        return {
            "columns": cols,
            "rows": [list(r) for r in rows],
            "row_count": len(rows),
            "executed_sql": sql_safe,
        }
    except sqlite3.Error as e:
        return {"error": f"SQLiteError: {e}", "executed_sql": sql_safe}
    except Exception as e:
        return {"error": f"UnexpectedError: {e}", "executed_sql": sql_safe}


def describe(table: str) -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info([{table}])")
        cols = [
            {"name": r[1], "type": r[2], "nullable": not r[3], "pk": bool(r[5])}
            for r in cur.fetchall()
        ]
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        except sqlite3.Error:
            cnt = -1
        conn.close()
        return {"table": table, "columns": cols, "row_count": cnt}
    except Exception as e:
        return {"error": f"describe failed: {e}"}


def list_all_tables() -> list:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [r[0] for r in cur.fetchall()]
        conn.close()
        return tables
    except Exception:
        return []


if __name__ == "__main__":
    print("DB_PATH:", DB_PATH, "exists?", DB_PATH.exists())
    print("Tables:", list_all_tables())
    print("Describe books:")
    import json
    print(json.dumps(describe("books"), indent=2, ensure_ascii=False)[:1500])
    print("\nSafe execute test:")
    print(safe_execute("SELECT COUNT(*) FROM books"))
    print("\nGuardrail test (DROP):")
    print(safe_execute("DROP TABLE books"))