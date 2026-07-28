

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WIDE_CSV_PATH = PROJECT_ROOT / "config" / "DataTPCN.csv"
NORMALIZED_CSV_PATH = PROJECT_ROOT / "data" / "products.csv"
CSV_PATH = WIDE_CSV_PATH if WIDE_CSV_PATH.is_file() else NORMALIZED_CSV_PATH

REQUIRED_COLUMNS = {
    "product_id",
    "product_name",
    "brand",
    "price_vnd",
    "servings_per_container",
    "ingredient_name",
    "amount",
    "unit",
}
OPTIONAL_COLUMNS = {"product_url", "ingredient_type", "note"}

WIDE_REQUIRED_COLUMNS = {
    "Tên thực phẩm chức năng",
    "Giá tiền",
    "Cách dùng",
    "Chống chỉ định",
    "Liều dùng",
}

AMOUNT_PATTERN = re.compile(
    r"(?P<amount>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>mg|mcg|µg|ug|g|kg|iu|cfu|ml|l|%)\b",
    re.IGNORECASE,
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _error(message: str, **details: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"success": False, "error": message}
    result.update(details)
    return result


def _csv_path(csv_path: str | Path | None) -> Path:
    if not csv_path:
        return CSV_PATH
    path = Path(csv_path).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _number(value: Any, field_name: str) -> float:
    text = _clean(value).replace(" ", "")
    if not text:
        raise ValueError(f"{field_name} đang để trống.")

    # Hỗ trợ 450000, 450.000 và 450,000 cho các trường số nguyên lớn.
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", text):
        text = text.replace(".", "").replace(",", "")
    else:
        text = text.replace(",", ".")

    number = float(text)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} không phải số hữu hạn.")
    return number


