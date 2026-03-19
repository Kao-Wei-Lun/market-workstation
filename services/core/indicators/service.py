from __future__ import annotations

from sqlalchemy.orm import Session

from services.core.indicators.base import BarDataPoint, IndicatorCalculator, PersistedIndicatorValue
from services.core.indicators.engine import IndicatorEngine
from services.db.repositories.daily_bars import DailyBarRepository
from services.db.repositories.indicator_values import IndicatorValueRepository
from services.models.indicator_value import IndicatorValue


def compute_and_persist_indicators(
    session: Session,
    *,
    instrument_id: int,
    calculators: list[IndicatorCalculator],
) -> int:
    bar_rows = DailyBarRepository(session).list_for_instrument(instrument_id)
    bar_points = [
        BarDataPoint(
            trade_date=bar.trade_date,
            close=bar.close,
            high=bar.high,
            low=bar.low,
            volume=bar.volume,
        )
        for bar in bar_rows
    ]
    outputs = IndicatorEngine(calculators).compute(bar_points)
    persisted_values = [
        PersistedIndicatorValue(
            instrument_id=instrument_id,
            trade_date=item.trade_date,
            indicator_name=item.indicator_name,
            component=item.component,
            parameter_signature=item.parameter_signature,
            value=item.value,
        )
        for item in outputs
    ]
    return IndicatorValueRepository(session).upsert_many(persisted_values)


def query_indicator_values(
    session: Session,
    *,
    instrument_id: int,
    indicator_name: str | None = None,
    component: str | None = None,
) -> list[IndicatorValue]:
    return IndicatorValueRepository(session).list_for_instrument(
        instrument_id,
        indicator_name=indicator_name,
        component=component,
    )
