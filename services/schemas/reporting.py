from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from services.core.derivatives.summary import DailyInstitutionalBiasSummary
from services.schemas.candidates import CandidateSummaryRead
from services.schemas.classification import GroupMemberChange, GroupSummaryRead

REPORT_BUNDLE_VERSION = "v1"


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


class TopMoversSummaryContent(BaseModel):
    trade_date: date
    top_gainers: list[GroupMemberChange]
    top_losers: list[GroupMemberChange]


class TechnicalBreadthSummaryContent(BaseModel):
    trade_date: date
    instrument_count: int
    gainers: int
    losers: int
    unchanged: int
    percentage_above_sma20: Decimal
    positive_momentum_signal_count: int


class RankedSummaryEntry(BaseModel):
    name: str
    average_daily_return_pct: Decimal
    percentage_above_sma: Decimal | None = None
    member_count: int


class GroupScannerSummaryContent(BaseModel):
    trade_date: date
    strongest_groups: list[RankedSummaryEntry]
    weakest_groups: list[RankedSummaryEntry]


class WatchlistHighlightSummaryContent(BaseModel):
    trade_date: date
    strongest_watchlists: list[RankedSummaryEntry]
    weakest_watchlists: list[RankedSummaryEntry]


class ReportSectionRead(BaseModel):
    title: str
    section_type: str
    markdown_body: str
    payload_json: dict[str, Any]


class DailyReportBundleMetadata(BaseModel):
    report_date: date
    bundle_version: str = REPORT_BUNDLE_VERSION
    section_count: int
    strongest_group_name: str | None = None
    weakest_group_name: str | None = None
    strongest_watchlist_name: str | None = None
    weakest_watchlist_name: str | None = None
    top_candidate_symbols: list[str] = Field(default_factory=list)


class DailyReportBundleContent(BaseModel):
    report_date: date
    metadata: DailyReportBundleMetadata
    sections: list[ReportSectionRead]


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
