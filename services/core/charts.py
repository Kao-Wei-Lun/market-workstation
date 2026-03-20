from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session

from services.core.derivatives.summary import DailyInstitutionalBiasSummary, load_daily_institutional_bias_summary
from services.db.repositories.chart_annotations import ChartAnnotationRepository
from services.db.repositories.daily_bars import DailyBarRepository
from services.db.repositories.indicator_values import IndicatorValueRepository
from services.db.repositories.instruments import InstrumentRepository
from services.models.instrument import Instrument
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
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

    derivatives_rows: list[TwDerivativesDaily] = (
        session.query(TwDerivativesDaily)
        .filter(
            TwDerivativesDaily.trade_date >= trade_dates[0],
            TwDerivativesDaily.trade_date <= trade_dates[-1],
            TwDerivativesDaily.institution == "foreign_investors",
        )
        .order_by(TwDerivativesDaily.trade_date.asc(), TwDerivativesDaily.product_code.asc())
        .all()
    )
    feature_rows: list[TwDerivativesFeature] = (
        session.query(TwDerivativesFeature)
        .filter(
            TwDerivativesFeature.trade_date >= trade_dates[0],
            TwDerivativesFeature.trade_date <= trade_dates[-1],
            TwDerivativesFeature.institution == "foreign_investors",
        )
        .order_by(TwDerivativesFeature.trade_date.asc())
        .all()
    )

    by_date: dict[date, dict[str, Decimal | int | None]] = {
        trade_date: {
            "futures_net_open_interest": 0,
            "futures_net_amount": Decimal("0"),
            "options_net_open_interest": 0,
            "options_net_amount": Decimal("0"),
            "average_bias_score": None,
            "bullish_count": 0,
            "bearish_count": 0,
            "anomaly_count": 0,
        }
        for trade_date in trade_dates
    }
    for row in derivatives_rows:
        bucket = by_date.setdefault(
            row.trade_date,
            {
                "futures_net_open_interest": 0,
                "futures_net_amount": Decimal("0"),
                "options_net_open_interest": 0,
                "options_net_amount": Decimal("0"),
                "average_bias_score": None,
                "bullish_count": 0,
                "bearish_count": 0,
                "anomaly_count": 0,
            },
        )
        if row.is_options:
            bucket["options_net_open_interest"] = int(bucket["options_net_open_interest"] or 0) + row.net_open_interest
            bucket["options_net_amount"] = (bucket["options_net_amount"] or Decimal("0")) + (row.net_amount or Decimal("0"))
        else:
            bucket["futures_net_open_interest"] = int(bucket["futures_net_open_interest"] or 0) + row.net_open_interest
            bucket["futures_net_amount"] = (bucket["futures_net_amount"] or Decimal("0")) + (row.net_amount or Decimal("0"))

    feature_by_date: dict[date, list[TwDerivativesFeature]] = defaultdict(list)
    for feature_row in feature_rows:
        feature_by_date[feature_row.trade_date].append(feature_row)

    flow_points: list[InstitutionalFlowPointRead] = []
    for trade_date in trade_dates:
        features = feature_by_date.get(trade_date, [])
        summary = generate_institutional_flow_summary(trade_date, features)
        bucket = by_date[trade_date]
        futures_net_amount = cast(Decimal | None, bucket["futures_net_amount"])
        options_net_amount = cast(Decimal | None, bucket["options_net_amount"])
        flow_points.append(
            InstitutionalFlowPointRead(
                trade_date=trade_date,
                futures_net_open_interest=int(bucket["futures_net_open_interest"] or 0),
                futures_net_amount=futures_net_amount,
                options_net_open_interest=int(bucket["options_net_open_interest"] or 0),
                options_net_amount=options_net_amount,
                average_bias_score=summary.average_bias_score if features else None,
                bullish_count=summary.bullish_count,
                bearish_count=summary.bearish_count,
                anomaly_count=summary.anomaly_count,
            )
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
        spot_flow_available=False,
        summary_highlights=[
            "目前先提供外資期貨／選擇權未平倉與 bias foundation，現貨買賣超待 V1 後續資料源擴充。",
            *latest_summary.highlights[:3],
        ],
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


def _chart_instrument_read(instrument: object, *, latest_data_date: date | None) -> ChartInstrumentRead:
    base = ChartInstrumentRead.model_validate(instrument)
    return base.model_copy(update={"latest_data_date": latest_data_date})
