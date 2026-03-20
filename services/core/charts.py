from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Sequence, cast

from sqlalchemy.orm import Session

from services.core.derivatives.summary import DailyInstitutionalBiasSummary, load_daily_institutional_bias_summary
from services.db.repositories.chart_annotations import ChartAnnotationRepository
from services.db.repositories.daily_bars import DailyBarRepository
from services.db.repositories.indicator_values import IndicatorValueRepository
from services.db.repositories.instruments import InstrumentRepository
from services.db.repositories.tw_institutional_spot import TwInstitutionalSpotDailyRepository
from services.models.daily_bar import DailyBar
from services.models.instrument import Instrument
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.tw_institutional_spot_daily import TwInstitutionalSpotDaily
from services.schemas.charts import (
    ChartAnnotationCreate,
    ChartAnnotationRead,
    ChartCandleRead,
    ChartDataRead,
    ChartIndicatorPointRead,
    ChartIndicatorSeriesRead,
    ChartInstrumentRead,
    InstitutionalFlowChartRead,
    InstitutionalFlowPointRead,
    MarketStructureChartRead,
    MarketStructureSummaryRead,
)

DEFAULT_CHART_INDICATORS = ("sma", "ema", "bollinger", "supertrend")


def list_chart_instruments(
    session: Session,
    *,
    query: str | None = None,
    market: str | None = None,
    asset_type: str | None = None,
    limit: int = 50,
) -> list[ChartInstrumentRead]:
    rows = InstrumentRepository(session).list_for_chart_selection(
        query=query,
        market=market,
        asset_type=asset_type,
        limit=limit,
    )
    return [
        _chart_instrument_read(instrument, latest_data_date=latest_data_date)
        for instrument, latest_data_date in rows
    ]


def load_chart_data(
    session: Session,
    *,
    symbol: str,
    date_from: date | None = None,
    date_to: date | None = None,
    indicator_names: list[str] | None = None,
    view_kind: str = "instrument",
) -> ChartDataRead:
    instrument = _require_instrument(session, symbol)
    daily_bars = DailyBarRepository(session).list_for_instrument(
        instrument.id,
        start_date=date_from,
        end_date=date_to,
    )
    normalized_indicator_names = [item.strip().lower() for item in (indicator_names or list(DEFAULT_CHART_INDICATORS)) if item.strip()]
    indicator_rows = []
    if normalized_indicator_names:
        indicator_repo = IndicatorValueRepository(session)
        for indicator_name in normalized_indicator_names:
            indicator_rows.extend(
                indicator_repo.list_for_instrument(
                    instrument.id,
                    indicator_name=indicator_name,
                    start_date=date_from,
                    end_date=date_to,
                )
            )

    grouped_indicators: dict[tuple[str, str, str], list[ChartIndicatorPointRead]] = defaultdict(list)
    for item in indicator_rows:
        grouped_indicators[(item.indicator_name, item.component, item.parameter_signature)].append(
            ChartIndicatorPointRead(trade_date=item.trade_date, value=item.value)
        )

    return ChartDataRead(
        instrument=_chart_instrument_read(
            instrument,
            latest_data_date=daily_bars[-1].trade_date if daily_bars else None,
        ),
        candles=[
            ChartCandleRead(
                trade_date=item.trade_date,
                open=item.open,
                high=item.high,
                low=item.low,
                close=item.close,
                volume=item.volume,
                change_percent=item.change_percent,
            )
            for item in daily_bars
        ],
        indicators=[
            ChartIndicatorSeriesRead(
                indicator_name=indicator_name,
                component=component,
                parameter_signature=parameter_signature,
                points=points,
            )
            for (indicator_name, component, parameter_signature), points in sorted(grouped_indicators.items())
        ],
        annotations=[
            ChartAnnotationRead.model_validate(item)
            for item in ChartAnnotationRepository(session).list_for_instrument(instrument.id, view_kind=view_kind)
        ],
        available_indicator_keys=sorted({item.indicator_name for item in indicator_rows}),
    )


def create_chart_annotation(session: Session, payload: ChartAnnotationCreate) -> ChartAnnotationRead:
    instrument = _require_instrument(session, payload.symbol)
    _validate_annotation_payload(payload)
    annotation = ChartAnnotationRepository(session).create(
        instrument_id=instrument.id,
        symbol_snapshot=instrument.symbol,
        payload=payload,
    )
    session.commit()
    session.refresh(annotation)
    return ChartAnnotationRead.model_validate(annotation)


def delete_chart_annotation(session: Session, annotation_id: int) -> bool:
    repository = ChartAnnotationRepository(session)
    annotation = repository.get(annotation_id)
    if annotation is None:
        return False
    repository.delete(annotation)
    session.commit()
    return True


