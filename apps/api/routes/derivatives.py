from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.core.derivatives.summary import (
    DailyInstitutionalBiasSummary,
    get_latest_institutional_bias_summary,
    load_daily_institutional_bias_summary,
)
from services.db.session import get_db_session

router = APIRouter(prefix="/derivatives", tags=["derivatives"])


@router.get("/summary/latest", response_model=DailyInstitutionalBiasSummary)
async def get_latest_derivatives_summary_route(
    session: Session = Depends(get_db_session),
) -> DailyInstitutionalBiasSummary:
    summary = get_latest_institutional_bias_summary(session)
    if summary is None:
        raise HTTPException(status_code=404, detail="derivatives summary not found")
    return summary


@router.get("/summary/{trade_date}", response_model=DailyInstitutionalBiasSummary)
async def get_derivatives_summary_route(
    trade_date: date,
    session: Session = Depends(get_db_session),
) -> DailyInstitutionalBiasSummary:
    summary = load_daily_institutional_bias_summary(session, trade_date=trade_date)
    if summary.bullish_count == 0 and summary.bearish_count == 0 and summary.neutral_count == 0:
        raise HTTPException(status_code=404, detail="derivatives summary not found")
    return summary
