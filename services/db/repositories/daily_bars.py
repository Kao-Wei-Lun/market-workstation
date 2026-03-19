from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from services.models.daily_bar import DailyBar
from services.schemas.etl import NormalizedDailyBarRecord


class DailyBarRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, records: list[NormalizedDailyBarRecord]) -> int:
        if not records:
            return 0

        loaded = 0
        for record in records:
            if record.instrument_id is None:
                msg = "instrument_id is required to persist daily bars"
                raise ValueError(msg)

            existing = (
                self.session.query(DailyBar)
                .filter(
                    DailyBar.instrument_id == record.instrument_id,
                    DailyBar.trade_date == record.trade_date,
                )
                .one_or_none()
            )

            if existing is None:
                self.session.add(
                    DailyBar(
                        instrument_id=record.instrument_id,
                        trade_date=record.trade_date,
                        open=record.open,
                        high=record.high,
                        low=record.low,
                        close=record.close,
                        volume=record.volume,
                        turnover_value=record.turnover_value,
                        transactions_count=record.transactions_count,
                        change=record.change,
                        change_percent=record.change_percent,
                    )
                )
            else:
                existing.open = record.open
                existing.high = record.high
                existing.low = record.low
                existing.close = record.close
                existing.volume = record.volume
                existing.turnover_value = record.turnover_value
                existing.transactions_count = record.transactions_count
                existing.change = record.change
                existing.change_percent = record.change_percent
            loaded += 1

        self.session.flush()
        return loaded

    def list_for_instrument(
        self,
        instrument_id: int,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[DailyBar]:
        query = self.session.query(DailyBar).filter(DailyBar.instrument_id == instrument_id)
        if start_date is not None:
            query = query.filter(DailyBar.trade_date >= start_date)
        if end_date is not None:
            query = query.filter(DailyBar.trade_date <= end_date)
        return query.order_by(DailyBar.trade_date.asc()).all()
