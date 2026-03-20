from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.core.visibility import build_system_status, build_universe_coverage
from services.db.session import get_db_session
from services.schemas.visibility import SystemStatusRead, UniverseCoverageRead

router = APIRouter(tags=["system"])


@router.get("/api/system/coverage", response_model=UniverseCoverageRead)
async def get_system_coverage_route(
    preset_name: str = "v1_market_expanded",
    session: Session = Depends(get_db_session),
) -> UniverseCoverageRead:
    return build_universe_coverage(session, preset_name=preset_name)


@router.get("/api/system/status", response_model=SystemStatusRead)
async def get_system_status_route(
    job_limit: int = Query(default=20, ge=1, le=100),
    worker_stale_minutes: int = Query(default=30, ge=1, le=24 * 60),
    session: Session = Depends(get_db_session),
) -> SystemStatusRead:
    return build_system_status(
        session,
        job_limit=job_limit,
        worker_stale_minutes=worker_stale_minutes,
    )
