from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from services.core.backtesting.search import (
    create_and_run_parameter_search,
    get_parameter_search_run,
    list_parameter_search_results,
)
from services.core.backtesting.service import (
    create_and_run_backtest,
    export_backtest_run,
    get_backtest_run,
    list_backtest_runs,
    list_backtest_trades,
    query_backtest_trades,
)
from services.core.backtesting.walk_forward import (
    create_and_run_walk_forward,
    get_walk_forward_run,
    list_walk_forward_windows,
)
from services.db.session import get_db_session
from services.schemas.backtesting import (
    BacktestCreateRequest,
    BacktestCreateResponse,
    BacktestParameterSearchRequest,
    BacktestRunRead,
    BacktestSearchResponse,
    BacktestSearchResultRead,
    BacktestSearchRunRead,
    BacktestTradeRead,
    BacktestWalkForwardRequest,
    BacktestWalkForwardResponse,
    BacktestWalkForwardRunRead,
    BacktestWalkForwardWindowRead,
    StrategyRead,
)

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/runs", response_model=BacktestCreateResponse)
async def create_backtest_run(
    request: BacktestCreateRequest,
    session: Session = Depends(get_db_session),
) -> BacktestCreateResponse:
    strategy, run = create_and_run_backtest(session, request)
    session.commit()
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


@router.get("/runs", response_model=list[BacktestRunRead])
async def list_backtest_runs_route(
    strategy_id: int | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[BacktestRunRead]:
    runs = list_backtest_runs(session, strategy_id=strategy_id, limit=limit)
    return [BacktestRunRead.model_validate(run) for run in runs]


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


@router.get("/trades", response_model=list[BacktestTradeRead])
async def query_backtest_trades_route(
    run_id: int | None = None,
    instrument_id: int | None = None,
    session: Session = Depends(get_db_session),
) -> list[BacktestTradeRead]:
    trades = query_backtest_trades(session, run_id=run_id, instrument_id=instrument_id)
    return [BacktestTradeRead.model_validate(trade) for trade in trades]


@router.get("/runs/{run_id}/export")
async def export_backtest_run_route(
    run_id: int,
    export_format: Literal["json", "csv"] = Query(default="json"),
    session: Session = Depends(get_db_session),
) -> Response:
    try:
        file_name, content = export_backtest_run(session, run_id=run_id, export_format=export_format)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    media_type = "application/json" if export_format == "json" else "text/csv"
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{file_name}"'})


@router.post("/searches", response_model=BacktestSearchResponse)
async def create_parameter_search_route(
    request: BacktestParameterSearchRequest,
    session: Session = Depends(get_db_session),
) -> BacktestSearchResponse:
    strategy, search_run, results = create_and_run_parameter_search(session, request)
    session.commit()
    return BacktestSearchResponse(
        strategy=StrategyRead.model_validate(strategy),
        search_run=BacktestSearchRunRead.model_validate(search_run),
        results=[BacktestSearchResultRead.model_validate(result) for result in results],
    )


@router.get("/searches/{search_run_id}", response_model=BacktestSearchRunRead)
async def get_parameter_search_route(
    search_run_id: int,
    session: Session = Depends(get_db_session),
) -> BacktestSearchRunRead:
    search_run = get_parameter_search_run(session, search_run_id)
    if search_run is None:
        raise HTTPException(status_code=404, detail="parameter search not found")
    return BacktestSearchRunRead.model_validate(search_run)


@router.get("/searches/{search_run_id}/results", response_model=list[BacktestSearchResultRead])
async def list_parameter_search_results_route(
    search_run_id: int,
    session: Session = Depends(get_db_session),
) -> list[BacktestSearchResultRead]:
    search_run = get_parameter_search_run(session, search_run_id)
    if search_run is None:
        raise HTTPException(status_code=404, detail="parameter search not found")
    results = list_parameter_search_results(session, search_run_id)
    return [BacktestSearchResultRead.model_validate(result) for result in results]


@router.post("/walk-forward", response_model=BacktestWalkForwardResponse)
async def create_walk_forward_route(
    request: BacktestWalkForwardRequest,
    session: Session = Depends(get_db_session),
) -> BacktestWalkForwardResponse:
    strategy, walk_forward_run, windows = create_and_run_walk_forward(session, request)
    session.commit()
    return BacktestWalkForwardResponse(
        strategy=StrategyRead.model_validate(strategy),
        walk_forward_run=BacktestWalkForwardRunRead.model_validate(walk_forward_run),
        windows=[BacktestWalkForwardWindowRead.model_validate(window) for window in windows],
    )


@router.get("/walk-forward/{walk_forward_run_id}", response_model=BacktestWalkForwardRunRead)
async def get_walk_forward_route(
    walk_forward_run_id: int,
    session: Session = Depends(get_db_session),
) -> BacktestWalkForwardRunRead:
    walk_forward_run = get_walk_forward_run(session, walk_forward_run_id)
    if walk_forward_run is None:
        raise HTTPException(status_code=404, detail="walk-forward run not found")
    return BacktestWalkForwardRunRead.model_validate(walk_forward_run)


@router.get("/walk-forward/{walk_forward_run_id}/windows", response_model=list[BacktestWalkForwardWindowRead])
async def list_walk_forward_windows_route(
    walk_forward_run_id: int,
    session: Session = Depends(get_db_session),
) -> list[BacktestWalkForwardWindowRead]:
    walk_forward_run = get_walk_forward_run(session, walk_forward_run_id)
    if walk_forward_run is None:
        raise HTTPException(status_code=404, detail="walk-forward run not found")
    windows = list_walk_forward_windows(session, walk_forward_run_id)
    return [BacktestWalkForwardWindowRead.model_validate(window) for window in windows]
