from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from services.core.candidates.service import get_latest_candidate_run, list_candidate_items
from services.core.classification.summary import summarize_watchlist_group
from services.core.classification.watchlists import get_watchlist
from services.core.derivatives.summary import get_latest_institutional_bias_summary
from services.core.reports.service import build_latest_market_snapshot
from services.schemas.candidates import CandidateItemRead, CandidateRunRead
from services.schemas.output import (
    CandidateSummarySnapshotRead,
    DashboardOverviewRead,
    WatchlistSummarySnapshotRead,
)
from services.schemas.classification import WatchlistRead


def build_dashboard_overview(
    session: Session,
    *,
    trade_date: date | None = None,
    watchlist_id: int | None = None,
) -> DashboardOverviewRead | None:
    market_report = build_latest_market_snapshot(session, report_date=trade_date)
    if market_report is None:
        return None
    resolved_trade_date = market_report.content.trade_date

    watchlist_snapshot = None
    if watchlist_id is not None:
        watchlist = get_watchlist(session, watchlist_id=watchlist_id)
        if watchlist is not None:
            watchlist_snapshot = WatchlistSummarySnapshotRead(
                watchlist=WatchlistRead.model_validate(watchlist),
                trade_date=resolved_trade_date,
                summary=summarize_watchlist_group(
                    session,
                    watchlist_id=watchlist_id,
                    trade_date=resolved_trade_date,
                ),
            )

    candidate_snapshot = None
    candidate_run = get_latest_candidate_run(session)
    if candidate_run is not None:
        items = list_candidate_items(session, candidate_run.id)[:5]
        candidate_snapshot = CandidateSummarySnapshotRead(
            run=CandidateRunRead.model_validate(candidate_run),
            top_items=[CandidateItemRead.model_validate(item) for item in items],
        )

    derivatives_summary = get_latest_institutional_bias_summary(session)
    return DashboardOverviewRead(
        trade_date=resolved_trade_date,
        market_snapshot=market_report.content,
        watchlist_summary=watchlist_snapshot,
        candidate_summary=candidate_snapshot,
        derivatives_summary=derivatives_summary,
    )
