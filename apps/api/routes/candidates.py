from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from services.core.candidates.service import (
    export_candidate_items,
    generate_and_persist_candidate_run,
    get_latest_candidate_run,
    get_candidate_run,
    get_latest_candidate_run_for_date,
    list_candidate_runs,
    list_candidate_items,
)
from services.db.session import get_db_session
from services.schemas.candidates import (
    CandidateGenerateRequest,
    CandidateItemRead,
    CandidateRunRead,
    CandidateRunWithItemsRead,
)

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("/runs", response_model=CandidateRunWithItemsRead)
async def generate_candidate_run_route(
    request: CandidateGenerateRequest,
    session: Session = Depends(get_db_session),
) -> CandidateRunWithItemsRead:
    run, items = generate_and_persist_candidate_run(
        session,
        candidate_date=request.candidate_date,
        top_n=request.top_n,
    )
    return CandidateRunWithItemsRead(
        run=CandidateRunRead.model_validate(run),
        items=[CandidateItemRead.model_validate(item) for item in items],
    )


@router.get("/runs/{run_id}", response_model=CandidateRunRead)
async def get_candidate_run_route(
    run_id: int,
    session: Session = Depends(get_db_session),
) -> CandidateRunRead:
    run = get_candidate_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="candidate run not found")
    return CandidateRunRead.model_validate(run)


@router.get("/runs", response_model=list[CandidateRunRead])
async def list_candidate_runs_route(
    candidate_date: date | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[CandidateRunRead]:
    runs = list_candidate_runs(session, candidate_date=candidate_date, limit=limit)
    return [CandidateRunRead.model_validate(run) for run in runs]


@router.get("/runs/by-date/{candidate_date}", response_model=CandidateRunRead)
async def get_candidate_run_by_date_route(
    candidate_date: date,
    session: Session = Depends(get_db_session),
) -> CandidateRunRead:
    run = get_latest_candidate_run_for_date(session, candidate_date)
    if run is None:
        raise HTTPException(status_code=404, detail="candidate run not found")
    return CandidateRunRead.model_validate(run)


@router.get("/runs/{run_id}/items", response_model=list[CandidateItemRead])
async def list_candidate_items_route(
    run_id: int,
    session: Session = Depends(get_db_session),
) -> list[CandidateItemRead]:
    run = get_candidate_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="candidate run not found")
    items = list_candidate_items(session, run_id)
    return [CandidateItemRead.model_validate(item) for item in items]


@router.get("/items", response_model=list[CandidateItemRead])
async def query_candidate_items_route(
    run_id: int | None = None,
    candidate_date: date | None = None,
    symbol: str | None = None,
    session: Session = Depends(get_db_session),
) -> list[CandidateItemRead]:
    items = list_candidate_items(session, run_id, candidate_date=candidate_date, symbol=symbol)
    return [CandidateItemRead.model_validate(item) for item in items]


@router.get("/summary/latest", response_model=CandidateRunWithItemsRead)
async def get_latest_candidate_summary_route(
    candidate_date: date | None = None,
    session: Session = Depends(get_db_session),
) -> CandidateRunWithItemsRead:
    run = (
        get_latest_candidate_run_for_date(session, candidate_date)
        if candidate_date is not None
        else get_latest_candidate_run(session)
    )
    if run is None:
        raise HTTPException(status_code=404, detail="candidate run not found")
    items = list_candidate_items(session, run.id)
    return CandidateRunWithItemsRead(
        run=CandidateRunRead.model_validate(run),
        items=[CandidateItemRead.model_validate(item) for item in items],
    )


@router.get("/runs/{run_id}/export")
async def export_candidate_run_route(
    run_id: int,
    export_format: Literal["json", "csv"] = Query(default="json"),
    session: Session = Depends(get_db_session),
) -> Response:
    if get_candidate_run(session, run_id) is None:
        raise HTTPException(status_code=404, detail="candidate run not found")
    file_name, content = export_candidate_items(session, run_id=run_id, export_format=export_format)
    media_type = "application/json" if export_format == "json" else "text/csv"
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{file_name}"'})
