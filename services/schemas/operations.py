from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from services.schemas.output import DashboardMetaRead, DashboardSummaryCardRead


class ManualTaskActionRead(BaseModel):
    action_key: str
    label: str
    description: str
    target_label: str
    target_route_name: str | None = None
    requires_trade_date: bool = True
    suggested_trade_date: date | None = None


class ManualTaskHistoryItemRead(BaseModel):
    id: int
    action_key: str
    label: str
    description: str
    target_label: str
    status: str
    trade_date: date | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error_summary: str | None = None
    source_route: str
    job_type: str


class ManualTaskCenterDataRead(BaseModel):
    available_actions: list[ManualTaskActionRead] = Field(default_factory=list)
    recent_tasks: list[ManualTaskHistoryItemRead] = Field(default_factory=list)


class ManualTaskCenterRead(BaseModel):
    meta: DashboardMetaRead
    summary_cards: list[DashboardSummaryCardRead] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    data: ManualTaskCenterDataRead


class ManualTaskRunRequest(BaseModel):
    trade_date: date | None = None


class ManualTaskRunRead(BaseModel):
    action_key: str
    label: str
    target_label: str
    target_route_name: str | None = None
    status: Literal["success", "failed"]
    trade_date: date | None = None
    metrics: dict[str, int] = Field(default_factory=dict)
    message: str
    history_item: ManualTaskHistoryItemRead
