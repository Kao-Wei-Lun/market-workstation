from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from services.core.derivatives.summary import DailyInstitutionalBiasSummary
from services.schemas.candidates import CandidateItemRead, CandidateRunRead
from services.schemas.classification import GroupSummaryRead, WatchlistRead
from services.schemas.reporting import MarketSummaryContent


class WatchlistSummarySnapshotRead(BaseModel):
    watchlist: WatchlistRead
    trade_date: date
    summary: GroupSummaryRead


class CandidateSummarySnapshotRead(BaseModel):
    run: CandidateRunRead
    top_items: list[CandidateItemRead]


class DashboardOverviewRead(BaseModel):
    trade_date: date
    market_snapshot: MarketSummaryContent
    watchlist_summary: WatchlistSummarySnapshotRead | None = None
    candidate_summary: CandidateSummarySnapshotRead | None = None
    derivatives_summary: DailyInstitutionalBiasSummary | None = None
