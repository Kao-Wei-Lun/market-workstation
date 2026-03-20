from __future__ import annotations

import csv
import io
from typing import Any


def rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    fieldnames = list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _serialize_csv_value(row.get(key)) for key in fieldnames})
    return buffer.getvalue()


def _serialize_csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return str(value)
    return value
