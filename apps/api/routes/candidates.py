from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.core.candidates.service import (
    generate_and_persist_candidate_run,
    get_candidate_run,
    get_latest_candidate_run_for_date,
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
