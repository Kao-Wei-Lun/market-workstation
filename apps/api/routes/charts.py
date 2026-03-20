from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from services.core.charts import (
    clear_chart_annotations,
    create_chart_annotation,
    delete_chart_annotation,
    list_chart_instruments,
    load_chart_data,
    load_institutional_flow_chart,
    load_market_structure_chart,
)
from services.db.session import get_db_session
from services.schemas.charts import (
    ChartAnnotationCreate,
    ChartAnnotationRead,
    ChartDataRead,
    ChartInstrumentRead,
    InstitutionalFlowChartRead,
    MarketStructureChartRead,
)

router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.get("/instruments", response_model=list[ChartInstrumentRead])
async def list_chart_instruments_route(
    query: str | None = None,
    market: str | None = None,
    asset_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[ChartInstrumentRead]:
    return list_chart_instruments(
        session,
        query=query,
        market=market,
        asset_type=asset_type,
        limit=limit,
    )


@router.get("/ohlcv/{symbol}", response_model=ChartDataRead)
async def get_chart_data_route(
    symbol: str,
    date_from: date | None = None,
    date_to: date | None = None,
    indicator_name: list[str] | None = Query(default=None),
    view_kind: str = Query(default="instrument"),
    session: Session = Depends(get_db_session),
) -> ChartDataRead:
    try:
        return load_chart_data(
            session,
            symbol=symbol,
            date_from=date_from,
            date_to=date_to,
            indicator_names=indicator_name,
            view_kind=view_kind,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/institutional-flow/{symbol}", response_model=InstitutionalFlowChartRead)
async def get_institutional_flow_chart_route(
    symbol: str,
    date_from: date | None = None,
    date_to: date | None = None,
    session: Session = Depends(get_db_session),
) -> InstitutionalFlowChartRead:
    try:
        return load_institutional_flow_chart(
            session,
            symbol=symbol,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/market-structure/{symbol}", response_model=MarketStructureChartRead)
async def get_market_structure_chart_route(
    symbol: str,
    date_from: date | None = None,
    date_to: date | None = None,
    session: Session = Depends(get_db_session),
) -> MarketStructureChartRead:
    try:
        return load_market_structure_chart(
            session,
            symbol=symbol,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/annotations", response_model=ChartAnnotationRead)
async def create_chart_annotation_route(
    payload: ChartAnnotationCreate,
    session: Session = Depends(get_db_session),
) -> ChartAnnotationRead:
    try:
        return create_chart_annotation(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/annotations/{annotation_id}", status_code=204, response_class=Response)
async def delete_chart_annotation_route(
    annotation_id: int,
    session: Session = Depends(get_db_session),
) -> Response:
    if not delete_chart_annotation(session, annotation_id):
        raise HTTPException(status_code=404, detail="chart annotation not found")
    return Response(status_code=204)


@router.delete("/annotations/clear/{symbol}")
async def clear_chart_annotations_route(
    symbol: str,
    view_kind: str = Query(default="instrument"),
    session: Session = Depends(get_db_session),
) -> dict[str, int | str]:
    try:
        deleted = clear_chart_annotations(session, symbol=symbol, view_kind=view_kind)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"symbol": symbol, "deleted": deleted}
