from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Generic, TypeVar

from pydantic import BaseModel

ReportContentT = TypeVar("ReportContentT", bound=BaseModel, covariant=True)


@dataclass(frozen=True)
class GeneratedReport(Generic[ReportContentT]):
    report_date: date
    report_type: str
    report_key: str
    title: str
    content: ReportContentT
    markdown_text: str

    def content_json(self) -> dict[str, object]:
        return json.loads(self.content.model_dump_json())
