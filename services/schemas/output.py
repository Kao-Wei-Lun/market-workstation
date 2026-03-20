from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from services.core.derivatives.summary import DailyInstitutionalBiasSummary
from services.schemas.backtesting import BacktestRunRead, BacktestTradeRead
from services.schemas.candidates import CandidateItemRead, CandidateRunRead
from services.schemas.classification import GroupScannerRead, GroupSummaryRead, WatchlistRead
from services.schemas.reporting import MarketSummaryContent, ReportDailyRead


class DashboardMetaRead(BaseModel):
    generated_at: datetime
    as_of_date: date | None = None
    is_empty: bool
    item_count: int = 0
    returned_count: int = 0
    limit: int | None = None
    offset: int | None = None


class DashboardSummaryCardRead(BaseModel):
    key: str
    label: str
    value: str
    display_value: str
    tone: Literal["positive", "negative", "neutral", "info"] = "neutral"


class DashboardRankedItemRead(BaseModel):
    key: str
    label: str
    primary_value: str
    secondary_value: str | None = None
    hint: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class DashboardRankedListRead(BaseModel):
    key: str
    title: str
    item_count: int
    items: list[DashboardRankedItemRead] = Field(default_factory=list)


class DashboardViewBaseRead(BaseModel):
    meta: DashboardMetaRead
    summary_cards: list[DashboardSummaryCardRead] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    ranked_lists: list[DashboardRankedListRead] = Field(default_factory=list)


class WatchlistSummarySnapshotRead(BaseModel):
    watchlist: WatchlistRead
    trade_date: date
    summary: GroupSummaryRead
    scanner: GroupScannerRead | None = None


class GroupSummarySnapshotRead(BaseModel):
    tag: str
    trade_date: date
    summary: GroupSummaryRead
    scanner: GroupScannerRead | None = None


class CandidateSummarySnapshotRead(BaseModel):
    run: CandidateRunRead
    top_items: list[CandidateItemRead]


class ReportSummarySnapshotRead(BaseModel):
    reports: list[ReportDailyRead] = Field(default_factory=list)


class BacktestSummarySnapshotRead(BaseModel):
    latest_run: BacktestRunRead | None = None
    recent_runs: list[BacktestRunRead] = Field(default_factory=list)
    recent_trades: list[BacktestTradeRead] = Field(default_factory=list)


class DashboardOverviewDataRead(BaseModel):
    market_snapshot: MarketSummaryContent | None = None
    watchlist_summary: WatchlistSummarySnapshotRead | None = None
    group_summary: GroupSummarySnapshotRead | None = None
    candidate_summary: CandidateSummarySnapshotRead | None = None
    derivatives_summary: DailyInstitutionalBiasSummary | None = None
    backtest_summary: BacktestSummarySnapshotRead | None = None
    report_summary: ReportSummarySnapshotRead | None = None


class DashboardOverviewRead(DashboardViewBaseRead):
    data: DashboardOverviewDataRead


class WatchlistDashboardRead(DashboardViewBaseRead):
    data: WatchlistSummarySnapshotRead | None = None


class GroupDashboardRead(DashboardViewBaseRead):
    data: GroupSummarySnapshotRead | None = None


class CandidatesDashboardRead(DashboardViewBaseRead):
    data: CandidateSummarySnapshotRead | None = None


class DerivativesDashboardRead(DashboardViewBaseRead):
    data: DailyInstitutionalBiasSummary | None = None


class BacktestsDashboardRead(DashboardViewBaseRead):
    data: BacktestSummarySnapshotRead | None = None


class ReportsDashboardRead(DashboardViewBaseRead):
    data: ReportSummarySnapshotRead | None = None
