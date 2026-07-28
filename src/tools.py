"""
🛠️ TOOL REGISTRY (Text-to-SQL Agent — Goodreads Books)
Theo tinh thần DAY3: tối thiểu 2 tool, đơn giản, an toàn.
- describe_table: khám phá schema
- execute_select_query: chạy SELECT an toàn
"""

import sqlite3
from db import describe, safe_execute, is_select_only, ensure_limit, get_connection


def describe_table(table: str) -> str:
    """
    Trả về schema của 1 bảng: tên cột, type, PK, nullable, row count.
    Dùng khi cần biết bảng X có cột nào, kiểu dữ liệu ra sao.
    Args:
        table (str): tên bảng (VD: 'books'). Không phân biệt hoa thường.
    Returns:
        str: mô tả cột + row count, hoặc thông báo lỗi nếu bảng không tồn tại.
    """
    info = describe(table.strip())
    if "error" in info:
        return info["error"]
    lines = [f"📋 Bảng {info['table']} (row_count={info['row_count']})"]
    lines.append("Cột:")
    for c in info["columns"]:
        pk = " [PK]" if c["pk"] else ""
        null = "" if c["nullable"] else " [NOT NULL]"
        lines.append(f"  - {c['name']} : {c['type']}{pk}{null}")
    return "\n".join(lines)


def execute_select_query(sql: str, limit: int = 100) -> str:
    """
    Thực thi câu SELECT an toàn trên books.db.
    - Tự chèn LIMIT nếu thiếu (mặc định 100, tối đa 500)
    - Reject mọi lệnh DML/DDL (INSERT/UPDATE/DROP/PRAGMA/...)
    - Bắt exception trả về string thay vì crash
    Args:
        sql (str): câu SELECT đầy đủ
        limit (int): số dòng tối đa trả về (mặc định 100)
    Returns:
        str: bảng kết quả dạng text. Nếu query lỗi trả về mô tả lỗi để Agent suy luận sửa.
    """
    limit = max(1, min(int(limit), 500))
    res = safe_execute(sql, limit=limit)
    if "error" in res:
        return res["error"]
    cols = res["columns"]
    rows = res["rows"]
    if not rows:
        return f"Query chạy thành công nhưng không có dòng nào trả về.\nExecuted SQL: {res['executed_sql']}"
    lines = [f"✅ Query OK (row_count={res['row_count']}, executed_sql={res['executed_sql']})"]
    lines.append(" | ".join(cols))
    lines.append("-" * 80)
    for row in rows[:limit]:
        lines.append(" | ".join(str(v) for v in row))
    if res["row_count"] > limit:
        lines.append(f"... ({res['row_count'] - limit} dòng bị cắt do LIMIT)")
    return "\n".join(lines)


# Đăng ký tool
AVAILABLE_TOOLS = {
    "describe_table": describe_table,
    "execute_select_query": execute_select_query,
}


if __name__ == "__main__":
    print("=== TEST TOOLS ===")
    print("\n[1] describe_table('books'):")
    print(describe_table("books"))
    print("\n[2] execute_select_query top 5 sách rating cao nhất:")
    sql = "SELECT title, author, avg_rating, num_ratings FROM books WHERE num_ratings >= 1000 ORDER BY avg_rating DESC, num_ratings DESC LIMIT 5"
    print(execute_select_query(sql))
    print("\n[3] Guardrail DROP:")
    print(execute_select_query("DROP TABLE books"))
    print("\n[4] Syntax error:")
    print(execute_select_query("SELECT * FORM books"))