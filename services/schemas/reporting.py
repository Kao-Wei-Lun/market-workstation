from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from services.core.derivatives.summary import DailyInstitutionalBiasSummary
from services.schemas.candidates import CandidateSummaryRead
from services.schemas.classification import GroupMemberChange, GroupSummaryRead


class MarketSummaryContent(BaseModel):
    trade_date: date
    instrument_count: int
    advancers: int
    decliners: int
    unchanged: int
    average_close_change_pct: Decimal
    percentage_above_sma20: Decimal
    top_gainers: list[GroupMemberChange]
    top_losers: list[GroupMemberChange]


class WatchlistSummaryContent(BaseModel):
    trade_date: date
    watchlist_id: int
    watchlist_name: str
    summary: GroupSummaryRead


class GroupSummarySnapshotContent(BaseModel):
    trade_date: date
    tag: str
    summary: GroupSummaryRead


class TaiwanDerivativesSummaryContent(BaseModel):
    trade_date: date
    summary: DailyInstitutionalBiasSummary


class NextDayWatchCandidate(BaseModel):
    instrument_id: int
    symbol: str
    candidate_date: date
    score: Decimal
    rank: int
    reasons: list[str] = Field(default_factory=list)
    supporting_metrics: dict[str, Any] = Field(default_factory=dict)


class NextDayWatchCandidatesContent(BaseModel):
    trade_date: date
    candidate_count: int
    summary: CandidateSummaryRead
    candidates: list[NextDayWatchCandidate]


class ReportDailyRead(BaseModel):
    id: int
    report_date: date
    report_type: str
    report_key: str
    title: str
    content_json: dict[str, Any]
    markdown_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