def _display_number(value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    try:
        number = _number(text, "amount")
    except ValueError:
        return text
    return str(int(number)) if number.is_integer() else str(number)


def _parse_price_vnd(value: str) -> str:
    """Chuyển '1.500.000 VNĐ' thành '1500000'."""
    digits = re.sub(r"\D", "", _clean(value))
    return digits


def _split_ingredient_value(
    column_name: str,
    raw_value: str,
) -> tuple[str, str, str, str]:
    """
    Tách tên/lượng/đơn vị từ một ô bảng rộng mà không làm mất text gốc.

    Với cột vitamin cố định, tên thành phần lấy từ tiêu đề cột.
    Với "Thành phần đặc biệt khác", tên được lấy từ chính nội dung ô.
    """
    value = _clean(raw_value)
    match = AMOUNT_PATTERN.search(value)
    amount = match.group("amount").replace(",", ".") if match else ""
    unit = match.group("unit") if match else ""

    if column_name != "Thành phần đặc biệt khác":
        return column_name, amount, unit, value

    if match:
        before = value[: match.start()].strip(" ,-:;")
        after = value[match.end() :].strip(" ,-:;")
        ingredient_name = after or before or value
    else:
        ingredient_name = value

    return ingredient_name, amount, unit, value


def _convert_wide_rows(
    source_rows: list[dict[str, str]],
    fieldnames: list[str],
) -> tuple[list[dict[str, str]], list[str]]:
    """Chuyển bảng rộng tiếng Việt thành dạng mỗi dòng = một thành phần."""
    ingredient_columns = [
        column for column in fieldnames if column not in WIDE_REQUIRED_COLUMNS
    ]
    normalized: list[dict[str, str]] = []
    warnings: list[str] = []

    for product_index, source in enumerate(source_rows, start=1):
        source_line = product_index + 1
        product_name = _clean(source.get("Tên thực phẩm chức năng"))
        product_id = f"P{product_index:03d}"
        found_ingredient = False

        for column in ingredient_columns:
            raw_value = _clean(source.get(column))
            if not raw_value:
                continue
            found_ingredient = True
            name, amount, unit, original = _split_ingredient_value(
                column, raw_value
            )
            normalized.append(
                {
                    "product_id": product_id,
                    "product_name": product_name,
                    "brand": "",
                    "price_vnd": _parse_price_vnd(source.get("Giá tiền", "")),
                    # Dataset chỉ có liều dùng, không có số serving trong hộp.
                    "servings_per_container": "",
                    "ingredient_name": name,
                    "amount": amount,
                    "unit": unit,
                    "product_url": "",
                    "ingredient_type": "",
                    "note": original,
                    "usage": _clean(source.get("Cách dùng")),
                    "contraindication": _clean(source.get("Chống chỉ định")),
                    "dosage": _clean(source.get("Liều dùng")),
                    "_csv_line": str(source_line),
                }
            )

        if not product_name:
            warnings.append(f"Dòng {source_line}: thiếu tên sản phẩm.")
        if not found_ingredient:
            warnings.append(
                f"Dòng {source_line} ({product_name or product_id}): "
                "không có ô thành phần nào."
            )

    warnings.append(
        "Dataset không có product_id nên tool tạo ID P001, P002... theo thứ tự dòng."
    )
    warnings.append(
        "Dataset không có servings_per_container; chưa thể tính cost/serving "
        "nếu người dùng không cung cấp giá trị này riêng."
    )
    return normalized, warnings


def _read_database(
    csv_path: str | Path | None = None,
) -> tuple[list[dict[str, str]], Path, list[str]]:
    """
    Đọc toàn bộ CSV. Không drop duplicate và không bỏ dòng thành phần lỗi.
    """
    path = _csv_path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy CSV: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV không có dòng tiêu đề.")

        fieldnames = [_clean(name) for name in reader.fieldnames if name]
        columns = set(fieldnames)
        is_normalized = REQUIRED_COLUMNS.issubset(columns)
        is_wide = WIDE_REQUIRED_COLUMNS.issubset(columns)
        if not is_normalized and not is_wide:
            missing_normalized = sorted(REQUIRED_COLUMNS - columns)
            missing_wide = sorted(WIDE_REQUIRED_COLUMNS - columns)
            raise ValueError(
                "CSV không khớp schema dạng dòng hoặc dạng bảng rộng. "
                f"Schema dòng thiếu: {', '.join(missing_normalized)}. "
                f"Schema rộng thiếu: {', '.join(missing_wide)}."
            )

        source_rows: list[dict[str, str]] = []
        warnings: list[str] = []
        for line_number, source_row in enumerate(reader, start=2):
            row = {
                _clean(key): _clean(value)
                for key, value in source_row.items()
                if key is not None
            }
            if not any(row.values()):
                continue
            if is_normalized:
                row["_csv_line"] = str(line_number)
                missing_values = [
                    column for column in REQUIRED_COLUMNS if not row.get(column)
                ]
                if missing_values:
                    warnings.append(
                        f"Dòng {line_number} thiếu giá trị: "
                        + ", ".join(sorted(missing_values))
                    )
            source_rows.append(row)

        if is_wide and not is_normalized:
            rows, conversion_warnings = _convert_wide_rows(
                source_rows, fieldnames
            )
            warnings.extend(conversion_warnings)
        else:
            rows = source_rows

    return rows, path, warnings


def load_product_database(
    csv_path: str | Path | None = None,
) -> dict[str, Any]:
    """Kiểm tra CSV và báo tổng số sản phẩm/dòng thành phần."""
    try:
        rows, path, warnings = _read_database(csv_path)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        return _error(str(exc))

    product_ids = {row.get("product_id") for row in rows if row.get("product_id")}
    return {
        "success": True,
        "csv_path": str(path),
        "product_count": len(product_ids),
        "ingredient_row_count": len(rows),
        "warnings": warnings,
    }


def search_products(
    product_name: str,
    csv_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Tìm sản phẩm bằng cách khớp CHÍNH XÁC toàn bộ tên sản phẩm.

    Không phân biệt chữ hoa/thường và bỏ qua khoảng trắng thừa ở đầu/cuối hoặc
    giữa các từ. Không tìm gần đúng, không tìm theo ID/thương hiệu/link.
    """
    product_name = _clean(product_name)
    if not product_name:
        return _error("Tên sản phẩm không được để trống.")

    try:
        rows, path, warnings = _read_database(csv_path)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        return _error(str(exc))

    expected_name = product_name.casefold()
    products: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for row in rows:
        product_id = row.get("product_id", "")
        actual_name = _clean(row.get("product_name", "")).casefold()
        if actual_name == expected_name and product_id not in seen_ids:
            seen_ids.add(product_id)
            products.append(
                {
                    "product_id": product_id,
                    "product_name": row.get("product_name", ""),
                    "brand": row.get("brand", ""),
                    "product_url": row.get("product_url", ""),
                }
            )

    if not products:
        return {
            "success": False,
            "error": "Không có sản phẩm.",
            "product_name": product_name,
            "match_count": 0,
            "products": [],
            "csv_path": str(path),
        }

    return {
        "success": True,
        "product_name": product_name,
        "match_count": len(products),
        "products": products,
        "csv_path": str(path),
        "warnings": warnings,
    }


def get_product_ingredients(
    product_id: str,
    csv_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Lấy 100% dòng thành phần thuộc một product_id, theo đúng thứ tự CSV.

    Không giới hạn số thành phần, không drop duplicate, không bỏ dòng thiếu
    amount/unit. Mỗi phần tử chứa csv_line để kiểm tra ngược dữ liệu nguồn.
    """
    product_id = _clean(product_id)
    if not product_id:
        return _error("product_id không được để trống.")

    try:
        rows, path, database_warnings = _read_database(csv_path)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        return _error(str(exc), product_id=product_id)

    matched = [
        row
        for row in rows
        if row.get("product_id", "").casefold() == product_id.casefold()
    ]
    if not matched:
        return _error(
            "Không tìm thấy product_id trong CSV.",
            product_id=product_id,
            csv_path=str(path),
        )

    first = matched[0]
    inconsistent: list[str] = []
    for field in (
        "product_name", "brand", "price_vnd", "servings_per_container"
    ):
        values = {row.get(field, "") for row in matched}
        if len(values) > 1:
            inconsistent.append(field)

    ingredients = [
        {
            "ingredient_name": row.get("ingredient_name")
            or "(Thiếu tên thành phần)",
            "amount": row.get("amount", ""),
            "unit": row.get("unit", ""),
            "ingredient_type": row.get("ingredient_type", ""),
            "note": row.get("note", ""),
            "csv_line": int(row["_csv_line"]),
        }
        for row in matched
    ]

    warnings = list(database_warnings)
    if inconsistent:
        warnings.append(
            f"{product_id} có metadata không nhất quán giữa các dòng: "
            + ", ".join(inconsistent)
        )

    return {
        "success": True,
        "product_id": first.get("product_id", product_id),
        "product_name": first.get("product_name") or "(Thiếu tên sản phẩm)",
        "brand": first.get("brand") or "(Không xác định)",
        "product_url": first.get("product_url", ""),
        "price_vnd": first.get("price_vnd", ""),
        "servings_per_container": first.get("servings_per_container", ""),
        "usage": first.get("usage", ""),
        "contraindication": first.get("contraindication", ""),
        "dosage": first.get("dosage", ""),
        "ingredient_count": len(ingredients),
        "ingredients": ingredients,
        "csv_path": str(path),
        "warnings": warnings,
    }


def calculate_cost_per_serving(
    price_vnd: float,
    servings_per_container: float,
) -> dict[str, Any]:
    """Tính chi phí VNĐ trên mỗi khẩu phần."""
    try:
        price = _number(price_vnd, "price_vnd")
        servings = _number(servings_per_container, "servings_per_container")
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    if price <= 0:
        return _error("price_vnd phải lớn hơn 0.")
    if servings <= 0:
        return _error("servings_per_container phải lớn hơn 0.")
    return {
        "success": True,
        "cost_per_serving_vnd": round(price / servings, 2),
    }


def calculate_cost_per_active_amount(
    price_vnd: float,
    servings_per_container: float,
    amount_per_serving: float,
    unit: str,
) -> dict[str, Any]:
    """
    Tính VNĐ trên một đơn vị hoạt chất trong toàn bộ hộp.

    Ví dụ: 500 mg/serving, 60 servings, giá 450.000 VNĐ
    => 15 VNĐ/mg.
    """
    try:
        price = _number(price_vnd, "price_vnd")
        servings = _number(servings_per_container, "servings_per_container")
        amount = _number(amount_per_serving, "amount_per_serving")
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    unit = _clean(unit)
    if price <= 0 or servings <= 0 or amount <= 0:
        return _error("Giá, số serving và lượng hoạt chất phải lớn hơn 0.")
    if not unit:
        return _error("unit không được để trống.")

    return {
        "success": True,
        "cost_per_active_unit_vnd": round(price / (servings * amount), 6),
        "active_unit": unit,
    }


def _matrix_markdown(
    product_names: list[str],
    matrix: list[dict[str, Any]],
) -> str:
    headers = ["Thành phần", *product_names]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in matrix:
        values = [row["ingredient_name"]]
        values.extend(row["products"].get(name) or "—" for name in product_names)
        escaped = [
            _clean(value).replace("\\", "\\\\").replace("|", r"\|")
            for value in values
        ]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines)


def _markdown_cell(value: Any) -> str:
    return _clean(value).replace("\\", "\\\\").replace("|", r"\|")


def _format_vnd(value: Any) -> str:
    try:
        amount = _number(value, "price_vnd")
    except ValueError:
        return _clean(value) or "—"
    return f"{amount:,.0f}".replace(",", ".") + " VNĐ"


def _comparison_markdown(
    products: list[dict[str, Any]],
    matrix_result: dict[str, Any],
) -> str:
    """Tạo đúng một bảng Markdown gồm thông tin chung và toàn bộ thành phần."""
    headers = ["Tiêu chí", *(product["product_name"] for product in products)]
    lines = [
        "| " + " | ".join(_markdown_cell(value) for value in headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]

    cost_values: list[str] = []
    notes: list[str] = []
    for product in products:
        cost = calculate_cost_per_serving(
            product["price_vnd"], product["servings_per_container"]
        )
        if cost.get("success"):
            cost_values.append(_format_vnd(cost["cost_per_serving_vnd"]))
            notes.append("TPCN không phải thuốc và không thay thế thuốc chữa bệnh.")
        else:
            cost_values.append("N/A — thiếu số khẩu phần/hộp")
            notes.append(
                "TPCN không phải thuốc; thiếu số khẩu phần/hộp nên không thể "
                "tính chi phí chính xác."
            )

    fixed_rows = [
        ("Mã sản phẩm", [product["product_id"] for product in products]),
        ("Giá hộp", [_format_vnd(product["price_vnd"]) for product in products]),
        ("Liều dùng", [product.get("dosage") or "—" for product in products]),
        ("Cách dùng", [product.get("usage") or "—" for product in products]),
        (
            "Chống chỉ định",
            [product.get("contraindication") or "—" for product in products],
        ),
        ("Chi phí mỗi liều", cost_values),
        ("Chi phí mỗi ngày", cost_values),
    ]

    for label, values in fixed_rows:
        lines.append(
            "| "
            + " | ".join(_markdown_cell(value) for value in [label, *values])
            + " |"
        )

    for ingredient in matrix_result["matrix"]:
        values = [
            ingredient["products"].get(column) or "—"
            for column in matrix_result["product_columns"]
        ]
        lines.append(
            "| "
            + " | ".join(
                _markdown_cell(value)
                for value in [ingredient["ingredient_name"], *values]
            )
            + " |"
        )

    lines.append(
        "| "
        + " | ".join(_markdown_cell(value) for value in ["Lưu ý", *notes])
        + " |"
    )
    return "\n".join(lines)


def build_comparison_matrix(
    product_ids: Iterable[str],
    csv_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Tạo ma trận dùng HỢP của mọi ingredient thuộc N sản phẩm.

    Mỗi hàng là một thành phần, mỗi cột là một sản phẩm. Thành phần không có
    trong sản phẩm được biểu diễn bằng None/—. Nếu CSV có duplicate cùng
    product + ingredient, mọi giá trị được nối bằng " | " chứ không bị xóa.
    """
    if isinstance(product_ids, str):
        product_ids = [product_ids]
    ids = [_clean(item) for item in product_ids if _clean(item)]
    if not ids:
        return _error("Cần ít nhất một product_id.")

    # Loại ID lặp trong input nhưng giữ nguyên thứ tự lựa chọn.
    unique_ids = list(dict.fromkeys(item.casefold() for item in ids))
    products = [get_product_ingredients(item, csv_path) for item in unique_ids]
    failures = [
        {
            "product_id": product.get("product_id", unique_ids[index]),
            "error": product.get("error", "Lỗi không xác định."),
        }
        for index, product in enumerate(products)
        if not product.get("success")
    ]
    valid_products = [product for product in products if product.get("success")]
    if not valid_products:
        return _error("Không tìm thấy sản phẩm nào.", failures=failures)

    # Dùng tên + ID để tránh hai sản phẩm trùng tên tạo thành cùng một cột.
    column_names = [
        f"{product['product_name']} ({product['product_id']})"
        for product in valid_products
    ]
    ingredient_order: list[str] = []
    canonical_names: dict[str, str] = {}
    values: dict[str, dict[str, list[str]]] = {}

    for product, column_name in zip(valid_products, column_names):
        for ingredient in product["ingredients"]:
            name = ingredient["ingredient_name"]
            key = name.casefold()
            if key not in canonical_names:
                canonical_names[key] = name
                ingredient_order.append(key)
                values[key] = {}

            amount = _display_number(ingredient.get("amount"))
            unit = _clean(ingredient.get("unit"))
            value = " ".join(part for part in (amount, unit) if part) or "Có"
            values[key].setdefault(column_name, []).append(value)

    matrix: list[dict[str, Any]] = []
    for key in ingredient_order:
        cells = {
            column: " | ".join(values[key][column])
            if column in values[key]
            else None
            for column in column_names
        }
        matrix.append(
            {
                "ingredient_name": canonical_names[key],
                "products": cells,
            }
        )

    return {
        "success": True,
        "requested_product_count": len(unique_ids),
        "matched_product_count": len(valid_products),
        "ingredient_count": len(matrix),
        "product_columns": column_names,
        "matrix": matrix,
        "markdown_table": _matrix_markdown(column_names, matrix),
        "failures": failures,
        "warnings": list(
            dict.fromkeys(
                warning
                for product in valid_products
                for warning in product.get("warnings", [])
            )
        ),
    }


def compare_products(
    product_ids: Iterable[str],
    csv_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Tổng hợp ma trận và xếp hạng chi phí/serving từ thấp đến cao.
    """
    matrix_result = build_comparison_matrix(product_ids, csv_path)
    if not matrix_result.get("success"):
        return matrix_result

    rankings: list[dict[str, Any]] = []
    products: list[dict[str, Any]] = []
    for column in matrix_result["product_columns"]:
        product_id = column.rsplit("(", 1)[-1].rstrip(")")
        product = get_product_ingredients(product_id, csv_path)
        products.append(product)
        cost = calculate_cost_per_serving(
            product["price_vnd"], product["servings_per_container"]
        )
        rankings.append(
            {
                "product_id": product_id,
                "product_name": product["product_name"],
                "cost_per_serving_vnd": (
                    cost["cost_per_serving_vnd"]
                    if cost.get("success")
                    else None
                ),
                "cost_error": cost.get("error"),
            }
        )

    rankings.sort(
        key=lambda item: (
            item["cost_per_serving_vnd"] is None,
            item["cost_per_serving_vnd"]
            if item["cost_per_serving_vnd"] is not None
            else math.inf,
        )
    )
    comparison_payload = dict(matrix_result)
    comparison_payload.pop("markdown_table", None)
    return {
        "success": True,
        "comparison_matrix": comparison_payload,
        "cost_per_serving_ranking": rankings,
        "markdown_table": _comparison_markdown(products, matrix_result),
    }


AVAILABLE_TOOLS = {
    "search_products": search_products,
    "get_product_ingredients": get_product_ingredients,
    "build_comparison_matrix": build_comparison_matrix,
    "calculate_cost_per_serving": calculate_cost_per_serving,
    "calculate_cost_per_active_amount": calculate_cost_per_active_amount,
    "compare_products": compare_products,
}


def _configure_console() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass


# def _main() -> int:
#     _configure_console()
#     parser = argparse.ArgumentParser(description="Medicine CSV tools")
#     parser.add_argument(
#         "command", choices=["check", "search", "ingredients", "matrix", "compare"]
#     )
#     parser.add_argument("values", nargs="*")
#     parser.add_argument("--csv", dest="csv_path", default=str(CSV_PATH))
#     parser.add_argument("--json", action="store_true")
#     args = parser.parse_args()

#     if args.command == "check":
#         result = load_product_database(args.csv_path)
#     elif args.command == "search":
#         result = search_products(" ".join(args.values), args.csv_path)
#     elif args.command == "ingredients":
#         result = (
#             get_product_ingredients(args.values[0], args.csv_path)
#             if args.values
#             else _error("Thiếu product_id.")
#         )
#     elif args.command == "matrix":
#         result = build_comparison_matrix(args.values, args.csv_path)
#     else:
#         result = compare_products(args.values, args.csv_path)

#     if args.json:
#         print(json.dumps(result, ensure_ascii=False, indent=2))
#     elif "markdown_table" in result:
#         print(result["markdown_table"])
#     else:
#         print(json.dumps(result, ensure_ascii=False, indent=2))
#     return 0 if result.get("success") else 1


# if __name__ == "__main__":
#     raise SystemExit(_main())
