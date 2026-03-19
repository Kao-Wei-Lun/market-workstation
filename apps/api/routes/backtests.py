from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.core.backtesting.service import create_and_run_backtest, get_backtest_run, list_backtest_trades
from services.db.session import get_db_session
from services.schemas.backtesting import (
    BacktestCreateRequest,
    BacktestCreateResponse,
    BacktestRunRead,
    BacktestTradeRead,
    StrategyRead,
)

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/runs", response_model=BacktestCreateResponse)
async def create_backtest_run(
    request: BacktestCreateRequest,
    session: Session = Depends(get_db_session),
) -> BacktestCreateResponse:
    strategy, run = create_and_run_backtest(session, request)
    trades = list_backtest_trades(session, run.id)
    return BacktestCreateResponse(
        strategy=StrategyRead.model_validate(strategy),
        run=BacktestRunRead.model_validate(run),
        trades=[BacktestTradeRead.model_validate(trade) for trade in trades],
    )


@router.get("/runs/{run_id}", response_model=BacktestRunRead)
async def get_backtest_run_route(
    run_id: int,
    session: Session = Depends(get_db_session),
) -> BacktestRunRead:
    run = get_backtest_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="backtest run not found")
    return BacktestRunRead.model_validate(run)


@router.get("/runs/{run_id}/trades", response_model=list[BacktestTradeRead])
async def list_backtest_trades_route(
    run_id: int,
    session: Session = Depends(get_db_session),
) -> list[BacktestTradeRead]:
    run = get_backtest_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="backtest run not found")
    trades = list_backtest_trades(session, run_id)
    return [BacktestTradeRead.model_validate(trade) for trade in trades]