def list_chart_annotations(
    session: Session,
    *,
    symbol: str,
    view_kind: str,
) -> list[ChartAnnotationRead]:
    instrument = _require_instrument(session, symbol)
    return [
        ChartAnnotationRead.model_validate(item)
        for item in ChartAnnotationRepository(session).list_for_instrument(instrument.id, view_kind=view_kind)
    ]


def clear_chart_annotations(
    session: Session,
    *,
    symbol: str,
    view_kind: str,
) -> int:
    instrument = _require_instrument(session, symbol)
    deleted = ChartAnnotationRepository(session).clear_for_instrument(instrument.id, view_kind=view_kind)
    session.commit()
    return deleted


def load_institutional_flow_chart(
    session: Session,
    *,
    symbol: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> InstitutionalFlowChartRead:
    instrument = _require_instrument(session, symbol)
    candles = DailyBarRepository(session).list_for_instrument(
        instrument.id,
        start_date=date_from,
        end_date=date_to,
    )
    trade_dates = [item.trade_date for item in candles]
    if not trade_dates:
        return InstitutionalFlowChartRead(
            instrument=_chart_instrument_read(instrument, latest_data_date=None),
            candles=[],
            flow_points=[],
            summary_highlights=["目前尚無可供法人流向圖表使用的日線資料。"],
        )

    flow_points = _build_market_structure_points(
        session,
        market=instrument.market,
        trade_dates=trade_dates,
        start_date=trade_dates[0],
        end_date=trade_dates[-1],
    )

    latest_summary = load_daily_institutional_bias_summary(session, trade_date=trade_dates[-1])
    return InstitutionalFlowChartRead(
        instrument=_chart_instrument_read(instrument, latest_data_date=trade_dates[-1]),
        candles=[
            ChartCandleRead(
                trade_date=item.trade_date,
                open=item.open,
                high=item.high,
                low=item.low,
                close=item.close,
                volume=item.volume,
                change_percent=item.change_percent,
            )
            for item in candles
        ],
        flow_points=flow_points,
        spot_flow_available=any(point.spot_net_amount is not None for point in flow_points),
        summary_highlights=[
            "目前可同時對照外資現貨、期貨與選擇權方向，但現貨仍屬 market-level summary。",
            *latest_summary.highlights[:3],
        ],
    )


def load_market_structure_chart(
    session: Session,
    *,
    symbol: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> MarketStructureChartRead:
    instrument = _require_instrument(session, symbol)
    candles = DailyBarRepository(session).list_for_instrument(
        instrument.id,
        start_date=date_from,
        end_date=date_to,
    )
    trade_dates = [item.trade_date for item in candles]
    flow_points = (
        _build_market_structure_points(
            session,
            market=instrument.market,
            trade_dates=trade_dates,
            start_date=trade_dates[0],
            end_date=trade_dates[-1],
        )
        if trade_dates
        else []
    )
    latest_point = flow_points[-1] if flow_points else None
    latest_bias_summary = (
        load_daily_institutional_bias_summary(session, trade_date=trade_dates[-1])
        if trade_dates
        else DailyInstitutionalBiasSummary(
            trade_date=date_from or date.today(),
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            anomaly_count=0,
            average_bias_score=Decimal("0"),
            overall_regime="neutral",
            highlights=[],
        )
    )
    summary = MarketStructureSummaryRead(
        trade_date=trade_dates[-1] if trade_dates else None,
        overall_regime=latest_bias_summary.overall_regime,
        spot_direction=_direction_label(latest_point.spot_net_amount if latest_point else None),
        futures_direction=_direction_label(latest_point.futures_net_amount if latest_point else None),
        options_direction=_direction_label(latest_point.options_directional_bias if latest_point else None),
        divergence_hints=_build_divergence_hints(candles, latest_point),
        anomaly_hints=_build_anomaly_hints(latest_point, latest_bias_summary),
        highlights=_build_market_structure_highlights(candles, latest_point, latest_bias_summary),
    )
    return MarketStructureChartRead(
        instrument=_chart_instrument_read(
            instrument,
            latest_data_date=trade_dates[-1] if trade_dates else None,
        ),
        candles=[
            ChartCandleRead(
                trade_date=item.trade_date,
                open=item.open,
                high=item.high,
                low=item.low,
                close=item.close,
                volume=item.volume,
                change_percent=item.change_percent,
            )
            for item in candles
        ],
        flow_points=flow_points,
        available_series=["spot_net_amount", "futures_net_open_interest", "options_directional_bias", "average_bias_score"],
        summary=summary,
    )


def generate_institutional_flow_summary(
    trade_date: date,
    features: list[TwDerivativesFeature],
) -> DailyInstitutionalBiasSummary:
    if not features:
        return DailyInstitutionalBiasSummary(
            trade_date=trade_date,
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            anomaly_count=0,
            average_bias_score=Decimal("0"),
            overall_regime="neutral",
            highlights=[],
        )
    return load_daily_institutional_bias_summary_from_features(trade_date, features)


def load_daily_institutional_bias_summary_from_features(
    trade_date: date,
    features: list[TwDerivativesFeature],
) -> DailyInstitutionalBiasSummary:
    from services.core.derivatives.summary import generate_daily_institutional_bias_summary

    return generate_daily_institutional_bias_summary(trade_date, features)


def _require_instrument(session: Session, symbol: str) -> Instrument:
    instrument = InstrumentRepository(session).get_by_symbol(symbol)
    if instrument is None:
        msg = f"instrument not found: {symbol}"
        raise ValueError(msg)
    return instrument


def _validate_annotation_payload(payload: ChartAnnotationCreate) -> None:
    if payload.annotation_type == "horizontal_line":
        _require_payload_keys(payload, "price")
        return
    if payload.annotation_type == "vertical_line":
        _require_payload_keys(payload, "trade_date")
        return
    if payload.annotation_type == "point_marker":
        _require_payload_keys(payload, "trade_date", "price")
        return
    if payload.annotation_type in {"trend_line", "range_box"}:
        _require_payload_keys(payload, "start_date", "start_price", "end_date", "end_price")
        return


def _require_payload_keys(payload: ChartAnnotationCreate, *keys: str) -> None:
    missing = [key for key in keys if payload.payload_json.get(key) in (None, "")]
    if not missing:
        return
    msg = f"annotation payload missing required keys: {', '.join(missing)}"
    raise ValueError(msg)


def _chart_instrument_read(instrument: object, *, latest_data_date: date | None) -> ChartInstrumentRead:
    base = ChartInstrumentRead.model_validate(instrument)
    return base.model_copy(update={"latest_data_date": latest_data_date})


def _build_market_structure_points(
    session: Session,
    *,
    market: str,
    trade_dates: list[date],
    start_date: date,
    end_date: date,
) -> list[InstitutionalFlowPointRead]:
    derivatives_rows: list[TwDerivativesDaily] = (
        session.query(TwDerivativesDaily)
        .filter(
            TwDerivativesDaily.trade_date >= start_date,
            TwDerivativesDaily.trade_date <= end_date,
            TwDerivativesDaily.institution == "foreign_investors",
        )
        .order_by(TwDerivativesDaily.trade_date.asc(), TwDerivativesDaily.product_code.asc())
        .all()
    )
    feature_rows: list[TwDerivativesFeature] = (
        session.query(TwDerivativesFeature)
        .filter(
            TwDerivativesFeature.trade_date >= start_date,
            TwDerivativesFeature.trade_date <= end_date,
            TwDerivativesFeature.institution == "foreign_investors",
        )
        .order_by(TwDerivativesFeature.trade_date.asc())
        .all()
    )
    spot_rows: list[TwInstitutionalSpotDaily] = TwInstitutionalSpotDailyRepository(session).list_for_market(
        market=market,
        institution="foreign_investors",
        start_date=start_date,
        end_date=end_date,
    )

    by_date: dict[date, dict[str, Decimal | int | None]] = {
        trade_date: {
            "spot_net_amount": None,
            "futures_net_open_interest": 0,
            "futures_net_amount": Decimal("0"),
            "options_net_open_interest": 0,
            "options_net_amount": Decimal("0"),
            "options_directional_bias": None,
            "average_bias_score": None,
            "bullish_count": 0,
            "bearish_count": 0,
            "anomaly_count": 0,
        }
        for trade_date in trade_dates
    }

    for spot_row in spot_rows:
        bucket = by_date.setdefault(spot_row.trade_date, {})
        bucket["spot_net_amount"] = spot_row.net_amount

    for derivative_row in derivatives_rows:
        bucket = by_date.setdefault(
            derivative_row.trade_date,
            {
                "spot_net_amount": None,
                "futures_net_open_interest": 0,
                "futures_net_amount": Decimal("0"),
                "options_net_open_interest": 0,
                "options_net_amount": Decimal("0"),
                "options_directional_bias": None,
                "average_bias_score": None,
                "bullish_count": 0,
                "bearish_count": 0,
                "anomaly_count": 0,
            },
        )
        if derivative_row.is_options:
            bucket["options_net_open_interest"] = (
                int(bucket["options_net_open_interest"] or 0) + derivative_row.net_open_interest
            )
            bucket["options_net_amount"] = (bucket["options_net_amount"] or Decimal("0")) + (
                derivative_row.net_amount or Decimal("0")
            )
        else:
            bucket["futures_net_open_interest"] = (
                int(bucket["futures_net_open_interest"] or 0) + derivative_row.net_open_interest
            )
            bucket["futures_net_amount"] = (bucket["futures_net_amount"] or Decimal("0")) + (
                derivative_row.net_amount or Decimal("0")
            )

    feature_by_date: dict[date, list[TwDerivativesFeature]] = defaultdict(list)
    for feature_row in feature_rows:
        feature_by_date[feature_row.trade_date].append(feature_row)

    flow_points: list[InstitutionalFlowPointRead] = []
    for trade_date in trade_dates:
        features = feature_by_date.get(trade_date, [])
        summary = generate_institutional_flow_summary(trade_date, features)
        options_features = [feature for feature in features if feature.call_put is not None]
        options_directional_bias = (
            sum((feature.bias_score for feature in options_features), Decimal("0")) / Decimal(len(options_features))
            if options_features
            else None
        )
        bucket = by_date[trade_date]
        futures_net_amount = cast(Decimal | None, bucket["futures_net_amount"])
        options_net_amount = cast(Decimal | None, bucket["options_net_amount"])
        spot_net_amount = cast(Decimal | None, bucket["spot_net_amount"])
        flow_points.append(
            InstitutionalFlowPointRead(
                trade_date=trade_date,
                spot_net_amount=spot_net_amount,
                futures_net_open_interest=int(bucket["futures_net_open_interest"] or 0),
                futures_net_amount=futures_net_amount,
                options_net_open_interest=int(bucket["options_net_open_interest"] or 0),
                options_net_amount=options_net_amount,
                options_directional_bias=options_directional_bias,
                average_bias_score=summary.average_bias_score if features else None,
                bullish_count=summary.bullish_count,
                bearish_count=summary.bearish_count,
                anomaly_count=summary.anomaly_count,
            )
        )
    return flow_points


def _direction_label(value: Decimal | None) -> str:
    if value is None:
        return "無資料"
    if value > 0:
        return "偏多"
    if value < 0:
        return "偏空"
    return "中性"


def _build_divergence_hints(
    candles: Sequence[DailyBar],
    latest_point: InstitutionalFlowPointRead | None,
) -> list[str]:
    if not candles or latest_point is None:
        return []
    latest_candle = candles[-1]
    change_percent = latest_candle.change_percent
    hints: list[str] = []
    if change_percent is not None and latest_point.spot_net_amount is not None:
        if change_percent > 0 and latest_point.spot_net_amount < 0:
            hints.append("指數上漲但外資現貨賣超，短線需留意追價風險。")
        if change_percent < 0 and latest_point.futures_net_open_interest > 0:
            hints.append("指數回落但外資期貨淨多增加，可能出現期現分歧。")
    if latest_point.options_directional_bias is not None and latest_point.options_directional_bias < 0 and latest_point.futures_net_open_interest > 0:
        hints.append("期貨偏多但選擇權方向偏空，需留意避險性布局。")
    return hints


def _build_anomaly_hints(
    latest_point: InstitutionalFlowPointRead | None,
    latest_bias_summary: DailyInstitutionalBiasSummary,
) -> list[str]:
    hints: list[str] = []
    if latest_point is None:
        return hints
    if latest_point.anomaly_count > 0:
        hints.append(f"最新一日有 {latest_point.anomaly_count} 筆法人特徵異常。")
    if latest_bias_summary.overall_regime != "neutral" and latest_bias_summary.anomaly_count > 0:
        hints.append("偏向結論與異常同時出現，建議配合報表與候選頁交叉確認。")
    return hints


def _build_market_structure_highlights(
    candles: Sequence[DailyBar],
    latest_point: InstitutionalFlowPointRead | None,
    latest_bias_summary: DailyInstitutionalBiasSummary,
) -> list[str]:
    if not candles or latest_point is None:
        return ["目前尚無完整的市場結構資料。"]
    latest_candle = candles[-1]
    highlights = [
        f"最新資料日為 {latest_candle.trade_date.isoformat()}，大盤收在 {latest_candle.close}。",
        f"外資現貨{_direction_label(latest_point.spot_net_amount)}、期貨{_direction_label(latest_point.futures_net_amount)}、選擇權{_direction_label(latest_point.options_directional_bias)}。",
        f"整體法人 regime 為 {latest_bias_summary.overall_regime}。",
    ]
    highlights.extend(latest_bias_summary.highlights[:2])
    return highlights
