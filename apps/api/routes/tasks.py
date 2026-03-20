from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from services.core.operations import build_manual_task_center, execute_manual_task
from services.db.session import get_db_session
from services.schemas.operations import ManualTaskCenterRead, ManualTaskRunRead, ManualTaskRunRequest

router = APIRouter(prefix="/api/system/tasks", tags=["system"])


@router.get("", response_model=ManualTaskCenterRead)
async def get_manual_task_center_route(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db_session),
) -> ManualTaskCenterRead:
    return build_manual_task_center(session, limit=limit)


@router.post("/{action_key}", response_model=ManualTaskRunRead)
async def run_manual_task_route(
    action_key: str,
    request: ManualTaskRunRequest,
    session: Session = Depends(get_db_session),
) -> ManualTaskRunRead:
    try:
        return execute_manual_task(
            session,
            action_key=action_key,
            trade_date=request.trade_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
