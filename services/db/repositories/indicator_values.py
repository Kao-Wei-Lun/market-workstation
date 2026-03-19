from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from services.core.indicators.base import PersistedIndicatorValue
from services.models.indicator_value import IndicatorValue


class IndicatorValueRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, values: list[PersistedIndicatorValue]) -> int:
        if not values:
            return 0

        persisted = 0
        for item in values:
            existing = (
                self.session.query(IndicatorValue)
                .filter(
                    IndicatorValue.instrument_id == item.instrument_id,
                    IndicatorValue.trade_date == item.trade_date,
                    IndicatorValue.indicator_name == item.indicator_name,
                    IndicatorValue.component == item.component,
                    IndicatorValue.parameter_signature == item.parameter_signature,
                )
                .one_or_none()
            )

            if existing is None:
                self.session.add(
                    IndicatorValue(
                        instrument_id=item.instrument_id,
                        trade_date=item.trade_date,
                        indicator_name=item.indicator_name,
                        component=item.component,
                        parameter_signature=item.parameter_signature,
                        value=item.value,
                    )
                )
            else:
                existing.value = item.value
            persisted += 1

        self.session.flush()
        return persisted

    def list_for_instrument(
        self,
        instrument_id: int,
        *,
        indicator_name: str | None = None,
        component: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[IndicatorValue]:
        query = self.session.query(IndicatorValue).filter(IndicatorValue.instrument_id == instrument_id)
        if indicator_name is not None:
            query = query.filter(IndicatorValue.indicator_name == indicator_name)
        if component is not None:
            query = query.filter(IndicatorValue.component == component)
        if start_date is not None:
            query = query.filter(IndicatorValue.trade_date >= start_date)
        if end_date is not None:
            query = query.filter(IndicatorValue.trade_date <= end_date)
        return query.order_by(IndicatorValue.trade_date.asc()).all()
