from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.core.dashboard import build_dashboard_overview
from services.db.session import get_db_session
from services.schemas.output import DashboardOverviewRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview/latest", response_model=DashboardOverviewRead)
async def get_dashboard_overview_route(
    trade_date: date | None = None,
    watchlist_id: int | None = None,
    session: Session = Depends(get_db_session),
) -> DashboardOverviewRead:
    overview = build_dashboard_overview(session, trade_date=trade_date, watchlist_id=watchlist_id)
    if overview is None:
        raise HTTPException(status_code=404, detail="dashboard overview not found")
    return overview
