from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.series_point import SeriesPoint
from services.schemas.etl import NormalizedSeriesPointRecord


class SeriesPointRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, records: list[NormalizedSeriesPointRecord]) -> int:
        if not records:
            return 0

        loaded = 0
        for record in records:
            existing = (
                self.session.query(SeriesPoint)
                .filter(
                    SeriesPoint.series_key == record.series_key,
                    SeriesPoint.trade_date == record.trade_date,
                )
                .one_or_none()
            )

            if existing is None:
                self.session.add(
                    SeriesPoint(
                        instrument_id=record.instrument_id,
                        series_key=record.series_key,
                        source_route=record.source_route,
                        trade_date=record.trade_date,
                        value=record.value,
                    )
                )
            else:
                existing.instrument_id = record.instrument_id
                existing.source_route = record.source_route
                existing.value = record.value
            loaded += 1

        self.session.flush()
        return loaded
