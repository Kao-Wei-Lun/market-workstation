from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from services.core.dashboard import (
    build_backtests_dashboard,
    build_candidates_dashboard,
    build_dashboard_overview,
    build_derivatives_dashboard,
    build_group_dashboard,
    build_reports_dashboard,
    build_watchlist_dashboard,
)
from services.db.session import get_db_session
from services.schemas.output import (
    BacktestsDashboardRead,
    CandidatesDashboardRead,
    DashboardOverviewRead,
    DerivativesDashboardRead,
    GroupDashboardRead,
    ReportsDashboardRead,
    WatchlistDashboardRead,
)

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard/overview", response_model=DashboardOverviewRead)
@router.get("/dashboard/overview/latest", response_model=DashboardOverviewRead, include_in_schema=False)
async def get_dashboard_overview_route(
    trade_date: date | None = None,
    watchlist_id: int | None = None,
    tag: str | None = None,
    top_n: int = Query(default=5, ge=1, le=20),
    session: Session = Depends(get_db_session),
) -> DashboardOverviewRead:
    return build_dashboard_overview(
        session,
        trade_date=trade_date,
        watchlist_id=watchlist_id,
        tag=tag,
        top_n=top_n,
    )


@router.get("/api/dashboard/watchlists/{watchlist_id}", response_model=WatchlistDashboardRead)
async def get_dashboard_watchlist_route(
    watchlist_id: int,
    trade_date: date | None = None,
    top_n: int = Query(default=5, ge=1, le=20),
    session: Session = Depends(get_db_session),
) -> WatchlistDashboardRead:
    response = build_watchlist_dashboard(session, watchlist_id=watchlist_id, trade_date=trade_date, top_n=top_n)
    if response.data is None and response.meta.is_empty:
        raise HTTPException(status_code=404, detail="watchlist not found")
    return response


@router.get("/api/dashboard/groups/{tag}", response_model=GroupDashboardRead)
async def get_dashboard_group_route(
    tag: str,
    trade_date: date | None = None,
    top_n: int = Query(default=5, ge=1, le=20),
    session: Session = Depends(get_db_session),
) -> GroupDashboardRead:
    return build_group_dashboard(session, tag=tag, trade_date=trade_date, top_n=top_n)


@router.get("/api/dashboard/candidates/latest", response_model=CandidatesDashboardRead)
async def get_dashboard_candidates_route(
    candidate_date: date | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
) -> CandidatesDashboardRead:
    return build_candidates_dashboard(session, candidate_date=candidate_date, limit=limit, offset=offset)


@router.get("/api/dashboard/derivatives/latest", response_model=DerivativesDashboardRead)
async def get_dashboard_derivatives_route(
    trade_date: date | None = None,
    session: Session = Depends(get_db_session),
) -> DerivativesDashboardRead:
    return build_derivatives_dashboard(session, trade_date=trade_date)


@router.get("/api/dashboard/backtests/latest", response_model=BacktestsDashboardRead)
async def get_dashboard_backtests_route(
    limit: int = Query(default=5, ge=1, le=20),
    session: Session = Depends(get_db_session),
) -> BacktestsDashboardRead:
    return build_backtests_dashboard(session, limit=limit)


@router.get("/api/dashboard/reports/latest", response_model=ReportsDashboardRead)
async def get_dashboard_reports_route(
    report_date: date | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
) -> ReportsDashboardRead:
    return build_reports_dashboard(session, report_date=report_date, limit=limit, offset=offset)
